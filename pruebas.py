import pandas as pd
m = pd.read_csv("sesiones/sesion_20261019_182219.csv")   # cambia XXXX
print((m["manos"] == 2).mean())               

d = pd.read_csv("sesiones/sesion_20261019_182728.csv")        # pon el nombre real de esa sesión
hueco = d["t_cap_ms"].diff()                       # ms entre ciclos con cuerpo consecutivos
print(hueco.describe())
print((hueco > 150).sum(), "huecos > 150 ms")
raros = d[d["lat_tick_ms"] > 250][["t_cap_ms", "lat_tick_ms"]].copy()
raros["hueco_previo_ms"] = hueco[raros.index]
print(raros)



d = pd.read_csv("latencias/latencias_2026-10-19T23-29-35-711Z.csv")          # pon aquí el nombre real del archivo
umbral = {"continuo": 100, "tick_sorteo": 250}
for tipo, g in d.groupby("tipo"):
    x = g["latencia_ms"]
    pct = (x > umbral[tipo]).mean() * 100 if tipo in umbral else float("nan")
    print(f"{tipo:12s} n={len(x)} media={x.mean():.0f} p95={x.quantile(.95):.0f} max={x.max():.0f} >umbral={pct:.1f}%")