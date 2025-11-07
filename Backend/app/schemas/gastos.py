from pydantic import BaseModel, field_validator, validator
from typing import Optional, List
from datetime import date
from ..utils.tasa_bcv import obtener_tasa_bcv


# ======================
# ---- GASTO BASE ------
# ======================


class GastoBase(BaseModel):
    tipo_gasto: str
    monto_bs: Optional[float] = None
    monto_usd: Optional[float] = None
    descripcion: Optional[str] = None
    responsable: str
    id_reporte_financiero: Optional[int] = None
    fecha_creacion: Optional[date] = None

    @field_validator("monto_bs", "monto_usd")
    def validar_montos(cls, v, field):
        if v is not None and v <= 0:
            raise ValueError(f"El {field.name} debe ser mayor a 0")
        return v

    @field_validator("tipo_gasto")
    def validar_tipo(cls, v):
        if not v.strip():
            raise ValueError("El tipo de gasto no puede estar vacío")
        return v

    @field_validator("responsable")
    def validar_responsable(cls, v):
        if not v.strip():
            raise ValueError("El responsable no puede estar vacío")
        return v

    # --- Cálculo automático según la tasa BCV ---
    @validator("monto_bs", always=True)
    def calcular_monto_bs(cls, v, values):
        tasa = obtener_tasa_bcv()
        if not v and values.get("monto_usd"):
            return round(values["monto_usd"] * tasa, 2)
        return v

    @validator("monto_usd", always=True)
    def calcular_monto_usd(cls, v, values):
        tasa = obtener_tasa_bcv()
        if not v and values.get("monto_bs"):
            return round(values["monto_bs"] / tasa, 2)
        return v


# ==========================
# ---- GASTOS FIJOS --------
# ==========================


class GastoFijoCreate(GastoBase):
    id_apartamento: Optional[int] = None


class GastoFijoOut(GastoBase):
    id: int
    id_apartamento: Optional[int] = None

    class Config:
        from_attributes = True


# ==========================
# ---- GASTOS VARIABLES ----
# ==========================


class GastoVariableCreate(GastoBase):
    id_apartamento: Optional[int] = None
    id_residente: Optional[int] = None
    id_apartamentos: Optional[List[int]] = None
    id_pisos: Optional[List[int]] = None
    id_torres: Optional[List[int]] = None


class GastoVariableOut(GastoBase):
    id: int
    id_apartamento: Optional[int] = None
    id_residente: Optional[int] = None

    class Config:
        from_attributes = True
