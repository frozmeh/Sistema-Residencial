from pydantic import (
    BaseModel,
    field_validator,
    EmailStr,
)
from typing import Optional
from datetime import datetime, date

# ==================
# ---- Usuario ----
# ==================


class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    id_rol: Optional[int] = 2  # "Administrador" tiene id = 1, "Residente" tiene id = 2,
    estado: Optional[str] = "Activo"  # Es opcional y por defecto "Activo"
    fecha_creacion: Optional[date] = None
    ultima_sesion: Optional[datetime] = None  # Es opcional, porque el usuario puede no haber iniciado sesión aún.
    ultimo_ip: Optional[str] = None


class UsuarioOut(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    id_rol: int
    estado: str
    fecha_creacion: Optional[date] = None
    ultima_sesion: Optional[datetime] = None

    class Config:
        from_attributes = True  # Lee los objetos directamente y los convierte en JSON

    @field_validator("fecha_creacion", "ultima_sesion", mode="before")
    def solo_fecha(cls, v):  # Permite mostrar la fecha sin la hora
        if isinstance(v, (datetime, date)):
            return v.strftime("%Y-%m-%d")
        return v
