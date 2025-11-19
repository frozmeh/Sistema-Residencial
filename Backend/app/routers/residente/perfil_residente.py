from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session, joinedload
from ... import models, schemas, crud
from ...database import get_db
from ...core.security import verificar_residente, get_usuario_actual

router = APIRouter(prefix="/residente", tags=["Residente - Perfil y Gestión"])

# =======================================
# ---- Rutas disponibles al residente ----
# =======================================


@router.post("/", response_model=schemas.ResidenteOut)
def registrar_residente(
    residente: schemas.ResidenteCreate,
    request: Request = None,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_actual),
):
    residente_creado = crud.crear_residente(db, residente, usuario.id, request=request, usuario_actual=usuario)

    residente_con_datos = (
        db.query(models.Residente)
        .options(
            joinedload(models.Residente.apartamento).joinedload(models.Apartamento.piso).joinedload(models.Piso.torre)
        )
        .filter(models.Residente.id == residente_creado.id)
        .first()
    )

    return residente_con_datos


@router.get("/me", response_model=schemas.ResidenteOut)
def obtener_mi_residente(usuario=Depends(verificar_residente), db: Session = Depends(get_db)):
    return crud.obtener_residente_asociado(db, usuario.id)


@router.put("/me", response_model=schemas.ResidenteOut)
def actualizar_mi_residente(
    datos_actualizados: schemas.ResidenteUpdateResidente,
    request: Request = None,
    db: Session = Depends(get_db),
    usuario=Depends(verificar_residente),
):
    residente = crud.obtener_residente_asociado(db, usuario.id)
    return crud.actualizar_residente(db, residente.id, datos_actualizados, usuario_actual=usuario, request=request)


@router.get("/buscar", response_model=list[schemas.ResidenteOut])
def buscar_residente(
    termino: str = Query(..., description="Nombre, cédula o correo"),
    db: Session = Depends(get_db),
    usuario=Depends(verificar_residente),
):
    return crud.buscar_residente(db, termino)


@router.get("/torre/{nombre_torre}", response_model=list[schemas.ResidenteOut])
def listar_residentes_por_torre(
    nombre_torre: str, db: Session = Depends(get_db), usuario=Depends(verificar_residente)
):
    return crud.obtener_residentes_por_torre(db, nombre_torre)


@router.get("/historial/apartamento/{id_apartamento}", response_model=list[schemas.ResidenteOut])
def historial_residentes_apartamento(
    id_apartamento: int, db: Session = Depends(get_db), usuario=Depends(verificar_residente)
):
    return crud.obtener_historial_residentes_por_apartamento(db, id_apartamento)


@router.get("/estadisticas-torre/{nombre_torre}")
def estadisticas_torre(nombre_torre: str, db: Session = Depends(get_db), usuario=Depends(verificar_residente)):
    """Estadísticas básicas de residentes en una torre"""
    residentes_torre = crud.obtener_residentes_por_torre(db, nombre_torre)
    total = len(residentes_torre)
    propietarios = len([r for r in residentes_torre if r.tipo_residente == "Propietario"])
    inquilinos = len([r for r in residentes_torre if r.tipo_residente == "Inquilino"])

    return {
        "torre": nombre_torre,
        "total_residentes": total,
        "propietarios": propietarios,
        "inquilinos": inquilinos,
        "porcentaje_propietarios": (propietarios / total * 100) if total > 0 else 0,
        "porcentaje_inquilinos": (inquilinos / total * 100) if total > 0 else 0,
    }


@router.get("/verificar-estado")
def verificar_estado_residente(usuario=Depends(verificar_residente), db: Session = Depends(get_db)):
    """Verificar estado actual del residente (útil para frontend)"""
    residente = crud.obtener_residente_asociado(db, usuario.id)

    return {
        "residente_id": residente.id,
        "nombre": residente.nombre,
        "estado_aprobacion": residente.estado_aprobacion,
        "estado_operativo": residente.estado_operativo,
        "reside_actualmente": residente.reside_actualmente,
        "apartamento": residente.apartamento.numero if residente.apartamento else None,
        "torre": residente.apartamento.piso.torre.nombre if residente.apartamento else None,
        "puede_usar_sistema": residente.estado_aprobacion == "Aprobado" and residente.estado_operativo == "Activo",
    }
