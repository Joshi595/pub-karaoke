const T = {
  en: { title: "Karaoke staff", pinText: "Enter the staff PIN.", pin: "PIN", unlock: "Unlock", wrongPin: "Wrong PIN.", locked: "Too many wrong PINs. Wait a minute.",
        pinTooEasy: "From the internet, the staff page needs its own PIN. On the laptop, change \"pin\" in settings.json from 1234 and restart the app.",
        nobody: "Nobody is singing", idle: "The TV will start the next song by itself.",
        skip: "Skip", skipSure: "Tap again to skip", pause: "Pause", resume: "Resume",
        help: "Help vocals", helpNote: "The original singer, quietly underneath. Saved for this song.", volume: "Volume",
        upNext: "Up next", empty: "Nobody is waiting.", playNext: "Play next", remove: "Remove", removeSure: "Tap again",
        pinnedNote: "Plays next", offline: "Can't reach the karaoke laptop.",
        lyricsTiming: "Lyrics timing", earlier: "Earlier", later: "Later", inTime: "as made",
        nudged: s => `${Math.abs(s).toFixed(1)} s ${s > 0 ? "earlier" : "later"}`,
        nudgeNote: "If the words light up before or after the singing. Saved for this song.",
        venue: "Venue look", venueName: "Name on the screens", lookPick: "Look", accent: "Accent colour", accentReset: "Use the look's own",
        icon: "Icon", iconNote: "One emoji, shown in browser tabs.", shelvesPick: "Song lists on guests' phones",
        looks: { stage: ["Stage", "Velvet and a spotlight"], pub: ["Pub", "Bottle green and brass"], neon: ["Neon", "A late-night sign"], daylight: ["Daylight", "Bright, for daytime"] },
        shelf: { ready: "Ready now", here: "Popular here", top: "Top hits", classics: "Crowd favourites", irish: "Irish", german: "German",
                 schlager: "Schlager", "80s": "80s", rock: "Rock", country: "Country", duets: "Duets" },
        screen: "TV screen", layout: "Lyrics style", highlight: "Highlight", size: "Text size", position: "Position",
        theme: "Song look", nextLine: "Show the next line", dots: "Countdown dots before each verse", band: "Dark band behind the lyrics",
        delay: "Screen delay", delayNote: "Set once with the sync test: the TV picture and the speakers each add their own delay.",
        syncStart: "Start sync test", syncStop: "Stop sync test", preview: "Preview", rules: "Rules", perSinger: "Songs one person may have waiting",
        bad_setting: "That setting wasn't saved.",
        hideExplicit: "Hide songs marked explicit",
        autoDownload: "Make likely songs while the laptop is idle", diskLimit: "Stop making new songs when they use",
        languages: "Song languages guests can find (none ticked = all)",
        langNames: { English: "English", German: "German", French: "French", Spanish: "Spanish", Italian: "Italian", Dutch: "Dutch", Portuguese: "Portuguese" },
        songCare: "Songs", idleMaker: "The song maker has nothing to do.",
        makingNow: (what, stage, pct) => `Making ${what}: ${stage}, ${pct}%`,
        stages: { starting: "starting", lyrics: "finding the lyrics", search: "finding the recording", download: "downloading",
                  separate: "removing the vocals", timing: "timing the words", finish: "finishing" },
        nextUp: list => `Next: ${list.join(" · ")}`,
        weakTitle: "Timing may be off", weakNote: "Fewer than half of the lines were timed by ear. Re-time them, or delete the song and pick it again.",
        failedTitle: "Couldn't be made", why: { no_lyrics: "No timed lyrics anywhere", failed: "No matching recording found" },
        retime: "Re-time", del: "Delete", delSure: "Tap again", retry: "Try again", none: "None.", timed: p => p == null ? "Made before timing was checked" : `${Math.round(p * 100)}% timed by ear`,
        disk: gb => `The songs use ${gb} GB.`,
        opts: { layout: { auto: "From the song's look", classic: "Two lines", scroll: "Scrolling", bigline: "One big line", ball: "Bouncing ball" },
                library_max_gb: { 5: "5 GB", 10: "10 GB", 20: "20 GB", 50: "50 GB", 100: "100 GB", 200: "200 GB" },
                highlight: { auto: "From the song's look", wipe: "Colour wipe", glow: "Glow", pop: "Pop" },
                size: { S: "Small", M: "Medium", L: "Large", XL: "Extra large" }, position: { middle: "Middle", lower: "Lower third" },
                theme: { auto: "Matches each song", celtic: "Irish", neon80s: "80s neon", disco: "Disco", rock: "Rock", ballad: "Ballad", pop: "Pop", cover: "Album colours" } } },
  de: { title: "Karaoke-Personal", pinText: "Gib die Personal-PIN ein.", pin: "PIN", unlock: "Entsperren", wrongPin: "Falsche PIN.", locked: "Zu viele falsche PINs. Bitte eine Minute warten.",
        pinTooEasy: "Über das Internet braucht die Personal-Seite eine eigene PIN. Auf dem Laptop in settings.json \"pin\" von 1234 ändern und die App neu starten.",
        nobody: "Gerade singt niemand", idle: "Der Fernseher startet den nächsten Song von selbst.",
        skip: "Überspringen", skipSure: "Nochmal tippen zum Überspringen", pause: "Pause", resume: "Weiter",
        help: "Hilfsgesang", helpNote: "Der Originalgesang, leise im Hintergrund. Wird für diesen Song gespeichert.", volume: "Lautstärke",
        upNext: "Als Nächstes", empty: "Niemand wartet.", playNext: "Als Nächstes", remove: "Entfernen", removeSure: "Nochmal tippen",
        pinnedNote: "Kommt als Nächstes", offline: "Keine Verbindung zum Karaoke-Laptop.",
        lyricsTiming: "Text-Timing", earlier: "Früher", later: "Später", inTime: "wie erstellt",
        nudged: s => `${Math.abs(s).toFixed(1).replace(".", ",")} s ${s > 0 ? "früher" : "später"}`,
        nudgeNote: "Wenn die Wörter vor oder nach dem Gesang aufleuchten. Wird für diesen Song gespeichert.",
        venue: "Aussehen", venueName: "Name auf den Bildschirmen", lookPick: "Stil", accent: "Akzentfarbe", accentReset: "Farbe des Stils",
        icon: "Symbol", iconNote: "Ein Emoji, erscheint im Browser-Tab.", shelvesPick: "Songlisten auf den Handys der Gäste",
        looks: { stage: ["Bühne", "Samt und Scheinwerfer"], pub: ["Pub", "Flaschengrün und Messing"], neon: ["Neon", "Leuchtreklame bei Nacht"], daylight: ["Tageslicht", "Hell, für tagsüber"] },
        shelf: { ready: "Sofort singbar", here: "Beliebt hier", top: "Top-Hits", classics: "Publikumslieblinge", irish: "Irisch", german: "Deutsch",
                 schlager: "Schlager", "80s": "80er", rock: "Rock", country: "Country", duets: "Duette" },
        screen: "Fernseher", layout: "Textdarstellung", highlight: "Hervorhebung", size: "Schriftgröße", position: "Position",
        theme: "Song-Stil", nextLine: "Nächste Zeile zeigen", dots: "Countdown-Punkte vor jeder Strophe", band: "Dunkles Band hinter dem Text",
        delay: "Bildverzögerung", delayNote: "Einmal mit dem Synchrontest einstellen: Fernseher und Boxen haben jeweils eine eigene Verzögerung.",
        syncStart: "Synchrontest starten", syncStop: "Synchrontest beenden", preview: "Vorschau", rules: "Regeln", perSinger: "Songs, die eine Person gleichzeitig eintragen darf",
        bad_setting: "Diese Einstellung wurde nicht gespeichert.",
        hideExplicit: "Songs mit anstößigem Text ausblenden",
        autoDownload: "Wahrscheinliche Songs vorbereiten, wenn der Laptop nichts zu tun hat", diskLimit: "Keine neuen Songs mehr, wenn sie belegen",
        languages: "Sprachen, die Gäste finden (nichts angehakt = alle)",
        langNames: { English: "Englisch", German: "Deutsch", French: "Französisch", Spanish: "Spanisch", Italian: "Italienisch", Dutch: "Niederländisch", Portuguese: "Portugiesisch" },
        songCare: "Songs", idleMaker: "Der Song-Macher hat gerade nichts zu tun.",
        makingNow: (what, stage, pct) => `Wird gemacht: ${what}: ${stage}, ${pct} %`,
        stages: { starting: "startet", lyrics: "sucht den Text", search: "sucht die Aufnahme", download: "lädt herunter",
                  separate: "entfernt den Gesang", timing: "timt die Wörter", finish: "schließt ab" },
        nextUp: list => `Danach: ${list.join(" · ")}`,
        weakTitle: "Timing evtl. ungenau", weakNote: "Weniger als die Hälfte der Zeilen wurde nach Gehör getimt. Neu timen, oder den Song löschen und neu wählen.",
        failedTitle: "Konnte nicht gemacht werden", why: { no_lyrics: "Nirgends getimter Text", failed: "Keine passende Aufnahme gefunden" },
        retime: "Neu timen", del: "Löschen", delSure: "Nochmal tippen", retry: "Nochmal versuchen", none: "Keine.", timed: p => p == null ? "Vor der Timing-Prüfung gemacht" : `${Math.round(p * 100)} % nach Gehör getimt`,
        disk: gb => `Die Songs belegen ${String(gb).replace(".", ",")} GB.`,
        opts: { layout: { auto: "Passend zum Song", classic: "Zwei Zeilen", scroll: "Laufend", bigline: "Eine große Zeile", ball: "Hüpfender Ball" },
                library_max_gb: { 5: "5 GB", 10: "10 GB", 20: "20 GB", 50: "50 GB", 100: "100 GB", 200: "200 GB" },
                highlight: { auto: "Passend zum Song", wipe: "Farbverlauf", glow: "Leuchten", pop: "Hüpfen" },
                size: { S: "Klein", M: "Mittel", L: "Groß", XL: "Sehr groß" }, position: { middle: "Mitte", lower: "Unteres Drittel" },
                theme: { auto: "Passend zu jedem Song", celtic: "Irisch", neon80s: "80er-Neon", disco: "Disco", rock: "Rock", ballad: "Ballade", pop: "Pop", cover: "Albumfarben" } } },
};
const $ = id => document.getElementById(id);
const store = (k, v) => { try { return v === undefined ? sessionStorage.getItem(k) : sessionStorage.setItem(k, v); } catch { return null; } };
const local = (k, v) => { try { return v === undefined ? localStorage.getItem(k) : localStorage.setItem(k, v); } catch { return null; } };
let lang = local("lang") || ((navigator.language || "").startsWith("de") ? "de" : "en");
let pin = store("pin") || "", state = null, dragging = { help: false, vol: false, delay: false };
const t = () => T[lang];
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };

function toast(msg) { const b = $("toast"); b.textContent = msg; b.classList.add("show"); clearTimeout(toast.h); toast.h = setTimeout(() => b.classList.remove("show"), 3000); }
async function admin(path, body) {
  const r = await fetch(`/api/admin/${path}`, { method: "POST", headers: { "Content-Type": "application/json", "X-Pin": pin }, body: JSON.stringify(body || {}) });
  if (r.status === 403) { lockUp(); throw "pin"; }
  if (!r.ok) throw (await r.json().catch(() => ({}))).error || "error";
  poll();
}
function lockUp() { pin = ""; store("pin", ""); $("lock").hidden = false; $("panel").hidden = true; }

// Two taps for anything that interrupts a singer.
function confirmTap(button, sureText, action) {
  if (button.dataset.armed) { delete button.dataset.armed; button.classList.remove("armed"); return action(); }
  button.dataset.armed = "1"; button.classList.add("armed"); const label = button.textContent; button.textContent = sureText;
  setTimeout(() => { if (button.dataset.armed) { delete button.dataset.armed; button.classList.remove("armed"); button.textContent = label; } }, 3000);
}

function debounce(fn, ms) { let h; return (...a) => { clearTimeout(h); h = setTimeout(() => fn(...a), ms); }; }
const sendHelp = debounce(v => admin("help_vocals", { level: v / 100 }).finally(() => dragging.help = false), 300);
const sendVol = debounce(v => admin("volume", { level: v / 100 }).finally(() => dragging.vol = false), 300);

function applyLang() {
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-t]").forEach(n => n.textContent = t()[n.dataset.t]);
  document.querySelectorAll("[data-tp]").forEach(n => { n.placeholder = t()[n.dataset.tp]; n.setAttribute("aria-label", t()[n.dataset.tp]); });
  document.querySelectorAll(".lang button").forEach(b => b.setAttribute("aria-pressed", b.dataset.lang === lang));
  document.querySelectorAll("select[data-key]").forEach(s => {
    const labels = t().opts[s.dataset.key] || Object.fromEntries([1, 2, 3, 4, 5].map(n => [n, String(n)]));
    s.replaceChildren(...Object.entries(labels).map(([v, label]) => new Option(label, v)));
  });
  $("langs").replaceChildren(...Object.entries(t().langNames).map(([value, label]) => {
    const box = el("label", "check"), input = el("input");
    input.type = "checkbox"; input.value = value;
    input.onchange = () => saveSetting("languages", [...document.querySelectorAll("#langs input:checked")].map(i => i.value), true);
    box.append(input, el("span", null, label));
    return box;
  }));
  $("looks").replaceChildren(...Object.entries(t().looks).map(([value, [name, note]]) => {
    const tile = el("label", "look"), input = el("input");
    tile.dataset.look = value;
    input.type = "radio"; input.name = "look"; input.value = value;
    input.onchange = () => saveSetting("look", value, true);
    tile.append(input, el("b", null, name), el("small", null, note), el("i"));
    return tile;
  }));
  $("shelfBoxes").replaceChildren(...Object.entries(t().shelf).map(([value, label]) => {
    const box = el("label", "check"), input = el("input");
    input.type = "checkbox"; input.value = value;
    input.onchange = () => saveSetting("shelves", [...document.querySelectorAll("#shelfBoxes input:checked")].map(i => i.value), true);
    box.append(input, el("span", null, label));
    return box;
  }));
  render(); renderCare();
}

function render() {
  if (!state) return;
  const np = state.now_playing;
  $("who").textContent = np ? np.name : t().nobody;
  $("what").textContent = np ? `${np.title}, ${np.artist}` : t().idle;
  $("skip").disabled = !np;
  if ($("skip").dataset.armed && (!np || np.id !== skipId)) { delete $("skip").dataset.armed; $("skip").classList.remove("armed"); }
  if (!$("skip").dataset.armed) $("skip").textContent = t().skip;
  $("pause").textContent = state.paused ? t().resume : t().pause;
  $("help").disabled = !np;
  if (!dragging.help) $("help").value = Math.round((state.help_vocals ?? 0.25) * 100);
  if (!dragging.vol) $("vol").value = Math.round(state.volume * 100);
  $("helpOut").textContent = `${$("help").value}%`;
  $("volOut").textContent = `${$("vol").value}%`;
  const timed = !!(np && np.song_id);  // a YouTube video has no lyrics of ours to move
  $("earlier").disabled = $("later").disabled = !timed;
  $("nudgeOut").textContent = !timed ? "" : state.nudge ? t().nudged(state.nudge) : t().inTime;
  const d = state.display;
  document.querySelectorAll("#screen [data-key], #rules [data-key]").forEach(el => {
    if (el === document.activeElement) return;  // don't fight the staff member mid-change
    const v = el.dataset.top ? (state.rules || {})[el.dataset.key] ?? state[el.dataset.key] : d[el.dataset.key];
    if (el.type === "checkbox") el.checked = !!v; else el.value = String(v);
  });
  document.querySelectorAll("#langs input").forEach(i => { if (i !== document.activeElement) i.checked = (state.rules?.languages || []).includes(i.value); });
  applyVenueLook(state.look);
  const idle = n => n !== document.activeElement;  // don't fight the staff member mid-change
  if (idle($("venueName"))) $("venueName").value = state.pub_name;
  if (idle($("icon"))) $("icon").value = state.look.icon;
  if (idle($("accent"))) $("accent").value = (state.look.accent || getComputedStyle(document.documentElement).getPropertyValue("--accent").trim()).toLowerCase();
  document.querySelectorAll("#looks input").forEach(i => i.checked = i.value === state.look.look);
  document.querySelectorAll("#shelfBoxes input").forEach(i => { if (idle(i)) i.checked = state.shelves.includes(i.value); });
  if (!dragging.delay) $("delay").value = d.screen_delay_ms;
  $("delayOut").textContent = `${$("delay").value} ms`;
  $("syncTest").textContent = state.synctest ? t().syncStop : t().syncStart;
  const q = new URLSearchParams({ demo: d.theme === "auto" ? "cover" : d.theme, size: d.size });
  if (d.layout !== "auto") q.set("layout", d.layout);
  if (d.highlight !== "auto") q.set("highlight", d.highlight);
  $("preview").href = `/tv?${q}`;
  $("nextTitle").replaceChildren(t().upNext + " ", el("span", "count", `(${state.queue.length})`));
  if (document.querySelector(".queue [data-armed]")) return; // don't redraw under a pending second tap
  $("queue").replaceChildren(...(state.queue.length ? state.queue.map(e => {
    const li = el("li");
    const name = el("span", "name", e.name);
    if (e.pinned) name.append(" ", el("span", "pinned", t().pinnedNote));
    const acts = el("div", "acts");
    const up = el("button", "btn", t().playNext); up.type = "button"; up.disabled = e.pinned;
    up.onclick = () => admin("pin", { id: e.id });
    const rm = el("button", "btn", t().remove); rm.type = "button";
    rm.onclick = () => confirmTap(rm, t().removeSure, () => admin("remove", { id: e.id }));
    acts.append(up, rm);
    const song = el("span", "song", `${e.song.title}, ${e.song.artist}`); song.translate = false;
    li.append(name, song, acts);
    return li;
  }) : [el("li", "empty", t().empty)]));
}

async function poll() {
  try { state = await (await fetch("/api/state")).json(); render(); }
  catch { toast(t().offline); }
  if ($("songCare").open) loadCare();
}

// Songs: what the song maker is doing, and the songs that need a hand.
let care = null;
async function loadCare() {
  const r = await fetch("/api/admin/songs", { headers: { "X-Pin": pin } }).catch(() => null);
  if (r && r.ok) { care = await r.json(); renderCare(); }
}
function renderCare() {
  if (!care || document.querySelector(".care [data-armed]")) return;  // don't redraw under a pending second tap
  const m = care.making;
  const what = m.wish ? (m.wish.startsWith("RETIME ") ? m.wish.slice(7) : m.wish) : "";
  $("makingNow").textContent = m.wish ? t().makingNow(what, t().stages[m.stage] || m.stage, m.pct || 0) : t().idleMaker;
  $("nextUp").textContent = care.next.length ? t().nextUp(care.next.slice(0, 3)) : "";
  const item = (label, note, buttons) => {
    const li = el("li"), info = el("span", null, label), acts = el("div", "acts");
    info.translate = false;
    info.append(el("small", null, note));
    acts.append(...buttons);
    li.append(info, acts);
    return li;
  };
  const button = (text, onclick, song) => {  // the song's name too, for screen readers: every row has the same buttons
    const b = el("button", "btn", text); b.type = "button"; b.onclick = onclick; b.setAttribute("aria-label", `${text}: ${song}`); return b;
  };
  const after = p => p.then(loadCare, () => {});
  $("weakList").replaceChildren(...(care.weak.length ? care.weak.map(s => {
    const del = button(t().del, () => confirmTap(del, t().delSure, () => after(admin("delete_song", { slug: s.slug }))), s.name);
    return item(s.name, t().timed(s.aligned), [button(t().retime, () => after(admin("retime", { slug: s.slug })), s.name), del]);
  }) : [el("li", "empty", t().none)]));
  $("failedList").replaceChildren(...(care.failed.length ? care.failed.map(s =>
    item(`${s.artist} - ${s.title}`, t().why[s.why] || s.why, [button(t().retry, () => after(admin("retry", { id: s.id })), `${s.artist} - ${s.title}`)])
  ) : [el("li", "empty", t().none)]));
  $("disk").textContent = t().disk(care.disk_gb);
}
$("songCare").addEventListener("toggle", () => { if ($("songCare").open) loadCare(); });

$("pinForm").addEventListener("submit", async ev => {
  ev.preventDefault();
  pin = $("pin").value.trim();
  const r = await fetch("/api/admin/check", { method: "POST", headers: { "X-Pin": pin } }).catch(() => null);
  if (!r) return toast(t().offline);
  if (!r.ok) { $("pin").value = ""; return toast(r.status === 409 ? t().pinTooEasy : r.status === 429 ? t().locked : t().wrongPin); }
  store("pin", pin); unlock();
});
function unlock() { $("lock").hidden = true; $("panel").hidden = false; poll(); }
// the song is chosen at the first tap: if it changes before the second tap, that tap must not skip the new singer
let skipId = null;
$("skip").onclick = () => {
  if (!$("skip").dataset.armed) skipId = state.now_playing && state.now_playing.id;
  confirmTap($("skip"), t().skipSure, () => admin("skip", { id: skipId }));
};
$("pause").onclick = () => admin("pause", { paused: !state.paused });
$("help").oninput = e => { dragging.help = true; $("helpOut").textContent = `${e.target.value}%`; sendHelp(+e.target.value); };
$("vol").oninput = e => { dragging.vol = true; $("volOut").textContent = `${e.target.value}%`; sendVol(+e.target.value); };
const saveSetting = (key, value, top) => admin("settings", top ? { [key]: value } : { display: { [key]: value } }).catch(code => code !== "pin" && toast(t().bad_setting));
document.querySelectorAll("#screen [data-key], #rules [data-key]").forEach(el => el.onchange = () => {
  const v = el.type === "checkbox" ? el.checked : el.dataset.top ? +el.value : el.value;
  saveSetting(el.dataset.key, v, el.dataset.top);
});
const sendDelay = debounce(v => saveSetting("screen_delay_ms", v).finally(() => dragging.delay = false), 300);
$("delay").oninput = e => { dragging.delay = true; $("delayOut").textContent = `${e.target.value} ms`; sendDelay(+e.target.value); };
$("venueName").onchange = e => e.target.value.trim() && saveSetting("pub_name", e.target.value.trim(), true);
$("icon").onchange = e => e.target.value.trim() && saveSetting("icon", e.target.value.trim(), true);
$("accent").onchange = e => saveSetting("accent", e.target.value, true);
$("accentReset").onclick = () => saveSetting("accent", "", true);
$("earlier").onclick = () => admin("nudge", { delta: 0.1 });
$("later").onclick = () => admin("nudge", { delta: -0.1 });
$("syncTest").onclick = () => admin("synctest", { on: !state.synctest });
document.querySelectorAll(".lang button").forEach(b => b.onclick = () => { lang = b.dataset.lang; local("lang", lang); applyLang(); });

applyLang();
if (pin) unlock();
setInterval(() => { if (pin) poll(); }, 2000);
