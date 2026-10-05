"""
Gráficos de una sesión del sistema de generación musical adaptativa.

Uso:
    python3.11 grafico.py                          -> usa la sesión más reciente de la carpeta "sesiones"
    python3.11 grafico.py sesiones/sesion_X.csv    -> usa una sesión específica

Genera dos imágenes junto al CSV:
    <sesion>_linea_tiempo.png  -> todas las métricas a lo largo del tiempo
    <sesion>_resumen.png       -> distribuciones y resumen de la sesión
"""
import glob
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# =====================================================================
# Parámetros
# =====================================================================
CARPETA_SESIONES = "sesiones"
ARCHIVO_ANTIGUO = "sesion_file.csv"   # formato anterior, se usa si no hay carpeta "sesiones"
VENTANA_SUAVIZADO = 9                 # frames para suavizar lambda y apertura (1 = sin suavizar)
UMBRAL_LAMBDA = 0.5

COLOR_PRINCIPAL = "#E30613"
COLOR_OSCURO = "#1F2933"
COLOR_IZQ = "#2563EB"
COLOR_DER = "#F59E0B"
COLORES_ZONA = {"grave": "#2563EB", "medio": "#9CA3AF", "agudo": "#E30613"}

ORDEN_ZONAS = ["grave", "medio", "agudo"]
# Posición de cada nota dentro de la octava (pasos de escala, para que queden equiespaciadas)
POSICION_NOTA = {"Do": 0, "Re": 1, "Mi": 2, "Fa": 3, "Sol": 4, "La": 5, "Si": 6}


# =====================================================================
# Carga de datos
# =====================================================================
def elegir_archivo():
    if len(sys.argv) > 1:
        return sys.argv[1]
    sesiones = sorted(glob.glob(os.path.join(CARPETA_SESIONES, "sesion_*.csv")))
    if sesiones:
        return sesiones[-1]
    if os.path.exists(ARCHIVO_ANTIGUO):
        return ARCHIVO_ANTIGUO
    sys.exit("No encontré ninguna sesión. Ejecuta primero main.py.")


def cargar_sesion(ruta):
    df = pd.read_csv(ruta)
    if df.empty:
        sys.exit(f"La sesión {ruta} está vacía (¿no se detectó ningún cuerpo?).")

    df["t"] = df["timestamp"] - df["timestamp"].iloc[0]

    # Columnas que pueden faltar en sesiones antiguas
    for col in ["apertura", "apertura_izq", "apertura_der"]:
        if col not in df:
            df[col] = np.nan
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if "manos" not in df:
        df["manos"] = df[["apertura_izq", "apertura_der"]].notna().sum(axis=1)

    # En sesiones antiguas una mano no detectada se guardaba como 0: no es apertura real
    if ruta.endswith(ARCHIVO_ANTIGUO):
        for col in ["apertura", "apertura_izq", "apertura_der"]:
            df.loc[df[col] == 0, col] = np.nan

    df["zona_num"] = df["zona"].map({z: i for i, z in enumerate(ORDEN_ZONAS)})
    df["altura"] = df["octava"] * 7 + df["nota"].map(POSICION_NOTA)
    df["nota_completa"] = df["nota"] + df["octava"].astype(str)
    df["dt"] = df["t"].diff().fillna(0).clip(upper=1.0)  # tiempo de cada frame (para % de tiempo)
    return df


def suavizar(serie):
    if VENTANA_SUAVIZADO <= 1:
        return serie
    return serie.rolling(VENTANA_SUAVIZADO, center=True, min_periods=1).mean()


def cambios_de_nota(df):
    """Solo los momentos en que la nota cambia: así se ve la melodía real."""
    cambio = df["nota_completa"] != df["nota_completa"].shift()
    return df[cambio]


# =====================================================================
# Figura 1: línea de tiempo
# =====================================================================
def sombrear_zonas(ax, df):
    """Pinta de fondo la zona activa en cada momento."""
    bloques = (df["zona"] != df["zona"].shift()).cumsum()
    for _, bloque in df.groupby(bloques):
        zona = bloque["zona"].iloc[0]
        ax.axvspan(bloque["t"].iloc[0], bloque["t"].iloc[-1],
                   color=COLORES_ZONA.get(zona, "#FFFFFF"), alpha=0.08, linewidth=0)


def figura_linea_tiempo(df, titulo, salida):
    fig, ejes = plt.subplots(5, 1, figsize=(12, 12), sharex=True,
                             height_ratios=[2, 1, 2, 2, 1])
    ax_lam, ax_zona, ax_nota, ax_ap, ax_manos = ejes

    for ax in ejes:
        sombrear_zonas(ax, df)
        ax.grid(axis="x", alpha=0.2)

    # 1. Fluidez
    ax_lam.plot(df["t"], df["lambda"], color=COLOR_PRINCIPAL, alpha=0.25, linewidth=0.8)
    ax_lam.plot(df["t"], suavizar(df["lambda"]), color=COLOR_PRINCIPAL, linewidth=1.8,
                label="λ suavizado")
    ax_lam.axhline(UMBRAL_LAMBDA, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)
    ax_lam.set_ylim(-0.05, 1.05)
    ax_lam.set_ylabel("λ (fluidez)")
    ax_lam.legend(loc="upper right", fontsize=8, frameon=False)
    ax_lam.set_title(titulo)

    # 2. Zona / registro
    ax_zona.step(df["t"], df["zona_num"], where="post", color=COLOR_OSCURO, linewidth=1.5)
    ax_zona.set_yticks(range(len(ORDEN_ZONAS)))
    ax_zona.set_yticklabels([z.capitalize() for z in ORDEN_ZONAS])
    ax_zona.set_ylim(-0.5, len(ORDEN_ZONAS) - 0.5)
    ax_zona.set_ylabel("Registro")

    # 3. Notas (melodía)
    notas = cambios_de_nota(df)
    ax_nota.step(df["t"], df["altura"], where="post", color=COLOR_OSCURO, linewidth=1, alpha=0.6)
    ax_nota.scatter(notas["t"], notas["altura"], s=18, zorder=3,
                    c=[COLORES_ZONA.get(z, COLOR_OSCURO) for z in notas["zona"]])
    alturas = sorted(df["altura"].dropna().unique())
    etiquetas = df.drop_duplicates("altura").set_index("altura")["nota_completa"]
    ax_nota.set_yticks(alturas)
    ax_nota.set_yticklabels([etiquetas[a] for a in alturas], fontsize=8)
    ax_nota.set_ylabel("Nota")

    # 4. Apertura de manos
    ax_ap.plot(df["t"], suavizar(df["apertura_izq"]), color=COLOR_IZQ, linewidth=1.3,
               label="Mano izquierda")
    ax_ap.plot(df["t"], suavizar(df["apertura_der"]), color=COLOR_DER, linewidth=1.3,
               label="Mano derecha")
    ax_ap.plot(df["t"], suavizar(df["apertura"]), color=COLOR_OSCURO, linewidth=1.8,
               linestyle="--", label="Promedio")
    ax_ap.set_ylabel("Apertura de manos")
    ax_ap.legend(loc="upper right", fontsize=8, frameon=False, ncol=3)

    # 5. Manos detectadas
    ax_manos.step(df["t"], df["manos"], where="post", color=COLOR_OSCURO, linewidth=1.2)
    ax_manos.fill_between(df["t"], df["manos"], step="post", color=COLOR_OSCURO, alpha=0.15)
    ax_manos.set_yticks([0, 1, 2])
    ax_manos.set_ylim(-0.2, 2.3)
    ax_manos.set_ylabel("Manos\ndetectadas")
    ax_manos.set_xlabel("Tiempo (s)")

    fig.tight_layout()
    fig.savefig(salida, dpi=200)
    return fig


# =====================================================================
# Figura 2: resumen de la sesión
# =====================================================================
def figura_resumen(df, titulo, salida):
    fig, ((ax_z, ax_n), (ax_l, ax_a)) = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle(titulo)

    # % de tiempo en cada zona
    tiempo_zona = df.groupby("zona")["dt"].sum().reindex(ORDEN_ZONAS, fill_value=0)
    pct_zona = 100 * tiempo_zona / max(tiempo_zona.sum(), 1e-9)
    barras = ax_z.bar([z.capitalize() for z in ORDEN_ZONAS], pct_zona,
                      color=[COLORES_ZONA[z] for z in ORDEN_ZONAS])
    ax_z.bar_label(barras, fmt="%.0f%%", fontsize=9)
    ax_z.set_ylabel("% del tiempo")
    ax_z.set_title("Tiempo en cada registro")

    # Notas tocadas (solo cambios de nota), ordenadas de grave a agudo
    notas = cambios_de_nota(df)
    conteo = notas.groupby(["altura", "nota_completa"]).size().reset_index(name="n")
    conteo = conteo.sort_values("altura")
    ax_n.bar(conteo["nota_completa"], conteo["n"], color=COLOR_OSCURO)
    ax_n.set_ylabel("Veces tocada")
    ax_n.set_title(f"Notas tocadas ({len(notas)} en total)")
    ax_n.tick_params(axis="x", labelsize=8, rotation=45)

    # Distribución de la fluidez
    ax_l.hist(df["lambda"], bins=20, range=(0, 1), color=COLOR_PRINCIPAL, alpha=0.8)
    ax_l.axvline(df["lambda"].mean(), color=COLOR_OSCURO, linestyle="--",
                 label=f"Media = {df['lambda'].mean():.2f}")
    ax_l.set_xlabel("λ (fluidez)")
    ax_l.set_ylabel("Frames")
    ax_l.set_title("Distribución de la fluidez")
    ax_l.legend(fontsize=8, frameon=False)

    # Apertura por mano
    datos = [df["apertura_izq"].dropna(), df["apertura_der"].dropna()]
    etiquetas = [f"Izquierda\n(detectada {100 * df['apertura_izq'].notna().mean():.0f}%)",
                 f"Derecha\n(detectada {100 * df['apertura_der'].notna().mean():.0f}%)"]
    if all(len(d) for d in datos):
        caja = ax_a.boxplot(datos, patch_artist=True, widths=0.5)
        ax_a.set_xticks([1, 2], etiquetas)
        for parte, color in zip(caja["boxes"], [COLOR_IZQ, COLOR_DER]):
            parte.set_facecolor(color)
            parte.set_alpha(0.5)
    else:
        ax_a.text(0.5, 0.5, "Sin datos de apertura", ha="center", va="center",
                  transform=ax_a.transAxes)
    ax_a.set_ylabel("Apertura")
    ax_a.set_title("Apertura de manos")

    fig.tight_layout()
    fig.savefig(salida, dpi=200)
    return fig


def imprimir_resumen(df, ruta):
    duracion = df["t"].iloc[-1]
    notas = cambios_de_nota(df)
    tiempo_zona = df.groupby("zona")["dt"].sum()
    print(f"\nSesión: {ruta}")
    print(f"  Duración:              {duracion:.1f} s ({len(df)} frames con cuerpo)")
    print(f"  Fluidez λ:             media {df['lambda'].mean():.2f} | "
          f"mín {df['lambda'].min():.2f} | máx {df['lambda'].max():.2f}")
    print(f"  Frames con λ > {UMBRAL_LAMBDA}:    {100 * (df['lambda'] > UMBRAL_LAMBDA).mean():.0f}%")
    print(f"  Notas tocadas:         {len(notas)} ({notas['nota_completa'].nunique()} distintas)")
    for z in ORDEN_ZONAS:
        pct = 100 * tiempo_zona.get(z, 0) / max(tiempo_zona.sum(), 1e-9)
        print(f"  Tiempo en '{z}':".ljust(25) + f"{pct:.0f}%")
    print(f"  Apertura media:        izq {df['apertura_izq'].mean():.3f} | "
          f"der {df['apertura_der'].mean():.3f}")
    print(f"  Detección de manos:    2 manos {100 * (df['manos'] == 2).mean():.0f}% | "
          f"1 mano {100 * (df['manos'] == 1).mean():.0f}% | "
          f"ninguna {100 * (df['manos'] == 0).mean():.0f}%")


if __name__ == "__main__":
    ruta = elegir_archivo()
    df = cargar_sesion(ruta)
    base = os.path.splitext(ruta)[0]
    nombre = os.path.basename(base)

    imprimir_resumen(df, ruta)
    figura_linea_tiempo(df, f"Sesión con Azure Kinect: métricas en el tiempo ({nombre})",
                        f"{base}_linea_tiempo.png")
    figura_resumen(df, f"Resumen de la sesión ({nombre})", f"{base}_resumen.png")
    print(f"\nGráficos guardados en:\n  {base}_linea_tiempo.png\n  {base}_resumen.png")
    plt.show()