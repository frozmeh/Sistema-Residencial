from sqlalchemy.orm import Session
from sqlalchemy import and_
from . import models, schemas
from fastapi import HTTPException
from typing import Optional, List
from datetime import date
from ..utils.auditoria_decorator import auditar_completo


# =====================
# ---- Incidencias ----
# =====================


@auditar_completo("incidencias")
def crear_incidencia(db: Session, incidencia: schemas.IncidenciaCreate):
    nuevo = models.Incidencia(**incidencia.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@auditar_completo("incidencias")
def obtener_incidencias(
    db: Session,
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
) -> List[models.Incidencia]:
    query = db.query(models.Incidencia)

    if estado:
        query = query.filter(models.Incidencia.estado == estado)
    if prioridad:
        query = query.filter(models.Incidencia.prioridad == prioridad)
    if fecha_inicio and fecha_fin:
        query = query.filter(
            and_(
                models.Incidencia.fecha_reporte >= fecha_inicio,
                models.Incidencia.fecha_reporte <= fecha_fin,
            )
        )

    return query.all()


@auditar_completo("incidencias")
def obtener_incidencia_por_id(db: Session, id_incidencia: int):
    incidencia = db.query(models.Incidencia).filter(models.Incidencia.id == id_incidencia).first()
    if not incidencia:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    return incidencia


@auditar_completo("incidencias")
def actualizar_incidencia(db: Session, id_incidencia: int, datos: schemas.IncidenciaUpdate):
    inc = obtener_incidencia_por_id(db, id_incidencia)
    for key, value in datos.dict(exclude_unset=True).items():
        setattr(inc, key, value)
    db.commit()
    db.refresh(inc)
    return inc


@auditar_completo("incidencias")
def eliminar_incidencia(db: Session, id_incidencia: int):
    inc = obtener_incidencia_por_id(db, id_incidencia)
    if inc.estado != "Cerrada":
        raise HTTPException(status_code=400, detail="Solo se pueden eliminar incidencias con estado 'Cerrada'")
    db.delete(inc)
    db.commit()
    return inc
