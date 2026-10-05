import random

NOTAS = ["Do", "Re", "Mi", "Sol", "La"]

def _distancia_circular(i, j, n=5):
    d = abs(i - j)
    return min(d, n - d)

def construir_tabla_pesos():
    """Genera los pesos por distancia en la escala pentatónica: pasos cercanos
    más probables, repetir la misma nota, menos probable. Son valores
    ILUSTRATIVOS de partida — ajústalos escuchando, como dice el documento."""
    pesos_por_distancia = {0: 0.05, 1: 0.30, 2: 0.175}
    tabla = {}
    for i, nota_anterior in enumerate(NOTAS):
        fila = {}
        for j, nota_siguiente in enumerate(NOTAS):
            d = _distancia_circular(i, j)
            fila[nota_siguiente] = pesos_por_distancia[d]
        tabla[nota_anterior] = fila
    return tabla

TABLA_PESOS = construir_tabla_pesos()

def elegir_siguiente_nota(nota_anterior, lam, tabla_pesos=TABLA_PESOS):
    fila = tabla_pesos[nota_anterior]
    nota_moda = max(fila, key=fila.get)

    pesos_finales = {}
    for nota, peso_original in fila.items():
        peso_moda = 1.0 if nota == nota_moda else 0.0
        pesos_finales[nota] = lam * peso_original + (1 - lam) * peso_moda

    notas = list(pesos_finales.keys())
    pesos = list(pesos_finales.values())
    return random.choices(notas, weights=pesos, k=1)[0]

def calcular_octava(zona):
    mapa = {"grave": 3, "medio": 4, "agudo": 5}
    return mapa.get(zona, 4)