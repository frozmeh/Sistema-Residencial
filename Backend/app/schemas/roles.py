from pydantic import (
    BaseModel,
)
from typing import Optional

# ===============
# ---- Roles ----
# ===============


class RolCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None


class RolOut(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]

    class Config:
        from_attributes = True


class RolMensajeOut(BaseModel):
    mensaje: str
    rol: RolOut
