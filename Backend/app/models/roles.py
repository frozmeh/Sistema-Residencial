from sqlalchemy import Column, Integer, String
from ..database import Base
from sqlalchemy.orm import relationship


class Rol(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    descripcion = Column(String(255), nullable=True)

    usuarios = relationship("Usuario", back_populates="rol")
