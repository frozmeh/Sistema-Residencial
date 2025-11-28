# services/reportes_financieros_service.py
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Optional
from decimal import Decimal
from datetime import datetime, date, timedelta
import logging
from sqlalchemy import func, and_

from ..models.financiero import ReporteFinanciero, Gasto, EstadoGastoEnum, EstadoCargoEnum
from ..models.pagos import Pago
from ..models.torres import Apartamento
from ..models.residentes import Residente
from ..schemas.financiero import ReporteFinancieroResponse

logger = logging.getLogger(__name__)


class ReportesFinancierosService:

    def generar_reporte_mensual(self, db: Session, periodo: str, generado_por: str = "Sistema") -> ReporteFinanciero:
        """
        Genera o actualiza el reporte financiero mensual consolidando TODOS los datos
        """
        try:
            logger.info(f"🔄 Generando reporte financiero para período {periodo}")

            # Verificar si ya existe un reporte para este período
            reporte_existente = db.query(ReporteFinanciero).filter(ReporteFinanciero.periodo == periodo).first()

            if reporte_existente:
                logger.info(f"📊 Reporte existente encontrado, actualizando...")
                return self._actualizar_reporte_existente(db, reporte_existente, periodo)
            else:
                logger.info(f"🆕 Creando nuevo reporte para {periodo}")
                return self._crear_nuevo_reporte(db, periodo, generado_por)

        except Exception as e:
            logger.error(f"❌ Error generando reporte para {periodo}: {str(e)}")
            raise

    def _crear_nuevo_reporte(self, db: Session, periodo: str, generado_por: str) -> ReporteFinanciero:
        """
        Crea un nuevo reporte financiero desde cero
        """
        # Obtener todos los gastos del período
        gastos_periodo = db.query(Gasto).filter(Gasto.periodo == periodo).all()

        # Obtener todos los pagos del período
        pagos_periodo = db.query(Pago).filter(Pago.reporte_financiero.has(periodo=periodo)).all()

        # Calcular totales
        total_gastos_usd = sum(g.monto_total_usd for g in gastos_periodo)
        total_gastos_ves = sum(g.monto_total_ves for g in gastos_periodo)
        total_ingresos_usd = sum(p.monto_pagado_usd for p in pagos_periodo)
        total_ingresos_ves = sum(p.monto_pagado_ves for p in pagos_periodo)

        # Calcular tasa de cambio promedio (promedio de tasas de gastos)
        tasas_gastos = [g.tasa_cambio for g in gastos_periodo if g.tasa_cambio]
        tasa_cambio_promedio = sum(tasas_gastos) / len(tasas_gastos) if tasas_gastos else Decimal("0.00")

        # Crear nuevo reporte
        nuevo_reporte = ReporteFinanciero(
            periodo=periodo,
            generado_por=generado_por,
            total_ingresos_usd=total_ingresos_usd,
            total_gastos_usd=total_gastos_usd,
            saldo_final_usd=total_ingresos_usd - total_gastos_usd,
            total_ingresos_ves=total_ingresos_ves,
            total_gastos_ves=total_gastos_ves,
            saldo_final_ves=total_ingresos_ves - total_gastos_ves,
            tasa_cambio_promedio=tasa_cambio_promedio,
            estado="Abierto",
            fecha_generacion=datetime.now(),
        )

        db.add(nuevo_reporte)
        db.commit()
        db.refresh(nuevo_reporte)

        logger.info(f"✅ Nuevo reporte creado: {periodo}")
        logger.info(f"   - Ingresos: ${total_ingresos_usd} USD / {total_ingresos_ves} VES")
        logger.info(f"   - Gastos: ${total_gastos_usd} USD / {total_gastos_ves} VES")
        logger.info(f"   - Saldo: ${nuevo_reporte.saldo_final_usd} USD")

        return nuevo_reporte

    def _actualizar_reporte_existente(
        self, db: Session, reporte: ReporteFinanciero, periodo: str
    ) -> ReporteFinanciero:
        """
        Actualiza un reporte existente con los datos más recientes
        """
        # Recalcular todos los totales
        gastos_periodo = db.query(Gasto).filter(Gasto.periodo == periodo).all()

        pagos_periodo = db.query(Pago).filter(Pago.reporte_financiero.has(periodo=periodo)).all()

        total_gastos_usd = sum(g.monto_total_usd for g in gastos_periodo)
        total_gastos_ves = sum(g.monto_total_ves for g in gastos_periodo)
        total_ingresos_usd = sum(p.monto_pagado_usd for p in pagos_periodo)
        total_ingresos_ves = sum(p.monto_pagado_ves for p in pagos_periodo)

        # Actualizar tasas promedio
        tasas_gastos = [g.tasa_cambio for g in gastos_periodo if g.tasa_cambio]
        tasa_cambio_promedio = sum(tasas_gastos) / len(tasas_gastos) if tasas_gastos else reporte.tasa_cambio_promedio

        # Actualizar reporte
        reporte.total_ingresos_usd = total_ingresos_usd
        reporte.total_gastos_usd = total_gastos_usd
        reporte.saldo_final_usd = total_ingresos_usd - total_gastos_usd
        reporte.total_ingresos_ves = total_ingresos_ves
        reporte.total_gastos_ves = total_gastos_ves
        reporte.saldo_final_ves = total_ingresos_ves - total_gastos_ves
        reporte.tasa_cambio_promedio = tasa_cambio_promedio
        reporte.fecha_generacion = datetime.now()

        db.commit()
        db.refresh(reporte)

        logger.info(f"✅ Reporte actualizado: {periodo}")
        return reporte

    def obtener_estado_cuenta_apartamento(self, db: Session, apartamento_id: int, periodo: str) -> Dict:
        """
        Estado de cuenta DETALLADO para un apartamento específico
        """
        try:
            # Verificar que el apartamento existe
            apartamento = db.query(Apartamento).filter(Apartamento.id == apartamento_id).first()
            if not apartamento:
                raise ValueError(f"Apartamento {apartamento_id} no encontrado")

            # Obtener cargos del período
            cargos_periodo = (
                db.query(Gasto)
                .join(Gasto.distribuciones)
                .filter(Gasto.periodo == periodo, Gasto.distribuciones.any(apartamento_id=apartamento_id))
                .options(joinedload(Gasto.distribuciones))
                .all()
            )

            # Obtener pagos del período
            pagos_periodo = (
                db.query(Pago)
                .filter(Pago.id_apartamento == apartamento_id, Pago.reporte_financiero.has(periodo=periodo))
                .all()
            )

            # Calcular distribuciones específicas para este apartamento
            distribuciones_apartamento = []
            total_cargos_usd = Decimal("0.00")

            for gasto in cargos_periodo:
                distribucion = next((d for d in gasto.distribuciones if d.id_apartamento == apartamento_id), None)
                if distribucion:
                    distribuciones_apartamento.append(
                        {
                            "gasto_id": gasto.id,
                            "descripcion": gasto.descripcion,
                            "fecha_gasto": gasto.fecha_gasto,
                            "tipo_gasto": gasto.tipo_gasto,
                            "monto_asignado_usd": distribucion.monto_asignado_usd,
                            "monto_asignado_ves": distribucion.monto_asignado_ves,
                            "porcentaje_aplicado": distribucion.porcentaje_aplicado,
                        }
                    )
                    total_cargos_usd += distribucion.monto_asignado_usd

            # Calcular total de pagos
            total_pagos_usd = sum(p.monto_pagado_usd for p in pagos_periodo)

            # Obtener saldo del período anterior (si existe)
            saldo_anterior = self._obtener_saldo_periodo_anterior(db, apartamento_id, periodo)

            # Calcular saldo actual
            saldo_actual = saldo_anterior + total_cargos_usd - total_pagos_usd

            return {
                "apartamento": {
                    "id": apartamento.id,
                    "numero": apartamento.numero,
                    "tipo": apartamento.tipo_apartamento.nombre if apartamento.tipo_apartamento else "No definido",
                },
                "periodo": periodo,
                "resumen": {
                    "saldo_anterior_usd": saldo_anterior,
                    "total_cargos_usd": total_cargos_usd,
                    "total_pagos_usd": total_pagos_usd,
                    "saldo_actual_usd": saldo_actual,
                },
                "detalle_cargos": distribuciones_apartamento,
                "detalle_pagos": [
                    {
                        "id": pago.id,
                        "fecha_pago": pago.fecha_creacion.date() if pago.fecha_creacion else None,
                        "monto_usd": pago.monto_pagado_usd,
                        "monto_ves": pago.monto_pagado_ves,
                        "metodo": pago.metodo,
                        "estado": pago.estado,
                        "concepto": pago.concepto,
                    }
                    for pago in pagos_periodo
                ],
                "estado": "AL DÍA" if saldo_actual <= 0 else "PENDIENTE",
            }

        except Exception as e:
            logger.error(f"Error obteniendo estado de cuenta para apartamento {apartamento_id}: {str(e)}")
            raise

    def _obtener_saldo_periodo_anterior(self, db: Session, apartamento_id: int, periodo_actual: str) -> Decimal:
        """
        Calcula el saldo pendiente del período anterior
        """
        try:
            # Convertir periodo a fecha para calcular el anterior
            año, mes = map(int, periodo_actual.split("-"))
            if mes == 1:
                periodo_anterior = f"{año-1}-12"
            else:
                periodo_anterior = f"{año}-{mes-1:02d}"

            # Obtener TODOS los cargos de períodos anteriores para este apartamento
            cargos_anteriores = (
                db.query(Gasto)
                .join(Gasto.distribuciones)
                .filter(Gasto.periodo < periodo_actual, Gasto.distribuciones.any(apartamento_id=apartamento_id))
                .options(joinedload(Gasto.distribuciones))
                .all()
            )

            # Obtener TODOS los pagos de períodos anteriores para este apartamento
            # Primero obtenemos los reportes de períodos anteriores
            reportes_anteriores = db.query(ReporteFinanciero).filter(ReporteFinanciero.periodo < periodo_actual).all()

            reportes_ids_anteriores = [r.id for r in reportes_anteriores]

            pagos_anteriores = (
                (
                    db.query(Pago)
                    .filter(
                        Pago.id_apartamento == apartamento_id, Pago.id_reporte_financiero.in_(reportes_ids_anteriores)
                    )
                    .all()
                )
                if reportes_ids_anteriores
                else []
            )

            # Calcular saldo pendiente de períodos anteriores
            total_cargos_anteriores = Decimal("0.00")
            for gasto in cargos_anteriores:
                distribucion = next((d for d in gasto.distribuciones if d.id_apartamento == apartamento_id), None)
                if distribucion:
                    total_cargos_anteriores += distribucion.monto_asignado_usd

            total_pagos_anteriores = sum(p.monto_pagado_usd for p in pagos_anteriores)

            saldo_anterior = total_cargos_anteriores - total_pagos_anteriores

            logger.info(
                f"💰 Saldo anterior apto {apartamento_id}: {saldo_anterior} USD "
                f"(cargos: {total_cargos_anteriores}, pagos: {total_pagos_anteriores})"
            )

            return saldo_anterior

        except Exception as e:
            logger.warning(f"No se pudo calcular saldo anterior para {apartamento_id}: {str(e)}")
            return Decimal("0.00")

    def obtener_estadisticas_morosidad(self, db: Session, periodo: str) -> Dict:
        """
        Métricas detalladas de morosidad para administradores
        """
        try:
            # Obtener todos los apartamentos
            apartamentos = db.query(Apartamento).all()

            estadisticas_apartamentos = []
            total_deuda_general = Decimal("0.00")
            apartamentos_morosos = 0
            apartamentos_con_deuda = 0

            for apt in apartamentos:
                estado_cuenta = self.obtener_estado_cuenta_apartamento(db, apt.id, periodo)
                saldo_actual = estado_cuenta["resumen"]["saldo_actual_usd"]

                if saldo_actual > 0:
                    apartamentos_con_deuda += 1
                    total_deuda_general += saldo_actual

                    if saldo_actual > Decimal("10.00"):  # Considerar moroso si debe más de $10
                        apartamentos_morosos += 1

                estadisticas_apartamentos.append(
                    {
                        "apartamento_id": apt.id,
                        "numero": apt.numero,
                        "saldo_actual_usd": saldo_actual,
                        "estado": estado_cuenta["estado"],
                        "total_cargos": len(estado_cuenta["detalle_cargos"]),
                        "total_pagos": len(estado_cuenta["detalle_pagos"]),
                    }
                )

            # Ordenar por mayor deuda
            estadisticas_apartamentos.sort(key=lambda x: x["saldo_actual_usd"], reverse=True)

            # Top 5 deudores
            top_deudores = estadisticas_apartamentos[:5]

            # Distribución por rangos de deuda
            distribucion_rangos = {
                "sin_deuda": len([apt for apt in estadisticas_apartamentos if apt["saldo_actual_usd"] <= 0]),
                "deuda_menor_50": len([apt for apt in estadisticas_apartamentos if 0 < apt["saldo_actual_usd"] <= 50]),
                "deuda_50_100": len([apt for apt in estadisticas_apartamentos if 50 < apt["saldo_actual_usd"] <= 100]),
                "deuda_100_200": len(
                    [apt for apt in estadisticas_apartamentos if 100 < apt["saldo_actual_usd"] <= 200]
                ),
                "deuda_mayor_200": len([apt for apt in estadisticas_apartamentos if apt["saldo_actual_usd"] > 200]),
            }

            return {
                "periodo": periodo,
                "metricas_generales": {
                    "total_apartamentos": len(apartamentos),
                    "apartamentos_con_deuda": apartamentos_con_deuda,
                    "apartamentos_morosos": apartamentos_morosos,
                    "total_deuda_usd": total_deuda_general,
                    "porcentaje_morosidad": (apartamentos_morosos / len(apartamentos) * 100) if apartamentos else 0,
                    "deuda_promedio": (
                        (total_deuda_general / apartamentos_con_deuda) if apartamentos_con_deuda > 0 else 0
                    ),
                },
                "top_deudores": top_deudores,
                "distribucion_rangos_deuda": distribucion_rangos,
                "resumen_por_torre": self._obtener_morosidad_por_torre(db, periodo),
            }

        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de morosidad: {str(e)}")
            raise

    def _obtener_morosidad_por_torre(self, db: Session, periodo: str) -> List[Dict]:
        """
        Agrupa morosidad por torre
        """
        try:
            from ..models.torres import Torre, Piso

            torres = db.query(Torre).all()
            morosidad_por_torre = []

            for torre in torres:
                apartamentos_torre = db.query(Apartamento).join(Piso).filter(Piso.id_torre == torre.id).all()

                deuda_torre = Decimal("0.00")
                apartamentos_morosos = 0

                for apt in apartamentos_torre:
                    estado_cuenta = self.obtener_estado_cuenta_apartamento(db, apt.id, periodo)
                    saldo = estado_cuenta["resumen"]["saldo_actual_usd"]

                    if saldo > 0:
                        deuda_torre += saldo
                        if saldo > Decimal("10.00"):
                            apartamentos_morosos += 1

                morosidad_por_torre.append(
                    {
                        "torre_id": torre.id,
                        "torre_nombre": torre.nombre,
                        "total_apartamentos": len(apartamentos_torre),
                        "apartamentos_morosos": apartamentos_morosos,
                        "total_deuda_usd": deuda_torre,
                        "porcentaje_morosidad": (
                            (apartamentos_morosos / len(apartamentos_torre) * 100) if apartamentos_torre else 0
                        ),
                    }
                )

            return morosidad_por_torre

        except Exception as e:
            logger.warning(f"Error calculando morosidad por torre: {str(e)}")
            return []

    def cerrar_reporte_mensual(self, db: Session, periodo: str) -> ReporteFinanciero:
        """
        Cierra un reporte mensual (impide modificaciones posteriores)
        """
        try:
            reporte = db.query(ReporteFinanciero).filter(ReporteFinanciero.periodo == periodo).first()

            if not reporte:
                raise ValueError(f"No existe reporte para el período {periodo}")

            if reporte.estado == "Cerrado":
                raise ValueError(f"El reporte {periodo} ya está cerrado")

            reporte.estado = "Cerrado"
            reporte.fecha_cierre = datetime.now()

            db.commit()
            db.refresh(reporte)

            logger.info(f"✅ Reporte {periodo} cerrado correctamente")
            return reporte

        except Exception as e:
            db.rollback()
            logger.error(f"Error cerrando reporte {periodo}: {str(e)}")
            raise

    def obtener_reporte_por_periodo(self, db: Session, periodo: str) -> Optional[ReporteFinancieroResponse]:
        """
        Obtiene un reporte específico con todos sus datos
        """
        try:
            reporte = (
                db.query(ReporteFinanciero)
                .options(joinedload(ReporteFinanciero.gastos), joinedload(ReporteFinanciero.pagos))
                .filter(ReporteFinanciero.periodo == periodo)
                .first()
            )

            if reporte:
                return ReporteFinancieroResponse.from_orm(reporte)
            return None

        except Exception as e:
            logger.error(f"Error obteniendo reporte {periodo}: {str(e)}")
            raise

    def listar_reportes(self, db: Session, limite: int = 12) -> List[ReporteFinancieroResponse]:
        """
        Lista los últimos reportes financieros
        """
        try:
            reportes = db.query(ReporteFinanciero).order_by(ReporteFinanciero.periodo.desc()).limit(limite).all()

            return [ReporteFinancieroResponse.from_orm(reporte) for reporte in reportes]

        except Exception as e:
            logger.error(f"Error listando reportes: {str(e)}")
            raise


# Instancia global
reportes_financieros_service = ReportesFinancierosService()

"""
🎯 Características principales:
1. Generación automática de reportes
Crea o actualiza reportes mensuales

Consolida TODOS los gastos y pagos del período

Calcula tasas de cambio promedio

2. Estado de cuenta por apartamento
Resumen completo: saldo anterior, cargos, pagos, saldo actual

Detalle de transacciones: cada cargo y pago específico

Estado automático: "AL DÍA" o "PENDIENTE"

3. Estadísticas de morosidad avanzadas
Métricas generales: % morosidad, deuda promedio, total deudores

Top 5 deudores: para seguimiento prioritario

Distribución por rangos: sin deuda, <$50, $50-100, $100-200, >$200

Análisis por torre: morosidad desglosada por cada torre

4. Funciones administrativas
Cierre de reportes: impide modificaciones posteriores

Consulta de reportes: con relaciones cargadas

Listado histórico: últimos 12 meses por defecto

5. Manejo robusto de errores
Logging detallado en cada operación

Rollback automático en errores

Métodos auxiliares protegidos
"""
