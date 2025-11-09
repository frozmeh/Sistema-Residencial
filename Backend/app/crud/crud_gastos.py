from sqlalchemy.orm import Session
from fastapi import HTTPException
from decimal import Decimal
from datetime import date
from typing import List, Optional
from .. import models, schemas
from ..utils.tasa_bcv import obtener_tasa_bcv, obtener_tasa_historica_bcv
from ..utils.auditoria_helpers import registrar_auditoria
from ..utils.db_helpers import guardar_y_refrescar

# ==================================================
# =============== FUNCIONES AUXILIARES =============
# ==================================================


def obtener_apartamentos_desde_pisos_torres(
    db: Session, id_pisos: Optional[List[int]] = None, id_torres: Optional[List[int]] = None
) -> List[int]:
    """
    Devuelve una lista de IDs de apartamentos a partir de pisos o torres.
    """
    apartamentos = set()

    if id_pisos:
        pisos = db.query(models.Piso).filter(models.Piso.id.in_(id_pisos)).all()
        for piso in pisos:
            apts = db.query(models.Apartamento.id).filter(models.Apartamento.id_piso == piso.id).all()
            apartamentos.update([apt[0] for apt in apts])

    if id_torres:
        torres = db.query(models.Torre).filter(models.Torre.id.in_(id_torres)).all()
        for torre in torres:
            pisos = db.query(models.Piso.id).filter(models.Piso.id_torre == torre.id).all()
            for piso_id in [p[0] for p in pisos]:
                apts = db.query(models.Apartamento.id).filter(models.Apartamento.id_piso == piso_id).all()
                apartamentos.update([apt[0] for apt in apts])

    return list(apartamentos)


def calcular_montos(
    monto_usd: Optional[Decimal],
    monto_bs: Optional[Decimal],
    tasa_bcv: Decimal,
    fecha: date,
    usar_tasa_historica: bool = True,
):
    """
    Calcula y devuelve ambos montos (USD y Bs) usando la tasa BCV actual.
    """

    if monto_usd is None and monto_bs is None:
        raise HTTPException(status_code=400, detail="Debe proporcionar monto en USD o Bs")

    if usar_tasa_historica:
        from ..utils.tasa_bcv import obtener_tasa_historica_bcv

        tasa_bcv, fecha_tasa = obtener_tasa_historica_bcv(fecha)
    else:
        from ..utils.tasa_bcv import obtener_tasa_bcv

        tasa_bcv, fecha_tasa = obtener_tasa_bcv()

    if monto_usd is None:
        monto_usd = Decimal(str(monto_bs)) / tasa_bcv
    if monto_bs is None:
        monto_bs = Decimal(str(monto_usd)) * tasa_bcv

    return round(monto_usd, 2), round(monto_bs, 2), tasa_bcv, fecha_tasa


def asignar_montos_a_apartamentos(
    db: Session, gasto: models.GastoVariable, apartamentos_ids: List[int], tasa_bcv: Decimal
):
    """
    Asigna montos a apartamentos en tabla intermedia
    Aplica porcentaje de aporte sobre el MONTO TOTAL, no sobre la parte equitativa
    """
    if not apartamentos_ids:
        return

    # Eliminar asignaciones previas
    db.execute(
        models.gastos_variables_apartamentos.delete().where(
            models.gastos_variables_apartamentos.c.id_gasto_variable == gasto.id
        )
    )

    # Calcular suma total de porcentajes para normalizar
    total_porcentaje = Decimal(0)
    porcentajes_apartamentos = {}

    for apt_id in apartamentos_ids:
        apt = db.query(models.Apartamento).filter(models.Apartamento.id == apt_id).first()
        if not apt:
            continue

        porcentaje = Decimal(100)  # Por defecto 100% (distribución equitativa)

        # Si tiene tipo de apartamento, usar su porcentaje de aporte
        if hasattr(apt, "id_tipo_apartamento") and apt.id_tipo_apartamento:
            tipo = (
                db.query(models.TipoApartamento).filter(models.TipoApartamento.id == apt.id_tipo_apartamento).first()
            )
            if tipo and hasattr(tipo, "porcentaje_aporte"):
                porcentaje = Decimal(str(tipo.porcentaje_aporte))

        porcentajes_apartamentos[apt_id] = porcentaje
        total_porcentaje += porcentaje

    # Si no hay porcentajes, distribución equitativa
    if total_porcentaje == 0:
        total_porcentaje = Decimal(100) * len(apartamentos_ids)
        for apt_id in apartamentos_ids:
            porcentajes_apartamentos[apt_id] = Decimal(100)

    # Aplicar porcentaje sobre el MONTO TOTAL
    for apt_id in apartamentos_ids:
        porcentaje = porcentajes_apartamentos[apt_id]
        monto_final_usd = (gasto.monto_usd * porcentaje) / total_porcentaje
        monto_final_bs = round(monto_final_usd * tasa_bcv, 2)
        monto_final_usd = round(monto_final_usd, 2)

        db.execute(
            models.gastos_variables_apartamentos.insert().values(
                id_gasto_variable=gasto.id,
                id_apartamento=apt_id,
                monto_asignado_usd=monto_final_usd,
                monto_asignado_bs=monto_final_bs,
            )
        )
    db.commit()


# ==================================================
# ================ GASTOS FIJOS ====================
# ==================================================


def crear_gasto_fijo(db: Session, gasto: schemas.GastoFijoCreate, usuario_actual: None, request=None):
    """
    Crea un gasto fijo, ya sea para un apartamento específico o distribuido entre todos.
    """
    fecha_gasto = gasto.fecha_creacion or date.today()
    monto_usd, monto_bs, tasa_bcv, fecha_tasa = calcular_montos(
        gasto.monto_usd, gasto.monto_bs, fecha_gasto, usar_tasa_historica=True
    )

    # Caso 1: Gasto asociado a un solo apartamento
    if gasto.id_apartamento:
        apt = db.query(models.Apartamento).filter(models.Apartamento.id == gasto.id_apartamento).first()
        if not apt:
            raise HTTPException(status_code=404, detail="Apartamento no encontrado")

        monto_usd, monto_bs = calcular_montos(gasto.monto_usd, gasto.monto_bs, tasa_bcv)

        nuevo_gasto = models.GastoFijo(
            tipo_gasto=gasto.tipo_gasto,
            monto_usd=monto_usd,
            monto_bs=monto_bs,
            tasa_cambio=tasa_bcv,
            descripcion=gasto.descripcion,
            responsable=gasto.responsable,
            id_reporte_financiero=gasto.id_reporte_financiero,
            id_apartamento=apt.id,
            fecha_creacion=gasto.fecha_creacion or date.today(),
            fecha_tasa_bcv=fecha_tasa,
        )
        db.add(nuevo_gasto)
        db.commit()
        db.refresh(nuevo_gasto)
        if usuario_actual:
            registrar_auditoria(
                db=db,
                usuario_id=usuario_actual.id,
                usuario_nombre=usuario_actual.nombre,
                accion="Creación de gasto fijo",
                tabla="gastos_fijos",
                objeto_previo=None,
                objeto_nuevo={c.name: getattr(nuevo_gasto, c.name) for c in nuevo_gasto.__table__.columns},
                request=request,
                campos_visibles=[
                    "tipo_gasto",
                    "monto_usd",
                    "monto_bs",
                    "responsable",
                    "descripcion",
                    "id_apartamento",
                ],
                forzar=True,
            )

        return nuevo_gasto

    # Caso 2: Gasto general — se reparte según porcentaje de aporte
    apartamentos = db.query(models.Apartamento).all()
    if not apartamentos:
        raise HTTPException(status_code=404, detail="No hay apartamentos registrados")

    gastos_creados = []
    for apt in apartamentos:
        tipo = db.query(models.TipoApartamento).filter(models.TipoApartamento.id == apt.id_tipo_apartamento).first()
        if not tipo:
            raise HTTPException(status_code=404, detail=f"Tipo de apartamento no encontrado para apt {apt.id}")

        # Aplicar porcentaje sobre el monto total
        monto_usd = Decimal(str(gasto.monto_usd)) * Decimal(str(tipo.porcentaje_aporte)) / Decimal("100")
        monto_bs = monto_usd * tasa_bcv

        nuevo_gasto = models.GastoFijo(
            tipo_gasto=gasto.tipo_gasto,
            monto_usd=round(monto_usd, 2),
            monto_bs=round(monto_bs, 2),
            descripcion=gasto.descripcion,
            responsable=gasto.responsable,
            id_reporte_financiero=gasto.id_reporte_financiero,
            id_apartamento=apt.id,
            fecha_creacion=gasto.fecha_creacion or date.today(),
            fecha_tasa_bcv=fecha_tasa,
        )
        db.add(nuevo_gasto)
        gastos_creados.append(nuevo_gasto)

    db.commit()
    for g in gastos_creados:
        db.refresh(g)

    if usuario_actual and gastos_creados:
        registrar_auditoria(
            db=db,
            usuario_id=usuario_actual.id,
            usuario_nombre=usuario_actual.nombre,
            accion=f"Creación de {len(gastos_creados)} gastos fijos distribuidos",
            tabla="gastos_fijos",
            objeto_previo=None,
            objeto_nuevo={"cantidad": len(gastos_creados), "monto_total_usd": float(gasto.monto_usd)},
            request=request,
            forzar=True,
        )
    return gastos_creados


def obtener_gastos_fijos(
    db: Session,
    responsable: Optional[str] = None,
    id_apartamento: Optional[int] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    actualizar_tasa: bool = False,
) -> List[models.GastoFijo]:
    """
    Retorna los gastos fijos filtrados opcionalmente por responsable, apartamento o fechas.
    No actualiza tasas por defecto (mantiene valores históricos)
    """
    consulta = db.query(models.GastoFijo)
    if responsable:
        consulta = consulta.filter(models.GastoFijo.responsable == responsable)
    if id_apartamento:
        consulta = consulta.filter(models.GastoFijo.id_apartamento == id_apartamento)
    if fecha_inicio and fecha_fin:
        consulta = consulta.filter(models.GastoFijo.fecha_creacion.between(fecha_inicio, fecha_fin))

    gastos = consulta.all()

    # Solo actualizar si se solicita explícitamente
    if actualizar_tasa and gastos:
        tasa, fecha_tasa = obtener_tasa_bcv()
        for g in gastos:
            if g.monto_usd:
                g.monto_bs = round(g.monto_usd * tasa, 2)
            elif g.monto_bs:
                g.monto_usd = round(g.monto_bs / tasa, 2)
            g.fecha_tasa_bcv = fecha_tasa

    return gastos


def actualizar_gasto_fijo(
    db: Session, id_gasto: int, datos: schemas.GastoFijoCreate, usuario_actual=None, request=None
):
    gasto = db.query(models.GastoFijo).filter(models.GastoFijo.id == id_gasto).first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto fijo no encontrado")

    gasto_previo = {c.name: getattr(gasto, c.name) for c in gasto.__table__.columns}

    tasa, fecha_tasa = obtener_tasa_bcv()
    datos.monto_usd, datos.monto_bs = calcular_montos(datos.monto_usd, datos.monto_bs, tasa)

    for campo, valor in datos.dict(exclude_unset=True).items():
        setattr(gasto, campo, valor)
    gasto.fecha_tasa_bcv = fecha_tasa

    db.commit()
    db.refresh(gasto)
    if usuario_actual:
        registrar_auditoria(
            db=db,
            usuario_id=usuario_actual.id,
            usuario_nombre=usuario_actual.nombre,
            accion="Actualización de gasto fijo",
            tabla="gastos_fijos",
            objeto_previo=gasto_previo,
            objeto_nuevo={c.name: getattr(gasto, c.name) for c in gasto.__table__.columns},
            request=request,
            campos_visibles=["tipo_gasto", "monto_usd", "monto_bs", "responsable", "descripcion", "id_apartamento"],
        )
    return gasto


def eliminar_gasto_fijo(db: Session, id_gasto: int, usuario_actual=None, request=None):
    gasto = db.query(models.GastoFijo).filter(models.GastoFijo.id == id_gasto).first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto fijo no encontrado")
    gasto_previo = {c.name: getattr(gasto, c.name) for c in gasto.__table__.columns}
    db.delete(gasto)
    db.commit()
    if usuario_actual:
        registrar_auditoria(
            db=db,
            usuario_id=usuario_actual.id,
            usuario_nombre=usuario_actual.nombre,
            accion="Eliminación de gasto fijo",
            tabla="gastos_fijos",
            objeto_previo=gasto_previo,
            objeto_nuevo=None,
            request=request,
        )
    return {"mensaje": "Gasto fijo eliminado exitosamente"}


# ==================================================
# =============== GASTOS VARIABLES =================
# ==================================================


def procesar_gasto_variable(
    db: Session,
    gasto_datos: schemas.GastoVariableCreate,
    gasto_existente: Optional[models.GastoVariable] = None,
    usuario_actual=None,
    request=None,
) -> models.GastoVariable:
    """
    Función central para crear o actualizar un gasto variable
    """
    tasa_bcv, fecha_tasa = obtener_tasa_bcv()
    monto_usd, monto_bs = calcular_montos(gasto_datos.monto_usd, gasto_datos.monto_bs, tasa_bcv)

    # Obtener apartamentos desde pisos y torres
    apartamentos_ids = set(gasto_datos.id_apartamentos or [])
    apartamentos_ids.update(obtener_apartamentos_desde_pisos_torres(db, gasto_datos.id_pisos, gasto_datos.id_torres))

    if not apartamentos_ids:
        raise HTTPException(status_code=400, detail="Debe especificar apartamentos, pisos o torres para el gasto.")

    # Guardar estado previo para auditoría (si es actualización)
    gasto_previo = None
    if gasto_existente:
        gasto_previo = {c.name: getattr(gasto_existente, c.name) for c in gasto_existente.__table__.columns}

    if gasto_existente is None:
        gasto = models.GastoVariable(
            tipo_gasto=gasto_datos.tipo_gasto,
            monto_usd=monto_usd,
            monto_bs=monto_bs,
            descripcion=gasto_datos.descripcion,
            responsable=gasto_datos.responsable,
            id_reporte_financiero=gasto_datos.id_reporte_financiero,
            id_residente=gasto_datos.id_residente,
            fecha_creacion=gasto_datos.fecha_creacion or date.today(),
            fecha_tasa_bcv=fecha_tasa,
        )
        db.add(gasto)
        guardar_y_refrescar(db, gasto)

        # Creación de gasto variable
        if usuario_actual:
            registrar_auditoria(
                db=db,
                usuario_id=usuario_actual.id,
                usuario_nombre=usuario_actual.nombre,
                accion="Creación de gasto variable",
                tabla="gastos_variables",
                objeto_previo=None,
                objeto_nuevo={c.name: getattr(gasto, c.name) for c in gasto.__table__.columns},
                request=request,
                campos_visibles=["tipo_gasto", "monto_usd", "monto_bs", "responsable", "descripcion", "id_residente"],
                forzar=True,
            )
    else:
        gasto = gasto_existente
        for campo, valor in gasto_datos.dict(exclude_unset=True).items():
            if campo not in ["id_apartamentos", "id_pisos", "id_torres"]:
                setattr(gasto, campo, valor)
        gasto.monto_usd = monto_usd
        gasto.monto_bs = monto_bs
        gasto.fecha_tasa_bcv = fecha_tasa
        guardar_y_refrescar(db, gasto)

        # Actualización de gasto variable
        if usuario_actual:
            registrar_auditoria(
                db=db,
                usuario_id=usuario_actual.id,
                usuario_nombre=usuario_actual.nombre,
                accion="Actualización de gasto variable",
                tabla="gastos_variables",
                objeto_previo=gasto_previo,
                objeto_nuevo={c.name: getattr(gasto, c.name) for c in gasto.__table__.columns},
                request=request,
                campos_visibles=["tipo_gasto", "monto_usd", "monto_bs", "responsable", "descripcion", "id_residente"],
            )

    # Pasar tasa_bcv a la función
    asignar_montos_a_apartamentos(db, gasto, list(apartamentos_ids), tasa_bcv)
    return gasto


def crear_gasto_variable(
    db: Session, gasto_datos: schemas.GastoVariableCreate, usuario_actual=None, request=None
) -> models.GastoVariable:
    return procesar_gasto_variable(db, gasto_datos, usuario_actual=usuario_actual, request=request)


def obtener_gastos_variables(
    db: Session,
    responsable: Optional[str] = None,
    id_residente: Optional[int] = None,
    id_apartamento: Optional[int] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    actualizar_tasa: bool = True,
) -> List[models.GastoVariable]:
    """
    Retorna los gastos variables filtrados opcionalmente por responsable, residente, apartamento o fechas.
    También permite actualizar los montos según la tasa BCV actual.
    """
    consulta = db.query(models.GastoVariable)

    if responsable:
        consulta = consulta.filter(models.GastoVariable.responsable == responsable)
    if id_residente:
        consulta = consulta.filter(models.GastoVariable.id_residente == id_residente)
    if id_apartamento:
        # Filtra usando la tabla intermedia de apartamentos asignados al gasto
        consulta = consulta.join(
            models.gastos_variables_apartamentos,
            models.GastoVariable.id == models.gastos_variables_apartamentos.c.id_gasto_variable,
        ).filter(models.gastos_variables_apartamentos.c.id_apartamento == id_apartamento)
    if fecha_inicio and fecha_fin:
        consulta = consulta.filter(models.GastoVariable.fecha_creacion.between(fecha_inicio, fecha_fin))

    gastos = consulta.all()

    # Actualiza valores con la tasa BCV actual (si se desea)
    if actualizar_tasa and gastos:
        tasa, fecha_tasa = obtener_tasa_bcv()
        for g in gastos:
            if g.monto_usd:
                g.monto_bs = round(g.monto_usd * tasa, 2)
            elif g.monto_bs:
                g.monto_usd = round(g.monto_bs / tasa, 2)
            g.fecha_tasa_bcv = fecha_tasa
    return gastos


def actualizar_gasto_variable(
    db: Session, id_gasto: int, gasto_datos: schemas.GastoVariableCreate, usuario_actual=None, request=None
) -> models.GastoVariable:
    gasto_existente = db.query(models.GastoVariable).filter(models.GastoVariable.id == id_gasto).first()
    if not gasto_existente:
        raise HTTPException(status_code=404, detail="Gasto variable no encontrado")
    return procesar_gasto_variable(db, gasto_datos, gasto_existente, usuario_actual=usuario_actual, request=request)


def eliminar_gasto_variable(db: Session, id_gasto: int, usuario_actual=None, request=None):
    gasto = db.query(models.GastoVariable).filter(models.GastoVariable.id == id_gasto).first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto variable no encontrado")

    # Guardar estado previo para auditoría
    gasto_previo = {c.name: getattr(gasto, c.name) for c in gasto.__table__.columns}

    db.delete(gasto)
    db.commit()

    # Eliminación de gasto variable
    if usuario_actual:
        registrar_auditoria(
            db=db,
            usuario_id=usuario_actual.id,
            usuario_nombre=usuario_actual.nombre,
            accion="Eliminación de gasto variable",
            tabla="gastos_variables",
            objeto_previo=gasto_previo,
            objeto_nuevo=None,
            request=request,
        )

    return {"mensaje": "Gasto variable eliminado exitosamente"}
