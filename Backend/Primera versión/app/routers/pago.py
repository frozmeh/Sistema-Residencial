from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import SessionLocal

router = APIRouter(prefix="/pagos", tags=["Pagos"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.PagoOut)
def crear(pago: schemas.PagoCreate, db: Session = Depends(get_db)):
    return crud.crear_pago(db, pago)

@router.get("/", response_model=list[schemas.PagoOut])
def leer_pagos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.obtener_pagos(db, skip=skip, limit=limit)

@router.get("/{id_pago}", response_model=schemas.PagoOut)
def leer_pago(id_pago: int, db: Session = Depends(get_db)):
    db_pago = crud.obtener_pago(db, id_pago)
    if not db_pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return db_pago

@router.put("/{id_pago}", response_model=schemas.PagoOut)
def actualizar(id_pago: int, pago: schemas.PagoUpdate, db: Session = Depends(get_db)):
    db_pago = crud.actualizar_pago(db, id_pago, pago)
    if not db_pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return db_pago

@router.delete("/{id_pago}", response_model=schemas.PagoOut)
def eliminar(id_pago: int, db: Session = Depends(get_db)):
    db_pago = crud.eliminar_pago(db, id_pago)
    if not db_pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return db_pago
