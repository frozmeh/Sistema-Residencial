from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from sqlalchemy import func, and_
from . import models, schemas
from ..utils.db_helpers import guardar_y_refrescar
from decimal import Decimal

# =====================
# ---- CRUD Pagos -----
# =====================


def crear_pago(db: Session, pago: schemas.PagoCreate):
    # Validar residente
    residente = db.query(models.Residente).filter(models.Residente.id == pago.id_residente).first()
    if not residente:
        raise HTTPException(status_code=404, detail="El residente especificado no existe")
    if getattr(residente, "estado", None) != "Activo":
        raise HTTPException(status_code=400, detail="El residente no está activo")

    # Validación coherencia moneda / tipo_cambio
    if pago.moneda == "VES" and not pago.tipo_cambio_bcv:
        raise HTTPException(status_code=400, detail="Debe especificar tipo_cambio_bcv para pagos en VES")
    if pago.moneda == "USD" and pago.tipo_cambio_bcv:
        raise HTTPException(status_code=400, detail="No debe indicar tipo_cambio_bcv para pagos en USD")

    # Evitar pagos duplicados en mismo día y concepto
    pago_existente = (
        db.query(models.Pago)
        .filter(
            models.Pago.id_residente == pago.id_residente,
            models.Pago.concepto == pago.concepto,
            func.date(models.Pago.fecha_pago) == pago.fecha_pago.date(),
        )
        .first()
    )
    if pago_existente:
        raise HTTPException(status_code=400, detail="Ya existe un pago con el mismo concepto en esta fecha")

    nuevo_pago = models.Pago(**pago.model_dump())
    db.add(nuevo_pago)
    return guardar_y_refrescar(db, nuevo_pago)


def obtener_pagos(db: Session):
    pagos = db.query(models.Pago).order_by(models.Pago.fecha_creacion.desc()).all()
    if not pagos:
        raise HTTPException(status_code=404, detail="No hay pagos registrados")
    return pagos


def obtener_pago_por_id(db: Session, id_pago: int):
    pago = db.query(models.Pago).filter(models.Pago.id == id_pago).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return pago


def actualizar_pago(db: Session, id_pago: int, datos_actualizados: schemas.PagoUpdate):
    pago = obtener_pago_por_id(db, id_pago)
    datos = datos_actualizados.model_dump(exclude_unset=True)

    # Validaciones cruzadas
    if "id_residente" in datos:
        residente = db.query(models.Residente).filter(models.Residente.id == datos["id_residente"]).first()
        if not residente:
            raise HTTPException(status_code=404, detail="El nuevo residente no existe")
        if getattr(residente, "estado", None) != "Activo":
            raise HTTPException(status_code=400, detail="El nuevo residente no está activo")

    # Coherencia moneda / tipo_cambio
    moneda = datos.get("moneda")
    tipo_cambio = datos.get("tipo_cambio_bcv")
    if moneda == "VES" and (not tipo_cambio or tipo_cambio <= 0):
        raise HTTPException(status_code=400, detail="Debe especificar tipo_cambio_bcv válido para pagos en VES")
    if moneda == "USD" and tipo_cambio:
        raise HTTPException(status_code=400, detail="No debe indicar tipo_cambio_bcv para pagos en USD")

    # Coherencia verificado / estado
    if "verificado" in datos or "estado" in datos:
        verificado = datos.get("verificado", pago.verificado)
        estado = datos.get("estado", pago.estado)
        if verificado and estado not in ["Validado", "Rechazado"]:
            raise HTTPException(
                status_code=400,
                detail="Un pago verificado solo puede tener estado 'Validado' o 'Rechazado'",
            )

    for key, value in datos.items():
        setattr(pago, key, value)

    return guardar_y_refrescar(db, pago)


def eliminar_pago(db: Session, id_pago: int):
    pago = obtener_pago_por_id(db, id_pago)
    db.delete(pago)
    db.commit()
    return {"detalle": f"Pago con id {id_pago} eliminado correctamente"}


def filtrar_pagos(
    db: Session,
    id_residente: int = None,
    id_apartamento: int = None,
    estado: str = None,
    fecha_inicio: datetime = None,
    fecha_fin: datetime = None,
):
    query = db.query(models.Pago)

    if id_residente:
        query = query.filter(models.Pago.id_residente == id_residente)
    if id_apartamento:
        query = query.filter(models.Pago.id_apartamento == id_apartamento)
    if estado:
        query = query.filter(models.Pago.estado == estado)
    if fecha_inicio and fecha_fin:
        query = query.filter(and_(models.Pago.fecha_pago >= fecha_inicio, models.Pago.fecha_pago <= fecha_fin))
    elif fecha_inicio:
        query = query.filter(models.Pago.fecha_pago >= fecha_inicio)
    elif fecha_fin:
        query = query.filter(models.Pago.fecha_pago <= fecha_fin)

    pagos = query.order_by(models.Pago.fecha_pago.desc()).all()
    if not pagos:
        raise HTTPException(status_code=404, detail="No se encontraron pagos con los filtros aplicados")
    return pagos


def actualizar_estado_pago(db: Session, id_pago: int, nuevo_estado: str, verificado: bool = False):
    pago = obtener_pago_por_id(db, id_pago)

    if nuevo_estado not in ["Pendiente", "Validado", "Rechazado"]:
        raise HTTPException(status_code=400, detail="Estado de pago inválido")

    if verificado and nuevo_estado not in ["Validado", "Rechazado"]:
        raise HTTPException(
            status_code=400,
            detail="Un pago verificado solo puede tener estado 'Validado' o 'Rechazado'",
        )

    pago.estado = nuevo_estado
    pago.verificado = verificado or (nuevo_estado == "Validado")
    pago.fecha_actualizacion = datetime.now()

    return guardar_y_refrescar(db, pago)


def obtener_resumen_pagos(db: Session):
    resumen = (
        db.query(
            models.Pago.estado,
            func.count(models.Pago.id).label("cantidad"),
            func.sum(models.Pago.monto).label("total_pagado"),
        )
        .group_by(models.Pago.estado)
        .all()
    )

    if not resumen:
        raise HTTPException(status_code=404, detail="No hay pagos para generar resumen")

    # Mantener Decimal en total_pagado
    return [
        {"estado": r.estado, "cantidad": int(r.cantidad), "total_pagado": Decimal(r.total_pagado or 0)}
        for r in resumen
    ]
