from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db


router = APIRouter(prefix="/pagos", tags=["Pagos"])


@router.post("/", response_model=schemas.PagoOut)
def crear_pago(pago: schemas.PagoCreate, db: Session = Depends(get_db)):
    return crud.crear_pago(db, pago)


@router.get("/", response_model=list[schemas.PagoOut])
def listar_pagos(db: Session = Depends(get_db)):
    return crud.obtener_pagos(db)


@router.get("/{id_pago}", response_model=schemas.PagoOut)
def obtener_pago(id_pago: int, db: Session = Depends(get_db)):
    return crud.obtener_pago_por_id(db, id_pago)


@router.put("/{id_pago}", response_model=schemas.PagoOut)
def actualizar_pago(id_pago: int, datos_actualizados: schemas.PagoUpdate, db: Session = Depends(get_db)):
    return crud.actualizar_pago(db, id_pago, datos_actualizados)


@router.delete("/{id_pago}")
def eliminar_pago(id_pago: int, db: Session = Depends(get_db)):
    return crud.eliminar_pago(db, id_pago)
