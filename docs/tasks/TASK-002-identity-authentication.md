# TASK-002 — Identity: autenticación local y Google

## Objetivo
Implementar el primer módulo Identity de FaceSud con registro e inicio de sesión mediante correo electrónico/contraseña, inicio de sesión alternativo con Google OpenID Connect y sesiones web opacas en cookies HttpOnly.

## Base aprobada
- D-017: cookie HttpOnly con identificador opaco; hash de sesión persistido en PostgreSQL; Redis no se usa para sesiones.
- D-018: correo/contraseña y Google son métodos de autenticación válidos. Ambos resuelven a una cuenta interna de FaceSud.
- La cédula de miembro de La Iglesia de Jesucristo de los Santos de los Últimos Días será requisito obligatorio de elegibilidad comunitaria, pero su verificación queda fuera de esta tarea porque no se dispone aún del procedimiento ni de las fuentes de datos.

## Estado de implementación

### Base implementada en esta rama
- [x] Modelos SQLAlchemy para cuentas, credenciales locales, identidades externas y sesiones.
- [x] Migración Alembic `0002_identity_foundation`.
- [x] Hash de contraseñas con Argon2 y validación básica de política de longitud.
- [x] Generación de tokens opacos de sesión y CSRF; solo se persisten sus hashes.
- [x] Servicios de creación, consulta de sesión activa, validación CSRF y revocación.
- [x] Cuenta `pending_email` no puede utilizar una sesión activa.
- [x] Pruebas unitarias de hashing, normalización, CSRF, expiración y revocación.

### Pendiente para completar la tarea
- [ ] Registro, login, logout y endpoint de identidad actual.
- [ ] Verificación de correo y recuperación de contraseña con proveedor configurado.
- [ ] Google OpenID Connect y vinculación explícita de cuentas.
- [ ] Middleware/dependencias HTTP, cookies y defensa CSRF/origen integradas a FastAPI.
- [ ] Frontend de autenticación y pruebas de integración/E2E.

## Alcance de esta tarea
1. Definir entidades y migraciones para cuentas, credenciales locales, identidades externas y sesiones.
2. Implementar registro con correo/contraseña, login, logout y endpoint de identidad actual.
3. Usar un algoritmo de hashing de contraseñas apropiado y parámetros versionables; nunca cifrado reversible ni texto plano.
4. Implementar verificación de correo y recuperación de contraseña una vez configurado un proveedor de correo transaccional.
5. Integrar Google con OpenID Connect, validando firma, issuer, audience, expiración, nonce y redirect URI.
6. Implementar vinculación explícita de identidad Google a una cuenta existente. No fusionar cuentas automáticamente por coincidencia de correo.
7. Emitir identificadores de sesión criptográficamente aleatorios; guardar solo el hash en PostgreSQL; aplicar expiración, rotación, revocación y protección CSRF/origen.
8. Configurar CORS con credenciales solo para orígenes explícitos y configurar cookies seguras según entorno.
9. Incorporar pruebas unitarias, integración y documentación OpenAPI.
10. Mantener el frontend de autenticación coherente con las guías visuales y de accesibilidad del proyecto.

## Fuera de alcance
- Verificación de cédula de miembro y cualquier integración institucional.
- Almacenamiento del número de cédula.
- Roles de responsables de unidad, moderación y permisos comunitarios.
- Autorización de acceso a feed, publicaciones, chat o aportes.
- Aplicación móvil o tokens Bearer para terceros.
- Uso de Redis para sesiones, rate limiting o tareas en segundo plano sin decisión específica.

## Condiciones previas / decisiones aún necesarias
- Definir correo como identificador único y reglas de normalización.
- Elegir proveedor de correo transaccional y configurar secretos.
- Definir duración de sesión, expiración por inactividad y política de dispositivos.
- Definir flujo de recuperación y verificación de correo.
- Configurar credenciales OAuth de Google y URLs de callback por entorno.
- Definir límites de intentos y estrategia de rate limiting sin asumir Redis.
- Revisar política legal y de privacidad aplicable.

## Criterios de aceptación
- Un usuario puede registrarse, verificar su correo, iniciar sesión y cerrar sesión.
- La cookie no es legible desde JavaScript y no contiene datos personales.
- La base de datos almacena solo el hash del identificador de sesión.
- El logout revoca la sesión del lado servidor.
- Las operaciones mutables protegidas rechazan solicitudes sin defensa CSRF válida o con origen no permitido.
- Google login valida completamente el flujo OIDC y nunca confía solo en un email recibido del navegador.
- Una identidad externa no puede apropiarse de una cuenta existente por coincidencia de correo.
- Las sesiones sobreviven reinicios de API porque están persistidas en PostgreSQL.
- Las pruebas cubren credenciales incorrectas, cuenta no verificada, sesión expirada/revocada, CSRF, callback OIDC inválido y vinculación de cuentas.
- La ausencia del procedimiento de verificación de membresía no se suplanta con una validación ficticia ni bloquea el desarrollo local de esta tarea.
