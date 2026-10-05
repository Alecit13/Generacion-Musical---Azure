import faulthandler
faulthandler.enable(all_threads=True)  # si el proceso muere por un fallo nativo, muestra dónde

import asyncio
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.framework.formats import landmark_pb2
import pykinect_azure as pykinect
import websockets
import csv
import os
import time
from datetime import datetime
from zona import calcular_zona
from fluidez import calcular_fluidez
from muestreo import elegir_siguiente_nota, calcular_octava
from manos import calcular_apertura
from servidor import manejar_cliente, enviar_a_todos

# =====================================================================
# PARÁMETROS (todo lo ajustable está aquí arriba)
# =====================================================================
# Servidor
HOST_WS = "localhost"
PUERTO_WS = 8765

# Música / movimiento
TICKS_POR_NOTA = 8          # cada cuántos frames con cuerpo se elige una nota nueva
VENTANA_FLUIDEZ = 15        # cuántas posiciones de muñeca se usan para calcular lambda
NOTA_INICIAL, OCTAVA_INICIAL = "Do", 4
ZONA_INICIAL = "medio"

# Detección de manos (MediaPipe sobre un recorte alrededor de cada mano)
CONFIANZA_DETECCION_MANO = 0.5   # bájalo a 0.3-0.4 si aún se pierden manos
COMPLEJIDAD_MODELO = 1           # 0 = rápido, 1 = más preciso
FOCAL_COLOR_PX = 610             # focal aprox. de la cámara de color a 720p
TAMANO_MANO_M = 0.35             # tamaño del recuadro en metros (mano + margen)
ROI_MIN_PX, ROI_MAX_PX = 96, 400 # límites del recuadro en píxeles
CONF_MIN_ARTICULACION = 1        # 0=NONE, 1=LOW, 2=MEDIUM (confianza de la Kinect)
MOSTRAR_RECUADROS = False        # True = dibuja el recuadro de cada mano (útil para depurar)

# Body tracking: dónde corre la red neuronal del esqueleto
#   "cpu"      -> más lento pero estable (úsalo para comprobar si el cierre viene de la GPU)
#   "directml" -> GPU con cualquier tarjeta (es lo que se usaba antes por defecto)
#   "cuda"     -> GPU NVIDIA con CUDA (más rápido, requiere los DLL de CUDA del SDK)
MODO_BODY_TRACKER = "cpu"

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
historial_muneca = []
nota_actual, octava_actual = NOTA_INICIAL, OCTAVA_INICIAL
contador_frames = 0

# Cada ejecución guarda su propio log en la carpeta "sesiones" (no se sobrescriben)
CARPETA_SESIONES = "sesiones"
os.makedirs(CARPETA_SESIONES, exist_ok=True)
ruta_log = os.path.join(CARPETA_SESIONES, f"sesion_{datetime.now():%Y%m%d_%H%M%S}.csv")

log_file = open(ruta_log, "w", newline="")
log_writer = csv.writer(log_file)
log_writer.writerow(["timestamp", "zona", "lambda", "nota", "octava", "apertura",
                     "apertura_izq", "apertura_der", "manos"])
log_file.flush()
print(f"Guardando la sesión en: {ruta_log}")


def _fmt(valor):
    """Número redondeado, o vacío si esa mano no se detectó (así no cuenta como 0 en los gráficos)."""
    return "" if valor is None else round(valor, 3)


def detectar_mano(detector, color_rgb, centro, profundidad_mm):
    """Recorta un cuadrado alrededor de la mano (según la Kinect) y corre MediaPipe ahí.
    Devuelve los landmarks en coordenadas de la imagen completa, o None."""
    alto, ancho = color_rgb.shape[:2]
    cx, cy = centro
    if not (0 <= cx < ancho and 0 <= cy < alto):
        return None, None

    # Más lejos -> mano más pequeña en la imagen -> recuadro más pequeño
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

    # Pasar los landmarks del recorte a coordenadas normalizadas de la imagen completa
    w_rec, h_rec = x1 - x0, y1 - y0
    landmarks = landmark_pb2.NormalizedLandmarkList()
    for p in resultado.multi_hand_landmarks[0].landmark:
        landmarks.landmark.add(
            x=(x0 + p.x * w_rec) / ancho,
            y=(y0 + p.y * h_rec) / alto,
            z=p.z * w_rec / ancho,
        )
    return landmarks, recuadro


async def bucle_kinect():
    global zona_actual, contador_estable, nota_actual, octava_actual, contador_frames

    while True:
        capture = device.update()

        # A veces la Kinect entrega una captura sin imagen de profundidad (frame perdido).
        # Si se la pasamos así al body tracker, falla y cierra el programa: la saltamos.
        ok_depth, _ = capture.get_depth_image()
        ok_color, color_image = capture.get_color_image()
        if not ok_depth or not ok_color:
            await asyncio.sleep(0)
            continue

        # Copia propia de la imagen: el arreglo de pykinect apunta a memoria de la Kinect
        # que se libera con la siguiente captura; usarla después provoca cierres de golpe.
        color_image = color_image.copy()

        body_frame = body_tracker.update()

        # Copia de 3 canales solo para dibujar; color_image queda limpia para MediaPipe
        display = cv2.cvtColor(color_image, cv2.COLOR_BGRA2BGR)

        num_bodies = body_frame.get_num_bodies()
        if num_bodies > 0:
            skeleton = body_frame.get_body_skeleton(0)

            muneca = skeleton.joints[pykinect.K4ABT_JOINT_WRIST_LEFT].position.xyz
            hombro = skeleton.joints[pykinect.K4ABT_JOINT_SHOULDER_LEFT].position.xyz
            cadera = skeleton.joints[pykinect.K4ABT_JOINT_HIP_LEFT].position.xyz

            zona_actual, contador_estable = calcular_zona(
                muneca.y, hombro.y, cadera.y, zona_actual, contador_estable
            )

            historial_muneca.append((muneca.x, muneca.y))
            if len(historial_muneca) > VENTANA_FLUIDEZ:
                historial_muneca.pop(0)
            lam = calcular_fluidez(historial_muneca)

            contador_frames += 1
            if contador_frames >= TICKS_POR_NOTA:
                nota_actual = elegir_siguiente_nota(nota_actual, lam)
                octava_actual = calcular_octava(zona_actual)
                contador_frames = 0

            # ---- Manos: la Kinect dice dónde está cada mano, MediaPipe la analiza de cerca ----
            color_rgb = cv2.cvtColor(color_image, cv2.COLOR_BGRA2RGB)
            body2d = body_frame.get_body2d(0, pykinect.K4A_CALIBRATION_TYPE_COLOR)

            aperturas = {"izq": None, "der": None}
            manos_detectadas = []
            for lado, id_articulacion in ARTICULACIONES_MANO.items():
                articulacion = skeleton.joints[id_articulacion]
                if articulacion.confidence_level < CONF_MIN_ARTICULACION:
                    continue
                centro = body2d.joints[id_articulacion].get_coordinates()
                landmarks, recuadro = detectar_mano(
                    detectores[lado], color_rgb, centro, articulacion.position.xyz.z
                )
                if MOSTRAR_RECUADROS and recuadro is not None:
                    color_caja = (0, 255, 0) if landmarks is not None else (0, 0, 255)
                    cv2.rectangle(display, recuadro[:2], recuadro[2:], color_caja, 2)
                if landmarks is not None:
                    aperturas[lado] = calcular_apertura(landmarks)
                    manos_detectadas.append(landmarks)

            valores = [a for a in aperturas.values() if a is not None]
            apertura_val = sum(valores) / len(valores) if valores else 0.0
            ap_izq = aperturas["izq"] if aperturas["izq"] is not None else 0.0
            ap_der = aperturas["der"] if aperturas["der"] is not None else 0.0

            # Superposición: esqueleto proyectado a la cámara de color + manos
            display = body_frame.draw_bodies(display, pykinect.K4A_CALIBRATION_TYPE_COLOR)
            for h in manos_detectadas:
                mp_drawing.draw_landmarks(display, h, mp_hands.HAND_CONNECTIONS)

            await enviar_a_todos({
                "nota": nota_actual,
                "octava": octava_actual,
                "lam": round(lam, 2),
                "apertura": round(apertura_val, 3),
                "apertura_izq": round(ap_izq, 3),
                "apertura_der": round(ap_der, 3),
                "manos": len(manos_detectadas),
            })

            print(f"Nota: {nota_actual}{octava_actual} | zona={zona_actual:<6} | lambda={lam:.2f} "
                  f"| apertura={apertura_val:.3f} (izq={ap_izq:.3f}, der={ap_der:.3f}) "
                  f"| manos={len(manos_detectadas)}")
            log_writer.writerow([time.time(), zona_actual, round(lam, 3), nota_actual, octava_actual,
                                 _fmt(apertura_val if valores else None),
                                 _fmt(aperturas["izq"]), _fmt(aperturas["der"]),
                                 len(manos_detectadas)])
            log_file.flush()  # guarda cada fila de inmediato

        cv2.imshow('Kinect', display)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        await asyncio.sleep(0)  # cede el control para que el servidor pueda enviar mensajes


async def main():
    server = await websockets.serve(manejar_cliente, HOST_WS, PUERTO_WS)
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