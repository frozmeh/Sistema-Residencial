from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import SessionLocal

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

# Dependencia de sesión de DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Crear usuario
@router.post("/", response_model=schemas.UsuarioOut)
def crear(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    return crud.crear_usuario(db, usuario)

# Leer todos los usuarios
@router.get("/", response_model=list[schemas.UsuarioOut])
def leer_usuarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.obtener_usuarios(db, skip=skip, limit=limit)

# Leer usuario por id
@router.get("/{id_usuario}", response_model=schemas.UsuarioOut)
def leer_usuario(id_usuario: int, db: Session = Depends(get_db)):
    db_usuario = crud.obtener_usuario(db, id_usuario)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_usuario

# Actualizar usuario
@router.put("/{id_usuario}", response_model=schemas.UsuarioOut)
def actualizar(id_usuario: int, usuario: schemas.UsuarioUpdate, db: Session = Depends(get_db)):
    db_usuario = crud.actualizar_usuario(db, id_usuario, usuario)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_usuario

# Eliminar usuario
@router.delete("/{id_usuario}", response_model=schemas.UsuarioOut)
def eliminar(id_usuario: int, db: Session = Depends(get_db)):
    db_usuario = crud.eliminar_usuario(db, id_usuario)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_usuario
