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


if __name__ == "__main__":
    unittest.main(verbosity=2)
