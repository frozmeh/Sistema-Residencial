from fastapi import HTTPException, status
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


def crear_residente(db: Session, datos: schemas.ResidenteCreate, id_usuario: int, request=None):
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

    try:
        db.add(nuevo_residente)
        guardar_y_refrescar(db, nuevo_residente)

        # Registro de nuevo residente
        registrar_auditoria(
            db=db,
            usuario_id=id_usuario,
            usuario_nombre=datos.nombre,
            accion="Registro inicial de residente",
            tabla="residentes",
            objeto_previo=None,
            objeto_nuevo={c.name: getattr(nuevo_residente, c.name) for c in nuevo_residente.__table__.columns},
            request=request,
            campos_visibles=["nombre", "cedula", "correo", "tipo_residente", "estado_aprobacion", "fecha_registro"],
            forzar=True,
        )

        return nuevo_residente
    except IntegrityError as error:
        db.rollback()
        if "unique constraint" in str(error).lower():
            if "cedula" in str(error).lower():
                raise HTTPException(status_code=400, detail="La cédula ya está registrada en el sistema")
            elif "correo" in str(error).lower():
                raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado")
            elif "id_usuario" in str(error).lower():
                raise HTTPException(status_code=400, detail="El usuario ya tiene un residente asociado")
        raise HTTPException(status_code=400, detail="Error de duplicación en la base de datos")


def verificar_apartamento_disponible(db: Session, apartamento_id: int):
    apartamento = db.query(models.Apartamento).filter(models.Apartamento.id == apartamento_id).first()
    if not apartamento:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")

    if apartamento.estado.lower() == "ocupado":
        raise HTTPException(status_code=400, detail="El apartamento ya está ocupado")

    return apartamento


def aprobar_residente(db: Session, id_residente: int, usuario_actual=None, request=None):
    residente = get_residente_or_404(db, id_residente)

    if not residente.id_apartamento:
        raise HTTPException(status_code=400, detail="El residente no tiene apartamento asignado para aprobar")

    apartamento = verificar_apartamento_disponible(db, residente.id_apartamento)

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}
    apartamento_previo = {c.name: getattr(apartamento, c.name) for c in apartamento.__table__.columns}

    # Aprobar residente
    residente.estado_aprobacion = "Aprobado"
    residente.estado_operativo = "Activo"
    residente.reside_actualmente = True
    apartamento.estado = "Ocupado"

    db.commit()

    # Aprobación de residente
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

        # Cambio de estado del apartamento
        registrar_auditoria(
            db=db,
            usuario_id=usuario_actual.id,
            usuario_nombre=usuario_actual.nombre,
            accion="Asignación de apartamento",
            tabla="apartamentos",
            objeto_previo=apartamento_previo,
            objeto_nuevo={c.name: getattr(apartamento, c.name) for c in apartamento.__table__.columns},
            request=request,
        )

    return {"mensaje": f"Residente {residente.nombre} aprobado correctamente", "residente": residente}


def rechazar_residente(
    db: Session,
    id_residente: int,
    motivo: str = "Registro rechazado por el administrador.",
    usuario_actual=None,
    request=None,
):
    residente = get_residente_or_404(db, id_residente)

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}

    residente.estado_aprobacion = "Rechazado"
    residente.estado_operativo = "Inactivo"
    residente.reside_actualmente = False

    db.commit()

    # Rechazo de residente
    if usuario_actual:
        registrar_auditoria(
            db=db,
            usuario_id=usuario_actual.id,
            usuario_nombre=usuario_actual.nombre,
            accion=f"Rechazo de residente: {motivo}",
            tabla="residentes",
            objeto_previo=residente_previo,
            objeto_nuevo={c.name: getattr(residente, c.name) for c in residente.__table__.columns},
            request=request,
        )

    return {"mensaje": motivo}


def suspender_residente(db: Session, id_residente: int, usuario_actual=None, request=None):
    residente = get_residente_or_404(db, id_residente)

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}

    residente.estado_operativo = "Suspendido"
    guardar_y_refrescar(db, residente)

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

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}

    residente.estado_operativo = "Activo"
    guardar_y_refrescar(db, residente)

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


def obtener_residentes(db: Session):
    return db.query(models.Residente).order_by(models.Residente.id.asc()).all()


def obtener_residente_por_id(db: Session, id_residente: int):
    residente = get_residente_or_404(db, id_residente)
    return residente


def actualizar_residente(
    db: Session,
    id_residente: int,
    datos_actualizados: schemas.ResidenteUpdateResidente,
    usuario_actual=None,
    request=None,
):
    residente = obtener_residente_por_id(db, id_residente)

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}

    update_data = datos_actualizados.dict(exclude_unset=True)
    validar_unicidad_residente(db, update_data.get("cedula"), update_data.get("correo"), id_residente)

    for key, value in update_data.items():
        setattr(residente, key, value)

    try:
        guardar_y_refrescar(db, residente)

        # Actualización de datos de residente
        if usuario_actual:
            registrar_auditoria(
                db=db,
                usuario_id=usuario_actual.id,
                usuario_nombre=usuario_actual.nombre,
                accion="Actualización de datos de residente",
                tabla="residentes",
                objeto_previo=residente_previo,
                objeto_nuevo={c.name: getattr(residente, c.name) for c in residente.__table__.columns},
                request=request,
            )

        return residente
    except IntegrityError as error:
        db.rollback()
        if "unique constraint" in str(error).lower():
            if "cedula" in str(error).lower():
                raise HTTPException(status_code=400, detail="La cédula ya está registrada")
            elif "correo" in str(error).lower():
                raise HTTPException(status_code=400, detail="El correo ya está registrado")
        raise HTTPException(status_code=400, detail="Error de duplicación en la base de datos")


def eliminar_residente(db: Session, id_residente: int, usuario_actual=None, request=None):
    residente = obtener_residente_por_id(db, id_residente)

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}

    # Liberar apartamento si existe
    if residente.id_apartamento:
        apartamento = db.query(models.Apartamento).filter(models.Apartamento.id == residente.id_apartamento).first()
        if apartamento:
            # Guardar estado previo del apartamento para auditoría
            apartamento_previo = {c.name: getattr(apartamento, c.name) for c in apartamento.__table__.columns}

            apartamento.estado = "Disponible"
            if hasattr(apartamento, "id_residente"):
                apartamento.id_residente = None

            # Liberación de apartamento
            if usuario_actual:
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

    db.delete(residente)
    db.commit()

    # Eliminación de residente
    if usuario_actual:
        registrar_auditoria(
            db=db,
            usuario_id=usuario_actual.id,
            usuario_nombre=usuario_actual.nombre,
            accion="Eliminación de residente",
            tabla="residentes",
            objeto_previo=residente_previo,
            objeto_nuevo=None,
            request=request,
        )

    return {"mensaje": f"Residente con ID {id_residente} eliminado correctamente."}


def asignar_residente_a_apartamento(
    db: Session, id_residente: int, id_apartamento: int, usuario_actual=None, request=None
):
    residente = get_residente_or_404(db, id_residente)

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

    residente.id_apartamento = apartamento.id
    apartamento.estado = "Ocupado"
    if hasattr(apartamento, "id_residente"):
        apartamento.id_residente = residente.id

    db.commit()
    db.refresh(residente)
    db.refresh(apartamento)

    # Asignación de apartamento
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


def desasignar_residente(db: Session, id_residente: int, inactivar: bool = False, usuario_actual=None, request=None):
    residente = get_residente_or_404(db, id_residente)

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}

    if residente.id_apartamento:
        apartamento = db.query(models.Apartamento).filter(models.Apartamento.id == residente.id_apartamento).first()
        if apartamento:
            # Guardar estado previo del apartamento para auditoría
            apartamento_previo = {c.name: getattr(apartamento, c.name) for c in apartamento.__table__.columns}

            apartamento.estado = "Disponible"
            if hasattr(apartamento, "id_residente"):
                apartamento.id_residente = None

            # Liberación de apartamento
            if usuario_actual:
                registrar_auditoria(
                    db=db,
                    usuario_id=usuario_actual.id,
                    usuario_nombre=usuario_actual.nombre,
                    accion="Desasignación de apartamento",
                    tabla="apartamentos",
                    objeto_previo=apartamento_previo,
                    objeto_nuevo={c.name: getattr(apartamento, c.name) for c in apartamento.__table__.columns},
                    request=request,
                )
        residente.id_apartamento = None

    if inactivar:
        residente.estado_operativo = "Inactivo"
        residente.reside_actualmente = False

    guardar_y_refrescar(db, residente)

    # Desasignación de residente
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

    return {
        "mensaje": f"Residente {residente.nombre} desasignado correctamente.",
        "estado_operativo": residente.estado_operativo,
    }


def activar_residente(db: Session, id_residente: int, usuario_actual=None, request=None):
    residente = obtener_residente_por_id(db, id_residente)

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}

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


def obtener_residentes_no_validados(db: Session, torre: str = None, piso: int = None):
    Torre = aliased(models.Torre)
    Piso = aliased(models.Piso)
    Apartamento = aliased(models.Apartamento)
    Residente = aliased(models.Residente)

    query = (
        db.query(
            Residente.id,
            Residente.nombre,
            Residente.cedula,
            Residente.correo,
            Residente.telefono,
            Residente.tipo_residente,
            Residente.fecha_registro,
            Torre.nombre.label("torre"),
            Piso.numero.label("piso"),
            Apartamento.numero.label("apartamento"),
        )
        .join(Apartamento, Residente.id_apartamento == Apartamento.id)
        .join(Piso, Apartamento.id_piso == Piso.id)
        .join(Torre, Piso.id_torre == Torre.id)
        .filter(Residente.estado_aprobacion == "Pendiente")
    )

    if torre:
        query = query.filter(func.lower(Torre.nombre) == torre.lower())
    if piso:
        query = query.filter(Piso.numero == piso)

    resultados = query.order_by(Residente.fecha_registro.asc()).all()

    return [
        schemas.ResidentePendienteOut(
            id=r.id,
            nombre=r.nombre,
            cedula=r.cedula,
            correo=r.correo,
            telefono=r.telefono,
            tipo_residente=r.tipo_residente,
            fecha_registro=r.fecha_registro,
            torre=r.torre,
            piso=r.piso,
            apartamento=r.apartamento,
        )
        for r in resultados
    ]


def obtener_residentes_por_torre(db: Session, nombre_torre: str):
    return (
        db.query(models.Residente)
        .join(models.Apartamento, models.Residente.id_apartamento == models.Apartamento.id)
        .join(models.Piso, models.Apartamento.id_piso == models.Piso.id)
        .join(models.Torre, models.Piso.id_torre == models.Torre.id)
        .filter(func.lower(models.Torre.nombre) == nombre_torre.lower())
        .order_by(models.Residente.nombre.asc())
        .all()
    )


def obtener_residente_asociado(db: Session, id_usuario: int):
    residente = db.query(models.Residente).filter(models.Residente.id_usuario == id_usuario).first()

    if not residente:
        raise HTTPException(status_code=404, detail="No se encontró un residente asociado a este usuario.")

    return residente


def buscar_residente(db: Session, termino: str):
    termino = f"%{termino.lower()}%"
    return (
        db.query(models.Residente)
        .filter(
            func.lower(models.Residente.nombre).like(termino)
            | func.lower(models.Residente.cedula).like(termino)
            | func.lower(models.Residente.correo).like(termino)
        )
        .order_by(models.Residente.nombre.asc())
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
        .filter(models.Residente.id_apartamento == id_apartamento)
        .order_by(models.Residente.fecha_registro.asc())
        .all()
    )


def reasignar_apartamento_pendiente(
    db: Session, id_residente: int, torre: str, numero_apartamento: str, piso: int, usuario_actual=None, request=None
):
    """Reasigna apartamento a un residente pendiente de validación"""
    residente = get_residente_or_404(db, id_residente)

    if residente.estado_aprobacion == "Aprobado":
        raise HTTPException(status_code=400, detail="No se puede reasignar apartamento a residente ya validado")

    # Guardar estado previo para auditoría
    residente_previo = {c.name: getattr(residente, c.name) for c in residente.__table__.columns}

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

    # Liberar apartamento anterior si existe
    if residente.id_apartamento:
        apartamento_anterior = (
            db.query(models.Apartamento).filter(models.Apartamento.id == residente.id_apartamento).first()
        )
        if apartamento_anterior:
            apartamento_anterior.estado = "Disponible"

    # Asignar nuevo apartamento
    if nuevo_apartamento.estado.lower() == "ocupado":
        raise HTTPException(status_code=400, detail="El nuevo apartamento ya está ocupado")

    residente.id_apartamento = nuevo_apartamento.id
    db.commit()

    # Reasignación de apartamento
    if usuario_actual:
        registrar_auditoria(
            db=db,
            usuario_id=usuario_actual.id,
            usuario_nombre=usuario_actual.nombre,
            accion="Reasignación de apartamento a residente pendiente",
            tabla="residentes",
            objeto_previo=residente_previo,
            objeto_nuevo={c.name: getattr(residente, c.name) for c in residente.__table__.columns},
            request=request,
        )

    return {"mensaje": f"Residente {residente.nombre} reasignado al apartamento {numero_apartamento}"}


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
    estado_aprobacion: Optional[bool] = None,
):
    # Búsqueda avanzada de residentes con múltiples filtros
    query = db.query(models.Residente)

    if nombre:
        query = query.filter(func.lower(models.Residente.nombre).like(f"%{nombre.lower()}%"))
    if cedula:
        query = query.filter(func.lower(models.Residente.cedula).like(f"%{cedula.lower()}%"))
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
