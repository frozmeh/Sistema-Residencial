import requests
from decimal import Decimal
from datetime import datetime, timedelta

# Cache global
_cache_tasa = {"valor": None, "ultima_actualizacion": None}


def obtener_tasa_bcv(cache_duracion_horas: int = 12) -> tuple[Decimal, datetime]:
    """
    Obtiene la tasa oficial (BCV) desde DolarApi.com.
    Devuelve un tuple: (tasa, fecha_ultima_actualizacion)
    """
    global _cache_tasa
    ahora = datetime.now()

    if (
        _cache_tasa["valor"] is not None
        and _cache_tasa["ultima_actualizacion"] is not None
        and ahora - _cache_tasa["ultima_actualizacion"] < timedelta(hours=cache_duracion_horas)
    ):
        return _cache_tasa["valor"], _cache_tasa["ultima_actualizacion"]

    try:
        url = "https://dolarapi.com/v1/dolares/oficial"
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
