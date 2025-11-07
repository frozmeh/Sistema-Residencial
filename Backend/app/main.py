from fastapi import FastAPI
from .database import engine, Base, SessionLocal

# Trae el motor de conexión y la clase Base de la database.py
# Importar routers (más adelante)
from .routers import (
    auth,
    pagos,
    gastos,
    incidencias,
    reservas,
    notificaciones,
    auditoria,
    reporte_financiero,
    usuarios,
)
from .routers.admin import (
    roles,
    torres,
    usuarios as admin_usuarios,
    residentes as admin_residentes,
    gastos as admin_gastos,
)
from .routers.residente import perfil_usuario, perfil_residente, gastos_apartamento as residente_gastos
from .crud import inicializar_roles

# from . import initial_data
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="Sistema de Gestión de Residencias"
)  # Crea la instancia principal de la API, donde se registrarán las rutas

# Permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)  # Crear tablas en la base de datos


@app.on_event("startup")
def startup_event():
    with SessionLocal() as db:
        inicializar_roles(db)  # Inicializar roles fijos
        # initial_data.inicializar_db(db)  # Inicializar datos básicos


# Incluir routers (más adelante)
app.include_router(auth.router)
app.include_router(roles.router)
app.include_router(usuarios.router)
app.include_router(admin_usuarios.router)
app.include_router(perfil_usuario.router)
app.include_router(admin_residentes.router)
app.include_router(perfil_residente.router)
app.include_router(torres.router)
app.include_router(admin_gastos.router)
app.include_router(residente_gastos.router)
app.include_router(pagos.router)
app.include_router(incidencias.router)
app.include_router(reservas.router)
app.include_router(notificaciones.router)
app.include_router(auditoria.router)
app.include_router(reporte_financiero.router)


@app.get("/")
def root():
    return {"mensaje": "API del sistema de condominio funcionando"}
