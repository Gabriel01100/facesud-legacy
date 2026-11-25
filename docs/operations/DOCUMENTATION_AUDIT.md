# Auditoría documental — Etapa 1

Auditoría de los documentos de referencia del repositorio y de los archivos de documentación relevantes para la primera versión ejecutable. La clasificación evalúa suficiencia para esta etapa, no si un documento podría ampliarse en el futuro.

## Inventario

| Documento | Clasificación | Evaluación |
|---|---|---|
| `README.md` | Existente, actualizado y suficiente para Etapa 1 | Describe stack, servicios, endpoints, arranque y estado de validación pendiente. |
| `AGENTS.md` | Faltante; creado y completo para Etapa 1 | Instrucciones operativas para agentes y límites de cambios. |
| `docs/decisions/DECISIONS.md` | Existente, actualizado y completo para decisiones aprobadas | Registra decisiones vigentes, supersedidas e historial de cambios. |
| `docs/decisions/OPEN_DECISIONS.md` | Existente, sustantivo y deliberadamente pendiente | Contiene decisiones de producto, técnica, operación y gobernanza todavía abiertas. Se conserva sin aprobarlas. |
| `docs/product/PRODUCT_SCOPE.md` | Existente, sustantivo; pendiente de detalle funcional futuro | Describe el alcance conceptual del MVP de producto, no el alcance de la primera versión ejecutable. Se aclara esa diferencia en el propio documento y en TASK-001. |
| `docs/security/SECURITY_BASELINE.md` | Existente, sustantivo pero incompleto como threat model | Establece controles importantes, pero no es un threat model ni un plan operativo completo. No se amplía con supuestos. |
| `docs/architecture/ARCHITECTURE.md` | Existente, actualizado y suficiente para Etapa 1 | Distingue servicios implementados de capacidades futuras y documenta Redis. |
| `docs/architecture/API_CONTRACTS.md` | Faltante; creado y completo para Etapa 1 | Documenta únicamente endpoints y convenciones disponibles. |
| `docs/architecture/FRONTEND_GUIDELINES.md` | Faltante; creado y completo para Etapa 1 | Documenta estructura y convenciones del frontend actual. |
| `docs/tasks/TASK-001-base-docker-ci.md` | Faltante; creado y completo para Etapa 1 | Define alcance y criterios verificables de la base ejecutable y CI. |
| `docs/operations/AI_WORK_CONTRACT.md` | Existente, conciso y útil; incompleto como manual de proceso | Define reglas generales de trabajo, sin detallar todos los flujos de desarrollo. Se mantiene para evitar duplicación. |
| `docs/operations/TESTING_STRATEGY.md` | Faltante; creado y completo para Etapa 1 | Define pruebas aplicables a esta etapa y cómo reportar resultados. |
| `docs/operations/LOCAL_DEVELOPMENT.md` | Faltante; creado y completo para Etapa 1 | Documenta requisitos, inicio, endpoints y operación local. |
| `docs/operations/DOCUMENTATION_AUDIT.md` | Faltante; creado y completo para esta auditoría | Registra este inventario, contradicciones y documentos futuros. |

## Placeholders y documentos faltantes detectados

- `AGENTS.md` no existía y fue creado con instrucciones específicas para este repositorio.
- `docs/tasks/TASK-001-base-docker-ci.md` no existía y fue creado con el alcance de Etapa 1.
- Los cuatro documentos solicitados de arquitectura y operaciones no existían y fueron creados.
- No se encontró una plantilla de pull request; se agrega una plantilla mínima en `.github/pull_request_template.md`.
- El `.env.example` preexistente contenía variables de autenticación/secretos de ejemplo que no correspondían a esta etapa; se reemplazó por las dos variables locales realmente utilizadas.
- No se detectaron documentos cuyo único contenido fuera un título o placeholder entre los documentos revisados. Algunos documentos existentes son breves, pero contienen decisiones o restricciones concretas.

## Contradicciones detectadas y resolución

1. **Visibilidad:** README y D-002 indicaban repositorio privado. La decisión posterior del propietario establece que es público por ahora. README y registro se actualizaron; no se cambió la configuración de GitHub.
2. **Redis:** ARCHITECTURE indicaba incorporarlo solo ante una necesidad concreta. D-013 registra la nueva decisión: Redis es obligatorio en la infraestructura inicial y se usa solo para conectividad/readiness en esta etapa.
3. **Estado del proyecto:** README decía que solo existía documentación/scaffold. Se actualizó para describir la implementación de la base ejecutable en esta rama. El estado de ejecución local queda pendiente de validación real con Docker.
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
