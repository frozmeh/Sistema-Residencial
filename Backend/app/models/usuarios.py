from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, func, Enum, Index, CheckConstraint
from ..database import Base
from sqlalchemy.orm import relationship


# =================
# ---- Usuario ----
# =================


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    id_rol = Column(Integer, ForeignKey("roles.id", ondelete="RESTRICT"))

    nombre = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)  # Compatible con bcrypt
    estado = Column(Enum("Activo", "Inactivo", "Bloqueado", name="estado_usuario"), default="Activo")

    # Campos de auditoría y seguridad
    fecha_creacion = Column(DateTime, default=func.now(), nullable=False)
    ultima_sesion = Column(DateTime, nullable=True)
    ultimo_ip = Column(String(45), nullable=True)  # IPv6 compatible
    intentos_fallidos = Column(Integer, default=0)
    fecha_bloqueo = Column(DateTime, nullable=True)

    __table_args__ = (
        # Índices para consultas frecuentes
        Index("idx_usuario_estado_fecha", "estado", "fecha_creacion"),
        Index("idx_usuario_rol_estado", "id_rol", "estado"),
        Index("idx_usuario_estado_activo", "estado", "ultima_sesion"),
        # Validaciones de negocio
        CheckConstraint("intentos_fallidos >= 0 AND intentos_fallidos <= 5", name="check_intentos_fallidos_rango"),
        # Validación de fechas coherentes
        CheckConstraint("fecha_bloqueo IS NULL OR fecha_bloqueo >= fecha_creacion", name="check_fecha_bloqueo_logica"),
        CheckConstraint("ultima_sesion IS NULL OR ultima_sesion >= fecha_creacion", name="check_ultima_sesion_logica"),
    )

    rol = relationship("Rol", back_populates="usuarios")
    residente = relationship("Residente", back_populates="usuario", uselist=False)
    notificaciones = relationship("Notificacion", back_populates="usuario", cascade="all, delete-orphan")
    incidencias_atendidas = relationship("Incidencia", back_populates="administrador", cascade="all, delete-orphan")
    auditorias = relationship("Auditoria", back_populates="usuario", cascade="all, delete-orphan")

    def esta_activo(self):
        """Verifica si el usuario puede operar en el sistema"""
        return self.estado == "Activo" and self.intentos_fallidos < 5

    def incrementar_intentos_fallidos(self):
        """Incrementa intentos y bloquea si excede el límite"""
        self.intentos_fallidos += 1
        if self.intentos_fallidos >= 5:
            self.estado = "Bloqueado"
            self.fecha_bloqueo = func.now()

    def resetear_intentos(self):
        """Resetea los intentos fallidos"""
        self.intentos_fallidos = 0
        if self.estado == "Bloqueado":
            self.estado = "Activo"
            self.fecha_bloqueo = None
