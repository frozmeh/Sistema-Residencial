from fastapi import HTTPException
from sqlalchemy.orm import Session
import logging

from ... import models
from ...utils.auditoria_helpers import registrar_auditoria
from ...utils.db_helpers import guardar_y_refrescar
from .operaciones_basicas import get_residente_or_404

logger = logging.getLogger(__name__)

# ===========================
# ---- Gestión de Estados ----
# ===========================


def suspender_residente(db: Session, id_residente: int, usuario_actual=None, request=None):
    """Suspender residente (mantiene aprobación pero limita operaciones)"""
    residente = get_residente_or_404(db, id_residente)

    # Validaciones
    if residente.estado_operativo == "Suspendido":
        raise HTTPException(status_code=400, detail="El residente ya está suspendido")

    if residente.estado_aprobacion != "Aprobado":
        raise HTTPException(
            status_code=400, detail=f"No se puede suspender un residente con estado: {residente.estado_aprobacion}"
        )

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}

    try:
        # Suspender residente
        residente.estado_operativo = "Suspendido"
        # Mantener estado_aprobacion como "Aprobado" pero cambiar operativo a "Suspendido"

        db.commit()
        db.refresh(residente)

        # Auditoría
        if usuario_actual:
            registrar_auditoria(
                db=db,
                usuario_id=usuario_actual.id,
                usuario_nombre=usuario_actual.nombre,
                accion="Suspensión de residente",
                tabla="residentes",
                objeto_previo=residente_previo,
                objeto_nuevo={c.name: getattr(residente, c.name) for c in residente.__table__.columns},
                request=request,
            )

        logger.info(f"⏸️ Residente {residente.nombre} suspendido")
        return residente

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al suspender residente {id_residente}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al suspender residente: {str(e)}")


def reactivar_residente(db: Session, id_residente: int, usuario_actual=None, request=None):
    """Reactivar residente suspendido"""
    residente = get_residente_or_404(db, id_residente)

    # Validaciones
    if residente.estado_operativo == "Activo":
        raise HTTPException(status_code=400, detail="El residente ya está activo")

    if residente.estado_aprobacion != "Aprobado":
        raise HTTPException(
            status_code=400, detail=f"No se puede reactivar un residente con estado: {residente.estado_aprobacion}"
        )

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}

    try:
        # Reactivar residente
        residente.estado_operativo = "Activo"

        db.commit()
        db.refresh(residente)

        # Auditoría
        if usuario_actual:
            registrar_auditoria(
                db=db,
                usuario_id=usuario_actual.id,
                usuario_nombre=usuario_actual.nombre,
                accion="Reactivación de residente",
                tabla="residentes",
                objeto_previo=residente_previo,
                objeto_nuevo={c.name: getattr(residente, c.name) for c in residente.__table__.columns},
                request=request,
            )

        logger.info(f"▶️ Residente {residente.nombre} reactivado")
        return residente

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al reactivar residente {id_residente}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al reactivar residente: {str(e)}")


def activar_residente(db: Session, id_residente: int, usuario_actual=None, request=None):
    """Activar residente (para residentes inactivos pero aprobados)"""
    residente = get_residente_or_404(db, id_residente)

    # Validaciones
    if residente.estado_operativo == "Activo":
        raise HTTPException(status_code=400, detail="El residente ya está activo")

    if residente.estado_aprobacion != "Aprobado":
        raise HTTPException(
            status_code=400, detail=f"No se puede activar un residente con estado: {residente.estado_aprobacion}"
        )

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}

    try:
        # Activar residente
        residente.estado_operativo = "Activo"
        residente.reside_actualmente = True

        guardar_y_refrescar(db, residente)

        # Auditoría
        if usuario_actual:
            registrar_auditoria(
                db=db,
                usuario_id=usuario_actual.id,
                usuario_nombre=usuario_actual.nombre,
                accion="Activación manual de residente",
                tabla="residentes",
                objeto_previo=residente_previo,
                objeto_nuevo={c.name: getattr(residente, c.name) for c in residente.__table__.columns},
                request=request,
            )

        logger.info(f"✅ Residente {residente.nombre} activado manualmente")
        return {
            "mensaje": f"Residente {residente.nombre} activado correctamente.",
            "estado_operativo": residente.estado_operativo,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al activar residente {id_residente}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al activar residente: {str(e)}")


def cambiar_estado_residente(
    db: Session, id_residente: int, nuevo_estado_operativo: str, usuario_actual=None, request=None
):
    """Cambiar estado operativo del residente de forma genérica"""
    residente = get_residente_or_404(db, id_residente)

    # Estados válidos
    estados_validos = ["Activo", "Inactivo", "Suspendido"]
    if nuevo_estado_operativo not in estados_validos:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Opciones: {', '.join(estados_validos)}")

    # Validar que no sea el mismo estado
    if residente.estado_operativo == nuevo_estado_operativo:
        raise HTTPException(
            status_code=400, detail=f"El residente ya se encuentra en estado '{nuevo_estado_operativo}'"
        )

    # Validaciones específicas por estado
    if nuevo_estado_operativo == "Activo" and residente.estado_aprobacion != "Aprobado":
        raise HTTPException(status_code=400, detail="Solo residentes aprobados pueden ser activados")

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}

    try:
        # Cambiar estado
        estado_anterior = residente.estado_operativo
        residente.estado_operativo = nuevo_estado_operativo

        # Lógica adicional según el estado
        if nuevo_estado_operativo == "Activo":
            residente.reside_actualmente = True
        elif nuevo_estado_operativo in ["Inactivo", "Suspendido"]:
            residente.reside_actualmente = False

        db.commit()
        db.refresh(residente)

        # Auditoría
        if usuario_actual:
            registrar_auditoria(
                db=db,
                usuario_id=usuario_actual.id,
                usuario_nombre=usuario_actual.nombre,
                accion=f"Cambio de estado operativo: {estado_anterior} → {nuevo_estado_operativo}",
                tabla="residentes",
                objeto_previo=residente_previo,
                objeto_nuevo={c.name: getattr(residente, c.name) for c in residente.__table__.columns},
                request=request,
            )

        logger.info(f"🔄 Residente {residente.nombre} cambió estado: {estado_anterior} → {nuevo_estado_operativo}")
        return {
            "residente": residente,
            "estado_anterior": estado_anterior,
            "estado_nuevo": nuevo_estado_operativo,
            "mensaje": f"Estado cambiado exitosamente de '{estado_anterior}' a '{nuevo_estado_operativo}'",
        }

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al cambiar estado del residente {id_residente}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al cambiar estado del residente: {str(e)}")


def obtener_estados_disponibles():
    """Retorna los estados operativos disponibles para residentes"""
    return {
        "estados_operativos": [
            {
                "valor": "Activo",
                "descripcion": "Residente activo con acceso completo al sistema",
                "requisitos": ["Debe estar aprobado", "Puede tener apartamento asignado"],
            },
            {
                "valor": "Inactivo",
                "descripcion": "Residente inactivo temporalmente",
                "requisitos": ["Puede estar aprobado o pendiente", "No puede realizar operaciones"],
            },
            {
                "valor": "Suspendido",
                "descripcion": "Residente suspendido por incumplimiento",
                "requisitos": ["Debe estar aprobado", "Acceso restringido al sistema"],
            },
        ],
        "estados_aprobacion": [
            {"valor": "Pendiente", "descripcion": "Esperando aprobación administrativa"},
            {"valor": "Aprobado", "descripcion": "Residente validado y activo"},
            {"valor": "Corrección Requerida", "descripcion": "Requiere corrección de datos"},
            {"valor": "Rechazado", "descripcion": "Registro rechazado permanentemente"},
        ],
    }


def verificar_estado_residente(residente: models.Residente) -> dict:
    """Verifica el estado actual del residente y retorna información detallada"""
    estado_info = {
        "id": residente.id,
        "nombre": residente.nombre,
        "estado_aprobacion": residente.estado_aprobacion,
        "estado_operativo": residente.estado_operativo,
        "reside_actualmente": residente.reside_actualmente,
        "puede_realizar_operaciones": False,
        "restricciones": [],
        "permisos": [],
    }

    # Determinar permisos basados en estados
    if residente.estado_aprobacion == "Aprobado" and residente.estado_operativo == "Activo":
        estado_info["puede_realizar_operaciones"] = True
        estado_info["permisos"] = [
            "consultar_estado_cuenta",
            "realizar_pagos",
            "ver_comunicaciones",
            "actualizar_datos_personales",
        ]
    elif residente.estado_aprobacion == "Aprobado" and residente.estado_operativo == "Suspendido":
        estado_info["restricciones"] = [
            "No puede realizar pagos",
            "No puede actualizar datos",
            "Solo consulta limitada",
        ]
        estado_info["permisos"] = ["consultar_estado_cuenta_basico"]
    elif residente.estado_operativo == "Inactivo":
        estado_info["restricciones"] = ["Acceso completamente restringido"]
    elif residente.estado_aprobacion in ["Pendiente", "Corrección Requerida"]:
        estado_info["restricciones"] = ["Esperando aprobación administrativa"]
        estado_info["permisos"] = ["actualizar_datos_personales"]

    return estado_info


def contar_residentes_por_estado(db: Session) -> dict:
    """Cuenta residentes agrupados por estado operativo y de aprobación"""
    from sqlalchemy import func

    # Conteo por estado operativo
    conteo_operativo = (
        db.query(models.Residente.estado_operativo, func.count(models.Residente.id).label("cantidad"))
        .group_by(models.Residente.estado_operativo)
        .all()
    )

    # Conteo por estado de aprobación
    conteo_aprobacion = (
        db.query(models.Residente.estado_aprobacion, func.count(models.Residente.id).label("cantidad"))
        .group_by(models.Residente.estado_aprobacion)
        .all()
    )

    # Conteo de residentes que residen actualmente
    residentes_que_residen = (
        db.query(func.count(models.Residente.id)).filter(models.Residente.reside_actualmente == True).scalar() or 0
    )

    return {
        "por_estado_operativo": {estado: cantidad for estado, cantidad in conteo_operativo},
        "por_estado_aprobacion": {estado: cantidad for estado, cantidad in conteo_aprobacion},
        "residentes_que_residen_actualmente": residentes_que_residen,
        "total_residentes": db.query(func.count(models.Residente.id)).scalar() or 0,
    }
