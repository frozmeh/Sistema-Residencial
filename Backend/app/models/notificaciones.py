from sqlalchemy import Column, Integer, String, ForeignKey, Date, func, Boolean, Enum, Text, DateTime
import enum
from ..database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

# ========================
# ---- Notificaciones ----
# ========================


class TipoNotificacion(enum.Enum):
    PAGO = "Pago"
    INCIDENCIA = "Incidencia"
    SISTEMA = "Sistema"
    DOCUMENTO = "Documento"
    RESERVA = "Reserva"


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    mensaje = Column(String, nullable=False)  # O Text() si esperas mensajes largos
    fecha_envio = Column(DateTime(timezone=True), default=func.now())
    tipo = Column(Enum(TipoNotificacion))
    leido = Column(Boolean, default=False)
    url = Column(String, nullable=True)
    prioridad = Column(String, default="Media")
    fecha_leido = Column(DateTime, nullable=True)

    usuario = relationship("Usuario", back_populates="notificaciones")
