# Arquitectura

## Enfoque
Monorepo con límites modulares claros. Comenzar con una aplicación modular y pocos despliegues; no adoptar microservicios distribuidos prematuramente. La separación lógica de dominios no autoriza a un módulo a escribir directamente en las tablas privadas de otro.

## Stack de la primera versión ejecutable
- API: Python 3.12, FastAPI y Pydantic Settings.
- Persistencia: PostgreSQL 17, SQLAlchemy 2 y Alembic.
- Cache/infraestructura: Redis 7, obligatorio en el entorno local de esta etapa.
- Web: React 19, TypeScript 5 y Vite 6.
- Pruebas: Pytest.
- Entorno: Docker Compose v2.

Las versiones exactas se mantienen en `apps/api/pyproject.toml`, `apps/web/package.json` y `docker-compose.yml`.

## Servicios implementados
- `web`: interfaz React servida por Vite en desarrollo.
- `api`: API FastAPI.
- `db`: PostgreSQL con volumen persistente.
- `redis`: Redis con persistencia AOF y volumen persistente.

PostgreSQL y Redis se mantienen en la red interna de Docker Compose y no publican puertos al host. La API espera a que ambos servicios estén saludables antes de iniciar.

## Uso inicial de Redis
Redis forma parte obligatoria de la infraestructura inicial, pero no se incorpora como dependencia funcional de los módulos de producto. En esta etapa solo se comprueba su conectividad mediante `PING` en `GET /api/v1/health/ready`.

No se implementan colas, workers, sesiones, caché de negocio ni pub/sub. La adopción de esos patrones requiere una necesidad y una decisión específicas.

## Módulos y capacidades de producto previstas
Los límites de dominio conceptuales son Identity, Community, Social, Trust & Safety y Notifications. El MVP también contempla chat bajo modalidad `request` y aportes voluntarios bajo modalidad `both`, según D-015 y D-016. Estas capacidades no están implementadas en la primera versión ejecutable y sus detalles deben especificarse antes de desarrollarlas.

## Autenticación web — decisión aprobada para la siguiente etapa
Conforme a D-017, el navegador utilizará una cookie `HttpOnly` con un identificador opaco de sesión. El backend generará el identificador con aleatoriedad criptográfica, persistirá únicamente su hash en PostgreSQL y validará la sesión en cada petición protegida. La cookie tendrá `Secure` en HTTPS, `HttpOnly`, `SameSite=Lax`, `Path=/` y no tendrá atributo `Domain`. El prefijo `__Host-` se reservará para entornos compatibles con sus requisitos.

Las sesiones tendrán expiración y revocación del lado servidor. El logout invalidará la sesión antes de borrar la cookie. Las operaciones que modifican estado deberán validar el origen y usar una defensa CSRF explícita. No se guardarán credenciales de sesión en `localStorage` ni `sessionStorage`.

PostgreSQL será el almacén de sesiones inicial. Redis no se utilizará para sesiones, de acuerdo con el límite de D-013. Los detalles de expiración, concurrencia de dispositivos, verificación y recuperación de cuentas siguen pendientes.

## Comunicación y contratos
REST para operaciones síncronas. FastAPI publica OpenAPI. Los contratos actualmente implementados se describen en [API_CONTRACTS.md](API_CONTRACTS.md). No se incorpora Kafka ni RabbitMQ.

## Diagrama de ejecución local
Navegador → Vite/React → FastAPI → PostgreSQL y Redis.

La API también recibe comprobaciones de salud. No se incorpora Nginx, almacenamiento S3 ni servicios externos en esta etapa.

## Estructura actual
- `apps/api/app/core`: configuración y conexiones a dependencias.
- `apps/api/app/api`: endpoints HTTP.
- `apps/api/migrations`: revisiones Alembic.
- `apps/web/src/api`: cliente HTTP centralizado.
- `apps/web/src`: interfaz y estilos.

Las convenciones del cliente se detallan en [FRONTEND_GUIDELINES.md](FRONTEND_GUIDELINES.md).
