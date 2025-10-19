from pydantic import (
    BaseModel,
    validator,
)
from typing import Optional, Literal


# ======================
# ---- Apartamentos ----
# ======================


class ApartamentoCreate(BaseModel):
    numero: str
    torre: str
    piso: int
    tipo_apartamento: str
    porcentaje_aporte: float
    id_residente: Optional[int] = None
    estado: Optional[Literal["Disponible", "Ocupado"]] = "Disponible"

    @validator("porcentaje_aporte")
    def validar_porcentaje(cls, v):
        if v <= 0 or v > 100:
            raise ValueError("El porcentaje_aporte debe ser mayor a 0 y menor o igual a 100")
        return v


class ApartamentoUpdate(BaseModel):
    numero: Optional[str]
    torre: Optional[str]
    piso: Optional[int]
    tipo_apartamento: Optional[str]
    porcentaje_aporte: Optional[float]
    id_residente: Optional[int]
    estado: Optional[Literal["Disponible", "Ocupado"]]

    @validator("porcentaje_aporte")
    def validar_porcentaje(cls, v):
        if v is not None and (v <= 0 or v > 100):
            raise ValueError("El porcentaje_aporte debe ser mayor a 0 y menor o igual a 100")
        return v


class ApartamentoOut(BaseModel):
    id: int
    numero: str
    torre: str
    piso: int
    tipo_apartamento: str
    porcentaje_aporte: float
    id_residente: Optional[int]
    estado: Literal["Disponible", "Ocupado"]

    class Config:
        from_attributes = True
