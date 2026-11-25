# Auditoría documental — Etapa 1

Auditoría realizada sobre el contenido del repositorio al preparar la primera versión ejecutable. La clasificación evalúa suficiencia para esta etapa, no si un documento podría ampliarse en el futuro.

## Inventario

| Documento | Estado | Evaluación |
|---|---|---|
| `README.md` | Actualizado | Describe la versión ejecutable, servicios, endpoints y arranque local. |
| `AGENTS.md` | Creado | Instrucciones operativas para agentes y límites de cambios. |
| `docs/decisions/DECISIONS.md` | Actualizado | Registra decisiones vigentes, supersedidas e historial de cambios. |
| `docs/decisions/OPEN_DECISIONS.md` | Existente, pendiente | Contiene decisiones de producto, técnica, operación y gobernanza todavía abiertas. Se conserva sin aprobarlas. |
| `docs/product/PRODUCT_SCOPE.md` | Existente, sustantivo; parcial para Etapa 1 | Describe el alcance conceptual del MVP de producto, no el alcance de la primera versión ejecutable. Se conserva y se aclara esa diferencia en README y TASK-001. |
| `docs/security/SECURITY_BASELINE.md` | Existente, sustantivo; parcial | Establece controles importantes, pero no es un threat model ni un plan operativo completo. No se amplía con supuestos. |
| `docs/architecture/ARCHITECTURE.md` | Actualizado | Distingue servicios realmente implementados de módulos futuros y documenta Redis. |
| `docs/architecture/API_CONTRACTS.md` | Creado | Documenta únicamente endpoints y convenciones disponibles. |
| `docs/architecture/FRONTEND_GUIDELINES.md` | Creado | Documenta estructura y convenciones del frontend actual. |
| `docs/tasks/TASK-001-base-docker-ci.md` | Creado | Define alcance y criterios verificables de la base ejecutable. |
| `docs/operations/AI_WORK_CONTRACT.md` | Existente, conciso y útil; parcial | Define reglas generales de trabajo, sin detallar todos los flujos de desarrollo. Se mantiene para evitar duplicación. |
| `docs/operations/TESTING_STRATEGY.md` | Creado | Define pruebas aplicables a esta etapa y cómo reportar resultados. |
| `docs/operations/LOCAL_DEVELOPMENT.md` | Creado | Documenta requisitos, inicio, endpoints y operación local. |

## Placeholders y documentos faltantes detectados

- `AGENTS.md) no existía y fue creado con instrucciones específicas para este repositorio.
- `docs/tasks/TASK-001-base-docker-ci.md) no existía y fue creado con el alcance de Etapa 1.
- Los cuatro documentos solicitados de arquitectura y operaciones no existían y fueron creados.
- No se encontró una plantilla de pull request; se agrega una plantilla mínima.
- No se detectaron documentos cuyo único contenido fuera un título o placeholder entre los archivos leídos. Los documentos existentes son breves, pero contienen decisiones o restricciones concretas.

## Contradicciones detectadas y resolución

1. **Visibilidad:** README y D-002 indicaban repositorio privado. La decisión posterior del propietario establece que es público por ahora. README y registro se actualizaron; no se cambió la configuración de GitHub.
2. **Redis:** ARCHITECTURE indicaba incorporarlo solo ante una necesidad concreta. D-013 registra la nueva decisión: Redis es obligatorio en la infraestructura inicial y se usa solo para conectividad/readiness en esta etapa.
3. **Estado del proyecto:** README decía que solo existía documentación/scaffold. Se actualizó para describir la primera aplicación ejecutable prevista en esta rama. El estado final de ejecución debe completarse después de verificarla en Docker.
4. **MVP vs. Etapa 1:** PRODUCT_SCOPE describe funciones del MVP conceptual; TASK-001 excluye lógica de negocio de la primera versión ejecutable. No son alcances equivalentes. Se mantienen separados.
5. **Chat:** la exclusión histórica de mensajes privados fue supersedida por la decisión posterior del propietario de incluir chat bajo modalidad `request`. Se registra como D-015 y permanece fuera de Etapa 1.
6. **Aportes:** la decisión histórica de postergar donaciones fue supersedida por la modalidad `both` elegida para aportes voluntarios. Se registra como D-016 y permanece fuera de Etapa 1.

## Documentos pendientes para etapas futuras

| Documento | Etapa sugerida | Motivo |
|---|---|---|
| Modelo de identidad, autenticación y sesiones | Etapa de cuentas | Definir ciclo de vida, recuperación, sesiones y protección de credenciales antes de programar auth. |
| Modelo de datos y contratos de Community/unidades | Etapa de comunidad | Definir roles, solicitudes, revisión y revocación sin asumir reglas institucionales. |
| Contratos de publicaciones, feed y relaciones | Etapa social | Aterrizar visibilidad, amistades/seguimiento y contenido tras resolver OPEN_DECISIONS. |
| Diseño funcional y contratos del chat request | Etapa de chat | Precisar solicitud, aceptación, bloqueo, límites y estados. |
| Especificación de aportes voluntarios | Etapa de aportes | Precisar el significado operativo de `both`, flujo y responsabilidades antes de pagos. |
| Política de privacidad, retención y borrado | Antes de almacenar datos personales reales | Resolver minimización, retención, exportación y eliminación. |
| Threat model y plan de respuesta a incidentes | Antes de piloto con usuarios | Evaluar riesgos concretos de identidad, datos comunitarios y moderación. |
| Runbook de producción, backups y recuperación | Antes de despliegue público operativo | Definir hosting, observabilidad, backups y restauración. |
| Guía de moderación y salvaguardas | Antes de habilitar contenido/usuarios | Establecer procesos y responsables operativos. |

## Criterio de mantenimiento
Actualizar este inventario cuando se incorporen documentos nuevos o cambie el estado de los pendientes. No documentar funcionalidades hipotéticas como si estuvieran implementadas.
