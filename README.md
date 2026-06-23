# FitPlan

MVP funcional para generar y adaptar planes semanales de entrenamiento mediante una arquitectura React + FastAPI + PostgreSQL y prácticas DevOps.

## Funciones implementadas

- Registro, confirmación de correo en modo desarrollo, inicio y cierre de sesión con JWT.
- Perfil físico editable con validación de edad, peso, altura, nivel, objetivo y disponibilidad.
- Selección de equipo y restricciones físicas.
- Generación automática de una semana con series, repeticiones, descansos y RPE.
- Filtrado de ejercicios incompatibles con equipo o restricciones.
- Sesión recomendada del día con video o imagen de respaldo.
- Registro irreversible de sesión completada.
- Retroalimentación de dificultad, energía, satisfacción y dolor.
- Historial con filtros semanales y mensuales.
- Regeneración adaptativa: progresión, mantenimiento o reducción de volumen.

## Ejecutar con Docker

```bash
cp .env.example .env
docker compose up --build
```

Aplicación: `http://localhost:5173`
Swagger: `http://localhost:8000/docs`

## Flujo de prueba

1. Crear una cuenta. En este MVP la interfaz consume el token de confirmación automáticamente; en producción debe enviarse por correo con un proveedor SMTP.
2. Completar el perfil, equipo y restricciones.
3. Generar la rutina semanal.
4. Abrir una sesión, revisar ejercicios y registrarla como completada.
5. Consultar el historial o regenerar para aplicar la adaptación.

## Calidad

```bash
cd apps/api && pip install -e ".[dev]" && ruff check app tests && pytest
cd apps/web && npm ci && npm run lint && npm run build
```

## Nota de seguridad

FitPlan no sustituye una evaluación médica o profesional. El sistema evita ejercicios etiquetados como incompatibles, pero el usuario debe detenerse ante dolor agudo.
