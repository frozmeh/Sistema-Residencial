from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import SessionLocal

router = APIRouter(prefix="/residentes", tags=["Residentes"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoints CRUD
@router.post("/", response_model=schemas.ResidenteOut)
def crear(residente: schemas.ResidenteCreate, db: Session = Depends(get_db)):
    return crud.crear_residente(db, residente)

@router.get("/", response_model=list[schemas.ResidenteOut])
def leer_residentes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.obtener_residentes(db, skip=skip, limit=limit)

@router.get("/{id_residente}", response_model=schemas.ResidenteOut)
def leer_residente(id_residente: int, db: Session = Depends(get_db)):
    db_residente = crud.obtener_residente(db, id_residente)
    if not db_residente:
        raise HTTPException(status_code=404, detail="Residente no encontrado")
    return db_residente

@router.put("/{id_residente}", response_model=schemas.ResidenteOut)
def actualizar(id_residente: int, residente: schemas.ResidenteUpdate, db: Session = Depends(get_db)):
    db_residente = crud.actualizar_residente(db, id_residente, residente)
    if not db_residente:
        raise HTTPException(status_code=404, detail="Residente no encontrado")
    return db_residente

@router.delete("/{id_residente}", response_model=schemas.ResidenteOut)
def eliminar(id_residente: int, db: Session = Depends(get_db)):
    db_residente = crud.eliminar_residente(db, id_residente)
    if not db_residente:
        raise HTTPException(status_code=404, detail="Residente no encontrado")
    return db_residente
