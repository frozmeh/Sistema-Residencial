# services/deudas_service.py (VERSIÓN CORREGIDA Y MEJORADA)
from sqlalchemy.orm import Session
from typing import List, Dict
from decimal import Decimal
from datetime import date, datetime, timedelta
import logging

from ..models.financiero import Cargo, EstadoCargoEnum
from .cargos_service import cargos_service
from .pagos_service import pagos_service

logger = logging.getLogger(__name__)


class DeudasService:

    def obtener_resumen_deudas_apartamento(self, db: Session, apartamento_id: int) -> Dict:
        """
        Resumen COMPLETO y PRÁCTICO de deudas para un apartamento
        """
        try:
            # Obtener cargos pendientes
            cargos_pendientes = cargos_service.obtener_cargos_por_apartamento(
                db, apartamento_id, incluir_pagados=False
            )

            # Obtener historial de pagos (últimos 3 meses para contexto)
            pagos_recientes = pagos_service.obtener_pagos_por_apartamento(db, apartamento_id)
            pagos_ultimos_3_meses = [
                p
                for p in pagos_recientes
                if p.fecha_creacion and p.fecha_creacion.date() >= (date.today() - timedelta(days=90))
            ]

            # Calcular métricas
            cargos_vencidos = [c for c in cargos_pendientes if c.estado == EstadoCargoEnum.VENCIDO]
            cargos_proximos_vencer = [
                c
                for c in cargos_pendientes
                if c.estado in [EstadoCargoEnum.PENDIENTE, EstadoCargoEnum.PARCIAL]
                and c.fecha_vencimiento <= (date.today() + timedelta(days=7))
            ]

            # Encontrar próximo vencimiento (excluyendo ya vencidos)
            vencimientos_futuros = [
                c.fecha_vencimiento for c in cargos_pendientes if c.fecha_vencimiento >= date.today()
            ]
            proximo_vencimiento = min(vencimientos_futuros) if vencimientos_futuros else None

            return {
                "apartamento_id": apartamento_id,
                "resumen": {
                    "total_pendiente_usd": sum(c.saldo_pendiente_usd for c in cargos_pendientes),
                    "total_pendiente_ves": sum(c.saldo_pendiente_ves for c in cargos_pendientes),
                    "total_cargos_pendientes": len(cargos_pendientes),
                    "cargos_vencidos": len(cargos_vencidos),
                    "cargos_proximos_vencer": len(cargos_proximos_vencer),
                },
                "alertas": {
                    "tiene_vencidos": len(cargos_vencidos) > 0,
                    "tiene_proximos_vencer": len(cargos_proximos_vencer) > 0,
                    "proximo_vencimiento": proximo_vencimiento,
                    "dias_para_proximo_vencimiento": (
                        (proximo_vencimiento - date.today()).days if proximo_vencimiento else None
                    ),
                },
                "detalle_cargos": {
                    "vencidos": [
                        {
                            "id": c.id,
                            "descripcion": c.descripcion,
                            "monto_original_usd": c.monto_usd,
                            "saldo_pendiente_usd": c.saldo_pendiente_usd,
                            "fecha_vencimiento": c.fecha_vencimiento,
                            "dias_vencido": (date.today() - c.fecha_vencimiento).days,
                        }
                        for c in cargos_vencidos
                    ],
                    "proximos_vencer": [
                        {
                            "id": c.id,
                            "descripcion": c.descripcion,
                            "saldo_pendiente_usd": c.saldo_pendiente_usd,
                            "fecha_vencimiento": c.fecha_vencimiento,
                            "dias_para_vencer": (c.fecha_vencimiento - date.today()).days,
                        }
                        for c in cargos_proximos_vencer
                    ],
                    "otros_pendientes": [
                        {
                            "id": c.id,
                            "descripcion": c.descripcion,
                            "saldo_pendiente_usd": c.saldo_pendiente_usd,
                            "fecha_vencimiento": c.fecha_vencimiento,
                            "estado": c.estado.value,
                        }
                        for c in cargos_pendientes
                        if c not in cargos_vencidos and c not in cargos_proximos_vencer
                    ],
                },
                "historial_reciente": {
                    "pagos_ultimos_3_meses": len(pagos_ultimos_3_meses),
                    "total_pagado_3_meses_usd": sum(p.monto_pagado_usd for p in pagos_ultimos_3_meses),
                    "ultimo_pago": (
                        {
                            "fecha": max(p.fecha_creacion for p in pagos_ultimos_3_meses),
                            "monto_usd": max(p.monto_pagado_usd for p in pagos_ultimos_3_meses),
                        }
                        if pagos_ultimos_3_meses
                        else None
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Error obteniendo resumen de deudas para apartamento {apartamento_id}: {str(e)}")
            raise

    def obtener_morosidad_condominio(self, db: Session) -> Dict:
        """
        Vista GENERAL de morosidad para administradores
        """
        try:
            # Obtener todos los cargos pendientes del condominio
            todos_cargos_pendientes = (
                db.query(Cargo)
                .filter(
                    Cargo.estado.in_([EstadoCargoEnum.PENDIENTE, EstadoCargoEnum.PARCIAL, EstadoCargoEnum.VENCIDO])
                )
                .all()
            )

            # Agrupar por apartamento
            deudas_por_apartamento = {}
            for cargo in todos_cargos_pendientes:
                apt_id = cargo.id_apartamento
                if apt_id not in deudas_por_apartamento:
                    deudas_por_apartamento[apt_id] = {
                        "cargos": [],
                        "total_pendiente_usd": Decimal("0.00"),
                        "cargos_vencidos": 0,
                    }

                deudas_por_apartamento[apt_id]["cargos"].append(cargo)
                deudas_por_apartamento[apt_id]["total_pendiente_usd"] += cargo.saldo_pendiente_usd
                if cargo.estado == EstadoCargoEnum.VENCIDO:
                    deudas_por_apartamento[apt_id]["cargos_vencidos"] += 1

            # Calcular métricas generales
            apartamentos_con_deuda = len(deudas_por_apartamento)
            total_deuda_general = sum(apt_data["total_pendiente_usd"] for apt_data in deudas_por_apartamento.values())
            apartamentos_morosos = sum(
                1 for apt_data in deudas_por_apartamento.values() if apt_data["cargos_vencidos"] > 0
            )

            # Top 5 apartamentos con mayor deuda
            top_deudores = sorted(
                [
                    {
                        "apartamento_id": apt_id,
                        "total_deuda_usd": apt_data["total_pendiente_usd"],
                        "cargos_vencidos": apt_data["cargos_vencidos"],
                        "total_cargos": len(apt_data["cargos"]),
                    }
                    for apt_id, apt_data in deudas_por_apartamento.items()
                ],
                key=lambda x: x["total_deuda_usd"],
                reverse=True,
            )[:5]

            return {
                "metricas_generales": {
                    "total_deuda_condominio_usd": total_deuda_general,
                    "apartamentos_con_deuda": apartamentos_con_deuda,
                    "apartamentos_morosos": apartamentos_morosos,
                    "porcentaje_morosidad": (
                        (apartamentos_morosos / apartamentos_con_deuda * 100) if apartamentos_con_deuda > 0 else 0
                    ),
                    "deuda_promedio_por_apartamento": (
                        total_deuda_general / apartamentos_con_deuda if apartamentos_con_deuda > 0 else 0
                    ),
                },
                "top_deudores": top_deudores,
                "distribucion_deuda": {
                    "rango_0_50": len(
                        [apt for apt in deudas_por_apartamento.values() if apt["total_pendiente_usd"] <= 50]
                    ),
                    "rango_50_100": len(
                        [apt for apt in deudas_por_apartamento.values() if 50 < apt["total_pendiente_usd"] <= 100]
                    ),
                    "rango_100_200": len(
                        [apt for apt in deudas_por_apartamento.values() if 100 < apt["total_pendiente_usd"] <= 200]
                    ),
                    "rango_200_plus": len(
                        [apt for apt in deudas_por_apartamento.values() if apt["total_pendiente_usd"] > 200]
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Error calculando morosidad del condominio: {str(e)}")
            raise

    def obtener_historial_12_meses(self, db: Session, apartamento_id: int) -> List[Dict]:
        """
        Historial de deuda mensual de los últimos 12 meses
        """
        try:
            historial = []
            hoy = date.today()

            for i in range(12):
                # Calcular periodo (mes anterior al actual)
                periodo_date = hoy.replace(day=1) - timedelta(days=i * 30)
                periodo = periodo_date.strftime("%Y-%m")

                # Obtener cargos de ese periodo
                cargos_periodo = (
                    db.query(Cargo)
                    .join(Cargo.gasto)
                    .filter(Cargo.id_apartamento == apartamento_id, Cargo.gasto.has(periodo=periodo))
                    .all()
                )

                deuda_periodo = {
                    "periodo": periodo,
                    "total_cargos_usd": sum(c.monto_usd for c in cargos_periodo),
                    "saldo_pendiente_usd": sum(c.saldo_pendiente_usd for c in cargos_periodo),
                    "cargos_vencidos": len([c for c in cargos_periodo if c.estado == EstadoCargoEnum.VENCIDO]),
                    "total_cargos": len(cargos_periodo),
                }

                historial.append(deuda_periodo)

            return historial

        except Exception as e:
            logger.error(f"Error obteniendo historial 12 meses para apartamento {apartamento_id}: {str(e)}")
            return []  # Retorna lista vacía en caso de error para no romper el flujo

    def obtener_deuda_total_apartamento(self, db: Session, apartamento_id: int) -> Dict:
        """
        Versión SIMPLE - solo totales (para casos donde no se necesita el detalle completo)
        """
        try:
            cargos_pendientes = cargos_service.obtener_cargos_por_apartamento(
                db, apartamento_id, incluir_pagados=False
            )

            return {
                "apartamento_id": apartamento_id,
                "total_deuda_usd": sum(c.saldo_pendiente_usd for c in cargos_pendientes),
                "total_deuda_ves": sum(c.saldo_pendiente_ves for c in cargos_pendientes),
                "cargos_pendientes": len(cargos_pendientes),
                "cargos_vencidos": len([c for c in cargos_pendientes if c.estado == EstadoCargoEnum.VENCIDO]),
            }
        except Exception as e:
            logger.error(f"Error obteniendo deuda total para apartamento {apartamento_id}: {str(e)}")
            raise


# Instancia global
deudas_service = DeudasService()
