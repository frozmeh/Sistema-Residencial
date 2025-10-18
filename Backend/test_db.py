from app.database import engine

try:
    conn = engine.connect()
    print("✅ Conexión a PostgreSQL exitosa")
    conn.close()
except Exception as e:
    print("❌ Error al conectar a PostgreSQL:", e)
