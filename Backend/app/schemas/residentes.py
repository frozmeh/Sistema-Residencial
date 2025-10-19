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


class ResidenteCreate(BaseModel):
    tipo_residente: Literal["Propietario", "Inquilino"]
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre del residente")
    cedula: str = Field(..., min_length=5, max_length=15, description="Cédula de identidad")
    telefono: Optional[str] = Field(None, max_length=20, description="Teléfono de contacto")
    correo: Optional[EmailStr] = None
    id_apartamento: Optional[int] = None
    id_usuario: Optional[int] = None


class ResidenteUpdate(BaseModel):
    tipo_residente: Optional[Literal["Propietario", "Inquilino"]] = None
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    cedula: Optional[str] = Field(None, min_length=5, max_length=15)
    telefono: Optional[str] = Field(None, max_length=20)
    correo: Optional[EmailStr] = None
    id_apartamento: Optional[int] = None
    id_usuario: Optional[int] = None
    residente_actual: Optional[bool] = None
    estado: Optional[Literal["Activo", "Inactivo", "Suspendido"]] = None


class ResidenteOut(BaseModel):
    id: int
    tipo_residente: str
    nombre: str
    cedula: str
    telefono: Optional[str] = None
    correo: Optional[str] = None
    id_apartamento: Optional[int] = None
    id_usuario: Optional[int] = None
    residente_actual: Optional[bool] = None
    estado: str
    fecha_registro: date

    class Config:
        from_attributes = True
