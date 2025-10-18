from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/reservas", tags=["Reservas"])


@router.post("/", response_model=schemas.ReservaOut)
def crear_reserva(reserva: schemas.ReservaCreate, db: Session = Depends(get_db)):
    return crud.crear_reserva(db, reserva)


@router.get("/", response_model=list[schemas.ReservaOut])
def listar_reservas(db: Session = Depends(get_db)):
    return crud.obtener_reservas(db)


@router.get("/{id_reserva}", response_model=schemas.ReservaOut)
def obtener_reserva(id_reserva: int, db: Session = Depends(get_db)):
    res = crud.obtener_reserva_por_id(db, id_reserva)
    if not res:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return res


@router.put("/{id_reserva}", response_model=schemas.ReservaOut)
def actualizar_reserva(
    id_reserva: int, datos: schemas.ReservaUpdate, db: Session = Depends(get_db)
):
    res = crud.actualizar_reserva(db, id_reserva, datos)
    if not res:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return res


@router.delete("/{id_reserva}")
def eliminar_reserva(id_reserva: int, db: Session = Depends(get_db)):
    eliminado = crud.eliminar_reserva(db, id_reserva)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return {"mensaje": "Reserva eliminada correctamente"}
