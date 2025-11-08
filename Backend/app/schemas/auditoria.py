from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


# Para los cambios dentro del detalle
class Cambios(BaseModel):
    antes: Optional[Any]
    despues: Optional[Any]


class DetalleAuditoria(BaseModel):
    cambios: Optional[Dict[str, Cambios]] = None
    ip: Optional[str] = None
    endpoint: Optional[str] = None


class AuditoriaCreate(BaseModel):
    id_usuario: int
    nombre_usuario: str
    accion: str
    tabla_afectada: Optional[str] = None
    detalle: Optional[dict] = None


class AuditoriaOut(AuditoriaCreate):
    id: int
    fecha: datetime

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
        json_encoders = {dict: lambda v: v}
