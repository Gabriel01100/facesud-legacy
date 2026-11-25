# TASK-002 — Identity: autenticación local y Google

## Objetivo
Implementar el módulo Identity de FaceSud con autenticación local por correo/contraseña, Google OpenID Connect como proveedor adicional y sesiones web opacas en cookies HttpOnly.

## Base aprobada
- D-017: cookie HttpOnly con identificador opaco; hash de sesión persistido en PostgreSQL; Redis no se usa para sesiones.
- D-018: correo/contraseña y Google son métodos de autenticación válidos. Ambos resuelven a una cuenta interna de FaceSud.
- D-019: duración absoluta de 7 días, expiración por inactividad de 30 minutos y máximo de 5 sesiones simultáneas por cuenta. Al crear una sexta se revoca la más antigua.
- La cédula de miembro de La Iglesia de Jesucristo de los Santos de los Últimos Días será requisito obligatorio de elegibilidad comunitaria, pero su verificación queda fuera de esta tarea porque no se dispone aún del procedimiento ni de las fuentes de datos.

## Estado de implementación

### Base de persistencia y seguridad implementada
- [x] Modelos SQLAlchemy para cuentas, credenciales locales, identidades externas y sesiones.
- [x] Migración Alembic `0002_identity_foundation`.
- [x] Hash de contraseñas con Argon2 y validación básica de política de longitud.
- [x] Generación de tokens opacos de sesión y CSRF; solo se persisten sus hashes.
- [x] Cuenta `pending_email` no puede utilizar una sesión activa.
- [x] Servicios de creación, consulta, expiración por inactividad, límite de sesiones, CSRF y revocación.

### Integración HTTP de esta subetapa
- [x] `POST /api/v1/auth/login` para credenciales locales de cuentas activas.
- [x] `GET /api/v1/auth/me` para consultar la cuenta autenticada.
- [x] `POST /api/v1/auth/logout` para revocar la sesión actual.
- [x] Cookie de sesión HttpOnly, Secure en producción, SameSite=Lax, Path=/ y sin Domain.
- [x] Cookie CSRF no HttpOnly y validación doble mediante cookie, encabezado y hash almacenado.
- [x] Validación estricta del encabezado Origin para login/logout.
- [x] CORS con credenciales y lista explícita de orígenes.
- [x] Pruebas de integración HTTP y de política de sesiones agregadas; pendientes de ejecución CI.

### Pendiente
- [ ] Registro de cuentas y verificación de correo (requiere definir/configurar proveedor transaccional).
- [ ] Recuperación y cambio de contraseña.
- [ ] Google OpenID Connect y vinculación explícita de cuentas.
- [ ] Rate limiting de login/registro (límites y estrategia siguen pendientes).
- [ ] Frontend de autenticación y pruebas E2E.
- [ ] Política de revocación ante cambio de contraseña y eventos de seguridad.

## Alcance
1. Implementar registro con correo/contraseña, login, logout y endpoint de identidad actual.
2. Usar hashing de contraseñas apropiado; nunca cifrado reversible ni texto plano.
3. Implementar verificación de correo y recuperación una vez configurado un proveedor de correo transaccional.
4. Integrar Google con OpenID Connect, validando firma, issuer, audience, expiración, nonce y redirect URI.
5. Implementar vinculación explícita de identidad Google a una cuenta existente. No fusionar cuentas automáticamente por coincidencia de correo.
6. Guardar solo hashes de identificadores de sesión en PostgreSQL; aplicar expiración, revocación y protección CSRF/origen.
7. Configurar CORS con credenciales solo para orígenes explícitos y cookies seguras según entorno.
8. Incorporar pruebas unitarias, integración y documentación OpenAPI.
9. Mantener el frontend de autenticación coherente con las guías visuales y de accesibilidad del proyecto.

## Fuera de alcance
- Verificación de cédula de miembro y cualquier integración institucional.
- Almacenamiento del número de cédula.
- Roles de responsables de unidad, moderación y permisos comunitarios.
- Autorización de acceso a feed, publicaciones, chat o aportes.
- Aplicación móvil o tokens Bearer para terceros.
- Uso de Redis para sesiones, rate limiting o tareas en segundo plano sin decisión específica.

## Condiciones pendientes
- Reglas estrictas de normalización y validación de correo.
- Proveedor de correo transaccional y plantillas.
- Flujo de recuperación y verificación de correo.
- Credenciales OAuth de Google y URLs de callback por entorno.
- Límites de intentos y estrategia de rate limiting.
- Revisión legal y de privacidad aplicable.

## Criterios de aceptación
- Las cuentas no activas no pueden iniciar sesión ni usar sesiones.
- La cookie de sesión no es legible desde JavaScript ni contiene datos personales.
- La base de datos almacena solo el hash del identificador de sesión y del token CSRF.
- El logout revoca la sesión del lado servidor.
- Las operaciones mutables protegidas rechazan solicitudes sin defensa CSRF válida o con origen no permitido.
- Las sesiones sobreviven reinicios de API porque están persistidas en PostgreSQL.
- La política D-019 se cumple y se prueba.
- Google login valida completamente el flujo OIDC y nunca confía solo en un email recibido del navegador.
- Una identidad externa no puede apropiarse de una cuenta existente por coincidencia de correo.
- La ausencia del procedimiento de verificación de membresía no se suplanta con una validación ficticia ni bloquea el desarrollo actual.

## Referencias
- D-017, D-018 y D-019 en [DECISIONS.md](../decisions/DECISIONS.md).
- Pendientes en [OPEN_DECISIONS.md](../decisions/OPEN_DECISIONS.md).
