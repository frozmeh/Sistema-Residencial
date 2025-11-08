from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, JSON
from ..database import Base
from sqlalchemy.orm import relationship


class Auditoria(Base):
    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    nombre_usuario = Column(String(100))
    accion = Column(String(50), nullable=False)
    tabla_afectada = Column(String(50), nullable=True)
    fecha = Column(DateTime, default=func.now())
    detalle = Column(JSON, nullable=True)  # <-- cambio aquí

    usuario = relationship("Usuario", back_populates="auditorias")
