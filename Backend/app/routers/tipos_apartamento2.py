from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/tipos-apartamento", tags=["Tipos de Apartamento"])


@router.get("/", response_model=list[schemas.TipoApartamentoOut])
def obtener_tipos_apartamentos(db: Session = Depends(get_db)):
    return crud.obtener_tipos_apartamentos(db)


@router.get("/{id_tipo}", response_model=schemas.TipoApartamentoOut)
def obtener_tipo_apartamento(id_tipo: int, db: Session = Depends(get_db)):
    return crud.obtener_tipo_apartamento_por_id(db, id_tipo)
