from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    func,
    DECIMAL,
    Table,
    DateTime,
    Numeric,
    Index,
    event,
    Boolean,
    Enum,
    UniqueConstraint,
    Text,
)
import enum
from ..database import Base
from sqlalchemy.orm import relationship

# ======================
# ---- Tasa Cambio ----
# ======================


class TasaCambio(Base):
    __tablename__ = "tasas_cambio"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False, index=True)
    tasa_usd_ves = Column(Numeric(10, 4), nullable=False)
    fuente = Column(String(50), default="BCV")
    es_historica = Column(Boolean, default=False)
    fecha_creacion = Column(DateTime, default=func.now())

    __table_args__ = (UniqueConstraint("fecha", "fuente", name="uq_tasa_fecha_fuente"),)


# ======================
# ---- Enums ----
# ======================


class EstadoCargoEnum(str, enum.Enum):
    PENDIENTE = "Pendiente"  # Creado pero no pagado
    PAGADO = "Pagado"  # Totalmente pagado
    PARCIAL = "Parcial"  # Parcialmente pagado
    VENCIDO = "Vencido"  # Fecha de vencimiento pasada y no pagado


class TipoGastoEnum(str, enum.Enum):
    FIJO = "Fijo"  # Gastos recurrentes (Mantenimiento, administración)
    VARIABLE = "Variable"  # Gastos imprevistos (reparaciones, emergencias)


class EstadoGastoEnum(str, enum.Enum):
    PENDIENTE = "Pendiente"  # Gasto registrado pero no distribuido
    DISTRIBUIDO = "Distribuido"  # Gasto distribuido entre apartamentos
    CERRADO = "Cerrado"  # Gasto completamente pagado


# ======================
# ---- Gasto ----
# ======================


class Gasto(Base):
    __tablename__ = "gastos"

    id = Column(Integer, primary_key=True, index=True)
    id_reporte_financiero = Column(Integer, ForeignKey("reportes_financieros.id", ondelete="CASCADE"), nullable=False)
    tipo_gasto = Column(Enum(TipoGastoEnum), nullable=False)  # Fijo/Variable/Extraordinario
    descripcion = Column(String(500), nullable=False)  # "Reparación ascensor Torre A"
    monto_total_usd = Column(Numeric(12, 2), nullable=False)  # 1000.00 (monto original)
    monto_total_ves = Column(Numeric(15, 2), nullable=False)  # 36000000.00 (convertido)
    tasa_cambio = Column(Numeric(10, 4), nullable=False)  # 36000.0000 (tasa BCV)
    criterio_seleccion = Column(String(50), nullable=True)  # "Todas Torres", "Torre Específica", etc.
    parametros_criterio = Column(Text, nullable=True)
    fecha_gasto = Column(Date, nullable=False, index=True)  # 2024-01-15 (cuando ocurrió)
    fecha_tasa_bcv = Column(Date, nullable=False)  # 2024-01-15 (fecha de la tasa)
    responsable = Column(String(200), nullable=False)  # "Juan Pérez - Administrador"
    estado = Column(Enum(EstadoGastoEnum), default=EstadoGastoEnum.PENDIENTE)  # Control de proceso
    fecha_creacion = Column(DateTime, default=func.now())
    fecha_actualizacion = Column(DateTime, default=func.now(), onupdate=func.now())
    periodo = Column(String(7), nullable=False, index=True)  # 🆕 CRÍTICO: "2025-01", "2025-11"

    # Relaciones
    reporte_financiero = relationship("ReporteFinanciero", back_populates="gastos")
    distribuciones = relationship("DistribucionGasto", back_populates="gasto", cascade="all, delete-orphan")
    cargos = relationship("Cargo", back_populates="gasto", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_gastos_tipo_fecha", "tipo_gasto", "fecha_gasto"),
        Index("ix_gastos_estado", "estado"),
    )
    pagos = relationship("Pago", back_populates="gasto")
    reporte_financiero = relationship("ReporteFinanciero", back_populates="gastos")


# ======================
# ---- Distribucion Gasto ----
# ======================


class DistribucionGasto(Base):
    __tablename__ = "distribuciones_gasto"

    id = Column(Integer, primary_key=True, index=True)
    id_gasto = Column(Integer, ForeignKey("gastos.id", ondelete="CASCADE"), nullable=False)
    id_apartamento = Column(Integer, ForeignKey("apartamentos.id", ondelete="CASCADE"), nullable=False)
    monto_asignado_usd = Column(Numeric(12, 2), nullable=False)  # 4.63 (parte del apto)
    monto_asignado_ves = Column(Numeric(15, 2), nullable=False)  # 166680.00 (convertido)
    porcentaje_aplicado = Column(Numeric(6, 4), nullable=False)  # 0.27 (27% para 1 hab)
    fecha_creacion = Column(DateTime, default=func.now())

    gasto = relationship("Gasto", back_populates="distribuciones")
    apartamento = relationship("Apartamento", back_populates="distribuciones_gasto")

    __table_args__ = (
        UniqueConstraint("id_gasto", "id_apartamento", name="uq_distribucion_gasto_apartamento"),
        Index("ix_distribucion_apartamento", "id_apartamento", "fecha_creacion"),
    )


# ======================
# ---- Cargo ----
# ======================


# ======================
# ---- Cargo ----
# ======================


class Cargo(Base):
    __tablename__ = "cargos"

    id = Column(Integer, primary_key=True, index=True)
    id_apartamento = Column(Integer, ForeignKey("apartamentos.id", ondelete="CASCADE"), nullable=False)
    id_gasto = Column(Integer, ForeignKey("gastos.id", ondelete="CASCADE"), nullable=False)
    descripcion = Column(String(500), nullable=False)
    monto_usd = Column(Numeric(12, 2), nullable=False)  # ✅ Monto total que debe
    monto_ves = Column(Numeric(15, 2), nullable=False)  # ✅ Monto total en VES
    saldo_pendiente_usd = Column(Numeric(12, 2), nullable=False)  # 🆕 NUEVO: Lo que falta pagar
    saldo_pendiente_ves = Column(Numeric(15, 2), nullable=False)  # 🆕 NUEVO: Lo que falta en VES
    fecha_vencimiento = Column(Date, nullable=False, index=True)
    estado = Column(Enum(EstadoCargoEnum), default=EstadoCargoEnum.PENDIENTE)
    fecha_creacion = Column(DateTime, default=func.now())
    fecha_actualizacion = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relaciones (MANTENER igual)
    apartamento = relationship("Apartamento", back_populates="cargos")
    gasto = relationship("Gasto", back_populates="cargos")
    pagos = relationship("Pago", back_populates="cargo")

    __table_args__ = (
        Index("ix_cargos_apartamento_estado", "id_apartamento", "estado"),
        Index("ix_cargos_vencimiento", "fecha_vencimiento", "estado"),
    )


# ======================
# ---- Reporte Financiero ----
# ======================


class ReporteFinanciero(Base):
    __tablename__ = "reportes_financieros"
    __table_args__ = (UniqueConstraint("periodo", name="uq_reporte_periodo"),)

    id = Column(Integer, primary_key=True, index=True)
    periodo = Column(String(10), nullable=False)

    # TOTALES EN USD
    total_ingresos_usd = Column(Numeric(12, 2), default=0)
    total_gastos_usd = Column(Numeric(12, 2), default=0)
    saldo_final_usd = Column(Numeric(12, 2), default=0)

    # TOTALES EN VES
    total_ingresos_ves = Column(Numeric(15, 2), default=0)
    total_gastos_ves = Column(Numeric(15, 2), default=0)
    saldo_final_ves = Column(Numeric(15, 2), default=0)

    # TASA DE CAMBIO PROMEDIO
    tasa_cambio_promedio = Column(Numeric(10, 4), nullable=True)

    # METADATOS
    generado_por = Column(String(200), nullable=False)
    fecha_generacion = Column(DateTime, default=func.now())
    fecha_cierre = Column(DateTime, nullable=True)
    estado = Column(String(20), default="Abierto")

    # Solo relaciones que EXISTEN
    gastos = relationship("Gasto", back_populates="reporte_financiero")
    pagos = relationship("Pago", back_populates="reporte_financiero")
