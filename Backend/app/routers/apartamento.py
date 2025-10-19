from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/apartamentos", tags=["Apartamentos"])


@router.post("/", response_model=schemas.ApartamentoOut)
def crear_apartamento(apt: schemas.ApartamentoCreate, db: Session = Depends(get_db)):
    return crud.crear_apartamento(db, apt)


@router.get("/", response_model=list[schemas.ApartamentoOut])
def obtener_apartamentos(db: Session = Depends(get_db)):
    return crud.obtener_apartamentos(db)


@router.get("/{id_apartamento}", response_model=schemas.ApartamentoOut)
def obtener_apartamento(id_apartamento: int, db: Session = Depends(get_db)):
    apt = crud.obtener_apartamento_por_id(db, id_apartamento)
    if not apt:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
    return apt


@router.put("/{id_apartamento}", response_model=schemas.ApartamentoOut)
def actualizar_apartamento(id_apartamento: int, datos: schemas.ApartamentoUpdate, db: Session = Depends(get_db)):
    apt_actualizado = crud.actualizar_apartamento(db, id_apartamento, datos)
    if not apt_actualizado:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
    return apt_actualizado


@router.delete("/{id_apartamento}")
def eliminar_apartamento(id_apartamento: int, db: Session = Depends(get_db)):
    eliminado = crud.eliminar_apartamento(db, id_apartamento)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
    return {"mensaje": "Apartamento eliminado correctamente"}
