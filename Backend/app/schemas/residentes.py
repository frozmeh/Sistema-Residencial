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
    id_apartamento: Optional[int] = None
    id_usuario: Optional[int] = None

    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    cedula: Optional[str] = Field(None, min_length=5, max_length=15)
    telefono: Optional[str] = Field(None, max_length=20)
    correo: Optional[EmailStr] = None
    tipo_residente: Optional[Literal["Propietario", "Inquilino"]] = None

    residente_actual: Optional[bool] = None
    estado: Optional[Literal["Activo", "Inactivo", "Suspendido"]] = None


class ResidenteCreate(ResidenteBase):
    nombre: str
    cedula: str
    correo: EmailStr
    tipo_residente: Literal["Propietario", "Inquilino"]
    torre: str
    numero_apartamento: str
    piso: int


class ResidenteUpdate(ResidenteBase):
    pass


class ResidenteOut(ResidenteBase):
    id: int
    fecha_registro: date

    class Config:
        from_attributes = True
