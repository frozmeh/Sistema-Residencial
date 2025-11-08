from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional, List, Union

from .. import schemas, crud
from ..database import get_db
from ..core.security import verificar_admin, verificar_residente  # funciones existentes

router = APIRouter(prefix="/gastos", tags=["Gastos"])


# =======================
# ---- GASTOS FIJOS ----
# =======================


@router.post(
    "/fijos",
    response_model=Union[schemas.GastoFijoOut, List[schemas.GastoFijoOut]],
    dependencies=[Depends(verificar_admin)],
)
def crear_gasto_fijo_admin(gasto: schemas.GastoFijoCreate, db: Session = Depends(get_db)):
    """Crea un gasto fijo (solo admin)."""
    return crud.crear_gasto_fijo(db, gasto)


@router.get("/fijos/admin", response_model=List[schemas.GastoFijoOut], dependencies=[Depends(verificar_admin)])
def listar_gastos_fijos_admin(responsable: Optional[str] = None, db: Session = Depends(get_db)):
    """Admin ve todos los gastos fijos."""
    return crud.obtener_gastos_fijos(db, responsable=responsable)


@router.put("/fijos/{id_gasto}", response_model=schemas.GastoFijoOut, dependencies=[Depends(verificar_admin)])
def actualizar_gasto_fijo_admin(id_gasto: int, datos: schemas.GastoFijoCreate, db: Session = Depends(get_db)):
    """Actualizar gasto fijo (solo admin)."""
    return crud.actualizar_gasto_fijo(db, id_gasto, datos)


@router.delete("/fijos/{id_gasto}", dependencies=[Depends(verificar_admin)])
def eliminar_gasto_fijo_admin(id_gasto: int, db: Session = Depends(get_db)):
    """Eliminar gasto fijo (solo admin)."""
    return crud.eliminar_gasto_fijo(db, id_gasto)


# --- RESIDENTE ---
@router.get("/fijos", response_model=List[schemas.GastoFijoOut])
def listar_gastos_fijos_residente(residente: dict = Depends(verificar_residente), db: Session = Depends(get_db)):
    """Residente ve solo los gastos de su apartamento."""
    return crud.obtener_gastos_fijos(db, id_apartamento=residente["id_apartamento"])


# ==========================
# ---- GASTOS VARIABLES ----
# ==========================


# --- ADMIN ---
@router.post(
    "/variables",
    response_model=Union[schemas.GastoVariableOut, List[schemas.GastoVariableOut]],
    dependencies=[Depends(verificar_admin)],
)
def crear_gasto_variable_admin(gasto: schemas.GastoVariableCreate, db: Session = Depends(get_db)):
    """Crear gasto variable (solo admin)."""
    return crud.crear_gasto_variable(db, gasto)


@router.get("/variables/admin", response_model=List[schemas.GastoVariableOut], dependencies=[Depends(verificar_admin)])
def listar_gastos_variables_admin(responsable: Optional[str] = None, db: Session = Depends(get_db)):
    """Admin ve todos los gastos variables."""
    return crud.obtener_gastos_variables(db, responsable=responsable)


@router.put("/variables/{id_gasto}", response_model=schemas.GastoVariableOut, dependencies=[Depends(verificar_admin)])
def actualizar_gasto_variable_admin(id_gasto: int, datos: schemas.GastoVariableCreate, db: Session = Depends(get_db)):
    """Actualizar gasto variable (solo admin)."""
    return crud.actualizar_gasto_variable(db, id_gasto, datos)


@router.delete("/variables/{id_gasto}", dependencies=[Depends(verificar_admin)])
def eliminar_gasto_variable_admin(id_gasto: int, db: Session = Depends(get_db)):
    """Eliminar gasto variable (solo admin)."""
    return crud.eliminar_gasto_variable(db, id_gasto)


# --- RESIDENTE ---
@router.get("/variables", response_model=List[schemas.GastoVariableOut])
def listar_gastos_variables_residente(residente: dict = Depends(verificar_residente), db: Session = Depends(get_db)):
    """Residente ve solo los gastos de su apartamento o los asignados directamente a él."""
    return crud.obtener_gastos_variables(db, id_apartamento=residente["id_apartamento"], id_residente=residente["id"])
