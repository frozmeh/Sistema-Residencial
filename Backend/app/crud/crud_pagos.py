from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from sqlalchemy import func, and_
from . import models, schemas
from ..utils.db_helpers import guardar_y_refrescar
from ..utils.auditoria_helpers import registrar_auditoria
from decimal import Decimal
from typing import Union, Optional

# =====================
# ---- CRUD Pagos -----
# =====================


def crear_pago(db: Session, pago: schemas.PagoCreate, usuario_actual=None, request=None):
    # Validar residente
    residente = db.query(models.Residente).filter(models.Residente.id == pago.id_residente).first()
    if not residente:
        raise HTTPException(status_code=404, detail="El residente especificado no existe")
    if getattr(residente, "estado_operativo", None) != "Activo":
        raise HTTPException(status_code=400, detail="El residente no está activo")

    if pago.id_apartamento and residente.id_apartamento != pago.id_apartamento:
        raise HTTPException(status_code=400, detail="El residente no pertenece a este apartamento")

    # Validación coherencia moneda / tipo_cambio
    if pago.moneda == "VES" and not pago.tipo_cambio_bcv:
        raise HTTPException(status_code=400, detail="Debe especificar tipo_cambio_bcv para pagos en VES")
    if pago.moneda == "USD" and pago.tipo_cambio_bcv:
        raise HTTPException(status_code=400, detail="No debe indicar tipo_cambio_bcv para pagos en USD")

    # Evitar pagos duplicados por COMPROBANTE (no por concepto)
    if pago.comprobante:  # Solo validar si hay comprobante
        pago_existente = (
            db.query(models.Pago)
            .filter(
                models.Pago.id_residente == pago.id_residente,
                models.Pago.comprobante == pago.comprobante,
                func.date(models.Pago.fecha_pago) == pago.fecha_pago.date(),
            )
            .first()
        )
        if pago_existente:
            raise HTTPException(status_code=400, detail="Ya existe un pago con el mismo comprobante en esta fecha")

    if pago.id_gasto_fijo and pago.id_gasto_variable:
        raise HTTPException(status_code=400, detail="No se puede asignar tanto gasto fijo como variable al mismo pago")

    # Validar que el gasto existe y pertenece al residente
    gasto = None
    if pago.id_gasto_fijo:
        gasto = db.query(models.GastoFijo).filter(models.GastoFijo.id == pago.id_gasto_fijo).first()
        if not gasto:
            raise HTTPException(status_code=404, detail="Gasto fijo no encontrado")
        # Verificar que el gasto esté asignado al apartamento del residente
        if gasto.id_apartamento != residente.id_apartamento:  # Usar residente.id_apartamento
            raise HTTPException(status_code=400, detail="El gasto no corresponde al apartamento del residente")

    elif pago.id_gasto_variable:
        gasto = db.query(models.GastoVariable).filter(models.GastoVariable.id == pago.id_gasto_variable).first()
        if not gasto:
            raise HTTPException(status_code=404, detail="Gasto variable no encontrado")
        # Verificar que el gasto esté asignado al apartamento del residente
        gasto_apto = (
            db.query(models.gastos_variables_apartamentos)
            .filter(
                models.gastos_variables_apartamentos.c.id_gasto_variable == pago.id_gasto_variable,
                models.gastos_variables_apartamentos.c.id_apartamento
                == residente.id_apartamento,  # Usar residente.id_apartamento
            )
            .first()
        )
        if not gasto_apto:
            raise HTTPException(
                status_code=400, detail="El gasto variable no corresponde al apartamento del residente"
            )

    # Validación de saldo disponible en el gasto (usando la misma variable 'gasto')
    if gasto:  # Solo validar si hay un gasto asociado
        monto_pago_usd = convertir_monto_pago_a_usd(pago)
        if gasto.saldo_pendiente < monto_pago_usd:
            raise HTTPException(
                status_code=400,
                detail=f"El pago excede el saldo pendiente del gasto. Saldo disponible: {float(gasto.saldo_pendiente)} USD, Monto del pago: {float(monto_pago_usd)} USD",
            )

    if pago.moneda == "VES":
        if not pago.tipo_cambio_bcv:
            raise HTTPException(
                status_code=400, detail="Para pagos en BOLÍVARES es OBLIGATORIO especificar tipo_cambio_bcv"
            )
        if pago.tipo_cambio_bcv <= 0:
            raise HTTPException(status_code=400, detail="tipo_cambio_bcv debe ser mayor a 0")

        # VALIDAR que la tasa sea razonable (evitar errores de digitación)
        from ..utils.tasa_bcv import obtener_tasa_bcv

        tasa_actual, _ = obtener_tasa_bcv()
        tasa_pago = float(pago.tipo_cambio_bcv)

        # Validar que la tasa no difiera más del 50% de la tasa actual
        if abs(tasa_pago - tasa_actual) / tasa_actual > 0.5:
            raise HTTPException(
                status_code=400,
                detail=f"El tipo de cambio especificado ({tasa_pago}) parece incorrecto. "
                f"Tasa BCV actual: {tasa_actual}. Verifique el valor.",
            )

    # Si no hay id_apartamento en el pago, usar el del residente
    if not pago.id_apartamento:
        pago_data = pago.model_dump()
        pago_data["id_apartamento"] = residente.id_apartamento
        nuevo_pago = models.Pago(**pago_data)
    else:
        nuevo_pago = models.Pago(**pago.model_dump())

    db.add(nuevo_pago)
    guardar_y_refrescar(db, nuevo_pago)

    if usuario_actual:
        registrar_auditoria(
            db=db,
            usuario_id=usuario_actual.id,
            usuario_nombre=usuario_actual.nombre,
            accion="Creación de pago",
            tabla="pagos",
            objeto_previo=None,
            objeto_nuevo={c.name: getattr(nuevo_pago, c.name) for c in nuevo_pago.__table__.columns},
            request=request,
            campos_visibles=["monto", "moneda", "concepto", "metodo", "estado", "id_residente"],
            forzar=True,
        )

    return nuevo_pago


def obtener_pagos(db: Session):
    pagos = db.query(models.Pago).order_by(models.Pago.fecha_creacion.desc()).all()
    if not pagos:
        raise HTTPException(status_code=404, detail="No hay pagos registrados")
    return pagos


def obtener_pago_por_id(db: Session, id_pago: int):
    pago = db.query(models.Pago).filter(models.Pago.id == id_pago).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return pago


def actualizar_pago(
    db: Session, id_pago: int, datos_actualizados: schemas.PagoUpdate, usuario_actual=None, request=None
):
    pago = obtener_pago_por_id(db, id_pago)
    pago_previo = {c.name: getattr(pago, c.name) for c in pago.__table__.columns}
    datos = datos_actualizados.model_dump(exclude_unset=True)

    # Validaciones cruzadas
    if "id_residente" in datos:
        residente = db.query(models.Residente).filter(models.Residente.id == datos["id_residente"]).first()
        if not residente:
            raise HTTPException(status_code=404, detail="El nuevo residente no existe")
        if getattr(residente, "estado", None) != "Activo":
            raise HTTPException(status_code=400, detail="El nuevo residente no está activo")

    # Coherencia moneda / tipo_cambio
    moneda = datos.get("moneda")
    tipo_cambio = datos.get("tipo_cambio_bcv")
    if moneda == "VES" and (not tipo_cambio or tipo_cambio <= 0):
        raise HTTPException(status_code=400, detail="Debe especificar tipo_cambio_bcv válido para pagos en VES")
    if moneda == "USD" and tipo_cambio:
        raise HTTPException(status_code=400, detail="No debe indicar tipo_cambio_bcv para pagos en USD")

    # Coherencia verificado / estado
    if "verificado" in datos or "estado" in datos:
        verificado = datos.get("verificado", pago.verificado)
        estado = datos.get("estado", pago.estado)
        if verificado and estado not in ["Validado", "Rechazado"]:
            raise HTTPException(
                status_code=400,
                detail="Un pago verificado solo puede tener estado 'Validado' o 'Rechazado'",
            )

    for key, value in datos.items():
        setattr(pago, key, value)

    guardar_y_refrescar(db, pago)

    if usuario_actual:
        registrar_auditoria(
            db=db,
            usuario_id=usuario_actual.id,
            usuario_nombre=usuario_actual.nombre,
            accion="Actualización de pago",
            tabla="pagos",
            objeto_previo=pago_previo,
            objeto_nuevo={c.name: getattr(pago, c.name) for c in pago.__table__.columns},
            request=request,
            campos_visibles=["monto", "moneda", "concepto", "metodo", "estado", "verificado"],
        )

    return pago


def eliminar_pago(db: Session, id_pago: int, usuario_actual=None, request=None, es_admin=False):
    pago = obtener_pago_por_id(db, id_pago)

    # Si NO es admin, verificar permisos
    if not es_admin:
        # Verificar que el usuario actual sea el residente del pago
        if usuario_actual and pago.id_residente != usuario_actual.get("id"):
            raise HTTPException(status_code=403, detail="No tienes permisos para eliminar este pago")

        # Verificar que el pago esté pendiente
        if pago.estado != "Pendiente":
            raise HTTPException(status_code=400, detail="Solo se pueden eliminar pagos pendientes")

    # Revertir saldo si el pago estaba validado
    if pago.estado == "Validado" and (pago.id_gasto_fijo or pago.id_gasto_variable):
        revertir_saldo_gasto(db, pago)

    # Guardar estado previo para auditoría
    pago_previo = {c.name: getattr(pago, c.name) for c in pago.__table__.columns}

    db.delete(pago)
    db.commit()

    # Eliminación de pago
    if usuario_actual:
        accion = "Eliminación de pago" + (" (admin)" if es_admin else " (residente)")
        registrar_auditoria(
            db=db,
            usuario_id=usuario_actual.id,
            usuario_nombre=usuario_actual.nombre,
            accion=accion,
            tabla="pagos",
            objeto_previo=pago_previo,
            objeto_nuevo=None,
            request=request,
        )

    return {"detalle": f"Pago con id {id_pago} eliminado correctamente"}


def revertir_saldo_gasto(db: Session, pago: models.Pago):
    """
    Revertir el saldo del gasto cuando se elimina un pago validado
    """
    monto_pago_usd = convertir_monto_pago_a_usd(pago)
    monto_pago_decimal = Decimal(str(monto_pago_usd))

    gasto = None
    if pago.id_gasto_fijo:
        gasto = db.query(models.GastoFijo).filter(models.GastoFijo.id == pago.id_gasto_fijo).first()
    elif pago.id_gasto_variable:
        gasto = db.query(models.GastoVariable).filter(models.GastoVariable.id == pago.id_gasto_variable).first()

    if gasto:
        # Solo revertir si el pago estaba validado
        if pago.estado == "Validado":
            gasto.monto_pagado -= monto_pago_decimal
            gasto.saldo_pendiente += monto_pago_decimal

            # Validaciones de consistencia
            if gasto.saldo_pendiente < 0:
                gasto.saldo_pendiente = Decimal("0")
            if gasto.monto_pagado < 0:
                gasto.monto_pagado = Decimal("0")

        db.commit()


def filtrar_pagos(
    db: Session,
    id_residente: int = None,
    id_apartamento: int = None,
    estado: str = None,
    fecha_inicio: datetime = None,
    fecha_fin: datetime = None,
):
    query = db.query(models.Pago)

    if id_residente:
        query = query.filter(models.Pago.id_residente == id_residente)
    if id_apartamento:
        query = query.filter(models.Pago.id_apartamento == id_apartamento)
    if estado:
        query = query.filter(models.Pago.estado == estado)
    if fecha_inicio and fecha_fin:
        query = query.filter(and_(models.Pago.fecha_pago >= fecha_inicio, models.Pago.fecha_pago <= fecha_fin))
    elif fecha_inicio:
        query = query.filter(models.Pago.fecha_pago >= fecha_inicio)
    elif fecha_fin:
        query = query.filter(models.Pago.fecha_pago <= fecha_fin)

    pagos = query.order_by(models.Pago.fecha_pago.desc()).all()
    if not pagos:
        raise HTTPException(status_code=404, detail="No se encontraron pagos con los filtros aplicados")
    return pagos


def actualizar_estado_pago(
    db: Session, id_pago: int, nuevo_estado: str, verificado: bool = False, usuario_actual=None, request=None
):
    pago = obtener_pago_por_id(db, id_pago)
    pago_previo = {c.name: getattr(pago, c.name) for c in pago.__table__.columns}

    if nuevo_estado not in ["Pendiente", "Validado", "Rechazado"]:
        raise HTTPException(status_code=400, detail="Estado de pago inválido")

    if verificado and nuevo_estado not in ["Validado", "Rechazado"]:
        raise HTTPException(
            status_code=400,
            detail="Un pago verificado solo puede tener estado 'Validado' o 'Rechazado'",
        )

    # Actualizar saldos del gasto cuando el pago se valida/rechaza
    estado_anterior = pago.estado
    pago.estado = nuevo_estado
    pago.verificado = verificado or (nuevo_estado == "Validado")
    pago.fecha_actualizacion = datetime.now()

    # ACTUALIZAR SALDOS DEL GASTO ASOCIADO
    if pago.id_gasto_fijo or pago.id_gasto_variable:
        actualizar_saldo_gasto(db, pago, estado_anterior, nuevo_estado)

    guardar_y_refrescar(db, pago)

    if usuario_actual:
        registrar_auditoria(
            db=db,
            usuario_id=usuario_actual.id,
            usuario_nombre=usuario_actual.nombre,
            accion=f"Cambio de estado a {nuevo_estado}",
            tabla="pagos",
            objeto_previo=pago_previo,
            objeto_nuevo={c.name: getattr(pago, c.name) for c in pago.__table__.columns},
            request=request,
            campos_visibles=["estado", "verificado"],
        )

    return pago


def convertir_monto_pago_a_usd(pago: Union[schemas.PagoCreate, models.Pago]) -> Decimal:
    """
    Convierte el monto del pago a USD para consistencia con gastos
    """
    if pago.moneda == "USD":
        return Decimal(str(pago.monto))
    elif pago.moneda == "VES":
        if not pago.tipo_cambio_bcv:
            # ❌ NO MÁS FALLBACK: Esto genera pérdidas
            raise ValueError(
                "No se puede convertir pago en VES a USD sin tipo_cambio_bcv. "
                "Este campo es OBLIGATORIO para pagos en bolívares."
            )
        return Decimal(str(pago.monto)) / Decimal(str(pago.tipo_cambio_bcv))
    else:
        raise ValueError(f"Moneda no soportada: {pago.moneda}")


def actualizar_saldo_gasto(db: Session, pago: models.Pago, estado_anterior: str, nuevo_estado: str):
    """
    Actualiza el saldo del gasto cuando un pago cambia de estado
    CORREGIDA: Maneja conversión de moneda y validaciones
    """
    monto_pago_usd = convertir_monto_pago_a_usd(pago)

    # Determinar el gasto (fijo o variable)
    gasto = None
    if pago.id_gasto_fijo:
        gasto = db.query(models.GastoFijo).filter(models.GastoFijo.id == pago.id_gasto_fijo).first()
    elif pago.id_gasto_variable:
        gasto = db.query(models.GastoVariable).filter(models.GastoVariable.id == pago.id_gasto_variable).first()

    if not gasto:
        return

    # Usar Decimal para cálculos precisos
    monto_pago_decimal = Decimal(str(monto_pago_usd))

    # Lógica de actualización de saldos
    if estado_anterior == "Validado" and nuevo_estado != "Validado":
        # Pago dejó de estar validado: REVERTIR
        gasto.monto_pagado -= monto_pago_decimal
        gasto.saldo_pendiente += monto_pago_decimal

    elif estado_anterior != "Validado" and nuevo_estado == "Validado":
        # Pago se validó: APLICAR
        gasto.monto_pagado += monto_pago_decimal
        gasto.saldo_pendiente -= monto_pago_decimal

    # alidaciones de consistencia
    if gasto.saldo_pendiente < 0:
        gasto.saldo_pendiente = Decimal("0")
    if gasto.monto_pagado < 0:
        gasto.monto_pagado = Decimal("0")

    # No puede pagar más del monto total
    if gasto.monto_pagado > gasto.monto_usd:
        gasto.monto_pagado = gasto.monto_usd
        gasto.saldo_pendiente = Decimal("0")

    db.commit()


def obtener_resumen_pagos(db: Session):
    resumen = (
        db.query(
            models.Pago.estado,
            func.count(models.Pago.id).label("cantidad"),
            func.sum(models.Pago.monto).label("total_pagado"),
        )
        .group_by(models.Pago.estado)
        .all()
    )

    if not resumen:
        raise HTTPException(status_code=404, detail="No hay pagos para generar resumen")

    return [
        {"estado": r.estado, "cantidad": int(r.cantidad), "total_pagado": Decimal(r.total_pagado or 0)}
        for r in resumen
    ]


def calcular_estado_cuenta(db: Session, id_residente: int):
    """
    Calcula el estado de cuenta completo de un residente
    Incluye gastos asignados, pagos realizados y saldos pendientes
    """
    # Obtener residente y su apartamento
    residente = db.query(models.Residente).filter(models.Residente.id == id_residente).first()
    if not residente:
        raise HTTPException(status_code=404, detail="Residente no encontrado")

    id_apartamento = residente.id_apartamento
    if not id_apartamento:
        raise HTTPException(status_code=400, detail="El residente no tiene apartamento asignado")

    # 1. OBTENER GASTOS FIJOS DEL APARTAMENTO
    gastos_fijos = db.query(models.GastoFijo).filter(models.GastoFijo.id_apartamento == id_apartamento).all()

    # 2. OBTENER GASTOS VARIABLES ASIGNADOS AL APARTAMENTO
    gastos_variables = (
        db.query(models.GastoVariable)
        .join(
            models.gastos_variables_apartamentos,
            models.GastoVariable.id == models.gastos_variables_apartamentos.c.id_gasto_variable,
        )
        .filter(models.gastos_variables_apartamentos.c.id_apartamento == id_apartamento)
        .all()
    )

    # 3. OBTENER PAGOS DEL RESIDENTE
    pagos = (
        db.query(models.Pago)
        .filter(models.Pago.id_residente == id_residente)
        .order_by(models.Pago.fecha_pago.desc())
        .all()
    )

    # 4. CALCULAR TOTALES DE GASTOS
    total_gastos_fijos = sum([g.monto_usd for g in gastos_fijos]) if gastos_fijos else 0
    total_gastos_variables = sum([g.monto_usd for g in gastos_variables]) if gastos_variables else 0
    total_gastos = total_gastos_fijos + total_gastos_variables

    # 5. CALCULAR TOTALES DE PAGOS
    pagos_validados = [p for p in pagos if p.estado == "Validado"]
    total_pagado = Decimal("0")
    for pago in pagos_validados:
        try:
            monto_usd = convertir_monto_pago_a_usd(pago)
            total_pagado += monto_usd
        except ValueError as e:
            print(f"Advertencia: No se pudo convertir pago {pago.id}: {e}")
            continue

    # 6. CALCULAR SALDO PENDIENTE
    total_gastos = Decimal(str(total_gastos_fijos)) + Decimal(str(total_gastos_variables))
    saldo_pendiente = total_gastos - total_pagado

    # 7. DETALLE DE GASTOS CON SU ESTADO DE PAGO
    detalle_gastos = []

    # Gastos fijos
    for gasto in gastos_fijos:
        pagos_gasto = [p for p in pagos_validados if p.id_gasto_fijo == gasto.id]
        monto_pagado_gasto = Decimal("0")

        for pago in pagos_gasto:
            try:
                monto_usd_pago = convertir_monto_pago_a_usd(pago)
                monto_pagado_gasto += monto_usd_pago
            except ValueError as e:
                print(f"Advertencia: No se pudo convertir pago {pago.id} del gasto fijo {gasto.id}: {e}")
                continue

        saldo_gasto = Decimal(str(gasto.monto_usd)) - monto_pagado_gasto

        detalle_gastos.append(
            {
                "tipo": "fijo",
                "id": gasto.id,
                "concepto": f"{gasto.tipo_gasto} - {gasto.descripcion or ''}",
                "monto_total": float(gasto.monto_usd),
                "monto_pagado": float(monto_pagado_gasto),
                "saldo_pendiente": float(saldo_gasto),
                "fecha_creacion": gasto.fecha_creacion,
                "completado": saldo_gasto <= 0,
            }
        )

    # Gastos variables
    for gasto in gastos_variables:
        # Obtener monto asignado específico a este apartamento
        asignacion = (
            db.query(models.gastos_variables_apartamentos)
            .filter(
                models.gastos_variables_apartamentos.c.id_gasto_variable == gasto.id,
                models.gastos_variables_apartamentos.c.id_apartamento == id_apartamento,
            )
            .first()
        )

        monto_asignado = Decimal(str(asignacion.monto_asignado_usd)) if asignacion else Decimal(str(gasto.monto_usd))

        pagos_gasto = [p for p in pagos_validados if p.id_gasto_variable == gasto.id]
        monto_pagado_gasto = Decimal("0")

        for pago in pagos_gasto:
            try:
                monto_usd_pago = convertir_monto_pago_a_usd(pago)
                monto_pagado_gasto += monto_usd_pago
            except ValueError as e:
                print(f"Advertencia: No se pudo convertir pago {pago.id} del gasto variable {gasto.id}: {e}")
                continue

        saldo_gasto = monto_asignado - monto_pagado_gasto

        detalle_gastos.append(
            {
                "tipo": "variable",
                "id": gasto.id,
                "concepto": f"{gasto.tipo_gasto} - {gasto.descripcion or ''}",
                "monto_total": float(monto_asignado),
                "monto_pagado": float(monto_pagado_gasto),
                "saldo_pendiente": float(saldo_gasto),
                "fecha_creacion": gasto.fecha_creacion,
                "completado": saldo_gasto <= 0,
            }
        )

    # 8. DETALLE DE PAGOS
    detalle_pagos = []
    for pago in pagos:
        # Determinar a qué gasto pertenece
        gasto_concepto = "Pago general"
        if pago.id_gasto_fijo:
            gasto_fijo = db.query(models.GastoFijo).filter(models.GastoFijo.id == pago.id_gasto_fijo).first()
            gasto_concepto = f"Gasto fijo: {gasto_fijo.tipo_gasto}" if gasto_fijo else "Gasto fijo"
        elif pago.id_gasto_variable:
            gasto_var = (
                db.query(models.GastoVariable).filter(models.GastoVariable.id == pago.id_gasto_variable).first()
            )
            gasto_concepto = f"Gasto variable: {gasto_var.tipo_gasto}" if gasto_var else "Gasto variable"

        detalle_pagos.append(
            {
                "id": pago.id,
                "monto": float(pago.monto),
                "moneda": pago.moneda,
                "tipo_cambio": float(pago.tipo_cambio_bcv) if pago.tipo_cambio_bcv else None,
                "fecha_pago": pago.fecha_pago,
                "concepto": pago.concepto,
                "gasto_asociado": gasto_concepto,
                "metodo": pago.metodo,
                "estado": pago.estado,
                "verificado": pago.verificado,
                "comprobante": pago.comprobante,
            }
        )

    # 9. RESUMEN FINAL
    resumen = {
        "residente": {
            "id": residente.id,
            "nombre": residente.nombre,
            "apartamento": residente.apartamento.numero if residente.apartamento else "No asignado",
            "torre": (
                residente.apartamento.piso.torre.nombre
                if residente.apartamento and residente.apartamento.piso
                else "No asignado"
            ),
        },
        "totales": {
            "total_gastos": float(total_gastos),
            "total_pagado": float(total_pagado),
            "saldo_pendiente": float(saldo_pendiente),
            "porcentaje_pagado": (total_pagado / total_gastos * 100) if total_gastos > 0 else 0,
        },
        "desglose_gastos": {
            "fijos": {"cantidad": len(gastos_fijos), "total": float(total_gastos_fijos)},
            "variables": {"cantidad": len(gastos_variables), "total": float(total_gastos_variables)},
        },
        "desglose_pagos": {
            "validados": len(pagos_validados),
            "pendientes": len([p for p in pagos if p.estado == "Pendiente"]),
            "rechazados": len([p for p in pagos if p.estado == "Rechazado"]),
            "total": len(pagos),
        },
        "detalle_gastos": detalle_gastos,
        "detalle_pagos": detalle_pagos,
        "fecha_consulta": datetime.now().isoformat(),
    }

    return resumen
