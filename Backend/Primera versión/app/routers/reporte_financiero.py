from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import SessionLocal

router = APIRouter(prefix="/reportes", tags=["Reportes"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.ReporteFinancieroOut)
def crear_reporte(reporte: schemas.ReporteFinancieroCreate, db: Session = Depends(get_db)):
    return crud.crear_reporte(db, reporte)

@router.get("/", response_model=list[schemas.ReporteFinancieroOut])
def leer_reportes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.obtener_reportes(db, skip=skip, limit=limit)

@router.get("/{id_reporte}", response_model=schemas.ReporteFinancieroOut)
def leer_reporte(id_reporte: int, db: Session = Depends(get_db)):
    db_reporte = crud.obtener_reporte(db, id_reporte)
    if not db_reporte:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return db_reporte

@router.delete("/{id_reporte}", response_model=schemas.ReporteFinancieroOut)
def eliminar(id_reporte: int, db: Session = Depends(get_db)):
    db_reporte = crud.eliminar_reporte(db, id_reporte)
    if not db_reporte:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return db_reporte

from fastapi import Query

@router.post("/generar/", response_model=schemas.ReporteFinancieroOut)
def generar_reporte(mes: int = Query(..., ge=1, le=12),
                    año: int = Query(..., ge=2000),
                    usuario: str = Query(...),
                    db: Session = Depends(get_db)):
    return crud.generar_reporte_mensual(db, mes, año, usuario)
