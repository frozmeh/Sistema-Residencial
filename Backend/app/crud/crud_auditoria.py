from sqlalchemy.orm import Session
from . import models, schemas


# ===================
# ---- Auditoria ----
# ===================


def crear_auditoria(db: Session, audit: schemas.AuditoriaCreate):
    nuevo = models.Auditoria(**audit.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_auditorias(db: Session):
    return db.query(models.Auditoria).all()
