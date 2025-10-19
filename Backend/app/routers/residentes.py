from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/residentes", tags=["Residentes"])


@router.post("/", response_model=schemas.ResidenteOut)
def crear_residente(residente: schemas.ResidenteCreate, db: Session = Depends(get_db)):
    nuevo_residente = crud.crear_residente(db, residente)
    return {"mensaje": "Residente creado correctamente", "residente": nuevo_residente}


# > Obtener todos los residentes <
@router.get("/", response_model=list[schemas.ResidenteOut])
def obtener_residentes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    residentes = crud.obtener_residentes(db)[skip : skip + limit]
    return residentes


# > Obtener un residente por su ID <
@router.get("/{id_residente}", response_model=schemas.ResidenteOut)
def obtener_residente(id_residente: int, db: Session = Depends(get_db)):
    residente = crud.obtener_residente_por_id(db, id_residente)
    return residente


@router.put("/{id_residente}", response_model=schemas.ResidenteOut)
def actualizar_residente(
    id_residente: int,
    datos_actualizados: schemas.ResidenteUpdate,
    db: Session = Depends(get_db),
):
    residente_actualizado = crud.actualizar_residente(db, id_residente, datos_actualizados)
    return {"mensaje": "Residente actualizado correctamente", "residente": residente_actualizado}


@router.delete("/{id_residente}")
def eliminar_residente(id_residente: int, db: Session = Depends(get_db)):
    eliminado = crud.eliminar_residente(db, id_residente)
    return {"mensaje": "Residente eliminado correctamente", "residente": eliminado}


# > Asignar apartamento a residente <
@router.put("/{id_residente}/asignar_apartamento")
def asignar_apartamento(id_residente: int, id_apartamento: int, db: Session = Depends(get_db)):
    resultado = crud.asignar_residente_a_apartamento(db, id_residente, id_apartamento)
    return {"mensaje": "Residente asignado correctamente", "residente": resultado, "apartamento": "Asignado"}


# > Desasignar apartamento de residente <
@router.put("/{id_residente}/desasignar_apartamento")
def desasignar_residente(
    id_residente: int,
    inactivar: bool = Query(False, description="Indica si se inactiva el residente"),
    db: Session = Depends(get_db),
):
    resultado = crud.desasignar_residente(db, id_residente, inactivar)
    return {
        "mensaje": f"Residente {'inactivado y ' if inactivar else ''}desasignado correctamente",
        "residente": resultado,
        "apartamento": "Liberado" if resultado.id_apartamento is None else "Asignado",
        "estado": resultado.estado,
    }


# > Activar residente <
@router.put("/{id_residente}/activar")
def activar_residente(id_residente: int, db: Session = Depends(get_db)):
    resultado = crud.activar_residente(db, id_residente)
    return {"mensaje": "Residente activado correctamente", "residente": resultado, "estado": resultado.estado}
