# schemas/financiero.py - ACTUALIZA tu schema Pago
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, Literal
from decimal import Decimal
from datetime import datetime, date
from ..schemas.torres import ApartamentoOut
from ..schemas.financiero import CargoResponse, GastoResponse

# ----- Literales -----
EstadoPago = Literal["Pendiente", "Validado", "Rechazado"]
MonedaPago = Literal["USD", "VES"]
MetodoPago = Literal["Transferencia", "Efectivo", "Pago Móvil"]


class PagoCargoCreate(BaseModel):
    """Schema para pagos de cargos - CON SOPORTE PARA USD Y VES"""

    id_cargo: int
    id_residente: int
    monto_pagado: Decimal  # ← Monto en la moneda que elija el usuario
    moneda_pago: Literal["USD", "VES"]  # ← Moneda en la que pagó el usuario
    metodo_pago: str
    referencia: Optional[str] = None
    comprobante_url: Optional[str] = None
    fecha_pago: date
    concepto: str

    @field_validator("monto_pagado")
    def monto_positivo(cls, v):
        if v <= 0:
            raise ValueError("El monto debe ser mayor a 0")
        return v


# ====================
# ---- Esquemas EXISTENTES (modificados) ----
# ====================


class PagoBase(BaseModel):
    monto: Optional[Decimal] = None
    moneda: Optional[MonedaPago] = None
    tipo_cambio_bcv: Optional[Decimal] = None
    fecha_pago: Optional[datetime] = None
    concepto: Optional[str] = None
    metodo: Optional[MetodoPago] = None
    comprobante: Optional[str] = None
    estado: Optional[EstadoPago] = "Pendiente"
    verificado: Optional[bool] = False
    id_apartamento: Optional[int] = None
    id_reporte_financiero: Optional[int] = None
    id_gasto: Optional[int] = None  # 🆕 Cambiar de id_gasto_fijo/id_gasto_variable a id_gasto
    id_cargo: Optional[int] = None  # 🆕 NUEVO campo para el flujo de cargos

    # ----- Validaciones ACTUALIZADAS -----

    @field_validator("monto")
    def monto_positivo(cls, v):
        if v is not None and v <= 0:
            raise ValueError("El monto debe ser mayor a 0")
        return v

    @field_validator("tipo_cambio_bcv", mode="before")
    def cambio_si_ves(cls, v, info):
        moneda = info.data.get("moneda")
        if moneda == "VES":
            if v is None or v <= 0:
                raise ValueError("Debe especificar tipo_cambio_bcv mayor a 0 para pagos en VES")
        elif moneda == "USD" and v is not None:
            raise ValueError("No debe especificar tipo_cambio_bcv para pagos en USD")
        return v

    @field_validator("fecha_pago")
    def fecha_valida(cls, v):
        if v is not None and v > datetime.now():
            raise ValueError("La fecha de pago no puede ser futura")
        return v

    @field_validator("comprobante")
    def comprobante_requerido_para_transferencia(cls, v, info):
        metodo = info.data.get("metodo")
        if metodo == "Transferencia" and not v:
            raise ValueError("Comprobante requerido para pagos por transferencia")
        return v


# ==============================
# ---- CREAR / ACTUALIZAR ----
# ==============================


class PagoCreate(PagoBase):
    id_residente: int
    monto: Decimal
    moneda: MonedaPago
    fecha_pago: datetime
    concepto: str
    metodo: MetodoPago


class PagoUpdate(PagoBase):
    id_residente: Optional[int] = None


# ==============================
# ---- RESPUESTA GENERAL ----
# ==============================


class PagoOut(PagoBase):
    id: int
    id_residente: int
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    # 🆕 AGREGAR relaciones para respuesta completa
    residente: Optional["ResidenteSimple"] = None
    cargo: Optional["CargoResponse"] = None
    apartamento: Optional["ApartamentoOut"] = None
    gasto: Optional["GastoResponse"] = None

    class Config:
        from_attributes = True


# ==============================
# ---- VALIDACIÓN ADMIN ----
# ==============================


class PagoValidacion(BaseModel):
    estado: EstadoPago
    verificado: bool = True


# ==============================
# ---- SCHEMAS ADICIONALES ----
# ==============================


class ValidarPagoRequest(BaseModel):
    """Para que el administrador valide un pago"""

    accion: str  # "completo", "parcial", "rechazado"
    observaciones: Optional[str] = None


class ResidenteSimple(BaseModel):
    """Schema simple para residente en respuestas"""

    id: int
    nombre: str
    cedula: str
    tipo_residente: str

    class Config:
        from_attributes = True
