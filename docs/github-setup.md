# Creación del repositorio en GitHub

## Opción con la interfaz web

1. Crear un repositorio llamado `fitplan` sin README ni `.gitignore` adicionales.
2. En Ubuntu WSL, ubicarse en la carpeta del proyecto.
3. Ejecutar:

```bash
git init -b main
git config user.name "Patricio Alvarez Vidales"
git config user.email "TU_CORREO_DE_GITHUB"
git add .
git commit -m "chore: initialize FitPlan monorepo"
git remote add origin git@github.com:TU_USUARIO/fitplan.git
git push -u origin main
git switch -c develop
git push -u origin develop
```

## Primera rama de trabajo

```bash
git switch develop
git switch -c feature/1-database-design
```

## Reglas recomendadas

En GitHub, crear reglas para `main` y `develop`:

- bloquear force push y eliminación;
- requerir Pull Request;
- requerir que los checks de CI terminen correctamente;
- no exigir aprobador adicional mientras el proyecto tenga un solo desarrollador.
