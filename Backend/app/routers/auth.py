from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import func
from ..database import get_db
from ..models import Usuario  # Ajusta el import según tu estructura
from passlib.context import CryptContext
from jose import jwt


SECRET_KEY = "Santiago.02"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def crear_token(data: dict, expira_en_minutos: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expiracion = datetime.utcnow() + timedelta(minutes=expira_en_minutos)
    to_encode.update({"exp": expiracion})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token


router = APIRouter(prefix="/auth", tags=["Auth"])

# Creamos el contexto para manejar hashes con bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Función para encriptar contraseñas nuevas
def encriptar_contrasena(contrasena: str):
    return pwd_context.hash(contrasena)


# Función para verificar contraseñas al iniciar sesión
def verificar_contrasena(contrasena_plana: str, hash_guardado: str):
    return pwd_context.verify(contrasena_plana, hash_guardado)


class Credenciales(BaseModel):
    nombre_usuario: str
    contrasena: str


@router.post("/login")
def login(credenciales: Credenciales, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(func.lower(Usuario.nombre) == credenciales.nombre_usuario.lower()).first()
    if not usuario:
        raise HTTPException(status_code=400, detail="Usuario no encontrado")

    if not verificar_contrasena(credenciales.contrasena, usuario.password):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    # Crear token JWT
    token = crear_token({"sub": str(usuario.id), "rol": usuario.id_rol})

    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": {"id": usuario.id, "nombre": usuario.nombre, "rol": usuario.id_rol, "correo": usuario.email},
    }
