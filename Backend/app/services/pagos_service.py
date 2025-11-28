# services/pagos_service.py
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from decimal import Decimal
import logging
from datetime import date, datetime

from ..models import Pago, Residente, EstadoPagoEnum, MetodoPagoEnum
from ..models.financiero import Cargo, EstadoCargoEnum, Gasto, ReporteFinanciero
from ..models.torres import Apartamento
from ..schemas.financiero import PagoCargoCreate, ValidarPagoRequest

logger = logging.getLogger(__name__)


class PagosService:

    def registrar_pago_residente(self, db: Session, datos: PagoCargoCreate) -> Pago:
        """
        Registra un pago realizado por un residente - SOPORTA USD Y VES
        """
        try:
            # 1. Verificar que el cargo existe
            cargo = db.query(Cargo).options(joinedload(Cargo.apartamento)).filter(Cargo.id == datos.id_cargo).first()

            if not cargo:
                raise ValueError(f"Cargo {datos.id_cargo} no encontrado")

            # 2. Verificar que el residente existe y pertenece al apartamento
            residente = (
                db.query(Residente)
                .filter(Residente.id == datos.id_residente, Residente.id_apartamento == cargo.id_apartamento)
                .first()
            )

            if not residente:
                raise ValueError(f"Residente {datos.id_residente} no pertenece al apartamento del cargo")

            # 3. 🆕 OBTENER TASA DE CAMBIO ACTUAL
            from ..services.tasa_cambio_service import tasa_cambio_service

            tasa_cambio = tasa_cambio_service.obtener_tasa_actual(db)
            if not tasa_cambio:
                raise ValueError("No hay tasa de cambio disponible")

            # 4. 🆕 CALCULAR MONTOS SEGÚN LA MONEDA DE PAGO
            monto_pagado_usd = Decimal("0.00")
            monto_pagado_ves = Decimal("0.00")
            tipo_cambio_bcv = None

            if datos.moneda_pago == "USD":
                # Pago en USD → convertir a VES
                monto_pagado_usd = datos.monto_pagado
                monto_pagado_ves = datos.monto_pagado * tasa_cambio.tasa_usd_ves
                tipo_cambio_bcv = None  # Para USD, no necesitamos tipo_cambio_bcv

            elif datos.moneda_pago == "VES":
                # Pago en VES → convertir a USD
                monto_pagado_ves = datos.monto_pagado
                monto_pagado_usd = datos.monto_pagado / tasa_cambio.tasa_usd_ves
                tipo_cambio_bcv = tasa_cambio.tasa_usd_ves  # Para VES, sí necesitamos

            else:
                raise ValueError(f"Moneda no válida: {datos.moneda_pago}")

            # 5. Verificar que no excede el saldo pendiente
            if monto_pagado_usd > cargo.saldo_pendiente_usd:
                raise ValueError(
                    f"Monto pagado (${monto_pagado_usd} USD) excede saldo pendiente (${cargo.saldo_pendiente_usd} USD)"
                )

            # 6. Obtener reporte financiero del periodo actual
            periodo_actual = datetime.now().strftime("%Y-%m")
            reporte = db.query(ReporteFinanciero).filter(ReporteFinanciero.periodo == periodo_actual).first()

            if not reporte:
                reporte = ReporteFinanciero(
                    periodo=periodo_actual,
                    generado_por="Sistema Automático",
                    total_ingresos_usd=0,
                    total_gastos_usd=0,
                    saldo_final_usd=0,
                    total_ingresos_ves=0,
                    total_gastos_ves=0,
                    saldo_final_ves=0,
                    estado="Abierto",
                )
                db.add(reporte)
                db.flush()

            # 7. Crear registro de pago - VERSIÓN MEJORADA
            pago = Pago(
                id_cargo=datos.id_cargo,
                id_residente=datos.id_residente,
                id_apartamento=cargo.id_apartamento,
                id_reporte_financiero=reporte.id,
                id_gasto=cargo.id_gasto,
                # Campos nuevos del flujo (calculados por el sistema)
                monto_pagado_usd=monto_pagado_usd,
                monto_pagado_ves=monto_pagado_ves,
                tasa_cambio_pago=tasa_cambio.tasa_usd_ves,  # Tasa usada para la conversión
                # Campos legacy (para compatibilidad)
                monto=datos.monto_pagado,  # Monto original que pagó el usuario
                moneda=datos.moneda_pago,  # Moneda en la que pagó el usuario
                tipo_cambio_bcv=tipo_cambio_bcv,  # Solo para pagos en VES
                concepto=datos.concepto,
                metodo=MetodoPagoEnum(datos.metodo_pago),
                comprobante=datos.comprobante_url,
                estado=EstadoPagoEnum.PENDIENTE,
                verificado=False,
                fecha_creacion=datetime.now(),
            )

            db.add(pago)
            db.flush()

            # 8. Aplicar pago al cargo (actualizar saldos)
            self._aplicar_pago_a_cargo(db, pago, cargo)

            db.commit()

            logger.info(f"✅ Pago {pago.id} registrado por residente {datos.id_residente}")
            logger.info(f"   - Monto original: {datos.monto_pagado} {datos.moneda_pago}")
            logger.info(f"   - Convertido a: ${monto_pagado_usd} USD / {monto_pagado_ves} VES")
            logger.info(f"   - Tasa utilizada: {tasa_cambio.tasa_usd_ves}")
            return pago

        except Exception as e:
            db.rollback()
            logger.error(f"Error registrando pago: {str(e)}")
            raise

    def _aplicar_pago_a_cargo(self, db: Session, pago: Pago, cargo: Cargo):
        """
        Aplica el pago al cargo y actualiza saldos pendientes
        """
        try:
            # Actualizar saldos pendientes del cargo
            cargo.saldo_pendiente_usd -= pago.monto_pagado_usd
            cargo.saldo_pendiente_ves -= pago.monto_pagado_ves

            # Verificar que los saldos no sean negativos
            if cargo.saldo_pendiente_usd < 0:
                cargo.saldo_pendiente_usd = Decimal("0.00")
            if cargo.saldo_pendiente_ves < 0:
                cargo.saldo_pendiente_ves = Decimal("0.00")

            # Actualizar estado del cargo
            from ..services.cargos_service import cargos_service

            cargos_service.actualizar_estado_cargo(db, cargo.id)

            # Actualizar reporte financiero (ingresos)
            reporte = db.query(ReporteFinanciero).filter(ReporteFinanciero.id == pago.id_reporte_financiero).first()

            if reporte:
                reporte.total_ingresos_usd += pago.monto_pagado_usd
                reporte.total_ingresos_ves += pago.monto_pagado_ves
                reporte.saldo_final_usd = reporte.total_ingresos_usd - reporte.total_gastos_usd
                reporte.saldo_final_ves = reporte.total_ingresos_ves - reporte.total_gastos_ves

            logger.info(
                f"🔄 Pago {pago.id} aplicado a cargo {cargo.id}. Saldo restante: ${cargo.saldo_pendiente_usd} USD"
            )

        except Exception as e:
            logger.error(f"Error aplicando pago a cargo: {str(e)}")
            raise

    def validar_pago_administrador(self, db: Session, pago_id: int, admin_id: int, datos: ValidarPagoRequest) -> Pago:
        """
        Valida o rechaza un pago por parte del administrador - AJUSTADO
        """
        try:
            pago = (
                db.query(Pago)
                .options(joinedload(Pago.cargo), joinedload(Pago.residente))
                .filter(Pago.id == pago_id)
                .first()
            )

            if not pago:
                raise ValueError(f"Pago {pago_id} no encontrado")

            if pago.estado != EstadoPagoEnum.PENDIENTE:
                raise ValueError(f"Pago {pago_id} ya fue procesado (estado: {pago.estado})")

            # En tu modelo actual no tienes campo "validado_por", usaremos observaciones temporalmente
            # O podrías agregar el campo si lo necesitas

            if datos.accion == "completo":
                pago.estado = EstadoPagoEnum.VALIDADO
                pago.verificado = True
                # pago.validado_por = f"Admin_{admin_id}"  # Si agregas este campo
                # pago.fecha_validacion = datetime.now()
                pago.comprobante = pago.comprobante or "Validado sin comprobante"

                logger.info(f"✅ Pago {pago_id} validado COMPLETAMENTE por admin {admin_id}")

            elif datos.accion == "parcial":
                # En tu Enum no tienes "Parcial", manejaremos como Validado pero con observaciones
                pago.estado = EstadoPagoEnum.VALIDADO
                pago.verificado = True
                pago.comprobante = f"Pago parcial - {datos.observaciones or 'Sin observaciones'}"

                logger.info(f"🟡 Pago {pago_id} validado PARCIALMENTE por admin {admin_id}")

            elif datos.accion == "rechazado":
                pago.estado = EstadoPagoEnum.RECHAZADO
                pago.verificado = False
                pago.comprobante = f"Rechazado - {datos.observaciones or 'Sin observaciones'}"

                # Revertir el pago en el cargo (saldos pendientes)
                if pago.cargo:
                    pago.cargo.saldo_pendiente_usd += pago.monto_pagado_usd
                    pago.cargo.saldo_pendiente_ves += pago.monto_pagado_ves

                    from ..services.cargos_service import cargos_service

                    cargos_service.actualizar_estado_cargo(db, pago.cargo.id)

                logger.info(f"❌ Pago {pago_id} RECHAZADO por admin {admin_id}")

            else:
                raise ValueError(f"Acción no válida: {datos.accion}")

            pago.fecha_actualizacion = datetime.now()
            db.commit()
            return pago

        except Exception as e:
            db.rollback()
            logger.error(f"Error validando pago {pago_id}: {str(e)}")
            raise

    def obtener_pagos_por_periodo(self, db: Session, periodo: str) -> List[Pago]:
        """
        Obtiene todos los pagos de un período específico
        """
        try:
            pagos = (
                db.query(Pago)
                .options(
                    joinedload(Pago.cargo).joinedload(Cargo.apartamento),
                    joinedload(Pago.residente),
                    joinedload(Pago.reporte_financiero),
                )
                .join(ReporteFinanciero)
                .filter(ReporteFinanciero.periodo == periodo)
                .order_by(Pago.fecha_creacion.desc())
                .all()
            )

            logger.info(f"✅ Encontrados {len(pagos)} pagos para período {periodo}")
            return pagos

        except Exception as e:
            logger.error(f"Error obteniendo pagos para período {periodo}: {str(e)}")
            raise

    def obtener_pagos_por_apartamento(self, db: Session, apartamento_id: int) -> List[Pago]:
        """
        Obtiene todos los pagos de un apartamento específico
        """
        try:
            pagos = (
                db.query(Pago)
                .options(joinedload(Pago.cargo), joinedload(Pago.residente), joinedload(Pago.reporte_financiero))
                .filter(Pago.id_apartamento == apartamento_id)
                .order_by(Pago.fecha_creacion.desc())
                .all()
            )

            logger.info(f"✅ Encontrados {len(pagos)} pagos para apartamento {apartamento_id}")
            return pagos

        except Exception as e:
            logger.error(f"Error obteniendo pagos para apartamento {apartamento_id}: {str(e)}")
            raise

    def obtener_pagos_pendientes_validacion(self, db: Session) -> List[Pago]:
        """
        Obtiene todos los pagos pendientes de validación por administrador
        """
        try:
            pagos = (
                db.query(Pago)
                .options(joinedload(Pago.cargo).joinedload(Cargo.apartamento), joinedload(Pago.residente))
                .filter(Pago.estado == EstadoPagoEnum.PENDIENTE)
                .order_by(Pago.fecha_creacion.asc())
                .all()
            )

            logger.info(f"✅ Encontrados {len(pagos)} pagos pendientes de validación")
            return pagos

        except Exception as e:
            logger.error(f"Error obteniendo pagos pendientes de validación: {str(e)}")
            raise

    def obtener_pago_por_id(self, db: Session, pago_id: int) -> Optional[Pago]:
        """
        Obtiene un pago específico con todas sus relaciones
        """
        try:
            pago = (
                db.query(Pago)
                .options(
                    joinedload(Pago.cargo).joinedload(Cargo.apartamento),
                    joinedload(Pago.cargo).joinedload(Cargo.gasto),
                    joinedload(Pago.residente),
                    joinedload(Pago.reporte_financiero),
                )
                .filter(Pago.id == pago_id)
                .first()
            )

            return pago

        except Exception as e:
            logger.error(f"Error obteniendo pago {pago_id}: {str(e)}")
            raise


# Instancia global
pagos_service = PagosService()
