from sqlalchemy.orm import Session
from .. import models, schemas
from ..utils.db_helpers import guardar_y_refrescar
from fastapi import HTTPException, status


# ======================
# ---- Apartamentos ----
# ======================


def crear_apartamento(db: Session, apt: schemas.ApartamentoCreate):
    nuevo_apt = models.Apartamento(**apt.dict())
    db.add(nuevo_apt)
    return guardar_y_refrescar(db, nuevo_apt)


def obtener_apartamentos(db: Session):
    return db.query(models.Apartamento).order_by(models.Apartamento.id.asc()).all()


def obtener_apartamento_por_id(db: Session, id_apartamento: int):
    apt = db.query(models.Apartamento).filter(models.Apartamento.id == id_apartamento).first()
    if not apt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"No se encontró el apartamento con ID {id_apartamento}"
        )
    return apt


def actualizar_apartamento(db: Session, id_apartamento: int, datos: schemas.ApartamentoUpdate):
    apt = obtener_apartamento_por_id(db, id_apartamento)
    for key, value in datos.dict(exclude_unset=True).items():
        setattr(apt, key, value)
    return guardar_y_refrescar(db, apt)


def eliminar_apartamento(db: Session, id_apartamento: int):
    apt = obtener_apartamento_por_id(db, id_apartamento)
    db.delete(apt)
    db.commit()
    return {"mensaje": f"Apartamento con ID {id_apartamento} eliminado correctamente."}
