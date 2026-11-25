# Guías de frontend — primera versión ejecutable

## Stack
- React y React DOM con versiones exactas en `apps/web/package.json`.
- TypeScript estricto.
- Vite como servidor de desarrollo y herramienta de build.

## Estructura actual
- `src/main.tsx`: punto de entrada.
- `src/App.tsx`: composición de la pantalla inicial y estado de conexión.
- `src/api/client.ts`: único punto de acceso HTTP para la API.
- `src/styles.css`: estilos globales y responsive.

## Convenciones
- Mantener las llamadas HTTP fuera de los componentes cuando puedan centralizarse en `src/api`.
- Usar variables de entorno `VITE_*` para configuración pública del cliente. Nunca colocar secretos en variables expuestas al navegador.
- Representar explícitamente carga, éxito y error en operaciones asíncronas.
- Mantener interfaz responsive y accesible; usar etiquetas semánticas y anuncios de estado cuando corresponda.
- El frontend puede validar para mejorar la experiencia, pero nunca será autoridad de permisos o validaciones de negocio.

## Alcance actual
La pantalla inicial muestra identidad del proyecto, descripción y resultado de `GET /api/v1/health`. No hay navegación de producto, formularios, autenticación ni controles ficticios.

## Pendiente para etapas posteriores
No seleccionar todavía librería global de estado, router, sistema de diseño, estrategia de formularios ni herramientas E2E. Resolverlas cuando una funcionalidad aprobada las requiera.
