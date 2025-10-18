from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/gastos", tags=["Gastos"])


# Gastos Fijos
@router.post("/fijos", response_model=schemas.GastoFijoOut)
def crear_gasto_fijo(gasto: schemas.GastoFijoCreate, db: Session = Depends(get_db)):
    return crud.crear_gasto_fijo(db, gasto)


@router.get("/fijos", response_model=list[schemas.GastoFijoOut])
def listar_gastos_fijos(db: Session = Depends(get_db)):
    return crud.obtener_gastos_fijos(db)


@router.delete("/fijos/{id_gasto}")
def eliminar_gasto_fijo(id_gasto: int, db: Session = Depends(get_db)):
    eliminado = crud.eliminar_gasto_fijo(db, id_gasto)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Gasto fijo no encontrado")
    return {"mensaje": "Gasto fijo eliminado correctamente"}


# Gastos Variables
@router.post("/variables", response_model=schemas.GastoVariableOut)
def crear_gasto_variable(
    gasto: schemas.GastoVariableCreate, db: Session = Depends(get_db)
):
    return crud.crear_gasto_variable(db, gasto)


@router.get("/variables", response_model=list[schemas.GastoVariableOut])
def listar_gastos_variables(db: Session = Depends(get_db)):
    return crud.obtener_gastos_variables(db)


@router.delete("/variables/{id_gasto}")
def eliminar_gasto_variable(id_gasto: int, db: Session = Depends(get_db)):
    eliminado = crud.eliminar_gasto_variable(db, id_gasto)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Gasto variable no encontrado")
    return {"mensaje": "Gasto variable eliminado correctamente"}
