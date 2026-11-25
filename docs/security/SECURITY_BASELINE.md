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

## API y archivos
Validar entrada/salida; DTOs explícitos; CORS limitado; consultas parametrizadas; paginación y límites. Validar tipo real y tamaño de archivos, renombrar, almacenar fuera del webroot y usar URLs controladas. No confiar en Content-Type del cliente.

## Comunidad
Reportar, bloquear y moderar; auditar acciones administrativas; preparar respuesta a incidentes. No habilitar menores hasta completar evaluación legal y salvaguardas.

## Operación
Dependencias actualizadas, escaneo de secretos, backups cifrados y pruebas de restauración, TLS, monitoreo y revisión de permisos. No lanzar con secretos de ejemplo, endpoints sin autorización o cargas inseguras.
