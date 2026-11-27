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
- Verificar carga autenticada con CSRF, normalización WebP, límites, reemplazo, eliminación y acceso exclusivo del titular a su fotografía.

## Social
- Cubrir requisito de vinculación aprobada para lectura y escritura.
- Verificar aislamiento estricto entre unidades y ocultamiento de autores inactivos o desvinculados.
- Verificar CSRF, no-cache, paginación estable, normalización y límite de texto.
- Verificar que solo el autor pueda eliminar una publicación y comentarios propios.
- Verificar aislamiento por unidad en lectura/creación de comentarios y reacciones.
- Verificar idempotencia y unicidad de reacciones, conteos del feed, CSRF y respuestas privadas.
- Verificar que comentarios y publicaciones no expongan correo ni UUID de cuenta.
- Verificar formato real del archivo, recodificación WebP, límites de tamaño/píxeles/cantidad, eliminación EXIF y rechazo de SVG/GIF animado.
- Verificar autorización de carga y descarga por autor/unidad, CSRF, no-store/nosniff y limpieza de objetos tras commit/rollback.

## Frontend
- Build TypeScript/Vite.
- Node.js test runner nativo para pruebas unitarias de lógica TypeScript pura, sin dependencias adicionales; Node 22.15 o superior.
- `npm test` valida la normalización del formulario de perfil y el límite de tamaño de archivo en el cliente (la validación definitiva sigue siendo responsabilidad del servidor).
- authenticatedFetch renueva token CSRF y reintenta una vez ante el error específico de CSRF.
- Pruebas de componentes, E2E y pruebas multi-pestaña quedan pendientes de seleccionar e incorporar una herramienta de DOM/navegador.
\n## Infraestructura
- Validar configuración y build de Docker Compose.
- Verificar healthchecks de PostgreSQL, Redis y API.
- API ejecutada como usuario sin privilegios.
- Volumen local de medios escribible por el usuario de API y no publicado como directorio web.
- Configuración de producción exige S3-compatible privado y credenciales; no generar URLs públicas.
- Producción exige Redis con contraseña y cookies Secure.
- La imagen optimizada de producción para frontend queda diferida a la etapa de despliegue.

## Seguridad de cadena de suministro
- Gitleaks escanea el historial del repositorio en CI.
- Ruff analiza backend.
- El frontend versiona package-lock.json y utiliza `npm ci` en CI para instalaciones reproducibles.

## CI
El workflow ejecuta backend (PostgreSQL, migraciones, tests y Ruff), build frontend, escaneo de secretos y validación/build de contenedores.

## Reporte
Distinguir pruebas ejecutadas, pasadas, fallidas y no ejecutadas. No declarar cobertura ni resultados no medidos.
