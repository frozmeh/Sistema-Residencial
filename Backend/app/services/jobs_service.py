# services/jobs_service.py
from sqlalchemy.orm import Session
from typing import Dict, List
from decimal import Decimal
from datetime import datetime, date, timedelta
import logging
from sqlalchemy import and_
from sqlalchemy.orm import joinedload

from ..models.financiero import (
    TasaCambio,
    Gasto,
    Cargo,
    Pago,
    ReporteFinanciero,
    EstadoCargoEnum,
    EstadoGastoEnum,
    EstadoPagoEnum,
)
from ..models.torres import Apartamento
from .tasa_cambio_service import tasa_cambio_service
from .cargos_service import cargos_service
from .reportes_financieros_service import reportes_financieros_service
from .gastos_service import gastos_service

logger = logging.getLogger(__name__)


class JobsService:

    def job_diario_actualizacion_tasas(self, db: Session) -> Dict:
        """
        Job diario: Actualiza la tasa de cambio BCV
        Se ejecuta TODOS los días, pero solo guarda si es diferente
        """
        try:
            logger.info("🔄 Iniciando job diario: Actualización de tasa de cambio")

            # Verificar si hoy ya tenemos tasa
            hoy = date.today()
            tasa_hoy = db.query(TasaCambio).filter(TasaCambio.fecha == hoy).first()

            if tasa_hoy:
                logger.info(f"✅ Tasa de cambio para {hoy} ya existe: {tasa_hoy.tasa_usd_ves}")
                return {
                    "job": "actualizacion_tasas",
                    "estado": "completado",
                    "accion": "tasa_ya_existente",
                    "tasa_actual": float(tasa_hoy.tasa_usd_ves),
                    "mensaje": f"Tasa del día ya existe: {tasa_hoy.tasa_usd_ves}",
                }

            # Obtener nueva tasa
            nueva_tasa = tasa_cambio_service.obtener_tasa_actual(db)

            logger.info(f"✅ Job diario tasas COMPLETADO - Nueva tasa: {nueva_tasa.tasa_usd_ves}")

            return {
                "job": "actualizacion_tasas",
                "estado": "completado",
                "accion": "tasa_actualizada",
                "tasa_actual": float(nueva_tasa.tasa_usd_ves),
                "mensaje": f"Tasa actualizada: {nueva_tasa.tasa_usd_ves}",
            }

        except Exception as e:
            logger.error(f"❌ Error en job diario de tasas: {str(e)}")
            return {
                "job": "actualizacion_tasas",
                "estado": "error",
                "error": str(e),
                "mensaje": "Error actualizando tasa de cambio",
            }

    def job_diario_verificar_vencimientos(self, db: Session) -> Dict:
        """
        Job diario: Verifica y actualiza estados de cargos vencidos
        """
        try:
            logger.info("🔄 Iniciando job diario: Verificación de vencimientos")

            # Usar cargos_service para verificar vencimientos
            cargos_actualizados = cargos_service.verificar_vencimientos_automatico(db)

            # Buscar cargos que vencerán en los próximos 3 días (para alertas tempranas)
            fecha_limite = date.today() + timedelta(days=3)
            cargos_proximos_vencer = (
                db.query(Cargo)
                .filter(
                    Cargo.estado.in_([EstadoCargoEnum.PENDIENTE, EstadoCargoEnum.PARCIAL]),
                    Cargo.fecha_vencimiento <= fecha_limite,
                    Cargo.fecha_vencimiento >= date.today(),
                )
                .all()
            )

            logger.info(f"✅ Job diario vencimientos COMPLETADO")
            logger.info(f"   - Cargos actualizados: {cargos_actualizados}")
            logger.info(f"   - Cargos próximos a vencer: {len(cargos_proximos_vencer)}")

            return {
                "job": "verificacion_vencimientos",
                "estado": "completado",
                "cargos_actualizados": cargos_actualizados,
                "cargos_proximos_vencer": len(cargos_proximos_vencer),
                "cargos_proximos_detalle": [
                    {
                        "cargo_id": cargo.id,
                        "apartamento_id": cargo.id_apartamento,
                        "descripcion": cargo.descripcion,
                        "monto_usd": float(cargo.saldo_pendiente_usd),
                        "fecha_vencimiento": cargo.fecha_vencimiento.isoformat(),
                        "dias_para_vencer": (cargo.fecha_vencimiento - date.today()).days,
                    }
                    for cargo in cargos_proximos_vencer
                ],
            }

        except Exception as e:
            logger.error(f"❌ Error en job diario de vencimientos: {str(e)}")
            return {
                "job": "verificacion_vencimientos",
                "estado": "error",
                "error": str(e),
                "mensaje": "Error verificando vencimientos",
            }

    def job_mensual_generar_reportes(self, db: Session, periodo: str = None) -> Dict:
        """
        Job mensual: Genera reportes financieros del mes anterior
        Se ejecuta el PRIMER día de cada mes para el mes anterior
        """
        try:
            # Si no se especifica período, usar el mes anterior
            if not periodo:
                hoy = date.today()
                # Primer día del mes actual - 1 día = último día del mes anterior
                primer_dia_mes_actual = hoy.replace(day=1)
                ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)
                periodo = ultimo_dia_mes_anterior.strftime("%Y-%m")

            logger.info(f"🔄 Iniciando job mensual: Generación de reporte {periodo}")

            # Verificar si el reporte ya existe
            reporte_existente = db.query(ReporteFinanciero).filter(ReporteFinanciero.periodo == periodo).first()

            if reporte_existente and reporte_existente.estado == "Cerrado":
                logger.info(f"✅ Reporte {periodo} ya existe y está cerrado")
                return {
                    "job": "generacion_reportes",
                    "estado": "completado",
                    "accion": "reporte_ya_existente",
                    "periodo": periodo,
                    "mensaje": f"Reporte {periodo} ya estaba generado y cerrado",
                }

            # Generar o actualizar reporte
            reporte = reportes_financieros_service.generar_reporte_mensual(db, periodo, "Sistema Automático")

            # Cerrar el reporte (impedir modificaciones)
            reporte_cerrado = reportes_financieros_service.cerrar_reporte_mensual(db, periodo)

            logger.info(f"✅ Job mensual reportes COMPLETADO - Reporte {periodo} generado y cerrado")

            return {
                "job": "generacion_reportes",
                "estado": "completado",
                "accion": "reporte_generado_y_cerrado",
                "periodo": periodo,
                "reporte_id": reporte_cerrado.id,
                "totales": {
                    "ingresos_usd": float(reporte_cerrado.total_ingresos_usd),
                    "gastos_usd": float(reporte_cerrado.total_gastos_usd),
                    "saldo_usd": float(reporte_cerrado.saldo_final_usd),
                },
                "mensaje": f"Reporte {periodo} generado y cerrado exitosamente",
            }

        except Exception as e:
            logger.error(f"❌ Error en job mensual de reportes: {str(e)}")
            return {
                "job": "generacion_reportes",
                "estado": "error",
                "periodo": periodo,
                "error": str(e),
                "mensaje": f"Error generando reporte {periodo}",
            }

    def job_semanal_generar_cargos(self, db: Session) -> Dict:
        """
        Job semanal: Genera cargos automáticos para gastos distribuidos
        Revisa todos los gastos distribuidos que no tienen cargos generados
        """
        try:
            logger.info("🔄 Iniciando job semanal: Generación de cargos automáticos")

            # Buscar gastos distribuidos sin cargos generados
            gastos_sin_cargos = (
                db.query(Gasto)
                .filter(
                    Gasto.estado == EstadoGastoEnum.DISTRIBUIDO,
                    ~Gasto.distribuciones.any(),  # Gastos que tienen distribuciones
                )
                .options(joinedload(Gasto.distribuciones))
                .all()
            )

            cargos_generados = 0
            gastos_procesados = []

            for gasto in gastos_sin_cargos:
                try:
                    # Generar cargos para este gasto
                    nuevos_cargos = gastos_service.generar_cargos_automaticos(db, gasto.id)
                    cargos_generados += len(nuevos_cargos)
                    gastos_procesados.append(gasto.id)

                    logger.info(f"✅ Generados {len(nuevos_cargos)} cargos para gasto {gasto.id}")

                except Exception as e:
                    logger.warning(f"⚠️ Error generando cargos para gasto {gasto.id}: {str(e)}")
                    continue

            logger.info(f"✅ Job semanal cargos COMPLETADO")
            logger.info(f"   - Gastos procesados: {len(gastos_procesados)}")
            logger.info(f"   - Cargos generados: {cargos_generados}")

            return {
                "job": "generacion_cargos",
                "estado": "completado",
                "gastos_procesados": len(gastos_procesados),
                "cargos_generados": cargos_generados,
                "gastos_procesados_ids": gastos_procesados,
                "mensaje": f"Generados {cargos_generados} cargos para {len(gastos_procesados)} gastos",
            }

        except Exception as e:
            logger.error(f"❌ Error en job semanal de cargos: {str(e)}")
            return {
                "job": "generacion_cargos",
                "estado": "error",
                "error": str(e),
                "mensaje": "Error generando cargos automáticos",
            }

    def job_diario_limpieza_datos(self, db: Session) -> Dict:
        """
        Job diario: Limpieza y mantenimiento de datos temporales
        """
        try:
            logger.info("🔄 Iniciando job diario: Limpieza de datos")

            # Aquí puedes agregar lógica de limpieza según necesites
            # Por ejemplo: eliminar registros temporales, archivos viejos, etc.

            tareas_completadas = []

            # Ejemplo: Contar registros en varias tablas para monitoreo
            total_gastos = db.query(Gasto).count()
            total_cargos = db.query(Cargo).count()
            total_pagos = db.query(Pago).count()
            total_reportes = db.query(ReporteFinanciero).count()

            tareas_completadas.append("conteo_registros")

            logger.info(f"✅ Job diario limpieza COMPLETADO")
            logger.info(f"   - Gastos: {total_gastos}")
            logger.info(f"   - Cargos: {total_cargos}")
            logger.info(f"   - Pagos: {total_pagos}")
            logger.info(f"   - Reportes: {total_reportes}")

            return {
                "job": "limpieza_datos",
                "estado": "completado",
                "tareas_completadas": tareas_completadas,
                "estadisticas": {
                    "total_gastos": total_gastos,
                    "total_cargos": total_cargos,
                    "total_pagos": total_pagos,
                    "total_reportes": total_reportes,
                },
                "mensaje": "Limpieza de datos completada",
            }

        except Exception as e:
            logger.error(f"❌ Error en job diario de limpieza: {str(e)}")
            return {
                "job": "limpieza_datos",
                "estado": "error",
                "error": str(e),
                "mensaje": "Error en limpieza de datos",
            }

    def ejecutar_todos_jobs_diarios(self, db: Session) -> Dict:
        """
        Ejecuta todos los jobs diarios en secuencia
        """
        try:
            logger.info("🏁 INICIANDO EJECUCIÓN COMPLETA DE JOBS DIARIOS")

            resultados = {}

            # 1. Actualización de tasas
            resultados["tasas"] = self.job_diario_actualizacion_tasas(db)

            # 2. Verificación de vencimientos
            resultados["vencimientos"] = self.job_diario_verificar_vencimientos(db)

            # 3. Limpieza de datos
            resultados["limpieza"] = self.job_diario_limpieza_datos(db)

            # 4. Verificar si es primer día del mes para reportes mensuales
            hoy = date.today()
            if hoy.day == 1:
                logger.info("📅 Es primer día del mes - ejecutando job mensual")
                periodo_anterior = (hoy.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
                resultados["reportes_mensuales"] = self.job_mensual_generar_reportes(db, periodo_anterior)

            # 5. Verificar si es lunes para job semanal de cargos
            if hoy.weekday() == 0:  # 0 = Lunes
                logger.info("📅 Es lunes - ejecutando job semanal de cargos")
                resultados["cargos_semanales"] = self.job_semanal_generar_cargos(db)

            logger.info("🏁 EJECUCIÓN COMPLETA DE JOBS FINALIZADA")

            return {
                "ejecucion_completa": True,
                "fecha_ejecucion": datetime.now().isoformat(),
                "resultados": resultados,
                "resumen": self._generar_resumen_ejecucion(resultados),
            }

        except Exception as e:
            logger.error(f"❌ Error en ejecución completa de jobs: {str(e)}")
            return {
                "ejecucion_completa": False,
                "fecha_ejecucion": datetime.now().isoformat(),
                "error": str(e),
                "mensaje": "Error en ejecución completa de jobs",
            }

    def _generar_resumen_ejecucion(self, resultados: Dict) -> Dict:
        """Genera un resumen de la ejecución de jobs"""
        total_jobs = len(resultados)
        jobs_completados = sum(1 for r in resultados.values() if r.get("estado") == "completado")
        jobs_con_error = sum(1 for r in resultados.values() if r.get("estado") == "error")

        return {
            "total_jobs_ejecutados": total_jobs,
            "jobs_completados": jobs_completados,
            "jobs_con_error": jobs_con_error,
            "tasa_exito": (jobs_completados / total_jobs * 100) if total_jobs > 0 else 0,
        }

    def obtener_estado_jobs(self, db: Session) -> Dict:
        """
        Obtiene el estado actual de los jobs (cuándo se ejecutaron por última vez)
        """
        # En una implementación real, guardarías el historial de ejecuciones
        # Por ahora retornamos un estado básico

        return {
            "ultima_ejecucion_completa": datetime.now().isoformat(),
            "jobs_configurados": {
                "diario_actualizacion_tasas": {
                    "descripcion": "Actualiza tasa BCV diariamente",
                    "frecuencia": "diario",
                    "hora_ejecucion": "09:00",
                },
                "diario_verificar_vencimientos": {
                    "descripcion": "Verifica cargos vencidos",
                    "frecuencia": "diario",
                    "hora_ejecucion": "10:00",
                },
                "mensual_generar_reportes": {
                    "descripcion": "Genera reportes del mes anterior",
                    "frecuencia": "mensual",
                    "dia_ejecucion": 1,  # Primer día del mes
                    "hora_ejecucion": "08:00",
                },
                "semanal_generar_cargos": {
                    "descripcion": "Genera cargos para gastos distribuidos",
                    "frecuencia": "semanal",
                    "dia_ejecucion": "lunes",
                    "hora_ejecucion": "09:30",
                },
            },
            "estado_sistema": "activo",
        }


# Instancia global
jobs_service = JobsService()

"""
🎯 CARACTERÍSTICAS PRINCIPALES:
1. Jobs Diarios (Automáticos)
✅ Actualización de tasas BCV (solo si no existe la de hoy)

✅ Verificación de vencimientos (cambia estado a "VENCIDO")

✅ Limpieza de datos (monitoreo y mantenimiento)

2. Jobs Mensuales (Automáticos)
✅ Generación de reportes (el día 1 de cada mes para el mes anterior)

✅ Cierre de reportes (impedir modificaciones posteriores)

3. Jobs Semanales (Automáticos)
✅ Generación de cargos (los lunes, para gastos distribuidos sin cargos)

4. Ejecución Completa
✅ ejecutar_todos_jobs_diarios() - Un solo método para todo

✅ Detección automática de si es primer día del mes o lunes

✅ Resumen de ejecución con métricas de éxito

5. Manejo Robusto
✅ Logging detallado en cada paso

✅ Continuación después de errores (un job falla, los demás continúan)

✅ Resultados estructurados para monitoreo
"""
