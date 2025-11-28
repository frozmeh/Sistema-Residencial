from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..services import DeudasService, TasaCambioService
from datetime import date
from decimal import Decimal
from typing import Optional


router = APIRouter(prefix="/financiero", tags=["Financieros"])
tasa_cambio_service = TasaCambioService()
deudas_service = DeudasService()


@router.get("/deudas/mensual/{apartamento_id}")
def obtener_deuda_mensual(apartamento_id: int, periodo: str, db: Session = Depends(get_db)):
    return deudas_service.obtener_deuda_mensual(db, apartamento_id, periodo)


@router.get("/deudas/historial/{apartamento_id}")
def obtener_historial_deudas(apartamento_id: int, db: Session = Depends(get_db)):
    return deudas_service.obtener_historial_12_meses(db, apartamento_id)


@router.get("/deudas/total/{apartamento_id}")
def obtener_deuda_total(apartamento_id: int, db: Session = Depends(get_db)):
    return deudas_service.obtener_deuda_total(db, apartamento_id)


@router.get("/tasas/actual")
def get_tasa_actual(db: Session = Depends(get_db)):
    return tasa_cambio_service.obtener_tasa_actual(db)


@router.post("/tasas/convertir")
def convertir_monto(
    monto_usd: Optional[Decimal] = None,
    monto_ves: Optional[Decimal] = None,
    db: Session = Depends(get_db),
):
    return tasa_cambio_service.convertir_monto(db, monto_usd, monto_ves)
