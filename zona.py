def zona_desde_registro(registro01, zona_anterior, pendiente, tiempo_s, dt_s,
                        umbral_grave=0.33, umbral_agudo=0.66, umbral_s=0.250, dt_max_s=0.1):
    """Cambio 5 (HU0015-2, D-010): convierte registro01 (0-1) en zona "grave" | "medio" | "agudo" con histéresis en
    tiempo. La zona cambia solo cuando registro01 lleva >= umbral_s segundos CONTINUOS dentro de la MISMA zona candidata.
    Antes contaba el tiempo fuera de la zona actual aunque la candidata cambiara (grave -> medio -> agudo), así que el paso
    por "medio" sumaba para "agudo" y un relámpago podía cambiar la zona.
    La cuenta empieza en 0 en la primera muestra dentro de la candidata y cada ciclo siguiente suma su duración dt_s, con
    tope dt_max_s (tras una ausencia del cuerpo, el hueco no cuenta como sostenido).
    Relación: la llama bucle_kinect (main.py) una vez por ciclo con cuerpo, con los umbrales de main.py; guarda
    `pendiente` y `tiempo_s` para el siguiente ciclo. Su salida la convierte calcular_octava (muestreo.py) en octava.
    Devuelve (zona, pendiente, tiempo_s); pendiente = None cuando la candidata es la zona actual."""
    if registro01 < umbral_grave:
        candidata = "grave"
    elif registro01 < umbral_agudo:
        candidata = "medio"
    else:
        candidata = "agudo"
    if candidata == zona_anterior:
        return zona_anterior, None, 0.0
    if candidata != pendiente:
        return zona_anterior, candidata, 0.0        # primera muestra dentro de esta candidata: la cuenta empieza aquí
    tiempo_s += min(dt_s, dt_max_s)
    if tiempo_s >= umbral_s:
        return candidata, None, 0.0
    return zona_anterior, pendiente, tiempo_s