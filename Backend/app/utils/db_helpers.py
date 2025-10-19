# > Función para reducir líneas de código al hacer commit y refresh en la DB <
from sqlalchemy.orm import Session
from fastapi import HTTPException
from .. import models


# > Función para reducir líneas de código al hacer commit y refresh en la DB <
def guardar_y_refrescar(db: Session, obj):
    db.commit()
    db.refresh(obj)
    return obj


# > Obtener el usuario por ID <
def obtener_usuario_por_id(db: Session, id_usuario: int):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario
