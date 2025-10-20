from sqlalchemy import Column, Integer, String, DECIMAL, Enum, CheckConstraint, UniqueConstraint
from ..database import Base
from sqlalchemy.orm import relationship


# ======================
# ---- Apartamentos ----
# ======================


class Apartamento(Base):
    __tablename__ = "apartamentos"  # Nombre de la tabla Apartamentos en la DB

    id = Column(Integer, primary_key=True, index=True)  # PK

    numero = Column(String, nullable=False)  # Ej. 1-3
    torre = Column(String, nullable=False)  # Torre 1, 2
    piso = Column(Integer, nullable=False)  # Nivel
    tipo_apartamento = Column(String, nullable=False)  # 1 habitación, 2 habitaciones...
    porcentaje_aporte = Column(DECIMAL(5, 2), nullable=False)  # Ej. 20%
    estado = Column(
        Enum("Disponible", "Ocupado", name="estado_apartamento_enum"),
        default="Disponible",
        nullable=False,
    )  # Ocupado / Disponible

    __table_args__ = (
        CheckConstraint("porcentaje_aporte >= 0 AND porcentaje_aporte <= 100", name="check_porcentaje_aporte"),
        UniqueConstraint("numero", "torre", name="unique_apartamento_numero_torre"),
    )

    # Relaciones
    residente = relationship(
        "Residente", back_populates="apartamento", uselist=False
    )  # Uselist indica que la relación es 1-1
    pagos = relationship("Pago", back_populates="apartamento", cascade="all, delete-orphan")
    gastos_fijos = relationship("GastoFijo", back_populates="apartamento")
    gastos_variables = relationship("GastoVariable", back_populates="apartamento")
