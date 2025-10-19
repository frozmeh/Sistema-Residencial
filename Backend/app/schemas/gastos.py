from pydantic import (
    BaseModel,
)
from typing import Optional
from datetime import date


# ======================
# ---- Gastos Fijos ----
# ======================


class GastoFijoCreate(BaseModel):
    tipo: str
    monto: float
    descripcion: Optional[str] = None
    responsable: str


class GastoFijoOut(GastoFijoCreate):
    id: int
    fecha_registro: date

    class Config:
        from_attributes = True


# ==========================
# ---- Gastos Variables ----
# ==========================


class GastoVariableCreate(BaseModel):
    tipo: str
    monto: float
    descripcion: Optional[str] = None
    responsable: str


class GastoVariableOut(GastoVariableCreate):
    id: int
    fecha_registro: date

    class Config:
        from_attributes = True


from pydantic import BaseModel
from typing import Optional
from datetime import date
