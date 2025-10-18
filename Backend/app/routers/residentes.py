from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db
from typing import Optional

router = APIRouter(prefix="/residentes", tags=["Residentes"])


# Crear un residente
@router.post("/", response_model=schemas.ResidenteOut)
def crear_residente(residente: schemas.ResidenteCreate, db: Session = Depends(get_db)):
    nuevo_residente = crud.crear_residente(db, residente)
    return nuevo_residente


# Obtener todos los residentes
@router.get("/", response_model=list[schemas.ResidenteOut])
def obtener_residentes(db: Session = Depends(get_db)):
    return crud.obtener_residentes(db)


# Obtener un residente por su ID
@router.get("/{id_residente}", response_model=schemas.ResidenteOut)
def obtener_residente(id_residente: int, db: Session = Depends(get_db)):
    residente = crud.obtener_residente_por_id(db, id_residente)
    if not residente:
        raise HTTPException(status_code=404, detail="Residente no encontrado")
    return residente


# Actualizar residente
@router.put("/{id_residente}", response_model=schemas.ResidenteOut)
def actualizar_residente(
    id_residente: int,
    datos_actualizados: schemas.ResidenteUpdate,
    db: Session = Depends(get_db),
):
    residente_actualizado = crud.actualizar_residente(
        db, id_residente, datos_actualizados
    )
    if not residente_actualizado:
        raise HTTPException(status_code=404, detail="Residente no encontrado")
    return residente_actualizado


# Eliminar residente
@router.delete("/{id_residente}")
def eliminar_residente(id_residente: int, db: Session = Depends(get_db)):
    eliminado = crud.eliminar_residente(db, id_residente)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Residente no encontrado")
    return {"mensaje": "Residente eliminado correctamente"}


# routers/residentes.py
@router.put("/{id_residente}/asignar_apartamento")
def asignar_apartamento(
    id_residente: int, id_apartamento: int, db: Session = Depends(get_db)
):
    resultado = crud.asignar_residente_a_apartamento(db, id_residente, id_apartamento)
    if resultado is None:
        raise HTTPException(
            status_code=404, detail="Residente o apartamento no encontrado"
        )
    elif resultado == "Apartamento ocupado":
        raise HTTPException(status_code=400, detail="Apartamento ya está ocupado")
    return {"mensaje": "Residente asignado correctamente", "residente": resultado}


@router.put("/{id_residente}/desasignar_apartamento")
def desasignar_residente(
    id_residente: int, inactivar: Optional[bool] = False, db: Session = Depends(get_db)
):
    resultado = crud.desasignar_residente(db, id_residente, inactivar)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Residente no encontrado")
    return {"mensaje": "Residente desasignado correctamente", "residente": resultado}
