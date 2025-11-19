from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Literal
from datetime import date


# ====================
# ---- Residentes ----
# ====================


class ResidenteCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    cedula: str = Field(..., min_length=5, max_length=15)
    correo: EmailStr
    tipo_residente: Literal["Propietario", "Inquilino"]
    telefono: Optional[str] = Field(None, max_length=20)

    torre: str
    numero_apartamento: str
    piso: int = Field(..., ge=0, le=50)

    @field_validator("cedula")
    @classmethod
    def validar_cedula(cls, v):
        if not v.replace("-", "").isdigit():
            raise ValueError("La cédula debe contener solo números y guiones")
        cedula_limpia = v.replace("-", "")
        if len(cedula_limpia) < 5 or len(cedula_limpia) > 12:
            raise ValueError("La cédula debe tener entre 5 y 12 dígitos")
        return v

    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, v):
        if v and not v.replace("+", "").replace(" ", "").replace("-", "").isdigit():
            raise ValueError("El teléfono debe contener solo números, +, espacios y guiones")
        return v


class ResidenteUpdateAdmin(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    cedula: Optional[str] = Field(None, min_length=5, max_length=15)
    telefono: Optional[str] = Field(None, max_length=20)
    correo: Optional[EmailStr] = None
    tipo_residente: Optional[Literal["Propietario", "Inquilino"]] = None
    estado_operativo: Optional[Literal["Activo", "Inactivo", "Suspendido"]] = None
    estado_aprobacion: Optional[Literal["Pendiente", "Aprobado", "Rechazado", "Corrección Requerida"]] = None


class ResidenteUpdateResidente(BaseModel):
    telefono: Optional[str] = Field(None, max_length=20)
    correo: Optional[EmailStr] = None


class UsuarioBase(BaseModel):
    id: int

    class Config:
        from_attributes = True


class ApartamentoBase(BaseModel):
    id: int
    numero: str

    class Config:
        from_attributes = True


class PisoBase(BaseModel):
    id: int
    numero: int
    torre: Optional["TorreBase"] = None

    class Config:
        from_attributes = True


class TorreBase(BaseModel):
    id: int
    nombre: str

    class Config:
        from_attributes = True


class ApartamentoBase(BaseModel):
    id: int
    numero: str
    piso: Optional[PisoBase] = None

    class Config:
        from_attributes = True


class ResidenteOutBase(BaseModel):
    id: int
    nombre: str
    cedula: str
    correo: Optional[EmailStr]
    telefono: Optional[str]
    tipo_residente: str
    fecha_registro: date
    estado_aprobacion: str
    estado_operativo: str


class ResidenteOut(ResidenteOutBase):
    reside_actualmente: bool
    usuario: Optional[UsuarioBase] = None
    apartamento: Optional[ApartamentoBase] = None

    class Config:
        from_attributes = True


class ResidentePendienteOut(ResidenteOutBase):
    torre: str
    piso: int
    apartamento: str

    class Config:
        from_attributes = True
