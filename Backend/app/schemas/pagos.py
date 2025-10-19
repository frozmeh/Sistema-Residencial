from pydantic import (
    BaseModel,
)
from typing import Optional
from datetime import date


# ===============
# ---- Pagos ----
# ===============


class PagoCreate(BaseModel):
    id_residente: int
    monto: float
    moneda: str
    tipo_cambio_bcv: Optional[float] = None
    fecha_pago: date
    concepto: str
    metodo: str
    comprobante: Optional[str] = None
    estado: Optional[str] = "Pendiente"
    verificado: Optional[bool] = False


class PagoUpdate(BaseModel):
    monto: Optional[float] = None
    moneda: Optional[str] = None
    tipo_cambio_bcv: Optional[float] = None
    fecha_pago: Optional[date] = None
    concepto: Optional[str] = None
    metodo: Optional[str] = None
    comprobante: Optional[str] = None
    estado: Optional[str] = None
    verificado: Optional[bool] = None


class PagoOut(PagoCreate):
    id: int
    fecha_creacion: Optional[date]

    class Config:
        from_attributes = True
