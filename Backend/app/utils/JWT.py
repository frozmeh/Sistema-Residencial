from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db

SECRET_KEY = "clave_super_secreta_que_debes_cambiar"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")  # Ruta de login


# -----------------
# Contraseñas
# -----------------
def encriptar_contrasena(password: str):
    return pwd_context.hash(password)


def verificar_contrasena(password_plano: str, password_hash: str):
    return pwd_context.verify(password_plano, password_hash)


# -----------------
# JWT
# -----------------
def crear_token(data: dict, expira_en_minutos: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expiracion = datetime.utcnow() + timedelta(minutes=expira_en_minutos)
    to_encode.update({"exp": expiracion})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decodificar_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


# -----------------
# Obtener usuario logueado
# -----------------
def get_usuario_actual(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decodificar_token(token)
    usuario_id = payload.get("sub")
    if usuario_id is None:
        raise HTTPException(status_code=401, detail="Token inválido")
    usuario = db.query(models.Usuario).filter(models.Usuario.id == int(usuario_id)).first()
    if not usuario or usuario.estado != "Activo":
        raise HTTPException(status_code=403, detail="Usuario inactivo o bloqueado")
    return usuario
