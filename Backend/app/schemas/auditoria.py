from pydantic import (
    BaseModel,
)
from typing import Optional
from datetime import date


# ===================
# ---- Auditoria ----
# ===================


class AuditoriaCreate(BaseModel):
    id_usuario: int
    accion: str
    tabla_afectada: Optional[str] = None
    detalle: Optional[str] = None


class AuditoriaOut(AuditoriaCreate):
    id: int
    fecha: date

    class Config:
        from_attributes = True
