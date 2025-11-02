from functools import wraps
from sqlalchemy.orm import Session
from .. import models, schemas
import json


def auditar_completo(tabla_afectada: str):
    """
    Decorador para registrar auditoría con detalle completo y cambios exactos en actualizaciones.
    tabla_afectada: nombre de la tabla sobre la que se realiza la acción.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            db: Session = kwargs.get("db")
            id_usuario_actual: int = kwargs.get("id_usuario_actual")

            if db is None or id_usuario_actual is None:
                raise ValueError("Se requiere 'db' y 'id_usuario_actual' como argumentos")

            # Para actualizaciones, capturar estado previo
            objeto_previo = None
            if func.__name__.startswith("actualizar") or func.__name__.startswith("modificar"):
                obj_id = kwargs.get("id_" + tabla_afectada[:-1])  # asume convención 'id_usuario', 'id_pago', etc.
                objeto_previo = db.query(getattr(models, tabla_afectada.capitalize())).get(obj_id)
                if objeto_previo:
                    objeto_previo = {c.name: getattr(objeto_previo, c.name) for c in objeto_previo.__table__.columns}

            # Ejecutar función CRUD
            resultado = func(*args, **kwargs)

            # Determinar acción
            if func.__name__.startswith("crear"):
                accion = "Crear"
            elif func.__name__.startswith("actualizar") or func.__name__.startswith("modificar"):
                accion = "Actualizar"
            elif func.__name__.startswith("eliminar") or func.__name__.startswith("borrar"):
                accion = "Eliminar"
            else:
                accion = "Acción"

            # Generar detalle
            detalle = ""
            try:
                if accion == "Actualizar" and objeto_previo:
                    # diff entre objeto previo y resultado
                    objeto_nuevo = {c.name: getattr(resultado, c.name) for c in resultado.__table__.columns}
                    cambios = {
                        k: {"antes": objeto_previo[k], "después": objeto_nuevo[k]}
                        for k in objeto_previo
                        if objeto_previo[k] != objeto_nuevo[k]
                    }
                    detalle = json.dumps(cambios, ensure_ascii=False)
                elif hasattr(resultado, "__table__"):
                    detalle = json.dumps(
                        {c.name: getattr(resultado, c.name) for c in resultado.__table__.columns}, ensure_ascii=False
                    )
                elif isinstance(resultado, list):
                    detalle = json.dumps(
                        [
                            {c.name: getattr(item, c.name) for c in item.__table__.columns}
                            for item in resultado
                            if hasattr(item, "__table__")
                        ],
                        ensure_ascii=False,
                    )
                elif isinstance(resultado, bool):
                    detalle = f"Resultado: {resultado}"
                else:
                    detalle = str(resultado)
            except Exception as e:
                detalle = f"No se pudo generar detalle automáticamente: {str(e)}"

            # Registrar auditoría
            audit = schemas.AuditoriaCreate(
                id_usuario=id_usuario_actual, accion=accion, tabla_afectada=tabla_afectada, detalle=detalle
            )
            nuevo = models.Auditoria(**audit.dict())
            db.add(nuevo)
            db.commit()

            return resultado

        return wrapper

    return decorator
