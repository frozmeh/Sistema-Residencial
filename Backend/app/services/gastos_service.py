# services/gastos_service.py (CORREGIDO para tu modelo exacto)
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from decimal import Decimal
import logging
from datetime import date
import json
from ..models.financiero import Gasto, TipoGastoEnum, EstadoGastoEnum, DistribucionGasto
from ..models.torres import Apartamento, Piso, Torre
from ..schemas.financiero import GastoCompletoCreate, GastoFilter

from ..services.tasa_cambio_service import tasa_cambio_service
from ..services.distribucion_service import distribucion_service

logger = logging.getLogger(__name__)


class GastosService:

    def crear_gasto_completo(self, db: Session, datos: GastoCompletoCreate) -> Gasto:
        """
        Versión SIMPLIFICADA usando los schemas actualizados
        """
        try:
            # 1. Obtener tasa
            tasa_cambio = tasa_cambio_service.obtener_tasa_actual(db)
            if not tasa_cambio:
                raise ValueError("No hay tasa de cambio disponible")

            # 2. Calcular monto VES
            monto_ves = datos.monto_usd * tasa_cambio.tasa_usd_ves
            periodo = datos.fecha_gasto.strftime("%Y-%m")

            # 3. Obtener o crear reporte
            reporte = self._obtener_o_crear_reporte(db, periodo)

            # 4. Crear gasto SIMPLIFICADO
            gasto = Gasto(
                id_reporte_financiero=reporte.id,
                tipo_gasto=datos.tipo_gasto,
                descripcion=datos.descripcion,
                monto_total_usd=datos.monto_usd,
                monto_total_ves=monto_ves,
                tasa_cambio=tasa_cambio.tasa_usd_ves,
                criterio_seleccion=datos.criterio_seleccion.value,  # Convertir Enum a string
                parametros_criterio=datos.obtener_parametros_json(),  # JSON con parámetros
                fecha_gasto=datos.fecha_gasto,
                fecha_tasa_bcv=tasa_cambio.fecha,
                responsable=datos.responsable,
                estado=EstadoGastoEnum.PENDIENTE,
                periodo=periodo,
            )

            db.add(gasto)
            db.flush()

            # 5. Seleccionar y distribuir
            apartamentos_ids = self._seleccionar_apartamentos_por_criterio(db, datos)

            if apartamentos_ids:
                distribuciones = distribucion_service.calcular_distribucion_gasto(
                    db=db,
                    gasto=gasto,
                    apartamentos_ids=apartamentos_ids,
                    forzar_equitativa=datos.forzar_distribucion_equitativa,
                )

                if distribuciones:
                    distribucion_service.guardar_distribuciones(db, distribuciones)
                    gasto.estado = EstadoGastoEnum.DISTRIBUIDO

            db.commit()
            return self._obtener_gasto_con_relaciones(db, gasto.id)

        except Exception as e:
            db.rollback()
            logger.error(f"Error creando gasto: {str(e)}")
            raise

    def eliminar_y_recrear_gasto(self, db: Session, gasto_id: int, nuevos_datos: GastoCompletoCreate) -> Gasto:
        """
        ✅ MÁS PRÁCTICO: Eliminar gasto mal hecho y crear uno nuevo correcto
        """
        try:
            # 1. Obtener datos del gasto original para referencia
            gasto_original = db.query(Gasto).filter(Gasto.id == gasto_id).first()
            if not gasto_original:
                raise ValueError(f"Gasto {gasto_id} no encontrado")

            # 2. Eliminar gasto existente (esto elimina distribuciones por CASCADE)
            db.delete(gasto_original)
            db.commit()

            # 3. Crear NUEVO gasto con datos corregidos
            nuevo_gasto = self.crear_gasto_completo(db, nuevos_datos)

            logger.info(f"✅ Gasto {gasto_id} reemplazado por {nuevo_gasto.id}")
            return nuevo_gasto

        except Exception as e:
            db.rollback()
            logger.error(f"Error recreando gasto: {str(e)}")
            raise

    def _obtener_gasto_con_relaciones(self, db: Session, gasto_id: int) -> Gasto:
        """Carga eager de relaciones"""
        return (
            db.query(Gasto)
            .options(
                joinedload(Gasto.distribuciones)
                .joinedload(DistribucionGasto.apartamento)
                .joinedload(Apartamento.tipo_apartamento)
            )
            .filter(Gasto.id == gasto_id)
            .first()
        )

    def _obtener_o_crear_reporte(self, db: Session, periodo: str):
        """Obtiene o crea reporte financiero"""
        from ..models.financiero import ReporteFinanciero

        reporte = db.query(ReporteFinanciero).filter(ReporteFinanciero.periodo == periodo).first()
        if not reporte:
            reporte = ReporteFinanciero(
                periodo=periodo,
                generado_por="Sistema Automático",
                total_ingresos_usd=0,
                total_gastos_usd=0,
                saldo_final_usd=0,
                total_ingresos_ves=0,
                total_gastos_ves=0,
                saldo_final_ves=0,
                estado="Abierto",
            )
            db.add(reporte)
            db.flush()
        return reporte

    def generar_cargos_automaticos(self, db: Session, gasto_id: int) -> bool:
        """
        Genera cargos automáticamente para un gasto distribuido
        """
        try:
            from .cargos_service import cargos_service

            # 1. Verificar que el gasto existe y está distribuido
            gasto = db.query(Gasto).filter(Gasto.id == gasto_id).first()
            if not gasto:
                raise ValueError(f"Gasto {gasto_id} no encontrado")

            if gasto.estado != EstadoGastoEnum.DISTRIBUIDO:
                raise ValueError(f"Gasto {gasto_id} no está distribuido")

            # 2. Generar cargos
            cargos_creados = cargos_service.generar_cargos_desde_gasto(db, gasto_id)

            logger.info(f"✅ {len(cargos_creados)} cargos generados para gasto {gasto_id}")
            return True

        except Exception as e:
            logger.error(f"Error generando cargos para gasto {gasto_id}: {str(e)}")
            raise

    def obtener_gastos_por_filtro(self, db: Session, filtro: GastoFilter) -> List[Gasto]:
        """
        Obtiene gastos aplicando filtros con eager loading de relaciones
        """
        try:
            query = db.query(Gasto).options(
                joinedload(Gasto.distribuciones)
                .joinedload(DistribucionGasto.apartamento)
                .joinedload(Apartamento.tipo_apartamento)
            )

            # Aplicar filtros
            if filtro.tipo_gasto:
                query = query.filter(Gasto.tipo_gasto == filtro.tipo_gasto)

            if filtro.fecha_inicio:
                query = query.filter(Gasto.fecha_gasto >= filtro.fecha_inicio)

            if filtro.fecha_fin:
                query = query.filter(Gasto.fecha_gasto <= filtro.fecha_fin)

            if filtro.responsable:
                query = query.filter(Gasto.responsable.ilike(f"%{filtro.responsable}%"))

            # Ordenar por fecha de gasto (más reciente primero)
            query = query.order_by(Gasto.fecha_gasto.desc(), Gasto.id.desc())

            gastos = query.all()
            logger.info(f"✅ Encontrados {len(gastos)} gastos con los filtros aplicados")

            return gastos

        except Exception as e:
            logger.error(f"Error obteniendo gastos por filtro: {str(e)}")
            raise

    # Los métodos de selección se mantienen igual...
    def _seleccionar_apartamentos_por_criterio(self, db: Session, datos: GastoCompletoCreate) -> List[int]:
        """
        MISMA LÓGICA de selección
        """
        try:
            if datos.criterio_seleccion == "todas_torres":
                return self._obtener_todos_apartamentos(db)

            elif datos.criterio_seleccion == "torre_especifica":
                if not datos.torre_id:
                    raise ValueError("Se requiere torre_id para criterio torre_especifica")
                return self._obtener_apartamentos_por_torre(db, datos.torre_id)

            elif datos.criterio_seleccion == "piso_especifico":
                if not datos.torre_id or not datos.piso:
                    raise ValueError("Se requiere torre_id y piso para criterio piso_especifico")
                return self._obtener_apartamentos_por_piso(db, datos.torre_id, datos.piso)

            elif datos.criterio_seleccion == "apartamentos_especificos":
                if not datos.apartamentos_ids:
                    raise ValueError("Se requiere apartamentos_ids para criterio apartamentos_especificos")
                return self._obtener_apartamentos_especificos(db, datos.apartamentos_ids)

            else:
                raise ValueError(f"Criterio de selección no válido: {datos.criterio_seleccion}")

        except Exception as e:
            logger.error(f"Error seleccionando apartamentos: {str(e)}")
            raise

    def _obtener_todos_apartamentos(self, db: Session) -> List[int]:
        apartamentos = db.query(Apartamento.id).all()
        return [apto.id for apto in apartamentos]

    def _obtener_apartamentos_por_torre(self, db: Session, torre_id: int) -> List[int]:
        apartamentos = db.query(Apartamento.id).join(Piso).filter(Piso.id_torre == torre_id).all()
        return [apto.id for apto in apartamentos]

    def _obtener_apartamentos_por_piso(self, db: Session, torre_id: int, piso: int) -> List[int]:
        apartamentos = (
            db.query(Apartamento.id)
            .join(Piso)  # ✅ JOIN con Piso
            .filter(Piso.id_torre == torre_id, Piso.numero == piso)  # ✅ Torre específica  # ✅ Piso específico
            .all()
        )
        return [apto.id for apto in apartamentos]

    def _obtener_apartamentos_especificos(self, db: Session, apartamentos_ids: List[int]) -> List[int]:
        apartamentos = db.query(Apartamento.id).filter(Apartamento.id.in_(apartamentos_ids)).all()
        return [apto.id for apto in apartamentos]


# Instancia global
gastos_service = GastosService()
