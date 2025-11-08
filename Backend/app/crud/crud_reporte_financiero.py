from sqlalchemy.orm import Session
from . import models, schemas
from ..utils.auditoria_decorator import auditar_completo


# ==============================
# ---- Reportes Financieros ----
# ==============================


# @auditar_completo("reportes_financieros")
def crear_reporte(db: Session, reporte: schemas.ReporteFinancieroCreate):
    nuevo = models.ReporteFinanciero(**reporte.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_reportes(db: Session):
    return db.query(models.ReporteFinanciero).order_by(models.ReporteFinanciero.fecha_generacion.desc()).all()


def obtener_reporte_por_id(db: Session, id_reporte: int):
    return db.query(models.ReporteFinanciero).filter(models.ReporteFinanciero.id == id_reporte).first()


# @auditar_completo("reportes_financieros")
def actualizar_reporte(db: Session, id_reporte: int, datos: schemas.ReporteFinancieroUpdate):
    rep = obtener_reporte_por_id(db, id_reporte)
    if not rep:
        return None

    for key, value in datos.dict(exclude_unset=True).items():
        setattr(rep, key, value)

    # Recalcular total_general si cambian gastos
    if "total_gastos_fijos" in datos.dict(exclude_unset=True) or "total_gastos_variables" in datos.dict(
        exclude_unset=True
    ):
        rep.total_general = (rep.total_gastos_fijos or 0) + (rep.total_gastos_variables or 0)

    db.commit()
    db.refresh(rep)
    return rep


# @auditar_completo("reportes_financieros")
def eliminar_reporte(db: Session, id_reporte: int):
    rep = obtener_reporte_por_id(db, id_reporte)
    if not rep:
        return None
    db.delete(rep)
    db.commit()
    return rep
