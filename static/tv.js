// The karaoke TV. Scenes: lobby -> upnext -> singing -> applause -> (next singer or lobby).
// The server owns the queue; this page follows /api/state and plays whatever /api/next hands it.
const $ = id => document.getElementById(id);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const post = (url, body) => fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) }).then(r => r.json());
const DEFAULT_PALETTE = ["rgb(31,107,74)", "rgb(201,160,69)", "rgb(140,59,42)"];

// ---------------------------------------------------------------- audio

const ctx = new (window.AudioContext || window.webkitAudioContext)();
const master = ctx.createGain(), vocGain = ctx.createGain(), analyser = ctx.createAnalyser();
analyser.fftSize = 1024;
vocGain.connect(master);
master.connect(analyser);
analyser.connect(ctx.destination);
let sources = [], startedAt = 0;

async function loadSong(slug) {
  const base = `/library/${encodeURIComponent(slug)}/`;
  const get = async name => { const r = await fetch(base + name); if (!r.ok) throw new Error(`${slug}/${name} ${r.status}`); return r; };
  const audio = async name => ctx.decodeAudioData(await (await get(name)).arrayBuffer());
  const [inst, voc, lyrics, song] = await Promise.all([
    audio("instrumental.m4a"), audio("vocals.m4a"), get("lyrics.json").then(r => r.json()), get("song.json").then(r => r.json()),
  ]);
  return { inst, voc, lyrics, song };
}

function startSong(bufs, offset = 0) {
  stopAudio();
  const when = ctx.currentTime + 0.2;
  const inst = ctx.createBufferSource(), voc = ctx.createBufferSource();
  inst.buffer = bufs.inst; voc.buffer = bufs.voc;
  inst.connect(master); voc.connect(vocGain);
  inst.start(when, offset); voc.start(when, offset);  // same `when`: the stems stay sample-locked
  sources = [inst, voc];
  startedAt = when - offset;
}
function stopAudio() { sources.forEach(s => { try { s.stop(); } catch (e) {} }); sources = []; }
// /tv?demo=<theme>[&layout=..&highlight=..&size=..]: preview a look with fake lyrics, no audio
const PARAMS = new URLSearchParams(location.search), DEMO = PARAMS.get("demo");
const songTime = () => DEMO ? (performance.now() / 1000) % 24 : ctx.currentTime - startedAt;
// Where the singer is in the song as the room hears it: the sound reaches the speakers a little after the audio clock
// (sound card), while the TV shows a frame a little late (screen delay, set once with the sync test), plus the
// staff's per-song nudge. Positive = lyrics earlier.
const lyricTime = () => songTime() + (DEMO ? 0 : (state?.display?.screen_delay_ms || 0) / 1000 + (state?.nudge || 0)
  - (ctx.outputLatency || 0) - (ctx.baseLatency || 0));

const samples = new Uint8Array(analyser.fftSize);
let level = 0;
function measureBeat() {
  analyser.getByteTimeDomainData(samples);
  let sum = 0;
  for (const v of samples) { const x = (v - 128) / 128; sum += x * x; }
  level = Math.max(Math.min(1, Math.sqrt(sum / samples.length) * 3), level * 0.92);
  if (DEMO) level = Math.max(0, Math.sin(performance.now() / 1000 * Math.PI * 2 * 2)) ** 3;  // a fake 120 bpm pulse
}
const beat = () => level;

// ---------------------------------------------------------------- themes and colours

let theme = null, themeName = null;
function palette(url) {
  return new Promise(resolve => {
    const img = new Image();
    img.onload = () => { try { resolve(mainColours(img)); } catch (e) { resolve(DEFAULT_PALETTE); } };
    img.onerror = () => resolve(DEFAULT_PALETTE);
    img.src = url;
  });
}
// Three most distinct average colours of the cover: tiny k-means on a 16x16 thumbnail.
function mainColours(img) {
  const c = document.createElement("canvas"); c.width = c.height = 16;
  const g = c.getContext("2d"); g.drawImage(img, 0, 0, 16, 16);
  const d = g.getImageData(0, 0, 16, 16).data, px = [];
  for (let i = 0; i < d.length; i += 4) px.push([d[i], d[i + 1], d[i + 2]]);
  const dist = (a, b) => (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2;
  const centres = [px[0]];
  while (centres.length < 3) centres.push(px.reduce((best, p) => Math.min(...centres.map(c => dist(c, p))) > Math.min(...centres.map(c => dist(c, best))) ? p : best));
  for (let round = 0; round < 6; round++) {
    const sums = centres.map(() => [0, 0, 0, 0]);
    for (const p of px) { const k = centres.reduce((bi, c, i) => dist(c, p) < dist(centres[bi], p) ? i : bi, 0); sums[k][0] += p[0]; sums[k][1] += p[1]; sums[k][2] += p[2]; sums[k][3]++; }
    sums.forEach((s, i) => { if (s[3]) centres[i] = [s[0] / s[3], s[1] / s[3], s[2] / s[3]]; });
  }
  return centres.map(c => `rgb(${c.map(Math.round).join(",")})`);
}

async function setTheme(name, coverUrl, seed) {
  const pal = coverUrl ? await palette(coverUrl) : DEFAULT_PALETTE;
  const t = Object.hasOwn(THEMES, name) ? THEMES[name] : THEMES.cover;
  if (theme) theme.stop();
  document.body.removeAttribute("style");
  $("bg").replaceChildren();
  document.body.className = t.cls;
  themeName = name;
  theme = t.start($("bg"), { beat, palette: pal, seed: String(seed) });
}

// ---------------------------------------------------------------- QR codes

const qrCache = {};
function qr(target, text) {
  if (!text) return;
  if (!qrCache[text]) {
    const q = qrcode(0, "M"); q.addData(text); q.make();
    qrCache[text] = q.createSvgTag({ cellSize: 1, margin: 2, scalable: true });
  }
  if (target.dataset.text !== text) { target.innerHTML = qrCache[text]; target.dataset.text = text; }
}
const wifiCode = w => `WIFI:T:WPA;S:${w.name.replace(/([\\;,:"])/g, "\\$1")};P:${w.password.replace(/([\\;,:"])/g, "\\$1")};;`;

// ---------------------------------------------------------------- lyrics

// Four layouts share one timing: each word lights up from when it's sung (t) to when the voice lets go of it (e).
//   classic  two fixed lines; the one just finished is swapped for the line after next, so nothing jumps
//   scroll   the whole song scrolls past, the line being sung big in the middle
//   bigline  one huge line and a small preview of the next
//   ball     classic, with a ball hopping onto each word as it's sung
let lyrics = null, titleUntil = 0, look = null, slots = [], ball = null, shownLine = -1;
const wordsOf = line => line.words.length ? line.words : [{ w: line.text, t: line.start, e: line.end }];
function wordEnd(line, k) {
  const ws = wordsOf(line), w = ws[k];
  if (w.e != null) return w.e;
  const next = k + 1 < ws.length ? ws[k + 1].t : line.end;  // songs made before word ends were kept
  return Math.min(next, w.t + 0.25 + 0.09 * w.w.length);
}
function fillLine(p, line, idx) {
  p.dataset.i = idx;
  p.replaceChildren(...(line ? wordsOf(line).flatMap((w, k) => {
    const s = document.createElement("span"); s.className = "w"; s.textContent = w.w;
    return k ? [" ", s] : [s];
  }) : []));
}
function paint(p, line, t) {
  if (!line) return;
  p.querySelectorAll(".w").forEach((span, k) => {
    const start = wordsOf(line)[k].t, end = wordEnd(line, k);
    span.style.setProperty("--p", Math.max(0, Math.min(1, (t - start) / Math.max(0.05, end - start))).toFixed(3));
    span.classList.toggle("on", t >= start && t < end);
    span.classList.toggle("done", t >= end);
  });
}

// The look: a URL preview beats the staff's choice, which beats the theme's own style.
function lookNow() {
  const d = state?.display || {}, th = THEMES[themeName] || THEMES.cover;
  const pick = (k, fallback) => PARAMS.get(k) || (d[k] && d[k] !== "auto" ? d[k] : fallback);
  return { layout: pick("layout", th.layout || "classic"), highlight: pick("highlight", th.highlight || "wipe"),
           size: PARAMS.get("size") || d.size || "L", position: d.position || "middle", band: !!d.band,
           next_line: d.next_line !== false, dots: d.dots !== false };
}
function applyLook() {
  const l = lookNow();
  if (JSON.stringify(l) === JSON.stringify(look)) return;
  look = l;
  const box = $("lyrics");
  box.className = `layout-${l.layout} hl-${l.highlight} size-${l.size} pos-${l.position}${l.band ? " band" : ""}`;
  buildLyrics();
}
function buildLyrics() {
  shownLine = -1;
  const holder = $("lines");
  if (look.layout === "scroll") {  // every line once; the holder slides up as the song goes on
    slots = (lyrics || []).map((line, i) => { const p = document.createElement("p"); p.className = "line"; fillLine(p, line, i); return p; });
  } else {
    slots = [0, 1].map(() => { const p = document.createElement("p"); p.className = "line"; p.dataset.i = -1; return p; });
  }
  holder.style.transform = "";
  holder.replaceChildren(...slots);
  ball = look.layout === "ball" ? $("ball") : null;
  $("ball").hidden = !ball;
}

function updateLyrics(t) {
  const lines = lyrics;
  let i = lines.findIndex(l => l.end > t);
  if (i < 0) i = lines.length;
  const line = lines[i], showTitle = t < titleUntil;
  $("title").classList.toggle("gone", !showTitle);
  $("lyrics").style.visibility = showTitle ? "hidden" : "visible";
  const soon = j => lines[j] && lines[j].start - t < 8;  // lines more than 8 s away wait; the gap bar shows instead
  if (look.layout === "scroll") {
    if (i !== shownLine) {
      slots.forEach((p, j) => { p.classList.toggle("now", j === i); p.classList.toggle("past", j < i); });
      const target = slots[Math.min(i, slots.length - 1)];
      if (target) $("lines").style.transform = `translateY(${-(target.offsetTop + target.offsetHeight / 2)}px)`;
      shownLine = i;
    }
    paint(slots[i], line, t);
  } else {
    // bigline: line i big on top, the next one small below. classic and ball: line j always sits in slot j % 2.
    const big = look.layout === "bigline";
    [i, i + 1].forEach(j => {
      const p = big ? slots[j - i] : slots[j % 2], show = soon(j) && (j === i || look.next_line), key = show ? j : -1;
      if (+p.dataset.i !== key) fillLine(p, show && lines[j], key);
      p.className = j === i ? "line now" : "line next";
      if (show) paint(p, lines[j], t);
    });
    if (ball) moveBall(slots[i % 2], line, t);
  }
  if (!line) { $("dots").replaceChildren(); $("gap").hidden = true; return; }
  const prevEnd = i > 0 ? lines[i - 1].end : 0, wait = line.start - t, gapLen = line.start - prevEnd;
  const dots = look.dots && gapLen > 3 && wait > 0 && wait <= 3 ? Math.ceil(wait) : 0;
  if ($("dots").childElementCount !== dots) $("dots").replaceChildren(...Array.from({ length: dots }, () => document.createElement("i")));
  const inGap = gapLen > 5 && wait > 3 && !showTitle;
  $("gap").hidden = !inGap;
  if (inGap) $("gapBar").style.width = `${Math.min(100, 100 * (t - prevEnd) / (gapLen - 3))}%`;
}

// The ball lands on each word as it's sung, in an arc from the word before.
function moveBall(p, line, t) {
  const spans = p.querySelectorAll(".w");
  if (!line || !spans.length) { ball.style.opacity = 0; return; }
  const ws = wordsOf(line), box = $("lyrics").getBoundingClientRect();
  const centre = k => { const r = spans[Math.min(k, spans.length - 1)].getBoundingClientRect(); return [r.left + r.width / 2 - box.left, r.top - box.top]; };
  let k = -1;
  while (k + 1 < ws.length && ws[k + 1].t <= t) k++;
  let x, y, hop = 0;
  if (k < 0) {  // before the first word: wait on it, bouncing in time for the last second
    [x, y] = centre(0); const f = 1 - Math.min(1, ws[0].t - t); hop = f > 0 ? Math.abs(Math.sin(f * Math.PI * 2)) * 0.5 : 0;
  } else if (k + 1 < ws.length) {
    const f = Math.min(1, (t - ws[k].t) / Math.max(0.05, ws[k + 1].t - ws[k].t)), [x0, y0] = centre(k), [x1, y1] = centre(k + 1);
    x = x0 + (x1 - x0) * f; y = y0 + (y1 - y0) * f; hop = 4 * f * (1 - f);
  } else [x, y] = centre(k);
  const size = ball.offsetHeight || 20;
  ball.style.opacity = ws[0].t - t > 1.5 ? 0 : 1;
  const squash = k >= 0 && hop < 0.12 ? " scale(1.18, .82)" : "";  // a little squash as it lands on the word
  ball.style.transform = `translate(${x - size / 2}px, ${y - size * (0.7 + 1.1 * hop)}px)${squash}`;
}

// Sync test, started from the staff page: a click on every second and a flash timed like the lyrics.
// Staff move "Screen delay" until the flash and the click land together; every song then uses that delay.
let clickBuf = null, nextClick = 0, syncStart = 0, clicks = [];
function startSyncTest() {
  if (!clickBuf) {
    clickBuf = ctx.createBuffer(1, Math.round(ctx.sampleRate * 0.03), ctx.sampleRate);
    const d = clickBuf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.sin(2 * Math.PI * 1500 * i / ctx.sampleRate) * (1 - i / d.length);
  }
  syncStart = ctx.currentTime + 0.5; nextClick = 0;
  show("synctest");
}
function stopSyncTest() { clicks.forEach(s => { try { s.stop(); } catch (e) {} }); clicks = []; show("lobby"); }
function drawSyncTest() {
  while (syncStart + nextClick < ctx.currentTime + 1) {  // keep a second of clicks queued on the audio clock
    const s = ctx.createBufferSource(); s.buffer = clickBuf; s.connect(master); s.start(syncStart + nextClick++);
    clicks = [...clicks.slice(-4), s];
  }
  const seen = ctx.currentTime - syncStart + (state?.display?.screen_delay_ms || 0) / 1000 - (ctx.outputLatency || 0) - (ctx.baseLatency || 0);
  const f = ((seen % 1) + 1) % 1;
  $("flash").classList.toggle("on", f < 0.1);
  $("syncDelay").textContent = `${state?.display?.screen_delay_ms || 0} ms`;
}

// ---------------------------------------------------------------- scenes

let state = null, scene = "lobby", current = null, song = null, run = 0, busy = false, unlocked = false;
function show(name) { document.querySelectorAll(".scene").forEach(s => s.hidden = s.id !== name); scene = name; }

function renderLobby() {
  $("pub").textContent = state.pub_name;
  applyVenueLook(state.look);
  document.title = state.pub_name;
  qr($("joinQr"), state.join_url);
  $("joinUrl").textContent = state.join_url.replace(/^https?:\/\//, "").replace(/\/$/, "");
  const w = state.wifi;
  $("wifi").hidden = !w.name;
  if (w.name) { qr($("wifiQr"), wifiCode(w)); $("wifiText").textContent = w.password ? `${w.name}
${w.password}` : w.name; }
  const rows = state.queue.slice(0, 5).map(e => {
    const li = document.createElement("li"), title = document.createElement("span");
    title.textContent = ` – ${e.song.title}`;
    li.append(e.name, title);
    if (e.status === "making" || e.status === "waiting") {
      const later = document.createElement("span"); later.className = "later"; later.textContent = " ⏳"; li.append(later);
    }
    return li;
  });
  $("lineup").replaceChildren(...rows);
  $("free").hidden = rows.length > 0 || !!state.now_playing;
  // nobody's song is ready yet: say so, so the room knows the screen isn't stuck
  const head = state.queue[0], none = !state.now_playing && head && state.queue.every(e => e.status === "making" || e.status === "waiting");
  $("prep").hidden = !none;
  if (none) $("prep").textContent = `Getting ${head.name}'s song ready… ${head.pct || 0}% / ${head.name}s Song wird vorbereitet… ${head.pct || 0} %`;
}
function renderBar() {
  if (!current) return;
  $("barSinger").textContent = current.name;
  $("barSong").textContent = `${current.artist} – ${current.title}`;
  const nxt = state.queue[0];
  $("barNext").textContent = nxt ? `Next / Als Nächstes: ${nxt.name}` : "";
  qr($("barQr"), state.join_url);
  qr($("upQr"), state.join_url);
}

async function poll() {
  const asked = performance.now();
  try { state = await (await fetch("/api/state")).json(); } catch (e) { return; }
  master.gain.setTargetAtTime(state.volume, ctx.currentTime, 0.05);
  vocGain.gain.setTargetAtTime(state.help_vocals ?? 0.25, ctx.currentTime, 0.05);
  if (unlocked) {
    if (state.paused && scene === "singing" && ctx.state === "running") ctx.suspend();
    if (!state.paused && ctx.state === "suspended") ctx.resume();
  }
  if (player && player.setVolume) {
    player.setVolume(Math.round(state.volume * 100));
    if (state.paused !== videoPaused) { videoPaused = state.paused; videoPaused ? player.pauseVideo() : player.playVideo(); }
  }
  renderLobby(); renderBar();
  if (scene === "singing") applyLook();  // staff changed the look mid-song
  // only a state fetched after this song started can say it was skipped (an older response predates /api/next)
  const skipped = current && asked > current.since && (scene === "upnext" || scene === "singing" || scene === "video") && (!state.now_playing || state.now_playing.id !== current.id);
  if (skipped) return abort();
  if (unlocked && state.synctest && scene === "lobby" && !busy) startSyncTest();
  if (!state.synctest && scene === "synctest") stopSyncTest();
  if (scene === "lobby" && !busy && unlocked && (state.queue.length || state.now_playing)) next();
}

async function next() {
  if (busy) return;
  busy = true;
  try {
    const { entry, error } = await post("/api/next");
    if (error === "forbidden") {  // only the laptop itself may run the queue, so a guest's phone can't
      $("start").innerText = `Open the TV screen on the karaoke laptop as http://localhost:${location.port || 80}/tv\nDen Fernseh-Bildschirm auf dem Karaoke-Laptop als http://localhost:${location.port || 80}/tv öffnen`;
      $("start").hidden = false;
    } else if (unlocked) $("start").hidden = true;  // allowed again (e.g. the server was updated): clear the message
    if (entry) perform(entry); else { current = null; show("lobby"); }
  } catch (e) { show("lobby"); }
  finally { busy = false; }
}

function abort() { run++; stopAudio(); stopVideo(""); current = null; song = null; show("lobby"); next(); }

async function perform(entry) {
  const my = ++run;
  const alive = () => my === run;
  current = { ...entry, since: performance.now() };
  const cover = entry.song_id && `/library/${encodeURIComponent(entry.song_id)}/cover.jpg`;
  const forced = state?.display?.theme;  // staff can set one theme for the whole night
  setTheme(forced && forced !== "auto" ? forced : entry.theme || "cover", cover, entry.song_id);
  $("upWho").textContent = entry.name;
  $("upSong").textContent = [entry.title, entry.artist].filter(Boolean).join(" – ");
  renderBar();
  show("upnext");
  let loadError = "";
  // no song_id: a guest's wish that isn't made yet, played as a YouTube karaoke video instead
  const loading = entry.song_id ? loadSong(entry.song_id).catch(e => { console.error(e); loadError = String(e); return null; }) : null;
  for (let s = state ? state.upnext_seconds : 15; s > 0; s--) {
    $("upCount").textContent = s;
    await sleep(1000);
    while (alive() && state && state.paused) await sleep(300);
    if (!alive()) return;
  }
  const bufs = loading && await loading;
  if (!alive()) return;
  if (!loading) loadError = await playVideo(entry.yt || []);
  if (!alive()) return;
  if (loadError) {  // a broken song folder or video must not block the night: drop it and move on
    await post("/api/done", { id: entry.id, error: loadError }); current = null; show("lobby"); return next();
  }
  if (bufs) await sing(entry, bufs, alive);
  if (!alive()) return;
  await post("/api/done", { id: entry.id });
  $("clapWho").textContent = entry.name;
  show("applause");
  await sleep(4000);
  if (!alive()) return;
  current = null; song = null;
  show("lobby");
  next();
}

// YouTube's player: loaded only the first time a wish is played, so the TV works without internet otherwise.
let ytApi = null, player = null, videoEnded = null, videoPaused = false;
const loadYt = () => ytApi ||= new Promise((ok, fail) => {
  window.onYouTubeIframeAPIReady = ok;
  const s = document.createElement("script");
  s.src = "https://www.youtube.com/iframe_api";
  s.onerror = () => { ytApi = null; s.remove(); fail(new Error("YouTube not reachable")); };
  document.head.append(s);
});
function stopVideo(why) {
  if (player) { player.destroy(); player = null; }
  $("video").replaceChildren();
  if (videoEnded) { videoEnded(why); videoEnded = null; }
}
// Plays the first video that works (some don't allow playing outside YouTube). Resolves "" when one ends, else the error.
async function playVideo(ids) {
  let error = "no karaoke video found on YouTube";
  for (const id of ids) {
    try { await loadYt(); } catch (e) { return String(e); }
    show("video");
    $("video").replaceChildren(document.createElement("div"));
    videoPaused = false;
    error = await new Promise(done => {
      videoEnded = done;
      player = new YT.Player($("video").firstChild, { videoId: id, playerVars: { autoplay: 1, controls: 0, rel: 0, playsinline: 1 }, events: {
        onReady: e => { e.target.setVolume(Math.round((state ? state.volume : 1) * 100)); e.target.playVideo(); },
        onStateChange: e => { if (e.data === YT.PlayerState.ENDED) stopVideo(""); },
        onError: e => stopVideo(`YouTube error ${e.data} on video ${id}`),
      } });
    });
    if (!error) return "";
  }
  return error;
}

async function sing(entry, bufs, alive) {
  song = bufs; lyrics = bufs.lyrics; look = null; applyLook();
  $("tTitle").textContent = entry.title; $("tArtist").textContent = entry.artist; $("tSinger").textContent = entry.name;
  titleUntil = Math.max(0, Math.min(5, (lyrics[0] ? lyrics[0].start : 5) - 0.5));
  $("title").classList.remove("gone");
  show("singing");
  startSong(bufs);
  while (alive() && songTime() < bufs.inst.duration - 0.05) await sleep(200);
  stopAudio();
}

// ---------------------------------------------------------------- main loop

let lobbyTheme = 0;
function cycleLobbyTheme() {
  if (scene !== "lobby") return;
  const names = Object.keys(THEMES).filter(n => n !== "celtic" || state?.look?.look === "pub");  // Irish only in the pub look
  setTheme(names[lobbyTheme++ % names.length], null, `lobby-${lobbyTheme}`);
}

function frame() {
  requestAnimationFrame(frame);  // scheduled first: one bad lyrics file must not freeze the screen for the night
  measureBeat();
  if (scene === "singing" && lyrics && look) {
    try { updateLyrics(lyricTime()); } catch (e) { console.error(e); }
    if (song) $("barProgress").style.width = `${Math.min(100, 100 * songTime() / song.inst.duration)}%`;
  }
  if (scene === "synctest") drawSyncTest();
}

// A browser without AAC (e.g. VS Code's built-in browser) would take every song off the queue and then drop it.
const CAN_PLAY = !!new Audio().canPlayType('audio/mp4; codecs="mp4a.40.2"');

// The browser decides when sound may start: at once in the kiosk (autoplay flag), otherwise after a click, and the
// sound device can take a second to wake up. So the screen unlocks when the audio actually runs, whenever that is.
// It stays unlocked after that: a staff pause suspends the audio on purpose.
function audioStarted() {
  if (ctx.state !== "running" || unlocked) return;
  unlocked = true;
  $("start").hidden = true;
  navigator.wakeLock?.request("screen").catch(() => {});
  poll();
}
ctx.addEventListener("statechange", audioStarted);

function unlock() {
  if (!CAN_PLAY) {
    $("start").innerText = "This browser can't play the songs. Open this page in Microsoft Edge or Chrome.\nDieser Browser kann die Songs nicht abspielen. Bitte in Microsoft Edge oder Chrome öffnen.";
    $("start").hidden = false;
    return;
  }
  ctx.resume().then(audioStarted, () => {});  // without a click this never settles: the welcome screen carries on
  audioStarted();
  setTimeout(() => { if (!unlocked) $("start").hidden = false; }, 1500);  // still no sound: ask for a click
}
["click", "keydown"].forEach(ev => addEventListener(ev, () => { if (!unlocked) unlock(); }));

function startDemo(name) {
  // each word: when it's sung and for how long; "Nacht" and "again" are held notes
  const line = (start, text, hold = {}) => {
    let t = start;
    const words = text.split(" ").map(w => { const len = hold[w] || 0.4; const word = { w, t, e: t + len }; t += len + 0.12; return word; });
    return { start, end: t, text, words };
  };
  lyrics = [line(2, "Sing it loud for the whole room"), line(5.6, "Every word lights up in time"), line(9.2, "Atemlos durch die Nacht", { Nacht: 2.2 }),
            line(18, "After the gap the dots count in"), line(21.2, "And round we go again", { again: 1.6 })];
  current = { name: "Anna", artist: "Demo Artist", title: `Theme: ${name}` };
  $("barSinger").textContent = "Anna"; $("barSong").textContent = `Demo Artist – Theme: ${name}`; $("barNext").textContent = "Next / Als Nächstes: Ben";
  titleUntil = 0;
  setTheme(name, null, "demo").then(() => { look = null; applyLook(); });
  show("singing");
  requestAnimationFrame(frame);
  const follow = async () => { try { state = await (await fetch("/api/state")).json(); applyLook(); } catch (e) {} };  // the staff's settings
  follow(); setInterval(follow, 2000);
}

(async function startTv() {
  if (DEMO) return startDemo(DEMO);
  show("lobby");
  cycleLobbyTheme();
  setInterval(cycleLobbyTheme, 30000);
  unlock();
  requestAnimationFrame(frame);
  await poll();
  setInterval(poll, 1000);
  document.addEventListener("visibilitychange", () => { if (!document.hidden && unlocked) navigator.wakeLock?.request("screen").catch(() => {}); });
})();
