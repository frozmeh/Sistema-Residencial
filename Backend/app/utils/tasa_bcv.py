import requests
from decimal import Decimal
from datetime import datetime, timedelta, date
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


# Cache global
_cache_tasa = {"valor": None, "ultima_actualizacion": None}


def obtener_tasa_bcv(cache_duracion_horas: int = 12) -> tuple[Decimal, datetime]:
    global _cache_tasa
    ahora = datetime.now()

    if (
        _cache_tasa["valor"] is not None
        and _cache_tasa["ultima_actualizacion"] is not None
        and ahora - _cache_tasa["ultima_actualizacion"] < timedelta(hours=cache_duracion_horas)
    ):
        return _cache_tasa["valor"], _cache_tasa["ultima_actualizacion"]

    try:
        url = "https://ve.dolarapi.com/v1/dolares/oficial"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        tasa = Decimal(str(data["promedio"]))

        # Actualizar cache
        _cache_tasa["valor"] = tasa
        _cache_tasa["ultima_actualizacion"] = ahora

        return tasa, ahora

    except Exception as e:
        print(f"Error obteniendo tasa BCV: {e}")
        return Decimal("40.00"), ahora


def obtener_tasa_historica_bcv(fecha: date) -> Tuple[Decimal, datetime]:
    """
    Obtiene la tasa BCV para una fecha histórica específica
    IMPORTANTE: Esta función debe ser implementada con una API real de BCV
    Por ahora, usamos un placeholder que devuelve la tasa actual
    """
    try:
        # TODO: Implementar con API de BCV histórica
        # Por ahora, devolvemos la tasa actual como placeholder
        # ⚠️ ESTO ES TEMPORAL - DEBES IMPLEMENTAR LA LÓGICA REAL
        return obtener_tasa_bcv()
    except Exception as e:
        logger.error(f"Error obteniendo tasa histórica para {fecha}: {e}")
        # Fallback a tasa actual
        return obtener_tasa_bcv()
