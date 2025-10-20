## Instrucciones rápidas para agentes de código (Proyecto: Sistema-Residencial)

Objetivo: facilitar a un agente (Copilot/IA) ser productivo de inmediato con convenciones y puntos críticos del repositorio.

- Proyecto principal: Backend en Python (FastAPI) y Frontend en React (Vite) ubicado en `Backend/` y `Frontend/sistema-residencial/`.
- Backend usa SQLAlchemy (ORM) + PostgreSQL; carga variables desde `Backend/.env` (ver `Backend/app/database.py`).

Puntos estructurales clave (leer antes de editar):
- `Backend/app/main.py` — punto de entrada FastAPI. Registra routers y crea tablas con `Base.metadata.create_all(bind=engine)`. También ejecuta `inicializar_roles(db)` para poblar roles fijos.
- `Backend/app/database.py` — define `engine`, `SessionLocal`, `Base` y la función `get_db()` usada por dependencias de FastAPI.
- `Backend/app/crud/` — contiene la lógica de acceso y mutación a la base de datos. Prefiere modificar/añadir funciones aquí en lugar de directamente en routers.
- `Backend/app/routers/` — rutas agrupadas por entidad (usuarios, roles, auth, pagos, gastos...). Cada archivo define un `APIRouter` y usa `get_db` para la sesión.
- `Backend/app/schemas/` — modelos Pydantic (entrada/salida). Respeta los modelos existentes para `response_model`.
- `Backend/app/utils/seguridad2.py` — función `validar_permiso(usuario, entidad, accion)` que valida permisos basados en JSON de permisos en `roles`.
- `Backend/app/utils/seguridad.py` — helpers para hashing/verificación de contraseñas (PassLib bcrypt).

Convenciones de desarrollo y patrones observados:
- Separación clara: `routers` (endpoints) -> `crud` (lógica DB) -> `schemas` (DTOs) -> `models` (SQLAlchemy). Sigue este flujo al añadir features.
- Todas las interacciones con DB hacen `db: Session = Depends(get_db)` en endpoints. Usa `crud` para nada más que la consulta/actualización.
- Roles y permisos: los roles guardan un campo `permisos` (JSON). Usa `validar_permiso` antes de acciones sensibles. Revísalo en `Backend/app/utils/seguridad2.py`.
- Encriptación: utiliza `passlib` con bcrypt (ver `routers/auth.py` y `utils/seguridad.py`). No introducir otro esquema de hashing sin actualizar toda la lógica.

Comandos y workflows (arranque, tests, front):
- Backend (desarrollo): desde la raíz del repo, entra a `Backend/` y usa uvicorn con la app FastAPI.

  Ejemplo (bash):
  ```bash
  # instalar deps en un venv
  python -m venv .venv
  source .venv/Scripts/activate  # Windows (git bash) -> usar path correcto
  pip install -r Backend/requirements.txt

  # exportar .env en Backend/.env (POSTGRES_* variables)

  # lanzar servidor
  uvicorn app.main:app --reload --reload-dir Backend/app --port 8000 --app-dir Backend/app
  ```

- Frontend (desarrollo):
  ```bash
  cd Frontend/sistema-residencial
  npm install
  npm run dev
  ```

Consideraciones importantes para ediciones de código:
- Mantener los contratos Pydantic en `schemas/`. Al cambiar un schema, actualiza los `response_model` en routers y cualquier uso en `crud/`.
- Evitar llamadas directas a `Session` fuera de `crud/` y routers; centraliza la lógica de persistencia en `crud/`.
- Cuando añadas campos a modelos SQLAlchemy (`Backend/app/models/*.py`), crea o actualiza migraciones con Alembic (si está configurado). Actualmente el proyecto llama `Base.metadata.create_all(...)` en `main.py`.
- Para permisos, actualiza el JSON de `roles` y el initializer en `Backend/app/crud/inicializar_roles` si corresponde.

Ejemplos concretos referenciados:
- Login: `Backend/app/routers/auth.py` — usa `passlib` para verificar contraseña y retorna datos básicos (id, nombre, rol, correo).
- Usuarios: `Backend/app/routers/usuarios.py` — endpoints CRUD que delegan a `crud/` (ver `crear_usuario`, `obtener_usuarios`, `cambiar_password`).
- DB helpers: `Backend/app/utils/db_helpers.py` — `guardar_y_refrescar(db, obj)` patrón usado para commit+refresh.

Errores y límites detectables por un agente:
- No asumas migraciones automáticas: aunque hay `alembic` en requirements, el código usa `create_all()`; confirmar con el mantenedor si usar Alembic.
- Variables de entorno necesarias: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB (cargadas en `database.py`).
- Autenticación de tokens no implementada: El `/auth/login` devuelve datos de usuario sin JWT; si necesitas token-based auth, confirmar la estrategia antes de añadirla.

Si modificas rutas o contratos, agrega pruebas unitarias en `Backend/` (hay `pytest` en requirements). Añade tests pequeños que usen `TestClient` de FastAPI para validar endpoints críticos.

Preguntas habituales para aclarar con mantenedores:
- ¿Deseamos introducir JWT u otro mecanismo de sesión (actualmente no hay tokens)?
- ¿Se usa Alembic para migraciones en producción o se confía en `create_all`?

Si quieres, adapto y reduzco esto a un checklist más corto o añado ejemplos de commit/PR recomendados.
