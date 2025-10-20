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

# =====================
# ---- Incidencias ----
# =====================


class Incidencia(Base):
    __tablename__ = "incidencias"

    id = Column(Integer, primary_key=True, index=True)
    id_residente = Column(Integer, ForeignKey("residentes.id"), nullable=False)
    tipo = Column(String(50), nullable=False)
    descripcion = Column(String(255), nullable=False)
    fecha_reporte = Column(Date, default=func.current_date())
    estado = Column(String(20), default="Abierta")
    prioridad = Column(String(10), default="Media")
    respuesta_admin = Column(String(255), nullable=True)
    id_usuario_admin = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    fecha_atencion = Column(Date, nullable=True)

    # Relaciones
    residente = relationship("Residente", back_populates="incidencias")
    administrador = relationship("Usuario", lazy="joined")  # Relación opcional directa
