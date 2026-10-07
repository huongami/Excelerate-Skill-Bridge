// Radar (spider) chart in SVG, with a table of the same numbers. It compares 1 to 5 things on 3 to 10 axes, each from 0 to 100.
// Colours and line styles come from CSS classes series-1 … series-5 (styles-core.css, design tokens). The 5 series differ in
// colour, line style (solid, dashed, dotted, dash-dot, long-dash) and marker shape, so colour is not the only signal.
// Every number is in the table (radarTableHtml). The chart never adds the axes up: there is no total.
//
// Old call, still works:   radarHtml({ axes: [{label}], series: [{name, values}] }, { caption })
// Two-layer mode:          radarHtml({ axes, series, layers: true })  or  radarHtml(data, { layers: true })
//   series 1 = "You have": a filled shape. series 2 = "Job requires": an outline only, thicker. The legend names are the series names.
import { esc } from "../core/dom.js";

export const MAX_SERIES = 5;

const num = (v) => Math.max(0, Math.min(100, Number(v) || 0));
const has = (v) => v != null && v !== "" && Number.isFinite(Number(v));
const fmt = (v) => (has(v) ? Number(v).toFixed(1) : "—");
const nameOf = (s, k) => String(s?.name ?? s?.label ?? s?.alias ?? `Series ${k + 1}`);

const W = 560, H = 470, CX = W / 2, CY = 235, R = 140;
const LINE_H = 14;       // line height of an axis label, in SVG units
const LABEL_CHARS = 14;  // characters in one line of an axis label
const LABEL_LINES = 3;   // lines in one axis label

/**
 * Split an axis label into at most 3 short lines, so labels do not run into each other.
 * Words stay whole. A word that is too long, and text that does not fit in 3 lines, end with "…".
 */
export function wrapLabel(text, maxChars = LABEL_CHARS, maxLines = LABEL_LINES) {
  const words = String(text ?? "").trim().split(/\s+/).filter(Boolean);
  if (!words.length) return [""];
  const cut = (w) => (w.length > maxChars + 3 ? `${w.slice(0, maxChars + 1)}…` : w);
  const lines = [];
  let cur = "";
  for (const raw of words) {
    const w = cut(raw);
    if (!cur) cur = w;
    else if ((cur + " " + w).length <= maxChars) cur += " " + w;
    else { lines.push(cur); cur = w; }
  }
  lines.push(cur);
  if (lines.length > maxLines) {
    const kept = lines.slice(0, maxLines);
    kept[maxLines - 1] = `${kept[maxLines - 1].replace(/…$/, "")}…`;
    return kept;
  }
  return lines;
}

// Marker shapes, one for each series: circle, square, diamond, triangle, cross
function marker(k, x, y, cls) {
  const f = (v) => v.toFixed(1);
  switch (k % MAX_SERIES) {
    case 1: return `<rect class="${cls}" x="${f(x - 3.5)}" y="${f(y - 3.5)}" width="7" height="7"/>`;
    case 2: return `<polygon class="${cls}" points="${f(x)},${f(y - 5)} ${f(x + 5)},${f(y)} ${f(x)},${f(y + 5)} ${f(x - 5)},${f(y)}"/>`;
    case 3: return `<polygon class="${cls}" points="${f(x)},${f(y - 5)} ${f(x + 4.6)},${f(y + 3.5)} ${f(x - 4.6)},${f(y + 3.5)}"/>`;
    case 4: return `<path class="${cls} rd-dot-cross" d="M${f(x - 4)} ${f(y - 4)}L${f(x + 4)} ${f(y + 4)}M${f(x + 4)} ${f(y - 4)}L${f(x - 4)} ${f(y + 4)}"/>`;
    default: return `<circle class="${cls}" cx="${f(x)}" cy="${f(y)}" r="3.6"/>`;
  }
}

/**
 * @param {{ axes: {label: string}[], series: {name: string, values: number[]}[], layers?: boolean }} data
 * @param {{ caption?: string, layers?: boolean }} o
 */
export function radarHtml({ axes, series, layers: dataLayers }, { caption = "", layers: optLayers } = {}) {
  axes = Array.isArray(axes) ? axes : [];
  series = (Array.isArray(series) ? series : []).slice(0, MAX_SERIES);
  const n = axes.length;
  if (n < 3 || !series.length) return "";
  const layers = !!(dataLayers || optLayers);

  const angle = (i) => -Math.PI / 2 + (2 * Math.PI * i) / n;
  const pt = (i, v, r = R) => [CX + Math.cos(angle(i)) * r * (v / 100), CY + Math.sin(angle(i)) * r * (v / 100)];
  const pts = (arr) => arr.map((p) => p.map((c) => c.toFixed(1)).join(",")).join(" ");
  const poly = (values) => pts(axes.map((_, i) => pt(i, num(values?.[i]))));

  const rings = [25, 50, 75, 100].map((r) => `<polygon class="rd-ring" points="${pts(axes.map((_, i) => pt(i, r)))}"/>`).join("");
  const ringNums = [25, 50, 75, 100].map((r) => `<text class="rd-num" x="${CX + 4}" y="${(CY - (R * r) / 100 + 3).toFixed(1)}">${r}</text>`).join("");
  const spokes = axes.map((_, i) => { const [x, y] = pt(i, 100); return `<line class="rd-spoke" x1="${CX}" y1="${CY}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}"/>`; }).join("");

  const labels = axes.map((a, i) => {
    const text = String(a?.label ?? a?.name ?? "");
    const lines = wrapLabel(text);
    const c = Math.cos(angle(i)), s = Math.sin(angle(i));
    const [px, py] = pt(i, 100, R + 12);
    const anchor = c > 0.25 ? "start" : c < -0.25 ? "end" : "middle";
    // Where the first line sits: the block of lines grows up at the top, down at the bottom, and both ways at the sides
    const y0 = s < -0.5 ? py - (lines.length - 1) * LINE_H - 4 : s > 0.5 ? py + 12 : py + 4 - ((lines.length - 1) * LINE_H) / 2;
    const tspans = lines.map((t, j) => `<tspan x="${px.toFixed(1)}" dy="${j === 0 ? 0 : LINE_H}">${esc(t)}</tspan>`).join("");
    return `<text class="rd-label" x="${px.toFixed(1)}" y="${y0.toFixed(1)}" text-anchor="${anchor}" data-axis="${i}"><title>${esc(text)}</title>${tspans}</text>`;
  }).join("");

  const shapes = series.map((s, k) => {
    const cls = `series-${k + 1}`;
    const dots = axes.map((_, i) => (has(s.values?.[i]) ? marker(k, ...pt(i, num(s.values[i])), `rd-dot ${cls}`) : "")).join("");
    return `<g class="rd-series ${cls}" data-series="${k + 1}"><polygon class="rd-shape ${cls}" points="${poly(s.values)}"/>${dots}</g>`;
  }).join("");

  const summary = series.map((s, k) => `${nameOf(s, k)}: ${axes.map((a, i) => `${a?.label ?? a?.name ?? ""} ${fmt(s.values?.[i])}`).join(", ")}`).join(". ");

  const filled = (k) => !layers || k === 0;
  const legend = series.map((s, k) => `<li><svg class="rd-swatch" viewBox="0 0 40 12" aria-hidden="true" focusable="false">${filled(k) ? `<rect class="rd-swatch-fill series-${k + 1}" x="1" y="1" width="38" height="10" rx="2"/>` : ""}<line class="rd-swatch-line series-${k + 1}" x1="2" y1="6" x2="38" y2="6"/></svg><span>${esc(nameOf(s, k))}</span></li>`).join("");

  const cls = ["chart", "radar", layers ? "radar-layers" : "", series.length > 2 ? "radar-many" : ""].filter(Boolean).join(" ");
  return `
    <figure class="${cls}">
      ${caption ? `<figcaption>${esc(caption)}</figcaption>` : ""}
      <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(summary)}" class="rd-svg" data-axes="${n}">${rings}${spokes}${ringNums}${shapes}${labels}</svg>
      <ul class="rd-legend">${legend}</ul>
    </figure>`;
}

/** The same numbers as text: one row for each axis, one column for each series. `note(axis)` can add a small text after the axis name. */
export function radarTableHtml({ axes, series }, { note = () => "" } = {}) {
  axes = Array.isArray(axes) ? axes : [];
  series = (Array.isArray(series) ? series : []).slice(0, MAX_SERIES);
  const head = series.map((s, k) => `<th scope="col">${esc(nameOf(s, k))}</th>`).join("");
  const rows = axes.map((a, i) => {
    const extra = note(a);
    return `<tr><th scope="row">${esc(a?.label ?? a?.name ?? "")}${extra ? ` <span class="hint">${esc(extra)}</span>` : ""}</th>${series.map((s) => `<td>${fmt(s.values?.[i])}</td>`).join("")}</tr>`;
  }).join("");
  return `<div class="table-wrap"><table class="data-table radar-table"><thead><tr><th scope="col">Axis (0 to 100)</th>${head}</tr></thead><tbody>${rows}</tbody></table></div>`;
}
