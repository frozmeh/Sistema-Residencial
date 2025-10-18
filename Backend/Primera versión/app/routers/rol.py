from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import SessionLocal

router = APIRouter(prefix="/roles", tags=["Roles"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoints CRUD
@router.post("/", response_model=schemas.RolOut)
def crear(rol: schemas.RolCreate, db: Session = Depends(get_db)):
    return crud.crear_rol(db, rol)

@router.get("/", response_model=list[schemas.RolOut])
def leer_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.obtener_roles(db, skip=skip, limit=limit)

@router.get("/{id_rol}", response_model=schemas.RolOut)
def leer_rol(id_rol: int, db: Session = Depends(get_db)):
    db_rol = crud.obtener_rol(db, id_rol)
    if not db_rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return db_rol

@router.put("/{id_rol}", response_model=schemas.RolOut)
def actualizar(id_rol: int, rol: schemas.RolUpdate, db: Session = Depends(get_db)):
    db_rol = crud.actualizar_rol(db, id_rol, rol)
    if not db_rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return db_rol

@router.delete("/{id_rol}", response_model=schemas.RolOut)
def eliminar(id_rol: int, db: Session = Depends(get_db)):
    db_rol = crud.eliminar_rol(db, id_rol)
    if not db_rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return db_rol
