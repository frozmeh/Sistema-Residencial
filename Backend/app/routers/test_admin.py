from fastapi import APIRouter, Depends
from ..core.security import get_usuario_actual, validar_permiso

router = APIRouter(prefix="/admin/test", tags=["Test Admin"])


@router.get("/roles")
def probar_roles(usuario=Depends(get_usuario_actual)):
    validar_permiso(usuario, "Apartamento", "crear")
    return {"mensaje": "Tienes permiso para leer usuarios"}
