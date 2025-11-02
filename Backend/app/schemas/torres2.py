from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List


# ======================
# ---- Tipos de Apartamentos ----
# ======================


class TipoApartamentoBase(BaseModel):
    nombre: str
    habitaciones: int
    banos: int
    descripcion: Optional[str] = None
    porcentaje_aporte: float

    @field_validator("porcentaje_aporte")
    def validar_porcentaje(cls, v):
        if v <= 0 or v > 100:
            raise ValueError("El porcentaje_aporte debe ser mayor a 0 y menor o igual a 100")
        return v


class TipoApartamentoCreate(TipoApartamentoBase):
    pass


class TipoApartamentoOut(TipoApartamentoBase):
    id: int

    class Config:
        from_attributes = True


# ======================
# ---- Torres ----------
# ======================


class TorreBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    direccion: Optional[str] = None


class TorreCreate(TorreBase):
    pass


class TorreOut(TorreBase):
    id: int
    cantidad_pisos: Optional[int] = 0
    cantidad_apartamentos: Optional[int] = 0
    pisos: Optional[List["PisoOut"]] = None  # Relación opcional, no cargada siempre

    class Config:
        from_attributes = True


# ======================
# ---- Pisos -----------
# ======================


class PisoBase(BaseModel):
    numero: int
    id_torre: int
    descripcion: Optional[str] = None


class PisoCreate(PisoBase):
    pass


class PisoOut(PisoBase):
    id: int
    torre: Optional[TorreOut] = None  # Relación simplificada
    cantidad_apartamentos: Optional[int] = 0
    apartamentos: Optional[List["ApartamentoOut"]] = None  # Lista opcional

    class Config:
        from_attributes = True


# ======================
# ---- Apartamentos ----
# ======================


class ApartamentoBase(BaseModel):
    numero: Optional[str]
    id_piso: Optional[int]
    id_tipo_apartamento: Optional[int]
    id_residente: Optional[int] = None
    estado: Optional[Literal["Disponible", "Ocupado"]] = "Disponible"


class ApartamentoCreate(ApartamentoBase):
    numero: str
    id_piso: int
    id_tipo_apartamento: int


class ApartamentoUpdate(ApartamentoBase):
    pass


class ApartamentoOut(ApartamentoBase):
    id: int
    piso: Optional[PisoOut] = None
    tipo_apartamento: Optional[TipoApartamentoOut] = None

    class Config:
        from_attributes = True


# ===============================
# ---- Historial de Apartamento --
# ===============================


class HistorialApartamentoBase(BaseModel):
    id_apartamento: int
    id_residente: int
    fecha_asignacion: Optional[str] = None
    fecha_desasignacion: Optional[str] = None


class HistorialApartamentoCreate(HistorialApartamentoBase):
    pass


class HistorialApartamentoOut(HistorialApartamentoBase):
    id: int
    apartamento: Optional[ApartamentoOut] = None

    class Config:
        from_attributes = True


# ===============================
# ---- Residente ----------------
# ===============================


class ResidenteOut(BaseModel):
    id: int
    nombre: str
    apellido: str
    telefono: Optional[str] = None
    correo_contacto: Optional[str] = None

    class Config:
        from_attributes = True


# ---- Forward refs para relaciones cruzadas
PisoOut.update_forward_refs()
TorreOut.update_forward_refs()
ApartamentoOut.update_forward_refs()
