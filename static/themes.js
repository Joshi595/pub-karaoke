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
// ctl.banner: a strip on a phone (look.js), slower, and leaving the page's own colours alone.
function sketchTheme(cls, width, height, build, colours) {
  return {
    cls,
    start(el, ctl) {
      if (colours && !ctl.banner) Object.entries(colours(ctl)).forEach(([k, v]) => document.body.style.setProperty(k, v));
      const reduced = matchMedia("(prefers-reduced-motion: reduce)");
      const inst = new p5(p => {
        const seed = seedOf(ctl.seed);
        const draw = build(p, ctl);
        p.setup = () => {
          p.pixelDensity(1);
          p.createCanvas(width, height);
          p.frameRate(ctl.banner ? 20 : 30);
          p.randomSeed(seed); p.noiseSeed(seed);
          if (draw.setup) draw.setup();
          if (reduced.matches) p.noLoop();
        };
        p.draw = () => draw.frame(ctl.beat());
      }, el);
      const change = () => { if (reduced.matches) { inst.redraw(); inst.noLoop(); } else inst.loop(); };
      reduced.addEventListener("change", change);
      return { stop() { reduced.removeEventListener("change", change); inst.remove(); }, pause(on) { on || reduced.matches ? inst.noLoop() : inst.loop(); } };
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

// halloween: bats cross a full moon, fog creeps over the hills and the jack-o'-lanterns flicker with the music.
// It shares its name with the Halloween look, so that look shows it for the lobby and every song (tv.js).
THEMES.halloween = sketchTheme("theme-halloween", 640, 360, p => {
  const bats = [], fog = [], ridge = [], lanterns = [];
  const ridgeAt = x => ridge[Math.min(ridge.length - 1, Math.round(x / 8))];
  const bat = (x, y, s, flap) => {
    const w = Math.sin(flap) * s * 0.6;  // wingtips rise and fall
    p.beginShape();
    p.vertex(x, y - s * 0.1);
    p.vertex(x - s * 0.5, y - s * 0.2 - w); p.vertex(x - s, y - w * 1.3); p.vertex(x - s * 0.7, y + s * 0.1); p.vertex(x - s * 0.35, y + s * 0.05);
    p.vertex(x, y + s * 0.25);
    p.vertex(x + s * 0.35, y + s * 0.05); p.vertex(x + s * 0.7, y + s * 0.1); p.vertex(x + s, y - w * 1.3); p.vertex(x + s * 0.5, y - s * 0.2 - w);
    p.endShape(p.CLOSE);
  };
  const lantern = (x, y, s, glow) => {
    const g = p.drawingContext, halo = g.createRadialGradient(x, y, s * 0.3, x, y, s * 1.8);  // candlelight on the grass
    halo.addColorStop(0, `rgba(255,150,40,${0.35 * glow})`); halo.addColorStop(1, "rgba(255,150,40,0)");
    g.fillStyle = halo; g.fillRect(x - s * 1.8, y - s * 1.8, s * 3.6, s * 3.6);
    p.fill(214, 98, 18);
    p.ellipse(x - s * 0.3, y, s * 0.75, s * 0.9); p.ellipse(x + s * 0.3, y, s * 0.75, s * 0.9); p.ellipse(x, y, s * 0.85, s);
    p.fill(70, 90, 30); p.rect(x - s * 0.06, y - s * 0.62, s * 0.12, s * 0.2, 2);
    p.fill(255, 214, 90, 110 + 145 * glow);
    p.triangle(x - s * 0.36, y - s * 0.05, x - s * 0.12, y - s * 0.05, x - s * 0.24, y - s * 0.28);
    p.triangle(x + s * 0.36, y - s * 0.05, x + s * 0.12, y - s * 0.05, x + s * 0.24, y - s * 0.28);
    p.arc(x, y + s * 0.06, s * 0.62, s * 0.36, 0, p.PI, p.CHORD);  // the grin
  };
  return {
    setup() {
      for (let x = 0; x <= p.width + 8; x += 8) ridge.push(p.height * 0.84 + (p.noise(x * 0.006) - 0.5) * 60);
      for (let i = 0; i < 8; i++) bats.push({ x: p.random(p.width), y: p.random(30, p.height * 0.5), s: p.random(7, 14), v: p.random(0.6, 1.4), ph: p.random(p.TWO_PI) });
      for (let i = 0; i < 6; i++) fog.push({ o: p.random(1000), r: p.random(120, 220) });
      for (const x of [70, 230, 420, 570]) { const s = p.random(22, 32); lanterns.push({ x, y: ridgeAt(x) - s * 0.25, s, o: p.random(1000) }); }
    },
    frame(beat) {
      const g = p.drawingContext, t = p.frameCount * 0.01;
      const sky = g.createLinearGradient(0, 0, 0, p.height);
      sky.addColorStop(0, "#1d0f2e"); sky.addColorStop(0.6, "#2a1236"); sky.addColorStop(1, "#0b0610");
      g.fillStyle = sky; g.fillRect(0, 0, p.width, p.height);
      const mx = p.width * 0.78, my = p.height * 0.24, r = 44;
      const halo = g.createRadialGradient(mx, my, r * 0.9, mx, my, r * (2.6 + beat * 0.8));
      halo.addColorStop(0, `rgba(255,236,190,${0.3 + beat * 0.25})`); halo.addColorStop(1, "rgba(255,236,190,0)");
      g.fillStyle = halo; g.fillRect(0, 0, p.width, p.height);
      p.noStroke();
      p.fill(246, 236, 212); p.circle(mx, my, r * 2);
      p.fill(226, 212, 186); p.circle(mx - 14, my - 8, 16); p.circle(mx + 12, my + 12, 11); p.circle(mx + 6, my - 18, 7);
      p.fill(8, 4, 12);
      for (const b of bats) {
        b.x += b.v * (1 + beat * 1.5);
        if (b.x > p.width + 20) { b.x = -20; b.y = p.random(30, p.height * 0.5); }
        bat(b.x, b.y + Math.sin(p.frameCount * 0.03 + b.ph) * 8, b.s, p.frameCount * (0.35 + beat * 0.3) + b.ph);
      }
      g.filter = "blur(18px)";
      p.fill(150, 120, 170, 38);
      for (const f of fog) p.circle(p.width * p.noise(f.o, t * 0.3), p.height * (0.68 + 0.25 * p.noise(f.o + 50, t * 0.3)), f.r);
      g.filter = "none";
      p.fill(8, 4, 12);
      p.beginShape(); p.vertex(0, p.height);
      ridge.forEach((y, i) => p.vertex(i * 8, y));
      p.vertex(p.width, p.height); p.endShape(p.CLOSE);
      for (const l of lanterns) lantern(l.x, l.y, l.s, Math.max(0, Math.min(1, 0.55 + 0.45 * beat + (p.noise(l.o, t * 8) - 0.5) * 0.5)));
    },
  };
}, () => ({ "--sung": "#FF8A1F", "--accent": "#FF7A1A", "--title-font": "Creepster, Oswald, sans-serif" }));

// ---- more scenes for one theme all night: tonight's look picks a family of them (look.js), a different one each song

const spooky = () => ({ "--accent": "#FF7A1A", "--title-font": "Creepster, Oswald, sans-serif" });

// graveyard: ghosts drift up out of the graves under a thin moon, swaying to the music.
THEMES.graveyard = sketchTheme("theme-graveyard", 640, 360, p => {
  const stones = [], ghosts = [];
  const ghost = (x, y, s, sway, a) => {
    p.fill(235, 240, 255, a);
    p.beginShape();
    p.vertex(x - s * 0.5, y);
    p.bezierVertex(x - s * 0.5, y - s * 0.95, x + s * 0.5, y - s * 0.95, x + s * 0.5, y);  // the head
    for (let k = 0; k <= 4; k++) p.vertex(x + s * 0.5 - k * s * 0.25, y + s * 0.7 + (k % 2) * s * 0.16 + Math.sin(sway + k) * s * 0.1);  // ragged hem
    p.endShape(p.CLOSE);
    p.fill(20, 10, 30, a);
    p.ellipse(x - s * 0.17, y - s * 0.28, s * 0.14, s * 0.2); p.ellipse(x + s * 0.17, y - s * 0.28, s * 0.14, s * 0.2);
  };
  return {
    setup() {
      for (let i = 0; i < 9; i++) stones.push({ x: 30 + i * 72 + p.random(-15, 15), w: p.random(26, 40), h: p.random(34, 60), cross: p.random() < 0.3 });
      for (let i = 0; i < 6; i++) ghosts.push({ x: p.random(p.width), y: p.random(p.height), s: p.random(22, 40), v: p.random(0.25, 0.55), ph: p.random(p.TWO_PI) });
    },
    frame(beat) {
      const g = p.drawingContext, sky = g.createLinearGradient(0, 0, 0, p.height);
      sky.addColorStop(0, "#161b36"); sky.addColorStop(1, "#0b0a14");
      g.fillStyle = sky; g.fillRect(0, 0, p.width, p.height);
      p.noStroke();
      p.fill(235, 230, 200); p.circle(110, 70, 50); p.fill(20, 24, 48); p.circle(123, 62, 46);  // a thin moon (the sky's colour bites it)
      for (const gh of ghosts) {
        gh.y -= gh.v * (1 + beat); gh.ph += 0.03;
        if (gh.y < -60) { gh.y = p.height + 40; gh.x = p.random(p.width); }
        const fade = Math.min(1, (p.height + 40 - gh.y) / 120, (gh.y + 60) / 120);  // fades in over the graves, out at the top
        ghost(gh.x + Math.sin(gh.ph) * 18, gh.y, gh.s * (1 + beat * 0.12), gh.ph * 2, 150 * fade * (0.7 + beat * 0.6));
      }
      g.filter = "blur(16px)";
      p.fill(120, 160, 140, 40);
      for (let i = 0; i < 5; i++) p.circle(p.width * p.noise(i * 7, p.frameCount * 0.004), p.height * 0.86, 200);  // ground mist
      g.filter = "none";
      p.fill(8, 8, 14); p.rect(0, p.height * 0.86, p.width, p.height);
      for (const s of stones) {
        const base = p.height * 0.88;
        if (s.cross) { p.rect(s.x - 4, base - s.h, 8, s.h); p.rect(s.x - s.w * 0.35, base - s.h * 0.75, s.w * 0.7, 8); continue; }
        p.rect(s.x - s.w / 2, base - s.h + s.w / 2, s.w, s.h - s.w / 2); p.arc(s.x, base - s.h + s.w / 2, s.w, s.w, p.PI, p.TWO_PI);
      }
    },
  };
}, () => ({ ...spooky(), "--sung": "#9FE8C6" }));

// webs: dew on the spider webs in the corners glints on the beat, spiders drop on their threads and climb back up.
THEMES.webs = sketchTheme("theme-webs", 640, 360, p => {
  const spiders = [], dust = [];
  const web = (cx, cy, r, a0, a1, shine) => {
    p.noFill(); p.stroke(205, 205, 225, 50 + 130 * shine); p.strokeWeight(1);
    const at = (i, rr) => [cx + Math.cos(a0 + (a1 - a0) * i / 7) * rr, cy + Math.sin(a0 + (a1 - a0) * i / 7) * rr];
    for (let i = 0; i <= 7; i++) p.line(cx, cy, ...at(i, r));
    for (let ring = 1; ring <= 7; ring++) { p.beginShape(); for (let i = 0; i <= 7; i++) p.vertex(...at(i, r * ring / 7.5)); p.endShape(); }
  };
  const spider = (x, y, s, wiggle) => {
    p.stroke(205, 205, 225, 90); p.strokeWeight(1); p.line(x, 0, x, y - s);  // the thread
    p.stroke(10, 6, 14); p.strokeWeight(1.6);
    for (let k = 0; k < 4; k++) for (const side of [-1, 1]) {
      const knee = y - s * 0.6 + k * s * 0.35, foot = y - s * 0.2 + k * s * 0.5 + Math.sin(wiggle + k) * s * 0.15;
      p.line(x, y, x + side * s * 0.9, knee); p.line(x + side * s * 0.9, knee, x + side * s * 1.5, foot);
    }
    p.noStroke(); p.fill(10, 6, 14); p.circle(x, y, s * 1.2); p.circle(x, y - s * 0.8, s * 0.7);
    p.fill(255, 120, 40); p.circle(x - s * 0.15, y - s * 0.85, 2); p.circle(x + s * 0.15, y - s * 0.85, 2);  // eyes in the pumpkin light
  };
  return {
    setup() {
      for (const x of [0.16, 0.38, 0.64, 0.86]) spiders.push({ x: p.width * x, s: p.random(7, 11), depth: p.random(60, 190), t: p.random(p.TWO_PI) });
      for (let i = 0; i < 70; i++) dust.push({ x: p.random(p.width), y: p.random(p.height), v: p.random(0.1, 0.4) });
    },
    frame(beat) {
      p.background(12, 8, 20);
      const g = p.drawingContext, glow = g.createRadialGradient(p.width / 2, p.height * 1.1, 20, p.width / 2, p.height * 1.1, 420);
      glow.addColorStop(0, `rgba(255,120,30,${0.25 + beat * 0.2})`); glow.addColorStop(1, "rgba(255,120,30,0)");
      g.fillStyle = glow; g.fillRect(0, 0, p.width, p.height);  // pumpkin light from below
      web(0, 0, 220, 0, p.HALF_PI, beat);
      web(p.width, 0, 170, p.HALF_PI, p.PI, beat);
      web(p.width, p.height, 130, p.PI, p.PI * 1.5, beat);
      p.noStroke();
      for (const d of dust) { d.y -= d.v; if (d.y < 0) { d.y = p.height; d.x = p.random(p.width); } p.fill(255, 200, 150, 60 + 80 * beat); p.circle(d.x, d.y, 1.6); }
      for (const s of spiders) { s.t += 0.008 * (1 + beat); spider(s.x, 20 + s.depth * (0.5 - 0.5 * Math.cos(s.t)) + beat * 6, s.s, p.frameCount * 0.2); }
    },
  };
}, () => ({ ...spooky(), "--sung": "#FF8A1F" }));

// cauldron: a witch's brew bubbles over the fire, green bubbles rise and pop with the beat; now and then a witch
// rides her broom across the moon.
THEMES.cauldron = sketchTheme("theme-cauldron", 640, 360, p => {
  const bubbles = [];
  let witch = null;
  const rider = (x, y) => {
    p.stroke(8, 4, 12); p.strokeWeight(2); p.line(x - 26, y + 6, x + 22, y - 2); p.noStroke();  // the broom
    p.fill(8, 4, 12);
    p.triangle(x - 28, y + 3, x - 20, y + 5, x - 31, y + 12);   // its bristles
    p.triangle(x - 5, y + 4, x + 9, y + 2, x + 2, y - 14);      // her cloak
    p.triangle(x - 3, y - 12, x + 11, y - 15, x + 6, y - 29);   // her hat
  };
  return {
    frame(beat) {
      const g = p.drawingContext, sky = g.createLinearGradient(0, 0, 0, p.height);
      sky.addColorStop(0, "#1a0f2b"); sky.addColorStop(1, "#0a1210");
      g.fillStyle = sky; g.fillRect(0, 0, p.width, p.height);
      const halo = g.createRadialGradient(130, 85, 30, 130, 85, 120);
      halo.addColorStop(0, "rgba(255,236,190,0.25)"); halo.addColorStop(1, "rgba(255,236,190,0)");
      g.fillStyle = halo; g.fillRect(0, 0, 300, 220);
      p.noStroke(); p.fill(240, 232, 205); p.circle(130, 85, 70);
      if (!witch && p.random() < 0.004) witch = { x: -40, y: p.random(65, 105) };
      if (witch) { rider(witch.x, witch.y + Math.sin(witch.x * 0.05) * 4); witch.x += 2.2; if (witch.x > p.width + 40) witch = null; }
      const cx = p.width / 2, cy = p.height * 0.73;  // above the TV's song bar, below the lyrics
      const fire = g.createRadialGradient(cx, cy + 40, 10, cx, cy + 40, 170 + beat * 60);
      fire.addColorStop(0, `rgba(255,140,40,${0.45 + beat * 0.3})`); fire.addColorStop(1, "rgba(255,140,40,0)");
      g.fillStyle = fire; g.fillRect(0, 0, p.width, p.height);
      for (let i = 0; i < 7; i++) {  // flames lick up round the pot
        const fx = cx - 60 + i * 20, fh = 18 + 16 * p.noise(i, p.frameCount * 0.08) + beat * 14;
        p.fill(255, 120 + 60 * p.noise(i + 9, p.frameCount * 0.05), 30, 200); p.triangle(fx - 9, cy + 46, fx + 9, cy + 46, fx, cy + 46 - fh);
      }
      p.fill(14, 10, 16); p.ellipse(cx, cy + 10, 160, 96);             // the pot
      p.fill(24, 18, 28); p.ellipse(cx, cy - 26, 150, 26);            // its rim
      p.fill(90, 255, 120, 150 + 80 * beat); p.ellipse(cx, cy - 26, 130, 18);  // the brew
      if (p.random() < 0.15 + beat * 0.4) bubbles.push({ x: cx + p.random(-55, 55), y: cy - 28, r: p.random(4, 10), v: p.random(0.6, 1.6), life: 1 });
      for (const b of bubbles) {
        b.y -= b.v * (1 + beat); b.x += Math.sin(b.y * 0.08) * 0.4; b.r += 0.05; b.life -= 0.006;
        p.noFill(); p.stroke(120, 255, 150, 200 * b.life); p.strokeWeight(1.4); p.circle(b.x, b.y, b.r * 2);
      }
      p.noStroke();
      while (bubbles.length && bubbles[0].life <= 0) bubbles.shift();
    },
  };
}, () => ({ ...spooky(), "--sung": "#7CFF8A" }));

const irish = () => ({ "--sung": "#E9C46A", "--accent": "#E9C46A" });

// knot: a golden Celtic trefoil knot turns slowly in a ring, its strands brightening with the beat while gold motes circle.
THEMES.knot = sketchTheme("theme-knot", 640, 360, p => {
  const motes = [];
  const strands = (cx, cy, s, rot, draw) => {  // the trefoil, then its ring
    p.beginShape();
    for (let i = 0; i <= 240; i++) {
      const t = i / 240 * p.TWO_PI, x = Math.sin(t) + 2 * Math.sin(2 * t), y = Math.cos(t) - 2 * Math.cos(2 * t);
      p.vertex(cx + s * (x * Math.cos(rot) - y * Math.sin(rot)), cy + s * (x * Math.sin(rot) + y * Math.cos(rot)));
    }
    p.endShape();
    if (draw) p.circle(cx, cy, s * 7.4);
  };
  return {
    setup() { for (let i = 0; i < 140; i++) motes.push({ a: p.random(p.TWO_PI), r: p.random(40, 360), v: p.random(0.0008, 0.003), s: p.random(1, 2.4) }); },
    frame(beat) {
      p.background(6, 30, 20);
      const g = p.drawingContext, light = g.createRadialGradient(p.width / 2, p.height / 2, 10, p.width / 2, p.height / 2, 330);
      light.addColorStop(0, "rgba(40,110,70,0.55)"); light.addColorStop(1, "rgba(40,110,70,0)");
      g.fillStyle = light; g.fillRect(0, 0, p.width, p.height);
      const cx = p.width / 2, cy = p.height / 2, s = 46 * (1 + beat * 0.04), rot = p.frameCount * 0.003;
      p.noFill(); p.strokeJoin(p.ROUND);
      for (const [w, c] of [[15, [4, 20, 12, 200]], [10, [200, 160, 70, 90 + 70 * beat]], [3, [255, 236, 180, 90 + 90 * beat]]]) {
        p.stroke(...c); p.strokeWeight(w); strands(cx, cy, s, rot, true);  // dark edge, gold, a shine along the middle
      }
      p.noStroke();
      for (const m of motes) { m.a += m.v * (1 + beat * 3); p.fill(233, 196, 106, 110 + 100 * beat); p.circle(cx + Math.cos(m.a) * m.r, cy + Math.sin(m.a) * m.r * 0.6, m.s); }
    },
  };
}, irish);

// hills: green hills roll away under a soft rainbow at dusk; clouds drift and fireflies rise with the music.
THEMES.hills = sketchTheme("theme-hills", 640, 360, p => {
  const ridges = [], flies = [], clouds = [];
  const greens = [[52, 98, 78], [36, 80, 56], [22, 62, 40], [10, 42, 26]];  // far to near
  return {
    setup() {
      for (let l = 0; l < 4; l++) { const r = []; for (let x = 0; x <= p.width + 10; x += 10) r.push(p.height * (0.56 + l * 0.11) + (p.noise(x * 0.004, l * 10) - 0.5) * 90); ridges.push(r); }
      for (let i = 0; i < 50; i++) flies.push({ x: p.random(p.width), y: p.random(p.height * 0.55, p.height), ph: p.random(p.TWO_PI) });
      for (let i = 0; i < 5; i++) clouds.push({ x: p.random(p.width), y: p.random(20, 110), s: p.random(40, 80), v: p.random(0.1, 0.3) });
    },
    frame(beat) {
      const g = p.drawingContext, sky = g.createLinearGradient(0, 0, 0, p.height * 0.7);
      sky.addColorStop(0, "#14223a"); sky.addColorStop(0.6, "#3a4c5c"); sky.addColorStop(1, "#86684a");
      g.fillStyle = sky; g.fillRect(0, 0, p.width, p.height);
      p.noFill(); p.strokeWeight(7);
      [[255, 80, 80], [255, 170, 60], [250, 230, 90], [90, 210, 110], [80, 150, 255], [150, 100, 220]].forEach(([r, gg, b], i) => {
        p.stroke(r, gg, b, 38 + beat * 30); p.arc(p.width * 0.62, p.height * 0.98, 640 - i * 14, 560 - i * 14, p.PI, p.TWO_PI);
      });
      p.noStroke();
      g.filter = "blur(10px)";
      for (const c of clouds) { c.x = (c.x + c.v) % (p.width + 160); p.fill(210, 215, 230, 50); p.ellipse(c.x - 80, c.y, c.s * 2.4, c.s); }
      g.filter = "none";
      ridges.forEach((r, l) => { p.fill(...greens[l]); p.beginShape(); p.vertex(0, p.height); r.forEach((y, i) => p.vertex(i * 10, y)); p.vertex(p.width, p.height); p.endShape(p.CLOSE); });
      for (const f of flies) {
        f.y -= 0.15 * (1 + beat * 2); f.x += Math.sin(f.ph + p.frameCount * 0.02) * 0.3;
        if (f.y < p.height * 0.45) { f.y = p.height; f.x = p.random(p.width); }
        p.fill(220, 255, 140, (110 + 110 * Math.sin(f.ph + p.frameCount * 0.07)) * (0.6 + beat)); p.circle(f.x, f.y, 2.2);
      }
    },
  };
}, irish);

// harp: the strings of an Irish harp shimmer gold on green, plucked by the music, while shamrock leaves float down.
THEMES.harp = sketchTheme("theme-harp", 640, 360, p => {
  const strings = [], leaves = [];
  return {
    setup() {
      for (let i = 0; i < 24; i++) strings.push({ x: 110 + i * 18, top: 40 + 140 * (i / 23) ** 1.6, energy: 0, ph: p.random(p.TWO_PI) });
      for (let i = 0; i < 10; i++) leaves.push({ x: p.random(p.width), y: p.random(p.height), r: p.random(p.TWO_PI), s: p.random(5, 9), v: p.random(0.3, 0.7) });
    },
    frame(beat) {
      p.background(5, 26, 18);
      const g = p.drawingContext, light = g.createLinearGradient(0, 0, p.width, 0);
      light.addColorStop(0, "rgba(30,90,60,0)"); light.addColorStop(0.5, `rgba(60,140,90,${0.25 + beat * 0.2})`); light.addColorStop(1, "rgba(30,90,60,0)");
      g.fillStyle = light; g.fillRect(0, 0, p.width, p.height);
      if (beat > 0.45) p.random(strings).energy = 1;  // the loud notes pluck a string
      p.noFill();
      for (const s of strings) {
        s.energy = Math.max(0.08, s.energy * 0.96); s.ph += 0.6;
        p.stroke(233, 196, 106, 70 + 170 * s.energy); p.strokeWeight(1 + s.energy * 1.5);
        p.beginShape();
        for (let k = 0; k <= 20; k++) { const u = k / 20; p.vertex(s.x + Math.sin(Math.PI * u) * Math.sin(s.ph) * 7 * s.energy, s.top + (330 - s.top) * u); }
        p.endShape();
      }
      p.stroke(150, 110, 40); p.strokeWeight(6);  // the harp's neck and soundboard, in brass
      p.beginShape(); strings.forEach(s => p.vertex(s.x, s.top - 4)); p.endShape();
      p.line(100, 334, 540, 334);
      p.noStroke();
      for (const l of leaves) {
        l.y += l.v; l.r += 0.01; if (l.y > p.height + 10) { l.y = -10; l.x = p.random(p.width); }
        p.push(); p.translate(l.x, l.y); p.rotate(l.r); p.fill(60, 170, 90, 150);
        for (let k = 0; k < 3; k++) { p.rotate(p.TWO_PI / 3); p.circle(0, -l.s * 0.6, l.s); }
        p.pop();
      }
    },
  };
}, irish);

// How each theme shows its lyrics, not just its background; staff can override both on the admin page.
Object.entries({
  cover: ["classic", "wipe"], celtic: ["ball", "wipe"], neon80s: ["classic", "glow"], disco: ["classic", "pop"],
  rock: ["bigline", "pop"], ballad: ["scroll", "glow"], pop: ["classic", "pop"], halloween: ["classic", "glow"],
  graveyard: ["classic", "glow"], webs: ["bigline", "glow"], cauldron: ["classic", "pop"],
  knot: ["classic", "glow"], hills: ["classic", "wipe"], harp: ["ball", "wipe"],
}).forEach(([name, [layout, highlight]]) => Object.assign(THEMES[name], { layout, highlight }));
// Scenes that belong to one venue look: the TV lobby's mixed rotation shows them only in that look.
Object.entries({ pub: ["celtic", "knot", "hills", "harp"], halloween: ["halloween", "graveyard", "webs", "cauldron"] })
  .forEach(([look, names]) => names.forEach(n => { THEMES[n].look = look; }));
