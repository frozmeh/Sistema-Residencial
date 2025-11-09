from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from ... import schemas, crud, models
from ...database import get_db
from ...core.security import verificar_admin

router = APIRouter(prefix="/usuarios", tags=["Usuarios (Administración)"])


# ================================
# ----- Ruta Usuario (Admin) -----
# ================================


@router.post("/", response_model=schemas.UsuarioOut)
def crear_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db), request: Request = None):
    return crud.crear_usuario(db, usuario, request=request)


@router.get("/", response_model=list[schemas.UsuarioOut])
def listar_usuarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    return crud.obtener_usuarios(db, skip, limit)


@router.get("/activos", response_model=list[schemas.UsuarioOut])
def listar_usuarios_activos(db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    return crud.listar_usuarios_activos(db)


@router.get("/buscar", response_model=list[schemas.UsuarioOut])
def buscar_usuarios(q: str, db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    return crud.buscar_usuarios(db, q)


@router.get("/buscar/nombre", response_model=schemas.UsuarioOut)
def buscar_usuario_por_nombre(nombre: str, db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    return crud.obtener_usuario_por_nombre(db, nombre)


@router.get("/buscar/email", response_model=schemas.UsuarioOut)
def obtener_usuario_por_email(email: str, db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    return crud.obtener_usuario_por_email(db, email)


@router.get("/{id_usuario}", response_model=schemas.UsuarioOut)
def obtener_usuario(id_usuario: int, db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    return crud.obtener_usuario_por_id(db, id_usuario)


@router.put("/{id_usuario}", response_model=schemas.UsuarioOut)
def actualizar_usuario(
    id_usuario: int,
    datos: schemas.UsuarioUpdate,
    db: Session = Depends(get_db),
    admin: models.Usuario = Depends(verificar_admin),
    request: Request = None,
):
    return crud.actualizar_usuario(db, id_usuario, datos.nombre, datos.email, usuario_actual=admin, request=request)


@router.put("/{id_usuario}/rol", response_model=schemas.UsuarioEstadoResponse)
def cambiar_rol(
    id_usuario: int,
    datos: schemas.UsuarioUpdate,
    db: Session = Depends(get_db),
    admin=Depends(verificar_admin),
    request: Request = None,
):
    return crud.cambiar_rol_usuario(db, id_usuario, datos.id_rol, request=request)


@router.put("/{id_usuario}/desactivar", response_model=schemas.UsuarioEstadoResponse)
def desactivar_usuario(
    id_usuario: int, db: Session = Depends(get_db), admin=Depends(verificar_admin), request: Request = None
):
    return crud.cambiar_estado_usuario(db, id_usuario, "Inactivo", request=request)


@router.put("/{id_usuario}/reactivar", response_model=schemas.UsuarioEstadoResponse)
def reactivar_usuario(
    id_usuario: int, db: Session = Depends(get_db), admin=Depends(verificar_admin), request: Request = None
):
    return crud.cambiar_estado_usuario(db, id_usuario, "Activo", request=request)


@router.put("/{id_usuario}/bloquear", response_model=schemas.UsuarioEstadoResponse)
def bloquear_usuario(
    id_usuario: int, db: Session = Depends(get_db), admin=Depends(verificar_admin), request: Request = None
):
    return crud.cambiar_estado_usuario(db, id_usuario, "Bloqueado", request=request)


@router.put("/{id_usuario}/cambiar-password", response_model=schemas.UsuarioEstadoResponse)
def resetear_password(
    id_usuario: int,
    datos: schemas.UsuarioUpdate,
    db: Session = Depends(get_db),
    admin=Depends(verificar_admin),
    request: Request = None,
):
    return crud.cambiar_password(db, id_usuario, datos.password, request=request)


@router.get("/{id_usuario}/residente", response_model=schemas.ResidenteOut)
def obtener_residente_asociado(id_usuario: int, db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    return crud.obtener_residente_asociado(db, id_usuario)
