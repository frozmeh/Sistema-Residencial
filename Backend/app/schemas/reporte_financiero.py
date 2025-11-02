from pydantic import BaseModel, model_validator, field_validator
from pydantic.types import condecimal
from typing import Optional, Annotated
from datetime import date
from decimal import Decimal


# ==============================
# ---- Reportes Financieros ----
# ==============================


class ReporteFinancieroCreate(BaseModel):
    periodo: str
    total_gastos_fijos: Annotated[Decimal, condecimal(max_digits=10, decimal_places=2, ge=0)]
    total_gastos_variables: Annotated[Decimal, condecimal(max_digits=10, decimal_places=2, ge=0)]
    generado_por: str
    total_general: Optional[Annotated[Decimal, condecimal(max_digits=10, decimal_places=2, ge=0)]] = None

    # Calcula automáticamente el total_general si no se envía
    @model_validator(mode="after")
    def calcular_total_general(self):
        if self.total_general is None:
            self.total_general = self.total_gastos_fijos + self.total_gastos_variables
        return self

    @field_validator("periodo")
    def validar_periodo(cls, v):
        if not v.strip():
            raise ValueError("El periodo no puede estar vacío")
        return v


class ReporteFinancieroUpdate(BaseModel):
    total_gastos_fijos: Optional[Annotated[Decimal, condecimal(max_digits=10, decimal_places=2, ge=0)]] = None
    total_gastos_variables: Optional[Annotated[Decimal, condecimal(max_digits=10, decimal_places=2, ge=0)]] = None
    total_general: Optional[Annotated[Decimal, condecimal(max_digits=10, decimal_places=2, ge=0)]] = None


class ReporteFinancieroOut(BaseModel):
    id: int
    periodo: str
    total_gastos_fijos: Decimal
    total_gastos_variables: Decimal
    total_general: Decimal
    generado_por: str
    fecha_generacion: date

    class Config:
        from_attributes = True
