"""Movimiento -> parámetros musicales continuos (RF04, RF05). Sin Kinect ni puerto: se importa en las pruebas.
Contenido (copiado sin cambios de main.py en el refactor KISS):
  NormalizadorAdaptativo  lleva una medida cruda a [0,1] con el rango del usuario en los últimos NORM_VENTANA_S s
  VelocidadAngular        velocidad angular suavizada (EMA_VEL_RODILLA) de un ángulo, con el dt real
  angulo_articulacion     ángulo en b de a-b-c (grados)
  MapeoExtremidades       tempo (rodillas), intensidad (amplitud en 2 s) y λ (suavidad) de un esqueleto
  RegistroPorAngulo       registro01 (tono) desde el ángulo de los hombros, y los 8 ángulos del CSV
  estado_articulaciones   HU0007-2: articulaciones fiables y no disponibles
Relación: main.py crea `mapeo`, `registro` y el normalizador del timbre y los llama una vez por ciclo en bucle_kinect;
pruebas_unitarias.py y validacion_offline.py los prueban con esqueletos falsos.
Variables clave: las constantes de abajo (antes en la cabecera de main.py) y los índices J_* de articulaciones."""
import collections

import numpy as np
import pykinect_azure as pykinect

# Mapeo de extremidades (RF05) y normalización por usuario (RF04)
VENTANA_INTENSIDAD_S = 2.0   # ventana de tiempo para medir la amplitud de las 4 extremidades
VENTANA_FLUIDEZ_S = 0.6      # ventana de tiempo para medir la suavidad (lambda)
LAMBDA_MIN = 0.05            # lambda nunca baja de aquí (igual que antes)
EMA_VEL_RODILLA = 0.4        # suavizado de la velocidad angular (0-1; más alto = menos suavizado)
NORM_VENTANA_S = 20.0        # el usuario "se calibra" con sus últimos 20 s de movimiento
NORM_CALENTAMIENTO_S = 3.0   # durante los primeros 3 s la salida normalizada vale 0.5
# Rangos mínimos: evitan que el ruido del sensor se amplifique cuando el usuario está quieto
RANGO_MIN_VEL_RODILLA = 30.0     # grados/s
RANGO_MIN_AMPLITUD = 100.0       # mm
RANGO_MIN_ACC = 3000.0           # mm/s^2
CONF_MIN_RODILLA_TEMPO = 1       # confianza mínima de cadera, rodilla y tobillo para el tempo; main.py pasa 2 con --tempo-medium

# Tono: REGISTRO (octava) a partir del ángulo de los hombros (RF05: ángulos articulares -> tono)
CONF_MIN_ANGULO_BRAZO = 2         # confianza mínima para usar el ángulo de un brazo (2 = MEDIUM; 1 = LOW = pose "predicha")
EMA_ANGULO_BRAZO = 0.5            # suavizado del ángulo del hombro (0-1; más alto = menos suavizado)
RANGO_MIN_ANGULO_BRAZO = 60.0     # grados: rango mínimo para normalizar (evita que 20° de movimiento ya sea "agudo")
HOLD_ANGULO_S = 0.5               # si un brazo deja de ser fiable, se mantiene su último valor este tiempo

# Disponibilidad de articulaciones (HU0007)
CONF_MIN_ARTICULACION = 1        # 0=NONE, 1=LOW, 2=MEDIUM (confianza de la Kinect)
N_JOINTS = 32                    # articulaciones del esqueleto de Azure Kinect

# Articulaciones usadas por el mapeo de extremidades
J_PELVIS = pykinect.K4ABT_JOINT_PELVIS
J_MUNECAS = (pykinect.K4ABT_JOINT_WRIST_LEFT, pykinect.K4ABT_JOINT_WRIST_RIGHT)
J_TOBILLOS = (pykinect.K4ABT_JOINT_ANKLE_LEFT, pykinect.K4ABT_JOINT_ANKLE_RIGHT)
J_EXTREMIDADES = J_MUNECAS + J_TOBILLOS            # las 4 extremidades
J_BRAZOS = {                                         # (cadera, hombro, codo) de cada lado: ángulo del hombro
    "izq": (pykinect.K4ABT_JOINT_HIP_LEFT, pykinect.K4ABT_JOINT_SHOULDER_LEFT, pykinect.K4ABT_JOINT_ELBOW_LEFT),
    "der": (pykinect.K4ABT_JOINT_HIP_RIGHT, pykinect.K4ABT_JOINT_SHOULDER_RIGHT, pykinect.K4ABT_JOINT_ELBOW_RIGHT),
}
J_RODILLAS = {                                       # (cadera, rodilla, tobillo) de cada pierna
    "izq": (pykinect.K4ABT_JOINT_HIP_LEFT, pykinect.K4ABT_JOINT_KNEE_LEFT, pykinect.K4ABT_JOINT_ANKLE_LEFT),
    "der": (pykinect.K4ABT_JOINT_HIP_RIGHT, pykinect.K4ABT_JOINT_KNEE_RIGHT, pykinect.K4ABT_JOINT_ANKLE_RIGHT),
}
J_ANGULOS = {                                        # los 8 ángulos "candidatos" que se guardan en el CSV
    "hombro_izq": J_BRAZOS["izq"], "hombro_der": J_BRAZOS["der"],
    "codo_izq": (pykinect.K4ABT_JOINT_SHOULDER_LEFT, pykinect.K4ABT_JOINT_ELBOW_LEFT, pykinect.K4ABT_JOINT_WRIST_LEFT),
    "codo_der": (pykinect.K4ABT_JOINT_SHOULDER_RIGHT, pykinect.K4ABT_JOINT_ELBOW_RIGHT, pykinect.K4ABT_JOINT_WRIST_RIGHT),
    "cadera_izq": (pykinect.K4ABT_JOINT_SHOULDER_LEFT, pykinect.K4ABT_JOINT_HIP_LEFT, pykinect.K4ABT_JOINT_KNEE_LEFT),
    "cadera_der": (pykinect.K4ABT_JOINT_SHOULDER_RIGHT, pykinect.K4ABT_JOINT_HIP_RIGHT, pykinect.K4ABT_JOINT_KNEE_RIGHT),
    "rodilla_izq": J_RODILLAS["izq"],
    "rodilla_der": J_RODILLAS["der"],
}


class NormalizadorAdaptativo:
    """Convierte una medida cruda (grados/s, mm, ...) a [0,1] según el propio rango del usuario.
    Guarda los valores de los últimos NORM_VENTANA_S segundos y usa sus percentiles 5 y 95
    como 'mínimo' y 'máximo' (robusto a picos). `rango_min` evita amplificar ruido si el
    usuario está quieto. Lo usan MapeoExtremidades (tempo, intensidad, lambda) y bucle_kinect
    (apertura)."""

    def __init__(self, rango_min):
        self.muestras = collections.deque()   # pares (tiempo, valor)
        self.rango_min = rango_min

    def actualizar(self, valor, t):
        self.muestras.append((t, valor))
        while t - self.muestras[0][0] > NORM_VENTANA_S:
            self.muestras.popleft()
        return self.normalizar(valor, t)

    def normalizar(self, valor, t):
        """Lleva `valor` a [0,1] con las muestras ya guardadas, SIN añadirlo (cambio 6: TimbrePorManos lo usa en los
        ciclos sin dato nuevo de manos, para no recalibrar con valores mantenidos). actualizar() termina aquí."""
        if not self.muestras or t - self.muestras[0][0] < NORM_CALENTAMIENTO_S:
            return 0.5                      # aún calibrando: valor neutro
        vals = np.fromiter((v for _, v in self.muestras), dtype=float)
        lo, hi = np.percentile(vals, [5, 95])
        hi = max(hi, lo + self.rango_min)
        return float(np.clip((valor - lo) / (hi - lo), 0.0, 1.0))


class VelocidadAngular:
    """Velocidad angular suavizada (grados/s) de un ángulo que llega ciclo a ciclo.
    Usa el tiempo REAL entre ciclos (dt), no el número de ciclos. Si pasa más de 0.5 s
    sin datos, se reinicia. Una instancia por rodilla dentro de MapeoExtremidades."""

    def __init__(self):
        self.ang_prev = None
        self.t_prev = None
        self.suav = 0.0

    def actualizar(self, angulo, t):
        w = None
        if self.t_prev is not None:
            dt = t - self.t_prev
            if 0.0 < dt <= 0.5:
                bruta = abs(angulo - self.ang_prev) / dt
                self.suav = EMA_VEL_RODILLA * bruta + (1 - EMA_VEL_RODILLA) * self.suav
                w = self.suav
        self.ang_prev, self.t_prev = angulo, t
        return w


def angulo_articulacion(a, b, c):
    """Ángulo (grados) en el punto b formado por a-b-c. Con cadera, rodilla y tobillo
    da el ángulo de la rodilla (180° = pierna estirada). Lo usa MapeoExtremidades."""
    v1, v2 = a - b, c - b
    cos = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
    return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))


class MapeoExtremidades:
    """Traduce el esqueleto a los parámetros musicales de la tabla del TI (RF05):
         velocidad angular de rodillas       -> tempo       (0-1)
         amplitud de 4 extremidades en ~2 s  -> intensidad  (0-1)
         suavidad de muñecas + tobillos      -> lambda      (0.05-1)
    (registro/tono y timbre se calculan aparte: altura de muñeca y apertura de manos).
    Variables importantes: `hist` (posiciones recientes de las 4 extremidades RELATIVAS a la
    pelvis, para ignorar si el usuario camina), y un NormalizadorAdaptativo por parámetro (RF04).
    Se llama una vez por ciclo desde bucle_kinect: actualizar(skeleton, t) -> dict.
    `conf_min_rodilla_tempo`: confianza mínima de cadera, rodilla y tobillo para usar una rodilla en el tempo
    (CONF_MIN_RODILLA_TEMPO = 1; main.py pasa 2 con --tempo-medium)."""

    def __init__(self, conf_min_rodilla_tempo=CONF_MIN_RODILLA_TEMPO):
        self.conf_min_rodilla_tempo = conf_min_rodilla_tempo
        self.hist = collections.deque()      # (t, array 4x3 en mm)
        self.vel_rod = {"izq": VelocidadAngular(), "der": VelocidadAngular()}
        self.n_tempo = NormalizadorAdaptativo(RANGO_MIN_VEL_RODILLA)
        self.n_inten = NormalizadorAdaptativo(RANGO_MIN_AMPLITUD)
        self.n_acc = NormalizadorAdaptativo(RANGO_MIN_ACC)
        # últimos valores (se conservan si una articulación no es fiable en este ciclo)
        self.tempo, self.intensidad, self.lam = 0.5, 0.0, 1.0
        self.vel_rodilla, self.amplitud_mm, self.acc_mm = 0.0, 0.0, 0.0

    @staticmethod
    def _pos(joints, i):
        p = joints[i].position.xyz
        return np.array([p.x, p.y, p.z], dtype=float)

    @staticmethod
    def _ok(joints, i):
        return joints[i].confidence_level >= CONF_MIN_ARTICULACION

    def actualizar(self, skeleton, t):
        J = skeleton.joints

        # --- Tempo: velocidad angular media de las rodillas ---
        omegas = []
        for lado, (cad, rod, tob) in J_RODILLAS.items():
            if all(J[i].confidence_level >= self.conf_min_rodilla_tempo for i in (cad, rod, tob)):   # 1 = igual que _ok
                ang = angulo_articulacion(self._pos(J, cad), self._pos(J, rod), self._pos(J, tob))
                w = self.vel_rod[lado].actualizar(ang, t)
                if w is not None:
                    omegas.append(w)
        if omegas:
            self.vel_rodilla = float(np.mean(omegas))
            self.tempo = self.n_tempo.actualizar(self.vel_rodilla, t)

        # --- Intensidad y lambda: las 4 extremidades relativas a la pelvis ---
        if self._ok(J, J_PELVIS) and all(self._ok(J, i) for i in J_EXTREMIDADES):
            pelvis = self._pos(J, J_PELVIS)
            self.hist.append((t, np.stack([self._pos(J, i) - pelvis for i in J_EXTREMIDADES])))
            while t - self.hist[0][0] > VENTANA_INTENSIDAD_S:
                self.hist.popleft()

            if len(self.hist) >= 5 and t - self.hist[0][0] >= 0.5:
                P = np.stack([p for _, p in self.hist])                  # (n, 4, 3)
                rango = P.max(axis=0) - P.min(axis=0)                    # (4, 3)
                self.amplitud_mm = float(np.linalg.norm(rango, axis=1).mean())
                self.intensidad = self.n_inten.actualizar(self.amplitud_mm, t)

            recientes = [(ti, p) for ti, p in self.hist if t - ti <= VENTANA_FLUIDEZ_S]
            if len(recientes) >= 4:
                ts = np.array([ti for ti, _ in recientes])
                P = np.stack([p for _, p in recientes])
                dt = np.maximum(np.diff(ts), 1e-3)
                V = np.diff(P, axis=0) / dt[:, None, None]               # velocidad mm/s
                tv = (ts[1:] + ts[:-1]) / 2
                A = np.diff(V, axis=0) / np.maximum(np.diff(tv), 1e-3)[:, None, None]
                self.acc_mm = float(np.linalg.norm(A, axis=2).mean())    # aceleración mm/s^2
                acc01 = self.n_acc.actualizar(self.acc_mm, t)
                self.lam = max(1.0 - acc01, LAMBDA_MIN)

        return {
            "tempo": self.tempo, "intensidad": self.intensidad, "lam": self.lam,
            "vel_rodilla": self.vel_rodilla, "amplitud_mm": self.amplitud_mm, "acc_mm": self.acc_mm,
        }


class RegistroPorAngulo:
    """Tono (REGISTRO) a partir de ÁNGULOS ARTICULARES (RF05): usa el ángulo de elevación de cada
    hombro (cadera-hombro-codo: ~0° con el brazo colgando, ~90° horizontal, ~180° arriba).
    Cada brazo se normaliza por separado con su propio NormalizadorAdaptativo (RF04: así quien
    tiene menos rango, o es zurdo, igual recorre todo el registro) y luego se promedian los brazos
    vigentes (D-002). Además calcula los 8 ángulos candidatos (hombro, codo,
    cadera, rodilla; izq/der) SOLO para guardarlos en el CSV y poder analizarlos después.
    Relación con el resto: reutiliza angulo_articulacion y MapeoExtremidades._pos; su salida
    `registro01` la convierte en zona zona_desde_registro, y calcular_octava (muestreo.py) la
    vuelve octava. Se llama una vez por ciclo desde bucle_kinect, igual que `mapeo`.
    Variables importantes: `reg01` (0-1 por brazo), `t_ok` (cuándo fue fiable cada brazo; sirve para
    el HOLD), `registro01` (resultado combinado). Si ningún brazo es fiable, conserva el último valor."""

    def __init__(self):
        self.norm = {l: NormalizadorAdaptativo(RANGO_MIN_ANGULO_BRAZO) for l in J_BRAZOS}
        self.ang_suav = {l: None for l in J_BRAZOS}
        self.reg01 = {l: None for l in J_BRAZOS}
        self.t_ok = {l: -1e9 for l in J_BRAZOS}
        self.registro01 = 0.5

    def actualizar(self, skeleton, t):
        """Actualiza ambos brazos y devuelve {registro01, reg01_izq, reg01_der, conf_izq, conf_der}."""
        J = skeleton.joints
        for lado, (cad, hom, cod) in J_BRAZOS.items():
            if all(J[i].confidence_level >= CONF_MIN_ANGULO_BRAZO for i in (cad, hom, cod)):
                ang = angulo_articulacion(MapeoExtremidades._pos(J, cad), MapeoExtremidades._pos(J, hom),
                                          MapeoExtremidades._pos(J, cod))
                prev = self.ang_suav[lado]
                self.ang_suav[lado] = ang if prev is None else EMA_ANGULO_BRAZO * ang + (1 - EMA_ANGULO_BRAZO) * prev
                self.reg01[lado] = self.norm[lado].actualizar(self.ang_suav[lado], t)
                self.t_ok[lado] = t
        vigentes = [v for l, v in self.reg01.items() if v is not None and t - self.t_ok[l] <= HOLD_ANGULO_S]
        if vigentes:
            self.registro01 = float(np.mean(vigentes))
        return {
            "registro01": self.registro01,
            "reg01_izq": self.reg01["izq"], "reg01_der": self.reg01["der"],
            "conf_izq": int(J[J_BRAZOS["izq"][1]].confidence_level),
            "conf_der": int(J[J_BRAZOS["der"][1]].confidence_level),
        }

    def angulos_candidatos(self, skeleton):
        """Los 8 ángulos (grados) de hombros, codos, caderas y rodillas, o None si alguna de sus
        articulaciones tiene menos confianza que CONF_MIN_ARTICULACION. Solo para el CSV."""
        J = skeleton.joints
        salida = {}
        for nombre, (a, b, c) in J_ANGULOS.items():
            if all(J[i].confidence_level >= CONF_MIN_ARTICULACION for i in (a, b, c)):
                salida[nombre] = angulo_articulacion(MapeoExtremidades._pos(J, a), MapeoExtremidades._pos(J, b),
                                                     MapeoExtremidades._pos(J, c))
            else:
                salida[nombre] = None
        return salida


def estado_articulaciones(skeleton):
    """HU0007-2: cuántas de las N_JOINTS articulaciones son fiables en este frame y cuáles NO están
    disponibles (confianza < CONF_MIN_ARTICULACION). Devuelve (n_ok, [índices no disponibles]).
    Se usa en bucle_kinect para el CSV y el payload; sirve para medir el % de frames con 32 joints."""
    J = skeleton.joints
    no_disp = [i for i in range(N_JOINTS) if J[i].confidence_level < CONF_MIN_ARTICULACION]
    return N_JOINTS - len(no_disp), no_disp
