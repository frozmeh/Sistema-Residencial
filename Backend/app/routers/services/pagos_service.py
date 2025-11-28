# routes/pagos.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from ...models import Pago
from ...database import get_db
from ...services.pagos_service import pagos_service
from ...schemas.pagos import PagoCargoCreate, PagoCreate, PagoUpdate, PagoOut, PagoValidacion, ValidarPagoRequest

router = APIRouter(prefix="/pagos", tags=["pagos"])


@router.post(
    "/cargos/registrar",
    status_code=status.HTTP_201_CREATED,
    response_model=PagoOut,
    summary="Registrar pago de cargo por residente",
)
def registrar_pago_cargo(datos: PagoCargoCreate, db: Session = Depends(get_db)):
    """
    Endpoint para que los residentes registren pagos de cargos específicos

    **Flujo:**
    1. Residente selecciona un cargo pendiente
    2. Registra el pago con los montos en USD y VES
    3. Sistema actualiza automáticamente el saldo pendiente del cargo
    4. Pago queda en estado "Pendiente" hasta validación del administrador
    """
    try:
        pago = pagos_service.registrar_pago_residente(db, datos)
        return pago
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registrando pago: {str(e)}")


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PagoOut, summary="Registrar pago tradicional")
def crear_pago(datos: PagoCreate, db: Session = Depends(get_db)):
    """
    Endpoint tradicional para registrar pagos (mantener compatibilidad)

    **Para pagos que no vienen del flujo de cargos**
    """
    try:
        # Aquí iría la lógica para tu método tradicional de pagos
        # Por ahora redirigimos al nuevo método adaptado
        pago_data = PagoCargoCreate(
            id_cargo=0,  # Temporal - necesitarías adaptar esta lógica
            id_residente=datos.id_residente,
            monto_pagado_usd=datos.monto,
            monto_pagado_ves=datos.monto * Decimal("1.0"),  # Usar tasa real
            tasa_cambio_pago=Decimal("1.0"),  # Usar tasa real
            metodo_pago=datos.metodo,
            referencia=None,
            comprobante_url=datos.comprobante,
            fecha_pago=datos.fecha_pago.date(),
            concepto=datos.concepto,
        )

        pago = pagos_service.registrar_pago_residente(db, pago_data)
        return pago

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando pago: {str(e)}")


@router.put("/{pago_id}/validar", response_model=PagoOut, summary="Validar pago (administrador)")
def validar_pago(
    pago_id: int,
    datos: ValidarPagoRequest,
    admin_id: int = Query(..., description="ID del administrador"),  # En producción vendría del token
    db: Session = Depends(get_db),
):
    """
    Endpoint para que administradores validen o rechacen pagos

    **Acciones disponibles:**
    - "completo": Pago validado completamente
    - "parcial": Pago validado parcialmente (con observaciones)
    - "rechazado": Pago rechazado (se revierten saldos)
    """
    try:
        pago = pagos_service.validar_pago_administrador(db, pago_id, admin_id, datos)
        return pago
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validando pago: {str(e)}")


@router.get("/", response_model=List[PagoOut], summary="Obtener todos los pagos")
def obtener_pagos(
    skip: int = Query(0, description="Paginación - registros a saltar"),
    limit: int = Query(100, description="Paginación - límite de registros"),
    db: Session = Depends(get_db),
):
    """
    Obtiene todos los pagos con paginación
    """
    try:
        # Esto es un ejemplo básico - en producción usarías paginación real
        pagos = pagos_service.obtener_pagos_por_periodo(db, "2025-11")  # Ejemplo
        return pagos[skip : skip + limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/periodo/{periodo}", response_model=List[PagoOut], summary="Obtener pagos por período")
def obtener_pagos_periodo(periodo: str, db: Session = Depends(get_db)):  # Formato: "2024-11"
    """
    Obtiene todos los pagos de un período específico
    """
    try:
        pagos = pagos_service.obtener_pagos_por_periodo(db, periodo)
        return pagos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/apartamentos/{apartamento_id}", response_model=List[PagoOut], summary="Obtener pagos de un apartamento")
def obtener_pagos_apartamento(apartamento_id: int, db: Session = Depends(get_db)):
    """
    Obtiene el historial completo de pagos de un apartamento
    """
    try:
        pagos = pagos_service.obtener_pagos_por_apartamento(db, apartamento_id)
        return pagos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/residentes/{residente_id}", response_model=List[PagoOut], summary="Obtener pagos de un residente")
def obtener_pagos_residente(residente_id: int, db: Session = Depends(get_db)):
    """
    Obtiene el historial de pagos de un residente específico
    """
    try:
        # Podrías agregar este método al service si lo necesitas
        pagos = db.query(Pago).filter(Pago.id_residente == residente_id).all()
        return pagos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pendientes-validacion", response_model=List[PagoOut], summary="Obtener pagos pendientes de validación")
def obtener_pagos_pendientes_validacion(db: Session = Depends(get_db)):
    """
    Obtiene todos los pagos que esperan validación del administrador

    **Útil para el dashboard del administrador**
    """
    try:
        pagos = pagos_service.obtener_pagos_pendientes_validacion(db)
        return pagos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vencidos", response_model=List[PagoOut], summary="Obtener pagos vencidos")
def obtener_pagos_vencidos(db: Session = Depends(get_db)):
    """
    Obtiene pagos asociados a cargos vencidos
    """
    try:
        # Podrías implementar esta lógica en el service
        from ...models.financiero import Pago, Cargo

        pagos = db.query(Pago).join(Cargo).filter(Cargo.estado == "Vencido").all()
        return pagos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{pago_id}", response_model=PagoOut, summary="Obtener pago específico")
def obtener_pago(pago_id: int, db: Session = Depends(get_db)):
    """
    Obtiene un pago específico con todas sus relaciones
    """
    try:
        pago = pagos_service.obtener_pago_por_id(db, pago_id)
        if not pago:
            raise HTTPException(status_code=404, detail="Pago no encontrado")
        return pago
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{pago_id}", response_model=PagoOut, summary="Actualizar pago")
def actualizar_pago(pago_id: int, datos: PagoUpdate, db: Session = Depends(get_db)):
    """
    Actualiza la información de un pago existente
    """
    try:
        # Implementar lógica de actualización según tus necesidades
        pago = pagos_service.obtener_pago_por_id(db, pago_id)
        if not pago:
            raise HTTPException(status_code=404, detail="Pago no encontrado")

        # Actualizar campos
        for field, value in datos.dict(exclude_unset=True).items():
            setattr(pago, field, value)

        pago.fecha_actualizacion = datetime.now()
        db.commit()
        db.refresh(pago)

        return pago

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{pago_id}", status_code=status.HTTP_200_OK, summary="Eliminar pago")
def eliminar_pago(pago_id: int, db: Session = Depends(get_db)):
    """
    Elimina un pago (solo para administradores)
    """
    try:
        pago = db.query(Pago).filter(Pago.id == pago_id).first()
        if not pago:
            raise HTTPException(status_code=404, detail="Pago no encontrado")

        # Aquí deberías agregar lógica para revertir saldos si es necesario
        db.delete(pago)
        db.commit()

        return {"message": "Pago eliminado exitosamente"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint para verificación manual de vencimientos
@router.post("/verificar-vencimientos", summary="Ejecutar verificación de vencimientos")
def ejecutar_verificacion_vencimientos(db: Session = Depends(get_db)):
    """
    Endpoint manual para ejecutar la verificación de cargos vencidos
    (Normalmente esto correría automáticamente cada día)
    """
    try:
        from ..services.cargos_service import cargos_service

        cargos_actualizados = cargos_service.verificar_vencimientos_automatico(db)
        return {"message": "Verificación de vencimientos completada", "cargos_actualizados": cargos_actualizados}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
