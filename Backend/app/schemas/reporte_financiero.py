from pydantic import (
    BaseModel,
)
from typing import Optional
from datetime import date


# ==============================
# ---- Reportes Financieros ----
# ==============================


class ReporteFinancieroCreate(BaseModel):
    periodo: str
    total_gastos_fijos: float
    total_gastos_variables: float
    total_general: float
    generado_por: str


class ReporteFinancieroUpdate(BaseModel):
    total_gastos_fijos: Optional[float]
    total_gastos_variables: Optional[float]
    total_general: Optional[float]


class ReporteFinancieroOut(ReporteFinancieroCreate):
    id: int
    fecha_generacion: date

    class Config:
        from_attributes = True
