from pydantic import BaseModel, field_validator, model_validator, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from ..utils.tasa_bcv import obtener_tasa_historica_bcv


# ======================
# ---- GASTO BASE ------
# ======================


class GastoBase(BaseModel):
    # Agregar fecha_creacion que se usa en el validator
    fecha_creacion: Optional[date] = None
    tipo_gasto: str
    descripcion: Optional[str] = None
    responsable: str
    monto_usd: Optional[float] = None
    monto_bs: Optional[float] = None
    tasa_cambio: Optional[float] = None
    fecha_tasa_bcv: Optional[datetime] = None
    id_reporte_financiero: Optional[int] = None
    monto_pagado: float = 0.0  # Cambiado a no-optional con valor por defecto
    saldo_pendiente: Optional[float] = None

    # --- Validaciones de contenido ---
    @field_validator("tipo_gasto", "responsable")
    def no_vacio(cls, v, field):
        if not v or not v.strip():
            raise ValueError(f"El campo '{field.name}' no puede estar vacío.")
        return v.strip()

    @field_validator("monto_usd", "monto_bs", "monto_pagado")
    def validar_montos(cls, v, field):
        if v is not None:
            if v < 0:
                raise ValueError(f"El {field.name} no puede ser negativo.")
            if field.name != "monto_pagado" and v == 0:
                raise ValueError(f"El {field.name} debe ser mayor que 0.")
        return v

    @field_validator("monto_usd", "monto_bs", "monto_pagado", mode="before")
    def redondear_montos(cls, v):
        """Redondear a 2 decimales para consistencia con la BD"""
        if v is not None:
            return float(Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        return v

    # --- Cálculos automáticos con tasa BCV ---
    @model_validator(mode="after")
    def calcular_tasas_automaticas(cls, values):
        # fecha_creacion ahora existe
        fecha_gasto = values.fecha_creacion or date.today()

        try:
            tasa, fecha_tasa = obtener_tasa_historica_bcv(fecha_gasto)
            tasa_decimal = Decimal(str(tasa))
        except Exception as e:
            raise ValueError(f"Error al obtener tasa BCV para la fecha {fecha_gasto}: {str(e)}")

        # Validar que tenemos al menos un monto
        if values.monto_usd is None and values.monto_bs is None:
            raise ValueError("Debe proporcionar al menos un monto (USD o Bs)")

        # Calcular montos faltantes
        if values.monto_usd is not None and values.monto_bs is None:
            values.monto_bs = float(Decimal(str(values.monto_usd)) * tasa_decimal)
        elif values.monto_bs is not None and values.monto_usd is None:
            values.monto_usd = float(Decimal(str(values.monto_bs)) / tasa_decimal)

        # Redondear montos
        if values.monto_usd is not None:
            values.monto_usd = float(Decimal(str(values.monto_usd)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        if values.monto_bs is not None:
            values.monto_bs = float(Decimal(str(values.monto_bs)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

        values.tasa_cambio = float(tasa_decimal)
        values.fecha_tasa_bcv = fecha_tasa

        # Cálculo correcto de saldo pendiente
        if values.saldo_pendiente is None and values.monto_usd is not None:
            values.saldo_pendiente = values.monto_usd - (values.monto_pagado or 0)

        # Validar que monto_pagado no sea mayor que monto_usd
        if values.monto_usd is not None and values.monto_pagado > values.monto_usd:
            raise ValueError("El monto pagado no puede ser mayor que el monto total")

        return values

    model_config = ConfigDict(from_attributes=True)


# ==========================
# ---- GASTOS FIJOS --------
# ==========================


class GastoFijoCreate(GastoBase):
    id_apartamento: Optional[int] = None

    @model_validator(mode="after")
    def validar_apartamento_requerido_si_no_general(cls, values):
        """Validar que si no es gasto general, tenga apartamento"""
        if values.id_apartamento is None:
            # Es gasto general que se distribuirá
            pass
        return values


class GastoFijoOut(GastoBase):
    id: int
    id_apartamento: Optional[int] = None
    # Consistencia con GastoBase
    monto_pagado: float = 0.0
    saldo_pendiente: float

    model_config = ConfigDict(from_attributes=True)


# ==========================
# ---- GASTOS VARIABLES ----
# ==========================


class GastoVariableCreate(GastoBase):
    id_residente: Optional[int] = None
    id_apartamentos: Optional[List[int]] = None
    id_pisos: Optional[List[int]] = None
    id_torres: Optional[List[int]] = None

    @model_validator(mode="after")
    def validar_alcance_gasto(cls, values):
        """Validar que se especifique alcance del gasto (apartamentos, pisos o torres)"""
        apartamentos = values.id_apartamentos or []
        pisos = values.id_pisos or []
        torres = values.id_torres or []

        if not any([apartamentos, pisos, torres]):
            raise ValueError("Debe especificar apartamentos, pisos o torres para el gasto variable")

        return values


class GastoVariableOut(GastoBase):
    id: int
    id_residente: Optional[int] = None
    apartamentos: Optional[List[int]] = None
    # Consistencia con GastoBase
    monto_pagado: float = 0.0
    saldo_pendiente: float

    model_config = ConfigDict(from_attributes=True)


# ==========================
# ---- SCHEMAS ADICIONALES ----
# ==========================


class ResumenGastoOut(BaseModel):
    """Schema para respuestas de resumen"""

    id: int
    tipo_gasto: str
    descripcion: Optional[str] = None
    monto_total: float
    monto_pagado: float
    saldo_pendiente: float
    fecha_creacion: date
    completado: bool

    model_config = ConfigDict(from_attributes=True)
