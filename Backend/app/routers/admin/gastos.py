from fastapi import APIRouter, Depends, HTTPException, Query, Request
from datetime import date
from sqlalchemy.orm import Session
from typing import Optional, List, Union

from ... import schemas, crud, models
from ...database import get_db
from ...core.security import verificar_admin

router = APIRouter(prefix="/admin/gastos", tags=["Admin - Gastos"])

# =======================
# ---- GASTOS FIJOS ----
# =======================


@router.post(
    "/fijos",
    response_model=Union[schemas.GastoFijoOut, List[schemas.GastoFijoOut]],
    summary="Crear gasto fijo",
    description="Crea un gasto fijo. Si no se especifica apartamento, se distribuye entre todos.",
)
def crear_gasto_fijo_admin(
    gasto: schemas.GastoFijoCreate, request: Request, db: Session = Depends(get_db), admin=Depends(verificar_admin)
):
    return crud.crear_gasto_fijo(db, gasto, usuario_actual=admin, request=request)


@router.get(
    "/fijos",
    response_model=List[schemas.GastoFijoOut],
    summary="Listar gastos fijos",
    description="Obtiene todos los gastos fijos con filtros opcionales",
)
def listar_gastos_fijos_admin(
    responsable: Optional[str] = Query(None, description="Filtrar por responsable"),
    id_apartamento: Optional[int] = Query(None, description="Filtrar por ID de apartamento"),
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicial para filtrar"),
    fecha_fin: Optional[date] = Query(None, description="Fecha final para filtrar"),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=500, description="Límite de registros"),
    db: Session = Depends(get_db),
    admin=Depends(verificar_admin),
):
    gastos = crud.obtener_gastos_fijos(
        db, responsable=responsable, id_apartamento=id_apartamento, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    return gastos[skip : skip + limit]


@router.get("/fijos/{id_gasto}", response_model=schemas.GastoFijoOut, summary="Obtener gasto fijo específico")
def obtener_gasto_fijo_admin(id_gasto: int, db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    gasto = db.query(models.GastoFijo).filter(models.GastoFijo.id == id_gasto).first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto fijo no encontrado")
    return gasto


@router.put("/fijos/{id_gasto}", response_model=schemas.GastoFijoOut, summary="Actualizar gasto fijo")
def actualizar_gasto_fijo_admin(
    id_gasto: int,
    datos: schemas.GastoFijoCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(verificar_admin),
):
    return crud.actualizar_gasto_fijo(db, id_gasto, datos, usuario_actual=admin, request=request)


@router.delete("/fijos/{id_gasto}", summary="Eliminar gasto fijo")
def eliminar_gasto_fijo_admin(
    id_gasto: int, request: Request, db: Session = Depends(get_db), admin=Depends(verificar_admin)
):
    return crud.eliminar_gasto_fijo(db, id_gasto, usuario_actual=admin, request=request)


# ==========================
# ---- GASTOS VARIABLES ----
# ==========================


@router.post(
    "/variables",
    response_model=schemas.GastoVariableOut,
    summary="Crear gasto variable",
    description="Crea un gasto variable distribuido entre apartamentos especificados",
)
def crear_gasto_variable_admin(
    gasto: schemas.GastoVariableCreate, request: Request, db: Session = Depends(get_db), admin=Depends(verificar_admin)
):
    return crud.crear_gasto_variable(db, gasto, usuario_actual=admin, request=request)


@router.get(
    "/variables",
    response_model=List[schemas.GastoVariableOut],
    summary="Listar gastos variables",
    description="Obtiene todos los gastos variables con filtros opcionales",
)
def listar_gastos_variables_admin(
    responsable: Optional[str] = Query(None, description="Filtrar por responsable"),
    id_residente: Optional[int] = Query(None, description="Filtrar por ID de residente"),
    id_apartamento: Optional[int] = Query(None, description="Filtrar por ID de apartamento"),
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicial para filtrar"),
    fecha_fin: Optional[date] = Query(None, description="Fecha final para filtrar"),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=500, description="Límite de registros"),
    db: Session = Depends(get_db),
    admin=Depends(verificar_admin),
):
    gastos = crud.obtener_gastos_variables(
        db,
        responsable=responsable,
        id_residente=id_residente,
        id_apartamento=id_apartamento,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )
    return gastos[skip : skip + limit]


@router.get(
    "/variables/{id_gasto}", response_model=schemas.GastoVariableOut, summary="Obtener gasto variable específico"
)
def obtener_gasto_variable_admin(id_gasto: int, db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    gasto = db.query(models.GastoVariable).filter(models.GastoVariable.id == id_gasto).first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto variable no encontrado")
    return gasto


@router.put("/variables/{id_gasto}", response_model=schemas.GastoVariableOut, summary="Actualizar gasto variable")
def actualizar_gasto_variable_admin(
    id_gasto: int,
    datos: schemas.GastoVariableCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(verificar_admin),
):
    return crud.actualizar_gasto_variable(db, id_gasto, datos, usuario_actual=admin, request=request)


@router.delete("/variables/{id_gasto}", summary="Eliminar gasto variable")
def eliminar_gasto_variable_admin(
    id_gasto: int, request: Request, db: Session = Depends(get_db), admin=Depends(verificar_admin)
):
    return crud.eliminar_gasto_variable(db, id_gasto, usuario_actual=admin, request=request)
