# CLAUDE.md — Generación musical adaptativa por movimiento (Azure Kinect + MediaPipe + Tone.js)

> Este archivo es ESTABLE: contexto, reglas, arquitectura y criterios. Lo que cambia (mediciones, plan, hipótesis, decisiones) vive en `docs/`. Solo Ale lo edita.
> **Prompt de arranque de cada sesión:** `Lee CLAUDE.md, docs/HISTORIAS.md, docs/MEDICIONES.md y docs/DECISIONES.md. Dime en 5 líneas dónde estamos, qué decisiones siguen "por aprobar" y cuál es el siguiente paso pendiente del plan. No edites nada hasta que yo confirme.`

@docs/HISTORIAS.md
@docs/MEDICIONES.md
@docs/DECISIONES.md

## 1. Contexto
- Tesis UPC (código TP202620503). Autores: Freddy Cuadros (PM) y Jimena Quintana (SM). Asesor: Willy Ugarte.
- Pipeline: Azure Kinect DK (Body Tracking, 32 articulaciones, color 720p, 30 fps) → MediaPipe Hands sobre recortes (ROI) en un hilo aparte → bucle `asyncio` en Python → WebSocket `localhost:8765` (JSON) → Tone.js en Chrome → parlante.
- Ya no se usan Leap Motion ni TV/proyector.
- Objetivo técnico en revisión: ciclo del pipeline ≤ 33.3 ms (30 Hz, igual que la cámara). Los desvíos frente a los criterios de las historias (HU0007-1, HU0008-1, HU0023-1) se deciden con Ale en `docs/DECISIONES.md`; no se "arreglan" cambiando el criterio.
- Equipo de desarrollo: HP Victus, Intel Core i5-13420H, 16 GB RAM, NVIDIA GeForce RTX 3050 6 GB Laptop. Las mediciones solo se comparan entre corridas hechas con el mismo plan de energía y en la misma sesión de trabajo (ver sección 6, regla 10).

## 2. Cómo ejecutar
- Entorno: venv `env_cv` (Python 3.12.10; pykinect_azure 0.0.4, mediapipe 0.10.21, websockets 17.2, cv2 4.11) — versiones medidas el 31/10/2026. El Python global (3.14) no es el del proyecto. En CMD se activa con `env_cv\Scripts\activate.bat`; en PowerShell con `.\env_cv\Scripts\Activate.ps1`.
- Comando: `python main.py cuda lite` (Windows, GPU NVIDIA). Abrir `index.html` en **una sola** pestaña de Chrome.
- Opciones de línea de comandos (D-011, D-012, D-013, D-015): `--con-ventana` (enciende la ventana de OpenCV; por defecto está apagada, D-012), `--sin-decod-hilo` (desactiva la decodificación del color en el hilo de manos, que es el valor por defecto desde D-015; `--decod-hilo` se sigue aceptando), `--swi1ms` y `--sin-manos` (solo diagnóstico). Con `COLOR_BGRA32=True` hay que pasar `--sin-decod-hilo`. Cuando una opción se sale del valor por defecto, `VERSION_MAIN` lleva un sufijo (`-conventana`, `-sindecodhilo`, `-swi1ms`, `-sinmanos`) y la cabecera de `_perf.txt` anota la configuración. `--con-ventana` y `--sin-ventana` juntas dan error.
- Cierre: **un solo Ctrl+C** (es lo normal, porque no hay ventana). Con `--con-ventana` también sirve `q`. Al cerrar, Python espera 1 s para recibir el último lote de latencias del navegador.
- Salidas (D-006), en `sesiones/`: CSV de sesión (el nombre lleva `VERSION_MAIN`), `<sesion>_perf.txt` (reportes `[PERF]`, `[PERF-LINEA]`, `[CAMARA]`, `[FUSION]`, `[ROI]`) y `<sesion>_latencias.csv` (el navegador lo envía por el WebSocket; el botón de descarga sigue existiendo).

## 3. Archivos del sistema
- `main.py`: bucle principal, mapeo de extremidades, registro por ángulo, `HiloManos`, métricas `[PERF]`/`[CAMARA]`/`[FUSION]`.
- `servidor.py`: WebSocket. `index.html`: Tone.js local y medición de latencia en el navegador.
- `zona.py` (solo si `REGISTRO_POR_ANGULO=False`; sigue contando frames), `muestreo.py` (nota y octava), `manos.py` (apertura).
- `fluidez.py` **no se importa** (código muerto): la fluidez λ está en `main.py` (`MapeoExtremidades`).
- `grafico.py`, `evidencia.py`, `pruebas.py`: análisis offline.
- `registrar_procesos.ps1`: registra cada ≈ 1 s el uso de CPU por proceso durante una corrida.
- `docs/HISTORIAS.md`: criterios de aceptación US07–US28 (no lo edita Code).

## 4. Arquitectura (cómo funciona el ciclo)
Un solo bucle secuencial en `bucle_kinect`, en el hilo del event loop:
1. `obtener_capture_reciente()`: espera el primer capture y vacía la cola de la cámara (FIFO) para quedarse con el más reciente. Luego se estampa `t_cap_ms`.
2. Color: por defecto (D-015) el ciclo solo copia los bytes JPEG y `HiloManos` los decodifica; con `--sin-decod-hilo` se decodifica con `to_numpy()` en el ciclo (≈ 6 ms). `COLOR_BGRA32=True` es un experimento descartado como defecto (D-008): el SDK entrega el frame más tarde.
3. `body_tracker.update()` (GPU, ≈ 21–24 ms según el estado del equipo; es el piso del ciclo).
4. Registro: ángulo de hombros, `COMBINACION_BRAZOS = "media"`; histéresis de **250 ms sostenidos** (`UMBRAL_ESTABILIDAD_ZONA_S`, D-010), con tope `DT_MAX_ZONA_S` por ciclo para que un hueco de cuerpo no cuente. Ya no cuenta ciclos.
5. Manos: se ofrece el frame a `HiloManos` (cola de 1 hueco + bandera `ocupado`; si está ocupado, el frame se salta, nunca se acumula). El recuadro (ROI) sale de las articulaciones del Kinect. Cuerpo y manos salen del mismo frame (`par_dt_ms = 0`). El hilo alterna las manos (`ALTERNAR_MANOS=True`).
6. `mapeo.actualizar` (tempo, intensidad, λ) y tick de nota (una evaluación por ciclo).
7. `await enviar_a_todos(...)` + `print` + escritura del CSV con `flush()`.
8. Dibujo OpenCV (1 de cada `DIBUJAR_CADA` ciclos), después del envío; no se ejecuta salvo con `--con-ventana` (D-012).
- El servidor WebSocket comparte el event loop: conectar y reconectar solo avanza una vez por ciclo. Para un cliente local el envío no se ve afectado.

## 5. Definiciones de métricas (no cambian sin decisión escrita en `docs/DECISIONES.md`)
- **Cuatro instantes distintos** (detalle en `docs/MEDICIONES.md` sección 0): (a) Python recibe el frame; (b) el frame llega al PC; (c) el sensor captura / el sonido sale (extremo a extremo); RNF01b mide dentro de Python.
- (a) `latencia_ms` (navegador, tipo `continuo`) = `Date.now() − t_cap_ms`. **Excluye** la espera de cámara (`lag_cam_ms`), la latencia interna del SDK/USB y la salida de audio. `t_cap_ms` se estampa después de vaciar la cola.
- `lag_cam_ms` = `t_upd − system_timestamp` del SDK: cuánto esperó el frame desde que llegó al PC hasta que Python lo tomó.
- (b) `latencia_llegada_ms` = `latencia_ms + lag_cam_ms`, por muestra (se mide en línea desde el paso 7). **Definición ACEPTADA para RNF01/US23 (100 ms)** por Ale el 02/11/2026 (D-009). (a) se informa como secundaria.
- (c) Extremo a extremo: **sigue siendo el objetivo**. No está medido (paso 11 del plan). Se informará aunque no cumpla. La definición de RNF01/US23 no se cambia después de ver el resultado de (c).
- `transporte_ms` = `tRecv − t_env_ms`.
- `lat_tick_ms` (RNF01b, ≤ 250 ms): retraso entre el tick programado y el sorteo de la nota.
- `edad_manos_ms` = `(t_ciclo − max(ult_t_ap)) × 1000`: edad del frame que originó el dato de manos más fresco de cualquiera de las dos manos, medida desde la recepción del frame actual. No incluye tracker ni envío.
- Manos (HU0008-1): hay dos medidas distintas, **trabajos/s** del hilo (frames procesados) y **actualizaciones por mano/s**. Cuál cuenta para el criterio está abierto (P-009); mientras tanto se informan las dos y no se declara "cumple" ni "no cumple".
- Los números van siempre con su definición. Si dos documentos dan cifras distintas, revisa primero que usen la misma definición.

## 6. Reglas de trabajo (obligatorias)
1. **Antes de escribir código**, describe la función: qué hace, con qué otras funciones se relaciona y cuáles son sus variables clave.
2. Al revisar o cambiar código, muestra **solo los fragmentos cambiados** y explica cada uno con esos tres puntos.
3. Separa siempre **MEDIDO** de **INFERIDO**. No inventes cifras ni citas. Si falta un dato, escribe `[POR COMPLETAR]` o pregunta.
4. Trabaja en rama; un cambio por commit; sin commit previo no se toca `main.py`.
5. No cambies comportamiento musical (registro, histéresis, tempo, timbre) sin preguntar.
6. No crees documentos nuevos salvo que se pidan. "Hecho" es binario: cumple el criterio medido o no cumple.
7. Una cifra solo entra a `docs/MEDICIONES.md` si cita el archivo CSV o log de origen.
8. No edites `CLAUDE.md` ni `docs/HISTORIAS.md` por tu cuenta. Los cambios a reglas, definiciones o criterios los decide Ale.
9. Cada cambio de código o medición dice qué criterio de historia cumple o afecta (HU0007-1, HU0023-2, …). Si un cambio contradice un criterio, detente y avisa.
10. Protocolo de corrida: plan de energía de máximo rendimiento y laptop enchufada (D-014); una sola pestaña de `index.html` (sin recargarla durante la tanda); sin otros clientes conectados (ni pestañas de prueba de Code); calentamiento descartado; configuraciones **intercaladas** (A B C A B C), no en bloques; una corrida base al final para detectar ralentización del equipo; cierre con un solo Ctrl+C o `q`. Si el `_latencias.csv` tiene el doble de filas `continuo` que el CSV de sesión, la corrida se repite. No se comparan corridas de días distintos o con plan de energía distinto sin decirlo. Detalle en `docs/MEDICIONES.md` sección 10. Antes de la tanda, **cierra VS Code** y los programas que no uses, y revisa el Administrador de tareas: el 04/11 `code` usó ≈ 1.6 núcleos y degradó la corrida (MEDIDO por proceso, causa INFERIDA con evidencia fuerte). Durante cada corrida, una terminal aparte ejecuta `registrar_procesos.ps1`. Anota en cada corrida la ropa y cualquier evento externo (por ejemplo, alguien pasando detrás): la ropa puede afectar las rodillas (INFERIDO, por probar con shorts).
11. Las decisiones "por aprobar" en `docs/DECISIONES.md` son recomendaciones; no se aplican hasta que Ale las apruebe por escrito.

## 7. Criterios de aceptación del trabajo de ciclo (binarios; corrida de 10 min con `python main.py cuda lite`)
- C1. Ciclos/s ≥ 29.5 sostenidos y `cap_update` > 0 ms (Python espera a la cámara). Cómo contar una ventana baja que viene de la cámara lo fija Ale; mientras no lo fije, se reporta el resultado estricto (todas las ventanas) y las caídas aparte.
- C2. Espera de cámara: p95 ≤ línea base y sin crecimiento durante los 10 min.
- C3. Latencia (b) `latencia_llegada_ms`: media, p95 y máx no peores que la línea base vigente de `docs/MEDICIONES.md` (misma definición); se informa (a) y se compara con la prueba de 100 ms de HU0023-1. El máximo es una sola muestra y varía entre corridas iguales; se informa junto con el % de muestras > 100 ms.
- C4. `lat_tick_ms` ≤ 250 ms en el 100% de los sorteos.
- C5. Comportamiento musical igual al aprobado en `docs/DECISIONES.md` (cambios solo con decisión escrita).
- Si C1 no se cumple, reporta el porcentaje de ciclos > 33.3 ms y qué etapa los causa. No declares "hecho".
- Si el ciclo se ralentiza durante la corrida, reporta la tendencia (inicio frente a final) y el uso de CPU por proceso (`registrar_procesos.ps1`), no solo el promedio.

## 8. Cierre de sesión (Ale lo pega al terminar)
`Cierra la sesión: (1) actualiza docs/MEDICIONES.md con lo medido hoy, separando MEDIDO de INFERIDO y citando el CSV o log de origen; (2) si hubo una decisión, añádela a docs/DECISIONES.md con fecha y razón, y deja como "por aprobar" lo que decide Ale; (3) marca en el plan lo hecho y lo pendiente; (4) muéstrame solo los fragmentos cambiados. No toques CLAUDE.md ni docs/HISTORIAS.md.`

## 9. Fuera de alcance por ahora
- Reescribir en C++ u otro lenguaje (el tracker ocupa ≈ 58% del ciclo; no hay evidencia de que Python sea el cuello).
- Cambiar umbrales de la tesis. Eso se argumenta en el documento, no en el código.
- Medir la latencia total hasta el sonido (c): requiere captura de audio; es el paso 11 y se decide el método con Ale.