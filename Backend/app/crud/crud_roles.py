from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..utils.db_helpers import guardar_y_refrescar


# ===============
# ---- Roles ----
# ===============


def inicializar_roles(db: Session):
    if db.query(models.Rol).count() == 0:
        db.add_all(
            [
                models.Rol(
                    nombre="Administrador",
                    descripcion="Acceso completo al sistema",
                ),
                models.Rol(
                    nombre="Residente",
                    descripcion="Acceso limitado a funcionalidades de residente",
                ),
            ]
        )
        db.commit()


def obtener_roles(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Rol).offset(skip).limit(limit).all()
