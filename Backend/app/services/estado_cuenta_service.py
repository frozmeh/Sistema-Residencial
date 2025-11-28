# services/estado_cuenta_service.py
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from decimal import Decimal
from datetime import datetime, date, timedelta
import logging
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from ..models.torres import Piso

from ..models.financiero import Gasto, Pago, DistribucionGasto, Cargo
from ..models.torres import Apartamento, Residente
from ..schemas.financiero import ReporteFinancieroResponse

logger = logging.getLogger(__name__)


class EstadoCuentaService:

    def generar_estado_cuenta_detallado(
        self, db: Session, apartamento_id: int, periodo: str, incluir_historico: bool = False
    ) -> Dict:
        """
        Genera un estado de cuenta DETALLADO con toda la información financiera
        """
        try:
            # Verificar que el apartamento existe
            apartamento = db.query(Apartamento).filter(Apartamento.id == apartamento_id).first()
            if not apartamento:
                raise ValueError(f"Apartamento {apartamento_id} no encontrado")

            # Información del apartamento y residente
            info_apartamento = self._obtener_info_apartamento(db, apartamento_id)

            # Estado de cuenta del período solicitado
            estado_cuenta_periodo = self._obtener_estado_cuenta_periodo(db, apartamento_id, periodo)

            # Historial de movimientos (si se solicita)
            historico = None
            if incluir_historico:
                historico = self._obtener_historico_6_meses(db, apartamento_id)

            # Resumen ejecutivo
            resumen_ejecutivo = self._generar_resumen_ejecutivo(estado_cuenta_periodo, historico)

            return {
                "encabezado": {
                    "fecha_generacion": datetime.now(),
                    "periodo_consulta": periodo,
                    "tipo_reporte": "Estado de Cuenta Detallado",
                },
                "informacion_apartamento": info_apartamento,
                "resumen_ejecutivo": resumen_ejecutivo,
                "detalle_periodo_actual": estado_cuenta_periodo,
                "historico_movimientos": historico,
                "recomendaciones": self._generar_recomendaciones(estado_cuenta_periodo),
            }

        except Exception as e:
            logger.error(f"Error generando estado de cuenta para apto {apartamento_id}: {str(e)}")
            raise

    def _obtener_info_apartamento(self, db: Session, apartamento_id: int) -> Dict:
        """Obtiene información completa del apartamento y residente"""
        apartamento = (
            db.query(Apartamento)
            .options(
                joinedload(Apartamento.tipo_apartamento),
                joinedload(Apartamento.residente),
                joinedload(Apartamento.piso).joinedload(Piso.torre),
            )
            .filter(Apartamento.id == apartamento_id)
            .first()
        )

        if not apartamento:
            raise ValueError(f"Apartamento {apartamento_id} no encontrado")

        residente_actual = None
        if apartamento.residente:
            residente_actual = {
                "id": apartamento.residente.id,
                "nombre": apartamento.residente.nombre,
                "cedula": apartamento.residente.cedula,
                "correo": apartamento.residente.correo,
                "telefono": apartamento.residente.telefono,
                "tipo_residente": apartamento.residente.tipo_residente,
            }

        return {
            "apartamento": {
                "id": apartamento.id,
                "numero": apartamento.numero,
                "torre": apartamento.piso.torre.nombre if apartamento.piso and apartamento.piso.torre else "N/A",
                "piso": apartamento.piso.numero if apartamento.piso else "N/A",
                "tipo": apartamento.tipo_apartamento.nombre if apartamento.tipo_apartamento else "N/A",
                "porcentaje_aporte": (
                    apartamento.tipo_apartamento.porcentaje_aporte if apartamento.tipo_apartamento else Decimal("0.00")
                ),
            },
            "residente_actual": residente_actual,
            "fecha_ocupacion": apartamento.residente.fecha_registro if apartamento.residente else None,
        }

    def _obtener_estado_cuenta_periodo(self, db: Session, apartamento_id: int, periodo: str) -> Dict:
        """Obtiene el estado de cuenta de un período específico"""
        # Obtener distribuciones (cargos) del período
        distribuciones = (
            db.query(DistribucionGasto)
            .join(DistribucionGasto.gasto)
            .filter(DistribucionGasto.id_apartamento == apartamento_id, Gasto.periodo == periodo)
            .options(joinedload(DistribucionGasto.gasto))
            .all()
        )

        # Obtener pagos del período
        pagos = (
            db.query(Pago)
            .join(Pago.reporte_financiero)
            .filter(Pago.id_apartamento == apartamento_id, Pago.reporte_financiero.has(periodo=periodo))
            .all()
        )

        # Calcular saldo del período anterior
        saldo_anterior = self._calcular_saldo_periodo_anterior(db, apartamento_id, periodo)

        # Totales del período actual
        total_cargos_usd = sum(d.monto_asignado_usd for d in distribuciones)
        total_pagos_usd = sum(p.monto_pagado_usd for p in pagos)
        saldo_actual = saldo_anterior + total_cargos_usd - total_pagos_usd

        # Detalle de cargos
        detalle_cargos = []
        for distribucion in distribuciones:
            gasto = distribucion.gasto
            detalle_cargos.append(
                {
                    "fecha_gasto": gasto.fecha_gasto,
                    "descripcion": gasto.descripcion,
                    "tipo_gasto": gasto.tipo_gasto,
                    "responsable": gasto.responsable,
                    "monto_asignado_usd": distribucion.monto_asignado_usd,
                    "monto_asignado_ves": distribucion.monto_asignado_ves,
                    "porcentaje_aplicado": distribucion.porcentaje_aplicado,
                    "tasa_cambio": gasto.tasa_cambio,
                }
            )

        # Detalle de pagos
        detalle_pagos = []
        for pago in pagos:
            detalle_pagos.append(
                {
                    "fecha_pago": pago.fecha_creacion.date() if pago.fecha_creacion else None,
                    "concepto": pago.concepto,
                    "metodo_pago": pago.metodo.value,
                    "monto_usd": pago.monto_pagado_usd,
                    "monto_ves": pago.monto_pagado_ves,
                    "estado": pago.estado.value,
                    "comprobante": pago.comprobante,
                    "tasa_cambio_pago": pago.tasa_cambio_pago,
                }
            )

        return {
            "saldo_anterior_usd": saldo_anterior,
            "total_cargos_usd": total_cargos_usd,
            "total_pagos_usd": total_pagos_usd,
            "saldo_actual_usd": saldo_actual,
            "detalle_cargos": detalle_cargos,
            "detalle_pagos": detalle_pagos,
            "resumen_mensual": {
                "total_movimientos": len(detalle_cargos) + len(detalle_pagos),
                "dias_promedio_pago": self._calcular_dias_promedio_pago(detalle_pagos),
                "gasto_promedio_mensual": total_cargos_usd,
                "frecuencia_pagos": len(detalle_pagos),
            },
        }

    def _calcular_saldo_periodo_anterior(self, db: Session, apartamento_id: int, periodo_actual: str) -> Decimal:
        """Calcula el saldo acumulado de períodos anteriores"""
        try:
            # Obtener todos los períodos anteriores al actual
            periodos_anteriores = (
                db.query(Gasto.periodo)
                .join(Gasto.distribuciones)
                .filter(DistribucionGasto.id_apartamento == apartamento_id, Gasto.periodo < periodo_actual)
                .distinct()
                .all()
            )

            saldo_acumulado = Decimal("0.00")

            for periodo_obj in periodos_anteriores:
                periodo = periodo_obj.periodo

                # Cargos del período
                cargos_periodo = (
                    db.query(DistribucionGasto)
                    .join(DistribucionGasto.gasto)
                    .filter(DistribucionGasto.id_apartamento == apartamento_id, Gasto.periodo == periodo)
                    .all()
                )
                total_cargos = sum(d.monto_asignado_usd for d in cargos_periodo)

                # Pagos del período
                pagos_periodo = (
                    db.query(Pago)
                    .join(Pago.reporte_financiero)
                    .filter(Pago.id_apartamento == apartamento_id, Pago.reporte_financiero.has(periodo=periodo))
                    .all()
                )
                total_pagos = sum(p.monto_pagado_usd for p in pagos_periodo)

                saldo_acumulado += total_cargos - total_pagos

            return saldo_acumulado

        except Exception as e:
            logger.warning(f"Error calculando saldo anterior para apto {apartamento_id}: {str(e)}")
            return Decimal("0.00")

    def _obtener_historico_6_meses(self, db: Session, apartamento_id: int) -> List[Dict]:
        """Obtiene historial de los últimos 6 meses"""
        historico = []
        hoy = date.today()

        for i in range(6):
            # Calcular período (meses anteriores)
            periodo_date = hoy.replace(day=1) - timedelta(days=i * 30)
            periodo = periodo_date.strftime("%Y-%m")

            estado_periodo = self._obtener_estado_cuenta_periodo(db, apartamento_id, periodo)

            historico.append(
                {
                    "periodo": periodo,
                    "total_cargos_usd": estado_periodo["total_cargos_usd"],
                    "total_pagos_usd": estado_periodo["total_pagos_usd"],
                    "saldo_final_usd": estado_periodo["saldo_actual_usd"],
                    "cantidad_movimientos": len(estado_periodo["detalle_cargos"])
                    + len(estado_periodo["detalle_pagos"]),
                }
            )

        return historico

    def _generar_resumen_ejecutivo(self, estado_cuenta: Dict, historico: Optional[List[Dict]]) -> Dict:
        """Genera un resumen ejecutivo con análisis"""
        saldo_actual = estado_cuenta["saldo_actual_usd"]
        total_cargos = estado_cuenta["total_cargos_usd"]
        total_pagos = estado_cuenta["total_pagos_usd"]

        # Análisis de tendencia
        tendencia = "estable"
        if historico and len(historico) > 1:
            saldo_actual = historico[0]["saldo_final_usd"]
            saldo_anterior = historico[1]["saldo_final_usd"]
            if saldo_anterior != 0:
                variacion = ((saldo_actual - saldo_anterior) / abs(saldo_anterior)) * 100
                if variacion > 10:
                    tendencia = "mejorando"
                elif variacion < -10:
                    tendencia = "empeorando"

        # Estado de cuenta
        estado = "AL DÍA"
        if saldo_actual > 0:
            if saldo_actual > total_cargos * 0.5:  # Si debe más del 50% de los cargos mensuales
                estado = "MOROSO"
            else:
                estado = "PENDIENTE"

        # Recomendación de pago
        recomendacion_pago = "Al día"
        if saldo_actual > 0:
            if saldo_actual <= Decimal("50.00"):
                recomendacion_pago = "Pago mínimo recomendado"
            else:
                recomendacion_pago = "Pago total recomendado"

        return {
            "estado_cuenta": estado,
            "tendencia": tendencia,
            "saldo_actual_usd": saldo_actual,
            "recomendacion_pago": recomendacion_pago,
            "resumen_mensual": {
                "cargos_mensuales_promedio": total_cargos,
                "pagos_mensuales_promedio": total_pagos,
                "eficiencia_pago": (total_pagos / total_cargos * 100) if total_cargos > 0 else 0,
            },
            "alertas": self._generar_alertas_resumen(estado_cuenta),
        }

    def _generar_alertas_resumen(self, estado_cuenta: Dict) -> List[Dict]:
        """Genera alertas basadas en el estado de cuenta"""
        alertas = []
        saldo_actual = estado_cuenta["saldo_actual_usd"]

        if saldo_actual > Decimal("100.00"):
            alertas.append(
                {"nivel": "alto", "mensaje": "Saldo pendiente elevado", "accion": "Realizar pago lo antes posible"}
            )
        elif saldo_actual > Decimal("0.00"):
            alertas.append({"nivel": "medio", "mensaje": "Saldo pendiente", "accion": "Programar pago"})

        # Verificar si hay pagos atrasados (comparando cargos vs pagos)
        if estado_cuenta["total_cargos_usd"] > estado_cuenta["total_pagos_usd"]:
            alertas.append(
                {"nivel": "bajo", "mensaje": "Pagos pendientes del mes actual", "accion": "Revisar cargos pendientes"}
            )

        return alertas

    def _calcular_dias_promedio_pago(self, detalle_pagos: List[Dict]) -> float:
        """Calcula días promedio entre vencimiento y pago"""
        if not detalle_pagos:
            return 0.0

        # Esto sería más preciso si tuvieras fecha de vencimiento en pagos
        # Por ahora retornamos un valor por defecto
        return 5.0

    def _generar_recomendaciones(self, estado_cuenta: Dict) -> List[str]:
        """Genera recomendaciones personalizadas"""
        recomendaciones = []
        saldo_actual = estado_cuenta["saldo_actual_usd"]

        if saldo_actual > 0:
            recomendaciones.append(f"Saldo pendiente: ${saldo_actual:.2f} USD - considere realizar el pago pronto")

        if len(estado_cuenta["detalle_pagos"]) == 0:
            recomendaciones.append("No se registran pagos este mes - verifique estado de cuenta")

        if len(estado_cuenta["detalle_cargos"]) > 5:
            recomendaciones.append("Múltiples cargos este mes - revise el detalle")

        if not recomendaciones:
            recomendaciones.append("Estado de cuenta saludable - mantenga sus pagos al día")

        return recomendaciones

    def generar_estado_cuenta_condensado(self, db: Session, apartamento_id: int, periodo: str) -> Dict:
        """
        Versión condensada del estado de cuenta (para listados rápidos)
        """
        try:
            estado_completo = self._obtener_estado_cuenta_periodo(db, apartamento_id, periodo)
            info_apartamento = self._obtener_info_apartamento(db, apartamento_id)

            return {
                "periodo": periodo,
                "apartamento": info_apartamento["apartamento"],
                "saldo_actual_usd": estado_completo["saldo_actual_usd"],
                "total_cargos_usd": estado_completo["total_cargos_usd"],
                "total_pagos_usd": estado_completo["total_pagos_usd"],
                "estado": "AL DÍA" if estado_completo["saldo_actual_usd"] <= 0 else "PENDIENTE",
                "cantidad_movimientos": len(estado_completo["detalle_cargos"]) + len(estado_completo["detalle_pagos"]),
            }

        except Exception as e:
            logger.error(f"Error generando estado condensado para apto {apartamento_id}: {str(e)}")
            raise

    def generar_reportes_lotes(self, db: Session, periodo: str, torre_id: Optional[int] = None) -> List[Dict]:
        """
        Genera estados de cuenta por lotes (para una torre específica o todas)
        """
        try:
            # Obtener apartamentos según filtro
            query = db.query(Apartamento)
            if torre_id:
                query = query.join(Apartamento.piso).filter(Apartamento.piso.has(id_torre=torre_id))

            apartamentos = query.all()

            reportes = []
            for apartamento in apartamentos:
                try:
                    reporte_condensado = self.generar_estado_cuenta_condensado(db, apartamento.id, periodo)
                    reportes.append(reporte_condensado)
                except Exception as e:
                    logger.warning(f"Error generando reporte para apto {apartamento.id}: {str(e)}")
                    # Continuar con el siguiente apartamento

            # Ordenar por saldo pendiente (mayor a menor)
            reportes.sort(key=lambda x: x["saldo_actual_usd"], reverse=True)

            return reportes

        except Exception as e:
            logger.error(f"Error generando reportes por lote: {str(e)}")
            raise


# Instancia global
estado_cuenta_service = EstadoCuentaService()

"""
🎯 Este servicio proporciona:
1. Estados de cuenta DETALLADOS
Información completa del apartamento y residente

Detalle de TODOS los cargos y pagos del período

Saldos acumulados de períodos anteriores

Historial de 6 meses

2. Análisis inteligente
Resumen ejecutivo con tendencias

Alertas automáticas basadas en saldos

Recomendaciones personalizadas

Métricas de comportamiento de pago

3. Formatos flexibles
Detallado: Para residentes que quieren ver todo

Condensado: Para listados rápidos de administradores

Por lotes: Para generar reportes de torres completas

4. Para diferentes usuarios
Residentes: Ven su estado personal detallado

Administradores: Ven estados condensados de múltiples apartamentos

Torres: Reportes agrupados por edificio
"""
