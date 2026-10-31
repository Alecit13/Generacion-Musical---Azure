"""Evidencia de US12 (suavizado): compara cada señal CRUDA con su versión FILTRADA usando el CSV de una sesión.
Uso:  python evidencia_us12.py ruta/de/la/sesion.csv
Idea: si el filtro funciona, la señal filtrada tiene menos 'temblor' (jitter) que la cruda, sin perder la forma del gesto."""
import sys
import warnings
import numpy as np
import pandas as pd

warnings.simplefilter("ignore", RuntimeWarning)   # la 1ª muestra es NaN; no afecta al resultado


def z(x):
    """Estandariza (media 0, desviación 1) para comparar señales de distinta escala. Lo usan jitter y ruido_hf."""
    x = np.asarray(x, float)
    return (x - np.nanmean(x)) / np.nanstd(x)


def jitter(x):
    """Desviación estándar de las diferencias entre muestras consecutivas de la señal estandarizada.
    Más alto = más temblor muestra a muestra. Es la métrica principal de la tabla."""
    return float(np.nanstd(np.diff(z(x))))


def ruido_hf(x, k=5):
    """Ruido de alta frecuencia: desviación de la señal estandarizada respecto a su media móvil de k muestras.
    Segunda métrica; confirma lo que dice jitter."""
    s = pd.Series(z(x))
    return float((s - s.rolling(k, center=True).mean()).std())


def fila(nombre, cruda, filtrada):
    """Calcula y devuelve (nombre, n, jitter crudo, jitter filtrado, reducción %, ruido HF crudo, filtrado, reducción %)."""
    jc, jf, hc, hf = jitter(cruda), jitter(filtrada), ruido_hf(cruda), ruido_hf(filtrada)
    return (nombre, len(cruda), round(jc, 3), round(jf, 3), round((1 - jf / jc) * 100), round(hc, 3), round(hf, 3), round((1 - hf / hc) * 100))


def main(ruta):
    """Lee el CSV, arma las señales cruda/filtrada y escribe la tabla en pantalla.
    Hombros: cruda = ang_hombro_* (ángulo sin filtro), filtrada = reg01_* (ángulo con EMA, ya normalizado); solo filas con confianza >= 2.
    Rodilla: cruda = |d ang_rodilla/dt| reconstruida desde los ángulos del CSV, filtrada = vel_rodilla (con EMA)."""
    s = pd.read_csv(ruta)
    ts = s["timestamp"].values
    dt = np.diff(ts)
    filas = []
    for lado in ("izq", "der"):
        m = (s["conf_hombro_" + lado] >= 2) & s["ang_hombro_" + lado].notna() & s["reg01_" + lado].notna()
        filas.append(fila(f"hombro {lado} (EMA 0.5)", s.loc[m, "ang_hombro_" + lado].values, s.loc[m, "reg01_" + lado].values))
    vs = []
    for lado in ("izq", "der"):
        a = s["ang_rodilla_" + lado].values
        v = np.r_[np.nan, np.abs(np.diff(a)) / np.maximum(dt, 1e-3)]
        v[np.r_[False, dt > 0.5]] = np.nan                      # saltos largos (cuerpo ausente) no cuentan
        vs.append(v)
    cruda = np.nanmean(np.vstack(vs), axis=0)
    filt = s["vel_rodilla"].values
    m = ~np.isnan(cruda) & (filt > 0)
    filas.append(fila("vel. rodilla (EMA 0.4)", cruda[m], filt[m]))
    tabla = pd.DataFrame(filas, columns=["señal", "n", "jitter crudo", "jitter filtrado", "reduc. %", "ruido HF crudo", "ruido HF filtrado", "reduc. HF %"])
    print(tabla.to_string(index=False))
    ciclo_ms = float(np.mean(dt)) * 1000
    print(f"\nCiclo medio: {ciclo_ms:.1f} ms")
    for nombre, alfa in (("hombro", 0.5), ("rodilla", 0.4)):
        print(f"Costo del filtro (retardo teórico de una EMA con alfa={alfa}): ~{(1 - alfa) / alfa * ciclo_ms:.0f} ms para {nombre}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Uso: python evidencia_us12.py ruta/de/la/sesion.csv")
    main(sys.argv[1])