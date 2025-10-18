from pydantic import (
    BaseModel,
    field_validator,
)  # Para definir tipos de datos y validaciones, también para configurar valores por defecto
from typing import Optional  # Para campos None (opcional)
from datetime import datetime, date  # Fecha y hora
from sqlalchemy import (
    func,
)  # Genera valores por defecto como la fecha actual en la DB (func.now)

# Create = POST, Update = PUT, Out = GET


# ---- Usuarios ----
class UsuarioCreate(BaseModel):
    nombre: str
    email: str
    password: str
    id_rol: Optional[int] = 2  # "Administrador" tiene id = 1, "Residente" tiene id = 2,
    estado: Optional[str] = "Activo"  # Es opcional y por defecto "Activo"
    fecha_creacion: Optional[date] = None
    ultima_sesion: Optional[datetime] = (
        None  # Es opcional, porque el usuario puede no haber iniciado sesión aún.
    )
    ultimo_ip: Optional[str] = None


class UsuarioOut(BaseModel):
    id: int
    nombre: str
    email: str
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


# ---- Roles ----
class RolCreate(BaseModel):
    nombre: str
    permisos: Optional[dict] = None
    descripcion: Optional[str] = None


class RolOut(BaseModel):
    id: int
    nombre: str
    permisos: Optional[dict]
    descripcion: Optional[str]

    class Config:
        from_attributes = True


# ---- Residentes ----
class ResidenteCreate(BaseModel):
    tipo_residente: str
    nombre: str
    cedula: str
    telefono: str | None = None
    correo: str | None = None
    id_apartamento: Optional[int] = None
    id_usuario: int


class ResidenteUpdate(BaseModel):
    tipo_residente: Optional[str] = None
    nombre: Optional[str] = None
    cedula: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    id_apartamento: Optional[int] = None
    id_usuario: Optional[int] = None


class ResidenteOut(BaseModel):
    id: int
    tipo_residente: str
    nombre: str
    cedula: str
    telefono: Optional[str] = None
    correo: Optional[str] = None
    id_apartamento: Optional[int] = None
    id_usuario: Optional[int] = None
    estado: Optional[str] = None

    class Config:
        from_attributes = True


# ---- Apartamentos ----
class ApartamentoCreate(BaseModel):
    numero: str
    torre: str
    piso: int
    tipo_apartamento: str
    porcentaje_aporte: float
    id_residente: Optional[int] = None
    estado: Optional[str] = "Disponible"


class ApartamentoUpdate(BaseModel):
    numero: Optional[str]
    torre: Optional[str]
    piso: Optional[int]
    tipo_apartamento: Optional[str]
    porcentaje_aporte: Optional[float]
    id_residente: Optional[int]
    estado: Optional[str]


class ApartamentoOut(BaseModel):
    id: int
    numero: str
    torre: str
    piso: int
    tipo_apartamento: str
    porcentaje_aporte: float
    id_residente: Optional[int]
    estado: str

    class Config:
        from_attributes = True


# ---- Pagos ----
class PagoCreate(BaseModel):
    id_residente: int
    monto: float
    moneda: str
    tipo_cambio_bcv: Optional[float] = None
    fecha_pago: date
    concepto: str
    metodo: str
    comprobante: Optional[str] = None
    estado: Optional[str] = "Pendiente"
    verificado: Optional[bool] = False


class PagoUpdate(BaseModel):
    monto: Optional[float] = None
    moneda: Optional[str] = None
    tipo_cambio_bcv: Optional[float] = None
    fecha_pago: Optional[date] = None
    concepto: Optional[str] = None
    metodo: Optional[str] = None
    comprobante: Optional[str] = None
    estado: Optional[str] = None
    verificado: Optional[bool] = None


class PagoOut(PagoCreate):
    id: int
    fecha_creacion: Optional[date]

    class Config:
        from_attributes = True


# ---- Gastos Fijos ----
class GastoFijoCreate(BaseModel):
    tipo: str
    monto: float
    descripcion: Optional[str] = None
    responsable: str


class GastoFijoOut(GastoFijoCreate):
    id: int
    fecha_registro: date

    class Config:
        from_attributes = True


# ---- Gastos Variables ----
class GastoVariableCreate(BaseModel):
    tipo: str
    monto: float
    descripcion: Optional[str] = None
    responsable: str


class GastoVariableOut(GastoVariableCreate):
    id: int
    fecha_registro: date

    class Config:
        from_attributes = True


from pydantic import BaseModel
from typing import Optional
from datetime import date


# ---- Incidencia ----
class IncidenciaCreate(BaseModel):
    id_residente: int
    tipo: str
    descripcion: str
    prioridad: Optional[str] = "Media"


class IncidenciaUpdate(BaseModel):
    tipo: Optional[str]
    descripcion: Optional[str]
    estado: Optional[str]
    prioridad: Optional[str]
    respuesta_admin: Optional[str]


class IncidenciaOut(IncidenciaCreate):
    id: int
    fecha_reporte: date
    estado: str
    respuesta_admin: Optional[str]

    class Config:
        from_attributes = True


# ---- Reserva ----
class ReservaCreate(BaseModel):
    id_residente: int
    area: str
    fecha_reserva: date
    hora_inicio: str
    hora_fin: str
    numero_personas: int
    notas: Optional[str] = None


class ReservaUpdate(BaseModel):
    area: Optional[str]
    fecha_reserva: Optional[date]
    hora_inicio: Optional[str]
    hora_fin: Optional[str]
    estado: Optional[str]
    numero_personas: Optional[int]
    notas: Optional[str]


class ReservaOut(ReservaCreate):
    id: int
    estado: str

    class Config:
        from_attributes = True


# ---- Notificación ----
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


# ---- Auditoría ----
class AuditoriaCreate(BaseModel):
    id_usuario: int
    accion: str
    tabla_afectada: Optional[str] = None
    detalle: Optional[str] = None


class AuditoriaOut(AuditoriaCreate):
    id: int
    fecha: date

    class Config:
        from_attributes = True


# ---- Reporte Financiero ----
class ReporteFinancieroCreate(BaseModel):
    periodo: str
    total_gastos_fijos: float
    total_gastos_variables: float
    total_general: float
    generado_por: str


class ReporteFinancieroUpdate(BaseModel):
    total_gastos_fijos: Optional[float]
    total_gastos_variables: Optional[float]
    total_general: Optional[float]


class ReporteFinancieroOut(ReporteFinancieroCreate):
    id: int
    fecha_generacion: date

    class Config:
        from_attributes = True
