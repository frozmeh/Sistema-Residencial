from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List, Dict
import logging
from datetime import datetime, timedelta

from ... import models, schemas

logger = logging.getLogger(__name__)

# ========================
# ---- Estadísticas ----
# ========================


def estadisticas_residentes(db: Session) -> Dict:
    """Estadísticas detalladas de residentes para dashboard administrativo"""
    try:
        # Totales básicos
        total_residentes = db.query(func.count(models.Residente.id)).scalar()
        residentes_validados = (
            db.query(func.count(models.Residente.id)).filter(models.Residente.estado_aprobacion == "Aprobado").scalar()
        )
        residentes_pendientes = (
            db.query(func.count(models.Residente.id))
            .filter(models.Residente.estado_aprobacion == "Pendiente")
            .scalar()
        )
        residentes_activos = (
            db.query(func.count(models.Residente.id)).filter(models.Residente.estado_operativo == "Activo").scalar()
        )

        # Por tipo de residente
        propietarios = (
            db.query(func.count(models.Residente.id)).filter(models.Residente.tipo_residente == "Propietario").scalar()
        )
        inquilinos = (
            db.query(func.count(models.Residente.id)).filter(models.Residente.tipo_residente == "Inquilino").scalar()
        )

        # Por torre
        residentes_por_torre = (
            db.query(models.Torre.nombre, func.count(models.Residente.id).label("cantidad"))
            .join(models.Piso)
            .join(models.Apartamento)
            .join(models.Residente)
            .group_by(models.Torre.nombre)
            .all()
        )

        # Distribución por estados operativos
        estados_operativos = (
            db.query(models.Residente.estado_operativo, func.count(models.Residente.id).label("cantidad"))
            .group_by(models.Residente.estado_operativo)
            .all()
        )

        # Distribución por estados de aprobación
        estados_aprobacion = (
            db.query(models.Residente.estado_aprobacion, func.count(models.Residente.id).label("cantidad"))
            .group_by(models.Residente.estado_aprobacion)
            .all()
        )

        # Residentes que residen actualmente
        residentes_que_residen = (
            db.query(func.count(models.Residente.id)).filter(models.Residente.reside_actualmente == True).scalar()
        )

        logger.info(f"📊 Estadísticas de residentes generadas: {total_residentes} residentes totales")

        return {
            "totales": {
                "total_residentes": total_residentes,
                "validados": residentes_validados,
                "pendientes": residentes_pendientes,
                "activos": residentes_activos,
                "residentes_que_residen": residentes_que_residen,
                "tasa_aprobacion": (residentes_validados / total_residentes * 100) if total_residentes > 0 else 0,
                "tasa_activacion": (residentes_activos / total_residentes * 100) if total_residentes > 0 else 0,
            },
            "por_tipo": {
                "propietarios": propietarios,
                "inquilinos": inquilinos,
                "porcentaje_propietarios": (propietarios / total_residentes * 100) if total_residentes > 0 else 0,
            },
            "por_torre": [
                {
                    "torre": torre,
                    "cantidad": cantidad,
                    "porcentaje": (cantidad / total_residentes * 100) if total_residentes > 0 else 0,
                }
                for torre, cantidad in residentes_por_torre
            ],
            "distribucion_estados": {
                "operativos": {estado: cantidad for estado, cantidad in estados_operativos},
                "aprobacion": {estado: cantidad for estado, cantidad in estados_aprobacion},
            },
            "metricas_calidad": {
                "aprobados_activos": residentes_validados and residentes_activos,
                "tasa_residencia_activa": (
                    (residentes_que_residen / residentes_activos * 100) if residentes_activos > 0 else 0
                ),
                "proporcion_propietarios_inquilinos": (propietarios / inquilinos) if inquilinos > 0 else propietarios,
            },
        }

    except Exception as e:
        logger.error(f"❌ Error generando estadísticas de residentes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generando estadísticas: {str(e)}")


def obtener_estadisticas_dashboard(db: Session) -> Dict:
    """Estadísticas rápidas para dashboard administrativo"""
    try:
        total = db.query(func.count(models.Residente.id)).scalar()
        aprobados = (
            db.query(func.count(models.Residente.id)).filter(models.Residente.estado_aprobacion == "Aprobado").scalar()
        )
        pendientes = (
            db.query(func.count(models.Residente.id))
            .filter(models.Residente.estado_aprobacion == "Pendiente")
            .scalar()
        )
        activos = (
            db.query(func.count(models.Residente.id)).filter(models.Residente.estado_operativo == "Activo").scalar()
        )

        # Residentes por tipo (para gráfico)
        por_tipo = (
            db.query(models.Residente.tipo_residente, func.count(models.Residente.id).label("cantidad"))
            .group_by(models.Residente.tipo_residente)
            .all()
        )

        # Tendencias (últimos 30 días)
        from datetime import datetime, timedelta

        fecha_limite = datetime.now() - timedelta(days=30)

        nuevos_ultimo_mes = (
            db.query(func.count(models.Residente.id)).filter(models.Residente.fecha_registro >= fecha_limite).scalar()
        )

        aprobados_ultimo_mes = (
            db.query(func.count(models.Residente.id))
            .filter(models.Residente.estado_aprobacion == "Aprobado", models.Residente.fecha_registro >= fecha_limite)
            .scalar()
        )

        return {
            "resumen": {
                "total_residentes": total,
                "aprobados": aprobados,
                "pendientes": pendientes,
                "activos": activos,
                "tasa_aprobacion": (aprobados / total * 100) if total > 0 else 0,
            },
            "distribucion_tipos": {tipo: cantidad for tipo, cantidad in por_tipo},
            "tendencias": {
                "nuevos_ultimo_mes": nuevos_ultimo_mes,
                "aprobados_ultimo_mes": aprobados_ultimo_mes,
                "tasa_aprobacion_mensual": (
                    (aprobados_ultimo_mes / nuevos_ultimo_mes * 100) if nuevos_ultimo_mes > 0 else 0
                ),
            },
            "alertas": {
                "alta_pendientes": pendientes > 10,  # Más de 10 pendientes
                "baja_aprobacion": (
                    (aprobados / total * 100) < 80 if total > 0 else False
                ),  # Menos del 80% de aprobación
                "sin_nuevos_mes": nuevos_ultimo_mes == 0,
            },
        }

    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas de dashboard: {str(e)}")
        return {
            "resumen": {
                "total_residentes": 0,
                "aprobados": 0,
                "pendientes": 0,
                "activos": 0,
                "tasa_aprobacion": 0,
            },
            "distribucion_tipos": {},
            "tendencias": {
                "nuevos_ultimo_mes": 0,
                "aprobados_ultimo_mes": 0,
                "tasa_aprobacion_mensual": 0,
            },
            "alertas": {
                "alta_pendientes": False,
                "baja_aprobacion": False,
                "sin_nuevos_mes": False,
            },
        }


def buscar_residente(db: Session, termino: str, limite: int = 50) -> List[models.Residente]:
    """Búsqueda de residentes por nombre, cédula o correo"""
    try:
        if not termino or len(termino.strip()) < 2:
            raise HTTPException(status_code=400, detail="Término de búsqueda debe tener al menos 2 caracteres")

        termino_busqueda = f"%{termino.strip()}%"

        residentes = (
            db.query(models.Residente)
            .filter(
                models.Residente.nombre.ilike(termino_busqueda)
                | models.Residente.cedula.ilike(termino_busqueda)
                | models.Residente.correo.ilike(termino_busqueda)
            )
            .order_by(models.Residente.nombre.asc())
            .limit(limite)
            .all()
        )

        logger.info(f"🔍 Búsqueda de residentes: '{termino}' -> {len(residentes)} resultados")
        return residentes

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en búsqueda de residentes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en búsqueda: {str(e)}")


def busqueda_avanzada(
    db: Session,
    nombre: Optional[str] = None,
    cedula: Optional[str] = None,
    torre: Optional[str] = None,
    tipo_residente: Optional[str] = None,
    estado_operativo: Optional[str] = None,
    estado_aprobacion: Optional[str] = None,
) -> List[models.Residente]:
    """Búsqueda avanzada de residentes con múltiples filtros"""
    try:
        query = db.query(models.Residente)

        # Aplicar filtros individuales
        if nombre:
            query = query.filter(models.Residente.nombre.ilike(f"%{nombre}%"))
        if cedula:
            query = query.filter(models.Residente.cedula.ilike(f"%{cedula}%"))
        if tipo_residente:
            query = query.filter(models.Residente.tipo_residente == tipo_residente)
        if estado_operativo:
            query = query.filter(models.Residente.estado_operativo == estado_operativo)
        if estado_aprobacion:
            query = query.filter(models.Residente.estado_aprobacion == estado_aprobacion)

        # Filtro por torre (necesita joins)
        if torre:
            query = (
                query.join(models.Apartamento)
                .join(models.Piso)
                .join(models.Torre)
                .filter(func.lower(models.Torre.nombre) == torre.lower())
            )

        residentes = query.order_by(models.Residente.nombre.asc()).all()

        logger.info(f"🔍 Búsqueda avanzada: {len(residentes)} resultados")
        return residentes

    except Exception as e:
        logger.error(f"❌ Error en búsqueda avanzada: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en búsqueda avanzada: {str(e)}")


def contar_residentes(db: Session, solo_activos: bool = True) -> int:
    """Contar residentes totales o solo activos"""
    try:
        query = db.query(func.count(models.Residente.id))
        if solo_activos:
            query = query.filter(models.Residente.estado_operativo == "Activo")
        return query.scalar() or 0

    except Exception as e:
        logger.error(f"❌ Error contando residentes: {str(e)}")
        return 0


def obtener_metricas_tiempo_real(db: Session) -> Dict:
    """Métricas en tiempo real para monitoreo del sistema"""
    try:
        # Residentes por estado
        por_estado_aprobacion = (
            db.query(models.Residente.estado_aprobacion, func.count(models.Residente.id).label("cantidad"))
            .group_by(models.Residente.estado_aprobacion)
            .all()
        )

        por_estado_operativo = (
            db.query(models.Residente.estado_operativo, func.count(models.Residente.id).label("cantidad"))
            .group_by(models.Residente.estado_operativo)
            .all()
        )

        # Registros recientes (últimas 24 horas)
        from datetime import datetime, timedelta

        ultimas_24h = datetime.now() - timedelta(hours=24)

        registros_recientes = (
            db.query(func.count(models.Residente.id)).filter(models.Residente.fecha_registro >= ultimas_24h).scalar()
        )

        # Cambios de estado recientes (última semana)
        ultima_semana = datetime.now() - timedelta(days=7)
        # Nota: Esto requeriría una tabla de auditoría para ser preciso

        return {
            "timestamp": datetime.now().isoformat(),
            "totales": {
                "total_residentes": db.query(func.count(models.Residente.id)).scalar(),
                "registros_ultimas_24h": registros_recientes,
            },
            "distribucion": {
                "aprobacion": {estado: cantidad for estado, cantidad in por_estado_aprobacion},
                "operativo": {estado: cantidad for estado, cantidad in por_estado_operativo},
            },
            "estado_sistema": {
                "saludable": True,  # Podría basarse en métricas específicas
                "alertas": _generar_alertas_sistema(db),
                "ultima_actualizacion": datetime.now().isoformat(),
            },
        }

    except Exception as e:
        logger.error(f"❌ Error obteniendo métricas en tiempo real: {str(e)}")
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "estado_sistema": {"saludable": False, "alertas": ["Error obteniendo métricas"]},
        }


def _generar_alertas_sistema(db: Session) -> List[str]:
    """Generar alertas del sistema basadas en métricas"""
    alertas = []

    try:
        # Alerta por muchos residentes pendientes
        pendientes = (
            db.query(func.count(models.Residente.id))
            .filter(models.Residente.estado_aprobacion.in_(["Pendiente", "Corrección Requerida"]))
            .scalar()
        )

        if pendientes > 10:
            alertas.append(f"Alta cantidad de residentes pendientes: {pendientes}")

        # Alerta por residentes suspendidos
        suspendidos = (
            db.query(func.count(models.Residente.id))
            .filter(models.Residente.estado_operativo == "Suspendido")
            .scalar()
        )

        if suspendidos > 5:
            alertas.append(f"Residentes suspendidos que requieren atención: {suspendidos}")

        # Alerta por falta de nuevos registros (última semana)
        from datetime import datetime, timedelta

        ultima_semana = datetime.now() - timedelta(days=7)

        nuevos_ultima_semana = (
            db.query(func.count(models.Residente.id)).filter(models.Residente.fecha_registro >= ultima_semana).scalar()
        )

        if nuevos_ultima_semana == 0:
            alertas.append("No hay nuevos registros de residentes en la última semana")

        return alertas

    except Exception as e:
        logger.warning(f"⚠️ Error generando alertas del sistema: {str(e)}")
        return ["Error generando alertas del sistema"]


def exportar_estadisticas_residentes(db: Session) -> Dict:
    """Estadísticas completas para exportación o reportes"""
    estadisticas_completas = estadisticas_residentes(db)
    metricas_tiempo_real = obtener_metricas_tiempo_real(db)

    return {
        "metadata": {
            "fecha_generacion": datetime.now().isoformat(),
            "tipo_reporte": "estadisticas_residentes_completo",
            "total_registros": estadisticas_completas["totales"]["total_residentes"],
        },
        "estadisticas": estadisticas_completas,
        "metricas_tiempo_real": metricas_tiempo_real,
        "resumen_ejecutivo": _generar_resumen_ejecutivo(estadisticas_completas),
    }


def _generar_resumen_ejecutivo(estadisticas: Dict) -> Dict:
    """Generar resumen ejecutivo de las estadísticas"""
    total = estadisticas["totales"]["total_residentes"]
    aprobados = estadisticas["totales"]["validados"]
    activos = estadisticas["totales"]["activos"]

    return {
        "puntos_clave": [
            f"Total de residentes: {total}",
            f"Tasa de aprobación: {estadisticas['totales']['tasa_aprobacion']:.1f}%",
            f"Residentes activos: {activos}",
            f"Propietarios vs Inquilinos: {estadisticas['por_tipo']['propietarios']} / {estadisticas['por_tipo']['inquilinos']}",
        ],
        "recomendaciones": _generar_recomendaciones(estadisticas),
        "estado_general": (
            "Excelente"
            if estadisticas["totales"]["tasa_aprobacion"] > 90
            else "Bueno" if estadisticas["totales"]["tasa_aprobacion"] > 70 else "Requiere atención"
        ),
    }


def _generar_recomendaciones(estadisticas: Dict) -> List[str]:
    """Generar recomendaciones basadas en las estadísticas"""
    recomendaciones = []

    if estadisticas["totales"]["pendientes"] > 10:
        recomendaciones.append("Revisar y procesar residentes pendientes de aprobación")

    if estadisticas["totales"]["tasa_aprobacion"] < 80:
        recomendaciones.append("Mejorar proceso de aprobación para aumentar tasa de éxito")

    if estadisticas["por_tipo"]["inquilinos"] > estadisticas["por_tipo"]["propietarios"]:
        recomendaciones.append("Considerar estrategias para atraer más propietarios")

    return recomendaciones
