from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    Time,
)
from ..database import Base
from sqlalchemy.orm import relationship


# ==================
# ---- Reservas ----
# ==================


class Reserva(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    id_residente = Column(Integer, ForeignKey("residentes.id"), nullable=False)
    area = Column(String, nullable=False)
    fecha_reserva = Column(Date, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    estado = Column(String, default="Activa")
    numero_personas = Column(Integer)
    notas = Column(String, nullable=True)

    residente = relationship("Residente", back_populates="reservas")
