import numpy as np

PUNTAS_DEDOS = [4, 8, 12, 16, 20]  # pulgar, índice, medio, anular, meñique

def calcular_apertura(hand_landmarks):
    centro = hand_landmarks.landmark[0]  # muñeca, como aproximación del centro de la palma
    distancias = []
    for idx in PUNTAS_DEDOS:
        punta = hand_landmarks.landmark[idx]
        d = np.sqrt((punta.x - centro.x) ** 2 + (punta.y - centro.y) ** 2)
        distancias.append(d)
    return np.mean(distancias)  # típicamente ~0.05 (puño) a ~0.25 (mano abierta) — ajustar viendo valores reales


def apertura_vigente(ult_apertura, ult_t_ap, t_ahora, hold_s):
    """Cambio 1 (HU0008-2, P-006): qué aperturas de mano siguen vigentes en este instante.
    Una mano es vigente si tiene dato y ese dato salió de un frame de hace <= hold_s segundos
    (main.py usa HOLD_APERTURA_S = 0.5). Relación: la llama bucle_kinect con lo que devuelve
    HiloManos.estado(); si no queda ninguna mano vigente, bucle_kinect reporta ausencia
    (apertura y apertura01 vacías) y el navegador lleva el timbre al valor neutro.
    Variables: `ult_apertura` {"izq"|"der": apertura o None}, `ult_t_ap` {lado: perf_counter del frame},
    `t_ahora` (perf_counter del frame actual).
    Devuelve (efectivas, apertura_val): {lado: apertura} vigentes y su promedio, o ({}, None)."""
    efectivas = {l: v for l, v in ult_apertura.items()
                 if v is not None and t_ahora - ult_t_ap[l] <= hold_s}
    apertura_val = float(np.mean(list(efectivas.values()))) if efectivas else None
    return efectivas, apertura_val