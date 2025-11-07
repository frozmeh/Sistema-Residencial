from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ...schemas.roles import RolMensajeOut
from ... import crud, schemas
from ...database import get_db
from ...core.security import verificar_admin

router = APIRouter(prefix="/roles", tags=["Roles"])


# ---- Schemas adicionales ----


# ===============
# ---- Roles ----
# ===============


@router.get("/", response_model=list[schemas.RolOut])
def listar_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    return crud.obtener_roles(db, skip, limit)


@router.post("/", response_model=RolMensajeOut)
def crear_nuevo_rol(rol: schemas.RolCreate, db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    rol_creado = crud.crear_rol(db, rol)
    return {"mensaje": "Rol creado correctamente", "rol": rol_creado}
