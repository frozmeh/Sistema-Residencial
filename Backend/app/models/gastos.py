from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    func,
    DECIMAL,
)
from ..database import Base
from sqlalchemy.orm import relationship


# ======================
# ---- Gastos Fijos ----
# ======================


class GastoFijo(Base):
    __tablename__ = "gastos_fijos"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String, nullable=False)  # Mantenimiento, limpieza, seguridad
    monto = Column(DECIMAL(10, 2), nullable=False)
    fecha_registro = Column(Date, default=func.current_date())
    descripcion = Column(String, nullable=True)
    responsable = Column(String, nullable=False)
    id_reporte_financiero = Column(Integer, ForeignKey("reportes_financieros.id"))

    reporte_financiero = relationship("ReporteFinanciero", back_populates="gastos_fijos")  # en GastoFijo


# ==========================
# ---- Gastos Variables ----
# ==========================


class GastoVariable(Base):
    __tablename__ = "gastos_variables"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String, nullable=False)
    monto = Column(DECIMAL(10, 2), nullable=False)
    fecha_registro = Column(Date, default=func.current_date())
    descripcion = Column(String, nullable=True)
    responsable = Column(String, nullable=False)
    id_reporte_financiero = Column(Integer, ForeignKey("reportes_financieros.id"))

    reporte_financiero = relationship("ReporteFinanciero", back_populates="gastos_variables")  # en GastoVariable
