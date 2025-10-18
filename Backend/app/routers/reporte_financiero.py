from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/reportes", tags=["Reportes Financieros"])


@router.post("/", response_model=schemas.ReporteFinancieroOut)
def crear_reporte(
    reporte: schemas.ReporteFinancieroCreate, db: Session = Depends(get_db)
):
    return crud.crear_reporte(db, reporte)


@router.get("/", response_model=list[schemas.ReporteFinancieroOut])
def listar_reportes(db: Session = Depends(get_db)):
    return crud.obtener_reportes(db)


@router.get("/{id_reporte}", response_model=schemas.ReporteFinancieroOut)
def obtener_reporte(id_reporte: int, db: Session = Depends(get_db)):
    r = crud.obtener_reporte_por_id(db, id_reporte)
    if not r:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return r


@router.put("/{id_reporte}", response_model=schemas.ReporteFinancieroOut)
def actualizar_reporte(
    id_reporte: int,
    datos: schemas.ReporteFinancieroUpdate,
    db: Session = Depends(get_db),
):
    r = crud.actualizar_reporte(db, id_reporte, datos)
    if not r:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return r


@router.delete("/{id_reporte}")
def eliminar_reporte(id_reporte: int, db: Session = Depends(get_db)):
    eliminado = crud.eliminar_reporte(db, id_reporte)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return {"mensaje": "Reporte eliminado correctamente"}
