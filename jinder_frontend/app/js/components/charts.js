// Simple bar charts with HTML and CSS (Feature 7). Each bar shows its number as text, so colour is not the only signal.
// Widths are set with paintMeters() (data-w), because the CSP blocks inline style attributes.
import { esc, iconHtml } from "../core/dom.js";

/**
 * @param {Array<{label: string, value: number}>} rows
 * @param {object} o { title, empty, unit }
 */
export function barChartHtml(rows, { title = "", empty = "No data yet.", unit = "" } = {}) {
  const max = Math.max(1, ...rows.map((r) => r.value));
  const body = rows.length
    ? `<ul class="bar-chart">${rows.map((r) => `
        <li><span class="bar-label">${esc(r.label)}</span>
          <span class="bar-track" aria-hidden="true"><span class="bar-fill" data-w="${Math.round((r.value / max) * 100)}"></span></span>
          <span class="bar-value">${esc(r.value)}${unit ? ` ${esc(unit)}` : ""}</span></li>`).join("")}</ul>`
    : `<p class="muted">${esc(empty)}</p>`;
  return `<figure class="chart">${title ? `<figcaption>${esc(title)}</figcaption>` : ""}${body}</figure>`;
}

// Upgrade prompt for Premium-only charts and features (a Basic user sees the gold "Premium" chip with a lock)
export const upgradeHtml = (text) => `
  <div class="upgrade">
    <span class="chip chip-gold locked-badge">${iconHtml("i-lock")}Premium</span>
    <p>${esc(text)}</p>
    <a class="btn btn-secondary" href="#/settings?section=plan">See plans</a>
  </div>`;
