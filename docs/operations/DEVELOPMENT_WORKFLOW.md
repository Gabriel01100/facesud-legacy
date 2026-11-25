# Flujo de desarrollo

1. Cada tarea define alcance, criterios de aceptación y pruebas.
2. Un solo agente/desarrollador modifica una rama a la vez; otro realiza revisión independiente.
3. PRs describen problema, cambios, migraciones/API, pruebas realmente ejecutadas, riesgos y limitaciones.
4. Proteger `main`; ramas `feat/*`, `fix/*`, `docs/*`.
5. CI: formato/lint, pruebas, revisión de dependencias/secretos y migraciones desde DB limpia.
6. Desarrollo usa datos ficticios; staging y producción separados. No copiar datos reales a desarrollo sin autorización y anonimización.
7. No desplegar ni conectar servicios externos sin aprobación explícita.
