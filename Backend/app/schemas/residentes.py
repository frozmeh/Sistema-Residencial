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
    validado: Optional[bool] = False


class ResidenteCreate(ResidenteBase):
    nombre: str
    cedula: str
    correo: EmailStr
    tipo_residente: Literal["Propietario", "Inquilino"]

    # Campos auxiliares para asociar el apartamento
    torre: str
    numero_apartamento: str
    piso: int


class ResidenteUpdateAdmin(ResidenteBase):
    validado: Optional[bool] = None


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


class ResidenteOut(ResidenteBase):
    id: int
    fecha_registro: Optional[date]
    validado: bool

    # Datos derivados (para retornar en joins)
    usuario: Optional[UsuarioBase] = None
    apartamento: Optional[ApartamentoBase] = None
    """ Por ejemplo para usar
        query = db.query(Residente, Usuario.nombre.label("usuario"), Apartamento.numero.label("apartamento"))
        .join(Usuario, Usuario.id == Residente.id_usuario)
        .join(Apartamento, Apartamento.id == Residente.id_apartamento)
        .all() """

    class Config:
        from_attributes = True


class ResidentePendienteOut(BaseModel):
    id: int
    nombre: str
    cedula: str
    correo: Optional[EmailStr]
    telefono: Optional[str]
    tipo_residente: str
    fecha_registro: date
    torre: str
    piso: int
    apartamento: str

    class Config:
        from_attributes = True


class ResidenteValidadoOut(BaseModel):
    id: int
    nombre: str
    cedula: str
    correo: Optional[EmailStr]
    telefono: Optional[str]
    tipo_residente: str
    fecha_registro: date
    torre: str
    piso: int
    apartamento: str

    class Config:
        from_attributes = True
