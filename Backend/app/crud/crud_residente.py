from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..utils.db_helpers import guardar_y_refrescar
from .. import models, schemas


# ====================
# ---- Residentes ----
# ====================


def crear_residente(db: Session, residente: schemas.ResidenteCreate):
    # Verificar si el usuario ya tiene un residente asignado
    existente = db.query(models.Residente).filter(models.Residente.id_usuario == residente.id_usuario).first()
    if existente:
        raise HTTPException(
            status_code=400,
            detail=f"El usuario con ID {residente.id_usuario} ya está asociado a otro residente.",
        )

    # Validar cédula única
    existente_cedula = db.query(models.Residente).filter(models.Residente.cedula == residente.cedula).first()
    if existente_cedula:
        raise HTTPException(
            status_code=400,
            detail=f"La cédula {residente.cedula} ya está registrada.",
        )

    # Validar correo único si se proporciona
    if residente.correo:
        existente_correo = db.query(models.Residente).filter(models.Residente.correo == residente.correo).first()
        if existente_correo:
            raise HTTPException(
                status_code=400,
                detail=f"El correo {residente.correo} ya está registrado.",
            )

    # Crear residente
    nuevo_residente = models.Residente(**residente.dict())
    db.add(nuevo_residente)
    try:
        return guardar_y_refrescar(db, nuevo_residente)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad: Verifica que la cédula y el usuario no estén duplicados.",
        )


def obtener_residentes(db: Session):
    return db.query(models.Residente).order_by(models.Residente.id.asc()).all()


def obtener_residente_por_id(db: Session, id_residente: int):
    residente = db.query(models.Residente).filter(models.Residente.id == id_residente).first()
    if not residente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró un residente con ID {id_residente}.",
        )
    return residente


def actualizar_residente(db: Session, id_residente: int, datos_actualizados: schemas.ResidenteUpdate):
    residente = obtener_residente_por_id(db, id_residente)

    # Validaciones para cédula y correo únicos
    update_data = datos_actualizados.dict(exclude_unset=True)
    if "cedula" in update_data:
        existente_cedula = (
            db.query(models.Residente)
            .filter(models.Residente.cedula == update_data["cedula"], models.Residente.id != id_residente)
            .first()
        )
        if existente_cedula:
            raise HTTPException(status_code=400, detail=f"La cédula {update_data['cedula']} ya está registrada.")
    if "correo" in update_data:
        existente_correo = (
            db.query(models.Residente)
            .filter(models.Residente.correo == update_data["correo"], models.Residente.id != id_residente)
            .first()
        )
        if existente_correo:
            raise HTTPException(status_code=400, detail=f"El correo {update_data['correo']} ya está registrado.")

    # Actualizar campos
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
    db.delete(residente)
    db.commit()
    return {"mensaje": f"Residente con ID {id_residente} eliminado correctamente."}


def asignar_residente_a_apartamento(db: Session, id_residente: int, id_apartamento: int):
    residente = db.query(models.Residente).filter(models.Residente.id == id_residente).first()
    apartamento = db.query(models.Apartamento).filter(models.Apartamento.id == id_apartamento).first()

    if not residente:
        raise HTTPException(status_code=404, detail=f"No se encontró el residente con ID {id_residente}.")
    if not apartamento:
        raise HTTPException(status_code=404, detail=f"No se encontró el apartamento con ID {id_apartamento}.")

    if residente.id_apartamento:
        raise HTTPException(status_code=400, detail="El residente ya tiene un apartamento asignado.")
    if apartamento.estado == "Ocupado":
        raise HTTPException(status_code=400, detail="El apartamento ya está ocupado.")

    residente.id_apartamento = apartamento.id
    apartamento.estado = "Ocupado"
    apartamento.id_residente = residente.id  # coherencia bidireccional

    db.commit()
    db.refresh(residente)
    db.refresh(apartamento)

    return {"mensaje": f"Residente {residente.nombre} asignado al apartamento {apartamento.numero}."}


def desasignar_residente(db: Session, id_residente: int, inactivar: bool = False):
    residente = db.query(models.Residente).filter(models.Residente.id == id_residente).first()
    if not residente:
        raise HTTPException(status_code=404, detail="Residente no encontrado.")

    if residente.id_apartamento:
        apartamento = db.query(models.Apartamento).filter(models.Apartamento.id == residente.id_apartamento).first()
        if apartamento:
            apartamento.estado = "Disponible"
            apartamento.id_residente = None
        residente.id_apartamento = None

    if inactivar:
        residente.estado = "Inactivo"
        residente.residente_actual = False

    db.commit()
    db.refresh(residente)

    return {
        "mensaje": f"Residente {residente.nombre} desasignado correctamente.",
        "estado": residente.estado,
    }


def activar_residente(db: Session, id_residente: int):
    residente = obtener_residente_por_id(db, id_residente)

    residente.estado = "Activo"
    residente.residente_actual = True

    db.commit()
    db.refresh(residente)

    return {"mensaje": f"Residente {residente.nombre} activado correctamente.", "estado": residente.estado}
