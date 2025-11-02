from fastapi import APIRouter, Depends
from ..core.security import get_usuario_actual

router = APIRouter(prefix="/test", tags=["Pruebas"])


@router.get("/usuario")
def obtener_usuario(usuario_actual=Depends(get_usuario_actual)):
    return {"id": usuario_actual.id, "rol": usuario_actual.rol.nombre}
