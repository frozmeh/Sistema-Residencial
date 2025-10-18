from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

# Esquema para crear usuario
class UsuarioCreate(BaseModel):
    nombre_usuario: str
    contraseña: str
    correo: EmailStr
    id_rol: int
    estado: Optional[bool] = True
    fecha_creacion: Optional[date] = None

# Esquema para actualizar usuario
class UsuarioUpdate(BaseModel):
    nombre_usuario: Optional[str] = None
    contraseña: Optional[str] = None
    correo: Optional[EmailStr] = None
    id_rol: Optional[int] = None
    estado: Optional[bool] = None

# Esquema para mostrar usuario
class UsuarioOut(BaseModel):
    id_usuario: int
    nombre_usuario: str
    correo: EmailStr
    id_rol: int
    estado: bool

    class Config:
        orm_mode = True  # Permite devolver objetos SQLAlchemy

# Rol
class RolCreate(BaseModel):
    nombre_rol: str
    permisos: Optional[str] = None
    descripcion: Optional[str] = None

class RolUpdate(BaseModel):
    nombre_rol: Optional[str] = None
    permisos: Optional[str] = None
    descripcion: Optional[str] = None

class RolOut(BaseModel):
    id_rol: int
    nombre_rol: str
    permisos: Optional[str]
    descripcion: Optional[str]

    class Config:
        orm_mode = True

# Residente
class ResidenteCreate(BaseModel):
    tipo_residente: str
    nombre: str
    cedula: str
    telefono: Optional[str] = None
    correo: EmailStr
    id_apartamento: Optional[int] = None
    id_usuario: int
    fecha_registro: Optional[date] = None
    estado: Optional[str] = "Activo"

class ResidenteUpdate(BaseModel):
    tipo_residente: Optional[str] = None
    nombre: Optional[str] = None
    cedula: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[EmailStr] = None
    id_apartamento: Optional[int] = None
    id_usuario: Optional[int] = None
    fecha_registro: Optional[date] = None
    estado: Optional[str] = None

class ResidenteOut(BaseModel):
    id_residente: int
    tipo_residente: str
    nombre: str
    cedula: str
    telefono: Optional[str]
    correo: str
    id_apartamento: Optional[int]
    id_usuario: int
    fecha_registro: date
    estado: str

    class Config:
        orm_mode = True

class ApartamentoCreate(BaseModel):
    numero: str
    torre: str
    piso: int
    tipo_apartamento: str
    porcentaje_aporte: float
    estado: Optional[str] = "Disponible"

class ApartamentoUpdate(BaseModel):
    numero: Optional[str] = None
    torre: Optional[str] = None
    piso: Optional[int] = None
    tipo_apartamento: Optional[str] = None
    porcentaje_aporte: Optional[float] = None
    estado: Optional[str] = None

class ApartamentoOut(BaseModel):
    id_apartamento: int
    numero: str
    torre: str
    piso: int
    tipo_apartamento: str
    porcentaje_aporte: float
    estado: str

    class Config:
        orm_mode = True

class PagoCreate(BaseModel):
    id_residente: int
    id_apartamento: Optional[int] = None
    monto: float
    moneda: Optional[str] = "VES"
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

class PagoOut(BaseModel):
    id_pago: int
    id_residente: int
    id_apartamento: Optional[int]
    monto: float
    moneda: str
    tipo_cambio_bcv: Optional[float]
    fecha_pago: date
    concepto: str
    metodo: str
    comprobante: Optional[str]
    estado: str
    fecha_creacion: date
    verificado: bool

    class Config:
        orm_mode = True
        
# Gasto Fijo
class GastoFijoCreate(BaseModel):
    tipo: str
    monto: float
    fecha_registro: date
    descripcion: Optional[str] = None
    responsable: Optional[str] = None

class GastoFijoUpdate(BaseModel):
    tipo: Optional[str] = None
    monto: Optional[float] = None
    fecha_registro: Optional[date] = None
    descripcion: Optional[str] = None
    responsable: Optional[str] = None

class GastoFijoOut(BaseModel):
    id_gasto_fijo: int
    tipo: str
    monto: float
    fecha_registro: date
    descripcion: Optional[str]
    responsable: Optional[str]

    class Config:
        orm_mode = True

# Gasto Variable
class GastoVariableCreate(BaseModel):
    tipo: str
    monto: float
    fecha_registro: date
    descripcion: Optional[str] = None
    responsable: Optional[str] = None

class GastoVariableUpdate(BaseModel):
    tipo: Optional[str] = None
    monto: Optional[float] = None
    fecha_registro: Optional[date] = None
    descripcion: Optional[str] = None
    responsable: Optional[str] = None

class GastoVariableOut(BaseModel):
    id_gasto_variable: int
    tipo: str
    monto: float
    fecha_registro: date
    descripcion: Optional[str]
    responsable: Optional[str]

    class Config:
        orm_mode = True

class ReporteFinancieroCreate(BaseModel):
    periodo: str
    total_gastos_fijos: float
    total_gastos_variables: float
    total_general: float
    generado_por: str
    fecha_generacion: date

class ReporteFinancieroOut(BaseModel):
    id_reporte: int
    periodo: str
    total_gastos_fijos: float
    total_gastos_variables: float
    total_general: float
    generado_por: str
    fecha_generacion: date

    class Config:
        orm_mode = True

class IncidenciaCreate(BaseModel):
    id_residente: int
    tipo: str
    descripcion: str
    fecha_reporte: date
    prioridad: Optional[str] = "Media"

class IncidenciaOut(BaseModel):
    id_incidencia: int
    id_residente: int
    tipo: str
    descripcion: str
    fecha_reporte: date
    estado: str
    prioridad: str
    respuesta_admin: Optional[str]

    class Config:
        orm_mode = True

class ReservaCreate(BaseModel):
    id_residente: int
    area: str
    fecha_reserva: date
    hora_inicio: str
    hora_fin: str
    numero_personas: int
    notas: Optional[str] = None

class ReservaOut(BaseModel):
    id_reserva: int
    id_residente: int
    area: str
    fecha_reserva: date
    hora_inicio: str
    hora_fin: str
    estado: str
    numero_personas: int
    notas: Optional[str]

    class Config:
        orm_mode = True

class NotificacionCreate(BaseModel):
    id_usuario: int
    mensaje: str
    fecha_envio: date
    tipo: str

class NotificacionOut(BaseModel):
    id_notificacion: int
    id_usuario: int
    mensaje: str
    fecha_envio: date
    tipo: str
    leido: bool

    class Config:
        orm_mode = True

class AuditoriaCreate(BaseModel):
    id_usuario: int
    accion: str
    tabla_afectada: str
    fecha: date
    detalle: Optional[str] = None

class AuditoriaOut(BaseModel):
    id_log: int
    id_usuario: int
    accion: str
    tabla_afectada: str
    fecha: date
    detalle: Optional[str]

    class Config:
        orm_mode = True
