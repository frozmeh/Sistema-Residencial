from pydantic import (
    BaseModel,
    field_validator,
)
from typing import Optional, Literal


# ======================
# ---- Apartamentos ----
# ======================


class ApartamentoBase(BaseModel):
    numero: Optional[str]
    torre: Optional[str]
    piso: Optional[int]
    tipo_apartamento: Optional[str]
    porcentaje_aporte: Optional[float]
    id_residente: Optional[int]
    estado: Optional[Literal["Disponible", "Ocupado"]] = "Disponible"

    @field_validator("porcentaje_aporte")
    def validar_porcentaje(cls, v):
        if v is not None and (v <= 0 or v > 100):
            raise ValueError("El porcentaje_aporte debe ser mayor a 0 y menor o igual a 100")
        return v


class ApartamentoCreate(ApartamentoBase):
    numero: str
    torre: str
    piso: int
    tipo_apartamento: str
    porcentaje_aporte: float


class ApartamentoUpdate(ApartamentoBase):
    pass


class ApartamentoOut(ApartamentoBase):
    id: int

    class Config:
        from_attributes = True
