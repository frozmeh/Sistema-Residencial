from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    Time,
    Enum
)
import enum
from ..database import Base
from sqlalchemy.orm import relationship


# ==================
# ---- Reservas ----
# ==================

class EstadoReserva(enum.Enum):
    Activa = "Activa"
    Cancelada = "Cancelada"
    Finalizada = "Finalizada"


class Reserva(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    id_residente = Column(Integer, ForeignKey("residentes.id"), nullable=False)
    area = Column(String, nullable=False)
    fecha_reserva = Column(Date, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    estado = Column(Enum(EstadoReserva), default=EstadoReserva.Activa, nullable=False)
    numero_personas = Column(Integer, default=1, nullable=False)
    notas = Column(String, nullable=True)

    residente = relationship("Residente", back_populates="reservas")
