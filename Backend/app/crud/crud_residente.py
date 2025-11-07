# crud/residentes.py (versión mejorada)
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, aliased
from sqlalchemy.exc import IntegrityError

from ..utils.db_helpers import guardar_y_refrescar
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


def crear_residente(db: Session, datos: schemas.ResidenteCreate, id_usuario: int):
    # Normalizar entradas
    torre_nombre = datos.torre.strip() if datos.torre else ""
    numero_apto = str(datos.numero_apartamento).strip()
    cedula_norm = datos.cedula.strip()
    correo_norm = datos.correo.strip().lower() if datos.correo else None

    # Buscar torre -> piso -> apartamento (usar ilike / func.lower para evitar mayúsc/minúsc)
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

    # Validar que el usuario no tenga ya un residente asociado
    if db.query(models.Residente).filter(models.Residente.id_usuario == id_usuario).first():
        raise HTTPException(status_code=400, detail="El usuario ya tiene un residente asociado.")

    # Crear residente pendiente (no ocupamos el apto todavía)
    nuevo_residente = models.Residente(
        id_usuario=id_usuario,
        tipo_residente=datos.tipo_residente,
        nombre=datos.nombre.strip(),
        cedula=cedula_norm,
        correo=correo_norm,
        telefono=datos.telefono.strip() if datos.telefono else None,
        id_apartamento=apartamento.id,
        estado="Activo",  # o "Pendiente" si prefieres
        validado=False,
        residente_actual=False,
    )

    try:
        db.add(nuevo_residente)
        guardar_y_refrescar(db, nuevo_residente)
        return nuevo_residente
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error de integridad: posible duplicado.")


def aprobar_residente(db: Session, id_residente: int):
    residente = get_residente_or_404(db, id_residente)

    apartamento = db.query(models.Apartamento).filter(models.Apartamento.id == residente.id_apartamento).first()
    if not apartamento:
        raise HTTPException(status_code=404, detail="Apartamento asociado no encontrado.")

    if apartamento.estado.lower() == "ocupado":
        raise HTTPException(status_code=400, detail="El apartamento ya está ocupado por otro residente.")

    # Intentar aprobar y ocupar apartamento en una transacción
    try:
        residente.validado = True
        residente.residente_actual = True
        residente.estado = "Activo"
        apartamento.estado = "Ocupado"
        db.commit()
        db.refresh(residente)
        return {"mensaje": f"Residente {residente.nombre} validado y asignado correctamente.", "residente": residente}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error al aprobar residente. Intenta de nuevo.")


def rechazar_residente(db: Session, id_residente: int, motivo: str = "Registro rechazado por el administrador."):
    residente = get_residente_or_404(db, id_residente)

    residente.validado = False
    residente.estado = "Inactivo"
    residente.residente_actual = False

    db.commit()
    return {"mensaje": motivo}


def obtener_residentes(db: Session):
    return db.query(models.Residente).order_by(models.Residente.id.asc()).all()


def obtener_residente_por_id(db: Session, id_residente: int):
    residente = get_residente_or_404(db, id_residente)
    return residente


def actualizar_residente(db: Session, id_residente: int, datos_actualizados: schemas.ResidenteUpdateResidente):
    residente = obtener_residente_por_id(db, id_residente)
    update_data = datos_actualizados.dict(exclude_unset=True)

    validar_unicidad_residente(db, update_data.get("cedula"), update_data.get("correo"), id_residente)

    for key, value in update_data.items():
        setattr(residente, key, value)

    try:
        return guardar_y_refrescar(db, residente)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al actualizar: datos duplicados o conflicto de integridad.",
        )


def eliminar_residente(db: Session, id_residente: int):
    residente = obtener_residente_por_id(db, id_residente)

    # Liberar apartamento si existe
    if residente.id_apartamento:
        apartamento = db.query(models.Apartamento).filter(models.Apartamento.id == residente.id_apartamento).first()
        if apartamento:
            apartamento.estado = "Disponible"
            # si existe id_residente en la tabla apartamento, limpiarlo
            if hasattr(apartamento, "id_residente"):
                apartamento.id_residente = None

    db.delete(residente)
    db.commit()
    return {"mensaje": f"Residente con ID {id_residente} eliminado correctamente."}


def asignar_residente_a_apartamento(db: Session, id_residente: int, id_apartamento: int):
    residente = get_residente_or_404(db, id_residente)

    apartamento = db.query(models.Apartamento).filter(models.Apartamento.id == id_apartamento).first()
    if not apartamento:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado.")

    if residente.id_apartamento:
        raise HTTPException(status_code=400, detail="El residente ya tiene un apartamento asignado.")
    if apartamento.estado.lower() == "ocupado":
        raise HTTPException(status_code=400, detail="El apartamento ya está ocupado.")

    residente.id_apartamento = apartamento.id
    apartamento.estado = "Ocupado"
    if hasattr(apartamento, "id_residente"):
        apartamento.id_residente = residente.id

    db.commit()
    db.refresh(residente)
    db.refresh(apartamento)
    return {
        "mensaje": f"Residente {residente.nombre} asignado al apartamento {apartamento.numero}.",
        "residente": residente,
    }


def desasignar_residente(db: Session, id_residente: int, inactivar: bool = False):
    residente = get_residente_or_404(db, id_residente)

    if residente.id_apartamento:
        apartamento = db.query(models.Apartamento).filter(models.Apartamento.id == residente.id_apartamento).first()
        if apartamento:
            apartamento.estado = "Disponible"
            if hasattr(apartamento, "id_residente"):
                apartamento.id_residente = None
        residente.id_apartamento = None

    if inactivar:
        residente.estado = "Inactivo"
        residente.residente_actual = False

    guardar_y_refrescar(db, residente)
    return {"mensaje": f"Residente {residente.nombre} desasignado correctamente.", "estado": residente.estado}


def activar_residente(db: Session, id_residente: int):
    residente = obtener_residente_por_id(db, id_residente)
    residente.estado = "Activo"
    residente.residente_actual = True

    guardar_y_refrescar(db, residente)
    return {"mensaje": f"Residente {residente.nombre} activado correctamente.", "estado": residente.estado}


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
        .filter(Residente.validado == False)
    )

    if torre:
        query = query.filter(func.lower(Torre.nombre) == torre.lower())
    if piso:
        query = query.filter(Piso.numero == piso)

    resultados = query.order_by(Residente.fecha_registro.asc()).all()

    return [
        {
            "id": r.id,
            "nombre": r.nombre,
            "cedula": r.cedula,
            "correo": r.correo,
            "telefono": r.telefono,
            "tipo_residente": r.tipo_residente,
            "fecha_registro": r.fecha_registro,
            "torre": r.torre,
            "piso": r.piso,
            "apartamento": r.apartamento,
        }
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
        query = query.filter(models.Residente.estado == "Activo")
    return query.scalar()


def obtener_historial_residentes_por_apartamento(db: Session, id_apartamento: int):
    return (
        db.query(models.Residente)
        .filter(models.Residente.id_apartamento == id_apartamento)
        .order_by(models.Residente.fecha_registro.asc())
        .all()
    )
