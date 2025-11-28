# quick_test_gastos.py
from app.database import SessionLocal
from app.services.gastos_service import gastos_service
from app.schemas.financiero import GastoCompletoCreate, CriterioSeleccion
from decimal import Decimal
from datetime import date


def quick_test():
    """Prueba rápida de todas las funciones"""
    db = SessionLocal()

    try:
        print("🧪 INICIANDO PRUEBAS RÁPIDAS DE gastos_service...")

        # Test 1: Selección todas torres
        print("\n1. Probando selección TODAS_TORRES...")
        datos = GastoCompletoCreate(
            monto_usd=Decimal("100"),
            descripcion="Prueba rápida",
            categoria="TEST",
            fecha_gasto=date.today(),
            criterio_seleccion=CriterioSeleccion.TODAS_TORRES,
        )
        ids = gastos_service._seleccionar_apartamentos_por_criterio(db, datos)
        print(f"   ✅ Apartamentos seleccionados: {len(ids)}")

        # Test 2: Crear gasto completo
        print("\n2. Probando creación completa de gasto...")
        gasto = gastos_service.crear_gasto_completo(db, datos)
        print(f"   ✅ Gasto creado: ID {gasto.id}, Distribuido: {gasto.distribuido}")

        # Test 3: Obtener gastos por filtro
        print("\n3. Probando obtención con filtros...")
        from app.schemas.financiero import GastoFilter

        filtro = GastoFilter()
        gastos = gastos_service.obtener_gastos_por_filtro(db, filtro)
        print(f"   ✅ Gastos encontrados: {len(gastos)}")

        print("\n🎉 TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")

    except Exception as e:
        print(f"❌ ERROR en pruebas: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    quick_test()
