from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ... import models, schemas, crud
from ...database import get_db
from ...core.security import verificar_residente

router = APIRouter(prefix="/residente", tags=["Residente - Perfil y Gestión"])

# =======================================
# ---- Rutas disponibles al residente ----
# =======================================


@router.post("/", response_model=schemas.ResidenteOut)
def registrar_residente(
    residente: schemas.ResidenteCreate,
    db: Session = Depends(get_db),
    usuario=Depends(verificar_residente),
):
    return crud.crear_residente(db, residente, usuario.id)


@router.get("/me", response_model=schemas.ResidenteOut)
def obtener_mi_residente(usuario=Depends(verificar_residente), db: Session = Depends(get_db)):
    return crud.obtener_residente_asociado(db, usuario.id)


@router.put("/me", response_model=schemas.ResidenteOut)
def actualizar_mi_residente(
    datos_actualizados: schemas.ResidenteUpdateResidente,
    db: Session = Depends(get_db),
    usuario=Depends(verificar_residente),
):
    residente = crud.obtener_residente_asociado(db, usuario.id)
    return crud.actualizar_residente(db, residente.id, datos_actualizados)


@router.get("/buscar", response_model=list[schemas.ResidenteOut])
def buscar_residente(
    termino: str = Query(..., description="Nombre, cédula o correo"),
    db: Session = Depends(get_db),
    usuario=Depends(verificar_residente),
):
    return crud.buscar_residente(db, termino)


@router.get("/torre/{nombre_torre}", response_model=list[schemas.ResidenteOut])
def listar_residentes_por_torre(
    nombre_torre: str, db: Session = Depends(get_db), usuario=Depends(verificar_residente)
):
    return crud.obtener_residentes_por_torre(db, nombre_torre)


@router.get("/historial/apartamento/{id_apartamento}", response_model=list[schemas.ResidenteOut])
def historial_residentes_apartamento(
    id_apartamento: int, db: Session = Depends(get_db), usuario=Depends(verificar_residente)
):
    return crud.obtener_historial_residentes_por_apartamento(db, id_apartamento)
