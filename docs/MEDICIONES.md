# MEDICIONES — línea base, hipótesis y plan (corte: 02/11/2026; mediciones hasta el 02/11)

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
- **Frente al 31/10 (4b):** ciclo 39.0–39.4 → 33.3–34.8 ms; (b) media 59.5–60.1 → 45.2–53.5 ms. Cambiaron a la vez el modo de energía, el salón, el calor y el segundo cliente: la mejora no se puede atribuir a una sola causa (INFERIDO). La comparación de energía de 4d indica que el modo de energía pesa (6–9 ms).
- `to_numpy` en el ciclo: 5.4–5.9 ms. 133838 fue más lenta en todas las etapas sin cambio visible en GPU ni CPU (como 171408 el 31/10).

## 4d. Tanda del 02/11 por la tarde (14:45–16:00): ventana, decodificación, energía y diagnóstico de `mapeo` (MEDIDO)
Fuentes en `sesiones/`: `sesion_20261102_<hora>_mjpg-histeresis-ms-2026-11-02<sufijo>_cuda-lite.*` (código hasta `1b69a33`; incluye D-010; el sufijo dice la configuración: `-sinventana`, `-sinventana-decodhilo`, `-swi1ms`, `-sinmanos`); GPU en `gpu_tanda_20261102.csv`; CPU en `cpu_tanda_20261102.csv` (% de rendimiento y % de tiempo del procesador). Calentamiento 144537 (descartado). Configuraciones intercaladas por rondas, como pidió Ale.
- **Validez:** un solo cliente en las 19 corridas; en todas, las filas `continuo` que faltan están solo antes del primer mensaje (reconexión del navegador al arrancar: 0–154 filas) y ninguna después; la última fila de sesión está en `_latencias.csv` en todas (espera de cierre `b98258b`); (b) sin celdas vacías.

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
- **Error al salir:** en las 3 corridas `--decod-hilo`, "access violation" en `k4abt_frame_release` después de "Sesión guardada" (archivos ya cerrados; datos completos). Causa (leída en pykinect): el último frame del tracker se soltaba después de destruir el tracker. Arreglo `6ed5c0a` sin verificar todavía con la Kinect.

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
- H6 (02/11, INFERIDA): el rendimiento depende del estado del equipo más que de los cambios probados (modo de energía: +6–9 ms en Equilibrado; ralentización de ≈ 8 ms en Base entre 14:49 y 15:26 con más uso de CPU). Prueba propuesta: registrar el uso de CPU por proceso (`python`, `chrome`) en la próxima tanda.
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
Tarea 2 (reducción del ciclo). Un paso por commit; cada paso se mide con el protocolo de la sección 10. Orden del 02/11 (7 → 10 → 5 → 5b): **HECHO**. **Siguiente:** Ale decide P-003 y P-005 → paso 9 (10 min) con la configuración elegida.
| # | Paso | Estado |
|---|---|---|
| 1 | Commit del estado actual en la rama `wip-28e` | HECHO 31/10 (`368c20a`) |
| 2 | Rama `perf/ciclo-30hz` y `HILO_POR_MANO=False` (ver D-003; Ale confirma) | HECHO 31/10 (`9b2d30a`) |
| 3 | Cronómetros por línea en `[PERF]` para `to_numpy()`, `print` e `imshow`, sin cambiar comportamiento | HECHO 31/10 (`1764380`, `[PERF-LINEA]`) |
| 3b | Guardar `[PERF]` en `_perf.txt` y las latencias del navegador en `_latencias.csv` (D-006) | HECHO 31/10 (`e2fef0d`, `3151709`) |
| 4 | Línea base: 3 corridas de 3 min con la rutina fija (sección 10) | HECHO 31/10 (171408, 171755, 172123; sección 4b), **con un cliente de prueba de más y sin calentamiento**; se repite en el paso 10 |
| 5 | Color sin decodificar en el ciclo y sin ventana en sesiones de evaluación; volver a medir | MEDIDO. BGRA32 (`f453ac0`, 31/10): no cumple C1 ni C2. Sin ventana (`6b83b6c`) y decodificación en el hilo de manos (`47b8a3e`), 3 corridas cada una el 02/11 (4d): solo sin ventana + decodificación sostuvo ≥ 29.5 ciclos/s en las 3 rondas. Elegir configuración: P-003 y P-005 (decide Ale) |
| 5b | Explicar `mapeo` (3.6 ms real frente a 0.7 aislado): corrida con `sys.setswitchinterval(0.001)` y corrida sin hilo de manos (diagnóstico) | HECHO 02/11 (`66b9ebd`, `529e248`; 4d): `setswitchinterval` sin efecto; sin hilo de manos −0.6 ms; el resto sigue al estado del equipo (H6). Queda abierto qué consume la CPU (sección 11) |
| 6 | Decidir histéresis y EMA en milisegundos (P-001) | HECHO 02/11: D-010 (histéresis 250 ms, `d0331e8`; EMA sin cambios) |
| 7 | Enviar `lag_cam_ms` en el mensaje y guardar `latencia_llegada_ms` (= `latencia_ms + lag_cam_ms`) en `_latencias.csv`, sin cambiar columnas existentes ni comportamiento musical | HECHO 02/11 (`eb68590`); verificado contra el cálculo offline (≤ 0.05 ms, 4c) |
| 7b | Cierre y operación de las corridas: esperar el último lote de latencias al cerrar (`b98258b`), interruptores por línea de comandos (`1b69a33`, D-011), soltar el último frame del tracker antes de destruirlo (`6ed5c0a`) | HECHO 02/11. `6ed5c0a` falta verificarlo con la Kinect (próxima corrida con `--decod-hilo`) |
| 8 | Pipeline de 2 etapas (H5) solo si 5–11 no cumplen C1 | CONDICIONAL (con sin ventana + decodificación en el hilo C1 se cumplió en corridas de 3 min; falta el paso 9) |
| 9 | Corrida de 10 min y verificación de C1–C5 | PENDIENTE. Bloqueado por P-003/P-005. Registrar CPU por proceso (sección 10) |
| 10 | Repetir la línea base MJPG: 1 pestaña, calentamiento descartado, plan de energía de máximo rendimiento, 3 corridas de 3 min | HECHO 02/11 (133512, 133838, 134201; 4c). La comparación 1 vs 2 hilos de D-003 **no** se repitió |
| 11 | Método para medir (c) extremo a extremo (US23): micrófono o loopback, y latencia interna del SDK | PENDIENTE (decide Ale el método; no bloquea 7 ni 10) |
Fuera de este plan: `latencia_interna_SDK` `[POR COMPLETAR]`.

## 10. Protocolo de corrida (repetible)
1. Laptop enchufada, modo de energía de **máximo rendimiento** (obligatorio: en Equilibrado el ciclo empeora 6–9 ms, 4d), solo Chrome con **una sola pestaña** de `index.html` (ninguna otra pestaña ni navegador integrado de Code con la página abierta), misma distancia (de pie), misma luz y el mismo salón para toda la tanda. Antes de empezar, revisar en el Administrador de tareas que ningún otro proceso use la CPU de forma sostenida. Segunda terminal: `nvidia-smi --query-gpu=timestamp,clocks.sm,clocks.max.sm,temperature.gpu,power.draw,clocks_throttle_reasons.active --format=csv -l 1 -f sesiones\gpu_<tanda>.csv`. Tercera terminal (Símbolo del sistema como administrador; contadores localizados en español): `typeperf "\Información del procesador(_Total)\% de rendimiento del procesador" "\Información del procesador(_Total)\% de tiempo de procesador" -si 1 -o sesiones\cpu_<tanda>.csv`; propuesta para la próxima tanda: añadir el uso por proceso de `python` y `chrome` (H6). Arrancar ambos una vez y detenerlos con Ctrl+C al terminar la tanda.
1b. Una corrida de calentamiento de ≈ 1 min que se descarta (31/10: la 1ª corrida de la tanda MJPG salió ≈ 7 ms más lenta en todas las etapas). Filtro: si `[PERF-LINEA]` muestra `to_numpy` ≥ 8 ms/llamada, el equipo está lento (02/11: 144008 dio 9.4 ms); esperar, revisar procesos y repetir el calentamiento.
2. `python main.py cuda lite [--sin-ventana] [--decod-hilo] [--swi1ms] [--sin-manos]` (D-011); esperar 5 s (el navegador tarda hasta ≈ 5 s en reconectarse y esas filas faltan en `_latencias.csv`); rutina fija de 3 min: 30 s quieto, 60 s brazos arriba y abajo, 60 s baile amplio, 30 s abrir y cerrar manos con las dos manos visibles. No recargar la pestaña entre corridas.
3. `q` para cerrar (con `--sin-ventana`, **un** Ctrl+C en la consola) y esperar a "Kinect cerrada correctamente". Quedan en `sesiones/` el CSV de sesión, `_perf.txt` y `_latencias.csv`. Comprobar que las filas `continuo` de `_latencias.csv` ≈ filas del CSV de sesión (si son el doble, había 2 clientes: repetir). La configuración queda en el nombre (sufijo de `VERSION_MAIN`). No usar `Start-Transcript` (no graba la salida de Python).
4. 3 corridas por configuración, **intercaladas por rondas** (A B C, A B C, …) para que la deriva del equipo afecte a todas por igual; comparar dentro de cada ronda (02/11: Base varió 33.2 → 41.8 ms en 37 min). No cambiar código durante la tanda. No mezclar con pruebas de sonido.

## 11. Pendientes y huecos
- ~~Perfil de un ciclo real con cronómetros por línea (paso 3–4).~~ HECHO 31/10 (sección 4b).
- `[POR COMPLETAR]` latencia interna del SDK entre `system_timestamp` y la disponibilidad del capture. Con BGRA32 `lag_cam_ms` sube ≈ 22 ms; falta saber qué parte es decodificación y qué parte es espera dentro del SDK.
- `[POR COMPLETAR]` latencia real hasta el sonido (c) (US23, paso 11).
- `[POR COMPLETAR]` origen exacto de las cifras RNF01 p95 78–83 y máx 112–115. Candidato: (b) (sección 0.2). Ale no lo recuerda; no se puede confirmar.
- `[POR COMPLETAR]` significado del bit `0x400` en las razones de reloj de la GPU.
- ~~`[POR COMPLETAR]` causa de los 3.6 ms de `mapeo` (paso 5b).~~ Diagnóstico HECHO 02/11 (4d): no es el intervalo del GIL; el hilo de manos explica ≈ 0.6 ms; el resto acompaña al estado del equipo.
- `[POR COMPLETAR]` qué consumió CPU durante la tanda del 02/11 (Base 33.2 → 41.8 ms, % de tiempo de CPU 34.8 → 46.6 %; H6). Falta el uso por proceso.
- `[POR COMPLETAR]` verificar con la Kinect que `6ed5c0a` elimina el "access violation" al salir (visto solo con `--decod-hilo`, 02/11).
- Riesgo para HU0008-1 con decodificación en el hilo: trabajo de manos 26–31 ms y edad p95 71–109 ms (4d). Medirlo en la corrida de 10 min.
- Pendiente de datos (no medido): confianza de rodillas y tobillos en el CSV. Ale observó el 31/10 más movimiento falso de piernas al subir los brazos; en las sesiones 164334/164633 la mediana de la velocidad de rodilla es 35–111 °/s con los hombros a 45–135° (11–16 °/s quieto con los brazos abajo), y eso sube el tempo.
- Garantía FIFO del SDK al vaciar la cola: INFERIDA; las cifras de `lag_cam_ms` la respaldan.