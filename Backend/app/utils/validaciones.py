import re
from fastapi import HTTPException


# > Función que verifica que se respete el formato email@example.com <
def validar_email(email: str):
    patron_email = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(patron_email, email):
        raise HTTPException(status_code=400, detail="El correo electrónico no tiene un formato válido")
    return True


# > Función para validar que el usuario solo tenga letras, números, guiones bajos y tenga entre 3 y 20 caracteres <
def validar_nombre_usuario(nombre: str):
    patron_nombre = r"^[a-zA-Z0-9_]{3,20}$"
    if not re.match(patron_nombre, nombre):
        raise HTTPException(
            status_code=400,
            detail="El nombre de usuario solo puede contener letras, números y '_' (3-20 caracteres)",
        )
    return True


# > Función para validar contraseña <
# (+8 caracteres, al menos 1 letra mayúscula, al menos 1 letra minúscula, al menos 1 número)
def validar_contrasena(password: str):
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres")
    if not re.search(r"[A-Z]", password):
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe incluir al menos una letra mayúscula",
        )
    if not re.search(r"[a-z]", password):
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe incluir al menos una letra minúscula",
        )
    if not re.search(r"[0-9]", password):
        raise HTTPException(status_code=400, detail="La contraseña debe incluir al menos un número")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe incluir al menos un carácter especial (!@#$...)",
        )
    return True


# > Función general para validar el usuario(nombre, correo, contraseña) <
def validar_usuario(nombre=None, email=None, password=None):
    if nombre:
        validar_nombre_usuario(nombre)
    if email:
        validar_email(email)
    if password:
        validar_contrasena(password)
