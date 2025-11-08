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
    # id_gasto = Column(Integer, ForeignKey("gastos.id"), nullable=True)  # ← Reservado para integración futura

    monto = Column(DECIMAL(12, 2), nullable=False)  # Monto total pagado
    moneda = Column(Enum(MonedaEnum), nullable=False)  # USD o VES
    tipo_cambio_bcv = Column(DECIMAL(12, 2), nullable=True)  # Tasa usada si el pago fue en VES
    fecha_pago = Column(DateTime, nullable=False)  # Fecha real del pago
    concepto = Column(String(100), nullable=False)  # Ejemplo: mantenimiento, reserva, etc.
    metodo = Column(Enum(MetodoPagoEnum), nullable=False)  # Medio usado: transferencia, efectivo, etc.
    comprobante = Column(String(255), nullable=True)  # Ruta o referencia de comprobante
    estado = Column(Enum(EstadoPagoEnum), default=EstadoPagoEnum.PENDIENTE, nullable=False)
    verificado = Column(Boolean, default=False, nullable=False)  # Si ha sido validado por el Admin

    fecha_creacion = Column(DateTime, default=func.now(), nullable=False)  # Fecha de registro
    fecha_actualizacion = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    residente = relationship("Residente", back_populates="pagos")
    apartamento = relationship("Apartamento", back_populates="pagos")
    reporte_financiero = relationship("ReporteFinanciero", back_populates="pagos")
    # gasto = relationship("Gasto", back_populates="pagos")  # ← Activar si se enlaza con módulo de gastos

    # Índices para mejorar rendimiento en búsquedas frecuentes
    __table_args__ = (
        Index("idx_residente_fecha", "id_residente", "fecha_pago"),
        Index("idx_estado_pago", "estado"),
        Index("idx_moneda_metodo", "moneda", "metodo"),
    )
