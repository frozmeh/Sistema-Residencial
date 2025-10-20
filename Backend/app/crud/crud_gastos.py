from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Optional, Type, Any
from . import models, schemas

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


def crear_gasto_fijo(db: Session, gasto: schemas.GastoFijoCreate):
    return crear_entidad(db, models.GastoFijo, gasto)


def obtener_gastos_fijos(db: Session, responsable: Optional[str] = None):
    filtros = {"responsable": responsable} if responsable else None
    return obtener_entidades(db, models.GastoFijo, filtros)


def actualizar_gasto_fijo(db: Session, id_gasto: int, datos_actualizados: schemas.GastoFijoCreate):
    return actualizar_entidad(db, models.GastoFijo, id_gasto, datos_actualizados)


def eliminar_gasto_fijo(db: Session, id_gasto: int):
    return eliminar_entidad(db, models.GastoFijo, id_gasto)


# ==========================
# ---- Gastos Variables ----
# ==========================


def crear_gasto_variable(db: Session, gasto: schemas.GastoVariableCreate):
    return crear_entidad(db, models.GastoVariable, gasto)


def obtener_gastos_variables(db: Session, responsable: Optional[str] = None):
    filtros = {"responsable": responsable} if responsable else None
    return obtener_entidades(db, models.GastoVariable, filtros)


def actualizar_gasto_variable(db: Session, id_gasto: int, datos_actualizados: schemas.GastoVariableCreate):
    return actualizar_entidad(db, models.GastoVariable, id_gasto, datos_actualizados)


def eliminar_gasto_variable(db: Session, id_gasto: int):
    return eliminar_entidad(db, models.GastoVariable, id_gasto)
