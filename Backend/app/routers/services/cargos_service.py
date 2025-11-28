# routes/cargos.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ...database import get_db
from ...services.cargos_service import cargos_service
from ...schemas.financiero import CargoResponse

router = APIRouter(prefix="/cargos", tags=["cargos"])


@router.post(
    "/gastos/{gasto_id}/generar-cargos",
    status_code=status.HTTP_201_CREATED,
    summary="Generar cargos desde un gasto distribuido",
)
def generar_cargos_desde_gasto(gasto_id: int, db: Session = Depends(get_db)):
    """
    Genera cargos automáticamente para todas las distribuciones de un gasto

    **Flujo:**
    1. El gasto debe estar en estado 'Distribuido'
    2. Crea un cargo por cada distribución existente
    3. Los cargos tendrán fecha de vencimiento = fecha_gasto + 30 días
    """
    try:
        cargos_creados = cargos_service.generar_cargos_desde_gasto(db, gasto_id)

        return {
            "message": f"Se generaron {len(cargos_creados)} cargos exitosamente",
            "gasto_id": gasto_id,
            "cargos_generados": len(cargos_creados),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando cargos: {str(e)}")


@router.get(
    "/apartamentos/{apartamento_id}", response_model=List[CargoResponse], summary="Obtener cargos de un apartamento"
)
def obtener_cargos_apartamento(
    apartamento_id: int,
    incluir_pagados: bool = Query(False, description="Incluir cargos ya pagados"),
    db: Session = Depends(get_db),
):
    """
    Obtiene todos los cargos de un apartamento específico
    """
    try:
        cargos = cargos_service.obtener_cargos_por_apartamento(db, apartamento_id, incluir_pagados)
        return cargos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/apartamentos/{apartamento_id}/pendientes",
    response_model=List[CargoResponse],
    summary="Obtener cargos pendientes de un apartamento",
)
def obtener_cargos_pendientes(apartamento_id: int, db: Session = Depends(get_db)):
    """
    Obtiene solo los cargos pendientes/parciales/vencidos de un apartamento
    """
    try:
        cargos = cargos_service.obtener_cargos_pendientes(db, apartamento_id)
        return cargos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cargo_id}", response_model=CargoResponse, summary="Obtener un cargo específico")
def obtener_cargo(cargo_id: int, db: Session = Depends(get_db)):
    """
    Obtiene un cargo específico con todas sus relaciones
    """
    try:
        cargo = cargos_service.obtener_cargo_por_id(db, cargo_id)
        if not cargo:
            raise HTTPException(status_code=404, detail="Cargo no encontrado")
        return cargo
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vencidos/todos", response_model=List[CargoResponse], summary="Obtener todos los cargos vencidos")
def obtener_cargos_vencidos(db: Session = Depends(get_db)):
    """
    Obtiene todos los cargos con estado 'Vencido'
    Útil para seguimiento de morosos
    """
    try:
        cargos = cargos_service.obtener_cargos_vencidos(db)
        return cargos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/apartamentos/{apartamento_id}/resumen", summary="Resumen de deudas de un apartamento")
def obtener_resumen_deudas(apartamento_id: int, db: Session = Depends(get_db)):
    """
    Obtiene un resumen de todas las deudas pendientes de un apartamento
    """
    try:
        resumen = cargos_service.calcular_total_pendiente_apartamento(db, apartamento_id)
        return resumen
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verificar-vencimientos", summary="Ejecutar verificación automática de vencimientos")
def ejecutar_verificacion_vencimientos(db: Session = Depends(get_db)):
    """
    Endpoint manual para ejecutar la verificación de vencimientos
    (Normalmente esto correría automáticamente cada día)
    """
    try:
        cargos_actualizados = cargos_service.verificar_vencimientos_automatico(db)
        return {"message": f"Verificación completada", "cargos_actualizados": cargos_actualizados}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
