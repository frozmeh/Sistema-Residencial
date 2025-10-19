from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
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
    accion = Column(String, nullable=False)
    tabla_afectada = Column(String)
    fecha = Column(Date, default=func.current_date())
    detalle = Column(String, nullable=True)

    usuario = relationship("Usuario", back_populates="auditorias")
