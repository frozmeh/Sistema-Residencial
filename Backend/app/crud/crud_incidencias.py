from sqlalchemy.orm import Session
from . import models, schemas


# =====================
# ---- Incidencias ----
# =====================


def crear_incidencia(db: Session, incidencia: schemas.IncidenciaCreate):
    nuevo = models.Incidencia(**incidencia.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_incidencias(db: Session):
    return db.query(models.Incidencia).all()


def obtener_incidencia_por_id(db: Session, id_incidencia: int):
    return db.query(models.Incidencia).filter(models.Incidencia.id == id_incidencia).first()


def actualizar_incidencia(db: Session, id_incidencia: int, datos: schemas.IncidenciaUpdate):
    inc = obtener_incidencia_por_id(db, id_incidencia)
    if not inc:
        return None
    for key, value in datos.dict(exclude_unset=True).items():
        setattr(inc, key, value)
    db.commit()
    db.refresh(inc)
    return inc


def eliminar_incidencia(db: Session, id_incidencia: int):
    inc = obtener_incidencia_por_id(db, id_incidencia)
    if inc:
        db.delete(inc)
        db.commit()
    return inc
