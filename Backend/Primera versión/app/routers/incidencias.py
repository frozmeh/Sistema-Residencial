from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import SessionLocal
router = APIRouter(prefix="/incidencias", tags=["Incidencias"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.IncidenciaOut)
def crear_incidencia(incidencia: schemas.IncidenciaCreate, db: Session = Depends(get_db)):
    return crud.crear_incidencia(db, incidencia)

@router.get("/", response_model=list[schemas.IncidenciaOut])
def leer_incidencias(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.obtener_incidencias(db, skip=skip, limit=limit)
