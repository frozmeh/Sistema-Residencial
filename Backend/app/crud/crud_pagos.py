from sqlalchemy.orm import Session
from . import models, schemas
from fastapi import HTTPException
from . import models, schemas
from ..utils.db_helpers import guardar_y_refrescar
from ..utils.auditoria_decorator import auditar_completo


# ===============
# ---- Pagos ----
# ===============


@auditar_completo("pagos")
def crear_pago(db: Session, pago: schemas.PagoCreate):
    # Validar residente existente y activo
    residente = db.query(models.Residente).filter(models.Residente.id == pago.id_residente).first()
    if not residente or residente.estado != "Activo":
        raise HTTPException(status_code=400, detail="Residente no existe o no está activo")

    # Validar tipo de cambio si es VES
    if pago.moneda == "VES" and not pago.tipo_cambio_bcv:
        raise HTTPException(status_code=400, detail="Debe especificar tipo_cambio_bcv para pagos en VES")

    nuevo_pago = models.Pago(**pago.dict())
    db.add(nuevo_pago)
    return guardar_y_refrescar(db, nuevo_pago)


@auditar_completo("pagos")
def obtener_pagos(db: Session):
    return db.query(models.Pago).all()


@auditar_completo("pagos")
def obtener_pago_por_id(db: Session, id_pago: int):
    pago = db.query(models.Pago).filter(models.Pago.id == id_pago).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return pago


@auditar_completo("pagos")
def actualizar_pago(db: Session, id_pago: int, datos_actualizados: schemas.PagoUpdate):
    pago = obtener_pago_por_id(db, id_pago)

    # Validaciones cruzadas
    if datos_actualizados.id_residente:
        residente = db.query(models.Residente).filter(models.Residente.id == datos_actualizados.id_residente).first()
        if not residente or residente.estado != "Activo":
            raise HTTPException(status_code=400, detail="Residente no existe o no está activo")

    if datos_actualizados.moneda == "VES" and not datos_actualizados.tipo_cambio_bcv:
        raise HTTPException(status_code=400, detail="Debe especificar tipo_cambio_bcv para pagos en VES")

    for key, value in datos_actualizados.dict(exclude_unset=True).items():
        setattr(pago, key, value)

    return guardar_y_refrescar(db, pago)


@auditar_completo("pagos")
def eliminar_pago(db: Session, id_pago: int):
    pago = obtener_pago_por_id(db, id_pago)
    db.delete(pago)
    db.commit()
    return {"detalle": f"Pago con id {id_pago} eliminado correctamente"}
