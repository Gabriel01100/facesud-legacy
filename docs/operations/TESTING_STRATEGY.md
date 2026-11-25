# Estrategia de pruebas

## Backend
- Pytest como runner.
- Pruebas HTTP con FastAPI TestClient.
- Cubrir los endpoints de salud y readiness.
- Cubrir Identity: login válido/incorrecto, cuenta pendiente, cookies, sesión actual, logout, CSRF, Origin, expiración absoluta, inactividad y límite de sesiones.
- Las pruebas de integración principales deben ejecutarse contra PostgreSQL; SQLite puede utilizarse para pruebas unitarias cuando no altera la semántica bajo prueba.
- Validar migraciones Alembic contra una base vacía y contra una base con migraciones previas.

## Frontend
- El criterio actual es el build TypeScript/Vite sin errores.
- Las integraciones de autenticación requieren pruebas de navegador/E2E cuando se implemente el frontend.

## Infraestructura
- Validar construcción y arranque de los cuatro servicios con Docker Compose.
- Verificar healthchecks de PostgreSQL, Redis y API.
- Comprobar los endpoints de salud y readiness.
- Confirmar que detener PostgreSQL o Redis provoca readiness HTTP 503.

## CI
El workflow ejecuta pruebas backend, build frontend y validación/build de Docker Compose. Los resultados deben verificarse en el run correspondiente antes de declarar una tarea validada.

## Reporte
Distinguir pruebas ejecutadas, pruebas que pasaron, fallaron y no se pudieron ejecutar. No declarar cobertura ni resultados no medidos.
