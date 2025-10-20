from pydantic import (
    BaseModel,
    field_validator,
)
from typing import Optional
from datetime import date


# ======================
# ---- Gastos Fijos ----
# ======================


class GastoBase(BaseModel):
    tipo_gasto: str
    monto: float
    descripcion: Optional[str] = None
    responsable: str
    id_reporte_financiero: Optional[int] = None
    id_apartamento: Optional[int] = None

    @field_validator("monto")
    def validar_monto(cls, v):
        if v <= 0:
            raise ValueError("El monto debe ser mayor a 0")
        return v


class GastoFijoCreate(GastoBase): ...


class GastoFijoOut(GastoBase):
    id: int
    fecha_creacion: date

    class Config:
        from_attributes = True


# ==========================
# ---- Gastos Variables ----
# ==========================


class GastoVariableCreate(GastoBase): ...


class GastoVariableOut(GastoBase):
    id: int
    fecha_creacion: date

    class Config:
        from_attributes = True
