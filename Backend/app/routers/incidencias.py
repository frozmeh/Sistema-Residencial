from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/incidencias", tags=["Incidencias"])


# =====================
# ---- Incidencias ----
# =====================


@router.post(
    "/",
    response_model=schemas.IncidenciaOut,
    summary="Crear una nueva incidencia",
    description="Permite a un residente crear una incidencia de tipo Mantenimiento, Queja o Sugerencia.",
)
def crear_incidencia(
    incidencia: schemas.IncidenciaCreate,
    db: Session = Depends(get_db),
):
    return crud.crear_incidencia(db, incidencia)


def listar_incidencias(
    estado: Optional[str] = Query(None, description="Filtrar por estado (Abierta, En progreso, Cerrada)"),
    prioridad: Optional[str] = Query(None, description="Filtrar por prioridad (Alta, Media, Baja)"),
    fecha_inicio: Optional[date] = Query(None, description="Filtrar incidencias desde esta fecha"),
    fecha_fin: Optional[date] = Query(None, description="Filtrar incidencias hasta esta fecha"),
    db: Session = Depends(get_db),
):
    return crud.obtener_incidencias(db, estado, prioridad, fecha_inicio, fecha_fin)


@router.get(
    "/{id_incidencia}",
    response_model=schemas.IncidenciaOut,
    summary="Obtener una incidencia por ID",
)
def obtener_incidencia(id_incidencia: int, db: Session = Depends(get_db)):
    return crud.obtener_incidencia_por_id(db, id_incidencia)


@router.put(
    "/{id_incidencia}",
    response_model=schemas.IncidenciaOut,
    summary="Actualizar una incidencia existente",
    description="Permite modificar el estado, descripción o prioridad de una incidencia.",
)
@router.put(
    "/{id_incidencia}",
    response_model=schemas.IncidenciaOut,
    summary="Actualizar una incidencia existente",
    description="Permite modificar el estado, descripción o prioridad de una incidencia.",
)
def actualizar_incidencia(
    id_incidencia: int,
    datos: schemas.IncidenciaUpdate,
    db: Session = Depends(get_db),
):
    return crud.actualizar_incidencia(db, id_incidencia, datos)


@router.delete(
    "/{id_incidencia}",
    summary="Eliminar una incidencia por ID",
    description="Elimina una incidencia solo si está en estado 'Cerrada'.",
)
def eliminar_incidencia(id_incidencia: int, db: Session = Depends(get_db)):
    crud.eliminar_incidencia(db, id_incidencia)
    return {"mensaje": "Incidencia eliminada correctamente"}
