from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from ... import models
from ...utils.auditoria_helpers import registrar_auditoria
from ...utils.db_helpers import guardar_y_refrescar
from .operaciones_basicas import get_residente_or_404, _validar_apartamento_disponible

logger = logging.getLogger(__name__)

# ===========================
# ---- Asignación Apartamentos ----
# ===========================


def asignar_residente_a_apartamento(
    db: Session, id_residente: int, id_apartamento: int, usuario_actual=None, request=None
):
    """Asignar residente aprobado a un apartamento específico"""
    residente = get_residente_or_404(db, id_residente)

    # Validar que el residente esté aprobado
    if residente.estado_aprobacion != "Aprobado":
        raise HTTPException(
            status_code=400,
            detail=f"No se puede asignar apartamento a residente con estado: {residente.estado_aprobacion}",
        )

    # Validar que no tenga ya un apartamento asignado
    if residente.id_apartamento:
        raise HTTPException(status_code=400, detail="El residente ya tiene un apartamento asignado.")

    # Obtener y validar apartamento
    apartamento = db.query(models.Apartamento).filter(models.Apartamento.id == id_apartamento).first()
    if not apartamento:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado.")

    # Validar que el apartamento esté disponible
    _validar_apartamento_disponible(db, id_apartamento)

    # Guardar estados previos para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}
    apartamento_previo = {c.name: getattr(apartamento, c.name) for c in apartamento.__table__.columns}

    try:
        # Asignar apartamento al residente
        residente.id_apartamento = apartamento.id
        apartamento.estado = "Ocupado"

        # Asignar residente al apartamento si existe la relación
        if hasattr(apartamento, "id_residente"):
            apartamento.id_residente = residente.id

        db.commit()
        db.refresh(residente)
        db.refresh(apartamento)

        # Auditorías
        if usuario_actual:
            registrar_auditoria(
                db=db,
                usuario_id=usuario_actual.id,
                usuario_nombre=usuario_actual.nombre,
                accion="Asignación manual de apartamento a residente",
                tabla="residentes",
                objeto_previo=residente_previo,
                objeto_nuevo={c.name: getattr(residente, c.name) for c in residente.__table__.columns},
                request=request,
            )

            registrar_auditoria(
                db=db,
                usuario_id=usuario_actual.id,
                usuario_nombre=usuario_actual.nombre,
                accion="Cambio de estado de apartamento por asignación",
                tabla="apartamentos",
                objeto_previo=apartamento_previo,
                objeto_nuevo={c.name: getattr(apartamento, c.name) for c in apartamento.__table__.columns},
                request=request,
            )

        logger.info(f"✅ Residente {residente.nombre} asignado al apartamento {apartamento.numero}")
        return {
            "mensaje": f"Residente {residente.nombre} asignado al apartamento {apartamento.numero}.",
            "residente": residente,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al asignar apartamento {id_apartamento} a residente {id_residente}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al asignar apartamento: {str(e)}")


def desasignar_residente(db: Session, id_residente: int, inactivar: bool = False, usuario_actual=None, request=None):
    """Desasignar residente de su apartamento (con opción de inactivar)"""
    residente = get_residente_or_404(db, id_residente)

    # Validaciones
    if not residente.id_apartamento:
        raise HTTPException(status_code=400, detail="El residente no tiene apartamento asignado.")

    if residente.estado_aprobacion != "Aprobado":
        raise HTTPException(status_code=400, detail="Solo se pueden desasignar residentes aprobados")

    # Obtener apartamento
    apartamento = db.query(models.Apartamento).filter(models.Apartamento.id == residente.id_apartamento).first()
    if not apartamento:
        raise HTTPException(status_code=404, detail="El apartamento asignado no existe en el sistema")

    # Guardar estados previos para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}
    apartamento_previo = {c.name: getattr(apartamento, c.name) for c in apartamento.__table__.columns}

    try:
        # Liberar apartamento
        apartamento.estado = "Disponible"
        if hasattr(apartamento, "id_residente"):
            apartamento.id_residente = None

        # Liberar relación del residente
        residente.id_apartamento = None

        # Inactivar si se solicita
        if inactivar:
            residente.estado_operativo = "Inactivo"
            residente.reside_actualmente = False

        db.commit()
        db.refresh(residente)
        db.refresh(apartamento)

        # Auditorías
        if usuario_actual:
            registrar_auditoria(
                db=db,
                usuario_id=usuario_actual.id,
                usuario_nombre=usuario_actual.nombre,
                accion="Desasignación de residente" + (" con inactivación" if inactivar else ""),
                tabla="residentes",
                objeto_previo=residente_previo,
                objeto_nuevo={c.name: getattr(residente, c.name) for c in residente.__table__.columns},
                request=request,
            )

            registrar_auditoria(
                db=db,
                usuario_id=usuario_actual.id,
                usuario_nombre=usuario_actual.nombre,
                accion="Liberación de apartamento por desasignación",
                tabla="apartamentos",
                objeto_previo=apartamento_previo,
                objeto_nuevo={c.name: getattr(apartamento, c.name) for c in apartamento.__table__.columns},
                request=request,
            )

        logger.info(f"✅ Residente {residente.nombre} desasignado del apartamento")
        return {
            "mensaje": f"Residente {residente.nombre} desasignado correctamente."
            + (" Fue inactivado del sistema." if inactivar else " Permanece activo."),
            "estado_operativo": residente.estado_operativo,
            "apartamento_liberado": True,
            "residente_inactivado": inactivar,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al desasignar residente {id_residente}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al desasignar residente: {str(e)}")


def reasignar_apartamento_pendiente(
    db: Session, id_residente: int, torre: str, numero_apartamento: str, piso: int, usuario_actual=None, request=None
):
    """Reasignar apartamento a residente pendiente de validación"""
    residente = get_residente_or_404(db, id_residente)

    # Validar que el residente esté en estado pendiente
    if residente.estado_aprobacion not in ["Pendiente", "Corrección Requerida"]:
        raise HTTPException(
            status_code=400, detail="Solo se puede reasignar apartamento a residentes pendientes o en corrección"
        )

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}
    apartamento_anterior_previo = None

    # Obtener apartamento anterior si existe
    apartamento_anterior = None
    if residente.id_apartamento:
        apartamento_anterior = (
            db.query(models.Apartamento).filter(models.Apartamento.id == residente.id_apartamento).first()
        )
        if apartamento_anterior:
            apartamento_anterior_previo = {
                c.name: getattr(apartamento_anterior, c.name) for c in apartamento_anterior.__table__.columns
            }

    # Buscar nuevo apartamento
    nuevo_apartamento = _buscar_apartamento_por_direccion(db, torre, piso, numero_apartamento)

    # Validar que el nuevo apartamento esté disponible
    _validar_apartamento_disponible(db, nuevo_apartamento.id, id_residente)

    try:
        # Liberar apartamento anterior si existe
        if apartamento_anterior:
            apartamento_anterior.estado = "Disponible"
            if hasattr(apartamento_anterior, "id_residente"):
                apartamento_anterior.id_residente = None

        # Asignar nuevo apartamento
        residente.id_apartamento = nuevo_apartamento.id

        db.commit()
        db.refresh(residente)
        if apartamento_anterior:
            db.refresh(apartamento_anterior)

        # Auditorías
        if usuario_actual:
            # Auditoría para residente
            registrar_auditoria(
                db=db,
                usuario_id=usuario_actual.id,
                usuario_nombre=usuario_actual.nombre,
                accion=f"Reasignación de apartamento: {apartamento_anterior.numero if apartamento_anterior else 'Sin asignar'} → {nuevo_apartamento.numero}",
                tabla="residentes",
                objeto_previo=residente_previo,
                objeto_nuevo={c.name: getattr(residente, c.name) for c in residente.__table__.columns},
                request=request,
            )

            # Auditoría para apartamento anterior si existía
            if apartamento_anterior_previo and apartamento_anterior:
                registrar_auditoria(
                    db=db,
                    usuario_id=usuario_actual.id,
                    usuario_nombre=usuario_actual.nombre,
                    accion="Liberación de apartamento por reasignación",
                    tabla="apartamentos",
                    objeto_previo=apartamento_anterior_previo,
                    objeto_nuevo={
                        c.name: getattr(apartamento_anterior, c.name) for c in apartamento_anterior.__table__.columns
                    },
                    request=request,
                )

        logger.info(f"🔄 Residente {residente.nombre} reasignado a apartamento {nuevo_apartamento.numero}")
        return {
            "mensaje": f"Residente {residente.nombre} reasignado al apartamento {nuevo_apartamento.numero}",
            "apartamento_anterior": apartamento_anterior.numero if apartamento_anterior else None,
            "apartamento_nuevo": nuevo_apartamento.numero,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al reasignar apartamento a residente {id_residente}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al reasignar apartamento: {str(e)}")


# ========================
# ---- Helpers Internos ----
# ========================


def _buscar_apartamento_por_direccion(db: Session, torre_nombre: str, piso_numero: int, numero_apartamento: str):
    """Buscar apartamento por torre, piso y número"""
    # Buscar torre
    torre = db.query(models.Torre).filter(func.lower(models.Torre.nombre) == torre_nombre.lower()).first()
    if not torre:
        raise HTTPException(status_code=404, detail=f"Torre '{torre_nombre}' no encontrada")

    # Buscar piso
    piso = db.query(models.Piso).filter(models.Piso.id_torre == torre.id, models.Piso.numero == piso_numero).first()
    if not piso:
        raise HTTPException(status_code=404, detail=f"Piso {piso_numero} no encontrado en {torre_nombre}")

    # Buscar apartamento
    apartamento = (
        db.query(models.Apartamento)
        .filter(
            models.Apartamento.id_piso == piso.id,
            func.lower(models.Apartamento.numero) == numero_apartamento.lower(),
        )
        .first()
    )

    if not apartamento:
        raise HTTPException(status_code=404, detail=f"Apartamento {numero_apartamento} no encontrado")

    return apartamento


def obtener_residentes_por_torre(db: Session, nombre_torre: str, skip: int = 0, limit: int = 100):
    """Obtener residentes filtrados por torre"""
    return (
        db.query(models.Residente)
        .join(models.Apartamento, models.Residente.id_apartamento == models.Apartamento.id)
        .join(models.Piso, models.Apartamento.id_piso == models.Piso.id)
        .join(models.Torre, models.Piso.id_torre == models.Torre.id)
        .filter(func.lower(models.Torre.nombre) == nombre_torre.lower())
        .order_by(models.Residente.nombre.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def obtener_historial_residentes_por_apartamento(db: Session, id_apartamento: int):
    """Obtener historial de residentes que han ocupado un apartamento"""
    return (
        db.query(models.Residente)
        .join(models.Apartamento, models.Residente.id_apartamento == models.Apartamento.id)
        .join(models.Piso, models.Apartamento.id_piso == models.Piso.id)
        .join(models.Torre, models.Piso.id_torre == models.Torre.id)
        .filter(models.Residente.id_apartamento == id_apartamento)
        .order_by(models.Residente.fecha_registro.desc())
        .all()
    )
