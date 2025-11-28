# services/cargos_service.py
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from decimal import Decimal
import logging
from datetime import date, datetime, timedelta

from ..models.financiero import Cargo, DistribucionGasto, EstadoCargoEnum, Gasto
from ..models.torres import Apartamento
from ..schemas.financiero import CargoCreate, CargoResponse

logger = logging.getLogger(__name__)


class CargosService:

    def crear_cargo_por_distribucion(self, db: Session, distribucion: DistribucionGasto) -> Cargo:
        """
        Crea un cargo a partir de una distribución de gasto
        """
        try:
            # Obtener datos del gasto para la descripción
            gasto = db.query(Gasto).filter(Gasto.id == distribucion.id_gasto).first()
            if not gasto:
                raise ValueError(f"Gasto {distribucion.id_gasto} no encontrado")

            # Obtener datos del apartamento
            apartamento = db.query(Apartamento).filter(Apartamento.id == distribucion.id_apartamento).first()

            # Calcular fecha de vencimiento (30 días después del gasto)
            fecha_vencimiento = gasto.fecha_gasto + timedelta(days=30)

            # Crear descripción descriptiva
            descripcion = f"{gasto.descripcion} - {gasto.periodo}"
            if apartamento:
                descripcion += f" - Apt {apartamento.numero}"

            # Crear el cargo
            cargo = Cargo(
                id_apartamento=distribucion.id_apartamento,
                id_gasto=distribucion.id_gasto,
                descripcion=descripcion,
                monto_usd=distribucion.monto_asignado_usd,
                monto_ves=distribucion.monto_asignado_ves,
                saldo_pendiente_usd=distribucion.monto_asignado_usd,  # Inicialmente igual al monto
                saldo_pendiente_ves=distribucion.monto_asignado_ves,
                fecha_vencimiento=fecha_vencimiento,
                estado=EstadoCargoEnum.PENDIENTE,
            )

            db.add(cargo)
            db.flush()

            logger.info(
                f"✅ Cargo {cargo.id} creado para apartamento {distribucion.id_apartamento} - ${cargo.monto_usd} USD"
            )
            return cargo

        except Exception as e:
            logger.error(f"Error creando cargo para distribución {distribucion.id}: {str(e)}")
            raise

    def generar_cargos_desde_gasto(self, db: Session, gasto_id: int) -> List[Cargo]:
        """
        Genera cargos para todas las distribuciones de un gasto
        """
        try:
            # Verificar que el gasto existe y está distribuido
            gasto = db.query(Gasto).filter(Gasto.id == gasto_id).first()
            if not gasto:
                raise ValueError(f"Gasto {gasto_id} no encontrado")

            if gasto.estado != "Distribuido":
                raise ValueError(f"Gasto {gasto_id} no está distribuido")

            # Obtener todas las distribuciones del gasto
            distribuciones = db.query(DistribucionGasto).filter(DistribucionGasto.id_gasto == gasto_id).all()

            if not distribuciones:
                raise ValueError(f"No hay distribuciones para el gasto {gasto_id}")

            cargos_creados = []
            for distribucion in distribuciones:
                # Verificar si ya existe un cargo para esta distribución
                cargo_existente = (
                    db.query(Cargo)
                    .filter(Cargo.id_apartamento == distribucion.id_apartamento, Cargo.id_gasto == gasto_id)
                    .first()
                )

                if not cargo_existente:
                    cargo = self.crear_cargo_por_distribucion(db, distribucion)
                    cargos_creados.append(cargo)
                else:
                    logger.info(f"⚠️ Cargo ya existe para apto {distribucion.id_apartamento} y gasto {gasto_id}")

            db.commit()
            logger.info(f"✅ {len(cargos_creados)} cargos generados para gasto {gasto_id}")
            return cargos_creados

        except Exception as e:
            db.rollback()
            logger.error(f"Error generando cargos para gasto {gasto_id}: {str(e)}")
            raise

    def obtener_cargos_pendientes(self, db: Session, apartamento_id: int) -> List[Cargo]:
        """
        Obtiene todos los cargos pendientes de un apartamento
        """
        try:
            cargos = (
                db.query(Cargo)
                .options(
                    joinedload(Cargo.gasto), joinedload(Cargo.apartamento).joinedload(Apartamento.tipo_apartamento)
                )
                .filter(
                    Cargo.id_apartamento == apartamento_id,
                    Cargo.estado.in_([EstadoCargoEnum.PENDIENTE, EstadoCargoEnum.PARCIAL, EstadoCargoEnum.VENCIDO]),
                )
                .order_by(Cargo.fecha_vencimiento.asc())
                .all()
            )

            logger.info(f"✅ Encontrados {len(cargos)} cargos pendientes para apartamento {apartamento_id}")
            return cargos

        except Exception as e:
            logger.error(f"Error obteniendo cargos pendientes para apto {apartamento_id}: {str(e)}")
            raise

    def obtener_cargos_por_apartamento(
        self, db: Session, apartamento_id: int, incluir_pagados: bool = False
    ) -> List[Cargo]:
        """
        Obtiene todos los cargos de un apartamento (con filtro opcional de estado)
        """
        try:
            query = (
                db.query(Cargo)
                .options(
                    joinedload(Cargo.gasto),  # 🆕 CARGAR GASTO COMPLETO
                    joinedload(Cargo.apartamento).joinedload(Apartamento.tipo_apartamento),
                    joinedload(Cargo.apartamento).joinedload(Apartamento.residente),  # 🆕 CARGAR RESIDENTE
                )
                .filter(Cargo.id_apartamento == apartamento_id)
            )

            if not incluir_pagados:
                query = query.filter(Cargo.estado != EstadoCargoEnum.PAGADO)

            cargos = query.order_by(Cargo.fecha_vencimiento.asc()).all()

            logger.info(f"✅ Encontrados {len(cargos)} cargos para apartamento {apartamento_id}")
            return cargos

        except Exception as e:
            logger.error(f"Error obteniendo cargos para apto {apartamento_id}: {str(e)}")
            raise

    def actualizar_estado_cargo(self, db: Session, cargo_id: int) -> Cargo:
        """
        Actualiza el estado de un cargo basado en saldo pendiente y fecha
        """
        try:
            cargo = db.query(Cargo).filter(Cargo.id == cargo_id).first()
            if not cargo:
                raise ValueError(f"Cargo {cargo_id} no encontrado")

            estado_anterior = cargo.estado

            # Determinar nuevo estado
            if cargo.saldo_pendiente_usd == 0:
                cargo.estado = EstadoCargoEnum.PAGADO
            elif cargo.saldo_pendiente_usd < cargo.monto_usd:
                cargo.estado = EstadoCargoEnum.PARCIAL
            elif cargo.fecha_vencimiento < date.today():
                cargo.estado = EstadoCargoEnum.VENCIDO
            else:
                cargo.estado = EstadoCargoEnum.PENDIENTE

            cargo.fecha_actualizacion = datetime.now()

            db.commit()

            if estado_anterior != cargo.estado:
                logger.info(f"🔄 Cargo {cargo_id} cambió de {estado_anterior} a {cargo.estado}")

            return cargo

        except Exception as e:
            db.rollback()
            logger.error(f"Error actualizando estado del cargo {cargo_id}: {str(e)}")
            raise

    def verificar_vencimientos_automatico(self, db: Session) -> int:
        """
        Job diario: Verifica y actualiza cargos vencidos
        Retorna número de cargos actualizados
        """
        try:
            # Buscar cargos pendientes con fecha de vencimiento pasada
            cargos_a_actualizar = (
                db.query(Cargo)
                .filter(
                    Cargo.estado.in_([EstadoCargoEnum.PENDIENTE, EstadoCargoEnum.PARCIAL]),
                    Cargo.fecha_vencimiento < date.today(),
                )
                .all()
            )

            cargos_actualizados = 0
            for cargo in cargos_a_actualizar:
                estado_anterior = cargo.estado
                cargo.estado = EstadoCargoEnum.VENCIDO
                cargo.fecha_actualizacion = datetime.now()
                cargos_actualizados += 1

                logger.info(f"⚠️ Cargo {cargo.id} marcado como VENCIDO (era {estado_anterior})")

            if cargos_actualizados > 0:
                db.commit()
                logger.info(f"✅ {cargos_actualizados} cargos actualizados a VENCIDO")
            else:
                logger.info("✅ No hay cargos para marcar como vencidos")

            return cargos_actualizados

        except Exception as e:
            db.rollback()
            logger.error(f"Error en verificación automática de vencimientos: {str(e)}")
            return 0

    def obtener_cargos_vencidos(self, db: Session) -> List[Cargo]:
        """
        Obtiene todos los cargos vencidos
        """
        try:
            cargos = (
                db.query(Cargo)
                .options(joinedload(Cargo.apartamento), joinedload(Cargo.gasto))
                .filter(Cargo.estado == EstadoCargoEnum.VENCIDO)
                .order_by(Cargo.fecha_vencimiento.asc())
                .all()
            )

            logger.info(f"✅ Encontrados {len(cargos)} cargos vencidos")
            return cargos

        except Exception as e:
            logger.error(f"Error obteniendo cargos vencidos: {str(e)}")
            raise

    def obtener_cargo_por_id(self, db: Session, cargo_id: int) -> Optional[Cargo]:
        """
        Obtiene un cargo específico con todas sus relaciones
        """
        try:
            cargo = (
                db.query(Cargo)
                .options(
                    joinedload(Cargo.gasto),
                    joinedload(Cargo.apartamento).joinedload(Apartamento.tipo_apartamento),
                    joinedload(Cargo.apartamento).joinedload(Apartamento.residente),
                )
                .filter(Cargo.id == cargo_id)
                .first()
            )

            return cargo

        except Exception as e:
            logger.error(f"Error obteniendo cargo {cargo_id}: {str(e)}")
            raise

    def calcular_total_pendiente_apartamento(self, db: Session, apartamento_id: int) -> dict:
        """
        Calcula el total pendiente de un apartamento
        """
        try:
            cargos = self.obtener_cargos_pendientes(db, apartamento_id)

            total_usd = sum(cargo.saldo_pendiente_usd for cargo in cargos)
            total_ves = sum(cargo.saldo_pendiente_ves for cargo in cargos)

            return {
                "apartamento_id": apartamento_id,
                "total_pendiente_usd": total_usd,
                "total_pendiente_ves": total_ves,
                "total_cargos_pendientes": len(cargos),
                "cargos_vencidos": len([c for c in cargos if c.estado == EstadoCargoEnum.VENCIDO]),
            }

        except Exception as e:
            logger.error(f"Error calculando total pendiente para apto {apartamento_id}: {str(e)}")
            raise


# Instancia global
cargos_service = CargosService()
