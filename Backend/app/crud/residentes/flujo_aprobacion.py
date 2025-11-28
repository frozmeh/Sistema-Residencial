from fastapi import HTTPException
from sqlalchemy.orm import Session
import logging

from ... import models
from ...utils.auditoria_helpers import registrar_auditoria
from .operaciones_basicas import get_residente_or_404, _validar_apartamento_disponible

logger = logging.getLogger(__name__)

# ========================
# ---- Flujo Aprobación ----
# ========================


def aprobar_residente(db: Session, id_residente: int, usuario_actual=None, request=None):
    """Aprobar residente y asignar apartamento"""
    residente = get_residente_or_404(db, id_residente)

    # Validaciones de estado
    if residente.estado_aprobacion == "Aprobado":
        raise HTTPException(status_code=400, detail="El residente ya está aprobado")

    if residente.estado_aprobacion == "Rechazado":
        raise HTTPException(status_code=400, detail="No se puede aprobar un residente rechazado")

    if not residente.id_apartamento:
        raise HTTPException(status_code=400, detail="El residente no tiene apartamento asignado para aprobar")

    # Validar que el apartamento esté disponible
    apartamento = _validar_apartamento_disponible(db, residente.id_apartamento, residente.id)

    # Guardar estados previos para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}
    apartamento_previo = {c.name: getattr(apartamento, c.name) for c in apartamento.__table__.columns}

    try:
        # Aprobar residente
        residente.estado_aprobacion = "Aprobado"
        residente.estado_operativo = "Activo"
        residente.reside_actualmente = True

        # Ocupar apartamento
        apartamento.estado = "Ocupado"

        db.commit()
        db.refresh(residente)
        db.refresh(apartamento)

        # Auditorías
        if usuario_actual:
            registrar_auditoria(
                db=db,
                usuario_id=usuario_actual.id,
                usuario_nombre=usuario_actual.nombre,
                accion="Aprobación de residente",
                tabla="residentes",
                objeto_previo=residente_previo,
                objeto_nuevo={c.name: getattr(residente, c.name) for c in residente.__table__.columns},
                request=request,
            )

            registrar_auditoria(
                db=db,
                usuario_id=usuario_actual.id,
                usuario_nombre=usuario_actual.nombre,
                accion="Cambio de estado de apartamento a Ocupado",
                tabla="apartamentos",
                objeto_previo=apartamento_previo,
                objeto_nuevo={c.name: getattr(apartamento, c.name) for c in apartamento.__table__.columns},
                request=request,
            )

        logger.info(f"✅ Residente {residente.nombre} aprobado exitosamente")
        return residente

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al aprobar residente {id_residente}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al aprobar residente: {str(e)}")


def solicitar_correccion_residente(
    db: Session,
    id_residente: int,
    motivo: str = "Se requiere corrección de datos.",
    usuario_actual=None,
    request=None,
):
    """Solicitar corrección de datos del residente"""
    residente = get_residente_or_404(db, id_residente)

    # Validaciones
    if residente.estado_aprobacion == "Corrección Requerida":
        raise HTTPException(status_code=400, detail="Ya se solicitó corrección para este residente")

    if residente.estado_aprobacion == "Rechazado":
        raise HTTPException(
            status_code=400, detail="No se puede solicitar corrección a un residente rechazado permanentemente"
        )

    if residente.estado_aprobacion == "Aprobado":
        raise HTTPException(status_code=400, detail="No se puede solicitar corrección a un residente ya aprobado")

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}

    try:
        # Cambiar estado a corrección requerida
        residente.estado_aprobacion = "Corrección Requerida"
        residente.estado_operativo = "Inactivo"
        residente.reside_actualmente = False
        # NO liberar apartamento - mantener asignación para corrección

        db.commit()
        db.refresh(residente)

        # Auditoría
        if usuario_actual:
            registrar_auditoria(
                db=db,
                usuario_id=usuario_actual.id,
                usuario_nombre=usuario_actual.nombre,
                accion=f"Solicitud de corrección: {motivo}",
                tabla="residentes",
                objeto_previo=residente_previo,
                objeto_nuevo={c.name: getattr(residente, c.name) for c in residente.__table__.columns},
                request=request,
                campos_visibles=[
                    "nombre",
                    "cedula",
                    "correo",
                    "telefono",
                    "tipo_residente",
                    "estado_aprobacion",
                    "estado_operativo",
                ],
            )

        logger.info(f"📝 Corrección solicitada para residente {residente.nombre}: {motivo}")
        return {
            "mensaje": f"Se solicitó corrección: {motivo}",
            "residente_id": residente.id,
            "estado_aprobacion": residente.estado_aprobacion,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al solicitar corrección para residente {id_residente}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al solicitar corrección: {str(e)}")


def rechazar_residente_permanentemente(
    db: Session,
    id_residente: int,
    motivo: str = "Registro rechazado permanentemente.",
    usuario_actual=None,
    request=None,
):
    """Rechazar residente permanentemente y liberar apartamento"""
    residente = get_residente_or_404(db, id_residente)

    # Validaciones
    if residente.estado_aprobacion == "Rechazado":
        raise HTTPException(status_code=400, detail="El residente ya está rechazado permanentemente")

    # Guardar estados previos para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}
    apartamento_previo = None

    # Obtener apartamento si existe
    apartamento = None
    if residente.id_apartamento:
        apartamento = db.query(models.Apartamento).filter(models.Apartamento.id == residente.id_apartamento).first()
        if apartamento:
            apartamento_previo = {c.name: getattr(apartamento, c.name) for c in apartamento.__table__.columns}

    try:
        # Rechazar residente permanentemente
        residente.estado_aprobacion = "Rechazado"
        residente.estado_operativo = "Inactivo"
        residente.reside_actualmente = False

        # Liberar apartamento si existe
        if residente.id_apartamento and apartamento:
            apartamento.estado = "Disponible"
            # Opcional: desasignar completamente
            residente.id_apartamento = None

        db.commit()
        db.refresh(residente)
        if apartamento:
            db.refresh(apartamento)

        # Auditorías
        if usuario_actual:
            # Auditoría para residente
            registrar_auditoria(
                db=db,
                usuario_id=usuario_actual.id,
                usuario_nombre=usuario_actual.nombre,
                accion=f"Rechazo permanente: {motivo}",
                tabla="residentes",
                objeto_previo=residente_previo,
                objeto_nuevo={c.name: getattr(residente, c.name) for c in residente.__table__.columns},
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

            # Auditoría para apartamento si se liberó
            if apartamento_previo and apartamento:
                registrar_auditoria(
                    db=db,
                    usuario_id=usuario_actual.id,
                    usuario_nombre=usuario_actual.nombre,
                    accion="Liberación de apartamento por rechazo permanente de residente",
                    tabla="apartamentos",
                    objeto_previo=apartamento_previo,
                    objeto_nuevo={c.name: getattr(apartamento, c.name) for c in apartamento.__table__.columns},
                    request=request,
                )

        logger.info(f"❌ Residente {residente.nombre} rechazado permanentemente: {motivo}")
        return {"mensaje": motivo, "residente_id": residente.id, "apartamento_liberado": apartamento is not None}

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al rechazar residente {id_residente}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al rechazar residente: {str(e)}")


def reenviar_para_aprobacion(
    db: Session,
    id_residente: int,
    usuario_actual=None,
    request=None,
):
    """Permitir que residente en 'Corrección Requerida' vuelva a 'Pendiente'"""
    residente = get_residente_or_404(db, id_residente)

    if residente.estado_aprobacion != "Corrección Requerida":
        raise HTTPException(
            status_code=400, detail="Solo residentes con 'Corrección Requerida' pueden reenviarse para aprobación"
        )

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}

    try:
        residente.estado_aprobacion = "Pendiente"

        db.commit()
        db.refresh(residente)

        # Auditoría
        if usuario_actual:
            registrar_auditoria(
                db=db,
                usuario_id=usuario_actual.id,
                usuario_nombre=usuario_actual.nombre,
                accion="Reenvío para aprobación después de corrección",
                tabla="residentes",
                objeto_previo=residente_previo,
                objeto_nuevo={c.name: getattr(residente, c.name) for c in residente.__table__.columns},
                request=request,
            )

        logger.info(f"🔄 Residente {residente.nombre} reenviado para aprobación")
        return {
            "mensaje": "Residente reenviado para aprobación exitosamente",
            "residente_id": residente.id,
            "estado_aprobacion": residente.estado_aprobacion,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al reenviar residente {id_residente} para aprobación: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al reenviar para aprobación: {str(e)}")


def obtener_residentes_no_validados(db: Session, torre: str = None, piso: int = None):
    """Obtener residentes pendientes de validación"""
    from sqlalchemy import func

    query = (
        db.query(
            models.Residente.id,
            models.Residente.nombre,
            models.Residente.cedula,
            models.Residente.correo,
            models.Residente.telefono,
            models.Residente.tipo_residente,
            models.Residente.fecha_registro,
            models.Residente.estado_aprobacion,
            models.Torre.nombre.label("torre"),
            models.Piso.numero.label("piso"),
            models.Apartamento.numero.label("apartamento"),
        )
        .join(models.Apartamento, models.Residente.id_apartamento == models.Apartamento.id)
        .join(models.Piso, models.Apartamento.id_piso == models.Piso.id)
        .join(models.Torre, models.Piso.id_torre == models.Torre.id)
        .filter(models.Residente.estado_aprobacion.in_(["Pendiente", "Corrección Requerida"]))
    )

    if torre:
        query = query.filter(func.lower(models.Torre.nombre) == torre.lower())
    if piso:
        query = query.filter(models.Piso.numero == piso)

    resultados = query.order_by(models.Residente.fecha_registro.asc()).all()

    from ... import schemas

    return [
        schemas.ResidentePendienteOut(
            id=r.id,
            nombre=r.nombre,
            cedula=r.cedula,
            correo=r.correo,
            telefono=r.telefono,
            tipo_residente=r.tipo_residente,
            fecha_registro=r.fecha_registro,
            estado_aprobacion=r.estado_aprobacion,
            torre=r.torre,
            piso=r.piso,
            apartamento=r.apartamento,
        )
        for r in resultados
    ]
