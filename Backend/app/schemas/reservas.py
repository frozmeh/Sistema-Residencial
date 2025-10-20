from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date, time
from enum import Enum


class EstadoReserva(str, Enum):
    Activa = "Activa"
    Cancelada = "Cancelada"
    Finalizada = "Finalizada"


# ==================
# ---- Reservas ----
# ==================


class ReservaBase(BaseModel):
    id_residente: int
    area: str
    fecha_reserva: date
    hora_inicio: time
    hora_fin: time
    numero_personas: int = 1
    notas: Optional[str] = None

    @field_validator("hora_fin")
    def validar_hora_fin(cls, v, values):
        if "hora_inicio" in values and v <= values["hora_inicio"]:
            raise ValueError("La hora de fin debe ser posterior a la hora de inicio")
        return v


class ReservaCreate(ReservaBase):
    pass


class ReservaUpdate(BaseModel):
    area: Optional[str]
    fecha_reserva: Optional[date]
    hora_inicio: Optional[time]
    hora_fin: Optional[time]
    estado: Optional[EstadoReserva]
    numero_personas: Optional[int]
    notas: Optional[str]

    @field_validator("hora_fin")
    def validar_hora_fin(cls, v, values):
        if "hora_inicio" in values and v is not None and values.get("hora_inicio") and v <= values["hora_inicio"]:
            raise ValueError("La hora de fin debe ser posterior a la hora de inicio")
        return v


class ReservaOut(ReservaBase):
    id: int
    estado: EstadoReserva

    class Config:
        from_attributes = True
