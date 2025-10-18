from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DECIMAL, Date, Boolean
from sqlalchemy.orm import relationship
from datetime import date
from .database import Base

class Rol(Base):
    __tablename__ = "roles"

    id_rol = Column(Integer, primary_key=True, index=True)
    nombre_rol = Column(String, unique=True, nullable=False)
    permisos = Column(String)
    descripcion = Column(String)

    usuarios = relationship("Usuario", back_populates="rol")

class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre_usuario = Column(String, unique=True, nullable=False)
    contraseña = Column(String, nullable=False)
    correo = Column(String, unique=True, nullable=False)
    id_rol = Column(Integer, ForeignKey("roles.id_rol"))
    estado = Column(Boolean, default=True)
    fecha_creacion = Column(Date)
    ultima_sesion = Column(Date)

    rol = relationship("Rol", back_populates="usuarios")
    residente = relationship("Residente", back_populates="usuario", uselist=False)

class Residente(Base):
    __tablename__ = "residentes"

    id_residente = Column(Integer, primary_key=True, index=True)
    tipo_residente = Column(String)
    nombre = Column(String)
    cedula = Column(String)
    telefono = Column(String)
    correo = Column(String)
    id_apartamento = Column(Integer, ForeignKey("apartamentos.id_apartamento"))
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"))
    fecha_registro = Column(Date)
    estado = Column(String)

    usuario = relationship("Usuario", back_populates="residente")
    apartamento = relationship("Apartamento", back_populates="residentes")
    pagos = relationship("Pago", back_populates="residente")

class Apartamento(Base):
    __tablename__ = "apartamentos"

    id_apartamento = Column(Integer, primary_key=True, index=True)
    numero = Column(String, unique=True, nullable=False)
    torre = Column(String, nullable=False)
    piso = Column(Integer, nullable=False)
    tipo_apartamento = Column(String, nullable=False)
    porcentaje_aporte = Column(DECIMAL, nullable=False)
    estado = Column(String, default="Disponible")

    # Relación con Residente
    residentes = relationship("Residente", back_populates="apartamento")
    
class Pago(Base):
    __tablename__ = "pagos"

    id_pago = Column(Integer, primary_key=True, index=True)
    id_residente = Column(Integer, ForeignKey("residentes.id_residente"), nullable=False)
    id_apartamento = Column(Integer, ForeignKey("apartamentos.id_apartamento"), nullable=True)
    monto = Column(DECIMAL, nullable=False)
    moneda = Column(String, default="VES")
    tipo_cambio_bcv = Column(DECIMAL, nullable=True)
    fecha_pago = Column(Date, nullable=False)
    concepto = Column(String, nullable=False)
    metodo = Column(String, nullable=False)
    comprobante = Column(String, nullable=True)
    estado = Column(String, default="Pendiente")  # Pendiente / Validado / Rechazado
    fecha_creacion = Column(Date, default=date.today)
    verificado = Column(Boolean, default=False)

    residente = relationship("Residente", back_populates="pagos")
    apartamento = relationship("Apartamento")
    
class GastoFijo(Base):
    __tablename__ = "gastos_fijos"

    id_gasto_fijo = Column(Integer, primary_key=True, index=True)
    tipo = Column(String, nullable=False)  # Ej: mantenimiento, seguridad
    monto = Column(DECIMAL, nullable=False)
    fecha_registro = Column(Date, nullable=False)
    descripcion = Column(String, nullable=True)
    responsable = Column(String, nullable=True)

class GastoVariable(Base):
    __tablename__ = "gastos_variables"

    id_gasto_variable = Column(Integer, primary_key=True, index=True)
    tipo = Column(String, nullable=False)  # Ej: reparación, sustitución
    monto = Column(DECIMAL, nullable=False)
    fecha_registro = Column(Date, nullable=False)
    descripcion = Column(String, nullable=True)
    responsable = Column(String, nullable=True)
    
from sqlalchemy import Column, Integer, String, DECIMAL, Date

class ReporteFinanciero(Base):
    __tablename__ = "reportes_financieros"

    id_reporte = Column(Integer, primary_key=True, index=True)
    periodo = Column(String, nullable=False)  # Ej: "2025-10"
    total_gastos_fijos = Column(DECIMAL, default=0)
    total_gastos_variables = Column(DECIMAL, default=0)
    total_general = Column(DECIMAL, default=0)
    generado_por = Column(String, nullable=False)  # Usuario que generó
    fecha_generacion = Column(Date, nullable=False)

class Incidencia(Base):
    __tablename__ = "incidencias"

    id_incidencia = Column(Integer, primary_key=True, index=True)
    id_residente = Column(Integer, nullable=False)
    tipo = Column(String, nullable=False)  # Ej: falla eléctrica, agua
    descripcion = Column(String, nullable=False)
    fecha_reporte = Column(Date, nullable=False)
    estado = Column(String, default="Abierta")  # Abierta / En proceso / Cerrada
    prioridad = Column(String, default="Media")  # Alta / Media / Baja
    respuesta_admin = Column(String, nullable=True)

class Reserva(Base):
    __tablename__ = "reservas"

    id_reserva = Column(Integer, primary_key=True, index=True)
    id_residente = Column(Integer, nullable=False)
    area = Column(String, nullable=False)  # Ej: salón, parrillera, cancha
    fecha_reserva = Column(Date, nullable=False)
    hora_inicio = Column(String, nullable=False)  # Hora en formato HH:MM
    hora_fin = Column(String, nullable=False)
    estado = Column(String, default="Activa")  # Activa / Cancelada / Finalizada
    numero_personas = Column(Integer, nullable=False)
    notas = Column(String, nullable=True)

class Notificacion(Base):
    __tablename__ = "notificaciones"

    id_notificacion = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, nullable=False)
    mensaje = Column(String, nullable=False)
    fecha_envio = Column(Date, nullable=False)
    tipo = Column(String, nullable=False)  # Ej: pago, incidencia, sistema
    leido = Column(Boolean, default=False)

class Auditoria(Base):
    __tablename__ = "auditoria"

    id_log = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, nullable=False)
    accion = Column(String, nullable=False)  # Ej: crear, eliminar, actualizar
    tabla_afectada = Column(String, nullable=False)  # Ej: pagos, residentes
    fecha = Column(Date, nullable=False)
    detalle = Column(String, nullable=True)  # Información adicional

    usuario = relationship("Usuario")