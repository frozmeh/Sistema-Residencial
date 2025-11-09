from fastapi import FastAPI
from .database import engine, Base, SessionLocal
from .routers import (
    auth,
    # incidencias,
    # reservas,
    # notificaciones,,
    # reporte_financiero,
)
from .routers.admin import (
    auditoria,
    roles,
    torres,
    usuarios as admin_usuarios,
    residentes as admin_residentes,
    gastos as admin_gastos,
    pagos as admin_pagos,
)
from .routers.residente import (
    perfil_usuario,
    perfil_residente,
    gastos_apartamento as residente_gastos,
    pagos_residente as residente_pagos,
)
from . import initial_data

# from . import initial_data
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Sistema de Gestión de Residencias")

# Permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def startup_event():
    with SessionLocal() as db:
        initial_data.inicializar_db(db)


# Incluir routers
app.include_router(auth.router)
app.include_router(roles.router)
app.include_router(admin_usuarios.router)
app.include_router(perfil_usuario.router)
app.include_router(admin_residentes.router)
app.include_router(perfil_residente.router)
app.include_router(torres.router)
app.include_router(admin_gastos.router)
app.include_router(residente_gastos.router)
app.include_router(admin_pagos.router)
app.include_router(residente_pagos.router)
# app.include_router(incidencias.router)
# app.include_router(reservas.router)
# app.include_router(notificaciones.router)
app.include_router(auditoria.router)
# app.include_router(reporte_financiero.router)


@app.get("/")
def root():
    return {"mensaje": "API del sistema de condominio funcionando"}
