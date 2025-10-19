from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    func,
    DECIMAL,
)
from ..database import Base
from sqlalchemy.orm import relationship

# ==============================
# ---- Reportes Financieros ----
# ==============================


class ReporteFinanciero(Base):
    __tablename__ = "reportes_financieros"

    id = Column(Integer, primary_key=True, index=True)
    periodo = Column(String, nullable=False)
    total_gastos_fijos = Column(DECIMAL(10, 2), default=0)
    total_gastos_variables = Column(DECIMAL(10, 2), default=0)
    total_general = Column(DECIMAL(10, 2), default=0)
    generado_por = Column(String, nullable=False)
    fecha_generacion = Column(Date, default=func.current_date())

    gastos_fijos = relationship("GastoFijo", back_populates="reporte_financiero", cascade="all, delete-orphan")
    gastos_variables = relationship(
        "GastoVariable",
        back_populates="reporte_financiero",
        cascade="all, delete-orphan",
    )
    pagos = relationship("Pago", back_populates="reporte_financiero", cascade="all, delete-orphan")
