from sqlalchemy import Column, Integer, String, Date, func, DECIMAL, DateTime, UniqueConstraint
from ..database import Base
from sqlalchemy.orm import relationship

# ==============================
# ---- Reportes Financieros ----
# ==============================


class ReporteFinanciero(Base):
    __tablename__ = "reportes_financieros"
    __table_args__ = (UniqueConstraint("periodo", name="uq_reporte_periodo"),)

    id = Column(Integer, primary_key=True, index=True)
    periodo = Column(String, nullable=False)
    total_gastos_fijos = Column(DECIMAL(10, 2), default=0)
    total_gastos_variables = Column(DECIMAL(10, 2), default=0)
    total_general = Column(DECIMAL(10, 2), default=0)
    generado_por = Column(String, nullable=False)
    fecha_generacion = Column(DateTime, default=func.now())

    gastos_fijos = relationship("GastoFijo", back_populates="reporte_financiero", cascade="all, delete-orphan")
    gastos_variables = relationship(
        "GastoVariable",
        back_populates="reporte_financiero",
        cascade="all, delete-orphan",
    )
    pagos = relationship("Pago", back_populates="reporte_financiero", cascade="all, delete-orphan")
