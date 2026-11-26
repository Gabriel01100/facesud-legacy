# TASK-006 — Perfiles básicos

## Objetivo
Implementar el primer módulo funcional de perfiles de FaceSud, limitado a la consulta y edición del perfil propio. La tarea debe respetar la decisión D-023: los perfiles son privados por defecto y no se habilita la consulta de perfiles ajenos hasta que exista un procedimiento operativo de aprobación de vinculación comunitaria.

## Decisiones y contexto
- D-023 está confirmada: solo el titular puede consultar su perfil mientras no exista el procedimiento de aprobación comunitaria; el acceso de otros usuarios queda condicionado a que su propia vinculación comunitaria esté aprobada.
- La autenticación de la cuenta y la vinculación comunitaria son conceptos separados.
- La membresía comunitaria se modela en el dominio Community mediante `OrganizationUnit` y `UnitMembership`; no debe duplicarse como texto libre en Identity/Profile.
- La cédula de miembro, documentos personales e integración institucional quedan fuera de esta tarea.
- La interfaz debe respetar FaceSud v1.0 y los mockups aprobados de perfil.

## Campos del perfil

| Campo | Regla |
|---|---|
| Nombre visible | Dato editable por el titular. |
| Nombre de usuario | Identificador público único con formato `@usuario`; editable por el titular sujeto a unicidad y validación. |
| Foto de perfil | Imagen gestionada mediante el mecanismo de almacenamiento protegido definido para la aplicación. |
| Biografía breve | Dato editable por el titular, con límite de longitud validado en servidor. |
| Fecha de creación de cuenta | Dato de solo lectura, derivado de la cuenta; no duplicar ni permitir su edición desde el perfil. |
| Unidad comunitaria | Dato visible en la presentación del perfil. Debe derivarse de la vinculación comunitaria aprobada y de su `OrganizationUnit` (rama, barrio o estaca, según corresponda); nunca permitir que el usuario la establezca como texto libre ni presentarla como verificada si no está aprobada. |

La unidad comunitaria no es un dato de autenticación ni un campo editable del perfil. Si no existe una vinculación aprobada, la interfaz no debe afirmar que la persona pertenece a una unidad. La presentación de la unidad en el perfil no modifica la regla de privacidad de D-023.

## Alcance

### Backend
- Definir el modelo persistente de perfil y sus migraciones.
- Relacionar el perfil con la cuenta interna sin mezclar credenciales, sesiones ni estados de membresía.
- Implementar consulta del perfil propio y actualización de los campos editables.
- Aplicar allowlist de campos de entrada y salida; nunca serializar directamente entidades ORM.
- Validar en servidor los campos, la normalización y unicidad del nombre de usuario, y manejar conflictos sin filtrar información de otras cuentas.
- Derivar fecha de creación desde la cuenta y unidad desde Community/UnitMembership.
- Aplicar autorización en cada operación. No crear endpoints públicos, listados, búsquedas ni consultas de perfiles ajenos.
- Diseñar la carga y entrega de fotos con almacenamiento protegido, límites de tamaño/formato, validación real del contenido y autorización de acceso. No confiar en el nombre, extensión ni MIME declarados por el cliente.
- Mantener protección CSRF y validación de Origin en operaciones mutables conforme a los contratos existentes.

### Frontend
- Conectar la pantalla de perfil propio a la API.
- Permitir editar nombre visible, nombre de usuario y biografía.
- Incorporar la foto de perfil mediante el flujo protegido definido por backend.
- Mostrar fecha de creación como solo lectura.
- Mostrar la unidad comunitaria únicamente cuando exista una vinculación aprobada; distinguir claramente rama, barrio y estaca.
- Implementar estados de carga, guardado, éxito y error; controles accesibles por teclado y responsive.
- Reutilizar tokens `--fs-*`; no agregar enlaces o acciones a perfiles ajenos.

### Pruebas
- Titular autenticado puede consultar su propio perfil.
- Titular puede actualizar solo los campos permitidos.
- Usuario no autenticado no puede consultar ni modificar un perfil.
- No se puede consultar un perfil ajeno mediante UUID, username, parámetros alternativos ni rutas derivadas.
- No existen endpoints de listado o búsqueda de perfiles en esta etapa.
- Cuenta autenticada sin vinculación aprobada no obtiene acceso comunitario por el mero hecho de iniciar sesión.
- La unidad solo se presenta como pertenencia cuando la vinculación correspondiente está aprobada.
- Se prueban unicidad, normalización, límites, entradas inválidas y concurrencia relevante del username.
- Se prueban acceso no autorizado, CSRF, validación de imágenes y límites de carga.
- Las respuestas no exponen correo, credenciales, hashes, sesiones, tokens, datos de membresía internos ni campos ORM no permitidos.

## Fuera de alcance
- Consulta de perfiles ajenos, perfiles públicos, listados, búsquedas y directorios.
- Flujo de solicitud, revisión o aprobación de vinculación comunitaria.
- Verificación institucional mediante cédula de miembro o integración con sistemas institucionales.
- Visibilidad individual de publicaciones, amistades, bloqueos o excepciones administrativas.
- Perfil de menores y sus salvaguardas.
- Google OpenID Connect.

## Criterios de aceptación
1. El titular puede ver y editar únicamente su perfil mediante sesión válida.
2. La autorización se aplica en backend y no depende de ocultar elementos de interfaz.
3. Ninguna ruta permite a un usuario consultar perfiles ajenos mientras no se implemente la aprobación comunitaria.
4. Los campos devueltos por la API están limitados a una allowlist documentada.
5. La unidad se obtiene del dominio Community, es visible cuando está aprobada y no puede falsificarse desde el formulario de perfil.
6. El frontend sigue FaceSud v1.0, es responsive y accesible.
7. Las migraciones, pruebas automatizadas y CI pasan sin regresiones en autenticación.

## Orden de implementación sugerido
1. Revisar modelos, migraciones, módulos y convenciones existentes.
2. Definir validaciones y contratos exactos del perfil.
3. Implementar persistencia, servicios, esquemas y endpoints de perfil propio.
4. Implementar pruebas de autorización, validación y privacidad.
5. Implementar almacenamiento protegido de avatar y sus pruebas.
6. Conectar la interfaz de perfil propio y verificar responsive/accesibilidad.
7. Actualizar `DOMAIN_MODEL.md`, `API_CONTRACTS.md` y documentación de producto según el comportamiento realmente implementado.

## Entrega incremental

La primera entrega implementa el perfil propio básico: persistencia separada del módulo Identity, consulta y edición de nombre visible, username y biografía, fecha de creación de cuenta de solo lectura, autorización de servidor, protección CSRF y ausencia de rutas de perfiles ajenos. La fotografía y la unidad comunitaria permanecen sin datos en esta entrega: la primera requiere almacenamiento protegido; la segunda depende del módulo Community y del procedimiento de aprobación. Esta entrega no completa TASK-006.

## Nota de ejecución
Este documento define el alcance de la tarea; no declara que las funcionalidades estén implementadas. Las decisiones técnicas aún no especificadas (por ejemplo, límites exactos de longitud, formato/recorte de avatar y backend de almacenamiento) deben resolverse durante el diseño técnico antes de codificar, sin ampliar el alcance de privacidad de D-023.
