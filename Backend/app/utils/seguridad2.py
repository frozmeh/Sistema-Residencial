from fastapi import HTTPException
from ..crud import obtener_usuario_por_id
from ..models import Usuario


def validar_permiso(usuario: "Usuario", entidad: str, accion: str):
    """
    Valida que el usuario tenga permiso para realizar la acción sobre la entidad.
    """
    if not usuario or not usuario.rol or not usuario.rol.permisos:
        raise HTTPException(status_code=403, detail="No tiene permisos asignados")

    permisos_rol = usuario.rol.permisos  # JSON almacenado en DB

    # Verificar si la entidad existe en los permisos
    if entidad not in permisos_rol:
        raise HTTPException(
            status_code=403,
            detail=f"Su rol no tiene acceso a la entidad '{entidad}'",
        )

    # Verificar si la acción está permitida
    if accion not in permisos_rol[entidad]:
        raise HTTPException(
            status_code=403,
            detail=f"Su rol no tiene permiso para '{accion}' en '{entidad}'",
        )

    return True
