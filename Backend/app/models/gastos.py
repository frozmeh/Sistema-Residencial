from sqlalchemy import Column, Integer, String, ForeignKey, Date, func, DECIMAL, Table, DateTime, Numeric

from sqlalchemy.orm import relationship
from ..database import Base

# ======================
# ---- Gastos Fijos ----
# ======================


class GastoFijo(Base):
    __tablename__ = "gastos_fijos"

    id = Column(Integer, primary_key=True, index=True)
    id_reporte_financiero = Column(Integer, ForeignKey("reportes_financieros.id", ondelete="CASCADE"))
    id_apartamento = Column(Integer, ForeignKey("apartamentos.id", ondelete="SET NULL"))

    tipo_gasto = Column(String, nullable=False, index=True)  # Ejemplo: mantenimiento, limpieza, seguridad
    descripcion = Column(String, nullable=True)
    responsable = Column(String, nullable=False)

    monto_usd = Column(Numeric(12, 2), nullable=False)
    monto_bs = Column(Numeric(12, 2), nullable=False)
    tasa_cambio = Column(Numeric(10, 4), nullable=False)
    monto_pagado = Column(Numeric(12, 2), default=0, nullable=False)
    saldo_pendiente = Column(Numeric(12, 2), nullable=False)

    fecha_creacion = Column(Date, default=func.current_date(), index=True)
    fecha_tasa_bcv = Column(DateTime, nullable=True)

    # Relaciones
    reporte_financiero = relationship("ReporteFinanciero", back_populates="gastos_fijos")
    apartamento = relationship("Apartamento", back_populates="gastos_fijos")
    pagos = relationship("Pago", back_populates="gasto_fijo")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Calcular saldo pendiente inicial
        self.saldo_pendiente = self.monto_usd


# ========================================
# ---- Tabla intermedia para Gastos Variables ----
# ========================================

gastos_variables_apartamentos = Table(
    "gastos_variables_apartamentos",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("id_gasto_variable", Integer, ForeignKey("gastos_variables.id", ondelete="CASCADE")),
    Column("id_apartamento", Integer, ForeignKey("apartamentos.id", ondelete="CASCADE")),
    Column("monto_asignado_usd", Numeric(12, 2), nullable=False),
    Column("monto_asignado_bs", Numeric(12, 2), nullable=False),
)


# ==========================
# ---- Gastos Variables ----
# ==========================


class GastoVariable(Base):
    __tablename__ = "gastos_variables"

    id = Column(Integer, primary_key=True, index=True)
    id_reporte_financiero = Column(Integer, ForeignKey("reportes_financieros.id", ondelete="CASCADE"))
    id_residente = Column(Integer, ForeignKey("residentes.id", ondelete="SET NULL"), nullable=True)

    tipo_gasto = Column(String, nullable=False, index=True)
    descripcion = Column(String, nullable=True)
    responsable = Column(String, nullable=False)

    monto_usd = Column(Numeric(12, 2), nullable=False)
    monto_bs = Column(Numeric(12, 2), nullable=False)
    tasa_cambio = Column(Numeric(10, 4), nullable=False)
    monto_pagado = Column(Numeric(12, 2), default=0, nullable=False)
    saldo_pendiente = Column(Numeric(12, 2), nullable=False)

    fecha_creacion = Column(Date, default=func.current_date(), index=True)
    fecha_tasa_bcv = Column(DateTime, nullable=True)

    # Relaciones
    reporte_financiero = relationship("ReporteFinanciero", back_populates="gastos_variables")
    residente = relationship("Residente", back_populates="gastos_variables")
    pagos = relationship("Pago", back_populates="gasto_variable")

    # Relación muchos a muchos con apartamentos
    apartamentos = relationship(
        "Apartamento", secondary=gastos_variables_apartamentos, back_populates="gastos_variables"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Calcular saldo pendiente inicial
        self.saldo_pendiente = self.monto_usd
