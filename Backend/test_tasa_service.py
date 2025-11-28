# test_api_tasas.py
import requests
from decimal import Decimal
from datetime import datetime


def obtener_tasa_con_fallbacks():
    """Prueba el sistema de múltiples APIs con fallback"""

    print("🧪 Probando sistema de múltiples APIs con fallback...")

    # ✅ Lista de APIs con prioridad (igual que en el servicio)
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

    # ✅ Ordenar por prioridad
    apis_ordenadas = sorted(apis, key=lambda x: x["prioridad"])

    tasa_encontrada = None
    fecha_encontrada = None
    api_exitosa = None

    # ✅ Intentar cada API en orden
    for api in apis_ordenadas:
        try:
            print(f"🔗 Intentando {api['nombre']}...")
            resp = requests.get(api["url"], timeout=5)
            resp.raise_for_status()
            data = resp.json()

            # ✅ Extraer tasa (manejar diferentes estructuras JSON)
            tasa = data
            for key in api["tasa_path"]:
                tasa = tasa[key]
            tasa_encontrada = round(Decimal(str(tasa)), 2)

            # ✅ Extraer fecha
            fecha_data = data
            for key in api["fecha_path"]:
                fecha_data = fecha_data[key]
            fecha_encontrada = fecha_data.split("T")[0] if "T" in str(fecha_data) else str(fecha_data)

            api_exitosa = api["nombre"]
            print(f"✅ Éxito con {api['nombre']}: {tasa_encontrada} VES")
            break  # ¡Salir del loop si funciona!

        except Exception as e:
            print(f"❌ {api['nombre']} falló: {str(e)[:50]}...")
            continue  # Intentar siguiente API

    # ✅ Mostrar resultados
    if tasa_encontrada and fecha_encontrada:
        print(f"\n🎉 SISTEMA FUNCIONANDO:")
        print(f"   ✅ API utilizada: {api_exitosa}")
        print(f"   💰 Tasa obtenida: 1 USD = {tasa_encontrada} VES")
        print(f"   📅 Fecha banco: {fecha_encontrada}")

        # Probar conversiones
        print(f"\n💱 Probando conversiones:")
        monto_usd = Decimal("100")
        monto_ves = monto_usd * tasa_encontrada
        print(f"   $100 USD = {monto_ves:.2f} VES")

        monto_ves2 = Decimal("1000000")
        monto_usd2 = monto_ves2 / tasa_encontrada
        print(f"   1,000,000 VES = ${monto_usd2:.2f} USD")

    else:
        print(f"\n💥 TODAS LAS APIS FALLARON")
        print("   El sistema no pudo obtener tasas de ninguna fuente")


def test_apis_individualmente():
    """Prueba cada API individualmente para diagnóstico"""

    print("\n🔍 Probando cada API individualmente...")

    apis = [
        {
            "nombre": "DolarVzla - Principal",
            "url": "https://api.dolarvzla.com/public/exchange-rate",
            "tasa": "current.usd",
            "fecha": "current.date",
        },
        {
            "nombre": "DolarAPI - Oficial",
            "url": "https://ve.dolarapi.com/v1/dolares/oficial",
            "tasa": "promedio",
            "fecha": "fechaActualizacion",
        },
    ]

    for api in apis:
        try:
            resp = requests.get(api["url"], timeout=5)
            data = resp.json()

            # Manejar diferentes estructuras
            if api["nombre"] == "DolarVzla - Principal":
                tasa = data["current"]["usd"]
                fecha = data["current"]["date"]
            else:
                tasa = data["promedio"]
                fecha = data["fechaActualizacion"].split("T")[0]

            tasa_redondeada = round(Decimal(str(tasa)), 2)
            print(f"   ✅ {api['nombre']}: 1 USD = {tasa_redondeada} VES, fecha: {fecha}")

        except Exception as e:
            print(f"   ❌ {api['nombre']}: Error - {str(e)[:50]}...")


if __name__ == "__main__":
    # Probar el sistema completo con fallback
    obtener_tasa_con_fallbacks()

    # Probar cada API individualmente para diagnóstico
    test_apis_individualmente()
