from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/auditorias", tags=["Auditorias"])


@router.post("/", response_model=schemas.AuditoriaOut)
def crear_auditoria(audit: schemas.AuditoriaCreate, db: Session = Depends(get_db)):
    return crud.crear_auditoria(db, audit)


@router.get("/", response_model=list[schemas.AuditoriaOut])
def listar_auditorias(db: Session = Depends(get_db)):
    return crud.obtener_auditorias(db)
