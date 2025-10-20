from pydantic import (
    BaseModel,
    EmailStr,
    Field,
)
from typing import Optional, Literal
from datetime import date


# ====================
# ---- Residentes ----
# ====================


class ResidenteBase(BaseModel):
    tipo_residente: Optional[Literal["Propietario", "Inquilino"]] = None
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    cedula: Optional[str] = Field(None, min_length=5, max_length=15)
    telefono: Optional[str] = Field(None, max_length=20)
    correo: Optional[EmailStr] = None
    id_apartamento: Optional[int] = None
    id_usuario: Optional[int] = None
    residente_actual: Optional[bool] = None
    estado: Optional[Literal["Activo", "Inactivo", "Suspendido"]] = None


class ResidenteCreate(ResidenteBase):
    tipo_residente: Literal["Propietario", "Inquilino"]
    nombre: str
    cedula: str


class ResidenteUpdate(ResidenteBase):
    pass


class ResidenteOut(ResidenteBase):
    id: int
    fecha_registro: date

    class Config:
        from_attributes = True
