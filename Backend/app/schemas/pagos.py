from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import date

# ----- Literales -----

EstadoPago = Literal["Pendiente", "Validado", "Rechazado"]
MonedaPago = Literal["USD", "VES"]

# ===============
# ---- Pagos ----
# ===============


class PagoBase(BaseModel):
    monto: Optional[float] = None
    moneda: Optional[MonedaPago] = None
    tipo_cambio_bcv: Optional[float] = None
    fecha_pago: Optional[date] = None
    concepto: Optional[str] = None
    metodo: Optional[str] = None
    comprobante: Optional[str] = None
    estado: Optional[EstadoPago] = "Pendiente"
    verificado: Optional[bool] = False
    id_apartamento: Optional[int] = None
    id_reporte_financiero: Optional[int] = None

    # ----- Validaciones -----
    @field_validator("monto")
    def monto_positivo(cls, v):
        if v is not None and v <= 0:
            raise ValueError("El monto debe ser mayor a 0")
        return v

    @field_validator("tipo_cambio_bcv", mode="before")
    def cambio_si_ves(cls, v, info):
        moneda = info.data.get("moneda")
        if moneda == "VES" and (v is None or v <= 0):
            raise ValueError("Debe especificar tipo_cambio_bcv mayor a 0 para pagos en VES")
        return v

    @field_validator("fecha_pago")
    def fecha_valida(cls, v):
        if v is not None and v > date.today():
            raise ValueError("La fecha de pago no puede ser futura")
        return v


class PagoCreate(PagoBase):
    id_residente: int
    monto: float
    moneda: MonedaPago
    fecha_pago: date
    concepto: str
    metodo: str


class PagoUpdate(PagoBase):
    id_residente: Optional[int] = None


class PagoOut(PagoBase):
    id: int
    id_residente: int
    fecha_creacion: Optional[date]

    class Config:
        from_attributes = True
