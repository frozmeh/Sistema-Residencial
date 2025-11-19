from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models, schemas
from ..core.security import encriptar_contrasena
from ..utils.validaciones import validar_usuario, validar_contrasena
from ..utils.db_helpers import guardar_y_refrescar
from ..utils.auditoria_helpers import registrar_auditoria


# =================
# ---- Usuario ----
# =================


def crear_usuario(
    db: Session,
    usuario: schemas.UsuarioCreate,
    request=None,
):
    validar_usuario(nombre=usuario.nombre, email=usuario.email, password=usuario.password)

    if db.query(models.Usuario).filter(func.lower(models.Usuario.nombre) == usuario.nombre.lower()).first():
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")

    if db.query(models.Usuario).filter(func.lower(models.Usuario.email) == usuario.email.lower()).first():
        raise HTTPException(status_code=400, detail="El correo ya está en uso")

    datos_usuario = usuario.dict()
    datos_usuario["password"] = encriptar_contrasena(usuario.password)
    db_usuario = models.Usuario(**datos_usuario)
    db.add(db_usuario)
    guardar_y_refrescar(db, db_usuario)

    registrar_auditoria(
        db=db,
        usuario_id=db_usuario.id,
        usuario_nombre=db_usuario.nombre,
        accion="Registro inicial de cuenta",
        tabla="usuarios",
        objeto_previo=None,
        objeto_nuevo={c.name: getattr(db_usuario, c.name) for c in db_usuario.__table__.columns},
        request=request,
        campos_visibles=["nombre", "email", "estado", "fecha_creacion", "password"],
        forzar=True,
    )

    return db_usuario


def obtener_usuarios(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Usuario).order_by(models.Usuario.id.asc()).offset(skip).limit(limit).all()


def listar_usuarios_activos(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Usuario)
        .filter(models.Usuario.estado == "Activo")
        .order_by(models.Usuario.id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def buscar_usuarios(db: Session, q: str):
    return (
        db.query(models.Usuario)
        .filter((models.Usuario.nombre.ilike(f"%{q}%")) | (models.Usuario.email.ilike(f"%{q}%")))
        .all()
    )


def obtener_usuario_por_nombre(db: Session, nombre_usuario: int):
    usuario = db.query(models.Usuario).filter(models.Usuario.nombre == nombre_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


def obtener_usuario_por_email(db: Session, email_usuario: int):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


def obtener_usuario_por_id(db: Session, id_usuario: int):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


def actualizar_usuario(
    db: Session,
    id_usuario: int,
    nuevo_nombre: str = None,
    nuevo_email: str = None,
    usuario_actual=None,
    request=None,
):
    usuario = db.get(models.Usuario, id_usuario)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario_previo = {c.name: getattr(usuario, c.name) for c in usuario.__table__.columns}

    if nuevo_nombre:
        if (
            db.query(models.Usuario)
            .filter(func.lower(models.Usuario.nombre) == nuevo_nombre.lower(), models.Usuario.id != id_usuario)
            .first()
        ):
            raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")

    if nuevo_email:
        if (
            db.query(models.Usuario)
            .filter(func.lower(models.Usuario.email) == nuevo_email.lower(), models.Usuario.id != id_usuario)
            .first()
        ):
            raise HTTPException(status_code=400, detail="El correo ya está en uso")

    if nuevo_nombre or nuevo_email:
        validar_usuario(
            nombre=nuevo_nombre if nuevo_nombre else usuario.nombre,
            email=nuevo_email if nuevo_email else usuario.email,
        )

    if nuevo_nombre:
        usuario.nombre = nuevo_nombre
    if nuevo_email:
        usuario.email = nuevo_email

    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    if usuario_actual:

        registrar_auditoria(
            db=db,
            usuario_id=usuario_actual.id,
            usuario_nombre=usuario_actual.nombre,
            accion="Actualizar datos de Usuario",
            tabla="usuarios",
            objeto_previo=usuario_previo,
            objeto_nuevo={c.name: getattr(usuario, c.name) for c in usuario.__table__.columns},
            request=request,
        )

    return usuario


def cambiar_rol_usuario(db: Session, id_usuario: int, nuevo_id_rol: int, request=None):
    usuario = obtener_usuario_por_id(db, id_usuario)

    usuario_previo = {c.name: getattr(usuario, c.name) for c in usuario.__table__.columns}
    usuario.id_rol = nuevo_id_rol

    guardar_y_refrescar(db, usuario)
    registrar_auditoria(
        db=db,
        usuario_id=usuario.id,
        usuario_nombre=usuario.nombre,
        accion="Actualización de rol de Usuario",
        tabla="usuarios",
        objeto_previo=usuario_previo,
        objeto_nuevo={c.name: getattr(usuario, c.name) for c in usuario.__table__.columns},
        request=request,
    )
    return usuario


def cambiar_estado_usuario(db: Session, id_usuario: int, nuevo_estado: str, request=None):
    usuario = obtener_usuario_por_id(db, id_usuario)

    estados_validos = ["Activo", "Inactivo", "Bloqueado"]
    if nuevo_estado not in estados_validos:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Opciones: {', '.join(estados_validos)}")

    if usuario.estado == nuevo_estado:
        raise HTTPException(status_code=400, detail=f"El usuario ya se encuentra en estado '{nuevo_estado}'.")

    usuario_previo = {c.name: getattr(usuario, c.name) for c in usuario.__table__.columns}
    usuario.estado = nuevo_estado
    guardar_y_refrescar(db, usuario)

    registrar_auditoria(
        db=db,
        usuario_id=usuario.id,
        usuario_nombre=usuario.nombre,
        accion="Actualización de estado de Usuario",
        tabla="usuarios",
        objeto_previo=usuario_previo,
        objeto_nuevo={c.name: getattr(usuario, c.name) for c in usuario.__table__.columns},
        request=request,
    )
    return usuario


def cambiar_password(db: Session, id_usuario: int, nueva_password: str, request=None):
    usuario = obtener_usuario_por_id(db, id_usuario)
    validar_contrasena(nueva_password)

    usuario_previo = {c.name: getattr(usuario, c.name) for c in usuario.__table__.columns}
    usuario.password = encriptar_contrasena(nueva_password)
    guardar_y_refrescar(db, usuario)

    registrar_auditoria(
        db=db,
        usuario_id=usuario.id,
        usuario_nombre=usuario.nombre,
        accion="Actualización de contraseña",
        tabla="usuarios",
        objeto_previo=usuario_previo,
        objeto_nuevo={c.name: getattr(usuario, c.name) for c in usuario.__table__.columns},
        request=request,
        campos_visibles=["nombre", "email", "password"],
        forzar=True,
    )
    return usuario
