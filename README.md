# FaceSud

Plataforma social independiente orientada a la comunidad SUD. No es un producto oficial ni implica respaldo o integración con La Iglesia de Jesucristo de los Santos de los Últimos Días.

**Repositorio previsto:** `facesud-legacy` · **Visibilidad:** privada · **Frontend:** reconstrucción desde cero.

## Stack acordado en principio
- Backend: Python + FastAPI, Pydantic.
- Datos: PostgreSQL, SQLAlchemy, Alembic.
- Frontend: React (TypeScript recomendado).
- Pruebas: Pytest; pruebas de componentes y E2E por definir.
- Entorno: Docker Compose; Nginx/reverse proxy.
- Media: almacenamiento compatible con S3.
- API: REST + OpenAPI.

## Alcance inicial
Cuentas, perfiles, unidades comunitarias y membresías provisionales, publicaciones de texto/imagen, feed, reacciones, comentarios, amistades, notificaciones, reportes, bloqueos y moderación.

Fuera del MVP: mensajería privada, marketplace, publicidad, pagos/donaciones, integración institucional y verificación automática. Grupos y eventos requieren especificación antes de implementarse. No habilitar menores hasta resolver requisitos legales y salvaguardas.

## Estructura
`apps/api` · `apps/web` · `services` · `contracts` · `infra` · `docs` · `tests`

## Primeros pasos
Leer `docs/product/PRODUCT_SCOPE.md`, `docs/architecture/ARCHITECTURE.md`, `docs/security/SECURITY_BASELINE.md` y `docs/decisions/OPEN_DECISIONS.md`. Este paquete es documentación y scaffold: todavía no es una aplicación ejecutable.
