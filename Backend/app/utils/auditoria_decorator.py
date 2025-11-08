from functools import wraps
from sqlalchemy.orm import Session
from fastapi import Request
from .. import models
import datetime
from decimal import Decimal


def to_serializable(value):
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    elif isinstance(value, Decimal):
        return float(value)
    elif value is None:
        return None
    else:
        return str(value)


def auditar_completo(modelo, nombre_tabla: str):
    """
    Decorador para auditar funciones CRUD de FastAPI.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            db: Session = kwargs.get("db")
            request: Request = kwargs.get("request")
            usuario_actual = kwargs.get("usuario") or kwargs.get("usuario_actual")
            id_usuario_actual = getattr(usuario_actual, "id", None)
            obj_id = kwargs.get("id_objeto") or getattr(kwargs.get("datos", None), "id", None) or kwargs.get("id")

            if db is None:
                raise ValueError("No se encontró 'db' para la auditoría")
            if id_usuario_actual is None:
                raise ValueError("No se encontró 'usuario_actual' para la auditoría")

            # Estado previo (solo actualizar/eliminar)
            objeto_previo = None
            if func.__name__.startswith(("actualizar", "modificar", "eliminar")) and obj_id:
                objeto_previo_db = db.get(modelo, obj_id)
                if objeto_previo_db:
                    objeto_previo = {
                        c.name: to_serializable(getattr(objeto_previo_db, c.name))
                        for c in objeto_previo_db.__table__.columns
                    }

            # Ejecutar función original
            resultado = func(*args, **kwargs)

            # Acción
            if func.__name__.startswith("crear"):
                accion = "Crear"
            elif func.__name__.startswith(("actualizar", "modificar", "cambiar")):
                accion = "Actualizar"
            elif func.__name__.startswith(("eliminar", "borrar")):
                accion = "Eliminar"
            else:
                return resultado  # no auditar lecturas

            # Cambios
            cambios = {}
            if accion == "Actualizar" and objeto_previo and hasattr(resultado, "__table__"):
                objeto_nuevo = {
                    c.name: to_serializable(getattr(resultado, c.name)) for c in resultado.__table__.columns
                }
                cambios = {
                    k: {"antes": objeto_previo[k], "después": objeto_nuevo[k]}
                    for k in objeto_previo
                    if objeto_previo[k] != objeto_nuevo[k]
                }

            # Info request
            ip = request.client.host if request else "Desconocida"
            endpoint = f"{request.method} {request.url.path}" if request else "Desconocido"

            # Detalle estructurado
            detalle_struct = {"cambios": cambios if cambios else None, "ip": ip, "endpoint": endpoint}

            # Guardar auditoría
            audit = models.Auditoria(
                id_usuario=id_usuario_actual,
                accion=accion,
                tabla_afectada=nombre_tabla,
                detalle=detalle_struct,
                fecha=datetime.datetime.now(),
            )

            nueva_sesion = Session(bind=db.bind)
            nueva_sesion.add(audit)
            nueva_sesion.commit()
            nueva_sesion.close()

            return resultado

        return wrapper

    return decorator
