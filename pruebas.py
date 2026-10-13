import pandas as pd
d = pd.read_csv("sesiones/sesion_20261012_174822.csv")   # cambia XXXX
print((d["manos"] == 2).mean())               