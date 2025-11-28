from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from ... import schemas, crud
from ...database import get_db
from ...core.security import verificar_residente

router = APIRouter(prefix="/residente/pagos", tags=["Pagos (Residente)"])

# ==========================
# ---- OPERACIONES CRUD ----
# ==========================


@router.post(
    "/",
    response_model=schemas.PagoOut,
    summary="Registrar nuevo pago",
    description="Registra un nuevo pago. Para pagos en VES, es OBLIGATORIO especificar tipo_cambio_bcv.",
)
def crear_pago_residente(
    pago: schemas.PagoCreate,
    request: Request = None,
    residente: dict = Depends(verificar_residente),
    db: Session = Depends(get_db),
):
    """
    Registra un nuevo pago:
    - El id_residente se asigna automáticamente desde el token
    - Para pagos en USD: no especificar tipo_cambio_bcv
    - Para pagos en VES: OBLIGATORIO especificar tipo_cambio_bcv
    - Se valida automáticamente el saldo disponible en gastos asociados
    """
    pago.id_residente = residente["id"]
    return crud.crear_pago(db, pago, usuario_actual=residente, request=request)


@router.get(
    "/mis-pagos",
    response_model=List[schemas.PagoOut],
    summary="Mis pagos",
    description="Obtiene todos mis pagos ordenados por fecha más reciente.",
)
def listar_pagos_residente(
    estado: Optional[str] = Query(None, description="Filtrar por estado (Pendiente/Validado/Rechazado)"),
    fecha_inicio: Optional[datetime] = Query(None, description="Fecha inicial para filtrar"),
    fecha_fin: Optional[datetime] = Query(None, description="Fecha final para filtrar"),
    residente: dict = Depends(verificar_residente),
    db: Session = Depends(get_db),
):
    pagos = crud.filtrar_pagos(
        db, id_residente=residente["id"], estado=estado, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )

    if not pagos:
        raise HTTPException(status_code=404, detail="No se encontraron pagos asociados a tu cuenta.")
    return pagos


@router.delete(
    "/{id_pago}",
    summary="Eliminar mi pago",
    description="Elimina uno de mis pagos. Solo se pueden eliminar pagos en estado 'Pendiente'.",
)
def eliminar_pago_residente(
    id_pago: int,
    request: Request = None,
    residente: dict = Depends(verificar_residente),
    db: Session = Depends(get_db),
):
    return crud.eliminar_pago(db, id_pago, usuario_actual=residente, request=request)


# ==========================
# ---- REPORTES Y CONSULTAS ----
# ==========================


@router.get(
    "/mis-resumen", summary="Resumen de mis pagos", description="Obtiene un resumen estadístico de todos mis pagos."
)
def resumen_pagos_residente(
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicial para filtrar"),
    fecha_fin: Optional[date] = Query(None, description="Fecha final para filtrar"),
    residente: dict = Depends(verificar_residente),
    db: Session = Depends(get_db),
):
    """Resumen detallado de mis pagos con filtros opcionales"""
    pagos = crud.filtrar_pagos(db, id_residente=residente["id"], fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

    # Cálculos detallados
    total_pagado_usd = 0
    total_pagado_ves = 0
    estados = {"Pendiente": 0, "Validado": 0, "Rechazado": 0}
    metodos = {"Transferencia": 0, "Efectivo": 0, "Pago Móvil": 0}

    for pago in pagos:
        estados[pago.estado] += 1
        metodos[pago.metodo] += 1

        if pago.moneda == "USD":
            total_pagado_usd += float(pago.monto)
        elif pago.moneda == "VES":
            total_pagado_ves += float(pago.monto)

    # Pagos validados (que afectan saldos)
    pagos_validados = [p for p in pagos if p.estado == "Validado"]
    total_validado_usd = sum(float(p.monto) for p in pagos_validados if p.moneda == "USD")
    total_validado_ves = sum(float(p.monto) for p in pagos_validados if p.moneda == "VES")

    return {
        "residente_id": residente["id"],
        "periodo": {
            "fecha_inicio": fecha_inicio.isoformat() if fecha_inicio else None,
            "fecha_fin": fecha_fin.isoformat() if fecha_fin else None,
        },
        "resumen": {
            "total_pagos": len(pagos),
            "total_pagado_usd": total_pagado_usd,
            "total_pagado_ves": total_pagado_ves,
            "total_validado_usd": total_validado_usd,
            "total_validado_ves": total_validado_ves,
            "estados": estados,
            "metodos": metodos,
        },
        "ultimos_pagos": [
            {
                "id": p.id,
                "monto": float(p.monto),
                "moneda": p.moneda,
                "concepto": p.concepto,
                "estado": p.estado,
                "fecha_pago": p.fecha_pago.isoformat(),
                "metodo": p.metodo,
            }
            for p in pagos[:10]  # Últimos 10 pagos
        ],
    }


@router.get(
    "/mis-estado-cuenta",
    summary="Mi estado de cuenta",
    description="Obtiene mi estado de cuenta completo con todos los gastos, pagos y saldos pendientes.",
)
def obtener_mi_estado_cuenta(
    residente: dict = Depends(verificar_residente),
    db: Session = Depends(get_db),
):
    """Obtener mi estado de cuenta completo con información detallada"""
    return crud.calcular_estado_cuenta(db, residente["id"])


@router.get(
    "/pagos-pendientes",
    summary="Mis pagos pendientes",
    description="Obtiene solo mis pagos que están pendientes de validación.",
)
def mis_pagos_pendientes(
    residente: dict = Depends(verificar_residente),
    db: Session = Depends(get_db),
):
    """Obtiene los pagos que están pendientes de validación por administración"""
    pagos_pendientes = crud.filtrar_pagos(db, id_residente=residente["id"], estado="Pendiente")

    return {
        "pagos_pendientes": [
            {
                "id": p.id,
                "monto": float(p.monto),
                "moneda": p.moneda,
                "concepto": p.concepto,
                "fecha_pago": p.fecha_pago.isoformat(),
                "metodo": p.metodo,
                "comprobante": p.comprobante,
            }
            for p in pagos_pendientes
        ],
        "total_pendientes": len(pagos_pendientes),
        "total_monto_pendiente": sum(float(p.monto) for p in pagos_pendientes),
    }


@router.get(
    "/estadisticas/mensuales",
    summary="Estadísticas mensuales",
    description="Obtiene estadísticas mensuales de mis pagos del año actual.",
)
def estadisticas_mensuales_residente(
    año: int = Query(None, description="Año para las estadísticas (por defecto año actual)"),
    residente: dict = Depends(verificar_residente),
    db: Session = Depends(get_db),
):
    """Estadísticas mensuales de pagos para gráficos y análisis"""
    año_actual = año or datetime.now().year
    estadisticas = []

    for mes in range(1, 13):
        fecha_inicio = datetime(año_actual, mes, 1)
        if mes == 12:
            fecha_fin = datetime(año_actual + 1, 1, 1)
        else:
            fecha_fin = datetime(año_actual, mes + 1, 1)

        pagos_mes = crud.filtrar_pagos(
            db, id_residente=residente["id"], fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
        )

        total_mes = sum(float(p.monto) for p in pagos_mes)
        validados_mes = sum(1 for p in pagos_mes if p.estado == "Validado")

        estadisticas.append(
            {
                "mes": mes,
                "año": año_actual,
                "total_pagos": len(pagos_mes),
                "total_monto": total_mes,
                "pagos_validados": validados_mes,
                "nombre_mes": fecha_inicio.strftime("%B"),
            }
        )

    return {
        "año": año_actual,
        "estadisticas_mensuales": estadisticas,
        "total_anual": sum(item["total_monto"] for item in estadisticas),
        "total_pagos_anual": sum(item["total_pagos"] for item in estadisticas),
    }
