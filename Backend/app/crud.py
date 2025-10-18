import re
from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Función para encriptar contraseñas nuevas
def encriptar_contrasena(contrasena: str):
    return pwd_context.hash(contrasena)


# Función para verificar contraseñas al iniciar sesión
def verificar_contrasena(contrasena_plana: str, hash_guardado: str):
    return pwd_context.verify(contrasena_plana, hash_guardado)


def crear_usuario(db: Session, usuario: schemas.UsuarioCreate):
    # Validaciones
    validar_nombre_usuario(usuario.nombre)
    validar_email(usuario.email)
    validar_contrasena(usuario.password)

    if db.query(models.Usuario).filter(models.Usuario.nombre == usuario.nombre).first():
        raise HTTPException(
            status_code=400, detail="El nombre de usuario ya está en uso"
        )
    if db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first():
        raise HTTPException(status_code=400, detail="El correo ya está en uso")

    datos_usuario = usuario.dict()
    datos_usuario["password"] = encriptar_contrasena(usuario.password)
    db_usuario = models.Usuario(**datos_usuario)
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario


def cambiar_password(db: Session, id_usuario: int, nueva_password: str):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == id_usuario).first()
    if not usuario:
        raise Exception("Usuario no encontrado")

    # Validar contraseña
    validar_contrasena(nueva_password)

    usuario.password = encriptar_contrasena(nueva_password)
    db.commit()
    db.refresh(usuario)
    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "mensaje": "Contraseña actualizada",
    }


def validar_email(email: str):
    """
    Valida que el email tenga un formato correcto.
    """
    patron_email = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(patron_email, email):
        raise HTTPException(
            status_code=400, detail="El correo electrónico no tiene un formato válido"
        )
    return True


def validar_nombre_usuario(nombre: str):
    """
    Valida que el nombre de usuario:
    - Solo tenga letras, números, guiones bajos
    - Entre 3 y 20 caracteres
    """
    patron_nombre = r"^[a-zA-Z0-9_]{3,20}$"
    if not re.match(patron_nombre, nombre):
        raise HTTPException(
            status_code=400,
            detail="El nombre de usuario solo puede contener letras, números y '_' (3-20 caracteres)",
        )
    return True


def validar_contrasena(password: str):
    """
    Valida que la contraseña cumpla con los requisitos mínimos de seguridad:
    - Al menos 8 caracteres
    - Al menos una letra mayúscula
    - Al menos una letra minúscula
    - Al menos un número
    - Opcional: al menos un carácter especial
    """
    if len(password) < 8:
        raise HTTPException(
            status_code=400, detail="La contraseña debe tener al menos 8 caracteres"
        )
    if not re.search(r"[A-Z]", password):
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe incluir al menos una letra mayúscula",
        )
    if not re.search(r"[a-z]", password):
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe incluir al menos una letra minúscula",
        )
    if not re.search(r"[0-9]", password):
        raise HTTPException(
            status_code=400, detail="La contraseña debe incluir al menos un número"
        )
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe incluir al menos un carácter especial (!@#$...)",
        )
    return True


def actualizar_usuario(
    db: Session,
    id_usuario: int,
    nuevo_nombre: str = None,
    nuevo_email: str = None,
    nueva_password: str = None,
):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if nuevo_nombre:
        validar_nombre_usuario(nuevo_nombre)
        usuario.nombre = nuevo_nombre

    if nuevo_email:
        validar_email(nuevo_email)
        usuario.email = nuevo_email

    if nueva_password:
        validar_contrasena(nueva_password)
        usuario.password = encriptar_contrasena(nueva_password)

    db.commit()
    db.refresh(usuario)
    return usuario


def obtener_usuarios(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Usuario).offset(skip).limit(limit).all()


def actualizar_ultima_sesion(db: Session, id_usuario: int):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == id_usuario).first()
    if usuario:
        usuario.ultima_sesion = datetime.utcnow()
        db.commit()
        db.refresh(usuario)
    return usuario


def cambiar_rol_usuario(db: Session, id_usuario: int, nuevo_id_rol: int):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == id_usuario).first()
    if not usuario:
        raise Exception("Usuario no encontrado")

    usuario.id_rol = nuevo_id_rol
    db.commit()
    db.refresh(usuario)
    return usuario


def desactivar_usuario(db: Session, id_usuario: int):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == id_usuario).first()
    if not usuario:
        raise Exception("Usuario no encontrado")

    usuario.estado = "Inactivo"
    db.commit()
    db.refresh(usuario)
    return usuario


# ---- Roles ----
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
    db_rol = models.Rol(**rol.dict())
    db.add(db_rol)
    db.commit()
    db.refresh(db_rol)
    return db_rol


def obtener_roles(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Rol).offset(skip).limit(limit).all()


# ---- Residentes ----
def crear_residente(db: Session, residente: schemas.ResidenteCreate):
    # Verificar si el usuario ya tiene un residente asignado
    existente = (
        db.query(models.Residente)
        .filter(models.Residente.id_usuario == residente.id_usuario)
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=400,
            detail=f"El usuario con id {residente.id_usuario} ya está asignado a otro residente.",
        )

    # Crear residente normalmente
    nuevo_residente = models.Residente(**residente.dict())
    db.add(nuevo_residente)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="No se pudo crear el residente por conflicto de datos.",
        )
    db.refresh(nuevo_residente)
    return nuevo_residente


def obtener_residentes(db: Session):
    return db.query(models.Residente).all()


def obtener_residente_por_id(db: Session, id_residente: int):
    return (
        db.query(models.Residente).filter(models.Residente.id == id_residente).first()
    )


def actualizar_residente(
    db: Session, id_residente: int, datos_actualizados: schemas.ResidenteUpdate
):
    residente = obtener_residente_por_id(db, id_residente)
    if residente:
        for key, value in datos_actualizados.dict(exclude_unset=True).items():
            setattr(residente, key, value)
        db.commit()
        db.refresh(residente)
    return residente


def eliminar_residente(db: Session, id_residente: int):
    residente = obtener_residente_por_id(db, id_residente)
    if residente:
        db.delete(residente)
        db.commit()
    return residente


def asignar_residente_a_apartamento(
    db: Session, id_residente: int, id_apartamento: int
):
    apt = (
        db.query(models.Apartamento)
        .filter(models.Apartamento.id == id_apartamento)
        .first()
    )
    res = db.query(models.Residente).filter(models.Residente.id == id_residente).first()
    if not apt or not res:
        return None

    if apt.estado == "Ocupado":
        return "Apartamento ocupado"

    # Asignar
    res.id_apartamento = apt.id
    apt.estado = "Ocupado"

    db.commit()
    db.refresh(res)
    db.refresh(apt)
    return res


def desasignar_residente(db: Session, id_residente: int, inactivar: bool = False):
    res = db.query(models.Residente).filter(models.Residente.id == id_residente).first()
    if not res:
        return None

    # Si tiene apartamento asignado, liberarlo
    if res.id_apartamento:
        apt = (
            db.query(models.Apartamento)
            .filter(models.Apartamento.id == res.id_apartamento)
            .first()
        )
        if apt:
            apt.estado = "Disponible"
        res.id_apartamento = None

    # Inactivar al residente si corresponde
    if inactivar:
        res.estado = "Inactivo"

    db.commit()
    db.refresh(res)
    if res.id_apartamento:
        if apt:
            db.refresh(apt)
    return res


# ---- Apartamentos ----
def crear_apartamento(db: Session, apt: schemas.ApartamentoCreate):
    nuevo_apt = models.Apartamento(**apt.dict())
    db.add(nuevo_apt)
    db.commit()
    db.refresh(nuevo_apt)
    return nuevo_apt


def obtener_apartamentos(db: Session):
    return db.query(models.Apartamento).all()


def obtener_apartamento_por_id(db: Session, id_apartamento: int):
    return (
        db.query(models.Apartamento)
        .filter(models.Apartamento.id == id_apartamento)
        .first()
    )


def actualizar_apartamento(
    db: Session, id_apartamento: int, datos: schemas.ApartamentoUpdate
):
    apt = (
        db.query(models.Apartamento)
        .filter(models.Apartamento.id == id_apartamento)
        .first()
    )
    if not apt:
        return None
    for key, value in datos.dict(exclude_unset=True).items():
        setattr(apt, key, value)
    db.commit()
    db.refresh(apt)
    return apt


def eliminar_apartamento(db: Session, id_apartamento: int):
    apt = (
        db.query(models.Apartamento)
        .filter(models.Apartamento.id == id_apartamento)
        .first()
    )
    if not apt:
        return False
    db.delete(apt)
    db.commit()
    return True


# ---- Pagos ----
def crear_pago(db: Session, pago: schemas.PagoCreate):
    nuevo_pago = models.Pago(**pago.dict())
    db.add(nuevo_pago)
    db.commit()
    db.refresh(nuevo_pago)
    return nuevo_pago


def obtener_pagos(db: Session):
    return db.query(models.Pago).all()


def obtener_pago_por_id(db: Session, id_pago: int):
    return db.query(models.Pago).filter(models.Pago.id == id_pago).first()


def actualizar_pago(db: Session, id_pago: int, datos_actualizados: schemas.PagoCreate):
    pago = obtener_pago_por_id(db, id_pago)
    if pago:
        for key, value in datos_actualizados.dict(exclude_unset=True).items():
            setattr(pago, key, value)
        db.commit()
        db.refresh(pago)
    return pago


def eliminar_pago(db: Session, id_pago: int):
    pago = obtener_pago_por_id(db, id_pago)
    if pago:
        db.delete(pago)
        db.commit()
    return pago


## ---- Gastos Fijos ----
def crear_gasto_fijo(db: Session, gasto: schemas.GastoFijoCreate):
    nuevo = models.GastoFijo(**gasto.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_gastos_fijos(db: Session):
    return db.query(models.GastoFijo).all()


def actualizar_gasto_fijo(
    db: Session, id_gasto: int, datos_actualizados: schemas.GastoFijoCreate
):
    gasto = db.query(models.GastoFijo).filter(models.GastoFijo.id == id_gasto).first()
    if gasto:
        for key, value in datos_actualizados.dict(exclude_unset=True).items():
            setattr(gasto, key, value)
        db.commit()
        db.refresh(gasto)
    return gasto


def eliminar_gasto_fijo(db: Session, id_gasto: int):
    gasto = db.query(models.GastoFijo).filter(models.GastoFijo.id == id_gasto).first()
    if gasto:
        db.delete(gasto)
        db.commit()
    return gasto


# ---- Gastos Variables ----
def crear_gasto_variable(db: Session, gasto: schemas.GastoVariableCreate):
    nuevo = models.GastoVariable(**gasto.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_gastos_variables(db: Session):
    return db.query(models.GastoVariable).all()


def actualizar_gasto_variable(
    db: Session, id_gasto: int, datos_actualizados: schemas.GastoVariableCreate
):
    gasto = (
        db.query(models.GastoVariable)
        .filter(models.GastoVariable.id == id_gasto)
        .first()
    )
    if gasto:
        for key, value in datos_actualizados.dict(exclude_unset=True).items():
            setattr(gasto, key, value)
        db.commit()
        db.refresh(gasto)
    return gasto


def eliminar_gasto_variable(db: Session, id_gasto: int):
    gasto = (
        db.query(models.GastoVariable)
        .filter(models.GastoVariable.id == id_gasto)
        .first()
    )
    if gasto:
        db.delete(gasto)
        db.commit()
    return gasto


# ---- Incidencias ----
def crear_incidencia(db: Session, incidencia: schemas.IncidenciaCreate):
    nuevo = models.Incidencia(**incidencia.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_incidencias(db: Session):
    return db.query(models.Incidencia).all()


def obtener_incidencia_por_id(db: Session, id_incidencia: int):
    return (
        db.query(models.Incidencia)
        .filter(models.Incidencia.id == id_incidencia)
        .first()
    )


def actualizar_incidencia(
    db: Session, id_incidencia: int, datos: schemas.IncidenciaUpdate
):
    inc = obtener_incidencia_por_id(db, id_incidencia)
    if not inc:
        return None
    for key, value in datos.dict(exclude_unset=True).items():
        setattr(inc, key, value)
    db.commit()
    db.refresh(inc)
    return inc


def eliminar_incidencia(db: Session, id_incidencia: int):
    inc = obtener_incidencia_por_id(db, id_incidencia)
    if inc:
        db.delete(inc)
        db.commit()
    return inc


# ---- Reservas ----
def crear_reserva(db: Session, reserva: schemas.ReservaCreate):
    nuevo = models.Reserva(**reserva.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_reservas(db: Session):
    return db.query(models.Reserva).all()


def obtener_reserva_por_id(db: Session, id_reserva: int):
    return db.query(models.Reserva).filter(models.Reserva.id == id_reserva).first()


def actualizar_reserva(db: Session, id_reserva: int, datos: schemas.ReservaUpdate):
    res = obtener_reserva_por_id(db, id_reserva)
    if not res:
        return None
    for key, value in datos.dict(exclude_unset=True).items():
        setattr(res, key, value)
    db.commit()
    db.refresh(res)
    return res


def eliminar_reserva(db: Session, id_reserva: int):
    res = obtener_reserva_por_id(db, id_reserva)
    if res:
        db.delete(res)
        db.commit()
    return res


# ---- Notificaciones ----
def crear_notificacion(db: Session, noti: schemas.NotificacionCreate):
    nuevo = models.Notificacion(**noti.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_notificaciones(db: Session):
    return db.query(models.Notificacion).all()


def obtener_notificacion_por_id(db: Session, id_notificacion: int):
    return (
        db.query(models.Notificacion)
        .filter(models.Notificacion.id == id_notificacion)
        .first()
    )


def actualizar_notificacion(
    db: Session, id_notificacion: int, datos: schemas.NotificacionUpdate
):
    noti = obtener_notificacion_por_id(db, id_notificacion)
    if not noti:
        return None
    for key, value in datos.dict(exclude_unset=True).items():
        setattr(noti, key, value)
    db.commit()
    db.refresh(noti)
    return noti


# ---- Auditoría ----
def crear_auditoria(db: Session, audit: schemas.AuditoriaCreate):
    nuevo = models.Auditoria(**audit.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_auditorias(db: Session):
    return db.query(models.Auditoria).all()


# ---- Reportes Financieros ----
def crear_reporte(db: Session, reporte: schemas.ReporteFinancieroCreate):
    nuevo = models.ReporteFinanciero(**reporte.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_reportes(db: Session):
    return db.query(models.ReporteFinanciero).all()


def obtener_reporte_por_id(db: Session, id_reporte: int):
    return (
        db.query(models.ReporteFinanciero)
        .filter(models.ReporteFinanciero.id == id_reporte)
        .first()
    )


def actualizar_reporte(
    db: Session, id_reporte: int, datos: schemas.ReporteFinancieroUpdate
):
    rep = obtener_reporte_por_id(db, id_reporte)
    if not rep:
        return None
    for key, value in datos.dict(exclude_unset=True).items():
        setattr(rep, key, value)
    db.commit()
    db.refresh(rep)
    return rep


def eliminar_reporte(db: Session, id_reporte: int):
    rep = obtener_reporte_por_id(db, id_reporte)
    if rep:
        db.delete(rep)
        db.commit()
    return rep
