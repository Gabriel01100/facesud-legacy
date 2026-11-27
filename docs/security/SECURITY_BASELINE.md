# Línea base de seguridad y privacidad

La afiliación religiosa y los datos que revelen pertenencia a una comunidad religiosa requieren protección reforzada. Minimizar recolección, finalidad, acceso y retención.

## Datos
No almacenar número de miembro, documentos ni pruebas documentales en el MVP. No exponer datos internos en perfiles, logs, analítica ni notificaciones.

## Autenticación y autorización
- Hash moderno de contraseñas (Argon2id recomendado).
- Secretos fuera de Git; tokens revocables y de corta duración.
- Rate limits en login, registro y recuperación.
- Denegar por defecto y autorizar cada recurso en backend.
- No confiar en IDs, roles ni estados enviados por el cliente.
- Prevenir IDOR; respuestas de recuperación sin enumeración de cuentas.

## Perfiles
- Los perfiles son privados por defecto. La cuenta solo puede consultar su propio perfil hasta que exista un procedimiento operativo de aprobación comunitaria.
- No exponer perfiles por ID, username, listados o búsquedas antes de habilitar expresamente la autorización comunitaria.
- Las respuestas de perfil deben ser no cacheables y variar por cookie de sesión.
- Las fotografías se almacenan fuera del webroot en almacenamiento privado, se normalizan en el servidor y solo se entregan al titular mediante una ruta autenticada; no se publican URLs ni rutas de almacenamiento.
- Mantener separados identidad de cuenta, atributos de perfil y vinculación comunitaria.

## API y archivos
Validar entrada/salida; DTOs explícitos; CORS limitado; consultas parametrizadas; paginación y límites. Validar tipo real y tamaño de archivos, renombrar, almacenar fuera del webroot y usar URLs controladas. No confiar en Content-Type del cliente.

## Comunidad
Reportar, bloquear y moderar; auditar acciones administrativas; preparar respuesta a incidentes. No habilitar menores hasta completar evaluación legal y salvaguardas.

## Operación
Dependencias actualizadas, escaneo de secretos, backups cifrados y pruebas de restauración, TLS, monitoreo y revisión de permisos. No lanzar con secretos de ejemplo, endpoints sin autorización o cargas inseguras.
