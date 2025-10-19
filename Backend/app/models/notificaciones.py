from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    func,
    Boolean,
)
from ..database import Base
from sqlalchemy.orm import relationship

# ========================
# ---- Notificaciones ----
# ========================


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    mensaje = Column(String, nullable=False)
    fecha_envio = Column(Date, default=func.current_date())
    tipo = Column(String)
    leido = Column(Boolean, default=False)

    usuario = relationship("Usuario", back_populates="notificaciones")
