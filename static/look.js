// The venue's look on every page: looks.css holds the palettes; this picks one, applies the staff's accent, icon and
// logo, and remembers them so the next visit starts in the venue's look instead of flashing the default first.
// On a special night (look.night) that night's look shows instead, in its own colours: the pub's accent would clash.
function applyVenueLook(look) {
  if (!look) return;
  const root = document.documentElement, night = look.night !== look.look && look.night;
  root.dataset.look = night || look.look;
  root.toggleAttribute("data-logo", !!look.logo);  // looks.css shows img.logo only then
  document.querySelectorAll("img.logo").forEach(img => { if (look.logo && img.getAttribute("src") !== look.logo) img.src = look.logo; });
  if (look.accent && !night) {
    const [r, g, b] = [1, 3, 5].map(i => parseInt(look.accent.slice(i, i + 2), 16) / 255)
      .map(c => c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
    root.style.setProperty("--accent", look.accent);  // and text on it that stays readable, whatever the colour
    root.style.setProperty("--on-accent", 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.18 ? "#111111" : "#FFFFFF");
  } else {
    root.style.removeProperty("--accent");
    root.style.removeProperty("--on-accent");
  }
  let icon = document.querySelector("link[rel=icon]");
  if (!icon) { icon = document.createElement("link"); icon.rel = "icon"; document.head.append(icon); }
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">${look.icon}</text></svg>`;
  icon.href = `data:image/svg+xml,${encodeURIComponent(svg)}`;
  const theme = document.querySelector("meta[name=theme-color]");
  if (theme) theme.content = getComputedStyle(root).getPropertyValue("--bg").trim();
  try { localStorage.setItem("look", JSON.stringify(look)); } catch (e) {}
}
try { applyVenueLook(JSON.parse(localStorage.getItem("look"))); } catch (e) {}

// The TV scenes (themes.js) that go with each look, when staff want tonight's theme everywhere: the TV shows another
// one for each song; phones and the staff page keep the first.
const LOOK_THEMES = {
  stage: ["ballad", "rock", "cover"], pub: ["celtic", "knot", "hills", "harp"], neon: ["neon80s", "disco"],
  daylight: ["pop", "cover"], halloween: ["halloween", "graveyard", "webs", "cauldron"],
};

// Tonight's theme in a strip (guests' phones, the staff page): the TV's own backdrop, gentler and without the music.
// p5 and the backdrops load the first time a strip is shown, so pages without one stay light. No look: no strip.
let themesLoaded = null;
const banners = new Map();
const loadScript = src => new Promise((ok, fail) => document.head.append(Object.assign(document.createElement("script"), { src, onload: ok, onerror: fail })));
function themeBanner(el, look) {
  const name = LOOK_THEMES[look]?.[0] || "";
  if ((el.dataset.theme || "") === name) return;
  el.dataset.theme = name;
  banners.get(el)?.stop();
  banners.delete(el);
  el.classList.toggle("live", !!name);
  if (!name) return;
  themesLoaded ||= loadScript("/static/vendor/p5.min.js").then(() => loadScript("/static/themes.js"));
  themesLoaded.then(() => {
    if (el.dataset.theme !== name || banners.has(el)) return;  // the look changed again while loading
    const pulse = () => 0.15 + 0.25 * Math.max(0, Math.sin(performance.now() / 500 * Math.PI)) ** 3;  // a gentle 60 bpm
    banners.set(el, THEMES[name].start(el, { beat: pulse, palette: ["rgb(31,107,74)", "rgb(201,160,69)", "rgb(140,59,42)"], seed: "banner", banner: true }));
    if (!el.dataset.watched) {  // scrolled away: no drawing, for the phone's battery
      el.dataset.watched = "1";
      new IntersectionObserver(([e]) => banners.get(el)?.pause(!e.isIntersecting)).observe(el);
    }
  }, () => { themesLoaded = null; });
}

// Tonight's theme in words too, when staff want it everywhere: what the TV (tv…), the table cards (cards), the guests'
// phones and the staff page say in a look's own voice. A word a voice leaves out keeps the page's usual one.
const VOICES = {
  halloween: {
    en: { tvScan: "Scan if you dare", tvNextUp: "Next to be haunted", tvBar: "Next to haunt", tvCall: "Rise up and grab the mic!",
          tvFree: "The stage lies empty… Scan the code and raise a song from the dead!", tvApplause: "A ghoulish round of applause for",
          cards: "Sing tonight… if you dare!", title: "Karaoke crypt keepers",
          tagline: "Pick a song… if you dare. We'll summon you.", next: "You're next… the stage awaits!",
          onNow: "It's your turn! Grab the mic before it grabs you.", stageFree: "The stage lies empty… Who dares to go first?",
          nameTitle: "Your name, for the summoning", addMine: "Summon my song", added: "Added! Watch the screen… we'll summon you.",
          wishTitle: "Can't find your song? Conjure it up", stageOn: (n, s) => ["Haunting the stage: ", n, `, with ${s}.`] },
    de: { tvScan: "Scannen, wenn du dich traust", tvNextUp: "Als Nächstes spukt", tvBar: "Als Nächstes spukt", tvCall: "Erheb dich und schnapp dir das Mikro!",
          tvFree: "Die Bühne liegt verlassen… Code scannen und einen Song zum Leben erwecken!", tvApplause: "Schaurig schönen Applaus für",
          cards: "Sing heute Abend mit… wenn du dich traust!", title: "Karaoke-Gruftwächter",
          tagline: "Such dir einen Song aus… wenn du dich traust. Wir rufen dich herbei.", next: "Du bist als Nächstes dran… die Bühne wartet!",
          onNow: "Du bist dran! Schnapp dir das Mikro, bevor es dich schnappt.", stageFree: "Die Bühne liegt verlassen… Wer traut sich zuerst?",
          nameTitle: "Dein Name für die Beschwörung", addMine: "Song heraufbeschwören", added: "Eingetragen! Behalte den Bildschirm im Blick… wir rufen dich herbei.",
          wishTitle: "Song nicht gefunden? Beschwör ihn herauf", stageOn: (n, s) => ["Auf der Bühne spukt: ", n, ` mit ${s}.`] },
  },
  pub: {
    en: { tvScan: "Scan to sing. Sláinte!", tvNextUp: "Next round", tvBar: "Next round", tvCall: "Up you get, the mic is yours!",
          tvFree: "The stage is free. Scan the code and give us a song!", tvApplause: "Sláinte! A big hand for",
          cards: "Give us a song tonight! Sláinte!", title: "Behind the bar",
          tagline: "Pick a song, we'll call you up. Sláinte!", next: "You're up next, get ready!",
          stageFree: "The stage is free. Who'll give us the first song?", addMine: "Put my song on",
          added: "On the list! Watch the screen for your name.", stageOn: (n, s) => ["On stage: ", n, `, giving us ${s}.`] },
    de: { tvScan: "Scannen & singen. Sláinte!", tvNextUp: "Nächste Runde", tvBar: "Nächste Runde", tvCall: "Auf geht's, das Mikro gehört dir!",
          tvFree: "Die Bühne ist frei. Code scannen und uns was vorsingen!", tvApplause: "Sláinte! Applaus für",
          cards: "Sing uns heute Abend was vor! Sláinte!", title: "Hinter der Theke",
          tagline: "Such dir einen Song aus, wir rufen dich auf. Sláinte!", next: "Du bist als Nächstes dran, mach dich bereit!",
          stageFree: "Die Bühne ist frei. Wer singt uns das erste Lied?", addMine: "Meinen Song eintragen",
          added: "Steht auf der Liste! Achte auf deinen Namen am Bildschirm.", stageOn: (n, s) => ["Auf der Bühne: ", n, ` mit ${s}.`] },
  },
};
let voice = null;  // tonight's: VOICES[look], or null for the usual words
function useVoice(state) {
  voice = state?.display?.theme === "venue" ? VOICES[state.look.night || state.look.look] || null : null;
}
// A page's words (T[lang]) with tonight's voice laid over them.
const voicedWords = new Map();
function voiced(words, lang) {
  const own = voice?.[lang];
  if (!own) return words;
  if (!voicedWords.has(own)) voicedWords.set(own, { ...words, ...own });
  return voicedWords.get(own);
}
// The TV and the table cards say both languages: [data-say] elements get English and German in tonight's voice,
// on two lines (data-join="br") or with " / " between, else their usual words.
function speak() {
  document.querySelectorAll("[data-say]").forEach(n => {
    n.dataset.usual ??= n.innerHTML;
    const en = voice?.en[n.dataset.say], de = voice?.de[n.dataset.say];
    if (!en || !de) {
      if (n.innerHTML !== n.dataset.usual) n.innerHTML = n.dataset.usual;  // the page's own markup
      return;
    }
    const br = n.dataset.join === "br";
    if (n.textContent !== (br ? en + de : `${en} / ${de}`)) n.replaceChildren(...(br ? [en, document.createElement("br"), de] : [`${en} / ${de}`]));
  });
}

// After an update, open pages load the new version by themselves, but only when that interrupts nobody (safe).
let pageVersion = null;
function reloadIfUpdated(version, safe) {
  if (pageVersion === null) pageVersion = version;
  else if (version !== pageVersion && safe) location.reload();
}
