# TASK-005 — Base visual del frontend

## Objetivo
Establecer una base visual y de accesibilidad consistente para FaceSud antes de construir las pantallas del Social Core. Esta tarea no implementa funcionalidades sociales ni resuelve decisiones de producto pendientes.

## Contexto
- La autenticación ya cuenta con registro, inicio de sesión, verificación de correo, recuperación y cambio de contraseña.
- El frontend usa React 19, TypeScript y Vite.
- El sistema visual FaceSud v1.0 fue aprobado: primario `#167A99`, primario suave `#DCEFF2`, azul marino `#172F43`, fondo `#F5F7F8`, superficies blancas, texto secundario `#647582` y bordes `#E5EAED`.
- Los mockups aprobados orientan la futura composición de la aplicación; no deben confundirse con pantallas funcionales ya implementadas.

## Alcance de esta entrega
- [x] Centralizar la paleta y los valores visuales recurrentes en custom properties CSS `--fs-*`.
- [x] Definir tokens iniciales de tipografía, radios, sombra y foco.
- [x] Establecer foco visible, selección de texto coherente y respeto por movimiento reducido.
- [x] Documentar convenciones para evitar controles ficticios y estilos inconsistentes.
- [x] Implementar shell autenticado de escritorio y móvil.
- [x] Mantener solo la navegación de Inicio, sin enlaces a destinos sociales todavía inexistentes.
- [x] Usar landmarks semánticos y anunciar el estado de conexión de la API a tecnologías de asistencia.
- [x] Ofrecer cierre de sesión tanto en escritorio como en móvil.
- [ ] Añadir pruebas visuales y de teclado en navegador.

## Fuera de alcance
- Feed, perfiles, publicaciones, amistades, comentarios, reacciones y almacenamiento de imágenes.
- Definir visibilidad de publicaciones, modelo de amistad o ranking del feed.
- Chat, aportes, verificación de membresía y salvaguardas de edad.
- Cambiar los flujos o políticas de autenticación existentes.

## Criterios de aceptación de la etapa completa
1. Los componentes nuevos consumen los tokens visuales y no duplican colores de marca.
2. El shell es responsive y no presenta desbordamiento horizontal a 320 px.
3. Todos los controles operativos son accesibles por teclado y tienen foco visible.
4. No se muestran acciones que aparenten funcionar si su destino todavía no existe.
5. Los flujos de autenticación existentes conservan su comportamiento.
6. El build TypeScript/Vite y las pruebas correspondientes pasan en CI.

## Estado
Parcial: tokens visuales, lineamientos y shell autenticado responsive implementados. Las pruebas E2E de navegador y la revisión visual en distintos tamaños quedan pendientes.
