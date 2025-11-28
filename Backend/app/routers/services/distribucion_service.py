from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import List
from ...database import get_db
from ...services.distribucion_service import distribucion_service
from ...services.tasa_cambio_service import tasa_cambio_service
from ...models.financiero import Gasto

router = APIRouter(prefix="/distribucion", tags=["Distribución"])

# 📋 SCHEMAS PARA LAS PETICIONES
from pydantic import BaseModel


class DistribucionPreviewRequest(BaseModel):
    monto_total_usd: Decimal
    apartamentos_ids: List[int]
    forzar_equitativa: bool = False


class DistribucionCreateRequest(BaseModel):
    id_gasto: int
    apartamentos_ids: List[int]
    forzar_equitativa: bool = False


# 🧮 ENDPOINTS DE PRUEBA
@router.post("/preview")
def calcular_distribucion_preview(request: DistribucionPreviewRequest, db: Session = Depends(get_db)):
    """
    🔍 PREVIEW de distribución SIN guardar
    Perfecto para probar la lógica
    """
    try:
        resultado = distribucion_service.calcular_distribucion_preview(
            db=db,
            monto_total_usd=request.monto_total_usd,
            apartamentos_ids=request.apartamentos_ids,
            forzar_equitativa=request.forzar_equitativa,
        )
        return {"success": True, "data": resultado, "message": "Preview de distribución calculado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/calcular")
def calcular_distribucion_real(request: DistribucionCreateRequest, db: Session = Depends(get_db)):
    """
    🎯 Distribución REAL (crea registros en DB)
    """
    try:
        # Obtener el gasto de la base de datos
        gasto = db.query(Gasto).filter(Gasto.id == request.id_gasto).first()
        if not gasto:
            raise HTTPException(status_code=404, detail="Gasto no encontrado")

        # Calcular distribución
        distribuciones = distribucion_service.calcular_distribucion_gasto(
            db=db, gasto=gasto, apartamentos_ids=request.apartamentos_ids, forzar_equitativa=request.forzar_equitativa
        )

        # Guardar en base de datos
        distribuciones_guardadas = distribucion_service.guardar_distribuciones(db=db, distribuciones=distribuciones)

        return {
            "success": True,
            "data": {
                "total_distribuciones": len(distribuciones_guardadas),
                "distribuciones": [
                    {
                        "id": dist.id,
                        "id_apartamento": dist.id_apartamento,
                        "monto_usd": float(dist.monto_asignado_usd),
                        "monto_ves": float(dist.monto_asignado_ves),
                        "porcentaje": float(dist.porcentaje_aplicado),
                    }
                    for dist in distribuciones_guardadas
                ],
            },
            "message": "Distribución creada y guardada exitosamente",
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/porcentaje/{tipo_apartamento_id}")
def obtener_porcentaje_aporte(tipo_apartamento_id: int, db: Session = Depends(get_db)):
    """
    📊 Obtener porcentaje de aporte de un tipo de apartamento
    """
    try:
        porcentaje = distribucion_service.obtener_porcentaje_aporte(db=db, tipo_apartamento_id=tipo_apartamento_id)
        return {
            "success": True,
            "data": {"tipo_apartamento_id": tipo_apartamento_id, "porcentaje_aporte": float(porcentaje)},
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/test")
def test_distribucion_service(db: Session = Depends(get_db)):
    """
    🧪 ENDPOINT DE PRUEBA RÁPIDA
    """
    try:
        # Datos de prueba
        test_data = {
            "monto_total_usd": Decimal("1000.00"),
            "apartamentos_ids": [1, 2, 3],  # IDs que existan en tu DB
            "tasa_cambio": tasa_cambio_service.obtener_tasa_cambio_actual(db),
            "forzar_equitativa": False,
        }

        resultado = distribucion_service.calcular_distribucion_preview(db=db, **test_data)

        return {
            "success": True,
            "test_data": test_data,
            "resultado": resultado,
            "message": "✅ DistribucionService funcionando correctamente",
        }

    except Exception as e:
        return {"success": False, "error": str(e), "message": "❌ Error en DistribucionService"}
