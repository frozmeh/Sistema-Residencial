from sqlalchemy.orm import Session
from . import models, schemas
from datetime import date

# Crear usuario

def crear_usuario(db: Session, usuario: schemas.UsuarioCreate, actor_id: int | None = None):
    db_usuario = models.Usuario(
        nombre_usuario=usuario.nombre_usuario,
        contraseña=usuario.contraseña,
        correo=usuario.correo,
        id_rol=usuario.id_rol,
        estado=usuario.estado,
        fecha_creacion=usuario.fecha_creacion or date.today()
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)

    # Registrar auditoría (si se pasó actor_id)
    if actor_id:
        crear_log(db, schemas.AuditoriaCreate(
            id_usuario=actor_id,
            accion="crear",
            tabla_afectada="usuarios",
            fecha=date.today(),
            detalle=f"Usuario creado id={db_usuario.id_usuario}"
        ))

    return db_usuario

# Obtener todos los usuarios
def obtener_usuarios(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Usuario).offset(skip).limit(limit).all()

# Obtener usuario por id
def obtener_usuario(db: Session, id_usuario: int):
    return db.query(models.Usuario).filter(models.Usuario.id_usuario == id_usuario).first()

# Actualizar usuario
def actualizar_usuario(db: Session, id_usuario: int, usuario: schemas.UsuarioUpdate):
    db_usuario = db.query(models.Usuario).filter(models.Usuario.id_usuario == id_usuario).first()
    if not db_usuario:
        return None
    for key, value in usuario.dict(exclude_unset=True).items():
        setattr(db_usuario, key, value)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

# Eliminar usuario
def eliminar_usuario(db: Session, id_usuario: int):
    db_usuario = db.query(models.Usuario).filter(models.Usuario.id_usuario == id_usuario).first()
    if not db_usuario:
        return None
    db.delete(db_usuario)
    db.commit()
    return db_usuario

# Crear rol
def crear_rol(db: Session, rol: schemas.RolCreate):
    db_rol = models.Rol(
        nombre_rol=rol.nombre_rol,
        permisos=rol.permisos,
        descripcion=rol.descripcion
    )
    db.add(db_rol)
    db.commit()
    db.refresh(db_rol)
    return db_rol

# Obtener todos los roles
def obtener_roles(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Rol).offset(skip).limit(limit).all()

# Obtener rol por id
def obtener_rol(db: Session, id_rol: int):
    return db.query(models.Rol).filter(models.Rol.id_rol == id_rol).first()

# Actualizar rol
def actualizar_rol(db: Session, id_rol: int, rol: schemas.RolUpdate):
    db_rol = db.query(models.Rol).filter(models.Rol.id_rol == id_rol).first()
    if not db_rol:
        return None
    for key, value in rol.dict(exclude_unset=True).items():
        setattr(db_rol, key, value)
    db.commit()
    db.refresh(db_rol)
    return db_rol

# Eliminar rol
def eliminar_rol(db: Session, id_rol: int):
    db_rol = db.query(models.Rol).filter(models.Rol.id_rol == id_rol).first()
    if not db_rol:
        return None
    db.delete(db_rol)
    db.commit()
    return db_rol

# Crear residente
def crear_residente(db: Session, residente: schemas.ResidenteCreate):
    db_residente = models.Residente(
        tipo_residente=residente.tipo_residente,
        nombre=residente.nombre,
        cedula=residente.cedula,
        telefono=residente.telefono,
        correo=residente.correo,
        id_apartamento=residente.id_apartamento,
        id_usuario=residente.id_usuario,
        fecha_registro=residente.fecha_registro or date.today(),
        estado=residente.estado
    )
    db.add(db_residente)
    db.commit()
    db.refresh(db_residente)
    return db_residente

# Obtener todos los residentes
def obtener_residentes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Residente).offset(skip).limit(limit).all()

# Obtener residente por id
def obtener_residente(db: Session, id_residente: int):
    return db.query(models.Residente).filter(models.Residente.id_residente == id_residente).first()

# Actualizar residente
def actualizar_residente(db: Session, id_residente: int, residente: schemas.ResidenteUpdate):
    db_residente = db.query(models.Residente).filter(models.Residente.id_residente == id_residente).first()
    if not db_residente:
        return None
    for key, value in residente.dict(exclude_unset=True).items():
        setattr(db_residente, key, value)
    db.commit()
    db.refresh(db_residente)
    return db_residente

# Eliminar residente
def eliminar_residente(db: Session, id_residente: int):
    db_residente = db.query(models.Residente).filter(models.Residente.id_residente == id_residente).first()
    if not db_residente:
        return None
    db.delete(db_residente)
    db.commit()
    return db_residente

# Crear apartamento
def crear_apartamento(db: Session, apto: schemas.ApartamentoCreate):
    db_apto = models.Apartamento(
        numero=apto.numero,
        torre=apto.torre,
        piso=apto.piso,
        tipo_apartamento=apto.tipo_apartamento,
        porcentaje_aporte=apto.porcentaje_aporte,
        estado=apto.estado
    )
    db.add(db_apto)
    db.commit()
    db.refresh(db_apto)
    return db_apto

# Obtener todos los apartamentos
def obtener_apartamentos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Apartamento).offset(skip).limit(limit).all()

# Obtener apartamento por id
def obtener_apartamento(db: Session, id_apartamento: int):
    return db.query(models.Apartamento).filter(models.Apartamento.id_apartamento == id_apartamento).first()

# Actualizar apartamento
def actualizar_apartamento(db: Session, id_apartamento: int, apto: schemas.ApartamentoUpdate):
    db_apto = db.query(models.Apartamento).filter(models.Apartamento.id_apartamento == id_apartamento).first()
    if not db_apto:
        return None
    for key, value in apto.dict(exclude_unset=True).items():
        setattr(db_apto, key, value)
    db.commit()
    db.refresh(db_apto)
    return db_apto

# Eliminar apartamento
def eliminar_apartamento(db: Session, id_apartamento: int):
    db_apto = db.query(models.Apartamento).filter(models.Apartamento.id_apartamento == id_apartamento).first()
    if not db_apto:
        return None
    db.delete(db_apto)
    db.commit()
    return db_apto


# Crear pago
def crear_pago(db: Session, pago: schemas.PagoCreate):
    db_pago = models.Pago(
        id_residente=pago.id_residente,
        id_apartamento=pago.id_apartamento,
        monto=pago.monto,
        moneda=pago.moneda,
        tipo_cambio_bcv=pago.tipo_cambio_bcv,
        fecha_pago=pago.fecha_pago,
        concepto=pago.concepto,
        metodo=pago.metodo,
        comprobante=pago.comprobante,
        estado=pago.estado,
        verificado=pago.verificado
    )
    db.add(db_pago)
    db.commit()
    db.refresh(db_pago)
    return db_pago

# Obtener todos los pagos
def obtener_pagos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Pago).offset(skip).limit(limit).all()

# Obtener pago por id
def obtener_pago(db: Session, id_pago: int):
    return db.query(models.Pago).filter(models.Pago.id_pago == id_pago).first()

# Actualizar pago
def actualizar_pago(db: Session, id_pago: int, pago: schemas.PagoUpdate):
    db_pago = db.query(models.Pago).filter(models.Pago.id_pago == id_pago).first()
    if not db_pago:
        return None
    for key, value in pago.dict(exclude_unset=True).items():
        setattr(db_pago, key, value)
    db.commit()
    db.refresh(db_pago)
    return db_pago

# Eliminar pago
def eliminar_pago(db: Session, id_pago: int):
    db_pago = db.query(models.Pago).filter(models.Pago.id_pago == id_pago).first()
    if not db_pago:
        return None
    db.delete(db_pago)
    db.commit()
    return db_pago

# Gasto Fijo
def crear_gasto_fijo(db: Session, gasto: schemas.GastoFijoCreate):
    db_gasto = models.GastoFijo(**gasto.dict())
    db.add(db_gasto)
    db.commit()
    db.refresh(db_gasto)
    return db_gasto

def obtener_gastos_fijos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.GastoFijo).offset(skip).limit(limit).all()

def actualizar_gasto_fijo(db: Session, id_gasto_fijo: int, gasto: schemas.GastoFijoUpdate):
    db_gasto = db.query(models.GastoFijo).filter(models.GastoFijo.id_gasto_fijo == id_gasto_fijo).first()
    if not db_gasto:
        return None
    for key, value in gasto.dict(exclude_unset=True).items():
        setattr(db_gasto, key, value)
    db.commit()
    db.refresh(db_gasto)
    return db_gasto

def eliminar_gasto_fijo(db: Session, id_gasto_fijo: int):
    db_gasto = db.query(models.GastoFijo).filter(models.GastoFijo.id_gasto_fijo == id_gasto_fijo).first()
    if not db_gasto:
        return None
    db.delete(db_gasto)
    db.commit()
    return db_gasto

# Gasto Variable
def crear_gasto_variable(db: Session, gasto: schemas.GastoVariableCreate):
    db_gasto = models.GastoVariable(**gasto.dict())
    db.add(db_gasto)
    db.commit()
    db.refresh(db_gasto)
    return db_gasto

def obtener_gastos_variables(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.GastoVariable).offset(skip).limit(limit).all()

def actualizar_gasto_variable(db: Session, id_gasto_variable: int, gasto: schemas.GastoVariableUpdate):
    db_gasto = db.query(models.GastoVariable).filter(models.GastoVariable.id_gasto_variable == id_gasto_variable).first()
    if not db_gasto:
        return None
    for key, value in gasto.dict(exclude_unset=True).items():
        setattr(db_gasto, key, value)
    db.commit()
    db.refresh(db_gasto)
    return db_gasto

def eliminar_gasto_variable(db: Session, id_gasto_variable: int):
    db_gasto = db.query(models.GastoVariable).filter(models.GastoVariable.id_gasto_variable == id_gasto_variable).first()
    if not db_gasto:
        return None
    db.delete(db_gasto)
    db.commit()
    return db_gasto


# Crear reporte financiero
def crear_reporte(db: Session, reporte: schemas.ReporteFinancieroCreate):
    db_reporte = models.ReporteFinanciero(**reporte.dict())
    db.add(db_reporte)
    db.commit()
    db.refresh(db_reporte)
    return db_reporte

# Obtener todos los reportes
def obtener_reportes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ReporteFinanciero).offset(skip).limit(limit).all()

# Obtener reporte por id
def obtener_reporte(db: Session, id_reporte: int):
    return db.query(models.ReporteFinanciero).filter(models.ReporteFinanciero.id_reporte == id_reporte).first()

# Eliminar reporte
def eliminar_reporte(db: Session, id_reporte: int):
    db_reporte = db.query(models.ReporteFinanciero).filter(models.ReporteFinanciero.id_reporte == id_reporte).first()
    if not db_reporte:
        return None
    db.delete(db_reporte)
    db.commit()
    return db_reporte

from sqlalchemy import func

def generar_reporte_mensual(db: Session, mes: int, año: int, usuario: str):
    # Convertimos a string el periodo
    periodo = f"{año}-{mes:02d}"

    # Sumar gastos fijos del mes
    total_gastos_fijos = db.query(func.coalesce(func.sum(models.GastoFijo.monto), 0)) \
        .filter(func.extract('month', models.GastoFijo.fecha_registro) == mes) \
        .filter(func.extract('year', models.GastoFijo.fecha_registro) == año).scalar()

    # Sumar gastos variables del mes
    total_gastos_variables = db.query(func.coalesce(func.sum(models.GastoVariable.monto), 0)) \
        .filter(func.extract('month', models.GastoVariable.fecha_registro) == mes) \
        .filter(func.extract('year', models.GastoVariable.fecha_registro) == año).scalar()

    # Total general
    total_general = total_gastos_fijos + total_gastos_variables

    # Crear el reporte
    db_reporte = models.ReporteFinanciero(
        periodo=periodo,
        total_gastos_fijos=total_gastos_fijos,
        total_gastos_variables=total_gastos_variables,
        total_general=total_general,
        generado_por=usuario,
        fecha_generacion=date.today()
    )

    db.add(db_reporte)
    db.commit()
    db.refresh(db_reporte)
    return db_reporte

def crear_incidencia(db: Session, incidencia: schemas.IncidenciaCreate):
    db_incidencia = models.Incidencia(**incidencia.dict())
    db.add(db_incidencia)
    db.commit()
    db.refresh(db_incidencia)
    return db_incidencia

def obtener_incidencias(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Incidencia).offset(skip).limit(limit).all()

def crear_reserva(db: Session, reserva: schemas.ReservaCreate):
    db_reserva = models.Reserva(**reserva.dict())
    db.add(db_reserva)
    db.commit()
    db.refresh(db_reserva)
    return db_reserva

def obtener_reservas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Reserva).offset(skip).limit(limit).all()

def crear_notificacion(db: Session, notificacion: schemas.NotificacionCreate):
    db_notificacion = models.Notificacion(**notificacion.dict())
    db.add(db_notificacion)
    db.commit()
    db.refresh(db_notificacion)
    return db_notificacion

def obtener_notificaciones(db: Session, id_usuario: int, skip: int = 0, limit: int = 100):
    return db.query(models.Notificacion).filter(models.Notificacion.id_usuario == id_usuario).offset(skip).limit(limit).all()

def marcar_como_leido(db: Session, id_notificacion: int):
    db_notificacion = db.query(models.Notificacion).filter(models.Notificacion.id_notificacion == id_notificacion).first()
    if db_notificacion:
        db_notificacion.leido = True
        db.commit()
        db.refresh(db_notificacion)
    return db_notificacion

def crear_log(db: Session, log: schemas.AuditoriaCreate):
    db_log = models.Auditoria(**log.dict())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def obtener_logs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Auditoria).offset(skip).limit(limit).all()
