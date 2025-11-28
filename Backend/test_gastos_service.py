# tests/test_gastos_service.py
import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from app.services.gastos_service import gastos_service
from app.schemas.financiero import GastoCompletoCreate, CriterioSeleccion


def test_crear_gasto_completo_todas_torres(db: Session):
    """Test crear gasto para todas las torres"""
    datos = GastoCompletoCreate(
        monto_usd=Decimal("1000"),
        descripcion="Limpieza áreas comunes Enero",
        categoria="MANTENIMIENTO",
        fecha_gasto=date(2024, 1, 15),
        criterio_seleccion=CriterioSeleccion.TODAS_TORRES,
        forzar_distribucion_equitativa=False,
    )

    gasto = gastos_service.crear_gasto_completo(db, datos)

    assert gasto.id is not None
    assert gasto.monto_usd == Decimal("1000")
    assert gasto.distribuido == True
    assert gasto.descripcion == "Limpieza áreas comunes Enero"
    print("✅ TEST PASADO: Crear gasto todas torres")


def test_crear_gasto_torre_especifica(db: Session):
    """Test crear gasto para torre específica"""
    datos = GastoCompletoCreate(
        monto_usd=Decimal("500"),
        descripcion="Reparación ascensor Torre A",
        categoria="REPARACIONES",
        fecha_gasto=date(2024, 1, 10),
        criterio_seleccion=CriterioSeleccion.TORRE_ESPECIFICA,
        torre_id=1,  # Torre A
        forzar_distribucion_equitativa=False,
    )

    gasto = gastos_service.crear_gasto_completo(db, datos)

    assert gasto.id is not None
    assert gasto.distribuido == True
    print("✅ TEST PASADO: Crear gasto torre específica")


def test_seleccion_apartamentos_todas_torres(db: Session):
    """Test que selecciona todos los apartamentos"""
    datos = GastoCompletoCreate(
        monto_usd=Decimal("100"),
        descripcion="Test todas torres",
        categoria="TEST",
        fecha_gasto=date(2024, 1, 1),
        criterio_seleccion=CriterioSeleccion.TODAS_TORRES,
    )

    apartamentos_ids = gastos_service._seleccionar_apartamentos_por_criterio(db, datos)

    # Debería seleccionar todos los apartamentos activos
    assert len(apartamentos_ids) > 0
    print(f"✅ TEST PASADO: Selección todas torres - {len(apartamentos_ids)} apartamentos")


def test_seleccion_apartamentos_torre_especifica(db: Session):
    """Test que selecciona apartamentos de torre específica"""
    datos = GastoCompletoCreate(
        monto_usd=Decimal("100"),
        descripcion="Test torre específica",
        categoria="TEST",
        fecha_gasto=date(2024, 1, 1),
        criterio_seleccion=CriterioSeleccion.TORRE_ESPECIFICA,
        torre_id=1,  # Torre A
    )

    apartamentos_ids = gastos_service._seleccionar_apartamentos_por_criterio(db, datos)

    assert len(apartamentos_ids) > 0
    # Verificar que todos los apartamentos son de la torre 1
    from app.models.torres import Apartamento

    apartamentos = db.query(Apartamento).filter(Apartamento.id.in_(apartamentos_ids)).all()
    for apto in apartamentos:
        assert apto.torre_id == 1
    print(f"✅ TEST PASADO: Selección torre específica - {len(apartamentos_ids)} apartamentos")
