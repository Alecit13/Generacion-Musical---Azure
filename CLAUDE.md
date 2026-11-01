# CLAUDE.md — Generación musical adaptativa por movimiento (Azure Kinect + MediaPipe + Tone.js)

> Este archivo es ESTABLE: contexto, reglas, arquitectura y criterios. Lo que cambia (mediciones, plan, hipótesis) vive en `docs/`.
> **Prompt de arranque de cada sesión:** `Lee CLAUDE.md, docs/MEDICIONES.md y docs/DECISIONES.md. Dime en 5 líneas dónde estamos y cuál es el siguiente paso pendiente del plan. No edites nada hasta que yo confirme.`

@docs/MEDICIONES.md
@docs/DECISIONES.md

## 1. Contexto
- Tesis UPC (código TP202620503). Autores: Freddy Cuadros (PM) y Jimena Quintana (SM). Asesor: Willy Ugarte.
- Pipeline: Azure Kinect DK (Body Tracking, 32 articulaciones, color 720p, 30 fps) → MediaPipe Hands sobre recortes (ROI) en hilo(s) aparte → bucle `asyncio` en Python → WebSocket `localhost:8765` (JSON) → Tone.js en Chrome → parlante.
- Ya no se usan Leap Motion ni TV/proyector.
- Objetivo técnico en revisión: ciclo del pipeline ≤ 33.3 ms (30 Hz, igual que la cámara).

## 2. Cómo ejecutar
- Entorno: venv `env_cv` (Python 3.12.10; pykinect_azure 0.0.4, mediapipe 0.10.21, websockets 17.2, cv2 4.11) — versiones medidas el 31/10/2026.
- Comando: `python main.py cuda lite` (Windows, GPU NVIDIA). Abrir `index.html` en Chrome.
- Salidas: CSV de sesión en `sesiones/` (el nombre lleva `VERSION_MAIN`); CSV de latencias con el botón "Descargar latencias (CSV)" de la página. `q` en la ventana de OpenCV cierra.

## 3. Archivos del sistema
- `main.py`: bucle principal, mapeo de extremidades, registro por ángulo, `HiloManos`, métricas `[PERF]`/`[CAMARA]`/`[FUSION]`.
- `servidor.py`: WebSocket. `index.html`: Tone.js local y medición de latencia en el navegador.
- `zona.py` (solo si `REGISTRO_POR_ANGULO=False`), `muestreo.py` (nota y octava), `manos.py` (apertura).
- `fluidez.py` **no se importa** (código muerto): la fluidez λ está en `main.py` (`MapeoExtremidades`).
- `grafico.py`, `evidencia.py`, `pruebas.py`: análisis offline.

## 4. Arquitectura (cómo funciona el ciclo)
Un solo bucle secuencial en `bucle_kinect`, en el hilo del event loop:
1. `obtener_capture_reciente()`: espera el primer capture y vacía la cola de la cámara (FIFO) para quedarse con el más reciente. Luego se estampa `t_cap_ms`.
2. `to_numpy()` del color (la cámara entrega MJPG y se decodifica en cada ciclo) y copia.
3. `body_tracker.update()` (GPU, ≈ 23–24 ms; es el piso del ciclo).
4. Registro: ángulo de hombros, `COMBINACION_BRAZOS = "media"`; histéresis por conteo de ciclos.
5. Manos: se ofrece el frame a `HiloManos` (cola de 1 hueco + bandera `ocupado`; si está ocupado, el frame se salta, nunca se acumula). El recuadro (ROI) sale de las articulaciones del Kinect. Cuerpo y manos salen del mismo frame (`par_dt_ms = 0`).
6. `mapeo.actualizar` (tempo, intensidad, λ) y tick de nota (una evaluación por ciclo).
7. `await enviar_a_todos(...)` + `print` + escritura del CSV con `flush()`.
8. Dibujo OpenCV (1 de cada `DIBUJAR_CADA` ciclos), después del envío.
- El servidor WebSocket comparte el event loop: conectar y reconectar solo avanza una vez por ciclo. Para un cliente local el envío no se ve afectado.

## 5. Definiciones de métricas (no cambian sin decisión escrita en `docs/DECISIONES.md`)
- `latencia_ms` (navegador, tipo `continuo`) = `Date.now() − t_cap_ms`. **Excluye** la espera de cámara (`lag_cam_ms`), la latencia interna del SDK/USB y la salida de audio.
- `lag_cam_ms` = `t_upd − system_timestamp` del SDK: cuánto esperó el frame desde que llegó al PC hasta que Python lo tomó.
- `transporte_ms` = `tRecv − t_env_ms`.
- `lat_tick_ms` (RNF01b, ≤ 250 ms): retraso entre el tick programado y el sorteo de la nota.
- `edad_manos_ms` = `(t_ciclo − max(ult_t_ap)) × 1000`: edad del frame que originó el dato de manos más fresco de cualquiera de las dos manos, medida desde la recepción del frame actual. No incluye tracker ni envío.
- Los números van siempre con su definición. Si dos documentos dan cifras distintas, revisa primero que usen la misma definición.

## 6. Reglas de trabajo (obligatorias)
1. **Antes de escribir código**, describe la función: qué hace, con qué otras funciones se relaciona y cuáles son sus variables clave.
2. Al revisar o cambiar código, muestra **solo los fragmentos cambiados** y explica cada uno con esos tres puntos.
3. Separa siempre **MEDIDO** de **INFERIDO**. No inventes cifras ni citas. Si falta un dato, escribe `[POR COMPLETAR]` o pregunta.
4. Trabaja en rama; un cambio por commit; sin commit previo no se toca `main.py`.
5. No cambies comportamiento musical (registro, histéresis, tempo, timbre) sin preguntar.
6. No crees documentos nuevos salvo que se pidan. "Hecho" es binario: cumple el criterio medido o no cumple.
7. Una cifra solo entra a `docs/MEDICIONES.md` si cita el archivo CSV o log de origen.
8. No edites `CLAUDE.md` por tu cuenta. Los cambios a reglas o definiciones los decide Ale.

## 7. Criterios de aceptación del trabajo de ciclo (binarios; corrida de 10 min con `python main.py cuda lite`)
- C1. Ciclos/s ≥ 29.5 sostenidos y `cap_update` > 0 ms (Python espera a la cámara).
- C2. Espera de cámara: p95 ≤ línea base y sin crecimiento durante los 10 min.
- C3. `latencia_ms`: media, p95 y máx no peores que la línea base (misma definición).
- C4. `lat_tick_ms` ≤ 250 ms en el 100% de los sorteos.
- C5. Mismo CSV de sesión y mismo comportamiento musical (o cambio aprobado en `docs/DECISIONES.md`).
Si C1 no se cumple, reporta el porcentaje de ciclos > 33.3 ms y qué etapa los causa. No declares "hecho".

## 8. Cierre de sesión (Ale lo pega al terminar)
`Cierra la sesión: (1) actualiza docs/MEDICIONES.md con lo medido hoy, separando MEDIDO de INFERIDO y citando el CSV o log de origen; (2) si hubo una decisión, añádela a docs/DECISIONES.md con fecha y razón; (3) marca en el plan lo hecho y lo pendiente; (4) muéstrame solo los fragmentos cambiados. No toques CLAUDE.md.`

## 9. Fuera de alcance por ahora
- Reescribir en C++ u otro lenguaje (el tracker ocupa ≈ 58% del ciclo; no hay evidencia de que Python sea el cuello).
- Cambiar umbrales de la tesis. Eso se argumenta en el documento, no en el código.
- Medir la latencia total hasta el sonido (US23): requiere captura de audio; se hace después.
