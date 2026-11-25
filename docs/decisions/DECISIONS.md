# Registro de decisiones

Este registro conserva decisiones anteriores y deja explícitos los cambios aprobados por el propietario. Las propuestas y decisiones pendientes no se consideran aprobadas por aparecer en otros documentos.

## Decisiones vigentes

| ID | Decisión | Estado |
|---|---|---|
| D-001 | Repositorio `facesud-legacy` | Confirmada |
| D-002 | Visibilidad privada | Supersedida por D-012 |
| D-003 | Frontend reconstruido desde cero | Confirmada |
| D-004 | FastAPI + Python | Confirmada para la base técnica |
| D-005 | PostgreSQL | Confirmada para la base técnica |
| D-006 | React + TypeScript | Confirmada para la base técnica |
| D-007 | Monorepo con límites modulares | Confirmada |
| D-008 | Sin mensajes privados en MVP conceptual inicial | Supersedida por D-015 |
| D-009 | Sin marketplace ni publicidad en MVP | Confirmada |
| D-010 | Donaciones en etapa posterior | Supersedida por D-016 |
| D-011 | Verificación de unidad provisional, sin integración institucional | Restricción vigente |
| D-012 | Repositorio público por ahora | Confirmada por el propietario |
| D-013 | Redis obligatorio en la infraestructura inicial | Confirmada por el propietario |
| D-014 | Primera versión ejecutable sin funcionalidades de negocio | Confirmada para Etapa 1 |
| D-015 | Chat en el MVP bajo modalidad `request` | Confirmada por el propietario; fuera de Etapa 1 |
| D-016 | Aportes voluntarios bajo modalidad `both` | Confirmada por el propietario; fuera de Etapa 1 |

## Historial y contexto de cambios

### D-002 — Visibilidad privada (decisión anterior)
- **Decisión anterior:** el README y el registro inicial indicaban que el repositorio debía ser privado.
- **Nueva decisión:** el repositorio debe permanecer público por ahora.
- **Justificación:** instrucción explícita y posterior del propietario.
- **Efecto:** se actualiza la documentación; no se modifica la configuración de visibilidad del repositorio.

### D-012 — Visibilidad pública por ahora
- **Estado:** confirmada.
- **Alcance:** describe la visibilidad vigente; no implica que deba mantenerse pública indefinidamente.

### D-013 — Redis en infraestructura inicial
- **Decisión anterior:** la arquitectura indicaba incorporar Redis/colas solo ante una necesidad concreta.
- **Nueva decisión:** Redis es un servicio obligatorio de la infraestructura inicial de esta etapa.
- **Justificación:** requisito explícito del propietario para disponer desde el inicio de PostgreSQL y Redis en el entorno Compose.
- **Uso inicial:** conexión y comprobación de disponibilidad mediante `PING` en el endpoint de readiness.
- **Límites:** no se implementan colas, sesiones, caché de negocio, pub/sub ni workers. Su presencia en infraestructura no obliga a todos los módulos a depender funcionalmente de Redis.

### D-014 — Alcance de la primera versión ejecutable
- **Decisión:** entregar una aplicación local ejecutable con interfaz web conectada a la API, PostgreSQL y Redis.
- **Límites:** no implementar autenticación ni funcionalidades sociales en esta etapa.

### D-008 — Sin mensajería privada (decisión anterior)
- **Decisión anterior:** el registro inicial excluía mensajes privados del MVP.
- **Nueva decisión:** el chat forma parte del MVP bajo el modelo `request`, según la elección posterior del propietario.
- **Efecto:** D-008 queda supersedida por D-015. El chat no se implementa en la primera versión ejecutable.

### D-015 — Chat bajo modalidad request
- **Estado:** confirmada por el propietario.
- **Alcance:** define el modelo de acceso al chat; no determina por sí sola detalles funcionales no especificados. Su diseño e implementación se harán en una etapa posterior.

### D-010 — Aportes/donaciones posteriores (decisión anterior)
- **Decisión anterior:** el registro inicial postergaba las donaciones.
- **Nueva decisión:** los aportes voluntarios se modelan bajo la modalidad `both`, según la elección posterior del propietario.
- **Efecto:** D-010 queda supersedida por D-016. Los aportes no se implementan en esta etapa.

### D-016 — Aportes voluntarios bajo modalidad both
- **Estado:** confirmada por el propietario.
- **Alcance:** registra la modalidad elegida; no define proveedor de pagos, flujos, comisiones ni tratamiento contable.

## Decisiones técnicas anteriores
Las decisiones técnicas confirmadas para esta base no aprueban automáticamente herramientas o funcionalidades futuras. Las decisiones abiertas siguen listadas en [OPEN_DECISIONS.md](OPEN_DECISIONS.md).
