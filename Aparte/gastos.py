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
    description="Crea un gasto fijo. Si no se especifica apartamento, se distribuye entre todos usando porcentajes de aporte.",
)
def crear_gasto_fijo_admin(
    gasto: schemas.GastoFijoCreate, request: Request, db: Session = Depends(get_db), admin=Depends(verificar_admin)
):
    """
    Crea un gasto fijo:
    - Si se especifica id_apartamento: crea un gasto para ese apartamento específico
    - Si NO se especifica id_apartamento: distribuye el gasto entre todos los apartamentos según su porcentaje de aporte
    """
    return crud.crear_gasto_fijo(db, gasto, usuario_actual=admin, request=request)


@router.get(
    "/fijos",
    response_model=List[schemas.GastoFijoOut],
    summary="Listar gastos fijos",
    description="Obtiene todos los gastos fijos con filtros opcionales. Por defecto usa tasas históricas.",
)
def listar_gastos_fijos_admin(
    responsable: Optional[str] = Query(None, description="Filtrar por responsable"),
    id_apartamento: Optional[int] = Query(None, description="Filtrar por ID de apartamento"),
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicial para filtrar"),
    fecha_fin: Optional[date] = Query(None, description="Fecha final para filtrar"),
    actualizar_tasa: bool = Query(False, description="Actualizar montos con tasa BCV actual"),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=500, description="Límite de registros"),
    db: Session = Depends(get_db),
    admin=Depends(verificar_admin),
):
    gastos = crud.obtener_gastos_fijos(
        db,
        responsable=responsable,
        id_apartamento=id_apartamento,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        actualizar_tasa=actualizar_tasa,
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
    description="Crea un gasto variable distribuido entre apartamentos especificados (directamente o por pisos/torres).",
)
def crear_gasto_variable_admin(
    gasto: schemas.GastoVariableCreate, request: Request, db: Session = Depends(get_db), admin=Depends(verificar_admin)
):
    """
    Crea un gasto variable distribuido entre apartamentos:
    - Puede especificar apartamentos directamente (id_apartamentos)
    - O especificar pisos (id_pisos) o torres (id_torres) para incluir todos sus apartamentos
    - Los montos se distribuyen según porcentajes de aporte de cada apartamento
    """
    return crud.crear_gasto_variable(db, gasto, usuario_actual=admin, request=request)


@router.get(
    "/variables",
    response_model=List[schemas.GastoVariableOut],
    summary="Listar gastos variables",
    description="Obtiene todos los gastos variables con filtros opcionales.",
)
def listar_gastos_variables_admin(
    responsable: Optional[str] = Query(None, description="Filtrar por responsable"),
    id_residente: Optional[int] = Query(None, description="Filtrar por ID de residente"),
    id_apartamento: Optional[int] = Query(None, description="Filtrar por ID de apartamento"),
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicial para filtrar"),
    fecha_fin: Optional[date] = Query(None, description="Fecha final para filtrar"),
    actualizar_tasa: bool = Query(True, description="Actualizar montos con tasa BCV actual"),
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
        actualizar_tasa=actualizar_tasa,
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


# ==========================
# ---- ENDPOINTS ADICIONALES ----
# ==========================


@router.get(
    "/resumen/general",
    summary="Resumen general de gastos",
    description="Obtiene un resumen general de todos los gastos (fijos y variables).",
)
def resumen_gastos_general_admin(
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicial para filtrar"),
    fecha_fin: Optional[date] = Query(None, description="Fecha final para filtrar"),
    db: Session = Depends(get_db),
    admin=Depends(verificar_admin),
):
    """Resumen completo de gastos para administración"""
    # Obtener gastos fijos
    gastos_fijos = crud.obtener_gastos_fijos(db, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, actualizar_tasa=False)

    # Obtener gastos variables
    gastos_variables = crud.obtener_gastos_variables(
        db, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, actualizar_tasa=False
    )

    # Calcular totales
    total_fijos_usd = sum(g.monto_usd for g in gastos_fijos) if gastos_fijos else 0
    total_variables_usd = sum(g.monto_usd for g in gastos_variables) if gastos_variables else 0
    total_general_usd = total_fijos_usd + total_variables_usd

    # Calcular saldos pendientes
    saldo_fijos = sum(g.saldo_pendiente for g in gastos_fijos) if gastos_fijos else 0
    saldo_variables = sum(g.saldo_pendiente for g in gastos_variables) if gastos_variables else 0
    saldo_total = saldo_fijos + saldo_variables

    return {
        "resumen": {
            "total_gastos_fijos": len(gastos_fijos),
            "total_gastos_variables": len(gastos_variables),
            "total_gastos_general": len(gastos_fijos) + len(gastos_variables),
            "total_fijos_usd": float(total_fijos_usd),
            "total_variables_usd": float(total_variables_usd),
            "total_general_usd": float(total_general_usd),
            "saldo_pendiente_fijos": float(saldo_fijos),
            "saldo_pendiente_variables": float(saldo_variables),
            "saldo_pendiente_total": float(saldo_total),
            "porcentaje_pagado": (
                (total_general_usd - saldo_total) / total_general_usd * 100 if total_general_usd > 0 else 0
            ),
        },
        "periodo": {
            "fecha_inicio": fecha_inicio.isoformat() if fecha_inicio else None,
            "fecha_fin": fecha_fin.isoformat() if fecha_fin else None,
        },
        "ultima_actualizacion": date.today().isoformat(),
    }
