// Two panels of the job detail for the talent:
//  1. "How this job fits you": 8 numbers of the formulas on a radar chart, with a table (unchanged).
//  2. "Your path to this job" (R10, decision D7): a radar with two layers ("You have" and "Job requires") over the skill groups,
//     a list of what fits and a list of the gaps to close, each with what you have, what the job needs and the months.
//     The 12-month line chart is gone.
// This is for the talent only. The API never sends it to an employer. It is a guide, not a score on the person.
import { esc, iconHtml as icon } from "../core/dom.js";
import { radarHtml, radarTableHtml } from "./radar.js";

const has = (v) => v != null && v !== "" && Number.isFinite(Number(v));
const num = (v) => (has(v) ? String(Math.round(Number(v) * 10) / 10) : "—");
const list = (v) => (Array.isArray(v) ? v : []);
const cap = (t) => { const s = String(t ?? "").trim(); return s ? s[0].toUpperCase() + s.slice(1) : s; };

const monthsText = (m) => (Number(m) < 1 ? "less than 1 month" : `about ${Math.round(Number(m) * 10) / 10} ${Number(m) <= 1.05 ? "month" : "months"}`);

// ---------- "How this job fits you" ----------
// The formula behind each axis, in plain words
const FORMULA = { F1: "Formula 1: your occupation and skills against the job", F2: "Formula 2: how severe the gaps are", F5: "Formula 5: the feed score of the job" };

// "How this job fits you": the 8 numbers of Formulas 1, 2 and 5 on a radar chart, and the same numbers in a table
function fitHtml(b) {
  if (!b.axes || b.axes.length < 3) return "";
  const data = { axes: b.axes, series: [{ name: "This job", values: b.axes.map((a) => a.value) }] };
  return `
    <section class="panel fit" aria-labelledby="fitTitle">
      <div class="panel-head"><div>
        <h2 id="fitTitle">How this job fits you</h2>
        <p class="muted">Eight numbers from 0 to 100. A higher number is a better fit. Jinder does not add them up into one verdict.</p>
      </div>${b.score != null ? `<span class="chip chip-blue" title="Your skill match mixed with the feed score of Formula 5">Fit score ${Number(b.score).toFixed(1)}</span>` : ""}</div>
      <div class="fit-grid">
        ${radarHtml(data)}
        <div>${radarTableHtml(data, { note: (a) => a.formula })}
          <ul class="hint fit-formulas">${[...new Set(b.axes.map((a) => a.formula))].map((f) => `<li>${esc(f)}: ${esc((FORMULA[f] || "").split(": ")[1] || "")}</li>`).join("")}</ul>
        </div>
      </div>
    </section>`;
}

// ---------- "Your path to this job" ----------
// The status of one axis: an icon and a word, so that colour is not the only signal
const STATUS = {
  fit: { text: "Fit", icon: "check", cls: "path-status-fit" },
  above: { text: "Above", icon: "star", cls: "path-status-above" },
  gap: { text: "Gap", icon: "alert", cls: "path-status-gap" },
};
// The kind of a gap, in plain words
const GAP_KIND = {
  missing: { text: "Missing", chip: "chip-rose" },
  below_level: { text: "Below level", chip: "chip-yellow" },
  experience: { text: "Experience", chip: "chip-blue" },
  level: { text: "Level", chip: "chip-blue" },
  certification: { text: "Certification", chip: "chip-pink" },
};
const FIT_KIND = { skill: "Skill", experience: "Experience", level: "Level", certification: "Certification", award: "Award" };

const kindText = (map, k) => map[k]?.text || map[k] || cap(String(k || "").replace(/_/g, " "));

// "You: Advanced · Needs: Proficient"
function haveNeedHtml(have, need) {
  const parts = [];
  if (has(have) || (typeof have === "string" && have)) parts.push(`You: ${esc(cap(have))}`);
  if (has(need) || (typeof need === "string" && need)) parts.push(`Needs: ${esc(cap(need))}`);
  return parts.length ? `<p class="path-detail">${parts.join(" · ")}</p>` : "";
}

function fitItemHtml(f) {
  const kind = String(f?.kind || "skill");
  return `<li class="path-item path-fit" data-kind="${esc(kind)}">
    <span class="path-icon" aria-hidden="true">${icon("check")}</span>
    <div class="path-body">
      <p class="path-title"><strong>${esc(f?.label)}</strong>${kind !== "skill" ? `<span class="chip chip-neutral path-kind">${esc(kindText(FIT_KIND, kind))}</span>` : ""}</p>
      ${haveNeedHtml(f?.have, f?.need)}
      ${f?.note ? `<p class="hint path-note">${esc(f.note)}</p>` : ""}
    </div></li>`;
}

function gapItemHtml(g) {
  const kind = String(g?.kind || "missing");
  const info = GAP_KIND[kind] || { text: kindText(GAP_KIND, kind), chip: "chip-neutral" };
  return `<li class="path-item path-gap" data-kind="${esc(kind)}">
    <span class="path-icon" aria-hidden="true">${icon("alert")}</span>
    <div class="path-body">
      <p class="path-title"><span class="chip ${info.chip} path-kind">${esc(info.text)}</span><strong>${esc(g?.label)}</strong>${g?.must ? `<span class="chip path-required">Required</span>` : ""}</p>
      ${haveNeedHtml(g?.have, g?.need)}
      ${has(g?.months) ? `<p class="path-months">${icon("clock")}${esc(monthsText(g.months))}</p>` : ""}
      ${g?.note ? `<p class="hint path-note">${esc(g.note)}</p>` : ""}
    </div></li>`;
}

function summaryHtml(path, fit, gaps) {
  const s = path.summary || {};
  const fitN = has(s.fitCount) ? Number(s.fitCount) : fit.length;
  const gapN = has(s.gapCount) ? Number(s.gapCount) : gaps.length;
  const chips = [
    `<li><span class="chip chip-green">${icon("check")}${fitN} fit</span></li>`,
    `<li><span class="chip chip-yellow">${icon("alert")}${gapN} ${gapN === 1 ? "gap" : "gaps"}</span></li>`,
  ];
  if (gapN > 0 && has(s.monthsToClose)) chips.push(`<li><span class="chip chip-neutral">${icon("clock")}${esc(monthsText(s.monthsToClose))} to close the gaps</span></li>`);
  if (s.readinessTier) chips.push(`<li><span class="chip chip-blue"><span class="sr-only">Readiness: </span>${esc(s.readinessTier)}</span></li>`);
  return `<ul class="path-summary" aria-label="Summary of your path">${chips.join("")}</ul>`;
}

function axesBlockHtml(axes) {
  if (!axes.length) return "";
  const data = {
    axes: axes.map((a) => ({ label: String(a?.label ?? a?.key ?? "") })),
    series: [{ name: "You have", values: axes.map((a) => a?.have) }, { name: "Job requires", values: axes.map((a) => a?.required) }],
  };
  const chart = axes.length >= 3 ? radarHtml(data, { layers: true }) : `<p class="muted">There are too few numbers for a chart. The table has them.</p>`;
  const rows = axes.map((a) => {
    const st = STATUS[a?.status];
    return `<tr><th scope="row">${esc(a?.label ?? a?.key ?? "")}</th><td>${num(a?.required)}</td><td>${num(a?.have)}</td>
      <td>${st ? `<span class="path-status ${st.cls}">${icon(st.icon)}${st.text}</span>` : "—"}</td></tr>`;
  }).join("");
  return `
    <div class="path-chart">
      ${chart}
      <div class="table-wrap"><table class="data-table path-table">
        <caption class="sr-only">Skill groups: what the job requires and what you have, each from 0 to 100</caption>
        <thead><tr><th scope="col">Skill group (0 to 100)</th><th scope="col">Job requires</th><th scope="col">You have</th><th scope="col">Status</th></tr></thead>
        <tbody>${rows}</tbody></table></div>
    </div>`;
}

/**
 * "Your path to this job". @param {object} path  `bridge.path` of the API (plan section 5.3). A missing or empty path gives a short note.
 * Axes: [{ key, label, group, required, have, status: "gap"|"fit"|"above" }]. Lists: fit [{ kind, label, have, need, note }],
 * gaps [{ kind, label, have, need, months, must, note }]. Summary: { fitCount, gapCount, monthsToClose, readinessTier }.
 */
export function pathHtml(path) {
  const head = `
      <div class="panel-head"><div>
        <h2 id="pathTitle">Your path to this job</h2>
        <p class="muted">What you already have for this job, and what is still missing. This is a guide for you. Employers never see it.</p>
      </div></div>`;
  const axes = list(path?.axes), fit = list(path?.fit), gaps = list(path?.gaps);
  if (!path || typeof path !== "object" || !(axes.length || fit.length || gaps.length || path.summary)) {
    return `<section class="panel bridge path" aria-labelledby="pathTitle">${head}<p class="muted path-empty-note">A detailed path is not available for this job.</p></section>`;
  }
  return `
    <section class="panel bridge path" aria-labelledby="pathTitle">
      ${head}
      ${summaryHtml(path, fit, gaps)}
      <div class="path-grid">
        ${axesBlockHtml(axes) || `<div class="path-chart"><p class="muted">There are no numbers by skill group for this job.</p></div>`}
        <div class="path-lists">
          <section class="path-col" aria-labelledby="pathFitTitle">
            <h3 class="jd-sub" id="pathFitTitle">Where you fit</h3>
            ${fit.length ? `<ul class="path-list">${fit.map(fitItemHtml).join("")}</ul>` : `<p class="muted path-empty">Nothing in your profile meets a requirement of this job yet.</p>`}
          </section>
          <section class="path-col" aria-labelledby="pathGapTitle">
            <h3 class="jd-sub" id="pathGapTitle">Gaps to close</h3>
            ${gaps.length ? `<ul class="path-list">${gaps.map(gapItemHtml).join("")}</ul>` : `<p class="muted path-empty">No gaps: you meet every requirement.</p>`}
          </section>
        </div>
      </div>
      <p class="hint bridge-note">These are estimates from the type of each gap. They are not a promise and not a decision about you.</p>
    </section>`;
}

/** @param {object} b  JobDetail.bridge from the API. The "How this job fits you" panel (if it has axes) and "Your path to this job". */
export function bridgeHtml(b) {
  return `${b ? fitHtml(b) : ""}${pathHtml(b?.path)}`;
}
