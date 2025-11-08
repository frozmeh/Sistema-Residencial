from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from ... import schemas, crud
from ...database import get_db
from ...core.security import verificar_admin

router = APIRouter(prefix="/admin/residentes", tags=["Admin - Residentes"])

# ==========================
# ---- Rutas para Admin ----
# ==========================


@router.get("/", response_model=list[schemas.ResidenteOut])
def listar_residentes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    return crud.obtener_residentes(db)[skip : skip + limit]


@router.get("/pendientes")
def listar_pendientes(
    torre: str | None = None, piso: int | None = None, db: Session = Depends(get_db), admin=Depends(verificar_admin)
):
    return crud.obtener_residentes_no_validados(db, torre, piso)


@router.put("/aprobar/{id_residente}")
def aprobar_residente(id_residente: int, db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    return crud.aprobar_residente(db, id_residente)


@router.put("/rechazar/{id_residente}")
def rechazar_residente(
    id_residente: int,
    motivo: str = "Registro rechazado por el administrador.",
    db: Session = Depends(get_db),
    admin=Depends(verificar_admin),
):
    return crud.rechazar_residente(db, id_residente, motivo)


@router.put("/{id_residente}/asignar_apartamento")
def asignar_apartamento(
    id_residente: int, id_apartamento: int, db: Session = Depends(get_db), admin=Depends(verificar_admin)
):
    return crud.asignar_residente_a_apartamento(db, id_residente, id_apartamento)


@router.put("/{id_residente}/desasignar_apartamento")
def desasignar_residente(
    id_residente: int, inactivar: bool = Query(False), db: Session = Depends(get_db), admin=Depends(verificar_admin)
):
    return crud.desasignar_residente(db, id_residente, inactivar)


@router.put("/{id_residente}/activar")
def activar_residente(id_residente: int, db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    return crud.activar_residente(db, id_residente)


@router.delete("/{id_residente}")
def eliminar_residente(id_residente: int, db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    return crud.eliminar_residente(db, id_residente)


@router.get("/contar/")
def contar_residentes(solo_activos: bool = True, db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    cantidad = crud.contar_residentes(db, solo_activos)
    return {"total_residentes": cantidad, "solo_activos": solo_activos}
