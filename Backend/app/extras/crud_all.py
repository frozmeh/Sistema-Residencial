from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from .. import models, schemas
from ..utils.db_helpers import guardar_y_refrescar
from ..utils.auditoria_decorator import auditar_completo


# ======================
# ---- Apartamentos ----
# ======================


@auditar_completo("apartamentos")
def crear_apartamento(db: Session, apt: schemas.ApartamentoCreate):
    existente = (
        db.query(models.Apartamento)
        .filter(models.Apartamento.numero == apt.numero, models.Apartamento.torre == apt.torre)
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un apartamento con número {apt.numero} en la torre {apt.torre}.",
        )
    if apt.id_residente:
        # Verificar que el residente exista
        residente = db.query(models.Residente).filter(models.Residente.id == apt.id_residente).first()
        if not residente:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El residente asignado no existe.")

        # Verificar que el residente no esté ya asociado a otro apartamento
        residente_ocupado = (
            db.query(models.Apartamento).filter(models.Apartamento.id_residente == apt.id_residente).first()
        )
        if residente_ocupado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="El residente ya está asignado a otro apartamento."
            )

    nuevo_apt = models.Apartamento(**apt.dict())
    db.add(nuevo_apt)
    return guardar_y_refrescar(db, nuevo_apt)


@auditar_completo("apartamentos")
def obtener_apartamentos(db: Session):
    return db.query(models.Apartamento).order_by(models.Apartamento.id.asc()).all()


@auditar_completo("apartamentos")
def obtener_apartamento_por_id(db: Session, id_apartamento: int):
    apt = db.query(models.Apartamento).filter(models.Apartamento.id == id_apartamento).first()
    if not apt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"No se encontró el apartamento con ID {id_apartamento}"
        )
    return apt


@auditar_completo("apartamentos")
def actualizar_apartamento(db: Session, id_apartamento: int, datos: schemas.ApartamentoUpdate):
    apt = obtener_apartamento_por_id(db, id_apartamento)

    if datos.id_residente:
        residente = db.query(models.Residente).filter(models.Residente.id == datos.id_residente).first()
        if not residente:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El residente asignado no existe.")

        # Evitar asignar un residente que ya tiene otro apartamento
        otro_apt = (
            db.query(models.Apartamento)
            .filter(models.Apartamento.id_residente == datos.id_residente, models.Apartamento.id != id_apartamento)
            .first()
        )
        if otro_apt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="El residente ya está asignado a otro apartamento."
            )

    for key, value in datos.dict(exclude_unset=True).items():
        setattr(apt, key, value)

    return guardar_y_refrescar(db, apt)


@auditar_completo("apartamentos")
def eliminar_apartamento(db: Session, id_apartamento: int):
    apt = obtener_apartamento_por_id(db, id_apartamento)
    db.delete(apt)
    db.commit()
    return {"mensaje": f"Apartamento con ID {id_apartamento} eliminado correctamente."}


from sqlalchemy.orm import Session
from . import models, schemas
from ..utils.auditoria_decorator import auditar_completo
from datetime import date


# ===================
# ---- Auditoria ----
# ===================


def crear_auditoria(db: Session, audit: schemas.AuditoriaCreate):
    nuevo = models.Auditoria(**audit.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_auditorias(
    db: Session, id_usuario: int = None, tabla: str = None, fecha_inicio: date = None, fecha_fin: date = None
):
    query = db.query(models.Auditoria)
    if id_usuario:
        query = query.filter(models.Auditoria.id_usuario == id_usuario)
    if tabla:
        query = query.filter(models.Auditoria.tabla_afectada == tabla)
    if fecha_inicio:
        query = query.filter(models.Auditoria.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.filter(models.Auditoria.fecha <= fecha_fin)
    return query.all()


from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Optional, Type, Any
from . import models, schemas
from ..utils.auditoria_decorator import auditar_completo

# ===============================
# ---- Funciones genéricas -----
# ===============================


def crear_entidad(db: Session, modelo: Type[Any], datos: Optional[dict] = None):
    nuevo = modelo(**datos.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_entidades(db: Session, modelo: Type[Any], filtros: Optional[str] = None):
    query = db.query(modelo)
    if filtros:
        for campo, valor in filtros.items():
            query = query.filter(getattr(modelo, campo) == valor)
    return query.all()


def actualizar_entidad(db: Session, modelo: Type[Any], id_entidad: int, datos_actualizados):
    entidad = db.query(modelo).filter(modelo.id == id_entidad).first()
    if not entidad:
        raise HTTPException(status_code=404, detail=f"{modelo.__tablename__} no encontrado")
    try:
        for key, value in datos_actualizados.dict(exclude_unset=True).items():
            setattr(entidad, key, value)
        db.commit()
        db.refresh(entidad)
        return entidad
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al actualizar: {str(e)}")


def eliminar_entidad(db: Session, modelo: Type[Any], id_entidad: int):
    entidad = db.query(modelo).filter(modelo.id == id_entidad).first()
    if not entidad:
        raise HTTPException(status_code=404, detail=f"{modelo.__tablename__} no encontrado")
    try:
        db.delete(entidad)
        db.commit()
        return {"detalle": f"{modelo.__tablename__} con id {id_entidad} eliminado correctamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al eliminar: {str(e)}")


# =======================
# ---- Gastos Fijos ----
# ======================


@auditar_completo("gastos_fijos")
def crear_gasto_fijo(db: Session, gasto: schemas.GastoFijoCreate):
    return crear_entidad(db, models.GastoFijo, gasto)


@auditar_completo("gastos_fijos")
def obtener_gastos_fijos(db: Session, responsable: Optional[str] = None):
    filtros = {"responsable": responsable} if responsable else None
    return obtener_entidades(db, models.GastoFijo, filtros)


@auditar_completo("gastos_fijos")
def actualizar_gasto_fijo(db: Session, id_gasto: int, datos_actualizados: schemas.GastoFijoCreate):
    return actualizar_entidad(db, models.GastoFijo, id_gasto, datos_actualizados)


@auditar_completo("gastos_fijos")
def eliminar_gasto_fijo(db: Session, id_gasto: int):
    return eliminar_entidad(db, models.GastoFijo, id_gasto)


# ==========================
# ---- Gastos Variables ----
# ==========================


@auditar_completo("gastos_variables")
def crear_gasto_variable(db: Session, gasto: schemas.GastoVariableCreate):
    return crear_entidad(db, models.GastoVariable, gasto)


@auditar_completo("gastos_variables")
def obtener_gastos_variables(db: Session, responsable: Optional[str] = None):
    filtros = {"responsable": responsable} if responsable else None
    return obtener_entidades(db, models.GastoVariable, filtros)


@auditar_completo("gastos_variables")
def actualizar_gasto_variable(db: Session, id_gasto: int, datos_actualizados: schemas.GastoVariableCreate):
    return actualizar_entidad(db, models.GastoVariable, id_gasto, datos_actualizados)


@auditar_completo("gastos_variables")
def eliminar_gasto_variable(db: Session, id_gasto: int):
    return eliminar_entidad(db, models.GastoVariable, id_gasto)


from sqlalchemy.orm import Session
from sqlalchemy import and_
from . import models, schemas
from fastapi import HTTPException
from typing import Optional, List
from datetime import date
from ..utils.auditoria_decorator import auditar_completo


# =====================
# ---- Incidencias ----
# =====================


@auditar_completo("incidencias")
def crear_incidencia(db: Session, incidencia: schemas.IncidenciaCreate):
    nuevo = models.Incidencia(**incidencia.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@auditar_completo("incidencias")
def obtener_incidencias(
    db: Session,
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
) -> List[models.Incidencia]:
    query = db.query(models.Incidencia)

    if estado:
        query = query.filter(models.Incidencia.estado == estado)
    if prioridad:
        query = query.filter(models.Incidencia.prioridad == prioridad)
    if fecha_inicio and fecha_fin:
        query = query.filter(
            and_(
                models.Incidencia.fecha_reporte >= fecha_inicio,
                models.Incidencia.fecha_reporte <= fecha_fin,
            )
        )

    return query.all()


@auditar_completo("incidencias")
def obtener_incidencia_por_id(db: Session, id_incidencia: int):
    incidencia = db.query(models.Incidencia).filter(models.Incidencia.id == id_incidencia).first()
    if not incidencia:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    return incidencia


@auditar_completo("incidencias")
def actualizar_incidencia(db: Session, id_incidencia: int, datos: schemas.IncidenciaUpdate):
    inc = obtener_incidencia_por_id(db, id_incidencia)
    for key, value in datos.dict(exclude_unset=True).items():
        setattr(inc, key, value)
    db.commit()
    db.refresh(inc)
    return inc


@auditar_completo("incidencias")
def eliminar_incidencia(db: Session, id_incidencia: int):
    inc = obtener_incidencia_por_id(db, id_incidencia)
    if inc.estado != "Cerrada":
        raise HTTPException(status_code=400, detail="Solo se pueden eliminar incidencias con estado 'Cerrada'")
    db.delete(inc)
    db.commit()
    return inc


from sqlalchemy.orm import Session
from . import models, schemas
from fastapi import HTTPException
from datetime import datetime
from ..utils.auditoria_decorator import auditar_completo


# ========================
# ---- Notificaciones ----
# ========================


@auditar_completo("notificaciones")
def crear_notificacion(db: Session, noti: schemas.NotificacionCreate):
    nuevo = models.Notificacion(**noti.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@auditar_completo("notificaciones")
def obtener_notificaciones(db: Session, id_usuario: int = None, tipo: str = None, leido: bool = None):
    query = db.query(models.Notificacion)

    if id_usuario is not None:
        query = query.filter(models.Notificacion.id_usuario == id_usuario)
    if tipo is not None:
        query = query.filter(models.Notificacion.tipo == tipo)
    if leido is not None:
        query = query.filter(models.Notificacion.leido == leido)

    return query.order_by(models.Notificacion.fecha_envio.desc()).all()


@auditar_completo("notificaciones")
def obtener_notificacion_por_id(db: Session, id_notificacion: int):
    return db.query(models.Notificacion).filter(models.Notificacion.id == id_notificacion).first()


@auditar_completo("notificaciones")
def actualizar_notificacion(db: Session, id_notificacion: int, datos: schemas.NotificacionUpdate):
    noti = obtener_notificacion_por_id(db, id_notificacion)
    if not noti:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")

    for key, value in datos.dict(exclude_unset=True).items():
        setattr(noti, key, value)

    if datos.leido:
        noti.fecha_leido = datetime.utcnow()

    db.commit()
    db.refresh(noti)
    return noti


@auditar_completo("notificaciones")
def eliminar_notificacion(db: Session, id_notificacion: int):
    noti = obtener_notificacion_por_id(db, id_notificacion)
    if not noti:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")

    db.delete(noti)
    db.commit()
    return {"detalle": "Notificación eliminada correctamente"}


from sqlalchemy.orm import Session
from . import models, schemas
from fastapi import HTTPException, status
from . import models, schemas
from ..utils.db_helpers import guardar_y_refrescar
from ..utils.auditoria_decorator import auditar_completo


# ===============
# ---- Pagos ----
# ===============


@auditar_completo("pagos")
def crear_pago(db: Session, pago: schemas.PagoCreate):
    # Validar residente existente y activo
    residente = db.query(models.Residente).filter(models.Residente.id == pago.id_residente).first()
    if not residente or residente.estado != "Activo":
        raise HTTPException(status_code=400, detail="Residente no existe o no está activo")

    # Validar tipo de cambio si es VES
    if pago.moneda == "VES" and not pago.tipo_cambio_bcv:
        raise HTTPException(status_code=400, detail="Debe especificar tipo_cambio_bcv para pagos en VES")

    nuevo_pago = models.Pago(**pago.dict())
    db.add(nuevo_pago)
    return guardar_y_refrescar(db, nuevo_pago)


@auditar_completo("pagos")
def obtener_pagos(db: Session):
    return db.query(models.Pago).all()


@auditar_completo("pagos")
def obtener_pago_por_id(db: Session, id_pago: int):
    pago = db.query(models.Pago).filter(models.Pago.id == id_pago).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return pago


@auditar_completo("pagos")
def actualizar_pago(db: Session, id_pago: int, datos_actualizados: schemas.PagoUpdate):
    pago = obtener_pago_por_id(db, id_pago)

    # Validaciones cruzadas
    if datos_actualizados.id_residente:
        residente = db.query(models.Residente).filter(models.Residente.id == datos_actualizados.id_residente).first()
        if not residente or residente.estado != "Activo":
            raise HTTPException(status_code=400, detail="Residente no existe o no está activo")

    if datos_actualizados.moneda == "VES" and not datos_actualizados.tipo_cambio_bcv:
        raise HTTPException(status_code=400, detail="Debe especificar tipo_cambio_bcv para pagos en VES")

    for key, value in datos_actualizados.dict(exclude_unset=True).items():
        setattr(pago, key, value)

    return guardar_y_refrescar(db, pago)


@auditar_completo("pagos")
def eliminar_pago(db: Session, id_pago: int):
    pago = obtener_pago_por_id(db, id_pago)
    db.delete(pago)
    db.commit()
    return {"detalle": f"Pago con id {id_pago} eliminado correctamente"}


from sqlalchemy.orm import Session
from . import models, schemas
from ..utils.auditoria_decorator import auditar_completo


# ==============================
# ---- Reportes Financieros ----
# ==============================


@auditar_completo("reportes_financieros")
def crear_reporte(db: Session, reporte: schemas.ReporteFinancieroCreate):
    nuevo = models.ReporteFinanciero(**reporte.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_reportes(db: Session):
    return db.query(models.ReporteFinanciero).order_by(models.ReporteFinanciero.fecha_generacion.desc()).all()


def obtener_reporte_por_id(db: Session, id_reporte: int):
    return db.query(models.ReporteFinanciero).filter(models.ReporteFinanciero.id == id_reporte).first()


@auditar_completo("reportes_financieros")
def actualizar_reporte(db: Session, id_reporte: int, datos: schemas.ReporteFinancieroUpdate):
    rep = obtener_reporte_por_id(db, id_reporte)
    if not rep:
        return None

    for key, value in datos.dict(exclude_unset=True).items():
        setattr(rep, key, value)

    # Recalcular total_general si cambian gastos
    if "total_gastos_fijos" in datos.dict(exclude_unset=True) or "total_gastos_variables" in datos.dict(
        exclude_unset=True
    ):
        rep.total_general = (rep.total_gastos_fijos or 0) + (rep.total_gastos_variables or 0)

    db.commit()
    db.refresh(rep)
    return rep


@auditar_completo("reportes_financieros")
def eliminar_reporte(db: Session, id_reporte: int):
    rep = obtener_reporte_por_id(db, id_reporte)
    if not rep:
        return None
    db.delete(rep)
    db.commit()
    return rep


from sqlalchemy.orm import Session
from . import models, schemas
from fastapi import HTTPException
from datetime import datetime, date, time
from ..utils.db_helpers import guardar_y_refrescar
from ..utils.auditoria_decorator import auditar_completo


# ==================
# ---- Reservas ----
# ==================


@auditar_completo("reservas")
def validar_disponibilidad(
    db: Session, area: str, fecha: date, hora_inicio: time, hora_fin: time, id_excluir: int = None
):
    query = db.query(models.Reserva).filter(
        models.Reserva.area == area, models.Reserva.fecha_reserva == fecha, models.Reserva.estado == "Activa"
    )
    if id_excluir:
        query = query.filter(models.Reserva.id != id_excluir)

    for reserva in query.all():
        # Verificar si hay solapamiento
        if not (hora_fin <= reserva.hora_inicio or hora_inicio >= reserva.hora_fin):
            raise HTTPException(
                status_code=400, detail=f"El horario de {hora_inicio} a {hora_fin} ya está ocupado en {area}"
            )


@auditar_completo("reservas")
def crear_reserva(db: Session, reserva: schemas.ReservaCreate):
    # Validar que la fecha de reserva no sea pasada
    if reserva.fecha_reserva < date.today():
        raise HTTPException(status_code=400, detail="La fecha de reserva no puede ser pasada")

    # Validar que la hora de fin sea mayor que la hora de inicio
    if reserva.hora_fin <= reserva.hora_inicio:
        raise HTTPException(status_code=400, detail="La hora de fin debe ser posterior a la hora de inicio")

    validar_disponibilidad(db, reserva.area, reserva.fecha_reserva, reserva.hora_inicio, reserva.hora_fin)

    nuevo = models.Reserva(**reserva.dict())
    db.add(nuevo)
    return guardar_y_refrescar(db, nuevo)


@auditar_completo("reservas")
def obtener_reservas(db: Session):
    return db.query(models.Reserva).all()


@auditar_completo("reservas")
def obtener_reserva_por_id(db: Session, id_reserva: int):
    res = db.query(models.Reserva).filter(models.Reserva.id == id_reserva).first()
    if not res:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return res


@auditar_completo("reservas")
def actualizar_reserva(db: Session, id_reserva: int, datos: schemas.ReservaUpdate):
    res = obtener_reserva_por_id(db, id_reserva)

    # Actualizar atributos
    for key, value in datos.dict(exclude_unset=True).items():
        setattr(res, key, value)

    # Validar hora_fin > hora_inicio si se actualizaron
    if res.hora_inicio and res.hora_fin and res.hora_fin <= res.hora_inicio:
        raise HTTPException(status_code=400, detail="La hora de fin debe ser posterior a la hora de inicio")

    # Validar fecha de reserva no pasada
    if res.fecha_reserva and res.fecha_reserva < date.today():
        raise HTTPException(status_code=400, detail="La fecha de reserva no puede ser pasada")

    validar_disponibilidad(db, res.area, res.fecha_reserva, res.hora_inicio, res.hora_fin)

    return guardar_y_refrescar(db, res)


@auditar_completo("reservas")
def eliminar_reserva(db: Session, id_reserva: int):
    res = obtener_reserva_por_id(db, id_reserva)
    db.delete(res)
    db.commit()
    return res


from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..utils.db_helpers import guardar_y_refrescar
from .. import models, schemas
from ..utils.auditoria_decorator import auditar_completo


# ====================
# ---- Residentes ----
# ====================


@auditar_completo("residentes")
def crear_residente(db: Session, residente: schemas.ResidenteCreate):
    # Verificar si el usuario ya tiene un residente asignado
    existente = db.query(models.Residente).filter(models.Residente.id_usuario == residente.id_usuario).first()
    if existente:
        raise HTTPException(
            status_code=400,
            detail=f"El usuario con ID {residente.id_usuario} ya está asociado a otro residente.",
        )

    # Validar cédula única
    existente_cedula = db.query(models.Residente).filter(models.Residente.cedula == residente.cedula).first()
    if existente_cedula:
        raise HTTPException(
            status_code=400,
            detail=f"La cédula {residente.cedula} ya está registrada.",
        )

    # Validar correo único si se proporciona
    if residente.correo:
        existente_correo = db.query(models.Residente).filter(models.Residente.correo == residente.correo).first()
        if existente_correo:
            raise HTTPException(
                status_code=400,
                detail=f"El correo {residente.correo} ya está registrado.",
            )

    # Crear residente
    nuevo_residente = models.Residente(**residente.dict())
    db.add(nuevo_residente)
    try:
        return guardar_y_refrescar(db, nuevo_residente)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad: Verifica que la cédula y el usuario no estén duplicados.",
        )


@auditar_completo("residentes")
def obtener_residentes(db: Session):
    return db.query(models.Residente).order_by(models.Residente.id.asc()).all()


@auditar_completo("residentes")
def obtener_residente_por_id(db: Session, id_residente: int):
    residente = db.query(models.Residente).filter(models.Residente.id == id_residente).first()
    if not residente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró un residente con ID {id_residente}.",
        )
    return residente


@auditar_completo("residentes")
def actualizar_residente(db: Session, id_residente: int, datos_actualizados: schemas.ResidenteUpdate):
    residente = obtener_residente_por_id(db, id_residente)

    # Validaciones para cédula y correo únicos
    update_data = datos_actualizados.dict(exclude_unset=True)
    if "cedula" in update_data:
        existente_cedula = (
            db.query(models.Residente)
            .filter(models.Residente.cedula == update_data["cedula"], models.Residente.id != id_residente)
            .first()
        )
        if existente_cedula:
            raise HTTPException(status_code=400, detail=f"La cédula {update_data['cedula']} ya está registrada.")
    if "correo" in update_data:
        existente_correo = (
            db.query(models.Residente)
            .filter(models.Residente.correo == update_data["correo"], models.Residente.id != id_residente)
            .first()
        )
        if existente_correo:
            raise HTTPException(status_code=400, detail=f"El correo {update_data['correo']} ya está registrado.")

    # Actualizar campos
    for key, value in update_data.items():
        setattr(residente, key, value)

    try:
        return guardar_y_refrescar(db, residente)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al actualizar: datos duplicados o conflicto de integridad.",
        )


@auditar_completo("residentes")
def eliminar_residente(db: Session, id_residente: int):
    residente = obtener_residente_por_id(db, id_residente)
    db.delete(residente)
    db.commit()
    return {"mensaje": f"Residente con ID {id_residente} eliminado correctamente."}


@auditar_completo("residentes")
def asignar_residente_a_apartamento(db: Session, id_residente: int, id_apartamento: int):
    residente = db.query(models.Residente).filter(models.Residente.id == id_residente).first()
    apartamento = db.query(models.Apartamento).filter(models.Apartamento.id == id_apartamento).first()

    if not residente:
        raise HTTPException(status_code=404, detail=f"No se encontró el residente con ID {id_residente}.")
    if not apartamento:
        raise HTTPException(status_code=404, detail=f"No se encontró el apartamento con ID {id_apartamento}.")

    if residente.id_apartamento:
        raise HTTPException(status_code=400, detail="El residente ya tiene un apartamento asignado.")
    if apartamento.estado == "Ocupado":
        raise HTTPException(status_code=400, detail="El apartamento ya está ocupado.")

    residente.id_apartamento = apartamento.id
    apartamento.estado = "Ocupado"
    apartamento.id_residente = residente.id  # coherencia bidireccional

    db.commit()
    db.refresh(residente)
    db.refresh(apartamento)

    return {"mensaje": f"Residente {residente.nombre} asignado al apartamento {apartamento.numero}."}


@auditar_completo("residentes")
def desasignar_residente(db: Session, id_residente: int, inactivar: bool = False):
    residente = db.query(models.Residente).filter(models.Residente.id == id_residente).first()
    if not residente:
        raise HTTPException(status_code=404, detail="Residente no encontrado.")

    if residente.id_apartamento:
        apartamento = db.query(models.Apartamento).filter(models.Apartamento.id == residente.id_apartamento).first()
        if apartamento:
            apartamento.estado = "Disponible"
            apartamento.id_residente = None
        residente.id_apartamento = None

    if inactivar:
        residente.estado = "Inactivo"
        residente.residente_actual = False

    db.commit()
    db.refresh(residente)

    return {
        "mensaje": f"Residente {residente.nombre} desasignado correctamente.",
        "estado": residente.estado,
    }


@auditar_completo("residentes")
def activar_residente(db: Session, id_residente: int):
    residente = obtener_residente_por_id(db, id_residente)

    residente.estado = "Activo"
    residente.residente_actual = True

    db.commit()
    db.refresh(residente)

    return {"mensaje": f"Residente {residente.nombre} activado correctamente.", "estado": residente.estado}


from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..utils.db_helpers import guardar_y_refrescar


# ===============
# ---- Roles ----
# ===============


def inicializar_roles(db: Session):
    if db.query(models.Rol).count() == 0:
        admin_permisos = {
            "Usuario": ["crear", "leer", "actualizar", "eliminar"],
            "Residente": ["crear", "leer", "actualizar", "eliminar"],
            "Apartamento": ["crear", "leer", "actualizar", "eliminar"],
            "Pago": ["crear", "leer", "actualizar", "eliminar"],
            "GastoFijo": ["crear", "leer", "actualizar", "eliminar"],
            "GastoVariable": ["crear", "leer", "actualizar", "eliminar"],
            "Incidencia": ["leer", "actualizar", "eliminar"],
            "Reserva": ["leer", "actualizar", "eliminar"],
            "Notificacion": ["crear", "leer", "actualizar"],
            "ReporteFinanciero": ["crear", "leer", "actualizar", "eliminar"],
            "Auditoria": ["crear", "leer"],
        }

        residente_permisos = {
            "Usuario": ["leer", "actualizar"],
            "Residente": ["leer", "actualizar"],
            "Apartamento": ["leer"],
            "Pago": ["crear", "leer"],
            "GastoFijo": ["leer"],
            "GastoVariable": ["leer"],
            "Incidencia": ["crear", "leer", "actualizar"],
            "Reserva": ["crear", "leer", "actualizar", "eliminar"],
            "Notificacion": ["leer", "actualizar"],
            "ReporteFinanciero": ["leer"],
            "Auditoria": ["leer"],
        }

        db.add_all(
            [
                models.Rol(
                    nombre="Administrador",
                    permisos=admin_permisos,
                    descripcion="Acceso completo",
                ),
                models.Rol(
                    nombre="Residente",
                    permisos=residente_permisos,
                    descripcion="Acceso limitado",
                ),
            ]
        )
        db.commit()


def crear_rol(db: Session, rol: schemas.RolCreate):
    raise HTTPException(status_code=403, detail="No se pueden crear roles manualmente")
    """
    db_rol = models.Rol(**rol.dict())
    db.add(db_rol)
    guardar_y_refrescar(db, db_rol)
    return db_rol """


def obtener_roles(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Rol).offset(skip).limit(limit).all()


from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models, schemas
from ..utils.seguridad import encriptar_contrasena
from ..utils.validaciones import validar_usuario, validar_contrasena
from ..utils.db_helpers import guardar_y_refrescar, obtener_usuario_por_id
from ..utils.auditoria_decorator import auditar_completo


# ==================
# ---- Usuario ----
# ==================


@auditar_completo("usuarios")
def crear_usuario(db: Session, usuario: schemas.UsuarioCreate):
    validar_usuario(nombre=usuario.nombre, email=usuario.email, password=usuario.password)

    if db.query(models.Usuario).filter(func.lower(models.Usuario.nombre) == usuario.nombre.lower()).first():
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")

    if db.query(models.Usuario).filter(func.lower(models.Usuario.email) == usuario.email.lower()).first():
        raise HTTPException(status_code=400, detail="El correo ya está en uso")

    datos_usuario = usuario.dict()
    datos_usuario["password"] = encriptar_contrasena(usuario.password)
    db_usuario = models.Usuario(**datos_usuario)
    db.add(db_usuario)
    guardar_y_refrescar(db, db_usuario)
    return db_usuario


@auditar_completo("usuarios")
def actualizar_usuario(
    db: Session,
    id_usuario: int,
    nuevo_nombre: str = None,
    nuevo_email: str = None,
    nueva_password: str = None,
):
    usuario = obtener_usuario_por_id(db, id_usuario)
    validar_usuario(nombre=nuevo_nombre, email=nuevo_email, password=nueva_password)

    usuario.nombre = nuevo_nombre
    usuario.email = nuevo_email
    usuario.password = encriptar_contrasena(nueva_password)

    guardar_y_refrescar(db, usuario)
    return usuario


@auditar_completo("usuarios")
def cambiar_password(db: Session, id_usuario: int, nueva_password: str):
    usuario = obtener_usuario_por_id(db, id_usuario)

    validar_contrasena(nueva_password)

    usuario.password = encriptar_contrasena(nueva_password)
    guardar_y_refrescar(db, usuario)
    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "mensaje": "Contraseña actualizada",
    }


@auditar_completo("usuarios")
def actualizar_ultima_sesion(db: Session, id_usuario: int):
    usuario = obtener_usuario_por_id(db, id_usuario)
    usuario.ultima_sesion = datetime.utcnow()
    guardar_y_refrescar(db, usuario)
    return usuario


@auditar_completo("usuarios")
def cambiar_rol_usuario(db: Session, id_usuario: int, nuevo_id_rol: int):
    usuario = obtener_usuario_por_id(db, id_usuario)

    usuario.id_rol = nuevo_id_rol
    guardar_y_refrescar(db, usuario)
    return usuario


@auditar_completo("usuarios")
def desactivar_usuario(db: Session, id_usuario: int):
    usuario = obtener_usuario_por_id(db, id_usuario)

    usuario.estado = "Inactivo"
    guardar_y_refrescar(db, usuario)
    return usuario


@auditar_completo("usuarios")
def obtener_usuarios(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Usuario).offset(skip).limit(limit).all()
