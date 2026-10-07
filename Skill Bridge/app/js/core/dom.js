// DOM helpers. Use h() and textContent for user data. Use HTML strings only for static markup.

export function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === false || v == null) continue;
    if (k === "class") el.className = v;
    else if (k === "text") el.textContent = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  children.flat().forEach((c) => c != null && el.append(c));
  return el;
}

// SVG icon node from the sprite (icons.svg)
export function icon(id) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("class", "icon");
  svg.setAttribute("aria-hidden", "true");
  const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
  use.setAttribute("href", `icons.svg#${id}`);
  svg.append(use);
  return svg;
}

// SVG icon as an HTML string (for static templates)
export const iconHtml = (id) => `<svg class="icon" aria-hidden="true"><use href="icons.svg#${id}"/></svg>`;

// Escape text before it goes into an HTML string
export const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

// Some answers can be a list or (in older data) one string. Always work with a list.
export const toList = (v) => (Array.isArray(v) ? v : v ? [v] : []);

export const formatDate = (d) =>
  new Date(d).toLocaleDateString("en-AU", { day: "numeric", month: "short", year: "numeric" });

// Tell screen-reader users about a change (polite live region #announcer in index.html)
export function announce(msg) {
  const el = document.getElementById("announcer");
  if (!el) return;
  el.textContent = "";
  setTimeout(() => (el.textContent = msg), 50);
}

// Logo + wordmark (static markup)
export const logoHtml = (href = "#/", label = "Jinder home") =>
  `<a href="${href}" class="logo" aria-label="${label}"><svg class="logo-mark" aria-hidden="true"><use href="icons.svg#logo"/></svg><span class="logo-word"><span>J</span>inder</span></a>`;
