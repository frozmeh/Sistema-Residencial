from pydantic import (
    BaseModel,
)
from typing import Optional
from datetime import datetime
from enum import Enum


# ========================
# ---- Notificaciones ----
# ========================


class TipoNotificacionEnum(str, Enum):
    PAGO = "Pago"
    INCIDENCIA = "Incidencia"
    SISTEMA = "Sistema"
    DOCUMENTO = "Documento"
    RESERVA = "Reserva"


class NotificacionBase(BaseModel):
    id_usuario: int
    mensaje: str
    tipo: Optional[TipoNotificacionEnum] = TipoNotificacionEnum.SISTEMA
    url: Optional[str] = None
    prioridad: Optional[str] = "Media"


class NotificacionCreate(NotificacionBase):
    pass  # No necesitas agregar nada extra


class NotificacionUpdate(BaseModel):
    leido: Optional[bool] = None
    fecha_leido: Optional[datetime] = None


class NotificacionOut(NotificacionBase):
    id: int
    fecha_envio: datetime
    leido: bool

    class Config:
        from_attributes = True
