from app.models import Apartamento, Piso, Torre
from app.database import SessionLocal
from sqlalchemy.orm import joinedload

# Crear la sesión
session = SessionLocal()

# Parámetros de búsqueda
id_torre = 3
numero_piso = 6
numero_apartamento = "6-7"

# Consulta
apartamento = (
    session.query(Apartamento)
    .join(Piso)
    .join(Torre)
    .options(joinedload(Apartamento.tipo_apartamento))
    .filter(Torre.id == id_torre, Piso.numero == numero_piso, Apartamento.numero == numero_apartamento)
    .first()
)

if apartamento:
    print("Apartamento encontrado:")
    print("Número:", apartamento.numero)
    print("Tipo:", apartamento.tipo_apartamento.nombre)
else:
    print("Apartamento no encontrado")
