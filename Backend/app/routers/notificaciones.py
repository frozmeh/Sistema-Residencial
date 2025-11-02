from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


# Crear notificación
@router.post("/", response_model=schemas.NotificacionOut)
def crear_notificacion(noti: schemas.NotificacionCreate, db: Session = Depends(get_db)):
    return crud.crear_notificacion(db, noti)


# Listar notificaciones con filtros opcionales
@router.get("/", response_model=list[schemas.NotificacionOut])
def listar_notificaciones(
    id_usuario: int | None = Query(None, description="Filtrar por ID de usuario"),
    tipo: str | None = Query(None, description="Filtrar por tipo de notificación"),
    leido: bool | None = Query(None, description="Filtrar por estado de lectura"),
    db: Session = Depends(get_db),
):
    return crud.obtener_notificaciones(db, id_usuario=id_usuario, tipo=tipo, leido=leido)


# Obtener notificación por ID
@router.get("/{id_notificacion}", response_model=schemas.NotificacionOut)
def obtener_notificacion(id_notificacion: int, db: Session = Depends(get_db)):
    n = crud.obtener_notificacion_por_id(db, id_notificacion)
    if not n:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return n


# Actualizar notificación
@router.put("/{id_notificacion}", response_model=schemas.NotificacionOut)
def actualizar_notificacion(id_notificacion: int, datos: schemas.NotificacionUpdate, db: Session = Depends(get_db)):
    return crud.actualizar_notificacion(db, id_notificacion, datos)


# Eliminar notificación
@router.delete("/{id_notificacion}")
def eliminar_notificacion(id_notificacion: int, db: Session = Depends(get_db)):
    return crud.eliminar_notificacion(db, id_notificacion)
