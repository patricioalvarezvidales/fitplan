# FitPlan

Prototipo web que genera un plan semanal de entrenamiento y adapta cada sesión usando disponibilidad, equipo, progreso y retroalimentación del usuario.

## Stack

- React + TypeScript + Vite
- FastAPI + Python
- PostgreSQL
- SQLAlchemy + Alembic
- Docker Compose
- GitHub Actions

## Inicio rápido en Ubuntu WSL

Guarda el proyecto dentro del sistema Linux, por ejemplo:

```bash
mkdir -p ~/projects
cd ~/projects
# Descomprime o mueve aquí la carpeta fitplan
cd fitplan
cp .env.example .env
docker compose up --build
```

Servicios:

- Frontend: http://localhost:5173
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- PostgreSQL: localhost:5432

Detener servicios:

```bash
docker compose down
```

## Flujo Git

- `main`: versión estable y demostrable.
- `develop`: integración y staging.
- `feature/*`, `fix/*`, `docs/*`: ramas temporales.

Consulta `docs/github-setup.md` y `docs/branching-strategy.md`.

## Estado actual

- [x] Estructura monorepo.
- [x] Docker Compose con frontend, API y PostgreSQL.
- [x] Health checks.
- [x] CI para lint, pruebas, build y contenedores.
- [x] Página inicial de FitPlan.
- [ ] Diseño de base de datos.
- [ ] Autenticación y perfil.
- [ ] Catálogo de ejercicios.
- [ ] Motor de rutinas.
- [ ] Seguimiento y adaptación.
