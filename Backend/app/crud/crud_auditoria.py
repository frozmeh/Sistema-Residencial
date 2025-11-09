from sqlalchemy.orm import Session
from . import models, schemas
from datetime import date, datetime
import json


# ===================
# ---- Auditoria ----
# ===================


def registrar_auditoria(
    db: Session,
    usuario_id: int,
    usuario_nombre: str,
    accion: str,
    tabla: str,
    objeto_previo: dict = None,
    objeto_nuevo: dict = None,
    request: any = None,
):
    # Calcular cambios
    cambios = {}
    if objeto_previo and objeto_nuevo:
        cambios = {
            k: {"antes": objeto_previo[k], "despues": objeto_nuevo[k]}
            for k in objeto_previo
            if objeto_previo[k] != objeto_nuevo[k]
        }

    # Datos extra
    ip = request.client.host if request else None
    endpoint = f"{request.method} {request.url.path}" if request else None

    # Crear detalle
    detalle = {"cambios": cambios if cambios else None, "ip": ip, "endpoint": endpoint}

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


def obtener_auditorias(
    db: Session, id_usuario: int = None, tabla: str = None, fecha_inicio: date = None, fecha_fin: date = None
):
    query = db.query(models.Auditoria)
    if id_usuario:
        query = query.filter(models.Auditoria.id_usuario == id_usuario)
    if tabla:
        query = query.filter(models.Auditoria.tabla_afectada == tabla)
    if fecha_inicio:
        query = query.filter(models.Auditoria.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.filter(models.Auditoria.fecha <= fecha_fin)

    auditorias = query.all()
    resultado = []
    for a in auditorias:
        # Asegurarse de que 'detalle' sea un dict (por si SQLAlchemy lo devuelve como string)
        try:
            detalle_dict = a.detalle if isinstance(a.detalle, dict) else json.loads(a.detalle)
        except Exception:
            detalle_dict = {}

        resultado.append(
            schemas.AuditoriaOut(
                id=a.id,
                id_usuario=a.id_usuario,
                nombre_usuario=a.nombre_usuario,
                accion=a.accion,
                tabla_afectada=a.tabla_afectada,
                fecha=a.fecha,
                detalle=detalle_dict,  # ✅ Pasamos dict directamente
            )
        )
    return resultado
