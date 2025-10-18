from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import SessionLocal

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.NotificacionOut)
def crear_notificacion(notificacion: schemas.NotificacionCreate, db: Session = Depends(get_db)):
    return crud.crear_notificacion(db, notificacion)

@router.get("/{id_usuario}", response_model=list[schemas.NotificacionOut])
def leer_notificaciones(id_usuario: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.obtener_notificaciones(db, id_usuario, skip, limit)

@router.put("/leer/{id_notificacion}", response_model=schemas.NotificacionOut)
def actualizar_leido(id_notificacion: int, db: Session = Depends(get_db)):
    return crud.marcar_como_leido(db, id_notificacion)
