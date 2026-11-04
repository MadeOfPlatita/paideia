(async () => {
  const rgb = (value) => (value.match(/\d+(?:\.\d+)?/g) || []).slice(0, 3).map(Number);
  const bg = rgb(getComputedStyle(document.body).backgroundColor);
  const text = rgb(getComputedStyle(document.body).color);
  const pass = bg.length === 3 && text.length === 3 && Math.max(...bg) < 45 && Math.min(...text) > 200;
  return { ok: pass, background: bg, text, title: document.title };
})()
