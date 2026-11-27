# Guías de frontend — FaceSud

## Stack
- React y React DOM con versiones exactas en `apps/web/package.json`.
- TypeScript estricto.
- Vite como servidor de desarrollo y herramienta de build.

## Estructura
- `src/main.tsx`: punto de entrada.
- `src/App.tsx`: composición de vistas y flujos de autenticación/workspace.
- `src/api/client.ts`: único punto de acceso HTTP para la API y gestión CSRF.
- `src/features/<feature>/`: componentes, tipos y adaptadores API cohesivos por funcionalidad.
- `src/styles.css`: estilos globales, tokens visuales y responsive.

## Sistema visual FaceSud v1.0
Usar los tokens CSS `--fs-*` definidos en `src/styles.css`; evitar repetir valores hexadecimales en nuevos componentes.

| Token | Valor |
|---|---|
| Primario | `#167A99` |
| Primario suave | `#DCEFF2` |
| Azul marino | `#172F43` |
| Fondo | `#F5F7F8` |
| Superficie | `#FFFFFF` |
| Texto secundario | `#647582` |
| Bordes | `#E5EAED` |

La interfaz debe ser minimalista, clara y consistente con los mockups aprobados. No introducir gradientes, sombras intensas ni colores de marca alternativos sin una decisión de diseño explícita.

## Convenciones
- Mantener las llamadas HTTP en adaptadores de `src/features/<feature>/api.ts`, usando el cliente centralizado de `src/api/client.ts`.
- Usar variables de entorno `VITE_*` solo para configuración pública. Nunca colocar secretos en variables expuestas al navegador.
- Representar explícitamente carga, éxito y error en operaciones asíncronas.
- Mantener interfaz responsive y accesible: HTML semántico, labels asociados, estados anunciados y foco visible.
- Respetar `prefers-reduced-motion`.
- Los controles deben tener una acción real y un estado accesible. No representar funcionalidades pendientes como botones activos o enlaces ficticios.
- El frontend puede validar para mejorar la experiencia, pero nunca será autoridad de permisos o validaciones de negocio.
- No almacenar credenciales de sesión ni tokens CSRF persistentes en `localStorage` o `sessionStorage`.

## Estado funcional
La aplicación incluye registro, login, verificación de correo, reenvío de verificación, recuperación de contraseña y cambio de contraseña. El acceso utiliza cookies de sesión HttpOnly y el cliente HTTP centralizado gestiona CSRF.

El módulo Profiles permite al titular consultar y editar nombre visible, username y biografía. No ofrece navegación ni consulta de perfiles ajenos. La fecha de creación se muestra como dato de solo lectura. La fotografía de perfil se carga y visualiza mediante solicitudes autenticadas y URLs de objeto locales; solo el titular puede verla. La unidad comunitaria se deriva de una vinculación aprobada.

## Dependencias
No incorporar librerías de UI, iconos, estado global, routing o formularios sin una necesidad concreta, evaluación de mantenimiento y versiones fijadas. Preferir componentes pequeños y nativos mientras el alcance lo permita.

## Pruebas
Cada flujo visual debe cubrir estados de carga, error y éxito. Los formularios deben poder operarse con teclado. Incorporar pruebas de navegador para los primeros flujos de producto.
