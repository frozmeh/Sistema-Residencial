from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from enum import Enum

from ... import schemas, crud
from ...database import get_db
from ...core.security import verificar_admin

router = APIRouter(prefix="/admin/pagos", tags=["Pagos (Administración)"])

# ==========================
# ---- ENUMS Y VALIDACIONES ----
# ==========================


class EstadoPagoEnum(str, Enum):
    PENDIENTE = "Pendiente"
    VALIDADO = "Validado"
    RECHAZADO = "Rechazado"


class MonedaPagoEnum(str, Enum):
    USD = "USD"
    VES = "VES"


class MetodoPagoEnum(str, Enum):
    TRANSFERENCIA = "Transferencia"
    EFECTIVO = "Efectivo"
    PAGO_MOVIL = "Pago Móvil"


# ==========================
# ---- CONSULTAS Y LISTADOS ----
# ==========================


@router.get(
    "/",
    response_model=List[schemas.PagoOut],
    summary="Listar todos los pagos",
    description="Obtiene todos los pagos del sistema ordenados por fecha de creación.",
)
def listar_pagos_admin(
    admin: dict = Depends(verificar_admin),
    db: Session = Depends(get_db),
):
    return crud.obtener_pagos(db)


@router.get(
    "/filtros",
    response_model=List[schemas.PagoOut],
    summary="Filtrar pagos",
    description="Filtra pagos por residente, apartamento, estado, fechas u otros criterios.",
)
def filtrar_pagos_admin(
    admin: dict = Depends(verificar_admin),
    db: Session = Depends(get_db),
    id_residente: Optional[int] = Query(None, description="Filtrar por ID de residente"),
    id_apartamento: Optional[int] = Query(None, description="Filtrar por ID de apartamento"),
    estado: Optional[EstadoPagoEnum] = Query(None, description="Filtrar por estado del pago"),
    moneda: Optional[MonedaPagoEnum] = Query(None, description="Filtrar por moneda"),
    metodo: Optional[MetodoPagoEnum] = Query(None, description="Filtrar por método de pago"),
    fecha_inicio: Optional[datetime] = Query(None, description="Fecha inicial para filtrar (fecha_pago)"),
    fecha_fin: Optional[datetime] = Query(None, description="Fecha final para filtrar (fecha_pago)"),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=500, description="Límite de registros"),
):
    # Validación de fechas
    if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
        raise HTTPException(status_code=400, detail="La fecha de inicio no puede ser mayor a la fecha final")

    # Convertir Enum a string para el filtro
    estado_filtro = estado.value if estado else None

    pagos = crud.filtrar_pagos(
        db,
        id_residente=id_residente,
        id_apartamento=id_apartamento,
        estado=estado_filtro,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )

    # Aplicar filtros adicionales manualmente
    if moneda:
        pagos = [p for p in pagos if p.moneda == moneda.value]
    if metodo:
        pagos = [p for p in pagos if p.metodo == metodo.value]

    return pagos[skip : skip + limit]


@router.get(
    "/{id_pago}",
    response_model=schemas.PagoOut,
    summary="Obtener pago específico",
    description="Obtiene los detalles completos de un pago específico por su ID.",
)
def obtener_pago_admin(
    id_pago: int,
    admin: dict = Depends(verificar_admin),
    db: Session = Depends(get_db),
):
    return crud.obtener_pago_por_id(db, id_pago)


# ==========================
# ---- OPERACIONES CRUD ----
# ==========================


@router.put(
    "/{id_pago}",
    response_model=schemas.PagoOut,
    summary="Actualizar pago",
    description="Actualiza la información de un pago existente.",
)
def actualizar_pago_admin(
    id_pago: int,
    datos_actualizados: schemas.PagoUpdate,
    request: Request = None,
    admin: dict = Depends(verificar_admin),
    db: Session = Depends(get_db),
):
    return crud.actualizar_pago(db, id_pago, datos_actualizados, usuario_actual=admin, request=request)


@router.put(
    "/{id_pago}/estado",
    response_model=schemas.PagoOut,
    summary="Actualizar estado del pago",
    description="Cambia el estado de un pago (Pendiente/Validado/Rechazado) y actualiza saldos de gastos automáticamente.",
)
def actualizar_estado_pago_admin(
    id_pago: int,
    nuevo_estado: EstadoPagoEnum,
    request: Request = None,
    verificado: bool = Query(False, description="Marcar como verificado por administrador"),
    admin: dict = Depends(verificar_admin),
    db: Session = Depends(get_db),
):
    return crud.actualizar_estado_pago(
        db, id_pago, nuevo_estado.value, verificado, usuario_actual=admin, request=request
    )


@router.delete(
    "/{id_pago}",
    summary="Eliminar pago",
    description="Elimina un pago del sistema. Si estaba validado, revierte automáticamente los saldos de gastos.",
)
def eliminar_pago_admin(
    id_pago: int,
    request: Request = None,
    admin: dict = Depends(verificar_admin),
    db: Session = Depends(get_db),
):
    return crud.eliminar_pago(db, id_pago, usuario_actual=admin, request=request, es_admin=True)


# ==========================
# ---- REPORTES Y ESTADÍSTICAS ----
# ==========================


@router.get(
    "/resumen/general",
    summary="Resumen general de pagos",
    description="Obtiene un resumen estadístico de todos los pagos por estado.",
)
def obtener_resumen_pagos_admin(
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicial para filtrar"),
    fecha_fin: Optional[date] = Query(None, description="Fecha final para filtrar"),
    admin: dict = Depends(verificar_admin),
    db: Session = Depends(get_db),
):
    """Resumen general de pagos con filtros opcionales por fecha"""
    resumen = crud.obtener_resumen_pagos(db)

    # Aplicar filtros de fecha si se proporcionan
    if fecha_inicio or fecha_fin:
        pagos_filtrados = crud.filtrar_pagos(db, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

        # Recalcular resumen con los pagos filtrados
        estados = {}
        for pago in pagos_filtrados:
            if pago.estado not in estados:
                estados[pago.estado] = {"cantidad": 0, "total_pagado": 0}
            estados[pago.estado]["cantidad"] += 1
            estados[pago.estado]["total_pagado"] += float(pago.monto)

        resumen = [
            {"estado": estado, "cantidad": datos["cantidad"], "total_pagado": datos["total_pagado"]}
            for estado, datos in estados.items()
        ]

    return {
        "resumen": resumen,
        "periodo": {
            "fecha_inicio": fecha_inicio.isoformat() if fecha_inicio else None,
            "fecha_fin": fecha_fin.isoformat() if fecha_fin else None,
        },
        "fecha_consulta": datetime.now().isoformat(),
    }


@router.get(
    "/estado-cuenta/{id_residente}",
    summary="Estado de cuenta de residente",
    description="Obtiene el estado de cuenta completo de un residente específico.",
)
def obtener_estado_cuenta_residente(
    id_residente: int,
    admin: dict = Depends(verificar_admin),
    db: Session = Depends(get_db),
):
    """Obtener estado de cuenta completo de un residente con todos sus gastos y pagos"""
    return crud.calcular_estado_cuenta(db, id_residente)


@router.get(
    "/reporte/mensual",
    summary="Reporte mensual de pagos",
    description="Genera un reporte mensual de pagos con estadísticas detalladas.",
)
def reporte_mensual_pagos_admin(
    mes: int = Query(..., ge=1, le=12, description="Mes del reporte (1-12)"),
    año: int = Query(..., ge=2020, description="Año del reporte"),
    admin: dict = Depends(verificar_admin),
    db: Session = Depends(get_db),
):
    """Reporte mensual detallado de pagos"""
    fecha_inicio = datetime(año, mes, 1)
    if mes == 12:
        fecha_fin = datetime(año + 1, 1, 1)
    else:
        fecha_fin = datetime(año, mes + 1, 1)

    pagos_mes = crud.filtrar_pagos(db, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

    # Estadísticas por moneda
    total_usd = sum(p.monto for p in pagos_mes if p.moneda == "USD")
    total_ves = sum(p.monto for p in pagos_mes if p.moneda == "VES")

    # Estadísticas por método
    metodos = {}
    for pago in pagos_mes:
        if pago.metodo not in metodos:
            metodos[pago.metodo] = 0
        metodos[pago.metodo] += 1

    # Estadísticas por estado
    estados = {}
    for pago in pagos_mes:
        if pago.estado not in estados:
            estados[pago.estado] = 0
        estados[pago.estado] += 1

    return {
        "periodo": {
            "mes": mes,
            "año": año,
            "fecha_inicio": fecha_inicio.date().isoformat(),
            "fecha_fin": fecha_fin.date().isoformat(),
        },
        "estadisticas": {
            "total_pagos": len(pagos_mes),
            "total_usd": float(total_usd),
            "total_ves": float(total_ves),
            "distribucion_metodos": metodos,
            "distribucion_estados": estados,
        },
        "detalle_pagos": [
            {
                "id": p.id,
                "residente_id": p.id_residente,
                "residente_nombre": p.residente.nombre if p.residente else "N/A",
                "monto": float(p.monto),
                "moneda": p.moneda,
                "metodo": p.metodo,
                "estado": p.estado,
                "fecha_pago": p.fecha_pago.isoformat(),
                "concepto": p.concepto,
            }
            for p in pagos_mes
        ],
    }
