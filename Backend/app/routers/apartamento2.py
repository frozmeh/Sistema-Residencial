from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/apartamentos", tags=["Apartamentos"])


@router.get("/", response_model=list[schemas.ApartamentoOut])
def obtener_apartamentos(db: Session = Depends(get_db)):
    return crud.obtener_apartamentos(db)


@router.get("/{id_apartamento}", response_model=schemas.ApartamentoOut)
def obtener_apartamento(id_apartamento: int, db: Session = Depends(get_db)):
    return crud.obtener_apartamento_por_id(db, id_apartamento)


@router.put("/{id_apartamento}", response_model=schemas.ApartamentoOut)
def actualizar_apartamento(id_apartamento: int, datos: schemas.ApartamentoUpdate, db: Session = Depends(get_db)):
    return crud.actualizar_apartamento(db, id_apartamento, datos)
