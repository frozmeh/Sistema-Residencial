from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from .. import schemas, crud, models
from ..database import get_db


router = APIRouter(prefix="/pagos", tags=["Pagos"])


@router.post("/", response_model=schemas.PagoOut)
def crear_pago(pago: schemas.PagoCreate, db: Session = Depends(get_db)):
    residente = (
        db.query(models.Residente)
        .filter(models.Residente.id == pago.id_residente)
        .first()
    )
    if not residente:
        raise HTTPException(status_code=400, detail="El residente no existe")
    return crud.crear_pago(db, pago)


@router.get("/", response_model=list[schemas.PagoOut])
def listar_pagos(db: Session = Depends(get_db)):
    return crud.obtener_pagos(db)


@router.get("/{id_pago}", response_model=schemas.PagoOut)
def obtener_pago(id_pago: int, db: Session = Depends(get_db)):
    pago = crud.obtener_pago_por_id(db, id_pago)
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return pago


@router.put("/{id_pago}", response_model=schemas.PagoOut)
def actualizar_pago(
    id_pago: int, datos_actualizados: schemas.PagoUpdate, db: Session = Depends(get_db)
):
    pago_actualizado = crud.actualizar_pago(db, id_pago, datos_actualizados)
    if not pago_actualizado:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return pago_actualizado


@router.delete("/{id_pago}")
def eliminar_pago(id_pago: int, db: Session = Depends(get_db)):
    eliminado = crud.eliminar_pago(db, id_pago)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return {"mensaje": f"Pago {id_pago} eliminado correctamente"}
