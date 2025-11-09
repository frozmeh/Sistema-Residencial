from fastapi import APIRouter, Depends, Query, status, Request
from sqlalchemy.orm import Session
from typing import Optional
from ... import schemas, crud
from ...database import get_db
from ...core.security import verificar_admin

router = APIRouter(prefix="/admin/residentes", tags=["Admin - Residentes"])

# ==========================
# ---- Rutas para Admin ----
# ==========================


@router.get("/", response_model=list[schemas.ResidenteOut])
def listar_residentes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    return crud.obtener_residentes(db)[skip : skip + limit]


@router.get("/{id_residente}", response_model=schemas.ResidenteOut)
def obtener_residente(id_residente: int, db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    """Obtener un residente específico por ID"""
    return crud.obtener_residente_por_id(db, id_residente)


@router.get("/pendientes")
def listar_pendientes(
    torre: str | None = None, piso: int | None = None, db: Session = Depends(get_db), admin=Depends(verificar_admin)
):
    return crud.obtener_residentes_no_validados(db, torre, piso)


@router.put("/aprobar/{id_residente}")
def aprobar_residente(
    id_residente: int, request: Request = None, db: Session = Depends(get_db), admin=Depends(verificar_admin)
):
    return crud.aprobar_residente(db, id_residente, usuario_actual=admin, request=request)


@router.put("/rechazar/{id_residente}")
def rechazar_residente(
    id_residente: int,
    motivo: str = "Registro rechazado por el administrador.",
    request: Request = None,
    db: Session = Depends(get_db),
    admin=Depends(verificar_admin),
):
    return crud.rechazar_residente(db, id_residente, motivo, usuario_actual=admin, request=request)


@router.put("/{id_residente}/suspender")
def suspender_residente(
    id_residente: int, request: Request = None, db: Session = Depends(get_db), admin=Depends(verificar_admin)
):
    """Suspender residente (por mora, etc.)"""
    return crud.suspender_residente(db, id_residente, usuario_actual=admin, request=request)


@router.put("/{id_residente}/reactivar")
def reactivar_residente(
    id_residente: int, request: Request = None, db: Session = Depends(get_db), admin=Depends(verificar_admin)
):
    """Reactivar residente suspendido"""
    return crud.reactivar_residente(db, id_residente, usuario_actual=admin, request=request)


@router.put("/{id_residente}/asignar_apartamento")
def asignar_apartamento(
    id_residente: int,
    id_apartamento: int,
    request: Request = None,
    db: Session = Depends(get_db),
    admin=Depends(verificar_admin),
):
    return crud.asignar_residente_a_apartamento(
        db, id_residente, id_apartamento, usuario_actual=admin, request=request
    )


@router.put("/{id_residente}/desasignar_apartamento")
def desasignar_residente(
    id_residente: int,
    inactivar: bool = Query(False),
    request: Request = None,
    db: Session = Depends(get_db),
    admin=Depends(verificar_admin),
):
    return crud.desasignar_residente(db, id_residente, inactivar, usuario_actual=admin, request=request)


@router.put("/{id_residente}/reasignar_apartamento")
def reasignar_apartamento_pendiente(
    id_residente: int,
    torre: str,
    numero_apartamento: str,
    piso: int,
    request: Request = None,
    db: Session = Depends(get_db),
    admin=Depends(verificar_admin),
):
    return crud.reasignar_apartamento_pendiente(
        db, id_residente, torre, numero_apartamento, piso, usuario_actual=admin, request=request
    )


@router.put("/{id_residente}/activar")
def activar_residente(
    id_residente: int, request: Request = None, db: Session = Depends(get_db), admin=Depends(verificar_admin)
):
    return crud.activar_residente(db, id_residente, usuario_actual=admin, request=request)


@router.put("/{id_residente}", response_model=schemas.ResidenteOut)
def actualizar_residente_admin(
    id_residente: int,
    datos_actualizados: schemas.ResidenteUpdateAdmin,
    request: Request = None,
    db: Session = Depends(get_db),
    admin=Depends(verificar_admin),
):
    """Actualizar residente (solo admin) - permite cambiar más campos"""
    return crud.actualizar_residente(db, id_residente, datos_actualizados, usuario_actual=admin, request=request)


@router.delete("/{id_residente}")
def eliminar_residente(
    id_residente: int, request: Request = None, db: Session = Depends(get_db), admin=Depends(verificar_admin)
):
    return crud.eliminar_residente(db, id_residente, usuario_actual=admin, request=request)


@router.get("/contar/")
def contar_residentes(solo_activos: bool = True, db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    cantidad = crud.contar_residentes(db, solo_activos)
    return {"total_residentes": cantidad, "solo_activos": solo_activos}


@router.get("/estadisticas")
def obtener_estadisticas_residentes(db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    return crud.estadisticas_residentes(db)


@router.get("/estadisticas-dashboard")
def obtener_estadisticas_dashboard(db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    return crud.obtener_estadisticas_dashboard(db)


@router.get("/busqueda-avanzada", response_model=list[schemas.ResidenteOut])
def busqueda_avanzada_residentes(
    nombre: Optional[str] = Query(None),
    cedula: Optional[str] = Query(None),
    torre: Optional[str] = Query(None),
    tipo_residente: Optional[str] = Query(None),
    estado_operativo: Optional[str] = Query(None),
    estado_aprobacion: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin=Depends(verificar_admin),
):
    return crud.busqueda_avanzada(db, nombre, cedula, torre, tipo_residente, estado_operativo, estado_aprobacion)


@router.get("/buscar/{termino}", response_model=list[schemas.ResidenteOut])
def buscar_residente_admin(termino: str, db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    """Búsqueda básica de residentes (admin)"""
    return crud.buscar_residente(db, termino)


@router.get("/torre/{nombre_torre}", response_model=list[schemas.ResidenteOut])
def listar_residentes_por_torre_admin(
    nombre_torre: str, db: Session = Depends(get_db), admin=Depends(verificar_admin)
):
    return crud.obtener_residentes_por_torre(db, nombre_torre)


@router.get("/historial/apartamento/{id_apartamento}", response_model=list[schemas.ResidenteOut])
def historial_residentes_apartamento_admin(
    id_apartamento: int, db: Session = Depends(get_db), admin=Depends(verificar_admin)
):
    return crud.obtener_historial_residentes_por_apartamento(db, id_apartamento)
