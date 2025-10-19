from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db
from ..utils.seguridad2 import validar_permiso
from ..models import Usuario


router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


# ---- Schemas de entrada adicionales ----


class CambiarRol(schemas.BaseModel):
    nuevo_id_rol: int


class CambiarPassword(schemas.BaseModel):
    nueva_password: str


class UsuarioMensajeOut(schemas.BaseModel):
    mensaje: str
    usuario: schemas.UsuarioOut


# ---- Endpoints ----


@router.post("/", response_model=schemas.UsuarioOut)
def crear_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    return crud.crear_usuario(db, usuario)


@router.get("/", response_model=list[schemas.UsuarioOut])
def listar_usuarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.obtener_usuarios(db, skip, limit)


@router.put("/ultima_sesion/{id_usuario}", response_model=schemas.UsuarioOut)
def actualizar_sesion(id_usuario: int, db: Session = Depends(get_db)):
    crud.actualizar_ultima_sesion(db, id_usuario)


@router.put("/{id_usuario}/desactivar", response_model=UsuarioMensajeOut)
def desactivar_usuario(id_usuario: int, db: Session = Depends(get_db)):
    usuario_desactivado = crud.desactivar_usuario(db, id_usuario)
    return {
        "mensaje": f"Usuario {id_usuario} desactivado correctamente",
        "usuario": usuario_desactivado,
    }


"""
@router.put("/{id_usuario}/desactivar", response_model=schemas.UsuarioOut)
def desactivar_usuario_endpoint(
    id_usuario: int,
    db: Session = Depends(get_db),
    usuario_actual: "Usuario" = Depends(
        crud.get_usuario_logueado
    ),  # ejemplo: tu función de login
):
    # Validar permiso
    validar_permiso(usuario_actual, entidad="Usuario", accion="eliminar")

    # Ejecutar la acción
    usuario_desactivado = crud.desactivar_usuario(db, id_usuario)
    return usuario_desactivado
"""


@router.put("/{id_usuario}/rol", response_model=UsuarioMensajeOut)
def actualizar_rol_usuario(id_usuario: int, datos: CambiarRol, db: Session = Depends(get_db)):
    usuario_actualizado = crud.cambiar_rol_usuario(db, id_usuario, datos.nuevo_id_rol)
    return {"mensaje": "Rol actualizado", "usuario": usuario_actualizado}


@router.put("/{id_usuario}/cambiar_password", response_model=UsuarioMensajeOut)
def cambiar_password(id_usuario: int, datos: CambiarPassword, db: Session = Depends(get_db)):
    return crud.cambiar_password(db, id_usuario, datos.nueva_password)
