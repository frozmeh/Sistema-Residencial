# services/dashboard_service.py
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import date, datetime, timedelta
import logging
from sqlalchemy import func, and_

from ..models.financiero import Gasto, Pago, ReporteFinanciero, Cargo, EstadoCargoEnum, EstadoGastoEnum
from ..models.torres import Apartamento, Residente, Torre
from .reportes_financieros_service import reportes_financieros_service
from .deudas_service import deudas_service
from .cargos_service import cargos_service

logger = logging.getLogger(__name__)


class DashboardService:

    def obtener_metricas_administrativas(self, db: Session) -> Dict:
        """
        Métricas RÁPIDAS para el dashboard del administrador
        """
        try:
            periodo_actual = datetime.now().strftime("%Y-%m")

            # 1. Métricas Financieras
            metricas_financieras = self._obtener_metricas_financieras(db, periodo_actual)

            # 2. Métricas de Morosidad
            metricas_morosidad = self._obtener_metricas_morosidad(db, periodo_actual)

            # 3. Métricas de Residentes
            metricas_residentes = self._obtener_metricas_residentes(db)

            # 4. Alertas y Recordatorios
            alertas = self._obtener_alertas_administrativas(db)

            return {
                "periodo_actual": periodo_actual,
                "fecha_actualizacion": datetime.now(),
                "financiero": metricas_financieras,
                "morosidad": metricas_morosidad,
                "residentes": metricas_residentes,
                "alertas": alertas,
                "resumen_torres": self._obtener_resumen_torres(db),
            }

        except Exception as e:
            logger.error(f"Error obteniendo métricas administrativas: {str(e)}")
            raise

    def _obtener_metricas_financieras(self, db: Session, periodo_actual: str) -> Dict:
        """Métricas financieras del mes actual"""
        try:
            # Obtener reporte actual o calcular en tiempo real
            reporte_actual = db.query(ReporteFinanciero).filter(ReporteFinanciero.periodo == periodo_actual).first()

            if reporte_actual:
                # Usar reporte existente
                ingresos_usd = reporte_actual.total_ingresos_usd
                gastos_usd = reporte_actual.total_gastos_usd
                saldo_usd = reporte_actual.saldo_final_usd
            else:
                # Calcular en tiempo real
                ingresos_usd = db.query(func.sum(Pago.monto_pagado_usd)).filter(
                    Pago.reporte_financiero.has(periodo=periodo_actual)
                ).scalar() or Decimal("0.00")

                gastos_usd = db.query(func.sum(Gasto.monto_total_usd)).filter(
                    Gasto.periodo == periodo_actual
                ).scalar() or Decimal("0.00")

                saldo_usd = ingresos_usd - gastos_usd

            # Gastos por tipo
            gastos_por_tipo = (
                db.query(Gasto.tipo_gasto, func.sum(Gasto.monto_total_usd))
                .filter(Gasto.periodo == periodo_actual)
                .group_by(Gasto.tipo_gasto)
                .all()
            )

            # Proyección mensual (basado en día del mes)
            hoy = date.today()
            dias_en_mes = 30  # Simplificado
            dia_actual = hoy.day
            factor_proyeccion = dias_en_mes / dia_actual if dia_actual > 0 else 1

            return {
                "ingresos_mes_actual_usd": ingresos_usd,
                "gastos_mes_actual_usd": gastos_usd,
                "saldo_actual_usd": saldo_usd,
                "proyeccion_ingresos_mensual_usd": ingresos_usd * factor_proyeccion,
                "gastos_por_tipo": {tipo: monto for tipo, monto in gastos_por_tipo},
                "tendencia": self._calcular_tendencia_financiera(db, periodo_actual),
            }

        except Exception as e:
            logger.error(f"Error calculando métricas financieras: {str(e)}")
            return {
                "ingresos_mes_actual_usd": Decimal("0.00"),
                "gastos_mes_actual_usd": Decimal("0.00"),
                "saldo_actual_usd": Decimal("0.00"),
                "proyeccion_ingresos_mensual_usd": Decimal("0.00"),
                "gastos_por_tipo": {},
                "tendencia": "estable",
            }

    def _obtener_metricas_morosidad(self, db: Session, periodo_actual: str) -> Dict:
        """Métricas de morosidad resumidas"""
        try:
            # Usar deudas_service para obtener morosidad
            morosidad_condominio = deudas_service.obtener_morosidad_condominio(db)

            # Cargos vencidos (críticos)
            cargos_vencidos = db.query(Cargo).filter(Cargo.estado == EstadoCargoEnum.VENCIDO).count()

            # Cargos próximos a vencer (esta semana)
            fecha_limite = date.today() + timedelta(days=7)
            cargos_proximos_vencer = (
                db.query(Cargo)
                .filter(
                    Cargo.estado.in_([EstadoCargoEnum.PENDIENTE, EstadoCargoEnum.PARCIAL]),
                    Cargo.fecha_vencimiento <= fecha_limite,
                )
                .count()
            )

            return {
                "porcentaje_morosidad": morosidad_condominio.get("metricas_generales", {}).get(
                    "porcentaje_morosidad", 0
                ),
                "total_deuda_condominio_usd": morosidad_condominio.get("metricas_generales", {}).get(
                    "total_deuda_condominio_usd", 0
                ),
                "apartamentos_morosos": morosidad_condominio.get("metricas_generales", {}).get(
                    "apartamentos_morosos", 0
                ),
                "cargos_vencidos_criticos": cargos_vencidos,
                "cargos_proximos_vencer": cargos_proximos_vencer,
                "alerta_nivel": self._determinar_nivel_alerta_morosidad(
                    morosidad_condominio.get("metricas_generales", {}).get("porcentaje_morosidad", 0)
                ),
            }

        except Exception as e:
            logger.error(f"Error calculando métricas de morosidad: {str(e)}")
            return {
                "porcentaje_morosidad": 0,
                "total_deuda_condominio_usd": Decimal("0.00"),
                "apartamentos_morosos": 0,
                "cargos_vencidos_criticos": 0,
                "cargos_proximos_vencer": 0,
                "alerta_nivel": "bajo",
            }

    def _obtener_metricas_residentes(self, db: Session) -> Dict:
        """Métricas de residentes y ocupación"""
        try:
            total_apartamentos = db.query(Apartamento).count()
            apartamentos_ocupados = db.query(Apartamento).filter(Apartamento.estado == "Ocupado").count()

            total_residentes = db.query(Residente).count()
            residentes_activos = db.query(Residente).filter(Residente.estado_operativo == "Activo").count()

            residentes_aprobados = db.query(Residente).filter(Residente.estado_aprobacion == "Aprobado").count()

            residentes_pendientes = (
                db.query(Residente)
                .filter(Residente.estado_aprobacion.in_(["Pendiente", "Corrección Requerida"]))
                .count()
            )

            return {
                "total_apartamentos": total_apartamentos,
                "apartamentos_ocupados": apartamentos_ocupados,
                "tasa_ocupacion": (apartamentos_ocupados / total_apartamentos * 100) if total_apartamentos > 0 else 0,
                "total_residentes": total_residentes,
                "residentes_activos": residentes_activos,
                "residentes_aprobados": residentes_aprobados,
                "residentes_pendientes_aprobacion": residentes_pendientes,
            }

        except Exception as e:
            logger.error(f"Error calculando métricas de residentes: {str(e)}")
            return {
                "total_apartamentos": 0,
                "apartamentos_ocupados": 0,
                "tasa_ocupacion": 0,
                "total_residentes": 0,
                "residentes_activos": 0,
                "residentes_aprobados": 0,
                "residentes_pendientes_aprobacion": 0,
            }

    def _obtener_alertas_administrativas(self, db: Session) -> List[Dict]:
        """Alertas importantes para el administrador"""
        alertas = []

        try:
            # 1. Gastos pendientes de distribución
            gastos_pendientes = db.query(Gasto).filter(Gasto.estado == EstadoGastoEnum.PENDIENTE).count()

            if gastos_pendientes > 0:
                alertas.append(
                    {
                        "tipo": "gastos_pendientes",
                        "nivel": "medio",
                        "titulo": "Gastos pendientes de distribución",
                        "mensaje": f"{gastos_pendientes} gastos esperando distribución",
                        "accion": "revisar_gastos",
                    }
                )

            # 2. Pagos pendientes de validación
            from ..models.financiero import EstadoPagoEnum

            pagos_pendientes = db.query(Pago).filter(Pago.estado == EstadoPagoEnum.PENDIENTE).count()

            if pagos_pendientes > 0:
                alertas.append(
                    {
                        "tipo": "pagos_pendientes",
                        "nivel": "alto",
                        "titulo": "Pagos pendientes de validación",
                        "mensaje": f"{pagos_pendientes} pagos esperando aprobación",
                        "accion": "validar_pagos",
                    }
                )

            # 3. Cargos vencidos críticos
            cargos_vencidos = db.query(Cargo).filter(Cargo.estado == EstadoCargoEnum.VENCIDO).count()

            if cargos_vencidos > 5:  # Umbral para alerta
                alertas.append(
                    {
                        "tipo": "cargos_vencidos",
                        "nivel": "critico",
                        "titulo": "Cargos vencidos",
                        "mensaje": f"{cargos_vencidos} cargos con vencimiento crítico",
                        "accion": "revisar_morosidad",
                    }
                )

            # 4. Reporte mensual pendiente
            periodo_actual = datetime.now().strftime("%Y-%m")
            reporte_actual = db.query(ReporteFinanciero).filter(ReporteFinanciero.periodo == periodo_actual).first()

            if not reporte_actual:
                alertas.append(
                    {
                        "tipo": "reporte_pendiente",
                        "nivel": "bajo",
                        "titulo": "Reporte mensual pendiente",
                        "mensaje": "Generar reporte financiero del mes actual",
                        "accion": "generar_reporte",
                    }
                )

            return alertas

        except Exception as e:
            logger.error(f"Error obteniendo alertas: {str(e)}")
            return []

    def _obtener_resumen_torres(self, db: Session) -> List[Dict]:
        """Resumen por torre para vista rápida"""
        try:
            torres = db.query(Torre).all()
            resumen = []

            for torre in torres:
                # Contar apartamentos por torre
                total_apartamentos = (
                    db.query(Apartamento)
                    .join(Apartamento.piso)
                    .filter(Apartamento.piso.has(id_torre=torre.id))
                    .count()
                )

                apartamentos_ocupados = (
                    db.query(Apartamento)
                    .join(Apartamento.piso)
                    .filter(Apartamento.piso.has(id_torre=torre.id), Apartamento.estado == "Ocupado")
                    .count()
                )

                resumen.append(
                    {
                        "torre_id": torre.id,
                        "torre_nombre": torre.nombre,
                        "total_apartamentos": total_apartamentos,
                        "apartamentos_ocupados": apartamentos_ocupados,
                        "tasa_ocupacion": (
                            (apartamentos_ocupados / total_apartamentos * 100) if total_apartamentos > 0 else 0
                        ),
                    }
                )

            return resumen

        except Exception as e:
            logger.error(f"Error obteniendo resumen de torres: {str(e)}")
            return []

    def _calcular_tendencia_financiera(self, db: Session, periodo_actual: str) -> str:
        """Calcula tendencia financiera vs mes anterior"""
        try:
            # Obtener período anterior
            año, mes = map(int, periodo_actual.split("-"))
            if mes == 1:
                periodo_anterior = f"{año-1}-12"
            else:
                periodo_anterior = f"{año}-{mes-1:02d}"

            # Saldo actual
            saldo_actual = self._obtener_saldo_periodo(db, periodo_actual)

            # Saldo anterior
            saldo_anterior = self._obtener_saldo_periodo(db, periodo_anterior)

            if saldo_anterior == 0:
                return "estable"

            variacion = ((saldo_actual - saldo_anterior) / saldo_anterior) * 100

            if variacion > 10:
                return "mejorando"
            elif variacion < -10:
                return "empeorando"
            else:
                return "estable"

        except Exception as e:
            logger.warning(f"Error calculando tendencia: {str(e)}")
            return "estable"

    def _obtener_saldo_periodo(self, db: Session, periodo: str) -> Decimal:
        """Obtiene saldo de un período específico"""
        reporte = db.query(ReporteFinanciero).filter(ReporteFinanciero.periodo == periodo).first()

        if reporte:
            return reporte.saldo_final_usd

        # Calcular en tiempo real si no existe reporte
        ingresos = db.query(func.sum(Pago.monto_pagado_usd)).filter(
            Pago.reporte_financiero.has(periodo=periodo)
        ).scalar() or Decimal("0.00")

        gastos = db.query(func.sum(Gasto.monto_total_usd)).filter(Gasto.periodo == periodo).scalar() or Decimal("0.00")

        return ingresos - gastos

    def _determinar_nivel_alerta_morosidad(self, porcentaje_morosidad: float) -> str:
        """Determina nivel de alerta basado en porcentaje de morosidad"""
        if porcentaje_morosidad > 20:
            return "critico"
        elif porcentaje_morosidad > 10:
            return "alto"
        elif porcentaje_morosidad > 5:
            return "medio"
        else:
            return "bajo"

    def obtener_dashboard_residente(self, db: Session, residente_id: int) -> Dict:
        """
        Dashboard personalizado para residentes
        """
        try:
            # Obtener residente y su apartamento
            residente = db.query(Residente).filter(Residente.id == residente_id).first()
            if not residente or not residente.id_apartamento:
                raise ValueError("Residente no encontrado o sin apartamento asignado")

            apartamento_id = residente.id_apartamento
            periodo_actual = datetime.now().strftime("%Y-%m")

            # Obtener resumen de deudas
            resumen_deudas = deudas_service.obtener_resumen_deudas_apartamento(db, apartamento_id)

            # Obtener cargos pendientes
            cargos_pendientes = cargos_service.obtener_cargos_pendientes(db, apartamento_id)

            # Obtener estado de cuenta actual
            estado_cuenta = reportes_financieros_service.obtener_estado_cuenta_apartamento(
                db, apartamento_id, periodo_actual
            )

            return {
                "residente": {
                    "id": residente.id,
                    "nombre": residente.nombre,
                    "apartamento": residente.apartamento.numero if residente.apartamento else "No asignado",
                },
                "resumen_financiero": resumen_deudas.get("resumen", {}),
                "alertas": resumen_deudas.get("alertas", {}),
                "cargos_pendientes": [
                    {
                        "id": cargo.id,
                        "descripcion": cargo.descripcion,
                        "monto_usd": cargo.saldo_pendiente_usd,
                        "fecha_vencimiento": cargo.fecha_vencimiento,
                        "estado": cargo.estado.value,
                        "dias_para_vencer": (cargo.fecha_vencimiento - date.today()).days,
                    }
                    for cargo in cargos_pendientes
                ],
                "estado_cuenta_actual": estado_cuenta,
                "ultimos_pagos": self._obtener_ultimos_pagos_residente(db, apartamento_id, limite=5),
            }

        except Exception as e:
            logger.error(f"Error obteniendo dashboard para residente {residente_id}: {str(e)}")
            raise

    def _obtener_ultimos_pagos_residente(self, db: Session, apartamento_id: int, limite: int = 5) -> List[Dict]:
        """Obtiene los últimos pagos del residente"""
        try:
            pagos = (
                db.query(Pago)
                .filter(Pago.id_apartamento == apartamento_id)
                .order_by(Pago.fecha_creacion.desc())
                .limit(limite)
                .all()
            )

            return [
                {
                    "id": pago.id,
                    "fecha": pago.fecha_creacion.date(),
                    "monto_usd": pago.monto_pagado_usd,
                    "concepto": pago.concepto,
                    "estado": pago.estado.value,
                    "metodo": pago.metodo.value,
                }
                for pago in pagos
            ]
        except Exception as e:
            logger.warning(f"Error obteniendo últimos pagos: {str(e)}")
            return []


# Instancia global
dashboard_service = DashboardService()
"""
🎯 Este dashboard service proporciona:
Para Administradores:
📊 Métricas financieras en tiempo real

⚠️ Alertas de morosidad con niveles de prioridad

👥 Estadísticas de residentes y ocupación

🏢 Resumen por torres

📈 Tendencias vs mes anterior

Para Residentes:
💰 Resumen de deudas personalizado

📋 Cargos pendientes con fechas de vencimiento

✅ Historial de pagos recientes

🚨 Alertas personales (vencimientos próximos)

Características técnicas:
✅ Reutiliza servicios existentes (deudas_service, reportes_financieros_service)

✅ Manejo robusto de errores

✅ Cálculos en tiempo real si no hay reportes

✅ Métricas contextuales (tendencias, proyecciones)
"""
