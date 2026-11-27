# Modelo de dominio inicial

Modelo conceptual; no es un esquema SQL completo.

- **Identity:** `Account`, `Credential`, `Session` y proveedor de identidad.
- **Profiles:** `UserProfile`, asociado uno a uno con una cuenta interna. Contiene únicamente atributos editables del perfil (nombre visible, username único y biografía). No contiene credenciales, correo, estado de cuenta ni membresía.
- **Community:** `OrganizationUnit` (tipo, parent_id, país, estado), `UnitMembership` (account, unit, estado, fechas, reviewer y nota interna). Las solicitudes aprobadas son vinculaciones administrativas provisionales; no acreditan membresía institucional. La unidad visible del perfil debe derivarse de una vinculación aprobada, nunca de texto ingresado libremente.
- **Social:** `Post` (implementado para texto y feed por unidad), `PostMedia`, `Comment`, `Reaction`, `FriendshipRequest`, `Friendship` (capacidades futuras).
- **Trust & Safety:** `UserBlock`, `Report`, `ModerationAction`, `AuditEvent`.
- **Notifications:** `Notification` (destinatario, tipo, referencia, leído, timestamps).

Estados implementados de vinculación: `pending`, `approved`, `rejected`, `revoked`. `approved` representa una aprobación administrativa provisional de FaceSud, no validación institucional. La verificación institucional sigue separada y diferida.

El módulo Profiles puede consultar el identificador y la fecha de creación de la cuenta mediante contratos explícitos; no debe leer ni modificar credenciales o sesiones. La unidad comunitaria se derivará de `UnitMembership` aprobada cuando se integre en el contrato de perfil. En esta etapa no se almacena texto de unidad editable en el perfil.

Definir restricciones únicas y claves foráneas; usar DTOs allowlist, no serializar modelos ORM completos. No diseñar ni almacenar número de miembro en esta etapa. Determinar política de borrado/retención antes de producción.


## Social implementado

`Post` pertenece a una cuenta autora y a la unidad que tenía aprobada al publicarlo. El feed consulta solo publicaciones de la unidad aprobada del lector y exige que el autor conserve una vinculación aprobada en esa misma unidad. La cuenta del autor debe permanecer activa. No se exponen correo ni UUID de cuenta del autor. La primera versión admite texto de hasta 2.000 caracteres; las imágenes requieren una etapa específica de almacenamiento y entrega protegidos.

