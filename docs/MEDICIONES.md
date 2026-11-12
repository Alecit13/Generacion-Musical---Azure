# MEDICIONES — línea base, hipótesis y plan (corte: 12/11/2026; mediciones hasta el 12/11)

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
- **FUERA DE PROTOCOLO (D-018, 05/11): las 3 finales tienen evento 506 en la segunda mitad.** Windows entró en espera moderna (Kernel-Power 506) 5.0 s después del hueco de ≈ 290 s y salió (507) al cerrar cada corrida (sección 4g). La corrida quieta 170136 también lo tiene. Los datos se conservan sin cambios; no cuentan para cerrar el paso 9. Las cifras de esta sección siguen siendo válidas como descripción de lo que pasó.
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
- **Caída a los ≈ 290 s (causa `[POR COMPLETAR]`).** Las 4 corridas de ≥ 5 min, **incluida la quieta**, tienen la ventana #144 con 20.7–21.4 ciclos/s, `cap_update` 23–25 ms y 73–76 lecturas de color en 60 ciclos (13–16 capturas incompletas), y un hueco de filas de 832–928 ms a los 288.7–290.0 s de la primera fila. Con 4e son **7 de 7** corridas de ≥ 5 min. Hipótesis: (i) baile: **no es causa única**, porque aparece también en la corrida quieta, sin rutina; (ii) persona detrás: abierta; (iii) evento de la cámara o del SDK: abierta. Prueba independiente en el plan (paso 12). Descripción del hueco (INFERIDO a partir de MEDIDO; no se usa como evidencia sobre (ii)): en las ventanas 140–147 hay tantos ciclos `[PERF]` como filas del CSV (≈ 0 ciclos sin cuerpo; igual al mover el ancla ± 1.5 s); el hueco son capturas incompletas y espera de la cámara. **Actualizado en 4g (05/11):** el hueco aparece también sin `main.py` (prueba A) y coincide en 7 de 7 corridas con la entrada de Windows en espera moderna.
- **Rodillas** (solo como dato; sin conclusión sobre la ropa hasta la prueba con shorts): corrida quieta, desviación estándar del ángulo de rodilla izq / der 7.7° / 5.2° (por minuto 4.7–8.6° / 3.6–7.7°), hombros 0.9–3.0°, `vel_rodilla` mediana 65.5 °/s (p95 158). Tramos quietos de la rutina bien ubicados (hombros ≤ 0.8°): 0.6–1.9° / 0.9–1.4°, `vel_rodilla` mediana 8–21 °/s. Tramos mal ubicados por tiempo (hombros 1.7–9.9°): 171221 a los 185–205 y 365–385 s, y 173544 a los 365–385 s.

## 4g. 05/11: prueba A de cámara, cruce con la espera moderna de Windows y corrida con pantalla en "Nunca" (MEDIDO)
Fuentes en `sesiones/`:
- MKV: `camara_A1.mkv`, `camara_A2.mkv`, `camara_A3.mkv` (en `.gitignore`, no versionados).
- Consola de A3: `consola_camara_A3.txt` (archivo local, no versionado por decisión de Ale). Las consolas de A1 y A2 aún no están en `sesiones/` `[POR COMPLETAR]`: los 10 mensajes de A1 y la consola limpia de A2 son dichos por Ale.
- Corrida: `sesion_20261105_<hora>_mjpg-d013-2026-11-04_cuda-lite.*` (código `9ecf383`, configuración por defecto).
- Registro de eventos del sistema de Windows: Kernel-Power 506/507 y servicio de hora (Time-Service 37/134), leído por Code con `Get-WinEvent`.

Análisis con scripts de solo lectura de Code (fuera del repositorio). Sobre los MKV, la reproducción de `pykinect_azure` lee por captura si hay color, profundidad e IR y su marca de tiempo del dispositivo, y recorre la IMU. Sobre la corrida, los mismos métodos de 4f; el script reproduce las cifras de 4f para 171221, 172514 y 173544 con diferencias ≤ 0.1 ms.

**Condiciones.**
- Ale quieto delante de la cámara, sin `main.py` ni Code abiertos durante las grabaciones; puerto USB directo al laptop, sin hub.
- No hubo registros de GPU, CPU ni procesos el 05/11.
- Comando de las grabaciones: `k4arecorder -c 720p -d NFOV_UNBINNED -r 30 --imu ON -l 360`.
- Configuración guardada en los 3 MKV (MEDIDO): `color_format=0` (MJPG), `color_resolution=1` (720p), `depth_mode=2` (NFOV_UNBINNED), `camera_fps=2` (30), `wired_sync_mode=0` (Standalone), `depth_delay_off_color_usec=0`, IMU e IR grabados. Son los mismos modos que `main.py` (líneas 196–200).
- Tamaño de cada MKV: 17.7–17.9 GB (≈ 3 GB/min; incluye el IR).

### 4g.1 Prueba A: A1, A2 y A3
| | A1 (pantalla en 5 min) | A2 (pantalla en "Nunca") | A3 (pantalla en 5 min, control) |
|---|---|---|---|
| Grabación (creación → última escritura del MKV) | 16:37:53 → 16:43:55 | 16:50:31 → 16:56:32 | 17:55:58 → 18:02:00 |
| Capturas · con color · con profundidad | 10 790 · 10 790 · 10 776 | 10 799 · 10 797 · 10 799 | 10 790 · 10 789 · 10 778 |
| Color: frames frente a 30 × 359.867 s + 1 = 10 797 | faltan 7 | faltan 0 | faltan 8 |
| Profundidad: frames que faltan | 21 | 0 | 20 |
| Saltos de color > 50 ms (marca del dispositivo) | 233.3 ms (fin 294.934 s) y 66.7 ms (fin 295.167 s) | ninguno (máx 33.345 ms) | 300.0 ms (fin 295.234 s) |
| Saltos de profundidad > 50 ms | 66.7, 100.0 y **633.3 ms** (294.834 → 295.467 s) | ninguno (máx 33.378 ms) | 66.7, 100.0 y **600.0 ms** (295.167 → 295.767 s) |
| Hueco de la IMU (mediana entre muestras 0.611 ms) | **351 ms** (294.650 → 295.001 s) | ninguno (máx 0.623 ms) | **336 ms** (294.972 → 295.308 s) |
| Capturas incompletas durante el evento | 14 solo color (marca 294.667–295.434 s) | ninguna (2 solo profundidad al arrancar) | 12 solo color (marca 295.000–295.734 s); 1 solo profundidad al arrancar |
| Frames de color entre 270 y 310 s (de ≈ 1200) | 1193 | 1200 | 1192 |
| Mensajes `capturesync_drop … type:Color` en la consola | 10, marcas 294.600–294.900 s (dicho por Ale) | ninguno (dicho por Ale) | 10, marcas 294.900 188–295.200 188 µs; el primero a las 18:00:54.181 |
| Kernel-Power 506 (entra en espera moderna) | 16:42:53.819 | ninguno | 18:00:58.688 |
| Kernel-Power 507 (sale) | 16:44:14.309 | — | 18:02:43.166 |
| 506 desde la creación del MKV | +300.42 s | — | +300.27 s (+300.61 s desde la creación de la consola, es decir, desde que se lanzó el comando) |
- **El corte de ≈ 295 s del reloj del dispositivo existe sin `main.py`, sin tracker y sin Python** (A1 y A3), y no aparece con la pantalla en "Nunca" (A2).
- En el corte se pierden a la vez profundidad (0.60–0.63 s), color (0.23–0.30 s) e IMU (0.34–0.35 s). INFERIDO: se interrumpe todo el flujo de la Kinect hacia el PC, no una sola cámara.
- **`capturesync_drop`.** La consola de A3 dice `capturesync.c (142): replace_sample(). capturesync_drop, releasing capture early due to full queue … type:Color`. El mismo texto está en `k4a.dll` del SDK 1.4.1 (búsqueda en el binario), la biblioteca que usa `main.py`.
  - INFERIDO del texto y de los datos: el sincronizador del SDK, que junta color y profundidad en una captura, soltó color sin su pareja de profundidad mientras faltaba la profundidad.
  - Esas son las capturas "solo color" que `main.py` cuenta como incompletas y se salta.
  - En A3 los 10 mensajes (294.900–295.200 s) no coinciden uno a uno con las 12 capturas solo color del MKV (295.000–295.734 s). Por qué el SDK registra solo esos 10 `[POR COMPLETAR]`.
- **¿Es `k4arecorder` equivalente a `main.py`?** Los modos de cámara son los mismos (MEDIDO). `synchronized_images_only` no queda en la configuración del MKV. INFERIDO: se comportó como `False`, igual que `main.py`, porque el MKV contiene capturas solo color. La carga del equipo no es la misma: no hay GPU, MediaPipe ni navegador, pero sí escritura a disco de ≈ 50 MB/s.
- **Límites.** El MKV no guarda la hora de llegada al PC. A2 y A3 son 1 grabación por condición. Que A2 tuviera además la suspensión en "Nunca" no está confirmado. Hoy (05/11, después de A2) `powercfg` da pantalla y suspensión CA/CC = 0 (MEDIDO por Code).

### 4g.2 Cruce del hueco de las corridas con la espera moderna de Windows
Hora del hueco = hora de pared (`timestamp` del CSV de sesión) de la última fila antes del mayor salto de `t_cap_ms`. Eventos 506/507 del registro de Windows.

| Corrida | Hueco | Kernel-Power 506 | 506 − hueco | Última fila → 507 |
|---|---|---|---|---|
| 144401 | 14:48:50.714 (863 ms) | 14:48:55.723 | 5.01 s | 14:54:05 → 14:54:07.704 |
| 153328 | 15:38:18.850 (944 ms) | 15:38:23.807 | 4.96 s | 15:43:30 → 15:43:32.736 |
| 154420 | 15:49:09.504 (944 ms) | 15:49:14.554 | 5.05 s | 15:54:24 → 15:54:25.412 |
| 170136 (quieta) | 17:06:25.122 (910 ms) | 17:06:30.128 | 5.01 s | 17:09:41 → 17:09:43.061 |
| 171221 | 17:17:11.883 (896 ms) | 17:17:16.916 | 5.03 s | 17:22:24 → 17:22:27.092 |
| 172514 | 17:30:03.569 (832 ms) | 17:30:08.577 | 5.01 s | 17:35:21 → 17:35:22.613 |
| 173544 | 17:40:34.224 (928 ms) | 17:40:39.264 | 5.04 s | 17:45:48 → 17:45:50.133 |
- **En 7 de 7 corridas el hueco empieza 4.96–5.05 s antes de que Windows entre en espera moderna.** La salida (507) llega 1–3 s después de la última fila, cuando Ale vuelve a tocar el equipo para cerrar. Toda la segunda mitad de esas corridas transcurrió con Windows en espera moderna.
- En A3, del primer `capturesync_drop` (18:00:54.181) al 506 pasan 4.5 s. Son relojes y marcas distintas a las de `main.py`; compatible con lo anterior.
- El hueco cae a 289.1–290.9 s de la hora `inicio` de la cabecera de `_perf.txt` en las 7 corridas, y el 506 a ≈ 300 s de lanzar el comando en A1 y A3. INFERIDO: el apagado de pantalla tras 300 s de inactividad (`VIDEOIDLE` CA = `0x12c`, Ale) lleva a Windows a la espera moderna. El apagado de pantalla en sí no queda registrado.
- **Escalón (4f) y espera moderna.** CPU, GPU y procesos del 04/11 antes y después del hueco (`cpu_paso9c.csv`, `gpu_paso9c.csv`, `procesos_paso9c.csv`; 4 corridas de la tarde):
  - % de rendimiento de la CPU: 202–205 → 201–210.
  - % de tiempo de la CPU: baja de 1.2 a 6.1 puntos.
  - GPU: sin cambio en reloj (1755–1762 MHz) ni potencia.
  - `python`: de −11 a +4 % de un núcleo.
  - `dwm` baja a ≈ 2 % en 2 de 4 corridas.
  - INFERIDO: el escalón está ligado al periodo de espera moderna; el mecanismo `[POR COMPLETAR]`.
- **Mecanismo `[POR COMPLETAR]`:** por qué la transición corta el flujo USB de la Kinect y qué hace Windows en los ≈ 5 s anteriores al 506.

### 4g.3 Corrida con pantalla en "Nunca" (171135), frente a las finales del 04/11
- **Condiciones (Ale):** pantalla en "Nunca"; pantalón recto (en las finales del 04/11, ancho); Edge; una sola pestaña; VS Code cerrado; configuración por defecto (D-012, D-015).
- **Corridas:** 170957 = arranque fallido (67 filas); 171013 = calentamiento (≈ 1 min, descartado); **171135 = corrida de 424.4 s**.
- **Validez:** un solo cliente, 0 filas `continuo` duplicadas. Faltan las 44 primeras (1.6 s, reconexión al arrancar) y ninguna después; la última fila llegó. Kernel-Power 506: ninguno entre 17:11 y 17:19.
- **Validez del reloj: NO.** `transporte_ms` pasó de 1.97 ms (primeros 30 s) a −36.71 ms (últimos 30 s), por escalones; mínimo −37.4 ms. En 171013 ya derivaba de 0.52 a −2.97 ms. En las 6 corridas del 04/11 revisadas (153328, 154420, 170136 y las 3 finales) se mantuvo en 0.0–0.2 ms al principio y al final.
  - Windows sincronizó la hora con `time.windows.com` el 05/11 a las 16:26:34 (Time-Service 37), después de fallar por DNS el 04/11 a las 21:58 y el 05/11 a las 15:43 (Time-Service 134).
  - INFERIDO: Windows corrigió la hora poco a poco durante la corrida. `Date.now()` siguió esa corrección y Python no, porque `ahora_ms()` ancla `time.time()` una vez al arrancar y luego avanza con `perf_counter`.
  - Consecuencia: **(a) y (b) de 171135 tal como se guardaron (media 5.4 y 14.2 ms) no son válidas** y no se usan para C3 (regla de validez D-019).
  - Como referencia INFERIDA, no como (b), se puede calcular (`t_env − t_cap`) + `lag_cam_ms`, que usa solo relojes de Python y omite el transporte (≈ 0.1 ms el 04/11).

| Métrica (ms salvo indicación) | **171135** ("Nunca", 424 s) | 171221 | 172514 | 173544 |
|---|---|---|---|---|
| C1: ventanas ≥ 29.5, sin #0 · con #0 | **211/211 · 211/212** | 297/301 · 297/302 | 302/303 · 302/304 | 299/302 · 299/303 |
| Ventana #144: ciclos/s (lecturas de color en 60 ciclos) | 30.0 (60) | 20.9 (75) | 21.4 (73) | 20.7 (76) |
| Lecturas de color por ventana, máx | 60 | 75 | 73 | 76 |
| Huecos de filas > 200 ms | **ninguno** | 896 ms a 290.2 s | 832 ms a 289.2 s | 928 ms a 289.5 s |
| Ciclos/s medio · `cap_update` · `tracker` | 29.98 · 9.9 · 21.0 | 29.94 · 9.7 · 21.0 | 29.95 · 9.8 · 21.0 | 29.95 · 10.0 · 20.9 |
| `mapeo` cada 30 ventanas | 1.0 → 1.4 (≈ 4–5 min) → 2.0 (último tramo) | 1.0 → 2.0 a los ≈ 5 min | 1.0 → 2.0 | 1.0 → 2.0 |
| Periodo media / p95 · % > 33.3 ms | 33.4 / 46.5 · **18.0** | 33.4 / 47.0 · 13.9 | 33.4 / 47.0 · 14.2 | 33.4 / 47.0 · 14.9 |
| `lag_cam_ms` media / p95 / máx · p95 por minuto | 8.8 / 21.1 / 38.4 · 20.9–21.2 | 8.3 / 20.0 / 51.2 · 19.6–20.5 | 8.3 / 20.2 / 43.0 · 19.8–20.7 | 8.8 / 20.6 / 50.1 · 20.0–21.0 |
| `lag_cam_ms` media 10–285 s → ≥ 295 s | 8.8 → 8.8 | 8.5 → 8.1 | 8.6 → 8.0 | 9.1 → 8.6 |
| (b) guardada media / p95 / máx | **no válida (reloj)** | 31.7 / 44.1 / 75.1 | 31.6 / 44.2 / 79.2 | 31.9 / 44.3 / 72.2 |
| Referencia INFERIDA (`t_env − t_cap`) + `lag_cam_ms` (n > 100) | 31.9 / 44.8 / 72.0 (0) | 31.6 / 44.3 / 75.5 (0) | 31.5 / 44.3 / 78.9 (0) | 31.9 / 44.5 / 72.1 (0) |
| `t_env − t_cap` media / p95 / máx | 23.1 / 24.9 / 57.9 | 23.3 / 26.2 / 63.4 | 23.2 / 26.1 / 63.5 | 23.0 / 25.7 / 65.6 |
| `transporte_ms` primeros 30 s → últimos 30 s | 1.97 → **−36.71** | 0.06 → 0.01 | 0.07 → 0.04 | 0.08 → −0.01 |
| `lat_tick_ms` media / p95 / máx (% > 250) | 40.1 / 54.7 / 75.8 (0) | 40.1 / 55.7 / 77.2 (0) | 39.8 / 55.0 / 72.6 (0) | 40.3 / 55.5 / 70.1 (0) |
| Trabajos/s · por tercios | 29.85 · 29.9 → 29.8 → 29.9 | 28.49 · 29.8 → 28.4 → 27.3 | 28.12 · 29.9 → 28.2 → 26.3 | 28.71 · 29.8 → 28.5 → 27.8 |
| Trabajos/s #1–#143 → #145 en adelante | **29.84 → 29.86** | 29.73 → 27.41 | 29.86 → 26.58 | 29.76 → 27.80 |
| Cambios de apertura por mano/s (izq / der) | 9.67 / 9.83 | 10.35 / 10.26 | 10.07 / 9.87 | 10.52 / 10.31 |
| Edad manos p95 · % ciclos con 2 manos | 47.8 · 94.0 | 79.1 · 87.5 | 65.1 · 92.1 | 64.7 · 92.7 |
- **Sin espera moderna no hay hueco, ni ventana baja, ni escalón** de trabajos/s o `lag_cam_ms` (MEDIDO, n = 1 corrida de 7 min). Tampoco aparecieron ventanas de 29.1–29.3 ciclos/s. El % de ciclos > 33.3 ms fue mayor (18.0 frente a 13.9–14.9). `mapeo` sigue creciendo, más despacio: no depende de la espera moderna.
- **Criterios (indicativo; no es corrida de 10 min ni pasa la validez del reloj):** C1 211/211 sin #0 y `cap_update` 9.9 ms > 0. C2 p95 21.1 ≤ 4c (27.1–35.9), sin crecimiento por minuto. C3 no evaluable con (b). C4 0 % > 250 ms. C5 sin cambios (D-010, D-012, D-015).
- **Afecta a:** HU0007-1 (C1), HU0008-1 (escalón de trabajos/s) y HU0023-1 (C3).
- **Rodillas** (solo como dato; no se concluye sobre la ropa). Tramos quietos elegidos a partir de los datos (ventanas de 20 s con los dos hombros con desviación ≤ 0.8°, misma regla para todas):
  - 171135 (pantalón recto): rodilla izq / der 0.9–1.7° / 0.3–1.3°, `vel_rodilla` mediana 12–21 °/s.
  - 171221, 172514 y 173544 (pantalón ancho): 0.5–2.2° / 0.9–5.1°, 6–20 °/s.
  - Los rangos se superponen.
  - Además de la ropa cambiaron: el día, la pantalla ("Nunca"), la hora del sistema y la rutina (`[POR COMPLETAR]` la de 171135). Salón y luz no anotados. El navegador fue Edge en ambos casos.

## 4h. 07/11: pruebas funcionales, cambios aprobados y tanda limpia del paso 14 (MEDIDO)
Fuentes en `sesiones/`: `sesion_20261107_<hora>_<VERSION_MAIN>_cuda-lite.*`; GPU, CPU y CPU por proceso en `gpu_paso14.csv`, `cpu_paso14.csv`, `procesos_paso14.csv`. Análisis con scripts de solo lectura de Code (fuera del repositorio). Ropa: **short y polo blanco** en todas las corridas del día (Ale). Navegador: Edge, una pestaña.
**Preparación (MEDIDO por comando):** `ActiveOverlayAcPowerScheme = ded574b5-…c238`; `VIDEOIDLE` y `STANDBYIDLE` CA/CC = 0; con corriente (`BatteryStatus = 2`); VS Code cerrado. Reloj: en la red `upc.edu.pe` NTP (UDP 123) no responde (`w32tm /stripchart`: error `0x800705B4` hacia `time.windows.com` y `pool.ntp.org`); `w32tm /resync` funcionó con el hotspot del celular (sincronización 07/11 14:54:27) y la tanda se corrió de vuelta en `upc.edu.pe`, donde Windows no puede corregir la hora.

### 4h.1 Fase 2: pruebas funcionales sin cambiar código (commit `754468b`, `VERSION_MAIN = mjpg-d013-2026-11-04`)
| Prueba | Archivo | Resultado |
|---|---|---|
| HU0014-2 (sin clic no suena) | 150233 | 765 filas de sesión (25.6 s) antes del clic y 0 filas `continuo`. Ale no oyó sonido |
| HU0014-1 (sin errores de inicio) | 150233 | Consola de Edge sin errores (dicho por Ale; no guardada) |
| HU0010-2 caso A (reconecta ≤ 2 s) | 150413 | 1ª fila `continuo` **2.09 s** después de la 1ª fila de sesión (n = 1): **no cumple por poco**. INFERIDO: la página reintenta 2000 ms después de cada fallo (`index.html`) |
| HU0010-2 caso B (pestaña cerrada) | 150413 | 43.0 s sin cliente: 1247 filas de sesión (29.0/s), sin hueco > 0.5 s; reconecta al reabrir: **cumple** |
| HU0007-2 | 151513, 152259; con ventana 151310, 151909 | Articulaciones 8, 9, 10, 15, 16, 17 (mano, punta, pulgar) NONE en el **100 %** de las filas y el resto sigue a 30 filas/s. Piernas **nunca** NONE (0 filas), también con la rodilla tapada. Fuera del encuadre se pierde el cuerpo entero (huecos de 7.2, 8.1 y 17.8 s en las corridas con ventana). INFERIDO: el SDK predice la pierna con confianza LOW y `CONF_MIN_ARTICULACION = 1` la cuenta como disponible; Ale vio los puntos de una pierna "juntarse" con la otra |
| Manos 2d(i): una abierta (der 0.045) y otra en puño (izq 0.024), 58 s | 151513 | `apertura01` cambia 16.8 veces/s, **14.6 saltos > 0.3 por segundo** (salto medio 0.48). Con las dos abiertas: 5 saltos en 13 s |
| Manos 2d(ii): manos atrás | 151513 | `apertura01` fija en 0.254 durante 9.0 s y en 0.0 durante 4.5 s (la columna `apertura` sí vacía) |
| HU0016-2 / HU0018-2 (saturación) | 152259 | `tempo` e `intensidad` en [0, 1], llegan a los dos topes (tempo 7.2 % de filas en 0 y 5.7 % en 1; intensidad 8.6 % y 13.0 %): **cumple** |
| HU0015-2 | 151513, 152259 | 72 y 108 cambios de zona en 3 min; **6/72 y 85/108** sin 250 ms continuos dentro de la zona nueva (el paso por "medio" sumaba para "agudo"; los relámpagos cambiaban la zona) |

### 4h.2 Fase 3: cambios aprobados por Ale (uno por commit; pruebas en `pruebas_unitarias.py`, 20/20 OK)
| Cambio | Commit | Prueba sin dispositivo | Prueba en vivo |
|---|---|---|---|
| 1 HU0008-2: sin mano vigente en 0.5 s, `apertura01` vacía (JSON `null`) y el timbre vuelve a 0.5 (1650 Hz) | `d01499a` | Vencimiento con reloj simulado (6 pruebas) | 155040: 545/545 filas sin mano con `apertura01` vacía |
| 2 HU0019-2: máx. 2 notas iguales seguidas (por nombre) | `170680a` | Racha ≤ 2 en 100 000 sorteos (λ 1, 0.5, 0.05); el código anterior daba hasta 4 con λ = 1 | 160759: racha máx 2 |
| 3 HU0021-1 / HU0022-1: `--seed=N`; columnas `nota_id`, `lam_sorteo` (λ exacto), `semilla`, `version`, `commit` | `534177e` | Misma semilla = misma secuencia; con λ redondeado a 3 decimales cambian 39 de 20 000 sorteos | 160759 (`--seed=123`): 94/94 notas reconstruidas |
| 6 HU0017-1 / D-024: `apertura01` desde el promedio de las manos vigentes (`TimbrePorManos`) | `080f36f` | Alternancia 0.02/0.05 → `apertura01` constante | 162433: **0.98 saltos > 0.3 por segundo** (antes 14.6), ninguno por pérdida de mano |
| `RANGO_MIN_APERTURA` 0.05 → 0.015 (HU0017-1, US27) | `46aced4` | — | 162433: dos abiertas 0.97 (p5 0.92), dos en puño 0.06 (p95 0.15); antes ≤ ≈ 0.58 |
| 5 HU0015-2: 250 ms continuos dentro de la misma candidata (`zona.zona_desde_registro`) | `3686feb` | 6 pruebas; offline: 72 → 66 y 108 → 82 cambios (la regla vieja reproduce la columna `zona` en 99.8–100 %) | 162433: 0/23 cambios con < 250 ms dentro |
- Datos para `RANGO_MIN_APERTURA` (151513, 152259, 155040, 160759): abierta ≈ 0.048, puño ≈ 0.021 (ancho ≈ 0.027); ruido en reposo p95 − p5 0.001–0.006 (resolución del CSV 0.001). En 155040 la apertura fue 0.038–0.064: INFERIDO, Ale más cerca de la cámara (la apertura está en coordenadas de la imagen completa).

### 4h.3 Fase 4: tanda limpia del paso 14 (3 × 10 min), commit **`3686feb`** (US22; cabecera sin `-sucio`)
`VERSION_MAIN = mjpg-cambios-2026-11-07`, configuración por defecto (sin ventana, decodificación en el hilo). Calentamiento 163444 (descartado). Rutina de 3 min repetida (30 s quieto, brazos, piernas con algo de brazos, 30 s manos). **Validez:** Kernel-Power 506/507: ninguno desde las 16:30; Time-Service sin eventos; un solo cliente (0 duplicadas); filas que faltan solo al arrancar; la última fila llegó en las 3.
| Métrica (ms salvo indicación) | **163615** | **165040** | **170224** |
|---|---|---|---|
| Semilla | 275989368 | 1394752313 | 611563737 |
| Reloj: Δ `transporte_ms` (últimos − primeros 30 s) | −0.20 | −0.13 | −0.10 |
| Faltan al arrancar | 55 | 86 | 15 |
| Ciclos/s media (sin #0) · ventana mín. · ventana #0 | 29.98 · 29.5 · 25.3 | 29.99 · 29.5 · 25.5 | 29.99 · 29.5 · 25.2 |
| C1: ventanas ≥ 29.5 sin #0 · con #0 | 299/299 · 299/300 | 299/299 · 299/300 | 299/299 · 299/300 |
| D-023 (media ≥ 29.5 y ninguna < 29.0) | cumple | cumple | cumple |
| `cap_update` · `tracker` · `mapeo` · `salida` | 10.4 · 20.1 · 1.0 · 0.9 | 10.4 · 20.2 · 1.1 · 0.9 | 10.4 · 20.1 · 1.0 · 0.9 |
| Periodo media / p95 · % > 33.3 ms | 33.4 / 47.8 · 8.7 | 33.4 / 47.8 · 8.6 | 33.4 / 47.8 · 8.6 |
| `lag_cam_ms` media / p95 / máx · p95 por minuto | 5.4 / 17.0 / 48.7 · 16.9–17.0 | 5.4 / 16.9 / 48.9 · 16.8–17.0 | 5.3 / 16.9 / 34.5 · 16.8–17.0 |
| (a) media / p95 / máx | 22.6 / 24.4 / 59.4 | 22.7 / 24.6 / 57.7 | 22.7 / 24.5 / 55.2 |
| **(b) RNF01** media / p95 / máx (n > 100) | 28.0 / 40.4 / 74.5 (0) | 28.1 / 39.8 / 71.8 (0) | 27.9 / 40.0 / 61.0 (0) |
| `lat_tick_ms` media / p95 / máx (% > 250) | 39.5 / 54.3 / 70.6 (0) | 39.0 / 54.5 / 69.9 (0) | 39.0 / 54.6 / 69.3 (0) |
| Trabajos/s del hilo de manos · por tercio | 29.87 · 29.9 → 29.9 → 29.9 | 29.86 · 29.9 → 29.8 → 29.9 | 29.94 · 29.9 → 29.9 → 30.0 |
| Cambios de apertura por mano/s (izq / der) | 9.06 / 8.94 | 8.67 / 8.23 | 8.66 / 8.51 |
| Trabajo del hilo · `decod_hilo` | 23.1 · 4.83 | 22.9 · 4.78 | 22.7 · 4.73 |
| Edad manos p95 · % ciclos con 2 manos · % filas sin mano | 95.8 · 81.6 · 0.2 | 79.8 · 78.5 · 0.1 | 79.9 · 81.7 · 0.1 |
| Huecos de filas > 0.5 s | ninguno | ninguno | ninguno |
| Notas reconstruidas con la semilla · racha máx | 954/954 · 2 | 863/863 · 2 | 878/878 · 2 |
| Cambios de zona · con < 250 ms dentro de la nueva | 194 · 3 | 208 · 3 | 201 · 0 |
| CPU % rendimiento · % tiempo (medianas) | 194 · 21.9 | 193 · 21.7 | 193 · 21.5 |
- GPU: SM mediana 1762 MHz, temperatura máx 68 °C (`gpu_paso14.csv`).
- **Criterios (CLAUDE.md sección 7), en las 3:** **C1 cumple** (299/299 ventanas ≥ 29.5 sin #0, D-016; `cap_update` 10.4 ms > 0; % de ciclos > 33.3 ms: 8.6–8.7). **C2 cumple** (p95 16.9–17.0 ≤ línea base 4c 27.1–35.9; plano por minuto). **C3 cumple** ((b) media, p95 y máx mejores que 4c; 0 muestras > 100 ms, HU0023-1). **C4 cumple** (0 % > 250 ms). **C5:** cambios aprobados por Ale el 07/11 (D-025 a D-030, borrador).
- **Sin escalón ni ralentización:** trabajos/s planos por tercio y `tracker` 20.1–20.2 ms en las 3 (reserva (2) de D-015: sin la espera moderna, la bajada no aparece).
- Los 6 cambios de zona "con < 250 ms" son INFERIDO artefacto del redondeo: en los 6, la fila del borde se lee exactamente 0.660 o 0.330 en el CSV (3 decimales); si esa fila ya era candidata nueva, el tiempo dentro es 256–273 ms.
- **Procesos ajenos durante la tanda** (`procesos_paso14.csv`, media en las muestras en que aparecen, % de un núcleo): `svchost#95` 151–443, `mousocoreworker` 27–65 (orquestador de Windows Update), `officeclicktorun` 67 y `sdxhelper` 43–95 (actualizaciones de Office). Media sobre todas las muestras de la tanda: `python` 135, `system` 24, el resto ≤ 7. No se vio efecto en el ciclo (INFERIDO).
- **Evento externo (Ale):** en los primeros minutos de 170224 la compañera apareció detrás. MEDIDO: entre 104.8 y 107 s los ángulos saltan de forma no humana (hombro 6° → 131° → 29° → 131° en 0.2 s; 10+ ciclos con ≥ 3 ángulos que saltan > 40°, frente a 1–2 sueltos en las otras corridas). INFERIDO: cambio de cuerpo o confusión del tracker por la segunda persona; el CSV no guarda el número de cuerpos. Sin efecto en C1–C4.

### 4h.4 Hallazgos `[POR REGISTRAR]` (sin resolver; cambian comportamiento musical o criterio, decide Ale)
- **Normalización adaptativa de 20 s** (`NORM_VENTANA_S`): un estado sostenido pasa a ser el "nuevo rango". Tempo lento y rápido casi iguales (0.38 frente a 0.35 con `vel_rodilla` 93 frente a 192 °/s, 152259); brazos horizontales salen "grave" después de tenerlos arriba (152259) o "agudo" si antes estaban abajo (162433); una mano abierta y otra cerrada sostenidas dan `apertura01` ≈ 0.10 (162433). Afecta a la redacción de HU0015-1, HU0016-1 y HU0017-1.
- **Parpadeo de zona cerca del umbral** estando quieto (grave ↔ medio cada 0.3–1 s, 152259 26.8–30.3 s): la histéresis de tiempo no lo evita; haría falta una banda muerta en `registro01`.
- **Apertura dependiente de la distancia** (coordenadas de la imagen completa): dividir por el tamaño de la palma en `calcular_apertura` la haría independiente.
- **HU0010-2 caso A:** 2.09 s (n = 1); bajar el reintento de `index.html` a 500 ms sería un cambio no aprobado.
- **Articulaciones de mano del Kinect NONE en el 100 %** de las filas el 07/11 (antes ≈ 53 %, ESTADO_ACTUAL 26–28/10). Causa desconocida.
- **Actualizaciones de apertura por mano: 8.2–9.1/s** en la tanda (04/11: 9.9–10.5). D-024 acepta "≈ 10": falta que Ale diga si 8.2–9.1 entra.
- **Rodillas con short** (misma regla que 4g.3: ventanas de 20 s con los dos hombros con desviación ≤ 0.8°). Tanda del 07/11 (short): 4 ventanas, desviación de rodilla izq / der 0.2° / 0.1–0.2°, `vel_rodilla` mediana 0–5 °/s. Finales del 04/11 (pantalón ancho): 7 ventanas, 0.5–2.2° / 0.9–1.6°, 6–18 °/s. INFERIDO: compatible con que el pantalón ancho empeore las rodillas; n pequeño y cambiaron también el día, la espera moderna (04/11) y los cambios de código (ninguno toca las piernas).

### 4h.5 Después de la tanda: análisis offline, cambios 4, 7 y 7b, piernas y corrida de confirmación (MEDIDO salvo indicación)
**Registro de qué código midió qué:** la tanda 3 × 10 min del paso 14 (4h.3) fue sobre **`3686feb`**; la corrida de confirmación de 10 min fue sobre **`30ccbf7`** (commit final del 07/11, cabecera sin `-sucio`).

**Por qué 29.9 trabajos/s dan 8.2–9.1 cambios de apertura por mano/s** (tanda 163615, 165040, 170224; `[ROI]` y `[PERF]` de `_perf.txt`, columnas `apertura_izq`/`apertura_der` del CSV):
| Paso | Valor |
|---|---|
| Trabajos/s del hilo | 29.86–29.94 |
| Por mano (`ALTERNAR_MANOS=True`: una mano por trabajo) | 14.9 |
| Aciertos de MediaPipe (`[ROI]`, recuadro desde la muñeca) | 87.2–88.8 % → 13.0–13.3 detecciones/s por mano |
| Cambios de valor en el CSV | 8.2–9.1/s; el 54–58 % de esos cambios es de 0.001 (la resolución del CSV) |
| Cambios por mano/s por fase (aprox. por tiempo) | quieto 7.3–8.7, brazos 9.4–9.6, piernas 9.2–9.4, manos 6.8–8.6 |
- INFERIDO: ≈ 1/3 de las detecciones nuevas repite el valor redondeado y no cuenta como "cambio"; la métrica de cambios subestima las actualizaciones (≈ 13/s por mano). Medirlas directo requiere guardar por mano el instante de su último dato (no aprobado). **HU0008-1 queda parcial; D-024 sigue abierta.**

**HU0019-3** (tanda, 2695 sorteos, código `3686feb`; teoría por sorteo con la racha real):
| λ | n | Repite obs/teo | 1 paso | 2 pasos | 3 pasos | χ² (3 gl) |
|---|---|---|---|---|---|---|
| 0.05–0.2 | 457 | 0.2 / 0.3 % | 96.7 / 96.4 % | 1.5 / 2.2 % | 1.5 / 1.0 % | 2.3 |
| 0.2–0.4 | 246 | 0.8 / 1.3 % | 82.5 / 85.4 % | 11.8 / 9.1 % | 4.9 / 4.2 % | 2.8 |
| 0.4–0.6 | 288 | 2.1 / 2.1 % | 76.7 / 75.9 % | 15.6 / 15.1 % | 5.6 / 6.9 % | 0.8 |
| 0.6–0.8 | 446 | 1.3 / 3.0 % | 67.0 / 65.8 % | 22.0 / 21.4 % | 9.6 / 9.8 % | 4.1 |
| 0.8–1.0 | 1258 | 5.0 / 3.9 % | 55.1 / 55.0 % | 27.5 / 28.2 % | 12.4 / 12.9 % | 4.7 |
- **Cumple:** la frecuencia de pasos cambia con λ (1 paso: 96.7 → 55.1 %) y coincide con la teoría (χ² ≤ 4.7 < 7.81 en cada rango; total 0.6). Con el cambio 4 la teoría pasa a usar λ efectivo.

**Cambio 4 (HU0021-2, `15fb93c`):** λ efectivo = (λ − 0.05)/0.95; con λ = 0.05 la secuencia es determinística (4 semillas, misma secuencia: escala con rebote en los extremos). Corrida de 3 min 174555 (`2bfd81e`): 29.99 ciclos/s, ventana mín. 29.8 (sin #0).

**HU0010-2 caso A** (1ª fila `continuo` − 1ª fila de sesión; la página sin tocar):
| Código | Arranques | Resultado |
|---|---|---|
| `754468b` (reintento 2000 ms) | 150413 | 2.09 s |
| `2bfd81e` (cambio 7, reintento 500 ms) | 174219, 174312, 174419, 174555 | 0.67 / 2.92 / 3.82 / 1.04 s: no cumple |
| `30ccbf7` (cambio 7b, socket abierto al arrancar) | 180446, 180540, 180633, 180729 | **0.18 / 0.18 / 0.20 / 0.18 s: cumple** (n = 4) |
- MEDIDO sin la Kinect: en este Windows cada `connect` a un puerto cerrado tarda 2.0 s en fallar (3/3 por `::1`, 3/3 por `127.0.0.1`) y `localhost` resuelve a los dos. INFERIDO: por eso el reintento solo no bastaba. Prueba sin Kinect del 7b: un cliente que se conecta durante un arranque de 3 s recibe el primer mensaje a los 3.0 s. Con 7b faltan solo 7 filas `continuo` al arrancar en 180729 (antes 15–154).

**Piernas (HU0007-2; línea `[PIERNAS]` de `_perf.txt`, `2bfd81e`, corrida 174555):** al tapar la pierna izquierda con la mano detrás del muslo (≈ 30–50 s), las rodillas siguieron en MEDIUM y solo el pie izquierdo bajó a LOW (hasta 67 % de la ventana). Las rodillas salen LOW en el baile libre (88–96 s: hasta 68 % izq y 100 % der; tobillos 79–100 %) y con piernas en movimiento y brazos arriba (174 s: todas las articulaciones de pierna LOW 100 %). **Nunca NONE.** En la corrida: 0 rodillas ≥ MEDIUM en el 5.4 % de los ciclos y 1 en el 4.6 % (180729: 1.9 % y 5.1 %). INFERIDO: el LOW sale cuando el tracker pierde la pose entera (mismo % en todas las articulaciones de la ventana), más que por tapar una pierna.

**Prueba A/B de `--tempo-medium`** (`d2d2de4`, apagada por defecto; A = 175432, B = 175618 con la opción; 78 s cada una, 29.99 ciclos/s; n = 1 por lado):
| Tramo | A: `vel_rodilla` mediana · tempo | B: `vel_rodilla` mediana · tempo |
|---|---|---|
| 0–20 s quieto, brazos abajo | 4 °/s · 0.13 | 157 °/s · 0.41 |
| 20–40 s brazos arriba, piernas quietas | 5 °/s · 0.16 | 6 °/s · 0.03 |
| 40–60 s piernas con brazos arriba | 108 °/s · 0.61 | 100 °/s · 0.66 |
| 60–80 s baile | 100 °/s · 0.29 | 116 °/s · 0.31 |
- **No concluyente:** en A no apareció velocidad falsa con los brazos arriba; los 157 °/s de B "quieto" no los puede producir la opción (solo quita rodillas). INFERIDO: Ale se estaba acomodando al empezar B. Ciclos con 0 rodillas ≥ MEDIUM: 2.1 % (A), 4.6 % (B).

**Corrida de confirmación de 10 min** (180729, `30ccbf7`, configuración por defecto; calentamiento: los 3 arranques cortos 180446–180633). Sin registros de GPU, CPU ni procesos. **Validez:** Δ `transporte_ms` −0.02 ms; sin Kernel-Power 506/507 ni Time-Service desde las 17:30; 0 duplicadas; faltan 7 filas al arrancar y ninguna después.
| Métrica (ms salvo indicación) | 180729 |
|---|---|
| Ciclos/s media (sin #0) · ventana #0 | 29.95 · 25.6 |
| Ventanas < 29.5 · < 29.0 (sin #0) | **5** (#2 29.3, #5 29.1, #12 29.3, #118 29.1, #249 29.1) · 0 |
| C1 estricto (≥ 29.5) · D-023 | **294/299: no cumple** · **cumple** |
| `cap_update` · `tracker` · `mapeo` · `salida` | 10.9 · 20.0 · 1.0 · 0.4 |
| Periodo media / p95 · % > 33.3 ms | 33.4 / 47.9 · 8.9 |
| `lag_cam_ms` media / p95 / máx · p95 por minuto | 5.5 / 16.9 / **98.0** · 16.7–17.0 |
| (a) media / p95 / máx | 22.3 / 23.5 / 55.4 |
| **(b) RNF01** media / p95 / máx (n > 100; %) | 27.8 / 40.1 / **127.2** (1; 0.01) |
| `lat_tick_ms` media / p95 / máx (% > 250) | 38.8 / 53.7 / 79.3 (0) |
| Trabajos/s · por tercio · cambios de apertura por mano/s (izq / der) | 29.83 · 29.8 → 29.8 → 29.9 · 9.41 / 8.35 |
| Edad manos p95 · % ciclos con 2 manos | 64.6 · 79.8 |
| Notas reconstruidas con la semilla · racha máx · cambios de zona (< 250 ms dentro) | 892/892 · 2 · 199 (3, mismo artefacto de redondeo que 4h.3) |
- Ventanas bajas: 60 lecturas de color en 60 ciclos y 0–0.02 frames descartados, igual que las de 29.1–29.3 del 04/11 (4f): no son capturas incompletas. La #118 tiene `tracker` 24 ms, `mapeo` 3 ms y trabajo de manos 32 ms (19.4 trabajos/s): INFERIDO, un pico de carga del equipo (sin registro de procesos para confirmarlo).
- La muestra de (b) > 100 ms coincide con el máximo de `lag_cam_ms` (98.0 ms): INFERIDO, una espera de cámara aislada. **C3:** media y p95 mejores que la línea base 4c; **máx peor** (127.2 frente a 81.4–101.3 de 4c), 1 muestra de 17 975 (0.01 %) > 100 ms. **C2** cumple (p95 16.9, plano). **C4** cumple.
- Frente a la tanda (`3686feb`): mismas cifras de ciclo y latencia salvo esas 5 ventanas y esa muestra. Con n = 1 no se distingue un efecto de los cambios 4, 7, 7b y `[PIERNAS]` de la variación entre corridas `[POR COMPLETAR]`.

## 4i. 10–11/11: visual (US38), P-012, P-015, tanda final y validación offline (MEDIDO salvo indicación)
Fuentes en `sesiones/`: `sesion_2026111[01]_<hora>_mjpg-cambios-2026-11-07[-tempomedium]_cuda-lite.*`; procesos y CPU en `prueba.csv` (162510), `procesos_ab_20261110.csv`, `procesos_ab2_20261110.csv` + `cpu_ab2_20261110.csv`, `procesos_ab3_20261110.csv` + `cpu_ab3_20261110.csv` (desde 17:52 del 10/11), `procesos_igpu_20261111.csv` + `cpu_igpu_20261111.csv`, `procesos_tanda_20261111.csv` + `cpu_tanda_20261111.csv` + `gpu_tanda_20261111.csv`, `procesos_tanda2_20261111.csv` + `cpu_tanda2_20261111.csv` + `gpu_tanda2_20261111.csv`. Análisis con scripts de solo lectura de Code (fuera del repositorio), mismos métodos que 4h; reproducen 163615 (4h.3) sin diferencias. Navegador: Edge, una pestaña. Ropa 11/11: short y polo (Ale); 10/11 `[POR COMPLETAR]`. Las filas `config` / `config_visual` de `_latencias.csv` dicen si el visual estaba encendido, los Hz de la pantalla (143–145) y el tope de cuadros.

### 4i.1 Todas las corridas del 10 y 11/11
"Datos nuevos por mano/s" = veces por segundo que baja `edad_izq_ms` / `edad_der_ms` (P-015, `23cd4fe`): cada bajada es un dato nuevo de MediaPipe para esa mano. Ventanas sin #0. Validez = protocolo (D-018 sin 506, D-019 reloj, un solo cliente).
| Corrida | Página / opción | Commit | s | Ciclos/s media · mín · ventanas < 29.0 | (b) > 100 ms | Datos nuevos por mano/s (izq / der) | D-023 | Validez y uso |
|---|---|---|---|---|---|---|---|---|
| 10/11 162510 | visual sin tope | `f873c5f` | 351 | 22.29 · 17.2 · 115 | 251 | 4.1 / 3.7 | no | Válida. Prueba en vivo del visual; motivó el tope (4i.2) |
| 10/11 164558 | `?visual=0` | `3d55697` | 64 | 29.96 · 29.2 · 0 | 0 | 6.9 / 6.4 | — | Calentamiento (descartada) |
| 10/11 164736 | `?visual=0` (A) | `3d55697` | 182 | 29.94 · 29.3 · 0 | 0 | 13.3 / 12.5 | sí | Válida |
| 10/11 165134 | visual, tope 30 (B) | `3d55697` | 180 | 29.94 · 29.0 · 0 | 1 | 7.0 / 6.7 | sí | Válida; no pasa la regla del visual (1 muestra 105.1 ms) |
| 10/11 165523 | `?visual=0` (A) | `3d55697` | 178 | 29.98 · 29.5 · 0 | 1 | 7.5 / 7.2 | sí | Válida por protocolo; **equipo degradado** (hilo de manos 45 ms, `decod_hilo` 8–9 ms con CPU total igual a 164736; causa sin registrar, INFERIDO estado del equipo): no se usa para comparar |
| 10/11 165907 | visual, tope 30 (B) | `3d55697` | 184 | 29.48 · 15.6 · 10 | 25 | 6.9 / 6.4 | no | **Invalidada:** `claude` (app de escritorio) 1351 % de un núcleo durante la corrida |
| 10/11 171546 | `?visual=0` (A) | `3d55697` | 184 | 29.96 · 29.3 · 0 | 0 | 14.0 / 13.7 | sí | Válida |
| 10/11 172023 | `?ligero=1` (B) | `3d55697` | 182 | 29.96 · 29.5 · 0 | 0 | 7.2 / 6.9 | sí | Válida; pasa la regla del visual |
| 10/11 173030 | P-012 A | `3d55697` | 122 | 29.97 · 29.5 · 0 | 0 | 13.9 / 13.3 | sí | Válida (P-012, 4i.3) |
| 10/11 173308 | P-012 B `--tempo-medium` | `3d55697` | 122 | 29.94 · 29.5 · 0 | 0 | 13.9 / 13.5 | sí | Válida |
| 10/11 173538 | P-012 A | `3d55697` | 122 | 29.95 · 29.1 · 0 | 0 | 13.5 / 13.3 | sí | Válida |
| 10/11 173823 | P-012 B `--tempo-medium` | `3d55697` | 122 | 29.98 · 29.5 · 0 | 0 | 14.1 / 14.0 | sí | Válida |
| 10/11 174056 | P-012 A | `3d55697` | 118 | 29.94 · 29.0 · 0 | 0 | 13.7 / 13.4 | sí | Válida |
| 10/11 174334 | P-012 B `--tempo-medium` | `3d55697` | 120 | 29.94 · 28.8 · 1 | 0 | 14.3 / 13.9 | no | Válida (corrida de 2 min; D-023 informativo) |
| 10/11 174900 | `?visual=0`, escucha D-024 | `3d55697` | 120 | 29.99 · 29.7 · 0 | 0 | 14.7 / 14.7 | sí | Válida (sin registro de CPU) |
| 10/11 175724 | `?ligero=1&fps=20` (B) | `3d55697` | 179 | 29.98 · 29.5 · 0 | 0 | 7.0 / 6.7 | sí | Válida; pasa la regla del visual |
| 11/11 145656 | `?visual=0` | `8d58820` | 62 | 29.99 · 29.8 · 0 | 0 | 13.2 / 14.7 | — | Calentamiento (descartada) |
| 11/11 145850 | `?visual=0` (A), Edge en GPU integrada | `8d58820` | 179 | 29.99 · 29.8 · 0 | 0 | 13.1 / 13.6 | sí | Válida |
| 11/11 150240 | `?ligero=1` (B), GPU integrada | `8d58820` | 186 | 29.99 · 29.6 · 0 | 1 | 7.1 / 6.8 | sí | Válida; no pasa la regla del visual (1 muestra 104.4 ms) |
| 11/11 150640 | visual completo (B), GPU integrada | `8d58820` | 182 | 29.98 · 29.4 · 0 | 0 | 6.6 / 6.6 | sí | Válida; **pasa la regla: valor por defecto** (D-042) |
| 11/11 152446 | `?visual=0` | `8d58820` | 62 | 29.99 · 29.7 · 0 | 0 | 13.6 / 13.4 | — | Calentamiento de la tanda (descartada) |
| 11/11 152609 | Base 1 | `8d58820` | 606 | 29.97 · 26.3 · 3 | 0 | 13.6 / 13.9 | no | Válida por protocolo; **excluida de las bases** (D-046): caídas con `msmpeng`, `searchindexer`, `svchost`, `taskhostw` (MEDIDO por proceso) |
| 11/11 153718 | Base 2 | `8d58820` | 604 | 29.95 · 26.8 · 5 | 2 | 13.7 / 14.2 | no | Válida por protocolo; **excluida de las bases** (D-046): `claude` 187–391 % (notificación) y `msmpeng` ≈ 75 % entre 110 y 123 s |
| 11/11 155202 | **C6**: visual completo | `8d58820` | 610 | 29.97 · 29.2 · 0 | 0 | 6.9 / 6.9 | sí | Válida (C6) |
| 11/11 160340 | Base 3 | `8d58820` | 606 | 29.99 · 29.6 · 0 | 0 | 14.2 / 14.3 | sí | Válida; **cuenta**. Compañero detrás ≈ 377–378 s (Ale; MEDIDO: grupo de ciclos con ≥ 3 ángulos que saltan > 40°) |
| 11/11 161438 | Base de control (3 min) | `8d58820` | 185 | 29.99 · 29.7 · 0 | 0 | 14.0 / 14.2 | sí | Válida |
| 11/11 162639 | `?visual=0` | `8d58820` | 66 | 29.98 · 29.7 · 0 | 0 | 12.0 / 12.5 | — | Calentamiento de la repetición (descartada) |
| 11/11 162802 | Base 1 (repetición) | `8d58820` | 605 | 29.99 · 29.7 · 0 | 0 | 13.8 / 13.8 | sí | Válida; **cuenta** ("No molestar", sin eventos externos) |
| 11/11 163902 | Base 2 (repetición) | `8d58820` | 604 | 29.99 · 29.5 · 0 | 0 | 13.3 / 14.3 | sí | Válida; **cuenta** |
| 11/11 164931 | Base de control (3 min) | `8d58820` | 184 | 29.98 · 29.5 · 0 | 0 | 14.1 / 14.4 | sí | Válida |
| 11/11 172140 | visual completo | `8d58820` | 35 | 30.00 · 29.7 · 0 | 0 | 1.8 / 1.7 | — | Corta; propósito `[POR COMPLETAR]` |

### 4i.2 Visual (US38): costo, escalera y forma de la mano
- **Sin tope (162510, `f873c5f`):** la pantalla va a 143 Hz y Edge redibujaba en cada refresco: 22.29 ciclos/s, `tracker` 37–43 ms (20 el 07/11), (b) 71.6 / 98.1 / 194.1 ms con 251 muestras > 100 ms, `msedge` 231 % y `dwm` 65 % de un núcleo (`prueba.csv`). Sin cuerpo (sin anillos) el ciclo volvía a 30/s. JS del dibujo: 0.79 ms de media.
- **Tope de 30 cuadros/s (`3d55697`)** y regla fijada por Ale antes del A/B (D-041): B pasa si cumple D-023 y tiene 0 muestras de (b) > 100 ms. Escalera: (2) `?ligero=1`; (3) `?fps=20`; (4) Edge en GPU integrada.
| Corrida | Configuración | `tracker` | (b) media / p95 / máx · > 100 | Regla |
|---|---|---|---|---|
| 165134 | tope 30 | 24.9 | 36.4 / 51.1 / 105.1 · 1 | no pasa |
| 172023 | tope 30 + ligero | 23.2 | 32.8 / 47.1 / 86.3 · 0 | pasa |
| 175724 | tope 20 + ligero | 23.2 | 32.9 / 46.8 / 95.7 · 0 | pasa |
| 150240 | tope 30 + ligero, GPU integrada | 22.9 | 32.0 / 46.4 / 104.4 · 1 | no pasa |
| 150640 | tope 30 completo, GPU integrada | 24.5 | 35.0 / 48.6 / 83.5 · 0 | **pasa** |
  - INFERIDO: ligero y completo son equivalentes; la regla con corridas de 3 min depende de una sola muestra cerca de 100 ms.
- **Manos con el visual encendido (limitación, HU0008-1 / D-024):** datos nuevos por mano 6.6–7.2/s frente a 12.5–14.7/s con `?visual=0`; trabajo del hilo 48 ms y `decod_hilo` 9.0–9.2 ms frente a 22–23 y 4.6 ms; % de rendimiento de la CPU 182 frente a 192 y % de tiempo 26.4 frente a 22.2 (`cpu_ab2_20261110.csv`). **No cambia** con tope 20 (175724) ni con Edge en GPU integrada (150640). Causa `[POR COMPLETAR]`; INFERIDO sin comprobar: reparto de núcleos P/E de Windows o memoria/caché con Edge dibujando.
- **C6 (155202, 10 min) frente a Base 3 (160340), misma sesión:** `tracker` 23.8 frente a 20.0 ms; (b) 33.8 / 47.6 / 84.5 frente a 27.5 / 40.0 / 64.0 ms; datos nuevos por mano 6.9 frente a 14.3/s. **Tiempo por cuadro** (trabajo de dibujo): media 0.17 ms, p95 por lote mediana 0.30 y máx 0.60 ms, máx absoluto 1.60 ms (objetivo por aprobar ≤ 16.7). **Intervalo entre cuadros:** 33.5 ms. **Latencia visual:** 46.1 / 60.9 / 376.6 ms (n = 922; el máximo es una muestra).
- **Destellos (MEDIDO en `?demo=1`, navegador integrado, 26 s):** luminancia relativa media del lienzo 0.006–0.026, salto máximo 0.005 entre muestras de 50 ms; ningún cambio ≥ 0.10 (umbral WCAG 2.3.1, interpretación de Code).
- **Forma de la mano:** Ale observó (10/11, dicho, no medido) que ≈ 70 % de las veces una mano entreabierta salía punteada. En los tramos de manos `apertura01` es bimodal (p10 0.00–0.02, p90 0.95–0.98; 2–7 % de filas entre 0.4 y 0.6; 165134, 165907). Umbrales del borde 0.4/0.6 → 0.25/0.5 (`8d58820`); el sonido no cambia.

### 4i.3 P-012: A/B de `--tempo-medium` (regla fijada antes de correr; `?visual=0`)
Guion: 0–30 s quieto, 30–60 s brazos arriba con piernas quietas, 60–90 s piernas con brazos arriba, 90–120 s quieto. B gana un par si la mediana de `tempo` en 35–60 s es ≥ 0.05 menor que la de A y la de 65–90 s no baja más de 0.10.
| Par | `tempo` 35–60 s A → B | `tempo` 65–90 s A → B | `vel_rodilla` 35–60 s A → B (°/s) | Resultado |
|---|---|---|---|---|
| 1 (173030 / 173308) | 0.29 → 0.39 | 0.32 → 0.31 | 35 → 33 | B no gana |
| 2 (173538 / 173823) | 0.18 → 0.23 | 0.35 → 0.39 | 44 → 14 | B no gana |
| 3 (174056 / 174334) | 0.24 → 0.19 | 0.33 → 0.36 | 77 → 21 | B gana |
- **B gana 1 de 3: no se adopta** (D-037). INFERIDO: la normalización de 20 s (D-035) diluye la bajada de `vel_rodilla`.

### 4i.4 P-015 y D-024
- Con `?visual=0`: **12.5–14.7 datos nuevos por mano/s** en las 17 corridas válidas sin calentamiento de la tabla 4i.1 (sin 165523, equipo degradado: 7.2–7.5) (medida directa; supera el ≈ 10 aceptado por el asesor). Los cambios de apertura del 07/11 (8.2–9.1/s) la subestimaban, como se había inferido en 4h.5.
- Con el visual encendido: 6.6–7.2/s (4i.2).
- Escucha de D-024 (174900, 2 min): Ale (dicho): con la mano rápida se sienten saltos de timbre; con la lenta casi no (quizá por el volumen bajo y los cambios suaves). MEDIDO: 14.7 datos nuevos por mano/s y 1.08 saltos de `apertura01` > 0.3 por segundo. Cierre de D-024 `[POR COMPLETAR]` (Ale).

### 4i.5 Tanda final (código `8d58820` = `congelado-11-11` = `medido-final`)
Condiciones: pantalla en "Nunca", enchufada, "Mejor rendimiento", `w32tm /resync` a las 15:20 (Time-Service 37), Edge en GPU integrada (Ale; `[POR CONFIRMAR]` que estaba aplicado), short y polo; sin Kernel-Power 506 ni otros eventos de hora durante las corridas. Repetición con "No molestar" (Ale). Reloj (D-019): Δ `transporte_ms` +0.03 a +0.54 ms. Un solo cliente; faltan 0–6 filas al arrancar.
| Corrida | C1: media · mín · < 29.5 · `cap_update` | C2: `lag_cam` p95 · por minuto | C3: (b) media / p95 / máx · > 100 | (a) media / p95 / máx | C4: `lat_tick` media / p95 / máx · > 250 |
|---|---|---|---|---|---|
| 152609 Base 1 (excluida) | 29.97 · 26.3 · 3 · 9.7 | 17.1 · 17.0–17.5 | 28.4 / 41.3 / 97.3 · 0 | 23.3 / 26.1 / 60.3 | 40.2 / 54.1 / 83.8 · 0 |
| 153718 Base 2 (excluida) | 29.95 · 26.8 · 5 · 9.8 | 17.0 · 16.9–19.3 | 28.6 / 41.3 / 113.1 · 2 | 23.5 / 25.8 / 74.0 | 40.1 / 54.8 / 85.2 · 0 |
| 155202 C6 (visual) | 29.97 · 29.2 · 1 · 4.8 | 17.2 · 17.0–17.7 | 33.8 / 47.6 / 84.5 · 0 | 28.4 / 32.6 / 83.8 | 44.8 / 61.0 / 80.1 · 0 |
| **160340 Base 3** | 29.99 · 29.6 · 0/303 · 10.7 | 16.9 · 16.8–16.9 | 27.5 / 40.0 / 64.0 · 0 | 22.7 / 24.3 / 63.4 | 38.5 / 53.5 / 69.5 · 0 |
| 161438 control | 29.99 · 29.7 · 0/92 · 10.7 | 16.9 | 27.3 / 40.4 / 69.4 · 0 | 22.5 / 24.4 / 52.8 | 39.2 / 54.6 / 68.1 · 0 |
| **162802 Base 1 (rep.)** | 29.99 · 29.7 · 0/302 · 10.0 | 16.9 · 16.9–17.0 | 28.2 / 41.1 / 59.2 · 0 | 23.2 / 25.3 / 58.0 | 39.3 / 54.6 / 75.3 · 0 |
| **163902 Base 2 (rep.)** | 29.99 · 29.5 · 0/302 · 10.1 | 16.9 · 16.9–17.0 | 27.8 / 40.8 / 60.9 · 0 | 22.9 / 24.9 / 59.9 | 39.2 / 54.6 / 87.7 · 0 |
| 164931 control | 29.98 · 29.5 · 0/92 · 10.1 | 17.0 | 27.9 / 40.6 / 60.7 · 0 | 23.0 / 25.1 / 51.0 | 40.3 / 55.4 / 69.0 · 0 |
- **Criterios en las 3 bases que cuentan (160340, 162802, 163902):** **C1 cumple**, con D-023 y también estricto (0 ventanas < 29.5); `cap_update` 10.0–10.7 ms > 0; ciclos > 33.3 ms 8.6–8.7 %. **C2 cumple** (p95 16.9 ≤ 4c 27.1–35.9; plano por minuto). **C3 cumple**: media, p95 y máx mejores que 4c (45.2–53.5 / 58.4–69.4 / 81.4–101.3); 0 muestras > 100 ms (HU0023-1). **C4 cumple** (0 % > 250 ms). **C5:** D-025 a D-034 confirmadas por Ale el 10/11 (D-036); el visual no cambia el sonido.
- Sin ralentización: las bases de control repiten las bases (`tracker` 20.0 ms).
- **Excluidas:** en 152609 y 153718 las ventanas < 29.0 y las 2 muestras > 100 ms coinciden con procesos ajenos (tabla 4i.1). Se conservan y se informan (D-046).

### 4i.6 Validación offline (SIMULADO; `validacion_offline.py`, commit `fab4f7b`, salida `sesiones/validacion_offline_20261111.txt`)
- **US12 (HU0012-2, definición D-044):** escalón 20° → 160° de los hombros por la `RegistroPorAngulo` real (`EMA_ANGULO_BRAZO` 0.5, 30 Hz): **tiempo al 50 % de registro01 = 0 ms** (el primer frame con el ángulo nuevo ya llega al 50 %; retardo de grupo teórico 33.3 ms) ≤ 100 ms; cola 63 % 33.3 ms, 90 % 100.0 ms. Aparte, intencional (D-028): la zona pasa de grave a agudo a los 300 ms. Velocidad de rodilla (`EMA_VEL_RODILLA` 0.4, informativo): 50 % 33.3, 63 % 33.3, 90 % 133.3 ms. Ruido blanco: −42.4 % (α 0.5; teoría −42.3 %) y −50.0 % (α 0.4; teoría −50.0 %); MEDIDO en sesiones (sección 5): −22 a −53 %.
- **US28 (umbrales fijados antes de correr, `[POR CONFIRMAR]` por Ale, P-018):** 20 semillas × 300 notas con λ fijo: notas distintas entre pares 0.0 / 84.8 / 85.0 / 85.4 % para λ 0.05 / 0.3 / 0.6 / 1.0; trigramas distintos 12 / 79 / 118 / 165; entropía 2.75–2.79 bits. Secuencia real de λ de 162802 (889 notas; entrada MEDIDA): 85.2 % de notas distintas entre semillas; con la semilla grabada se reproduce la melodía de la corrida. US28-2: con la misma entrada, octava y número de notas idénticos en las 20 semillas; 20 melodías distintas. D1, D2, D3 y C1: se cumplen. **Advertencia (INFERIDO):** el % de notas distintas se satura en ≈ 85 % para todo λ > 0.05 (D3 se cumple por poco: 84.8 < 85.0 < 85.4); el efecto de λ se ve mejor en los trigramas.
- **US25:** `pruebas_unitarias.py` 44/44 (`7c9e0a1`); cada prueba "apoya" un criterio. Cubiertos: `manos.py`, `muestreo.py`, `zona.zona_desde_registro`, `servidor.py` y las clases de `main.py` (`NormalizadorAdaptativo`, `VelocidadAngular`, `angulo_articulacion`, `MapeoExtremidades`, `RegistroPorAngulo`, cargadas sin importar `main.py`). Sin cubrir: `bucle_kinect`, `HiloManos`, `FusionTemporal`, `guardar_latencias`, arranque y cierre de la Kinect (US26), `zona.calcular_zona`, `index.html` y `visual.js`. Hallazgo sin arreglar: `angulo_articulacion` da 179.9974° con vectores unitarios (`+1e-9` del denominador); con mm, < 1e-4°.
- **(c) extremo a extremo:** el método A (celular) no se probó. Cota INFERIDA con el método B: (c) ≥ (b) + `baseLatency` = 27.5–28.2 + 10 ms de media (≥ ≈ 38 ms; p95 ≥ ≈ 50 ms), más la latencia interna del SDK y la del parlante `[POR COMPLETAR]`. No es una medida de (c).
- **US14:** captura de la consola de Edge en `sesiones/us14_consola_edge_20261111.png` (15:48, antes de pulsar "Empezar", Python apagado): avisos de autoplay (HU0014-2) y `ScriptProcessorNode` (interno de Tone.js 14.7.77); 4 errores rojos de WebSocket rechazado porque Python no corría. **Falta la captura después de pulsar "Empezar"** (HU0014-1).

## 4j. 12/11: validación con el visual encendido (D-047 a D-059) — la tanda NO es válida (MEDIDO salvo indicación)
Fuentes en `sesiones/`: `sesion_20261112_<hora>_mjpg-cambios-2026-11-07_cuda-lite.*`; `gpu_visual_20261112.csv`, `cpu_visual_20261112.csv`, `procesos_visual_20261112.csv`; registro de eventos de Windows (Kernel-Power y Time-Service, leído por Code con `Get-WinEvent`). Cifras con `analisis_visual.py` (`b309282`, solo lectura), que reproduce 155202 y 160340 de 4i sin diferencias.
**Condiciones (Ale):** rutina de siempre (30 s quieto, 1 min brazos, 1 min piernas, 30 s manos con el cuerpo quieto); pantalón largo en el calentamiento, short y polo en el resto; Edge en GPU integrada (`edge://gpu` muestra Intel: **cierra el `[POR CONFIRMAR]` de D-042 para el 12/11**; para el 11/11 sigue abierto); luz algo más baja que la habitual; ≈ 3 min entre el calentamiento y V1 (dicho por Ale; según los archivos, 143522 termina a las 14:40 y V1 empieza a las 14:48). `w32tm /resync` a las 14:30:56 (Time-Service 35/37). Sin Kernel-Power 506 durante las corridas (el último 506 fue a las 13:19:34, antes de 132848).
**Código:** las corridas registran `commit` = `7ff47c5` (132848, 140411) y `7ff47c5-sucio` (desde 143303). `git diff 8d58820 7ff47c5` no toca ningún archivo de código (`main.py`, `index.html`, `visual.js`, `manos.py`, `muestreo.py`, `servidor.py`, `zona.py`), y sus fechas de modificación son ≤ 11/11 (MEDIDO): **el código es el de `8d58820`**. INFERIDO: el `-sucio` viene de `CLAUDE.md`, modificado a las 14:17:12, entre 140411 (limpia) y 143303 (sucia). Límite de US22: `-sucio` no dice qué archivo estaba cambiado.

### 4j.1 Todas las corridas del 12/11 y la referencia con visual
| Corrida | Configuración (fila `config` · `config_visual`) | s | Validez y uso |
|---|---|---|---|
| 132848 | visual 1 · tope 30 | 906 | **Fuera de protocolo.** Kernel-Power 105 (cambio de fuente de energía) a las 13:29:57, 68 s después de arrancar; 12 ventanas de 4.1–17.0 ciclos/s al inicio (`tracker` 31.8 ms en el 1er tercio); huecos de filas de 0.3–2.2 s entre 19 y 67 s; la página se reconectó a los ≈ 4 min y las filas `continuo` acaban a los 286 s (faltan 13 061). Propósito `[POR COMPLETAR]` (Ale) |
| 140411 | visual 1 · tope 30 | 58 | Corta; hueco de 9.5 s a los 41 s (sin cuerpo, INFERIDO). Propósito `[POR COMPLETAR]` (¿US14?) |
| 143303 | visual 1 · tope 30 | 61 | Corta; hueco de 8.2 s a los 7 s. Propósito `[POR COMPLETAR]` |
| 143522 | visual 1 · tope 30 | 292 | Calentamiento (descartado; pantalón largo) |
| **144817 V1** | visual 1 · tope 30 | 600 | **Invalidada por reloj (D-019):** Δ `transporte_ms` +16.07 ms. Además no cumple C1 ni C2 (abajo), que no dependen del reloj del sistema |
| **145949 V2** | visual 1 · **sin `config_visual`** | 604 | **Invalidada por reloj (D-019):** Δ +13.22 ms. **Y el visual no dibujó:** 0 filas `cuadro_*` y `visual` |
| **151032 control** | visual 1 · **sin `config_visual`** | 182 | **Invalidada por reloj (D-019):** Δ +2.96 ms. El visual no dibujó (0 filas `cuadro_*` y `visual`) |
| 155202 (11/11, ref.) | visual 1 · tope 30 | 610 | Válida (4i): única corrida de 10 min válida con el visual encendido |
- **Reloj:** `transporte_ms` sube de forma lineal ≈ 1.6 ms/min en V1 (0.7 → 16.1 por minuto), ≈ 1.4 ms/min en V2 y ≈ 1.0 ms/min en el control; en 143522 (14:35–14:40) se mantuvo plano (0.3 ms). INFERIDO: tras la sincronización de las 14:30:56 el sondeo siguiente (intervalo 1024 s, `w32tm /query /status`) cae a las ≈ 14:48 y Windows corrige la hora poco a poco desde ahí; `Date.now()` lo sigue y Python no (como en 4g.3). (a) y (b) guardadas de V1, V2 y el control **no son válidas**; como referencia INFERIDA (solo relojes de Python, sin transporte): (a) − `transporte_ms` + `lag_cam_ms`.
- **Visual sin dibujar en V2 y el control:** la página tenía el visual encendido (fila `config` = 1) pero `requestAnimationFrame` no corrió en toda la corrida: sin `config_visual` ni filas `cuadro_*`/`visual`, `msedge` 6–7 % de un núcleo (V1: 53 %; 160340 sin visual: 21 %), y manos y `tracker` iguales a las bases sin visual. INFERIDO: la ventana de Edge estaba minimizada o tapada (Edge detiene `requestAnimationFrame` en ventanas ocultas). **No son corridas con el visual encendido (D-047)**; quedan como referencia sin visual de este día, también invalidadas por el reloj.

### 4j.2 Cifras (sin la ventana #0; C2 y C1 usan solo relojes de Python y del SDK)
| Métrica | **144817 V1** | 145949 V2 (sin dibujo) | 151032 control (sin dibujo) | 155202 (11/11) | Bases sin visual 11/11 (160340, 162802, 163902) |
|---|---|---|---|---|---|
| C1: media · mín · ventanas < 29.0 · < 29.5 | 29.83 · 28.3 · **7** · 40 | 29.98 · 29.3 · 0 · 2 | 29.97 · 29.2 · 0 · 2 | 29.97 · 29.2 · 0 · 1 | 29.99 · 29.5–29.7 · 0 · 0 |
| `cap_update` · `tracker` (ms) · % ciclos > 33.3 ms | 1.9 · 26.9 · 35.7 | 8.6 · 22.0 · 9.2 | 8.4 · 22.2 · 9.6 | 4.8 · 23.8 · 12.7 | 10.0–10.7 · 20.0–20.8 · 8.6–8.7 |
| C2: `lag_cam` p95 · p95 por minuto · último − primer minuto | 27.0 · **22.5–30.0** · **+5.9** | 17.3 · 17.2–17.4 · +0.2 | 17.4 · 17.3–17.5 · +0.0 | 17.2 · 17.0–17.7 · −0.1 | 16.9 · 16.8–17.0 · ≤ 0.02 |
| (b) guardada media / p95 / máx · > 100 | no válida (reloj) | no válida | no válida | 33.8 / 47.6 / 84.5 · 0 | 27.5–28.2 / 40.0–41.1 / 59.2–64.0 · 0 |
| Referencia INFERIDA (a) − transporte + `lag_cam` · > 100 | 42.4 / 59.7 / 100.4 · 1 | 30.5 / 42.8 / 78.5 · 0 | 30.7 / 43.0 / 80.7 · 0 | — | — |
| C4: `lat_tick` media / p95 / máx · > 250 | 47.1 / 64.0 / 79.8 · 0 de 870 | 41.3 / 56.2 / 71.8 · 0 | 41.0 / 55.9 / 72.1 · 0 | 44.8 / 61.0 / 80.1 · 0 de 921 | 38.5–39.3 / 53.5–54.7 / 69.5–87.7 · 0 |
| C7: datos nuevos por mano/s (izq / der) · trabajos/s | 9.33 / 9.04 · 19.9 | 14.13 / 13.69 · 29.7 | 14.14 / 13.70 · 29.3 | 6.92 / 6.87 · 15.0 | 13.27–14.24 / 13.79–14.31 · 29.8 |
| C6: tiempo por cuadro media · p95 por lote mediana / máx · máx | 0.26 · 0.45 / 0.80 · 4.0 | — | — | 0.17 · 0.30 / 0.60 · 1.6 | — |
| C6: latencia visual media / p95 / máx (n) | 55.9 / 72.5 / 285.4 (871) | — | — | 46.1 / 60.9 / 376.6 (922) | — |
| Intervalo entre cuadros (ms) | 33.5 | — | — | 33.5 | — |
| HU0017: saltos de `apertura01` > 0.3 por s · p5 / mediana / p95 | 0.35 · 0.00 / 0.54 / 0.97 | 0.28 · 0.00 / 0.49 / 0.96 | 0.31 · 0.00 / 0.52 / 0.98 | 0.20 · 0.00 / 0.32 / 0.94 | 0.11–0.19 · 0.00 / 0.28–0.34 / 0.96–0.98 |
| Cambios de zona por minuto · salto de tempo p99 / máx | 16.5 · 0.397 / 1.000 | 15.0 · 0.396 / 1.000 | 16.8 · 0.437 / 0.936 | 13.3 · 0.475 / 1.000 | 12.7–14.6 · 0.403–0.454 / 0.983–1.000 |
| Edad manos p95 · racha máx · notas reconstruidas | 112.5 · 2 · 871/871 | 64.1 · 2 · 863/863 | 64.2 · 2 · 274/274 | 144.5 · 2 · 922/922 | 48.2–64.2 · 2 · 100 % |
| GPU SM mediana · °C máx · CPU % rendimiento / % tiempo (medianas) | 1747 · 70 · 211 / 37.0 | 1762 · 70 · 198 / 24.9 | 1762 · 70 · 199 / 25.5 | 1762 · 67 · 185 / 27.6 | 1762 · 67–69 · 198 / 23.3–23.4 |
| `python` · `msedge` · `dwm` · `system` (% de un núcleo, media) | 198 · 53 · **46** · 36 | 173 · 6 · 20 · 22 | 176 · 7 · 21 · 25 | 189 · 38 · 8 · 21 | 163–167 · 18–21 · 1–4 · 19 |
- **V1 frente a 155202 (los dos con el visual dibujando, días distintos):** `tracker` 26.9 frente a 23.8 ms, `cap_update` 1.9 frente a 4.8 ms, `dwm` 46 frente a 8 % de un núcleo, `lag_cam` creciente. En el calentamiento 143522 también `tracker` 27.2 y `dwm` 30. Causa `[POR COMPLETAR]`; INFERIDO sin comprobar: otra disposición de ventanas en pantalla (más composición de `dwm`) o la luz más baja. Procesos ajenos ≥ 50 % de un núcleo en V1: `system` (27 muestras, máx 191 %), `dwm` (138 muestras, máx 69 %), sueltos de `svchost`, `mousocoreworker` 50 %; las muestras > 1200 % de `svchost#N` son imposibles (artefacto del contador, INFERIDO).
- **Criterios de V1** (aunque está invalidada por reloj): **C1 no cumple** (D-023: 7 ventanas de 28.3–28.9 < 29.0); **C2 no cumple** (p95 27.0 ≤ 27.1, pero crece 22.5 → 30.0 ms por minuto); C3 no evaluable (reloj); C4 cumple; C6 cumple (p95 por lote máx 0.80 ≤ 16.7; latencia visual p95 72.5 ≤ 100, umbral por aprobar); C7 cumple (9.3 / 9.0 ≥ 5).
- **HU0010-2 caso A** (1ª fila `continuo` − 1ª fila de sesión, con la página abierta antes de arrancar): 0.53 / 0.19 / 0.01 / 0.19 / 0.20 / 0.19 / 0.20 s en los 7 arranques: ≤ 2 s.
- **HU0019-3** (χ² por rango de λ, crítico 7.81): V1 0.5–2.6 en todos los rangos; 155202 0.4–5.1. En rangos con valor esperado < 5 el χ² solo orienta (151032 da 32.6 en λ < 0.2 por 1 repetición con esperado ≈ 0).
- **Sin evidencia guardada en `sesiones/` el 12/11** de US14 (captura después de "Empezar"), US20 (respuestas de la prueba de percepción), US38 (capturas) ni de las consolas de Python: `[POR COMPLETAR]` (Ale).

### 4j.3 Conclusión
- **La tanda de D-050 no es válida:** V1, V2 y el control fallan la regla de reloj (D-019), y V2 y el control además no tuvieron el visual dibujando. Con el visual encendido solo queda **una** corrida de 10 min válida (155202), que cumple C1 (D-023), C2, C3, C4, C6 y C7; el C1 estricto no (1 ventana de 29.2).
- **No se pone la etiqueta `validado-visual`.** Se repiten V1, V2 y el control por invalidez de protocolo (reloj; V2 y el control además por visual sin dibujar), según D-062, con D-060 (servicio de hora detenido) y D-061 (Edge al frente). Los fallos de C1 y C2 de V1 no son motivo de repetición por sí solos (D-062).
- **Estado por historia (configuración D-047):** ver la tabla de 4j.4.

### 4j.4 Estado de US07–US28 y US38 (12/11; "cumple" solo con criterio medido y binario)
| US | Estado | Evidencia | Pendiente |
|---|---|---|---|
| US07 | **Parcial** | -1: 155202 cumple D-023 (n = 1 con visual); V1 no cumple (7 ventanas < 29.0, corrida invalidada por reloj). -2: piernas LOW, nunca NONE (4h.5) | Repetir V1/V2; reescritura de -2 (LOW = disponible) |
| US08 | **Parcial** | -1 (D-048): 155202 6.92 / 6.87 datos nuevos por mano/s ≥ 5; V1 9.33 / 9.04 (invalidada). -2 cumple (D-025) | Tanda válida con visual |
| US09 | Cumple (texto por cambiar) | `par_dt_ms = 0` por construcción | Texto en el lote de D-058 (Ale) |
| US10 | Cumple | -1: 0 filas duplicadas ni errores de lectura en las 8 corridas. -2 caso A 0.01–0.53 s (7 arranques, 12/11); caso B (07/11, 4h.1) | Caso B con visual no medido (¿132848?) `[POR COMPLETAR]` |
| US11 | Cumple | 4h–4j | — |
| US12 | Cumple (SIMULADO -2) | Jitter MEDIDO (sección 5); escalón SIMULADO 0 ms ≤ 100 (D-044, 4i.6) | — |
| US13 | Cumple (texto por cambiar) | λ 0.05–1 y cambia la melodía (4h) | Cita en el lote de D-058 |
| US14 | **Cumple** (lectura por confirmar, Ale) | -2 cumple (4h.1). -1: captura de la consola de Edge **después** de "Empezar" con Python en marcha (`sesiones/us14_consola_edge_20261112.webp`, enviada por Ale el 12/11; la página muestra "Te veo", "Zona: grave" y "Terminar", y la pestaña indica audio): Tone.js v14.7.77 cargado; 1 aviso de `ScriptProcessorNode` (interno de Tone.js); 12 avisos de autoplay de antes del clic (HU0014-2); **1 error**: `WebSocket ... ERR_CONNECTION_REFUSED` (`index.html:249`). INFERIDO: es un intento de conexión antes de que Python abriera el socket (HU0010-2), no un error de inicialización del audio | Que Ale confirme que el error de WebSocket no cuenta para -1 |
| US15 | **Parcial** (texto) | -2 cumple (D-028); 13.3–16.8 cambios de zona por minuto con visual | Reescritura de -1 (D-035, Ale) |
| US16 | **Parcial** (texto) | -2 cumple; salto de tempo p99 0.397–0.475 | Reescritura de -1 con umbral de salto `[POR COMPLETAR]` |
| US17 | **Cumple** (n = 1 corrida válida con visual) | Rango p5–p95 0.00–0.94; saltos > 0.3: 0.20/s en 155202 ≤ 0.5 (D-064); V1 0.35/s (invalidada por reloj; el valor no depende del reloj) | Confirmar en la tanda repetida |
| US18 | **Parcial** (texto) | -2 cumple | Reescritura de -1 |
| US19 | Cumple | -1 7 notas; -2 racha 2 en todas; -3 χ² < 7.81 por rango (155202, V1) | — |
| US20 | **No cumple** (sin hacer) | Sin registro de la prueba | Prueba con visual y preguntas separadas (D-055), anotada |
| US21 | Cumple | 100 % de notas reconstruidas en las 8 corridas; λ mínimo determinístico (D-031) | — |
| US22 | Cumple, con observación | Semilla + `commit` + `lam_sorteo` reconstruyen todo; `version` = `VERSION_MAIN`, no la versión de las tablas; `-sucio` no dice qué archivo | Confirmar si basta (Ale) |
| US23 | **Parcial** | -1: 155202 (b) 0 > 100 (n = 1 con visual); V1 no evaluable (reloj). -2: `[PERF]` y `lag_cam_ms` por etapa. (c): cota del método B (D-059) | Tanda válida con visual |
| US24 | **Parcial** | -1: 0 % > 250 ms en todas las corridas válidas; -2: el valor queda por tick pero no se marca el incumplimiento (fase 1c) | Ale decide si -2 basta. Condiciones reales (D-059): Edge + JBL; Ale usa siempre el parlante JBL (dicho, 12/11) |
| US25 | **Parcial** (texto) | 44/44 (`7c9e0a1`) | Texto de D-056 (Ale) |
| US26 | **Parcial** | 155202 (10 min con visual, sin fallos de módulo) | Tanda válida; consolas de Python en `sesiones/` |
| US27 | **No cumple** (no iniciada) | Tablas fijas en `muestreo.py` | Fases 1 y 2 |
| US28 | Cumple (SIMULADO) | D1, D2, D3 en trigramas (D-057) y C1 (4i.6) | — |
| US38 | **Parcial** | -1/-2/-3 implementados (`visual.js`, `index.html`); -4 sin destellos en `?demo=1` (4i.2); -5 C6 cumple en 155202 y V1 | URL de cuestionarios; capturas; tanda válida (C6 con D-063); revisión de Ale y la profesora (-6) |

## 4k. 12/11 por la tarde: tanda con visual repetida (D-060 a D-062) — válida por protocolo; C1 y C3 no cumplen en todas (MEDIDO salvo indicación)
Fuentes en `sesiones/`: `sesion_20261112_<hora>_mjpg-cambios-2026-11-07_cuda-lite.*`; registro de eventos de Windows (`Get-WinEvent`, Code). Cifras con `analisis_visual.py` (`b83511b`). **Sin registros de GPU, CPU ni procesos de esta tanda** (no hay archivos nuevos `gpu_`/`cpu_`/`procesos_` después de las 15:32 en el repositorio): no se puede comprobar ni descartar un proceso ajeno (D-051, D-062) `[POR COMPLETAR]` (Ale: si se guardaron en otro lugar).
**Condiciones:** las de 4j (rutina de siempre, short y polo, Edge en GPU integrada, luz algo más baja, parlante JBL). Edge maximizado y al frente (Ale; anotación por corrida `[POR COMPLETAR]`). Código: encabezado `commit=1d70ce8` sin `-sucio` en las 5 corridas (MEDIDO); `git diff 8d58820 1d70ce8` no toca archivos de código (MEDIDO): **código de `8d58820`**. **Hora (D-060):** Time-Service 35/37 (resync) a las 15:50:52; ningún evento del servicio hasta 16:25:47 (158, arranque) y 16:25:58 (resync final); hoy `sc query w32time` = RUNNING (MEDIDO). Sin Kernel-Power desde las 15:20.

### 4k.1 Corridas
| Corrida | s | Uso | Validez (D-062) |
|---|---|---|---|
| 153900 | — | Arranque corto para comprobar el encabezado (`commit=1d70ce8`); 0 filas de sesión | No es corrida |
| 155234 | 89 | Calentamiento (descartado) | — |
| **155642 V1** | 601 | 10 min con visual | **Válida:** Δ `transporte_ms` +0.20 ms; visual dibujó (611 lotes de cuadro, 863 latencias visuales); un cliente; sin 506 |
| **161012 V2** | 602 | 10 min con visual | **Válida:** Δ −0.03 ms; 599 / 908; un cliente; sin 506 |
| **162149 control** | 180 | 3 min con visual | **Válida:** Δ +0.01 ms; 186 / 288 |
| 155202 (11/11) | 610 | 10 min con visual (D-050) | Válida (4i) |

### 4k.2 Criterios con el visual encendido (D-049, D-063, D-064, D-048)
| Métrica | **155642 V1** | **161012 V2** | 155202 (11/11) | 162149 control | Bases sin visual 11/11 (referencia) |
|---|---|---|---|---|---|
| C1: media · mín · < 29.0 · < 29.5 | 29.90 · 22.2 · **7** · 12 | 29.96 · 29.0 · 0 · 5 | 29.97 · 29.2 · 0 · 1 | 29.97 · 29.1 · 0 · 1 | 29.99 · 29.5–29.7 · 0 · 0 |
| `cap_update` · `tracker` · % ciclos > 33.3 ms | 3.1 · 25.5 · 19.7 | 2.3 · 26.2 · 25.5 | 4.8 · 23.8 · 12.7 | 3.3 · 25.4 · 19.3 | 10.0–10.7 · 20.0–20.8 · 8.6–8.7 |
| C2: `lag_cam` p95 · p95 por minuto · último − primer minuto | 18.4 · 17.6–**27.3** · **+9.5** | 19.2 · 17.9–23.5 · +0.2 | 17.2 · 17.0–17.7 · −0.1 | 17.7 · 17.5–17.9 · +0.2 | 16.9 · 16.8–17.0 |
| C3: (b) media / p95 / máx · > 100 | 37.2 / 50.6 / **206.7** · **8** | 38.5 / 51.7 / **115.7** · **4** | 33.8 / 47.6 / 84.5 · 0 | 36.3 / 49.7 / 83.7 · 0 | 27.5–28.2 / 40.0–41.1 / 59.2–64.0 · 0 |
| (a) media / p95 / máx | 29.9 / 33.7 / 194.0 | 30.5 / 34.3 / 111.8 | 28.4 / 32.6 / 83.8 | 29.8 / 33.7 / 82.9 | 22.7–23.2 / 24.3–25.3 / 58.0–63.4 |
| C4: `lat_tick` media / p95 / máx · > 250 | 47.1 / 64.8 / 79.9 · 0 de 862 | 47.2 / 62.8 / 95.9 · 0 de 908 | 44.8 / 61.0 / 80.1 · 0 | 47.1 / 63.6 / 97.0 · 0 | 38.5–39.3 / 53.5–54.7 / 69.5–87.7 · 0 |
| C6: tiempo por cuadro, máx de los p95 por lote · latencia visual p95 (máx) | 0.60 · 63.9 (88.1) | 0.70 · 63.8 (72.2) | 0.60 · 60.9 (376.6) | 0.50 · 63.7 (68.9) | — |
| C7: datos nuevos por mano/s (izq / der) | 7.18 / 6.97 | 7.26 / 6.83 | 6.92 / 6.87 | 6.92 / 6.40 | 13.27–14.24 / 13.79–14.31 |
| HU0017: saltos de `apertura01` > 0.3 por s | 0.34 | 0.27 | 0.20 | 0.46 | 0.11–0.19 |
| Edad manos p95 · racha máx · notas reconstruidas | 142.3 · 2 · 863/863 | 140.1 · 2 · 909/909 | 144.5 · 2 · 922/922 | 192.3 · 2 · 289/289 | 48.2–64.2 · 2 · 100 % |
| **Resultado** | C1 **no**, C2 **no**, C3 **no**; C4, C6, C7, HU0017 sí | C3 **no**; C1 (D-023), C2, C4, C6, C7, HU0017 sí | todos sí (estricto no) | todos sí (estricto no) | — |
- **Dónde fallan (MEDIDO):** en V1, 6 de las 8 muestras de (b) > 100 ms (112.7–206.7) y las ventanas más bajas (#288–#295: 22.2–29.2 ciclos/s, `tracker` 28–34 ms, `cap_update` 0–1 ms) caen entre 576 y 590 s, el final de la corrida; ahí el p95 de `lag_cam` del minuto 9 sube a 27.3 ms. Las otras 2 muestras (105.6 y 120.7 ms) están sueltas (207 y 402 s). En V2, 4 muestras sueltas de 110.6–115.7 ms (104, 196, 369 y 558 s). **Causa `[POR COMPLETAR]`:** sin registro de procesos no se puede atribuir (INFERIDO, sin comprobar: carga del equipo; Ale se acerca a cerrar solo al llegar a 600 s).
- **C2 de V1:** el p95 de la corrida (18.4) cumple ≤ 27.1; falla por "sin crecimiento" con la definición operativa de `analisis_visual.py` (último − primer minuto ≤ 1 ms, `[POR CONFIRMAR]`, P-021) y también porque el minuto 9 supera 27.1.
- **Equipo hoy:** `tracker` 25.4–26.2 ms con el visual en las 4 corridas de la tarde, frente a 23.8 en 155202 (11/11). INFERIDO: estado del equipo distinto entre días (sin registro de procesos para comprobarlo).
- **D-062:** V1 y V2 son válidas por protocolo; sus fallos de C1, C2 y C3 se informan y **no se repiten**.
- **Registro oficial (D-065, Ale, 12/11):** esta tanda queda como registro oficial de la validación con visual, con los fallos de C1, C2 y C3 tal como salieron.
- **Limitación:** sin registros de GPU, CPU y procesos, **la causa de los fallos es `[POR COMPLETAR]`** y **no se pudo aplicar la invalidación por proceso ajeno** (D-051, D-062): no se sabe si hubo un proceso ajeno durante las caídas de V1 (576–590 s) ni durante las muestras sueltas de V1 y V2.
- **Etiqueta:** `medido-visual` (anotada) en `1d70ce8`, el commit que registran las corridas; código idéntico a `8d58820`. No se usa `validado-visual`.

### 4k.3 Resultado de la tanda D-050 (155202, 155642, 161012; control 162149)
| Criterio | 155202 | V1 | V2 | Tanda |
|---|---|---|---|---|
| C1 (D-023) | cumple | **no** | cumple | **no cumple** (2/3) |
| C2 | cumple | **no** | cumple | **no cumple** (2/3) |
| C3 (0 de (b) > 100) | cumple | **no** (8) | **no** (4) | **no cumple** (1/3) |
| C4 | cumple | cumple | cumple | cumple |
| C6 (D-063) | cumple | cumple | cumple | cumple |
| C7 (D-048) | cumple | cumple | cumple | cumple |
| HU0017-1 (D-064) | cumple | cumple | cumple | cumple |

### 4k.4 Estado de US07–US28 y US38 tras la tanda (reemplaza a 4j.4 en estas filas; el resto sigue igual que 4j.4)
| US | Estado | Evidencia | Pendiente |
|---|---|---|---|
| US07 | **No cumple** (-1 con visual) | C1 (D-023) falla en V1 (7 ventanas < 29.0, mín. 22.2); cumple en 155202 y V2. -2 parcial (4h.5) | Ale decide (P-004); causa de las ventanas bajas `[POR COMPLETAR]` |
| US08 | **Cumple** | -1 (D-048): 6.83–7.26 datos nuevos por mano/s ≥ 5 en las 3 corridas; -2 (D-025) | — |
| US14 | **Cumple** | -1: segunda captura (`sesiones/us14_consola_edge_20261112b.png`, Ale, 12/11): página tras "Empezar" ("No te veo", "Terminar"), consola con **0 errores**: Tone.js v14.7.77, 1 aviso de `ScriptProcessorNode` y 12 de autoplay de antes del clic. Primera captura (`…_20261112.webp`): 1 error de WebSocket antes de que Python abriera el socket. -2 (4h.1) | — |
| US17 | **Cumple** | Saltos 0.20 / 0.34 / 0.27 por s ≤ 0.5 (D-064); rango p5–p95 0.00–0.94/0.97 | — |
| US23 | **No cumple** (-1 con visual) | C3: 8 (V1) y 4 (V2) muestras de (b) > 100 ms; 155202 0. -2: `[PERF]` y `lag_cam_ms` por etapa (cumple) | Ale decide (P-004, D-059); causa `[POR COMPLETAR]` |
| US24 | **Parcial** | -1: 0 % > 250 ms en las 3 corridas (Edge + JBL, D-059). -2: sin marca de incumplimiento (fase 1c) | Ale decide si -2 basta |
| US26 | **Parcial** | 3 corridas de 10 min con visual sin fallos de módulo (cierre normal; consolas no guardadas) | Consolas de Python en `sesiones/` |
| US38 | **Parcial** | -5 C6 cumple en las 3 corridas (D-063); -1/-2/-3 implementados (las capturas de US14 muestran "Te veo" / "No te veo", "Terminar" y anillos); -4 destellos en `?demo=1` | URL de cuestionarios; -6 revisión de Ale y la profesora |

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
- H7 (05/11, hipótesis de Ale): la caída de ≈ 290 s y el escalón posterior se deben al apagado de pantalla de Windows tras 5 min de inactividad.
  - **MEDIDO (4g):** con pantalla en 5 min el corte aparece en 2 de 2 grabaciones sin `main.py` (A1, A3) y en 7 de 7 corridas, siempre 4.5–5.05 s antes de la entrada en espera moderna (Kernel-Power 506). Con "Nunca" no aparece en A2 ni en la corrida 171135, que tampoco tiene 506 ni escalón.
  - **INFERIDO, con evidencia fuerte:** la causa es la transición a la espera moderna que sigue al apagado de pantalla.
  - **Sin comprobar:** el mecanismo dentro de Windows, el USB o el SDK. Hay n = 1 grabación y 1 corrida con "Nunca".
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
Tarea 2 (reducción del ciclo). Un paso por commit; cada paso se mide con el protocolo de la sección 10. Orden del 02/11 (7 → 10 → 5 → 5b): **HECHO**. Ale decidió D-012 (sin ventana), D-013 (decodificación en el hilo; condición cumplida con reservas el 04/11), D-014 (máximo rendimiento) y D-015 (decodificación en el hilo por defecto). Paso 9 corrido el 04/11 (4e y 4f), pero **las corridas tienen evento 506 y quedan fuera de protocolo (D-018, 05/11)**: el paso 9 vuelve a PENDIENTE. Prueba A HECHA el 05/11 (4g). **07/11:** paso 14 HECHO (tanda sobre `3686feb`, C1–C4 cumplen) y paso 9 cerrado con él; cambios aprobados del 07/11 aplicados (D-025 a D-033); corrida de confirmación sobre `30ccbf7` (4h.5): D-023 cumple, C1 estricto 294/299. **10–11/11 (4i):** visual US38 (pasos 17–18), P-012 cerrada, P-015 aplicada, tanda final sobre `8d58820` (`congelado-11-11` = `medido-final`): C1–C4 cumplen en 3 bases de 10 min y C6 informado; US25, US12 (SIMULADO) y US28 (SIMULADO) hechos offline. **12/11 (4j):** validación con el visual encendido (D-047 a D-059); la tanda (paso 26) **no es válida** (reloj y visual sin dibujar); sin etiqueta `validado-visual`. US14 hecha con captura; D-053/D-054 completadas (D-063, D-064). **12/11 por la tarde (4k):** tanda repetida, válida por protocolo; con el visual encendido US08, US14 y US17 cumplen; US07 (C1) y US23 (C3) no cumplen. Registro oficial (D-065), etiqueta `medido-visual` en `1d70ce8`. **Siguiente:** decisión de Ale sobre US07/US23 (P-004) y P-021; US20 con evidencia guardada; refactor KISS (regla 13). Pasos 11 (método A) y 13 quedan sin hacer en TP1.
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
| 8 | Pipeline de 2 etapas (H5) solo si 5–11 no cumplen C1 | CONDICIONAL. En las corridas del 04/11 C1 estricto no se cumplió por la ventana #144 y 0–2 ventanas de 29.1–29.3 ciclos/s por corrida (4f). Esas corridas quedan fuera de protocolo (D-018). Se decide después del paso 14 |
| 9 | Corrida de 10 min y verificación de C1–C5 | **HECHO 07/11 con el paso 14** (4h.3: C1–C4 cumplen en 3 corridas de 10 min válidas; C5 con D-025 a D-030 en borrador). Antes, PENDIENTE (05/11, D-018): las corridas del 04/11 tienen evento 506 en la segunda mitad y quedan **fuera de protocolo**; sus datos se conservan (4e, 4f y 4g.2). Se cierra con el paso 14. Corrido el 04/11 (4e y 4f). Mañana: 144401 con VS Code abierto (no cumple C1 estricto ni C3 máx); 153328 Base, 154420 decodificación y 155449 control. Tarde: corrida quieta 170136 y **3 corridas finales** 171221, 172514 y 173544 con la configuración por defecto: **C1 estricto no cumple** (297/301, 302/303 y 299/302 ventanas ≥ 29.5 sin #0); **C2–C5 cumplen**. Condición de D-013 cumplida con reservas; D-015 (`9ecf383`). Métrica de HU0008-1 abierta (P-009) |
| 10 | Repetir la línea base MJPG: 1 pestaña, calentamiento descartado, plan de energía de máximo rendimiento, 3 corridas de 3 min | HECHO 02/11 (133512, 133838, 134201; 4c). La comparación 1 vs 2 hilos de D-003 **no** se repitió |
| 11 | Método para medir (c) extremo a extremo (US23): micrófono o loopback, y latencia interna del SDK | PENDIENTE (decide Ale el método; no bloquea 7 ni 10) |
| 12 | **Prueba A de cámara**: grabar 6 min solo con la cámara (sin tracker, sin MediaPipe, sin Python) y buscar el hueco de la caída. Comando: `"C:\Program Files\Azure Kinect SDK v1.4.1\tools\k4arecorder.exe" -c 720p -d NFOV_UNBINNED -r 30 --imu ON -l 360 sesiones\camara_A1.mkv`. Modos iguales a `main.py` líneas 196–200: color 720p MJPG (`-c 720p`; NV12 y YUY2 son modos aparte), profundidad `NFOV_UNBINNED`, 30 fps, sin sincronización externa (Standalone, el valor por defecto). IMU encendida porque `pykinect` la arranca en `Device.start` (`start_imu()`). `main.py` usa `synchronized_images_only = False`; qué hace `k4arecorder` con eso `[POR COMPLETAR]`. Comprobar en el MKV que el formato de color grabado es MJPG. Mismo salón, persona quieta delante, `main.py` cerrado (la cámara es exclusiva), registros de GPU, CPU y procesos encendidos; si se puede, 2 grabaciones. Análisis (script de solo lectura con la reproducción de `pykinect_azure`): por captura, si hay color y profundidad y su marca de tiempo del dispositivo; saltos > 50 ms entre marcas de color, capturas incompletas y frames frente a 30 × duración; **hueco buscado entre 270 y 310 s** desde el primer frame. Límite: el MKV no guarda la hora de llegada al PC. Disco: **≈ 17.9 GB por grabación** (MEDIDO 05/11: 17.7–17.9 GB, ≈ 3 GB/min, incluye el IR; la estimación previa de ≈ 7.8 GB era errónea). `sesiones/*.mkv` está en `.gitignore` (`2d3920a`) | **HECHO 05/11** (4g.1): A1 (pantalla en 5 min) y A3 (control, 5 min) muestran el corte a ≈ 295 s del reloj del dispositivo; A2 ("Nunca") no. `synchronized_images_only` de `k4arecorder`: se comporta como `False` (INFERIDO) |
| 12b | **Prueba B de cámara**: script aparte (`prueba_camara.py`, sin tocar `main.py`) que abre la Kinect con el mismo `device_config`, sin tracker ni manos ni WebSocket, lee todas las capturas sin descartar y guarda por captura `t_perf`, las marcas de tiempo del sistema y del dispositivo de color y profundidad, `ok_color` y `ok_depth`. Ve también la entrega al PC | NO SE HACE: la prueba A mostró el hueco (condición no cumplida) |
| 13 | Función que pide a Windows mantener la pantalla encendida mientras corre `main.py` (`SetThreadExecutionState` con `ES_CONTINUOUS \| ES_SYSTEM_REQUIRED \| ES_DISPLAY_REQUIRED`), como opción apagable por línea de comandos con sufijo en `VERSION_MAIN` y campo en la cabecera de `_perf.txt` (D-021). Se pide en el hilo del event loop antes de `start_device` y se suelta en el cierre; verificar con `powercfg /requests` (administrador). No cambia el comportamiento musical (C5); afecta a la condición de medida de C1 (HU0007-1) | PENDIENTE (sesión siguiente; aprobada por Ale el 05/11) |
| 14 | Tanda nueva con pantalla en "Nunca" (D-017) y regla de reloj (D-019): `w32tm /resync` antes, calentamiento + 3 corridas de 10 min con la configuración por defecto y Edge (D-020); comprobar que no hay Kernel-Power 506 durante las corridas. Cierra el paso 9 | **HECHO 07/11** (4h.3): 163615, 165040 y 170224 sobre `3686feb`, válidas por reloj y sin 506; C1–C4 cumplen en las 3; C5 con los cambios del 07/11 (D-025 a D-030, borrador) |
| 15 | Cambios aprobados del 07/11 con prueba unitaria (`pruebas_unitarias.py`, 23/23) y prueba en vivo: 1, 2, 3, 5, 6, rango de apertura, 4, 7, 7b; registro `[PIERNAS]`; `--tempo-medium` (apagada) | HECHO 07/11 (4h.2, 4h.5; D-025 a D-033 en borrador) |
| 16 | Corrida de confirmación de 10 min sobre el commit final | HECHO 07/11 (180729, `30ccbf7`): válida; D-023 cumple; C1 estricto 294/299 y C3 máx 127.2 ms (1 muestra) no cumplen. Repetir con registros de GPU, CPU y procesos para ver la causa de las ventanas de 29.1–29.3 `[POR COMPLETAR]` |
| 17 | Visual "Ondas" US38 (solo navegador): anillos, "Te veo"/"No te veo", pantallas de inicio y cierre, `?visual=0`, `?demo=1`, filas `config`/`visual`/`cuadro_*` | HECHO (`f873c5f`; tope 30 y punteado `3d55697`; umbrales 0.25/0.5 `8d58820`). Escalera y valor por defecto en 4i.2 (D-041, D-042) |
| 18 | P-015: columnas `edad_izq_ms` / `edad_der_ms` (solo medición) | HECHO 10/11 (`23cd4fe`; costo aislado ≈ 0.002 ms/ciclo; 4i.4) |
| 19 | P-012: A/B de `--tempo-medium` (3 pares, regla fijada antes) | HECHO 10/11: no se adopta (B gana 1/3; 4i.3, D-037) |
| 20 | Tanda final: 3 bases de 10 min (`?visual=0`) + C6 (visual) + bases de control, con registros de GPU, CPU y procesos | HECHO 11/11 sobre `8d58820` (4i.5). Base 1 y 2 repetidas por procesos externos (D-046). Etiquetas `congelado-11-11` y `medido-final` (D-043) |
| 21 | US25 (pruebas por módulo), US12 (escalón SIMULADO), US28 (escenarios con semilla, SIMULADO) | HECHO 11/11 (`7c9e0a1`, `fab4f7b`; 4i.6). Umbrales de US28 `[POR CONFIRMAR]` (P-018) |
| 22 | US14: captura de la consola de Edge **después** de pulsar "Empezar", con Python en marcha | HECHO 12/11 (`sesiones/us14_consola_edge_20261112.webp`; 4j.4) |
| 23 | US20: prueba de percepción (Ale, autovalidación declarada como limitación), con visual y preguntas separadas (D-055) | PENDIENTE (12/11: sin registro) |
| 26 | Tanda de validación con visual (D-047, D-050): 155202 + V1 y V2 de 10 min + control de 3 min; `analisis_visual.py`; etiqueta `validado-visual` en `8d58820` si es válida | **NO VÁLIDA 12/11** (4j): V1, V2 y control fallan D-019 (reloj); V2 y control sin dibujo; V1 no cumple C1 ni C2. Sin etiqueta. Repetir V1, V2 y control (D-060, D-061, D-062). **Repetida 12/11 por la tarde (4k):** 155642, 161012 y 162149 válidas por protocolo (sin registros de procesos); C4, C6, C7 y HU0017 cumplen; C1 y C2 fallan en V1 y C3 en V1 y V2. **Registro oficial (D-065)**; etiqueta `medido-visual` en `1d70ce8` (sin `validado-visual`) |
| 24 | Manos con el visual encendido (≈ 7 datos/mano/s frente a ≈ 14) | Limitación informada (4i.2); causa `[POR COMPLETAR]`; opciones en P-017 |
| 25 | Refactor KISS (regla 13) en `refactor/kiss` desde `medido-final` | PENDIENTE (12/11) |
Fuera de este plan: `latencia_interna_SDK` `[POR COMPLETAR]`.

## 10. Protocolo de corrida (repetible)
0. **Antes de la tanda (D-017, D-019, 05/11).**
   - **Pantalla:** "Apagar la pantalla tras" en **"Nunca"**. Comprobar con `powercfg /query SCHEME_CURRENT SUB_VIDEO VIDEOIDLE`: índice CA `0x00000000`. Con 5 min (`0x12c`) Windows entra en espera moderna a los ≈ 300 s y la Kinect se corta (4g).
   - **Modo de energía:** se fija con el deslizador "Modo de energía: Mejor rendimiento" de Windows (Configuración > Sistema > Energía), no con el plan de `powercfg`, que sigue mostrando "Equilibrado". Comprobar con `reg query "HKLM\SYSTEM\CurrentControlSet\Control\Power\User\PowerSchemes" /v ActiveOverlayAcPowerScheme`: debe dar `ded574b5-45a0-4f42-8737-46345c09c238`. Que ese GUID sea "Mejor rendimiento" es según la documentación de Microsoft, no verificado por Code; es el valor leído el 05/11 con el deslizador en "Mejor rendimiento".
   - **Hora:** ejecutar `w32tm /resync` (terminal de administrador, con internet) y comprobar con `w32tm /query /status` que la "Última sincronización de hora correcta" es reciente.
   - **Interrupciones (D-051, 12/11):** "No molestar" activado; `msmpeng` y `searchindexer` en reposo antes de empezar (Administrador de tareas); la app de Claude minimizada y sin uso durante las corridas.
   - **Visual (D-047, 12/11):** `index.html` sin parámetros en Edge en GPU integrada (comprobar en `edge://gpu`), una pestaña, "Empezar" pulsado. Después de cada corrida, `analisis_visual.py <id>` debe mostrar filas de C6 (tiempo por cuadro y latencia visual); si no las hay, el visual no dibujó (4j.1) y la corrida no cuenta. Edge maximizado y al frente toda la corrida; Ale anota cómo estaba en cada corrida (D-061).
   - **Servicio de hora (D-060, 12/11):** al inicio de la tanda, `w32tm /resync`, comprobar con `w32tm /query /status` y luego `net stop w32time` (administrador); comprobar con `sc query w32time` que dice `STOPPED` antes de cada corrida (es un servicio que Windows puede volver a arrancar por sí solo). Al terminar la tanda, `net start w32time` y `w32tm /resync`.
   - **Repetición (D-062, 12/11):** una corrida se repite solo por invalidez de protocolo (506, reloj, visual sin dibujar, proceso ajeno medido). Si con reloj válido y el visual dibujando no cumple, se informa como fallo y no se repite.
1. Laptop enchufada, modo de energía de **máximo rendimiento** (requisito de operación, D-014; en Equilibrado la corrida salió más lenta, 4d), solo **Edge** (D-020; anotar el navegador en cada tanda) con **una sola pestaña** de `index.html` (ninguna otra pestaña ni navegador integrado de Code con la página abierta), misma distancia (de pie), misma luz y el mismo salón para toda la tanda. Antes de empezar, revisar en el Administrador de tareas que ningún otro proceso use la CPU de forma sostenida. Segunda terminal: `nvidia-smi --query-gpu=timestamp,clocks.sm,clocks.max.sm,temperature.gpu,power.draw,clocks_throttle_reasons.active --format=csv -l 1 -f sesiones\gpu_<tanda>.csv`. Tercera terminal (Símbolo del sistema como administrador; contadores localizados en español): `typeperf "\Información del procesador(_Total)\% de rendimiento del procesador" "\Información del procesador(_Total)\% de tiempo de procesador" -si 1 -o sesiones\cpu_<tanda>.csv`. Cuarta terminal (uso de CPU por proceso, H6; desde el 04/11): `powershell -ExecutionPolicy Bypass -File registrar_procesos.ps1 sesiones\procesos_<tanda>.csv` (columnas `t_local, proceso, pid, cpu_pct`; `cpu_pct` en % de un núcleo lógico, 12 núcleos = 1200 %). Arrancar las tres antes de la primera corrida y detenerlas con Ctrl+C al terminar la tanda.
1b. Una corrida de calentamiento de ≈ 1 min que se descarta (31/10: la 1ª corrida de la tanda MJPG salió ≈ 7 ms más lenta en todas las etapas). Filtro: si `[PERF-LINEA]` muestra `to_numpy` ≥ 8 ms/llamada, el equipo está lento (02/11: 144008 dio 9.4 ms); esperar, revisar procesos y repetir el calentamiento.
2. `python main.py cuda lite [--sin-decod-hilo] [--swi1ms] [--sin-manos] [--con-ventana]` (D-011; sin ventana por defecto desde D-012, `--con-ventana` solo para depurar; decodificación en el hilo por defecto desde D-015, `--sin-decod-hilo` para decodificar en el ciclo). VS Code cerrado (04/11: con VS Code abierto el ciclo empeora, 4e). Misma ropa en toda la tanda, anotada (04/11: pantalón ancho; rodillas más ruidosas, 4e); esperar 5 s (el navegador tarda hasta ≈ 5 s en reconectarse y esas filas faltan en `_latencias.csv`); rutina fija de 3 min: 30 s quieto, 60 s brazos arriba y abajo, 60 s baile amplio, 30 s abrir y cerrar manos con las dos manos visibles. No recargar la pestaña entre corridas.
3. **Un** Ctrl+C en la consola para cerrar (con `--con-ventana`, `q` en la ventana) y esperar a "Kinect cerrada correctamente". Quedan en `sesiones/` el CSV de sesión, `_perf.txt` y `_latencias.csv`. Comprobar que las filas `continuo` de `_latencias.csv` ≈ filas del CSV de sesión (si son el doble, había 2 clientes: repetir). La configuración queda en el nombre (sufijo de `VERSION_MAIN`). No usar `Start-Transcript` (no graba la salida de Python).
3b. **Validez (D-018, D-019, 05/11).**
   - **Reloj:** si la media de `transporte_ms` (filas `continuo`) de los últimos 30 s se aleja más de ±1 ms de la de los primeros 30 s, la corrida se repite (05/11: 1.97 → −36.71 ms, 4g.3).
   - **Espera moderna:** si durante la corrida hay un Kernel-Power 506, la corrida queda fuera de protocolo y se repite; no se excluyen ventanas de C1. Para revisarlo: `Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='Microsoft-Windows-Kernel-Power'; Id=506,507; StartTime=(Get-Date).AddHours(-2)}`.
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
- Riesgo para HU0008-1 con decodificación en el hilo: medido el 04/11 (4e), sin empeorar frente a Base en la misma sesión, con reservas (n = 1; tendencia de trabajos/s 29.7 → 26.9 en 10 min). **Actualizado 04/11 tarde (4f):** las 3 corridas finales repiten la bajada (≈ 29.8 → 26.3–27.8 por tercios); es sobre todo un escalón después de la caída de ≈ 290 s (29.7–29.9 → 26.6–27.8 trabajos/s), no una deriva continua. Causa del escalón `[POR COMPLETAR]`. **05/11 (4g):** el escalón coincide con el periodo de espera moderna de Windows y no aparece con la pantalla en "Nunca" (171135, n = 1).
- `[POR COMPLETAR]` métrica de HU0008-1: frames procesados por segundo o actualizaciones por mano (P-009). Hasta fijarla, "HU0008-1 cumple o no" queda abierto.
- ~~Causa de la caída a los ≈ 290 s (persona detrás o evento de la cámara).~~ **05/11 (4g, H7):** está asociada a la entrada de Windows en espera moderna tras el apagado de pantalla. Aparece sin `main.py` (A1, A3) y desaparece con "Nunca" (A2, 171135). La hipótesis "persona detrás" no explica la coincidencia de 5.0 s con el 506 en 7 de 7 corridas (INFERIDO); no se verificó quién estaba en el salón.
  - `[POR COMPLETAR]` mecanismo: por qué esa transición corta el flujo USB de la Kinect (profundidad, color e IMU) y qué hace Windows en los ≈ 5 s anteriores al 506.
- `[POR COMPLETAR]` mecanismo del escalón de trabajos/s y `lag_cam_ms` durante la espera moderna (4f, 4g.2).
- `[POR COMPLETAR]` por qué el SDK registra solo 10 `capturesync_drop` cuando el MKV tiene 12–14 capturas solo color (4g.1).
- `[POR COMPLETAR]` consolas de A1 y A2 en `sesiones/` (las pega Ale) para contrastar los 10 mensajes de A1 y la consola limpia de A2.
- `[POR COMPLETAR]` si en A2 la suspensión también estaba en "Nunca" (Ale cambió la pantalla desde la configuración de Windows).
- `[POR COMPLETAR]` rutina hecha en la corrida 171135 (7 min).
- (a) y (b) dependen de que el reloj de Windows no se corrija durante la corrida: `ahora_ms()` ancla `time.time()` una sola vez (4g.3). Regla de validez en la sección 10 (D-019). Cambiar el cálculo de (a)/(b) sería un cambio de definición (D-009) y no se hace.
- Git (05/11): `sesiones/gpu_20261031.csv` estaba recortado en la copia de trabajo (2134 de 2626 líneas; faltaban del 31/10 18:00:02 al 01/11 11:55:22, fecha de modificación 02/11 13:23, causa desconocida) y `sesion_file.csv` (formato antiguo, commit `f970444`, lo usa `grafico.py:24` como respaldo) estaba borrado sin commit. Ambos restaurados desde HEAD (D-022); la línea base de 4b (17:14–17:23 del 31/10) no estaba afectada.
- `[POR COMPLETAR]` por qué `mapeo` sube de ≈ 1 a ≈ 2 ms en los primeros ≈ 5 min con decodificación en el hilo (4f; con resolución de 1 ms).
- ~~Navegador del protocolo (P-010).~~ **05/11: Edge, anotado en cada tanda (D-020).** `[POR COMPLETAR]` en qué navegador se hicieron las tandas anteriores al 04/11 por la tarde.
- `[POR COMPLETAR]` ropa en las corridas del 02/11 (para comparar el ruido de rodilla, 4e). 04/11 mañana y tarde: pantalón ancho (baggy). 07/11: short y polo blanco (4h.4: rodillas más quietas con short, INFERIDO, n pequeño).
- 07/11 `[POR COMPLETAR]`: causa de las 5 ventanas de 29.1–29.3 ciclos/s y de la muestra de (b) de 127.2 ms en 180729 (sin registro de procesos).
- 07/11 `[POR COMPLETAR]`: medir directamente las actualizaciones por mano (instante del último dato por mano); hoy solo se aproximan por los cambios de valor (4h.5).
- 07/11 `[POR COMPLETAR]`: por qué las articulaciones de mano del Kinect salen NONE en el 100 % (antes ≈ 53 %).
- 07/11 `[POR COMPLETAR]`: navegador (Edge) y consola sin errores de US14 dichos por Ale; no guardados. **11/11:** captura guardada (`sesiones/us14_consola_edge_20261111.png`), pero de antes del clic; falta la de después de "Empezar".
- 11/11 `[POR COMPLETAR]`: causa de que el hilo de manos vaya a la mitad con el visual encendido (4i.2; P-017).
- 11/11 `[POR COMPLETAR]`: confirmar que Edge estaba en GPU integrada en la ronda y la tanda del 11/11; propósito de la corrida 172140 (35 s); ropa del 10/11; consolas de Python de las corridas de 10 min del 11/11 (están en el equipo de Ale; copiarlas a `sesiones/` para US26).
- 11/11 `[POR COMPLETAR]`: estado degradado del equipo en 165523 (10/11) sin causa registrada (no había `typeperf`).
- 11/11: (c) solo como cota INFERIDA (método B, 4i.6); el método A (celular en cámara lenta) no se probó.
- 12/11 `[POR COMPLETAR]`: propósito de 132848, 140411 y 143303; evidencia de US20 y US38; consolas de Python. (US14: captura guardada; JBL: siempre, dicho por Ale.)
- 12/11 `[POR COMPLETAR]`: por qué V1 (y el calentamiento) tuvieron `tracker` ≈ 27 ms y `dwm` 30–46 % frente a 23.8 ms y 8 % en 155202 (4j.2).
- 12/11 `[POR COMPLETAR]`: registros de GPU, CPU y procesos de la tanda repetida (155642, 161012, 162149) — no están en `sesiones/`; causa de las ventanas bajas y de las muestras de (b) > 100 ms de V1 (576–590 s) y V2 (4j/4k).
- 12/11: la regla de reloj (D-019) puede fallar aunque se haga `w32tm /resync` justo antes: el sondeo siguiente (≈ 17 min después) corrigió la hora durante V1, V2 y el control (INFERIDO; 4j.1). Propuesta P-019.
- 11/11: hallazgo de US25 sin arreglar (código congelado): `angulo_articulacion` da 179.9974° con vectores unitarios; sin efecto práctico en mm.
- Pendiente de datos (no medido): confianza de rodillas y tobillos en el CSV. Ale observó el 31/10 más movimiento falso de piernas al subir los brazos; en las sesiones 164334/164633 la mediana de la velocidad de rodilla es 35–111 °/s con los hombros a 45–135° (11–16 °/s quieto con los brazos abajo), y eso sube el tempo.
- Garantía FIFO del SDK al vaciar la cola: INFERIDA; las cifras de `lag_cam_ms` la respaldan.