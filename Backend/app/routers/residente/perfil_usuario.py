from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from ... import schemas, crud, models
from ...database import get_db
from ...core.security import verificar_residente

router = APIRouter(prefix="/perfil", tags=["Usuario - Perfil y Gestión"])


# =====================================
# ----- Ruta Usuario (Residentes) -----
# =====================================


@router.get("/me", response_model=schemas.UsuarioOut)
def obtener_mis_datos(usuario=Depends(verificar_residente), db: Session = Depends(get_db)):
    return crud.obtener_usuario_por_id(db, usuario.id)


@router.put("/me", response_model=schemas.UsuarioOut)
def actualizar_mis_datos(
    datos: schemas.UsuarioUpdate,
    db: Session = Depends(get_db),
    request: Request = None,
    usuario: models.Usuario = Depends(verificar_residente),
):
    return crud.actualizar_usuario(db, usuario.id, datos.nombre, datos.email, usuario_actual=usuario, request=request)


@router.put("/me/password", response_model=schemas.UsuarioEstadoResponse)
def cambiar_mi_password(
    datos: schemas.UsuarioUpdate,
    usuario=Depends(verificar_residente),
    db: Session = Depends(get_db),
    request: Request = None,
):
    return crud.cambiar_password(
        db=db, id_usuario=usuario.id, nueva_password=datos.password, usuario_actual=usuario, request=request
    )


@router.get("/me/residente", response_model=schemas.ResidenteOut)
def obtener_mi_residente(usuario=Depends(verificar_residente), db: Session = Depends(get_db)):
    return crud.obtener_residente_asociado(db, usuario.id)
