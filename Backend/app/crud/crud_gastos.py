from sqlalchemy.orm import Session
from fastapi import HTTPException
from decimal import Decimal
from datetime import date
from typing import List, Optional
from .. import models, schemas
from ..utils.tasa_bcv import obtener_tasa_bcv


# ================================
# ---- FUNCIONES AUXILIARES ------
# ================================


def obtener_apartamentos_desde_pisos_torres(
    db: Session, id_pisos: Optional[List[int]] = None, id_torres: Optional[List[int]] = None
) -> List[int]:
    """
    Devuelve lista de IDs de apartamentos a partir de pisos o torres.
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


def calcular_montos(monto_usd: Optional[Decimal], monto_bs: Optional[Decimal], tasa_bcv: Decimal):
    """
    Devuelve monto_usd y monto_bs completos a partir de uno de los dos.
    """
    if monto_usd is None and monto_bs is None:
        raise HTTPException(status_code=400, detail="Debe proporcionar monto en USD o Bs")
    if monto_usd is None:
        monto_usd = Decimal(str(monto_bs)) / tasa_bcv
    if monto_bs is None:
        monto_bs = Decimal(str(monto_usd)) * tasa_bcv
    return round(monto_usd, 2), round(monto_bs, 2)


def asignar_montos_a_apartamentos(
    db: Session, gasto: models.GastoVariable, apartamentos_ids: List[int], tasa_bcv: Decimal
):
    """
    Inserta o actualiza la tabla intermedia de apartamentos asignados para un gasto variable,
    aplicando porcentaje de aporte de cada tipo de apartamento.
    """
    if not apartamentos_ids:
        return

    # Eliminar asignaciones anteriores
    db.execute(
        models.gastos_variables_apartamentos.delete().where(
            models.gastos_variables_apartamentos.c.id_gasto_variable == gasto.id
        )
    )

    # Crear nuevas asignaciones
    for apt_id in apartamentos_ids:
        apt = db.query(models.Apartamento).filter(models.Apartamento.id == apt_id).first()
        if not apt:
            continue
        tipo = db.query(models.TipoApartamento).filter(models.TipoApartamento.id == apt.id_tipo_apartamento).first()
        monto_usd = gasto.monto_usd
        if tipo:
            monto_usd = monto_usd * Decimal(str(tipo.porcentaje_aporte)) / Decimal("100")
        monto_bs = round(monto_usd * tasa_bcv, 2)
        db.execute(
            models.gastos_variables_apartamentos.insert().values(
                id_gasto_variable=gasto.id, id_apartamento=apt_id, monto_asignado=monto_bs
            )
        )
    db.commit()


# ================================
# ---- GASTOS FIJOS -------------
# ================================


def crear_gasto_fijo(db: Session, gasto: schemas.GastoFijoCreate):
    tasa_bcv, fecha_tasa = obtener_tasa_bcv()

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
        return nuevo_gasto

    # Caso 2: Gasto general — se reparte según porcentaje aporte
    apartamentos = db.query(models.Apartamento).all()
    if not apartamentos:
        raise HTTPException(status_code=404, detail="No hay apartamentos registrados")

    gastos_creados = []
    for apt in apartamentos:
        tipo = db.query(models.TipoApartamento).filter(models.TipoApartamento.id == apt.id_tipo_apartamento).first()
        if not tipo:
            raise HTTPException(status_code=404, detail=f"Tipo de apartamento no encontrado para apt {apt.id}")

        monto_usd = Decimal(str(gasto.monto_usd)) * Decimal(str(tipo.porcentaje_aporte)) / Decimal("100")
        monto_bs = monto_usd * tasa_bcv

        monto_usd = round(monto_usd, 2)
        monto_bs = round(monto_bs, 2)

        nuevo_gasto = models.GastoFijo(
            tipo_gasto=gasto.tipo_gasto,
            monto_usd=monto_usd,
            monto_bs=monto_bs,
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
    return gastos_creados


def obtener_gastos_fijos(
    db: Session,
    responsable: Optional[str] = None,
    id_apartamento: Optional[int] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    actualizar_tasa: bool = True,
) -> List[models.GastoFijo]:
    consulta = db.query(models.GastoFijo)
    if responsable:
        consulta = consulta.filter(models.GastoFijo.responsable == responsable)
    if id_apartamento:
        consulta = consulta.filter(models.GastoFijo.id_apartamento == id_apartamento)
    if fecha_inicio and fecha_fin:
        consulta = consulta.filter(models.GastoFijo.fecha_creacion.between(fecha_inicio, fecha_fin))

    gastos = consulta.all()
    if actualizar_tasa and gastos:
        tasa, fecha_tasa = obtener_tasa_bcv()
        for g in gastos:
            g.monto_bs = round(g.monto_usd * tasa, 2) if g.monto_usd else g.monto_bs
            g.monto_usd = round(g.monto_bs / tasa, 2) if g.monto_bs else g.monto_usd
            g.fecha_tasa_bcv = fecha_tasa

    return gastos


def actualizar_gasto_fijo(db: Session, id_gasto: int, datos: schemas.GastoFijoCreate):
    gasto = db.query(models.GastoFijo).filter(models.GastoFijo.id == id_gasto).first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto fijo no encontrado")

    tasa, fecha_tasa = obtener_tasa_bcv()
    datos.monto_usd, datos.monto_bs = calcular_montos(datos.monto_usd, datos.monto_bs, tasa)

    for campo, valor in datos.dict(exclude_unset=True).items():
        setattr(gasto, campo, valor)
    gasto.fecha_tasa_bcv = fecha_tasa

    db.commit()
    db.refresh(gasto)
    return gasto


def eliminar_gasto_fijo(db: Session, id_gasto: int):
    gasto = db.query(models.GastoFijo).filter(models.GastoFijo.id == id_gasto).first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto fijo no encontrado")
    db.delete(gasto)
    db.commit()
    return {"mensaje": "Gasto fijo eliminado exitosamente"}


# ================================
# ---- GASTOS VARIABLES ----------
# ================================


def procesar_gasto_variable(
    db: Session, gasto_datos: schemas.GastoVariableCreate, gasto_existente: Optional[models.GastoVariable] = None
) -> models.GastoVariable:
    """
    Función unificada para crear o actualizar un gasto variable.
    - Si gasto_existente es None, crea uno nuevo.
    - Si existe, actualiza el gasto existente.
    """
    tasa_bcv, fecha_tasa = obtener_tasa_bcv()
    monto_usd, monto_bs = calcular_montos(gasto_datos.monto_usd, gasto_datos.monto_bs, tasa_bcv)

    # Construir lista final de apartamentos
    apartamentos_ids = set(gasto_datos.id_apartamentos or [])
    apartamentos_ids.update(obtener_apartamentos_desde_pisos_torres(db, gasto_datos.id_pisos, gasto_datos.id_torres))

    if not apartamentos_ids:
        raise HTTPException(
            status_code=400, detail="No se especificaron apartamentos, pisos o torres para asignar el gasto."
        )

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
        db.commit()
        db.refresh(gasto)
    else:
        gasto = gasto_existente
        for campo, valor in gasto_datos.dict(exclude_unset=True).items():
            if campo not in ["id_apartamentos", "id_pisos", "id_torres"]:
                setattr(gasto, campo, valor)
        gasto.monto_usd = monto_usd
        gasto.monto_bs = monto_bs
        gasto.fecha_tasa_bcv = fecha_tasa
        db.commit()
        db.refresh(gasto)

    # Asignar montos a apartamentos
    asignar_montos_a_apartamentos(db, gasto, list(apartamentos_ids), tasa_bcv)

    return gasto


def crear_gasto_variable(db: Session, gasto_datos: schemas.GastoVariableCreate) -> models.GastoVariable:
    return procesar_gasto_variable(db, gasto_datos)


def actualizar_gasto_variable(
    db: Session, id_gasto: int, gasto_datos: schemas.GastoVariableCreate
) -> models.GastoVariable:
    gasto_existente = db.query(models.GastoVariable).filter(models.GastoVariable.id == id_gasto).first()
    if not gasto_existente:
        raise HTTPException(status_code=404, detail="Gasto variable no encontrado")
    return procesar_gasto_variable(db, gasto_datos, gasto_existente)


def eliminar_gasto_variable(db: Session, id_gasto: int):
    gasto = db.query(models.GastoVariable).filter(models.GastoVariable.id == id_gasto).first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto variable no encontrado")
    db.delete(gasto)
    db.commit()
    return {"mensaje": "Gasto variable eliminado exitosamente"}
