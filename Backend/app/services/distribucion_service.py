# services/distribucion_service.py
from sqlalchemy.orm import Session
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional
import logging
from ..models.financiero import DistribucionGasto, Gasto
from ..models.torres import Apartamento, TipoApartamento
from ..services.tasa_cambio_service import tasa_cambio_service

logger = logging.getLogger(__name__)


class DistribucionService:

    def calcular_distribucion_gasto(
        self, db: Session, gasto: Gasto, apartamentos_ids: List[int], forzar_equitativa: bool = False
    ) -> List[DistribucionGasto]:
        """
        Calcula y crea las distribuciones de un gasto entre apartamentos.
        """
        logger.info(f"Calculando distribución para gasto {gasto.id} en {len(apartamentos_ids)} apartamentos")

        # Obtener apartamentos con sus tipos
        apartamentos = self._obtener_apartamentos_con_tipos(db, apartamentos_ids)

        if not apartamentos:
            raise ValueError("No se encontraron apartamentos para distribuir el gasto")

        # Calcular distribución
        if forzar_equitativa:
            distribuciones_calculadas = self._calcular_distribucion_equitativa(gasto, apartamentos)
        else:
            distribuciones_calculadas = self._calcular_distribucion_por_porcentaje(gasto, apartamentos)

        # Crear objetos DistribucionGasto
        distribuciones = []
        for distribucion in distribuciones_calculadas:
            distribucion_gasto = DistribucionGasto(
                id_gasto=gasto.id,
                id_apartamento=distribucion["apartamento_id"],
                monto_asignado_usd=distribucion["monto_usd"],
                monto_asignado_ves=distribucion["monto_ves"],
                porcentaje_aplicado=distribucion["porcentaje_aplicado"],
            )
            distribuciones.append(distribucion_gasto)

        logger.info(f"Distribución calculada: {len(distribuciones)} registros")
        return distribuciones

    def _calcular_distribucion_por_porcentaje(self, gasto: Gasto, apartamentos: List[Dict]) -> List[Dict]:
        """
        VERSIÓN CORREGIDA - SIN NORMALIZACIÓN
        Los porcentajes se aplican DIRECTAMENTE
        """
        distribuciones = []

        for apt in apartamentos:
            # USAR PORCENTAJE DIRECTAMENTE - SIN NORMALIZAR
            porcentaje = Decimal(str(apt["porcentaje_aporte"])) * Decimal("100.00")

            # Calcular monto USD: gasto_total × porcentaje_del_apartamento
            monto_usd = (gasto.monto_total_usd * porcentaje) / Decimal("100.00")
            monto_usd = monto_usd.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # Convertir a VES
            monto_ves = (monto_usd * gasto.tasa_cambio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            distribuciones.append(
                {
                    "apartamento_id": apt["id"],
                    "apartamento_numero": apt["numero"],
                    "tipo_apartamento": apt["tipo_nombre"],
                    "porcentaje_aplicado": porcentaje.quantize(Decimal("0.0001")),
                    "monto_usd": monto_usd,
                    "monto_ves": monto_ves,
                }
            )

        return distribuciones

    def _calcular_distribucion_equitativa(self, gasto: Gasto, apartamentos: List[Dict]) -> List[Dict]:
        """
        Calcula distribución equitativa (todos pagan igual).
        """
        total_apartamentos = len(apartamentos)
        monto_por_apartamento_usd = (gasto.monto_total_usd / total_apartamentos).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        monto_por_apartamento_ves = (monto_por_apartamento_usd * gasto.tasa_cambio).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        distribuciones = []
        porcentaje_equitativo = Decimal("100.00") / total_apartamentos

        for apt in apartamentos:
            distribuciones.append(
                {
                    "apartamento_id": apt["id"],
                    "apartamento_numero": apt["numero"],
                    "tipo_apartamento": apt["tipo_nombre"],
                    "porcentaje_aplicado": porcentaje_equitativo.quantize(Decimal("0.0001")),
                    "monto_usd": monto_por_apartamento_usd,
                    "monto_ves": monto_por_apartamento_ves,
                }
            )

        return distribuciones

    def _obtener_apartamentos_con_tipos(self, db: Session, apartamentos_ids: List[int]) -> List[Dict]:
        """
        Obtiene apartamentos con información de sus tipos y porcentajes.
        """
        apartamentos = (
            db.query(
                Apartamento.id,
                Apartamento.numero,
                TipoApartamento.nombre.label("tipo_nombre"),
                TipoApartamento.porcentaje_aporte,
            )
            .join(TipoApartamento, Apartamento.id_tipo_apartamento == TipoApartamento.id)
            .filter(Apartamento.id.in_(apartamentos_ids))
            .all()
        )

        return [
            {
                "id": apt.id,
                "numero": apt.numero,
                "tipo_nombre": apt.tipo_nombre,
                "porcentaje_aporte": apt.porcentaje_aporte,
            }
            for apt in apartamentos
        ]

    def obtener_porcentaje_aporte(self, db: Session, tipo_apartamento_id: int) -> Decimal:
        """
        Obtiene el porcentaje de aporte para un tipo de apartamento.
        """
        tipo = db.query(TipoApartamento).filter(TipoApartamento.id == tipo_apartamento_id).first()

        if not tipo:
            raise ValueError(f"Tipo de apartamento {tipo_apartamento_id} no encontrado")

        return Decimal(str(tipo.porcentaje_aporte))

    def calcular_distribucion_preview(
        self,
        db: Session,
        monto_total_usd: Decimal,
        apartamentos_ids: List[int],
        forzar_equitativa: bool = False,
    ) -> Dict:
        """
        Calcula distribución sin guardar (solo para preview).
        """
        # Crear objeto gasto temporal para los cálculos
        tasa_cambio = tasa_cambio_service.obtener_tasa_actual(db).tasa_usd_ves
        gasto_temporal = Gasto()
        gasto_temporal.monto_total_usd = monto_total_usd
        gasto_temporal.tasa_cambio = tasa_cambio

        apartamentos = self._obtener_apartamentos_con_tipos(db, apartamentos_ids)

        if forzar_equitativa:
            distribuciones = self._calcular_distribucion_equitativa(gasto_temporal, apartamentos)
        else:
            distribuciones = self._calcular_distribucion_por_porcentaje(gasto_temporal, apartamentos)

        return {
            "monto_total_usd": monto_total_usd,
            "monto_total_ves": monto_total_usd * tasa_cambio,
            "total_apartamentos": len(apartamentos_ids),
            "distribuciones": distribuciones,
        }

    def guardar_distribuciones(self, db: Session, distribuciones: List[DistribucionGasto]) -> List[DistribucionGasto]:
        """
        Guarda las distribuciones en la base de datos.
        """
        try:
            for distribucion in distribuciones:
                db.add(distribucion)

            db.commit()

            # Refrescar para obtener IDs
            for distribucion in distribuciones:
                db.refresh(distribucion)

            logger.info(f"Distribuciones guardadas: {len(distribuciones)} registros")
            return distribuciones

        except Exception as e:
            db.rollback()
            logger.error(f"Error guardando distribuciones: {e}")
            raise


# Instancia global del servicio
distribucion_service = DistribucionService()
