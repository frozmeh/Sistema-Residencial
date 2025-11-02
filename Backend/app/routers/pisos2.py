from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/torres/{id_torre}/pisos", tags=["Pisos"])


# ---- GET /pisos ----
@router.get("/", response_model=list[schemas.PisoOut])
def obtener_pisos(id_torre: int, db: Session = Depends(get_db)):
    """
    Devuelve todos los pisos de una torre específica
    """
    return crud.obtener_pisos_por_torre(db, id_torre)


# ---- GET /pisos/{id_piso} ----
@router.get("/{id_piso}", response_model=schemas.PisoOut)
def obtener_piso(id_torre: int, id_piso: int, db: Session = Depends(get_db)):
    """
    Devuelve un piso específico dentro de una torre
    """
    return crud.obtener_piso_por_id_torre(db, id_torre, id_piso)
