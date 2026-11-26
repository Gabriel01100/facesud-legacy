# Modelo de dominio inicial

Modelo conceptual; no es un esquema SQL completo.

- **Identity:** `Account`, `Credential`, `Session` y proveedor de identidad.
- **Profiles:** `UserProfile`, asociado uno a uno con una cuenta interna. Contiene únicamente atributos editables del perfil (nombre visible, username único y biografía). No contiene credenciales, correo, estado de cuenta ni membresía.
- **Community:** `OrganizationUnit` (tipo, parent_id, país, estado), `UnitMembership` (user, unit, estado, fechas, reviewer, rol). La unidad visible del perfil debe derivarse de una vinculación aprobada, nunca de texto ingresado libremente.
- **Social:** `Post`, `PostMedia`, `Comment`, `Reaction`, `FriendshipRequest`, `Friendship`.
- **Trust & Safety:** `UserBlock`, `Report`, `ModerationAction`, `AuditEvent`.
- **Notifications:** `Notification` (destinatario, tipo, referencia, leído, timestamps).

Estados de membresía sugeridos: `pending`, `provisional`, `verified`, `rejected`, `suspended`. `provisional` no significa validación institucional.

El módulo Profiles puede consultar el identificador y la fecha de creación de la cuenta mediante contratos explícitos; no debe leer ni modificar credenciales o sesiones. La unidad comunitaria se incorporará cuando exista el módulo Community y el procedimiento de aprobación. En esta etapa no se almacenan datos de unidad en el perfil.

Definir restricciones únicas y claves foráneas; usar DTOs allowlist, no serializar modelos ORM completos. No diseñar ni almacenar número de miembro en esta etapa. Determinar política de borrado/retención antes de producción.
