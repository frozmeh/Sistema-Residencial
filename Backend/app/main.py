from fastapi import FastAPI
from .database import engine, Base, SessionLocal

# Trae el motor de conexión y la clase Base de la database.py
# Importar routers (más adelante)
from .routers import (
    roles,
    usuarios,
    residentes,
    auth,
    apartamento,
    pagos,
    gastos,
    incidencias,
    reservas,
    notificaciones,
    auditoria,
    reporte_financiero,
)
from .crud import inicializar_roles
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="Sistema de Gestión de Residencias"
)  # Crea la instancia principal de la API, donde se registrarán las rutas

# Permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)  # Crear tablas en la base de datos

with SessionLocal() as db:
    inicializar_roles(db)  # Inicializar roles fijos

# Incluir routers (más adelante)
app.include_router(usuarios.router)
app.include_router(auth.router)
app.include_router(roles.router)
app.include_router(residentes.router)
app.include_router(apartamento.router)
app.include_router(pagos.router)
app.include_router(gastos.router)
app.include_router(incidencias.router)
app.include_router(reservas.router)
app.include_router(notificaciones.router)
app.include_router(auditoria.router)
app.include_router(reporte_financiero.router)


@app.get("/")
def root():
    return {"mensaje": "API del sistema de condominio funcionando"}
