from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ... import schemas, crud
from ...database import get_db
from ...core.security import verificar_residente
from ...utils.tasa_bcv import obtener_tasa_bcv  # nueva función que consulta el BCV

router = APIRouter(prefix="/gastos", tags=["Gastos"])


# =======================
# ---- GASTOS FIJOS ----
# =======================


@router.get("/fijos", response_model=List[schemas.GastoFijoOut])
def listar_gastos_fijos_residente(residente: dict = Depends(verificar_residente), db: Session = Depends(get_db)):
    gastos = crud.obtener_gastos_fijos(db, id_apartamento=residente["id_apartamento"])
    if not gastos:
        raise HTTPException(status_code=404, detail="No se encontraron gastos fijos asociados a tu apartamento.")

    # Obtener tasa BCV actual
    tasa_bcv = obtener_tasa_bcv()

    # Actualizar montos con la tasa actual antes de devolverlos
    for g in gastos:
        g.tasa_cambio = tasa_bcv
        g.monto_bs = g.monto_usd * tasa_bcv

    return gastos


# ==========================
# ---- GASTOS VARIABLES ----
# ==========================


@router.get("/variables", response_model=List[schemas.GastoVariableOut])
def listar_gastos_variables_residente(residente: dict = Depends(verificar_residente), db: Session = Depends(get_db)):
    gastos = crud.obtener_gastos_variables(
        db, id_apartamento=residente["id_apartamento"], id_residente=residente["id"]
    )
    if not gastos:
        raise HTTPException(status_code=404, detail="No se encontraron gastos variables asociados a tu cuenta.")

    # Obtener tasa BCV actual
    tasa_bcv = obtener_tasa_bcv()

    # Actualizar montos con la tasa actual antes de devolverlos
    for g in gastos:
        g.tasa_cambio = tasa_bcv
        g.monto_bs = g.monto_usd * tasa_bcv

    return gastos
