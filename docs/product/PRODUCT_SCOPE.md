# Alcance del producto

## Propósito
FaceSud busca facilitar la interacción comunitaria en un espacio social digital independiente. No debe presentarse como producto oficial ni insinuar integración institucional sin autorización formal.

## Lanzamiento
Piloto inicial en una rama local; expansión conceptual a barrios y estacas y, a futuro, otros países. La jerarquía debe ser configurable.

## MVP
- Registro, autenticación, recuperación de acceso y perfil básico.
- Solicitud de vinculación a unidad y consulta de estado.
- Publicaciones de texto e imágenes, feed, reacciones y comentarios.
- Solicitudes de amistad y gestión de amistades.
- Notificaciones internas.
- Chat bajo modalidad `request`, conforme a la decisión D-015.
- Aportes voluntarios bajo modalidad `both`, conforme a la decisión D-016.
- Reportes, bloqueos, moderación y límites contra spam.
- Revisión de solicitudes de unidad por responsables designados para el piloto.

## Fuera del MVP
Marketplace, publicidad, integración con sistemas/directorios institucionales y verificación automática con número de miembro. Grupos y eventos quedan pendientes de especificación. Los detalles funcionales del chat y de los aportes deben especificarse antes de sus respectivas implementaciones.

## Restricciones
La verificación de unidad será provisional/administrativa, no institucional. No recopilar número de miembro ni documentos en esta etapa; nunca exponerlos en perfiles. Un número por sí solo no prueba identidad. No habilitar menores hasta resolver edad/consentimiento, obligaciones legales, moderación reforzada y respuesta a incidentes.

## Criterios de aceptación
Las operaciones se autorizan en servidor; las respuestas API solo exponen campos permitidos; usuarios pueden gestionar contenido propio, amistades, reportes y bloqueos; acciones de moderación quedan auditadas; funcionalidades críticas tienen pruebas automatizadas.

## Diferencia entre MVP y primera versión ejecutable
El MVP describe el alcance de producto previsto. La primera versión ejecutable de Etapa 1 es únicamente una base técnica con frontend, API, PostgreSQL y Redis; no implementa ninguna de las funcionalidades de negocio enumeradas en este documento.
