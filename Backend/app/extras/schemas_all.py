from pydantic import (
    BaseModel,
    field_validator,
)
from typing import Optional, Literal


# ======================
# ---- Apartamentos ----
# ======================


class ApartamentoBase(BaseModel):
    numero: Optional[str]
    id_piso: Optional[int]
    id_tipo_apartamento: Optional[int]
    id_residente: Optional[int]
    estado: Optional[Literal["Disponible", "Ocupado"]] = "Disponible"

    @field_validator("porcentaje_aporte")
    def validar_porcentaje(cls, v):
        if v is not None and (v <= 0 or v > 100):
            raise ValueError("El porcentaje_aporte debe ser mayor a 0 y menor o igual a 100")
        return v


class ApartamentoCreate(ApartamentoBase):
    numero: str
    id_piso: int
    id_tipo_apartamento: int


class ApartamentoUpdate(ApartamentoBase):
    pass


class ApartamentoOut(ApartamentoBase):
    id: int

    piso: Optional["PisoOut"] = None
    tipo_apartamento: Optional["TipoApartamentoOut"] = None

    class Config:
        from_attributes = True


# =====================
# ---- Torres ---------
# =====================


class TorreBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    direccion: Optional[str] = None


class TorreCreate(TorreBase):
    pass


class TorreOut(TorreBase):
    id: int

    class Config:
        from_attributes = True


# =====================
# ---- Pisos ----------
# =====================


class PisoBase(BaseModel):
    numero: int
    id_torre: int
    descripcion: Optional[str] = None


class PisoCreate(PisoBase):
    pass


class PisoOut(PisoBase):
    id: int
    torre: Optional[TorreOut] = None  # Relación opcional

    class Config:
        from_attributes = True


# ===============================
# ---- Tipos de Apartamentos ----
# ===============================


class TipoApartamentoBase(BaseModel):
    nombre: str
    habitaciones: int
    banos: int
    descripcion: Optional[str] = None
    porcentaje_aporte: float

    @field_validator("porcentaje_aporte")
    def validar_porcentaje(cls, v):
        if v <= 0 or v > 100:
            raise ValueError("El porcentaje_aporte debe ser mayor a 0 y menor o igual a 100")
        return v


class TipoApartamentoCreate(TipoApartamentoBase):
    pass


class TipoApartamentoOut(TipoApartamentoBase):
    id: int

    class Config:
        from_attributes = True


# ===================
# ---- Auditoria ----
# ===================


class AuditoriaCreate(BaseModel):
    id_usuario: int
    accion: str
    tabla_afectada: Optional[str] = None
    detalle: Optional[str] = None


class AuditoriaOut(AuditoriaCreate):
    id: int
    fecha: datetime  # fecha y hora exacta

    class Config:
        from_attributes = True


from pydantic import (
    BaseModel,
    field_validator,
)
from typing import Optional
from datetime import date


# ======================
# ---- Gastos Fijos ----
# ======================


class GastoBase(BaseModel):
    tipo_gasto: str
    monto: float
    descripcion: Optional[str] = None
    responsable: str
    id_reporte_financiero: Optional[int] = None
    id_apartamento: Optional[int] = None

    @field_validator("monto")
    def validar_monto(cls, v):
        if v <= 0:
            raise ValueError("El monto debe ser mayor a 0")
        return v


class GastoFijoCreate(GastoBase): ...


class GastoFijoOut(GastoBase):
    id: int
    fecha_creacion: date

    class Config:
        from_attributes = True


# ==========================
# ---- Gastos Variables ----
# ==========================


class GastoVariableCreate(GastoBase): ...


class GastoVariableOut(GastoBase):
    id: int
    fecha_creacion: date

    class Config:
        from_attributes = True


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


from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import date

# ----- Literales -----

EstadoPago = Literal["Pendiente", "Validado", "Rechazado"]
MonedaPago = Literal["USD", "VES"]

# ===============
# ---- Pagos ----
# ===============


class PagoBase(BaseModel):
    monto: Optional[float] = None
    moneda: Optional[MonedaPago] = None
    tipo_cambio_bcv: Optional[float] = None
    fecha_pago: Optional[date] = None
    concepto: Optional[str] = None
    metodo: Optional[str] = None
    comprobante: Optional[str] = None
    estado: Optional[EstadoPago] = "Pendiente"
    verificado: Optional[bool] = False
    id_apartamento: Optional[int] = None
    id_reporte_financiero: Optional[int] = None

    # ----- Validaciones -----
    @field_validator("monto")
    def monto_positivo(cls, v):
        if v is not None and v <= 0:
            raise ValueError("El monto debe ser mayor a 0")
        return v

    @field_validator("tipo_cambio_bcv", mode="before")
    def cambio_si_ves(cls, v, info):
        moneda = info.data.get("moneda")
        if moneda == "VES" and (v is None or v <= 0):
            raise ValueError("Debe especificar tipo_cambio_bcv mayor a 0 para pagos en VES")
        return v

    @field_validator("fecha_pago")
    def fecha_valida(cls, v):
        if v is not None and v > date.today():
            raise ValueError("La fecha de pago no puede ser futura")
        return v


class PagoCreate(PagoBase):
    id_residente: int
    monto: float
    moneda: MonedaPago
    fecha_pago: date
    concepto: str
    metodo: str


class PagoUpdate(PagoBase):
    id_residente: Optional[int] = None


class PagoOut(PagoBase):
    id: int
    id_residente: int
    fecha_creacion: Optional[date]

    class Config:
        from_attributes = True


from pydantic import BaseModel, model_validator, field_validator
from pydantic.types import condecimal
from typing import Optional, Annotated
from datetime import date
from decimal import Decimal


# ==============================
# ---- Reportes Financieros ----
# ==============================


class ReporteFinancieroCreate(BaseModel):
    periodo: str
    total_gastos_fijos: Annotated[Decimal, condecimal(max_digits=10, decimal_places=2, ge=0)]
    total_gastos_variables: Annotated[Decimal, condecimal(max_digits=10, decimal_places=2, ge=0)]
    generado_por: str
    total_general: Optional[Annotated[Decimal, condecimal(max_digits=10, decimal_places=2, ge=0)]] = None

    # Calcula automáticamente el total_general si no se envía
    @model_validator(mode="after")
    def calcular_total_general(self):
        if self.total_general is None:
            self.total_general = self.total_gastos_fijos + self.total_gastos_variables
        return self

    @field_validator("periodo")
    def validar_periodo(cls, v):
        if not v.strip():
            raise ValueError("El periodo no puede estar vacío")
        return v


class ReporteFinancieroUpdate(BaseModel):
    total_gastos_fijos: Optional[Annotated[Decimal, condecimal(max_digits=10, decimal_places=2, ge=0)]] = None
    total_gastos_variables: Optional[Annotated[Decimal, condecimal(max_digits=10, decimal_places=2, ge=0)]] = None
    total_general: Optional[Annotated[Decimal, condecimal(max_digits=10, decimal_places=2, ge=0)]] = None


class ReporteFinancieroOut(BaseModel):
    id: int
    periodo: str
    total_gastos_fijos: Decimal
    total_gastos_variables: Decimal
    total_general: Decimal
    generado_por: str
    fecha_generacion: date

    class Config:
        from_attributes = True


from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date, time
from enum import Enum


class EstadoReserva(str, Enum):
    Activa = "Activa"
    Cancelada = "Cancelada"
    Finalizada = "Finalizada"


# ==================
# ---- Reservas ----
# ==================


class ReservaBase(BaseModel):
    id_residente: int
    area: str
    fecha_reserva: date
    hora_inicio: time
    hora_fin: time
    numero_personas: int = 1
    notas: Optional[str] = None

    @field_validator("hora_fin")
    def validar_hora_fin(cls, v, values):
        if "hora_inicio" in values and v <= values["hora_inicio"]:
            raise ValueError("La hora de fin debe ser posterior a la hora de inicio")
        return v


class ReservaCreate(ReservaBase):
    pass


class ReservaUpdate(BaseModel):
    area: Optional[str]
    fecha_reserva: Optional[date]
    hora_inicio: Optional[time]
    hora_fin: Optional[time]
    estado: Optional[EstadoReserva]
    numero_personas: Optional[int]
    notas: Optional[str]

    @field_validator("hora_fin")
    def validar_hora_fin(cls, v, values):
        if "hora_inicio" in values and v is not None and values.get("hora_inicio") and v <= values["hora_inicio"]:
            raise ValueError("La hora de fin debe ser posterior a la hora de inicio")
        return v


class ReservaOut(ReservaBase):
    id: int
    estado: EstadoReserva

    class Config:
        from_attributes = True


from pydantic import (
    BaseModel,
    EmailStr,
    Field,
)
from typing import Optional, Literal
from datetime import date


# ====================
# ---- Residentes ----
# ====================


class ResidenteBase(BaseModel):
    tipo_residente: Optional[Literal["Propietario", "Inquilino"]] = None
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    cedula: Optional[str] = Field(None, min_length=5, max_length=15)
    telefono: Optional[str] = Field(None, max_length=20)
    correo: Optional[EmailStr] = None
    id_apartamento: Optional[int] = None
    id_usuario: Optional[int] = None
    residente_actual: Optional[bool] = None
    estado: Optional[Literal["Activo", "Inactivo", "Suspendido"]] = None


class ResidenteCreate(ResidenteBase):
    tipo_residente: Literal["Propietario", "Inquilino"]
    nombre: str
    cedula: str


class ResidenteUpdate(ResidenteBase):
    pass


class ResidenteOut(ResidenteBase):
    id: int
    fecha_registro: date

    class Config:
        from_attributes = True


from pydantic import (
    BaseModel,
)
from typing import Optional

# ===============
# ---- Roles ----
# ===============


class RolCreate(BaseModel):
    nombre: str
    permisos: Optional[dict[str, list[str]]] = {}
    descripcion: Optional[str] = None


class RolOut(BaseModel):
    id: int
    nombre: str
    permisos: Optional[dict[str, list[str]]]
    descripcion: Optional[str]

    class Config:
        from_attributes = True


from pydantic import (
    BaseModel,
    field_validator,
    EmailStr,
)
from typing import Optional
from datetime import datetime, date

# ==================
# ---- Usuario ----
# ==================


class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    id_rol: Optional[int] = 2  # "Administrador" tiene id = 1, "Residente" tiene id = 2,
    estado: Optional[str] = "Activo"  # Es opcional y por defecto "Activo"
    fecha_creacion: Optional[date] = None
    ultima_sesion: Optional[datetime] = None  # Es opcional, porque el usuario puede no haber iniciado sesión aún.
    ultimo_ip: Optional[str] = None


class UsuarioOut(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    id_rol: int
    estado: str
    fecha_creacion: Optional[date] = None
    ultima_sesion: Optional[datetime] = None

    class Config:
        from_attributes = True  # Lee los objetos directamente y los convierte en JSON

    @field_validator("fecha_creacion", "ultima_sesion", mode="before")
    def solo_fecha(cls, v):  # Permite mostrar la fecha sin la hora
        if isinstance(v, (datetime, date)):
            return v.strftime("%Y-%m-%d")
        return v
