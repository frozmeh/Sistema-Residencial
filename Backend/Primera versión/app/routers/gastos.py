from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import SessionLocal

router = APIRouter(prefix="/gastos", tags=["Gastos"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Gasto Fijo
@router.post("/fijo/", response_model=schemas.GastoFijoOut)
def crear_gasto_fijo(gasto: schemas.GastoFijoCreate, db: Session = Depends(get_db)):
    return crud.crear_gasto_fijo(db, gasto)

@router.get("/fijo/", response_model=list[schemas.GastoFijoOut])
def leer_gastos_fijos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.obtener_gastos_fijos(db, skip=skip, limit=limit)

# Gasto Variable
@router.post("/variable/", response_model=schemas.GastoVariableOut)
def crear_gasto_variable(gasto: schemas.GastoVariableCreate, db: Session = Depends(get_db)):
    return crud.crear_gasto_variable(db, gasto)

@router.get("/variable/", response_model=list[schemas.GastoVariableOut])
def leer_gastos_variables(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.obtener_gastos_variables(db, skip=skip, limit=limit)
