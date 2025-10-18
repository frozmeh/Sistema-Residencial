from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.post("/", response_model=schemas.UsuarioOut)
def crear_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    return crud.crear_usuario(db, usuario)


@router.get("/", response_model=list[schemas.UsuarioOut])
def listar_usuarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.obtener_usuarios(db, skip, limit)


@router.put("/ultima_sesion/{id_usuario}", response_model=schemas.UsuarioOut)
def actualizar_sesion(id_usuario: int, db: Session = Depends(get_db)):
    usuario = crud.actualizar_ultima_sesion(db, id_usuario)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@router.put("/{id_usuario}/desactivar")
def desactivar_usuario(id_usuario: int, db: Session = Depends(get_db)):
    try:
        usuario_desactivado = crud.desactivar_usuario(db, id_usuario)
        return {
            "mensaje": f"Usuario {id_usuario} desactivado correctamente",
            "usuario": usuario_desactivado,
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# Endpoint para cambiar rol
@router.put("/{id_usuario}/rol")
def actualizar_rol_usuario(
    id_usuario: int, nuevo_id_rol: int, db: Session = Depends(get_db)
):
    try:
        usuario_actualizado = crud.cambiar_rol_usuario(db, id_usuario, nuevo_id_rol)
        return {"mensaje": "Rol actualizado", "usuario": usuario_actualizado}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{id_usuario}/cambiar_password")
def cambiar_password(
    id_usuario: int, nueva_password: str, db: Session = Depends(get_db)
):
    return crud.cambiar_password(db, id_usuario, nueva_password)
