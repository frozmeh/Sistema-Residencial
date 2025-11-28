# schemas/financiero.py
from pydantic import BaseModel, validator
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum
from ..models.financiero import TipoGastoEnum, EstadoGastoEnum
from ..schemas.torres import ApartamentoOut
import json
from typing import Dict, Any

# ======================
# ---- Schemas Tasa Cambio ----
# ======================


class TasaCambioBase(BaseModel):
    fecha: date
    tasa_usd_ves: Decimal
    fuente: str = "BCV"
    es_historica: bool = False


class TasaCambioCreate(TasaCambioBase):
    pass


class TasaCambioResponse(TasaCambioBase):
    id: int
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ======================
# ---- Schemas Gasto ----
# ======================


class GastoBase(BaseModel):
    tipo_gasto: str  # "Fijo" o "Variable"
    descripcion: str
    monto_total_usd: Decimal
    monto_total_ves: Decimal
    tasa_cambio: Decimal
    fecha_gasto: date
    fecha_tasa_bcv: date
    responsable: str
    id_reporte_financiero: Optional[int] = None
    periodo: str  # 🆕 Añadido periodo aquí
    criterio_seleccion: str  # 🆕 AGREGAR este campo
    parametros_criterio: Optional[str] = None


class GastoCreate(GastoBase):
    # Para creación, los montos pueden venir en una sola moneda
    monto_usd: Optional[Decimal] = None
    monto_ves: Optional[Decimal] = None

    @validator("monto_usd", "monto_ves")
    def validar_montos(cls, v, values):
        if v is None and values.get("monto_ves") is None and values.get("monto_usd") is None:
            raise ValueError("Debe proporcionar monto_usd o monto_ves")
        return v


class GastoResponse(GastoBase):
    id: int
    estado: str
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    distribuciones: List["DistribucionGastoResponse"] = []  # 🆕 Añadir distribuciones

    # 🆕 AGREGAR propiedad computada para parámetros
    @property
    def parametros(self) -> Optional[Dict[str, Any]]:
        """Devuelve los parámetros como diccionario"""
        if self.parametros_criterio:
            return json.loads(self.parametros_criterio)
        return None

    class Config:
        from_attributes = True


# ======================
# ---- Schemas Distribucion Gasto ----
# ======================


class DistribucionGastoBase(BaseModel):
    id_apartamento: int
    monto_asignado_usd: Decimal
    monto_asignado_ves: Decimal
    porcentaje_aplicado: Decimal


class DistribucionGastoCreate(DistribucionGastoBase):
    id_gasto: int  # Para crear distribuciones específicas


class DistribucionGastoResponse(DistribucionGastoBase):
    id: int
    id_gasto: int
    fecha_creacion: datetime
    apartamento: Optional[ApartamentoOut] = None

    class Config:
        from_attributes = True


# ======================
# ---- Schemas Cargo ----
# ======================


class CargoBase(BaseModel):
    id_apartamento: int
    id_gasto: int
    descripcion: str
    monto_usd: Decimal
    monto_ves: Decimal
    saldo_pendiente_usd: Decimal
    saldo_pendiente_ves: Decimal
    fecha_vencimiento: date


class CargoCreate(CargoBase):
    pass


class CargoResponse(CargoBase):
    id: int
    estado: str
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    apartamento: Optional[ApartamentoOut] = None
    gasto: Optional[GastoResponse] = None

    class Config:
        from_attributes = True


# ======================
# ---- Schemas Reporte Financiero ----
# ======================


class ReporteFinancieroBase(BaseModel):
    periodo: str
    generado_por: str


class ReporteFinancieroCreate(ReporteFinancieroBase):
    pass


class ReporteFinancieroResponse(ReporteFinancieroBase):
    id: int
    total_ingresos_usd: Decimal
    total_gastos_usd: Decimal
    saldo_final_usd: Decimal
    total_ingresos_ves: Decimal
    total_gastos_ves: Decimal
    saldo_final_ves: Decimal
    tasa_cambio_promedio: Optional[Decimal]
    fecha_generacion: datetime
    fecha_cierre: Optional[datetime]
    estado: str

    class Config:
        from_attributes = True


# ======================
# ---- Schemas para Cálculos de Distribución ----
# ======================


class CalculoDistribucionRequest(BaseModel):
    """Para calcular distribución sin guardar aún"""

    monto_total_usd: Decimal
    apartamentos_ids: List[int]
    forzar_distribucion_equitativa: bool = False  # Si True, ignora porcentajes


class ResumenDistribucion(BaseModel):
    """Resumen del cálculo completo"""

    monto_total_usd: Decimal
    monto_total_ves: Decimal
    total_apartamentos: int


# ======================
# ---- Schemas para Porcentajes de Aporte ----
# ======================


class PorcentajeAporteBase(BaseModel):
    tipo_apartamento: str  # "1hab", "2hab", "3hab"
    porcentaje_aporte: Decimal


class PorcentajeAporteUpdate(BaseModel):
    porcentaje_aporte: Decimal


class PorcentajeAporteResponse(PorcentajeAporteBase):
    id: int
    descripcion: Optional[str] = None

    class Config:
        from_attributes = True


# ======================
# ---- Schemas para Flujos Complejos ----
# ======================


class CriterioSeleccion(str, Enum):
    TODAS_TORRES = "todas_torres"
    TORRE_ESPECIFICA = "torre_especifica"
    PISO_ESPECIFICO = "piso_especifico"
    APARTAMENTOS_ESPECIFICOS = "apartamentos_especificos"


class ParametrosCriterio(BaseModel):
    """Schema para parámetros del criterio de selección"""

    torre_id: Optional[int] = None
    piso: Optional[int] = None
    apartamentos_ids: Optional[List[int]] = None


class GastoCompletoCreate(BaseModel):
    """Para crear gasto + distribución automática"""

    # Mantener tus campos existentes pero agregar criterios
    monto_usd: Decimal
    descripcion: str
    tipo_gasto: TipoGastoEnum
    fecha_gasto: date
    responsable: str = None

    # Criterios de selección (nuevo)
    criterio_seleccion: CriterioSeleccion
    torre_id: Optional[int] = None
    piso: Optional[int] = None
    apartamentos_ids: Optional[List[int]] = None
    forzar_distribucion_equitativa: bool = False

    def obtener_parametros_json(self) -> Optional[str]:
        """Convierte parámetros a JSON para guardar en BD"""
        parametros = {}
        if self.torre_id is not None:
            parametros["torre_id"] = self.torre_id
        if self.piso is not None:
            parametros["piso"] = self.piso
        if self.apartamentos_ids:
            parametros["apartamentos_ids"] = self.apartamentos_ids

        return json.dumps(parametros) if parametros else None

    @validator("torre_id")
    def validar_torre_id(cls, v, values):
        criterio = values.get("criterio_seleccion")
        if criterio in [CriterioSeleccion.TORRE_ESPECIFICA, CriterioSeleccion.PISO_ESPECIFICO] and v is None:
            raise ValueError("torre_id es requerido para este criterio de selección")
        return v

    @validator("piso")
    def validar_piso(cls, v, values):
        criterio = values.get("criterio_seleccion")
        if criterio == CriterioSeleccion.PISO_ESPECIFICO and v is None:
            raise ValueError("piso es requerido para criterio piso_especifico")
        return v

    @validator("apartamentos_ids")
    def validar_apartamentos_ids(cls, v, values):
        criterio = values.get("criterio_seleccion")
        if criterio == CriterioSeleccion.APARTAMENTOS_ESPECIFICOS and (not v or len(v) == 0):
            raise ValueError("apartamentos_ids es requerido para criterio apartamentos_especificos")
        return v


class GastoConDistribucionCreate(BaseModel):
    """Para crear gasto + distribución en una sola operación"""

    gasto: GastoCreate
    apartamentos_ids: List[int]
    calcular_distribucion_automatica: bool = True
    forzar_equitativa: bool = False


class GastoConDistribucionResponse(BaseModel):
    """Respuesta con gasto creado + sus distribuciones"""

    gasto: GastoResponse
    resumen: ResumenDistribucion


class PagoCargoCreate(BaseModel):
    """Para que el propietario registre un pago"""

    id_cargo: int
    id_residente: int
    monto_pagado_usd: Decimal
    monto_pagado_ves: Decimal
    tasa_cambio_pago: Decimal
    metodo_pago: str
    referencia: Optional[str] = None
    comprobante_url: Optional[str] = None
    fecha_pago: date
    concepto: str  # 🆕 Corregido typo: "conncepto" → "concepto"


class ValidarPagoRequest(BaseModel):
    """Para que el administrador valide un pago"""

    accion: str  # "completo", "parcial", "rechazado"
    observaciones: Optional[str] = None


# ======================
# ---- Schemas para Filtros ----
# ======================


class GastoFilter(BaseModel):
    tipo_gasto: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    responsable: Optional[str] = None


class CargoFilter(BaseModel):
    id_apartamento: Optional[int] = None
    estado: Optional[str] = None
    fecha_vencimiento_inicio: Optional[date] = None
    fecha_vencimiento_fin: Optional[date] = None


class DistribucionFilter(BaseModel):
    id_gasto: Optional[int] = None
    id_apartamento: Optional[int] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
