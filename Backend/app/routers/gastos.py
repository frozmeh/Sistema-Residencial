from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/gastos", tags=["Gastos"])


# =======================
# ---- Gastos Fijos -----
# =======================


@router.post("/fijos", response_model=schemas.GastoFijoOut)
def crear_gasto_fijo(gasto: schemas.GastoFijoCreate, db: Session = Depends(get_db)):
    return crud.crear_gasto_fijo(db, gasto)


@router.get("/fijos", response_model=list[schemas.GastoFijoOut])
def listar_gastos_fijos(responsable: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.obtener_gastos_fijos(db, responsable)


@router.put("/fijos/{id_gasto}", response_model=schemas.GastoFijoOut)
def actualizar_gasto_fijo(id_gasto: int, datos: schemas.GastoFijoCreate, db: Session = Depends(get_db)):
    return crud.actualizar_gasto_fijo(db, id_gasto, datos)


@router.delete("/fijos/{id_gasto}")
def eliminar_gasto_fijo(id_gasto: int, db: Session = Depends(get_db)):
    crud.eliminar_gasto_fijo(db, id_gasto)


# ==========================
# ---- Gastos Variables ----
# ==========================


@router.post("/variables", response_model=schemas.GastoVariableOut)
def crear_gasto_variable(gasto: schemas.GastoVariableCreate, db: Session = Depends(get_db)):
    return crud.crear_gasto_variable(db, gasto)


@router.get("/variables", response_model=list[schemas.GastoVariableOut])
def listar_gastos_variables(responsable: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.obtener_gastos_variables(db, responsable)


@router.put("/variables/{id_gasto}", response_model=schemas.GastoVariableOut)
def actualizar_gasto_variable(id_gasto: int, datos: schemas.GastoVariableCreate, db: Session = Depends(get_db)):
    return crud.actualizar_gasto_variable(db, id_gasto, datos)


@router.delete("/variables/{id_gasto}")
def eliminar_gasto_variable(id_gasto: int, db: Session = Depends(get_db)):
    crud.eliminar_gasto_variable(db, id_gasto)
