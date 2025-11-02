# ======================
# ---- Apartamentos ----
# ======================

from sqlalchemy import Column, Integer, String, DECIMAL, Enum, CheckConstraint, UniqueConstraint, ForeignKey, DateTime
from datetime import datetime
from ..database import Base
from sqlalchemy.orm import relationship


class Apartamento(Base):
    __tablename__ = "apartamentos"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String, nullable=False)  # Ej. 1-3
    id_piso = Column(Integer, ForeignKey("pisos.id"), nullable=False)
    id_tipo_apartamento = Column(Integer, ForeignKey("tipos_apartamentos.id"), nullable=False)

    estado = Column(
        Enum("Disponible", "Ocupado", name="estado_apartamento_enum"),
        default="Disponible",
        nullable=False,
    )

    __table_args__ = (UniqueConstraint("numero", "id_piso", name="unique_apartamento_numero_piso"),)

    # Relaciones
    piso = relationship("Piso", back_populates="apartamentos")
    tipo_apartamento = relationship("TipoApartamento", back_populates="apartamentos")
    historial = relationship("HistorialApartamento", back_populates="apartamento", cascade="all, delete-orphan")
    residente = relationship("Residente", back_populates="apartamento", uselist=False)
    pagos = relationship("Pago", back_populates="apartamento", cascade="all, delete-orphan")
    gastos_fijos = relationship("GastoFijo", back_populates="apartamento")
    gastos_variables = relationship("GastoVariable", back_populates="apartamento")


# ================
# ---- Torres ----
# ================


class Torre(Base):
    __tablename__ = "torres"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)  # Ej: Torre A, Torre B
    descripcion = Column(String, nullable=True)

    pisos = relationship("Piso", back_populates="torre", cascade="all, delete-orphan")


# ================
# ---- Pisos ----
# ================


class Piso(Base):
    __tablename__ = "pisos"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(Integer, nullable=False)  # Ej: 1, 2, 3...
    id_torre = Column(Integer, ForeignKey("torres.id"), nullable=False)
    descripcion = Column(String, nullable=True)

    torre = relationship("Torre", back_populates="pisos")
    apartamentos = relationship("Apartamento", back_populates="piso", cascade="all, delete-orphan")


# ===============================
# ---- Tipos de Apartamentos ----
# ===============================


class TipoApartamento(Base):
    __tablename__ = "tipos_apartamentos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)  # Ej: Tipo A, Tipo B
    habitaciones = Column(Integer, nullable=False)
    banos = Column(Integer, nullable=False)
    descripcion = Column(String, nullable=True)
    porcentaje_aporte = Column(DECIMAL(5, 2), nullable=False)  # Ej. 20.00

    __table_args__ = (
        CheckConstraint("porcentaje_aporte >= 0 AND porcentaje_aporte <= 100", name="check_porcentaje_aporte"),
        UniqueConstraint("nombre", name="unique_tipo_apartamento_nombre"),
    )

    apartamentos = relationship("Apartamento", back_populates="tipo_apartamento")


# ==================================
# ---- Historial de Apartamento ----
# ==================================


class HistorialApartamento(Base):
    __tablename__ = "historial_apartamentos"
    id = Column(Integer, primary_key=True)
    id_apartamento = Column(Integer, ForeignKey("apartamentos.id"), nullable=False)
    id_residente = Column(Integer, ForeignKey("residentes.id"), nullable=False)
    fecha_asignacion = Column(DateTime, default=datetime.utcnow)
    fecha_desasignacion = Column(DateTime, nullable=True)

    apartamento = relationship("Apartamento", back_populates="historial")
    residente = relationship("Residente", back_populates="historiales")
