from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import func
from ..database import get_db
from ..models import Usuario  # Ajusta el import según tu estructura
from passlib.context import CryptContext
from jose import jwt
from ..core.security import verificar_contrasena, crear_token
from ..schemas import Token


SECRET_KEY = "Santiago.02"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

router = APIRouter(prefix="/auth", tags=["Auth"])


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
