from sqlalchemy.orm import Session
from . import models, schemas


# ====================
# ---- Residentes ----
# ====================


def crear_reserva(db: Session, reserva: schemas.ReservaCreate):
    nuevo = models.Reserva(**reserva.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_reservas(db: Session):
    return db.query(models.Reserva).all()


def obtener_reserva_por_id(db: Session, id_reserva: int):
    return db.query(models.Reserva).filter(models.Reserva.id == id_reserva).first()


def actualizar_reserva(db: Session, id_reserva: int, datos: schemas.ReservaUpdate):
    res = obtener_reserva_por_id(db, id_reserva)
    if not res:
        return None
    for key, value in datos.dict(exclude_unset=True).items():
        setattr(res, key, value)
    db.commit()
    db.refresh(res)
    return res


def eliminar_reserva(db: Session, id_reserva: int):
    res = obtener_reserva_por_id(db, id_reserva)
    if res:
        db.delete(res)
        db.commit()
    return res
