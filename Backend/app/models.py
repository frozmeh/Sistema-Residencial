#
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Date,
    func,
    DECIMAL,
    Boolean,
    Time,
    Enum,
    JSON,
)
from .database import Base
from sqlalchemy.orm import relationship
from datetime import datetime, date


# ---- Usuarios ----
class Usuario(Base):
    __tablename__ = "usuarios"  # Nombre de la tabla Usuario en la DB

    id = Column(Integer, primary_key=True, index=True)  # PK
    nombre = Column(String, unique=True, nullable=False)  # Nombre de Acceso
    email = Column(
        String, unique=True, nullable=False
    )  # Correo de contacto y recuperación
    password = Column(String, nullable=False)  # Contraseña encriptada
    id_rol = Column(Integer, ForeignKey("roles.id"))  # FK
    estado = Column(
        Enum("Activo", "Inactivo", "Bloqueado", name="estado_usuario"), default="Activo"
    )  # Activo/Inactivo
    fecha_creacion = Column(
        Date, default=func.current_date(), nullable=False
    )  # Fecha de registro del usuario
    ultima_sesion = Column(DateTime, nullable=True)  # Fecha del último acceso
    ultimo_ip = Column(String, nullable=True)
    intentos_fallidos = Column(Integer, default=0)
    fecha_bloqueo = Column(DateTime, nullable=True)

    # Relaciones
    rol = relationship("Rol", back_populates="usuarios")  # Relación con la tabla Roles
    residente = relationship("Residente", back_populates="usuario", uselist=False)
    notificaciones = relationship(
        "Notificacion", back_populates="usuario", cascade="all, delete-orphan"
    )
    incidencias_atendidas = relationship(
        "Incidencia", back_populates="administrador", cascade="all, delete-orphan"
    )
    auditorias = relationship(
        "Auditoria", back_populates="usuario", cascade="all, delete-orphan"
    )


# ---- Roles ----
class Rol(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)  # Administrador / Residente
    permisos = Column(JSON, nullable=False)  # Acciones por módulo
    descripcion = Column(String, nullable=True)

    # Relaciones
    usuarios = relationship("Usuario", back_populates="rol")


# ---- Residentes ----
class Residente(Base):
    __tablename__ = "residentes"  # Nombre de la tabla Residentes en la DB

    id = Column(Integer, primary_key=True, index=True)  # PK
    tipo_residente = Column(String, nullable=False)  # Propietario o inquilino
    nombre = Column(String, nullable=False)  # Nombre del Propietario / Inquilino
    cedula = Column(String, nullable=False, unique=True)  # Cédula de Identidad
    telefono = Column(String)  # Teléfono de contacto
    correo = Column(String)  # Correo electrónico de contacto
    id_usuario = Column(
        Integer, ForeignKey("usuarios.id"), unique=True
    )  # Relación con la tabla Usuario
    id_apartamento = Column(Integer, ForeignKey("apartamentos.id"), nullable=False)
    residentes_actual = Column(Boolean, default=True)  # True = residente activo

    # Relaciones
    usuario = relationship("Usuario", back_populates="residente", uselist=False)
    apartamento = relationship("Apartamento", back_populates="residente", uselist=False)
    pagos = relationship(
        "Pago", back_populates="residente", cascade="all, delete-orphan"
    )
    incidencias = relationship(
        "Incidencia", back_populates="residente", cascade="all, delete-orphan"
    )
    reservas = relationship(
        "Reserva", back_populates="residente", cascade="all, delete-orphan"
    )


# ---- Apartamentos ----
class Apartamento(Base):
    __tablename__ = "apartamentos"  # Nombre de la tabla Apartamentos en la DB

    id = Column(Integer, primary_key=True, index=True)  # PK
    numero = Column(String, nullable=False)  # Ej. 1-3
    torre = Column(String, nullable=False)  # Torre 1, 2
    piso = Column(Integer, nullable=False)  # Nivel
    tipo_apartamento = Column(String, nullable=False)  # 1 habitación, 2 habitaciones...
    porcentaje_aporte = Column(DECIMAL(5, 2), nullable=False)  # Ej. 20%
    estado = Column(String, default="Disponible")  # Ocupado / Disponible

    # Relaciones
    residente = relationship(
        "Residente", back_populates="apartamento", uselist=False
    )  # Uselist indica que la relación es 1-1
    pagos = relationship(
        "Pago", back_populates="apartamento", cascade="all, delete-orphan"
    )


# ---- Pagos ----
class Pago(Base):
    __tablename__ = "pagos"

    id = Column(Integer, primary_key=True, index=True)
    id_residente = Column(Integer, ForeignKey("residentes.id"), nullable=False)
    monto = Column(DECIMAL(10, 2), nullable=False)  # Total pagado
    moneda = Column(String, nullable=False)  # USD o VES
    tipo_cambio_bcv = Column(
        DECIMAL(10, 2), nullable=True
    )  # Tasa usada si el pago fue en VES
    fecha_pago = Column(Date, nullable=False)  # Fecha del pago
    concepto = Column(String, nullable=False)  # Mantenimiento, reserva...
    metodo = Column(String, nullable=False)  # Transferencia, efectivo...
    comprobante = Column(String, nullable=True)  # Imagen o referencia
    estado = Column(String, default="Pendiente")  # Pendiente / Validado / Rechazado
    fecha_creacion = Column(
        Date, default=func.current_date()
    )  # Fecha de registro del pago
    verificado = Column(
        Boolean, default=False
    )  # Si el pago ha sido validado por el Admin
    id_reporte_financiero = Column(
        Integer, ForeignKey("reportes_financieros.id"), nullable=True
    )
    id_apartamento = Column(Integer, ForeignKey("apartamentos.id"))

    residente = relationship("Residente", back_populates="pagos")
    apartamento = relationship("Apartamento", back_populates="pagos")
    reporte_financiero = relationship("ReporteFinanciero", back_populates="pagos")


# ---- Gastos Fijos ----
class GastoFijo(Base):
    __tablename__ = "gastos_fijos"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String, nullable=False)  # Mantenimiento, limpieza, seguridad
    monto = Column(DECIMAL(10, 2), nullable=False)
    fecha_registro = Column(Date, default=func.current_date())
    descripcion = Column(String, nullable=True)
    responsable = Column(String, nullable=False)
    id_reporte_financiero = Column(Integer, ForeignKey("reportes_financieros.id"))

    reporte_financiero = relationship(
        "ReporteFinanciero", back_populates="gastos_fijos"
    )  # en GastoFijo


# ---- Gastos Variables ----
class GastoVariable(Base):
    __tablename__ = "gastos_variables"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String, nullable=False)
    monto = Column(DECIMAL(10, 2), nullable=False)
    fecha_registro = Column(Date, default=func.current_date())
    descripcion = Column(String, nullable=True)
    responsable = Column(String, nullable=False)
    id_reporte_financiero = Column(Integer, ForeignKey("reportes_financieros.id"))

    reporte_financiero = relationship(
        "ReporteFinanciero", back_populates="gastos_variables"
    )  # en GastoVariable


class Incidencia(Base):
    __tablename__ = "incidencias"

    id = Column(Integer, primary_key=True, index=True)
    id_residente = Column(Integer, ForeignKey("residentes.id"), nullable=False)
    tipo = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    fecha_reporte = Column(Date, default=func.current_date())
    estado = Column(String, default="Abierta")
    prioridad = Column(String)
    respuesta_admin = Column(String, nullable=True)
    id_usuario_admin = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    fecha_atencion = Column(Date, nullable=True)

    administrador = relationship("Usuario")  # relación opcional directa

    residente = relationship("Residente", back_populates="incidencias")


class Reserva(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    id_residente = Column(Integer, ForeignKey("residentes.id"), nullable=False)
    area = Column(String, nullable=False)
    fecha_reserva = Column(Date, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    estado = Column(String, default="Activa")
    numero_personas = Column(Integer)
    notas = Column(String, nullable=True)

    residente = relationship("Residente", back_populates="reservas")


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    mensaje = Column(String, nullable=False)
    fecha_envio = Column(Date, default=func.current_date())
    tipo = Column(String)
    leido = Column(Boolean, default=False)

    usuario = relationship("Usuario", back_populates="notificaciones")


class Auditoria(Base):
    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    accion = Column(String, nullable=False)
    tabla_afectada = Column(String)
    fecha = Column(Date, default=func.current_date())
    detalle = Column(String, nullable=True)

    usuario = relationship("Usuario", back_populates="auditorias")


class ReporteFinanciero(Base):
    __tablename__ = "reportes_financieros"

    id = Column(Integer, primary_key=True, index=True)
    periodo = Column(String, nullable=False)
    total_gastos_fijos = Column(DECIMAL(10, 2), default=0)
    total_gastos_variables = Column(DECIMAL(10, 2), default=0)
    total_general = Column(DECIMAL(10, 2), default=0)
    generado_por = Column(String, nullable=False)
    fecha_generacion = Column(Date, default=func.current_date())

    gastos_fijos = relationship(
        "GastoFijo", back_populates="reporte_financiero", cascade="all, delete-orphan"
    )
    gastos_variables = relationship(
        "GastoVariable",
        back_populates="reporte_financiero",
        cascade="all, delete-orphan",
    )
    pagos = relationship(
        "Pago", back_populates="reporte_financiero", cascade="all, delete-orphan"
    )
