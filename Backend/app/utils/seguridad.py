from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Usuario

# Configuración JWT
SECRET_KEY = "cambia_esta_clave_por_una_segura_y_larga"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 para FastAPI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


# ---------- Contraseñas ----------
def encriptar_contrasena(password: str):
    return pwd_context.hash(password)


def verificar_contrasena(password_plano: str, password_hash: str):
    return pwd_context.verify(password_plano, password_hash)


# ---------- JWT ----------
def crear_token(data: dict, expira_en_minutos: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expiracion = datetime.utcnow() + timedelta(minutes=expira_en_minutos)
    to_encode.update({"exp": expiracion})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decodificar_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------- Usuario logueado ----------
def get_usuario_actual(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decodificar_token(token)
    usuario_id = payload.get("sub")
    if not usuario_id:
        raise HTTPException(status_code=401, detail="Token inválido")
    usuario = db.query(Usuario).filter(Usuario.id == int(usuario_id)).first()
    if not usuario or usuario.estado != "Activo":
        raise HTTPException(status_code=403, detail="Usuario inactivo o bloqueado")
    return usuario
