"""Fusión cuerpo-manos por marca de tiempo (RF03 / HU0009): solo medición, no cambia el sonido.
FusionTemporal (copiada sin cambios de main.py en el refactor KISS) empareja cada dato nuevo de manos con el frame de
cuerpo más cercano, cuenta los pares dentro de ±VENTANA_FUSION_MS y mide la edad del dato de manos.
Relación: main.py crea `fusion`; bucle_kinect llama registrar_cuerpo y actualizar en cada ciclo con cuerpo y reportar()
escribe la línea [FUSION] con resumen_y_reiniciar. Variables clave: VENTANA_FUSION_MS, `t_cuerpo`, `edades`."""
import collections

import numpy as np

VENTANA_FUSION_MS = 16.0         # tolerancia del emparejado cuerpo-manos (TI: ±16 ms)


class FusionTemporal:
    """Fusión cuerpo-manos por TIMESTAMP del frame de origen (RF03 / HU0009).
    Cada resultado de manos lleva el instante (perf_counter) del frame que lo originó; aquí se
    empareja con el frame del cuerpo más cercano en el tiempo y se comprueba que la diferencia
    sea <= VENTANA_FUSION_MS. Como las manos salen del MISMO frame de la Kinect, la diferencia
    de pareja es ~0 ms; lo que sí se mide aparte es la EDAD del dato de manos cuando se usa
    (el hilo tarda 27-56 ms), porque eso es lo que afecta a la latencia del timbre.
    Relación con el resto: bucle_kinect llama registrar_cuerpo(t_ciclo) en cada ciclo con cuerpo
    y actualizar(...) con los tiempos que entrega hilo_manos.estado(); reportar() imprime el
    resumen. Si no hay dato de manos vigente, desync_manos=True (HU0009-2): el audio conserva el
    último valor y el CSV lo registra.
    Variables: `t_cuerpo` (tiempos de los últimos frames con cuerpo), `ultimo_t_manos` (frame del
    último resultado de manos ya emparejado), `pares_ok/pares_desync` (conteo), `edades` (ms)."""

    def __init__(self):
        self.t_cuerpo = collections.deque(maxlen=60)
        self.ultimo_t_manos = None
        self.par_dt_ms = None
        self.pares_ok, self.pares_desync = 0, 0
        self.edades = []
        self.n_ciclos, self.n_vigente = 0, 0

    def registrar_cuerpo(self, t_frame):
        """Anota el instante de un frame en el que SÍ hubo cuerpo."""
        self.t_cuerpo.append(t_frame)

    def actualizar(self, t_ciclo, ult_t_ap, hay_dato):
        """Se llama una vez por ciclo. `ult_t_ap` = {lado: instante del frame medido} del hilo de
        manos; `hay_dato` = hay apertura vigente (dentro del HOLD). Devuelve
        {edad_manos_ms, par_dt_ms, desync_manos}."""
        t_manos = max(ult_t_ap.values())
        if t_manos > -1e8 and (self.ultimo_t_manos is None or t_manos > self.ultimo_t_manos):
            self.ultimo_t_manos = t_manos                 # llegó un resultado nuevo: se empareja
            cerca = min((abs(tb - t_manos) for tb in self.t_cuerpo), default=None)
            self.par_dt_ms = None if cerca is None else cerca * 1000.0
            if self.par_dt_ms is not None and self.par_dt_ms <= VENTANA_FUSION_MS:
                self.pares_ok += 1
            else:
                self.pares_desync += 1
        # la edad solo cuenta cuando hay dato vigente: con la mano perdida seguiría creciendo sin sentido
        edad = (t_ciclo - self.ultimo_t_manos) * 1000.0 if (hay_dato and self.ultimo_t_manos is not None) else None
        self.n_ciclos += 1
        self.n_vigente += int(hay_dato)
        if edad is not None:
            self.edades.append(edad)
        return {"edad_manos_ms": edad, "par_dt_ms": self.par_dt_ms, "desync_manos": not hay_dato}

    def resumen_y_reiniciar(self):
        """Texto para la consola: % de pares sincronizados y edad del dato de manos (media, p95,
        % de ciclos con edad <= VENTANA_FUSION_MS). Reinicia la ventana de edades."""
        total = self.pares_ok + self.pares_desync
        pares = f"{100.0 * self.pares_ok / total:.0f}% pares en ±{VENTANA_FUSION_MS:.0f}ms (n={total})" if total else "sin pares aún"
        if self.edades:
            e = np.array(self.edades)
            edad = (f"edad manos media={e.mean():.0f}ms p95={np.percentile(e, 95):.0f}ms "
                    f"| edad<={VENTANA_FUSION_MS:.0f}ms: {100.0 * (e <= VENTANA_FUSION_MS).mean():.0f}% de ciclos")
        else:
            edad = "sin dato de manos vigente"
        vig = f"dato vigente en {100.0 * self.n_vigente / self.n_ciclos:.0f}% de ciclos" if self.n_ciclos else ""
        self.edades, self.n_ciclos, self.n_vigente = [], 0, 0
        return f"{pares} | {vig} | {edad}"
