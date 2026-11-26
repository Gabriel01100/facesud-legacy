# Instrucciones para agentes de desarrollo

1. Antes de modificar código, leer:
   - `README.md`
   - `docs/decisions/DECISIONS.md`
   - `docs/product/PRODUCT_SCOPE.md`
   - `docs/security/SECURITY_BASELINE.md`
   - `docs/architecture/ARCHITECTURE.md`
   - `docs/architecture/API_CONTRACTS.md`
   - `docs/architecture/FRONTEND_GUIDELINES.md`
   - `docs/operations/TESTING_STRATEGY.md`
   - `docs/operations/LOCAL_DEVELOPMENT.md`
   - `docs/operations/AI_WORK_CONTRACT.md`
2. Trabajar en ramas de tarea; nunca hacer commits directamente sobre `main`.
3. No inventar ni aprobar decisiones de producto pendientes. Consultar `docs/decisions/OPEN_DECISIONS.md`.
4. Respetar el alcance vigente de cada tarea. Identity/autenticación ya está implementado parcialmente; no asumir que los módulos sociales están disponibles.
5. No agregar secretos, datos personales reales ni valores de producción al repositorio.
6. Justificar dependencias nuevas y fijar versiones.
7. No afirmar que se ejecutaron pruebas, builds o despliegues si no se verificaron.
8. No cambiar decisiones de producto o la línea base de seguridad para facilitar una implementación.
9. Redis y PostgreSQL son servicios obligatorios de la infraestructura inicial. Mantenerlos en la red interna de Compose; no publicar sus puertos.
10. Documentar cambios arquitectónicos y de decisiones en los documentos correspondientes.
