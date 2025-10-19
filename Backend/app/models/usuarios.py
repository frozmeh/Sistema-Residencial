from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Date,
    func,
    Enum,
)
from ..database import Base
from sqlalchemy.orm import relationship


# ==================
# ---- Usuario ----
# ==================


class Usuario(Base):
    __tablename__ = "usuarios"  # Nombre de la tabla Usuario en la DB

    id = Column(Integer, primary_key=True, index=True)  # PK
    nombre = Column(String, unique=True, nullable=False)  # Nombre de Acceso
    email = Column(String, unique=True, nullable=False)  # Correo de contacto y recuperación
    password = Column(String, nullable=False)  # Contraseña encriptada
    id_rol = Column(Integer, ForeignKey("roles.id"))  # FK
    estado = Column(
        Enum("Activo", "Inactivo", "Bloqueado", name="estado_usuario"), default="Activo"
    )  # Activo/Inactivo
    fecha_creacion = Column(Date, default=func.current_date(), nullable=False)  # Fecha de registro del usuario
    ultima_sesion = Column(DateTime, nullable=True)  # Fecha del último acceso
    ultimo_ip = Column(String, nullable=True)
    intentos_fallidos = Column(Integer, default=0)
    fecha_bloqueo = Column(DateTime, nullable=True)

    # Relaciones
    rol = relationship("Rol", back_populates="usuarios")  # Relación con la tabla Roles
    residente = relationship("Residente", back_populates="usuario", uselist=False)
    notificaciones = relationship("Notificacion", back_populates="usuario", cascade="all, delete-orphan")
    incidencias_atendidas = relationship("Incidencia", back_populates="administrador", cascade="all, delete-orphan")
    auditorias = relationship("Auditoria", back_populates="usuario", cascade="all, delete-orphan")
