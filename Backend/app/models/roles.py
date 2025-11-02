from sqlalchemy import (
    Column,
    Integer,
    String,
    JSON,
)
from ..database import Base
from sqlalchemy.orm import relationship


# ===============
# ---- Roles ----
# ===============


class Rol(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)  # Administrador / Residente
    permisos = Column(JSON, nullable=False)  # Acciones por módulo
    descripcion = Column(String, nullable=True)

    usuarios = relationship("Usuario", back_populates="rol")
