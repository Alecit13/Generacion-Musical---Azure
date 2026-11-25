"""Validación offline SIN dispositivo (11/11/2026). TODO lo que imprime es SIMULADO (no MEDIDO con la Kinect).
  US12 (HU0012-2): retardo del filtro EMA ante un escalón, con las clases reales de main.py (cargadas con
        pruebas_unitarias.cargar_de_main, desde movimiento.py).
  US28 (HU0028-1, HU0028-2): diversidad de la melodía entre semillas y consistencia de los parámetros continuos.
Los criterios de abajo se fijaron ANTES de la primera ejecución (11/11). Los umbrales de US28 los propuso Code y están
[POR CONFIRMAR] por Ale; no se cambian después de ver el resultado.
Uso:  python validacion_offline.py          (escribe también sesiones/validacion_offline_<fecha>.txt)"""
import csv
import datetime as dt
import glob
import itertools
import math
import random
import statistics as st
import sys

import numpy as np

import muestreo
from pruebas_unitarias import cargar_de_main, esqueleto, CONST_REGISTRO

# ---------------------------------------------------------------------
# Criterios fijados antes de correr
# ---------------------------------------------------------------------
FPS = 30.0
UMBRAL_US12_MS = 100.0      # HU0012-2: "sin retrasos perceptibles superiores al umbral de latencia" (RNF01 = 100 ms)
# US12: el retardo que se compara con 100 ms es el TIEMPO AL 50 % del escalón de registro01 (no de la zona: la espera de
# 250 ms de D-028 es intencional y se informa aparte). 63 % y 90 % se informan como cola, sin umbral.
# t = 0 es el primer frame con el ángulo nuevo; el resultado va en múltiplos de 1/30 s.
NIVELES_COLA = (0.63, 0.90)

LAMBDAS_US28 = (0.05, 0.3, 0.6, 1.0)
SEMILLAS_US28 = list(range(1, 21))          # 20 semillas
NOTAS_POR_CORRIDA = 300
CORRIDA_REAL = "sesiones/sesion_20261111_162802_*cuda-lite.csv"   # Base 1 (repetición) del 11/11: λ y zona reales
# Umbrales de diversidad (propuestos por Code, [POR CONFIRMAR] por Ale):
D1_DETERMINISTA = 0.0       # con λ = LAMBDA_MIN (0.05), % de notas distintas entre pares de semillas = 0 (HU0021-2)
D2_MIN_REAL = 50.0          # con la secuencia real de λ, media de % de notas distintas entre pares de semillas >= 50 %
D3_MONOTONA = True          # el % de notas distintas crece con λ (0.05 < 0.3 < 0.6 < 1.0)
C1_CONSISTENCIA = 100.0     # con la misma entrada, λ, octava y número de notas son idénticos entre semillas (100 %)

salida = []


def p(texto=""):
    print(texto)
    salida.append(texto)


# ---------------------------------------------------------------------
# US12
# ---------------------------------------------------------------------
def _cruces(valores, antes, despues, niveles):
    """Primer índice en que `valores` alcanza cada nivel (fracción del escalón antes -> despues)."""
    res = {}
    for nivel in niveles:
        objetivo = antes + nivel * (despues - antes)
        sube = despues > antes
        idx = next((i for i, v in enumerate(valores) if (v >= objetivo - 1e-9 if sube else v <= objetivo + 1e-9)), None)
        res[nivel] = None if idx is None else idx * 1000.0 / FPS
    return res


def escalon_registro():
    """Escalón del ángulo de los dos hombros (20° -> 160°) por la RegistroPorAngulo real (EMA_ANGULO_BRAZO + normalizador
    de 20 s). Antes: 8 s de calibración alternando 20°/160° y 2 s quieto en 20°. Mide registro01 tras el escalón."""
    m = cargar_de_main(*CONST_REGISTRO, "NormalizadorAdaptativo", "angulo_articulacion", "MapeoExtremidades",
                       "RegistroPorAngulo")

    def pose(grados):
        r = math.radians(grados)
        pos = {}
        for cad, hom, cod in m.J_BRAZOS.values():
            pos[hom], pos[cad], pos[cod] = (0, 0, 2000), (0, 500, 2000), (300 * math.sin(r), 300 * math.cos(r), 2000)
        return esqueleto(pos)

    reg, t, k = m.RegistroPorAngulo(), 0.0, 0
    for a in [20] * 60 + [160] * 60 + [20] * 60 + [160] * 60 + [20] * 60:     # 10 s
        reg.actualizar(pose(a), k / FPS); k += 1
    antes = reg.registro01
    despues_vals = []
    for _ in range(int(FPS * 1.5)):                                              # 1.5 s en 160°
        despues_vals.append(reg.actualizar(pose(160), k / FPS)["registro01"]); k += 1
    despues = despues_vals[-1]
    cruces = _cruces(despues_vals, antes, despues, (0.5,) + NIVELES_COLA)
    p("US12 — escalón de registro01 (hombros 20° -> 160°), RegistroPorAngulo real, 30 Hz [SIMULADO]")
    p(f"  EMA_ANGULO_BRAZO = {m.EMA_ANGULO_BRAZO}; registro01 antes {antes:.3f} -> después {despues:.3f}")
    p(f"  tiempo al 50 %: {cruces[0.5]:.1f} ms  (umbral {UMBRAL_US12_MS:.0f} ms) -> "
      f"{'por debajo' if cruces[0.5] is not None and cruces[0.5] <= UMBRAL_US12_MS else 'por encima'}")
    p(f"  cola: 63 % {cruces[0.63]:.1f} ms · 90 % {cruces[0.90]:.1f} ms")
    p(f"  referencia teórica del EMA: retardo de grupo (1-α)/α ciclos = {(1 - m.EMA_ANGULO_BRAZO) / m.EMA_ANGULO_BRAZO * 1000 / FPS:.1f} ms")
    # Zona: se informa aparte (D-028, espera intencional de 250 ms continuos)
    from zona import zona_desde_registro
    zona, pend, tc = "grave", None, 0.0
    t_zona = None
    for i, v in enumerate(despues_vals):
        zona, pend, tc = zona_desde_registro(v, zona, pend, tc, 1 / FPS)
        if zona == "agudo" and t_zona is None:
            t_zona = i * 1000.0 / FPS
    p(f"  aparte (D-028, intencional): la zona pasa de grave a agudo a los {t_zona:.1f} ms del escalón")
    return cruces


def escalon_velocidad():
    """Escalón de velocidad angular de la rodilla (0 -> 100 °/s) por la VelocidadAngular real (EMA_VEL_RODILLA). Informativo."""
    m = cargar_de_main("EMA_VEL_RODILLA", "VelocidadAngular")
    v, ang, vals = m.VelocidadAngular(), 90.0, []
    for k in range(30):
        v.actualizar(ang, k / FPS)
    for k in range(30, 75):
        ang += 100.0 / FPS
        vals.append(v.actualizar(ang, k / FPS))
    cruces = _cruces(vals, 0.0, 100.0, (0.5,) + NIVELES_COLA)
    p("US12 — escalón de velocidad de rodilla (0 -> 100 °/s), VelocidadAngular real, 30 Hz [SIMULADO, informativo]")
    p(f"  EMA_VEL_RODILLA = {m.EMA_VEL_RODILLA}; al 50 % {cruces[0.5]:.1f} ms · 63 % {cruces[0.63]:.1f} ms · 90 % {cruces[0.90]:.1f} ms")


def ruido_ema():
    """Reducción del ruido blanco por los dos EMA (teoría: std sale × sqrt(α/(2-α))). Informativo."""
    rng = np.random.default_rng(0)
    p("US12 — ruido blanco por el EMA [SIMULADO, informativo]")
    for nombre, a in (("EMA_ANGULO_BRAZO", 0.5), ("EMA_VEL_RODILLA", 0.4)):
        x = rng.normal(0, 1, 200_000)
        y = np.empty_like(x); y[0] = x[0]
        for i in range(1, len(x)):
            y[i] = a * x[i] + (1 - a) * y[i - 1]
        red = 1 - y[1000:].std() / x[1000:].std()
        p(f"  {nombre} = {a}: desviación −{100 * red:.1f} % (teoría −{100 * (1 - math.sqrt(a / (2 - a))):.1f} %)")


# ---------------------------------------------------------------------
# US28
# ---------------------------------------------------------------------
def sortear(semilla, lams, inicial="Do"):
    """Lo mismo que hace main.py: random.seed(semilla), reiniciar_estado() y una nota por tick con el λ del tick."""
    random.seed(semilla)
    muestreo.reiniciar_estado()
    nota, notas = inicial, []
    for lam in lams:
        nota = muestreo.elegir_siguiente_nota(nota, lam)
        notas.append(nota)
    return notas


def diferencia_media(secuencias):
    """Media, sobre todos los pares de semillas, del % de posiciones con nota distinta."""
    pares = list(itertools.combinations(secuencias, 2))
    return st.mean(100.0 * sum(a != b for a, b in zip(x, y)) / len(x) for x, y in pares)


def entropia(notas):
    c = {n: notas.count(n) for n in set(notas)}
    return -sum(v / len(notas) * math.log2(v / len(notas)) for v in c.values())


def trigramas(notas):
    return len(set(zip(notas, notas[1:], notas[2:])))


def escenarios_us28():
    ok = {}
    p("US28-1 — diversidad entre semillas con λ fijo (20 semillas × 300 notas) [SIMULADO]")
    difs = []
    for lam in LAMBDAS_US28:
        secs = [sortear(s, [lam] * NOTAS_POR_CORRIDA) for s in SEMILLAS_US28]
        d = diferencia_media(secs)
        difs.append(d)
        p(f"  λ = {lam:<4}: notas distintas entre pares {d:5.1f} % · entropía media {st.mean(entropia(x) for x in secs):.2f} bits "
          f"· trigramas distintos (media) {st.mean(trigramas(x) for x in secs):.0f}")
    ok["D1"] = difs[0] == D1_DETERMINISTA
    ok["D3"] = all(a < b for a, b in zip(difs, difs[1:])) if D3_MONOTONA else True

    ruta = glob.glob(CORRIDA_REAL)[0]
    filas = list(csv.DictReader(open(ruta, newline="")))
    ticks = [r for r in filas if r["lam_sorteo"] != ""]
    lams = [float(r["lam_sorteo"]) for r in ticks]
    zonas = [r["zona"] for r in ticks]
    secs = [sortear(s, lams) for s in SEMILLAS_US28]
    d_real = diferencia_media(secs)
    reproducida = sortear(int(ticks[0]["semilla"]), lams) == [r["nota"] for r in ticks]
    p(f"US28-1 — secuencia real de λ ({ruta.split('/')[-1].split(chr(92))[-1][:30]}, {len(lams)} notas; la entrada es MEDIDA, "
      f"las melodías son SIMULADAS)")
    p(f"  notas distintas entre pares de semillas {d_real:.1f} % · entropía media {st.mean(entropia(x) for x in secs):.2f} bits; "
      f"con la semilla de la corrida se reproduce la melodía grabada: {reproducida}")
    ok["D2"] = d_real >= D2_MIN_REAL

    # US28-2: con la misma entrada, los parámetros continuos no dependen de la semilla (solo la melodía cambia)
    octavas = [[muestreo.calcular_octava(z) for z in zonas] for _ in SEMILLAS_US28]
    iguales_oct = all(o == octavas[0] for o in octavas)
    iguales_n = len({len(x) for x in secs}) == 1
    p("US28-2 — consistencia con la misma entrada y 20 semillas [SIMULADO]")
    p(f"  λ idéntico por construcción (es la entrada) · octava idéntica en todas: {iguales_oct} · nº de notas idéntico: {iguales_n} "
      f"· melodías distintas: {len({tuple(x) for x in secs})} de {len(secs)}")
    ok["C1"] = (100.0 if (iguales_oct and iguales_n) else 0.0) >= C1_CONSISTENCIA
    p("Criterios fijados antes de correr (umbrales [POR CONFIRMAR] por Ale):")
    p(f"  D1 λ=0.05 sin diferencias: {ok['D1']} · D2 secuencia real ≥ {D2_MIN_REAL:.0f} %: {ok['D2']} · "
      f"D3 diversidad crece con λ: {ok['D3']} · C1 consistencia {C1_CONSISTENCIA:.0f} %: {ok['C1']}")
    return ok


if __name__ == "__main__":
    p(f"validacion_offline.py — {dt.datetime.now():%d/%m/%Y %H:%M} — Python {sys.version.split()[0]} — TODO SIMULADO")
    p()
    escalon_registro(); p()
    escalon_velocidad(); p()
    ruido_ema(); p()
    escenarios_us28()
    destino = f"sesiones/validacion_offline_{dt.date.today():%Y%m%d}.txt"
    with open(destino, "w", encoding="utf-8") as f:
        f.write("\n".join(salida) + "\n")
    print(f"\nGuardado en {destino}")
