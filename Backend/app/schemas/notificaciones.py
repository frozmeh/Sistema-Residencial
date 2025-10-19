from pydantic import (
    BaseModel,
)
from typing import Optional
from datetime import date


# ========================
# ---- Notificaciones ----
# ========================


class NotificacionCreate(BaseModel):
    id_usuario: int
    mensaje: str
    tipo: Optional[str] = "Sistema"


class NotificacionUpdate(BaseModel):
    leido: Optional[bool]


class NotificacionOut(NotificacionCreate):
    id: int
    fecha_envio: date
    leido: bool

    class Config:
        from_attributes = True
