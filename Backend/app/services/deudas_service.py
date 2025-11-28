from sqlalchemy.orm import Session
from ..models import Cargo, Gasto


class DeudasService:
    def obtener_deuda_mensual(self, db: Session, apartamento_id: int, periodo: str):
        """Cuánto debe el apartamento en un mes específico"""
        cargos = (
            db.query(Cargo)
            .join(Gasto)
            .filter(
                Cargo.id_apartamento == apartamento_id,
                Gasto.periodo == periodo,
                Cargo.estado.in_(["Pendiente", "Parcial", "Vencido"]),
            )
            .all()
        )

        return {
            "periodo": periodo,
            "total_deuda_usd": sum(cargo.saldo_pendiente_usd for cargo in cargos),
            "total_deuda_ves": sum(cargo.saldo_pendiente_ves for cargo in cargos),
            "cargos": cargos,
        }

    def obtener_historial_12_meses(self, db: Session, apartamento_id: int):
        """Deuda de los últimos 12 meses"""
        # Calcular los últimos 12 periodos (ej: desde Ene 2025 hasta Nov 2025)
        periodos = [f"2025-{str(i).zfill(2)}" for i in range(1, 12)]

        historial = []
        for periodo in periodos:
            deuda_mensual = self.obtener_deuda_mensual(db, apartamento_id, periodo)
            historial.append(deuda_mensual)

        return historial

    def obtener_deuda_total(self, db: Session, apartamento_id: int):
        """Deuda acumulada de TODOS los meses pendientes"""
        cargos_pendientes = (
            db.query(Cargo)
            .filter(Cargo.id_apartamento == apartamento_id, Cargo.estado.in_(["Pendiente", "Parcial", "Vencido"]))
            .all()
        )

        return {
            "total_deuda_usd": sum(cargo.saldo_pendiente_usd for cargo in cargos_pendientes),
            "total_deuda_ves": sum(cargo.saldo_pendiente_ves for cargo in cargos_pendientes),
            "cargos_pendientes": len(cargos_pendientes),
        }
