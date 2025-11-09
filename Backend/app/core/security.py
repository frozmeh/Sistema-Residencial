from datetime import datetime, timedelta
from sqlalchemy import func
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload
from dotenv import load_dotenv
from ..database import get_db
from ..models import Usuario
from .. import crud
from ..core.config import settings

load_dotenv()

# Configuración desde variables de entorno
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def encriptar_contrasena(password: str):
    return pwd_context.hash(password)


def verificar_contrasena(password_plano: str, password_hash: str):
    return pwd_context.verify(password_plano, password_hash)


def crear_tokens(data: dict):
    access_token = crear_access_token(data)
    refresh_token = crear_refresh_token(data)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


def crear_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def crear_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decodificar_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_usuario_actual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    request: Request = None,  # ✅ Opcional: agregar request si quieres actualizar en cada llamada
):
    payload = decodificar_token(token)

    # Verificar tipo de token
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Tipo de token inválido")

    usuario_id = payload.get("sub")
    if not usuario_id:
        raise HTTPException(status_code=401, detail="Token inválido")

    usuario = db.query(Usuario).options(joinedload(Usuario.rol)).filter(Usuario.id == int(usuario_id)).first()

    if not usuario or usuario.estado != "Activo":  # ✅ Cambiar a comparación directa
        raise HTTPException(status_code=403, detail="Usuario inactivo o bloqueado")

    # Actualizar última actividad en cada llamada (comentar si no quieres)
    usuario.ultima_sesion = func.now()
    if request and request.client:
        usuario.ultimo_ip = request.client.host
    db.commit()

    return usuario


def refresh_access_token(refresh_token: str, db: Session):
    """Renueva el access token usando un refresh token válido"""
    try:
        payload = decodificar_token(refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token de refresh inválido")

        usuario_id = payload.get("sub")
        if not usuario_id:
            raise HTTPException(status_code=401, detail="Token inválido")

        # Verificar que el usuario aún existe y está activo
        usuario = db.query(Usuario).filter(Usuario.id == int(usuario_id), Usuario.estado == "Activo").first()

        if not usuario:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")

        # Crear nuevo access token
        new_access_token = crear_access_token({"sub": str(usuario.id)})

        return {"access_token": new_access_token, "token_type": "bearer"}

    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token inválido o expirado")


# ==============================
# ---- Verificación por rol ----
# ==============================


def verificar_admin(usuario: Usuario = Depends(get_usuario_actual)):
    if usuario.rol.nombre.lower() != "administrador":
        raise HTTPException(status_code=403, detail="Se requieren permisos de administrador.")
    return usuario


def verificar_residente(usuario: Usuario = Depends(get_usuario_actual), db: Session = Depends(get_db)):
    if usuario.rol.nombre.lower() != "residente":
        raise HTTPException(status_code=403, detail="Se requieren permisos de residente.")

    residente = crud.obtener_residente_asociado(db, usuario.id)

    if residente.estado_aprobacion != "Aprobado":
        raise HTTPException(status_code=403, detail="Residente no aprobado por administración.")

    if residente.estado_operativo != "Activo":
        raise HTTPException(status_code=403, detail="Residente inactivo o suspendido.")

    return residente
