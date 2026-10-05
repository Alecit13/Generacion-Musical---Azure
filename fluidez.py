import numpy as np

LIMITE_BRUSQUEDAD = 0.05  # ilustrativo — ajusta viendo los valores reales que imprime tu cámara

def calcular_fluidez(historial_posiciones):
    if len(historial_posiciones) < 3:
        return 1.0  # sin historial suficiente, asumimos fluido por defecto

    posiciones = np.array(historial_posiciones)
    velocidades = np.diff(posiciones, axis=0)
    aceleraciones = np.diff(velocidades, axis=0)
    aceleracion_promedio = np.mean(np.linalg.norm(aceleraciones, axis=1))

    lam = 1.0 - min(aceleracion_promedio / LIMITE_BRUSQUEDAD, 1.0)
    return max(lam, 0.05)  # nunca 0 absoluto, para que no se congele del todo