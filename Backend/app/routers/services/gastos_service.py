# routers/gastos.py (MODIFICADO para usar tu schema)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from fastapi import Query
import logging


from ...database import get_db
from ...schemas.financiero import (
    GastoCompletoCreate,
    GastoResponse,
    GastoFilter,
    GastoConDistribucionResponse,
)  # ✅ Usar TU schema
from ...services.gastos_service import gastos_service

router = APIRouter(prefix="/gastos", tags=["gastos"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=GastoResponse, status_code=status.HTTP_201_CREATED)
def crear_gasto_completo(datos: GastoCompletoCreate, db: Session = Depends(get_db)):
    """
    Crear un gasto completo usando TU schema existente
    """
    try:
        return gastos_service.crear_gasto_completo(db, datos)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.put(
    "/{gasto_id}/corregir",
    response_model=GastoConDistribucionResponse,
    status_code=status.HTTP_200_OK,
    summary="Corregir gasto con errores",
    description="""
    Elimina un gasto mal distribuido y crea uno nuevo con los datos corregidos.

    **Casos de uso:**
    - Te equivocaste de apartamentos (ej: 10,11 → 10,12)
    - Te equivocaste de torre o piso
    - Error en el monto o descripción
    - Criterio de selección incorrecto
    """,
)
def corregir_gasto(gasto_id: int, datos_corregidos: GastoCompletoCreate, db: Session = Depends(get_db)):
    """
    Corrige un gasto eliminando el original y creando uno nuevo con los datos corregidos.

    **Ejemplo de cuerpo de solicitud:**
    ```json
    {
        "monto_usd": 500.00,
        "descripcion": "Reparación filtraciones (corregido)",
        "tipo_gasto": "Variable",
        "fecha_gasto": "2024-01-15",
        "responsable": "Administrador",
        "criterio_seleccion": "apartamentos_especificos",
        "apartamentos_ids": [10, 12],
        "forzar_distribucion_equitativa": false
    }
    ```
    """
    try:
        # Verificar que el gasto existe antes de intentar corregirlo
        from ...models.financiero import Gasto

        gasto_existente = db.query(Gasto).filter(Gasto.id == gasto_id).first()
        if not gasto_existente:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Gasto {gasto_id} no encontrado")

        # Corregir el gasto
        gasto_corregido = gastos_service.eliminar_y_recrear_gasto(db, gasto_id, datos_corregidos)

        # Construir respuesta completa con distribuciones
        from ...schemas.financiero import GastoConDistribucionResponse

        respuesta = GastoConDistribucionResponse(
            gasto=gasto_corregido,
            distribuciones=gasto_corregido.distribuciones,
            resumen={
                "monto_total_usd": gasto_corregido.monto_total_usd,
                "monto_total_ves": gasto_corregido.monto_total_ves,
                "total_apartamentos": len(gasto_corregido.distribuciones),
            },
        )

        return respuesta

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Log del error completo para debugging
        import traceback

        logger.error(f"Error en corrección de gasto {gasto_id}: {str(e)}")
        logger.error(traceback.format_exc())

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno al corregir el gasto: {str(e)}"
        )


@router.post("/{gasto_id}/generar-cargos", status_code=status.HTTP_200_OK)
def generar_cargos_automaticos(gasto_id: int, db: Session = Depends(get_db)):
    """
    🚧 PREPARAR generación de cargos (FUNCIONALIDAD FUTURA)
    - Prepara el sistema para generar cargos
    - Valida que el gasto esté distribuido
    - Muestra información de preparación
    """
    try:
        success = gastos_service.generar_cargos_automaticos(db, gasto_id)
        return {
            "message": f"Preparando generación de cargos para gasto {gasto_id}",
            "gasto_id": gasto_id,
            "estado": "preparacion_cargos",
            "nota": "Esta funcionalidad se completará cuando cargos_service esté implementado",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/{gasto_id}", response_model=GastoResponse)
def obtener_gasto_por_id(gasto_id: int, db: Session = Depends(get_db)):
    """
    📋 Obtener un gasto específico por ID con todas sus distribuciones
    - Incluye información completa del gasto
    - Muestra todas las distribuciones con datos de apartamentos
    - Carga relaciones automáticamente
    """
    try:
        # Usar el método de filtro para obtener el gasto específico
        filtro = GastoFilter()  # Filtro vacío para obtener todos
        gastos = gastos_service.obtener_gastos_por_filtro(db, filtro)

        # Buscar el gasto específico por ID
        gasto = next((g for g in gastos if g.id == gasto_id), None)

        if not gasto:
            raise HTTPException(status_code=404, detail=f"Gasto con ID {gasto_id} no encontrado")

        return gasto

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno al obtener gasto: {str(e)}")


@router.get("/filtrar/", response_model=List[GastoResponse])
def filtrar_gastos(
    tipo_gasto: Optional[str] = Query(None, description="Filtrar por tipo: 'Fijo' o 'Variable'"),
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicial (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha final (YYYY-MM-DD)"),
    responsable: Optional[str] = Query(None, description="Nombre del responsable"),
    db: Session = Depends(get_db),
):
    """
    🔍 Buscar gastos aplicando filtros
    - Filtrar por tipo de gasto
    - Filtrar por rango de fechas
    - Filtrar por responsable
    - Combinar múltiples filtros
    """
    try:
        filtro = GastoFilter(
            tipo_gasto=tipo_gasto, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, responsable=responsable
        )
        gastos = gastos_service.obtener_gastos_por_filtro(db, filtro)

        return gastos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/test-seleccion", status_code=status.HTTP_200_OK)
def test_seleccion_apartamentos(
    criterio: str = Query(
        ..., description="Criterio: todas_torres, torre_especifica, piso_especifico, apartamentos_especificos"
    ),
    torre_id: Optional[int] = Query(
        None, description="ID de torre (requerido para torre_especifica y piso_especifico)"
    ),
    piso: Optional[int] = Query(None, description="Número de piso (requerido para piso_especifico)"),
    apartamentos_ids: Optional[str] = Query(
        None, description="IDs de apartamentos separados por coma (requerido para apartamentos_especificos)"
    ),
    db: Session = Depends(get_db),
):
    """
    🧪 Probar selección de apartamentos por criterio
    - Ver qué apartamentos selecciona cada criterio
    - Validar parámetros requeridos
    - Usar para testing y debugging
    """
    try:
        # Convertir string de IDs a lista
        aptos_ids_list = None
        if apartamentos_ids:
            aptos_ids_list = [int(id.strip()) for id in apartamentos_ids.split(",")]

        datos_test = GastoCompletoCreate(
            monto_usd=100,  # Valor dummy para la prueba
            descripcion="Test selección",
            tipo_gasto="Variable",
            fecha_gasto=date.today(),
            responsable="Usuario Test",
            criterio_seleccion=criterio,
            torre_id=torre_id,
            piso=piso,
            apartamentos_ids=aptos_ids_list,
            forzar_distribucion_equitativa=False,
        )

        apartamentos_ids = gastos_service._seleccionar_apartamentos_por_criterio(db, datos_test)

        return {
            "criterio": criterio,
            "parametros": {"torre_id": torre_id, "piso": piso, "apartamentos_ids": aptos_ids_list},
            "apartamentos_seleccionados": apartamentos_ids,
            "total_apartamentos": len(apartamentos_ids),
            "nota": "Esta es una prueba de selección, no se crea ningún gasto real",
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/debug/estado", status_code=status.HTTP_200_OK)
def debug_estado_sistema(db: Session = Depends(get_db)):
    """
    🐛 Debug del estado del sistema de gastos
    - Contar gastos por estado
    - Ver estadísticas generales
    - Usar para monitoreo
    """
    try:
        from ...models.financiero import Gasto, EstadoGastoEnum

        # Contar gastos por estado
        total_gastos = db.query(Gasto).count()
        gastos_pendientes = db.query(Gasto).filter(Gasto.estado == EstadoGastoEnum.PENDIENTE).count()
        gastos_distribuidos = db.query(Gasto).filter(Gasto.estado == EstadoGastoEnum.DISTRIBUIDO).count()
        gastos_cerrados = db.query(Gasto).filter(Gasto.estado == EstadoGastoEnum.CERRADO).count()

        # Obtener últimos gastos
        ultimos_gastos = db.query(Gasto).order_by(Gasto.fecha_creacion.desc()).limit(5).all()

        return {
            "estadisticas": {
                "total_gastos": total_gastos,
                "pendientes": gastos_pendientes,
                "distribuidos": gastos_distribuidos,
                "cerrados": gastos_cerrados,
            },
            "ultimos_gastos": [
                {
                    "id": g.id,
                    "descripcion": g.descripcion,
                    "estado": g.estado.value,
                    "fecha_creacion": g.fecha_creacion,
                }
                for g in ultimos_gastos
            ],
            "servicios_activos": {
                "gastos_service": "✅ Operacional",
                "distribucion_service": "✅ Operacional",
                "tasa_cambio_service": "✅ Operacional",
                "cargos_service": "🚧 Pendiente de implementar",
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en debug: {str(e)}")
