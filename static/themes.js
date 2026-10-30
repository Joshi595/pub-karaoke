// Song themes for the TV. Each theme: { cls, start(el, ctl) -> { stop() } }.
// ctl.beat() is the music level 0..1, ctl.palette three CSS colours from the cover, ctl.seed the song slug.
window.THEMES = {};

const seedOf = s => { let h = 2166136261; for (const c of String(s)) h = Math.imul(h ^ c.charCodeAt(0), 16777619); return h >>> 0; };

// Most colourful palette entry, lifted so sung words glow against any background.
function vivid(palette, lightness = 64) {
  const hsl = palette.map(css => {
    const [r, g, b] = css.match(/\d+/g).map(n => n / 255);
    const max = Math.max(r, g, b), min = Math.min(r, g, b), l = (max + min) / 2, d = max - min;
    const s = d === 0 ? 0 : d / (1 - Math.abs(2 * l - 1));
    let h = 0;
    if (d) h = max === r ? ((g - b) / d) % 6 : max === g ? (b - r) / d + 2 : (r - g) / d + 4;
    return { h: (h * 60 + 360) % 360, s };
  });
  const best = hsl.reduce((a, b) => (b.s > a.s ? b : a));
  return best.s < 0.15 ? "hsl(45 90% 62%)" : `hsl(${Math.round(best.h)} ${Math.max(70, Math.round(best.s * 100))}% ${lightness}%)`;
}

// Runs a p5 sketch in instance mode on a small canvas; CSS scales it to the screen, which softens it for free.
function sketchTheme(cls, width, height, build, colours) {
  return {
    cls,
    start(el, ctl) {
      if (colours) Object.entries(colours(ctl)).forEach(([k, v]) => document.body.style.setProperty(k, v));
      const inst = new p5(p => {
        const seed = seedOf(ctl.seed);
        const draw = build(p, ctl);
        p.setup = () => {
          p.pixelDensity(1);
          p.createCanvas(width, height);
          p.frameRate(30);
          p.randomSeed(seed); p.noiseSeed(seed);
          if (draw.setup) draw.setup();
        };
        p.draw = () => draw.frame(ctl.beat());
      }, el);
      return { stop() { inst.remove(); } };
    },
  };
}

// cover: the album's own colours drifting like lava-lamp light.
THEMES.cover = sketchTheme("theme-cover", 320, 180, (p, ctl) => {
  const blobs = [];
  return {
    setup() {
      for (let i = 0; i < 7; i++) blobs.push({ c: p.color(ctl.palette[i % 3]), o: p.random(1000), r: p.random(70, 150) });
      blobs.forEach(b => b.c.setAlpha(170));
    },
    frame(beat) {
      p.background(10, 14, 12);
      p.drawingContext.filter = "blur(14px)";
      p.noStroke();
      const t = p.frameCount * 0.003;
      for (const b of blobs) {
        p.fill(b.c);
        p.circle(p.width * p.noise(b.o, t), p.height * p.noise(b.o + 40, t), b.r * (1 + beat * 0.5));
      }
      p.drawingContext.filter = "none";
      p.background(0, 0, 0, 70);  // keep the lyrics the brightest thing on screen
    },
  };
}, ctl => ({ "--sung": vivid(ctl.palette), "--accent": vivid(ctl.palette, 70) }));

// celtic: gold motes ride a three-armed (triskele) swirl while shamrocks drift up out of the dark green.
THEMES.celtic = sketchTheme("theme-celtic", 640, 360, p => {
  const motes = [], leaves = [];
  const shamrock = (x, y, s, a) => {
    p.push(); p.translate(x, y); p.rotate(a);
    for (let k = 0; k < 3; k++) { p.rotate(p.TWO_PI / 3); p.circle(s * 0.2, -s * 0.42, s * 0.5); p.circle(-s * 0.2, -s * 0.42, s * 0.5); }
    p.rect(-s * 0.05, 0, s * 0.1, s * 0.8, s * 0.05);
    p.pop();
  };
  return {
    setup() {
      for (let i = 0; i < 260; i++) motes.push({ x: p.random(p.width), y: p.random(p.height), a: p.random(80, 200) });
      for (let i = 0; i < 9; i++) leaves.push({ x: p.random(p.width), y: p.random(p.height), s: p.random(14, 34), r: p.random(p.TWO_PI), v: p.random(0.15, 0.4) });
    },
    frame(beat) {
      p.background(7, 33, 22, 60);
      const cx = p.width / 2, cy = p.height / 2;
      p.noStroke();
      for (const m of motes) {
        const ang = Math.atan2(m.y - cy, m.x - cx), d = p.dist(m.x, m.y, cx, cy);
        const swirl = ang + p.HALF_PI + 0.6 * Math.sin(3 * ang + d * 0.02);  // three arms
        const sp = 0.5 + beat * 2;
        m.x += Math.cos(swirl) * sp; m.y += Math.sin(swirl) * sp;
        if (d > p.width * 0.6 || p.random() < 0.002) { m.x = cx + p.random(-40, 40); m.y = cy + p.random(-40, 40); }
        p.fill(230, 190, 90, m.a * (0.5 + beat)); p.circle(m.x, m.y, 1.6 + beat * 1.5);
      }
      p.fill(40, 140, 80, 110);
      for (const l of leaves) {
        l.y -= l.v * (1 + beat * 2); l.r += 0.004;
        if (l.y < -40) { l.y = p.height + 40; l.x = p.random(p.width); }
        shamrock(l.x, l.y, l.s * (1 + beat * 0.15), l.r);
      }
    },
  };
}, () => ({ "--sung": "#E9C46A", "--accent": "#E9C46A" }));

// neon80s: a sun sliced by scanlines sets over a grid that rushes toward you faster on the beat.
THEMES.neon80s = sketchTheme("theme-neon80s", 640, 360, p => {
  let z = 0;
  return {
    frame(beat) {
      const horizon = p.height * 0.58;
      p.noStroke();
      for (let y = 0; y < horizon; y += 4) { p.fill(p.lerpColor(p.color(20, 6, 48), p.color(140, 30, 110), y / horizon)); p.rect(0, y, p.width, 4); }
      p.fill(10, 4, 30); p.rect(0, horizon, p.width, p.height - horizon);
      const r = 95 + beat * 10;
      for (let y = -r; y < 0; y += 2) {
        const k = (y + r) / r;  // 0 at the top of the sun, 1 at the horizon
        if (k > 0.45 && Math.sin(y * 0.5) > 1.6 - k * 1.6) continue;  // scanline gaps widen toward the horizon
        const w = Math.sqrt(r * r - y * y);
        p.fill(p.lerpColor(p.color(255, 210, 90), p.color(255, 60, 150), k)); p.rect(p.width / 2 - w, horizon + y, w * 2, 2);
      }
      z = (z + 0.012 + beat * 0.05) % 1;
      p.drawingContext.shadowBlur = 8 + beat * 18; p.drawingContext.shadowColor = "#ff3fbf";
      p.stroke(255, 70, 200); p.strokeWeight(1.4);
      for (let i = 0; i < 14; i++) { const d = (i + z) / 14, y = horizon + (p.height - horizon) * d * d; p.line(0, y, p.width, y); }
      for (let i = -16; i <= 16; i++) p.line(p.width / 2 + i * 6, horizon, p.width / 2 + i * 60, p.height);
      p.drawingContext.shadowBlur = 0;
    },
  };
}, () => ({ "--sung": "#FF4FD8", "--accent": "#3FF0FF", "--title-font": "Orbitron, sans-serif" }));

// disco: a mirror ball turns overhead and throws light spots across the room; glitter pops on loud beats.
THEMES.disco = sketchTheme("theme-disco", 640, 360, (p, ctl) => {
  const facets = [], glitter = [];
  let tint;
  return {
    setup() {
      tint = [p.color(255, 120, 200), p.color(255, 210, 120), p.color(ctl.palette[0]), p.color(150, 140, 255)];
      for (let i = 0; i < 90; i++) facets.push({ lat: p.random(-1.2, 1.2), lon: p.random(p.TWO_PI), c: p.random(tint) });
    },
    frame(beat) {
      p.background(22, 6, 30, 90);
      const spin = p.frameCount * 0.006;
      p.blendMode(p.ADD); p.noStroke();
      for (const f of facets) {
        const lon = f.lon + spin, x = Math.cos(f.lat) * Math.sin(lon), y = Math.sin(f.lat), front = Math.cos(f.lat) * Math.cos(lon);
        if (front < 0) continue;
        p.fill(p.red(f.c), p.green(f.c), p.blue(f.c), 40 + 90 * front * (0.6 + beat));
        p.circle(p.width / 2 + x * p.width * 0.75, p.height * 0.45 + y * p.height * 0.7, 10 + 22 * front);
      }
      if (beat > 0.35) for (let i = 0; i < 6; i++) glitter.push({ x: p.random(p.width), y: p.random(p.height), life: 1 });
      for (const g of glitter) { p.fill(255, 255, 255, 255 * g.life); p.rect(g.x, g.y, 2, 2); g.life -= 0.05; }
      while (glitter.length && glitter[0].life <= 0) glitter.shift();
      p.blendMode(p.BLEND);
      p.fill(200); p.circle(p.width / 2, 0, 46);  // the ball itself
    },
  };
}, () => ({ "--sung": "#FF6EC7", "--accent": "#FFD36E" }));

// rock: embers climb out of the dark with smoke curling behind them; a hit on the beat stokes the fire.
THEMES.rock = sketchTheme("theme-rock", 320, 180, p => {
  const embers = [];
  return {
    setup() { for (let i = 0; i < 160; i++) embers.push({ x: p.random(p.width), y: p.random(p.height), v: p.random(0.3, 1.2), h: p.random(1000) }); },
    frame(beat) {
      p.background(12, 6, 4, 70);
      p.noStroke();
      const t = p.frameCount * 0.01;
      for (let i = 0; i < 6; i++) { p.fill(60, 50, 50, 18); p.circle(p.width * p.noise(i, t * 0.3), p.height * (0.4 + 0.6 * p.noise(i + 9, t * 0.2)), 120); }
      p.fill(120, 20, 0, 30 + 60 * beat); p.rect(0, p.height - 30, p.width, 30);
      for (const e of embers) {
        e.y -= e.v * (1 + beat * 3); e.x += (p.noise(e.h, e.y * 0.02) - 0.5) * 1.6;
        if (e.y < -5) { e.y = p.height + 5; e.x = p.random(p.width); }
        const heat = e.y / p.height;
        p.fill(255, 120 + 120 * heat, 30, 120 + 135 * heat * (0.5 + beat)); p.circle(e.x, e.y, 1 + heat * 1.6);
      }
    },
  };
}, () => ({ "--sung": "#FF7A1A", "--accent": "#FFB000", "--lyric-font": "Oswald, sans-serif", "--lyric-transform": "uppercase", "--title-font": "Oswald, sans-serif" }));

// ballad: a slow sky; stars breathe, a warm candle glow rises with the voice, now and then a star falls.
THEMES.ballad = sketchTheme("theme-ballad", 640, 360, p => {
  const stars = [];
  let shooting = null;
  return {
    setup() { for (let i = 0; i < 320; i++) stars.push({ x: p.random(p.width), y: p.random(p.height), s: p.random(0.6, 1.8), ph: p.random(p.TWO_PI) }); },
    frame(beat) {
      p.background(6, 10, 28);
      p.noStroke();
      const t = p.frameCount * 0.02;
      for (const s of stars) { s.x = (s.x + 0.03) % p.width; p.fill(230, 230, 255, 120 + 120 * Math.sin(t + s.ph)); p.circle(s.x, s.y, s.s); }
      const g = p.drawingContext.createRadialGradient(p.width / 2, p.height * 1.05, 10, p.width / 2, p.height * 1.05, 260 + beat * 80);
      g.addColorStop(0, `rgba(255,170,80,${0.35 + beat * 0.3})`); g.addColorStop(1, "rgba(255,170,80,0)");
      p.drawingContext.fillStyle = g; p.drawingContext.fillRect(0, 0, p.width, p.height);
      if (!shooting && p.random() < 0.004) shooting = { x: p.random(p.width), y: p.random(p.height * 0.4), life: 1 };
      if (shooting) {
        p.stroke(255, 255, 255, 255 * shooting.life); p.strokeWeight(1.2);
        p.line(shooting.x, shooting.y, shooting.x - 30, shooting.y - 12); p.noStroke();
        shooting.x += 6; shooting.y += 2.4; shooting.life -= 0.03;
        if (shooting.life <= 0) shooting = null;
      }
    },
  };
}, () => ({ "--sung": "#FFC98B", "--accent": "#FFC98B", "--title-font": "Fell, Georgia, serif" }));

// pop: candy-coloured blobs bounce to the beat while confetti tumbles down.
THEMES.pop = sketchTheme("theme-pop", 640, 360, (p, ctl) => {
  const blobs = [], confetti = [];
  const cols = ["#FF5D8F", "#FFD23F", "#3BCEAC", "#5E7BFF", ...ctl.palette];
  return {
    setup() {
      for (let i = 0; i < 6; i++) blobs.push({ x: p.random(p.width), y: p.random(p.height), vx: p.random(-1, 1), vy: p.random(-1, 1), r: p.random(90, 170), c: p.color(p.random(cols)) });
      for (let i = 0; i < 120; i++) confetti.push({ x: p.random(p.width), y: p.random(p.height), r: p.random(p.TWO_PI), c: p.color(p.random(cols)), v: p.random(0.5, 1.5) });
      blobs.forEach(b => b.c.setAlpha(150));
    },
    frame(beat) {
      p.background(24, 10, 40);
      p.noStroke();
      p.drawingContext.filter = "blur(30px)";
      for (const b of blobs) {
        b.x += b.vx * (1 + beat * 3); b.y += b.vy * (1 + beat * 3);
        if (b.x < 0 || b.x > p.width) b.vx *= -1;
        if (b.y < 0 || b.y > p.height) b.vy *= -1;
        p.fill(b.c); p.circle(b.x, b.y, b.r * (1 + beat * 0.3));
      }
      p.drawingContext.filter = "none";
      for (const c of confetti) {
        c.y += c.v; c.r += 0.05;
        if (c.y > p.height + 5) { c.y = -5; c.x = p.random(p.width); }
        p.push(); p.translate(c.x, c.y); p.rotate(c.r); p.fill(c.c); p.rect(-3, -1.5, 6 * Math.abs(Math.cos(c.r)), 3); p.pop();
      }
    },
  };
}, () => ({ "--sung": "#FFD23F", "--accent": "#FF5D8F", "--lyric-font": "Fredoka, sans-serif", "--lyric-weight": "600", "--title-font": "Fredoka, sans-serif" }));

// How each theme shows its lyrics, not just its background; staff can override both on the admin page.
Object.entries({
  cover: ["classic", "wipe"], celtic: ["ball", "wipe"], neon80s: ["classic", "glow"], disco: ["classic", "pop"],
  rock: ["bigline", "pop"], ballad: ["scroll", "glow"], pop: ["classic", "pop"],
}).forEach(([name, [layout, highlight]]) => Object.assign(THEMES[name], { layout, highlight }));
