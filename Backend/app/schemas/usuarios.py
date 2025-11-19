from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# ==================
# ---- Usuario ----
# ==================


class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=8)


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None


class UsuarioUpdatePassword(BaseModel):
    password: str = Field(..., min_length=8)


class UsuarioUpdateRol(BaseModel):
    id_rol: int


class UsuarioBase(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    estado: Optional[str] = None
    fecha_creacion: Optional[datetime] = None
    ultima_sesion: Optional[datetime] = None
    ultimo_ip: Optional[str] = None


class UsuarioAdminOut(UsuarioBase):
    id: Optional[int] = None
    id_rol: Optional[int] = None

    class Config:
        from_attributes = True


class UsuarioResidenteOut(UsuarioBase):

    class Config:
        from_attributes = True
