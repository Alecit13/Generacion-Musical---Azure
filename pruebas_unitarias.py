"""Pruebas unitarias SIN dispositivo (HU0025-1). Cada clase dice qué criterio APOYA (una prueba aislada no declara
que una historia "cumple": eso lo decide la medición).
No importan main.py (abre el puerto 8765 y la Kinect al importarse): las clases del movimiento se cargan de
movimiento.py con cargar_de_main (refactor KISS; hasta 8d58820 se leían de main.py con ast).
Cobertura (11/11):
  cubiertos  manos.py (calcular_apertura, apertura_vigente, edades_por_mano_ms, TimbrePorManos)
             muestreo.py (elegir_siguiente_nota, calcular_octava, escala activa)
             zona.py (zona_desde_registro)
             servidor.py (enviar_a_todos, manejar_cliente)
             movimiento.py: NormalizadorAdaptativo, VelocidadAngular, angulo_articulacion, MapeoExtremidades, RegistroPorAngulo
  sin cubrir main.py: bucle_kinect, HiloManos, FusionTemporal, guardar_latencias, arranque y cierre de la Kinect
             (necesitan el dispositivo: los cubre la prueba de integración US26); zona.calcular_zona (solo con
             REGISTRO_POR_ANGULO=False); index.html y visual.js (sin entorno de pruebas de JavaScript; probados con
             ?demo=1 y un servidor WebSocket falso)
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


# =====================================================================
# US25 (11/11): módulos que faltaban. Todas "apoyan" un criterio; ninguna lo declara cumplido.
# =====================================================================
import asyncio
import json
from types import SimpleNamespace


def cargar_de_main(*nombres):
    """Devuelve las clases, funciones y constantes pedidas de movimiento.py (refactor KISS: antes vivían en main.py y se
    leían con ast, porque importar main.py abre el puerto 8765 y la Kinect; movimiento.py se importa sin el dispositivo).
    Se conserva el nombre y la interfaz para no tocar las pruebas. Relación: lo usan las pruebas de NormalizadorAdaptativo,
    VelocidadAngular, angulo_articulacion, MapeoExtremidades y RegistroPorAngulo, y validacion_offline.py.
    Variables: `nombres` (lo que se pide). Devuelve un SimpleNamespace; LookupError si alguno no existe."""
    import movimiento
    faltan = sorted(k for k in nombres if not hasattr(movimiento, k))
    if faltan:
        raise LookupError(f"no están en movimiento.py: {faltan}")
    return SimpleNamespace(**{k: getattr(movimiento, k) for k in nombres})


CONST_NORM = ("NORM_VENTANA_S", "NORM_CALENTAMIENTO_S")
CONST_MAPEO = CONST_NORM + ("EMA_VEL_RODILLA", "VENTANA_INTENSIDAD_S", "VENTANA_FLUIDEZ_S", "LAMBDA_MIN",
                            "RANGO_MIN_VEL_RODILLA", "RANGO_MIN_AMPLITUD", "RANGO_MIN_ACC", "CONF_MIN_ARTICULACION",
                            "CONF_MIN_RODILLA_TEMPO", "J_PELVIS", "J_MUNECAS", "J_TOBILLOS", "J_EXTREMIDADES",
                            "J_RODILLAS")
CONST_REGISTRO = CONST_NORM + ("EMA_ANGULO_BRAZO", "RANGO_MIN_ANGULO_BRAZO", "HOLD_ANGULO_S",
                               "CONF_MIN_ANGULO_BRAZO", "J_BRAZOS")


def esqueleto(posiciones, conf=2, n=32):
    """Esqueleto falso con la forma que usa main.py: joints[i].position.xyz.{x,y,z} y joints[i].confidence_level.
    `posiciones` {índice: (x, y, z) en mm}; las demás articulaciones quedan en el origen. `conf` igual para todas
    (0 NONE, 1 LOW, 2 MEDIUM) o {índice: conf}."""
    joints = []
    for i in range(n):
        x, y, z = posiciones.get(i, (0.0, 0.0, 0.0))
        c = conf.get(i, 2) if isinstance(conf, dict) else conf
        joints.append(SimpleNamespace(position=SimpleNamespace(xyz=SimpleNamespace(x=x, y=y, z=z)), confidence_level=c))
    return SimpleNamespace(joints=joints)


class PruebaCalcularApertura(unittest.TestCase):
    """manos.calcular_apertura. Apoya HU0017-1 (la apertura crece al abrir la mano)."""

    @staticmethod
    def _mano(radio):
        puntos = [SimpleNamespace(x=0.5, y=0.5) for _ in range(21)]          # 0 = muñeca
        for k, idx in enumerate((4, 8, 12, 16, 20)):
            puntos[idx] = SimpleNamespace(x=0.5 + radio * (k + 1) / 5, y=0.5)  # distancias radio/5 ... radio
        return SimpleNamespace(landmark=puntos)

    def test_media_de_las_cinco_distancias(self):
        from manos import calcular_apertura
        self.assertAlmostEqual(calcular_apertura(self._mano(0.05)), 0.05 * 3 / 5)

    def test_abierta_mayor_que_puno(self):
        from manos import calcular_apertura
        self.assertGreater(calcular_apertura(self._mano(0.048)), calcular_apertura(self._mano(0.021)))


class PruebaOctavaYEscala(unittest.TestCase):
    """muestreo.calcular_octava y escala activa. Apoya HU0015-1 (zona -> octava) y HU0019-1 (nota de la escala activa)."""

    def test_octava_por_zona(self):
        from muestreo import calcular_octava
        self.assertEqual([calcular_octava(z) for z in ("grave", "medio", "agudo", "otra")], [3, 4, 5, 4])

    def test_todas_las_notas_en_la_escala(self):
        import random
        import muestreo
        random.seed(3)
        muestreo.reiniciar_estado()
        nota = "Do"
        for lam in (1.0, 0.5, 0.05):
            for _ in range(5000):
                nota = muestreo.elegir_siguiente_nota(nota, lam)
                self.assertIn(nota, muestreo.NOTAS)


class _WsFalso:
    """WebSocket falso para servidor.py: guarda lo enviado; `falla` hace que send lance una excepción; itera `entrantes`."""

    def __init__(self, falla=False, entrantes=()):
        self.enviados, self.falla, self.entrantes = [], falla, list(entrantes)

    async def send(self, mensaje):
        if self.falla:
            raise ConnectionError("cliente cerrado")
        self.enviados.append(mensaje)

    def __aiter__(self):
        self._it = iter(self.entrantes)
        return self

    async def __anext__(self):
        try:
            return next(self._it)
        except StopIteration:
            raise StopAsyncIteration


class PruebaServidor(unittest.TestCase):
    """servidor.py. Apoya HU0010-1 (JSON sin errores de serialización) y HU0010-2 (un cliente que se cae no detiene
    el envío a los demás ni a Python)."""

    def setUp(self):
        import servidor
        self.s = servidor
        servidor.clientes_conectados.clear()
        servidor.al_recibir = None

    tearDown = setUp

    def test_envia_json_a_todos(self):
        a, b = _WsFalso(), _WsFalso()
        self.s.clientes_conectados.update({a, b})
        asyncio.run(self.s.enviar_a_todos({"nota": "Do", "apertura01": None}))
        for ws in (a, b):
            self.assertEqual(json.loads(ws.enviados[0]), {"nota": "Do", "apertura01": None})

    def test_cliente_que_falla_se_quita_y_los_demas_reciben(self):
        bueno, malo = _WsFalso(), _WsFalso(falla=True)
        self.s.clientes_conectados.update({bueno, malo})
        asyncio.run(self.s.enviar_a_todos({"x": 1}))
        self.assertEqual(len(bueno.enviados), 1)
        self.assertNotIn(malo, self.s.clientes_conectados)
        self.assertIn(bueno, self.s.clientes_conectados)

    def test_sin_clientes_no_hace_nada(self):
        asyncio.run(self.s.enviar_a_todos({"x": 1}))          # no lanza

    def test_manejar_cliente_pasa_mensajes_y_tolera_errores(self):
        recibidos = []

        def al_recibir(m):
            if m == "malo":
                raise ValueError("JSON malformado")
            recibidos.append(m)
        self.s.al_recibir = al_recibir
        ws = _WsFalso(entrantes=["a", "malo", "b"])
        asyncio.run(self.s.manejar_cliente(ws))
        self.assertEqual(recibidos, ["a", "b"])               # el mensaje malo no corta la conexión
        self.assertNotIn(ws, self.s.clientes_conectados)      # al terminar, el cliente se quita


class PruebaNormalizadorAdaptativo(unittest.TestCase):
    """main.NormalizadorAdaptativo (RF04). Apoya HU0016-2 y HU0018-2 (saturación en [0, 1]) y D-035 (ventana de 20 s)."""

    def setUp(self):
        self.m = cargar_de_main(*CONST_NORM, "NormalizadorAdaptativo")

    def test_neutro_durante_el_calentamiento(self):
        n = self.m.NormalizadorAdaptativo(10.0)
        self.assertEqual([n.actualizar(v, t / 10) for t, v in enumerate([0, 100, 50])], [0.5, 0.5, 0.5])

    def test_satura_en_cero_y_uno(self):
        n = self.m.NormalizadorAdaptativo(10.0)
        for k in range(200):
            n.actualizar(k % 101, k * 0.05)
        self.assertEqual(n.normalizar(1000, 10.0), 1.0)
        self.assertEqual(n.normalizar(-1000, 10.0), 0.0)

    def test_rango_minimo_con_usuario_quieto(self):
        n = self.m.NormalizadorAdaptativo(10.0)
        for k in range(100):
            n.actualizar(50.0, k * 0.05)
        self.assertEqual(n.normalizar(50.0, 5.0), 0.0)        # hi = lo + 10: el ruido no se amplifica
        self.assertAlmostEqual(n.normalizar(55.0, 5.0), 0.5)

    def test_olvida_lo_de_hace_mas_de_20_s(self):
        n = self.m.NormalizadorAdaptativo(10.0)
        for k in range(30):
            n.actualizar(1000.0, k * 0.1)
        for k in range(100):
            n.actualizar(float(k % 11), 25.0 + k * 0.1)
        self.assertTrue(all(t >= 34.9 - self.m.NORM_VENTANA_S for t, _ in n.muestras))
        self.assertAlmostEqual(n.normalizar(10.0, 35.0), 1.0, places=6)


class PruebaVelocidadAngular(unittest.TestCase):
    """main.VelocidadAngular. Apoya HU0016-1 (velocidad con el dt real y suavizado EMA) y HU0012-1."""

    def setUp(self):
        self.m = cargar_de_main("EMA_VEL_RODILLA", "VelocidadAngular")

    def test_ema_con_dt_real(self):
        v, a = self.m.VelocidadAngular(), self.m.EMA_VEL_RODILLA
        self.assertIsNone(v.actualizar(0.0, 0.0))
        self.assertAlmostEqual(v.actualizar(10.0, 0.1), a * 100.0)
        self.assertAlmostEqual(v.actualizar(20.0, 0.2), a * 100.0 + (1 - a) * a * 100.0)

    def test_hueco_mayor_a_medio_segundo_no_da_velocidad(self):
        v = self.m.VelocidadAngular()
        v.actualizar(0.0, 0.0)
        self.assertIsNone(v.actualizar(90.0, 0.8))            # 0.8 s sin datos: no se inventa una velocidad
        w = v.actualizar(91.0, 0.9)                           # la siguiente parte del ángulo de después del hueco
        self.assertLess(w, 20.0)


class PruebaAnguloArticulacion(unittest.TestCase):
    """main.angulo_articulacion. Apoya HU0007 (ángulos a partir de las articulaciones) y HU0015-1."""

    def test_angulos_conocidos(self):
        """En mm (lo que recibe en main.py). Hallazgo del 11/11, sin arreglar (código congelado): con vectores UNITARIOS
        da 179.9974° en vez de 180° por el +1e-9 del denominador; con distancias en mm el efecto es < 1e-4°."""
        import numpy as np
        f = cargar_de_main("angulo_articulacion").angulo_articulacion
        o = np.zeros(3)
        self.assertAlmostEqual(f(np.array([300.0, 0, 0]), o, np.array([0, 500.0, 0])), 90.0, places=4)
        self.assertAlmostEqual(f(np.array([-300.0, 0, 0]), o, np.array([500.0, 0, 0])), 180.0, places=4)
        self.assertAlmostEqual(f(np.array([-1.0, 0, 0]), o, np.array([1.0, 0, 0])), 180.0, delta=0.01)


class PruebaMapeoExtremidades(unittest.TestCase):
    """main.MapeoExtremidades con esqueletos falsos. Apoya HU0011-1, HU0013-1, HU0016-2 y HU0018-2 (rangos de salida)
    y HU0007-2 (una articulación no fiable no inventa valores: se conserva el último)."""

    def setUp(self):
        import numpy as np
        self.np = np
        self.m = cargar_de_main(*CONST_MAPEO, "NormalizadorAdaptativo", "VelocidadAngular", "angulo_articulacion",
                                "MapeoExtremidades")

    def _pose(self, t, conf=2):
        np, m = self.np, self.m
        s = np.sin(2 * np.pi * 1.3 * t)
        pos = {m.J_PELVIS: (0, 0, 2000)}
        for k, j in enumerate(m.J_EXTREMIDADES):
            pos[j] = (300 * s * (k + 1), 200 * np.cos(3 * t + k), 2000)
        for lado, (cad, rod, tob) in m.J_RODILLAS.items():
            flex = 300 * abs(s)
            pos[cad], pos[rod], pos[tob] = (0, -100, 2000), (0, -500, 2000 + flex), (0, -900, 2000)
        return esqueleto(pos, conf)

    def test_salidas_en_rango(self):
        mapeo = self.m.MapeoExtremidades()
        for k in range(30 * 25):
            r = mapeo.actualizar(self._pose(k / 30), k / 30)
            self.assertTrue(0.0 <= r["tempo"] <= 1.0 and 0.0 <= r["intensidad"] <= 1.0)
            self.assertTrue(self.m.LAMBDA_MIN <= r["lam"] <= 1.0)

    def test_sin_articulaciones_fiables_conserva_el_ultimo(self):
        mapeo = self.m.MapeoExtremidades()
        for k in range(30 * 6):
            r = mapeo.actualizar(self._pose(k / 30), k / 30)
        antes = dict(r)
        for k in range(30 * 6, 30 * 7):
            r = mapeo.actualizar(self._pose(k / 30, conf=0), k / 30)
        self.assertEqual(r, antes)


class PruebaRegistroPorAngulo(unittest.TestCase):
    """main.RegistroPorAngulo con esqueletos falsos. Apoya HU0015-1 (brazos arriba = registro alto) y la regla de
    mantener el último valor si los brazos dejan de ser fiables."""

    def setUp(self):
        self.m = cargar_de_main(*CONST_REGISTRO, "NormalizadorAdaptativo", "angulo_articulacion", "MapeoExtremidades",
                                "RegistroPorAngulo")

    def _pose(self, grados, conf=2):
        import numpy as np
        pos = {}
        for lado, (cad, hom, cod) in self.m.J_BRAZOS.items():
            r = np.radians(grados)
            pos[hom], pos[cad], pos[cod] = (0, 0, 2000), (0, 500, 2000), (300 * np.sin(r), 300 * np.cos(r), 2000)
        return esqueleto(pos, conf)

    def _correr(self, reg, angulos, t0, dt=1 / 30, conf=2):
        out = None
        for k, a in enumerate(angulos):
            out = reg.actualizar(self._pose(a, conf), t0 + k * dt)
        return out

    def test_arriba_alto_abajo_bajo(self):
        reg = self.m.RegistroPorAngulo()
        self._correr(reg, [20] * 60 + [160] * 60 + [20] * 60 + [160] * 60, 0.0)   # 8 s de calibración
        alto = self._correr(reg, [160] * 30, 8.0)["registro01"]
        bajo = self._correr(reg, [20] * 30, 9.0)["registro01"]
        self.assertGreater(alto, 0.8)
        self.assertLess(bajo, 0.2)

    def test_brazos_no_fiables_conservan_el_ultimo_valor(self):
        reg = self.m.RegistroPorAngulo()
        self._correr(reg, [20] * 60 + [160] * 60 + [20] * 60, 0.0)
        antes = self._correr(reg, [160] * 30, 6.0)["registro01"]
        despues = self._correr(reg, [20] * 30, 7.0, conf=1)["registro01"]     # LOW < CONF_MIN_ANGULO_BRAZO
        self.assertEqual(despues, antes)


class PruebaCabeceraCSV(unittest.TestCase):
    """salidas.py (refactor KISS). Apoya HU0022-1: el CSV de sesión y el _latencias.csv tienen las mismas columnas que
    en 8d58820 (código medido), y la fila que arma bucle_kinect tiene tantos valores como columnas la cabecera."""

    # Copiadas de main.py en 8d58820 (log_writer.writerow de la cabecera y guardar_latencias)
    SESION_8D58820 = ["timestamp", "zona", "lambda", "acc_media", "nota", "octava", "apertura", "apertura_izq",
                      "apertura_der", "manos", "tempo", "intensidad", "apertura01", "vel_rodilla", "amplitud_mm",
                      "t_cap_ms", "lat_tick_ms", "ang_hombro_izq", "ang_hombro_der", "ang_codo_izq", "ang_codo_der",
                      "ang_cadera_izq", "ang_cadera_der", "ang_rodilla_izq", "ang_rodilla_der", "conf_hombro_izq",
                      "conf_hombro_der", "reg01_izq", "reg01_der", "registro01", "n_joints_ok", "joints_no_disp",
                      "edad_manos_ms", "par_dt_ms", "desync_manos", "roi_izq", "roi_der", "lag_cam_ms",
                      "frames_descartados", "nota_id", "lam_sorteo", "semilla", "version", "commit", "edad_izq_ms",
                      "edad_der_ms"]
    LATENCIAS_8D58820 = ["t_epoch_ms", "tipo", "latencia_ms", "transporte_ms", "output_latency_ms", "base_latency_ms",
                         "latencia_llegada_ms"]

    def test_cabeceras_iguales_a_8d58820(self):
        import salidas
        self.assertEqual(salidas.COLUMNAS_SESION, self.SESION_8D58820)
        self.assertEqual(len(salidas.COLUMNAS_SESION), 46)
        self.assertEqual(salidas.COLUMNAS_LATENCIAS, self.LATENCIAS_8D58820)

    def test_fila_de_bucle_kinect_con_tantos_valores_como_columnas(self):
        """Cuenta los elementos de la lista que bucle_kinect pasa a log_writer.writerow (sin ejecutar main.py)."""
        import ast
        import pathlib
        import salidas
        arbol = ast.parse(pathlib.Path(__file__).with_name("main.py").read_text(encoding="utf-8"))
        bucle = next(n for n in arbol.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "bucle_kinect")
        filas = [n.args[0] for n in ast.walk(bucle)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "writerow"
                 and isinstance(n.func.value, ast.Name) and n.func.value.id == "log_writer"]
        self.assertEqual(len(filas), 1)
        self.assertEqual(len(filas[0].elts), len(salidas.COLUMNAS_SESION))

    def test_abrir_csv_escribe_la_misma_cabecera(self):
        import csv
        import io
        import os
        import tempfile
        import salidas
        ruta = os.path.join(tempfile.mkdtemp(), "prueba.csv")
        archivo, _ = salidas.abrir_csv(ruta, salidas.COLUMNAS_SESION)
        archivo.close()
        esperado = io.StringIO(newline="")
        csv.writer(esperado).writerow(self.SESION_8D58820)
        with open(ruta, newline="") as f:
            self.assertEqual(f.read(), esperado.getvalue())
        os.remove(ruta)


if __name__ == "__main__":
    unittest.main(verbosity=2)
