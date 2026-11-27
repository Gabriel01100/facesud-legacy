# Modelo de dominio inicial

Modelo conceptual; no es un esquema SQL completo.

- **Identity:** `Account`, `Credential`, `Session` y proveedor de identidad.
- **Profiles:** `UserProfile`, asociado uno a uno con una cuenta interna. Contiene únicamente atributos editables del perfil (nombre visible, username único y biografía). No contiene credenciales, correo, estado de cuenta ni membresía.
- **Community:** `OrganizationUnit` (tipo, parent_id, país, estado), `UnitMembership` (account, unit, estado, fechas, reviewer y nota interna). Las solicitudes aprobadas son vinculaciones administrativas provisionales; no acreditan membresía institucional. La unidad visible del perfil debe derivarse de una vinculación aprobada, nunca de texto ingresado libremente.
- **Social:** `Post`, `PostMedia`, `Comment`, `Reaction`, `FriendshipRequest`, `Friendship`.
- **Trust & Safety:** `UserBlock`, `Report`, `ModerationAction`, `AuditEvent`.
- **Notifications:** `Notification` (destinatario, tipo, referencia, leído, timestamps).

Estados implementados de vinculación: `pending`, `approved`, `rejected`, `revoked`. `approved` representa una aprobación administrativa provisional de FaceSud, no validación institucional. La verificación institucional sigue separada y diferida.

El módulo Profiles puede consultar el identificador y la fecha de creación de la cuenta mediante contratos explícitos; no debe leer ni modificar credenciales o sesiones. La unidad comunitaria se derivará de `UnitMembership` aprobada cuando se integre en el contrato de perfil. En esta etapa no se almacena texto de unidad editable en el perfil.

Definir restricciones únicas y claves foráneas; usar DTOs allowlist, no serializar modelos ORM completos. No diseñar ni almacenar número de miembro en esta etapa. Determinar política de borrado/retención antes de producción.
