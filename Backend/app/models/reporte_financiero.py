from sqlalchemy import Column, Integer, String, Date, func, DECIMAL, DateTime, UniqueConstraint, Numeric
from ..database import Base
from sqlalchemy.orm import relationship

"""
class ReporteFinanciero(Base):
    __tablename__ = "reportes_financieros"
    __table_args__ = (UniqueConstraint("periodo", name="uq_reporte_periodo"),)

    id = Column(Integer, primary_key=True, index=True)
    periodo = Column(String(10), nullable=False)  # "2024-01", "2024-Q1", etc.

    # TOTALES EN USD (para consistencia)
    total_ingresos_usd = Column(Numeric(12, 2), default=0)
    total_gastos_usd = Column(Numeric(12, 2), default=0)
    saldo_final_usd = Column(Numeric(12, 2), default=0)

    # TOTALES EN VES (para reportes locales)
    total_ingresos_ves = Column(Numeric(15, 2), default=0)
    total_gastos_ves = Column(Numeric(15, 2), default=0)
    saldo_final_ves = Column(Numeric(15, 2), default=0)

    # TASA DE CAMBIO PROMEDIO DEL PERIODO
    tasa_cambio_promedio = Column(Numeric(10, 4), nullable=True)

    # METADATOS
    generado_por = Column(String(200), nullable=False)
    fecha_generacion = Column(DateTime, default=func.now())
    fecha_cierre = Column(DateTime, nullable=True)  # Cuando se cierra el período
    estado = Column(String(20), default="Abierto")  # Abierto, Cerrado, En revisión

    # RELACIONES (mantienes las actuales + nuevas)
    gastos_fijos = relationship("GastoFijo", back_populates="reporte_financiero", cascade="all, delete-orphan")
    gastos_variables = relationship("GastoVariable", back_populates="reporte_financiero", cascade="all, delete-orphan")
    pagos = relationship("Pago", back_populates="reporte_financiero", cascade="all, delete-orphan")

    # NUEVAS RELACIONES para la arquitectura
    gastos = relationship("Gasto", back_populates="reporte_financiero")
"""
