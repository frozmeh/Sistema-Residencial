from datetime import datetime
from sqlalchemy.orm import Session
from ..utils.db_helpers import guardar_y_refrescar
from . import obtener_usuario_por_id


# ===============================
# ---- Autenticación / Login ----
# ===============================


def actualizar_ultima_sesion(db: Session, id_usuario: int):
    usuario = obtener_usuario_por_id(db, id_usuario)
    usuario.ultima_sesion = datetime.utcnow()
    guardar_y_refrescar(db, usuario)
    return usuario
