#
from dotenv import load_dotenv
from pathlib import Path
import os  # load_dotenv y os cargan variables de entorno desde el archivo .env
from sqlalchemy import create_engine  # Función que crea la conexión con la DB

"""declarative_base = Crear clases que representen tablas en la DB
sessionmaker = crea sesiones con la base de datos para consultas / guardar datos"""
from sqlalchemy.orm import sessionmaker, declarative_base

from urllib.parse import quote_plus  # Permite caracteres especiales en password


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))
# Esto carga las variables del .env

DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = quote_plus(os.getenv("POSTGRES_PASSWORD"))
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    DATABASE_URL
)  # Crea el motor de conexión con la base de datos, pasando todas las operaciones de lectura/escritura
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
"""Crea una clase de sesión. Cada vez que quieras interactuar con la base, creas un db = SessionLocal().
autocommit=False: no se guardan cambios automáticamente, debes usar db.commit().
autoflush=False: no manda cambios automáticamente antes de consultar, se hace manualmente."""
Base = declarative_base()  # Clase base que se usará para crear modelos(tablas)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
