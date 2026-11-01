# DECISIONES — registro con fecha y razón

> Una decisión por fila. Si cambias una, no la borres: añade una nueva que la reemplace. Solo Ale decide; Code propone y registra.

## Decisiones vigentes
| ID | Fecha | Decisión | Razón | Evidencia | Estado |
|---|---|---|---|---|---|
| D-001 | 26/10/2026 | Uso siempre de pie | Estabilidad del seguimiento del cuerpo | ESTADO_ACTUAL | Vigente |
| D-002 | `[POR COMPLETAR]` | Registro por ángulo de ambos hombros combinados con la media (`COMBINACION_BRAZOS="media"`; el máximo queda como alternativa) | Cada brazo se normaliza por separado; la media usa ambos | `main.py` líneas 56 y 458–460 (auditoría 31/10) | Vigente |
| D-003 | 28/10/2026 | **Un** hilo de manos (se descarta un hilo por mano) | 1 → 2 hilos: ciclo 38.4 → 42.0 ms (p95 45 → 50), pipeline 23.8 Hz, RNF01 +3.6 ms; la ganancia a 23.5 actualizaciones/s por mano no compensa | `docs/MEDICIONES.md` secciones 1 y 3 | **Decidida, NO aplicada en el repo**: el repo está en 28e con `HILO_POR_MANO=True`. Ale confirma antes del paso 2 |
| D-004 | 28/10/2026 | Vaciar la cola de la cámara (`DESCARTAR_COLA_CAMARA=True`, hasta `MAX_DESCARTE_POR_CICLO=10`) | Espera de cámara 220 ms → ≈ 23 ms; no hay música "en diferido" | `[CAMARA]` y CSV de sesión | Vigente |
| D-005 | `[POR COMPLETAR]` | Leap Motion y TV/proyector fuera del sistema | Arquitectura con Kinect + MediaPipe | ESTADO_ACTUAL | Vigente |

## Decisiones pendientes (decide Ale; Code no las aplica)
| ID | Pregunta | Opciones | Información que falta |
|---|---|---|---|
| P-001 | Histéresis y EMA al subir a 30 Hz | (a) expresarlas en ms para conservar el "sentir" actual (propuesta: ≈ 250 ms de histéresis); (b) dejar los ciclos y aceptar el cambio | Prueba de oído y conteo de cambios de registro por minuto con ambas versiones |
| P-002 | Qué instante define RNF01 | (a) recepción en Python (hoy); (b) llegada del frame al PC, sumando `lag_cam_ms` por muestra (propuesta) | Paso 7 del plan; criterio de la tesis (el TI dice "extremo a extremo" en el objetivo y RF06, pero RNF01/US23 miden hasta el navegador) |
| P-003 | Dibujo en sesiones de evaluación | (a) sin ventana de OpenCV (propuesta); (b) mantenerla | Medición del ciclo sin ventana |
| P-004 | Hz objetivo de US07/US08 | (a) llegar a 30 Hz; (b) justificar el valor medido como decisión de diseño si no afecta la percepción | Resultado de los pasos 5–9 y evaluación con usuarios (TP2); consulta con el asesor |
