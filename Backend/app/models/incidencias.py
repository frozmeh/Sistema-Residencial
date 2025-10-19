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
    tipo = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    fecha_reporte = Column(Date, default=func.current_date())
    estado = Column(String, default="Abierta")
    prioridad = Column(String)
    respuesta_admin = Column(String, nullable=True)
    id_usuario_admin = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    fecha_atencion = Column(Date, nullable=True)

    administrador = relationship("Usuario")  # relación opcional directa

    residente = relationship("Residente", back_populates="incidencias")
