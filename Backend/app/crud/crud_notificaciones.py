from sqlalchemy.orm import Session
from . import models, schemas


# ========================
# ---- Notificaciones ----
# ========================


def crear_notificacion(db: Session, noti: schemas.NotificacionCreate):
    nuevo = models.Notificacion(**noti.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_notificaciones(db: Session):
    return db.query(models.Notificacion).all()


def obtener_notificacion_por_id(db: Session, id_notificacion: int):
    return db.query(models.Notificacion).filter(models.Notificacion.id == id_notificacion).first()


def actualizar_notificacion(db: Session, id_notificacion: int, datos: schemas.NotificacionUpdate):
    noti = obtener_notificacion_por_id(db, id_notificacion)
    if not noti:
        return None
    for key, value in datos.dict(exclude_unset=True).items():
        setattr(noti, key, value)
    db.commit()
    db.refresh(noti)
    return noti
