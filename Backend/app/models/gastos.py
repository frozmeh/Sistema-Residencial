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
    id_reporte_financiero = Column(Integer, ForeignKey("reportes_financieros.id"))
    id_apartamento = Column(Integer, ForeignKey("apartamentos.id"))

    tipo_gasto = Column(String, nullable=False)  # Mantenimiento, limpieza, seguridad
    monto = Column(DECIMAL(10, 2), nullable=False)
    fecha_creacion = Column(Date, default=func.current_date())
    descripcion = Column(String, nullable=True)
    responsable = Column(String, nullable=False)

    reporte_financiero = relationship("ReporteFinanciero", back_populates="gastos_fijos")  # en GastoFijo
    apartamento = relationship("Apartamento", back_populates="gastos_fijos")


# ==========================
# ---- Gastos Variables ----
# ==========================


class GastoVariable(Base):
    __tablename__ = "gastos_variables"

    id = Column(Integer, primary_key=True, index=True)
    id_reporte_financiero = Column(Integer, ForeignKey("reportes_financieros.id"))
    id_apartamento = Column(Integer, ForeignKey("apartamentos.id"))
    id_residente = Column(Integer, ForeignKey("residentes.id"), nullable=True)

    tipo_gasto = Column(String, nullable=False)
    monto = Column(DECIMAL(10, 2), nullable=False)
    fecha_creacion = Column(Date, default=func.current_date())
    descripcion = Column(String, nullable=True)
    responsable = Column(String, nullable=False)

    reporte_financiero = relationship("ReporteFinanciero", back_populates="gastos_variables")  # en GastoVariable
    apartamento = relationship("Apartamento", back_populates="gastos_variables")
    residente = relationship("Residente", back_populates="gastos_variables")
