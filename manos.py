import numpy as np

PUNTAS_DEDOS = [4, 8, 12, 16, 20]  # pulgar, índice, medio, anular, meñique

def calcular_apertura(hand_landmarks):
    centro = hand_landmarks.landmark[0]  # muñeca, como aproximación del centro de la palma
    distancias = []
    for idx in PUNTAS_DEDOS:
        punta = hand_landmarks.landmark[idx]
        d = np.sqrt((punta.x - centro.x) ** 2 + (punta.y - centro.y) ** 2)
        distancias.append(d)
    # Medido el 07/11 a la distancia del protocolo: ≈ 0.021 (puño) a ≈ 0.048 (abierta). Está en coordenadas normalizadas de la
    # imagen completa, así que depende de la distancia a la cámara.
    return np.mean(distancias)


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


def edades_por_mano_ms(ult_t_ap, t_ahora):
    """P-015 (HU0008-1, D-024; solo medición): edad en ms del último dato de CADA mano, medida desde el frame actual.
    HiloManos solo cambia ult_t_ap[lado] cuando MediaPipe detecta esa mano, así que cada vez que la edad de una mano
    BAJA entre filas del CSV hubo un dato nuevo: contándolas offline salen las actualizaciones por mano/s sin el
    redondeo de las columnas de apertura. Misma definición que edad_manos_ms (que es la menor de las dos).
    Relación: la llama bucle_kinect con lo que devuelve HiloManos.estado(); el resultado solo va al CSV.
    Variables: `ult_t_ap` {"izq"|"der": perf_counter del frame que la midió; -1e9 = nunca}, `t_ahora` (perf_counter
    del frame actual). Devuelve {lado: ms redondeado a 0.1, o None si esa mano nunca tuvo dato}."""
    return {l: (round((t_ahora - t) * 1000.0, 1) if t > -1e8 else None) for l, t in ult_t_ap.items()}


class TimbrePorManos:
    """Cambio 6 (HU0017-1, D-024): apertura01 (timbre) a partir del PROMEDIO de la última apertura válida de cada mano
    (vencimiento HOLD_APERTURA_S, ver apertura_vigente). Antes la normalizaba HiloManos con la mano del trabajo y, al
    alternar manos, saltaba entre las dos (fase 2d del 07/11: 14.6 saltos > 0.3 por segundo).
    Relación: bucle_kinect la llama una vez por ciclo con lo que devuelve apertura_vigente; recibe el normalizador desde
    fuera (main.py: NormalizadorAdaptativo(RANGO_MIN_APERTURA)) para poder probarla sin la Kinect.
    Variables: `norm` (necesita actualizar(valor, t) y normalizar(valor, t)), `t_ult_fresco` (instante del frame del dato
    de manos más nuevo ya usado para recalibrar)."""

    def __init__(self, normalizador):
        self.norm = normalizador
        self.t_ult_fresco = None

    def actualizar(self, apertura_val, t_fresco, t):
        """apertura_val: promedio de las manos vigentes o None; t_fresco: instante del frame del dato más nuevo de esas
        manos; t: instante del ciclo. Recalibra solo con datos nuevos (t_fresco creció) y en los demás ciclos solo normaliza.
        Devuelve apertura01 en [0,1], o None si no hay mano vigente (cambio 1: se reporta ausencia)."""
        if apertura_val is None:
            return None
        if self.t_ult_fresco is None or t_fresco > self.t_ult_fresco:
            self.t_ult_fresco = t_fresco
            return self.norm.actualizar(apertura_val, t_fresco)
        return self.norm.normalizar(apertura_val, t)