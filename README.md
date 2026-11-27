# FaceSud

FaceSud es una plataforma social independiente orientada a la comunidad SUD. No es un producto oficial ni implica respaldo o integración con La Iglesia de Jesucristo de los Santos de los Últimos Días.

**Repositorio:** `facesud-legacy` · **Visibilidad:** público por decisión vigente del propietario · **Frontend:** reconstruido desde cero.

## Estado del proyecto

`main` contiene una aplicación funcional con autenticación por correo/contraseña, verificación de correo, perfiles propios, vinculación comunitaria provisional y un feed social privado por unidad. Las publicaciones admiten texto, comentarios, reacciones e imágenes WebP protegidas. El registro local y la verificación de correo funcionan mediante Mailpit, que captura los mensajes sin enviarlos a destinatarios reales. Los perfiles ajenos siguen privados y no hay directorio ni búsqueda de usuarios.

La fotografía de perfil queda pendiente. La vinculación comunitaria disponible es administrativa/provisional y no verifica membresía institucional. La base visual FaceSud v1.0 orienta las pantallas.

## Stack de la primera versión ejecutable

- Backend: Python 3.12, FastAPI, Pydantic Settings.
- Persistencia: PostgreSQL 17, SQLAlchemy 2, Alembic.
- Servicio Redis 7 para infraestructura inicial y comprobación de disponibilidad.
- Mailpit para capturar correos transaccionales en desarrollo local.
- Pillow y un adaptador de almacenamiento local/S3 para imágenes privadas.
- Frontend: React 19, TypeScript 5, Vite 6.
- Pruebas backend: Pytest.
- Entorno local: Docker Compose v2.

Las versiones de dependencias e imágenes están fijadas en los manifiestos correspondientes.

## Servicios locales

| Servicio | Dirección |
|---|---|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| OpenAPI | http://localhost:8000/docs |
| Mailpit | http://localhost:8025 | Captura local de correos de verificación y recuperación |
| PostgreSQL | Red interna Compose: `db:5432` |
| Redis | Red interna Compose: `redis:6379` |

PostgreSQL y Redis no publican puertos en el host.

## Inicio rápido

Requisitos: Docker Engine/Docker Desktop y Docker Compose v2.

```bash
cp .env.example .env
docker compose up --build
```

En PowerShell:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

La API aplica las revisiones Alembic al iniciar.

## Endpoints de comprobación

- `GET /api/v1/health`: comprueba que la API HTTP responde.
- `GET /api/v1/health/ready`: comprueba conectividad con PostgreSQL y Redis; devuelve HTTP 503 si alguna dependencia no está disponible.

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/health/ready
```

## Alcance funcional actual

Incluye:
- Registro, autenticación por correo/contraseña, verificación y recuperación de correo.
- Perfil básico propio.
- Solicitud de vinculación comunitaria y revisión administrativa provisional.
- Publicaciones de texto de hasta 2.000 caracteres en feed cronológico por unidad.
- Comentarios, reacciones y hasta cuatro imágenes por publicación.
- Imágenes normalizadas a WebP, almacenadas en volumen privado local o bucket S3-compatible privado en producción.

Las publicaciones, comentarios, reacciones e imágenes solo son accesibles para cuentas activas con vinculación aprobada en la misma unidad. La aprobación comunitaria es provisional y no equivale a verificación institucional.

Todavía no incluye fotografía de perfil, perfiles ajenos, directorios, búsquedas, amistades, chat, notificaciones de producto, aportes/pagos ni integraciones externas. El alcance conceptual completo se mantiene en `docs/product/PRODUCT_SCOPE.md`.

## Documentación

- [Arquitectura](docs/architecture/ARCHITECTURE.md)
- [Contratos API](docs/architecture/API_CONTRACTS.md)
- [Guías frontend](docs/architecture/FRONTEND_GUIDELINES.md)
- [Estrategia de pruebas](docs/operations/TESTING_STRATEGY.md)
- [Desarrollo local](docs/operations/LOCAL_DEVELOPMENT.md)
- [Entrega de correo electrónico](docs/operations/EMAIL_DELIVERY.md)
- [Registro de decisiones](docs/decisions/DECISIONS.md)
- [Decisiones pendientes](docs/decisions/OPEN_DECISIONS.md)
- [Auditoría documental](docs/operations/DOCUMENTATION_AUDIT.md)

## Aviso sobre configuración

`.env.example` contiene valores solo para desarrollo local. No usar credenciales de ejemplo en producción ni subir archivos `.env`.
