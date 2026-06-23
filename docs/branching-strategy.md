# Estrategia de ramas

FitPlan utilizará una estrategia ligera compatible con un proyecto individual y con CI/CD.

## Ramas permanentes

- `main`: versión demostrable y candidata a producción.
- `develop`: integración de funcionalidades y ambiente de staging.

## Ramas temporales

- `feature/<numero>-<descripcion>`: funcionalidad nueva.
- `fix/<numero>-<descripcion>`: corrección.
- `docs/<numero>-<descripcion>`: documentación.
- `hotfix/<descripcion>`: corrección urgente nacida desde `main`.

## Flujo

1. Crear un Issue.
2. Crear la rama desde `develop`.
3. Realizar commits pequeños con formato convencional.
4. Abrir un Pull Request hacia `develop`.
5. Esperar a que CI apruebe lint, pruebas y build.
6. Hacer squash merge y eliminar la rama temporal.
7. Al completar un incremento, abrir PR de `develop` hacia `main`.
8. Crear una etiqueta como `v0.1.0`.

## Commits sugeridos

- `feat: agrega formulario de perfil`
- `fix: evita sesiones duplicadas`
- `test: cubre filtro por equipo`
- `docs: documenta motor adaptativo`
- `chore: configura Docker Compose`
