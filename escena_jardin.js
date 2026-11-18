// =====================================================================
// escena_jardin.js — US38, escena alternativa "Jardín de luz" (?escena=jardin; D-078, D-079).
// Sigue el prototipo de referencia prototipos_visual/jardin_de_luz.html (commit db2263a): cielo nocturno, 46 luciérnagas,
// 3 cintas de luz, una flor que respira, un anillo por nota y las últimas 24 notas como estrellas.
// Desvíos aprobados frente al prototipo (D-079 y tanda 1): anillos, estrellas, flor y cintas con el color de la ZONA
// (3 colores con fundido, HU0038-1); color continuo según `registro` solo en el cielo; halo de la flor precalculado
// (sin degradados nuevos por cuadro); el anillo entra en 0.2 s como en Ondas.
// Solo dibuja: no toca el audio ni el WebSocket. visual.js llama a alEstado (desde onmessage, solo guarda) y a dibujar
// (desde requestAnimationFrame). Coordenadas lógicas del prototipo: alto 720, ancho = 720 · ancho/alto real.
// =====================================================================
(() => {
  // ---------- Parámetros (LEÍDOS del prototipo) ----------
  const PALETA = { grave: [91, 141, 239], medio: [63, 197, 180], agudo: [183, 156, 242] };   // azul, turquesa, lavanda
  const CALIDO = [242, 207, 138];                       // acento cálido (luciérnagas, centro de la flor, última estrella)
  const CIELO = [[10, 18, 44], [8, 30, 40], [26, 20, 52]];
  const SOMBRA = "4,6,14";                              // el cielo se oscurece hacia abajo hasta mezclar 0.6 de este color
  const LINEA_MELODIA = "rgba(230,235,247,.18)";
  const H = 720;                                        // alto lógico del prototipo
  const N_LUCES = 46, MAX_ANILLOS = 40, MAX_ESTRELLAS = 24;
  const ENTRADA_S = 0.2;                                // aparición gradual del anillo, como en Ondas
  const NOTAS = ["Do", "Re", "Mi", "Fa", "Sol", "La", "Si"];
  const LADO_HALO = 256;                                // px del halo precalculado

  // ---------- Estado ----------
  let ctx = null, escala = 1, W = 1280;                 // W = ancho lógico
  let sombraCielo = null;
  const halos = {};
  const luces = [];
  const anillos = [], estrellas = [];
  const obj = { reg: 0.5, tempo: 0, amp: 0, open: 0.5, flu: 1 };   // objetivos (último estado de Python)
  const s = { ...obj };                                             // suavizados
  let vis = 0;                                                      // presencia suavizada (0 = sin cuerpo)
  let fundido = null;
  const tmp = [0, 0, 0];

  const mezclar = (A, B, k, out) => { for (let i = 0; i < 3; i++) out[i] = A[i] + (B[i] - A[i]) * k; return out; };
  const rgba = (c, a) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a.toFixed(3)})`;

  function cieloEn(r, out) {
    /* Color del cielo: continuo según registro (grave -> medio -> agudo), como el prototipo. */
    return r < 0.5 ? mezclar(CIELO[0], CIELO[1], r * 2, out) : mezclar(CIELO[1], CIELO[2], (r - 0.5) * 2, out);
  }

  function iniciar(contexto) {
    /* Guarda el contexto, crea el fundido de zona y los 3 halos (uno por zona) una sola vez. */
    ctx = contexto;
    fundido = Visual.fundidoZona(PALETA);
    for (const z of Object.keys(PALETA)) {
      const c = document.createElement("canvas");
      c.width = c.height = LADO_HALO;
      const g = c.getContext("2d"), m = LADO_HALO / 2;
      const gr = g.createRadialGradient(m, m, 0, m, m, m);
      gr.addColorStop(0, rgba(PALETA[z], 1)); gr.addColorStop(1, rgba(PALETA[z], 0));
      g.fillStyle = gr; g.fillRect(0, 0, LADO_HALO, LADO_HALO);
      halos[z] = c;
    }
  }

  function redimensionar(ancho, alto) {
    /* Escala lógica (alto 720) y la sombra del cielo, una vez por cambio de tamaño. Reubica las luciérnagas. */
    const Wantes = W;
    escala = alto / H; W = ancho / escala;
    if (luces.length === 0) {
      for (let i = 0; i < N_LUCES; i++) luces.push({ x: Math.random() * W, y: Math.random() * H, r: 1 + Math.random() * 2.2,
                                                    f: Math.random() * 6.283, v: 0.3 + Math.random() * 0.7 });
    } else for (const l of luces) l.x *= W / Wantes;
    sombraCielo = ctx.createLinearGradient(0, 0, 0, H);
    sombraCielo.addColorStop(0, `rgba(${SOMBRA},0)`); sombraCielo.addColorStop(1, `rgba(${SOMBRA},0.6)`);
  }

  function alEstado(d, esNota, t) {
    /* Solo guarda (se llama desde onmessage): objetivos, zona y, si hay nota nueva, su anillo y su estrella. */
    if (typeof d.registro === "number") obj.reg = d.registro;
    obj.tempo = d.tempo || 0;
    obj.amp = d.intensidad || 0;
    obj.open = (d.apertura01 === null || d.apertura01 === undefined) ? 0.5 : d.apertura01;   // sin mano: neutro
    obj.flu = typeof d.lam === "number" ? d.lam : obj.flu;
    if (d.zona) fundido.cambiar(d.zona, t);
    if (!esNota) return;
    const c = fundido.color(t);
    if (anillos.length >= MAX_ANILLOS) anillos.shift();
    anillos.push({ t0: t, c, tCap: d.t_cap_ms, nuevo: true, r0: 0, x: 0, y: 0 });
    const n = NOTAS.indexOf(d.nota);
    estrellas.push({ n: n < 0 ? 3 : n, c });
    if (estrellas.length > MAX_ESTRELLAS) estrellas.shift();
  }

  function dibujar(t, dt, sinCuerpo) {
    /* Un cuadro de la escena. Devuelve {vivos, llamadas, nuevas}: vivos cuenta como el contador del prototipo;
       nuevas = t_cap_ms de los anillos dibujados por primera vez (visual.js anota la latencia visual). */
    const nuevas = [];
    let vivos = 0, llamadas = 0;
    // Suavizado exponencial equivalente al del prototipo a 30 cuadros/s (0.06 registro, 0.12 el resto, 0.05 presencia)
    const k = (a) => 1 - Math.pow(1 - a, dt * 30);
    for (const key in obj) s[key] += (obj[key] - s[key]) * k(key === "reg" ? 0.06 : 0.12);
    vis += ((sinCuerpo ? 0 : 1) - vis) * k(0.05);
    const c = fundido.color(t);

    ctx.save();
    ctx.scale(escala, escala);

    // Cielo: relleno del color continuo y sombra precalculada hacia abajo (igual al degradado del prototipo)
    ctx.fillStyle = rgba(cieloEn(s.reg, tmp), 1); ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = sombraCielo; ctx.fillRect(0, 0, W, H);
    vivos++; llamadas += 2;

    // Luciérnagas
    for (const l of luces) {
      l.y -= (6 + 40 * s.tempo) * l.v * dt * vis; l.x += Math.sin(t * 0.6 + l.f) * 8 * dt;
      if (l.y < -10) { l.y = H + 10; l.x = Math.random() * W; }
      ctx.fillStyle = rgba(CALIDO, (0.18 + 0.25 * Math.sin(t * 1.3 + l.f) ** 2) * (0.35 + 0.65 * vis));
      ctx.beginPath(); ctx.arc(l.x, l.y, l.r, 0, 6.283); ctx.fill();
      vivos++; llamadas++;
    }

    // Cintas de luz: lisas si el movimiento es fluido (lam alto), rizadas si es brusco
    for (let j = 0; j < 3; j++) {
      ctx.beginPath();
      for (let x = 0; x <= W; x += 16) {
        const base = H * (0.58 + 0.11 * j), a = (18 + 46 * s.amp) * vis;
        const y = base + Math.sin(x * 0.006 + t * (0.35 + 1.1 * s.tempo) + j * 1.9) * a
                       + Math.sin(x * 0.035 + t * 3 + j) * (1 - s.flu) * 12 * vis;
        if (x) ctx.lineTo(x, y); else ctx.moveTo(x, y);
      }
      ctx.strokeStyle = rgba(c, 0.13 + 0.05 * j); ctx.lineWidth = 2 + j; ctx.stroke();
      vivos++; llamadas++;
    }

    // Flor: sube con el registro, crece con la intensidad, se abre con las manos y respira despacio
    const cx = W * 0.5, cy = H * (0.66 - 0.34 * s.reg), resp = 1 + 0.05 * Math.sin(t * 0.9);
    const R = (70 + 110 * s.amp) * resp * (0.55 + 0.45 * vis);
    const aHalo = 0.34 * (0.4 + 0.6 * vis), rh = R * 2.6, z = fundido.zonas(t);
    if (z.p < 1) { ctx.globalAlpha = aHalo * (1 - z.p); ctx.drawImage(halos[z.desde], cx - rh, cy - rh, 2 * rh, 2 * rh); llamadas++; }
    ctx.globalAlpha = aHalo * z.p; ctx.drawImage(halos[z.hacia], cx - rh, cy - rh, 2 * rh, 2 * rh); llamadas++;
    ctx.globalAlpha = 1;
    vivos++;
    for (let capa = 0; capa < 2; capa++) {
      ctx.beginPath();
      for (let i = 0; i <= 72; i++) {
        const th = i / 72 * 6.283, pet = Math.cos(th * 6 + t * 0.25 * (capa ? -1 : 1));
        const rr = R * (capa ? 0.62 : 1) * (1 + (0.08 + 0.34 * s.open) * pet) + (1 - s.flu) * 6 * Math.sin(th * 17 + t * 5);
        const x = cx + Math.cos(th) * rr, y = cy + Math.sin(th) * rr;
        if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y);
      }
      ctx.closePath();
      ctx.fillStyle = capa ? rgba(mezclar(c, CALIDO, 0.45, tmp), 0.5) : rgba(c, 0.22); ctx.fill();
      ctx.strokeStyle = rgba(c, 0.6); ctx.lineWidth = 1.5; ctx.stroke();
      vivos++; llamadas += 2;
    }

    // Anillos: uno por nota; nacen en la flor, crecen 90 px/s y se apagan en ~2 s (alfa 0.55 - 0.28/s)
    for (let i = anillos.length - 1; i >= 0; i--) if (0.55 - 0.28 * (t - anillos[i].t0) <= 0) anillos.splice(i, 1);
    ctx.lineWidth = 2;
    for (const a of anillos) {
      if (a.nuevo) { a.nuevo = false; a.r0 = R * 0.9; a.x = cx; a.y = cy; if (a.tCap !== undefined) nuevas.push(a.tCap); }
      const edad = t - a.t0;
      const alfa = (0.55 - 0.28 * edad) * Math.min(1, edad / ENTRADA_S);
      ctx.strokeStyle = rgba(a.c, Math.max(0, alfa));
      ctx.beginPath(); ctx.arc(a.x, a.y, a.r0 + 90 * edad, 0, 6.283); ctx.stroke();
      vivos++; llamadas++;
    }

    // Melodía: las últimas notas como estrellas unidas por una línea (la más reciente, cálida y más grande)
    const x0 = W * 0.08, paso = (W * 0.84) / (MAX_ESTRELLAS - 1), yBase = H * 0.9;
    if (estrellas.length > 0) {
      ctx.beginPath();
      estrellas.forEach((e, i) => { const x = x0 + i * paso, y = yBase - e.n * 11; if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y); });
      ctx.strokeStyle = LINEA_MELODIA; ctx.lineWidth = 1; ctx.stroke();
      vivos++; llamadas++;
    }
    estrellas.forEach((e, i) => {
      const ult = i === estrellas.length - 1;
      ctx.fillStyle = ult ? rgba(CALIDO, 1) : rgba(e.c, 0.4 + 0.5 * i / estrellas.length);
      ctx.beginPath(); ctx.arc(x0 + i * paso, yBase - e.n * 11, ult ? 5 : 3, 0, 6.283); ctx.fill();
      vivos++; llamadas++;
    });

    ctx.restore();
    return { vivos, llamadas, nuevas };
  }

  Visual.registrarEscena("jardin", { iniciar, redimensionar, alEstado, dibujar,
                                      colores: { PALETA, CALIDO, CIELO, SOMBRA, LINEA_MELODIA } });
})();
