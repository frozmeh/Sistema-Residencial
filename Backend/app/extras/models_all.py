# ======================
# ---- Apartamentos ----
# ======================

from sqlalchemy import Column, Integer, String, DECIMAL, Enum, CheckConstraint, UniqueConstraint, ForeignKey
from ..database import Base
from sqlalchemy.orm import relationship


class Apartamento(Base):
    __tablename__ = "apartamentos"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String, nullable=False)  # Ej. 1-3
    id_piso = Column(Integer, ForeignKey("pisos.id"), nullable=False)
    id_tipo_apartamento = Column(Integer, ForeignKey("tipos_apartamentos.id"), nullable=False)

    estado = Column(
        Enum("Disponible", "Ocupado", name="estado_apartamento_enum"),
        default="Disponible",
        nullable=False,
    )

    __table_args__ = (UniqueConstraint("numero", "id_piso", name="unique_apartamento_numero_piso"),)

    # Relaciones
    piso = relationship("Piso", back_populates="apartamentos")
    tipo_apartamento = relationship("TipoApartamento", back_populates="apartamentos")
    residente = relationship("Residente", back_populates="apartamento", uselist=False)
    pagos = relationship("Pago", back_populates="apartamento", cascade="all, delete-orphan")
    gastos_fijos = relationship("GastoFijo", back_populates="apartamento")
    gastos_variables = relationship("GastoVariable", back_populates="apartamento")


# ================
# ---- Torres ----
# ================


class Torre(Base):
    __tablename__ = "torres"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)  # Ej: Torre A, Torre B
    descripcion = Column(String, nullable=True)

    pisos = relationship("Piso", back_populates="torre", cascade="all, delete-orphan")


# ================
# ---- Pisos ----
# ================


class Piso(Base):
    __tablename__ = "pisos"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(Integer, nullable=False)  # Ej: 1, 2, 3...
    id_torre = Column(Integer, ForeignKey("torres.id"), nullable=False)
    descripcion = Column(String, nullable=True)

    torre = relationship("Torre", back_populates="pisos")
    apartamentos = relationship("Apartamento", back_populates="piso", cascade="all, delete-orphan")


# ===============================
# ---- Tipos de Apartamentos ----
# ===============================


class TipoApartamento(Base):
    __tablename__ = "tipos_apartamentos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)  # Ej: Tipo A, Tipo B
    habitaciones = Column(Integer, nullable=False)
    banos = Column(Integer, nullable=False)
    descripcion = Column(String, nullable=True)
    porcentaje_aporte = Column(DECIMAL(5, 2), nullable=False)  # Ej. 20.00
    __table_args__ = (
        CheckConstraint("porcentaje_aporte >= 0 AND porcentaje_aporte <= 100", name="check_porcentaje_aporte"),
        UniqueConstraint("numero", "torre", name="unique_apartamento_numero_torre"),
    )

    apartamentos = relationship("Apartamento", back_populates="tipo_apartamento")


from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    func,
)
from ..database import Base
from sqlalchemy.orm import relationship


# ==================================
# ---- Historial de Apartamento ----
# ==================================


class HistorialApartamento(Base):
    __tablename__ = "historial_apartamentos"
    id = Column(Integer, primary_key=True)
    id_apartamento = Column(Integer, ForeignKey("apartamentos.id"), nullable=False)
    id_residente = Column(Integer, ForeignKey("residentes.id"), nullable=False)
    fecha_asignacion = Column(DateTime, default=datetime.utcnow)
    fecha_desasignacion = Column(DateTime, nullable=True)

    apartamento = relationship("Apartamento", back_populates="historiales")
    residente = relationship("Residente", back_populates="historiales")


# ===================
# ---- Auditoria ----
# ===================


class Auditoria(Base):
    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    accion = Column(String(50), nullable=False)
    tabla_afectada = Column(String(50), nullable=True)
    fecha = Column(DateTime, default=func.now())  # Fecha y hora exacta
    detalle = Column(String(255), nullable=True)

    usuario = relationship("Usuario", back_populates="auditorias")


from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    func,
    DECIMAL,
)
from ..database import Base
from sqlalchemy.orm import relationship


# ======================
# ---- Gastos Fijos ----
# ======================


class GastoFijo(Base):
    __tablename__ = "gastos_fijos"

    id = Column(Integer, primary_key=True, index=True)
    id_reporte_financiero = Column(Integer, ForeignKey("reportes_financieros.id"))
    id_apartamento = Column(Integer, ForeignKey("apartamentos.id"))

    tipo_gasto = Column(String, nullable=False)  # Mantenimiento, limpieza, seguridad
    monto = Column(DECIMAL(10, 2), nullable=False)
    fecha_creacion = Column(Date, default=func.current_date())
    descripcion = Column(String, nullable=True)
    responsable = Column(String, nullable=False)

    reporte_financiero = relationship("ReporteFinanciero", back_populates="gastos_fijos")  # en GastoFijo
    apartamento = relationship("Apartamento", back_populates="gastos_fijos")


# ==========================
# ---- Gastos Variables ----
# ==========================


class GastoVariable(Base):
    __tablename__ = "gastos_variables"

    id = Column(Integer, primary_key=True, index=True)
    id_reporte_financiero = Column(Integer, ForeignKey("reportes_financieros.id"))
    id_apartamento = Column(Integer, ForeignKey("apartamentos.id"))
    id_residente = Column(Integer, ForeignKey("residentes.id"), nullable=True)

    tipo_gasto = Column(String, nullable=False)
    monto = Column(DECIMAL(10, 2), nullable=False)
    fecha_creacion = Column(Date, default=func.current_date())
    descripcion = Column(String, nullable=True)
    responsable = Column(String, nullable=False)

    reporte_financiero = relationship("ReporteFinanciero", back_populates="gastos_variables")  # en GastoVariable
    apartamento = relationship("Apartamento", back_populates="gastos_variables")
    residente = relationship("Residente", back_populates="gastos_variables")


from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    func,
)
from ..database import Base
from sqlalchemy.orm import relationship

# =====================
# ---- Incidencias ----
# =====================


class Incidencia(Base):
    __tablename__ = "incidencias"

    id = Column(Integer, primary_key=True, index=True)
    id_residente = Column(Integer, ForeignKey("residentes.id"), nullable=False)
    tipo = Column(String(50), nullable=False)
    descripcion = Column(String(255), nullable=False)
    fecha_reporte = Column(Date, default=func.current_date())
    estado = Column(String(20), default="Abierta")
    prioridad = Column(String(10), default="Media")
    respuesta_admin = Column(String(255), nullable=True)
    id_usuario_admin = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    fecha_atencion = Column(Date, nullable=True)

    # Relaciones
    residente = relationship("Residente", back_populates="incidencias")
    administrador = relationship("Usuario", lazy="joined")  # Relación opcional directa


from sqlalchemy import Column, Integer, String, ForeignKey, Date, func, Boolean, Enum, Text, DateTime
import enum
from ..database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

# ========================
# ---- Notificaciones ----
# ========================


class TipoNotificacion(enum.Enum):
    PAGO = "Pago"
    INCIDENCIA = "Incidencia"
    SISTEMA = "Sistema"
    DOCUMENTO = "Documento"
    RESERVA = "Reserva"


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    mensaje = Column(String, nullable=False)  # O Text() si esperas mensajes largos
    fecha_envio = Column(DateTime(timezone=True), default=func.now())
    tipo = Column(Enum(TipoNotificacion))
    leido = Column(Boolean, default=False)
    url = Column(String, nullable=True)
    prioridad = Column(String, default="Media")
    fecha_leido = Column(DateTime, nullable=True)

    usuario = relationship("Usuario", back_populates="notificaciones")


from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    func,
    DECIMAL,
    Boolean,
)
from ..database import Base
from sqlalchemy.orm import relationship


# ===============
# ---- Pagos ----
# ===============


class Pago(Base):
    __tablename__ = "pagos"

    id = Column(Integer, primary_key=True, index=True)
    id_residente = Column(Integer, ForeignKey("residentes.id"), nullable=False)
    id_apartamento = Column(Integer, ForeignKey("apartamentos.id"))
    id_reporte_financiero = Column(Integer, ForeignKey("reportes_financieros.id"), nullable=True)

    monto = Column(DECIMAL(10, 2), nullable=False)  # Total pagado
    moneda = Column(String, nullable=False)  # USD o VES
    tipo_cambio_bcv = Column(DECIMAL(10, 2), nullable=True)  # Tasa usada si el pago fue en VES
    fecha_pago = Column(Date, nullable=False)  # Fecha del pago
    concepto = Column(String, nullable=False)  # Mantenimiento, reserva...
    metodo = Column(String, nullable=False)  # Transferencia, efectivo...
    comprobante = Column(String, nullable=True)  # Imagen o referencia
    estado = Column(String, default="Pendiente")  # Pendiente / Validado / Rechazado
    fecha_creacion = Column(Date, default=func.current_date())  # Fecha de registro del pago
    verificado = Column(Boolean, default=False)  # Si el pago ha sido validado por el Admin

    # Relaciones
    residente = relationship("Residente", back_populates="pagos")
    apartamento = relationship("Apartamento", back_populates="pagos")
    reporte_financiero = relationship("ReporteFinanciero", back_populates="pagos")


from sqlalchemy import Column, Integer, String, Date, func, DECIMAL, DateTime, UniqueConstraint
from ..database import Base
from sqlalchemy.orm import relationship

# ==============================
# ---- Reportes Financieros ----
# ==============================


class ReporteFinanciero(Base):
    __tablename__ = "reportes_financieros"
    __table_args__ = (UniqueConstraint("periodo", name="uq_reporte_periodo"),)

    id = Column(Integer, primary_key=True, index=True)
    periodo = Column(String, nullable=False)
    total_gastos_fijos = Column(DECIMAL(10, 2), default=0)
    total_gastos_variables = Column(DECIMAL(10, 2), default=0)
    total_general = Column(DECIMAL(10, 2), default=0)
    generado_por = Column(String, nullable=False)
    fecha_generacion = Column(DateTime, default=func.now())

    gastos_fijos = relationship("GastoFijo", back_populates="reporte_financiero", cascade="all, delete-orphan")
    gastos_variables = relationship(
        "GastoVariable",
        back_populates="reporte_financiero",
        cascade="all, delete-orphan",
    )
    pagos = relationship("Pago", back_populates="reporte_financiero", cascade="all, delete-orphan")


from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time, Enum
import enum
from ..database import Base
from sqlalchemy.orm import relationship


# ==================
# ---- Reservas ----
# ==================


class EstadoReserva(enum.Enum):
    Activa = "Activa"
    Cancelada = "Cancelada"
    Finalizada = "Finalizada"


class Reserva(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    id_residente = Column(Integer, ForeignKey("residentes.id"), nullable=False)
    area = Column(String, nullable=False)
    fecha_reserva = Column(Date, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    estado = Column(Enum(EstadoReserva), default=EstadoReserva.Activa, nullable=False)
    numero_personas = Column(Integer, default=1, nullable=False)
    notas = Column(String, nullable=True)

    residente = relationship("Residente", back_populates="reservas")


from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    func,
    Boolean,
    Enum,
)
from ..database import Base
from sqlalchemy.orm import relationship


# ====================
# ---- Residentes ----
# ====================


class Residente(Base):
    __tablename__ = "residentes"  # Nombre de la tabla Residentes en la DB

    id = Column(Integer, primary_key=True, index=True)  # PK
    id_apartamento = Column(Integer, ForeignKey("apartamentos.id"), nullable=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), unique=True)  # Relación con la tabla Usuario

    tipo_residente = Column(
        Enum("Propietario", "Inquilino", name="tipo_residente_enum"), nullable=False
    )  # Propietario o inquilino
    nombre = Column(String, nullable=False)  # Nombre del Propietario / Inquilino
    cedula = Column(String, nullable=False, unique=True)  # Cédula de Identidad
    telefono = Column(String)  # Teléfono de contacto
    correo = Column(String)  # Correo electrónico de contacto
    fecha_registro = Column(Date, default=func.current_date(), nullable=False)  # Fecha de registro del residente
    residente_actual = Column(Boolean, default=True)  # True = residente activo
    estado = Column(
        Enum("Activo", "Inactivo", "Suspendido", name="estado_residente_enum"),
        default="Activo",
        nullable=False,
    )

    # Relaciones
    usuario = relationship("Usuario", back_populates="residente", uselist=False)
    apartamento = relationship("Apartamento", back_populates="residente", uselist=False)
    pagos = relationship("Pago", back_populates="residente", cascade="all, delete-orphan")
    incidencias = relationship("Incidencia", back_populates="residente", cascade="all, delete-orphan")
    reservas = relationship("Reserva", back_populates="residente", cascade="all, delete-orphan")
    gastos_variables = relationship("GastoVariable", back_populates="residente")


from sqlalchemy import (
    Column,
    Integer,
    String,
    JSON,
)
from ..database import Base
from sqlalchemy.orm import relationship


# ===============
# ---- Roles ----
# ===============


class Rol(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)  # Administrador / Residente
    permisos = Column(JSON, nullable=False)  # Acciones por módulo
    descripcion = Column(String, nullable=True)

    # Relaciones
    usuarios = relationship("Usuario", back_populates="rol")


from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Date,
    func,
    Enum,
)
from ..database import Base
from sqlalchemy.orm import relationship


# ==================
# ---- Usuario ----
# ==================


class Usuario(Base):
    __tablename__ = "usuarios"  # Nombre de la tabla Usuario en la DB

    id = Column(Integer, primary_key=True, index=True)  # PK
    nombre = Column(String, unique=True, nullable=False)  # Nombre de Acceso
    email = Column(String, unique=True, nullable=False)  # Correo de contacto y recuperación
    password = Column(String, nullable=False)  # Contraseña encriptada
    id_rol = Column(Integer, ForeignKey("roles.id"))  # FK
    estado = Column(
        Enum("Activo", "Inactivo", "Bloqueado", name="estado_usuario"), default="Activo"
    )  # Activo/Inactivo
    fecha_creacion = Column(Date, default=func.current_date(), nullable=False)  # Fecha de registro del usuario
    ultima_sesion = Column(DateTime, nullable=True)  # Fecha del último acceso
    ultimo_ip = Column(String, nullable=True)
    intentos_fallidos = Column(Integer, default=0)
    fecha_bloqueo = Column(DateTime, nullable=True)

    # Relaciones
    rol = relationship("Rol", back_populates="usuarios")  # Relación con la tabla Roles
    residente = relationship("Residente", back_populates="usuario", uselist=False)
    notificaciones = relationship("Notificacion", back_populates="usuario", cascade="all, delete-orphan")
    incidencias_atendidas = relationship("Incidencia", back_populates="administrador", cascade="all, delete-orphan")
    auditorias = relationship("Auditoria", back_populates="usuario", cascade="all, delete-orphan")
