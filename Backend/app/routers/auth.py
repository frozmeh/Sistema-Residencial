from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from .. import crud, schemas
from ..database import get_db
from ..models import Usuario
from ..core.security import verificar_contrasena, crear_tokens, refresh_access_token, get_usuario_actual


router = APIRouter(prefix="/auth", tags=["Autenticación (Login / Registro)"])


class Credenciales(BaseModel):
    nombre_usuario: str
    contrasena: str


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str
    usuario: dict


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/login", response_model=Token)
def login(
    credenciales: Credenciales,
    db: Session = Depends(get_db),
    request: Request = None,  # Agregar request para obtener IP
):
    # Buscar usuario por nombre
    usuario = (
        db.query(Usuario)
        .options(joinedload(Usuario.rol))
        .filter(func.lower(Usuario.nombre) == credenciales.nombre_usuario.lower())
        .first()
    )

    if not usuario:
        raise HTTPException(status_code=400, detail="Usuario no encontrado")

    if usuario.estado != "Activo":
        raise HTTPException(status_code=403, detail="Usuario inactivo o bloqueado")

    if not verificar_contrasena(credenciales.contrasena, usuario.password):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    usuario.ultima_sesion = func.now()
    if request and request.client:
        usuario.ultimo_ip = request.client.host
    usuario.intentos_fallidos = 0  # Resetear intentos fallidos en login exitoso
    db.commit()

    tokens = crear_tokens({"sub": str(usuario.id), "rol": usuario.id_rol})

    return {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "token_type": "bearer",
        "usuario": {
            "id": usuario.id,
            "nombre": usuario.nombre,
            "rol": usuario.id_rol,
            "email": usuario.email,
            "rol_nombre": usuario.rol.nombre,
        },
    }


@router.post("/refresh")
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Renueva el access token usando un refresh token"""
    return refresh_access_token(request.refresh_token, db)


@router.post("/registro", response_model=schemas.UsuarioOut)
def registrar_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    return crud.crear_usuario(db, usuario)


@router.get("/me", response_model=schemas.UsuarioOut)
def obtener_usuario_actual(usuario: Usuario = Depends(get_usuario_actual)):
    """Obtener información del usuario actualmente autenticado"""
    return usuario
