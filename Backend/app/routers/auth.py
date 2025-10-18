from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Usuario  # Ajusta el import según tu estructura
from passlib.context import CryptContext

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
    usuario = (
        db.query(Usuario).filter(Usuario.nombre == credenciales.nombre_usuario).first()
    )
    if not usuario:
        raise HTTPException(status_code=400, detail="Usuario no encontrado")

    if not verificar_contrasena(credenciales.contrasena, usuario.password):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "rol": usuario.id_rol,
        "correo": usuario.email,
    }
