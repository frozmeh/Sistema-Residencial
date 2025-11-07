from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import crud, schemas
from ..database import get_db
from ..models import Usuario  # Ajusta el import según tu estructura
from ..core.security import verificar_contrasena, crear_token
from ..schemas import Token


router = APIRouter(prefix="/auth", tags=["Autenticación (Login / Registro)"])


class Credenciales(BaseModel):
    nombre_usuario: str
    contrasena: str


@router.post("/login", response_model=Token)
def login(credenciales: Credenciales, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(func.lower(Usuario.nombre) == credenciales.nombre_usuario.lower()).first()
    if not usuario:
        raise HTTPException(status_code=400, detail="Usuario no encontrado")

    if not verificar_contrasena(credenciales.contrasena, usuario.password):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    token = crear_token({"sub": str(usuario.id), "rol": usuario.id_rol})

    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": {"id": usuario.id, "nombre": usuario.nombre, "rol": usuario.id_rol, "correo": usuario.email},
    }


@router.post("/registro", response_model=schemas.UsuarioOut)
def registrar_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    return crud.crear_usuario(db, usuario)
