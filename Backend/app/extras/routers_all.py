from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/apartamentos", tags=["Apartamentos"])


@router.post("/", response_model=schemas.ApartamentoOut)
def crear_apartamento(apt: schemas.ApartamentoCreate, db: Session = Depends(get_db)):
    return crud.crear_apartamento(db, apt)


@router.get("/", response_model=list[schemas.ApartamentoOut])
def obtener_apartamentos(db: Session = Depends(get_db)):
    return crud.obtener_apartamentos(db)


@router.get("/{id_apartamento}", response_model=schemas.ApartamentoOut)
def obtener_apartamento(id_apartamento: int, db: Session = Depends(get_db)):
    apt = crud.obtener_apartamento_por_id(db, id_apartamento)
    if not apt:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
    return apt


@router.put("/{id_apartamento}", response_model=schemas.ApartamentoOut)
def actualizar_apartamento(id_apartamento: int, datos: schemas.ApartamentoUpdate, db: Session = Depends(get_db)):
    apt_actualizado = crud.actualizar_apartamento(db, id_apartamento, datos)
    if not apt_actualizado:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
    return apt_actualizado


@router.delete("/{id_apartamento}")
def eliminar_apartamento(id_apartamento: int, db: Session = Depends(get_db)):
    eliminado = crud.eliminar_apartamento(db, id_apartamento)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
    return {"mensaje": "Apartamento eliminado correctamente"}


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/auditorias", tags=["Auditorias"])


@router.post("/", response_model=schemas.AuditoriaOut)
def crear_auditoria(audit: schemas.AuditoriaCreate, db: Session = Depends(get_db)):
    try:
        return crud.crear_auditoria(db, audit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo crear la auditoría: {str(e)}")


@router.get("/", response_model=list[schemas.AuditoriaOut])
def listar_auditorias(db: Session = Depends(get_db)):
    return crud.obtener_auditorias(db)


@router.get("/{id_auditoria}", response_model=schemas.AuditoriaOut)
def obtener_auditoria(id_auditoria: int, db: Session = Depends(get_db)):
    a = crud.obtener_auditoria_por_id(db, id_auditoria)
    if not a:
        raise HTTPException(status_code=404, detail="Auditoría no encontrada")
    return a


from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import func
from ..database import get_db
from ..models import Usuario  # Ajusta el import según tu estructura
from passlib.context import CryptContext
from jose import jwt
from ..utils.seguridad import verificar_contrasena, crear_token


SECRET_KEY = "Santiago.02"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

router = APIRouter(prefix="/auth", tags=["Auth"])


class Credenciales(BaseModel):
    nombre_usuario: str
    contrasena: str


@router.post("/login")
def login(credenciales: Credenciales, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(func.lower(Usuario.nombre) == credenciales.nombre_usuario.lower()).first()
    if not usuario:
        raise HTTPException(status_code=400, detail="Usuario no encontrado")

    if not verificar_contrasena(credenciales.contrasena, usuario.password):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    token = crear_token({"sub": str(usuario.id), "rol": usuario.id_rol})

    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": {"id": usuario.id, "nombre": usuario.nombre, "rol": usuario.id_rol, "correo": usuario.email},
    }


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/gastos", tags=["Gastos"])


# =======================
# ---- Gastos Fijos -----
# =======================


@router.post("/fijos", response_model=schemas.GastoFijoOut)
def crear_gasto_fijo(gasto: schemas.GastoFijoCreate, db: Session = Depends(get_db)):
    return crud.crear_gasto_fijo(db, gasto)


@router.get("/fijos", response_model=list[schemas.GastoFijoOut])
def listar_gastos_fijos(responsable: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.obtener_gastos_fijos(db, responsable)


@router.put("/fijos/{id_gasto}", response_model=schemas.GastoFijoOut)
def actualizar_gasto_fijo(id_gasto: int, datos: schemas.GastoFijoCreate, db: Session = Depends(get_db)):
    return crud.actualizar_gasto_fijo(db, id_gasto, datos)


@router.delete("/fijos/{id_gasto}")
def eliminar_gasto_fijo(id_gasto: int, db: Session = Depends(get_db)):
    crud.eliminar_gasto_fijo(db, id_gasto)


# ==========================
# ---- Gastos Variables ----
# ==========================


@router.post("/variables", response_model=schemas.GastoVariableOut)
def crear_gasto_variable(gasto: schemas.GastoVariableCreate, db: Session = Depends(get_db)):
    return crud.crear_gasto_variable(db, gasto)


@router.get("/variables", response_model=list[schemas.GastoVariableOut])
def listar_gastos_variables(responsable: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.obtener_gastos_variables(db, responsable)


@router.put("/variables/{id_gasto}", response_model=schemas.GastoVariableOut)
def actualizar_gasto_variable(id_gasto: int, datos: schemas.GastoVariableCreate, db: Session = Depends(get_db)):
    return crud.actualizar_gasto_variable(db, id_gasto, datos)


@router.delete("/variables/{id_gasto}")
def eliminar_gasto_variable(id_gasto: int, db: Session = Depends(get_db)):
    crud.eliminar_gasto_variable(db, id_gasto)


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/incidencias", tags=["Incidencias"])


# =====================
# ---- Incidencias ----
# =====================


@router.post(
    "/",
    response_model=schemas.IncidenciaOut,
    summary="Crear una nueva incidencia",
    description="Permite a un residente crear una incidencia de tipo Mantenimiento, Queja o Sugerencia.",
)
def crear_incidencia(
    incidencia: schemas.IncidenciaCreate,
    db: Session = Depends(get_db),
):
    return crud.crear_incidencia(db, incidencia)


def listar_incidencias(
    estado: Optional[str] = Query(None, description="Filtrar por estado (Abierta, En progreso, Cerrada)"),
    prioridad: Optional[str] = Query(None, description="Filtrar por prioridad (Alta, Media, Baja)"),
    fecha_inicio: Optional[date] = Query(None, description="Filtrar incidencias desde esta fecha"),
    fecha_fin: Optional[date] = Query(None, description="Filtrar incidencias hasta esta fecha"),
    db: Session = Depends(get_db),
):
    return crud.obtener_incidencias(db, estado, prioridad, fecha_inicio, fecha_fin)


@router.get(
    "/{id_incidencia}",
    response_model=schemas.IncidenciaOut,
    summary="Obtener una incidencia por ID",
)
def obtener_incidencia(id_incidencia: int, db: Session = Depends(get_db)):
    return crud.obtener_incidencia_por_id(db, id_incidencia)


@router.put(
    "/{id_incidencia}",
    response_model=schemas.IncidenciaOut,
    summary="Actualizar una incidencia existente",
    description="Permite modificar el estado, descripción o prioridad de una incidencia.",
)
@router.put(
    "/{id_incidencia}",
    response_model=schemas.IncidenciaOut,
    summary="Actualizar una incidencia existente",
    description="Permite modificar el estado, descripción o prioridad de una incidencia.",
)
def actualizar_incidencia(
    id_incidencia: int,
    datos: schemas.IncidenciaUpdate,
    db: Session = Depends(get_db),
):
    return crud.actualizar_incidencia(db, id_incidencia, datos)


@router.delete(
    "/{id_incidencia}",
    summary="Eliminar una incidencia por ID",
    description="Elimina una incidencia solo si está en estado 'Cerrada'.",
)
def eliminar_incidencia(id_incidencia: int, db: Session = Depends(get_db)):
    crud.eliminar_incidencia(db, id_incidencia)
    return {"mensaje": "Incidencia eliminada correctamente"}


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


# Crear notificación
@router.post("/", response_model=schemas.NotificacionOut)
def crear_notificacion(noti: schemas.NotificacionCreate, db: Session = Depends(get_db)):
    return crud.crear_notificacion(db, noti)


# Listar notificaciones con filtros opcionales
@router.get("/", response_model=list[schemas.NotificacionOut])
def listar_notificaciones(
    id_usuario: int | None = Query(None, description="Filtrar por ID de usuario"),
    tipo: str | None = Query(None, description="Filtrar por tipo de notificación"),
    leido: bool | None = Query(None, description="Filtrar por estado de lectura"),
    db: Session = Depends(get_db),
):
    return crud.obtener_notificaciones(db, id_usuario=id_usuario, tipo=tipo, leido=leido)


# Obtener notificación por ID
@router.get("/{id_notificacion}", response_model=schemas.NotificacionOut)
def obtener_notificacion(id_notificacion: int, db: Session = Depends(get_db)):
    n = crud.obtener_notificacion_por_id(db, id_notificacion)
    if not n:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return n


# Actualizar notificación
@router.put("/{id_notificacion}", response_model=schemas.NotificacionOut)
def actualizar_notificacion(id_notificacion: int, datos: schemas.NotificacionUpdate, db: Session = Depends(get_db)):
    return crud.actualizar_notificacion(db, id_notificacion, datos)


# Eliminar notificación
@router.delete("/{id_notificacion}")
def eliminar_notificacion(id_notificacion: int, db: Session = Depends(get_db)):
    return crud.eliminar_notificacion(db, id_notificacion)


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db


router = APIRouter(prefix="/pagos", tags=["Pagos"])


@router.post("/", response_model=schemas.PagoOut)
def crear_pago(pago: schemas.PagoCreate, db: Session = Depends(get_db)):
    return crud.crear_pago(db, pago)


@router.get("/", response_model=list[schemas.PagoOut])
def listar_pagos(db: Session = Depends(get_db)):
    return crud.obtener_pagos(db)


@router.get("/{id_pago}", response_model=schemas.PagoOut)
def obtener_pago(id_pago: int, db: Session = Depends(get_db)):
    return crud.obtener_pago_por_id(db, id_pago)


@router.put("/{id_pago}", response_model=schemas.PagoOut)
def actualizar_pago(id_pago: int, datos_actualizados: schemas.PagoUpdate, db: Session = Depends(get_db)):
    return crud.actualizar_pago(db, id_pago, datos_actualizados)


@router.delete("/{id_pago}")
def eliminar_pago(id_pago: int, db: Session = Depends(get_db)):
    return crud.eliminar_pago(db, id_pago)


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db
from ..utils.seguridad import get_usuario_actual

router = APIRouter(prefix="/reportes", tags=["Reportes Financieros"])


@router.post("/", response_model=schemas.ReporteFinancieroOut, status_code=status.HTTP_201_CREATED)
def crear_reporte(
    reporte: schemas.ReporteFinancieroCreate,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(get_usuario_actual),
):
    return crud.crear_reporte(db=db, reporte=reporte, id_usuario_actual=usuario_actual["id"])


@router.get("/", response_model=list[schemas.ReporteFinancieroOut])
def listar_reportes(db: Session = Depends(get_db)):
    return crud.obtener_reportes(db)


@router.get("/{id_reporte}", response_model=schemas.ReporteFinancieroOut)
def obtener_reporte(id_reporte: int, db: Session = Depends(get_db)):
    r = crud.obtener_reporte_por_id(db, id_reporte)
    if not r:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return r


@router.put("/{id_reporte}", response_model=schemas.ReporteFinancieroOut)
def actualizar_reporte(
    id_reporte: int,
    datos: schemas.ReporteFinancieroUpdate,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(get_usuario_actual),
):
    r = crud.actualizar_reporte(db=db, id_reporte=id_reporte, datos=datos, id_usuario_actual=usuario_actual["id"])
    if not r:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return r


@router.delete("/{id_reporte}", status_code=status.HTTP_200_OK)
def eliminar_reporte(id_reporte: int, db: Session = Depends(get_db)):
    eliminado = crud.eliminar_reporte(db, id_reporte)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return {"mensaje": "Reporte eliminado correctamente"}


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/reservas", tags=["Reservas"])


@router.post("/", response_model=schemas.ReservaOut)
def crear_reserva(reserva: schemas.ReservaCreate, db: Session = Depends(get_db)):
    return crud.crear_reserva(db, reserva)


@router.get("/", response_model=list[schemas.ReservaOut])
def listar_reservas(db: Session = Depends(get_db)):
    return crud.obtener_reservas(db)


@router.get("/{id_reserva}", response_model=schemas.ReservaOut)
def obtener_reserva(id_reserva: int, db: Session = Depends(get_db)):
    res = crud.obtener_reserva_por_id(db, id_reserva)
    if not res:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return res


@router.put("/{id_reserva}", response_model=schemas.ReservaOut)
def actualizar_reserva(id_reserva: int, datos: schemas.ReservaUpdate, db: Session = Depends(get_db)):
    res = crud.actualizar_reserva(db, id_reserva, datos)
    if not res:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return res


@router.delete("/{id_reserva}")
def eliminar_reserva(id_reserva: int, db: Session = Depends(get_db)):
    eliminado = crud.eliminar_reserva(db, id_reserva)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return {"mensaje": "Reserva eliminada correctamente"}


from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from .. import schemas, crud
from ..database import get_db

router = APIRouter(prefix="/residentes", tags=["Residentes"])


@router.post("/", response_model=schemas.ResidenteOut)
def crear_residente(residente: schemas.ResidenteCreate, db: Session = Depends(get_db)):
    nuevo_residente = crud.crear_residente(db, residente)
    return {"mensaje": "Residente creado correctamente", "residente": nuevo_residente}


# > Obtener todos los residentes <
@router.get("/", response_model=list[schemas.ResidenteOut])
def obtener_residentes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    residentes = crud.obtener_residentes(db)[skip : skip + limit]
    return residentes


# > Obtener un residente por su ID <
@router.get("/{id_residente}", response_model=schemas.ResidenteOut)
def obtener_residente(id_residente: int, db: Session = Depends(get_db)):
    residente = crud.obtener_residente_por_id(db, id_residente)
    return residente


@router.put("/{id_residente}", response_model=schemas.ResidenteOut)
def actualizar_residente(
    id_residente: int,
    datos_actualizados: schemas.ResidenteUpdate,
    db: Session = Depends(get_db),
):
    residente_actualizado = crud.actualizar_residente(db, id_residente, datos_actualizados)
    return {"mensaje": "Residente actualizado correctamente", "residente": residente_actualizado}


@router.delete("/{id_residente}")
def eliminar_residente(id_residente: int, db: Session = Depends(get_db)):
    eliminado = crud.eliminar_residente(db, id_residente)
    return {"mensaje": "Residente eliminado correctamente", "residente": eliminado}


# > Asignar apartamento a residente <
@router.put("/{id_residente}/asignar_apartamento")
def asignar_apartamento(id_residente: int, id_apartamento: int, db: Session = Depends(get_db)):
    resultado = crud.asignar_residente_a_apartamento(db, id_residente, id_apartamento)
    return {"mensaje": "Residente asignado correctamente", "residente": resultado, "apartamento": "Asignado"}


# > Desasignar apartamento de residente <
@router.put("/{id_residente}/desasignar_apartamento")
def desasignar_residente(
    id_residente: int,
    inactivar: bool = Query(False, description="Indica si se inactiva el residente"),
    db: Session = Depends(get_db),
):
    resultado = crud.desasignar_residente(db, id_residente, inactivar)
    return {
        "mensaje": f"Residente {'inactivado y ' if inactivar else ''}desasignado correctamente",
        "residente": resultado,
        "apartamento": "Liberado" if resultado.id_apartamento is None else "Asignado",
        "estado": resultado.estado,
    }


# > Activar residente <
@router.put("/{id_residente}/activar")
def activar_residente(id_residente: int, db: Session = Depends(get_db)):
    resultado = crud.activar_residente(db, id_residente)
    return {"mensaje": "Residente activado correctamente", "residente": resultado, "estado": resultado.estado}


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/roles", tags=["Roles"])


# ---- Schemas adicionales ----


class RolMensajeOut(schemas.BaseModel):
    mensaje: str
    rol: schemas.RolOut


# ---- Endpoints ----


@router.get("/", response_model=list[schemas.RolOut])
def listar_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.obtener_roles(db, skip, limit)


@router.post("/", response_model=RolMensajeOut)
def crear_nuevo_rol(rol: schemas.RolCreate, db: Session = Depends(get_db)):
    rol_creado = crud.crear_rol(db, rol)
    return {"mensaje": "Rol creado correctamente", "rol": rol_creado}


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas, crud
from ..database import get_db


router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


# ---- Schemas de entrada adicionales ----


class CambiarRol(schemas.BaseModel):
    nuevo_id_rol: int


class CambiarPassword(schemas.BaseModel):
    nueva_password: str


class UsuarioMensajeOut(schemas.BaseModel):
    mensaje: str
    usuario: schemas.UsuarioOut


# ---- Endpoints ----


@router.post("/", response_model=schemas.UsuarioOut)
def crear_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    return crud.crear_usuario(db, usuario)


@router.get("/", response_model=list[schemas.UsuarioOut])
def listar_usuarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.obtener_usuarios(db, skip, limit)


@router.put("/ultima_sesion/{id_usuario}", response_model=schemas.UsuarioOut)
def actualizar_sesion(id_usuario: int, db: Session = Depends(get_db)):
    crud.actualizar_ultima_sesion(db, id_usuario)


@router.put("/{id_usuario}/desactivar", response_model=UsuarioMensajeOut)
def desactivar_usuario(id_usuario: int, db: Session = Depends(get_db)):
    usuario_desactivado = crud.desactivar_usuario(db, id_usuario)
    return {
        "mensaje": f"Usuario {id_usuario} desactivado correctamente",
        "usuario": usuario_desactivado,
    }


"""
@router.put("/{id_usuario}/desactivar", response_model=schemas.UsuarioOut)
def desactivar_usuario_endpoint(
    id_usuario: int,
    db: Session = Depends(get_db),
    usuario_actual: "Usuario" = Depends(
        crud.get_usuario_logueado
    ),  # ejemplo: tu función de login
):
    # Validar permiso
    validar_permiso(usuario_actual, entidad="Usuario", accion="eliminar")

    # Ejecutar la acción
    usuario_desactivado = crud.desactivar_usuario(db, id_usuario)
    return usuario_desactivado
"""


@router.put("/{id_usuario}/rol", response_model=UsuarioMensajeOut)
def actualizar_rol_usuario(id_usuario: int, datos: CambiarRol, db: Session = Depends(get_db)):
    usuario_actualizado = crud.cambiar_rol_usuario(db, id_usuario, datos.nuevo_id_rol)
    return {"mensaje": "Rol actualizado", "usuario": usuario_actualizado}


@router.put("/{id_usuario}/cambiar_password", response_model=UsuarioMensajeOut)
def cambiar_password(id_usuario: int, datos: CambiarPassword, db: Session = Depends(get_db)):
    return crud.cambiar_password(db, id_usuario, datos.nueva_password)
