UMBRAL_ESTABILIDAD = 6  # frames que debe sostenerse una zona candidata antes de confirmarla (histéresis)

def _zona_candidata(muneca_y, hombro_y, cadera_y):
    # En coordenadas de imagen, y menor = más arriba. Por eso las comparaciones parecen "al revés".
    if muneca_y > cadera_y:
        return "grave"
    elif muneca_y > hombro_y:
        return "medio"
    else:
        return "agudo"

def calcular_zona(muneca_y, hombro_y, cadera_y, zona_anterior, contador_estable):
    candidata = _zona_candidata(muneca_y, hombro_y, cadera_y)
    if candidata == zona_anterior:
        return zona_anterior, 0
    contador_estable += 1
    if contador_estable >= UMBRAL_ESTABILIDAD:
        return candidata, 0  # se confirma el cambio de zona
    return zona_anterior, contador_estable  # todavía no se sostiene lo suficiente