from fastapi import HTTPException
from sqlalchemy import func
from typing import Optional
from sqlalchemy.orm import Session, aliased
from sqlalchemy.exc import IntegrityError

from ..utils.db_helpers import guardar_y_refrescar
from ..utils.auditoria_helpers import registrar_auditoria
from .. import models, schemas


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
# ---- Residentes ----
# ====================


def crear_residente(db: Session, datos: schemas.ResidenteCreate, id_usuario: int, request=None, usuario_actual=None):
    # Normalizar entradas
    torre_nombre = datos.torre.strip() if datos.torre else ""
    numero_apto = str(datos.numero_apartamento).strip()
    cedula_norm = datos.cedula.strip()
    correo_norm = datos.correo.strip().lower() if datos.correo else None

    # Buscar torre -> piso -> apartamento
    torre = db.query(models.Torre).filter(func.lower(models.Torre.nombre) == torre_nombre.lower()).first()
    if not torre:
        raise HTTPException(status_code=404, detail=f"Torre '{datos.torre}' no encontrada")

    piso = db.query(models.Piso).filter(models.Piso.id_torre == torre.id, models.Piso.numero == datos.piso).first()
    if not piso:
        raise HTTPException(status_code=404, detail=f"Piso {datos.piso} no encontrado en {torre.nombre}")

    apartamento = (
        db.query(models.Apartamento)
        .filter(models.Apartamento.id_piso == piso.id, func.lower(models.Apartamento.numero) == numero_apto.lower())
        .first()
    )
    if not apartamento:
        raise HTTPException(status_code=404, detail=f"Apartamento {datos.numero_apartamento} no encontrado")

    validar_unicidad_residente(db, cedula_norm, correo_norm)

    # Verificar si el apartamento está disponible
    if apartamento.estado.lower() == "ocupado":
        raise HTTPException(status_code=400, detail="El apartamento ya está ocupado por otro residente")

    # Verificar que no exista otro residente en el apartamento
    residente_existente = (
        db.query(models.Residente)
        .filter(
            models.Residente.id_apartamento == apartamento.id,
            models.Residente.estado_aprobacion.in_(["Pendiente", "Corrección Requerida", "Aprobado"]),
        )
        .first()
    )

    if residente_existente:
        raise HTTPException(
            status_code=400,
            detail=f"El apartamento ya tiene un residente asignado: {residente_existente.nombre} (estado: {residente_existente.estado_aprobacion})",
        )

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

    # Registro de nuevo residente
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


def verificar_apartamento_disponible(db: Session, apartamento_id: int, residente: models.Residente):
    apartamento = db.query(models.Apartamento).filter(models.Apartamento.id == apartamento_id).first()
    if not apartamento:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")

    otro_residente = (
        db.query(models.Residente)
        .filter(
            models.Residente.id_apartamento == apartamento.id,
            models.Residente.id != residente.id,
            models.Residente.estado_aprobacion == "Aprobado",
        )
        .first()
    )

    if otro_residente:
        raise HTTPException(status_code=400, detail=f"El apartamento ya está ocupado por {otro_residente.nombre}")

    return apartamento


def aprobar_residente(db: Session, id_residente: int, usuario_actual=None, request=None):
    residente = get_residente_or_404(db, id_residente)

    if residente.estado_aprobacion == "Aprobado":
        raise HTTPException(status_code=400, detail="El residente ya está aprobado")

    if residente.estado_aprobacion == "Rechazado":
        raise HTTPException(status_code=400, detail="No se puede aprobar un residente rechazado")

    if not residente.id_apartamento:
        raise HTTPException(status_code=400, detail="El residente no tiene apartamento asignado para aprobar")

    apartamento = verificar_apartamento_disponible(db, residente.id_apartamento, residente)

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}
    apartamento_previo = {c.name: getattr(apartamento, c.name) for c in apartamento.__table__.columns}

    try:
        # Aprobar residente
        residente.estado_aprobacion = "Aprobado"
        residente.estado_operativo = "Activo"
        residente.reside_actualmente = True
        apartamento.estado = "Ocupado"

        db.commit()
        db.refresh(residente)
        db.refresh(apartamento)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al aprobar residente: {str(e)}")

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

    return residente


def solicitar_correccion_residente(
    db: Session,
    id_residente: int,
    motivo: str = "Se requiere corrección de datos.",
    usuario_actual=None,
    request=None,
):
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

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al solicitar corrección: {str(e)}")

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

    return {
        "mensaje": f"Se solicitó corrección: {motivo}",
        "residente_id": residente.id,
        "estado_aprobacion": residente.estado_aprobacion,
    }


def rechazar_residente_permanentemente(
    db: Session,
    id_residente: int,
    motivo: str = "Registro rechazado permanentemente.",
    usuario_actual=None,
    request=None,
):
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

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al rechazar residente: {str(e)}")

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
            campos_visibles=["nombre", "cedula", "correo", "tipo_residente", "estado_aprobacion", "estado_operativo"],
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

    return {"mensaje": motivo, "residente_id": residente.id, "apartamento_liberado": apartamento is not None}


def reenviar_para_aprobacion(
    db: Session,
    id_residente: int,
    usuario_actual=None,
    request=None,
):
    """Permite que un residente en 'Corrección Requerida' vuelva a 'Pendiente'"""
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

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al reenviar para aprobación: {str(e)}")

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

    return {
        "mensaje": "Residente reenviado para aprobación exitosamente",
        "residente_id": residente.id,
        "estado_aprobacion": residente.estado_aprobacion,
    }


def suspender_residente(db: Session, id_residente: int, usuario_actual=None, request=None):
    residente = get_residente_or_404(db, id_residente)

    if residente.estado_operativo == "Suspendido":
        raise HTTPException(status_code=400, detail="El residente ya está suspendido")

    if residente.estado_aprobacion != "Aprobado":
        raise HTTPException(
            status_code=400, detail=f"No se puede suspender un residente con estado: {residente.estado_aprobacion}"
        )

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}

    try:
        residente.estado_operativo = "Suspendido"

        db.commit()
        db.refresh(residente)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al suspender residente: {str(e)}")

    # Suspensión de residente
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

    return residente


def reactivar_residente(db: Session, id_residente: int, usuario_actual=None, request=None):
    residente = get_residente_or_404(db, id_residente)

    if residente.estado_operativo == "Activo":
        raise HTTPException(status_code=400, detail="El residente ya está activo")

    if residente.estado_aprobacion != "Aprobado":
        raise HTTPException(
            status_code=400, detail=f"No se puede reactivar un residente con estado: {residente.estado_aprobacion}"
        )

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}

    try:
        residente.estado_operativo = "Activo"

        db.commit()
        db.refresh(residente)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al reactivar residente: {str(e)}")

    # Reactivación de residente
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

        campos_modificados = []
        for key in update_data:
            if getattr(residente_previo, key, None) != getattr(residente, key, None):
                campos_modificados.append(key)

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

    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Error de duplicación en la base de datos. Verifique cédula o correo."
        )

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

    if residente.estado_aprobacion == "Rechazado":
        # Podría tener historial de solicitudes, pero permitimos eliminación
        pass

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}

    # Liberar apartamento si existe
    apartamento_previo = None
    apartamento = None

    if residente.id_apartamento:
        apartamento = db.query(models.Apartamento).filter(models.Apartamento.id == residente.id_apartamento).first()
        if apartamento:
            # Guardar estado previo del apartamento para auditoría
            apartamento_previo = {c.name: getattr(apartamento, c.name) for c in apartamento.__table__.columns}

    try:
        if residente.id_apartamento:
            residente.id_apartamento = None

        # Liberar apartamento si existe
        if apartamento:
            apartamento.estado = "Disponible"
            if hasattr(apartamento, "id_residente"):
                apartamento.id_residente = None

        # Eliminar residente
        db.delete(residente)
        db.commit()

        if usuario_actual:
            # Auditoría para eliminación de residente
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

            # Auditoría para liberación de apartamento si existía
            if apartamento_previo and apartamento:
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


def asignar_residente_a_apartamento(
    db: Session, id_residente: int, id_apartamento: int, usuario_actual=None, request=None
):
    residente = get_residente_or_404(db, id_residente)

    if residente.estado_aprobacion != "Aprobado":
        raise HTTPException(
            status_code=400,
            detail=f"No se puede asignar apartamento a residente con estado: {residente.estado_aprobacion}",
        )

    apartamento = db.query(models.Apartamento).filter(models.Apartamento.id == id_apartamento).first()
    if not apartamento:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado.")

    if residente.id_apartamento:
        raise HTTPException(status_code=400, detail="El residente ya tiene un apartamento asignado.")

    if apartamento.estado.lower() == "ocupado":
        raise HTTPException(status_code=400, detail="El apartamento ya está ocupado.")

    # Guardar estados previos para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}
    apartamento_previo = {c.name: getattr(apartamento, c.name) for c in apartamento.__table__.columns}

    try:
        residente.id_apartamento = apartamento.id
        apartamento.estado = "Ocupado"
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

        return {
            "mensaje": f"Residente {residente.nombre} asignado al apartamento {apartamento.numero}.",
            "residente": residente,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al asignar apartamento: {str(e)}")


def desasignar_residente(db: Session, id_residente: int, inactivar: bool = False, usuario_actual=None, request=None):
    residente = get_residente_or_404(db, id_residente)

    if not residente.id_apartamento:
        raise HTTPException(status_code=400, detail="El residente no tiene apartamento asignado.")

    if residente.estado_aprobacion != "Aprobado":
        raise HTTPException(status_code=400, detail="Solo se pueden desasignar residentes aprobados")

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}
    apartamento_previo = None
    apartamento = None

    apartamento = db.query(models.Apartamento).filter(models.Apartamento.id == residente.id_apartamento).first()
    if not apartamento:
        raise HTTPException(status_code=404, detail="El apartamento asignado no existe en el sistema")

    apartamento_previo = {c.name: getattr(apartamento, c.name) for c in apartamento.__table__.columns}

    try:
        # Liberar apartamento
        apartamento.estado = "Disponible"
        if hasattr(apartamento, "id_residente"):
            apartamento.id_residente = None

        # Liberar relación
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

        return {
            "mensaje": f"Residente {residente.nombre} desasignado correctamente."
            + (" Fue inactivado del sistema." if inactivar else " Permanece activo."),
            "estado_operativo": residente.estado_operativo,
            "apartamento_liberado": True,
            "residente_inactivado": inactivar,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al desasignar residente: {str(e)}")


def activar_residente(db: Session, id_residente: int, usuario_actual=None, request=None):
    residente = obtener_residente_por_id(db, id_residente)

    if residente.estado_operativo == "Activo":
        raise HTTPException(status_code=400, detail="El residente ya está activo")

    if residente.estado_aprobacion != "Aprobado":
        raise HTTPException(
            status_code=400, detail=f"No se puede activar un residente con estado: {residente.estado_aprobacion}"
        )

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}

    try:
        residente.estado_operativo = "Activo"
        residente.reside_actualmente = True

        guardar_y_refrescar(db, residente)

        # Activación de residente
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

        return {
            "mensaje": f"Residente {residente.nombre} activado correctamente.",
            "estado_operativo": residente.estado_operativo,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al activar residente: {str(e)}")


def reasignar_apartamento_pendiente(
    db: Session, id_residente: int, torre: str, numero_apartamento: str, piso: int, usuario_actual=None, request=None
):
    """Reasigna apartamento a un residente pendiente de validación"""
    residente = get_residente_or_404(db, id_residente)

    if residente.estado_aprobacion not in ["Pendiente", "Corrección Requerida"]:
        raise HTTPException(
            status_code=400, detail="Solo se puede reasignar apartamento a residentes pendientes o en corrección"
        )

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}
    apartamento_anterior_previo = None
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
    torre_obj = db.query(models.Torre).filter(func.lower(models.Torre.nombre) == torre.lower()).first()
    if not torre_obj:
        raise HTTPException(status_code=404, detail=f"Torre '{torre}' no encontrada")

    piso_obj = db.query(models.Piso).filter(models.Piso.id_torre == torre_obj.id, models.Piso.numero == piso).first()
    if not piso_obj:
        raise HTTPException(status_code=404, detail=f"Piso {piso} no encontrado en {torre}")

    nuevo_apartamento = (
        db.query(models.Apartamento)
        .filter(
            models.Apartamento.id_piso == piso_obj.id,
            func.lower(models.Apartamento.numero) == numero_apartamento.lower(),
        )
        .first()
    )

    if not nuevo_apartamento:
        raise HTTPException(status_code=404, detail=f"Apartamento {numero_apartamento} no encontrado")

    residente_existente = (
        db.query(models.Residente)
        .filter(
            models.Residente.id_apartamento == nuevo_apartamento.id,
            models.Residente.estado_aprobacion.in_(["Pendiente", "Corrección Requerida", "Aprobado"]),
            models.Residente.id != id_residente,  # ✅ Excluir al residente actual
        )
        .first()
    )

    if residente_existente:
        raise HTTPException(
            status_code=400,
            detail=f"El nuevo apartamento ya tiene un residente asignado: {residente_existente.nombre}",
        )

    try:
        if apartamento_anterior:
            apartamento_anterior.estado = "Disponible"
            if hasattr(apartamento_anterior, "id_residente"):
                apartamento_anterior.id_residente = None

        residente.id_apartamento = nuevo_apartamento.id

        db.commit()
        db.refresh(residente)
        if apartamento_anterior:
            db.refresh(apartamento_anterior)

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

        return {
            "mensaje": f"Residente {residente.nombre} reasignado al apartamento {nuevo_apartamento.numero}",
            "apartamento_anterior": apartamento_anterior.numero if apartamento_anterior else None,
            "apartamento_nuevo": nuevo_apartamento.numero,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al reasignar apartamento: {str(e)}")


def obtener_residentes(db: Session):
    return db.query(models.Residente).order_by(models.Residente.id.asc()).all()


def obtener_residente_por_id(db: Session, id_residente: int):
    residente = get_residente_or_404(db, id_residente)
    return residente


def obtener_residente_asociado(db: Session, id_usuario: int):
    residente = db.query(models.Residente).filter(models.Residente.id_usuario == id_usuario).first()

    if not residente:
        raise HTTPException(status_code=404, detail="No se encontró un residente asociado a este usuario.")

    return residente


def obtener_residentes_no_validados(db: Session, torre: str = None, piso: int = None):
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


def obtener_residentes_por_torre(db: Session, nombre_torre: str, skip: int = 0, limit: int = 100):
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


def buscar_residente(db: Session, termino: str, limite: int = 50):
    termino_busqueda = f"%{termino}%"
    return (
        db.query(models.Residente)
        .filter(
            models.Residente.nombre.ilike(termino_busqueda)
            | models.Residente.cedula.ilike(termino_busqueda)
            | models.Residente.correo.ilike(termino_busqueda)
        )
        .order_by(models.Residente.nombre.asc())
        .limit(limite)
        .all()
    )


def contar_residentes(db: Session, solo_activos: bool = True):
    query = db.query(func.count(models.Residente.id))
    if solo_activos:
        query = query.filter(models.Residente.estado_operativo == "Activo")
    return query.scalar()


def obtener_historial_residentes_por_apartamento(db: Session, id_apartamento: int):
    return (
        db.query(models.Residente)
        .join(models.Apartamento, models.Residente.id_apartamento == models.Apartamento.id)
        .join(models.Piso, models.Apartamento.id_piso == models.Piso.id)
        .join(models.Torre, models.Piso.id_torre == models.Torre.id)
        .filter(models.Residente.id_apartamento == id_apartamento)
        .order_by(models.Residente.fecha_registro.desc())
        .all()
    )


def estadisticas_residentes(db: Session):
    """Obtener estadísticas detalladas de residentes"""
    total_residentes = db.query(func.count(models.Residente.id)).scalar()
    residentes_validados = (
        db.query(func.count(models.Residente.id)).filter(models.Residente.estado_aprobacion == "Aprobado").scalar()
    )
    residentes_pendientes = (
        db.query(func.count(models.Residente.id)).filter(models.Residente.estado_aprobacion == "Pendiente").scalar()
    )
    residentes_activos = (
        db.query(func.count(models.Residente.id)).filter(models.Residente.estado_operativo == "Activo").scalar()
    )

    # Por tipo de residente
    propietarios = (
        db.query(func.count(models.Residente.id)).filter(models.Residente.tipo_residente == "Propietario").scalar()
    )
    inquilinos = (
        db.query(func.count(models.Residente.id)).filter(models.Residente.tipo_residente == "Inquilino").scalar()
    )

    # Por torre
    residentes_por_torre = (
        db.query(models.Torre.nombre, func.count(models.Residente.id))
        .join(models.Piso)
        .join(models.Apartamento)
        .join(models.Residente)
        .group_by(models.Torre.nombre)
        .all()
    )

    return {
        "totales": {
            "total_residentes": total_residentes,
            "validados": residentes_validados,
            "pendientes": residentes_pendientes,
            "activos": residentes_activos,
        },
        "por_tipo": {"propietarios": propietarios, "inquilinos": inquilinos},
        "por_torre": [{"torre": torre, "cantidad": cantidad} for torre, cantidad in residentes_por_torre],
    }


def busqueda_avanzada(
    db: Session,
    nombre: Optional[str] = None,
    cedula: Optional[str] = None,
    torre: Optional[str] = None,
    tipo_residente: Optional[str] = None,
    estado_operativo: Optional[str] = None,
    estado_aprobacion: Optional[str] = None,
):
    # Búsqueda avanzada de residentes con múltiples filtros
    query = db.query(models.Residente)

    if nombre:
        query = query.filter(models.Residente.nombre.ilike(f"%{nombre}%"))
    if cedula:
        query = query.filter(models.Residente.cedula.ilike(f"%{cedula}%"))
    if tipo_residente:
        query = query.filter(models.Residente.tipo_residente == tipo_residente)
    if estado_operativo:
        query = query.filter(models.Residente.estado_operativo == estado_operativo)
    if estado_aprobacion:
        query = query.filter(models.Residente.estado_aprobacion == estado_aprobacion)

    # Filtro por torre (necesita joins)
    if torre:
        query = (
            query.join(models.Apartamento)
            .join(models.Piso)
            .join(models.Torre)
            .filter(func.lower(models.Torre.nombre) == torre.lower())
        )

    residentes = query.order_by(models.Residente.nombre.asc()).all()
    return residentes


def obtener_estadisticas_dashboard(db: Session):
    """Estadísticas para dashboard administrativo"""
    total = db.query(func.count(models.Residente.id)).scalar()
    aprobados = (
        db.query(func.count(models.Residente.id)).filter(models.Residente.estado_aprobacion == "Aprobado").scalar()
    )
    pendientes = (
        db.query(func.count(models.Residente.id)).filter(models.Residente.estado_aprobacion == "Pendiente").scalar()
    )
    activos = db.query(func.count(models.Residente.id)).filter(models.Residente.estado_operativo == "Activo").scalar()

    return {
        "total_residentes": total,
        "aprobados": aprobados,
        "pendientes": pendientes,
        "activos": activos,
        "tasa_aprobacion": (aprobados / total * 100) if total > 0 else 0,
    }
