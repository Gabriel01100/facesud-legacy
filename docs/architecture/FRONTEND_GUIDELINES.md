# Guías de frontend — FaceSud

## Stack
- React y React DOM con versiones exactas en `apps/web/package.json`.
- TypeScript estricto.
- Vite como servidor de desarrollo y herramienta de build.

## Estructura
- `src/main.tsx`: punto de entrada.
- `src/App.tsx`: composición de vistas y flujos de autenticación.
- `src/api/client.ts`: único punto de acceso HTTP para la API.
- `src/styles.css`: estilos globales, tokens visuales y responsive.
- Los componentes reutilizables de producto se incorporarán en módulos propios cuando existan flujos que los utilicen.

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
- Mantener las llamadas HTTP fuera de los componentes cuando puedan centralizarse en `src/api`.
- Usar variables de entorno `VITE_*` solo para configuración pública. Nunca colocar secretos en variables expuestas al navegador.
- Representar explícitamente carga, éxito y error en operaciones asíncronas.
- Mantener interfaz responsive y accesible: HTML semántico, labels asociados, estados anunciados y foco visible.
- Respetar `prefers-reduced-motion`.
- Los controles deben tener una acción real y un estado accesible. No representar funcionalidades pendientes como botones activos o enlaces ficticios.
- El frontend puede validar para mejorar la experiencia, pero nunca será autoridad de permisos o validaciones de negocio.
- No almacenar credenciales de sesión ni tokens CSRF persistentes en `localStorage` o `sessionStorage`.

## Estado funcional
La aplicación incluye registro, login, verificación de correo, reenvío de verificación, recuperación de contraseña y cambio de contraseña. El acceso utiliza cookies de sesión HttpOnly y el cliente HTTP centralizado gestiona CSRF.

La pantalla autenticada todavía no tiene el shell definitivo de producto. No asumir que existen perfiles, publicaciones, feed ni navegación social hasta que sus respectivos módulos estén implementados.

## Dependencias
No incorporar librerías de UI, iconos, estado global, routing o formularios sin una necesidad concreta, evaluación de mantenimiento y versiones fijadas. Preferir componentes pequeños y nativos mientras el alcance lo permita.

## Pruebas
Cada flujo visual debe cubrir estados de carga, error y éxito. Los formularios deben poder operarse con teclado. Incorporar pruebas de navegador al desarrollar el shell y los primeros flujos sociales.
