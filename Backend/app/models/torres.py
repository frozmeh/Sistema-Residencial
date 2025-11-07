from sqlalchemy import Column, Integer, String, DECIMAL, Enum, ForeignKey, DateTime
from ..models.torres import gastos_variables_apartamentos
from ..database import Base
from sqlalchemy.orm import relationship


# ================
# ---- Torres ----
# ================


class Torre(Base):
    __tablename__ = "torres"

    id = Column(Integer, primary_key=True, index=True)

    nombre = Column(String, unique=True, nullable=False)  # Ej: Torre A, Torre B

    pisos = relationship("Piso", back_populates="torre", cascade="all, delete-orphan", lazy="selectin")


# ===============
# ---- Pisos ----
# ===============


class Piso(Base):
    __tablename__ = "pisos"

    id = Column(Integer, primary_key=True, index=True)
    id_torre = Column(Integer, ForeignKey("torres.id"), nullable=False)

    numero = Column(Integer, nullable=False)  # Ej: 1, 2, 3...

    torre = relationship("Torre", back_populates="pisos")
    apartamentos = relationship("Apartamento", back_populates="piso", cascade="all, delete-orphan", lazy="selectin")


# ======================
# ---- Apartamentos ----
# ======================


class Apartamento(Base):
    __tablename__ = "apartamentos"

    id = Column(Integer, primary_key=True, index=True)
    id_piso = Column(Integer, ForeignKey("pisos.id"), nullable=False)
    id_tipo_apartamento = Column(Integer, ForeignKey("tipos_apartamentos.id"), nullable=False)

    numero = Column(String, nullable=False)  # Ej. 1-3
    estado = Column(
        Enum("Disponible", "Ocupado", name="estado_apartamento_enum"),
        default="Disponible",
        nullable=False,
    )

    piso = relationship("Piso", back_populates="apartamentos")
    tipo_apartamento = relationship("TipoApartamento", back_populates="apartamentos", uselist=False)
    # historial = relationship("HistorialApartamento", back_populates="apartamento", cascade="all, delete-orphan")
    residente = relationship("Residente", back_populates="apartamento", uselist=False)
    pagos = relationship("Pago", back_populates="apartamento", cascade="all, delete-orphan")
    gastos_fijos = relationship("GastoFijo", back_populates="apartamento")
    gastos_variables = relationship(
        "GastoVariable", secondary=gastos_variables_apartamentos, back_populates="apartamentos"
    )


# ===============================
# ---- Tipos de Apartamentos ----
# ===============================


class TipoApartamento(Base):
    __tablename__ = "tipos_apartamentos"

    id = Column(Integer, primary_key=True, index=True)

    nombre = Column(String, nullable=False)  # Ej: Tipo A, Tipo B
    habitaciones = Column(Integer, nullable=False)
    banos = Column(Integer, nullable=False)
    porcentaje_aporte = Column(DECIMAL(5, 2), nullable=False)

    apartamentos = relationship("Apartamento", back_populates="tipo_apartamento")
