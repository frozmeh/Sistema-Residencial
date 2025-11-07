from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session
from .. import schemas, crud
from ..core.security import get_usuario_actual
from ..database import get_db

router = APIRouter(prefix="/usuario", tags=["Usuarios (General)"])


# ===================================
# ----- Ruta general (Usuarios) -----
# ===================================


@router.get("/me", response_model=schemas.UsuarioOut)
def obtener_mis_datos(usuario=Depends(get_usuario_actual), db: Session = Depends(get_db)):
    return crud.obtener_usuario_por_id(db, usuario.id)
