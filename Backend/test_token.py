from app.core.security import crear_token, decodificar_token

# Simular usuario
data = {"sub": "1", "rol": "Administrador"}

# Crear token
token = crear_token(data, expira_en_minutos=1)
print("Token generado:\n", token)

# Decodificar token
payload = decodificar_token(token)
print("\nPayload decodificado:\n", payload)
