from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import date
from sqlalchemy.orm import Session
from typing import List, Optional

from ... import schemas, crud, models
from ...database import get_db
from ...core.security import verificar_residente

router = APIRouter(prefix="/residente/gastos", tags=["Residente - Gastos"])

# =======================
# ---- GASTOS FIJOS ----
# =======================


@router.get(
    "/fijos",
    response_model=List[schemas.GastoFijoOut],
    summary="Mis gastos fijos",
    description="Obtiene los gastos fijos asociados a mi apartamento con tasas actualizadas.",
)
def listar_gastos_fijos_residente(
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicial para filtrar"),
    fecha_fin: Optional[date] = Query(None, description="Fecha final para filtrar"),
    actualizar_tasa: bool = Query(True, description="Actualizar montos con tasa BCV actual"),
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
        actualizar_tasa=actualizar_tasa,
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
    description="Obtiene los gastos variables asociados a mi apartamento con tasas actualizadas.",
)
def listar_gastos_variables_residente(
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicial para filtrar"),
    fecha_fin: Optional[date] = Query(None, description="Fecha final para filtrar"),
    actualizar_tasa: bool = Query(True, description="Actualizar montos con tasa BCV actual"),
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
        actualizar_tasa=actualizar_tasa,
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


# ==========================
# ---- RESUMEN Y ESTADÍSTICAS ----
# ==========================


@router.get(
    "/resumen",
    summary="Resumen de mis gastos",
    description="Obtiene un resumen completo de todos los gastos del residente con saldos actualizados.",
)
def resumen_gastos_residente(
    actualizar_tasa: bool = Query(True, description="Actualizar montos con tasa BCV actual"),
    residente: dict = Depends(verificar_residente),
    db: Session = Depends(get_db),
):
    """Resumen completo de gastos para el residente con seguimiento de saldos"""
    if not residente.get("id_apartamento"):
        raise HTTPException(status_code=400, detail="No tienes un apartamento asignado")

    # Obtener gastos fijos
    gastos_fijos = crud.obtener_gastos_fijos(
        db, id_apartamento=residente["id_apartamento"], actualizar_tasa=actualizar_tasa
    )

    # Obtener gastos variables
    gastos_variables = crud.obtener_gastos_variables(
        db, id_apartamento=residente["id_apartamento"], id_residente=residente["id"], actualizar_tasa=actualizar_tasa
    )

    # Calcular totales y saldos
    total_fijos_usd = sum(g.monto_usd for g in gastos_fijos) if gastos_fijos else 0
    total_variables_usd = sum(g.monto_usd for g in gastos_variables) if gastos_variables else 0
    total_general_usd = total_fijos_usd + total_variables_usd

    saldo_fijos = sum(g.saldo_pendiente for g in gastos_fijos) if gastos_fijos else 0
    saldo_variables = sum(g.saldo_pendiente for g in gastos_variables) if gastos_variables else 0
    saldo_total = saldo_fijos + saldo_variables

    total_pagado = total_general_usd - saldo_total

    return {
        "residente_id": residente["id"],
        "apartamento_id": residente["id_apartamento"],
        "resumen": {
            "total_gastos_fijos": len(gastos_fijos),
            "total_gastos_variables": len(gastos_variables),
            "total_gastos_general": len(gastos_fijos) + len(gastos_variables),
            "total_fijos_usd": float(total_fijos_usd),
            "total_variables_usd": float(total_variables_usd),
            "total_general_usd": float(total_general_usd),
            "total_pagado_usd": float(total_pagado),
            "saldo_pendiente_fijos": float(saldo_fijos),
            "saldo_pendiente_variables": float(saldo_variables),
            "saldo_pendiente_total": float(saldo_total),
            "porcentaje_pagado": (total_pagado / total_general_usd * 100) if total_general_usd > 0 else 0,
        },
        "detalle_gastos_fijos": [
            {
                "id": g.id,
                "tipo_gasto": g.tipo_gasto,
                "descripcion": g.descripcion,
                "monto_total": float(g.monto_usd),
                "monto_pagado": float(g.monto_pagado),
                "saldo_pendiente": float(g.saldo_pendiente),
                "fecha_creacion": g.fecha_creacion,
                "completado": g.saldo_pendiente <= 0,
            }
            for g in gastos_fijos
        ],
        "detalle_gastos_variables": [
            {
                "id": g.id,
                "tipo_gasto": g.tipo_gasto,
                "descripcion": g.descripcion,
                "monto_total": float(g.monto_usd),
                "monto_pagado": float(g.monto_pagado),
                "saldo_pendiente": float(g.saldo_pendiente),
                "fecha_creacion": g.fecha_creacion,
                "completado": g.saldo_pendiente <= 0,
            }
            for g in gastos_variables
        ],
        "ultima_actualizacion": date.today().isoformat(),
    }


@router.get(
    "/saldos-pendientes",
    summary="Saldos pendientes",
    description="Obtiene solo los gastos con saldos pendientes de pago.",
)
def saldos_pendientes_residente(residente: dict = Depends(verificar_residente), db: Session = Depends(get_db)):
    """Obtiene los gastos que aún tienen saldo pendiente de pago"""
    if not residente.get("id_apartamento"):
        raise HTTPException(status_code=400, detail="No tienes un apartamento asignado")

    # Obtener gastos fijos con saldo pendiente
    gastos_fijos = crud.obtener_gastos_fijos(db, id_apartamento=residente["id_apartamento"], actualizar_tasa=False)
    gastos_fijos_pendientes = [g for g in gastos_fijos if g.saldo_pendiente > 0]

    # Obtener gastos variables con saldo pendiente
    gastos_variables = crud.obtener_gastos_variables(
        db, id_apartamento=residente["id_apartamento"], id_residente=residente["id"], actualizar_tasa=False
    )
    gastos_variables_pendientes = [g for g in gastos_variables if g.saldo_pendiente > 0]

    return {
        "gastos_fijos_pendientes": [
            {
                "id": g.id,
                "tipo_gasto": g.tipo_gasto,
                "descripcion": g.descripcion,
                "monto_total": float(g.monto_usd),
                "saldo_pendiente": float(g.saldo_pendiente),
                "fecha_creacion": g.fecha_creacion,
            }
            for g in gastos_fijos_pendientes
        ],
        "gastos_variables_pendientes": [
            {
                "id": g.id,
                "tipo_gasto": g.tipo_gasto,
                "descripcion": g.descripcion,
                "monto_total": float(g.monto_usd),
                "saldo_pendiente": float(g.saldo_pendiente),
                "fecha_creacion": g.fecha_creacion,
            }
            for g in gastos_variables_pendientes
        ],
        "total_pendiente": sum(g.saldo_pendiente for g in gastos_fijos_pendientes + gastos_variables_pendientes),
        "cantidad_pendientes": len(gastos_fijos_pendientes) + len(gastos_variables_pendientes),
    }
