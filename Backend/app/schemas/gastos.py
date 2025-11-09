from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List
from datetime import date, datetime
from ..utils.tasa_bcv import obtener_tasa_bcv


# ======================
# ---- GASTO BASE ------
# ======================


class GastoBase(BaseModel):
    tipo_gasto: str
    descripcion: Optional[str] = None
    responsable: str
    monto_usd: Optional[float] = None
    monto_bs: Optional[float] = None
    tasa_cambio: Optional[float] = None
    id_reporte_financiero: Optional[int] = None
    monto_pagado: Optional[float] = 0
    saldo_pendiente: Optional[float] = None

    # --- Validaciones de contenido ---
    @field_validator("tipo_gasto", "responsable")
    def no_vacio(cls, v, field):
        if not v or not v.strip():
            raise ValueError(f"El campo '{field.name}' no puede estar vacío.")
        return v

    @field_validator("monto_usd", "monto_bs")
    def validar_montos(cls, v, field):
        if v is not None and v <= 0:
            raise ValueError(f"El {field.name} debe ser mayor que 0.")
        return v

    # --- Cálculos automáticos con tasa BCV ---
    @model_validator(mode="after")
    def calcular_tasas_automaticas(cls, values):
        from decimal import Decimal
        from ..utils.tasa_bcv import obtener_tasa_historica_bcv

        # Usar tasa de la fecha del gasto, no la actual
        fecha_gasto = values.fecha_creacion or date.today()
        tasa, fecha_tasa = obtener_tasa_historica_bcv(fecha_gasto)
        tasa_decimal = Decimal(str(tasa))

        if values.monto_usd is not None and values.monto_bs is None:
            values.monto_bs = float(Decimal(str(values.monto_usd)) * tasa_decimal)
        elif values.monto_bs is not None and values.monto_usd is None:
            values.monto_usd = float(Decimal(str(values.monto_bs)) / tasa_decimal)
        elif values.monto_usd is None and values.monto_bs is None:
            raise ValueError("Debe proporcionar al menos un monto (USD o Bs)")

        values.tasa_cambio = float(tasa_decimal)
        values.fecha_tasa_bcv = fecha_tasa

        if values.saldo_pendiente is None and values.monto_usd is not None:
            values.saldo_pendiente = values.monto_usd

        return values


# ==========================
# ---- GASTOS FIJOS --------
# ==========================


class GastoFijoCreate(GastoBase):
    id_apartamento: Optional[int] = None


class GastoFijoOut(GastoBase):
    id: int
    id_apartamento: Optional[int] = None
    monto_pagado: Optional[float] = None
    saldo_pendiente: Optional[float] = None

    class Config:
        from_attributes = True


# ==========================
# ---- GASTOS VARIABLES ----
# ==========================


class GastoVariableCreate(GastoBase):
    id_residente: Optional[int] = None
    id_apartamentos: Optional[List[int]] = None  # para relación M-M
    id_pisos: Optional[List[int]] = None
    id_torres: Optional[List[int]] = None


class GastoVariableOut(GastoBase):
    id: int
    id_residente: Optional[int] = None
    apartamentos: Optional[List[int]] = None  # lista de IDs asociados
    monto_pagado: Optional[float] = None
    saldo_pendiente: Optional[float] = None

    class Config:
        from_attributes = True
