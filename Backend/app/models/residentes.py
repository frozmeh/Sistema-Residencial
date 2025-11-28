from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    func,
    Boolean,
    Enum,
)
from ..database import Base
from sqlalchemy.orm import relationship


# ====================
# ---- Residentes ----
# ====================


class Residente(Base):
    __tablename__ = "residentes"  # Nombre de la tabla Residentes en la DB

    id = Column(Integer, primary_key=True, index=True)  # PK
    id_apartamento = Column(Integer, ForeignKey("apartamentos.id"), nullable=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), unique=True)  # Relación con la tabla Usuario

    tipo_residente = Column(Enum("Propietario", "Inquilino", name="tipo_residente_enum"), nullable=False)
    nombre = Column(String, nullable=False)  # Nombre del Propietario / Inquilino
    cedula = Column(String, nullable=False, unique=True)
    telefono = Column(String)
    correo = Column(String)
    fecha_registro = Column(Date, default=func.current_date(), nullable=False)  # Fecha de registro del residente
    estado_aprobacion = Column(
        Enum("Pendiente", "Aprobado", "Rechazado", "Corrección Requerida", name="estado_aprobacion_enum"),
        default="Pendiente",
        nullable=False,
    )
    estado_operativo = Column(
        Enum("Activo", "Inactivo", "Suspendido", name="estado_operativo_enum"), default="Inactivo", nullable=False
    )
    reside_actualmente = Column(Boolean, default=False)

    usuario = relationship("Usuario", back_populates="residente", uselist=False)
    apartamento = relationship("Apartamento", back_populates="residente", uselist=False)
    pagos = relationship("Pago", back_populates="residente", cascade="all, delete-orphan")
    incidencias = relationship("Incidencia", back_populates="residente", cascade="all, delete-orphan")
    reservas = relationship("Reserva", back_populates="residente", cascade="all, delete-orphan")
    # gastos_variables = relationship("GastoVariable", back_populates="residente")
    # historiales = relationship("HistorialApartamento", back_populates="residente", cascade="all, delete-orphan")
