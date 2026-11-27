# Decisiones pendientes

## Producto
- Amistad bilateral, seguimiento unilateral o ambos.
- Campos públicos/privados del perfil.
- Tipos y límites de contenido.
- Roles, designación y revocación de responsables de unidad.
- Flujos completos de grupos y eventos.

## Comunidad y privacidad
- Procedimiento autorizado y evidencia mínima para verificar la cédula de miembro, apelación, revisión y revocación.
- Política de retención y borrado, incluyendo datos de identidad y membresía.
- Edad mínima y salvaguardas; no habilitar menores antes de resolverlo.

## Identidad y autenticación
- Política de sesiones ante eventos adicionales de seguridad (p. ej. sospecha de compromiso y cierre remoto de sesiones).
- Política de cierre de sesiones al cambiar contraseña o ante eventos de seguridad.
- Configuración OAuth/OIDC de Google: credenciales, URI de callback, scopes mínimos y entornos.
- Revisión de los límites iniciales de rate limiting de login, registro y reenvío con métricas reales antes de habilitar el registro público a gran escala.
- Política de limpieza/retención de tokens de verificación y recuperación: implementación inicial elimina tokens usados/expirados después de 7 días; validar el plazo con política de privacidad.

## Técnica y operación
- Hosting, almacenamiento y correo transaccional (proveedor SMTP/API definitivo, credenciales por entorno, SPF, DKIM, DMARC y monitoreo de entrega).
- Herramientas frontend de lint, formato, pruebas y E2E.
- Backups, monitoreo, alertas y recuperación.
- Política de versiones y dependencias.

## Legal y gobernanza
- Responsable legal/operativo.
- Términos, privacidad, cookies y normas comunitarias.
- Obligaciones de protección de datos por jurisdicción.
- Canal de soporte, denuncias y respuesta a incidentes.
- Evitar marcas o expresiones que sugieran respaldo oficial.
