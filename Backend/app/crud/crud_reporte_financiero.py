from sqlalchemy.orm import Session
from . import models, schemas


# ==============================
# ---- Reportes Financieros ----
# ==============================


def crear_reporte(db: Session, reporte: schemas.ReporteFinancieroCreate):
    nuevo = models.ReporteFinanciero(**reporte.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_reportes(db: Session):
    return db.query(models.ReporteFinanciero).all()


def obtener_reporte_por_id(db: Session, id_reporte: int):
    return db.query(models.ReporteFinanciero).filter(models.ReporteFinanciero.id == id_reporte).first()


def actualizar_reporte(db: Session, id_reporte: int, datos: schemas.ReporteFinancieroUpdate):
    rep = obtener_reporte_por_id(db, id_reporte)
    if not rep:
        return None
    for key, value in datos.dict(exclude_unset=True).items():
        setattr(rep, key, value)
    db.commit()
    db.refresh(rep)
    return rep


def eliminar_reporte(db: Session, id_reporte: int):
    rep = obtener_reporte_por_id(db, id_reporte)
    if rep:
        db.delete(rep)
        db.commit()
    return rep
