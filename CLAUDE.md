# CLAUDE.md — Generación musical adaptativa por movimiento (Azure Kinect + MediaPipe + Tone.js)

> Este archivo es ESTABLE: contexto, reglas, arquitectura y criterios. Lo que cambia (mediciones, plan, hipótesis, decisiones) vive en `docs/`. Solo Ale lo edita.
> **Prompt de arranque de cada sesión:** `Lee CLAUDE.md, docs/HISTORIAS.md, docs/MEDICIONES.md y docs/DECISIONES.md. Dime en 5 líneas dónde estamos, qué decisiones siguen "por aprobar" y cuál es el siguiente paso pendiente del plan. No edites nada hasta que yo confirme.`

@docs/HISTORIAS.md
@docs/MEDICIONES.md
@docs/DECISIONES.md

## 1. Contexto
- Tesis UPC (código TP202620503). Autores: Freddy Cuadros (PM) y Jimena Quintana (SM). Asesor: Willy Ugarte.
- Alcance de este curso (TP1): US01–US28 y US38 (visual). **US29–US37 (evaluación con estudiantes: PSS-10, SAM, SUS, protocolo, análisis) son del otro curso** (decisión de Ale, 10/11/2026). Cierre del Sprint 3: 14/11/2026. El 12/11 fue el último día con el Kinect: no hay corridas nuevas y el código está congelado en `8d58820` (D-043).
- Pipeline: Azure Kinect DK (Body Tracking, 32 articulaciones, color 720p, 30 fps) → MediaPipe Hands sobre recortes (ROI) en un hilo aparte → bucle `asyncio` en Python → WebSocket `127.0.0.1:8765` (JSON) → Tone.js (audio) y dibujo visual en **Edge** (D-020) → parlante JBL.
- Ya no se usan Leap Motion ni TV/proyector (D-005): la pantalla es la de la laptop.
- Objetivo técnico: ciclo del pipeline ≤ 33.3 ms (30 Hz, igual que la cámara). Los desvíos frente a los criterios de las historias (HU0007-1, HU0008-1, HU0023-1) se deciden con Ale en `docs/DECISIONES.md`; no se "arreglan" cambiando el criterio.
- Equipo de desarrollo: HP Victus, Intel Core i5-13420H, 16 GB RAM, NVIDIA GeForce RTX 3050 6 GB Laptop. Las mediciones solo se comparan entre corridas hechas con el mismo plan de energía y en la misma sesión de trabajo (ver sección 6, regla 10).
- Visual (US38): el sistema final lleva el visual **encendido** (decisión de Ale, 10/11/2026) y **todas las validaciones de US07–US28 y US38 se hacen con el visual encendido** (D-047). Las corridas con `?visual=0` son referencia de comparación (costo del visual) y se siguen registrando; el costo se informa aparte (sección 7, C6).

## 2. Cómo ejecutar
- Entorno: venv `env_cv` (Python 3.12.10; pykinect_azure 0.0.4, mediapipe 0.10.21, websockets 17.2, cv2 4.11) — versiones medidas el 31/10/2026. El Python global (3.14) no es el del proyecto. En CMD se activa con `env_cv\Scripts\activate.bat`; en PowerShell con `.\env_cv\Scripts\Activate.ps1`.
- Comando: `python main.py cuda lite` (Windows, GPU NVIDIA). Abrir `index.html` en **una sola** pestaña de **Edge**.
- Opciones de línea de comandos (D-011, D-012, D-013, D-015, D-027): `--con-ventana` (enciende la ventana de OpenCV; por defecto está apagada, D-012), `--sin-decod-hilo` (desactiva la decodificación del color en el hilo de manos, que es el valor por defecto desde D-015; `--decod-hilo` se sigue aceptando), `--swi1ms` y `--sin-manos` (solo diagnóstico), `--seed=N` (semilla del muestreo; D-027), `--tempo-medium` (rodilla en MEDIUM para el tempo; **no adoptada**, P-012). Cuando una opción se sale del valor por defecto, `VERSION_MAIN` lleva un sufijo (`-conventana`, `-sindecodhilo`, `-swi1ms`, `-sinmanos`) y la cabecera de `_perf.txt` anota la configuración. `--con-ventana` y `--sin-ventana` juntas dan error.
- Opciones de la página (`index.html`): `?visual=0` apaga el dibujo (corridas base); `?demo=1` genera estados falsos para probar el visual sin Kinect. La configuración se anota en `_latencias.csv`.
- Cierre: **un solo Ctrl+C** (es lo normal, porque no hay ventana). Con `--con-ventana` también sirve `q`. Al cerrar, Python espera 1 s para recibir el último lote de latencias del navegador.
- Salidas (D-006), en `sesiones/`: CSV de sesión (el nombre lleva `VERSION_MAIN`; columnas de reproducibilidad `nota_id`, `lam_sorteo`, `semilla`, `version`, `commit`, D-027), `<sesion>_perf.txt` (reportes `[PERF]`, `[PERF-LINEA]`, `[CAMARA]`, `[FUSION]`, `[ROI]`, `[PIERNAS]`) y `<sesion>_latencias.csv` (el navegador lo envía por el WebSocket; el botón de descarga sigue existiendo).

## 3. Archivos del sistema
- `main.py`: bucle principal, mapeo de extremidades, registro por ángulo, `HiloManos`, métricas `[PERF]`/`[CAMARA]`/`[FUSION]`.
- `servidor.py`: WebSocket. `index.html`: Tone.js local, medición de latencia en el navegador y pantallas de inicio y fin. `visual.js`: dibujo de las ondas (Canvas 2D); no toca el audio.
- `zona.py` (solo si `REGISTRO_POR_ANGULO=False`; sigue contando frames), `muestreo.py` (nota y octava), `manos.py` (apertura).
- `fluidez.py` **no se importa** (código muerto): la fluidez λ está en `main.py` (`MapeoExtremidades`).
- `grafico.py`, `evidencia.py`, `pruebas.py`: análisis offline.
- `registrar_procesos.ps1`: registra cada ≈ 1 s el uso de CPU por proceso durante una corrida.
- `docs/HISTORIAS.md`: criterios de aceptación US07–US28 y US38 (no lo edita Code).

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
9. Navegador (fuera del ciclo): `onmessage` solo guarda el último estado y aplica el sonido; el dibujo corre en `requestAnimationFrame`, nunca dentro de `onmessage`.
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
- Manos (HU0008-1, D-048): criterio = **datos nuevos por mano/s** (bajadas de `edad_izq_ms` / `edad_der_ms`, D-040), media de la corrida, cada mano por separado, ≥ 5. Los **trabajos/s** del hilo se informan aparte, sin criterio.
- Visual: **tiempo por cuadro** = ms de trabajo de dibujo dentro de cada `requestAnimationFrame` (mide el costo; criterio: máximo de los p95 por lote ≤ 16.7 ms, D-063); **intervalo entre cuadros** = tiempo entre dos cuadros seguidos (mide la fluidez; se informa, sin objetivo); **latencia visual** = de `t_cap_ms` a que se dibuja el anillo de esa nota (análoga a (a); criterio: p95 de todas las muestras ≤ 100 ms, D-063).
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
9. Cada cambio de código o medición dice qué criterio de historia cumple o afecta (HU0007-1, HU0023-2, HU0038-1, …). Si un cambio contradice un criterio, detente y avisa.
10. Protocolo de corrida: plan de energía de máximo rendimiento y laptop enchufada (D-014); pantalla en "Nunca" apagarse (D-017); una sola pestaña de `index.html` en Edge (D-020), sin recargarla durante la tanda; sin otros clientes conectados (ni pestañas de prueba de Code, ni el navegador integrado que se abre solo al editar `index.html`); calentamiento descartado; configuraciones **intercaladas** (A B C A B C), no en bloques; una corrida base al final para detectar ralentización del equipo; cierre con un solo Ctrl+C o `q`. Las validaciones se hacen con el visual encendido (D-047); las corridas con `?visual=0` son referencia. Si el `_latencias.csv` tiene el doble de filas `continuo` que el CSV de sesión, la corrida se repite. Una corrida con evento Kernel-Power 506 queda fuera de protocolo (D-018). Reloj: antes de la tanda `w32tm /resync` y `net stop w32time`; al final `net start w32time` y `w32tm /resync` (D-060); la deriva de `transporte_ms` debe quedar dentro de ±1 ms (D-019). "No molestar" activado, `msmpeng` y `searchindexer` en reposo y la app de Claude minimizada (D-051). Edge maximizado y al frente toda la corrida; después de cada corrida se cuentan las filas `cuadro_trabajo` y `visual` del `_latencias.csv` (D-061). Una corrida se repite solo por invalidez de protocolo (506, reloj, visual sin dibujar, proceso ajeno medido); si cumple el protocolo y falla un criterio, se informa como fallo y no se repite (D-062). No se comparan corridas de días distintos o con plan de energía distinto sin decirlo. Detalle en `docs/MEDICIONES.md` sección 10. Antes de la tanda, **cierra VS Code** y los programas que no uses, y revisa el Administrador de tareas: el 04/11 `code` usó ≈ 1.6 núcleos y degradó la corrida (MEDIDO por proceso, causa INFERIDA con evidencia fuerte). Durante cada corrida, una terminal aparte ejecuta `registrar_procesos.ps1`. Anota en cada corrida la ropa y cualquier evento externo (por ejemplo, alguien pasando detrás): la ropa puede afectar las rodillas (INFERIDO, por probar con shorts).
11. Las decisiones "por aprobar" en `docs/DECISIONES.md` son recomendaciones; no se aplican hasta que Ale las apruebe por escrito.
12. **Visual (US38):** solo en el navegador; Canvas 2D, sin WebGL, sin desenfoques ni sombras costosas; como máximo 200 elementos vivos (anillos y estrellas juntos); el dibujo va en `requestAnimationFrame`, nunca en `onmessage`; sin destellos (no más de 3 cambios bruscos de luz por segundo), sin rojo, sin puntajes ni cronómetros; el color no es la única señal (también cambian borde, forma o texto). No se toca el ciclo de Python por el visual; si hace falta un campo nuevo en el mensaje (identificador de nota nueva, cuerpo detectado), se propone con su costo medido y se espera la aprobación de Ale. Que el visual reduzca el estrés es una **hipótesis** (INFERIDO), no un resultado; se evalúa en el otro curso.
13. **Refactor (KISS):** solo al final, después de todas las mediciones. Se etiqueta el commit medido (`medido-final`) y se trabaja en la rama `refactor/kiss`. Un módulo por commit, sin cambiar comportamiento, sin clases ni capas nuevas salvo que quiten duplicación; funciones cortas, constantes en un solo lugar, nombres coherentes. No se toca `bucle_kinect` salvo orden explícita de Ale. Se valida con una corrida con semilla (mismas notas) y una de 10 min con C1–C5. Las cifras del paper citan el commit medido, no el refactorizado.

## 7. Criterios de aceptación (binarios; corrida de 10 min con `python main.py cuda lite`, visual encendido por defecto, D-042; GPU de Edge anotada y verificada en `edge://gpu`; una pestaña)
- C1. D-077: media ≥ 29.5 ciclos/s y ninguna ventana (sin #0) < 20.0; cap_update > 0 ms. Se informan también D-069 (< 25.0), D-023 (< 29.0) y el estricto. D-069 y D-077 se fijaron a posteriori.
- C2. D-066: `lag_cam` p95 de la corrida y de cada minuto con ≥ 20 s de datos ≤ 27.1 ms; "último − primer minuto" se informa sin umbral.
- C6. D-063: tiempo por cuadro (máximo de los p95 por lote) ≤ 16.7 ms; latencia visual p95 (todas las muestras) ≤ 100 ms; destellos ≤ 3/s.
- C7. Manos (HU0008-1, D-048): ≥ 5 datos nuevos por mano/s (media, cada mano).
- HU0017-1 (D-064): ≤ 0.5 saltos por segundo de `apertura01` mayores a 0.3 (media de la corrida).
- US20 (D-068): pregunta 1 (sonido) ≥ 4 de 5; el visual y los saltos se informan aparte.
- GPU de Edge: Intel como propuesta de diseño, sin ventaja demostrada frente a NVIDIA (D-070).
- Las corridas con `?visual=0` son referencia de comparación; se siguen registrando.

## 8. Cierre de sesión (Ale lo pega al terminar)
`Cierra la sesión: (1) actualiza docs/MEDICIONES.md con lo medido hoy, separando MEDIDO de INFERIDO y citando el CSV o log de origen; (2) si hubo una decisión, añádela a docs/DECISIONES.md con fecha y razón, y deja como "por aprobar" lo que decide Ale; (3) marca en el plan lo hecho y lo pendiente; (4) muéstrame solo los fragmentos cambiados. No toques CLAUDE.md ni docs/HISTORIAS.md.`

## 9. Fuera de alcance por ahora
- Reescribir en C++ u otro lenguaje (el tracker ocupa ≈ 58% del ciclo; no hay evidencia de que Python sea el cuello).
- Cambiar umbrales de la tesis. Eso se argumenta en el documento, no en el código.
- Medir la latencia total hasta el sonido (c): requiere captura de audio; es el paso 11 y se decide el método con Ale.
- Visual: WebGL, cámara en espejo o video del estudiante, luces externas, puntajes o niveles de juego.
- Cuestionarios dentro de la aplicación (PSS-10, SAM, SUS): son del otro curso. La aplicación solo abre los enlaces de "antes" y "después" (`[POR COMPLETAR]` las URL).