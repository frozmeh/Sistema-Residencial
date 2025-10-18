from dotenv import load_dotenv
from pathlib import Path
import os  # load_dotenv y os cargan variables de entorno desde el archivo .env
from sqlalchemy import create_engine  # Función que crea la conexión con la DB
from sqlalchemy.orm import sessionmaker, declarative_base


dotenv_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path)  # Esto carga las variables del .env

print("POSTGRES_PASSWORD:", os.getenv("POSTGRES_PASSWORD"))
