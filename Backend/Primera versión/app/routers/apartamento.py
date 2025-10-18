from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import SessionLocal

router = APIRouter(prefix="/apartamentos", tags=["Apartamentos"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.ApartamentoOut)
def crear(apto: schemas.ApartamentoCreate, db: Session = Depends(get_db)):
    return crud.crear_apartamento(db, apto)

@router.get("/", response_model=list[schemas.ApartamentoOut])
def leer_apartamentos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.obtener_apartamentos(db, skip=skip, limit=limit)

@router.get("/{id_apartamento}", response_model=schemas.ApartamentoOut)
def leer_apartamento(id_apartamento: int, db: Session = Depends(get_db)):
    db_apto = crud.obtener_apartamento(db, id_apartamento)
    if not db_apto:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
    return db_apto

@router.put("/{id_apartamento}", response_model=schemas.ApartamentoOut)
def actualizar(id_apartamento: int, apto: schemas.ApartamentoUpdate, db: Session = Depends(get_db)):
    db_apto = crud.actualizar_apartamento(db, id_apartamento, apto)
    if not db_apto:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
    return db_apto

@router.delete("/{id_apartamento}", response_model=schemas.ApartamentoOut)
def eliminar(id_apartamento: int, db: Session = Depends(get_db)):
    db_apto = crud.eliminar_apartamento(db, id_apartamento)
    if not db_apto:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
    return db_apto
