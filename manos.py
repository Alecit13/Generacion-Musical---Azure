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