from pydantic import BaseModel, field_validator, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date

# ==================
# ---- Usuario ----
# ==================


class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=8)
    id_rol: Optional[int] = Field(default=2, ge=1, le=2)
    estado: Optional[str] = Field(default="Activo")

    @field_validator("estado")
    @classmethod
    def validar_estado(cls, v):
        estados_validos = ["Activo", "Inactivo", "Bloqueado"]
        if v not in estados_validos:
            raise ValueError(f"Estado debe ser uno de: {estados_validos}")
        return v

    @field_validator("id_rol")
    @classmethod
    def validar_rol(cls, v):
        if v not in [1, 2]:  # Asumiendo 1=Admin, 2=Residente
            raise ValueError("Rol inválido")
        return v


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    id_rol: Optional[int] = None


class UsuarioOut(BaseModel):
    id: Optional[int] = None
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    id_rol: Optional[int] = None
    estado: Optional[str] = None
    fecha_creacion: Optional[date] = None
    ultima_sesion: Optional[datetime] = None
    ultimo_ip: Optional[str] = None

    class Config:
        from_attributes = True  # Lee los objetos directamente y los convierte en JSON


# Respuestas específicas con mensaje
class UsuarioResponse(BaseModel):
    mensaje: str
    usuario: UsuarioOut


class UsuarioListResponse(BaseModel):
    usuarios: Optional[List[UsuarioOut]]
    total: Optional[int]


class UsuarioEstadoResponse(BaseModel):
    mensaje: Optional[str]
    usuario: Optional[UsuarioOut] = None
