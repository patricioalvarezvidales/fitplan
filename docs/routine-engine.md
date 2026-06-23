# Motor de rutinas adaptativas

## Enfoque seleccionado

El MVP usará un motor híbrido de **reglas, restricciones y puntuación**. No se utilizará un árbol binario como estructura central y la IA generativa no tomará decisiones críticas de entrenamiento.

## Generación inicial

1. Recibir objetivo, nivel, días, minutos por sesión, lugar, equipo, preferencias y restricciones.
2. Elegir una plantilla semanal compatible con los días disponibles.
3. Filtrar ejercicios incompatibles.
4. Puntuar los ejercicios restantes por objetivo, nivel, grupo muscular, preferencia y variedad.
5. Construir sesiones dentro del límite de tiempo.
6. Guardar una explicación de cada selección.

## Retroalimentación por sesión

El usuario registrará:

- sesión completada o incompleta;
- dificultad percibida de 1 a 10;
- energía de 1 a 5;
- molestias o dolor;
- ejercicio omitido y motivo;
- equipo realmente disponible;
- comentario opcional.

## Adaptación

La adaptación se realizará al cerrar cada sesión y al finalizar la semana:

- mantener cuando el esfuerzo y cumplimiento estén dentro del rango esperado;
- progresar gradualmente cuando la sesión se complete con facilidad;
- reducir volumen o cambiar ejercicio cuando exista fatiga alta o incumplimiento repetido;
- bloquear y sustituir ejercicios que generen dolor o contradigan una restricción;
- registrar cada cambio en una bitácora de decisiones.

Los umbrales serán configurables y deberán validarse con un profesional antes de considerarse recomendaciones de salud.

## Uso futuro de IA

La IA puede añadirse después para resumir comentarios, explicar cambios o clasificar texto libre. No será necesaria para que el MVP funcione.
