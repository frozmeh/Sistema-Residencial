# services/tasa_cambio_service.py
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta, time
from decimal import Decimal
from typing import Optional, Tuple
import requests
import logging
from ..models.financiero import TasaCambio


logger = logging.getLogger(__name__)


def obtener_tasa_bcv() -> tuple[Decimal, str]:  # ← Solo tasa y fecha banco
    apis = [
        {
            "nombre": "DolarVzla - Principal",
            "url": "https://api.dolarvzla.com/public/exchange-rate",
            "tasa_path": ["current", "usd"],
            "fecha_path": ["current", "date"],
            "prioridad": 1,
        },
        {
            "nombre": "DolarAPI - Oficial",
            "url": "https://ve.dolarapi.com/v1/dolares/oficial",
            "tasa_path": ["promedio"],
            "fecha_path": ["fechaActualizacion"],
            "prioridad": 2,
        },
    ]

    #  Ordenar por prioridad
    apis_ordenadas = sorted(apis, key=lambda x: x["prioridad"])

    #  Intentar cada API en orden
    for api in apis_ordenadas:
        try:
            print(f"Consultando {api['nombre']}...")
            resp = requests.get(api["url"], timeout=5)
            resp.raise_for_status()
            data = resp.json()

            #  Extraer tasa (manejar diferentes estructuras JSON)
            tasa = data
            for key in api["tasa_path"]:
                tasa = tasa[key]
            tasa = round(Decimal(str(tasa)), 2)

            #  Extraer fecha
            fecha_data = data
            for key in api["fecha_path"]:
                fecha_data = fecha_data[key]
            fecha_banco = fecha_data.split("T")[0] if "T" in str(fecha_data) else str(fecha_data)

            return tasa, fecha_banco

        except Exception as e:
            logger.warning(f"❌ {api['nombre']} falló: {str(e)[:50]}...")
            continue  # Intentar siguiente API

    # ❌ Si todas las APIs fallan
    logger.error("Todas las APIs de tasas fallaron")
    raise Exception("No se pudo obtener la tasa de cambio de ninguna fuente")


class TasaCambioService:

    def obtener_tasa_actual(self, db: Session) -> TasaCambio:
        hoy = date.today()

        # PRIMERO: Buscar en BD tasa de HOY
        tasa_hoy = db.query(TasaCambio).filter(TasaCambio.fecha == hoy).first()

        hora_actual = datetime.now().time()
        hora_limite = time(16, 30)  # 4:30 PM

        if tasa_hoy:
            # Si YA PASÓ 4:30 PM HOY, obtener NUEVA tasa (no usar la vieja)
            if hora_actual >= hora_limite:
                logger.info(f"🔄 Después de 4:30 PM, obteniendo tasa ACTUAL...")
                return self._obtener_tasa_externa_y_guardar(db, hoy)
            else:
                # Si es antes de 4:30 PM, usar tasa existente
                logger.info(f"✅ Usando tasa existente (antes de 4:30 PM)")
                return tasa_hoy
        else:
            # No hay tasa para HOY, obtener nueva (sin importar la hora)
            logger.info(f"📅 No hay tasa para hoy, obteniendo nueva...")
            return self._obtener_tasa_externa_y_guardar(db, hoy)

    def actualizar_tasas_automaticamente(self, db: Session) -> TasaCambio:
        """
        Job diario: Siempre obtiene nueva tasa
        """
        hoy = date.today()

        logger.info(f"🔄 Actualizando tasa para {hoy}...")

        # Obtener nueva tasa (sin verificar si existe)
        # _obtener_tasa_externa_y_guardar ya maneja la lógica de guardado
        return self._obtener_tasa_externa_y_guardar(db, hoy)

    def convertir_monto(
        self,
        db: Session,
        monto_usd: Optional[Decimal] = None,
        monto_ves: Optional[Decimal] = None,
    ) -> Tuple[Decimal, Decimal]:
        """
        Convierte entre USD y VES usando una tasa ESPECÍFICA.
        """
        tasa_actual = self.obtener_tasa_actual(db)
        tasa_cambio = tasa_actual.tasa_usd_ves
        if monto_usd is None and monto_ves is None:
            raise ValueError("Debe proporcionar monto_usd o monto_ves")

        # Conversión directa con la tasa proporcionada
        if monto_usd is None:
            monto_usd = monto_ves / tasa_cambio
        if monto_ves is None:
            monto_ves = monto_usd * tasa_cambio

        return (round(monto_usd, 2), round(monto_ves, 2))

    def obtener_ultimas_tasas(self, db: Session, dias: int = 30) -> list[TasaCambio]:
        """
        Obtiene las últimas tasas de cambio para un número de días.
        """
        fecha_inicio = date.today() - timedelta(days=dias)

        return (
            db.query(TasaCambio)
            .filter(TasaCambio.fecha >= fecha_inicio, TasaCambio.fuente == "BCV")
            .order_by(TasaCambio.fecha.desc())
            .all()
        )

    def _obtener_tasa_externa_y_guardar(self, db: Session, fecha: date) -> TasaCambio:
        """
        Obtiene tasa de API externa y guarda en BD.
        """
        try:
            tasa_valor, fecha_banco = obtener_tasa_bcv()

            # Usar el approach de buscar y actualizar/crear
            tasa_existente = db.query(TasaCambio).filter(TasaCambio.fecha == fecha, TasaCambio.fuente == "BCV").first()

            if tasa_existente:
                # Actualizar existente
                tasa_existente.tasa_usd_ves = tasa_valor
                tasa_existente.fecha_creacion = datetime.now()
                db.commit()
                db.refresh(tasa_existente)
                logger.info(f"Tasa ACTUALIZADA para {fecha}: {tasa_valor}")
                return tasa_existente
            else:
                # Crear nueva
                nueva_tasa = TasaCambio(fecha=fecha, tasa_usd_ves=tasa_valor, fuente="BCV", es_historica=False)
                db.add(nueva_tasa)
                db.commit()
                db.refresh(nueva_tasa)
                logger.info(f"Tasa CREADA para {fecha}: {tasa_valor}")
                return nueva_tasa

        except Exception as e:
            logger.error(f"Error guardando tasa en BD: {e}")
            db.rollback()
            raise


# Instancia global del servicio
tasa_cambio_service = TasaCambioService()
