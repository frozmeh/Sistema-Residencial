from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    DECIMAL,
    Boolean,
    Enum,
    Index,
    func,
)
from sqlalchemy.orm import relationship
from ..database import Base
import enum


# ============================
# ---- Enumeraciones ----
# ============================


class MonedaEnum(str, enum.Enum):
    USD = "USD"
    VES = "VES"


class EstadoPagoEnum(str, enum.Enum):
    PENDIENTE = "Pendiente"
    VALIDADO = "Validado"
    RECHAZADO = "Rechazado"


class MetodoPagoEnum(str, enum.Enum):
    TRANSFERENCIA = "Transferencia"
    EFECTIVO = "Efectivo"
    PAGO_MOVIL = "Pago Móvil"


# =====================
# ---- Modelo Pago ----
# =====================


class Pago(Base):
    __tablename__ = "pagos"

    id = Column(Integer, primary_key=True, index=True)
    id_residente = Column(Integer, ForeignKey("residentes.id"), nullable=False)
    id_apartamento = Column(Integer, ForeignKey("apartamentos.id"), nullable=True)
    id_reporte_financiero = Column(Integer, ForeignKey("reportes_financieros.id"), nullable=True)
    id_cargo = Column(Integer, ForeignKey("cargos.id"), nullable=False)  # ✅ Cambiar a NOT NULL
    id_gasto = Column(Integer, ForeignKey("gastos.id"), nullable=True)

    # 🆕 NUEVOS CAMPOS para el flujo simplificado
    monto_pagado_usd = Column(DECIMAL(12, 2), nullable=False)  # Cuánto pagó en USD
    monto_pagado_ves = Column(DECIMAL(15, 2), nullable=False)  # Cuánto pagó en VES
    tasa_cambio_pago = Column(DECIMAL(10, 4), nullable=False)  # Tasa del día del pago

    monto = Column(DECIMAL(12, 2), nullable=True)  # Hacer opcional durante transición
    moneda = Column(Enum(MonedaEnum), nullable=True)  # Hacer opcional
    tipo_cambio_bcv = Column(DECIMAL(12, 2), nullable=True)  # Mantener

    concepto = Column(String(100), nullable=False)
    metodo = Column(Enum(MetodoPagoEnum), nullable=False)
    comprobante = Column(String(255), nullable=True)
    estado = Column(Enum(EstadoPagoEnum), default=EstadoPagoEnum.PENDIENTE, nullable=False)
    verificado = Column(Boolean, default=False, nullable=False)

    fecha_creacion = Column(DateTime, default=func.now(), nullable=False)
    fecha_actualizacion = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    residente = relationship("Residente", back_populates="pagos")
    apartamento = relationship("Apartamento", back_populates="pagos")
    reporte_financiero = relationship("ReporteFinanciero", back_populates="pagos")
    gasto = relationship("Gasto", back_populates="pagos")
    cargo = relationship("Cargo", back_populates="pagos")

    __table_args__ = (
        Index("idx_residente_fecha", "id_residente"),
        Index("idx_estado_pago", "estado"),
        Index("idx_moneda_metodo", "moneda", "metodo"),
        Index("idx_pago_cargo", "id_cargo"),  # 🆕 NUEVO índice
    )
