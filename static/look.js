// The venue's look on every page: looks.css holds the palettes; this picks one, applies the staff's accent and icon,
// and remembers them so the next visit starts in the venue's look instead of flashing the default first.
function applyVenueLook(look) {
  if (!look) return;
  const root = document.documentElement;
  root.dataset.look = look.look;
  if (look.accent) {
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
