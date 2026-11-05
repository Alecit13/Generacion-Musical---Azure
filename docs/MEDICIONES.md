# MEDICIONES — línea base, hipótesis y plan (corte: 05/11/2026; mediciones hasta el 04/11)

> Este archivo CAMBIA en cada sesión. Cada cifra cita su origen. MEDIDO = salió de un CSV o log. INFERIDO = deducción no comprobada.
> Toda cifra de latencia va con su definición (sección 0). Si dos cifras no coinciden, primero se revisa que usen la misma definición.

## 0. Definiciones de latencia y origen de las cifras de ESTADO_ACTUAL
### 0.1 Qué instante se mide (la misma frase "latencia" puede significar cuatro cosas)
| Letra | Hasta/desde | Cómo se obtiene | ¿Se puede medir hoy? |
|---|---|---|---|
| (a) | Python recibe el frame → el navegador recibe el mensaje | `latencia_ms = Date.now() − t_cap_ms` (`t_cap_ms` se estampa **después** de vaciar la cola de la cámara) | Sí (CSV `_latencias.csv`, tipo `continuo`) |
| (b) | El frame llega al PC → el navegador recibe el mensaje | `latencia_ms + lag_cam_ms`, por muestra (`lag_cam_ms = t_upd − system_timestamp` del SDK) | Sí. **En línea desde el paso 7** (`eb68590`): columna `latencia_llegada_ms` de `_latencias.csv` (vacía si no hay `lag_cam_ms`). Coincide con el cálculo offline de 4b con diferencia ≤ 0.05 ms (MEDIDO, corridas 133512, 133838 y 134201 del 02/11) |
| (c) | El sensor captura → el sonido sale del parlante (extremo a extremo) | Exposición del sensor + USB + SDK + (b) + audio del navegador + parlante | **No.** Falta método (micrófono o loopback) y la latencia interna del SDK `[POR COMPLETAR]` |
| RNF01b | Tick programado → sorteo de la nota | `lat_tick_ms`; se mide por completo dentro de Python | Sí (no tiene el problema de la definición) |
- "Llega al PC" y "llega a Python" **no** son el mismo instante: entre los dos el frame espera en la cola del SDK. `lag_cam_ms` mide esa espera (con vaciado de cola ≈ 23 ms; con BGRA32 ≈ 46 ms; sin vaciado ≈ 220 ms).
- Antes del vaciado de cola, (a) **no veía** esos 220 ms: `t_cap_ms` se estampa después de sacar el frame de la cola.
- **Decidido (D-009, Ale, 02/11):** RNF01/US23 = (b); (a) se informa como secundaria; (c) se mide aparte y se informa aunque no cumpla.

### 0.2 Origen de las cifras de ESTADO_ACTUAL (RNF01 media 58–62, p95 78–83, máx 112–115)
- No salen de `latencia_ms` (a) de los CSV del navegador del 28/10 (esos dan media 35.6–38.4, p95 39–42.5; sección 1).
- La media coincide con el CSV del 19/10 (media 59.2, p95 64.3, máx 104.9; cifras citadas en la auditoría de Code, CSV no revisado por Ale), cuando el ciclo duraba 58–63 ms; pero ese p95 (64.3) no es 78–83.
- **Actualización 01/11 (H2 REABIERTA).** La suma por muestra `latencia_ms + lag_cam_ms` (definición (b)), con vaciado de cola y 1 hilo de manos, da media 59.5–60.1, p95 80.3–80.4 y máx 113–123 ms (MEDIDO, corridas 171755 y 172123 del 31/10, sección 4b). Reproduce las tres cifras mejor que el CSV del 19/10.
- INFERIDO: esas cifras eran (b). **Ale no recuerda cómo se calcularon** (02/11), así que el origen original sigue sin confirmarse `[POR COMPLETAR]`.
- Regla hasta cerrar el origen: las cifras 58–62 / 78–83 / 112–115 se pueden citar **solo** como "(b), corridas 171755 y 172123 del 31/10, con un segundo cliente conectado" y no como resultado limpio. La línea base se repitió el 02/11 (paso 10, sección 4c).

## 1. HISTÓRICA (definición (a)) — Latencia del navegador por sesión (`Date.now() − t_cap_ms`, tipo `continuo`)
Fuente: CSV `latencias_*.csv` (hora UTC en el nombre; Perú = UTC−5). Cálculo hecho el 31/10 sobre los CSV adjuntos. Sirve como historia; la línea base vigente es la de la sección 4c (02/11).
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
- Antes del vaciado, la latencia real captura→sonido era ≈ 36 + 220 ms y (a) no la veía (INFERIDO por definición de `t_cap_ms`, confirmado por Code).

## 3. HISTÓRICA — Ciclo por etapa (`[PERF]`), sesiones del 28/10
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
- Nota 02/11: con 1 hilo el ciclo varió 38.0–46.5 ms entre corridas del 31/10, más que la diferencia 28d→28e; esta comparación 1 vs 2 hilos es débil (ver D-003).

## 4. Micro-benchmarks aislados (auditoría de Code, esqueleto sintético, sin Kinect)
- `imdecode` de un JPEG 720p sintético (221 KB): 4.1 ms. Copia BGRA: 0.9 ms. `cvtColor` BGRA→RGB 0.77 ms, BGRA→BGR 0.75 ms. Lectura de profundidad: 0.03 ms.
- `mapeo.actualizar` 0.37–0.41 ms; `registro.actualizar` 0.20–0.22; `angulos_candidatos` 0.09; `flush()` 0.02; `writerow` 0.02; `json.dumps` 0.01; `print` a archivo 0.01.
- Suma mapeo+salida aislada ≈ 0.7–0.8 ms **frente a 5–6 ms en el ciclo real**. Diferencia SIN EXPLICAR `[POR COMPLETAR]` (candidatos: competencia por el GIL con los hilos de manos, `print` a consola de Windows).
- El corte barato real es la decodificación MJPG (el SDK entrega MJPG por defecto), no la profundidad ni la copia. **Confirmado el 31/10 (MEDIDO):** `to_numpy` = 6.05–6.09 ms/llamada = 96 % de `cap_imgs` (sección 4b).
- `mapeo` real 31/10: 3.5–3.8 ms frente a 0.7 aislado; el `print` a consola mide 0.27 ms y está en `salida`, no en `mapeo`. Hipótesis (INFERIDA el 31/10): el hilo principal espera el GIL mientras el hilo de manos ejecuta Python. **Probada el 02/11 (paso 5b, sección 4d):** `setswitchinterval(0.001)` no cambia `mapeo` (3.4–3.5 ms frente a 3.43 de Base en la misma época) y sin hilo de manos baja ≈ 0.6 ms (2.8–2.9 ms). Lo que más mueve `mapeo` es el estado del equipo: 1.9 a 3.9 ms en Base a lo largo de la tanda (MEDIDO). INFERIDO: el GIL explica poco; el resto acompaña a la ralentización general del equipo.

## 4b. Línea base y paso 5 (BGRA32), corridas del 31/10 (MEDIDO)
Fuentes, todas en `sesiones/`: `sesion_20261031_<hora>_<VERSION_MAIN>_cuda-lite.csv` y sus `_perf.txt` y `_latencias.csv`; GPU en `gpu_20261031.csv` (línea base) y `gpu_bgra32.csv`; CPU en `cpu_bgra32.csv` (`typeperf`, % de rendimiento del procesador). Etapas: media de los reportes `[PERF]` de 60 ciclos sin el 1º (arranque). Periodo: `diff(t_cap_ms)` del CSV de sesión.
- Línea base: `VERSION_MAIN = perf30hz-a-un-hilo-manos-2026-10-31` (commit `3151709`; MJPG, 1 hilo de manos, ventana 1 de cada 3 ciclos). Corridas 171408, 171755, 172123.
- BGRA32: `VERSION_MAIN = perf30hz-b-bgra32-2026-10-31` (commit `f453ac0`; solo cambia `COLOR_BGRA32=True`). Calentamiento 175547 (descartado); corridas 175644, 175843, 180053, de 107–144 s con cuerpo (más cortas que los 3 min del protocolo).
- Equipo: HP Victus, Intel Core i5-13420H, 16 GB de RAM (3200 MT/s), NVIDIA GeForce RTX 3050 6 GB Laptop (driver 616.92); plan de energía "Equilibrado" el 31/10 (MEDIDO por Ale con comandos de PowerShell). El protocolo (sección 10) pide máximo rendimiento.

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
| (a) `latencia_ms` media / p95 / máx | 43.1 / 49.0 / 108.5 | 36.3 / 40.1 / 100.5 | 36.6 / 40.4 / 98.3 | 31.3 / 35.3 / 90.6 | 32.3 / 35.7 / 79.9 | 32.4 / 35.9 / 85.1 |
| (b) `latencia_ms + lag_cam_ms` por muestra: media / p95 / máx | — | 59.5 / 80.3 / 113.2 | 60.1 / 80.4 / 123.1 | 75.6 / 90.4 / 154.2 | 79.5 / 96.0 / 115.4 | 80.3 / 97.1 / 144.8 |
| % muestras de (b) > 100 ms | — | 0.05 | 0.04 | 0.70 | 1.81 | 2.36 |
| `lat_tick_ms` media / p95 / máx (% > 250) | 55.5 / 78.4 / 101.2 (0) | 48.8 / 66.9 / 82.3 (0) | 50.4 / 69.6 / 128.9 (0) | 45.7 / 62.3 / 68.2 (0) | 46.1 / 64.2 / 72.3 (0) | 47.1 / 64.3 / 84.0 (0) |
| Edad manos p95 | 141.9 | 115.7 | 198.8 | 161.5 | 183.3 | 173.0 |
| % ciclos con 2 manos | 83.8 | 83.8 | 76.0 | 76.7 | 77.4 | 71.7 |
| GPU reloj SM mediana (MHz) / potencia mediana (W) / temp. (°C) | 1650 / 26.5 / 63 | 1717 / 28.9 / 64 | 1717 / 28.9 / 66 | 1740 / 31.0 / 66 | 1729 / 31.0 / 68 | 1740 / 31.2 / 69 |
| CPU % rendimiento mediana | — | — | — | 217 | 217 | 217 |

- **Aviso sobre la línea base MJPG:** una pestaña de prueba de `index.html` que Code dejó abierta en su navegador integrado se conectó como segundo cliente a las 3 corridas, con audio. El `_latencias.csv` tiene cada mensaje 2 veces (las copias difieren 0.2–0.4 ms de media); las cifras (a) usan ambas copias y (b) usa la menor. Efecto en el ciclo no cuantificado; INFERIDO ≤ ≈ 1 ms (171755/172123 dan 39.2 ms frente a 38.4 de 28d sin ese cliente). Las corridas BGRA32 tienen 1 solo cliente (filas `continuo` = filas de sesión). **La primera corrida MJPG (171408) fue un valor atípico lento (46.3 ms) y no tuvo calentamiento previo.** Por esto la línea base MJPG se repite (paso 10).
- (b) se calcula emparejando cada fila `continuo` (`t_epoch_ms − latencia_ms`) con la fila del CSV de sesión de igual `t_cap_ms` (tolerancia 1 ms).
- **Dibujo:** agrupando los periodos por fase módulo 3 (`DIBUJAR_CADA = 3`), una de cada 3 filas es más larga. MJPG: 42.6–43.3 frente a 36.7–39.0 ms. BGRA32: 38.0–39.2 ms (> 33.3 ms en el 98–99 %) frente a 31.9–33.1 ms (> 33.3 ms en el 21–35 %). Los ciclos que dibujan causan la mayoría de los ciclos > 33.3 ms con BGRA32. Con MJPG el 99.4–99.8 % de los ciclos ya supera 33.3 ms aunque no se dibuje: la ventana no es la causa principal.
- **Corrida lenta 171408:** todas las etapas más lentas, incluida `to_numpy`, que solo usa CPU (+42 %). El reloj de la GPU se recuperó desde el 2º tercio (1713 MHz) y el ciclo siguió en ≈ 45 ms. Dentro de las corridas normales, corr(tracker, reloj SM) = 0.11. INFERIDO: estado de rendimiento del equipo (plan "Equilibrado"), no la GPU. La tanda BGRA32 con calentamiento y `typeperf` no mostró corrida lenta (CPU 217 % estable).
- **Razones de la GPU** (`clocks_event_reasons.active`): `0x4` = SW power cap (36–40 % de las muestras en las corridas rápidas, menos en la lenta: no es lo que limita el ciclo); `0x1` = GPU inactiva; `0x400` sin descripción en la ayuda de `nvidia-smi` `[POR COMPLETAR]`; `0x448` aparece 3 veces en la tanda BGRA32 (INFERIDO según nvml.h: `0x400` + HW thermal slowdown `0x40` + HW slowdown `0x8`, con 68–69 °C).
- **Efecto de BGRA32 (INFERIDO a partir de lo MEDIDO):** el ciclo de Python baja ≈ 4.5 ms (casi todo en `to_numpy`, de 6.07 a 1.76 ms), pero el SDK entrega cada frame ≈ 22 ms más tarde (`lag_cam_ms` 23.4 → 46.5 ms de media). El tiempo de decodificación no desaparece: pasa de (a) a `lag_cam_ms` y además crece. Resultado: (a) mejora ≈ 4.5 ms, pero (b) empeora ≈ 17–20 ms. Causa exacta del aumento dentro del SDK `[POR COMPLETAR]`.
- Copia BGRA real dentro de `to_numpy`: 1.72–1.79 ms por llamada (el micro-benchmark sintético daba 0.9 ms).

## 4c. Línea base MJPG repetida (paso 10), 02/11 por la mañana (MEDIDO)
Fuentes en `sesiones/`: `sesion_20261102_<hora>_mjpg-un-hilo-llegada-2026-11-02_cuda-lite.csv` y sus `_perf.txt` y `_latencias.csv` (commit `eb68590`: MJPG, 1 hilo de manos, ventana 1 de cada 3, histéresis de 6 ciclos); GPU en `gpu_lineabase_20261102.csv`; CPU en `cpu_lineabase_20261102.csv`. Mismos métodos que 4b; (b) leída de la columna en línea `latencia_llegada_ms`.
- Condiciones: **otro salón**, sin aire acondicionado, laptop más caliente que el 31/10 (Ale); modo de energía de máximo rendimiento (Ale; con corriente el perfil activo es "mejor rendimiento", leído por Code en el registro con `powercfg`, 02/11); apps abiertas casi iguales al 31/10 (Ale); 1 pestaña.
- Corridas: 132918 = calentamiento (27 s, descartado); 133109 = corrida sin GPU/CPU registrados (fuera de la tanda; cifras parecidas); **tanda: 133512, 133838, 134201** (182–185 s). Un solo cliente: `continuo` 5415/5415, 5243/5253, 5518/5518.

| Métrica (ms salvo indicación) | 133512 | 133838 | 134201 |
|---|---|---|---|
| Ciclos/s (ventanas `[PERF]` < 29.5) | 29.7 (17/93) | 28.8 (79/89) | 29.9 (7/96) |
| Ciclo · `cap_update` · `cap_imgs` | 33.5 · 0.5 · 6.2 | 34.8 · 0.3 · 6.1 | 33.3 · 0.7 · 5.5 |
| ↳ `to_numpy` (ms/llamada) | 5.87 | 5.85 | 5.36 |
| `tracker` · `manos` · `mapeo` · `salida` · `dibujo` | 20.7 · 1.0 · 2.0 · 1.0 · 2.0 | 21.8 · 1.0 · 2.7 · 1.0 · 2.0 | 21.6 · 1.0 · 2.0 · 1.0 · 1.9 |
| Trabajo del hilo de manos · trabajos/s | 21.5 · 28.8 | 25.8 · 26.6 | 21.5 · 28.6 |
| Periodo media / p95 · % ≤ 33.3 ms | 33.6 / 40.0 · 57.1 | 34.9 / 43.0 · 41.2 | 33.5 / 39.6 · 57.8 |
| `lag_cam_ms` media / p95 / máx | 16.7 / 31.1 / 49.4 | 21.2 / 35.9 / 50.0 | 14.1 / 27.1 / 49.5 |
| (a) media / p95 / máx | 31.0 / 34.2 / 70.0 | 32.3 / 36.4 / 75.6 | 31.1 / 33.8 / 69.9 |
| **(b) RNF01** media / p95 / máx (% > 100) | 47.7 / 62.4 / 84.3 (0) | 53.5 / 69.4 / 101.3 (0.04) | 45.2 / 58.4 / 81.4 (0) |
| `lat_tick_ms` media / p95 / máx (% > 250) | 40.6 / 57.9 / 63.3 (0) | 43.0 / 61.2 / 75.1 (0) | 41.9 / 56.9 / 61.8 (0) |
| Edad manos p95 · % ciclos con 2 manos | 43.5 · 96.7 | 69.9 · 97.0 | 43.7 · 95.4 |
| GPU SM mediana (MHz) / W / °C máx · CPU % rendimiento | 1762 / 31.8 / 68 · 207 | 1762 / 32.3 / 68 · 208 | 1762 / 32.5 / 70 · 208 |
- **Dibujo:** por fase módulo 3, el ciclo que dibuja mide 36.7–38.6 ms (> 33.3 en el 99–100 %) y los otros 31.7–33.5 ms.
- **Frente al 31/10 (4b):** ciclo 39.0–39.4 → 33.3–34.8 ms; (b) media 59.5–60.1 → 45.2–53.5 ms. Cambiaron a la vez el modo de energía, el salón, el calor y el segundo cliente: la mejora no se puede atribuir a una sola causa (INFERIDO). La comparación de energía de 4d indica que el modo de energía pesa (una corrida por lado; sin cuantificar, D-014).
- `to_numpy` en el ciclo: 5.4–5.9 ms. 133838 fue más lenta en todas las etapas sin cambio visible en GPU ni CPU (como 171408 el 31/10).

## 4d. Tanda del 02/11 por la tarde (14:45–16:00): ventana, decodificación, energía y diagnóstico de `mapeo` (MEDIDO)
Fuentes en `sesiones/`: `sesion_20261102_<hora>_mjpg-histeresis-ms-2026-11-02<sufijo>_cuda-lite.*` (código hasta `1b69a33`; incluye D-010; el sufijo dice la configuración: `-sinventana`, `-sinventana-decodhilo`, `-swi1ms`, `-sinmanos`); GPU en `gpu_tanda_20261102.csv`; CPU en `cpu_tanda_20261102.csv` (% de rendimiento y % de tiempo del procesador). Calentamiento 144537 (descartado). Configuraciones intercaladas por rondas, como pidió Ale.
- **Validez:** un solo cliente en las 19 corridas; en todas, las filas `continuo` que faltan están solo antes del primer mensaje (reconexión del navegador al arrancar: 0–154 filas) y ninguna después; la última fila de sesión está en `_latencias.csv` en todas (espera de cierre `b98258b`); (b) sin celdas vacías.

Las 19 corridas (ciclo medio = media de los reportes `[PERF]` de 60 ciclos sin el 1º; filas `continuo` < filas de sesión solo por la reconexión al arrancar):
| # | Archivo (en `sesiones/`) | Configuración | Filas de sesión | Filas `continuo` | Ciclo medio `[PERF]` (ms) |
|---|---|---|---|---|---|
| 0 | `sesion_20261102_144537_mjpg-histeresis-ms-2026-11-02_cuda-lite.csv` | Base (calentamiento) | 5451 | 5297 | 33.2 |
| 1 | `sesion_20261102_144917_mjpg-histeresis-ms-2026-11-02_cuda-lite.csv` | Base | 5524 | 5524 | 33.2 |
| 2 | `sesion_20261102_145316_mjpg-histeresis-ms-2026-11-02-sinventana_cuda-lite.csv` | Sin ventana | 5760 | 5702 | 33.1 |
| 3 | `sesion_20261102_145656_mjpg-histeresis-ms-2026-11-02-sinventana-decodhilo_cuda-lite.csv` | Sin ventana + decodificación en el hilo | 5863 | 5809 | 33.1 |
| 4 | `sesion_20261102_150132_mjpg-histeresis-ms-2026-11-02_cuda-lite.csv` | Base | 5332 | 5258 | 34.3 |
| 5 | `sesion_20261102_150533_mjpg-histeresis-ms-2026-11-02-sinventana_cuda-lite.csv` | Sin ventana | 5429 | 5367 | 33.4 |
| 6 | `sesion_20261102_150859_mjpg-histeresis-ms-2026-11-02-sinventana-decodhilo_cuda-lite.csv` | Sin ventana + decodificación en el hilo | 5821 | 5815 | 33.1 |
| 7 | `sesion_20261102_151330_mjpg-histeresis-ms-2026-11-02_cuda-lite.csv` | Base | 5016 | 5010 | 36.8 |
| 8 | `sesion_20261102_151707_mjpg-histeresis-ms-2026-11-02-sinventana_cuda-lite.csv` | Sin ventana | 5337 | 5331 | 34.6 |
| 9 | `sesion_20261102_152134_mjpg-histeresis-ms-2026-11-02-sinventana-decodhilo_cuda-lite.csv` | Sin ventana + decodificación en el hilo | 5427 | 5376 | 33.1 |
| 10 | `sesion_20261102_152559_mjpg-histeresis-ms-2026-11-02_cuda-lite.csv` | Base | 4335 | 4228 | 41.8 |
| 11 | `sesion_20261102_152953_mjpg-histeresis-ms-2026-11-02_cuda-lite.csv` | Base (Equilibrado) | 3806 | 3743 | 47.6 |
| 12 | `sesion_20261102_153456_mjpg-histeresis-ms-2026-11-02_cuda-lite.csv` | Base | 4697 | 4679 | 38.4 |
| 13 | `sesion_20261102_153828_mjpg-histeresis-ms-2026-11-02-swi1ms_cuda-lite.csv` | `--swi1ms` | 4804 | 4731 | 38.8 |
| 14 | `sesion_20261102_154207_mjpg-histeresis-ms-2026-11-02-sinmanos_cuda-lite.csv` | `--sin-manos` | 4797 | 4724 | 37.8 |
| 15 | `sesion_20261102_154541_mjpg-histeresis-ms-2026-11-02-swi1ms_cuda-lite.csv` | `--swi1ms` | 4713 | 4679 | 38.8 |
| 16 | `sesion_20261102_154916_mjpg-histeresis-ms-2026-11-02-sinmanos_cuda-lite.csv` | `--sin-manos` | 4728 | 4693 | 38.3 |
| 17 | `sesion_20261102_155246_mjpg-histeresis-ms-2026-11-02-swi1ms_cuda-lite.csv` | `--swi1ms` | 4734 | 4704 | 38.7 |
| 18 | `sesion_20261102_155624_mjpg-histeresis-ms-2026-11-02-sinmanos_cuda-lite.csv` | `--sin-manos` | 5584 | 5515 | 33.4 |

Rondas intercaladas (cada celda: Base / Sin ventana / Sin ventana + decodificación en el hilo):
| Ronda (corridas) | Ciclos/s · ventanas ≥ 29.5 | Ciclo · `cap_update` | `lag_cam_ms` media / p95 | (b) media / p95 / máx | Edad manos p95 · trabajos/s |
|---|---|---|---|---|---|
| 1 (144917, 145316, 145656) | 29.9 / 30.0 / 30.0 · 94 / 100 / 100 % | 33.2 / 33.1 / 33.1 · 1.4 / 2.9 / 8.4 | 12.0 / 26.7 · 7.0 / 18.5 · 6.5 / 18.7 | 42.4/57.9/86.8 · 37.3/49.1/78.8 · 31.2/44.0/81.0 | 58 / 62 / 71 · 29.6 / 29.9 / 29.0 |
| 2 (150132, 150533, 150859) | 29.2 / 29.8 / 30.0 · 33 / 87 / 100 % | 34.3 / 33.4 / 33.1 · 0.3 / 1.0 / 6.7 | 19.8 / 34.4 · 12.1 / 27.3 · 7.1 / 19.6 | 51.9/67.9/104.0 · 44.5/61.0/99.1 · 33.5/46.0/65.0 | 67 / 69 / 95 · 29.1 / 29.6 / 26.4 |
| 3 (151330, 151707, 152134) | 27.2 / 28.9 / 30.0 · 0 / 8 / 100 % | 36.8 / 34.6 / 33.1 · 0.2 / 0.1 / 5.0 | 23.3 / 40.8 · 21.1 / 36.6 · 8.2 / 20.4 | 57.7/76.0/97.1 · 55.2/72.0/105.9 · 36.3/49.1/83.1 | 77 / 78 / 109 · 26.9 / 28.8 / 23.1 |
- **Decodificación en el hilo:** `copia_jpeg` 0.15–0.18 ms/llamada en el ciclo (frente a `to_numpy` 5.0–5.5 en Base); `decod_hilo` 4.6 / 5.1 / 5.7 ms dentro de cada trabajo; trabajo del hilo 26.3 / 28.6 / 30.9 ms (Base 20.7 / 22.7 / 25.1). (a) media 24.8–28.2 ms. Periodos: 78–85 % en 33 ± 3 ms y ≈ 8.6 % > 40 ms (p95 47–48 ms) con `cap_update` 5–8 ms: INFERIDO, irregularidad de entrega de la cámara, no de Python. % ciclos con 2 manos 88–90 (Base 88–93).
- **Sin ventana:** desaparece la fase larga (fases 33.1–34.6 ms frente a 36.7–41.1 del ciclo que dibuja en Base).
- `lat_tick_ms` > 250 ms: 0 % en las 19 corridas (media 40.8–56.0).
- **Modo de energía** (Base; 152559 → 152953 → 153456): ciclo 41.8 → **47.6** → 38.4 ms; CPU % rendimiento 215 → **115** → 218; GPU 1740 / 29 W → **1519 / 22 W** → 1710 / 30 W; (b) 64.5/86.1/120.9 → **70.3/95.0/131.9 (2.06 % > 100 ms)** → 61.7/82.0/127.0. El modo se cambió a mano entre corridas (Ale).
- **Diagnóstico de `mapeo` (paso 5b):** `--swi1ms` (153828, 154541, 155246): ciclo 38.7–38.8, `mapeo` 3.4–3.5 ms; `--sin-manos` (154207, 154916): ciclo 37.8–38.3, `mapeo` 2.8–2.9 ms; Base de la misma época (153456): 38.4 y 3.43 ms. La 3ª `--sin-manos` (155624, 15:56) dio 33.4 y 1.9 ms: coincide con la recuperación del equipo y no sirve para comparar.
- **Ralentización durante la tanda:** en Base el ciclo pasó de 33.2 (14:49) a 34.3, 36.8 y 41.8 ms (15:26) y 38.4 (15:34), mientras el % de tiempo de CPU subía de 34.8 a 46.6 % con menos ciclos/s. El % de rendimiento de la CPU se mantuvo en 201–218 % (salvo la corrida en Equilibrado) y la GPU en 67–71 °C. INFERIDO: algo más usó la CPU (proceso en segundo plano o Chrome tras 75 min sin recargar); no es la frecuencia ni la GPU. No se puede identificar con estos contadores. Consecuencia: se comparan configuraciones dentro de cada ronda, no entre horas.
- **Pruebas de cierre** (142448, 143049 con ventana; 144008 sin ventana; Ctrl+C): cierre completo en las tres. 144008 salió lenta en todas las etapas (`to_numpy` 9.40 ms/llamada frente a 5.9), con corriente y máximo rendimiento.
- **Error al salir:** en las 3 corridas `--decod-hilo`, "access violation" en `k4abt_frame_release` después de "Sesión guardada" (archivos ya cerrados; datos completos). Causa (leída en pykinect): el último frame del tracker se soltaba después de destruir el tracker. Arreglo `6ed5c0a`. **04/11:** seguía el error, ahora en `Capture.__del__` → `k4a_capture_release` (Ale): pykinect guarda el único Capture en el atributo de clase `Device.capture` y nadie lo soltaba. Arreglo `9cf80d9` (`soltar_objetos_kinect`: Frame, `Device.capture` y sus Transformation antes de cerrar). **Verificado (Ale, 04/11):** consola limpia al cerrar con Ctrl+C en 3 corridas seguidas con `--decod-hilo` (`sesion_20261104_151602`, `_151702`, `_151757_mjpg-d012-2026-11-04-decodhilo_cuda-lite.*`; archivos completos, faltan solo 0/36/6 filas del arranque). **04/11 por la tarde:** cierre limpio en 5/5 corridas con la configuración por defecto (170000–173544, Ale; 4f), con el arreglo `9cf80d9`.

## 4e. Paso 9 (corridas de 10 min), 04/11 (MEDIDO)
Fuentes en `sesiones/`: `sesion_20261104_<hora>_mjpg-d012-2026-11-04<sufijo>_cuda-lite.*` (código `e5b6643`–`9cf80d9`: sin ventana por defecto, D-012); GPU, CPU y CPU por proceso en `gpu_paso9.csv`, `cpu_paso9.csv`, `procesos_paso9.csv` (1ª corrida) y `gpu_paso9b.csv`, `cpu_paso9b.csv`, `procesos_paso9b.csv` (repetición). Mismos métodos que 4b–4d. Ropa: **pantalón ancho (baggy)** en todas (Ale). Rutina: 3 bloques de 3 min (30 s quieto, 1 min brazos, 1 min todo el cuerpo, 30 s manos) + 1 min final.
- **1ª corrida, con VS Code abierto:** calentamiento 144251; corrida 144401 (`--decod-hilo`, 603 s).
- **Repetición, VS Code cerrado, misma sesión:** calentamiento 153206; **Base 153328** (601.7 s); **decodificación en el hilo 154420** (`--decod-hilo`, 603.3 s); **Base de control 155449** (182.4 s, un bloque).
- **Validez:** un solo cliente en todas; filas `continuo` que faltan solo al arrancar (86, 32, 127, 32) y ninguna después; la última fila llegó en todas; (b) sin celdas vacías.

| Métrica (ms salvo indicación) | 144401 decod. (VS Code abierto) | **153328 Base** | **154420 decod.** | 155449 Base control |
|---|---|---|---|---|
| Ciclos/s · ventanas `[PERF]` ≥ 29.5 | 29.89 · 94.4 % | 29.94 · 98.3 % | 29.96 · 99.7 % | 29.91 · 95.6 % |
| `cap_update` · `tracker` · `mapeo` | 3.1 · 25.0 · 3.3 | 3.8 · 20.7 · 2.0 | 9.9 · 21.0 · 1.5 | 3.7 · 20.9 · 2.0 |
| `cap_imgs` · `copia_jpeg` (ms/llamada) | 0.0 · 0.18 | 5.1 · — | 0.0 · 0.13 | 5.1 · — |
| Periodo media / p95 · % > 33.3 ms | 33.5 / 47.1 · 26.7 | 33.4 / 46.5 · 18.5 | 33.4 / 47.2 · 12.7 | 33.5 / 46.2 · 24.7 |
| `lag_cam_ms` media / p95 / máx | 11.7 / 23.9 / 56.8 | 8.5 / 20.1 / 54.6 | 7.8 / 19.7 / 50.1 | 9.5 / 21.4 / 61.7 |
| (a) media / p95 / máx | 30.0 / 34.7 / 115.6 | 29.2 / 32.7 / 65.6 | 23.2 / 26.1 / 59.0 | 29.7 / 32.9 / 59.2 |
| **(b) RNF01** media / p95 / máx (n > 100) | 41.6 / 55.8 / 126.7 (3) | 37.7 / 50.2 / 97.3 (0) | **31.0 / 43.4 / 77.2 (0)** | 39.2 / 52.2 / 109.3 (1) |
| `lat_tick_ms` media / p95 / máx (% > 250) | 46.3 / 63.7 / 87.0 (0) | 40.4 / 55.9 / 71.4 (0) | 40.2 / 55.4 / 70.1 (0) | 40.4 / 56.5 / 68.7 (0) |
| Trabajo del hilo de manos · `decod_hilo` | 37.6 · 6.9 | 19.7 · — | 25.3 · 5.0 | 20.0 · — |
| Trabajos/s · cambios de apertura por mano/s | 16.7 · 6.1–6.2 | 29.5 · 10.4–10.5 | 28.3 · 10.1–10.2 | 29.9 · 10.3–10.9 |
| Edad manos p95 · % ciclos con 2 manos | 113.1 · 91.3 | 63.9 · 91.0 | 65.1 · 92.6 | 47.7 · 93.1 |
| CPU % de tiempo (mediana por tercio) · `code` (% de 1 núcleo) | 42–48 · 158 | 23–27 · — | 25–26 · — | 27 · — |
| GPU SM mediana (MHz) · °C máx | 1702–1755 · 70 | 1718–1762 · 69 | 1755–1762 · 70 | 1762 · 65 |
- "Cambios de apertura por mano/s" = veces que cambia el valor de `apertura_izq`/`apertura_der` en el CSV de sesión dividido por la duración (un dato nuevo cambia el valor; el mantenido se repite). Es una aproximación de las actualizaciones por mano.
- **Criterios, 154420 (decodificación en el hilo, VS Code cerrado):** C1: 300 de 301 ventanas ≥ 29.5 y `cap_update` 9.9 ms; la ventana baja (20.7 ciclos/s, `cap_update` 25 ms, 76 lecturas de color en 60 ciclos) es la caída descrita abajo; % de ciclos > 33.3 ms: 12.7 (INFERIDO: irregularidad de entrega de la cámara; Python espera). C2: p95 19.7 ms ≤ línea base vigente (4c: 27.1–35.9) y ≤ Base de hoy (20.1); por minuto 19.3–20.0 ms, sin crecimiento. C3: (b) mejor que 4c y que la Base de hoy en media, p95 y máx; 0 muestras > 100 ms. C4: 0 % > 250 ms. C5: D-010 y D-012.
- **D-013 (Ale, 04/11): condición cumplida** — manos sin empeorar frente a Base en la misma sesión (trabajos/s −4 %, cambios de apertura por mano −2 a −3 %, edad p95 +1.2 ms, % con 2 manos 92.6 frente a 91.0). **Reservas:** (1) n = 1 corrida de 10 min con decodificación; la Base de control duró 3 min. (2) Tendencia en 10 min (por tercios): trabajos/s 29.7 → 28.2 → 26.9 con decodificación (trabajo de manos 24.2 → 26.3 ms) y 30.0 → 29.7 → 28.9 en Base; se vigila en las 3 corridas finales del paso 9. (3) "HU0008-1 cumple o no" sigue abierto hasta fijar la métrica (frames procesados por segundo o actualizaciones por mano, P-009); con cualquiera de las dos, hoy ≈ 10 actualizaciones/s por mano frente a 30 FPS.
- **VS Code (H6):** misma configuración y mismo día, 144401 (VS Code abierto, `code` 158 % de un núcleo) frente a 154420 (cerrado): `tracker` 25.0 → 21.0, `decod_hilo` 6.9 → 5.0, trabajo de manos 37.6 → 25.3 ms (en 144401 supera 33.3 ms y el hilo toma 1 frame de cada 2: 16.7 trabajos/s), edad p95 113 → 65 ms, CPU 42–48 → 25 %. INFERIDO con evidencia fuerte: VS Code causaba la competencia por CPU. Otros procesos (% de un núcleo): `svchost` 31–54, `dwm` 7–16, `msmpeng` ≤ 3, `omencommandcenterbackground` ≤ 1.
- **Base de control** (155449) igual que la Base 1 (`tracker` 20.9 frente a 20.7, `mapeo` 2.0): sin ralentización durante la tanda.
- **Caída a los ≈ 4.8 min — causa `[POR COMPLETAR]`.** En las tres corridas de 10 min (144401, 153328, 154420) hay **una** ventana `[PERF]` lenta en la misma posición (143–144: 20.7–21.0 ciclos/s, `cap_update` 17–25 ms, 75–76 lecturas de color en 60 ciclos) y **un** hueco de filas de 863–944 ms a los 288.5–289.7 s de la primera fila. Las lecturas de color de más son capturas sin color o sin profundidad, que se saltan. El CSV **no guarda el número de cuerpos** (`num_bodies` solo decide si se escribe la fila), así que el hueco no distingue "sin cuerpo" de "captura incompleta". Hipótesis sin elegir: (i) fase del baile de la rutina (a los 288 s es el minuto de "todo el cuerpo" del bloque 2; la misma fase de los bloques 1 y 3 no tiene hueco); (ii) una persona detrás (observación de Ale, no verificada); (iii) evento de la cámara o del SDK ligado al tiempo desde el arranque. **Actualizado en 4f:** la caída aparece también en la corrida quieta; (i) no es causa única.
- **Rodillas (ropa):** desviación estándar del ángulo de rodilla en los tramos quietos de la rutina (ubicados por tiempo, INFERIDO; un tramo de 154420 tiene el hombro con 11.5° de variación, así que la ubicación es aproximada): 144401 1.0–6.8°, 153328 1.3–6.1°, 154420 2.1–7.5°, 155449 0.7–3.2°; el 02/11 (144917, 145656, 150859, 152134) 0.2–1.4°. Hombro 0.5–1.0° en los tramos bien ubicados. Las articulaciones de pierna nunca se marcan NONE (0 %). INFERIDO: compatible con que el pantalón ancho empeore las rodillas; la ropa del 02/11 es `[POR COMPLETAR]`.

## 4f. Paso 9, tanda del 04/11 por la tarde (17:00–17:46): corrida quieta y 3 corridas finales de 10 min (MEDIDO)
Fuentes en `sesiones/` (commit `e5cc6cb`): `sesion_20261104_<hora>_mjpg-d013-2026-11-04_cuda-lite.*` (código `9ecf383`, configuración por defecto: sin ventana D-012 y decodificación en el hilo D-015; cabecera de `_perf.txt`: `ventana=no | decodif=hilo`); GPU, CPU y CPU por proceso en `gpu_paso9c.csv`, `cpu_paso9c.csv`, `procesos_paso9c.csv`. Mismos métodos que 4b–4e. C1 se cuenta sin la ventana #0 (arranque) y también con ella (D-016). Trabajos/s: media de ventanas sin la #0 ni las 2 de cierre (al cerrar caen a ≈ 0 con el ciclo a 30/s: Ale ya no está delante).
- **Condiciones (Ale):** navegador **Edge** en toda la tanda (no Chrome, como pide la sección 10; efecto sin cuantificar). `procesos_paso9c.csv` no tiene ningún proceso `chrome` y sí `msedge` (MEDIDO). **Pantalón ancho (baggy)** en toda la tanda. VS Code cerrado (sin `code` en el registro, MEDIDO). Eventos externos: ninguno. En la corrida quieta Ale estuvo de pie con las manos delante del pecho (postura distinta a la de los tramos quietos de la rutina).
- **Corridas:** 170000 calentamiento (68.7 s, descartado); **170136 quieta** (485.0 s); **finales 171221** (602.7 s), **172514** (606.9 s) y **173544** (603.7 s).
- **Validez:** un solo cliente en las 5 (0 filas `continuo` duplicadas); filas que faltan solo al arrancar (6, 10, 55, 85, 37) y ninguna después; la última fila llegó en todas; (b) sin celdas vacías. **Cierre limpio en 5/5** (consola sin "access violation", Ale), con el arreglo `9cf80d9`.

| Métrica (ms salvo indicación) | 170136 quieta | 171221 | 172514 | 173544 |
|---|---|---|---|---|
| C1: ventanas `[PERF]` ≥ 29.5, sin #0 · con #0 | 242/243 · 242/244 | 297/301 · 297/302 | 302/303 · 302/304 | 299/302 · 299/303 |
| Ventanas bajas sin #0 (ciclos/s) | #144 (20.9) | #73 (29.1), #114 (29.3), **#144 (20.9)**, #286 (29.3) | **#144 (21.4)** | #115 (29.3), **#144 (20.7)**, #187 (29.3) |
| Ciclos/s medio · `cap_update` · `tracker` · `mapeo` | 29.95 · 9.8 · 20.9 · 1.35 | 29.94 · 9.7 · 21.0 · 1.65 | 29.95 · 9.8 · 21.0 · 1.62 | 29.95 · 10.1 · 20.9 · 1.64 |
| Periodo media / p95 · % > 33.3 ms | 33.4 / 47.0 · 15.0 | 33.4 / 47.0 · 13.9 | 33.4 / 47.0 · 14.2 | 33.4 / 47.0 · 14.9 |
| `lag_cam_ms` media / p95 / máx | 8.2 / 20.4 / 48.5 | 8.3 / 20.0 / 51.2 | 8.3 / 20.2 / 43.0 | 8.8 / 20.6 / 50.1 |
| (a) media / p95 / máx | 23.2 / 26.0 / 56.3 | 23.4 / 26.3 / 63.1 | 23.3 / 26.2 / 63.5 | 23.1 / 25.8 / 65.1 |
| **(b) RNF01** media / p95 / máx (n > 100; % > 100) | 31.5 / 44.1 / 77.0 (0; 0) | 31.7 / 44.1 / 75.1 (0; 0) | 31.6 / 44.2 / 79.2 (0; 0) | 31.9 / 44.3 / 72.2 (0; 0) |
| `lat_tick_ms` media / p95 / máx (% > 250) | 40.5 / 55.7 / 69.5 (0) | 40.1 / 55.7 / 77.2 (0) | 39.8 / 55.0 / 72.6 (0) | 40.3 / 55.5 / 70.1 (0) |
| Trabajo del hilo de manos · `decod_hilo` | 25.1 · 4.92 | 25.0 · 5.10 | 25.5 · 5.24 | 24.7 · 4.80 |
| Trabajos/s · por tercio | 29.1 · 29.6 → 29.2 → 28.5 | 28.5 · 29.8 → 28.4 → 27.3 | 28.1 · 29.9 → 28.2 → 26.3 | 28.7 · 29.8 → 28.5 → 27.8 |
| Cambios de apertura por mano/s (izq / der) | 6.12 / 7.27 | 10.30 / 10.24 | 10.04 / 9.86 | 10.50 / 10.31 |
| Edad manos p95 · % ciclos con 2 manos | 61.7 · 99.9 | 79.1 · 87.5 | 65.1 · 92.1 | 64.7 · 92.7 |
| CPU % de tiempo (mediana por tercio) · `python` (% de 1 núcleo) | 29.2 / 27.8 / 22.4 · 172 | 26.6 / 25.8 / 24.6 · 174 | 26.2 / 25.9 / 24.7 · 173 | 26.7 / 24.7 / 23.1 · 168 |
| GPU SM mediana (MHz) · °C máx | 1762 · 69 | 1755 · 69 | 1755 · 69 | 1762 · 70 |
- **Criterios, 3 finales:** **C1 estricto no cumple** en ninguna, ni sin #0 ni con #0. Las ventanas bajas son la #144 (la caída, abajo) y 0–2 ventanas de 29.1–29.3 ciclos/s sin capturas incompletas (60 lecturas de color en 60 ciclos). % de ciclos > 33.3 ms: 13.9–14.9. `cap_update` 9.7–10.1 ms > 0 (Python espera a la cámara). **C2 cumple:** p95 20.0–20.6 ≤ línea base vigente (4c: 27.1–35.9); por minuto 19.6–21.0, sin crecimiento. **C3 cumple:** (b) mejor que 4c en media (45.2–53.5), p95 (58.4–69.4) y máx (81.4–101.3); 0 muestras > 100 ms (HU0023-1). **C4 cumple:** 0 % > 250 ms. **C5:** D-010, D-012 y D-015 (código `9ecf383`).
- **Entre corridas no hay ralentización:** `tracker` 21.0 / 21.0 / 20.9 ms; `python` 174 / 173 / 168 % de un núcleo; GPU igual. Otros procesos en las finales (media, % de un núcleo): `svchost` 35–37, `system` 15–18, `dwm` 7–15, `msedge` 7–8, `nvdisplay.container` 7, `audiodg` 5.
- **Escalón permanente después del evento de ≈ 290 s (MEDIDO).** Trabajos/s en las ventanas #1–#143 frente a las de #145 en adelante (sin las 2 de cierre); `lag_cam_ms` entre 10–285 s y entre 295 s y el final:

| Corrida | Trabajos/s antes → después | `lag_cam_ms` media antes → después | `lag_cam_ms` p95 antes → después |
|---|---|---|---|
| 170136 quieta | 29.54 → 28.53 | 8.7 → 7.6 | 20.7 → 19.5 |
| 171221 | 29.73 → 27.41 | 8.5 → 8.1 | 20.3 → 19.7 |
| 172514 | 29.86 → 26.58 | 8.6 → 8.0 | 20.5 → 19.9 |
| 173544 | 29.76 → 27.80 | 9.1 → 8.5 | 20.9 → 20.1 |
- Recalculado sobre los `_perf.txt` de 4e: 154420 (decodificación en el hilo) 29.72 → 27.11; 153328 (decodificación en el ciclo) 29.98 → 29.54. La bajada por tercios de los trabajos/s (reserva (2) de D-015) es sobre todo este escalón, no una deriva continua. Causa `[POR COMPLETAR]`.
- **`mapeo` crece** de ≈ 1.0 a ≈ 2.0 ms en los primeros ≈ 5 min y luego se queda plano, en las 4 corridas de la tarde y en 154420; en 153328 está en ≈ 2.0 desde el inicio. `[PERF]` da `mapeo` en ms enteros (son medias de ventanas). No es `NORM_VENTANA_S` (20 s). Causa `[POR COMPLETAR]`.
- **Caída a los ≈ 290 s (causa `[POR COMPLETAR]`).** Las 4 corridas de ≥ 5 min, **incluida la quieta**, tienen la ventana #144 con 20.7–21.4 ciclos/s, `cap_update` 23–25 ms y 73–76 lecturas de color en 60 ciclos (13–16 capturas incompletas), y un hueco de filas de 832–928 ms a los 288.7–290.0 s de la primera fila. Con 4e son **7 de 7** corridas de ≥ 5 min. Hipótesis: (i) baile: **no es causa única**, porque aparece también en la corrida quieta, sin rutina; (ii) persona detrás: abierta; (iii) evento de la cámara o del SDK: abierta. Prueba independiente en el plan (paso 12). Descripción del hueco (INFERIDO a partir de MEDIDO; no se usa como evidencia sobre (ii)): en las ventanas 140–147 hay tantos ciclos `[PERF]` como filas del CSV (≈ 0 ciclos sin cuerpo; igual al mover el ancla ± 1.5 s); el hueco son capturas incompletas y espera de la cámara.
- **Rodillas** (solo como dato; sin conclusión sobre la ropa hasta la prueba con shorts): corrida quieta, desviación estándar del ángulo de rodilla izq / der 7.7° / 5.2° (por minuto 4.7–8.6° / 3.6–7.7°), hombros 0.9–3.0°, `vel_rodilla` mediana 65.5 °/s (p95 158). Tramos quietos de la rutina bien ubicados (hombros ≤ 0.8°): 0.6–1.9° / 0.9–1.4°, `vel_rodilla` mediana 8–21 °/s. Tramos mal ubicados por tiempo (hombros 1.7–9.9°): 171221 a los 185–205 y 365–385 s, y 173544 a los 365–385 s.

## 5. Otras cifras vigentes (de ESTADO_ACTUAL, sesiones 26–28/10)
- Jitter con suavizado: hombros −22% a −32%; rodilla −52% a −53% (dos sesiones).
- Articulaciones de manos del Kinect sin valor (NONE) ≈ 53% de los frames; las otras 26 ≈ 100%.
- MediaPipe: ≥ 1 mano en 86–96% de los ciclos; ≈ 13 actualizaciones/s por mano con 1 hilo.
- Aciertos del recuadro por origen (log `[ROI]`, ventanas de 60 ciclos): muñeca 92–100% casi siempre; mano 51–100% con pocos intentos.

## 6. Estado de las hipótesis
- H1 (la espera de cámara baja si el ciclo baja de 33.3 ms): **CONFIRMADA en corridas de 3 min (02/11, 4d).** Con decodificación en el hilo y sin ventana, Python espera a la cámara (`cap_update` 5.0–8.4 ms) y `lag_cam_ms` baja a 6.5–8.2 ms de media (p95 18.7–20.4), frente a 12.0–23.3 (p95 26.7–40.8) de Base en las mismas rondas (MEDIDO). No llega a 0: el resto es la latencia interna del SDK `[POR COMPLETAR]`. Con BGRA32 (31/10) ese piso sube ≈ 22 ms.
- H2 (58–62 = latencia + espera de cámara): REFUTADA el 31/10; **REABIERTA el 01/11** y reproducida con (b) (sección 0.2 y 4b). El origen original de las cifras de ESTADO_ACTUAL sigue sin confirmarse (Ale no lo recuerda, 02/11).
- H3 (`lat_tick` ≈ etapas previas + espera hasta el siguiente ciclo): CONSISTENTE con 47.6–51.2 ms (28/10), 48.8–50.4 (MJPG 31/10), 45.7–47.1 (BGRA32 31/10), 40.6–43.0 (Base 02/11, 4c) y 40.8–56.0 (tanda 02/11, 4d): baja al bajar el ciclo.
- H4 (cortes baratos): el corte con evidencia es la decodificación MJPG; `flush`/`print` valen centésimas de ms aislados. 31/10: BGRA32 quita 4.3 ms de `to_numpy` pero empeora (b) (ver 4b); `print` = 0.27 ms (no vale la pena); ventana = 2.0 ms/ciclo de media y ≈ 6 ms en el ciclo que dibuja. **02/11 (4d):** decodificar en el hilo de manos saca ≈ 5 ms del ciclo sin empeorar `lag_cam_ms` (a diferencia de BGRA32), pero alarga el trabajo de manos 4.6–5.7 ms.
- H6 (02/11, INFERIDA): el rendimiento depende del estado del equipo más que de los cambios probados (modo de energía: la corrida en Equilibrado salió más lenta que las dos que la rodeaban, sin cuantificar por D-014; ralentización de ≈ 8 ms en Base entre 14:49 y 15:26 con más uso de CPU). **04/11 (4e):** con el registro por proceso, VS Code (`code`, 158 % de un núcleo) explica la corrida lenta del paso 9; cerrado, el `tracker` vuelve a ≈ 21 ms y el trabajo de manos baja de 37.6 a 25.3 ms (INFERIDO con evidencia fuerte; misma configuración y mismo día). La ralentización del 02/11 no se midió por proceso y su causa sigue sin confirmar.
- H5 (pipeline en 2 etapas): POSIBLE (las DLL se cargan con `ctypes.CDLL` y sueltan el GIL en la llamada nativa), pero 1→2 hilos de manos ya costó ≈ 3.6 ms de ciclo: NO es gratis; medir antes de asumir solapamiento. Solo si 5–11 no bastan.

## 7. Presupuesto (INFERIDO)
- Tracker 23–24 ms es el piso. Para 33.3 ms quedan ≤ 9.8 ms para todo lo demás; hoy son 15–17 ms (MJPG).
- Con decodificación fuera del ciclo (ahorro estimado 4–6 ms) y sin ventana de dibujo: ciclo ≈ 31.5 ms (margen ≈ 2 ms); si `mapeo` baja a lo medido aislado: ≈ 28.5 ms (margen ≈ 5 ms).
- Aviso: con `DIBUJAR_CADA=3`, cada tercer ciclo paga ≈ 7–9 ms y dispara el p95.
- **Con lo MEDIDO el 31/10 (4b), BGRA32:** fuera del tracker quedan ≈ 10.9 ms (ciclo medio 34.6 − tracker 23.7). Sin ventana (−2.0 ms MEDIDO): ≈ 32.6 ms, margen ≈ 0.7 ms (INFERIDO); los ciclos que no dibujan ya miden 31.9–33.1 ms. Aclarar `mapeo` (3.6 ms frente a 0.7 aislado) daría hasta ≈ 3 ms más.
- Alternativa a BGRA32: pedir MJPG y decodificar en el hilo de manos. **Medida el 02/11 (4d):** el ciclo queda limitado por la cámara (≈ 33.1 ms) con margen `cap_update` de 8.4 → 6.7 → 5.0 ms en las rondas 1–3; el margen se achica a medida que el equipo se pone lento (MEDIDO). El costo pasa al hilo de manos: su trabajo (26–31 ms) se acerca a 33.3 ms y los trabajos/s bajan de 29.0 a 23.1 (MEDIDO). Si el trabajo supera 33.3 ms, el hilo tomaría 1 frame de cada 2 (INFERIDO).

## 8. Parámetros que dependen de la tasa de ciclos (cambian si se pasa de ≈ 24 a 30 Hz)
- ~~`UMBRAL_ESTABILIDAD_ZONA = 6` ciclos~~ → **`UMBRAL_ESTABILIDAD_ZONA_S = 0.250` (D-010, `d0331e8`, 02/11)**: ya no depende de la tasa. Por ser en ciclos enteros, el cambio ocurre en el primer ciclo que llega a ≥ 250 ms: 267 ms a 30 Hz y 275 ms a 25.5 Hz (MEDIDO en simulación de la función aislada). Tras una ausencia del cuerpo, cada ciclo suma como máximo 0.1 s. (`zona.py` sigue en 6 frames, solo si `REGISTRO_POR_ANGULO=False`.)
- `EMA_ANGULO_BRAZO = 0.5` y `EMA_VEL_RODILLA = 0.4`: retardo ≈ (1−α)/α · ciclo (41 → 33 ms y 61 → 50 ms).
- `len(hist) >= 5` y `len(recientes) >= 4`; el tick se evalúa una vez por ciclo.
- 31/10 (MEDIDO): la tasa pasó de 25.4–25.6 Hz (MJPG) a 28.5–29.4 Hz (BGRA32). INFERIDO: la histéresis de 6 ciclos pasa de ≈ 235 a ≈ 208 ms. 02/11: con MJPG la tasa ya llegó a ≈ 29.7 Hz (4c); resuelto con D-010 (histéresis en ms). Los EMA siguen por ciclo: se acepta que su retardo baje (D-010).
- Sin efecto musical: `DIBUJAR_CADA`, `REPORTE_CADA`, `MAX_DESCARTE_POR_CICLO`.
- En segundos (no cambian): `VENTANA_INTENSIDAD_S`, `VENTANA_FLUIDEZ_S`, `NORM_VENTANA_S`, `NORM_CALENTAMIENTO_S`, `HOLD_ANGULO_S`, `HOLD_APERTURA_S`, `VENTANA_FUSION_MS`, `intervalo_s`, `dt` real de `VelocidadAngular`.

## 9. Plan vigente
Tarea 1 (auditoría de solo lectura): **HECHA el 31/10/2026** (resultados arriba).
Tarea 2 (reducción del ciclo). Un paso por commit; cada paso se mide con el protocolo de la sección 10. Orden del 02/11 (7 → 10 → 5 → 5b): **HECHO**. Ale decidió D-012 (sin ventana), D-013 (decodificación en el hilo; condición cumplida con reservas el 04/11), D-014 (máximo rendimiento) y D-015 (decodificación en el hilo por defecto). Paso 9 HECHO el 04/11 (4f). **Siguiente:** prueba A de cámara (paso 12) y fijar la métrica de HU0008-1 (P-009).
| # | Paso | Estado |
|---|---|---|
| 1 | Commit del estado actual en la rama `wip-28e` | HECHO 31/10 (`368c20a`) |
| 2 | Rama `perf/ciclo-30hz` y `HILO_POR_MANO=False` (ver D-003; Ale confirma) | HECHO 31/10 (`9b2d30a`) |
| 3 | Cronómetros por línea en `[PERF]` para `to_numpy()`, `print` e `imshow`, sin cambiar comportamiento | HECHO 31/10 (`1764380`, `[PERF-LINEA]`) |
| 3b | Guardar `[PERF]` en `_perf.txt` y las latencias del navegador en `_latencias.csv` (D-006) | HECHO 31/10 (`e2fef0d`, `3151709`) |
| 4 | Línea base: 3 corridas de 3 min con la rutina fija (sección 10) | HECHO 31/10 (171408, 171755, 172123; sección 4b), **con un cliente de prueba de más y sin calentamiento**; se repite en el paso 10 |
| 5 | Color sin decodificar en el ciclo y sin ventana en sesiones de evaluación; volver a medir | MEDIDO. BGRA32 (`f453ac0`, 31/10): no cumple C1 ni C2. Sin ventana (`6b83b6c`) y decodificación en el hilo de manos (`47b8a3e`), 3 corridas cada una el 02/11 (4d): solo sin ventana + decodificación sostuvo ≥ 29.5 ciclos/s en las 3 rondas. Configuración elegida: D-012 (sin ventana por defecto, `e5b6643`) y D-013 (`--decod-hilo`, condicionada al paso 9) |
| 5b | Explicar `mapeo` (3.6 ms real frente a 0.7 aislado): corrida con `sys.setswitchinterval(0.001)` y corrida sin hilo de manos (diagnóstico) | Corridas HECHAS 02/11 (`66b9ebd`, `529e248`; 4d): hipótesis GIL descartada; causa abierta (sección 11). Sin hilo de manos −0.6 ms; el resto sigue al estado del equipo (H6) |
| 6 | Decidir histéresis y EMA en milisegundos (P-001) | HECHO 02/11: D-010 (histéresis 250 ms, `d0331e8`; EMA sin cambios) |
| 7 | Enviar `lag_cam_ms` en el mensaje y guardar `latencia_llegada_ms` (= `latencia_ms + lag_cam_ms`) en `_latencias.csv`, sin cambiar columnas existentes ni comportamiento musical | HECHO 02/11 (`eb68590`); verificado contra el cálculo offline (≤ 0.05 ms, 4c) |
| 7b | Cierre y operación de las corridas: esperar el último lote de latencias al cerrar (`b98258b`), interruptores por línea de comandos (`1b69a33`, D-011), soltar el último frame del tracker antes de destruirlo (`6ed5c0a`, protegido en `e1616bf`; Capture compartido en `9cf80d9`), registro de CPU por proceso (`2892e6a`) | HECHO. Error al salir resuelto con `9cf80d9` (04/11), verificado en 3 cierres seguidos (4d) |
| 8 | Pipeline de 2 etapas (H5) solo si 5–11 no cumplen C1 | CONDICIONAL. Paso 9 hecho: C1 estricto no se cumple por la ventana de la caída (#144) y 0–2 ventanas de 29.1–29.3 ciclos/s por corrida (4f); cómo contarlas lo fija Ale (P-011) |
| 9 | Corrida de 10 min y verificación de C1–C5 | HECHO 04/11 (4e y 4f). Mañana: 144401 con VS Code abierto (no cumple C1 estricto ni C3 máx); 153328 Base, 154420 decodificación y 155449 control. Tarde: corrida quieta 170136 y **3 corridas finales** 171221, 172514 y 173544 con la configuración por defecto: **C1 estricto no cumple** (297/301, 302/303 y 299/302 ventanas ≥ 29.5 sin #0); **C2–C5 cumplen**. Condición de D-013 cumplida con reservas; D-015 (`9ecf383`). Métrica de HU0008-1 abierta (P-009) |
| 10 | Repetir la línea base MJPG: 1 pestaña, calentamiento descartado, plan de energía de máximo rendimiento, 3 corridas de 3 min | HECHO 02/11 (133512, 133838, 134201; 4c). La comparación 1 vs 2 hilos de D-003 **no** se repitió |
| 11 | Método para medir (c) extremo a extremo (US23): micrófono o loopback, y latencia interna del SDK | PENDIENTE (decide Ale el método; no bloquea 7 ni 10) |
| 12 | **Prueba A de cámara**: grabar 6 min solo con la cámara (sin tracker, sin MediaPipe, sin Python) y buscar el hueco de la caída. Comando: `"C:\Program Files\Azure Kinect SDK v1.4.1\tools\k4arecorder.exe" -c 720p -d NFOV_UNBINNED -r 30 --imu ON -l 360 sesiones\camara_A1.mkv`. Modos iguales a `main.py` líneas 196–200: color 720p MJPG (`-c 720p`; NV12 y YUY2 son modos aparte), profundidad `NFOV_UNBINNED`, 30 fps, sin sincronización externa (Standalone, el valor por defecto). IMU encendida porque `pykinect` la arranca en `Device.start` (`start_imu()`). `main.py` usa `synchronized_images_only = False`; qué hace `k4arecorder` con eso `[POR COMPLETAR]`. Comprobar en el MKV que el formato de color grabado es MJPG. Mismo salón, persona quieta delante, `main.py` cerrado (la cámara es exclusiva), registros de GPU, CPU y procesos encendidos; si se puede, 2 grabaciones. Análisis (script de solo lectura con la reproducción de `pykinect_azure`): por captura, si hay color y profundidad y su marca de tiempo del dispositivo; saltos > 50 ms entre marcas de color, capturas incompletas y frames frente a 30 × duración; **hueco buscado entre 270 y 310 s** desde el primer frame. Límite: el MKV no guarda la hora de llegada al PC. Disco: ≈ 1.3 GB/min (INFERIDO), ≈ 7.8 GB por grabación; libres 348 GB en C: (MEDIDO 05/11). `sesiones/*.mkv` está en `.gitignore` (`2d3920a`) | PENDIENTE (propuesta aprobada por Ale, 05/11) |
| 12b | **Prueba B de cámara**: script aparte (`prueba_camara.py`, sin tocar `main.py`) que abre la Kinect con el mismo `device_config`, sin tracker ni manos ni WebSocket, lee todas las capturas sin descartar y guarda por captura `t_perf`, las marcas de tiempo del sistema y del dispositivo de color y profundidad, `ok_color` y `ok_depth`. Ve también la entrega al PC | CONDICIONAL: solo si la prueba A no muestra hueco |
Fuera de este plan: `latencia_interna_SDK` `[POR COMPLETAR]`.

## 10. Protocolo de corrida (repetible)
1. Laptop enchufada, modo de energía de **máximo rendimiento** (requisito de operación, D-014; en Equilibrado la corrida salió más lenta, 4d), solo Chrome con **una sola pestaña** de `index.html` (ninguna otra pestaña ni navegador integrado de Code con la página abierta), misma distancia (de pie), misma luz y el mismo salón para toda la tanda. Antes de empezar, revisar en el Administrador de tareas que ningún otro proceso use la CPU de forma sostenida. Segunda terminal: `nvidia-smi --query-gpu=timestamp,clocks.sm,clocks.max.sm,temperature.gpu,power.draw,clocks_throttle_reasons.active --format=csv -l 1 -f sesiones\gpu_<tanda>.csv`. Tercera terminal (Símbolo del sistema como administrador; contadores localizados en español): `typeperf "\Información del procesador(_Total)\% de rendimiento del procesador" "\Información del procesador(_Total)\% de tiempo de procesador" -si 1 -o sesiones\cpu_<tanda>.csv`. Cuarta terminal (uso de CPU por proceso, H6; desde el 04/11): `powershell -ExecutionPolicy Bypass -File registrar_procesos.ps1 sesiones\procesos_<tanda>.csv` (columnas `t_local, proceso, pid, cpu_pct`; `cpu_pct` en % de un núcleo lógico, 12 núcleos = 1200 %). Arrancar las tres antes de la primera corrida y detenerlas con Ctrl+C al terminar la tanda.
1b. Una corrida de calentamiento de ≈ 1 min que se descarta (31/10: la 1ª corrida de la tanda MJPG salió ≈ 7 ms más lenta en todas las etapas). Filtro: si `[PERF-LINEA]` muestra `to_numpy` ≥ 8 ms/llamada, el equipo está lento (02/11: 144008 dio 9.4 ms); esperar, revisar procesos y repetir el calentamiento.
2. `python main.py cuda lite [--sin-decod-hilo] [--swi1ms] [--sin-manos] [--con-ventana]` (D-011; sin ventana por defecto desde D-012, `--con-ventana` solo para depurar; decodificación en el hilo por defecto desde D-015, `--sin-decod-hilo` para decodificar en el ciclo). VS Code cerrado (04/11: con VS Code abierto el ciclo empeora, 4e). Misma ropa en toda la tanda, anotada (04/11: pantalón ancho; rodillas más ruidosas, 4e); esperar 5 s (el navegador tarda hasta ≈ 5 s en reconectarse y esas filas faltan en `_latencias.csv`); rutina fija de 3 min: 30 s quieto, 60 s brazos arriba y abajo, 60 s baile amplio, 30 s abrir y cerrar manos con las dos manos visibles. No recargar la pestaña entre corridas.
3. **Un** Ctrl+C en la consola para cerrar (con `--con-ventana`, `q` en la ventana) y esperar a "Kinect cerrada correctamente". Quedan en `sesiones/` el CSV de sesión, `_perf.txt` y `_latencias.csv`. Comprobar que las filas `continuo` de `_latencias.csv` ≈ filas del CSV de sesión (si son el doble, había 2 clientes: repetir). La configuración queda en el nombre (sufijo de `VERSION_MAIN`). No usar `Start-Transcript` (no graba la salida de Python).
4. 3 corridas por configuración, **intercaladas por rondas** (A B C, A B C, …) para que la deriva del equipo afecte a todas por igual; comparar dentro de cada ronda (02/11: Base varió 33.2 → 41.8 ms en 37 min). No cambiar código durante la tanda. No mezclar con pruebas de sonido.

## 11. Pendientes y huecos
- ~~Perfil de un ciclo real con cronómetros por línea (paso 3–4).~~ HECHO 31/10 (sección 4b).
- `[POR COMPLETAR]` latencia interna del SDK entre `system_timestamp` y la disponibilidad del capture. Con BGRA32 `lag_cam_ms` sube ≈ 22 ms; falta saber qué parte es decodificación y qué parte es espera dentro del SDK.
- `[POR COMPLETAR]` latencia real hasta el sonido (c) (US23, paso 11).
- `[POR COMPLETAR]` origen exacto de las cifras RNF01 p95 78–83 y máx 112–115. Candidato: (b) (sección 0.2). Ale no lo recuerda; no se puede confirmar.
- `[POR COMPLETAR]` significado del bit `0x400` en las razones de reloj de la GPU.
- `[POR COMPLETAR]` causa de los 2–4 ms de `mapeo` (paso 5b): **hipótesis GIL descartada; causa abierta** (4d: `setswitchinterval(0.001)` sin efecto; sin hilo de manos −0.6 ms; `mapeo` varía 1.9–3.9 ms con el estado del equipo).
- `[POR COMPLETAR]` qué consumió CPU durante la tanda del 02/11 (Base 33.2 → 41.8 ms, % de tiempo de CPU 34.8 → 46.6 %; H6). Falta el uso por proceso.
- ~~`[POR COMPLETAR]` verificar con la Kinect que `6ed5c0a` elimina el "access violation" al salir.~~ Resuelto con `9cf80d9`; consola limpia en 3 cierres seguidos (Ale, 04/11; sesiones 151602, 151702, 151757).
- Riesgo para HU0008-1 con decodificación en el hilo: medido el 04/11 (4e), sin empeorar frente a Base en la misma sesión, con reservas (n = 1; tendencia de trabajos/s 29.7 → 26.9 en 10 min). **Actualizado 04/11 tarde (4f):** las 3 corridas finales repiten la bajada (≈ 29.8 → 26.3–27.8 por tercios); es sobre todo un escalón después de la caída de ≈ 290 s (29.7–29.9 → 26.6–27.8 trabajos/s), no una deriva continua. Causa del escalón `[POR COMPLETAR]`.
- `[POR COMPLETAR]` métrica de HU0008-1: frames procesados por segundo o actualizaciones por mano (P-009). Hasta fijarla, "HU0008-1 cumple o no" queda abierto.
- `[POR COMPLETAR]` causa de la caída a los ≈ 4.8 min (≈ 290 s), en 7 de 7 corridas de ≥ 5 min del 04/11 (4e y 4f), incluida la corrida quieta. Hipótesis sin elegir: persona detrás (Ale, no verificada) o evento de la cámara; el baile no es causa única (4f). El CSV no guarda el número de cuerpos; añadirlo sería un cambio de código (no hecho). Siguiente: prueba A (paso 12).
- `[POR COMPLETAR]` causa del escalón de trabajos/s y `lag_cam_ms` después de la caída (4f).
- `[POR COMPLETAR]` por qué `mapeo` sube de ≈ 1 a ≈ 2 ms en los primeros ≈ 5 min con decodificación en el hilo (4f; con resolución de 1 ms).
- `[POR COMPLETAR]` navegador: la sección 10 pide Chrome y la tanda del 04/11 por la tarde usó Edge (4f); en qué navegador se hicieron las tandas anteriores y cuál fija el protocolo (P-010).
- `[POR COMPLETAR]` ropa en las corridas del 02/11 (para comparar el ruido de rodilla, 4e). 04/11 mañana y tarde: pantalón ancho (baggy).
- Pendiente de datos (no medido): confianza de rodillas y tobillos en el CSV. Ale observó el 31/10 más movimiento falso de piernas al subir los brazos; en las sesiones 164334/164633 la mediana de la velocidad de rodilla es 35–111 °/s con los hombros a 45–135° (11–16 °/s quieto con los brazos abajo), y eso sube el tempo.
- Garantía FIFO del SDK al vaciar la cola: INFERIDA; las cifras de `lag_cam_ms` la respaldan.