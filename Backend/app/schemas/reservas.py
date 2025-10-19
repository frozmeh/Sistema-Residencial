from pydantic import (
    BaseModel,
)
from typing import Optional
from datetime import date


# ==================
# ---- Reservas ----
# ==================


class ReservaCreate(BaseModel):
    id_residente: int
    area: str
    fecha_reserva: date
    hora_inicio: str
    hora_fin: str
    numero_personas: int
    notas: Optional[str] = None


class ReservaUpdate(BaseModel):
    area: Optional[str]
    fecha_reserva: Optional[date]
    hora_inicio: Optional[str]
    hora_fin: Optional[str]
    estado: Optional[str]
    numero_personas: Optional[int]
    notas: Optional[str]


class ReservaOut(ReservaCreate):
    id: int
    estado: str

    class Config:
        from_attributes = True
