# Trazabilidad de requisitos

| Historia | Implementación |
|---|---|
| Registro | `POST /auth/register`, validación de correo y contraseña, hash Argon2 y confirmación por token de desarrollo. |
| Inicio de sesión | JWT, mensajes de error y rutas protegidas. |
| Perfil físico | Formulario editable con validaciones de rangos, objetivo, nivel, días y tiempo. |
| Objetivo | Pérdida de peso, ganancia muscular o resistencia. |
| Rutina semanal | Motor determinístico por reglas, restricciones y puntuación. |
| Rutina del día | Día actual o siguiente sesión pendiente resaltada. |
| Completar sesión | Registro único e irreversible con fecha, duración y feedback. |
| Historial | Listado cronológico con filtros de 7, 30 días o todo. |
| Actualizar perfil | Datos precargados y usados en la siguiente regeneración. |
| Cerrar sesión | Incremento de versión del token e invalidación inmediata. |
| Equipo y restricciones | Filtrado previo de ejercicios incompatibles. |
| Video e imagen | Video embebido; imagen de respaldo cuando no existe video. |
| Adaptación | Reduce, mantiene o aumenta volumen según dificultad, energía y dolor reciente. |
