from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# > Función para encriptar contraseñas nuevas <
def encriptar_contrasena(contrasena: str):
    return pwd_context.hash(contrasena)


# > Función para verificar contraseñas al iniciar sesión <
def verificar_contrasena(contrasena_plana: str, hash_guardado: str):
    return pwd_context.verify(contrasena_plana, hash_guardado)
