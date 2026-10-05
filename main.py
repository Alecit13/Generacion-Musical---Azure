import asyncio
import cv2
import numpy as np
import mediapipe as mp
import pykinect_azure as pykinect
import websockets
import csv
import time
from zona import calcular_zona
from fluidez import calcular_fluidez
from muestreo import elegir_siguiente_nota, calcular_octava
from manos import calcular_apertura
from servidor import manejar_cliente, enviar_a_todos

# ---------- Azure Kinect ----------
pykinect.initialize_libraries(track_body=True)

device_config = pykinect.default_configuration
device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_720P
device_config.depth_mode = pykinect.K4A_DEPTH_MODE_NFOV_UNBINNED
device_config.camera_fps = pykinect.K4A_FRAMES_PER_SECOND_30

device = pykinect.start_device(config=device_config)
body_tracker = pykinect.start_body_tracker()

# ---------- MediaPipe Hands ----------
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5)

# ---------- Estado entre frames ----------
zona_actual = "medio"
contador_estable = 0
historial_muneca = []
nota_actual, octava_actual = "Do", 4
TICKS_POR_NOTA = 8
contador_frames = 0

log_file = open("sesion_file.csv", "w", newline="")
log_writer = csv.writer(log_file)
log_writer.writerow(["timestamp", "zona", "lambda", "nota", "octava", "apertura"])
log_file.flush()


async def bucle_kinect():
    global zona_actual, contador_estable, nota_actual, octava_actual, contador_frames

    while True:
        capture = device.update()
        body_frame = body_tracker.update()

        ok_color, color_image = capture.get_color_image()
        if not ok_color:
            await asyncio.sleep(0)
            continue

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
            if len(historial_muneca) > 15:
                historial_muneca.pop(0)
            lam = calcular_fluidez(historial_muneca)

            contador_frames += 1
            if contador_frames >= TICKS_POR_NOTA:
                nota_actual = elegir_siguiente_nota(nota_actual, lam)
                octava_actual = calcular_octava(zona_actual)
                contador_frames = 0

            # Manos: MediaPipe lee la imagen de color limpia
            color_rgb = cv2.cvtColor(color_image, cv2.COLOR_BGRA2RGB)
            hands_result = hands.process(color_rgb)
            apertura_val = 0.0
            if hands_result.multi_hand_landmarks:
                aperturas = [calcular_apertura(h) for h in hands_result.multi_hand_landmarks]
                apertura_val = sum(aperturas) / len(aperturas)

            # Superposición: esqueleto proyectado a la cámara de color + manos
            display = body_frame.draw_bodies(display, pykinect.K4A_CALIBRATION_TYPE_COLOR)
            if hands_result.multi_hand_landmarks:
                for h in hands_result.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(display, h, mp_hands.HAND_CONNECTIONS)

            await enviar_a_todos({
                "nota": nota_actual,
                "octava": octava_actual,
                "lam": round(lam, 2),
                "apertura": round(apertura_val, 3),
            })

            print(f"Nota: {nota_actual}{octava_actual} | zona={zona_actual:<6} | lambda={lam:.2f} | apertura={apertura_val:.3f}")
            log_writer.writerow([time.time(), zona_actual, round(lam, 3), nota_actual, octava_actual, round(apertura_val, 3)])
            log_file.flush()  # guarda cada fila de inmediato

        cv2.imshow('Kinect', display)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        await asyncio.sleep(0)  # cede el control para que el servidor pueda enviar mensajes

    device.close()
    cv2.destroyAllWindows()
    log_file.close()


async def main():
    server = await websockets.serve(manejar_cliente, "localhost", 8765)
    await bucle_kinect()
    server.close()

asyncio.run(main())