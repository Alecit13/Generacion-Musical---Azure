"""Pruebas unitarias SIN dispositivo (HU0025-1) de los cambios del 07/11/2026.
No importan main.py (enciende la Kinect al importarse): prueban las funciones puras de manos.py, muestreo.py y zona.py.
Uso:  python -m unittest pruebas_unitarias -v      (desde la carpeta del proyecto, con env_cv activo)"""
import unittest

from manos import apertura_vigente

HOLD = 0.5   # igual que HOLD_APERTURA_S de main.py


class PruebaAperturaVigente(unittest.TestCase):
    """Cambio 1 (HU0008-2, P-006): vencimiento de la apertura con reloj simulado."""

    def test_dato_reciente_vigente(self):
        ef, val = apertura_vigente({"izq": 0.10, "der": None}, {"izq": 0.0, "der": -1e9}, 0.49, HOLD)
        self.assertEqual(ef, {"izq": 0.10})
        self.assertAlmostEqual(val, 0.10)

    def test_dato_vencido_reporta_ausencia(self):
        ef, val = apertura_vigente({"izq": 0.10, "der": None}, {"izq": 0.0, "der": -1e9}, 0.51, HOLD)
        self.assertEqual(ef, {})
        self.assertIsNone(val)

    def test_limite_exacto_sigue_vigente(self):
        ef, _ = apertura_vigente({"izq": 0.10, "der": None}, {"izq": 0.0, "der": -1e9}, 0.5, HOLD)
        self.assertIn("izq", ef)

    def test_promedio_de_las_dos_manos(self):
        _, val = apertura_vigente({"izq": 0.04, "der": 0.20}, {"izq": 1.0, "der": 1.1}, 1.2, HOLD)
        self.assertAlmostEqual(val, 0.12)

    def test_una_mano_vence_y_queda_la_otra(self):
        ef, val = apertura_vigente({"izq": 0.04, "der": 0.20}, {"izq": 0.0, "der": 0.4}, 0.6, HOLD)
        self.assertEqual(ef, {"der": 0.20})
        self.assertAlmostEqual(val, 0.20)

    def test_sin_datos_nunca(self):
        ef, val = apertura_vigente({"izq": None, "der": None}, {"izq": -1e9, "der": -1e9}, 10.0, HOLD)
        self.assertEqual((ef, val), ({}, None))


class PruebaTopeRepeticiones(unittest.TestCase):
    """Cambio 2 (HU0019-2): nunca más de MAX_REPETICIONES notas iguales seguidas."""

    def _secuencia(self, lam, n, semilla):
        import random
        import muestreo
        random.seed(semilla)
        muestreo.reiniciar_estado()
        nota, notas = "Do", []
        for _ in range(n):
            nota = muestreo.elegir_siguiente_nota(nota, lam)
            notas.append(nota)
        return notas

    @staticmethod
    def _racha_max(notas):
        mejor = actual = 1
        for a, b in zip(notas, notas[1:]):
            actual = actual + 1 if a == b else 1
            mejor = max(mejor, actual)
        return mejor

    def test_tope_con_varios_lambda(self):
        import muestreo
        for lam in (1.0, 0.5, 0.05):
            notas = self._secuencia(lam, 100_000, semilla=7)
            self.assertLessEqual(self._racha_max(notas), muestreo.MAX_REPETICIONES, f"lam={lam}")

    def test_repetir_una_vez_sigue_posible(self):
        """El tope no prohíbe repetir: con λ = 1 la probabilidad de repetir (racha 1 -> 2) sigue siendo
        peso(0) / suma de la fila = 0.05 / 1.16 ≈ 0.043 en la escala mayor."""
        notas = self._secuencia(1.0, 200_000, semilla=11)
        rep = sum(1 for a, b in zip(notas, notas[1:]) if a == b)
        # tras una repetición la siguiente no puede repetir: P(repetir) ≈ p / (1 + p)
        p = 0.05 / 1.16
        self.assertAlmostEqual(rep / (len(notas) - 1), p / (1 + p), delta=0.003)


class PruebaSemilla(unittest.TestCase):
    """Cambio 3 (HU0021-1): misma semilla + misma secuencia de λ = misma secuencia de notas."""

    @staticmethod
    def _sortear(semilla, lams):
        import random
        import muestreo
        random.seed(semilla)          # lo mismo que hace main.py al arrancar
        muestreo.reiniciar_estado()
        nota, notas = "Do", []        # NOTA_INICIAL de main.py
        for lam in lams:
            nota = muestreo.elegir_siguiente_nota(nota, lam)
            notas.append(nota)
        return notas

    def _lams(self, n=2000):
        import random
        r = random.Random(99)         # generador aparte: no toca el estado global
        return [max(0.05, r.random()) for _ in range(n)]

    def test_misma_semilla_misma_secuencia(self):
        lams = self._lams()
        self.assertEqual(self._sortear(123, lams), self._sortear(123, lams))

    def test_otra_semilla_otra_secuencia(self):
        lams = self._lams()
        self.assertNotEqual(self._sortear(123, lams), self._sortear(124, lams))

    def test_lambda_redondeado_puede_cambiar_la_secuencia(self):
        """Condición (1) de Ale: con λ redondeado a 3 decimales (columna `lambda`) el re-sorteo puede diferir del real;
        por eso main.py guarda lam_sorteo exacto. Esta prueba documenta que la diferencia existe."""
        lams = self._lams(20000)
        exacta = self._sortear(5, lams)
        redondeada = self._sortear(5, [round(l, 3) for l in lams])
        self.assertNotEqual(exacta, redondeada)


if __name__ == "__main__":
    unittest.main(verbosity=2)
