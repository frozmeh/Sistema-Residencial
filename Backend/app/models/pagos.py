from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    func,
    DECIMAL,
    Boolean,
)
from ..database import Base
from sqlalchemy.orm import relationship


# ===============
# ---- Pagos ----
# ===============


class Pago(Base):
    __tablename__ = "pagos"

    id = Column(Integer, primary_key=True, index=True)
    id_residente = Column(Integer, ForeignKey("residentes.id"), nullable=False)
    id_apartamento = Column(Integer, ForeignKey("apartamentos.id"))
    id_reporte_financiero = Column(Integer, ForeignKey("reportes_financieros.id"), nullable=True)

    monto = Column(DECIMAL(10, 2), nullable=False)  # Total pagado
    moneda = Column(String, nullable=False)  # USD o VES
    tipo_cambio_bcv = Column(DECIMAL(10, 2), nullable=True)  # Tasa usada si el pago fue en VES
    fecha_pago = Column(Date, nullable=False)  # Fecha del pago
    concepto = Column(String, nullable=False)  # Mantenimiento, reserva...
    metodo = Column(String, nullable=False)  # Transferencia, efectivo...
    comprobante = Column(String, nullable=True)  # Imagen o referencia
    estado = Column(String, default="Pendiente")  # Pendiente / Validado / Rechazado
    fecha_creacion = Column(Date, default=func.current_date())  # Fecha de registro del pago
    verificado = Column(Boolean, default=False)  # Si el pago ha sido validado por el Admin

    # Relaciones
    residente = relationship("Residente", back_populates="pagos")
    apartamento = relationship("Apartamento", back_populates="pagos")
    reporte_financiero = relationship("ReporteFinanciero", back_populates="pagos")
