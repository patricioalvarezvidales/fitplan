# Diseño de datos de FitPlan

El MVP utiliza PostgreSQL y SQLAlchemy. Las entidades principales son:

- `users`: identidad, correo confirmado, hash de contraseña y versión de sesión.
- `user_profiles`: edad, género, peso, altura, nivel, objetivo, días y duración.
- `equipment`, `user_equipment`: catálogo y equipo disponible por usuario.
- `restrictions`, `user_restrictions`: molestias o restricciones físicas declaradas.
- `exercises`: catálogo con objetivo, nivel, equipo, restricciones, video e imagen.
- `workout_plans`, `plan_sessions`, `session_exercises`: recomendación semanal versionada.
- `workout_logs`: sesión completada, duración y retroalimentación.

La rutina planeada se mantiene separada del entrenamiento realizado para permitir comparar cumplimiento y adaptar la siguiente versión.
