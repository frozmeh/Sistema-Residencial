from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("/", response_model=list[schemas.RolOut])
def listar_roles(db: Session = Depends(get_db)):
    return crud.obtener_roles(db)


@router.post("/", response_model=schemas.RolOut)
def crear_nuevo_rol(rol: schemas.RolCreate, db: Session = Depends(get_db)):
    return crud.crear_rol(db, rol)
