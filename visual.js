// =====================================================================
// visual.js — US38 "Ondas": retroalimentación visual en Canvas 2D (sin WebGL, sin blur ni sombras).
// No toca el audio ni el WebSocket: index.html le pasa cada estado con Visual.alRecibirEstado (desde onmessage,
// que solo guarda) y TODO el dibujo ocurre en requestAnimationFrame (CLAUDE.md regla 12).
// Mide (C6, HU0038-5): "tiempo por cuadro" = trabajo de dibujo dentro de cada requestAnimationFrame (objetivo p95
// <= 16.7 ms) y, aparte, el intervalo entre cuadros (sin objetivo), en resúmenes por lote de ~1 s (filas
// "cuadro_trabajo" y "cuadro_intervalo", ver filaLote); y "latencia visual" = de t_cap_ms a la
// llamada que dibuja por primera vez el anillo de esa nota (fila tipo "visual"; no incluye la composición ni la pantalla).
// =====================================================================
const Visual = (() => {
  // ---------- Parámetros ----------
  const COLOR_ZONA = { grave: [79, 163, 181], medio: [156, 139, 224], agudo: [242, 178, 122] };  // #4FA3B5 #9C8BE0 #F2B27A
  const NOMBRE_ZONA = { grave: "grave", medio: "media", agudo: "aguda" };  // texto: el color no es la única señal
  const COLOR_AVISO = "232, 176, 74";       // ámbar del marco sin cuerpo (sin rojo)
  const MAX_VIVOS = 200;                    // tope de elementos vivos (HU0038-4)
  const VIDA_ANILLO_S = 3.0;                // el anillo crece y se desvanece en ~3 s
  const ENTRADA_S = 0.2;                    // aparición gradual: sin cambio brusco de luz
  const FUNDIDO_COLOR_S = 0.4;              // fundido de color al cambiar de zona (P-013, Ale 10/11)
  const PUNTOS = 48;                        // vértices del polígono de cada anillo
  const ONDULACION_MAX = 0.12;              // radio relativo del ruido cuando lam = 0
  const SIN_CUERPO_MS = 500;                // sin mensajes durante esto = no hay cuerpo (Python solo envía con cuerpo)
  const TAU_FONDO_S = 3.0;                  // suavizado del fondo (varios segundos)
  const FONDO = [11, 14, 22];               // fondo oscuro

  // ---------- Estado ----------
  let canvas = null, ctx = null, ancho = 0, alto = 0;
  let anotar = null, medir = () => false;  // los da index.html: escribir una fila en _latencias.csv y si toca medir
  let ultimo = null, tUltimoMsg = -Infinity, conectado = false;
  const anillos = [];
  let zonaActual = "medio", colorDesde = COLOR_ZONA.medio, colorHacia = COLOR_ZONA.medio, tCambioColor = -Infinity;
  let tempoSuav = 0, intSuav = 0, fase = 0, tPrevCuadro = null, tAvisoCambio = 0, sinCuerpoPrev = true;
  const COS = [], SIN = [];
  for (let i = 0; i < PUNTOS; i++) { COS.push(Math.cos(2 * Math.PI * i / PUNTOS)); SIN.push(Math.sin(2 * Math.PI * i / PUNTOS)); }

  function iniciar(elCanvas, opciones) {
    /* Prepara el canvas a pantalla completa y arranca el bucle de requestAnimationFrame.
       opciones.anotar(fila): guarda una fila en _latencias.csv (la función anotar de index.html).
       opciones.medir(): true si hay que registrar filas (WebSocket abierto y audio iniciado; nunca en ?demo=1). */
    canvas = elCanvas; ctx = canvas.getContext("2d");
    anotar = opciones.anotar; medir = opciones.medir;
    ajustarTamano();
    window.addEventListener("resize", ajustarTamano);
    requestAnimationFrame(cuadro);
  }

  function ajustarTamano() {
    const dpr = window.devicePixelRatio || 1;
    ancho = window.innerWidth; alto = window.innerHeight;
    canvas.width = Math.round(ancho * dpr); canvas.height = Math.round(alto * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function ponerConexion(abierta) { conectado = abierta; }

  function colorEn(t) {
    /* Color de zona en el instante t (s), con fundido lineal de FUNDIDO_COLOR_S desde el color anterior. */
    const p = Math.min(1, Math.max(0, (t - tCambioColor) / FUNDIDO_COLOR_S));
    return colorDesde.map((c, i) => c + (colorHacia[i] - c) * p);
  }

  function alRecibirEstado(d, esNota) {
    /* Se llama desde ws.onmessage (o desde la demo): SOLO guarda el estado; no dibuja.
       Si cambió la zona, empieza el fundido de color; si hay nota nueva, crea su anillo. */
    const t = performance.now() / 1000;
    ultimo = d; tUltimoMsg = performance.now();
    if (d.zona && d.zona !== zonaActual && COLOR_ZONA[d.zona]) {
      colorDesde = colorEn(t); colorHacia = COLOR_ZONA[d.zona]; tCambioColor = t; zonaActual = d.zona;
    }
    if (esNota) nuevoAnillo(d, t);
  }

  function nuevoAnillo(d, t) {
    /* Un anillo por nota: color de la zona (con fundido), grosor y brillo = intensidad, borde nítido/suave = apertura01
       (null -> neutro 0.5), ondulación = 1 - lam. Si se llega a MAX_VIVOS se quita el más viejo. */
    if (anillos.length >= MAX_VIVOS) anillos.shift();
    const ap = (d.apertura01 === null || d.apertura01 === undefined) ? 0.5 : d.apertura01;
    anillos.push({
      t0: t, color: colorEn(t), intensidad: d.intensidad || 0, apertura: ap,
      ondulacion: ONDULACION_MAX * (1 - Math.min(1, Math.max(0, d.lam || 0))),
      f1: Math.random() * 6.283, f2: Math.random() * 6.283, tCap: d.t_cap_ms, dibujado: false,
    });
  }

  function cuadro(ts) {
    /* Bucle de requestAnimationFrame: suaviza fondo, dibuja fondo, anillos e indicador, borra los anillos muertos
       y mide el trabajo de dibujo de este cuadro y el intervalo desde el anterior. */
    const tIni = performance.now();
    const t = tIni / 1000;
    const dt = tPrevCuadro === null ? 0 : Math.min(0.1, (ts - tPrevCuadro) / 1000);
    const sinCuerpo = !conectado || (tIni - tUltimoMsg) > SIN_CUERPO_MS;
    if (sinCuerpo !== sinCuerpoPrev) { tAvisoCambio = t; sinCuerpoPrev = sinCuerpo; }

    // Fondo que respira: tempo e intensidad suavizados (tau 3 s); sin cuerpo vuelve despacio a reposo
    const k = 1 - Math.exp(-dt / TAU_FONDO_S);
    tempoSuav += ((sinCuerpo || !ultimo ? 0 : ultimo.tempo || 0) - tempoSuav) * k;
    intSuav += ((sinCuerpo || !ultimo ? 0 : ultimo.intensidad || 0) - intSuav) * k;
    fase += dt * 2 * Math.PI * (0.08 + 0.17 * tempoSuav);            // un respiro cada 12 s (quieto) a 4 s (rápido)
    dibujarFondo(t);

    // Anillos (los muertos se quitan; el dibujo marca la latencia visual de cada uno la primera vez)
    for (let i = anillos.length - 1; i >= 0; i--) if (t - anillos[i].t0 > VIDA_ANILLO_S) anillos.splice(i, 1);
    const registrar = medir();
    for (const a of anillos) {
      dibujarAnillo(a, t);
      if (!a.dibujado) {
        a.dibujado = true;
        if (registrar && a.tCap !== undefined) anotar([Date.now(), "visual", (Date.now() - a.tCap).toFixed(1), "", "", "", ""]);
      }
    }
    dibujarIndicador(t, sinCuerpo);

    const trabajo = performance.now() - tIni;
    if (tPrevCuadro !== null) { hist.trabajo[hist.i % HIST] = trabajo; hist.intervalo[hist.i % HIST] = ts - tPrevCuadro; hist.i++; }
    if (registrar && tPrevCuadro !== null) { lote.trabajo.push(trabajo); lote.intervalo.push(ts - tPrevCuadro); }
    if (tIni - lote.t0 >= LOTE_MS) {
      if (registrar && lote.trabajo.length > 0) {
        anotar(filaLote("cuadro_trabajo", lote.trabajo));
        anotar(filaLote("cuadro_intervalo", lote.intervalo));
      }
      lote.trabajo = []; lote.intervalo = []; lote.t0 = tIni;      // sin medir, el lote se descarta
    }
    tPrevCuadro = ts;
    requestAnimationFrame(cuadro);
  }

  // Resumen por lote de ~1 s para _latencias.csv (Ale, 10/11: no una fila por cuadro). Dos filas por lote:
  // tipo "cuadro_trabajo" y "cuadro_intervalo", con latencia_ms = media, transporte_ms = p95,
  // output_latency_ms = máximo y base_latency_ms = n (cuadros del lote). El p95 de toda la corrida se aproxima offline.
  const LOTE_MS = 1000;
  const lote = { trabajo: [], intervalo: [], t0: performance.now() };
  function filaLote(tipo, valores) {
    const v = [...valores].sort((a, b) => a - b), n = v.length;
    const media = v.reduce((s, x) => s + x, 0) / n;
    return [Date.now(), tipo, media.toFixed(2), v[Math.floor(0.95 * (n - 1))].toFixed(2), v[n - 1].toFixed(2), String(n), ""];
  }

  // Últimos HIST cuadros en memoria, para revisar en la consola sin Python (Visual.estadisticas(); también en ?demo=1)
  const HIST = 1800;
  const hist = { trabajo: new Float32Array(HIST), intervalo: new Float32Array(HIST), i: 0 };
  function estadisticas() {
    /* {n, trabajo: {media, p95, max}, intervalo: {...}, vivos} de los últimos HIST cuadros (ms). Solo diagnóstico. */
    const n = Math.min(hist.i, HIST);
    const resumen = (arr) => {
      const v = Array.from(arr.subarray(0, n)).sort((a, b) => a - b);
      return { media: +(v.reduce((s, x) => s + x, 0) / n).toFixed(2), p95: +v[Math.floor(0.95 * (n - 1))].toFixed(2),
               max: +v[n - 1].toFixed(2) };
    };
    return n === 0 ? { n } : { n, trabajo: resumen(hist.trabajo), intervalo: resumen(hist.intervalo), vivos: anillos.length };
  }

  function dibujarFondo(t) {
    /* Fondo oscuro con un halo central del color de la zona; brillo y tamaño cambian lento y poco (sin destellos). */
    ctx.fillStyle = `rgb(${FONDO.join(",")})`;
    ctx.fillRect(0, 0, ancho, alto);
    const respiro = 0.5 + 0.5 * Math.sin(fase);
    const alfa = 0.05 + 0.07 * intSuav + 0.03 * respiro;
    const radio = Math.max(ancho, alto) * (0.35 + 0.08 * respiro + 0.1 * intSuav);
    const c = colorEn(t).map(Math.round).join(",");
    const g = ctx.createRadialGradient(ancho / 2, alto / 2, 0, ancho / 2, alto / 2, radio);
    g.addColorStop(0, `rgba(${c},${alfa.toFixed(3)})`);
    g.addColorStop(1, `rgba(${c},0)`);
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, ancho, alto);
  }

  function dibujarAnillo(a, t) {
    /* Polígono de PUNTOS vértices con ruido suave (redondo si lam = 1, ondulado si lam baja); 1 trazo nítido si la
       mano está abierta, hasta 3 trazos con alfa decreciente si está cerrada. Aparece en ENTRADA_S y se desvanece. */
    const edad = t - a.t0, p = edad / VIDA_ANILLO_S;
    const entrada = Math.min(1, edad / ENTRADA_S);
    const alfaBase = (0.35 + 0.55 * a.intensidad) * entrada * Math.pow(1 - p, 1.5);
    if (alfaBase <= 0.003) return;
    const rMax = 0.48 * Math.min(ancho, alto);
    const r = 8 + (rMax - 8) * (1 - Math.pow(1 - p, 2));             // crece rápido al inicio y frena
    const grosor = 1.5 + 6 * a.intensidad;
    const trazos = 1 + Math.round(2 * (1 - a.apertura));
    const separacion = grosor * (0.6 + 1.2 * (1 - a.apertura));
    const cx = ancho / 2, cy = alto / 2, col = a.color.map(Math.round).join(",");
    for (let k = 0; k < trazos; k++) {
      const desp = k === 0 ? 0 : Math.ceil(k / 2) * separacion * (k % 2 ? 1 : -1);
      ctx.strokeStyle = `rgba(${col},${(alfaBase * Math.pow(0.45, k)).toFixed(3)})`;
      ctx.lineWidth = k === 0 ? grosor : grosor * 0.7;
      ctx.beginPath();
      for (let i = 0; i < PUNTOS; i++) {
        const th = 2 * Math.PI * i / PUNTOS;
        const ruido = 0.6 * Math.sin(3 * th + a.f1 + 0.6 * t) + 0.4 * Math.sin(5 * th + a.f2 - 0.4 * t);
        const R = Math.max(1, r * (1 + a.ondulacion * ruido) + desp);
        if (i === 0) ctx.moveTo(cx + R * COS[i], cy + R * SIN[i]); else ctx.lineTo(cx + R * COS[i], cy + R * SIN[i]);
      }
      ctx.closePath();
      ctx.stroke();
    }
  }

  function dibujarIndicador(t, sinCuerpo) {
    /* "Te veo" (círculo lleno) / "No te veo" (círculo vacío) y la zona en texto. Sin cuerpo: marco punteado ámbar y
       mensaje amable, que aparecen y desaparecen en 0.4 s. Sin conexión con Python: "Conectando…". */
    const transicion = Math.min(1, (t - tAvisoCambio) / 0.4);
    const aviso = sinCuerpo ? transicion : 1 - transicion;
    ctx.font = "600 20px system-ui, sans-serif";
    ctx.textBaseline = "middle";
    ctx.fillStyle = "rgba(235,238,245,0.9)";
    ctx.strokeStyle = "rgba(235,238,245,0.9)";
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(34, 34, 8, 0, 2 * Math.PI);
    if (sinCuerpo) ctx.stroke(); else ctx.fill();
    ctx.fillText(!conectado ? "Conectando…" : (sinCuerpo ? "No te veo" : "Te veo"), 52, 35);
    if (!sinCuerpo) {
      ctx.font = "500 18px system-ui, sans-serif";
      ctx.fillStyle = "rgba(235,238,245,0.75)";
      ctx.fillText(`Zona: ${NOMBRE_ZONA[zonaActual]}`, 26, alto - 30);
    }
    if (aviso > 0.01) {
      ctx.save();
      ctx.setLineDash([14, 10]);
      ctx.lineWidth = 4;
      ctx.strokeStyle = `rgba(${COLOR_AVISO},${(0.8 * aviso).toFixed(3)})`;
      ctx.strokeRect(16, 16, ancho - 32, alto - 32);
      ctx.restore();
      ctx.textAlign = "center";
      const tam = Math.round(Math.min(28, ancho / 22));                // cabe en pantallas estrechas
      ctx.font = `500 ${tam}px system-ui, sans-serif`;
      ctx.fillStyle = `rgba(245,240,230,${(0.9 * aviso).toFixed(3)})`;
      const lineas = conectado ? ["Ponte de pie frente a la cámara", "para crear música con tu cuerpo"]
                               : ["Esperando al sistema…"];
      lineas.forEach((l, i) => ctx.fillText(l, ancho / 2, alto / 2 + (i - (lineas.length - 1) / 2) * tam * 1.4));
      ctx.textAlign = "start";
    }
  }

  function iniciarDemo(alEstado) {
    /* ?demo=1: estados falsos a 30 Hz para probar el visual (y el sonido) sin Kinect ni Python. No abre el WebSocket,
       así que nunca es un segundo cliente. Cada 25 s simula 4 s sin cuerpo (deja de enviar) y cada 20 s, 2 s sin manos. */
    const notas = ["Do", "Re", "Mi", "Fa", "Sol", "La", "Si"];
    const zonas = ["grave", "medio", "agudo"];
    const t0 = performance.now() / 1000;
    let notaId = 0, tProx = 0, iNota = 0;
    ponerConexion(true);
    setInterval(() => {
      const s = performance.now() / 1000 - t0;
      if (s % 25 > 21) return;                                       // sin cuerpo: Python no envía nada
      const tempo = 0.5 + 0.5 * Math.sin(s / 7), intervalo = 1 / (1 + 3 * tempo);
      if (s >= tProx) { notaId++; iNota = (iNota + 1 + Math.floor(Math.random() * 2)) % 7; tProx = s + intervalo; }
      const zona = zonas[Math.floor(s / 6) % 3];
      alEstado({
        nota: notas[iNota], octava: { grave: 3, medio: 4, agudo: 5 }[zona], nota_id: notaId,
        intervalo_s: intervalo, lam: 0.5 + 0.5 * Math.sin(s / 11), tempo, zona,
        intensidad: 0.5 + 0.5 * Math.sin(s / 5), apertura01: (s % 20 > 18) ? null : 0.5 + 0.5 * Math.sin(s / 3),
        t_cap_ms: Date.now() - 25,
      });
    }, 1000 / 30);
  }

  return { iniciar, ponerConexion, alRecibirEstado, iniciarDemo, estadisticas };
})();
