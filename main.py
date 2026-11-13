import faulthandler
faulthandler.enable(all_threads=True)  # si el proceso muere por un fallo nativo, muestra dónde
import asyncio
import collections
import gc
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.framework.formats import landmark_pb2
import os
os.environ["PATH"] = r"C:\Program Files\Azure Kinect Body Tracking SDK\tools;" + os.environ["PATH"]
import pykinect_azure as pykinect
import websockets
import csv
import json
import queue
import random
import secrets
import socket
import subprocess
import threading
import time
import sys
from datetime import datetime
from zona import calcular_zona, zona_desde_registro
from muestreo import elegir_siguiente_nota, calcular_octava, reiniciar_estado
from manos import calcular_apertura, apertura_vigente, TimbrePorManos, edades_por_mano_ms
from servidor import manejar_cliente, enviar_a_todos
import servidor

# =====================================================================
# PARÁMETROS (todo lo ajustable está aquí arriba)
# =====================================================================

# Versión: queda escrita en consola y en el nombre del CSV, para saber SIEMPRE qué código se usó
VERSION_MAIN = "mjpg-cambios-2026-11-07"

# Servidor
HOST_WS = "127.0.0.1"   # cambio 7b: dirección IPv4 fija (antes "localhost", que en este equipo resuelve a ::1 y a 127.0.0.1)
PUERTO_WS = 8765

# Cambio 7b (HU0010-2): el socket de escucha se abre YA, antes de encender la Kinect y el tracker (varios segundos).
# En Windows cada intento contra un puerto cerrado tarda 2.0 s en fallar (MEDIDO 07/11), así que la página tardaba
# hasta ≈ 4 s en reconectar. Con el socket abierto, el navegador se conecta durante el arranque y queda esperando;
# main() lo entrega a websockets.serve(sock=SOCK_WS) y la conexión se completa en el primer ciclo.
SOCK_WS = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    SOCK_WS.bind((HOST_WS, PUERTO_WS))
except OSError as e:
    raise SystemExit(f"El puerto {PUERTO_WS} ya está en uso ({e}): ¿hay otro main.py abierto?") from None
SOCK_WS.listen(16)

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
RANGO_MIN_APERTURA = 0.015       # unidades de "apertura" de manos.py. 07/11 (MEDIDO, distancia del protocolo): abierta ≈ 0.048,
                                 # puño ≈ 0.021 (ancho ≈ 0.027); ruido en reposo 0.001-0.006. Antes 0.05 (> ancho real: apertura01 ≤ ≈ 0.58)

# Tono: REGISTRO (octava) a partir de ángulos de articulaciones (RF05: ángulos articulares -> tono)
REGISTRO_POR_ANGULO = True        # True = ángulo de los hombros; False = altura de la muñeca izquierda (versión anterior)
CONF_MIN_ANGULO_BRAZO = 2         # confianza mínima para usar el ángulo de un brazo (2 = MEDIUM; 1 = LOW = pose "predicha")
EMA_ANGULO_BRAZO = 0.5            # suavizado del ángulo del hombro (0-1; más alto = menos suavizado)
RANGO_MIN_ANGULO_BRAZO = 60.0     # grados: rango mínimo para normalizar (evita que 20° de movimiento ya sea "agudo")
HOLD_ANGULO_S = 0.5               # si un brazo deja de ser fiable, se mantiene su último valor este tiempo
UMBRAL_REG_GRAVE = 0.33           # registro01 < esto -> "grave" (octava 3)
UMBRAL_REG_AGUDO = 0.66           # registro01 >= esto -> "agudo" (octava 5); en medio -> "medio" (octava 4)
UMBRAL_ESTABILIDAD_ZONA_S = 0.250 # D-010 (HU0015-2): segundos que debe sostenerse una zona candidata antes de confirmarla
                                  # (antes 6 ciclos: ≈ 235 ms a 25.5 Hz, ≈ 200 ms a 30 Hz; zona.py sigue en frames)
DT_MAX_ZONA_S = 0.1               # tope del tiempo que suma un ciclo: tras una ausencia del cuerpo, el hueco no cuenta como "sostenido"

# Manos (MediaPipe sobre un recorte alrededor de cada mano) -> configuración A elegida
CONFIANZA_DETECCION_MANO = 0.5   # bájalo a 0.4 si se pierden manos
COMPLEJIDAD_MODELO = 0           # 0 = rápido (lite), 1 = más preciso
HILO_POR_MANO = False            # True = un hilo para cada mano (las dos se procesan EN PARALELO en cada ciclo; ignora ALTERNAR_MANOS)
                                 # perf/ciclo-30hz: False porque con 2 hilos el ciclo subió de 38.4 a 42.0 ms (sesiones 28d vs 28e)
                                 # False = un solo hilo para las dos manos (comportamiento de v6)
USAR_HILO_MANOS = True           # DIAGNÓSTICO (paso 5b): False = sin hilo de manos ni MediaPipe (sin timbre: apertura siempre "sin mano")
ALTERNAR_MANOS = True            # solo con HILO_POR_MANO=False: True = una mano por trabajo, alternando | False = las 2 manos del mismo frame
HOLD_APERTURA_S = 0.5            # si se pierde una mano, se mantiene su última apertura este tiempo
FOCAL_COLOR_PX = 610             # focal aprox. de la cámara de color a 720p
TAMANO_MANO_M = 0.45             # tamaño del recuadro en metros (mano + margen); antes 0.35: más grande compensa el desfase del modelo lite
ROI_MIN_PX, ROI_MAX_PX = 96, 400 # límites del recuadro en píxeles
CONF_MIN_ARTICULACION = 1        # 0=NONE, 1=LOW, 2=MEDIUM (confianza de la Kinect)
RESPALDO_MUNECA = True            # si la Kinect marca la MANO como NONE, centra el recuadro con la MUÑECA y el CODO
FACTOR_RESPALDO_MUNECA = 0.35    # cuánto se avanza más allá de la muñeca, como fracción del antebrazo (codo->muñeca) en píxeles
MOSTRAR_RECUADROS = False        # True = dibuja el recuadro de cada mano (útil para depurar)

# Ventana de vídeo
MOSTRAR_VENTANA = False          # D-012: sin ventana de OpenCV en evaluaciones (no dibuja ni llama a waitKey; se cierra con Ctrl+C)
                                 # --con-ventana la muestra para depurar (se cierra con q)
DIBUJAR_CADA = 3                # dibuja/muestra 1 de cada N ciclos (con 2 costaba ~3 ms por ciclo; con 3, ~2 ms). Sube a 4-5 si quieres ahorrar más
DESCARTAR_COLA_CAMARA = True     # True = si hay frames viejos en la cola del SDK, se descartan y se usa el MÁS RECIENTE (medido: la cola añadía ~220 ms)
                                 # False = comportamiento anterior (procesa todos los frames en orden, aunque lleguen con retraso)
MAX_DESCARTE_POR_CICLO = 10      # tope de frames que se descartan en un ciclo (seguridad)
COLOR_BGRA32 = False             # EXPERIMENTO (D-007, P-005): desactivado por defecto desde el 01/11 (D-008); con BGRA32 la espera de cámara sube ≈ 22 ms
                                 # True = el SDK entrega el color YA decodificado en BGRA (decodifica en su propio hilo, fuera del ciclo)
                                 # False = MJPG: Python decodifica el JPEG en cada ciclo con cv2.imdecode (medido: to_numpy ≈ 6 ms)
DECODIFICAR_EN_HILO_MANOS = True   # D-013/D-015: el ciclo solo copia el JPEG (MJPG) y lo decodifica HiloManos (el tracker no usa
                                   # el color); --sin-decod-hilo vuelve a to_numpy() en el ciclo (reversible)
SWITCH_INTERVAL_S = None         # DIAGNÓSTICO (paso 5b): None = valor de Python (5 ms); 0.001 = sys.setswitchinterval(0.001)
                                 # (el hilo principal recupera antes el GIL cuando el hilo de manos ejecuta Python)
LEER_PROFUNDIDAD_NUMPY = False   # False = NO descarga la imagen de profundidad a numpy (el tracker usa el capture directamente; solo se comprueba que exista)
                                 # True  = comportamiento anterior (copia ~0.7 MB por ciclo solo para verificar)

# Opciones de línea de comandos para los experimentos (así no se edita main.py entre corridas):
#   python main.py cuda lite                     (--sin-decod-hilo para decodificar en el ciclo; --con-ventana para depurar)
# Cada opción solo cambia un interruptor sobre la constante de arriba; sin opciones, todo queda como está.
# --sin-ventana (D-012) y --decod-hilo (D-015) coinciden con el valor por defecto; se aceptan para que los comandos anteriores
# sigan valiendo.
OPCIONES_VALIDAS = ("--con-ventana", "--sin-ventana", "--decod-hilo", "--sin-decod-hilo", "--swi1ms", "--sin-manos",
                    "--tempo-medium")
# PRUEBA (07/11, pendiente del OK de Ale): --tempo-medium exige confianza MEDIUM (2) en cadera, rodilla y tobillo para usar una
# rodilla en el tempo; con LOW (posición inferida) esa rodilla no cuenta y, si ninguna cuenta, el tempo mantiene su valor.
# Solo afecta al tempo: CONF_MIN_ARTICULACION (manos, intensidad, λ, n_joints_ok) no cambia.
CONF_MIN_RODILLA_TEMPO = 1
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]       # argumentos posicionales: modo del tracker y modelo
OPCIONES = [a for a in sys.argv[1:] if a.startswith("--")]
# Cambio 3 (HU0021-1, HU0022-1): --seed=N fija la semilla del sorteo de notas; sin --seed se genera una. Va con "=" porque
# un valor suelto ("--seed 42") caería en ARGS como modo del tracker. La semilla no cambia VERSION_MAIN (va en sus columnas).
_semillas = [o for o in OPCIONES if o.startswith("--seed=")]
OPCIONES = [o for o in OPCIONES if not o.startswith("--seed=")]
if len(_semillas) > 1:
    raise ValueError("--seed=N aparece más de una vez")
try:
    SEMILLA = int(_semillas[0].split("=", 1)[1]) if _semillas else secrets.randbelow(2**31)
except ValueError:
    raise ValueError(f"--seed necesita un entero: {_semillas[0]}") from None
_desconocidas = [o for o in OPCIONES if o not in OPCIONES_VALIDAS]
if _desconocidas:   # una errata no debe producir una corrida mal etiquetada
    raise ValueError(f"Opciones desconocidas {_desconocidas}; válidas: {', '.join(OPCIONES_VALIDAS)}")
if "--con-ventana" in OPCIONES and "--sin-ventana" in OPCIONES:
    raise ValueError("--con-ventana y --sin-ventana se contradicen: usa solo una")
if "--con-ventana" in OPCIONES:
    MOSTRAR_VENTANA = True
if "--sin-ventana" in OPCIONES:
    MOSTRAR_VENTANA = False
if "--decod-hilo" in OPCIONES and "--sin-decod-hilo" in OPCIONES:
    raise ValueError("--decod-hilo y --sin-decod-hilo se contradicen: usa solo una")
if "--decod-hilo" in OPCIONES:
    DECODIFICAR_EN_HILO_MANOS = True
if "--sin-decod-hilo" in OPCIONES:
    DECODIFICAR_EN_HILO_MANOS = False
if "--swi1ms" in OPCIONES:
    SWITCH_INTERVAL_S = 0.001
if "--sin-manos" in OPCIONES:
    USAR_HILO_MANOS = False
if "--tempo-medium" in OPCIONES:
    CONF_MIN_RODILLA_TEMPO = 2

if DECODIFICAR_EN_HILO_MANOS and COLOR_BGRA32:
    raise ValueError("DECODIFICAR_EN_HILO_MANOS solo sirve con MJPG: con COLOR_BGRA32=True usa --sin-decod-hilo")
if SWITCH_INTERVAL_S is not None:
    sys.setswitchinterval(SWITCH_INTERVAL_S)

# Los interruptores de experimento que no estén en su valor por defecto se añaden a VERSION_MAIN
# (nombre del CSV de sesión, _perf.txt y _latencias.csv), así cada corrida queda identificada sin editar el código.
SUFIJO_CONFIG = "".join(s for s, activo in (
    ("-conventana", MOSTRAR_VENTANA),          # desde D-012 la ventana es lo que se sale del defecto
    ("-sindecodhilo", not DECODIFICAR_EN_HILO_MANOS),   # desde D-015 decodificar en el ciclo es lo que se sale del defecto
    (f"-swi{(SWITCH_INTERVAL_S or 0) * 1000:g}ms", SWITCH_INTERVAL_S is not None),
    ("-sinmanos", not USAR_HILO_MANOS),
    ("-tempomedium", CONF_MIN_RODILLA_TEMPO == 2),
) if activo)
VERSION_MAIN += SUFIJO_CONFIG


def commit_git():
    """Cambio 3 (HU0022-1): hash corto del commit con el que corre main.py, con "-sucio" si hay cambios sin commit en
    archivos versionados (los archivos sin versionar, como los CSV nuevos de sesiones/, no cuentan). "desconocido" si
    git falla. Se llama una vez al arrancar; el valor va a la cabecera de _perf.txt y a la columna `commit` del CSV."""
    carpeta = os.path.dirname(os.path.abspath(__file__))
    try:
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=carpeta, capture_output=True,
                           text=True, timeout=5, check=True).stdout.strip()
        sucio = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=carpeta,
                               capture_output=True, text=True, timeout=5, check=True).stdout.strip()
        return h + ("-sucio" if sucio else "")
    except Exception:
        return "desconocido"


COMMIT_GIT = commit_git()
random.seed(SEMILLA)       # el sorteo de notas (muestreo.py) usa el módulo random; numpy no sortea nada en el proyecto
reiniciar_estado()         # dirección y racha iniciales: misma semilla + misma entrada = misma secuencia

# Body tracking: dónde corre la red neuronal del esqueleto
#   "cpu" | "directml" | "cuda"   (el sistema final usa "cuda": python main.py cuda)
MODO_BODY_TRACKER = ARGS[0] if len(ARGS) > 0 else "cpu"

# Modelo de la red del esqueleto (2º argumento):  python main.py cuda lite
#   "default" = más preciso | "lite" = ~2x más rápido y ~5% menos preciso (según el changelog de Microsoft v1.1.0)
MODELO_TRACKER = ARGS[1] if len(ARGS) > 1 else "default"
if MODELO_TRACKER not in ("default", "lite"):
    raise ValueError('El 2º argumento debe ser "default" o "lite"')
RUTAS_MODELO_LITE = [   # dónde busca el archivo del modelo lite (usa el primero que exista)
    r"C:\Program Files\Azure Kinect Body Tracking SDK\sdk\windows-desktop\amd64\release\bin\dnn_model_2_0_lite_op11.onnx",
    r"C:\Program Files\Azure Kinect Body Tracking SDK\tools\dnn_model_2_0_lite_op11.onnx",
]

# Fusión temporal (RF03 / HU0009) y disponibilidad de articulaciones (HU0007)
VENTANA_FUSION_MS = 16.0         # tolerancia del emparejado cuerpo-manos (TI: ±16 ms)
N_JOINTS = 32                    # articulaciones del esqueleto de Azure Kinect

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
    index.html los resta de Date.now() para obtener la latencia captura -> sonido."""
    return (_T0_PARED + (time.perf_counter() - _T0_PERF)) * 1000.0


# =====================================================================
# Azure Kinect
# =====================================================================
pykinect.initialize_libraries(track_body=True)

device_config = pykinect.default_configuration
device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_720P
device_config.color_format = pykinect.K4A_IMAGE_FORMAT_COLOR_BGRA32 if COLOR_BGRA32 else pykinect.K4A_IMAGE_FORMAT_COLOR_MJPG
device_config.depth_mode = pykinect.K4A_DEPTH_MODE_NFOV_UNBINNED
device_config.camera_fps = pykinect.K4A_FRAMES_PER_SECOND_30
device_config.wired_sync_mode = pykinect.K4A_WIRED_SYNC_MODE_STANDALONE

device = pykinect.start_device(config=device_config)

# pykinect usa esta configuración global al crear el tracker; aquí elegimos CPU/GPU
from pykinect_azure.k4abt import _k4abtTypes as k4abt_types
from pykinect_azure.k4a import _k4a          # para leer el timestamp del sistema de cada imagen (cola de cámara)
MODOS_TRACKER = {
    "cpu": k4abt_types.K4ABT_TRACKER_PROCESSING_MODE_CPU,
    "directml": k4abt_types.K4ABT_TRACKER_PROCESSING_MODE_GPU_DIRECTML,
    "cuda": k4abt_types.K4ABT_TRACKER_PROCESSING_MODE_GPU_CUDA,
}
k4abt_types.k4abt_tracker_default_configuration.processing_mode = MODOS_TRACKER[MODO_BODY_TRACKER]
modelo_en_uso = "default"
if MODELO_TRACKER == "lite":
    _cfg = k4abt_types.k4abt_tracker_default_configuration
    _ruta_lite = next((r for r in RUTAS_MODELO_LITE if os.path.isfile(r)), None)
    if _ruta_lite is None:
        print("[tracker] AVISO: no encontré dnn_model_2_0_lite_op11.onnx en RUTAS_MODELO_LITE; uso el modelo default")
    elif "model_path" not in [campo for campo, _ in _cfg._fields_]:
        print("[tracker] AVISO: esta versión de pykinect_azure no permite elegir modelo; uso el modelo default")
    else:
        _cfg.model_path = _ruta_lite.encode("utf-8")
        modelo_en_uso = "lite"
body_tracker = pykinect.start_body_tracker()
print(f"Body tracker en modo: {MODO_BODY_TRACKER} | modelo: {modelo_en_uso}")

# Articulaciones usadas por el mapeo de extremidades
J_PELVIS = pykinect.K4ABT_JOINT_PELVIS
J_MUNECAS = (pykinect.K4ABT_JOINT_WRIST_LEFT, pykinect.K4ABT_JOINT_WRIST_RIGHT)
J_TOBILLOS = (pykinect.K4ABT_JOINT_ANKLE_LEFT, pykinect.K4ABT_JOINT_ANKLE_RIGHT)
J_EXTREMIDADES = J_MUNECAS + J_TOBILLOS            # las 4 extremidades
J_BRAZOS = {                                         # (cadera, hombro, codo) de cada lado: ángulo del hombro
    "izq": (pykinect.K4ABT_JOINT_HIP_LEFT, pykinect.K4ABT_JOINT_SHOULDER_LEFT, pykinect.K4ABT_JOINT_ELBOW_LEFT),
    "der": (pykinect.K4ABT_JOINT_HIP_RIGHT, pykinect.K4ABT_JOINT_SHOULDER_RIGHT, pykinect.K4ABT_JOINT_ELBOW_RIGHT),
}
J_RODILLAS = {                                       # (cadera, rodilla, tobillo) de cada pierna
    "izq": (pykinect.K4ABT_JOINT_HIP_LEFT, pykinect.K4ABT_JOINT_KNEE_LEFT, pykinect.K4ABT_JOINT_ANKLE_LEFT),
    "der": (pykinect.K4ABT_JOINT_HIP_RIGHT, pykinect.K4ABT_JOINT_KNEE_RIGHT, pykinect.K4ABT_JOINT_ANKLE_RIGHT),
}
J_ANGULOS = {                                        # los 8 ángulos "candidatos" que se guardan en el CSV
    "hombro_izq": J_BRAZOS["izq"], "hombro_der": J_BRAZOS["der"],
    "codo_izq": (pykinect.K4ABT_JOINT_SHOULDER_LEFT, pykinect.K4ABT_JOINT_ELBOW_LEFT, pykinect.K4ABT_JOINT_WRIST_LEFT),
    "codo_der": (pykinect.K4ABT_JOINT_SHOULDER_RIGHT, pykinect.K4ABT_JOINT_ELBOW_RIGHT, pykinect.K4ABT_JOINT_WRIST_RIGHT),
    "cadera_izq": (pykinect.K4ABT_JOINT_SHOULDER_LEFT, pykinect.K4ABT_JOINT_HIP_LEFT, pykinect.K4ABT_JOINT_KNEE_LEFT),
    "cadera_der": (pykinect.K4ABT_JOINT_SHOULDER_RIGHT, pykinect.K4ABT_JOINT_HIP_RIGHT, pykinect.K4ABT_JOINT_KNEE_RIGHT),
    "rodilla_izq": J_RODILLAS["izq"],
    "rodilla_der": J_RODILLAS["der"],
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


ARTICULACIONES_MANO = {
    "izq": pykinect.K4ABT_JOINT_HAND_LEFT,
    "der": pykinect.K4ABT_JOINT_HAND_RIGHT,
}
ARTICULACIONES_MUNECA_CODO = {       # (muñeca, codo) de cada lado: sirven de respaldo cuando la mano es NONE
    "izq": (pykinect.K4ABT_JOINT_WRIST_LEFT, pykinect.K4ABT_JOINT_ELBOW_LEFT),
    "der": (pykinect.K4ABT_JOINT_WRIST_RIGHT, pykinect.K4ABT_JOINT_ELBOW_RIGHT),
}

# =====================================================================
# Estado entre frames
# =====================================================================
zona_actual = ZONA_INICIAL
contador_estable = 0      # histéresis en frames de zona.py (solo si REGISTRO_POR_ANGULO=False)
candidata_zona = None     # cambio 5: zona candidata que se está sosteniendo (None = la candidata es la zona actual)
tiempo_candidata = 0.0    # cambio 5 (D-010): segundos continuos dentro de candidata_zona (zona.zona_desde_registro)
nota_actual, octava_actual = NOTA_INICIAL, OCTAVA_INICIAL
nota_id = 0          # contador de notas nuevas: el HTML toca una nota cada vez que cambia
t_prox_tick = 0.0    # instante (perf_counter) en que toca el SIGUIENTE tick; se fija al sortear la nota anterior
lat_tick_ms = None   # RNF02: retraso entre el "tick" programado y el sorteo de la nota

# Cada ejecución guarda su propio log en la carpeta "sesiones" (no se sobrescriben)
CARPETA_SESIONES = "sesiones"
os.makedirs(CARPETA_SESIONES, exist_ok=True)
ruta_log = os.path.join(CARPETA_SESIONES, f"sesion_{datetime.now():%Y%m%d_%H%M%S}_{VERSION_MAIN}_{MODO_BODY_TRACKER}-{modelo_en_uso}.csv")

log_file = open(ruta_log, "w", newline="")
log_writer = csv.writer(log_file)
# Las 10 primeras columnas conservan el orden anterior (grafico.py sigue funcionando)
log_writer.writerow(["timestamp", "zona", "lambda", "acc_media", "nota", "octava", "apertura",
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
                     "edad_izq_ms", "edad_der_ms"])
log_file.flush()
# Los reportes [PERF]/[PERF-LINEA]/[CAMARA]/[FUSION]/[ROI] se guardan también en un .txt con el mismo nombre que el CSV,
# porque la consola se pierde (Start-Transcript de PowerShell no graba la salida de python)
ruta_perf = ruta_log[:-4] + "_perf.txt"
perf_file = open(ruta_perf, "w", encoding="utf-8")
perf_file.write(f"# {VERSION_MAIN} | tracker={MODO_BODY_TRACKER} modelo={modelo_en_uso} | color={'BGRA32' if COLOR_BGRA32 else 'MJPG'} | ventana={'si' if MOSTRAR_VENTANA else 'no'} | decodif={'hilo' if DECODIFICAR_EN_HILO_MANOS else 'ciclo'} | switchinterval={sys.getswitchinterval() * 1000:g}ms | manos={'hilo' if USAR_HILO_MANOS else 'no'} | conf_rodilla_tempo={CONF_MIN_RODILLA_TEMPO} | semilla={SEMILLA} | commit={COMMIT_GIT} | inicio={datetime.now():%Y-%m-%d %H:%M:%S}\n")
print(f"Versión de main.py: {VERSION_MAIN} | commit {COMMIT_GIT} | semilla {SEMILLA}")
print(f"Guardando la sesión en: {ruta_log}")
print(f"Guardando los reportes [PERF] en: {ruta_perf}")
if not MOSTRAR_VENTANA:
    print("Sin ventana de OpenCV (D-012; --con-ventana para depurar): para terminar, Ctrl+C en esta consola")

# Latencias del navegador: index.html las devuelve por el WebSocket cada 0.5 s y aquí se guardan con el mismo
# nombre que el CSV de sesión y el mismo formato que el botón "Descargar latencias" (ya no hace falta descargar).
ruta_latencias = ruta_log[:-4] + "_latencias.csv"
lat_file, lat_writer = None, None
ESPERA_ULTIMAS_LATENCIAS_S = 1.0   # al cerrar: tiempo para recibir el último lote (el navegador envía cada 0.5 s)


def guardar_latencias(mensaje):
    """Recibe un mensaje del navegador (str JSON). Si es {"tipo": "latencias", "filas": [...]}, escribe las filas
    en ruta_latencias (cabecera igual a la del CSV descargable) y hace flush. La llama servidor.manejar_cliente
    en los puntos `await` del ciclo. Variables: lat_file/lat_writer (se abren al primer mensaje: si no hay
    navegador, no se crea el archivo)."""
    global lat_file, lat_writer
    datos = json.loads(mensaje)
    if not isinstance(datos, dict) or datos.get("tipo") != "latencias":
        return
    if lat_file is None:
        lat_file = open(ruta_latencias, "w", newline="")
        lat_writer = csv.writer(lat_file)
        lat_writer.writerow(["t_epoch_ms", "tipo", "latencia_ms", "transporte_ms", "output_latency_ms", "base_latency_ms",
                             "latencia_llegada_ms"])   # D-009: latencia_ms + lag_cam_ms (columna nueva, al final)
        print(f"Guardando las latencias del navegador en: {ruta_latencias}")
    lat_writer.writerows(datos["filas"])
    lat_file.flush()


servidor.al_recibir = guardar_latencias

# ---------- Medición de rendimiento ----------
ETAPAS = ("cap_update", "cap_imgs", "tracker", "manos", "mapeo", "salida", "dibujo")
acum = dict.fromkeys(ETAPAS, 0.0)
perf = {"n": 0, "t": time.perf_counter()}
REPORTE_CADA = 60  # ciclos entre reportes
lags_cam = []      # lag_cam_ms de cada ciclo desde el último reporte (lo llena bucle_kinect)
descartes = []     # frames descartados por ciclo desde el último reporte
aviso_lag = {"mostrado": False}
# Cronómetros por LÍNEA (perf/ciclo-30hz): llamadas sueltas que hoy quedan dentro de una etapa agregada.
# to_numpy está dentro de cap_imgs; print dentro de salida; imshow y waitKey dentro de dibujo.
LINEAS = ("to_numpy", "print", "imshow", "waitKey") + (("copia_jpeg",) if DECODIFICAR_EN_HILO_MANOS else ())   # copia_jpeg: dentro de cap_imgs
# HU0007-2 (07/11, diagnóstico solo para el log): confianza de las articulaciones de pierna por ventana de reporte.
# No cambia el CSV ni el mapeo. conf_piernas[nombre] = [n NONE, n LOW, n MEDIUM, n HIGH]; rodillas_conf2 = ciclos con
# 2 / 1 / 0 rodillas con confianza >= MEDIUM (lo que vería el tempo si exigiera MEDIUM en las rodillas).
J_PIERNAS = {"cad_i": pykinect.K4ABT_JOINT_HIP_LEFT, "rod_i": pykinect.K4ABT_JOINT_KNEE_LEFT,
             "tob_i": pykinect.K4ABT_JOINT_ANKLE_LEFT, "pie_i": pykinect.K4ABT_JOINT_FOOT_LEFT,
             "cad_d": pykinect.K4ABT_JOINT_HIP_RIGHT, "rod_d": pykinect.K4ABT_JOINT_KNEE_RIGHT,
             "tob_d": pykinect.K4ABT_JOINT_ANKLE_RIGHT, "pie_d": pykinect.K4ABT_JOINT_FOOT_RIGHT}
conf_piernas = {k: [0, 0, 0, 0] for k in J_PIERNAS}
rodillas_conf2 = [0, 0, 0]   # [ciclos con 2, con 1, con 0 rodillas >= MEDIUM]


def anotar_conf_piernas(skeleton):
    """Cuenta el nivel de confianza (0 NONE, 1 LOW = posición inferida/predicha, 2 MEDIUM) de cada articulación de
    pierna en este ciclo. La llama bucle_kinect en cada ciclo con cuerpo; reportar() escribe [PIERNAS] y reinicia."""
    J = skeleton.joints
    for k, i in J_PIERNAS.items():
        conf_piernas[k][min(int(J[i].confidence_level), 3)] += 1
    n2 = sum(int(J[J_PIERNAS[k]].confidence_level) >= 2 for k in ("rod_i", "rod_d"))
    rodillas_conf2[2 - n2] += 1


acum_linea = dict.fromkeys(LINEAS, 0.0)   # segundos acumulados por línea desde el último reporte
n_linea = dict.fromkeys(LINEAS, 0)        # llamadas por línea desde el último reporte


def _reportar_linea(texto):
    """Imprime una línea de reporte en consola y la añade a perf_file (sin flush: lo hace reportar al final).
    La usa solo reportar(). Variable: `perf_file` (abierto junto al CSV de sesión)."""
    print(texto)
    perf_file.write(texto + "\n")


def reportar():
    """Imprime ciclos/s y milisegundos promedio por etapa cada REPORTE_CADA ciclos.
    Usa los acumuladores `acum` (que llena bucle_kinect) y el contador `perf`; luego los reinicia.
    Además pide a hilo_manos cuánto tardó cada trabajo de manos (ese tiempo ya NO está en `manos`)."""
    ahora = time.perf_counter()
    dur, n = ahora - perf["t"], perf["n"]
    etapas = " | ".join(f"{e}={acum[e] / n * 1000:.0f}ms" for e in ETAPAS)
    ms_hilo, n_hilo = hilo_manos.estadisticas_y_reiniciar()
    _reportar_linea(f"[FUSION] {fusion.resumen_y_reiniciar()}")
    _reportar_linea(f"[ROI] aciertos de MediaPipe por origen del recuadro -> {hilo_manos.estadisticas_roi_y_reiniciar()}")
    _reportar_linea(f"[PERF] {n / dur:.1f} ciclos/s | ciclo={dur / n * 1000:.0f}ms | {etapas} "
          f"| hilo_manos={ms_hilo:.0f}ms ({n_hilo / dur:.1f} trab/s"
          f"{f', {n_hilo / dur / hilo_manos.n_hilos:.1f} por hilo' if hilo_manos.n_hilos > 1 else ''})"
          f"{f' | decod_hilo={hilo_manos._ms_decod:.2f}ms/trabajo' if DECODIFICAR_EN_HILO_MANOS else ''}")
    _reportar_linea("[PERF-LINEA] " + " | ".join(
        f"{l}={acum_linea[l] / n_linea[l] * 1000:.2f}ms/llamada ({acum_linea[l] / n * 1000:.2f}ms/ciclo, {n_linea[l]} llamadas)"
        if n_linea[l] else f"{l}=sin llamadas" for l in LINEAS))
    if lags_cam:
        _reportar_linea(f"[CAMARA] espera del frame desde que llegó al PC hasta Python: media={np.mean(lags_cam):.1f}ms "
              f"| p95={np.percentile(lags_cam, 95):.1f}ms | max={max(lags_cam):.1f}ms (n={len(lags_cam)}) "
              f"| frames descartados/ciclo={np.mean(descartes) if descartes else 0:.2f}")
    else:
        _reportar_linea("[CAMARA] sin dato de timestamp del sistema")
    n_p = sum(rodillas_conf2)
    if n_p:   # % de ciclos con cuerpo por nivel N/L/M (NONE/LOW/MEDIUM); HIGH no lo usa el SDK
        _reportar_linea("[PIERNAS] " + " | ".join(
            f"{k} N{100 * c[0] / n_p:.0f} L{100 * c[1] / n_p:.0f} M{100 * (c[2] + c[3]) / n_p:.0f}" for k, c in conf_piernas.items())
            + f" | rodillas>=MEDIUM 2:{100 * rodillas_conf2[0] / n_p:.0f}% 1:{100 * rodillas_conf2[1] / n_p:.0f}% 0:{100 * rodillas_conf2[2] / n_p:.0f}%")
    for c in conf_piernas.values():
        c[:] = [0, 0, 0, 0]
    rodillas_conf2[:] = [0, 0, 0]
    perf_file.flush()
    lags_cam.clear()
    descartes.clear()
    for e in ETAPAS:
        acum[e] = 0.0
    for l in LINEAS:
        acum_linea[l], n_linea[l] = 0.0, 0
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
        return self.normalizar(valor, t)

    def normalizar(self, valor, t):
        """Lleva `valor` a [0,1] con las muestras ya guardadas, SIN añadirlo (cambio 6: TimbrePorManos lo usa en los
        ciclos sin dato nuevo de manos, para no recalibrar con valores mantenidos). actualizar() termina aquí."""
        if not self.muestras or t - self.muestras[0][0] < NORM_CALENTAMIENTO_S:
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
            if all(J[i].confidence_level >= CONF_MIN_RODILLA_TEMPO for i in (cad, rod, tob)):   # 1 = igual que _ok
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


class RegistroPorAngulo:
    """Tono (REGISTRO) a partir de ÁNGULOS ARTICULARES (RF05): usa el ángulo de elevación de cada
    hombro (cadera-hombro-codo: ~0° con el brazo colgando, ~90° horizontal, ~180° arriba).
    Cada brazo se normaliza por separado con su propio NormalizadorAdaptativo (RF04: así quien
    tiene menos rango, o es zurdo, igual recorre todo el registro) y luego se promedian los brazos
    vigentes (D-002). Además calcula los 8 ángulos candidatos (hombro, codo,
    cadera, rodilla; izq/der) SOLO para guardarlos en el CSV y poder analizarlos después.
    Relación con el resto: reutiliza angulo_articulacion y MapeoExtremidades._pos; su salida
    `registro01` la convierte en zona zona_desde_registro, y calcular_octava (muestreo.py) la
    vuelve octava. Se llama una vez por ciclo desde bucle_kinect, igual que `mapeo`.
    Variables importantes: `reg01` (0-1 por brazo), `t_ok` (cuándo fue fiable cada brazo; sirve para
    el HOLD), `registro01` (resultado combinado). Si ningún brazo es fiable, conserva el último valor."""

    def __init__(self):
        self.norm = {l: NormalizadorAdaptativo(RANGO_MIN_ANGULO_BRAZO) for l in J_BRAZOS}
        self.ang_suav = {l: None for l in J_BRAZOS}
        self.reg01 = {l: None for l in J_BRAZOS}
        self.t_ok = {l: -1e9 for l in J_BRAZOS}
        self.registro01 = 0.5

    def actualizar(self, skeleton, t):
        """Actualiza ambos brazos y devuelve {registro01, reg01_izq, reg01_der, conf_izq, conf_der}."""
        J = skeleton.joints
        for lado, (cad, hom, cod) in J_BRAZOS.items():
            if all(J[i].confidence_level >= CONF_MIN_ANGULO_BRAZO for i in (cad, hom, cod)):
                ang = angulo_articulacion(MapeoExtremidades._pos(J, cad), MapeoExtremidades._pos(J, hom),
                                          MapeoExtremidades._pos(J, cod))
                prev = self.ang_suav[lado]
                self.ang_suav[lado] = ang if prev is None else EMA_ANGULO_BRAZO * ang + (1 - EMA_ANGULO_BRAZO) * prev
                self.reg01[lado] = self.norm[lado].actualizar(self.ang_suav[lado], t)
                self.t_ok[lado] = t
        vigentes = [v for l, v in self.reg01.items() if v is not None and t - self.t_ok[l] <= HOLD_ANGULO_S]
        if vigentes:
            self.registro01 = float(np.mean(vigentes))
        return {
            "registro01": self.registro01,
            "reg01_izq": self.reg01["izq"], "reg01_der": self.reg01["der"],
            "conf_izq": int(J[J_BRAZOS["izq"][1]].confidence_level),
            "conf_der": int(J[J_BRAZOS["der"][1]].confidence_level),
        }

    def angulos_candidatos(self, skeleton):
        """Los 8 ángulos (grados) de hombros, codos, caderas y rodillas, o None si alguna de sus
        articulaciones tiene menos confianza que CONF_MIN_ARTICULACION. Solo para el CSV."""
        J = skeleton.joints
        salida = {}
        for nombre, (a, b, c) in J_ANGULOS.items():
            if all(J[i].confidence_level >= CONF_MIN_ARTICULACION for i in (a, b, c)):
                salida[nombre] = angulo_articulacion(MapeoExtremidades._pos(J, a), MapeoExtremidades._pos(J, b),
                                                     MapeoExtremidades._pos(J, c))
            else:
                salida[nombre] = None
        return salida


registro = RegistroPorAngulo()


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


def construir_objetivos(skeleton, body2d):
    """Decide, para cada mano, DÓNDE centrar el recuadro de MediaPipe en este frame.
    1) Si la Kinect da la articulación de la MANO con confianza suficiente, se usa ella (origen "mano").
    2) Si no (confianza NONE, ~53% de los frames en las pruebas) y RESPALDO_MUNECA=True, se usa la
       MUÑECA desplazada hacia afuera siguiendo codo->muñeca FACTOR_RESPALDO_MUNECA veces el
       antebrazo, en píxeles (origen "muneca"). Muñeca y codo estuvieron disponibles el 100% del tiempo.
    3) Si tampoco hay muñeca y codo fiables, esa mano queda en None (no se intenta, no se inventa).
    Relación: la llama bucle_kinect justo antes de HiloManos.enviar; el hilo usa el origen para sus
    estadísticas [ROI]. Devuelve {"izq": ((x, y), z_mm, origen) | None, "der": ...}."""
    objetivos = {}
    for lado, id_mano in ARTICULACIONES_MANO.items():
        art = skeleton.joints[id_mano]
        if art.confidence_level >= CONF_MIN_ARTICULACION:
            objetivos[lado] = (body2d.joints[id_mano].get_coordinates(), art.position.xyz.z, "mano")
            continue
        objetivos[lado] = None
        if RESPALDO_MUNECA:
            id_mun, id_cod = ARTICULACIONES_MUNECA_CODO[lado]
            mun, cod = skeleton.joints[id_mun], skeleton.joints[id_cod]
            if mun.confidence_level >= CONF_MIN_ARTICULACION and cod.confidence_level >= CONF_MIN_ARTICULACION:
                xm, ym = body2d.joints[id_mun].get_coordinates()
                xc, yc = body2d.joints[id_cod].get_coordinates()
                centro = (int(round(xm + FACTOR_RESPALDO_MUNECA * (xm - xc))),
                          int(round(ym + FACTOR_RESPALDO_MUNECA * (ym - yc))))
                objetivos[lado] = (centro, mun.position.xyz.z, "muneca")
    return objetivos


class HiloManos:
    """Corre MediaPipe de las manos en HILOS APARTE, para que el ciclo principal
    (captura -> esqueleto -> mapeo -> envío) no espere por ellas.
    Analogía: el cocinero (ciclo principal) no se queda mirando el horno; deja la masa
    (el frame) en la repisa y sigue cocinando. Con HILO_POR_MANO=True hay DOS ayudantes,
    uno por mano, que hornean a la vez; con False hay uno solo (como en v6).
    Relación con el resto: bucle_kinect le ofrece un frame con `enviar` solo si `libre()`;
    cada hilo usa detectar_mano + calcular_apertura y guarda su resultado; bucle_kinect lo lee
    con `estado()` cada ciclo (los datos de la Kinect NO cruzan el hilo: bucle_kinect extrae antes
    centro 2D y profundidad de cada mano).
    Variables importantes: `trabajadores` (lista; cada uno con su `cola` de 1 hueco, su bandera
    `ocupado` y sus `lados`), `lock` (protege los resultados compartidos), `ult_apertura/ult_t_ap/ult_landmarks`
    (último dato por mano), `recuadros_lado` (último recuadro por mano).
    Cambio 6: ya NO normaliza la apertura (con ALTERNAR_MANOS cada trabajo trae una sola mano y apertura01 saltaba
    entre las dos); la normaliza bucle_kinect con TimbrePorManos sobre el promedio de las manos vigentes.
    Cada detector de MediaPipe SOLO lo toca el hilo que lo creó (MediaPipe no es seguro entre hilos)."""

    def __init__(self):
        self.lock = threading.Lock()
        self.ult_apertura = {"izq": None, "der": None}
        self.ult_t_ap = {"izq": -1e9, "der": -1e9}      # perf_counter del frame que la midió
        self.ult_landmarks = {"izq": None, "der": None}  # solo para dibujar
        self.recuadros_lado = {"izq": None, "der": None} # (recuadro, acertó) de cada mano, solo para dibujar
        self._t_trabajo, self._n_trabajos = 0.0, 0
        self._t_decod = 0.0                              # DECODIFICAR_EN_HILO_MANOS: segundos decodificando (dentro de _t_trabajo)
        self._ms_decod = 0.0                             # ms de decodificación por trabajo del último reporte
        self.roi = {"mano": [0, 0], "muneca": [0, 0]}   # origen del recuadro -> [intentos, aciertos de MediaPipe]
        grupos = [("izq",), ("der",)] if HILO_POR_MANO else [("izq", "der")]
        if not USAR_HILO_MANOS:         # sin trabajadores: libre() es False (nunca se envía) y estado() queda "sin mano"
            grupos = []
        self.trabajadores = []
        for lados in grupos:
            self.trabajadores.append({"lados": lados, "cola": queue.Queue(maxsize=1), "ocupado": False, "ciclo": 0})
        self.n_hilos = len(self.trabajadores)
        for t in self.trabajadores:
            t["hilo"] = threading.Thread(target=self._correr, args=(t,), name="hilo-manos-" + "-".join(t["lados"]), daemon=True)
            t["hilo"].start()

    def libre(self):
        """True si algún hilo puede recibir un frame nuevo (no tiene uno esperando ni procesando).
        bucle_kinect lo consulta ANTES de convertir el color, para no gastar tiempo en vano."""
        return any(not t["ocupado"] for t in self.trabajadores)

    def enviar(self, color_rgb, objetivos, t_frame):
        """Deja el frame a cada hilo que esté libre. `objetivos` = {"izq": ((x, y), z_mm, origen) o None, "der": ...}
        (origen = "mano" o "muneca", ver construir_objetivos); None = esa mano no es fiable en este frame.
        `t_frame` = perf_counter de la captura. El mismo `color_rgb` lo leen los hilos SIN modificarlo.
        Devuelve True si al menos un hilo lo recibió."""
        enviado = False
        for t in self.trabajadores:
            if t["ocupado"]:
                continue
            t["ocupado"] = True                 # se marca aquí (no en el hilo) para evitar carreras
            try:
                t["cola"].put_nowait((color_rgb, objetivos, t_frame))
                enviado = True
            except queue.Full:                  # no debería pasar (ocupado=False => cola vacía); si pasa, no se bloquea
                t["ocupado"] = False
        return enviado

    def estado(self):
        """Copia consistente de los resultados para leer desde bucle_kinect.
        Devuelve (ult_apertura, ult_t_ap, ult_landmarks, recuadros)."""
        with self.lock:
            return (dict(self.ult_apertura), dict(self.ult_t_ap), dict(self.ult_landmarks),
                    [r for r in self.recuadros_lado.values() if r is not None])

    def estadisticas_y_reiniciar(self):
        """(ms promedio por trabajo, número de trabajos) desde el último reporte. Lo usa reportar().
        Con HILO_POR_MANO cada trabajo es UNA mano, así que `n` cuenta las dos manos juntas."""
        with self.lock:
            n, t = self._n_trabajos, self._t_trabajo
            self._n_trabajos, self._t_trabajo = 0, 0.0
            self._ms_decod = self._t_decod / n * 1000.0 if n else 0.0   # lo lee reportar justo después
            self._t_decod = 0.0
        return (t / n * 1000.0 if n else 0.0), n

    def estadisticas_roi_y_reiniciar(self):
        """Texto con el % de veces que MediaPipe encontró la mano según de dónde salió el recuadro
        ("mano" = articulación de la Kinect, "muneca" = respaldo). Sirve para medir si el respaldo
        funciona. Lo usa reportar(); reinicia los contadores."""
        with self.lock:
            r = {k: tuple(v) for k, v in self.roi.items()}
            for v in self.roi.values():
                v[0] = v[1] = 0
        return " | ".join(f"{k}: {100.0 * a / n:.0f}% de {n}" if n else f"{k}: sin intentos"
                          for k, (n, a) in r.items())

    def detener(self):
        """Pide a los hilos que terminen (cierran sus detectores) y espera. Se llama al apagar."""
        for t in self.trabajadores:
            try:
                t["cola"].put_nowait(None)
            except queue.Full:                  # hay un frame esperando: se descarta y se pone la señal
                try:
                    t["cola"].get_nowait()
                except queue.Empty:
                    pass
                t["cola"].put_nowait(None)
        for t in self.trabajadores:
            t["hilo"].join(timeout=5)

    def _correr(self, t):
        """Bucle de UN hilo: espera un frame, lo procesa y repite hasta recibir None.
        Crea aquí los detectores de sus manos (los usa solo este hilo) y los cierra al terminar."""
        detectores = {lado: crear_detector() for lado in t["lados"]}
        try:
            while True:
                trabajo = t["cola"].get()
                if trabajo is None:
                    break
                t0 = time.perf_counter()
                try:
                    self._procesar(trabajo, detectores, t)
                except Exception as e:          # un fallo de una mano no debe matar el hilo
                    print(f"[manos] error en el hilo {t['lados']}: {e!r}")
                with self.lock:
                    self._t_trabajo += time.perf_counter() - t0
                    self._n_trabajos += 1
                t["ocupado"] = False
        finally:
            for d in detectores.values():
                d.close()

    def _procesar(self, trabajo, detectores, t):
        """Un trabajo: detecta la(s) mano(s) de este hilo, mide la apertura y publica el resultado.
        Un hilo con una sola mano la hace siempre; un hilo con las dos hace las dos (o una por trabajo,
        alternando, si ALTERNAR_MANOS=True)."""
        color_rgb, objetivos, t_frame = trabajo
        if DECODIFICAR_EN_HILO_MANOS:   # llegaron los bytes del JPEG: mismas llamadas que to_numpy + bucle_kinect, aquí
            t0 = time.perf_counter()
            bgr = cv2.imdecode(color_rgb, -1)
            if bgr is None:             # JPEG dañado: se salta este frame
                return
            color_rgb = cv2.cvtColor(bgr, cv2.COLOR_BGRA2RGB)
            with self.lock:
                self._t_decod += time.perf_counter() - t0
        if len(t["lados"]) == 1 or not ALTERNAR_MANOS:
            lados = list(t["lados"])
        else:
            lados = [t["lados"][t["ciclo"] % 2]]
        t["ciclo"] += 1

        nuevos, recuadros = {}, {}
        for lado in lados:
            obj = objetivos.get(lado)
            nuevos[lado] = None
            recuadros[lado] = None
            if obj is None:
                continue
            centro, z_mm, origen = obj
            landmarks, recuadro = detectar_mano(detectores[lado], color_rgb, centro, z_mm)
            with self.lock:
                self.roi[origen][0] += 1
                self.roi[origen][1] += int(landmarks is not None)
            if recuadro is not None:
                recuadros[lado] = (recuadro, landmarks is not None)
            if landmarks is not None:
                ap = calcular_apertura(landmarks)
                nuevos[lado] = (ap, landmarks)

        with self.lock:
            for lado, r in nuevos.items():
                if r is None:
                    self.ult_landmarks[lado] = None
                else:
                    self.ult_apertura[lado], self.ult_landmarks[lado] = r
                    self.ult_t_ap[lado] = t_frame
                self.recuadros_lado[lado] = recuadros[lado]


hilo_manos = HiloManos()
timbre = TimbrePorManos(NormalizadorAdaptativo(RANGO_MIN_APERTURA))   # cambio 6: apertura01 desde el promedio de las manos


class FusionTemporal:
    """Fusión cuerpo-manos por TIMESTAMP del frame de origen (RF03 / HU0009).
    Cada resultado de manos lleva el instante (perf_counter) del frame que lo originó; aquí se
    empareja con el frame del cuerpo más cercano en el tiempo y se comprueba que la diferencia
    sea <= VENTANA_FUSION_MS. Como las manos salen del MISMO frame de la Kinect, la diferencia
    de pareja es ~0 ms; lo que sí se mide aparte es la EDAD del dato de manos cuando se usa
    (el hilo tarda 27-56 ms), porque eso es lo que afecta a la latencia del timbre.
    Relación con el resto: bucle_kinect llama registrar_cuerpo(t_ciclo) en cada ciclo con cuerpo
    y actualizar(...) con los tiempos que entrega hilo_manos.estado(); reportar() imprime el
    resumen. Si no hay dato de manos vigente, desync_manos=True (HU0009-2): el audio conserva el
    último valor y el CSV lo registra.
    Variables: `t_cuerpo` (tiempos de los últimos frames con cuerpo), `ultimo_t_manos` (frame del
    último resultado de manos ya emparejado), `pares_ok/pares_desync` (conteo), `edades` (ms)."""

    def __init__(self):
        self.t_cuerpo = collections.deque(maxlen=60)
        self.ultimo_t_manos = None
        self.par_dt_ms = None
        self.pares_ok, self.pares_desync = 0, 0
        self.edades = []
        self.n_ciclos, self.n_vigente = 0, 0

    def registrar_cuerpo(self, t_frame):
        """Anota el instante de un frame en el que SÍ hubo cuerpo."""
        self.t_cuerpo.append(t_frame)

    def actualizar(self, t_ciclo, ult_t_ap, hay_dato):
        """Se llama una vez por ciclo. `ult_t_ap` = {lado: instante del frame medido} del hilo de
        manos; `hay_dato` = hay apertura vigente (dentro del HOLD). Devuelve
        {edad_manos_ms, par_dt_ms, desync_manos}."""
        t_manos = max(ult_t_ap.values())
        if t_manos > -1e8 and (self.ultimo_t_manos is None or t_manos > self.ultimo_t_manos):
            self.ultimo_t_manos = t_manos                 # llegó un resultado nuevo: se empareja
            cerca = min((abs(tb - t_manos) for tb in self.t_cuerpo), default=None)
            self.par_dt_ms = None if cerca is None else cerca * 1000.0
            if self.par_dt_ms is not None and self.par_dt_ms <= VENTANA_FUSION_MS:
                self.pares_ok += 1
            else:
                self.pares_desync += 1
        # la edad solo cuenta cuando hay dato vigente: con la mano perdida seguiría creciendo sin sentido
        edad = (t_ciclo - self.ultimo_t_manos) * 1000.0 if (hay_dato and self.ultimo_t_manos is not None) else None
        self.n_ciclos += 1
        self.n_vigente += int(hay_dato)
        if edad is not None:
            self.edades.append(edad)
        return {"edad_manos_ms": edad, "par_dt_ms": self.par_dt_ms, "desync_manos": not hay_dato}

    def resumen_y_reiniciar(self):
        """Texto para la consola: % de pares sincronizados y edad del dato de manos (media, p95,
        % de ciclos con edad <= VENTANA_FUSION_MS). Reinicia la ventana de edades."""
        total = self.pares_ok + self.pares_desync
        pares = f"{100.0 * self.pares_ok / total:.0f}% pares en ±{VENTANA_FUSION_MS:.0f}ms (n={total})" if total else "sin pares aún"
        if self.edades:
            e = np.array(self.edades)
            edad = (f"edad manos media={e.mean():.0f}ms p95={np.percentile(e, 95):.0f}ms "
                    f"| edad<={VENTANA_FUSION_MS:.0f}ms: {100.0 * (e <= VENTANA_FUSION_MS).mean():.0f}% de ciclos")
        else:
            edad = "sin dato de manos vigente"
        vig = f"dato vigente en {100.0 * self.n_vigente / self.n_ciclos:.0f}% de ciclos" if self.n_ciclos else ""
        self.edades, self.n_ciclos, self.n_vigente = [], 0, 0
        return f"{pares} | {vig} | {edad}"


fusion = FusionTemporal()


def estado_articulaciones(skeleton):
    """HU0007-2: cuántas de las N_JOINTS articulaciones son fiables en este frame y cuáles NO están
    disponibles (confianza < CONF_MIN_ARTICULACION). Devuelve (n_ok, [índices no disponibles]).
    Se usa en bucle_kinect para el CSV y el payload; sirve para medir el % de frames con 32 joints."""
    J = skeleton.joints
    no_disp = [i for i in range(N_JOINTS) if J[i].confidence_level < CONF_MIN_ARTICULACION]
    return N_JOINTS - len(no_disp), no_disp


# =====================================================================
# Bucle principal
# =====================================================================
def obtener_capture_reciente():
    """Pide a la Kinect el capture más reciente y descarta los viejos que esperan en la cola del SDK.
    Relación: reemplaza a device.update() en bucle_kinect; lo que devuelve lo consume leer_frame y el tracker.
    Problema que resuelve: si el ciclo (38 ms) es más lento que la cámara (33 ms), los frames se acumulan en la cola
    del SDK y cada uno llega ~220 ms tarde (medido con lag_cam_ms).
    Variables: n_desc = frames viejos descartados en esta llamada. device.update() espera hasta tener un capture; después se
    piden más con timeout 0 (sin esperar) y cada uno que exista reemplaza al anterior. Se llama directo a la DLL porque
    pykinect cierra el programa (sys.exit) si el SDK devuelve 'timeout'."""
    capture = device.update()
    n_desc = 0
    if DESCARTAR_COLA_CAMARA:
        while n_desc < MAX_DESCARTE_POR_CICLO:
            handle = _k4a.k4a_capture_t()
            resultado = _k4a.k4a_device_get_capture(device.handle(), handle, 0)   # 0 = no esperar
            if resultado != _k4a.K4A_WAIT_RESULT_SUCCEEDED:                       # cola vacía (o error): nos quedamos con el actual
                break
            capture.release_handle()                                             # libera el frame viejo...
            capture._handle = handle                                             # ...y usa el más nuevo
            n_desc += 1
    return capture, n_desc


def leer_frame(capture, t_upd):
    """Extrae del capture la imagen de color (numpy) y mide la espera en la cola de la cámara.
    Relación: la llama bucle_kinect justo después de device.update(); devuelve lo que usan el tracker (ya lo tiene
    dentro del capture), el hilo de manos (color) y el CSV (lag_cam_ms).
    Variables: t_upd = perf_counter() del instante en que Python recibió el frame.
    lag_cam_ms = t_upd - timestamp del sistema de la imagen (QueryPerformanceCounter del SDK en Windows, el mismo reloj
    que time.perf_counter()) = tiempo que el frame esperó en la cola del SDK. None si el dato no es válido.
    Nota: to_numpy() ya devuelve una copia propia, por eso NO se hace otra .copy()."""
    img_color = capture.get_color_image_object()
    if LEER_PROFUNDIDAD_NUMPY:
        ok_depth, _ = capture.get_depth_image()
    else:
        ok_depth = bool(capture.get_depth_image_object().is_valid())    # solo comprueba que haya profundidad
    t0 = time.perf_counter()
    if DECODIFICAR_EN_HILO_MANOS:
        # Solo se copian los bytes del JPEG (el buffer del SDK se libera con el capture); los decodifica HiloManos
        ok_color = img_color.is_valid()
        color_image = (np.ctypeslib.as_array(img_color.buffer_pointer, shape=(img_color.get_size(),)).copy()
                       if ok_color else None)
        linea = "copia_jpeg"
    else:
        ok_color, color_image = img_color.to_numpy()  # MJPG: incluye cv2.imdecode (BGR, 3 canales) | BGRA32: solo copia (BGRA, 4 canales)
        linea = "to_numpy"
    acum_linea[linea] += time.perf_counter() - t0
    n_linea[linea] += 1
    lag_cam_ms = None
    if ok_color:
        try:
            ts_ns = _k4a.k4a_image_get_system_timestamp_nsec(img_color.handle())
            if ts_ns:                                    # 0 = sin dato
                lag = t_upd * 1000.0 - ts_ns / 1e6
                if -50.0 < lag < 5000.0:                 # fuera de rango = los relojes no coinciden: se descarta
                    lag_cam_ms = lag
        except Exception as e:                           # nunca debe tumbar el programa
            if not aviso_lag["mostrado"]:
                print(f"AVISO: no se pudo leer el timestamp del sistema ({e}); lag_cam_ms quedará vacío")
                aviso_lag["mostrado"] = True
    return (bool(ok_depth) and bool(ok_color)), color_image, lag_cam_ms


async def bucle_kinect():
    """Un ciclo: captura -> esqueleto -> manos -> mapeo -> nota -> ENVÍO -> dibujo.
    Une todo: usa calcular_zona (registro), detectar_mano+calcular_apertura (timbre),
    mapeo.actualizar (tempo, intensidad, lambda) y elegir_siguiente_nota (melodía);
    envía el resultado por WebSocket a index.html. El envío va ANTES de dibujar para
    no sumar el tiempo de dibujo a la latencia. t_cap_ms marca cuándo llegó el frame."""
    global zona_actual, contador_estable, candidata_zona, tiempo_candidata, nota_actual, octava_actual, nota_id, t_prox_tick, lat_tick_ms
    t_prev_cuerpo = None                          # último ciclo con cuerpo, para detectar ausencias
    ciclo_global = 0
    apertura01 = 0.5
    origen_roi = {"izq": None, "der": None}      # de dónde salió el último recuadro enviado (para el CSV)
    display = None

    while True:
        t = time.perf_counter()
        capture, n_descartados = obtener_capture_reciente()
        descartes.append(n_descartados)
        t_cap_ms = ahora_ms()                     # <- instante en que Python recibe el frame
        t_upd = time.perf_counter()
        acum["cap_update"] += t_upd - t           # espera/lectura del frame de la cámara

        ok_frame, color_image, lag_cam_ms = leer_frame(capture, t_upd)
        if not ok_frame:
            await asyncio.sleep(0)
            continue
        if lag_cam_ms is not None:
            lags_cam.append(lag_cam_ms)

        t_ciclo = time.perf_counter()
        acum["cap_imgs"] += t_ciclo - t_upd       # lectura de la imagen de color (y comprobación de profundidad)

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
            n_joints_ok, joints_no_disp = estado_articulaciones(skeleton)   # HU0007-2
            anotar_conf_piernas(skeleton)                                    # HU0007-2: solo para [PIERNAS] en _perf.txt
            fusion.registrar_cuerpo(t_ciclo)                                 # HU0009: frame con cuerpo

            # ---- Registro (tono): ángulo de los hombros (o altura de la muñeca si REGISTRO_POR_ANGULO=False) ----
            t = time.perf_counter()
            reg = registro.actualizar(skeleton, t_ciclo)         # siempre se calcula (queda en el CSV)
            cand = registro.angulos_candidatos(skeleton)
            if REGISTRO_POR_ANGULO:
                # dt = duración de este ciclo, desde el ciclo con cuerpo anterior (t_prev_cuerpo se actualiza más abajo)
                dt_zona = 0.0 if t_prev_cuerpo is None else t_ciclo - t_prev_cuerpo
                zona_actual, candidata_zona, tiempo_candidata = zona_desde_registro(
                    reg["registro01"], zona_actual, candidata_zona, tiempo_candidata, dt_zona,
                    UMBRAL_REG_GRAVE, UMBRAL_REG_AGUDO, UMBRAL_ESTABILIDAD_ZONA_S, DT_MAX_ZONA_S,
                )
            else:
                muneca = skeleton.joints[pykinect.K4ABT_JOINT_WRIST_LEFT].position.xyz
                hombro = skeleton.joints[pykinect.K4ABT_JOINT_SHOULDER_LEFT].position.xyz
                cadera = skeleton.joints[pykinect.K4ABT_JOINT_HIP_LEFT].position.xyz
                zona_actual, contador_estable = calcular_zona(
                    muneca.y, hombro.y, cadera.y, zona_actual, contador_estable
                )
            acum["mapeo"] += time.perf_counter() - t

            # ---- Manos (timbre): se ofrecen al hilo; aquí NO se espera su resultado ----
            t = time.perf_counter()
            if hilo_manos.libre():
                # con DECODIFICAR_EN_HILO_MANOS color_image son los bytes del JPEG: el hilo decodifica y convierte
                color_rgb = color_image if DECODIFICAR_EN_HILO_MANOS else cv2.cvtColor(color_image, cv2.COLOR_BGRA2RGB)
                body2d = body_frame.get_body2d(0, pykinect.K4A_CALIBRATION_TYPE_COLOR)
                objetivos = construir_objetivos(skeleton, body2d)
                origen_roi = {l: (o[2] if o else None) for l, o in objetivos.items()}
                hilo_manos.enviar(color_rgb, objetivos, t_ciclo)

            # Resultado más reciente del hilo. Si una mano se pierde, se mantiene su última
            # apertura HOLD_APERTURA_S segundos (el tiempo se compara con el del frame medido).
            ult_apertura, ult_t_ap, ult_landmarks, recuadros_hoy = hilo_manos.estado()
            # Cambio 1 (HU0008-2, P-006): sin mano vigente NO se inventa un valor: apertura_val y apertura01 = None
            # (CSV vacío; el navegador lleva el timbre al valor neutro)
            efectivas, apertura_val = apertura_vigente(ult_apertura, ult_t_ap, t_ciclo, HOLD_APERTURA_S)
            # Cambio 6: apertura01 = promedio de las manos vigentes, normalizado; recalibra solo con datos nuevos
            apertura01 = timbre.actualizar(apertura_val, max((ult_t_ap[l] for l in efectivas), default=None), t_ciclo)
            fus = fusion.actualizar(t_ciclo, ult_t_ap, bool(efectivas))      # HU0009: edad y desfase
            edades = edades_por_mano_ms(ult_t_ap, t_ciclo)                   # P-015: solo para el CSV
            manos_detectadas = [h for h in ult_landmarks.values() if h is not None]
            acum["manos"] += time.perf_counter() - t

            # ---- Extremidades: tempo, intensidad, lambda ----
            t = time.perf_counter()
            m = mapeo.actualizar(skeleton, t_ciclo)
            lam = m["lam"]

            intervalo_s = 1.0 / (NOTAS_POR_SEG_MIN + m["tempo"] * (NOTAS_POR_SEG_MAX - NOTAS_POR_SEG_MIN))
            lat_tick_ms = None                       # solo tiene valor en el ciclo en que hay nota nueva
            lam_sorteo = None                        # cambio 3: λ exacto del sorteo, solo en el ciclo con nota nueva
            reanclado = False
            # Si el cuerpo estuvo ausente >0.5 s, el reloj se re-ancla: eso es ausencia, no latencia
            if t_prev_cuerpo is not None and t_ciclo - t_prev_cuerpo > 0.5:
                t_prox_tick = t_ciclo
                reanclado = True
            t_prev_cuerpo = t_ciclo
            if t_ciclo >= t_prox_tick:
                es_primera = (nota_id == 0)          # la primera nota no tiene tick previo
                lam_sorteo = lam
                nota_actual = elegir_siguiente_nota(nota_actual, lam, lam_min=LAMBDA_MIN)   # cambio 4: λ mínimo = determinístico
                octava_actual = calcular_octava(zona_actual)
                nota_id += 1
                if not es_primera and not reanclado:
                    lat_tick_ms = (time.perf_counter() - t_prox_tick) * 1000.0   # RNF02
                # el siguiente tick se programa AHORA con el intervalo actual (sin deriva);
                # si vamos más atrasados que un intervalo, se re-ancla para no acumular
                t_prox_tick = (t_prox_tick if (t_ciclo - t_prox_tick) < intervalo_s else t_ciclo) + intervalo_s
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
                "registro": round(reg["registro01"], 3),
                "zona": zona_actual,
                "apertura": None if apertura_val is None else round(apertura_val, 3),
                "apertura01": None if apertura01 is None else round(apertura01, 3),
                "apertura_izq": None if ap_izq is None else round(ap_izq, 3),
                "apertura_der": None if ap_der is None else round(ap_der, 3),
                "joints_ok": n_joints_ok,
                "edad_manos_ms": None if fus["edad_manos_ms"] is None else round(fus["edad_manos_ms"], 1),
                "desync_manos": fus["desync_manos"],
                "manos": len(manos_detectadas),
                "t_cap_ms": round(t_cap_ms, 1),
                "t_env_ms": round(ahora_ms(), 1),
                "lat_tick_ms": None if lat_tick_ms is None else round(lat_tick_ms, 1),
                # D-009: el navegador suma lag_cam_ms a su latencia_ms -> latencia_llegada_ms (RNF01/US23)
                "lag_cam_ms": None if lag_cam_ms is None else round(lag_cam_ms, 1),
            })

            ap_txt = "---" if apertura_val is None else f"{apertura_val:.3f}"
            t0 = time.perf_counter()
            print(f"Nota: {nota_actual}{octava_actual} | zona={zona_actual:<6} | lambda={lam:.2f} "
                  f"| acc={m['acc_mm']:.0f}mm/s2 | tempo={m['tempo']:.2f} | inten={m['intensidad']:.2f} "
                  f"| reg={reg['registro01']:.2f} | apertura={ap_txt} | manos={len(manos_detectadas)}")
            acum_linea["print"] += time.perf_counter() - t0
            n_linea["print"] += 1
            log_writer.writerow([
                time.time(), zona_actual, round(lam, 3), round(m["acc_mm"], 1),
                nota_actual, octava_actual,
                _fmt(apertura_val), _fmt(ap_izq), _fmt(ap_der),
                len(manos_detectadas),
                round(m["tempo"], 3), round(m["intensidad"], 3), _fmt(apertura01),
                round(m["vel_rodilla"], 1), round(m["amplitud_mm"], 1), round(t_cap_ms, 1),
                "" if lat_tick_ms is None else round(lat_tick_ms, 1),
                _fmt(cand["hombro_izq"]), _fmt(cand["hombro_der"]), _fmt(cand["codo_izq"]), _fmt(cand["codo_der"]),
                _fmt(cand["cadera_izq"]), _fmt(cand["cadera_der"]), _fmt(cand["rodilla_izq"]), _fmt(cand["rodilla_der"]),
                reg["conf_izq"], reg["conf_der"],
                _fmt(reg["reg01_izq"]), _fmt(reg["reg01_der"]), round(reg["registro01"], 3),
                n_joints_ok, ";".join(map(str, joints_no_disp)), _fmt(fus["edad_manos_ms"]),
                _fmt(fus["par_dt_ms"]), int(fus["desync_manos"]),
                origen_roi["izq"] or "", origen_roi["der"] or "",
                _fmt(lag_cam_ms), n_descartados,
                nota_id, "" if lam_sorteo is None else repr(float(lam_sorteo)), SEMILLA, VERSION_MAIN, COMMIT_GIT,
                _fmt(edades["izq"]), _fmt(edades["der"]),   # P-015
            ])
            log_file.flush()
            acum["salida"] += time.perf_counter() - t

        # ---- Dibujo (después del envío, y solo 1 de cada DIBUJAR_CADA ciclos; nunca si MOSTRAR_VENTANA=False) ----
        if MOSTRAR_VENTANA and dibujar_ahora:
            t = time.perf_counter()
            # con DECODIFICAR_EN_HILO_MANOS + ventana (solo para depurar) este ciclo decodifica su propia copia
            display = cv2.cvtColor(cv2.imdecode(color_image, -1) if DECODIFICAR_EN_HILO_MANOS else color_image,
                                   cv2.COLOR_BGRA2BGR)
            if num_bodies > 0:
                if MOSTRAR_RECUADROS:
                    for rec, ok in recuadros_hoy:
                        cv2.rectangle(display, rec[:2], rec[2:], (0, 255, 0) if ok else (0, 0, 255), 2)
                display = body_frame.draw_bodies(display, pykinect.K4A_CALIBRATION_TYPE_COLOR)
                for h in manos_detectadas:
                    mp_drawing.draw_landmarks(display, h, mp_hands.HAND_CONNECTIONS)
            t0 = time.perf_counter()
            cv2.imshow('Kinect', display)
            t1 = time.perf_counter()
            tecla = cv2.waitKey(1) & 0xFF
            t2 = time.perf_counter()
            acum_linea["imshow"] += t1 - t0
            acum_linea["waitKey"] += t2 - t1
            n_linea["imshow"] += 1
            n_linea["waitKey"] += 1
            acum["dibujo"] += time.perf_counter() - t
            if tecla == ord("q"):
                break

        perf["n"] += 1
        if perf["n"] >= REPORTE_CADA:
            reportar()
        await asyncio.sleep(0)  # cede el control para que el servidor pueda enviar mensajes


async def main():
    """Abre el servidor WebSocket y corre bucle_kinect hasta `q`, Ctrl+C o un error.
    Al terminar, si hay navegador conectado, espera ESPERA_ULTIMAS_LATENCIAS_S con el servidor abierto: el
    navegador manda sus latencias cada 0.5 s y sin esta espera el último lote no llegaría a _latencias.csv."""
    server = await websockets.serve(manejar_cliente, sock=SOCK_WS, ping_interval=None)   # cambio 7b: socket abierto al arrancar
    try:
        await bucle_kinect()
    finally:
        if servidor.clientes_conectados:
            print("Recibiendo las últimas latencias del navegador…")
            await asyncio.sleep(ESPERA_ULTIMAS_LATENCIAS_S)
        server.close()


def soltar_objetos_kinect(dev, tracker):
    """Suelta, con la Kinect y el tracker todavía vivos, los objetos de pykinect que si no se soltarían al salir de
    Python, cuando ya no existen (access violation en k4abt_frame_release y k4a_capture_release, 02/11 y 04/11).
    Relación: la llama el finally del final, después de hilo_manos.detener() y antes de tracker.destroy() y dev.close().
    Variables: `type(dev).capture` = el ÚNICO Capture de pykinect, atributo de CLASE de Device que device.update() reutiliza
    (obtener_capture_reciente le cambia el handle); `tracker.frame` = el único Frame que reutiliza el tracker.
    Cada uno lleva una Transformation (camera_transform / transformation). reset()/destroy() dejan el handle en None,
    así su __del__ ya no llama a la DLL. dev o tracker pueden ser None si el programa falló antes de crearlos."""
    gc.collect()    # finaliza ya lo que retiene la excepción de cancelación de bucle_kinect (capture local, imágenes)
    frame = getattr(tracker, "frame", None)
    if frame is not None:
        frame.reset()
        if getattr(frame, "transformation", None) is not None:
            frame.transformation.destroy()
    cap = getattr(type(dev), "capture", None) if dev is not None else None
    if cap is not None:
        cap.reset()
        if getattr(cap, "camera_transform", None) is not None:
            cap.camera_transform.destroy()
        type(dev).capture = None
    gc.collect()


try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Detenido con Ctrl+C")
finally:
    # Se ejecuta siempre (q, Ctrl+C o error) para liberar la Kinect
    hilo_manos.detener()      # cierra los detectores de MediaPipe dentro de su propio hilo
    # HU0026-1: body_tracker o device pueden no existir si el programa falló antes de crearlos
    _bt, _dev = globals().get("body_tracker"), globals().get("device")
    soltar_objetos_kinect(_dev, _bt)   # último Frame y Capture ANTES de destruir el tracker y cerrar la Kinect
    if _bt is not None:
        _bt.destroy()
    if _dev is not None:
        _dev.close()
    cv2.destroyAllWindows()
    log_file.close()
    perf_file.close()
    if lat_file is not None:
        lat_file.close()
    print("Kinect cerrada correctamente")
    print(f"Sesión guardada en {ruta_log}. Para ver los gráficos: python3.11 grafico.py")