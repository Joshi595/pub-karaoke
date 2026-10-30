const SHELVES = ["ready", "here", "top", "classics", "irish", "german", "schlager", "80s", "rock", "country", "duets"];
const T = {
  en: {
    tagline: "Pick a song. We'll call your name.",
    search: "Song, artist or a line you remember",
    shelves: "Song lists",
    shelf: { ready: "Ready now", here: "Popular here", top: "Top hits", classics: "Crowd favourites", irish: "Irish", german: "German",
             schlager: "Schlager", "80s": "80s", rock: "Rock", country: "Country", duets: "Duets" },
    badge: { ready: "Ready", make: "~3 min", making: "Getting ready", video: "Video", duet: "Duet", mine: "On your list" },
    songCount: n => n === 1 ? "1 song" : `${n} songs`,
    more: "Show more", back: "All lists",
    shelfEmpty: { ready: "Nothing made yet. Search for a song and we'll get it ready.", here: "Nobody has picked a song here yet. Be the first!" },
    mine: "Your songs",
    next: "You're next!", before: n => n === 1 ? "1 song before this one" : `${n} songs before this one`, place: "in line",
    onNow: "You're on! Grab the mic.", now: "now",
    makingPct: p => `Getting your song ready… ${p}%`, waitingMake: "Your song gets made next.",
    whenReady: "You sing as soon as it's ready.", videoTicket: "Plays as a karaoke video.",
    remove: "Remove",
    stageOn: (n, s) => [`On stage: `, n, `, singing ${s}.`],
    waiting: n => n === 1 ? " 1 song waiting." : ` ${n} songs waiting.`,
    stageFree: "The stage is free. Be the first!",
    singingAs: n => `Singing as ${n}.`, change: "Change name",
    nameTitle: "Your name on the screen", nameText: "We'll show it on the TV when it's your turn.",
    cancel: "Cancel", addMine: "Add my song",
    added: "Added! Watch the screen for your name.", removed: "Removed.",
    found: n => n === 1 ? "1 match." : `${n} matches.`,
    none: "No match. Try the artist's name, or wish for the song below.",
    wishTitle: "Can't find your song?", wishText: "Tell us and we'll get it ready for your turn.",
    wishPlaceholder: "Artist – Song…", wishButton: "Wish for it",
    finding: "Checking we can make your song…", wished: "Added! We're making your song now. Watch the screen for your name.",
    videoTitle: "Karaoke video only",
    videoText: "We can't make this one ourselves because there are no timed lyrics for it, but a YouTube karaoke version can play instead.",
    videoAdd: "Add the video",
    err: { limit: n => `You already have ${n} songs waiting. Sing one first!`, duplicate: "That song is already on your list.",
           unknown_song: "That song isn't available any more.", bad_name: "Please type a name.",
           forbidden: "You can only remove your own songs.", not_found: "That song already left the queue.",
           empty: "Type the song you'd like.", offline: "No internet right now, so new songs can't be fetched. Pick one marked Ready.",
           no_video: "There's no karaoke version of this one. Try another song.",
           full: "The queue is full right now. Try again after a few songs.",
           network: "Can't reach the karaoke laptop. Are you on the Wi-Fi here?" },
  },
  de: {
    tagline: "Such dir einen Song aus. Wir rufen dich auf.",
    search: "Song, Interpret oder eine Textzeile",
    shelves: "Songlisten",
    shelf: { ready: "Sofort singbar", here: "Beliebt hier", top: "Top-Hits", classics: "Publikumslieblinge", irish: "Irisch", german: "Deutsch",
             schlager: "Schlager", "80s": "80er", rock: "Rock", country: "Country", duets: "Duette" },
    badge: { ready: "Bereit", make: "~3 Min.", making: "Wird vorbereitet", video: "Video", duet: "Duett", mine: "Auf deiner Liste" },
    songCount: n => n === 1 ? "1 Song" : `${n} Songs`,
    more: "Mehr zeigen", back: "Alle Listen",
    shelfEmpty: { ready: "Noch nichts fertig. Such einen Song, wir machen ihn bereit.", here: "Hier hat noch niemand einen Song gewählt. Fang du an!" },
    mine: "Meine Songs",
    next: "Du bist als Nächstes dran!", before: n => n === 1 ? "Noch 1 Song davor" : `Noch ${n} Songs davor`, place: "Platz",
    onNow: "Du bist dran! Schnapp dir das Mikro.", now: "jetzt",
    makingPct: p => `Dein Song wird vorbereitet… ${p} %`, waitingMake: "Dein Song wird als Nächstes vorbereitet.",
    whenReady: "Du bist dran, sobald er fertig ist.", videoTicket: "Läuft als Karaoke-Video.",
    remove: "Entfernen",
    stageOn: (n, s) => [`Auf der Bühne: `, n, ` mit ${s}.`],
    waiting: n => n === 1 ? " 1 Song in der Warteschlange." : ` ${n} Songs in der Warteschlange.`,
    stageFree: "Die Bühne ist frei. Sei die oder der Erste!",
    singingAs: n => `Du singst als ${n}.`, change: "Namen ändern",
    nameTitle: "Dein Name auf dem Bildschirm", nameText: "Wir zeigen ihn auf dem Fernseher, wenn du dran bist.",
    cancel: "Abbrechen", addMine: "Song eintragen",
    added: "Eingetragen! Achte auf deinen Namen auf dem Bildschirm.", removed: "Entfernt.",
    found: n => n === 1 ? "1 Treffer." : `${n} Treffer.`,
    none: "Nichts gefunden. Versuch's mit dem Interpreten oder wünsch dir den Song unten.",
    wishTitle: "Song nicht gefunden?", wishText: "Sag uns Bescheid, wir machen ihn bis zu deinem Auftritt bereit.",
    wishPlaceholder: "Interpret – Song…", wishButton: "Wünschen",
    finding: "Wir prüfen, ob wir deinen Song machen können…", wished: "Eingetragen! Wir machen deinen Song jetzt bereit. Achte auf deinen Namen auf dem Bildschirm.",
    videoTitle: "Nur als Karaoke-Video",
    videoText: "Diesen Song können wir nicht selbst machen, weil es keinen getimten Text gibt. Stattdessen kann eine Karaoke-Version von YouTube laufen.",
    videoAdd: "Video eintragen",
    err: { limit: n => `Du hast schon ${n} Songs in der Warteschlange. Sing erst einen!`, duplicate: "Der Song steht schon auf deiner Liste.",
           unknown_song: "Den Song gibt es nicht mehr.", bad_name: "Bitte gib einen Namen ein.",
           forbidden: "Du kannst nur deine eigenen Songs entfernen.", not_found: "Der Song ist schon aus der Warteschlange.",
           empty: "Schreib, welchen Song du dir wünschst.", offline: "Gerade kein Internet, neue Songs gehen nicht. Nimm einen mit „Bereit“.",
           no_video: "Dafür gibt es keine Karaoke-Version. Versuch einen anderen Song.",
           full: "Die Warteschlange ist gerade voll. Versuch es nach ein paar Songs nochmal.",
           network: "Keine Verbindung zum Karaoke-Laptop. Bist du hier im WLAN?" },
  },
};

const $ = id => document.getElementById(id);
const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch {} },
};
const param = new URLSearchParams(location.search).get("lang");
let lang = ["en", "de"].includes(param) ? param : store.get("lang") || ((navigator.language || "").startsWith("de") ? "de" : "en");
let device = store.get("device");
if (!device) { device = Math.random().toString(36).slice(2) + Date.now().toString(36); store.set("device", device); }
let name = store.get("name") || "";
let state = null, pendingSong = null;
// What the list shows: a shelf, an artist's songs, or search results for what's typed.
let view = { kind: "shelf", shelf: "ready", page: 0 }, rows = [], artists = [], hasMore = false, seq = 0;

const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
const t = () => T[lang];

function toast(msg, bad) {
  const box = $("toast");
  box.textContent = msg; box.classList.toggle("bad", !!bad); box.classList.add("show");
  clearTimeout(toast.timer); toast.timer = setTimeout(() => box.classList.remove("show"), 3500);
}
function errorText(code) {
  const e = t().err[code] || t().err.network;
  return typeof e === "function" ? e(state ? state.songs_per_singer : 2) : e;
}
async function api(method, url, body) {
  let r;
  try { r = await fetch(url, { method, headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined }); }
  catch { throw "network"; }
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw data.error || "network";
  return data;
}

function applyLang() {
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-t]").forEach(n => { n.textContent = t()[n.dataset.t]; });
  document.querySelectorAll("[data-tp]").forEach(n => { n.placeholder = t()[n.dataset.tp]; n.setAttribute("aria-label", t()[n.dataset.tp]); });
  document.querySelectorAll("[data-tl]").forEach(n => n.setAttribute("aria-label", t()[n.dataset.tl]));
  document.querySelectorAll(".lang button").forEach(b => b.setAttribute("aria-pressed", b.dataset.lang === lang));
  renderChips(); renderList(); renderState();
}

// ---------------------------------------------------------------- finding a song

// Bold the letters that match what was typed. Folding keeps one character per character, so positions line up.
const fold1 = s => Array.from(s, c => c.normalize("NFD")[0].toLowerCase());
function marked(text, q) {
  const chars = Array.from(text), f = fold1(text).join(""), hit = chars.map(() => false);
  fold1(q || "").join("").split(/[^\p{L}\p{N}]+/u).filter(Boolean).forEach(tk => {
    for (let i = f.indexOf(tk); i >= 0; i = f.indexOf(tk, i + tk.length)) for (let k = i; k < i + tk.length; k++) hit[k] = true;
  });
  const out = [];
  chars.forEach((c, i) => {
    if (hit[i] && !hit[i - 1]) out.push(el("mark"));
    if (hit[i]) out[out.length - 1].textContent += c;
    else if (typeof out[out.length - 1] === "string") out[out.length - 1] += c;
    else out.push(c);
  });
  return out;
}

function renderChips() {
  const box = $("chips");
  box.hidden = view.kind === "search";
  const shown = SHELVES.filter(s => !state || state.shelves.includes(s));  // the lists staff chose for this venue
  const chips = view.kind === "artist" ? [el("button", "chip", `‹ ${t().back}`)] : shown.map(s => el("button", "chip", t().shelf[s]));
  chips.forEach((b, i) => {
    b.type = "button";
    if (view.kind === "artist") { b.onclick = () => openShelf("ready"); return; }
    b.setAttribute("aria-pressed", view.kind === "shelf" && view.shelf === shown[i]);
    b.onclick = () => openShelf(shown[i]);
  });
  box.replaceChildren(...chips);
}

function songRow(s, q) {
  const mineIds = new Set(state ? state.queue.filter(e => e.mine).map(e => e.song.title + "\n" + e.song.artist) : []);
  const mine = mineIds.has(s.title + "\n" + s.artist);
  const b = el("button", "row");
  b.type = "button"; b.disabled = mine; b.translate = false;
  const info = el("span", "info"), title = el("span", "t"), by = el("span", "a");
  title.append(...marked(s.title, q));
  by.append(...marked(s.artist, q), s.year ? `, ${s.year}` : "");
  info.append(title, by);
  if (s.lyric) info.append(el("span", "lyr", `♪ “${s.lyric}”`));
  const badges = el("span", "badges"), status = mine ? "mine" : s.status;
  badges.append(el("span", `badge ${status}`, t().badge[status]));
  if (s.duo) badges.append(el("span", "badge duet", t().badge.duet));
  b.append(info, badges);
  b.setAttribute("aria-label", `${s.title}, ${s.artist}. ${t().badge[status]}`);
  b.onclick = () => pick(s);
  const li = el("li"); li.append(b);
  return li;
}

function artistRow(a) {
  const b = el("button", "row artist");
  b.type = "button"; b.translate = false;
  const info = el("span", "info");
  info.append(el("span", "t"), el("span", "a", t().songCount(a.count)));
  info.firstChild.append(...marked(a.artist, view.q));
  b.append(info, el("span", "chev", "›"));
  b.onclick = () => openArtist(a.artist);
  const li = el("li"); li.append(b);
  return li;
}

function renderList() {
  const q = view.kind === "search" ? view.q : "";
  // the best songs first, then up to two artists ("Queen · 91 songs"), then the rest of the songs
  $("songs").replaceChildren(...rows.slice(0, 3).map(s => songRow(s, q)), ...artists.slice(0, 2).map(artistRow), ...rows.slice(3).map(s => songRow(s, q)));
  $("more").hidden = !hasMore;
  const hint = $("hint");
  hint.classList.toggle("heading", view.kind === "artist");
  if (view.kind === "search") hint.textContent = rows.length || artists.length ? t().found(rows.length) : t().none;
  else if (view.kind === "artist") hint.textContent = view.artist;
  else hint.textContent = rows.length ? "" : (t().shelfEmpty[view.shelf] || t().none);
}

async function openShelf(shelf, page = 0) {
  const my = ++seq;
  view = { kind: "shelf", shelf, page };
  try {
    const got = (await api("GET", `/api/browse?shelf=${encodeURIComponent(shelf)}&page=${page}`)).songs;
    if (my !== seq) return;
    rows = page ? rows.concat(got) : got; artists = []; hasMore = got.length === 30;
  } catch (code) { if (my === seq) toast(errorText(code), true); }
  renderChips(); renderList();
}
async function openArtist(artist) {
  const my = ++seq;
  view = { kind: "artist", artist };
  $("q").value = "";
  try {
    const got = (await api("GET", `/api/browse?artist=${encodeURIComponent(artist)}`)).songs;
    if (my !== seq) return;
    rows = got; artists = []; hasMore = false;
  } catch (code) { if (my === seq) toast(errorText(code), true); }
  renderChips(); renderList();
  window.scrollTo({ top: $("q").getBoundingClientRect().top + scrollY - 8 });
}
async function search() {
  const q = $("q").value.trim();
  if (!q) return openShelf(view.kind === "shelf" ? view.shelf : "ready");
  const my = ++seq;
  try {
    const got = await api("GET", `/api/search?q=${encodeURIComponent(q)}`);
    if (my !== seq) return;  // an older search answered late: the newer one wins
    view = { kind: "search", q }; rows = got.songs; artists = got.artists; hasMore = false;
  } catch (code) { if (my === seq) toast(errorText(code), true); return; }
  renderChips(); renderList();
}
let typing;
$("q").addEventListener("input", () => { clearTimeout(typing); typing = setTimeout(search, 150); });
$("q").addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); $("q").blur(); } });
$("more").onclick = () => openShelf(view.shelf, view.page + 1);

// ---------------------------------------------------------------- your songs and the stage

function renderState() {
  if (!state) return;
  document.title = state.pub_name;
  $("pub").textContent = state.pub_name;
  applyVenueLook(state.look);
  if (String(state.shelves) !== renderState.shelves) { renderState.shelves = String(state.shelves); renderChips(); }
  const stage = $("stage");
  const np = state.now_playing;
  if (np) {
    const [a, who, b] = t().stageOn(np.name, np.title);
    stage.replaceChildren(a, el("strong", null, who), b + t().waiting(state.queue.length));
  } else {
    stage.textContent = state.queue.length ? t().waiting(state.queue.length).trim() : t().stageFree;
  }
  $("me").hidden = !name;
  $("meText").textContent = name ? t().singingAs(name) : "";

  const tickets = [];
  if (np && np.mine) tickets.push(ticket(np, t().now, t().onNow, true));
  state.queue.forEach((e, i) => {
    if (!e.mine) return;
    tickets.push(ticket(e, String(i + 1), i === 0 ? t().next : t().before(i), false));
  });
  $("tickets").hidden = !tickets.length;
  $("ticketList").replaceChildren(...tickets);
}

function ticket(e, count, when, on) {
  const card = el("article", "ticket" + (on ? " on" : ""));
  const c = el("div", "count", count);
  if (!on) c.append(el("small", null, t().place));
  card.append(c);
  if (!on) {
    const rm = el("button", "remove", t().remove);
    rm.type = "button";
    rm.setAttribute("aria-label", `${t().remove}: ${e.song.title}`);
    rm.onclick = async () => {
      try { await api("DELETE", `/api/queue/${encodeURIComponent(e.id)}?device=${encodeURIComponent(device)}`); toast(t().removed); poll(); }
      catch (code) { toast(errorText(code), true); }
    };
    card.append(rm);
  }
  const song = el("p", "song", e.song.title), by = el("p", "by", e.song.artist);
  song.translate = by.translate = false;
  card.append(song, by, el("p", "when", when));
  if (!on && (e.status === "making" || e.status === "waiting")) {
    card.append(el("p", "ready", `${e.status === "making" ? t().makingPct(e.pct || 0) : t().waitingMake} ${t().whenReady}`));
    if (e.status === "making") { const bar = el("div", "bar"), fill = el("i"); fill.style.width = `${e.pct || 0}%`; bar.append(fill); card.append(bar); }
  }
  if (!on && e.status === "video") card.append(el("p", "ready", t().videoTicket));
  return card;
}

// ---------------------------------------------------------------- adding a song

function pick(song) {
  if (song.status === "video" && !song.video) { pendingSong = song; return $("videoDialog").showModal(); }
  pendingSong = song;
  if (name) return add();
  $("nameInput").value = "";
  $("nameDialog").showModal();
}
async function add() {
  const song = pendingSong; pendingSong = null;
  if (!song) return;
  try {
    if (song.wish) {
      toast(t().finding);
      await api("POST", "/api/wish", { text: song.wish, name, device });
      toast(t().wished);
      $("wishInput").value = "";
    } else {
      if (song.status !== "ready") toast(t().finding);
      await api("POST", "/api/queue", { name, device, catalog_id: song.id, video: !!song.video });
      toast(song.status === "ready" ? t().added : song.video ? t().added : t().wished);
    }
    $("q").value = "";
    poll();
    if (view.kind === "search") openShelf("ready");
    window.scrollTo({ top: 0, behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  } catch (code) {
    if (code === "no_lyrics") { pendingSong = song; $("videoDialog").showModal(); return; }
    toast(errorText(code), true);
  }
}

$("nameForm").addEventListener("submit", ev => {
  const v = $("nameInput").value.trim();
  if (!v) { ev.preventDefault(); toast(errorText("bad_name"), true); return; }
  name = v.slice(0, 24); store.set("name", name);
  renderState(); add();
});
$("nameCancel").onclick = () => { pendingSong = null; $("nameDialog").close(); };
$("rename").onclick = () => { pendingSong = null; $("nameInput").value = name; $("nameDialog").showModal(); };
$("videoCancel").onclick = () => { pendingSong = null; $("videoDialog").close(); };
$("videoAdd").onclick = () => { const s = pendingSong; $("videoDialog").close(); if (s) pick({ ...s, video: true }); };
document.querySelectorAll(".lang button").forEach(b => b.onclick = () => { lang = b.dataset.lang; store.set("lang", lang); applyLang(); });
$("wishForm").addEventListener("submit", async ev => {
  ev.preventDefault();
  const wish = $("wishInput").value.trim();
  if (!wish) return toast(errorText("empty"), true);
  pick({ wish });
});

async function poll() {
  try {
    state = await api("GET", `/api/state?device=${encodeURIComponent(device)}`);
    renderState();
    const mine = state.queue.filter(e => e.mine).map(e => e.song.title).join();
    if (mine !== poll.mine) { poll.mine = mine; renderList(); }  // redraw the list only when its badges change, so taps aren't lost
  } catch { /* the next poll retries */ }
}
(async function start() {
  applyLang();
  await poll();
  openShelf("ready");
  setInterval(poll, 2000);
})();
