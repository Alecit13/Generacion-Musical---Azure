"""analisis_visual.py — análisis de SOLO LECTURA de corridas (D-047 a D-054, 12/11/2026).

Uso:  python analisis_visual.py 155202 160340 [más ids] [--procesos sesiones/procesos_X.csv] [--salida archivo.md]

Por cada id busca en sesiones/ el CSV de sesión, su _latencias.csv y su _perf.txt y calcula:
  validez (D-018 se revisa aparte con Get-WinEvent; aquí: un cliente, filas que faltan, reloj D-019),
  C1 (D-023 y estricto, D-016), cap_update, tracker, C2, C3 ((b) y (a)), C4, datos nuevos por mano/s (C7, D-048),
  C6 (tiempo por cuadro y latencia visual, D-053), métricas musicales con los métodos de MEDICIONES 4h
  (saltos de apertura01, rango, zona, tempo, edad de manos, racha, semilla, χ² de HU0019-3, % ciclos > 33.3 ms)
  y, si se da --procesos, los procesos ajenos con uso alto durante la corrida.
Las corridas con el visual encendido (fila "config" = 1) y sin visual se resumen en dos columnas de rango aparte.
No escribe nada en sesiones/ salvo que se pida --salida. Usa muestreo.py solo para repetir el sorteo con la semilla.
"""
import csv
import glob
import math
import os
import statistics as st
import sys
from datetime import datetime

import muestreo

CARPETA = "sesiones"
UMBRAL_B_MS = 100.0          # HU0023-1
UMBRAL_TICK_MS = 250.0       # HU0024-1
UMBRAL_LAG_P95 = 27.1        # C2 (D-049)
UMBRAL_DATOS_MANO = 5.0      # C7 (D-048)
UMBRAL_CUADRO_P95 = 16.7     # C6 (D-053)
UMBRAL_VISUAL_P95 = 100.0    # C6 (D-053, D-063)
UMBRAL_SALTOS_AP = 0.5       # HU0017-1: saltos de apertura01 > 0.3 por segundo (D-054, D-064)
CRECIMIENTO_MAX_MS = 1.0     # C2 "sin crecimiento": p95 del último minuto − p95 del primero ≤ esto [POR CONFIRMAR]
RANGOS_LAMBDA = [(0.05, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0001)]   # MEDICIONES 4h.5
CHI2_3GL_95 = 7.81


# ---------------------------------------------------------------------------- utilidades
def pct(xs, q):
    """Percentil con interpolación lineal (igual que numpy por defecto)."""
    xs = sorted(xs)
    if not xs:
        return math.nan
    k = (len(xs) - 1) * q / 100.0
    f = math.floor(k)
    c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def cargar(id_corrida):
    rutas = [r for r in glob.glob(os.path.join(CARPETA, f"sesion_*_{id_corrida}_*cuda-lite.csv"))
             if not r.endswith("_latencias.csv")]
    if len(rutas) != 1:
        raise SystemExit(f"{id_corrida}: se esperaba 1 CSV de sesión y hay {len(rutas)}")
    base = rutas[0][:-4]
    sesion = list(csv.DictReader(open(rutas[0], newline="", encoding="utf-8")))
    lat = list(csv.DictReader(open(base + "_latencias.csv", newline="", encoding="utf-8")))
    perf = open(base + "_perf.txt", encoding="utf-8").read().splitlines()
    return os.path.basename(rutas[0]), sesion, lat, perf


# ---------------------------------------------------------------------------- bloques de métricas
def ventanas_perf(perf):
    """Una entrada por línea [PERF]: ciclos/s, cap_update, tracker y trabajos/s del hilo de manos."""
    v = []
    for linea in perf:
        if not linea.startswith("[PERF] "):
            continue
        partes = dict(p.split("=", 1) for p in linea.split(" | ")[1:] if "=" in p)
        v.append({
            "cps": float(linea.split()[1]),
            "cap_update": float(partes["cap_update"].rstrip("ms")),
            "tracker": float(partes["tracker"].rstrip("ms")),
            "trab_s": float(partes["hilo_manos"].split("(")[1].split()[0]),
        })
    return v


def validez(sesion, lat):
    """Un solo cliente, filas `continuo` que faltan al arrancar y después, y deriva del reloj (D-019)."""
    cont = [r for r in lat if r["tipo"] == "continuo"]
    t_cap_cont = sorted(num(r["t_epoch_ms"]) - num(r["latencia_ms"]) for r in cont)
    import bisect

    def llego(t):
        i = bisect.bisect_left(t_cap_cont, t - 1.0)
        return i < len(t_cap_cont) and t_cap_cont[i] <= t + 1.0

    llegadas = [llego(float(r["t_cap_ms"])) for r in sesion]
    primera = llegadas.index(True) if True in llegadas else len(llegadas)
    t0 = num(cont[0]["t_epoch_ms"]) if cont else 0
    t1 = num(cont[-1]["t_epoch_ms"]) if cont else 0
    ini = [num(r["transporte_ms"]) for r in cont if num(r["t_epoch_ms"]) <= t0 + 30000]
    fin = [num(r["transporte_ms"]) for r in cont if num(r["t_epoch_ms"]) >= t1 - 30000]
    delta = st.mean(fin) - st.mean(ini) if ini and fin else math.nan
    return {
        "filas_sesion": len(sesion), "filas_continuo": len(cont),
        "duplicadas": max(0, len(cont) - len(sesion)),
        "faltan_arranque": primera, "faltan_despues": llegadas[primera:].count(False),
        "ultima_llego": bool(llegadas and llegadas[-1]), "delta_transporte": delta,
    }


def config_pagina(lat):
    cfg = next((r for r in lat if r["tipo"] == "config"), None)
    cv = next((r for r in lat if r["tipo"] == "config_visual"), None)
    return {
        "visual": cfg is not None and cfg["latencia_ms"] == "1",
        "hz": cfg["transporte_ms"] if cfg else "",
        "tope": cv["latencia_ms"] if cv else "", "ligero": cv["transporte_ms"] if cv else "",
    }


def por_minuto_p95(ts, xs):
    """p95 por minuto desde la primera fila; solo minutos con ≥ 20 s de datos (≥ 600 muestras a 30 Hz)."""
    cubos = {}
    for t, x in zip(ts, xs):
        cubos.setdefault(int((t - ts[0]) // 60), []).append(x)
    return [pct(v, 95) for k, v in sorted(cubos.items()) if len(v) >= 600]


def datos_nuevos(sesion, col):
    """Veces que baja la edad del último dato de esa mano (P-015): cada bajada es un dato nuevo de MediaPipe."""
    n, prev = 0, None
    for r in sesion:
        e = num(r[col])
        if e is not None and prev is not None and e < prev:
            n += 1
        prev = e
    return n


def distancia(i, j, n=len(muestreo.NOTAS)):
    return muestreo._distancia_circular(i, j, n)


def esperado_sorteo(prev, lam, direccion, racha):
    """Probabilidad de cada nota en un sorteo, con el estado (dirección, racha) que tenía muestreo antes de sortear.
    Repite elegir_siguiente_nota sin sortear: mezcla de 'no invierte' y 'invierte' la dirección de la moda."""
    notas = muestreo.NOTAS
    lam = min(max(lam, 0.0), 1.0)
    lam_ef = min(max((lam - 0.05) / 0.95, 0.0), 1.0)
    i = notas.index(prev)
    p_inv = muestreo.PROB_CAMBIO_DIRECCION * lam_ef
    total = {n: 0.0 for n in notas}
    for invierte, p in ((False, 1 - p_inv), (True, p_inv)):
        if p == 0:
            continue
        d = -direccion if invierte else direccion
        if not 0 <= i + d < len(notas):
            d = -d
        moda = notas[i + d]
        pesos = {n: lam_ef * w + (1 - lam_ef) * (1.0 if n == moda else 0.0)
                 for n, w in muestreo.TABLA_PESOS[prev].items()}
        if racha >= muestreo.MAX_REPETICIONES:
            pesos[prev] = 0.0
        s = sum(pesos.values())
        for n in notas:
            total[n] += p * pesos[n] / s
    return total


def melodia(sesion):
    """Racha máxima, reconstrucción con la semilla y χ² de pasos por rango de λ (HU0019-3, MEDICIONES 4h.5)."""
    ticks = [r for r in sesion if r["lam_sorteo"] != ""]
    notas_csv = [r["nota"] for r in ticks]
    racha = mx = 0
    for k, n in enumerate(notas_csv):
        racha = racha + 1 if k and n == notas_csv[k - 1] else 1
        mx = max(mx, racha)
    semilla = int(ticks[0]["semilla"]) if ticks else None
    import random
    random.seed(semilla)
    muestreo.reiniciar_estado()
    prev, iguales = "Do", 0                       # main.py: NOTA_INICIAL = "Do"
    obs = {r: [0] * 4 for r in RANGOS_LAMBDA}
    esp = {r: [0.0] * 4 for r in RANGOS_LAMBDA}
    for r_, nota_csv in zip(ticks, notas_csv):
        lam = float(r_["lam_sorteo"])
        e = esperado_sorteo(prev, lam, muestreo._direccion, muestreo._racha)
        nota = muestreo.elegir_siguiente_nota(prev, lam)
        iguales += nota == nota_csv
        rango = next(x for x in RANGOS_LAMBDA if x[0] <= lam < x[1])
        i = muestreo.NOTAS.index(prev)
        obs[rango][distancia(i, muestreo.NOTAS.index(nota_csv))] += 1
        for n, p in e.items():
            esp[rango][distancia(i, muestreo.NOTAS.index(n))] += p
        prev = nota_csv
    chi = {}
    for rg in RANGOS_LAMBDA:
        tot = sum(obs[rg])
        chi[rg] = (tot, sum((o - e) ** 2 / e for o, e in zip(obs[rg], esp[rg]) if e > 0),
                   min(esp[rg]), obs[rg], esp[rg])
    return {"n_notas": len(ticks), "reconstruidas": iguales, "racha_max": mx, "semilla": semilla, "chi": chi}


def procesos_ajenos(ruta, ts0, ts1, umbral=50.0):
    """Procesos (sin python, msedge, idle, _total) que pasan de `umbral` % de un núcleo durante la corrida.
    Una muestra > 1200 % (12 núcleos lógicos) es imposible: se cuenta aparte como `<proceso> (imposible)`;
    INFERIDO: el contador de Windows cambia de instancia (svchost#N) entre dos lecturas."""
    if not ruta:
        return []
    ini, fin = datetime.fromtimestamp(ts0), datetime.fromtimestamp(ts1)
    altos = {}
    for r in csv.DictReader(open(ruta, newline="", encoding="utf-8-sig")):
        t = datetime.strptime(r["t_local"][:19], "%Y-%m-%d %H:%M:%S")
        nombre = r["proceso"].split("#")[0].lower()
        if not ini <= t <= fin or nombre in ("python", "msedge", "idle", "_total"):
            continue
        c = num(r["cpu_pct"]) or 0.0
        if c >= umbral:
            a = altos.setdefault(r["proceso"] + (" (imposible)" if c > 1200 else ""), [0, 0.0, t])
            a[0] += 1
            if c > a[1]:
                a[1], a[2] = c, t
    return sorted(((p, n, mx, (t - ini).total_seconds()) for p, (n, mx, t) in altos.items()), key=lambda x: -x[2])


def analizar(id_corrida, ruta_procesos=None):
    nombre, sesion, lat, perf = cargar(id_corrida)
    ts = [float(r["timestamp"]) for r in sesion]
    dur = ts[-1] - ts[0]
    v = ventanas_perf(perf)[1:]                  # sin la ventana #0 (D-016)
    cps = [w["cps"] for w in v]
    cont = [r for r in lat if r["tipo"] == "continuo"]
    b = [num(r["latencia_llegada_ms"]) for r in cont if num(r["latencia_llegada_ms"]) is not None]
    a = [num(r["latencia_ms"]) for r in cont]
    tick = [num(r["lat_tick_ms"]) for r in sesion if num(r["lat_tick_ms"]) is not None]
    filas_lag = [(t, num(r["lag_cam_ms"])) for t, r in zip(ts, sesion) if num(r["lag_cam_ms"]) is not None]
    lag = [x for _, x in filas_lag]
    lag_min = por_minuto_p95([t for t, _ in filas_lag], lag)
    t_cap = [float(r["t_cap_ms"]) for r in sesion]
    periodos = [y - x for x, y in zip(t_cap, t_cap[1:])]
    trab = [r for r in lat if r["tipo"] == "cuadro_trabajo"]
    inter = [r for r in lat if r["tipo"] == "cuadro_intervalo"]
    vis = [num(r["latencia_ms"]) for r in lat if r["tipo"] == "visual"]
    ap = [num(r["apertura01"]) for r in sesion]
    saltos = sum(1 for x, y in zip(ap, ap[1:]) if x is not None and y is not None and abs(y - x) > 0.3)
    ap_v = [x for x in ap if x is not None]
    zonas = [r["zona"] for r in sesion]
    tempo = [float(r["tempo"]) for r in sesion]
    d_tempo = [abs(y - x) for x, y in zip(tempo, tempo[1:])]
    edad = [num(r["edad_manos_ms"]) for r in sesion if num(r["edad_manos_ms"]) is not None]
    mel = melodia(sesion)
    m = {
        "archivo": nombre, "commit": sesion[0]["commit"], "version": sesion[0]["version"],
        "inicio": datetime.fromtimestamp(ts[0]).strftime("%d/%m %H:%M:%S"), "dur_s": dur,
        **config_pagina(lat), **validez(sesion, lat),
        "cps_media": st.mean(cps), "cps_min": min(cps), "n_vent": len(cps),
        "vent_lt_290": sum(c < 29.0 for c in cps), "vent_lt_295": sum(c < 29.5 for c in cps),
        "cap_update": st.mean(w["cap_update"] for w in v), "tracker": st.mean(w["tracker"] for w in v),
        "trab_s": st.mean(w["trab_s"] for w in v),
        "lag_media": st.mean(lag), "lag_p95": pct(lag, 95), "lag_max": max(lag),
        "lag_min_p95_min": min(lag_min), "lag_min_p95_max": max(lag_min), "lag_delta": lag_min[-1] - lag_min[0],
        "b_media": st.mean(b), "b_p95": pct(b, 95), "b_max": max(b), "b_n100": sum(x > UMBRAL_B_MS for x in b),
        "b_vacias": len(cont) - len(b),
        "a_media": st.mean(a), "a_p95": pct(a, 95), "a_max": max(a),
        "tick_media": st.mean(tick), "tick_p95": pct(tick, 95), "tick_max": max(tick),
        "tick_n250": sum(x > UMBRAL_TICK_MS for x in tick), "tick_n": len(tick),
        "datos_izq": datos_nuevos(sesion, "edad_izq_ms") / dur, "datos_der": datos_nuevos(sesion, "edad_der_ms") / dur,
        "cuadro_media": (sum(num(r["latencia_ms"]) * num(r["base_latency_ms"]) for r in trab)
                         / sum(num(r["base_latency_ms"]) for r in trab)) if trab else math.nan,
        "cuadro_p95_mediana": st.median(num(r["transporte_ms"]) for r in trab) if trab else math.nan,
        "cuadro_p95_max": max(num(r["transporte_ms"]) for r in trab) if trab else math.nan,
        "cuadro_max": max(num(r["output_latency_ms"]) for r in trab) if trab else math.nan,
        "intervalo_media": (sum(num(r["latencia_ms"]) * num(r["base_latency_ms"]) for r in inter)
                            / sum(num(r["base_latency_ms"]) for r in inter)) if inter else math.nan,
        "vis_n": len(vis), "vis_media": st.mean(vis) if vis else math.nan,
        "vis_p95": pct(vis, 95) if vis else math.nan, "vis_max": max(vis) if vis else math.nan,
        "saltos_ap_s": saltos / dur, "ap_p5": pct(ap_v, 5), "ap_p50": pct(ap_v, 50), "ap_p95": pct(ap_v, 95),
        "ap_vacia_pct": 100.0 * (len(ap) - len(ap_v)) / len(ap),
        "zona_min": sum(x != y for x, y in zip(zonas, zonas[1:])) / (dur / 60),
        "tempo_p99": pct(d_tempo, 99), "tempo_max": max(d_tempo),
        "edad_p95": pct(edad, 95), "pct_33": 100.0 * sum(p > 33.3 for p in periodos) / len(periodos),
        **{k: mel[k] for k in ("n_notas", "reconstruidas", "racha_max", "semilla")},
        "chi": mel["chi"], "procesos": procesos_ajenos(ruta_procesos, ts[0], ts[-1]),
    }
    m["valida_reloj"] = abs(m["delta_transporte"]) <= 1.0
    m["un_cliente"] = m["duplicadas"] == 0
    m["C1"] = m["cps_media"] >= 29.5 and m["vent_lt_290"] == 0 and m["cap_update"] > 0
    m["C1_estricto"] = m["vent_lt_295"] == 0
    m["C2"] = m["lag_p95"] <= UMBRAL_LAG_P95 and m["lag_delta"] <= CRECIMIENTO_MAX_MS
    m["C3"] = m["b_n100"] == 0 and m["b_vacias"] == 0
    m["C4"] = m["tick_n250"] == 0
    m["C6"] = (m["cuadro_p95_max"] <= UMBRAL_CUADRO_P95 and m["vis_p95"] <= UMBRAL_VISUAL_P95) if m["visual"] else None
    m["C7"] = m["datos_izq"] >= UMBRAL_DATOS_MANO and m["datos_der"] >= UMBRAL_DATOS_MANO
    m["HU0017"] = m["saltos_ap_s"] <= UMBRAL_SALTOS_AP
    m["dibujo"] = m["vis_n"] > 0 and not math.isnan(m["cuadro_media"]) if m["visual"] else None
    return m


# ---------------------------------------------------------------------------- tabla
FILAS = [  # (etiqueta, clave, decimales); decimales None = texto
    ("Inicio", "inicio", None), ("Commit", "commit", None), ("Visual (fila config)", "visual", None),
    ("Hz pantalla · tope · ligero", None, None), ("Duración (s)", "dur_s", 0),
    ("Validez: filas sesión", "filas_sesion", 0), ("Validez: filas `continuo` de más (2 clientes)", "duplicadas", 0),
    ("Validez: faltan al arrancar", "faltan_arranque", 0), ("Validez: faltan después", "faltan_despues", 0),
    ("Validez: última fila llegó", "ultima_llego", None), ("Validez: Δ transporte (ms, D-019 ±1)", "delta_transporte", 2),
    ("C1: ciclos/s media (sin #0)", "cps_media", 2), ("C1: ventana mín.", "cps_min", 1),
    ("C1: ventanas < 29.0", "vent_lt_290", 0), ("C1: ventanas < 29.5 (estricto)", "vent_lt_295", 0),
    ("C1: nº ventanas sin #0", "n_vent", 0), ("`cap_update` (ms)", "cap_update", 1), ("`tracker` (ms)", "tracker", 1),
    ("% ciclos > 33.3 ms", "pct_33", 1),
    ("C2: `lag_cam` media", "lag_media", 1), ("C2: `lag_cam` p95", "lag_p95", 1), ("C2: `lag_cam` máx", "lag_max", 1),
    ("C2: p95 por minuto, mín", "lag_min_p95_min", 1), ("C2: p95 por minuto, máx", "lag_min_p95_max", 1),
    ("C2: p95 último − primer minuto", "lag_delta", 2),
    ("C3: (b) media", "b_media", 1), ("C3: (b) p95", "b_p95", 1), ("C3: (b) máx", "b_max", 1),
    ("C3: (b) n > 100", "b_n100", 0), ("(a) media", "a_media", 1), ("(a) p95", "a_p95", 1), ("(a) máx", "a_max", 1),
    ("C4: `lat_tick` media", "tick_media", 1), ("C4: `lat_tick` p95", "tick_p95", 1), ("C4: `lat_tick` máx", "tick_max", 1),
    ("C4: n > 250 (de n)", None, None),
    ("C7: datos nuevos mano izq/s", "datos_izq", 2), ("C7: datos nuevos mano der/s", "datos_der", 2),
    ("Trabajos/s del hilo de manos", "trab_s", 2),
    ("C6: tiempo por cuadro media (ms)", "cuadro_media", 2), ("C6: p95 por lote, mediana", "cuadro_p95_mediana", 2),
    ("C6: p95 por lote, máx", "cuadro_p95_max", 2), ("C6: tiempo por cuadro máx", "cuadro_max", 2),
    ("Intervalo entre cuadros media (ms)", "intervalo_media", 1),
    ("C6: latencia visual media", "vis_media", 1), ("C6: latencia visual p95", "vis_p95", 1),
    ("C6: latencia visual máx", "vis_max", 1), ("C6: latencia visual n", "vis_n", 0),
    ("HU0017: saltos `apertura01` > 0.3 por s", "saltos_ap_s", 2), ("HU0017: `apertura01` p5", "ap_p5", 2),
    ("HU0017: `apertura01` mediana", "ap_p50", 2), ("HU0017: `apertura01` p95", "ap_p95", 2),
    ("HU0008-2: % filas con `apertura01` vacía", "ap_vacia_pct", 1),
    ("HU0015: cambios de zona por minuto", "zona_min", 1),
    ("HU0016: salto de tempo p99", "tempo_p99", 3), ("HU0016: salto de tempo máx", "tempo_max", 3),
    ("Edad manos p95 (ms)", "edad_p95", 1),
    ("HU0019-2: racha máx", "racha_max", 0), ("HU0021/22: notas reconstruidas", None, None),
]


def celda(m, clave, dec):
    x = m[clave]
    if dec is None:
        return "sí" if x is True else "no" if x is False else str(x)
    return "—" if isinstance(x, float) and math.isnan(x) else f"{x:.{dec}f}"


def rango(ms, clave, dec):
    xs = [m[clave] for m in ms if not (isinstance(m[clave], float) and math.isnan(m[clave]))]
    if not xs or dec is None:
        return ""
    lo, hi = min(xs), max(xs)
    return f"{lo:.{dec}f}" if lo == hi else f"{lo:.{dec}f}–{hi:.{dec}f}"


def tabla(ms):
    con = [m for m in ms if m["visual"]]
    sin = [m for m in ms if not m["visual"]]
    ids = [m["archivo"].split("_")[2] for m in ms]
    out = ["| Métrica | " + " | ".join(ids) + " | Rango con visual | Rango sin visual |",
           "|---" * (len(ms) + 3) + "|"]
    for etiqueta, clave, dec in FILAS:
        if etiqueta.startswith("Hz"):
            cel = [f"{m['hz']} · {m['tope'] or '—'} · {m['ligero'] or '—'}" for m in ms]
            extra = ["", ""]
        elif etiqueta.startswith("C4: n > 250"):
            cel = [f"{m['tick_n250']} de {m['tick_n']}" for m in ms]
            extra = ["", ""]
        elif etiqueta.startswith("HU0021"):
            cel = [f"{m['reconstruidas']}/{m['n_notas']}" for m in ms]
            extra = ["", ""]
        else:
            cel = [celda(m, clave, dec) for m in ms]
            extra = [rango(con, clave, dec), rango(sin, clave, dec)]
        out.append(f"| {etiqueta} | " + " | ".join(cel + extra) + " |")
    out.append("")
    out.append("| Criterio | " + " | ".join(ids) + " |")
    out.append("|---" * (len(ms) + 1) + "|")
    for k, txt in (("un_cliente", "Un solo cliente"), ("valida_reloj", "Reloj D-019"),
                   ("dibujo", "Visual dibujó (filas cuadro y visual, D-061)"), ("C1", "C1 (D-023)"),
                   ("C1_estricto", "C1 estricto"), ("C2", f"C2 (p95 ≤ {UMBRAL_LAG_P95}, crecimiento ≤ {CRECIMIENTO_MAX_MS} ms)"),
                   ("C3", "C3 (0 de (b) > 100)"), ("C4", "C4 (100 % ≤ 250)"),
                   ("C6", "C6 (máx p95 por lote ≤ 16.7 y visual p95 ≤ 100)"), ("C7", "C7 (≥ 5 por mano/s)"),
                   ("HU0017", f"HU0017-1 (saltos de apertura01 ≤ {UMBRAL_SALTOS_AP}/s)")):
        out.append(f"| {txt} | " + " | ".join("—" if m[k] is None else "cumple" if m[k] else "NO" for m in ms) + " |")
    out.append("")
    out.append("HU0019-3, χ² (3 gl, crítico 7.81) por rango de λ: n · χ² · E mín. (obs. 0/1/2/3 pasos | esperado)")
    for m, i in zip(ms, ids):
        partes = []
        for (lo, hi), (n, chi, emin, o, e) in m["chi"].items():
            partes.append(f"[{lo:.2f}, {min(hi, 1):.1f}) n={n} χ²={chi:.1f} Emín={emin:.1f} "
                          f"({'/'.join(map(str, o))} | {'/'.join(f'{x:.0f}' for x in e)})")
        out.append(f"- {i} (semilla {m['semilla']}): " + "; ".join(partes))
    if any(m["procesos"] for m in ms):
        out.append("")
        out.append("Procesos ajenos ≥ 50 % de un núcleo durante la corrida (muestras · máx % · segundo del máx):")
        for m, i in zip(ms, ids):
            txt = "; ".join(f"{p} {n} · {mx:.0f} % · {s:.0f} s" for p, n, mx, s in m["procesos"]) or "ninguno"
            out.append(f"- {i}: {txt}")
    return "\n".join(out)


if __name__ == "__main__":
    args = sys.argv[1:]
    procesos = salida = None
    if "--procesos" in args:
        i = args.index("--procesos"); procesos = args[i + 1]; del args[i:i + 2]
    if "--salida" in args:
        i = args.index("--salida"); salida = args[i + 1]; del args[i:i + 2]
    texto = tabla([analizar(x, procesos) for x in args])
    print(texto)
    if salida:
        with open(salida, "w", encoding="utf-8") as f:
            f.write(texto + "\n")
