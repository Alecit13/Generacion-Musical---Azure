# MEDICIONES — línea base, hipótesis y plan (corte: 31/10/2026)

> Este archivo CAMBIA en cada sesión. Cada cifra cita su origen. MEDIDO = salió de un CSV o log. INFERIDO = deducción no comprobada.

## 0. Corrección importante
Las cifras de RNF01 que se usaron en ESTADO_ACTUAL y en borradores del short paper (media 58–62 ms, p95 78–83, máx 112–115) **no salen de los CSV del navegador del 28/10**. La media coincide con el CSV del 19/10 (media 59.2, p95 64.3, máx 104.9; cifras citadas en la auditoría de Code, CSV no revisado por Ale en esta sesión), cuando el ciclo duraba 58–63 ms. No se encontró el origen de p95 78–83 ni de máx 112–115. **No usar esas cifras.** Hipótesis H2 (58–62 = latencia + espera de cámara): REFUTADA.

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
- El corte barato real es la decodificación MJPG (el SDK entrega MJPG por defecto), no la profundidad ni la copia. INFERIDO: el `imdecode` es casi todo el `cap_imgs` de 6–7 ms.

## 5. Otras cifras vigentes (de ESTADO_ACTUAL, sesiones 26–28/10)
- Jitter con suavizado: hombros −22% a −32%; rodilla −52% a −53% (dos sesiones).
- Articulaciones de manos del Kinect sin valor (NONE) ≈ 53% de los frames; las otras 26 ≈ 100%.
- MediaPipe: ≥ 1 mano en 86–96% de los ciclos; ≈ 13 actualizaciones/s por mano con 1 hilo.
- Aciertos del recuadro por origen (log `[ROI]`, ventanas de 60 ciclos): muñeca 92–100% casi siempre; mano 51–100% con pocos intentos.

## 6. Estado de las hipótesis
- H1 (la espera de cámara baja si el ciclo baja de 33.3 ms): COMPATIBLE, NO PROBADA. Bajaría hacia la latencia interna del SDK, no a 0.
- H2: REFUTADA.
- H3 (`lat_tick` ≈ etapas previas + espera hasta el siguiente ciclo): CONSISTENTE con 47.6–51.2 ms.
- H4 (cortes baratos): el corte con evidencia es la decodificación MJPG; `flush`/`print` valen centésimas de ms aislados.
- H5 (pipeline en 2 etapas): POSIBLE (las DLL se cargan con `ctypes.CDLL` y sueltan el GIL en la llamada nativa), pero 1→2 hilos de manos ya costó ≈ 3.6 ms de ciclo: NO es gratis; medir antes de asumir solapamiento.

## 7. Presupuesto (INFERIDO)
- Tracker 23–24 ms es el piso. Para 33.3 ms quedan ≤ 9.8 ms para todo lo demás; hoy son 15–17 ms.
- Con `BGRA32` o decodificación en otro hilo (ahorro estimado 4–5 ms) y sin ventana de dibujo: ciclo ≈ 31.5 ms (margen ≈ 2 ms); si `mapeo` baja a lo medido aislado: ≈ 28.5 ms (margen ≈ 5 ms).
- Aviso: con `DIBUJAR_CADA=3`, cada tercer ciclo paga ≈ 7–9 ms y dispara el p95.

## 8. Parámetros que dependen de la tasa de ciclos (cambian si se pasa de ≈ 24 a 30 Hz)
- `UMBRAL_ESTABILIDAD_ZONA = 6` ciclos: ≈ 250 ms hoy → ≈ 200 ms a 30 Hz. (`zona.py`: 6 frames, solo si `REGISTRO_POR_ANGULO=False`.)
- `EMA_ANGULO_BRAZO = 0.5` y `EMA_VEL_RODILLA = 0.4`: retardo ≈ (1−α)/α · ciclo (41 → 33 ms y 61 → 50 ms).
- `len(hist) >= 5` y `len(recientes) >= 4`; el tick se evalúa una vez por ciclo.
- Sin efecto musical: `DIBUJAR_CADA`, `REPORTE_CADA`, `MAX_DESCARTE_POR_CICLO`.
- En segundos (no cambian): `VENTANA_INTENSIDAD_S`, `VENTANA_FLUIDEZ_S`, `NORM_VENTANA_S`, `NORM_CALENTAMIENTO_S`, `HOLD_ANGULO_S`, `HOLD_APERTURA_S`, `VENTANA_FUSION_MS`, `intervalo_s`, `dt` real de `VelocidadAngular`.

## 9. Plan vigente
Tarea 1 (auditoría de solo lectura): **HECHA el 31/10/2026** (resultados arriba).
Tarea 2 (reducción del ciclo). Un paso por commit; cada paso se mide con el protocolo de la sección 10.
| # | Paso | Estado |
|---|---|---|
| 1 | Commit del estado actual en la rama `wip-28e` (hay cambios sin commit en `main.py`, `servidor.py`, `index.html`) | PENDIENTE |
| 2 | Rama `perf/ciclo-30hz` y `HILO_POR_MANO=False` (ver D-003; Ale confirma) | PENDIENTE |
| 3 | Cronómetros por línea en `[PERF]` para `to_numpy()`, `print` e `imshow`, sin cambiar comportamiento | PENDIENTE |
| 4 | Línea base: 3 corridas de 3 min con la rutina fija (sección 10) | PENDIENTE (requiere Kinect y persona) |
| 5 | `BGRA32` (o decodificar en el hilo de manos) y sin ventana en sesiones de evaluación; volver a medir | PENDIENTE |
| 6 | Decidir histéresis y EMA en milisegundos (ver D-005) | PENDIENTE (decide Ale) |
| 7 | Enviar `lag_cam_ms` en el mensaje para calcular la latencia por muestra desde la llegada al PC | PENDIENTE |
| 8 | Pipeline de 2 etapas (H5) solo si 1–7 no cumplen C1 | CONDICIONAL |
| 9 | Corrida de 10 min y verificación de C1–C5 | PENDIENTE |
Fuera de este plan (US23): latencia total hasta el sonido (micrófono o loopback), `latencia_interna_SDK` `[POR COMPLETAR]`.

## 10. Protocolo de corrida (repetible)
1. Laptop enchufada, modo de máximo rendimiento, solo Chrome con `index.html`, misma distancia (de pie) y misma luz. Segunda terminal: `nvidia-smi --query-gpu=clocks.sm,clocks.max.sm,temperature.gpu,clocks_throttle_reasons.active --format=csv -l 1`.
2. `python main.py cuda lite`; esperar 5 s; rutina fija de 3 min: 30 s quieto, 60 s brazos arriba y abajo, 60 s baile amplio, 30 s abrir y cerrar manos con las dos manos visibles.
3. `q` para cerrar; descargar el CSV de latencias; conservar el CSV de `sesiones/`. Nombrar la configuración en `VERSION_MAIN`.
4. 3 corridas por configuración; comparar promedios (una sola corrida engaña: 28d→28e varió 38.4→42.0 ms). No cambiar código entre corridas de la misma configuración. No mezclar con pruebas de sonido.

## 11. Pendientes y huecos
- `[POR COMPLETAR]` perfil de un ciclo real con cronómetros por línea (paso 3–4).
- `[POR COMPLETAR]` latencia interna del SDK entre `system_timestamp` y la disponibilidad del capture.
- `[POR COMPLETAR]` latencia real hasta el sonido (US23).
- `[POR COMPLETAR]` origen de las cifras RNF01 p95 78–83 y máx 112–115 (o descartarlas).
- Garantía FIFO del SDK al vaciar la cola: INFERIDA; las cifras de `lag_cam_ms` la respaldan.
