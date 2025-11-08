from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ... import schemas, crud
from ...database import get_db
from ...core.security import verificar_residente

router = APIRouter(prefix="/pagos", tags=["Pagos"])


# ============================
# 🔹 SECCIÓN RESIDENTE
# ============================


@router.post("/", response_model=schemas.PagoOut)
def crear_pago_residente(
    pago: schemas.PagoCreate,
    residente: dict = Depends(verificar_residente),
    db: Session = Depends(get_db),
):
    pago.id_residente = residente["id"]
    return crud.crear_pago(db, pago)


@router.get("/mis-pagos", response_model=List[schemas.PagoOut])
def listar_pagos_residente(
    residente: dict = Depends(verificar_residente),
    db: Session = Depends(get_db),
):
    pagos = crud.filtrar_pagos(db, id_residente=residente["id"])
    if not pagos:
        raise HTTPException(status_code=404, detail="No se encontraron pagos asociados a tu cuenta.")
    return pagos
