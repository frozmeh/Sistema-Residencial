from sqlalchemy.orm import Session
from . import models, schemas


# ===============
# ---- Pagos ----
# ===============


def crear_pago(db: Session, pago: schemas.PagoCreate):
    nuevo_pago = models.Pago(**pago.dict())
    db.add(nuevo_pago)
    db.commit()
    db.refresh(nuevo_pago)
    return nuevo_pago


def obtener_pagos(db: Session):
    return db.query(models.Pago).all()


def obtener_pago_por_id(db: Session, id_pago: int):
    return db.query(models.Pago).filter(models.Pago.id == id_pago).first()


def actualizar_pago(db: Session, id_pago: int, datos_actualizados: schemas.PagoCreate):
    pago = obtener_pago_por_id(db, id_pago)
    if pago:
        for key, value in datos_actualizados.dict(exclude_unset=True).items():
            setattr(pago, key, value)
        db.commit()
        db.refresh(pago)
    return pago


def eliminar_pago(db: Session, id_pago: int):
    pago = obtener_pago_por_id(db, id_pago)
    if pago:
        db.delete(pago)
        db.commit()
    return pago
