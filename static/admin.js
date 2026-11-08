const T = {
  en: { title: "Karaoke staff", pinText: "Enter the staff PIN.", pin: "PIN", unlock: "Unlock", wrongPin: "Wrong PIN.", locked: "Too many wrong PINs. Wait a minute.",
        pinTooEasy: "From the internet, the staff page needs its own PIN. On the laptop, change \"pin\" in settings.json from 1234 and restart the app.",
        nobody: "Nobody is singing", idle: "The TV will start the next song by itself.",
        skip: "Skip", skipSure: "Tap again to skip", restart: "Start again", restartSure: "Tap again to start over", pause: "Pause", resume: "Resume",
        help: "Help vocals", helpNote: "The original singer, quietly underneath. Saved for this song.", volume: "Volume",
        upNext: "Up next", empty: "Nobody is waiting.", playNext: "Play next", remove: "Remove", removeSure: "Tap again",
        pinnedNote: "Plays next", offline: "Can't reach the karaoke laptop.",
        lyricsTiming: "Lyrics timing", earlier: "Earlier", later: "Later", inTime: "as made",
        nudged: s => `${Math.abs(s).toFixed(1)} s ${s > 0 ? "earlier" : "later"}`,
        nudgeNote: "If the words light up before or after the singing. Saved for this song.",
        venue: "Venue look", venueName: "Name on the screens", lookPick: "Look", accent: "Accent colour", accentReset: "Use the look's own",
        icon: "Icon", iconNote: "One emoji, shown in browser tabs.", shelvesPick: "Song lists on guests' phones",
        logo: "Logos", logoFor: "Add a logo for", everyLook: "Every look", logoFile: "Logo picture",
        logoNote: "JPG, PNG or WebP, up to 1 MB. Give a look logos of its own (Halloween ones, say): on those nights they show instead, and the TV changes between them with each song.",
        bad_image: "That file isn't a JPG, PNG or WebP picture.", logoTooBig: "That picture is over 1 MB. Save it smaller and try again.",
        too_many_logos: "That's 12 logos already. Remove one first.",
        nights: "Special nights", nightsNote: "On these dates every screen switches to that look by itself, from 6 am until 6 am the next morning.",
        addNight: "Add a night", yearly: "Every year", nightDate: "Date of the night",
        themeTitle: "Tonight's theme", everyday: name => `${name} (everyday)`,
        tonightNote: (same, everyday) => same ? "Your everyday look. Change it for good, or plan nights like Halloween, under Venue look."
                                              : `For tonight only: from 6 am it's ${everyday} again.`,
        everywhere: "Use it everywhere: for every song on the TV, on the guests' phones, and in what the screens say",
        looks: { stage: ["Stage", "Velvet and a spotlight"], pub: ["Pub", "Bottle green and brass"], neon: ["Neon", "A late-night sign"], daylight: ["Daylight", "Bright, for daytime"],
                 halloween: ["Halloween", "Pumpkins, bats and a full moon"] },
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
                theme: { auto: "Matches each song", venue: "Tonight's theme", celtic: "Irish", neon80s: "80s neon", disco: "Disco", rock: "Rock", ballad: "Ballad", pop: "Pop", cover: "Album colours", halloween: "Halloween" } } },
  de: { title: "Karaoke-Personal", pinText: "Gib die Personal-PIN ein.", pin: "PIN", unlock: "Entsperren", wrongPin: "Falsche PIN.", locked: "Zu viele falsche PINs. Bitte eine Minute warten.",
        pinTooEasy: "Über das Internet braucht die Personal-Seite eine eigene PIN. Auf dem Laptop in settings.json \"pin\" von 1234 ändern und die App neu starten.",
        nobody: "Gerade singt niemand", idle: "Der Fernseher startet den nächsten Song von selbst.",
        skip: "Überspringen", skipSure: "Nochmal tippen zum Überspringen", restart: "Von vorn", restartSure: "Nochmal tippen: von vorn", pause: "Pause", resume: "Weiter",
        help: "Hilfsgesang", helpNote: "Der Originalgesang, leise im Hintergrund. Wird für diesen Song gespeichert.", volume: "Lautstärke",
        upNext: "Als Nächstes", empty: "Niemand wartet.", playNext: "Als Nächstes", remove: "Entfernen", removeSure: "Nochmal tippen",
        pinnedNote: "Kommt als Nächstes", offline: "Keine Verbindung zum Karaoke-Laptop.",
        lyricsTiming: "Text-Timing", earlier: "Früher", later: "Später", inTime: "wie erstellt",
        nudged: s => `${Math.abs(s).toFixed(1).replace(".", ",")} s ${s > 0 ? "früher" : "später"}`,
        nudgeNote: "Wenn die Wörter vor oder nach dem Gesang aufleuchten. Wird für diesen Song gespeichert.",
        venue: "Aussehen", venueName: "Name auf den Bildschirmen", lookPick: "Stil", accent: "Akzentfarbe", accentReset: "Farbe des Stils",
        icon: "Symbol", iconNote: "Ein Emoji, erscheint im Browser-Tab.", shelvesPick: "Songlisten auf den Handys der Gäste",
        logo: "Logos", logoFor: "Logo hinzufügen für", everyLook: "Alle Stile", logoFile: "Logo-Bild",
        logoNote: "JPG, PNG oder WebP, bis 1 MB. Ein Stil kann eigene Logos haben (z. B. für Halloween): an solchen Abenden erscheinen sie stattdessen, und der Fernseher wechselt bei jedem Song.",
        bad_image: "Diese Datei ist kein JPG-, PNG- oder WebP-Bild.", logoTooBig: "Das Bild ist größer als 1 MB. Bitte kleiner speichern und nochmal versuchen.",
        too_many_logos: "Schon 12 Logos. Bitte erst eins entfernen.",
        nights: "Besondere Abende", nightsNote: "An diesen Tagen wechseln alle Bildschirme von selbst zu diesem Stil, von 6 Uhr bis 6 Uhr am nächsten Morgen.",
        addNight: "Abend hinzufügen", yearly: "Jedes Jahr", nightDate: "Datum des Abends",
        themeTitle: "Thema heute Abend", everyday: name => `${name} (sonst)`,
        tonightNote: (same, everyday) => same ? "Euer gewohnter Stil. Dauerhaft ändern oder Abende wie Halloween planen: unter Aussehen."
                                              : `Nur für heute Abend: ab 6 Uhr wieder ${everyday}.`,
        everywhere: "Überall verwenden: für jeden Song am Fernseher, auf den Handys der Gäste und in den Texten der Bildschirme",
        looks: { stage: ["Bühne", "Samt und Scheinwerfer"], pub: ["Pub", "Flaschengrün und Messing"], neon: ["Neon", "Leuchtreklame bei Nacht"], daylight: ["Tageslicht", "Hell, für tagsüber"],
                 halloween: ["Halloween", "Kürbisse, Fledermäuse und Vollmond"] },
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
                theme: { auto: "Passend zu jedem Song", venue: "Thema des Abends", celtic: "Irisch", neon80s: "80er-Neon", disco: "Disco", rock: "Rock", ballad: "Ballade", pop: "Pop", cover: "Albumfarben", halloween: "Halloween" } } },
};
Object.assign(T.en, { eventTitle: "Tonight's event", newEvent: "Start a fresh night", newEventSure: "Tap again to clear the queue",
  closeRequests: "Close requests", openRequests: "Reopen requests", requestOpen: "Requests open", requestClosed: "Requests closed",
  healthTitle: "System status", failedAction: "The change did not complete. Check the connection and try again.",
  storageFull: "Storage is full. Free some disk space before preparing more songs.", backupProblem: "Backup needs attention", backupOk: "Last backup",
  noBackup: "No successful backup yet", online: "Internet link connected", localOnly: "Local access only — internet link unavailable", workerUnavailable: "Song maker is not installed" });
Object.assign(T.de, { eventTitle: "Heutiger Abend", newEvent: "Neuen Abend starten", newEventSure: "Nochmal tippen: Warteschlange löschen",
  closeRequests: "Songwünsche schließen", openRequests: "Songwünsche wieder öffnen", requestOpen: "Songwünsche offen", requestClosed: "Songwünsche geschlossen",
  healthTitle: "Systemstatus", failedAction: "Die Änderung wurde nicht abgeschlossen. Verbindung prüfen und erneut versuchen.",
  storageFull: "Speicher voll. Vor weiteren Songs bitte Speicherplatz freigeben.", backupProblem: "Sicherung benötigt Aufmerksamkeit", backupOk: "Letzte Sicherung",
  noBackup: "Noch keine erfolgreiche Sicherung", online: "Internetverbindung aktiv", localOnly: "Nur lokaler Zugriff — Internetlink nicht verfügbar", workerUnavailable: "Song-Macher ist nicht installiert" });

const $ = id => document.getElementById(id);
const store = (k, v) => { try { return v === undefined ? sessionStorage.getItem(k) : sessionStorage.setItem(k, v); } catch { return null; } };
const local = (k, v) => { try { return v === undefined ? localStorage.getItem(k) : localStorage.setItem(k, v); } catch { return null; } };
let lang = local("lang") || ((navigator.language || "").startsWith("de") ? "de" : "en");
let pin = store("pin") || "", state = null, dragging = { help: false, vol: false, delay: false };
const t = () => voiced(T[lang], lang);  // the title in tonight's voice, when the theme is everywhere (look.js)
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };

function toast(msg) { const b = $("toast"); b.textContent = msg; b.classList.add("show"); clearTimeout(toast.h); toast.h = setTimeout(() => b.classList.remove("show"), 3000); }
async function admin(path, body, method = "POST") {
  try {
  const file = body instanceof Blob;  // the logo goes as it is; everything else as JSON
  const r = await fetch(`/api/admin/${path}`, { method, headers: { "Content-Type": file ? body.type : "application/json", "X-Pin": pin },
                                                 signal: AbortSignal.timeout(15000), body: file ? body : JSON.stringify(body || {}) });
  if (r.status === 403) { lockUp(); throw "pin"; }
  if (!r.ok) throw (await r.json().catch(() => ({}))).error || "error";
  poll();
  return true;
  } catch (code) {
    if (code !== "pin") toast(code === "locked" ? t().locked : t()[code] || t().failedAction);
    return false;
  }
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
  document.querySelectorAll("[data-tl]").forEach(n => n.setAttribute("aria-label", t()[n.dataset.tl]));
  const forLook = $("logoLook").value;
  $("logoLook").replaceChildren(new Option(t().everyLook, ""), ...Object.entries(t().looks).map(([v, [name]]) => new Option(name, v)));
  $("logoLook").value = forLook;
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
  $("eventStatus").textContent = state.event?.open === false ? t().requestClosed : t().requestOpen;
  $("eventToggle").textContent = state.event?.open === false ? t().openRequests : t().closeRequests;
  $("newEvent").disabled = !!np;
  $("who").textContent = np ? np.name : t().nobody;
  $("what").textContent = np ? `${np.title}, ${np.artist}` : t().idle;
  for (const [b, id, text] of [[$("skip"), skipId, t().skip], [$("restart"), restartId, t().restart]]) {
    b.disabled = !np;
    if (b.dataset.armed && (!np || np.id !== id)) { delete b.dataset.armed; b.classList.remove("armed"); }
    if (!b.dataset.armed) b.textContent = text;
  }
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
  const before = voice;
  useVoice(state);
  if (voice !== before) return applyLang();  // tonight's words changed (applyLang comes back here)
  const idle = n => n !== document.activeElement;  // don't fight the staff member mid-change
  if (idle($("venueName"))) $("venueName").value = state.pub_name;
  if (idle($("icon"))) $("icon").value = state.look.icon;
  if (idle($("accent"))) $("accent").value = (state.look.accent || getComputedStyle(document.documentElement).getPropertyValue("--accent").trim()).toLowerCase();
  document.querySelectorAll("#looks input").forEach(i => i.checked = i.value === state.look.look);  // the everyday look
  const everyday = state.look.look, shown = state.look.night || everyday, sel = $("tonightLook");
  if (sel.dataset.key !== lang + everyday) {  // the everyday look is marked as such
    sel.dataset.key = lang + everyday;
    sel.replaceChildren(...Object.entries(t().looks).map(([v, [name]]) => new Option(v === everyday ? t().everyday(name) : name, v)));
  }
  if (idle(sel)) sel.value = shown;
  $("tonightNote").textContent = t().tonightNote(shown === everyday, (t().looks[everyday] || [everyday])[0]);
  if (idle($("everywhere"))) $("everywhere").checked = d.theme === "venue";
  themeBanner($("themeBanner"), shown);
  renderNights();
  renderLogos();
  document.querySelectorAll("#shelfBoxes input").forEach(i => { if (idle(i)) i.checked = state.shelves.includes(i.value); });
  if (!dragging.delay) $("delay").value = d.screen_delay_ms;
  $("delayOut").textContent = `${$("delay").value} ms`;
  $("syncTest").textContent = state.synctest ? t().syncStop : t().syncStart;
  const q = new URLSearchParams({ demo: d.theme === "auto" ? "cover" : d.theme === "venue" ? (LOOK_THEMES[shown] || ["cover"])[0] : d.theme, size: d.size });
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

// Logos: a row each, with the look it is for.
function renderLogos() {
  const box = $("logos"), key = JSON.stringify([state.logos, lang]);
  if (box.dataset.key === key || box.querySelector("[data-armed]")) return;  // don't redraw under a pending second tap
  box.dataset.key = key;
  box.replaceChildren(...state.logos.map(e => {
    const li = el("li"), img = el("img", "thumb"), name = e.look ? (t().looks[e.look] || [e.look])[0] : t().everyLook;
    const rm = el("button", "btn", t().remove);
    img.src = `/logo/${encodeURIComponent(e.file)}`; img.alt = "";
    rm.type = "button"; rm.setAttribute("aria-label", `${t().remove}: ${name}`);
    rm.onclick = () => confirmTap(rm, t().removeSure, () => admin("logo", { file: e.file }, "DELETE").catch(failed));
    li.append(img, el("span", null, name), rm);
    return li;
  }));
}

// Special nights: a row each; every change saves the whole list, like the song lists.
const saveNights = list => saveSetting("nights", list, true);
const today = () => { const d = new Date(); return [d.getFullYear(), d.getMonth() + 1, d.getDate()].map(n => String(n).padStart(2, "0")).join("-"); };
function renderNights() {
  const a = document.activeElement, box = $("nights");
  if (box.contains(a) && a.tagName !== "BUTTON") return;  // don't fight the staff member mid-change
  const key = JSON.stringify([state.nights, lang]);
  if (box.dataset.key === key) return;
  box.dataset.key = key;
  box.replaceChildren(...state.nights.map((n, i) => {
    const li = el("li"), day = el("input", "text"), look = el("select"), every = el("label", "check"), yearly = el("input"), rm = el("button", "btn", t().remove);
    day.type = "date"; day.required = true; day.value = n.date; day.setAttribute("aria-label", t().nightDate);
    look.append(...Object.entries(t().looks).map(([v, [name]]) => new Option(name, v))); look.value = n.look; look.setAttribute("aria-label", t().lookPick);
    yearly.type = "checkbox"; yearly.checked = n.yearly;
    every.append(yearly, el("span", null, t().yearly));
    rm.type = "button"; rm.setAttribute("aria-label", `${t().remove}: ${n.date}`);
    const change = edit => saveNights(state.nights.map((m, j) => (j === i ? { ...m, ...edit } : m)));
    day.onchange = () => day.value && change({ date: day.value });
    look.onchange = () => change({ look: look.value });
    yearly.onchange = () => change({ yearly: yearly.checked });
    rm.onclick = () => saveNights(state.nights.filter((_, j) => j !== i));
    li.append(day, look, every, rm);
    return li;
  }));
}

async function poll() {
  if (poll.active) return;
  poll.active = true;
  try {
    const response = await fetch("/api/state", { signal: AbortSignal.timeout(5000) });
    if (!response.ok) throw new Error("state");
    state = await response.json(); render();
    $("connection").hidden = true;
    reloadIfUpdated(state.version, !document.activeElement?.matches("input, select") && !document.querySelector("[data-armed]"));
  }
  catch { $("connection").hidden = false; }
  finally { poll.active = false; }
  if (pin && Date.now() - (poll.healthAt || 0) > 10000) {
    poll.healthAt = Date.now(); loadHealth();
  }
  if ($("songCare").open) loadCare();
}

async function loadHealth() {
  try {
    const r = await fetch("/api/admin/health", { headers: { "X-Pin": pin }, signal: AbortSignal.timeout(5000) });
    if (r.status === 403) return lockUp();
    if (!r.ok) throw new Error("health");
    const h = await r.json();
    $("networkStatus").textContent = `${h.connection.internet ? t().online : t().localOnly}. ${h.connection.lan_url}`;
    $("diskStatus").textContent = h.storage.blocked ? t().storageFull : `${h.storage.library_gb} GB / ${h.storage.free_gb} GB free`;
    $("workerStatus").textContent = !h.worker.available ? t().workerUnavailable : h.worker.job.wish
      ? t().makingNow(h.worker.job.wish, t().stages[h.worker.job.stage] || h.worker.job.stage, h.worker.job.pct || 0) : t().idleMaker;
    if (h.worker.last_error) $("workerStatus").textContent += ` · ${h.worker.last_error}`;
    $("backupStatus").textContent = h.backup.error ? `${t().backupProblem}: ${h.backup.error}` : h.backup.last_success
      ? `${t().backupOk}: ${new Intl.DateTimeFormat(lang, { dateStyle: "short", timeStyle: "short" }).format(new Date(h.backup.last_success * 1000))}` : t().noBackup;
  } catch { $("connection").hidden = false; }
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
let skipId = null, restartId = null;
$("skip").onclick = () => {
  if (!$("skip").dataset.armed) skipId = state.now_playing && state.now_playing.id;
  confirmTap($("skip"), t().skipSure, () => admin("skip", { id: skipId }));
};
$("restart").onclick = () => {
  if (!$("restart").dataset.armed) restartId = state.now_playing && state.now_playing.id;
  confirmTap($("restart"), t().restartSure, () => admin("restart", { id: restartId }));
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
$("tonightLook").onchange = e => admin("tonight", { look: e.target.value }).catch(code => code !== "pin" && toast(t().bad_setting));
$("everywhere").onchange = e => saveSetting("theme", e.target.checked ? "venue" : "auto");
$("addNight").onclick = () => saveNights([...state.nights, { date: today(), look: "halloween", yearly: true }]);
const failed = code => code !== "pin" && toast(t()[code] || t().bad_setting);
$("logoFile").onchange = e => {
  const f = e.target.files[0];
  e.target.value = "";  // picking the same file again must still count
  if (f && f.size > 1e6) return toast(t().logoTooBig);
  if (f) admin(`logo?look=${encodeURIComponent($("logoLook").value)}`, f).catch(failed);
};
$("earlier").onclick = () => admin("nudge", { delta: 0.1 });
$("later").onclick = () => admin("nudge", { delta: -0.1 });
$("syncTest").onclick = () => admin("synctest", { on: !state.synctest });
$("eventToggle").onclick = () => admin("event", { action: state.event?.open === false ? "open" : "close" });
$("newEvent").onclick = () => confirmTap($("newEvent"), t().newEventSure, async () => {
  await admin("event", { action: "start" }); $("newEvent").textContent = t().newEvent;
});
document.querySelectorAll(".lang button").forEach(b => b.onclick = () => { lang = b.dataset.lang; local("lang", lang); applyLang(); });

applyLang();
if (pin) unlock();
setInterval(() => { if (pin) poll(); }, 2000);
