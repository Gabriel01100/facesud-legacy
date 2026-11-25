# Arquitectura objetivo

## Enfoque
Monorepo con límites de dominio claros. Aunque se diseña para poder separar servicios, comenzar con una aplicación modular y pocos despliegues. No adoptar microservicios distribuidos prematuramente. Ningún módulo escribe directamente en las tablas privadas de otro.

## Stack
FastAPI + Pydantic; PostgreSQL + SQLAlchemy + Alembic; React (TypeScript recomendado); Pytest; Docker Compose; Nginx; almacenamiento S3-compatible; OpenAPI. Timestamps UTC. Redis/colas solo si aparece una necesidad concreta.

## Módulos
- **Identity:** cuentas, credenciales, sesiones, autenticación y perfil básico.
- **Community:** unidades, jerarquía, membresías, solicitudes y roles locales.
- **Social:** publicaciones, medios, feed, comentarios, reacciones y amistades.
- **Trust & Safety:** reportes, bloqueos, moderación, rate limits y auditoría.
- **Notifications:** notificaciones internas.
- **Donations:** futuro, fuera del MVP.

## Comunicación
REST para operaciones síncronas; contratos OpenAPI versionados. Sin Kafka/RabbitMQ inicialmente. Evaluar cola y patrón outbox cuando existan tareas asíncronas reales. Una instancia PostgreSQL puede alojar inicialmente los módulos, con propiedad lógica de datos.

## Despliegue conceptual
Navegador → HTTPS/reverse proxy → React y FastAPI → PostgreSQL y almacenamiento de medios.

## Estructura sugerida
`apps/api/app/{core,modules/identity,modules/community,modules/social,modules/trust_safety,modules/notifications,shared}`.
`apps/web/src/{app,features,shared}`.

## Frontend
Se reconstruye desde cero; no migrar acoplamientos del cliente PHP anterior. Centralizar cliente HTTP, sesión, validaciones de interfaz y estados de carga/error/vacío. El backend sigue siendo la autoridad de permisos. Responsive y accesibilidad desde el inicio.
