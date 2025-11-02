from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    func,
)
from ..database import Base
from sqlalchemy.orm import relationship


# ===================
# ---- Auditoria ----
# ===================


class Auditoria(Base):
    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    accion = Column(String(50), nullable=False)
    tabla_afectada = Column(String(50), nullable=True)
    fecha = Column(DateTime, default=func.now())  # Fecha y hora exacta
    detalle = Column(String(255), nullable=True)

    usuario = relationship("Usuario", back_populates="auditorias")
