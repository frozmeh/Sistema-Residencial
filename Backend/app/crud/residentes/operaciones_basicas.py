from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import logging

from ... import models, schemas
from ...utils.db_helpers import guardar_y_refrescar
from ...utils.auditoria_helpers import registrar_auditoria

logger = logging.getLogger(__name__)

# =================
# ---- Helpers ----
# =================


def get_residente_or_404(db: Session, id_residente: int):
    residente = db.query(models.Residente).filter(models.Residente.id == id_residente).first()
    if not residente:
        raise HTTPException(status_code=404, detail="Residente no encontrado.")
    return residente


def validar_unicidad_residente(db: Session, cedula: str = None, correo: str = None, exclude_id: int = None):
    if cedula:
        existe_cedula = (
            db.query(models.Residente)
            .filter(func.lower(models.Residente.cedula) == cedula.lower())
            .filter(models.Residente.id != exclude_id if exclude_id else True)
            .first()
        )
        if existe_cedula:
            raise HTTPException(status_code=400, detail=f"La cédula {cedula} ya está registrada.")

    if correo:
        existe_correo = (
            db.query(models.Residente)
            .filter(func.lower(models.Residente.correo) == correo.lower())
            .filter(models.Residente.id != exclude_id if exclude_id else True)
            .first()
        )
        if existe_correo:
            raise HTTPException(status_code=400, detail=f"El correo {correo} ya está registrado.")


# ====================
# ---- Operaciones Básicas ----
# ====================


def crear_residente(db: Session, datos: schemas.ResidenteCreate, id_usuario: int, request=None, usuario_actual=None):
    """Crear nuevo residente con validaciones"""
    from .flujo_asignacion import _buscar_apartamento_por_direccion

    # Normalizar entradas
    torre_nombre = datos.torre.strip() if datos.torre else ""
    numero_apto = str(datos.numero_apartamento).strip()
    cedula_norm = datos.cedula.strip()
    correo_norm = datos.correo.strip().lower() if datos.correo else None

    # Buscar apartamento
    apartamento = _buscar_apartamento_por_direccion(db, torre_nombre, datos.piso, numero_apto)

    validar_unicidad_residente(db, cedula_norm, correo_norm)

    # Verificar disponibilidad del apartamento
    _validar_apartamento_disponible(db, apartamento.id, id_residente_exclude=None)

    # Validar que el usuario no tenga ya un residente asociado
    if db.query(models.Residente).filter(models.Residente.id_usuario == id_usuario).first():
        raise HTTPException(status_code=400, detail="El usuario ya tiene un residente asociado.")

    # Crear residente pendiente
    nuevo_residente = models.Residente(
        id_usuario=id_usuario,
        tipo_residente=datos.tipo_residente,
        nombre=datos.nombre.strip(),
        cedula=cedula_norm,
        correo=correo_norm,
        telefono=datos.telefono.strip() if datos.telefono else None,
        id_apartamento=apartamento.id,
        estado_aprobacion="Pendiente",
        estado_operativo="Inactivo",
        reside_actualmente=False,
    )

    db.add(nuevo_residente)
    guardar_y_refrescar(db, nuevo_residente)

    # Auditoría
    if usuario_actual:
        registrar_auditoria(
            db=db,
            usuario_id=id_usuario,
            usuario_nombre=usuario_actual.nombre,
            accion="Registro inicial de residente",
            tabla="residentes",
            objeto_previo=None,
            objeto_nuevo={c.name: getattr(nuevo_residente, c.name) for c in nuevo_residente.__table__.columns},
            request=request,
            campos_visibles=[
                "nombre",
                "cedula",
                "correo",
                "telefono",
                "tipo_residente",
                "estado_aprobacion",
                "fecha_registro",
            ],
            forzar=True,
        )

    return nuevo_residente


def obtener_residentes(db: Session):
    return db.query(models.Residente).order_by(models.Residente.id.asc()).all()


def obtener_residente_por_id(db: Session, id_residente: int):
    return get_residente_or_404(db, id_residente)


def obtener_residente_asociado(db: Session, id_usuario: int):
    residente = db.query(models.Residente).filter(models.Residente.id_usuario == id_usuario).first()
    if not residente:
        raise HTTPException(status_code=404, detail="No se encontró un residente asociado a este usuario.")
    return residente


def actualizar_residente(
    db: Session,
    id_residente: int,
    datos_actualizados: schemas.ResidenteUpdateResidente,
    usuario_actual=None,
    request=None,
):
    residente = obtener_residente_por_id(db, id_residente)

    # Validación de estado
    if residente.estado_aprobacion == "Rechazado":
        raise HTTPException(status_code=400, detail="No se puede actualizar un residente rechazado permanentemente")

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}
    update_data = datos_actualizados.dict(exclude_unset=True)

    if "cedula" in update_data or "correo" in update_data:
        validar_unicidad_residente(db, update_data.get("cedula"), update_data.get("correo"), id_residente)

    try:
        # Actualizar campos
        for key, value in update_data.items():
            setattr(residente, key, value)

        db.commit()
        db.refresh(residente)

        # Auditoría si hay cambios
        campos_modificados = [
            key for key in update_data if getattr(residente_previo, key, None) != getattr(residente, key, None)
        ]

        if usuario_actual and campos_modificados:
            registrar_auditoria(
                db=db,
                usuario_id=usuario_actual.id,
                usuario_nombre=usuario_actual.nombre,
                accion=f"Actualización de datos de residente: {', '.join(campos_modificados)}",
                tabla="residentes",
                objeto_previo=residente_previo,
                objeto_nuevo={c.name: getattr(residente, c.name) for c in residente.__table__.columns},
                request=request,
                campos_visibles=campos_modificados,
            )

        return residente

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error inesperado al actualizar residente: {str(e)}")


def eliminar_residente(db: Session, id_residente: int, usuario_actual=None, request=None):
    residente = obtener_residente_por_id(db, id_residente)

    if residente.estado_aprobacion == "Aprobado":
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar un residente aprobado. Use la función de desasignación en su lugar.",
        )

    if residente.estado_operativo == "Activo":
        raise HTTPException(
            status_code=400, detail="No se puede eliminar un residente activo. Inactive primero al residente."
        )

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}
    apartamento_previo = None

    # Liberar apartamento si existe
    apartamento = None
    if residente.id_apartamento:
        apartamento = db.query(models.Apartamento).filter(models.Apartamento.id == residente.id_apartamento).first()
        if apartamento:
            apartamento_previo = {c.name: getattr(apartamento, c.name) for c in apartamento.__table__.columns}

    try:
        # Liberar apartamento
        if apartamento:
            apartamento.estado = "Disponible"
            if hasattr(apartamento, "id_residente"):
                apartamento.id_residente = None

        # Eliminar residente
        db.delete(residente)
        db.commit()

        # Auditorías
        if usuario_actual:
            registrar_auditoria(
                db=db,
                usuario_id=usuario_actual.id,
                usuario_nombre=usuario_actual.nombre,
                accion="Eliminación de residente del sistema",
                tabla="residentes",
                objeto_previo=residente_previo,
                objeto_nuevo=None,
                request=request,
                campos_visibles=[
                    "nombre",
                    "cedula",
                    "correo",
                    "tipo_residente",
                    "estado_aprobacion",
                    "estado_operativo",
                ],
            )

            if apartamento_previo:
                registrar_auditoria(
                    db=db,
                    usuario_id=usuario_actual.id,
                    usuario_nombre=usuario_actual.nombre,
                    accion="Liberación de apartamento por eliminación de residente",
                    tabla="apartamentos",
                    objeto_previo=apartamento_previo,
                    objeto_nuevo={c.name: getattr(apartamento, c.name) for c in apartamento.__table__.columns},
                    request=request,
                )

        return {
            "mensaje": f"Residente {residente.nombre} eliminado correctamente del sistema.",
            "residente_id": id_residente,
            "apartamento_liberado": apartamento is not None,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar residente: {str(e)}")


# =================
# ---- Helpers Internos ----
# =================


def _validar_apartamento_disponible(db: Session, apartamento_id: int, id_residente_exclude: int = None):
    """Valida que el apartamento esté disponible"""
    apartamento = db.query(models.Apartamento).filter(models.Apartamento.id == apartamento_id).first()
    if not apartamento:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")

    if apartamento.estado.lower() == "ocupado":
        # Verificar si está ocupado por otro residente
        query = db.query(models.Residente).filter(
            models.Residente.id_apartamento == apartamento.id,
            models.Residente.estado_aprobacion.in_(["Pendiente", "Corrección Requerida", "Aprobado"]),
        )

        if id_residente_exclude:
            query = query.filter(models.Residente.id != id_residente_exclude)

        residente_existente = query.first()

        if residente_existente:
            raise HTTPException(
                status_code=400,
                detail=f"El apartamento ya tiene un residente asignado: {residente_existente.nombre} (estado: {residente_existente.estado_aprobacion})",
            )

    return apartamento
