from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from enum import Enum

from ... import schemas, crud
from ...database import get_db
from ...core.security import verificar_admin

router = APIRouter(prefix="/pagos", tags=["Pagos"])


# ----- Enum para validación de estado -----
class EstadoPagoEnum(str, Enum):
    PENDIENTE = "Pendiente"
    VALIDADO = "Validado"
    RECHAZADO = "Rechazado"


@router.get("/", response_model=List[schemas.PagoOut])
def listar_pagos_admin(
    admin: dict = Depends(verificar_admin),
    db: Session = Depends(get_db),
):
    return crud.obtener_pagos(db)


@router.get("/filtros", response_model=List[schemas.PagoOut])
def filtrar_pagos_admin(
    admin: dict = Depends(verificar_admin),
    db: Session = Depends(get_db),
    id_residente: Optional[int] = Query(None),
    id_apartamento: Optional[int] = Query(None),
    estado: Optional[schemas.EstadoPago] = Query(None),
    fecha_inicio: Optional[datetime] = Query(None),
    fecha_fin: Optional[datetime] = Query(None),
):
    # Validación fechas
    if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
        raise HTTPException(status_code=400, detail="fecha_inicio no puede ser mayor a fecha_fin")
    return crud.filtrar_pagos(
        db,
        id_residente=id_residente,
        id_apartamento=id_apartamento,
        estado=estado.value if estado else None,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )


@router.get("/{id_pago}", response_model=schemas.PagoOut)
def obtener_pago_admin(
    id_pago: int,
    admin: dict = Depends(verificar_admin),
    db: Session = Depends(get_db),
):
    return crud.obtener_pago_por_id(db, id_pago)


@router.put("/{id_pago}", response_model=schemas.PagoOut)
def actualizar_pago_admin(
    id_pago: int,
    datos_actualizados: schemas.PagoUpdate,
    admin: dict = Depends(verificar_admin),
    db: Session = Depends(get_db),
):
    return crud.actualizar_pago(db, id_pago, datos_actualizados)


@router.put("/{id_pago}/estado", response_model=schemas.PagoOut)
def actualizar_estado_pago_admin(
    id_pago: int,
    nuevo_estado: schemas.EstadoPago,
    verificado: bool = False,
    admin: dict = Depends(verificar_admin),
    db: Session = Depends(get_db),
):
    return crud.actualizar_estado_pago(db, id_pago, nuevo_estado.value, verificado)


@router.delete("/{id_pago}")
def eliminar_pago_admin(
    id_pago: int,
    admin: dict = Depends(verificar_admin),
    db: Session = Depends(get_db),
):
    return crud.eliminar_pago(db, id_pago)


@router.get("/resumen/general")
def obtener_resumen_pagos_admin(
    admin: dict = Depends(verificar_admin),
    db: Session = Depends(get_db),
):
    return crud.obtener_resumen_pagos(db)
