from pydantic import BaseModel, field_validator, Field
from typing import Optional
from datetime import date
from .residentes import ResidenteOut


# =====================
# ---- Incidencias ----
# =====================


class IncidenciaBase(BaseModel):
    tipo: str = Field(..., description="Tipo de incidencia: Mantenimiento, Queja o Sugerencia")
    descripcion: str = Field(..., min_length=5, max_length=255)
    prioridad: Optional[str] = Field("Media", description="Nivel de prioridad: Alta, Media o Baja")

    @field_validator("tipo")
    def validar_tipo(cls, value):
        tipos_permitidos = ["Mantenimiento", "Queja", "Sugerencia"]
        if value not in tipos_permitidos:
            raise ValueError(f"El tipo debe ser uno de: {', '.join(tipos_permitidos)}")
        return value

    @field_validator("prioridad")
    def validar_prioridad(cls, value):
        prioridades_permitidas = ["Alta", "Media", "Baja"]
        if value not in prioridades_permitidas:
            raise ValueError(f"La prioridad debe ser una de: {', '.join(prioridades_permitidas)}")
        return value


class IncidenciaCreate(IncidenciaBase):
    id_residente: int = Field(..., description="ID del residente que reporta la incidencia")


class IncidenciaUpdate(BaseModel):
    tipo: Optional[str]
    descripcion: Optional[str]
    estado: Optional[str]
    prioridad: Optional[str]
    respuesta_admin: Optional[str]

    @field_validator("estado")
    def validar_estado(cls, value):
        if value and value not in ["Abierta", "En Proceso", "Cerrada"]:
            raise ValueError("El estado debe ser: Abierta, En Proceso o Cerrada")
        return value


class IncidenciaOut(IncidenciaBase):
    id: int
    fecha_reporte: date
    estado: str
    respuesta_admin: Optional[str]
    id_residente: int
    residente: ResidenteOut

    class Config:
        from_attributes = True
