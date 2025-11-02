from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/auditorias", tags=["Auditorias"])


@router.post("/", response_model=schemas.AuditoriaOut)
def crear_auditoria(audit: schemas.AuditoriaCreate, db: Session = Depends(get_db)):
    try:
        return crud.crear_auditoria(db, audit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo crear la auditoría: {str(e)}")


@router.get("/", response_model=list[schemas.AuditoriaOut])
def listar_auditorias(db: Session = Depends(get_db)):
    return crud.obtener_auditorias(db)


@router.get("/{id_auditoria}", response_model=schemas.AuditoriaOut)
def obtener_auditoria(id_auditoria: int, db: Session = Depends(get_db)):
    a = crud.obtener_auditoria_por_id(db, id_auditoria)
    if not a:
        raise HTTPException(status_code=404, detail="Auditoría no encontrada")
    return a
