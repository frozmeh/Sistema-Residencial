from fastapi import FastAPI
from .database import engine
from . import models
from .routers import usuario, rol, residente, apartamento, pago, gastos, reporte_financiero, incidencias, reservas, notificaciones, auditoria




# Crear todas las tablas si no existen
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Registrar router
app.include_router(usuario.router)
app.include_router(rol.router)
app.include_router(residente.router)
app.include_router(apartamento.router)
app.include_router(pago.router)
app.include_router(gastos.router)
app.include_router(reporte_financiero.router)
app.include_router(incidencias.router)
app.include_router(reservas.router)
app.include_router(notificaciones.router)
app.include_router(auditoria.router)


@app.get("/")
def inicio():
    return {"mensaje": "Bienvenido a la API de la tesis"}
