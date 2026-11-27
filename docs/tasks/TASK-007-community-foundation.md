# TASK-007 — Community: unidades y vinculaciones

## Objetivo

Implementar el primer flujo funcional del dominio Community: catálogo jerárquico de unidades, solicitud de vinculación por una cuenta autenticada y revisión administrativa auditable. Mantener separadas la cuenta, la vinculación comunitaria y la elegibilidad institucional.

## Reglas de producto vigentes

- La persona debe ser miembro de La Iglesia de Jesucristo de los Santos de los Últimos Días para participar en la comunidad FaceSud (D-018).
- La verificación institucional queda diferida hasta disponer de un procedimiento y datos autorizados. No solicitar ni almacenar número de cédula ni documentos personales.
- La aprobación administrativa es una **vinculación comunitaria provisional**. No acredita ni debe etiquetarse como verificación institucional.
- Una cuenta autenticada sin vinculación aprobada no obtiene acceso a perfiles ajenos ni al contenido comunitario restringido (D-023).
- El piloto comienza en una rama, pero el modelo admite ramas, barrios y estacas, jerarquía configurable y expansión internacional.
- No habilitar menores hasta resolver edad mínima, consentimiento, obligaciones legales y salvaguardas.
- No presentar FaceSud como producto oficial ni insinuar integración institucional.

## Modelo de dominio

### OrganizationUnit
- id UUID.
- parent_id nullable, FK a OrganizationUnit.
- unit_type: branch, ward, stake.
- name.
- country_code ISO 3166-1 alpha-2.
- administrative_area y locality opcionales.
- status: active, inactive.
- timestamps.

Reglas:
- Una unidad puede tener padre; no puede ser su propio padre ni formar ciclos.
- La jerarquía válida se configura sin asumir que todos los países usan exactamente la misma estructura.
- El tipo de unidad y la relación padre-hijo deben validarse en servidor.
- No permitir borrar físicamente unidades con historial; desactivar.

### UnitMembership
- id UUID.
- account_id FK a Identity.Account.
- unit_id FK a OrganizationUnit.
- status: pending, approved, rejected, revoked.
- requested_at, reviewed_at.
- reviewer_account_id nullable FK a Identity.Account.
- review_note interna opcional, nunca expuesta a otros miembros.
- timestamps.

Reglas:
- Una cuenta puede tener una única vinculación vigente aprobada en el piloto; las solicitudes históricas se conservan.
- Evitar solicitudes duplicadas pendientes para la misma cuenta/unidad.
- El titular solo puede solicitar y consultar su propia vinculación.
- La revisión exige un permiso explícito de responsable comunitario asignado; no confiar en un rol enviado por el cliente.
- Toda aprobación, rechazo o revocación registra responsable, fecha y motivo interno cuando corresponda.
- La aprobación significa únicamente aceptación administrativa provisional en FaceSud.

## Alcance backend

1. Modelos SQLAlchemy y migración Alembic.
2. Servicios de dominio para árbol de unidades y ciclo de vida de vinculaciones.
3. Contratos Pydantic con allowlist estricta.
4. Endpoints autenticados:
   - GET /api/v1/community/units — unidades activas disponibles para solicitar vinculación.
   - POST /api/v1/community/membership-requests — solicitar vinculación.
   - GET /api/v1/community/membership/me — estado propio y unidad asociada.
   - GET /api/v1/community/review/requests — cola de revisión, solo responsables autorizados.
   - POST /api/v1/community/review/requests/{request_id} — aprobar o rechazar, solo responsables autorizados.
5. Autorización en servidor, CSRF y Origin para operaciones mutables.
6. No exponer notas internas, IDs internos de reviewer ni datos privados de cuentas en respuestas.
7. La asignación inicial de responsables debe ser una operación administrativa controlada/documentada; no crear un endpoint público para autoasignarse permisos.
8. La aprobación no habilita automáticamente perfiles públicos. Solo habilita el requisito de vinculación de D-023 una vez que la política de acceso comunitario esté implementada y probada.

## Alcance frontend

- Vista de unidades disponibles con jerarquía y ubicación comprensible.
- Solicitud de vinculación y confirmación.
- Estado propio: sin solicitud, pendiente, aprobada, rechazada o revocada.
- Panel de revisión separado, visible solo a responsables autorizados.
- Aprobar/rechazar con confirmación y feedback.
- Mostrar claramente que la aprobación es administrativa/provisional y no una verificación institucional.
- Mantener el sistema visual FaceSud v1.0 y accesibilidad responsive.

## Pruebas obligatorias

- Una cuenta sin sesión no puede consultar ni solicitar.
- Una cuenta puede solicitar una unidad activa y consultar solo su estado.
- No se admiten solicitudes duplicadas ni unidades inactivas.
- No se puede cambiar account_id, estado, reviewer o fechas desde el cliente.
- Una cuenta sin permiso de revisión recibe 403 en cola y decisiones.
- Un responsable autorizado puede aprobar/rechazar y queda auditoría.
- No se puede aprobar una solicitud ajena al alcance del responsable.
- No se pueden crear ciclos ni jerarquías inválidas.
- No se puede exponer información de cuenta, correo, notas internas o membresía institucional.
- La aprobación administrativa no se serializa como verificación institucional.
- Las operaciones mutables exigen CSRF y Origin.
- Las migraciones y pruebas existentes de Identity/Profiles no presentan regresiones.

## Fuera de alcance

- Consulta automática o integración con directorios/sistemas institucionales.
- Captura/almacenamiento de número de cédula o documentos.
- Alta de menores.
- Perfiles ajenos, feed, publicaciones o chat: requieren su propio módulo y autorización.
- Google OIDC.
- Marketplace y procesamiento de pagos.

## Orden de implementación

1. Revisar contratos y convenciones existentes.
2. Implementar modelos y migración.
3. Implementar servicios y reglas de jerarquía/solicitud.
4. Definir y proteger la asignación de responsables.
5. Implementar API y pruebas de autorización.
6. Implementar UI de solicitud y estado.
7. Implementar UI de revisión.
8. Integrar el estado de vinculación en el perfil propio sin exponer perfiles ajenos.
9. Actualizar modelo de dominio, contratos y guía local.
10. Ejecutar CI completo; no integrar hasta que esté verde.

## Criterio de entrega

La tarea se considera completa cuando el usuario puede iniciar sesión, solicitar vinculación a una unidad del catálogo, consultar el estado y un responsable autorizado puede revisar y decidir desde la interfaz. El sistema debe dejar explícito que esa decisión es provisional/administrativa y no verificación institucional.
