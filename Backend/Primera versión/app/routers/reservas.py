from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import SessionLocal

router = APIRouter(prefix="/reservas", tags=["Reservas"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.ReservaOut)
def crear_reserva(reserva: schemas.ReservaCreate, db: Session = Depends(get_db)):
    return crud.crear_reserva(db, reserva)

@router.get("/", response_model=list[schemas.ReservaOut])
def leer_reservas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.obtener_reservas(db, skip=skip, limit=limit)
