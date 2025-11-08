from sqlalchemy.orm import Session
from . import models, schemas
from fastapi import HTTPException
from datetime import datetime
from ..utils.auditoria_decorator import auditar_completo


# ========================
# ---- Notificaciones ----
# ========================


# @auditar_completo("notificaciones")
def crear_notificacion(db: Session, noti: schemas.NotificacionCreate):
    nuevo = models.Notificacion(**noti.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


# @auditar_completo("notificaciones")
def obtener_notificaciones(db: Session, id_usuario: int = None, tipo: str = None, leido: bool = None):
    query = db.query(models.Notificacion)

    if id_usuario is not None:
        query = query.filter(models.Notificacion.id_usuario == id_usuario)
    if tipo is not None:
        query = query.filter(models.Notificacion.tipo == tipo)
    if leido is not None:
        query = query.filter(models.Notificacion.leido == leido)

    return query.order_by(models.Notificacion.fecha_envio.desc()).all()


# @auditar_completo("notificaciones")
def obtener_notificacion_por_id(db: Session, id_notificacion: int):
    return db.query(models.Notificacion).filter(models.Notificacion.id == id_notificacion).first()


# @auditar_completo("notificaciones")
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


# @auditar_completo("notificaciones")
def eliminar_notificacion(db: Session, id_notificacion: int):
    noti = obtener_notificacion_por_id(db, id_notificacion)
    if not noti:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")

    db.delete(noti)
    db.commit()
    return {"detalle": "Notificación eliminada correctamente"}
