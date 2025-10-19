from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..utils.seguridad import encriptar_contrasena
from ..utils.validaciones import validar_usuario, validar_contrasena
from ..utils.db_helpers import guardar_y_refrescar, obtener_usuario_por_id


# ==================
# ---- Usuario ----
# ==================


def crear_usuario(db: Session, usuario: schemas.UsuarioCreate):
    validar_usuario(nombre=usuario.nombre, email=usuario.email, password=usuario.password)

    if db.query(models.Usuario).filter(models.Usuario.nombre == usuario.nombre).first():
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")
    if db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first():
        raise HTTPException(status_code=400, detail="El correo ya está en uso")

    datos_usuario = usuario.dict()
    datos_usuario["password"] = encriptar_contrasena(usuario.password)
    db_usuario = models.Usuario(**datos_usuario)
    db.add(db_usuario)
    guardar_y_refrescar(db, db_usuario)
    return db_usuario


def actualizar_usuario(
    db: Session,
    id_usuario: int,
    nuevo_nombre: str = None,
    nuevo_email: str = None,
    nueva_password: str = None,
):
    usuario = obtener_usuario_por_id(db, id_usuario)
    validar_usuario(nombre=nuevo_nombre, email=nuevo_email, password=nueva_password)

    usuario.nombre = nuevo_nombre
    usuario.email = nuevo_email
    usuario.password = encriptar_contrasena(nueva_password)

    guardar_y_refrescar(db, usuario)
    return usuario


def cambiar_password(db: Session, id_usuario: int, nueva_password: str):
    usuario = obtener_usuario_por_id(db, id_usuario)

    validar_contrasena(nueva_password)

    usuario.password = encriptar_contrasena(nueva_password)
    guardar_y_refrescar(db, usuario)
    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "mensaje": "Contraseña actualizada",
    }


def actualizar_ultima_sesion(db: Session, id_usuario: int):
    usuario = obtener_usuario_por_id(db, id_usuario)
    usuario.ultima_sesion = datetime.utcnow()
    guardar_y_refrescar(db, usuario)
    return usuario


def cambiar_rol_usuario(db: Session, id_usuario: int, nuevo_id_rol: int):
    usuario = obtener_usuario_por_id(db, id_usuario)

    usuario.id_rol = nuevo_id_rol
    guardar_y_refrescar(db, usuario)
    return usuario


def desactivar_usuario(db: Session, id_usuario: int):
    usuario = obtener_usuario_por_id(db, id_usuario)

    usuario.estado = "Inactivo"
    guardar_y_refrescar(db, usuario)
    return usuario


def obtener_usuarios(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Usuario).offset(skip).limit(limit).all()
