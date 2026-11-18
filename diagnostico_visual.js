// =====================================================================
// diagnostico_visual.js — puerta de la demo de US38 (D-078): ROJO y DESTELLOS sobre los píxeles reales del lienzo.
// NO lo carga index.html. Se carga a mano en la consola, con la página en ?demo=1 y "Empezar" pulsado:
//   const s = document.createElement("script"); s.src = "diagnostico_visual.js"; document.head.append(s);
//   // y luego:  await DiagnosticoVisual.medir()      (120 s; devuelve y guarda el resultado en window.__diagnostico)
// Se corre APARTE de la medición del tiempo por cuadro (Visual.estadisticas()): leer el lienzo cuesta CPU y la perturbaría.
//
// Definiciones de D-078 (docs/DECISIONES.md, commit 6d1baf5), con las mismas constantes:
//   ROJO: píxel con matiz en [340°, 360°) ∪ [0°, 20°], saturación >= 0.30 y valor >= 0.20 (HSV).
//         "Sin rojo" (parte MEDIDA): 1 muestra/s durante 120 s, <= 0.1 % de píxeles rojos en cada muestra.
//   DESTELLO (WCAG 2.3.1): luminancia relativa (sRGB a lineal, 0.2126 R + 0.7152 G + 0.0722 B) muestreada cada 50 ms;
//         destello = par de cambios opuestos, cada uno >= 0.10, con la luminancia más oscura < 0.80;
//         límite: <= 3 destellos en cualquier ventana de 1 s, en el lienzo completo y en cada celda de una cuadrícula 4 x 4
//         (regla de las celdas de D-078: si Ondas falla por celdas, las celdas pasan a ser solo informativas).
// Detalles de método que D-078 no fija (no cambian ninguna constante):
//   - Rojo: se lee el lienzo a resolución completa (todos los píxeles del canvas), 1 vez por segundo.
//   - Destellos: cada 50 ms el lienzo se reduce a ANCHO_REDUCIDO px de ancho (el navegador promedia los píxeles) y la
//     luminancia de cada píxel reducido se promedia en el lienzo y en cada celda. Promediar en sRGB antes de linealizar
//     es una aproximación (el error es pequeño frente al umbral de 0.10; INFERIDO).
//   - "Cambio": tramo monótono entre un extremo y el siguiente, detectado con histéresis de 0.10 (el mismo umbral).
//     Un destello = 2 cambios opuestos seguidos; en cada ventana de 1 s se cuentan floor(cambios / 2).
//   - Las marcas de tiempo son las de setInterval (aprox. 50 ms); se informa el intervalo real medio.
// =====================================================================
const DiagnosticoVisual = (() => {
  // ---- Constantes de D-078 ----
  const ROJO_MATIZ_DESDE = 340, ROJO_MATIZ_HASTA = 20;   // grados: [340, 360) ∪ [0, 20)
  const ROJO_S_MIN = 0.30, ROJO_V_MIN = 0.20;
  const ROJO_PCT_MAX = 0.1;                              // % de píxeles por muestra
  const ROJO_PERIODO_MS = 1000;
  const DESTELLO_PERIODO_MS = 50;
  const DESTELLO_DELTA = 0.10;
  const DESTELLO_OSCURO_MAX = 0.80;
  const DESTELLOS_MAX_1S = 3;
  const CELDAS = 4;
  const DURACION_S = 120;
  // ---- Método ----
  const ANCHO_REDUCIDO = 160;

  const LIN = new Float32Array(256);   // sRGB 8 bits -> lineal (IEC 61966-2-1)
  for (let i = 0; i < 256; i++) { const c = i / 255; LIN[i] = c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }

  function esRojo(r, g, b) {
    /* Aplica la definición de rojo de D-078 a un píxel (0-255). */
    const max = Math.max(r, g, b), min = Math.min(r, g, b);
    if (max === 0 || max / 255 < ROJO_V_MIN) return false;
    const d = max - min;
    if (d / max < ROJO_S_MIN || d === 0) return false;
    let h;
    if (max === r) h = 60 * (((g - b) / d) % 6);
    else if (max === g) h = 60 * ((b - r) / d + 2);
    else h = 60 * ((r - g) / d + 4);
    if (h < 0) h += 360;
    return h >= ROJO_MATIZ_DESDE || h < ROJO_MATIZ_HASTA;
  }

  function muestraRojo(lienzo) {
    /* % de píxeles rojos de todo el lienzo, a resolución completa. Solo cuenta píxeles con alfa > 0. */
    const datos = lienzo.getContext("2d").getImageData(0, 0, lienzo.width, lienzo.height).data;
    let rojos = 0, total = 0;
    for (let i = 0; i < datos.length; i += 4) {
      if (datos[i + 3] === 0) continue;
      total++;
      if (esRojo(datos[i], datos[i + 1], datos[i + 2])) rojos++;
    }
    return total ? 100 * rojos / total : 0;
  }

  function muestraLuminancia(lienzo, reducido, ctxR) {
    /* Luminancia relativa media del lienzo completo y de cada una de las CELDAS x CELDAS celdas. */
    ctxR.clearRect(0, 0, reducido.width, reducido.height);
    ctxR.drawImage(lienzo, 0, 0, reducido.width, reducido.height);
    const w = reducido.width, h = reducido.height, datos = ctxR.getImageData(0, 0, w, h).data;
    const suma = new Float64Array(CELDAS * CELDAS), n = new Uint32Array(CELDAS * CELDAS);
    let total = 0;
    for (let y = 0; y < h; y++) {
      const cy = Math.min(CELDAS - 1, Math.floor(y * CELDAS / h));
      for (let x = 0; x < w; x++) {
        const i = 4 * (y * w + x);
        const L = 0.2126 * LIN[datos[i]] + 0.7152 * LIN[datos[i + 1]] + 0.0722 * LIN[datos[i + 2]];
        const k = cy * CELDAS + Math.min(CELDAS - 1, Math.floor(x * CELDAS / w));
        suma[k] += L; n[k]++; total += L;
      }
    }
    return { lienzo: total / (w * h), celdas: Array.from(suma, (s, k) => s / n[k]) };
  }

  function cambios(serie, tiempos) {
    /* Cambios monótonos >= DESTELLO_DELTA entre extremos (histéresis), con la luminancia más oscura < DESTELLO_OSCURO_MAX.
       Devuelve los instantes (ms) en que termina cada cambio que cuenta. */
    const fin = [];
    const cuenta = (a, b) => Math.min(a, b) < DESTELLO_OSCURO_MAX;   // el estado más oscuro del cambio < 0.80
    let dir = 0, base = 0, ext = 0, tExt = 0;                         // dir: +1 subiendo, -1 bajando, 0 sin definir
    let min = Infinity, max = -Infinity;
    for (let i = 0; i < serie.length; i++) {
      const L = serie[i], t = tiempos[i];
      if (dir === 0) {                                 // hasta el primer cambio >= delta: se siguen el mínimo y el máximo
        min = Math.min(min, L); max = Math.max(max, L);
        if (L - min >= DESTELLO_DELTA) { dir = 1; base = min; ext = L; tExt = t; }
        else if (max - L >= DESTELLO_DELTA) { dir = -1; base = max; ext = L; tExt = t; }
      } else if (dir * (L - ext) > 0) {                // sigue en la misma dirección: el extremo avanza
        ext = L; tExt = t;
      } else if (Math.abs(L - ext) >= DESTELLO_DELTA) { // se dio vuelta >= delta: terminó el cambio base -> ext
        if (cuenta(base, ext)) fin.push(tExt);
        base = ext; ext = L; tExt = t; dir = -dir;
      }
    }
    if (dir !== 0 && cuenta(base, ext)) fin.push(tExt); // el último cambio (ya es >= delta)
    return fin;
  }

  function maxDestellos1s(serie, tiempos) {
    /* Máximo de destellos (pares de cambios opuestos) en cualquier ventana de 1 s. */
    const t = cambios(serie, tiempos);
    let max = 0, j = 0;
    for (let i = 0; i < t.length; i++) {
      while (t[i] - t[j] >= 1000) j++;
      max = Math.max(max, Math.floor((i - j + 1) / 2));
    }
    return max;
  }

  async function medir(opciones = {}) {
    /* Muestrea el lienzo #lienzo durante DURACION_S (o opciones.segundos) y devuelve el resultado.
       Rojo: 1 muestra/s a resolución completa. Destellos: 1 muestra cada 50 ms, lienzo y celdas. */
    const segundos = opciones.segundos || DURACION_S;
    const lienzo = document.getElementById("lienzo");
    const reducido = document.createElement("canvas");
    reducido.width = ANCHO_REDUCIDO;
    reducido.height = Math.max(CELDAS, Math.round(ANCHO_REDUCIDO * lienzo.height / lienzo.width));
    const ctxR = reducido.getContext("2d", { willReadFrequently: true });
    const tiempos = [], serieLienzo = [], seriesCeldas = Array.from({ length: CELDAS * CELDAS }, () => []);
    const rojo = [];
    const t0 = performance.now();
    await new Promise(resolver => {
      let proximoRojo = t0;
      const id = setInterval(() => {
        const ahora = performance.now();
        const m = muestraLuminancia(lienzo, reducido, ctxR);
        tiempos.push(ahora - t0); serieLienzo.push(m.lienzo);
        m.celdas.forEach((L, k) => seriesCeldas[k].push(L));
        if (ahora >= proximoRojo) { rojo.push(muestraRojo(lienzo)); proximoRojo += ROJO_PERIODO_MS; }
        if (ahora - t0 >= segundos * 1000) { clearInterval(id); resolver(); }
      }, DESTELLO_PERIODO_MS);
    });
    const dL = serieLienzo.slice(1).map((L, i) => Math.abs(L - serieLienzo[i]));
    const destCeldas = seriesCeldas.map(s => maxDestellos1s(s, tiempos));
    const peor = destCeldas.indexOf(Math.max(...destCeldas));
    const r = {
      escena: (window.Visual && Visual.estadisticas && Visual.estadisticas().escena) || "ondas (sin campo escena)",
      lienzo_px: `${lienzo.width}x${lienzo.height}`, segundos: +(tiempos[tiempos.length - 1] / 1000).toFixed(1),
      rojo_muestras: rojo.length, rojo_pct_max: +Math.max(...rojo).toFixed(4),
      rojo_cumple: rojo.length > 0 && Math.max(...rojo) <= ROJO_PCT_MAX,
      destello_muestras: tiempos.length,
      destello_intervalo_medio_ms: +((tiempos[tiempos.length - 1] - tiempos[0]) / (tiempos.length - 1)).toFixed(1),
      L_lienzo_min: +Math.min(...serieLienzo).toFixed(4), L_lienzo_max: +Math.max(...serieLienzo).toFixed(4),
      dL_lienzo_max: +Math.max(...dL).toFixed(4),
      destellos_1s_lienzo_max: maxDestellos1s(serieLienzo, tiempos),
      destellos_1s_celda_max: destCeldas[peor], celda_peor: `fila ${Math.floor(peor / CELDAS)}, columna ${peor % CELDAS}`,
    };
    r.destello_lienzo_cumple = r.destellos_1s_lienzo_max <= DESTELLOS_MAX_1S;
    r.destello_celdas_cumple = r.destellos_1s_celda_max <= DESTELLOS_MAX_1S;
    window.__diagnostico = r;
    console.table(r);
    return r;
  }

  return { medir, esRojo, cambios, maxDestellos1s };
})();
