import random

# =====================================================================
# PARÁMETROS
# =====================================================================
ESCALAS = {
    "pentatonica": ["Do", "Re", "Mi", "Sol", "La"],
    "mayor": ["Do", "Re", "Mi", "Fa", "Sol", "La", "Si"],
}
ESCALA_ACTIVA = "mayor"   # cambia a "pentatonica" para volver a la escala original
NOTAS = ESCALAS[ESCALA_ACTIVA]

# Pesos por distancia (en pasos de la escala). Valores ILUSTRATIVOS de partida:
# pasos cercanos más probables, repetir la misma nota menos probable.
# Cada fila se normaliza para que sume 1, así funciona con cualquier escala.
PESOS_POR_DISTANCIA = {0: 0.05, 1: 0.30, 2: 0.175, 3: 0.08}
PESO_DISTANCIA_LEJANA = 0.04   # para distancias mayores a 3 (escalas más largas)

# Con fluidez baja la melodía sigue la "moda": un paso en la dirección actual
# (sube o baja por la escala). Esta es la probabilidad de cambiar de dirección.
PROB_CAMBIO_DIRECCION = 0.2

_direccion = 1  # +1 sube, -1 baja


def _distancia_circular(i, j, n):
    d = abs(i - j)
    return min(d, n - d)


def construir_tabla_pesos(notas=NOTAS):
    """Tabla de transición: para cada nota anterior, el peso de cada nota siguiente."""
    n = len(notas)
    tabla = {}
    for i, nota_anterior in enumerate(notas):
        fila = {}
        for j, nota_siguiente in enumerate(notas):
            d = _distancia_circular(i, j, n)
            fila[nota_siguiente] = PESOS_POR_DISTANCIA.get(d, PESO_DISTANCIA_LEJANA)
        total = sum(fila.values())
        tabla[nota_anterior] = {nota: peso / total for nota, peso in fila.items()}
    return tabla


TABLA_PESOS = construir_tabla_pesos()


def _nota_moda(nota_anterior, notas=NOTAS):
    """Nota más probable. Como hay empate entre el paso de arriba y el de abajo,
    se desempata con la dirección actual de la melodía (antes siempre ganaba
    la primera de la lista y la melodía rebotaba entre las mismas dos notas)."""
    global _direccion
    if random.random() < PROB_CAMBIO_DIRECCION:
        _direccion *= -1
    i = notas.index(nota_anterior)
    return notas[(i + _direccion) % len(notas)]


def elegir_siguiente_nota(nota_anterior, lam, tabla_pesos=TABLA_PESOS):
    # lambda debe estar entre 0 y 1; fuera de ese rango los pesos serían negativos
    lam = min(max(float(lam), 0.0), 1.0)

    if nota_anterior not in tabla_pesos:
        nota_anterior = NOTAS[0]

    fila = tabla_pesos[nota_anterior]
    nota_moda = _nota_moda(nota_anterior)

    # lam alto (movimiento fluido) -> más variedad; lam bajo -> sigue la moda
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