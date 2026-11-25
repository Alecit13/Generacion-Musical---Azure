"""Archivos de salida de una corrida (D-006): cabeceras del CSV de sesión y del _latencias.csv, en un solo lugar.
Relación: main.py abre los dos CSV con abrir_csv (el de sesión al arrancar; el de latencias con el primer lote que manda
index.html, en guardar_latencias). La fila de cada ciclo la sigue armando bucle_kinect (main.py), en el mismo orden que
COLUMNAS_SESION; pruebas_unitarias.py comprueba la cabecera y el número de columnas frente a 8d58820.
Variables clave: COLUMNAS_SESION (46 columnas), COLUMNAS_LATENCIAS (7 columnas)."""
import csv

# Las 10 primeras columnas conservan el orden anterior (grafico.py sigue funcionando)
COLUMNAS_SESION = ["timestamp", "zona", "lambda", "acc_media", "nota", "octava", "apertura",
                   "apertura_izq", "apertura_der", "manos",
                   "tempo", "intensidad", "apertura01", "vel_rodilla", "amplitud_mm", "t_cap_ms",
                   "lat_tick_ms",
                   # candidatos de ángulo para decidir/justificar el mapeo del tono (grados)
                   "ang_hombro_izq", "ang_hombro_der", "ang_codo_izq", "ang_codo_der",
                   "ang_cadera_izq", "ang_cadera_der", "ang_rodilla_izq", "ang_rodilla_der",
                   "conf_hombro_izq", "conf_hombro_der",     # 0=NONE 1=LOW 2=MEDIUM 3=HIGH
                   "reg01_izq", "reg01_der", "registro01",
                   # HU0007-2 (articulaciones) y HU0009 (fusión): columnas nuevas, al final
                   "n_joints_ok", "joints_no_disp", "edad_manos_ms", "par_dt_ms", "desync_manos",
                   "roi_izq", "roi_der",   # origen del último recuadro enviado: mano | muneca | vacío (sin recuadro)
                   "lag_cam_ms",          # ms entre que el frame TERMINÓ de llegar al PC (USB) y que Python lo recibió (cola de cámara)
                   "frames_descartados",  # frames viejos descartados de la cola en este ciclo
                   # cambio 3 (HU0021-1, HU0022-1): para reconstruir la secuencia de notas. lam_sorteo = λ EXACTO
                   # (repr) que recibió elegir_siguiente_nota, solo en la fila con nota nueva (la columna lambda va redondeada)
                   "nota_id", "lam_sorteo", "semilla", "version", "commit",
                   # P-015 (HU0008-1, D-024; solo medición): edad del último dato de cada mano; si baja, hubo dato nuevo
                   "edad_izq_ms", "edad_der_ms"]

# Latencias del navegador: mismo formato que el botón "Descargar latencias" de index.html
COLUMNAS_LATENCIAS = ["t_epoch_ms", "tipo", "latencia_ms", "transporte_ms", "output_latency_ms", "base_latency_ms",
                      "latencia_llegada_ms"]   # D-009: latencia_ms + lag_cam_ms (columna nueva, al final)


def abrir_csv(ruta, columnas):
    """Abre `ruta` para escribir (newline="", como csv pide), escribe la fila de cabecera `columnas` y devuelve
    (archivo, writer). No hace flush: lo decide quien la llama (igual que antes del refactor)."""
    archivo = open(ruta, "w", newline="")
    writer = csv.writer(archivo)
    writer.writerow(columnas)
    return archivo, writer
