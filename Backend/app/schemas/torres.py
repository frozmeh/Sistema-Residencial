from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional, List, Literal


# ================
# ---- Torres ----
# ================


class TorreBase(BaseModel):
    nombre: str


class TorreCreate(TorreBase):
    pass


class TorreOut(TorreBase):
    id: int
    cantidad_pisos: Optional[int] = 0
    cantidad_apartamentos: Optional[int] = 0

    class Config:
        from_attributes = True


# ===============
# ---- Pisos ----
# ===============


class PisoBase(BaseModel):
    numero: int
    id_torre: int
    descripcion: Optional[str] = None


class PisoOut(PisoBase):
    id: int
    cantidad_apartamentos: Optional[int] = 0

    class Config:
        from_attributes = True


# ===============================
# ---- Tipos de Apartamentos ----
# ===============================


class TipoApartamentoBase(BaseModel):
    nombre: str
    habitaciones: int
    banos: int
    descripcion: Optional[str] = None
    porcentaje_aporte: float


class TipoApartamentoOut(TipoApartamentoBase):
    id: int

    class Config:
        from_attributes = True


class ResidenteSimple(BaseModel):
    id: int
    nombre: str
    cedula: str
    tipo_residente: Literal["Propietario", "Inquilino"]
    correo: Optional[EmailStr] = None
    telefono: Optional[str] = None

    class Config:
        from_attributes = True


# ======================
# ---- Apartamentos ----
# ======================


class ApartamentoBase(BaseModel):
    numero: str
    id_piso: int
    id_tipo_apartamento: int
    estado: Optional[Literal["Disponible", "Ocupado"]] = "Disponible"


class ApartamentoOut(ApartamentoBase):
    id: int
    tipo_apartamento: TipoApartamentoOut = None
    residente: Optional[ResidenteSimple] = None

    class Config:
        from_attributes = True


# =========================================
# ---- Estructura completa de la Torre ----
# =========================================


class ApartamentoBasicoOut(BaseModel):
    id: int
    numero: str
    id_piso: int
    tipo_apartamento: TipoApartamentoOut

    class Config:
        from_attributes = True


class PisoConApartamentosOut(BaseModel):
    id: int
    numero: int
    descripcion: Optional[str] = None
    apartamentos: List[ApartamentoBasicoOut]

    class Config:
        from_attributes = True


class TorreCompletaOut(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    cantidad_pisos: int
    cantidad_apartamentos: int
    pisos: List[PisoConApartamentosOut]

    class Config:
        from_attributes = True
