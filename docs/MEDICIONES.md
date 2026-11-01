# MEDICIONES — línea base, hipótesis y plan (corte: 01/11/2026; mediciones hasta el 31/10)

> Este archivo CAMBIA en cada sesión. Cada cifra cita su origen. MEDIDO = salió de un CSV o log. INFERIDO = deducción no comprobada.

## 0. Corrección importante
Las cifras de RNF01 que se usaron en ESTADO_ACTUAL y en borradores del short paper (media 58–62 ms, p95 78–83, máx 112–115) **no salen de los CSV del navegador del 28/10**. La media coincide con el CSV del 19/10 (media 59.2, p95 64.3, máx 104.9; cifras citadas en la auditoría de Code, CSV no revisado por Ale en esta sesión), cuando el ciclo duraba 58–63 ms. No se encontró el origen de p95 78–83 ni de máx 112–115. **No usar esas cifras.** Hipótesis H2 (58–62 = latencia + espera de cámara): REFUTADA.

**Actualización 01/11 (H2 REABIERTA).** La suma por muestra `latencia_ms + lag_cam_ms`, con vaciado de cola y 1 hilo de manos, da media 59.5–60.1, p95 80.3–80.4 y máx 113–123 ms (MEDIDO, corridas 171755 y 172123 del 31/10, sección 4b). Eso reproduce las tres cifras de ESTADO_ACTUAL (58–62 / 78–83 / 112–115) mejor que el CSV del 19/10, cuyo p95 era 64.3. INFERIDO: esas cifras eran la latencia desde la llegada del frame al PC (definición (b) de P-002), no `latencia_ms`. Falta confirmar con Ale cómo se calcularon. Hasta entonces se siguen sin usar.

## 1. Latencia del navegador por sesión (`Date.now() − t_cap_ms`, tipo `continuo`)
Fuente: CSV `latencias_*.csv` (hora UTC en el nombre; Perú = UTC−5). Cálculo hecho el 31/10 sobre los CSV adjuntos.
| Sesión (UTC) | n | Media | p95 | Máx | % > 100 ms | Transporte media | `lat_tick` media |
|---|---|---|---|---|---|---|---|
| 2026-10-26 20:20 | 3486 | 44.9 | 50.5 | 76.6 | 0.00 | 0.2 | 62.3 |
| 2026-10-28 19:59 | 13167 | 45.4 | 51.9 | 106.9 | 0.01 | 0.3 | 61.2 |
| 2026-10-28 20:09 | 18796 | 44.9 | 51.2 | 106.9 | 0.01 | 0.3 | 60.8 |
| 2026-10-28 20:27 | 26587 | 42.6 | 50.4 | 106.9 | 0.00 | 0.3 | 57.9 |
| 2026-10-28 20:51 | 4601 | 48.3 | 55.9 | 96.9 | 0.00 | 0.3 | 66.7 |
| 2026-10-28 21:13 | 6327 | 37.0 | 43.0 | 75.0 | 0.00 | 0.6 | 48.2 |
| 2026-10-28 21:28 | 12169 | 40.2 | 49.5 | 104.8 | 0.01 | 0.5 | 52.9 |
| 2026-10-28 22:03 | 4171 | 37.2 | 40.6 | 81.9 | 0.00 | 0.6 | 48.8 |
| 2026-10-28 22:17 (≈ sesión 28c, sin vaciado de cola) | 3652 | 35.8 | 39.1 | 93.3 | 0.00 | 0.6 | 48.0 |
| 2026-10-28 22:31 (≈ sesión 28d, vaciado, 1 hilo de manos) | 3977 | 35.6 | 39.0 | 101.1 | 0.03 | 0.6 | 47.6 |
| 2026-10-28 22:59 (≈ sesión 28e, vaciado, hilo por mano) | 3058 | 38.4 | 42.5 | 85.7 | 0.00 | 1.0 | 51.2 |
- La asociación de las tres últimas filas con 28c/28d/28e es INFERIDA (por hora y por la cifra de 35.8 ms que cita la auditoría para 28c).
- `lat_tick_ms` (auditoría de Code, 5 sesiones del 28/10): p95 67–71, máx 83–117, 0% > 250 ms. El 19/10 hubo 4.8% > 250 ms y un máx de 5691 ms, ya corregido con el reanclado del reloj.
- `base_latency` reportada por el navegador: 10 ms. `output_latency` reportada: 0.0 en todas las filas (no confiable).

## 2. Espera de cámara (`lag_cam_ms` / `[CAMARA]`)
| Configuración | Media | p95 | Máx | Fotogramas descartados/ciclo | Fuente |
|---|---|---|---|---|---|
| Sin vaciado de cola (28c) | 220.8–223.0 | 237.2–239.0 | 239.7–240.9 | — | log `[CAMARA]` de 17:22 |
| Con vaciado (28d/28e) | 21.1–25.6 | 38.2–45.4 | 47.1–50.0 | 0.23–0.28 | logs `[CAMARA]` de 18:36; auditoría (22.6–23.3 media) |
- Auditoría: cuando se descarta 1 frame, el lag del frame usado es 7–11 ms; cuando no se descarta ninguno, 25–27 ms (MEDIDO por Code en los CSV de sesión).
- Antes del vaciado, la latencia real captura→sonido era ≈ 36 + 220 ms y `latencia_ms` no la veía (INFERIDO por definición de `t_cap_ms`, confirmado por Code: se estampa después de vaciar la cola).

## 3. Ciclo por etapa (`[PERF]`)
| Etapa (ms/ciclo) | 28c (1 hilo, sin vaciado) | 28e (hilo por mano, con vaciado) |
|---|---|---|
| ciclo | 38–39 (25.8–26.3 ciclos/s) | 41–42 (23.6–24.1 ciclos/s) |
| cap_update | 0 | 0–1 |
| cap_imgs | 6–7 | 7 |
| tracker | 23 | 23–24 |
| manos | 1 | 1 |
| mapeo | 4 | 4 |
| salida | 1 | 2 |
| dibujo | 2 | 3 |
| hilo_manos (por trabajo) | 23–27 | 30–33 (≈ 47 trabajos/s en total, ≈ 23–24 por hilo) |
- Fuente: logs `[PERF]` de 17:22 (28c) y 18:36 (28e); ventanas de 60 ciclos, no estadísticas de toda la sesión.
- Periodo del ciclo (CSV de sesión, auditoría): 28d 38.4 ms media (p95 45) → 28e 42.0 ms (p95 50). 28e: 0.2% de ciclos ≤ 33.3 ms y 50% > 40 ms.
- `cap_update = 0`: Python nunca espera a la cámara; el bucle va siempre más lento que ella (MEDIDO).
- Edad de la mano (28e, CSV): media 46, mediana 40.5, p95 75 ms; 2 manos en 67% de ciclos; 0% de ciclos sin dato vigente. `par_dt_ms` = 0 siempre.
- GPU: reloj ≈ 1700–1750 de ≈ 2100 MHz durante el tracker (logs `nvidia-smi`, ESTADO_ACTUAL).

## 4. Micro-benchmarks aislados (auditoría de Code, esqueleto sintético, sin Kinect)
- `imdecode` de un JPEG 720p sintético (221 KB): 4.1 ms. Copia BGRA: 0.9 ms. `cvtColor` BGRA→RGB 0.77 ms, BGRA→BGR 0.75 ms. Lectura de profundidad: 0.03 ms.
- `mapeo.actualizar` 0.37–0.41 ms; `registro.actualizar` 0.20–0.22; `angulos_candidatos` 0.09; `flush()` 0.02; `writerow` 0.02; `json.dumps` 0.01; `print` a archivo 0.01.
- Suma mapeo+salida aislada ≈ 0.7–0.8 ms **frente a 5–6 ms en el ciclo real**. Diferencia SIN EXPLICAR `[POR COMPLETAR]` (candidatos: competencia por el GIL con los hilos de manos, `print` a consola de Windows).
- El corte barato real es la decodificación MJPG (el SDK entrega MJPG por defecto), no la profundidad ni la copia. INFERIDO: el `imdecode` es casi todo el `cap_imgs` de 6–7 ms. **Confirmado el 31/10 (MEDIDO):** `to_numpy` = 6.05–6.09 ms/llamada = 96 % de `cap_imgs` (sección 4b).
- `mapeo` real 31/10: 3.5–3.8 ms frente a 0.7 aislado; el `print` a consola mide 0.27 ms y está en `salida`, no en `mapeo`. Sigue SIN EXPLICAR. Hipótesis concreta (INFERIDA): el hilo principal espera el GIL mientras el hilo de manos ejecuta Python; el intervalo de cambio de hilo de Python es 5 ms. Prueba propuesta: una corrida con `sys.setswitchinterval(0.001)` y otra sin hilo de manos.

## 4b. Línea base y paso 5 (BGRA32), corridas del 31/10 (MEDIDO)
Fuentes, todas en `sesiones/`: `sesion_20261031_<hora>_<VERSION_MAIN>_cuda-lite.csv` y sus `_perf.txt` y `_latencias.csv`; GPU en `gpu_20261031.csv` (línea base) y `gpu_bgra32.csv`; CPU en `cpu_bgra32.csv` (`typeperf`, % de rendimiento del procesador). Etapas: media de los reportes `[PERF]` de 60 ciclos sin el 1º (arranque). Periodo: `diff(t_cap_ms)` del CSV de sesión.
- Línea base: `VERSION_MAIN = perf30hz-a-un-hilo-manos-2026-10-31` (commit `3151709`; MJPG, 1 hilo de manos, ventana 1 de cada 3 ciclos). Corridas 171408, 171755, 172123.
- BGRA32: `VERSION_MAIN = perf30hz-b-bgra32-2026-10-31` (commit `f453ac0`; solo cambia `COLOR_BGRA32=True`). Calentamiento 175547 (descartado); corridas 175644, 175843, 180053, de 107–144 s con cuerpo (más cortas que los 3 min del protocolo).

| Etapa (ms/ciclo) | MJPG 171408 | MJPG 171755 | MJPG 172123 | BGRA32 175644 | BGRA32 175843 | BGRA32 180053 |
|---|---|---|---|---|---|---|
| Ciclos/s | 21.7 | 25.6 | 25.4 | 29.4 | 28.7 | 28.5 |
| Ciclo | 46.3 | 39.0 | 39.4 | 33.9 | 34.9 | 35.1 |
| `cap_update` | 0.2 | 0.1 | 0.1 | 0.1 | 0.1 | 0.2 |
| `cap_imgs` | 9.4 | 6.4 | 6.3 | 2.0 | 2.0 | 2.0 |
| ↳ `to_numpy` (ms/llamada) | 8.65 | 6.09 | 6.05 | 1.72 | 1.78 | 1.79 |
| `tracker` | 26.1 | 23.2 | 23.8 | 23.2 | 24.0 | 24.0 |
| `manos` | 1.7 | 1.1 | 1.1 | 1.0 | 1.0 | 1.1 |
| `mapeo` | 4.5 | 3.7 | 3.8 | 3.7 | 3.5 | 3.6 |
| `salida` | 1.9 | 1.4 | 1.6 | 1.1 | 1.0 | 1.0 |
| ↳ `print` (ms/llamada) | 0.29 | 0.27 | 0.28 | 0.29 | 0.26 | 0.26 |
| `dibujo` | 2.5 | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 |
| ↳ `imshow` + `waitKey` (ms/ciclo) | 1.24 | 1.09 | 1.14 | 1.08 | 1.08 | 1.10 |
| Trabajo del hilo de manos | 37.9 | 28.8 | 27.6 | 31.3 | 28.0 | 28.2 |

| Métrica (ms salvo indicación) | MJPG 171408 | MJPG 171755 | MJPG 172123 | BGRA32 175644 | BGRA32 175843 | BGRA32 180053 |
|---|---|---|---|---|---|---|
| Periodo media / p95 | 46.6 / 56.4 | 39.2 / 45.7 | 39.7 / 46.2 | 34.1 / 40.7 | 35.0 / 41.7 | 35.1 / 42.1 |
| % ciclos ≤ 33.3 ms | 0.0 | 1.0 | 0.6 | 52.3 | 45.4 | 44.3 |
| `lag_cam_ms` media / p95 / máx | 24.0 / 45.1 / 68.7 | 23.3 / 43.3 / 50.3 | 23.5 / 43.6 / 51.4 | 44.4 / 58.4 / 68.7 | 47.2 / 62.4 / 71.1 | 47.9 / 62.7 / 72.0 |
| Frames descartados / ciclo | 0.40 | 0.17 | 0.19 | 0.02 | 0.05 | 0.06 |
| `latencia_ms` media / p95 / máx | 43.1 / 49.0 / 108.5 | 36.3 / 40.1 / 100.5 | 36.6 / 40.4 / 98.3 | 31.3 / 35.3 / 90.6 | 32.3 / 35.7 / 79.9 | 32.4 / 35.9 / 85.1 |
| `latencia_ms + lag_cam_ms` por muestra: media / p95 / máx | — | 59.5 / 80.3 / 113.2 | 60.1 / 80.4 / 123.1 | 75.6 / 90.4 / 154.2 | 79.5 / 96.0 / 115.4 | 80.3 / 97.1 / 144.8 |
| % muestras de esa suma > 100 ms | — | 0.05 | 0.04 | 0.70 | 1.81 | 2.36 |
| `lat_tick_ms` media / p95 / máx (% > 250) | 55.5 / 78.4 / 101.2 (0) | 48.8 / 66.9 / 82.3 (0) | 50.4 / 69.6 / 128.9 (0) | 45.7 / 62.3 / 68.2 (0) | 46.1 / 64.2 / 72.3 (0) | 47.1 / 64.3 / 84.0 (0) |
| Edad manos p95 | 141.9 | 115.7 | 198.8 | 161.5 | 183.3 | 173.0 |
| % ciclos con 2 manos | 83.8 | 83.8 | 76.0 | 76.7 | 77.4 | 71.7 |
| GPU reloj SM mediana (MHz) / potencia mediana (W) / temp. (°C) | 1650 / 26.5 / 63 | 1717 / 28.9 / 64 | 1717 / 28.9 / 66 | 1740 / 31.0 / 66 | 1729 / 31.0 / 68 | 1740 / 31.2 / 69 |
| CPU % rendimiento mediana | — | — | — | 217 | 217 | 217 |

- **Aviso sobre la línea base MJPG:** una pestaña de prueba de `index.html` que Code dejó abierta en su navegador integrado se conectó como segundo cliente a las 3 corridas, con audio. El `_latencias.csv` tiene cada mensaje 2 veces (las copias difieren 0.2–0.4 ms de media); las cifras de `latencia_ms` usan ambas copias y la suma por muestra usa la menor. Efecto en el ciclo no cuantificado; INFERIDO ≤ ≈ 1 ms (171755/172123 dan 39.2 ms frente a 38.4 de 28d sin ese cliente). Las corridas BGRA32 tienen 1 solo cliente (filas `continuo` = filas de sesión).
- La suma por muestra se calcula emparejando cada fila `continuo` (`t_epoch_ms − latencia_ms`) con la fila del CSV de sesión de igual `t_cap_ms` (tolerancia 1 ms).
- **Dibujo:** agrupando los periodos por fase módulo 3 (`DIBUJAR_CADA = 3`), una de cada 3 filas es más larga. MJPG: 42.6–43.3 frente a 36.7–39.0 ms. BGRA32: 38.0–39.2 ms (> 33.3 ms en el 98–99 %) frente a 31.9–33.1 ms (> 33.3 ms en el 21–35 %). Los ciclos que dibujan causan la mayoría de los ciclos > 33.3 ms con BGRA32.
- **Corrida lenta 171408:** todas las etapas más lentas, incluida `to_numpy`, que solo usa CPU (+42 %). El reloj de la GPU se recuperó desde el 2º tercio (1713 MHz) y el ciclo siguió en ≈ 45 ms. Dentro de las corridas normales, corr(tracker, reloj SM) = 0.11. INFERIDO: estado de rendimiento del equipo, no la GPU. La tanda BGRA32 con calentamiento y `typeperf` no mostró corrida lenta (CPU 217 % estable).
- **Razones de la GPU** (`clocks_event_reasons.active`): `0x4` = SW power cap (36–40 % de las muestras en las corridas rápidas, menos en la lenta: no es lo que limita el ciclo); `0x1` = GPU inactiva; `0x400` sin descripción en la ayuda de `nvidia-smi` `[POR COMPLETAR]`; `0x448` aparece 3 veces en la tanda BGRA32 (INFERIDO según nvml.h: `0x400` + HW thermal slowdown `0x40` + HW slowdown `0x8`, con 68–69 °C).
- **Efecto de BGRA32 (INFERIDO a partir de lo MEDIDO):** el ciclo de Python baja ≈ 4.5 ms (casi todo en `to_numpy`, de 6.07 a 1.76 ms), pero el SDK entrega cada frame ≈ 22 ms más tarde (`lag_cam_ms` 23.4 → 46.5 ms de media). El tiempo de decodificación no desaparece: pasa de `latencia_ms` a `lag_cam_ms` y además crece. Resultado: `latencia_ms` mejora ≈ 4.5 ms, pero la latencia desde la llegada del frame al PC empeora ≈ 17–20 ms. Causa exacta del aumento dentro del SDK `[POR COMPLETAR]`.
- Copia BGRA real dentro de `to_numpy`: 1.72–1.79 ms por llamada (el micro-benchmark sintético daba 0.9 ms).

## 5. Otras cifras vigentes (de ESTADO_ACTUAL, sesiones 26–28/10)
- Jitter con suavizado: hombros −22% a −32%; rodilla −52% a −53% (dos sesiones).
- Articulaciones de manos del Kinect sin valor (NONE) ≈ 53% de los frames; las otras 26 ≈ 100%.
- MediaPipe: ≥ 1 mano en 86–96% de los ciclos; ≈ 13 actualizaciones/s por mano con 1 hilo.
- Aciertos del recuadro por origen (log `[ROI]`, ventanas de 60 ciclos): muñeca 92–100% casi siempre; mano 51–100% con pocos intentos.

## 6. Estado de las hipótesis
- H1 (la espera de cámara baja si el ciclo baja de 33.3 ms): COMPATIBLE, NO PROBADA. Bajaría hacia la latencia interna del SDK, no a 0. Con BGRA32 el ciclo quedó en 34–35 ms y `cap_update` siguió ≈ 0 (MEDIDO, 4b): aún no se puede probar. Con BGRA32 la latencia interna del SDK sube ≈ 22 ms, así que el piso de H1 depende del formato de color.
- H2: REFUTADA el 31/10; **REABIERTA el 01/11** (sección 0 y 4b): la suma por muestra `latencia_ms + lag_cam_ms` reproduce media, p95 y máx de ESTADO_ACTUAL.
- H3 (`lat_tick` ≈ etapas previas + espera hasta el siguiente ciclo): CONSISTENTE con 47.6–51.2 ms (28/10), 48.8–50.4 (MJPG 31/10) y 45.7–47.1 (BGRA32 31/10): baja al bajar el ciclo.
- H4 (cortes baratos): el corte con evidencia es la decodificación MJPG; `flush`/`print` valen centésimas de ms aislados. 31/10: BGRA32 quita 4.3 ms de `to_numpy` pero empeora la llegada del frame (ver 4b); `print` = 0.27 ms (no vale la pena); ventana = 2.0 ms/ciclo de media y ≈ 6 ms en el ciclo que dibuja.
- H5 (pipeline en 2 etapas): POSIBLE (las DLL se cargan con `ctypes.CDLL` y sueltan el GIL en la llamada nativa), pero 1→2 hilos de manos ya costó ≈ 3.6 ms de ciclo: NO es gratis; medir antes de asumir solapamiento.

## 7. Presupuesto (INFERIDO)
- Tracker 23–24 ms es el piso. Para 33.3 ms quedan ≤ 9.8 ms para todo lo demás; hoy son 15–17 ms.
- Con `BGRA32` o decodificación en otro hilo (ahorro estimado 4–5 ms) y sin ventana de dibujo: ciclo ≈ 31.5 ms (margen ≈ 2 ms); si `mapeo` baja a lo medido aislado: ≈ 28.5 ms (margen ≈ 5 ms).
- Aviso: con `DIBUJAR_CADA=3`, cada tercer ciclo paga ≈ 7–9 ms y dispara el p95.
- **Actualización 31/10 con lo MEDIDO (4b).** Con BGRA32, fuera del tracker quedan ≈ 10.9 ms (ciclo medio 34.6 − tracker 23.7). Sin ventana (−2.0 ms MEDIDO): ≈ 32.6 ms, margen ≈ 0.7 ms (INFERIDO); los ciclos que no dibujan ya miden 31.9–33.1 ms. Aclarar `mapeo` (3.6 ms frente a 0.7 aislado) daría hasta ≈ 3 ms más.
- Alternativa a BGRA32 (INFERIDA, sin medir): pedir MJPG y decodificar en el hilo de manos (el tracker no usa el color). Conservaría `lag_cam_ms` ≈ 23 ms y quitaría ≈ 6 ms del ciclo; obliga a decidir de dónde sale la imagen que dibuja la ventana.

## 8. Parámetros que dependen de la tasa de ciclos (cambian si se pasa de ≈ 24 a 30 Hz)
- `UMBRAL_ESTABILIDAD_ZONA = 6` ciclos: ≈ 250 ms hoy → ≈ 200 ms a 30 Hz. (`zona.py`: 6 frames, solo si `REGISTRO_POR_ANGULO=False`.)
- `EMA_ANGULO_BRAZO = 0.5` y `EMA_VEL_RODILLA = 0.4`: retardo ≈ (1−α)/α · ciclo (41 → 33 ms y 61 → 50 ms).
- `len(hist) >= 5` y `len(recientes) >= 4`; el tick se evalúa una vez por ciclo.
- 31/10 (MEDIDO): la tasa pasó de 25.4–25.6 Hz (MJPG) a 28.5–29.4 Hz (BGRA32). INFERIDO: la histéresis de 6 ciclos pasa de ≈ 235 a ≈ 208 ms. Ya es un cambio de comportamiento musical pendiente de P-001.
- Sin efecto musical: `DIBUJAR_CADA`, `REPORTE_CADA`, `MAX_DESCARTE_POR_CICLO`.
- En segundos (no cambian): `VENTANA_INTENSIDAD_S`, `VENTANA_FLUIDEZ_S`, `NORM_VENTANA_S`, `NORM_CALENTAMIENTO_S`, `HOLD_ANGULO_S`, `HOLD_APERTURA_S`, `VENTANA_FUSION_MS`, `intervalo_s`, `dt` real de `VelocidadAngular`.

## 9. Plan vigente
Tarea 1 (auditoría de solo lectura): **HECHA el 31/10/2026** (resultados arriba).
Tarea 2 (reducción del ciclo). Un paso por commit; cada paso se mide con el protocolo de la sección 10.
| # | Paso | Estado |
|---|---|---|
| 1 | Commit del estado actual en la rama `wip-28e` (hay cambios sin commit en `main.py`, `servidor.py`, `index.html`) | HECHO 31/10 (`368c20a`) |
| 2 | Rama `perf/ciclo-30hz` y `HILO_POR_MANO=False` (ver D-003; Ale confirma) | HECHO 31/10 (`9b2d30a`) |
| 3 | Cronómetros por línea en `[PERF]` para `to_numpy()`, `print` e `imshow`, sin cambiar comportamiento | HECHO 31/10 (`1764380`, `[PERF-LINEA]`) |
| 3b | Guardar `[PERF]` en `_perf.txt` y las latencias del navegador en `_latencias.csv` automáticamente (D-006) | HECHO 31/10 (`e2fef0d`, `3151709`) |
| 4 | Línea base: 3 corridas de 3 min con la rutina fija (sección 10) | HECHO 31/10 (171408, 171755, 172123; sección 4b). Con un cliente de prueba de más; ver aviso en 4b |
| 5 | `BGRA32` (o decodificar en el hilo de manos) y sin ventana en sesiones de evaluación; volver a medir | PARCIAL. BGRA32 HECHO y medido (`f453ac0`): ciclo 34–35 ms, no cumple C1 ni C2 (sección 4b); mantenerlo o no es P-005. Sin ventana: PENDIENTE de P-003. Decodificar en el hilo de manos: PENDIENTE (alternativa de P-005) |
| 5b | Explicar `mapeo` (3.6 ms real frente a 0.7 aislado): corrida con `sys.setswitchinterval(0.001)` y corrida sin hilo de manos | PENDIENTE |
| 6 | Decidir histéresis y EMA en milisegundos (ver P-001; antes decía D-005 por error) | PENDIENTE (decide Ale). Ya urgente: con BGRA32 la tasa subió a ≈ 29 Hz |
| 7 | Enviar `lag_cam_ms` en el mensaje para calcular la latencia por muestra desde la llegada al PC | PENDIENTE. Mientras tanto se calcula offline uniendo CSV de sesión y `_latencias.csv` (sección 4b) |
| 8 | Pipeline de 2 etapas (H5) solo si 1–7 no cumplen C1 | CONDICIONAL |
| 9 | Corrida de 10 min y verificación de C1–C5 | PENDIENTE |
Fuera de este plan (US23): latencia total hasta el sonido (micrófono o loopback), `latencia_interna_SDK` `[POR COMPLETAR]`.

## 10. Protocolo de corrida (repetible)
1. Laptop enchufada, modo de máximo rendimiento, solo Chrome con **una sola pestaña** de `index.html`, misma distancia (de pie) y misma luz. Segunda terminal: `nvidia-smi --query-gpu=timestamp,clocks.sm,clocks.max.sm,temperature.gpu,power.draw,clocks_throttle_reasons.active --format=csv -l 1 -f sesiones\gpu_<config>.csv`. Tercera terminal: `typeperf "\Processor Information(_Total)\% Processor Performance" -si 1 -o sesiones\cpu_<config>.csv`. Detener ambos con Ctrl+C al terminar la tanda.
1b. Una corrida de calentamiento de ≈ 1 min que se descarta (31/10: la 1ª corrida de la tanda MJPG salió ≈ 7 ms más lenta en todas las etapas).
2. `python main.py cuda lite`; esperar 5 s; rutina fija de 3 min: 30 s quieto, 60 s brazos arriba y abajo, 60 s baile amplio, 30 s abrir y cerrar manos con las dos manos visibles.
3. `q` para cerrar. Desde `3151709` no hace falta descargar: quedan en `sesiones/` el CSV de sesión, `_perf.txt` y `_latencias.csv`. Comprobar que las filas `continuo` de `_latencias.csv` ≈ filas del CSV de sesión (si son el doble, había 2 clientes). Nombrar la configuración en `VERSION_MAIN`. No usar `Start-Transcript` (no graba la salida de Python).
4. 3 corridas por configuración; comparar promedios (una sola corrida engaña: 28d→28e varió 38.4→42.0 ms). No cambiar código entre corridas de la misma configuración. No mezclar con pruebas de sonido.

## 11. Pendientes y huecos
- ~~Perfil de un ciclo real con cronómetros por línea (paso 3–4).~~ HECHO 31/10 (sección 4b).
- `[POR COMPLETAR]` latencia interna del SDK entre `system_timestamp` y la disponibilidad del capture. Nuevo: con BGRA32 `lag_cam_ms` sube ≈ 22 ms; falta saber qué parte es decodificación y qué parte es espera dentro del SDK.
- `[POR COMPLETAR]` latencia real hasta el sonido (US23).
- `[POR COMPLETAR]` origen de las cifras RNF01 p95 78–83 y máx 112–115 (o descartarlas). Candidato encontrado el 01/11: `latencia_ms + lag_cam_ms` por muestra (sección 0). Ale confirma.
- `[POR COMPLETAR]` significado del bit `0x400` en las razones de reloj de la GPU.
- `[POR COMPLETAR]` causa de los 3.6 ms de `mapeo` (paso 5b).
- Pendiente de datos (no medido): confianza de rodillas y tobillos en el CSV. Ale observó el 31/10 más movimiento falso de piernas al subir los brazos; en las sesiones 164334/164633 la mediana de la velocidad de rodilla es 35–111 °/s con los hombros a 45–135° (11–16 °/s quieto con los brazos abajo), y eso sube el tempo.
- Garantía FIFO del SDK al vaciar la cola: INFERIDA; las cifras de `lag_cam_ms` la respaldan.
