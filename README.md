# FaceSud

FaceSud es una plataforma social independiente orientada a la comunidad SUD. No es un producto oficial ni implica respaldo o integración con La Iglesia de Jesucristo de los Santos de los Últimos Días.

**Repositorio:** `facesud-legacy` · **Visibilidad:** público por decisión vigente del propietario · **Frontend:** reconstruido desde cero.

## Estado del proyecto

La rama `feat/first-executable-version` contiene la primera base ejecutable: frontend React conectado a API FastAPI, PostgreSQL y Redis mediante Docker Compose. Esta etapa no implementa funcionalidades de negocio.

## Stack de la primera versión ejecutable

- Backend: Python 3.12, FastAPI, Pydantic Settings.
- Persistencia: PostgreSQL 17, SQLAlchemy 2, Alembic.
- Servicio Redis 7 para infraestructura inicial y comprobación de disponibilidad.
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

La API aplica la revisión inicial de Alembic al iniciar.

## Endpoints de comprobación

- `GET /api/v1/health`: comprueba que la API HTTP responde.
- `GET /api/v1/health/ready`: comprueba conectividad con PostgreSQL y Redis; devuelve HTTP 503 si alguna dependencia no está disponible.

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/health/ready
```

## Alcance de esta etapa

Incluye infraestructura local, migración inicial vacía, endpoints de salud y una pantalla inicial que informa el estado de conexión con la API.

No incluye registro, autenticación, usuarios, perfiles, publicaciones, feed, comentarios, reacciones, amistades, chat, notificaciones de producto, almacenamiento de medios, aportes/pagos ni integraciones externas. El alcance conceptual del producto se mantiene documentado en `docs/product/PRODUCT_SCOPE.md`; no implica que esas funciones estén implementadas.

## Documentación

- [Arquitectura](docs/architecture/ARCHITECTURE.md)
- [Contratos API](docs/architecture/API_CONTRACTS.md)
- [Guías frontend](docs/architecture/FRONTEND_GUIDELINES.md)
- [Estrategia de pruebas](docs/operations/TESTING_STRATEGY.md)
- [Desarrollo local](docs/operations/LOCAL_DEVELOPMENT.md)
- [Registro de decisiones](docs/decisions/DECISIONS.md)
- [Decisiones pendientes](docs/decisions/OPEN_DECISIONS.md)
- [Auditoría documental](docs/operations/DOCUMENTATION_AUDIT.md)

## Aviso sobre configuración

`.env.example` contiene valores solo para desarrollo local. No usar credenciales de ejemplo en producción ni subir archivos `.env`.
