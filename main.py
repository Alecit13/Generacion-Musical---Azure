import faulthandler
faulthandler.enable(all_threads=True)  # si el proceso muere por un fallo nativo, muestra dónde
import asyncio
import collections
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.framework.formats import landmark_pb2
import os
os.environ["PATH"] = r"C:\Program Files\Azure Kinect Body Tracking SDK\tools;" + os.environ["PATH"]
import pykinect_azure as pykinect
import websockets
import csv
import time
import sys
from datetime import datetime
from zona import calcular_zona
from muestreo import elegir_siguiente_nota, calcular_octava
from manos import calcular_apertura
from servidor import manejar_cliente, enviar_a_todos

# =====================================================================
# PARÁMETROS (todo lo ajustable está aquí arriba)
# =====================================================================

# Servidor
HOST_WS = "localhost"
PUERTO_WS = 8765

# Música
NOTA_INICIAL, OCTAVA_INICIAL = "Do", 4
ZONA_INICIAL = "medio"
NOTAS_POR_SEG_MIN = 1.0     # tempo mínimo (piernas quietas): 1 nota por segundo
NOTAS_POR_SEG_MAX = 4.0     # tempo máximo (piernas muy activas): 4 notas por segundo

# Mapeo de extremidades (RF05) y normalización por usuario (RF04)
VENTANA_INTENSIDAD_S = 2.0   # ventana de tiempo para medir la amplitud de las 4 extremidades
VENTANA_FLUIDEZ_S = 0.6      # ventana de tiempo para medir la suavidad (lambda)
LAMBDA_MIN = 0.05            # lambda nunca baja de aquí (igual que antes)
EMA_VEL_RODILLA = 0.4        # suavizado de la velocidad angular (0-1; más alto = menos suavizado)
NORM_VENTANA_S = 20.0        # el usuario "se calibra" con sus últimos 20 s de movimiento
NORM_CALENTAMIENTO_S = 3.0   # durante los primeros 3 s la salida normalizada vale 0.5
# Rangos mínimos: evitan que el ruido del sensor se amplifique cuando el usuario está quieto
RANGO_MIN_VEL_RODILLA = 30.0     # grados/s
RANGO_MIN_AMPLITUD = 100.0       # mm
RANGO_MIN_ACC = 3000.0           # mm/s^2
RANGO_MIN_APERTURA = 0.05        # unidades de "apertura" de manos.py

# Manos (MediaPipe sobre un recorte alrededor de cada mano) -> configuración A elegida
CONFIANZA_DETECCION_MANO = 0.5   # bájalo a 0.4 si se pierden manos
COMPLEJIDAD_MODELO = 0           # 0 = rápido (lite), 1 = más preciso
ALTERNAR_MANOS = True            # True = una mano por ciclo (más rápido)
HOLD_APERTURA_S = 0.5            # si se pierde una mano, se mantiene su última apertura este tiempo
APERTURA_NEUTRA = 0.12           # valor inicial si aún nunca se detectó una mano
FOCAL_COLOR_PX = 610             # focal aprox. de la cámara de color a 720p
TAMANO_MANO_M = 0.35             # tamaño del recuadro en metros (mano + margen)
ROI_MIN_PX, ROI_MAX_PX = 96, 400 # límites del recuadro en píxeles
CONF_MIN_ARTICULACION = 1        # 0=NONE, 1=LOW, 2=MEDIUM (confianza de la Kinect)
MOSTRAR_RECUADROS = False        # True = dibuja el recuadro de cada mano (útil para depurar)

# Ventana de vídeo
DIBUJAR_CADA = 2                 # dibuja/muestra 1 de cada N ciclos (ahorra ~3 ms por ciclo)

# Body tracking: dónde corre la red neuronal del esqueleto
#   "cpu" | "directml" | "cuda"   (el sistema final usa "cuda": python main.py cuda)
MODO_BODY_TRACKER = sys.argv[1] if len(sys.argv) > 1 else "cpu"

# =====================================================================
# Reloj de precisión para medir la latencia
# =====================================================================
def _anclar_reloj():
    """Sincroniza time.time() (≈15 ms de resolución en Windows) con perf_counter().
    Espera el siguiente 'tic' del reloj de pared y guarda ese instante en ambos relojes.
    Variables: devuelve (t_pared_s, t_perf_s), que se guardan en _T0_PARED y _T0_PERF."""
    t = time.time()
    while time.time() == t:
        pass
    return time.time(), time.perf_counter()


_T0_PARED, _T0_PERF = _anclar_reloj()


def ahora_ms():
    """Hora actual en milisegundos desde 1970 (epoch) con precisión de ~0.1 ms.
    Se usa en bucle_kinect para estampar t_cap_ms (llega el frame) y t_env_ms (se envía);
    index.html los resta de Date.now() para obtener la latencia captura -> sonido (RNF01)."""
    return (_T0_PARED + (time.perf_counter() - _T0_PERF)) * 1000.0


# =====================================================================
# Azure Kinect
# =====================================================================
pykinect.initialize_libraries(track_body=True)

device_config = pykinect.default_configuration
device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_720P
device_config.depth_mode = pykinect.K4A_DEPTH_MODE_NFOV_UNBINNED
device_config.camera_fps = pykinect.K4A_FRAMES_PER_SECOND_30
device_config.wired_sync_mode = pykinect.K4A_WIRED_SYNC_MODE_STANDALONE

device = pykinect.start_device(config=device_config)

# pykinect usa esta configuración global al crear el tracker; aquí elegimos CPU/GPU
from pykinect_azure.k4abt import _k4abtTypes as k4abt_types
MODOS_TRACKER = {
    "cpu": k4abt_types.K4ABT_TRACKER_PROCESSING_MODE_CPU,
    "directml": k4abt_types.K4ABT_TRACKER_PROCESSING_MODE_GPU_DIRECTML,
    "cuda": k4abt_types.K4ABT_TRACKER_PROCESSING_MODE_GPU_CUDA,
}
k4abt_types.k4abt_tracker_default_configuration.processing_mode = MODOS_TRACKER[MODO_BODY_TRACKER]
body_tracker = pykinect.start_body_tracker()
print(f"Body tracker en modo: {MODO_BODY_TRACKER}")

# Articulaciones usadas por el mapeo de extremidades
J_PELVIS = pykinect.K4ABT_JOINT_PELVIS
J_MUNECAS = (pykinect.K4ABT_JOINT_WRIST_LEFT, pykinect.K4ABT_JOINT_WRIST_RIGHT)
J_TOBILLOS = (pykinect.K4ABT_JOINT_ANKLE_LEFT, pykinect.K4ABT_JOINT_ANKLE_RIGHT)
J_EXTREMIDADES = J_MUNECAS + J_TOBILLOS            # las 4 extremidades
J_RODILLAS = {                                       # (cadera, rodilla, tobillo) de cada pierna
    "izq": (pykinect.K4ABT_JOINT_HIP_LEFT, pykinect.K4ABT_JOINT_KNEE_LEFT, pykinect.K4ABT_JOINT_ANKLE_LEFT),
    "der": (pykinect.K4ABT_JOINT_HIP_RIGHT, pykinect.K4ABT_JOINT_KNEE_RIGHT, pykinect.K4ABT_JOINT_ANKLE_RIGHT),
}

# =====================================================================
# MediaPipe Hands: un detector por mano
# =====================================================================
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands


def crear_detector():
    # static_image_mode=True porque el recorte se mueve con la mano en cada frame
    return mp_hands.Hands(
        static_image_mode=True,
        max_num_hands=1,
        model_complexity=COMPLEJIDAD_MODELO,
        min_detection_confidence=CONFIANZA_DETECCION_MANO,
    )


detectores = {"izq": crear_detector(), "der": crear_detector()}
ARTICULACIONES_MANO = {
    "izq": pykinect.K4ABT_JOINT_HAND_LEFT,
    "der": pykinect.K4ABT_JOINT_HAND_RIGHT,
}

# =====================================================================
# Estado entre frames
# =====================================================================
zona_actual = ZONA_INICIAL
contador_estable = 0
nota_actual, octava_actual = NOTA_INICIAL, OCTAVA_INICIAL
nota_id = 0          # contador de notas nuevas: el HTML toca una nota cada vez que cambia
t_ult_nota = 0.0     # instante (perf_counter) del último tick de nota
lat_tick_ms = None   # RNF02: retraso entre el "tick" programado y el sorteo de la nota

# Cada ejecución guarda su propio log en la carpeta "sesiones" (no se sobrescriben)
CARPETA_SESIONES = "sesiones"
os.makedirs(CARPETA_SESIONES, exist_ok=True)
ruta_log = os.path.join(CARPETA_SESIONES, f"sesion_{datetime.now():%Y%m%d_%H%M%S}.csv")

log_file = open(ruta_log, "w", newline="")
log_writer = csv.writer(log_file)
# Las 10 primeras columnas conservan el orden anterior (grafico.py sigue funcionando)
log_writer.writerow(["timestamp", "zona", "lambda", "acc_media", "nota", "octava", "apertura",
                     "apertura_izq", "apertura_der", "manos",
                     "tempo", "intensidad", "apertura01", "vel_rodilla", "amplitud_mm", "t_cap_ms",
                     "lat_tick_ms"])
log_file.flush()
print(f"Guardando la sesión en: {ruta_log}")

# ---------- Medición de rendimiento ----------
ETAPAS = ("captura", "tracker", "manos", "mapeo", "salida", "dibujo")
acum = dict.fromkeys(ETAPAS, 0.0)
perf = {"n": 0, "t": time.perf_counter()}
REPORTE_CADA = 60  # ciclos entre reportes


def reportar():
    """Imprime ciclos/s y milisegundos promedio por etapa cada REPORTE_CADA ciclos.
    Usa los acumuladores `acum` (que llena bucle_kinect) y el contador `perf`; luego los reinicia."""
    ahora = time.perf_counter()
    dur, n = ahora - perf["t"], perf["n"]
    etapas = " | ".join(f"{e}={acum[e] / n * 1000:.0f}ms" for e in ETAPAS)
    print(f"[PERF] {n / dur:.1f} ciclos/s | ciclo={dur / n * 1000:.0f}ms | {etapas}")
    for e in ETAPAS:
        acum[e] = 0.0
    perf["n"], perf["t"] = 0, ahora


def _fmt(valor):
    """Número redondeado, o vacío si no hay dato (así no cuenta como 0 en los gráficos)."""
    return "" if valor is None else round(valor, 3)


# =====================================================================
# Normalización por usuario (RF04) y mapeo de extremidades (RF05)
# =====================================================================
class NormalizadorAdaptativo:
    """Convierte una medida cruda (grados/s, mm, ...) a [0,1] según el propio rango del usuario.
    Guarda los valores de los últimos NORM_VENTANA_S segundos y usa sus percentiles 5 y 95
    como 'mínimo' y 'máximo' (robusto a picos). `rango_min` evita amplificar ruido si el
    usuario está quieto. Lo usan MapeoExtremidades (tempo, intensidad, lambda) y bucle_kinect
    (apertura)."""

    def __init__(self, rango_min):
        self.muestras = collections.deque()   # pares (tiempo, valor)
        self.rango_min = rango_min

    def actualizar(self, valor, t):
        self.muestras.append((t, valor))
        while t - self.muestras[0][0] > NORM_VENTANA_S:
            self.muestras.popleft()
        if t - self.muestras[0][0] < NORM_CALENTAMIENTO_S:
            return 0.5                      # aún calibrando: valor neutro
        vals = np.fromiter((v for _, v in self.muestras), dtype=float)
        lo, hi = np.percentile(vals, [5, 95])
        hi = max(hi, lo + self.rango_min)
        return float(np.clip((valor - lo) / (hi - lo), 0.0, 1.0))


class VelocidadAngular:
    """Velocidad angular suavizada (grados/s) de un ángulo que llega ciclo a ciclo.
    Usa el tiempo REAL entre ciclos (dt), no el número de ciclos. Si pasa más de 0.5 s
    sin datos, se reinicia. Una instancia por rodilla dentro de MapeoExtremidades."""

    def __init__(self):
        self.ang_prev = None
        self.t_prev = None
        self.suav = 0.0

    def actualizar(self, angulo, t):
        w = None
        if self.t_prev is not None:
            dt = t - self.t_prev
            if 0.0 < dt <= 0.5:
                bruta = abs(angulo - self.ang_prev) / dt
                self.suav = EMA_VEL_RODILLA * bruta + (1 - EMA_VEL_RODILLA) * self.suav
                w = self.suav
        self.ang_prev, self.t_prev = angulo, t
        return w


def angulo_articulacion(a, b, c):
    """Ángulo (grados) en el punto b formado por a-b-c. Con cadera, rodilla y tobillo
    da el ángulo de la rodilla (180° = pierna estirada). Lo usa MapeoExtremidades."""
    v1, v2 = a - b, c - b
    cos = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
    return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))


class MapeoExtremidades:
    """Traduce el esqueleto a los parámetros musicales de la tabla del TI (RF05):
         velocidad angular de rodillas       -> tempo       (0-1)
         amplitud de 4 extremidades en ~2 s  -> intensidad  (0-1)
         suavidad de muñecas + tobillos      -> lambda      (0.05-1)
    (registro/tono y timbre se calculan aparte: altura de muñeca y apertura de manos).
    Variables importantes: `hist` (posiciones recientes de las 4 extremidades RELATIVAS a la
    pelvis, para ignorar si el usuario camina), y un NormalizadorAdaptativo por parámetro (RF04).
    Se llama una vez por ciclo desde bucle_kinect: actualizar(skeleton, t) -> dict."""

    def __init__(self):
        self.hist = collections.deque()      # (t, array 4x3 en mm)
        self.vel_rod = {"izq": VelocidadAngular(), "der": VelocidadAngular()}
        self.n_tempo = NormalizadorAdaptativo(RANGO_MIN_VEL_RODILLA)
        self.n_inten = NormalizadorAdaptativo(RANGO_MIN_AMPLITUD)
        self.n_acc = NormalizadorAdaptativo(RANGO_MIN_ACC)
        # últimos valores (se conservan si una articulación no es fiable en este ciclo)
        self.tempo, self.intensidad, self.lam = 0.5, 0.0, 1.0
        self.vel_rodilla, self.amplitud_mm, self.acc_mm = 0.0, 0.0, 0.0

    @staticmethod
    def _pos(joints, i):
        p = joints[i].position.xyz
        return np.array([p.x, p.y, p.z], dtype=float)

    @staticmethod
    def _ok(joints, i):
        return joints[i].confidence_level >= CONF_MIN_ARTICULACION

    def actualizar(self, skeleton, t):
        J = skeleton.joints

        # --- Tempo: velocidad angular media de las rodillas ---
        omegas = []
        for lado, (cad, rod, tob) in J_RODILLAS.items():
            if self._ok(J, cad) and self._ok(J, rod) and self._ok(J, tob):
                ang = angulo_articulacion(self._pos(J, cad), self._pos(J, rod), self._pos(J, tob))
                w = self.vel_rod[lado].actualizar(ang, t)
                if w is not None:
                    omegas.append(w)
        if omegas:
            self.vel_rodilla = float(np.mean(omegas))
            self.tempo = self.n_tempo.actualizar(self.vel_rodilla, t)

        # --- Intensidad y lambda: las 4 extremidades relativas a la pelvis ---
        if self._ok(J, J_PELVIS) and all(self._ok(J, i) for i in J_EXTREMIDADES):
            pelvis = self._pos(J, J_PELVIS)
            self.hist.append((t, np.stack([self._pos(J, i) - pelvis for i in J_EXTREMIDADES])))
            while t - self.hist[0][0] > VENTANA_INTENSIDAD_S:
                self.hist.popleft()

            if len(self.hist) >= 5 and t - self.hist[0][0] >= 0.5:
                P = np.stack([p for _, p in self.hist])                  # (n, 4, 3)
                rango = P.max(axis=0) - P.min(axis=0)                    # (4, 3)
                self.amplitud_mm = float(np.linalg.norm(rango, axis=1).mean())
                self.intensidad = self.n_inten.actualizar(self.amplitud_mm, t)

            recientes = [(ti, p) for ti, p in self.hist if t - ti <= VENTANA_FLUIDEZ_S]
            if len(recientes) >= 4:
                ts = np.array([ti for ti, _ in recientes])
                P = np.stack([p for _, p in recientes])
                dt = np.maximum(np.diff(ts), 1e-3)
                V = np.diff(P, axis=0) / dt[:, None, None]               # velocidad mm/s
                tv = (ts[1:] + ts[:-1]) / 2
                A = np.diff(V, axis=0) / np.maximum(np.diff(tv), 1e-3)[:, None, None]
                self.acc_mm = float(np.linalg.norm(A, axis=2).mean())    # aceleración mm/s^2
                acc01 = self.n_acc.actualizar(self.acc_mm, t)
                self.lam = max(1.0 - acc01, LAMBDA_MIN)

        return {
            "tempo": self.tempo, "intensidad": self.intensidad, "lam": self.lam,
            "vel_rodilla": self.vel_rodilla, "amplitud_mm": self.amplitud_mm, "acc_mm": self.acc_mm,
        }


mapeo = MapeoExtremidades()
norm_apertura = NormalizadorAdaptativo(RANGO_MIN_APERTURA)


# =====================================================================
# Manos
# =====================================================================
def detectar_mano(detector, color_rgb, centro, profundidad_mm):
    """Recorta un cuadrado alrededor de la mano (según la Kinect) y corre MediaPipe ahí.
    Devuelve (landmarks en coordenadas de la imagen completa o None, recuadro usado).
    Variables: `lado` del recuadro depende de la distancia (más lejos = más pequeño)."""
    alto, ancho = color_rgb.shape[:2]
    cx, cy = centro
    if not (0 <= cx < ancho and 0 <= cy < alto):
        return None, None

    z_m = max(profundidad_mm / 1000.0, 0.3)
    lado = int(np.clip(FOCAL_COLOR_PX * TAMANO_MANO_M / z_m, ROI_MIN_PX, ROI_MAX_PX))

    x0 = int(np.clip(cx - lado // 2, 0, max(ancho - lado, 0)))
    y0 = int(np.clip(cy - lado // 2, 0, max(alto - lado, 0)))
    x1, y1 = min(x0 + lado, ancho), min(y0 + lado, alto)
    recuadro = (x0, y0, x1, y1)

    recorte = np.ascontiguousarray(color_rgb[y0:y1, x0:x1])
    if recorte.size == 0:
        return None, recuadro

    resultado = detector.process(recorte)
    if not resultado.multi_hand_landmarks:
        return None, recuadro

    w_rec, h_rec = x1 - x0, y1 - y0
    landmarks = landmark_pb2.NormalizedLandmarkList()
    for p in resultado.multi_hand_landmarks[0].landmark:
        landmarks.landmark.add(
            x=(x0 + p.x * w_rec) / ancho,
            y=(y0 + p.y * h_rec) / alto,
            z=p.z * w_rec / ancho,
        )
    return landmarks, recuadro


# =====================================================================
# Bucle principal
# =====================================================================
async def bucle_kinect():
    """Un ciclo: captura -> esqueleto -> manos -> mapeo -> nota -> ENVÍO -> dibujo.
    Une todo: usa calcular_zona (registro), detectar_mano+calcular_apertura (timbre),
    mapeo.actualizar (tempo, intensidad, lambda) y elegir_siguiente_nota (melodía);
    envía el resultado por WebSocket a index.html. El envío va ANTES de dibujar para
    no sumar el tiempo de dibujo a la latencia.
    Variables de latencia: t_cap_ms (cuándo llegó el frame; RNF01 se calcula en el HTML)
    y lat_tick_ms (retraso entre el tick programado y el sorteo de la nota; RNF02)."""
    global zona_actual, contador_estable, nota_actual, octava_actual, nota_id, t_ult_nota, lat_tick_ms
    ciclo_manos = 0
    ciclo_global = 0
    ult_apertura = {"izq": None, "der": None}     # última apertura conocida de cada mano
    ult_t_ap = {"izq": -1e9, "der": -1e9}         # cuándo se midió
    ult_landmarks = {"izq": None, "der": None}    # solo para dibujar
    apertura_prev = APERTURA_NEUTRA
    apertura01 = 0.5
    display = None

    while True:
        t = time.perf_counter()
        capture = device.update()
        t_cap_ms = ahora_ms()                     # <- instante en que Python recibe el frame

        ok_depth, _ = capture.get_depth_image()
        ok_color, color_image = capture.get_color_image()
        if not ok_depth or not ok_color:
            await asyncio.sleep(0)
            continue

        color_image = color_image.copy()
        t_ciclo = time.perf_counter()
        acum["captura"] += t_ciclo - t

        t = time.perf_counter()
        body_frame = body_tracker.update()
        num_bodies = body_frame.get_num_bodies()
        acum["tracker"] += time.perf_counter() - t

        dibujar_ahora = (ciclo_global % DIBUJAR_CADA == 0)
        ciclo_global += 1
        manos_detectadas = []
        recuadros_hoy = []

        if num_bodies > 0:
            skeleton = body_frame.get_body_skeleton(0)

            # ---- Registro (tono): altura de la muñeca izquierda ----
            muneca = skeleton.joints[pykinect.K4ABT_JOINT_WRIST_LEFT].position.xyz
            hombro = skeleton.joints[pykinect.K4ABT_JOINT_SHOULDER_LEFT].position.xyz
            cadera = skeleton.joints[pykinect.K4ABT_JOINT_HIP_LEFT].position.xyz
            zona_actual, contador_estable = calcular_zona(
                muneca.y, hombro.y, cadera.y, zona_actual, contador_estable
            )

            # ---- Manos (timbre) ----
            t = time.perf_counter()
            color_rgb = cv2.cvtColor(color_image, cv2.COLOR_BGRA2RGB)
            body2d = body_frame.get_body2d(0, pykinect.K4A_CALIBRATION_TYPE_COLOR)

            if ALTERNAR_MANOS:
                lados_hoy = ["izq"] if ciclo_manos % 2 == 0 else ["der"]
            else:
                lados_hoy = ["izq", "der"]
            ciclo_manos += 1

            frescos = []
            for lado in lados_hoy:
                id_articulacion = ARTICULACIONES_MANO[lado]
                articulacion = skeleton.joints[id_articulacion]
                ult_landmarks[lado] = None
                if articulacion.confidence_level < CONF_MIN_ARTICULACION:
                    continue
                centro = body2d.joints[id_articulacion].get_coordinates()
                landmarks, recuadro = detectar_mano(
                    detectores[lado], color_rgb, centro, articulacion.position.xyz.z
                )
                if recuadro is not None:
                    recuadros_hoy.append((recuadro, landmarks is not None))
                if landmarks is not None:
                    ult_apertura[lado] = calcular_apertura(landmarks)
                    ult_t_ap[lado] = t_ciclo
                    ult_landmarks[lado] = landmarks
                    frescos.append(ult_apertura[lado])

            # Si una mano se pierde, se mantiene su última apertura HOLD_APERTURA_S segundos
            efectivas = {l: v for l, v in ult_apertura.items()
                         if v is not None and t_ciclo - ult_t_ap[l] <= HOLD_APERTURA_S}
            apertura_val = float(np.mean(list(efectivas.values()))) if efectivas else apertura_prev
            apertura_prev = apertura_val
            if frescos:                            # solo se recalibra con datos nuevos
                apertura01 = norm_apertura.actualizar(float(np.mean(frescos)), t_ciclo)
            manos_detectadas = [h for h in ult_landmarks.values() if h is not None]
            acum["manos"] += time.perf_counter() - t

            # ---- Extremidades: tempo, intensidad, lambda ----
            t = time.perf_counter()
            m = mapeo.actualizar(skeleton, t_ciclo)
            lam = m["lam"]

            # ---- Reloj musical: tick -> sorteo de la nota (RNF02) ----
            intervalo_s = 1.0 / (NOTAS_POR_SEG_MIN + m["tempo"] * (NOTAS_POR_SEG_MAX - NOTAS_POR_SEG_MIN))
            lat_tick_ms = None                       # solo tiene valor en el ciclo en que hay nota nueva
            t_programado = t_ult_nota + intervalo_s  # instante en que "tocaba" el tick
            if t_ciclo >= t_programado:
                es_primera = (nota_id == 0)          # la primera nota no tiene tick previo
                nota_actual = elegir_siguiente_nota(nota_actual, lam)
                octava_actual = calcular_octava(zona_actual)
                nota_id += 1
                if not es_primera:
                    lat_tick_ms = (time.perf_counter() - t_programado) * 1000.0   # RNF02
                # se avanza desde el tick programado (no desde ahora) para no acumular deriva
                t_ult_nota = t_programado if (t_ciclo - t_programado) < intervalo_s else t_ciclo
            acum["mapeo"] += time.perf_counter() - t

            # ---- ENVÍO (antes de dibujar) ----
            t = time.perf_counter()
            ap_izq, ap_der = efectivas.get("izq"), efectivas.get("der")
            await enviar_a_todos({
                "nota": nota_actual,
                "octava": octava_actual,
                "nota_id": nota_id,
                "intervalo_s": round(intervalo_s, 3),
                "lam": round(lam, 2),
                "tempo": round(m["tempo"], 3),
                "intensidad": round(m["intensidad"], 3),
                "apertura": round(apertura_val, 3),
                "apertura01": round(apertura01, 3),
                "apertura_izq": round(ap_izq or 0.0, 3),
                "apertura_der": round(ap_der or 0.0, 3),
                "manos": len(manos_detectadas),
                "t_cap_ms": round(t_cap_ms, 1),
                "t_env_ms": round(ahora_ms(), 1),
                "lat_tick_ms": None if lat_tick_ms is None else round(lat_tick_ms, 1),
            })

            print(f"Nota: {nota_actual}{octava_actual} | zona={zona_actual:<6} | lambda={lam:.2f} "
                  f"| acc={m['acc_mm']:.0f}mm/s2 | tempo={m['tempo']:.2f} | inten={m['intensidad']:.2f} "
                  f"| apertura={apertura_val:.3f} | manos={len(manos_detectadas)}")
            log_writer.writerow([
                time.time(), zona_actual, round(lam, 3), round(m["acc_mm"], 1),
                nota_actual, octava_actual,
                _fmt(apertura_val if efectivas else None), _fmt(ap_izq), _fmt(ap_der),
                len(manos_detectadas),
                round(m["tempo"], 3), round(m["intensidad"], 3), round(apertura01, 3),
                round(m["vel_rodilla"], 1), round(m["amplitud_mm"], 1), round(t_cap_ms, 1),
                "" if lat_tick_ms is None else round(lat_tick_ms, 1),
            ])
            log_file.flush()
            acum["salida"] += time.perf_counter() - t

        # ---- Dibujo (después del envío, y solo 1 de cada DIBUJAR_CADA ciclos) ----
        if dibujar_ahora:
            t = time.perf_counter()
            display = cv2.cvtColor(color_image, cv2.COLOR_BGRA2BGR)
            if num_bodies > 0:
                if MOSTRAR_RECUADROS:
                    for rec, ok in recuadros_hoy:
                        cv2.rectangle(display, rec[:2], rec[2:], (0, 255, 0) if ok else (0, 0, 255), 2)
                display = body_frame.draw_bodies(display, pykinect.K4A_CALIBRATION_TYPE_COLOR)
                for h in manos_detectadas:
                    mp_drawing.draw_landmarks(display, h, mp_hands.HAND_CONNECTIONS)
            cv2.imshow('Kinect', display)
            tecla = cv2.waitKey(1) & 0xFF
            acum["dibujo"] += time.perf_counter() - t
            if tecla == ord("q"):
                break

        perf["n"] += 1
        if perf["n"] >= REPORTE_CADA:
            reportar()
        await asyncio.sleep(0)  # cede el control para que el servidor pueda enviar mensajes


async def main():
    server = await websockets.serve(manejar_cliente, HOST_WS, PUERTO_WS,ping_interval=None)
    try:
        await bucle_kinect()
    finally:
        server.close()


try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Detenido con Ctrl+C")
finally:
    # Se ejecuta siempre (q, Ctrl+C o error) para liberar la Kinect
    for d in detectores.values():
        d.close()
    body_tracker.destroy()
    device.close()
    cv2.destroyAllWindows()
    log_file.close()
    print("Kinect cerrada correctamente")
    print(f"Sesión guardada en {ruta_log}. Para ver los gráficos: python3.11 grafico.py")