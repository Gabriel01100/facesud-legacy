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

| D-023 | Perfiles privados por defecto y acceso condicionado a vinculación comunitaria aprobada | Confirmada por el propietario |
| D-024 | Publicaciones y feed cronológico restringidos a miembros aprobados de la misma unidad | Confirmada por el propietario |
| D-025 | Comentarios y reacciones restringidos a miembros aprobados de la unidad de la publicación | Implementada como extensión de D-024 |
| D-026 | Imágenes en almacenamiento privado, con normalización del lado servidor | Implementada para publicaciones y fotografías de perfil; la autorización de cada recurso sigue D-023/D-024 |
| D-027 | Fotografía de perfil privada, visible solo para su titular hasta definir el acceso a perfiles ajenos | Implementada en la etapa de perfiles |

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


### D-022 — Recuperación y cambio de contraseña
- **Estado:** política técnica inicial implementada; revisar antes de habilitar registro público.
- **Solicitud de recuperación:** respuesta genérica para no revelar si el correo corresponde a una cuenta activa.
- **Token:** valor opaco aleatorio, se almacena únicamente su hash SHA-256, vence a los 30 minutos y es de un solo uso. Una nueva solicitud invalida tokens anteriores de la cuenta.
- **Restablecimiento:** solo cuentas activas con credencial local pueden restablecer la contraseña. Se invalida el resto de los tokens de recuperación y se revocan todas las sesiones activas de la cuenta.
- **Cambio autenticado:** requiere contraseña actual y CSRF válido; se revocan todas las sesiones y se solicita iniciar sesión nuevamente.
- **Rate limiting:** solicitud de recuperación: 3 por hora por IP+correo y 10 por hora por IP. Cambio autenticado: 5 por 15 minutos por IP+correo y 20 por 15 minutos por IP. Se usan claves hash y respuesta 429.
- **Correo:** se utiliza el adaptador SMTP STARTTLS existente. El proveedor transaccional definitivo y sus credenciales por entorno siguen pendientes.
- **Justificación:** ofrecer recuperación sin exponer existencia de cuentas ni conservar tokens reutilizables en la base.


### D-023 — Visibilidad de perfiles y acceso comunitario
- **Estado:** confirmada por el propietario.
- **Decisión:** los perfiles de usuario serán privados por defecto. Un perfil solo podrá ser consultado por su titular y por otros usuarios cuya vinculación comunitaria haya sido aprobada.
- **Separación de estados:** crear una cuenta o autenticarse correctamente no concede acceso a perfiles ni acredita pertenencia a la comunidad. La identidad de cuenta y la vinculación comunitaria deben mantenerse como dominios y estados separados.
- **Implementación diferida:** mientras no exista un procedimiento definido y operativo para aprobar la vinculación comunitaria, no habilitar perfiles públicos ni endpoints que expongan perfiles a usuarios no aprobados. El titular podrá acceder a su propio perfil.
- **Autorización:** la regla debe aplicarse en el servidor/API, no solo ocultando elementos en la interfaz. Las consultas, listados, búsquedas y recursos derivados del perfil deberán respetar la misma política.
- **Alcance pendiente:** esta decisión no define todavía los campos individuales del perfil, la visibilidad de publicaciones, ni las excepciones de acceso administrativo; esos aspectos requieren decisiones separadas.
- **Justificación:** reducir la exposición de datos personales y evitar que una cuenta autenticada se interprete como una membresía comunitaria aprobada.


### D-024 — Visibilidad de publicaciones y feed comunitario
- **Estado:** confirmada por el propietario.
- **Decisión:** las publicaciones y el feed solo serán visibles para cuentas activas cuya vinculación comunitaria esté aprobada en la misma unidad que la publicación.
- **Alcance:** el feed se ordena cronológicamente, de más reciente a más antigua. La primera entrega admite publicaciones de texto de hasta 2.000 caracteres.
- **Autorización:** el servidor valida la vinculación del lector y del autor; la interfaz no es una frontera de seguridad. Una cuenta autenticada sin vinculación aprobada no puede leer ni crear publicaciones.
- **Privacidad:** no se publican perfiles, directorios ni búsquedas. El feed devuelve únicamente nombre visible/username opcionales y contenido de la publicación; no expone correo ni identificadores de cuenta del autor.
- **Evolución:** imágenes requieren una etapa separada de almacenamiento y entrega protegidos. Comentarios y reacciones se implementan conforme a D-025.
- **Justificación:** habilitar interacción local sin convertir publicaciones ni perfiles en contenido público o visible entre unidades.



### D-025 — Comentarios y reacciones por unidad
- **Estado:** implementada como extensión de la política de visibilidad social D-024.
- **Decisión:** solo cuentas activas con vinculación aprobada en la misma unidad que la publicación pueden leer o crear comentarios y reacciones.
- **Comentarios:** texto normalizado de hasta 1.000 caracteres. El autor puede eliminar sus propios comentarios; no puede modificar ni eliminar los de otras personas.
- **Reacciones:** la primera versión ofrece una única reacción positiva (Me gusta) por cuenta y publicación. La restricción única se garantiza en la base de datos y las operaciones de alta son idempotentes.
- **Privacidad:** no se exponen correos ni identificadores de cuenta de autores o personas que reaccionaron. No se ofrece un listado de quién reaccionó.
- **Autorización:** se verifica en backend la elegibilidad del lector, la unidad de la publicación y la vigencia de la vinculación del autor original. Las respuestas son privadas y no cacheables.
- **Justificación:** habilitar interacción básica sin ampliar el alcance de visibilidad establecido por D-024 ni crear directorios de participantes.


### D-026 — Almacenamiento privado de imágenes
- **Estado:** implementada para imágenes adjuntas a publicaciones; fotografía de perfil diferida.
- **Decisión:** almacenar archivos fuera de PostgreSQL mediante un adaptador de almacenamiento. Desarrollo usa filesystem en volumen privado; producción exige bucket S3-compatible privado.
- **Validación:** aceptar JPEG, PNG y WebP estáticos; decodificar y recodificar a WebP; quitar metadatos EXIF; máximo 5 MiB, 20 megapíxeles y cuatro imágenes por publicación.
- **Autorización:** solo el autor adjunta imágenes. La lectura requiere cuenta activa y vinculación aprobada en la misma unidad que la publicación, y que el autor siga siendo elegible.
- **Entrega:** todas las descargas pasan por la API autenticada; no exponer rutas de filesystem, URLs públicas ni URLs presignadas. Aplicar no-store, Vary: Cookie y nosniff.
- **Ciclo de vida:** coordinar altas y bajas de objetos con commit/rollback de la transacción SQLAlchemy.
- **Justificación:** evitar que la capa social conozca el proveedor de almacenamiento y preservar el aislamiento de unidad ya definido por D-024.
