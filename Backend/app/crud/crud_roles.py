from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..utils.db_helpers import guardar_y_refrescar


# ===============
# ---- Roles ----
# ===============


def inicializar_roles(db: Session):
    if db.query(models.Rol).count() == 0:
        admin_permisos = {
            "Usuario": ["crear", "leer", "actualizar", "eliminar"],
            "Residente": ["crear", "leer", "actualizar", "eliminar"],
            "Apartamento": ["crear", "leer", "actualizar", "eliminar"],
            "Pago": ["crear", "leer", "actualizar", "eliminar"],
            "GastoFijo": ["crear", "leer", "actualizar", "eliminar"],
            "GastoVariable": ["crear", "leer", "actualizar", "eliminar"],
            "Incidencia": ["leer", "actualizar", "eliminar"],
            "Reserva": ["leer", "actualizar", "eliminar"],
            "Notificacion": ["crear", "leer", "actualizar"],
            "ReporteFinanciero": ["crear", "leer", "actualizar", "eliminar"],
            "Auditoria": ["crear", "leer"],
        }

        residente_permisos = {
            "Usuario": ["leer", "actualizar"],
            "Residente": ["leer", "actualizar"],
            "Apartamento": ["leer"],
            "Pago": ["crear", "leer"],
            "GastoFijo": ["leer"],
            "GastoVariable": ["leer"],
            "Incidencia": ["crear", "leer", "actualizar"],
            "Reserva": ["crear", "leer", "actualizar", "eliminar"],
            "Notificacion": ["leer", "actualizar"],
            "ReporteFinanciero": ["leer"],
            "Auditoria": ["leer"],
        }

        db.add_all(
            [
                models.Rol(
                    nombre="Administrador",
                    permisos=admin_permisos,
                    descripcion="Acceso completo",
                ),
                models.Rol(
                    nombre="Residente",
                    permisos=residente_permisos,
                    descripcion="Acceso limitado",
                ),
            ]
        )
        db.commit()


def crear_rol(db: Session, rol: schemas.RolCreate):
    raise HTTPException(status_code=403, detail="No se pueden crear roles manualmente")
    """
    db_rol = models.Rol(**rol.dict())
    db.add(db_rol)
    guardar_y_refrescar(db, db_rol)
    return db_rol """


def obtener_roles(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Rol).offset(skip).limit(limit).all()
