# Estrategia de pruebas — primera versión ejecutable

## Backend
- Pytest como runner.
- Pruebas HTTP con FastAPI TestClient.
- Cubrir el contrato de `GET /api/v1/health`.
- Cubrir readiness con dependencias disponibles y con PostgreSQL o Redis no disponibles.
- Las pruebas de integración requieren PostgreSQL y Redis reales o servicios equivalentes.
- Validar la migración inicial ejecutando Alembic contra una base vacía.

## Frontend
- El criterio de esta etapa es el build TypeScript/Vite sin errores.
- La conexión de la pantalla con la API se verifica manualmente en navegador o mediante comprobación de integración cuando exista un runner E2E aprobado.

## Infraestructura
- Validar construcción y arranque de los cuatro servicios con Docker Compose.
- Verificar healthchecks de PostgreSQL, Redis y API.
- Comprobar los endpoints de salud y readiness.
- Confirmar que detener PostgreSQL o Redis provoca readiness HTTP 503.

## CI
El workflow ejecuta pruebas backend con servicios PostgreSQL/Redis, build frontend y validación/build de Docker Compose.

## Reporte
Distinguir pruebas ejecutadas, pruebas que pasaron, fallaron y no se pudieron ejecutar. No declarar cobertura ni resultados no medidos.
