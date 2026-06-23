# Arquitectura inicial

```mermaid
flowchart LR
    U[Usuario] --> W[React + TypeScript]
    W -->|REST / JSON| A[FastAPI]
    A --> R[Motor de reglas y puntuación]
    A --> D[(PostgreSQL)]
    D --> E[Catálogo de ejercicios]
    D --> P[Planes y sesiones]
    D --> F[Progreso y feedback]
    E --> M[video_url / image_url]
```

## Decisiones

- Monorepo para simplificar coordinación, CI y documentación.
- API REST separada del frontend.
- PostgreSQL por la naturaleza relacional de usuarios, ejercicios, planes y registros.
- Docker Compose para reproducir el ambiente local.
- Videos almacenados como URL en el MVP; cada ejercicio tendrá una imagen de respaldo.
- El núcleo adaptativo será determinista y explicable, no una llamada directa a IA generativa.
