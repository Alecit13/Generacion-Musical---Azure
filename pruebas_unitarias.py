"""Pruebas unitarias SIN dispositivo (HU0025-1) de los cambios del 07/11/2026.
No importan main.py (enciende la Kinect al importarse): prueban las funciones puras de manos.py, muestreo.py y zona.py.
Uso:  python -m unittest pruebas_unitarias -v      (desde la carpeta del proyecto, con env_cv activo)"""
import unittest

from manos import apertura_vigente, edades_por_mano_ms

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


class PruebaEdadesPorMano(unittest.TestCase):
    """P-015 (HU0008-1): edad del último dato de cada mano, con reloj simulado."""

    def test_edades_y_mano_sin_dato(self):
        self.assertEqual(edades_por_mano_ms({"izq": 1.000, "der": -1e9}, 1.0655), {"izq": 65.5, "der": None})

    def test_la_edad_baja_con_un_dato_nuevo(self):
        antes = edades_por_mano_ms({"izq": 1.0, "der": 1.0}, 1.1)["izq"]
        despues = edades_por_mano_ms({"izq": 1.1, "der": 1.0}, 1.133)["izq"]
        self.assertLess(despues, antes)


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


class PruebaVariabilidadMinima(unittest.TestCase):
    """Cambio 4 (HU0021-2): variabilidad mínima (λ = LAMBDA_MIN = 0.05) = secuencia determinística."""

    def test_lambda_minimo_igual_con_cualquier_semilla(self):
        secs = [PruebaSemilla._sortear(sem, [0.05] * 500) for sem in (1, 2, 123, 99999)]
        self.assertTrue(all(s == secs[0] for s in secs[1:]))

    def test_lambda_minimo_es_escala_con_rebote(self):
        sec = PruebaSemilla._sortear(7, [0.05] * 14)
        self.assertEqual(sec, ["Re", "Mi", "Fa", "Sol", "La", "Si", "La", "Sol", "Fa", "Mi", "Re", "Do", "Re", "Mi"])

    def test_por_encima_del_minimo_vuelve_a_variar(self):
        self.assertNotEqual(PruebaSemilla._sortear(1, [0.3] * 500), PruebaSemilla._sortear(2, [0.3] * 500))


class _NormalizadorDePrueba:
    """Sustituto de NormalizadorAdaptativo (vive en main.py, que enciende la Kinect): identidad, y cuenta las llamadas."""

    def __init__(self):
        self.n_actualizar, self.n_normalizar = 0, 0

    def actualizar(self, valor, t):
        self.n_actualizar += 1
        return valor

    def normalizar(self, valor, t):
        self.n_normalizar += 1
        return valor


class PruebaTimbrePorManos(unittest.TestCase):
    """Cambio 6 (HU0017-1): sin saltos al alternar manos; recalibra solo con datos nuevos; None sin manos."""

    @staticmethod
    def _simular(segundos=3.0, dt_ciclo=1 / 30, dt_trabajo=0.035, ap={"izq": 0.02, "der": 0.05}):
        """Reproduce la 2d(i): el hilo alterna manos, un trabajo cada dt_trabajo; el ciclo lee cada dt_ciclo."""
        from manos import TimbrePorManos
        norm = _NormalizadorDePrueba()
        timbre = TimbrePorManos(norm)
        ult_ap, ult_t = {"izq": None, "der": None}, {"izq": -1e9, "der": -1e9}
        t, t_trab, lado, salida = 0.0, 0.0, "izq", []
        while t < segundos:
            while t_trab <= t:                      # trabajos terminados hasta este ciclo
                ult_ap[lado], ult_t[lado] = ap[lado], t_trab
                lado = "der" if lado == "izq" else "izq"
                t_trab += dt_trabajo
            ef, val = apertura_vigente(ult_ap, ult_t, t, HOLD)
            salida.append(timbre.actualizar(val, max((ult_t[l] for l in ef), default=None), t))
            t += dt_ciclo
        return salida, norm

    def test_sin_saltos_con_una_abierta_y_otra_cerrada(self):
        salida, _ = self._simular()
        estable = salida[3:]                        # desde que las dos manos tienen dato
        self.assertTrue(all(abs(v - 0.035) < 1e-9 for v in estable))

    def test_recalibra_solo_con_datos_nuevos(self):
        _, norm = self._simular(segundos=3.0, dt_ciclo=1 / 30, dt_trabajo=0.07)   # el hilo va más lento que el ciclo
        self.assertGreater(norm.n_normalizar, 0)
        self.assertLess(norm.n_actualizar, 3.0 / 0.07 + 2)

    def test_sin_manos_devuelve_none(self):
        from manos import TimbrePorManos
        self.assertIsNone(TimbrePorManos(_NormalizadorDePrueba()).actualizar(None, None, 1.0))


class PruebaHisteresisZona(unittest.TestCase):
    """Cambio 5 (HU0015-2): la zona cambia solo tras 250 ms continuos dentro de la misma candidata (reloj simulado)."""
    DT = 1 / 30
    REG = {"grave": 0.1, "medio": 0.5, "agudo": 0.9}

    def _correr(self, secuencia, zona="grave", dts=None):
        """secuencia: lista de candidatas, una por ciclo. Devuelve la lista de zonas tras cada ciclo."""
        from zona import zona_desde_registro
        pend, tiempo, zonas = None, 0.0, []
        for i, c in enumerate(secuencia):
            dt = self.DT if dts is None else dts[i]
            zona, pend, tiempo = zona_desde_registro(self.REG[c], zona, pend, tiempo, dt)
            zonas.append(zona)
        return zonas

    def test_cambia_en_la_novena_muestra_a_30hz(self):
        z = self._correr(["agudo"] * 9)
        self.assertEqual(z[7], "grave")       # 8 muestras = 233 ms dentro: aún no
        self.assertEqual(z[8], "agudo")       # 9 muestras = 267 ms dentro: cambia

    def test_paso_por_medio_no_suma_para_agudo(self):
        z = self._correr(["medio"] * 4 + ["agudo"] * 5)
        self.assertTrue(all(v == "grave" for v in z))   # con la regla anterior cambiaba (9 ciclos fuera de grave)

    def test_relampago_no_cambia(self):
        z = self._correr(["agudo"] * 6 + ["grave"] * 10)   # 200 ms en agudo y vuelve
        self.assertTrue(all(v == "grave" for v in z))

    def test_volver_a_la_zona_reinicia(self):
        z = self._correr(["agudo"] * 7 + ["grave"] + ["agudo"] * 8)
        self.assertTrue(all(v == "grave" for v in z))

    def test_tope_dt_tras_ausencia(self):
        dts = [self.DT, 2.0, self.DT, self.DT]              # hueco de 2 s sin cuerpo en el 2º ciclo: suma solo 0.1 s
        z = self._correr(["agudo"] * 4, dts=dts)
        self.assertTrue(all(v == "grave" for v in z))

    def test_sostenido_largo_cambia_una_vez(self):
        z = self._correr(["medio"] * 30)
        self.assertEqual(z.count("grave"), 8)
        self.assertTrue(all(v == "medio" for v in z[8:]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
