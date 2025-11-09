from sqlalchemy.orm import Session
from . import models, schemas
from fastapi import HTTPException
from datetime import datetime, date, time
from ..utils.db_helpers import guardar_y_refrescar


# ==================
# ---- Reservas ----
# ==================


# @auditar_completo("reservas")
def validar_disponibilidad(
    db: Session, area: str, fecha: date, hora_inicio: time, hora_fin: time, id_excluir: int = None
):
    query = db.query(models.Reserva).filter(
        models.Reserva.area == area, models.Reserva.fecha_reserva == fecha, models.Reserva.estado == "Activa"
    )
    if id_excluir:
        query = query.filter(models.Reserva.id != id_excluir)

    for reserva in query.all():
        # Verificar si hay solapamiento
        if not (hora_fin <= reserva.hora_inicio or hora_inicio >= reserva.hora_fin):
            raise HTTPException(
                status_code=400, detail=f"El horario de {hora_inicio} a {hora_fin} ya está ocupado en {area}"
            )


# @auditar_completo("reservas")
def crear_reserva(db: Session, reserva: schemas.ReservaCreate):
    # Validar que la fecha de reserva no sea pasada
    if reserva.fecha_reserva < date.today():
        raise HTTPException(status_code=400, detail="La fecha de reserva no puede ser pasada")

    # Validar que la hora de fin sea mayor que la hora de inicio
    if reserva.hora_fin <= reserva.hora_inicio:
        raise HTTPException(status_code=400, detail="La hora de fin debe ser posterior a la hora de inicio")

    validar_disponibilidad(db, reserva.area, reserva.fecha_reserva, reserva.hora_inicio, reserva.hora_fin)

    nuevo = models.Reserva(**reserva.dict())
    db.add(nuevo)
    return guardar_y_refrescar(db, nuevo)


# @auditar_completo("reservas")
def obtener_reservas(db: Session):
    return db.query(models.Reserva).all()


# @auditar_completo("reservas")
def obtener_reserva_por_id(db: Session, id_reserva: int):
    res = db.query(models.Reserva).filter(models.Reserva.id == id_reserva).first()
    if not res:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return res


# @auditar_completo("reservas")
def actualizar_reserva(db: Session, id_reserva: int, datos: schemas.ReservaUpdate):
    res = obtener_reserva_por_id(db, id_reserva)

    # Actualizar atributos
    for key, value in datos.dict(exclude_unset=True).items():
        setattr(res, key, value)

    # Validar hora_fin > hora_inicio si se actualizaron
    if res.hora_inicio and res.hora_fin and res.hora_fin <= res.hora_inicio:
        raise HTTPException(status_code=400, detail="La hora de fin debe ser posterior a la hora de inicio")

    # Validar fecha de reserva no pasada
    if res.fecha_reserva and res.fecha_reserva < date.today():
        raise HTTPException(status_code=400, detail="La fecha de reserva no puede ser pasada")

    validar_disponibilidad(db, res.area, res.fecha_reserva, res.hora_inicio, res.hora_fin)

    return guardar_y_refrescar(db, res)


# @auditar_completo("reservas")
def eliminar_reserva(db: Session, id_reserva: int):
    res = obtener_reserva_por_id(db, id_reserva)
    db.delete(res)
    db.commit()
    return res
