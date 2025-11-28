# tests/test_gastos_endpoints.py
from fastapi.testclient import TestClient
from decimal import Decimal


def test_endpoint_crear_gasto(client: TestClient):
    """Test del endpoint POST /gastos/"""
    payload = {
        "monto_usd": "1000.00",
        "descripcion": "Limpieza piscina",
        "categoria": "MANTENIMIENTO",
        "fecha_gasto": "2024-01-15",
        "criterio_seleccion": "todas_torres",
        "forzar_distribucion_equitativa": False,
    }

    response = client.post("/gastos/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["distribuido"] == True
    print("✅ TEST PASADO: Endpoint crear gasto")


def test_endpoint_obtener_gastos(client: TestClient):
    """Test del endpoint GET /gastos/"""
    response = client.get("/gastos/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print("✅ TEST PASADO: Endpoint obtener gastos")
