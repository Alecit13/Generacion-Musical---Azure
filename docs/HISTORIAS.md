# HISTORIAS — qué debe cumplir el sistema (US07–US28) y cómo se relaciona con el código

> Fuente de los criterios: `Plantilla_01 – Historias de Usuario y Criterios de Aceptación v1.0` (archivo del 28/10/2026; puede no ser la última versión).
> Fuente del estado: `ESTADO_ACTUAL` (31/10/2026). La copia de Anexo5 del Project marca US09 y US12 como "En curso"; ESTADO_ACTUAL los marca "Completado". `[POR COMPLETAR]` confirmar cuál es la vigente.
> HU0007 = US07, etc. "Hecho" es binario: todos los criterios de la historia cumplen, medidos.
> Este archivo no se edita por cuenta de Code. Si un cambio contradice un criterio, se detiene y se avisa a Ale.

## Sprint 2 — Captura y procesamiento
| US | Criterios (resumen) | Estado | Contra lo medido / el código |
|---|---|---|---|
| US07 Esqueleto 32 articulaciones a ~30 Hz | **-1** el módulo publica las 32 articulaciones a ~30 Hz. **-2** una articulación perdida se marca "no disponible" sin detener el resto | En curso | **No cumple -1 hoy**: ciclo 24–26 Hz (cámara 30 fps). -2: las articulaciones de mano del Kinect quedan NONE ≈ 53% de los frames y el resto sigue (compatible) |
| US08 Manos con MediaPipe a 30 FPS | **-1** procesa cada frame RGB a 30 FPS; 21 puntos por mano (42) con marca de tiempo. **-2** manos fuera de alcance: reporta ausencia **sin inventar un valor de apertura** | En curso | **No cumple -1 hoy**: ≈ 13 actualizaciones/s por mano con 1 hilo. **-2 en duda**: el snapshot mantiene la última apertura `HOLD_APERTURA_S = 0.5 s`; decidir si eso cuenta como "inventar" (registrar en DECISIONES) |
| US09 Fusión temporal ±16 ms | **-1** el módulo de fusión elige el par más reciente dentro de ±16 ms (cola compartida). **-2** fuera de ventana: usa el último dato válido y registra **desincronización** | Completado (ESTADO) / En curso (Anexo5 Project) | Cumple por construcción (`par_dt_ms = 0`, mismo frame). El texto describe un módulo de fusión y cola compartida que el código actual no tiene: la historia está desactualizada |
| US10 WebSocket Python ↔ frontend | **-1** JSON sin errores de serialización. **-2** si se pierde la conexión, restablece sin reiniciar la sesión | Completado | **Falta la prueba en vivo HU0010-2** (Caso A: reiniciar Python y la página reconecta en ≤ 2 s; Caso B: cerrar la pestaña y Python no se detiene) |
| US11 Amplitud del desplazamiento | **-1** valor normalizado, independiente del ángulo articular, ventana temporal | Completado | `VENTANA_INTENSIDAD_S = 2.0` (en segundos) |
| US12 Filtro de suavizado | **-1** reduce el ruido del sensor de forma perceptible. **-2** un movimiento real y rápido conserva su tendencia, **sin retrasos perceptibles superiores al umbral de latencia** | Completado (ESTADO) / En curso (Anexo5 Project) | Jitter −22% a −32% hombros, −52% a −53% rodilla (MEDIDO, dos sesiones). El retardo del EMA depende del ciclo (≈ 41 → 33 ms al subir a 30 Hz): afecta -2 (ver P-001) |
| US13 Fluidez de la trayectoria | **-1** calcula la fluidez "según Camurri et al. (2024) y Piana et al. (2016)", se actualiza en tiempo real | En curso | λ = 1 − aceleración media normalizada sobre 0.6 s. El criterio cita Camurri 2024 como definición, pero Camurri 2024 es una aplicación; la definición viene de Piana 2016 y Camurri 2016. Corregir el texto con justificación |

## Sprint 3 — Generación musical (estado oficial: No iniciado; el código ya cubre parte, sin verificar criterios)
| US | Criterios (resumen) | Vínculo con el código |
|---|---|---|
| US14 Motor Tone.js | -1 reproduce audio sin errores de inicialización. -2 autoplay: requiere acción del usuario | `index.html` (Tone.js local, `lookAhead = 0`) |
| US15 Registro por postura | -1 asigna zona grave/media/aguda. -2 **no cambia de zona hasta sostener el movimiento un intervalo mínimo** | `RegistroPorAngulo` + histéresis `UMBRAL_ESTABILIDAD_ZONA = 6` **ciclos**: el criterio habla de un intervalo (tiempo) → apoya expresarla en ms (P-001) |
| US16 Tempo | -1 cambia proporcional, sin saltos. -2 se satura en los límites | `MapeoExtremidades`, `NOTAS_POR_SEG_MIN/MAX` |
| US17 Timbre | -1 timbre proporcional a la apertura de manos | `HiloManos`, `apertura01` |
| US18 Intensidad | -1 volumen refleja la energía acumulada. -2 se satura | `n_inten`, `intensidad` |
| US19 Muestreo ponderado | -1 nota de la escala activa. -2 no repite más del límite. -3 el nivel de variabilidad cambia la frecuencia | `muestreo.py` |
| US20 Transiciones suaves | -1 el usuario percibe fluidez (prueba de percepción) | Pendiente de prueba con personas |
| US21 Variabilidad + semilla | -1 misma secuencia con misma entrada, semilla y variabilidad. -2 variabilidad mínima = determinístico | `[POR COMPLETAR]` verificar en código |
| US22 Registro de semilla y versión | -1 el registro permite reconstruir la configuración | `VERSION_MAIN` en el nombre del CSV (parcial) |

## Sprint 4 — Medición y pruebas
| US | Criterios (resumen) | Vínculo con el plan de ciclo |
|---|---|---|
| US23 Latencia de parámetros continuos | **-1** mide "el tiempo entre la captura del movimiento y la actualización de los parámetros continuos"; **no supera 100 ms** en condiciones normales del laboratorio. **-2** si supera 100 ms, el registro **identifica en qué etapa ocurrió el mayor retardo** | Define qué es "captura" (ver P-002). -2 exige registrar el tiempo por etapa junto con cada medición: `[PERF]` + `lag_cam_ms` |
| US24 Latencia de cambio de nota | **-1** ≤ 250 ms entre el tick y el sorteo (RNF01b). **-2** registra el incumplimiento | `lat_tick_ms`: media 47.6–51.2 ms, 0% > 250 ms en las 5 sesiones del 28/10 (MEDIDO) |
| US25 Pruebas unitarias | -1 cada módulo produce el comportamiento esperado de forma aislada | Los micro-benchmarks de Code son un precedente |
| US26 Integración | -1 captura, procesa y genera audio sin errores en una sesión continua. -2 identifica qué módulo falló | La corrida de 10 min del plan |
| US27 Calibración de tablas | -1 rangos iniciales por literatura (Agres 2023, Mahfoudi 2023). -2 refinamiento por escucha interna, versión congelada | Sin relación con el plan de ciclo |
| US28 Validación offline del generador | -1 evidencia de diversidad entre ejecuciones. -2 parámetros continuos consistentes mientras la melodía varía | Sin relación con el plan de ciclo |

US29–US37 son de evaluación con usuarios (TP2). US34 (parlante JBL) y US35 (inicio y parada autónomos) tocan el código; se agregan aquí cuando entren a un sprint.

## Lo que esto implica para el plan de ciclo
- Un desvío frente a US07 (~30 Hz) y US08 (30 FPS) es un desvío frente a un criterio de aceptación escrito. Cambiarlo requiere una decisión argumentada en `DECISIONES.md` (P-004) y consulta con el asesor.
- Todo cambio de código o medición debe decir qué criterio (HU0007-1, HU0023-2, …) cumple o afecta.