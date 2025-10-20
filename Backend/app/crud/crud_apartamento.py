from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from .. import models, schemas
from ..utils.db_helpers import guardar_y_refrescar

# ======================
# ---- Apartamentos ----
# ======================


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


def eliminar_apartamento(db: Session, id_apartamento: int):
    apt = obtener_apartamento_por_id(db, id_apartamento)
    db.delete(apt)
    db.commit()
    return {"mensaje": f"Apartamento con ID {id_apartamento} eliminado correctamente."}
