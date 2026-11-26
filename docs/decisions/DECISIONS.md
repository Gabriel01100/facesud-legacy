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
| D-017 | Autenticación web mediante cookies HttpOnly y sesiones opacas persistidas en PostgreSQL | Confirmada por el propietario |
| D-018 | Acceso con correo/contraseña y Google; membresía SUD obligatoria | Confirmada por el propietario; verificación diferida |
| D-019 | Política de duración y concurrencia de sesiones | Confirmada por el propietario |

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

### D-017 — Autenticación web mediante cookies HttpOnly y sesiones opacas
- **Estado:** confirmada por el propietario.
- **Decisión:** la aplicación web autenticará mediante una cookie de sesión `HttpOnly` que contendrá un identificador opaco, aleatorio y no derivado de datos del usuario. El servidor validará la sesión contra un registro persistido en PostgreSQL.
- **Protección de la cookie:** configurar `HttpOnly`, `Secure` en entornos HTTPS, `SameSite=Lax` como valor inicial, `Path=/` y omitir `Domain`. El nombre con prefijo `__Host-` se utilizará en entornos que cumplan sus requisitos; desarrollo local deberá contemplar HTTP sin debilitar producción.
- **Protección de sesiones:** generar identificadores con un generador criptográficamente seguro; almacenar solo un hash del identificador, nunca el valor de la cookie; establecer expiración; invalidar en logout; rotar el identificador al autenticar y ante cambios sensibles.
- **CSRF y origen:** las operaciones que modifican estado deberán incorporar defensa CSRF y validación estricta del origen. `SameSite` no se considera la única defensa.
- **Persistencia:** PostgreSQL será el almacén inicial de sesiones. Redis conserva exclusivamente el uso de infraestructura/readiness aprobado por D-013.
- **Duración y concurrencia:** definidas por D-019.
- **Justificación:** reducir la exposición del identificador de sesión a JavaScript y permitir revocación del lado servidor.
- **Evolución:** una futura aplicación móvil o integración externa podrá tener un mecanismo separado.

### D-018 — Métodos de acceso y requisito de membresía
- **Estado:** confirmada por el propietario.
- **Métodos de autenticación:** el correo electrónico será el identificador único de la cuenta y la contraseña el método local de autenticación; Google será un proveedor adicional mediante OpenID Connect. Ambos métodos deben resolver a una única cuenta interna de FaceSud.
- **Vinculación de identidades:** no vincular automáticamente cuentas existentes solo porque coincida una dirección de correo. La vinculación de Google con una cuenta existente requerirá una prueba de control de la cuenta y un flujo explícito.
- **Requisito de elegibilidad:** para participar en la comunidad FaceSud, la persona debe tener cédula de miembro de La Iglesia de Jesucristo de los Santos de los Últimos Días. La autenticación por Google o por contraseña no acredita esa condición.
- **Implementación diferida:** durante las etapas actuales no se exigirá ni verificará la cédula porque todavía no están disponibles los datos ni el procedimiento autorizado. La verificación se diseñará e implementará en una etapa posterior antes de habilitar el acceso comunitario real.
- **Separación de dominios:** identidad/autenticación y membresía/verificación serán conceptos y estados separados. No asumir integración institucional, consulta automática ni almacenar/exponer el número de cédula sin una decisión específica y un diseño de privacidad.
- **Justificación:** admitir métodos de acceso convenientes sin confundir autenticación con pertenencia o elegibilidad comunitaria.

### D-019 — Política de duración y concurrencia de sesiones
- **Estado:** confirmada por el propietario.
- **Duración absoluta:** una sesión vence a los 7 días desde su creación, aunque se mantenga activa.
- **Expiración por inactividad:** una sesión se invalida después de 30 minutos sin actividad autenticada.
- **Concurrencia:** máximo de 5 sesiones activas por cuenta.
- **Al emitir una sexta sesión:** se revoca la sesión activa más antigua y se conserva la nueva.
- **Actividad:** una solicitud autenticada válida actualiza `last_seen_at`; solicitudes rechazadas por CSRF no deben considerarse actividad de negocio.
- **Persistencia:** los tiempos y revocaciones se controlan en PostgreSQL, no en Redis.

### D-020 — Rate limiting inicial de login
- **Estado:** decisión técnica adoptada para el endurecimiento de Identity.
- **Almacenamiento:** PostgreSQL, no Redis, para evitar una nueva dependencia operativa en la ruta de autenticación.
- **Ventana y límites iniciales:** 5 intentos por 15 minutos para cada combinación IP+correo y 30 intentos por 15 minutos por IP.
- **Respuesta:** HTTP 429 con Retry-After al superar el límite.
- **Privacidad:** se almacenan hashes SHA-256 de las claves de bucket; no se persisten IP ni correo en claro en la tabla de rate limiting.
- **Recuperación:** un login correcto elimina ambos buckets asociados a esa IP y correo.
- **Alcance:** limita login. Registro y reenvío de verificación se regulan por separado mediante D-021.
- **Justificación:** el límite combinado dificulta ataques automatizados sin crear un bloqueo global por correo que permita a terceros denegar el acceso a una víctima.
- **Revisión:** observar métricas y ajustar umbrales antes de habilitar registro público a gran escala.

## Decisiones técnicas anteriores
Las decisiones técnicas confirmadas para esta base no aprueban automáticamente herramientas o funcionalidades futuras. Las decisiones abiertas siguen listadas en [OPEN_DECISIONS.md](OPEN_DECISIONS.md).


### D-021 — Rate limiting inicial de registro y reenvío de verificación
- **Estado:** política técnica inicial implementada; requiere revisión con métricas antes de habilitar registro público a gran escala.
- **Almacenamiento:** se reutilizan los buckets persistidos en PostgreSQL y sus claves hash; no se guardan correos ni direcciones IP en claro.
- **Registro:** máximo de 2 intentos por hora por combinación IP+correo y 5 intentos por hora por IP.
- **Reenvío de verificación:** máximo de 3 intentos por hora por combinación IP+correo y 10 intentos por hora por IP.
- **Respuesta al superar el límite:** HTTP 429 con encabezado Retry-After. Dentro del límite, el endpoint mantiene una respuesta genérica para no revelar si una cuenta existe o está pendiente de verificación.
- **Separación de operaciones:** los buckets de login, registro y reenvío utilizan prefijos de alcance distintos; un límite en una operación no consume el cupo de otra.
- **Privacidad y abuso:** no se aplica un bloqueo global por correo, para evitar que terceros puedan impedir que una víctima registre o verifique su cuenta desde otras redes.
- **Operación:** la limpieza de buckets conserva los registros durante la ventana máxima configurada.
- **Consideración de proxy:** la IP usada debe ser la que entregue el servidor/proxy confiable. No se debe confiar en encabezados X-Forwarded-For suministrados directamente por clientes.
