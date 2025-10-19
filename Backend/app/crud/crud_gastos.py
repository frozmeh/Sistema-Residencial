from sqlalchemy.orm import Session
from . import models, schemas


# ======================
# ---- Gastos Fijos ----
# ======================


def crear_gasto_fijo(db: Session, gasto: schemas.GastoFijoCreate):
    nuevo = models.GastoFijo(**gasto.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_gastos_fijos(db: Session):
    return db.query(models.GastoFijo).all()


def actualizar_gasto_fijo(db: Session, id_gasto: int, datos_actualizados: schemas.GastoFijoCreate):
    gasto = db.query(models.GastoFijo).filter(models.GastoFijo.id == id_gasto).first()
    if gasto:
        for key, value in datos_actualizados.dict(exclude_unset=True).items():
            setattr(gasto, key, value)
        db.commit()
        db.refresh(gasto)
    return gasto


def eliminar_gasto_fijo(db: Session, id_gasto: int):
    gasto = db.query(models.GastoFijo).filter(models.GastoFijo.id == id_gasto).first()
    if gasto:
        db.delete(gasto)
        db.commit()
    return gasto


# ==========================
# ---- Gastos Variables ----
# ==========================


def crear_gasto_variable(db: Session, gasto: schemas.GastoVariableCreate):
    nuevo = models.GastoVariable(**gasto.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_gastos_variables(db: Session):
    return db.query(models.GastoVariable).all()


def actualizar_gasto_variable(db: Session, id_gasto: int, datos_actualizados: schemas.GastoVariableCreate):
    gasto = db.query(models.GastoVariable).filter(models.GastoVariable.id == id_gasto).first()
    if gasto:
        for key, value in datos_actualizados.dict(exclude_unset=True).items():
            setattr(gasto, key, value)
        db.commit()
        db.refresh(gasto)
    return gasto


def eliminar_gasto_variable(db: Session, id_gasto: int):
    gasto = db.query(models.GastoVariable).filter(models.GastoVariable.id == id_gasto).first()
    if gasto:
        db.delete(gasto)
        db.commit()
    return gasto
