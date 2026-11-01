# DECISIONES — registro con fecha y razón

> Una decisión por fila. Si cambias una, no la borres: añade una nueva que la reemplace. Solo Ale decide; Code propone y registra.

## Decisiones vigentes
| ID | Fecha | Decisión | Razón | Evidencia | Estado |
|---|---|---|---|---|---|
| D-001 | 26/10/2026 | Uso siempre de pie | Estabilidad del seguimiento del cuerpo | ESTADO_ACTUAL | Vigente |
| D-002 | `[POR COMPLETAR]` | Registro por ángulo de ambos hombros combinados con la media (`COMBINACION_BRAZOS="media"`; el máximo queda como alternativa) | Cada brazo se normaliza por separado; la media usa ambos | `main.py` líneas 56 y 458–460 (auditoría 31/10) | Vigente |
| D-003 | 28/10/2026 | **Un** hilo de manos (se descarta un hilo por mano) | 1 → 2 hilos: ciclo 38.4 → 42.0 ms (p95 45 → 50), pipeline 23.8 Hz, RNF01 +3.6 ms; la ganancia a 23.5 actualizaciones/s por mano no compensa | `docs/MEDICIONES.md` secciones 1 y 3 | **Aplicada el 31/10** (commit `9b2d30a`, rama `perf/ciclo-30hz`). Nota 31/10: con 1 hilo el ciclo varió 38.0–46.5 ms entre corridas del mismo día (CSV de sesión 31/10), más que el efecto 1→2 hilos (3.6 ms); la evidencia de la decisión es más débil de lo que parecía |
| D-004 | 28/10/2026 | Vaciar la cola de la cámara (`DESCARTAR_COLA_CAMARA=True`, hasta `MAX_DESCARTE_POR_CICLO=10`) | Espera de cámara 220 ms → ≈ 23 ms; no hay música "en diferido" | `[CAMARA]` y CSV de sesión | Vigente |
| D-005 | `[POR COMPLETAR]` | Leap Motion y TV/proyector fuera del sistema | Arquitectura con Kinect + MediaPipe | ESTADO_ACTUAL | Vigente |
| D-006 | 31/10/2026 | Guardar automáticamente los reportes `[PERF]`/`[PERF-LINEA]`/`[CAMARA]`/`[FUSION]`/`[ROI]` en `sesiones/<sesion>_perf.txt` y las latencias del navegador en `sesiones/<sesion>_latencias.csv` (el navegador las envía por el WebSocket cada 0.5 s; el botón de descarga se mantiene) | `Start-Transcript` no grabó la salida de Python y se perdieron los `[PERF]` de las corridas de las 16:43 y 16:46; la descarga manual se olvida | Commits `e2fef0d` y `3151709`; prueba sin Kinect: hash de 721 filas igual en navegador y disco | Vigente |
| D-008 | 01/11/2026 | `main` arranca con MJPG (`COLOR_BGRA32=False`, `VERSION_MAIN = mjpg-un-hilo-2026-11-01`); BGRA32 queda como experimento | Con BGRA32 la espera de cámara sube de 23 a 46.5 ms y no cumple C2; MJPG es la configuración de la línea base medida | Commit `d3c32be`; `docs/MEDICIONES.md` 4b | Vigente |
| D-007 | 31/10/2026 | Probar el color en BGRA32 (paso 5; `COLOR_BGRA32=True`) | `to_numpy` costaba 6 ms por ciclo por decodificar MJPG en Python | Commit `f453ac0`; resultado en `docs/MEDICIONES.md` 4b: ciclo 39 → 35 ms, pero llegada del frame +22 ms; no cumple C1 ni C2 | **EXPERIMENTO.** El código está en `main` y en `perf/ciclo-30hz`, pero desactivado por defecto desde el 01/11 (D-008). Se activa con `COLOR_BGRA32=True`. Mantener o no es P-005 |

## Decisiones pendientes (decide Ale; Code no las aplica)
| ID | Pregunta | Opciones | Información que falta |
|---|---|---|---|
| P-001 | Histéresis y EMA al subir a 30 Hz | (a) expresarlas en ms para conservar el "sentir" actual (propuesta: ≈ 250 ms de histéresis); (b) dejar los ciclos y aceptar el cambio | Prueba de oído y conteo de cambios de registro por minuto con ambas versiones |
| P-002 | Qué instante define RNF01 | (a) recepción en Python (hoy); (b) llegada del frame al PC, sumando `lag_cam_ms` por muestra (propuesta) | Paso 7 del plan; criterio de la tesis (el TI dice "extremo a extremo" en el objetivo y RF06, pero RNF01/US23 miden hasta el navegador). **31/10:** con BGRA32 las dos definiciones dan conclusiones opuestas: (a) mejora ≈ 4.5 ms y (b) empeora ≈ 17–20 ms. Además (b) parece ser la definición de las cifras de ESTADO_ACTUAL (MEDICIONES sección 0) |
| P-003 | Dibujo en sesiones de evaluación | (a) sin ventana de OpenCV (propuesta); (b) mantenerla | Medición del ciclo sin ventana. **31/10:** la ventana cuesta 2.0 ms/ciclo de media; con BGRA32 el ciclo que dibuja mide 38–39 ms y los otros 32–33 ms (MEDICIONES 4b) |
| P-005 | ¿Se mantiene BGRA32? | (a) mantener BGRA32 (ciclo −4.5 ms y `latencia_ms` −4.5 ms, pero llegada→navegador +17–20 ms; C2 no cumple); (b) volver a MJPG y decodificar en el hilo de manos (propuesta de Code, sin medir); (c) volver a MJPG como estaba | Decidir P-002 primero, porque cambia qué opción gana; medir (b) |
| P-004 | Hz objetivo de US07/US08 | (a) llegar a 30 Hz; (b) justificar el valor medido como decisión de diseño si no afecta la percepción | Resultado de los pasos 5–9 y evaluación con usuarios (TP2); consulta con el asesor |
