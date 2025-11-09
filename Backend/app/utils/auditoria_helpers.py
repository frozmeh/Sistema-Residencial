from sqlalchemy.orm import Session
from datetime import datetime, date
from .. import models


def limpiar_json(obj):
    """Convierte datetime y date a string para JSON."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: limpiar_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [limpiar_json(v) for v in obj]
    else:
        return obj


def filtrar_campos(datos: dict, visibles: list = None):
    """Filtra los campos según una lista visible o quita sensibles por defecto."""
    if not datos:
        return {}
    if visibles:
        return {k: v for k, v in datos.items() if k in visibles}
    else:
        campos_excluidos = {"ultimo_ip", "intentos_fallidos", "fecha_bloqueo"}
        return {k: v for k, v in datos.items() if k not in campos_excluidos}


def registrar_auditoria(
    db: Session,
    usuario_id: int,
    usuario_nombre: str,
    accion: str,
    tabla: str,
    objeto_previo: dict = None,
    objeto_nuevo: dict = None,
    request: any = None,
    campos_visibles: list = None,
    forzar: bool = False,
):
    # Calcular cambios
    previo_filtrado = {}
    nuevo_filtrado = {}
    cambios = {}
    if objeto_previo and objeto_nuevo:
        previo_filtrado = filtrar_campos(objeto_previo, campos_visibles)
        nuevo_filtrado = filtrar_campos(objeto_nuevo, campos_visibles)
        cambios = {
            k: {"antes": previo_filtrado[k], "despues": nuevo_filtrado[k]}
            for k in previo_filtrado
            if previo_filtrado[k] != nuevo_filtrado[k]
        }

    # Si es actualización y no hay cambios reales, no registrar
    if previo_filtrado and nuevo_filtrado and not cambios and not forzar:
        return  # nada que auditar

    # Datos extra
    ip = request.client.host if request else None
    endpoint = f"{request.method} {request.url.path}" if request else None

    # Si es un registro nuevo
    if not objeto_previo and objeto_nuevo:
        nuevo_filtrado = filtrar_campos(objeto_nuevo, campos_visibles)
        detalle = {"añadido": nuevo_filtrado, "ip": ip, "endpoint": endpoint}
    else:
        detalle = {"cambios": cambios if cambios else None, "ip": ip, "endpoint": endpoint}

    detalle = limpiar_json(detalle)

    # Guardar auditoría
    audit = models.Auditoria(
        id_usuario=usuario_id,
        nombre_usuario=usuario_nombre,
        accion=accion,
        tabla_afectada=tabla,
        detalle=detalle,
        fecha=datetime.now(),
    )
    db.add(audit)
    db.commit()
