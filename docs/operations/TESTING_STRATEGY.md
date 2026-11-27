# Estrategia de pruebas

## Backend
- Pytest como runner; Ruff para lint.
- Pruebas HTTP con FastAPI TestClient.
- Cubrir salud/readiness, login, registro, verificación, cookies, CSRF, sesiones, rate limiting, logout, Origin, expiración, inactividad y limpieza.
- Los tests HTTP de Identity usan PostgreSQL aislado en CI mediante IDENTITY_TEST_DATABASE_URL. SQLite queda como fallback local y para pruebas unitarias que no dependen de semántica de concurrencia/SQL.
- CI aplica migraciones Alembic a PostgreSQL y ejecuta tests de Identity contra una segunda base PostgreSQL aislada.
- Agregar pruebas concurrentes de creación/revocación de sesiones y rate limiting bajo carga antes de despliegue público.
- Validar migraciones Alembic contra una base vacía y una base con migraciones previas.

## Profiles
- Cubrir consulta del perfil propio, actualización allowlist, unicidad de username, normalización, CSRF, respuestas privadas no cacheables y ausencia de rutas de consulta ajena.
- Ejecutar migraciones de Profiles contra PostgreSQL y verificar que las tablas Identity existentes no sufren regresiones.

## Social
- Cubrir requisito de vinculación aprobada para lectura y escritura.
- Verificar aislamiento estricto entre unidades y ocultamiento de autores inactivos o desvinculados.
- Verificar CSRF, no-cache, paginación estable, normalización y límite de texto.
- Verificar que solo el autor pueda eliminar una publicación y que la API no exponga correo ni UUID de cuenta.

## Frontend
- Build TypeScript/Vite.
- authenticatedFetch renueva token CSRF y reintenta una vez ante el error específico de CSRF.
- Pruebas E2E y pruebas multi-pestaña pendientes hasta implementar pantallas de autenticación.

## Infraestructura
- Validar configuración y build de Docker Compose.
- Verificar healthchecks de PostgreSQL, Redis y API.
- API ejecutada como usuario sin privilegios.
- Producción exige Redis con contraseña y cookies Secure.
- La imagen optimizada de producción para frontend queda diferida a la etapa de despliegue.

## Seguridad de cadena de suministro
- Gitleaks escanea el historial del repositorio en CI.
- Ruff analiza backend.
- El frontend continúa con npm install hasta que package-lock.json se genere y se versione; no migrar a npm ci sin lockfile completo.

## CI
El workflow ejecuta backend (PostgreSQL, migraciones, tests y Ruff), build frontend, escaneo de secretos y validación/build de contenedores.

## Reporte
Distinguir pruebas ejecutadas, pasadas, fallidas y no ejecutadas. No declarar cobertura ni resultados no medidos.
