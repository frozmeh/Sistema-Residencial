from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import date
from sqlalchemy.orm import Session
from typing import List, Optional

from ... import schemas, crud, models
from ...database import get_db
from ...core.security import verificar_residente

router = APIRouter(prefix="/residente/gastos", tags=["Residente - Gastos"])  # ✅ Prefijo más específico

# =======================
# ---- GASTOS FIJOS ----
# =======================


@router.get(
    "/fijos",
    response_model=List[schemas.GastoFijoOut],
    summary="Mis gastos fijos",
    description="Obtiene los gastos fijos asociados a mi apartamento",
)
def listar_gastos_fijos_residente(
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicial para filtrar"),
    fecha_fin: Optional[date] = Query(None, description="Fecha final para filtrar"),
    residente: dict = Depends(verificar_residente),
    db: Session = Depends(get_db),
):
    if not residente.get("id_apartamento"):
        raise HTTPException(status_code=400, detail="No tienes un apartamento asignado")

    gastos = crud.obtener_gastos_fijos(
        db,
        id_apartamento=residente["id_apartamento"],
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        actualizar_tasa=True,
    )

    if not gastos:
        raise HTTPException(status_code=404, detail="No se encontraron gastos fijos asociados a tu apartamento.")

    return gastos


@router.get("/fijos/{id_gasto}", response_model=schemas.GastoFijoOut, summary="Obtener gasto fijo específico")
def obtener_gasto_fijo_residente(
    id_gasto: int, residente: dict = Depends(verificar_residente), db: Session = Depends(get_db)
):
    """Obtiene un gasto fijo específico solo si pertenece al apartamento del residente"""
    gasto = db.query(models.GastoFijo).filter(models.GastoFijo.id == id_gasto).first()

    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto fijo no encontrado")

    # Solo puede ver gastos de SU apartamento
    if gasto.id_apartamento != residente.get("id_apartamento"):
        raise HTTPException(status_code=403, detail="No tienes permiso para ver este gasto")

    return gasto


# ==========================
# ---- GASTOS VARIABLES ----
# ==========================


@router.get(
    "/variables",
    response_model=List[schemas.GastoVariableOut],
    summary="Mis gastos variables",
    description="Obtiene los gastos variables asociados a mi apartamento",
)
def listar_gastos_variables_residente(
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicial para filtrar"),
    fecha_fin: Optional[date] = Query(None, description="Fecha final para filtrar"),
    residente: dict = Depends(verificar_residente),
    db: Session = Depends(get_db),
):
    if not residente.get("id_apartamento"):
        raise HTTPException(status_code=400, detail="No tienes un apartamento asignado")

    gastos = crud.obtener_gastos_variables(
        db,
        id_apartamento=residente["id_apartamento"],
        id_residente=residente["id"],
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        actualizar_tasa=True,
    )

    if not gastos:
        raise HTTPException(status_code=404, detail="No se encontraron gastos variables asociados a tu cuenta.")

    return gastos


@router.get(
    "/variables/{id_gasto}", response_model=schemas.GastoVariableOut, summary="Obtener gasto variable específico"
)
def obtener_gasto_variable_residente(
    id_gasto: int, residente: dict = Depends(verificar_residente), db: Session = Depends(get_db)
):
    """Obtiene un gasto variable específico solo si está asociado a su apartamento"""
    gasto = db.query(models.GastoVariable).filter(models.GastoVariable.id == id_gasto).first()

    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto variable no encontrado")

    # Verificar si el gasto está asociado a su apartamento
    asociado = (
        db.query(models.gastos_variables_apartamentos)
        .filter(
            models.gastos_variables_apartamentos.c.id_gasto_variable == id_gasto,
            models.gastos_variables_apartamentos.c.id_apartamento == residente.get("id_apartamento"),
        )
        .first()
    )

    if not asociado and gasto.id_residente != residente.get("id"):
        raise HTTPException(status_code=403, detail="No tienes permiso para ver este gasto")

    return gasto


@router.get(
    "/resumen", summary="Resumen de mis gastos", description="Obtiene un resumen de todos los gastos del residente"
)
def resumen_gastos_residente(residente: dict = Depends(verificar_residente), db: Session = Depends(get_db)):
    """Resumen completo de gastos para el residente"""
    if not residente.get("id_apartamento"):
        raise HTTPException(status_code=400, detail="No tienes un apartamento asignado")

    # Obtener gastos fijos
    gastos_fijos = crud.obtener_gastos_fijos(db, id_apartamento=residente["id_apartamento"])

    # Obtener gastos variables
    gastos_variables = crud.obtener_gastos_variables(
        db, id_apartamento=residente["id_apartamento"], id_residente=residente["id"]
    )

    total_fijos_usd = sum(g.monto_usd for g in gastos_fijos) if gastos_fijos else 0
    total_variables_usd = sum(g.monto_usd for g in gastos_variables) if gastos_variables else 0
    total_general_usd = total_fijos_usd + total_variables_usd

    return {
        "residente_id": residente["id"],
        "apartamento_id": residente["id_apartamento"],
        "resumen": {
            "total_gastos_fijos": len(gastos_fijos),
            "total_gastos_variables": len(gastos_variables),
            "total_fijos_usd": float(total_fijos_usd),
            "total_variables_usd": float(total_variables_usd),
            "total_general_usd": float(total_general_usd),
        },
        "ultima_actualizacion": date.today().isoformat(),
    }
