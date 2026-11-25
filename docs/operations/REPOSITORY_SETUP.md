# Configuración inicial de GitHub

Crear `facesud-legacy` como **Private**. Subir este scaffold sin inicializar otro README/.gitignore en GitHub para evitar conflictos. Proteger `main`, exigir PR, activar alertas de dependencias y secret scanning si están disponibles, y otorgar mínimo privilegio.

```bash
git init
git add .
git commit -m "chore: initialize FaceSud platform"
git branch -M main
git remote add origin <URL_DEL_REPOSITORIO_PRIVADO>
git push -u origin main
```

Primero crear el repositorio remoto y verificar que sea privado. No subir `.env`, credenciales, dumps ni datos personales.
