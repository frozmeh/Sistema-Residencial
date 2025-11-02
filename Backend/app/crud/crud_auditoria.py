from sqlalchemy.orm import Session
from . import models, schemas
from ..utils.auditoria_decorator import auditar_completo
from datetime import date


# ===================
# ---- Auditoria ----
# ===================


def crear_auditoria(db: Session, audit: schemas.AuditoriaCreate):
    nuevo = models.Auditoria(**audit.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_auditorias(
    db: Session, id_usuario: int = None, tabla: str = None, fecha_inicio: date = None, fecha_fin: date = None
):
    query = db.query(models.Auditoria)
    if id_usuario:
        query = query.filter(models.Auditoria.id_usuario == id_usuario)
    if tabla:
        query = query.filter(models.Auditoria.tabla_afectada == tabla)
    if fecha_inicio:
        query = query.filter(models.Auditoria.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.filter(models.Auditoria.fecha <= fecha_fin)
    return query.all()
