from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


@router.post("/", response_model=schemas.NotificacionOut)
def crear_notificacion(noti: schemas.NotificacionCreate, db: Session = Depends(get_db)):
    return crud.crear_notificacion(db, noti)


@router.get("/", response_model=list[schemas.NotificacionOut])
def listar_notificaciones(db: Session = Depends(get_db)):
    return crud.obtener_notificaciones(db)


@router.get("/{id_notificacion}", response_model=schemas.NotificacionOut)
def obtener_notificacion(id_notificacion: int, db: Session = Depends(get_db)):
    n = crud.obtener_notificacion_por_id(db, id_notificacion)
    if not n:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return n


@router.put("/{id_notificacion}", response_model=schemas.NotificacionOut)
def actualizar_notificacion(
    id_notificacion: int,
    datos: schemas.NotificacionUpdate,
    db: Session = Depends(get_db),
):
    n = crud.actualizar_notificacion(db, id_notificacion, datos)
    if not n:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return n
