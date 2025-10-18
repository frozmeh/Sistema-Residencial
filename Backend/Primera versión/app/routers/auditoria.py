from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import SessionLocal

router = APIRouter(prefix="/auditoria", tags=["Auditoría"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.AuditoriaOut)
def registrar_accion(log: schemas.AuditoriaCreate, db: Session = Depends(get_db)):
    return crud.crear_log(db, log)

@router.get("/", response_model=list[schemas.AuditoriaOut])
def leer_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.obtener_logs(db, skip, limit)
