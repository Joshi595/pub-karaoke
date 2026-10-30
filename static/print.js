document.getElementById("printBtn").onclick = () => print();
const qr = (el, text) => { const q = qrcode(0, "M"); q.addData(text); q.make(); el.innerHTML = q.createSvgTag({ cellSize: 1, margin: 2, scalable: true }); };
const esc = s => s.replace(/([\\;,:"])/g, "\\$1");
fetch("/api/state").then(r => r.json()).then(s => {
  applyVenueLook(s.look);
  document.querySelectorAll(".pub").forEach(n => n.textContent = s.pub_name);
  document.title = `${s.pub_name}: printables`;
  qr(document.getElementById("joinQr"), s.join_url);
  document.getElementById("joinCap").textContent = s.join_url.replace(/^https?:\/\//, "").replace(/\/$/, "");
  if (s.wifi.name) {
    qr(document.getElementById("wifiQr"), `WIFI:T:WPA;S:${esc(s.wifi.name)};P:${esc(s.wifi.password)};;`);
    document.getElementById("wifiCap").textContent = s.wifi.password ? `${s.wifi.name} / ${s.wifi.password}` : s.wifi.name;
  } else document.getElementById("wifiFig").hidden = true;
  const admin = s.join_url.replace(/\/?$/, "/admin").replace(/^https?:\/\//, "");
  document.getElementById("adminUrl").textContent = admin;
  document.getElementById("adminUrlDe").textContent = admin;
  document.getElementById("ruleLimit").textContent = `Up to ${s.songs_per_singer} songs waiting per person. / Bis zu ${s.songs_per_singer} Songs pro Person in der Warteschlange.`;
  document.getElementById("ruleReady").textContent = `When your name is on the TV, you have ${s.upnext_seconds} seconds to get to the mic. / Wenn dein Name erscheint, hast du ${s.upnext_seconds} Sekunden bis zum Mikro.`;
  const card = document.getElementById("card");
  for (let i = 0; i < 3; i++) { const copy = card.cloneNode(true); copy.removeAttribute("id"); copy.querySelectorAll("[id]").forEach(n => n.removeAttribute("id")); card.parentNode.append(copy); }
});
