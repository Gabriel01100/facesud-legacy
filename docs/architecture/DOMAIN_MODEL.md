# Modelo de dominio inicial

Modelo conceptual, no esquema SQL definitivo.

- **Identity:** `User`, `Credential`, `Session`, `UserProfile`.
- **Community:** `OrganizationUnit` (tipo, parent_id, país, estado), `UnitMembership` (user, unit, estado, fechas, reviewer, rol).
- **Social:** `Post`, `PostMedia`, `Comment`, `Reaction`, `FriendshipRequest`, `Friendship`.
- **Trust & Safety:** `UserBlock`, `Report`, `ModerationAction`, `AuditEvent`.
- **Notifications:** `Notification` (destinatario, tipo, referencia, leído, timestamps).

Estados de membresía sugeridos: `pending`, `provisional`, `verified`, `rejected`, `suspended`. `provisional` no significa validación institucional.

Definir restricciones únicas y claves foráneas; usar DTOs allowlist, no serializar modelos ORM completos. No diseñar ni almacenar número de miembro en esta etapa. Determinar política de borrado/retención antes de producción.
