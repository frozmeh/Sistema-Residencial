from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/incidencias", tags=["Incidencias"])


@router.post("/", response_model=schemas.IncidenciaOut)
def crear_incidencia(
    incidencia: schemas.IncidenciaCreate, db: Session = Depends(get_db)
):
    return crud.crear_incidencia(db, incidencia)


@router.get("/", response_model=list[schemas.IncidenciaOut])
def listar_incidencias(db: Session = Depends(get_db)):
    return crud.obtener_incidencias(db)


@router.get("/{id_incidencia}", response_model=schemas.IncidenciaOut)
def obtener_incidencia(id_incidencia: int, db: Session = Depends(get_db)):
    inc = crud.obtener_incidencia_por_id(db, id_incidencia)
    if not inc:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    return inc


@router.put("/{id_incidencia}", response_model=schemas.IncidenciaOut)
def actualizar_incidencia(
    id_incidencia: int, datos: schemas.IncidenciaUpdate, db: Session = Depends(get_db)
):
    inc = crud.actualizar_incidencia(db, id_incidencia, datos)
    if not inc:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    return inc


@router.delete("/{id_incidencia}")
def eliminar_incidencia(id_incidencia: int, db: Session = Depends(get_db)):
    eliminado = crud.eliminar_incidencia(db, id_incidencia)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    return {"mensaje": "Incidencia eliminada correctamente"}
