# Modelo de dominio inicial

Modelo conceptual; no es un esquema SQL completo.

- **Identity:** `Account`, `Credential`, `Session` y proveedor de identidad.
- **Profiles:** `UserProfile`, asociado uno a uno con una cuenta interna. Contiene únicamente atributos editables del perfil (nombre visible, username único y biografía). La fotografía se mantiene en `ProfileAvatar`, separada de los atributos textuales. No contiene credenciales, correo, estado de cuenta ni membresía.
- **Community:** `OrganizationUnit` (tipo, parent_id, país, estado), `UnitMembership` (account, unit, estado, fechas, reviewer y nota interna). Las solicitudes aprobadas son vinculaciones administrativas provisionales; no acreditan membresía institucional. La unidad visible del perfil debe derivarse de una vinculación aprobada, nunca de texto ingresado libremente.
- **Social:** `Post` (texto y feed por unidad), `Comment`, `Reaction` y `MediaAsset` (imagen WebP privada asociada a una publicación); `FriendshipRequest` y `Friendship` (capacidades futuras).
- **Trust & Safety:** `UserBlock`, `Report`, `ModerationAction`, `AuditEvent`.
- **Notifications:** `Notification` (destinatario, tipo, referencia, leído, timestamps).

Estados implementados de vinculación: `pending`, `approved`, `rejected`, `revoked`. `approved` representa una aprobación administrativa provisional de FaceSud, no validación institucional. La verificación institucional sigue separada y diferida.

El módulo Profiles puede consultar el identificador y la fecha de creación de la cuenta mediante contratos explícitos; no debe leer ni modificar credenciales o sesiones. La unidad comunitaria se derivará de `UnitMembership` aprobada cuando se integre en el contrato de perfil. En esta etapa no se almacena texto de unidad editable en el perfil.

Definir restricciones únicas y claves foráneas; usar DTOs allowlist, no serializar modelos ORM completos. No diseñar ni almacenar número de miembro en esta etapa. Determinar política de borrado/retención antes de producción.


## Social implementado

`Post` pertenece a una cuenta autora y a la unidad que tenía aprobada al publicarlo. El feed consulta solo publicaciones de la unidad aprobada del lector y exige que el autor conserve una vinculación aprobada en esa misma unidad. La cuenta del autor debe permanecer activa. No se exponen correo ni UUID de cuenta del autor. La primera versión admite texto de hasta 2.000 caracteres; las imágenes se almacenan como WebP normalizado en un backend privado y solo se entregan a miembros activos aprobados de la misma unidad.



## Social: interacciones implementadas
- Comment pertenece a una publicación y a una cuenta autora. Solo puede consultarse o crearse desde una cuenta activa con vinculación aprobada en la misma unidad de la publicación. El autor puede eliminarlo.
- Reaction vincula una cuenta con una publicación. La restricción única (post_id, account_id) impide reacciones duplicadas. La primera versión solo registra Me gusta; no expone quién reaccionó.
- Comentarios y reacciones requieren que la publicación siga siendo visible: su autor debe conservar cuenta activa y vinculación aprobada en la unidad original.


## Media implementado
- `MediaAsset` conserva metadatos y una clave opaca; no guarda rutas locales ni URLs públicas.
- El archivo se almacena fuera de PostgreSQL mediante una interfaz de almacenamiento. Desarrollo usa un volumen local privado; producción requiere un bucket S3-compatible privado.
- Solo se aceptan JPEG, PNG y WebP estáticos. El backend decodifica y vuelve a codificar a WebP, elimina metadatos EXIF, limita el tamaño de entrada a 5 MiB, la resolución a 20 megapíxeles y cada publicación a cuatro imágenes.
- Solo el autor puede adjuntar imágenes a su publicación. La lectura exige cuenta activa y vinculación aprobada en la misma unidad, y que el autor original siga siendo elegible.
- Las descargas pasan por la API autenticada; no se generan URLs públicas ni presignadas. Respuestas no cacheables, con `nosniff`.
- Las escrituras y eliminaciones de objetos se coordinan con el commit/rollback de la sesión SQLAlchemy para evitar dejar archivos si la transacción se revierte.


## Profiles: fotografía privada
- `ProfileAvatar` mantiene una única referencia de almacenamiento por cuenta; la metadata no contiene bytes, rutas locales ni URLs públicas.
- El archivo utiliza el adaptador privado y el normalizador de `Media`; su ciclo de vida se coordina con commit/rollback.
- Solo el titular puede consultar, cargar o eliminar su fotografía. No se habilita su exposición en feed ni a perfiles ajenos en esta etapa.
