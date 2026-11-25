# TASK-001 — Base ejecutable con Docker Compose y CI

## Objetivo
Entregar la primera versión ejecutable de FaceSud en entorno local, con frontend React conectado a una API FastAPI y PostgreSQL y Redis disponibles.

## Alcance
- Monorepo con backend en `apps/api` y frontend en `apps/web`.
- FastAPI con endpoints de salud y readiness.
- PostgreSQL y Redis como servicios internos de Docker Compose.
- SQLAlchemy como capa de conexión SQL y Alembic con revisión inicial vacía.
- Interfaz React/TypeScript responsive que consulta la API.
- Pruebas automatizadas mínimas del endpoint de salud y readiness.
- CI para pruebas backend, build frontend y build de imágenes Compose.
- Documentación operativa y contractual de esta etapa.

## Fuera de alcance
Autenticación, usuarios, perfiles, publicaciones/feed, comentarios/reacciones, amistades, chat, notificaciones de producto, medios, aportes/pagos e integraciones externas.

## Criterios de aceptación
1. `docker compose up --build` construye e inicia los cuatro servicios.
2. PostgreSQL y Redis pasan sus healthchecks y no publican puertos al host.
3. `GET /api/v1/health` responde HTTP 200 con `{"status":"ok"}`.
4. `GET /api/v1/health/ready` responde HTTP 200 cuando PostgreSQL y Redis están disponibles.
5. Readiness responde HTTP 503 si PostgreSQL o Redis no están disponibles.
6. Alembic puede aplicar la revisión inicial sobre una base limpia.
7. Pytest pasa.
8. El build de producción de Vite/TypeScript pasa.
9. La interfaz muestra el estado de conexión real de la API.
10. CI valida backend, frontend y construcción de imágenes Compose.
11. README y documentación operativa reflejan lo efectivamente implementado.

## Seguridad y operación
- No incluir secretos reales.
- Mantener `.env` fuera de Git y proporcionar `.env.example`.
- No publicar puertos de PostgreSQL ni Redis.
- No usar credenciales de ejemplo con `APP_ENV=production`.
- No agregar funcionalidades adicionales a Redis en esta tarea.

## Entrega
Rama `feat/first-executable-version`, PR hacia `main`, sin merge. Informar pruebas ejecutadas y no ejecutadas por separado.
