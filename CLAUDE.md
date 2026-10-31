# CLAUDE.md — Generación musical adaptativa por movimiento (Azure Kinect + MediaPipe + Tone.js)

> Pon este archivo en la raíz del repo (`Generacion-Musical---Azure`). Claude Code lo lee al abrir la sesión.
> **Prompt de arranque (pégalo tal cual):**
> `Lee CLAUDE.md completo. Ejecuta SOLO la Tarea 1 (auditoría de solo lectura). No edites ningún archivo. Al terminar, entrégame la tabla de hallazgos y espera mi confirmación antes de la Tarea 2.`

## 1. Contexto
- Tesis UPC (TP202620503). Autores: Freddy Cuadros (PM) y Jimena Quintana (SM). Asesor: Willy Ugarte.
- Pipeline: Azure Kinect DK (Body Tracking, 32 articulaciones, color 720p, 30 fps) → MediaPipe Hands sobre recortes (ROI) en un hilo aparte → bucle `asyncio` en Python → WebSocket `localhost:8765` (JSON) → Tone.js en Chrome → parlante.
- Se ejecuta con `python main.py cuda lite` (Windows, GPU NVIDIA). Ya no se usan Leap Motion ni TV/proyector.
- Objetivo técnico en revisión: ciclo del pipeline ≤ 33.3 ms (30 Hz, igual que la cámara). Hoy es 38–42 ms (24–26 Hz).

## 2. Reglas de trabajo (obligatorias)
1. **Antes de escribir código**, describe la función: qué hace, con qué otras funciones se relaciona y cuáles son sus variables clave.
2. Al revisar o cambiar código, muestra **solo los fragmentos cambiados** (no archivos completos) y explica cada uno con esos tres puntos.
3. Separa siempre **MEDIDO** de **INFERIDO**. No inventes cifras ni citas. Si falta un dato, escribe `[POR COMPLETAR]` o pregunta.
4. Trabaja en una rama (`perf/ciclo-30hz`). Un cambio por commit. No toques `zona.py`, `muestreo.py` ni la lógica musical en la Tarea 2.
5. No crees documentos nuevos salvo que se pidan. "Hecho" es binario: cumple el criterio medido o no cumple.
6. Si un cambio altera el comportamiento musical (registro, histéresis, tempo), **detente y pregunta**.

## 3. Estado del código que conozco (snapshot) — VERIFICAR contra el repo real
Snapshot: `main.py` del 28/10 13:01 (`VERSION_MAIN = "tick-reanclado+manos-hilo+registro-angulo-2026-10-26"`).
Ese snapshot **no** tiene: vaciado de la cola de la cámara, los reportes `[FUSION]`/`[CAMARA]`, ni el recuadro de mano originado en la muñeca. El repo actual es más nuevo. **No asumas que el snapshot es el código vigente.**

Lo que sí hacía el snapshot, en un solo bucle secuencial (`bucle_kinect`):
`device.update()` → `get_depth_image()` + `get_color_image()` + `.copy()` → `body_tracker.update()` → registro (ángulo de hombros, media de ambos) → ofrece frame a `HiloManos` (cola de 1 hueco + bandera `ocupado`; si está ocupado, el frame se salta) → `mapeo.actualizar` (tempo, intensidad, λ) + tick de nota → `enviar_a_todos` (WebSocket) + `print` + escritura CSV con `flush()` en cada ciclo → dibujo OpenCV 1 de cada `DIBUJAR_CADA=2` ciclos.

## 4. Línea base MEDIDA (logs `[PERF]`/`[CAMARA]`, CSV de latencias del navegador, 26–28/10/2026)
| Etapa por ciclo | ms | Nota |
|---|---|---|
| `cap_update` | 0 | Python **nunca espera** a la cámara: siempre va atrasado |
| `cap_imgs` (depth + color + copy) | 6–7 | |
| `tracker` (Body Tracking, GPU, lite) | 23–24 | Es el piso del ciclo |
| `manos` (ofrecer frame + leer resultado) | 1 | |
| `mapeo` (registro, ángulos CSV, extremidades, tick) | 4 | |
| `salida` (WebSocket + print + CSV flush) | 1–2 | WebSocket solo: 0.6–1.0 ms |
| `dibujo` (promedio) | 2–3 | |
| **Ciclo total** | **38–42** | = suma de las etapas → todo es secuencial |
- Fuera del tracker quedan ≈ 15–17 ms. Para 33.3 ms hay que dejar ≤ ≈ 10 ms fuera del tracker, **si todo sigue en fila**.
- Cola de cámara: antes del arreglo 221–223 ms de espera (p95 ≈ 239); después ≈ 21–25 ms (p95 ≈ 38–45) con 0.23–0.28 fotogramas descartados por ciclo.
- Hilo de manos: 23–33 ms por trabajo; edad de la mano (mediana) ≈ 40 ms; ≈ 13 actualizaciones/s por mano.
- GPU limitada por potencia: ≈ 1700–1750 de ≈ 2100 MHz durante el tracker (logs `nvidia-smi`).
- Navegador (CSV, columna `latencia_ms` = `Date.now() − t_cap_ms`), sesiones finales 28/10: media 35.6–38.4, p95 39–42.5, máx 82–101, >100 ms en 0–0.03%. `base_latency` = 10 ms; `output_latency` reportada = 0.0 (no es confiable).
- `lat_tick_ms` (RNF01b ≤ 250 ms): media 47.6–51.2.

## 5. Hipótesis (INFERIDAS, no medidas) — la Tarea 1 debe confirmarlas o refutarlas
- H1. Los 23 ms de espera de cámara se deben a que el ciclo (≈ 41 ms) es más lento que la cámara (33.3 ms): siempre hay un fotograma ya esperando. Si el ciclo baja de 33.3 ms, `cap_update` pasará a > 0 y esa espera caerá hacia 0.
- H2. Las cifras RNF01 de ESTADO_ACTUAL (media 58–62, p95 78–83, máx 112–115) equivalen a `latencia_ms` del CSV (≈ 36–38) **más** la espera de cámara (≈ 23). Cuadra en la media; **no está verificado en p95/máx**. Confirmar qué instante estampa hoy `t_cap_ms` (¿recepción en Python o llegada al PC?).
- H3. `lat_tick_ms` ≈ 48–51 ms = tiempo desde `t_ciclo` hasta el sorteo (≈ 30 ms de etapas previas) + espera hasta el siguiente ciclo en que se evalúa el tick (0 a 41 ms).
- H4. Cortes baratos posibles (hay que medirlos, no suponerlos): quitar `get_depth_image()` si solo se usa para el `ok`; evitar la copia del color; `flush()` del CSV cada N ciclos; `print` cada N ciclos; sin ventana OpenCV en sesiones de evaluación; leer las articulaciones una sola vez por ciclo.
- H5. Un pipeline de 2 etapas en hilos (A: captura + tracker ≈ 31 ms; B: mapeo + envío + log ≈ 10 ms) permitiría 30 Hz sin recortar etapas. Los DLL de ctypes sueltan el GIL durante la llamada nativa, pero hay que comprobarlo con medición.

## 6. TAREA 1 — Auditoría de solo lectura (no edites nada)
Entrega una tabla `pregunta | respuesta | evidencia (archivo:línea) | MEDIDO o INFERIDO`.
1. ¿Qué archivos y versiones forman el sistema hoy? (`main.py`, `zona.py`, `muestreo.py`, `manos.py`, `servidor.py`, `index.html`, `fluidez.py` si existe). Muestra `VERSION_MAIN`.
2. ¿Existe vaciado de la cola de la cámara? Muestra el bucle y explica cómo garantiza que se procesa el fotograma **más reciente** y no uno viejo.
3. ¿Qué instante estampa `t_cap_ms` y cómo se calcula `latencia_ms` en `index.html`? ¿Incluye la espera de cámara? (confirma o refuta H2).
4. ¿Qué cola/umbral tiene `HiloManos` y por qué no acumula retraso? ¿Qué pasa con los fotogramas que se saltan?
5. ¿Dónde se espera de forma bloqueante dentro de `async def bucle_kinect`? ¿Las llamadas bloqueantes frenan también al servidor WebSocket?
6. Perfila un ciclo con `cProfile` o cronómetros por línea en `cap_imgs`, `mapeo` y `salida`. Reporta ms por línea. Ordena por costo.
7. ¿El código usa el promedio de los ángulos de ambos hombros para el registro? (esperado: `COMBINACION_BRAZOS = "media"`).
8. ¿La histéresis (`UMBRAL_ESTABILIDAD_ZONA = 6`) y las ventanas están en ciclos o en segundos? Lista cada parámetro que dependa de la tasa de ciclos.
9. ¿Qué mide `edad` de la mano exactamente (fórmula y punto de referencia)?
10. Con lo medido, responde: ¿es viable llegar a ciclo ≤ 33.3 ms **sin reescribir**? Da el presupuesto por etapa y el margen.

## 7. TAREA 2 — Plan de reducción del ciclo (solo después de que Ale confirme la Tarea 1)
Orden: (a) medir línea base: 3 sesiones de 3 min con el mismo movimiento; (b) cortes baratos de H4, uno por commit, con tabla antes/después; (c) si no basta, propón el pipeline de 2 etapas (H5): hilo A = captura + tracker, hilo B = mapeo + envío + log, con traspaso de **tamaño 1 que descarta lo viejo** (nunca acumula); (d) cada paso se mide con `[PERF]`, `[CAMARA]` y el CSV del navegador.

**Criterios de aceptación (binarios, 10 min continuos, `python main.py cuda lite`):**
- C1. Ciclos/s ≥ 29.5 sostenidos y `cap_update` > 0 ms.
- C2. Espera de cámara: p95 ≤ línea base y sin crecimiento durante los 10 min.
- C3. `latencia_ms` del CSV: media, p95 y máx **no peores** que la línea base (misma definición).
- C4. `lat_tick_ms` ≤ 250 ms en el 100% de los sorteos.
- C5. Mismo CSV de sesión y mismo comportamiento musical (sin cambios de registro, tempo o timbre).
Si C1 no se cumple, reporta el porcentaje de ciclos > 33.3 ms y qué etapa los causa. No declares "hecho".

## 8. Fuera de alcance por ahora
- Reescribir en C++ u otro lenguaje (no hay evidencia de que Python sea el cuello: el tracker ocupa ≈ 58% del ciclo).
- Cambiar umbrales de la tesis. Eso se argumenta en el documento, no en el código.
- Medir la latencia total hasta el sonido (US23): requiere captura de audio; se hace después.