from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from ... import schemas, crud
from ...database import get_db
from ...core.security import verificar_residente

router = APIRouter(prefix="/pagos", tags=["Pagos"])


# ==========================
# 🔹 SECCIÓN RESIDENTE
# ==========================


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


@router.get("/mis-resumen")
def resumen_pagos_residente(
    residente: dict = Depends(verificar_residente),
    db: Session = Depends(get_db),
):
    pagos = crud.filtrar_pagos(db, id_residente=residente["id"])
    total_pagado = sum([float(p.monto) for p in pagos])
    pendientes = sum(1 for p in pagos if p.estado == "Pendiente")
    validados = sum(1 for p in pagos if p.estado == "Validado")
    rechazados = sum(1 for p in pagos if p.estado == "Rechazado")
    return {
        "total_pagado": total_pagado,
        "cantidad_total": len(pagos),
        "pendientes": pendientes,
        "validados": validados,
        "rechazados": rechazados,
    }


@router.delete("/{id_pago}")
def eliminar_pago_residente(
    id_pago: int,
    residente: dict = Depends(verificar_residente),
    db: Session = Depends(get_db),
):
    pago = crud.obtener_pago_por_id(db, id_pago)
    if pago.id_residente != residente["id"]:
        raise HTTPException(status_code=403, detail="No puedes eliminar pagos de otros residentes")
    if pago.estado != "Pendiente":
        raise HTTPException(status_code=400, detail="Solo se pueden eliminar pagos pendientes")
    db.delete(pago)
    db.commit()
    return {"detalle": f"Pago con id {id_pago} eliminado correctamente"}
