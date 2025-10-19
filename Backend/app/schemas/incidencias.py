from pydantic import (
    BaseModel,
)
from typing import Optional
from datetime import date


# =====================
# ---- Incidencias ----
# =====================


class IncidenciaCreate(BaseModel):
    id_residente: int
    tipo: str
    descripcion: str
    prioridad: Optional[str] = "Media"


class IncidenciaUpdate(BaseModel):
    tipo: Optional[str]
    descripcion: Optional[str]
    estado: Optional[str]
    prioridad: Optional[str]
    respuesta_admin: Optional[str]


class IncidenciaOut(IncidenciaCreate):
    id: int
    fecha_reporte: date
    estado: str
    respuesta_admin: Optional[str]

    class Config:
        from_attributes = True
