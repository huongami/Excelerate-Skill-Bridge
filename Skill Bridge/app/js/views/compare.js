// The Compare page (Jinder V2). One full page for both roles: route "#/compare", optional "?ids=a,b,c" and (employer) "&jobId=".
//   Talent (free):        compare 2 to 5 JOBS.            Data: api.jobs.compare(ids)
//   Employer (Premium):   compare 2 to 5 TALENT profiles for ONE chosen job.   Data: api.recruiter.compare(ids, jobId)
// A Basic employer sees what Compare does and a locked Premium call to action. That page makes no compare request.
// The page never shows a total score and never ranks people. Every chart has a table with the same numbers.
// The chosen items live in the compare basket (compareStore) and in the address (?ids=...). The page keeps both in step.
// The address is changed with history.replaceState, so the router does not draw the page again.
import { api } from "../api/index.js";
import { compareStore } from "../core/compare-store.js";
import { COMPARE_MAX, skillLevelLabel } from "../data/levels.js";
import { h, esc, iconHtml, announce } from "../core/dom.js";
import { radarHtml } from "../components/radar.js";
import { upgradeHtml } from "../components/charts.js";
import { lockedBadgeHtml, bindPremiumLocks } from "../components/premium.js";
import { openModal } from "../components/modal.js";
import { coverageText } from "../components/status.js";

const MIN_ITEMS = 2;
const PICK_PAGE_JOBS = 20;
const PICK_PAGE_TALENT = 50;
const LAST_JOB_KEY = (userId) => `jinder.compare.lastJob.${userId}`;

// ---------- Small helpers ----------
const parseIds = (raw) => [...new Set(String(raw || "").split(",").map((s) => s.trim()).filter(Boolean))];
const levelText = (n) => (n == null ? "—" : `${skillLevelLabel(n) || "Level"} (${n})`);
const fmt1 = (v) => (v == null || v === "" || !Number.isFinite(Number(v)) ? "—" : Number(v).toFixed(1));
const money = (n) => (Number(n) > 0 ? `$${Number(n).toLocaleString("en-AU")} a year` : "");
const ordinal = (n) => ({ 1: "1st", 2: "2nd", 3: "3rd" }[n] || `${n}th`);
const plural = (n, one, many) => (n === 1 ? one : many);
const textOf = (x) => (typeof x === "string" ? x : x?.name || "");
// An award kind can be a key such as "kaggle_medal". Show it as words.
const tidy = (s) => { const t = String(s ?? "").replace(/[_]+/g, " ").trim(); return t ? t[0].toUpperCase() + t.slice(1) : ""; };
const yearsOf = (min, max) => {
  const a = min == null ? null : Number(min), b = max == null ? null : Number(max);
  if (a != null && b != null) return a === b ? `${a} years` : `${a} to ${b} years`;
  if (a != null) return `${a}+ years`;
  if (b != null) return `Up to ${b} years`;
  return "";
};
const dash = (label = "Not listed") => `<span class="cmp-none-text" aria-hidden="true">—</span><span class="sr-only">${esc(label)}</span>`;
const listHtml = (arr, label) => (arr.length ? `<ul class="cmp-list">${arr.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : dash(label));

// One label for each item. If two items have the same title, the second part (for example the employer) tells them apart.
function uniqueLabels(rows) {
  const count = {};
  rows.forEach((r) => { count[r.title] = (count[r.title] || 0) + 1; });
  const seen = {};
  return rows.map((r) => {
    if (count[r.title] < 2) return r.title;
    seen[r.title] = (seen[r.title] || 0) + 1;
    return r.sub ? `${r.title} (${r.sub})` : `${r.title} (${seen[r.title]})`;
  });
}

// The same swatch as the radar legend, so that a card or a column head matches its line in the chart
const swatch = (k) => `<svg class="rd-swatch cmp-swatch" viewBox="0 0 40 12" aria-hidden="true" focusable="false"><rect class="rd-swatch-fill series-${k + 1}" x="1" y="1" width="38" height="10" rx="2"/><line class="rd-swatch-line series-${k + 1}" x1="2" y1="6" x2="38" y2="6"/></svg>`;

// Skill states: icon and text. Colour only helps.
const STATE = {
  meets: { icon: "check", text: "Meets" },
  below: { icon: "alert", text: "Below" },
  missing: { icon: "x", text: "Missing" },
  related: { icon: "target", text: "Related" },
};
const stateHtml = (s) => `<span class="cmp-state">${iconHtml(STATE[s].icon)}<span>${STATE[s].text}</span></span>`;

const panelHtml = (id, title, intro, body) =>
  `<section class="panel cmp-panel" id="${id}" aria-labelledby="${id}Title"><h2 id="${id}Title">${esc(title)}</h2>${intro ? `<p class="muted">${esc(intro)}</p>` : ""}${body}</section>`;

// A table inside a region that scrolls sideways on narrow screens. The first column stays in place (CSS: .cmp-table).
const tableHtml = ({ caption, label, n, extra = "", head, body, foot = "" }) =>
  `<div class="table-wrap cmp-scroll" role="region" aria-label="${esc(label)}. This table scrolls sideways on a small screen." tabindex="0">
    <table class="data-table cmp-table cmp-n${Math.min(Math.max(n, 2), COMPARE_MAX)} ${extra}"><caption class="sr-only">${esc(caption)}</caption>
      <thead>${head}</thead><tbody>${body}</tbody>${foot ? `<tfoot>${foot}</tfoot>` : ""}</table></div>`;

const colHeads = (labels, { swatches = false } = {}) =>
  labels.map((l, k) => `<th scope="col"><span class="cmp-th">${swatches ? swatch(k) : ""}<span class="cmp-th-text" title="${esc(l)}">${esc(l)}</span></span></th>`).join("");

// ---------- The talent page content: jobs ----------
const axisValue = (job, key) => {
  const v = (job.axes || []).find((a) => a.key === key)?.value;
  return v == null || !Number.isFinite(Number(v)) ? null : Number(v);
};

function jobCardHtml(job, k, label) {
  const place = job.area || job.location || "";
  const facts = [
    ["Level", job.level || ""],
    ["Experience", yearsOf(job.minYears, job.maxYears)],
    ["Work mode", job.workMode || ""],
    ["Salary (middle)", money(job.salaryMidpoint)],
  ];
  const href = `#/jobs/${encodeURIComponent(job.id)}`;
  return `<li class="cmp-card" data-id="${esc(job.id)}">
    <div class="cmp-card-head">${swatch(k)}
      <h3 class="cmp-card-title"><a class="text-link" href="${href}">${esc(job.title)}</a></h3>
      <button type="button" class="btn btn-ghost btn-icon cmp-remove" data-remove="${esc(job.id)}" aria-label="Remove ${esc(label)} from compare">${iconHtml("x")}</button></div>
    <p class="cmp-card-meta">${esc([job.company, place].filter(Boolean).join(" · "))}${job.status === "closed" ? ` <span class="chip chip-rose">Closed</span>` : ""}</p>
    <dl class="cmp-facts">${facts.map(([t, v]) => `<div><dt>${t}</dt><dd>${v ? esc(v) : dash()}</dd></div>`).join("")}</dl>
    <a class="text-link cmp-card-link" href="${href}">View job<span class="sr-only">: ${esc(label)}</span></a></li>`;
}

function fitPanel(res, jobs, labels) {
  const axes = (res.axes || []).filter((a) => jobs.every((j) => axisValue(j, a.key) != null));
  if (!axes.length) return panelHtml("cmpFit", "How each job fits you", "", `<p class="muted">There are no fit numbers for these jobs yet.</p>`);
  const series = jobs.map((j, i) => ({ name: labels[i], values: axes.map((a) => axisValue(j, a.key)) }));
  const chart = radarHtml({ axes, series });
  const rows = axes.map((a) => {
    const vals = jobs.map((j) => axisValue(j, a.key));
    const max = Math.max(...vals);
    const same = vals.every((v) => v === vals[0]);
    return `<tr><th scope="row">${esc(a.label)} <span class="hint">${esc(a.formula || "")}</span></th>${vals.map((v) => `<td>${fmt1(v)}${!same && v === max ? ` <span class="cmp-best">Highest</span>` : ""}</td>`).join("")}</tr>`;
  }).join("");
  const table = tableHtml({
    caption: "How each job fits you, axis by axis, from 0 to 100. The highest value in a row is marked Highest, unless all values are equal.",
    label: "Fit numbers for each job", n: jobs.length, extra: "radar-table",
    head: `<tr><th scope="col">Axis (0 to 100)</th>${colHeads(labels, { swatches: true })}</tr>`, body: rows,
  });
  return panelHtml("cmpFit", "How each job fits you",
    "Each axis is a number from 0 to 100. The tag after the axis name tells which formula gives it. There is no total: you decide.",
    `<div class="cmp-fit${jobs.length <= 3 ? " cmp-fit-side" : ""}">${chart || ""}<div class="cmp-fit-table">${table}</div></div>`);
}

function skillsPanelTalent(res, jobs, labels) {
  const rows = res.skillMatrix || [];
  if (!rows.length) return panelHtml("cmpSkills", "Skills side by side", "", `<p class="muted">These jobs list no skills yet.</p>`);
  const counts = jobs.map(() => ({ asked: 0, meets: 0 }));
  const body = rows.map((r) => {
    const cells = jobs.map((j, k) => {
      const c = r.byJob?.[j.id];
      if (!c) return `<td class="cmp-cell cmp-none"><span class="cmp-sub">Not asked</span></td>`;
      const state = r.yours == null ? "missing" : r.yours >= c.required ? "meets" : "below";
      counts[k].asked++;
      if (state === "meets") counts[k].meets++;
      return `<td class="cmp-cell cmp-${state}">${stateHtml(state)}<span class="cmp-sub">Needs ${esc(levelText(c.required))} · ${c.must ? "Must have" : "Nice to have"}</span></td>`;
    }).join("");
    return `<tr><th scope="row"><span class="cmp-skill">${esc(r.skill)}</span><span class="cmp-sub">You: ${esc(r.yours == null ? "—" : levelText(r.yours))}</span></th>${cells}</tr>`;
  }).join("");
  const foot = `<tr><th scope="row">Skills you meet</th>${counts.map((c) => `<td>${c.meets} of ${c.asked} ${plural(c.asked, "skill", "skills")}</td>`).join("")}</tr>`;
  const table = tableHtml({
    caption: "Skills that the jobs ask for. The first column shows your own level. Each cell shows if you meet the level that the job asks for.",
    label: "Skills side by side", n: jobs.length, extra: "cmp-skills-table",
    head: `<tr><th scope="col">Skill and your level</th>${colHeads(labels)}</tr>`, body, foot,
  });
  return panelHtml("cmpSkills", "Skills side by side",
    "One row for each skill that a job asks for. Meets: your level is the same or higher. Below: you have the skill at a lower level. Missing: you have no level for this skill yet.", table);
}

function detailsPanelTalent(jobs, labels) {
  const rowsDef = [
    ["Level", (j) => [j.level]],
    ["Specialisation", (j) => [j.specialisation]],
    ["Experience", (j) => [yearsOf(j.minYears, j.maxYears)]],
    ["Work mode", (j) => [j.workMode]],
    ["Job type", (j) => [j.type]],
    ["Salary", (j) => [j.salary]],
    ["Salary (middle)", (j) => [money(j.salaryMidpoint)]],
    ["Education", (j) => [j.educationMin]],
    ["Certifications required", (j) => (j.certifications?.required || []).map(textOf), true],
    ["Certifications preferred", (j) => (j.certifications?.preferred || []).map(textOf), true],
    ["Preferred awards", (j) => (j.awards?.preferred || []).map((a) => tidy(textOf(a))), true],
  ];
  const rows = rowsDef.map(([label, get, asList]) => {
    const vals = jobs.map((j) => get(j).filter(Boolean));
    if (vals.every((v) => !v.length)) return "";   // no job has this row: hide it
    return `<tr><th scope="row">${esc(label)}</th>${vals.map((v) => `<td>${v.length ? (asList ? listHtml(v) : esc(v[0])) : dash()}</td>`).join("")}</tr>`;
  }).join("");
  if (!rows) return "";
  const table = tableHtml({
    caption: "Facts from each job: level, experience, work mode, salary, certifications and awards.",
    label: "Details of each job", n: jobs.length,
    head: `<tr><th scope="col">Detail</th>${colHeads(labels)}</tr>`, body: rows,
  });
  return panelHtml("cmpDetails", "Details", "A row is hidden when no job has a value for it.", table);
}

function pairsPanel(res, jobs, labels) {
  const pairs = res.pairs || [];
  if (!pairs.length) return "";
  const label = Object.fromEntries(jobs.map((j, i) => [j.id, labels[i]]));
  const find = (a, b) => pairs.find((p) => (p.a === a && p.b === b) || (p.a === b && p.b === a));
  const body = jobs.map((ja) => `<tr><th scope="row">${esc(label[ja.id])}</th>${jobs.map((jb) => {
    if (ja.id === jb.id) return `<td class="cmp-cell cmp-self"><span aria-hidden="true">—</span><span class="sr-only">Same job</span></td>`;
    const p = find(ja.id, jb.id);
    return p ? `<td class="cmp-cell"><strong class="cmp-index">${fmt1(p.index)}</strong><span class="cmp-sub">${esc(p.tier || "")}</span></td>` : `<td class="cmp-cell cmp-none"><span class="cmp-sub">No result</span></td>`;
  }).join("")}</tr>`).join("");
  const matrix = tableHtml({
    caption: "How close each pair of jobs is. The number is the overall result of Formula 3, from 0 to 100. A tier word follows it.",
    label: "How close the jobs are to each other", n: jobs.length, extra: "cmp-pairs-table",
    head: `<tr><th scope="col"><span class="sr-only">Job</span></th>${colHeads(jobs.map((j) => label[j.id]))}</tr>`, body,
  });
  const details = pairs.map((p) => `<details class="cmp-pair">
      <summary><span class="cmp-pair-names">${esc(label[p.a] || p.a)} and ${esc(label[p.b] || p.b)}</span><span class="chip chip-blue">${fmt1(p.index)} · ${esc(p.tier || "")}</span></summary>
      <div class="cmp-pair-body">
        <table class="data-table"><caption class="sr-only">Parts of the result for ${esc(label[p.a] || p.a)} and ${esc(label[p.b] || p.b)}</caption>
          <thead><tr><th scope="col">Part</th><th scope="col">Value (0 to 100)</th></tr></thead>
          <tbody>${(p.parts || []).map((x) => `<tr><th scope="row">${esc(x.label)}</th><td>${fmt1(x.value)}</td></tr>`).join("")}</tbody></table>
        ${p.advice ? `<p><strong>Advice:</strong> ${esc(p.advice)}</p>` : ""}
        ${p.salaryChange ? `<p><strong>Salary change, from the first job to the second:</strong> ${esc(p.salaryChange)}</p>` : ""}
      </div></details>`).join("");
  return panelHtml("cmpPairs", "How close the jobs are to each other",
    "Formula 3 compares two jobs by occupation, requirements, salary, sector and place. 100 means the same. Open a pair to see its parts.",
    `${matrix}<div class="cmp-pair-list"><h3 class="cmp-sub-title">Details for each pair</h3>${details}</div>`);
}

function talentResultsHtml(res) {
  const jobs = res.jobs || [];
  const labels = uniqueLabels(jobs.map((j) => ({ title: j.title, sub: j.company })));
  return {
    cards: jobs.map((j, k) => jobCardHtml(j, k, labels[k])).join(""),
    panels: [fitPanel(res, jobs, labels), skillsPanelTalent(res, jobs, labels), detailsPanelTalent(jobs, labels), pairsPanel(res, jobs, labels)].join(""),
    ids: jobs.map((j) => j.id),
    items: jobs.map((j) => ({ id: j.id, title: j.title, company: j.company || "" })),
  };
}

// ---------- The employer page content: talent ----------
function talentCardHtml(c, k, jobId) {
  const years = c.yearsExperience != null ? `${c.yearsExperience} years` : c.years || "";
  const roles = (c.roles || []).map((r) => textOf(r.title ? r.title : r)).filter(Boolean).slice(0, 2).join(", ");
  const skillsText = c.skills?.length ? coverageText({ skills: c.skills }) : "";
  const facts = [["Level", c.level || ""], ["Experience", years], ["Roles", roles], ["Skills for this job", skillsText]];
  const href = `#/candidates/${encodeURIComponent(c.id)}?jobId=${encodeURIComponent(jobId)}`;
  return `<li class="cmp-card" data-id="${esc(c.id)}">
    <div class="cmp-card-head">${swatch(k)}
      <h3 class="cmp-card-title"><a class="text-link" href="${href}">${esc(c.alias)}</a></h3>
      <button type="button" class="btn btn-ghost btn-icon cmp-remove" data-remove="${esc(c.id)}" aria-label="Remove ${esc(c.alias)} from compare">${iconHtml("x")}</button></div>
    <dl class="cmp-facts">${facts.map(([t, v]) => `<div><dt>${t}</dt><dd>${v ? esc(v) : dash()}</dd></div>`).join("")}</dl>
    <a class="text-link cmp-card-link" href="${href}">View profile for this job<span class="sr-only">: ${esc(c.alias)}</span></a></li>`;
}

const RADAR_NOTE = { F4: "merit model", F6: "fit to the job", skills: "from the skills table" };

function radarPanelEmployer(res, cands, jobTitle) {
  const radar = res.radar || {};
  const axes = radar.axes || [];
  const series = (radar.series || []).map((s) => ({ name: s.alias || s.id, values: s.values || [] }));
  if (!axes.length || !series.length) return panelHtml("cmpRadar", "Profiles on the same axes", "", `<p class="muted">There are no shared axes for these profiles yet.</p>`);
  const chart = radarHtml({ axes, series });
  const rows = axes.map((a, i) => `<tr><th scope="row">${esc(a.label)} <span class="hint">${esc(RADAR_NOTE[a.formula] || a.formula || "")}</span></th>${series.map((s) => `<td>${fmt1(s.values[i])}</td>`).join("")}</tr>`).join("");
  const table = tableHtml({
    caption: "The profiles on the same axes, from 0 to 100. The note after the axis name tells where the number comes from.",
    label: "Numbers for each profile", n: series.length, extra: "radar-table",
    head: `<tr><th scope="col">Axis (0 to 100)</th>${colHeads(series.map((s) => s.name), { swatches: true })}</tr>`, body: rows,
  });
  return panelHtml("cmpRadar", "Profiles on the same axes",
    `${jobTitle ? `For ${jobTitle}. ` : ""}Each axis is a number from 0 to 100, from the shared profile only. Jinder does not add the axes up and does not rank people.`,
    `<div class="cmp-fit${series.length <= 3 ? " cmp-fit-side" : ""}">${chart || `<p class="muted">The chart needs at least 3 shared axes. The table shows the numbers.</p>`}<div class="cmp-fit-table">${table}</div></div>`);
}

function skillsPanelEmployer(res, cands, jobTitle) {
  const rows = res.skillMatrix || [];
  if (!rows.length) return panelHtml("cmpSkills", "Skills side by side", "", `<p class="muted">This job lists no skills yet.</p>`);
  const meets = cands.map(() => 0);
  const body = rows.map((r) => {
    const cells = cands.map((c, k) => {
      const m = r.byCandidate?.[c.id];
      if (!m) return `<td class="cmp-cell cmp-none"><span class="cmp-sub">No result</span></td>`;
      const state = STATE[m.status] ? m.status : "missing";
      if (state === "meets") meets[k]++;
      const via = state === "related" ? c.skills?.find((s) => s.name === r.skill)?.via : "";
      const sub = m.level != null ? `Level: ${levelText(m.level)}` : state === "related" ? (via ? `Related via ${via}` : "Has a related skill") : "No level";
      return `<td class="cmp-cell cmp-${state}">${stateHtml(state)}<span class="cmp-sub">${esc(sub)}</span></td>`;
    }).join("");
    return `<tr><th scope="row"><span class="cmp-skill">${esc(r.skill)}</span><span class="cmp-sub">Job needs: ${esc(levelText(r.required))} · ${r.must ? "Must have" : "Nice to have"}</span></th>${cells}</tr>`;
  }).join("");
  const other = `<tr class="cmp-other"><th scope="row"><span class="cmp-skill">Other skills</span><span class="cmp-sub">Not asked by this job</span></th>${cands.map((c) => {
    const o = (c.otherSkills || []).map(textOf).filter(Boolean);
    const shown = o.slice(0, 8);
    return `<td>${o.length ? `${shown.map(esc).join(", ")}${o.length > shown.length ? ` <span class="cmp-sub">+${o.length - shown.length} more</span>` : ""}` : dash("None listed")}</td>`;
  }).join("")}</tr>`;
  const foot = `<tr><th scope="row">Skills that meet the job</th>${meets.map((n) => `<td>${n} of ${rows.length} ${plural(rows.length, "skill", "skills")}</td>`).join("")}</tr>`;
  const table = tableHtml({
    caption: "Skills that the job asks for. The first column shows the level that the job asks for. Each cell shows the level of one profile and the result for this skill.",
    label: "Skills side by side", n: cands.length, extra: "cmp-skills-table",
    head: `<tr><th scope="col">Skill and level that the job needs</th>${colHeads(cands.map((c) => c.alias))}</tr>`, body: body + other, foot,
  });
  return panelHtml("cmpSkills", "Skills side by side",
    `${jobTitle ? `Skills for ${jobTitle}. ` : ""}Meets: the level is the same or higher. Below: a lower level. Related: a related skill with no level of its own. Missing: no sign of the skill.`, table);
}

function qualificationsPanel(cands) {
  const dated = (x) => (x?.name ? `${x.name}${x.year ? ` (${x.year})` : ""}` : textOf(x));
  const defs = [
    ["Qualifications", (c) => (c.qualifications || []).map(textOf)],
    ["Certifications", (c) => (c.certifications || []).map(dated)],
    ["Awards", (c) => (c.awards || []).map(dated)],
  ];
  const body = defs.map(([label, get]) => `<tr><th scope="row">${esc(label)}</th>${cands.map((c) => `<td>${listHtml(get(c).filter(Boolean), "None listed")}</td>`).join("")}</tr>`).join("");
  const table = tableHtml({
    caption: "Qualifications, certifications and awards of each profile. Names and years only.",
    label: "Qualifications and recognition", n: cands.length,
    head: `<tr><th scope="col">Type</th>${colHeads(cands.map((c) => c.alias))}</tr>`, body,
  });
  return panelHtml("cmpQuals", "Qualifications and recognition", "Names and years only. A profile shows no person name.", table);
}

function areasPanel(res, cands) {
  const areas = res.areas || [];
  if (!areas.length) return "";
  const body = areas.map((a) => {
    const pos = Object.fromEntries((a.ranks || []).map((r) => [r.id, r.position]));
    const values = Object.values(pos);
    const allEqual = values.length > 0 && values.every((v) => v === values[0]);
    const cells = cands.map((c) => {
      const p = pos[c.id];
      if (p == null) return `<td>${dash("No result")}</td>`;
      if (allEqual) return `<td><span class="cmp-tie">Equal</span></td>`;
      const tied = values.filter((v) => v === p).length > 1;
      return `<td><span class="cmp-pos">${esc(ordinal(p))}</span>${tied ? ` <span class="cmp-tie">Equal</span>` : ""}</td>`;
    }).join("");
    return `<tr><th scope="row">${esc(a.area)}</th>${cells}</tr>`;
  }).join("");
  const table = tableHtml({
    caption: "Where the profiles differ. For each area, the place of each profile inside that area. Equal means the same place.",
    label: "Where the profiles differ", n: cands.length,
    head: `<tr><th scope="col">Area</th>${colHeads(cands.map((c) => c.alias))}</tr>`, body,
  });
  return panelHtml("cmpAreas", "Where the profiles differ",
    "One area at a time. 1st is the highest place in that area. Jinder does not add the areas up and does not rank people. You decide.", table);
}

function employerResultsHtml(res, jobId) {
  const cands = res.candidates || [];
  const jobTitle = res.job?.title || "";
  // The swatch of a card is the line of the same person in the chart (radar.series has its own order)
  const order = (res.radar?.series || []).map((s) => s.id);
  const lineOf = (c, k) => (order.indexOf(c.id) >= 0 ? order.indexOf(c.id) : k);
  return {
    cards: cands.map((c, k) => talentCardHtml(c, lineOf(c, k), jobId)).join(""),
    panels: [radarPanelEmployer(res, cands, jobTitle), skillsPanelEmployer(res, cands, jobTitle), qualificationsPanel(cands), areasPanel(res, cands)].join(""),
    ids: cands.map((c) => c.id),
    items: cands.map((c) => ({ id: c.id, alias: c.alias })),
  };
}

// ---------- The locked page (Basic employer) ----------
function lockedHtml() {
  const rows = [["Skill A", "meets", "meets", "below"], ["Skill B", "meets", "related", "missing"], ["Skill C", "below", "meets", "meets"]];
  return `<section class="panel cmp-locked" aria-labelledby="cmpLockedTitle">
    <div class="cmp-locked-head"><div class="icon-tile gold">${iconHtml("i-lock")}</div>
      <div><h2 id="cmpLockedTitle">Compare 2 to 5 talent profiles side by side</h2><p class="muted">This is a Premium feature.</p></div></div>
    <ul class="check-list cmp-locked-list">
      <li>${iconHtml("check")}<span>Choose one of your jobs. Compare is always for this job.</span></li>
      <li>${iconHtml("check")}<span>See all profiles in one chart, on the same axes.</span></li>
      <li>${iconHtml("check")}<span>See each skill: does the profile meet the level that the job asks for?</span></li>
      <li>${iconHtml("check")}<span>See certifications and awards next to each other.</span></li>
      <li>${iconHtml("check")}<span>See where the profiles differ, one area at a time. There is no total score and no ranking of people.</span></li>
    </ul>
    ${upgradeHtml("Compare is part of Premium. In this demo you can switch your plan in Settings.")}
    <figure class="cmp-example">
      <figcaption><span class="chip chip-neutral">Example</span> This picture is a sample. It does not show real people.</figcaption>
      <div class="cmp-example-table" aria-hidden="true">
        <div class="cmp-example-row cmp-example-head"><span></span><span>Profile A</span><span>Profile B</span><span>Profile C</span></div>
        ${rows.map(([name, ...cells]) => `<div class="cmp-example-row"><span class="cmp-skill">${name}</span>${cells.map((s) => `<span class="cmp-cell cmp-${s}">${stateHtml(s)}</span>`).join("")}</div>`).join("")}
      </div>
    </figure>
  </section>`;
}

// ---------- The page ----------
export async function compareView(root, ctx) {
  const isEmployer = ctx.user?.role === "recruiter";
  const kind = compareStore.kindForRole(isEmployer ? "recruiter" : "candidate");
  const userId = ctx.user?.id || "guest";
  const noun = isEmployer ? { many: "talent profiles", one: "talent profile" } : { many: "jobs", one: "job" };

  const st = {
    sel: [],          // the chosen items, in order: { id, title, ... } (talent items also have alias)
    jobs: [],         // employer: own jobs for the select
    jobId: "",
    data: null,       // the last good answer, drawn as { cards, panels, ids }
    loadId: 0,
    overflow: 0,      // how many ids the address had, when it had more than 5
    pickerOpen: false,
    focusAfter: null, // { index } the card to focus after a remove
  };

  // ----- the skeleton -----
  root.innerHTML = `
    <div class="dash compare-page" data-compare-page="${kind}">
      <header class="dash-head">
        <div><h1>${isEmployer ? "Compare talent" : "Compare jobs"}</h1>
          <p class="dash-sub">${isEmployer
            ? "Put 2 to 5 anonymous profiles side by side for one of your jobs, skill by skill. There is no total score and no ranking of people."
            : "Put 2 to 5 jobs side by side. See how each job fits you, skill by skill. There is no total score: you decide."}</p></div>
        <div class="panel-actions cmp-actions" data-actions hidden>
          <span class="hint cmp-count" id="cmpCount" data-count></span>
          <button type="button" class="btn btn-ghost" data-clear>Clear all</button>
          <button type="button" class="btn btn-primary" data-add aria-haspopup="dialog" aria-describedby="cmpCount">${iconHtml("plus")}Add to compare</button>
        </div>
      </header>
      <div class="cmp-toolbar" data-toolbar></div>
      <p class="cmp-note" data-note role="status" hidden></p>
      <div class="cmp-body" data-body></div>
    </div>`;
  const page = root.querySelector(".compare-page");
  const $ = (sel) => page.querySelector(sel);
  const bodyEl = $("[data-body]");
  const noteEl = $("[data-note]");
  const addBtn = $("[data-add]");
  const clearBtn = $("[data-clear]");
  const actionsEl = $("[data-actions]");
  const countEl = $("[data-count]");
  const toolbarEl = $("[data-toolbar]");
  const live = () => root.isConnected;

  // ----- the basket and the address -----
  function persist() {
    if (!live()) return;
    const have = compareStore.items(kind);
    const same = have.length === st.sel.length && have.every((x, i) => x.id === st.sel[i].id && x.title === (st.sel[i].title || st.sel[i].alias || st.sel[i].id));
    if (!same) {
      compareStore.clear(kind);
      st.sel.forEach((it) => compareStore.add(kind, it));
    }
    const params = [];
    if (st.sel.length) params.push(`ids=${st.sel.map((x) => encodeURIComponent(x.id)).join(",")}`);
    if (isEmployer && st.jobId) params.push(`jobId=${encodeURIComponent(st.jobId)}`);
    const next = `#/compare${params.length ? `?${params.join("&")}` : ""}`;
    if (location.hash.startsWith("#/compare") && location.hash !== next) history.replaceState(null, "", next);
  }

  function setNote(text) {
    noteEl.textContent = text || "";
    noteEl.hidden = !text;
  }

  function renderActions() {
    const n = st.sel.length;
    addBtn.disabled = n >= COMPARE_MAX;
    clearBtn.hidden = n === 0;
    countEl.textContent = n >= COMPARE_MAX ? `${n} of ${COMPARE_MAX} chosen. That is the most you can compare.` : `${n} of ${COMPARE_MAX} chosen`;
    actionsEl.hidden = false;
  }

  // What changed on the page: keep basket and address in step, say it, and load the new comparison
  function changed(message) {
    st.overflow = 0;
    setNote("");
    persist();
    renderActions();
    if (message) announce(message);
    load();
  }

  const labelOf = (it) => (it.title && it.title !== it.id ? it.title : it.alias || "this item");

  function removeItem(id) {
    const index = st.sel.findIndex((x) => x.id === id);
    if (index < 0) return;
    const [gone] = st.sel.splice(index, 1);
    const wasResults = bodyEl.dataset.mode === "results";
    // Draw the remaining cards at once from what we know, so that the keyboard focus does not get lost
    if (wasResults && st.sel.length) { st.focusAfter = { index }; drawCards(); }
    changed(`${labelOf(gone)} removed from compare. ${st.sel.length} ${plural(st.sel.length, noun.one, noun.many)} left.`);
    // The button that had the focus is gone: put the focus on the next useful item
    if (bodyEl.dataset.mode === "empty") bodyEl.querySelector("[data-add]")?.focus();
    else if (!wasResults) $("h1").focus({ preventScroll: true });
  }

  function clearAll() {
    if (!st.sel.length) return;
    st.sel = [];
    st.data = null;
    changed("Compare list cleared.");
    addBtn.focus();
  }

  // ----- drawing -----
  const cardMinimal = (it, k) => `<li class="cmp-card cmp-card-min" data-id="${esc(it.id)}">
      <div class="cmp-card-head">${swatch(k)}<h3 class="cmp-card-title">${esc(it.title && it.title !== it.id ? it.title : it.alias || "Loading…")}</h3>
        <button type="button" class="btn btn-ghost btn-icon cmp-remove" data-remove="${esc(it.id)}" aria-label="Remove ${esc(labelOf(it))} from compare">${iconHtml("x")}</button></div></li>`;

  function ensureShell() {
    if (bodyEl.dataset.mode === "results") return;
    bodyEl.dataset.mode = "results";
    bodyEl.innerHTML = `
      <section class="cmp-selected" aria-labelledby="cmpChosenTitle">
        <h2 id="cmpChosenTitle" class="sr-only">${isEmployer ? "Chosen profiles" : "Chosen jobs"}</h2>
        <div class="cmp-cards-wrap" role="region" aria-label="${isEmployer ? "Chosen profiles" : "Chosen jobs"}. This list scrolls sideways on a small screen." tabindex="0"><ul class="cmp-cards" data-cards></ul></div>
      </section>
      <div class="cmp-panels" data-panels></div>`;
  }

  // Draw the cards. An item that we have data for gets a full card (from the last answer). The others get a short card (title and Remove).
  // The swatch of a full card matches its line in the chart that is on the screen.
  function drawCards() {
    ensureShell();
    const cardsEl = $("[data-cards]");
    const hadFocus = document.activeElement?.closest?.("[data-remove]")?.dataset.remove || "";
    const full = new Map();
    if (st.data) {
      const tmp = document.createElement("ul");
      tmp.innerHTML = st.data.cards;
      tmp.querySelectorAll(".cmp-card").forEach((li) => full.set(li.dataset.id, li));
    }
    cardsEl.replaceChildren(...st.sel.map((it, k) => {
      const li = full.get(it.id);
      if (li) return li;
      const tmp = document.createElement("ul");
      tmp.innerHTML = cardMinimal(it, k);
      return tmp.firstElementChild;
    }));
    let target = null;
    if (st.focusAfter) {
      const buttons = cardsEl.querySelectorAll("[data-remove]");
      target = buttons[Math.min(st.focusAfter.index, buttons.length - 1)] || null;
      st.focusAfter = null;
    } else if (hadFocus) target = cardsEl.querySelector(`[data-remove="${CSS.escape(hadFocus)}"]`);
    target?.focus();
  }

  function drawResults() {
    ensureShell();
    const panelsEl = $("[data-panels]");
    panelsEl.innerHTML = st.data.panels;
    panelsEl.classList.remove("is-loading");
    panelsEl.removeAttribute("aria-busy");
    drawCards();
  }

  function showEmpty() {
    bodyEl.dataset.mode = "empty";
    const n = st.sel.length;
    bodyEl.innerHTML = `<section class="panel cmp-empty" aria-labelledby="cmpEmptyTitle"><div class="empty">
        <div class="icon-tile accent">${iconHtml("columns")}</div>
        <h2 id="cmpEmptyTitle">Choose at least ${MIN_ITEMS} ${noun.many} to compare</h2>
        <p>${isEmployer
          ? `Pick ${MIN_ITEMS} to ${COMPARE_MAX} talent profiles. You can also add them with the Compare button on the Talent page.`
          : `Pick ${MIN_ITEMS} to ${COMPARE_MAX} jobs. You can also add them with the Compare button on a job.`}${n ? ` You have chosen ${n} so far.` : ""}</p>
        ${n ? `<ul class="cmp-chip-list">${st.sel.map((it) => `<li class="chip chip-neutral compare-chip"><span>${esc(labelOf(it))}</span><button type="button" data-remove="${esc(it.id)}" aria-label="Remove ${esc(labelOf(it))} from compare">${iconHtml("x")}</button></li>`).join("")}</ul>` : ""}
        <button type="button" class="btn btn-primary" data-add aria-haspopup="dialog">${iconHtml("plus")}Choose ${noun.many}</button></div></section>`;
  }

  function showLoading() {
    bodyEl.dataset.mode = "loading";
    bodyEl.innerHTML = `<div class="empty cmp-loading" role="status"><p>${isEmployer ? "Comparing profiles…" : "Comparing jobs…"}</p></div>`;
  }

  // `missing`: the ids that the API names as the problem (404: not found. 400: above the limit). Those items get a visible mark and come first.
  function showError({ title, message, items = true, retry = true, missing = [], flag = "Not available" }) {
    bodyEl.dataset.mode = "error";
    const named = new Set((missing || []).map(String));
    const list = [...st.sel.filter((it) => named.has(String(it.id))), ...st.sel.filter((it) => !named.has(String(it.id)))];
    bodyEl.innerHTML = `<section class="panel cmp-error" role="alert" aria-labelledby="cmpErrTitle">
        <h2 id="cmpErrTitle">${esc(title)}</h2><p>${esc(message)}</p>
        ${items && st.sel.length ? `<ul class="cmp-fix-list">${list.map((it) => `<li${named.has(String(it.id)) ? ' class="is-missing"' : ""}><span class="cmp-fix-name">${esc(labelOf(it))}</span>${named.has(String(it.id)) ? `<span class="chip chip-rose cmp-fix-flag">${esc(flag)}</span>` : ""}
          <button type="button" class="btn btn-secondary btn-sm" data-remove="${esc(it.id)}" aria-label="Remove ${esc(labelOf(it))} from compare">${iconHtml("x")}Remove</button></li>`).join("")}</ul>` : ""}
        ${retry ? `<button type="button" class="btn btn-secondary" data-retry>Try again</button>` : ""}</section>`;
  }

  function showLocked(note = "") {
    bodyEl.dataset.mode = "locked";
    actionsEl.hidden = true;
    toolbarEl.innerHTML = "";
    setNote("");
    if (!$(".cmp-lockline")) $(".dash-sub").insertAdjacentHTML("afterend", `<p class="cmp-lockline">${lockedBadgeHtml("Compare talent")}</p>`);
    bodyEl.innerHTML = `${note ? `<p class="form-alert show error" role="alert">${esc(note)}</p>` : ""}${lockedHtml()}`;
    bindPremiumLocks(page);
  }

  // ----- loading -----
  async function load() {
    const myId = ++st.loadId;
    if (!live()) return;
    if (st.sel.length < MIN_ITEMS) { st.data = null; showEmpty(); return; }
    if (isEmployer && !st.jobId) return;
    // Keep the old result on the screen (dimmed) while the new one loads. At the start, show a loading text.
    if (bodyEl.dataset.mode === "results") {
      const panelsEl = $("[data-panels]");
      panelsEl.classList.add("is-loading");
      panelsEl.setAttribute("aria-busy", "true");
      setNote("Updating the comparison…");
    } else showLoading();
    const ids = st.sel.map((x) => x.id);
    try {
      const res = isEmployer ? await api.recruiter.compare(ids, st.jobId) : await api.jobs.compare(ids);
      if (myId !== st.loadId || !live()) return;
      st.data = isEmployer ? employerResultsHtml(res, st.jobId) : talentResultsHtml(res);
      adoptTitles(st.data.items);
      setNote(st.overflow ? `You chose ${st.overflow} ${noun.many}. You can compare up to ${COMPARE_MAX}, so this page uses the first ${COMPARE_MAX}.` : "");
      drawResults();
      renderActions();
    } catch (err) {
      if (myId !== st.loadId || !live()) return;
      setNote("");
      handleError(err);
    }
  }

  // The answer knows the titles. Keep them in the basket, so that the tray and the picker show real names.
  function adoptTitles(items) {
    let diff = false;
    items.forEach((x) => {
      const it = st.sel.find((s) => s.id === x.id);
      if (!it) return;
      Object.entries(x).forEach(([k, v]) => { if (it[k] !== v) { it[k] = v; diff = true; } });
      if (isEmployer && it.title !== x.alias) { it.title = x.alias; diff = true; }
    });
    if (diff) persist();
  }

  function handleError(err) {
    if (isEmployer && (err.code === "PREMIUM_REQUIRED" || err.status === 403)) { showLocked("Your plan does not include Compare now."); return; }
    const named = st.sel.filter((it) => (err.missing || []).includes(String(it.id)));
    if (err.status === 404) {
      showError({
        title: `We can't compare these ${noun.many}`,
        message: named.length
          ? `${err.message || "One of them does not exist or was removed."} ${named.length === 1 ? `This ${noun.one} is not there any more` : `These ${noun.many} are not there any more`}: ${named.map(labelOf).join(", ")}. Remove ${named.length === 1 ? "it" : "them"}, then try again.`
          : `${err.message || "One of them does not exist or was removed."} Remove the ${noun.one} that is not there any more, then try again.`,
        missing: err.missing, flag: "Not found",
      });
    } else if (err.status === 400) {
      showError({ title: "We can't compare yet", message: err.fields?.ids || err.fields?.jobId || err.message || "Check your choice and try again.", missing: err.missing, flag: "Over the limit" });
    } else {
      showError({ title: "We could not load the comparison", message: err.message || "Something went wrong. Try again." });
    }
  }

  // ----- the picker -----
  function openPicker(trigger) {
    if (st.pickerOpen) return;
    st.pickerOpen = true;
    const work = new Map(st.sel.map((x) => [x.id, x]));
    const P = { mode: isEmployer ? "all" : "saved", q: "", page: 0, totalPages: 1, items: [], token: 0, loading: false, error: "" };
    const uid = Math.random().toString(36).slice(2, 7);
    const tabs = isEmployer ? [["all", "Talent for this job"], ["saved", "Saved talent"]] : [["saved", "Saved jobs"], ["recommended", "Recommended"]];
    const size = isEmployer ? PICK_PAGE_TALENT : PICK_PAGE_JOBS;

    const box = h("div", { class: "cmp-picker" });
    box.innerHTML = `
      <div class="tabs cmp-tabs" role="tablist" aria-label="${isEmployer ? "Which talent to show" : "Which jobs to show"}">
        ${tabs.map(([v, label], i) => `<button type="button" role="tab" class="tab" id="cmpTab-${uid}-${v}" data-tab="${v}" aria-controls="cmpPanel-${uid}" aria-selected="${i === 0}" tabindex="${i === 0 ? 0 : -1}">${esc(label)}</button>`).join("")}
      </div>
      <div class="field cmp-search"><label for="cmpSearch-${uid}">${isEmployer ? "Search by alias" : "Search all jobs by title, skill or company"}</label>
        <input id="cmpSearch-${uid}" class="text-input" type="search" autocomplete="off" maxlength="100" placeholder="${isEmployer ? "For example: Teal" : "For example: Data engineer"}"></div>
      <p class="hint cmp-pick-count" role="status" aria-live="polite" data-pick-count></p>
      <ul class="cmp-chip-list" data-chosen aria-label="Chosen now"></ul>
      <div id="cmpPanel-${uid}" role="tabpanel" class="cmp-pick-panel" aria-labelledby="cmpTab-${uid}-${P.mode}">
        <ul class="cmp-pick-list" data-list></ul>
        <p class="cmp-pick-msg" role="status" data-msg></p>
        <button type="button" class="btn btn-secondary btn-sm" data-more hidden>Show more</button>
      </div>`;
    const q = (s) => box.querySelector(s);
    const searchEl = q(`#cmpSearch-${uid}`), listEl = q("[data-list]"), msgEl = q("[data-msg]"), moreEl = q("[data-more]"), countP = q("[data-pick-count]"), chosenEl = q("[data-chosen]"), panelEl = q(".cmp-pick-panel");

    const norm = isEmployer
      ? (c) => ({
        id: c.id, title: c.alias, alias: c.alias,
        sub: [(c.roles || []).map((r) => r.title).filter(Boolean).slice(0, 2).join(", "), c.level, c.yearsExperience != null ? `${c.yearsExperience} years` : c.years, c.total ? `${c.matched || 0} of ${c.total} skills` : ""].filter(Boolean).join(" · "),
      })
      : (j) => ({ id: j.id, title: j.title, company: j.company || "", sub: [j.company, j.area || j.location].filter(Boolean).join(" · "), closed: j.status === "closed" });
    // What goes into the basket: short text only
    const basketItem = (it) => (isEmployer ? { id: it.id, alias: it.alias } : { id: it.id, title: it.title, company: it.company || "" });

    const chosenLabel = (it) => it.title && it.title !== it.id ? it.title : it.alias || it.id;
    function renderChosen(refocus) {
      chosenEl.innerHTML = [...work.values()].map((it) => `<li class="chip chip-neutral compare-chip"><span>${esc(chosenLabel(it))}</span><button type="button" data-unpick="${esc(it.id)}" aria-label="Remove ${esc(chosenLabel(it))} from the choice">${iconHtml("x")}</button></li>`).join("");
      chosenEl.hidden = work.size === 0;
      if (refocus) (chosenEl.querySelector("[data-unpick]") || searchEl).focus();
    }
    function refreshChecks() {
      const full = work.size >= COMPARE_MAX;
      listEl.querySelectorAll(".cmp-pick-check").forEach((cb) => {
        const on = work.has(cb.dataset.id);
        cb.checked = on;
        cb.disabled = full && !on;
        const chip = cb.closest("li").querySelector("[data-chosen-chip]");
        if (chip) chip.hidden = !on;
      });
      countP.textContent = `${work.size} of ${COMPARE_MAX} chosen. ${work.size < MIN_ITEMS ? `Choose at least ${MIN_ITEMS}.` : full ? "That is the most you can compare. Remove one to choose another." : "You can choose more."}`;
    }
    function renderList() {
      const needle = P.q.trim().toLowerCase();
      const shown = isEmployer && needle ? P.items.filter((i) => i.title.toLowerCase().includes(needle)) : P.items;
      listEl.innerHTML = shown.map((it) => `<li class="cmp-pick-item"><label class="cmp-pick-label">
          <input type="checkbox" class="cmp-pick-check" data-id="${esc(it.id)}"${work.has(it.id) ? " checked" : ""}${work.size >= COMPARE_MAX && !work.has(it.id) ? " disabled" : ""}>
          <span class="cmp-pick-text"><span class="cmp-pick-title">${esc(it.title)}</span>${it.sub ? `<span class="cmp-pick-sub">${esc(it.sub)}</span>` : ""}</span></label>
          ${it.closed ? `<span class="chip chip-rose">Closed</span>` : ""}<span class="chip chip-green" data-chosen-chip${work.has(it.id) ? "" : " hidden"}>Chosen</span></li>`).join("");
      let msg = "";
      if (P.loading) msg = "Loading…";
      else if (P.error) msg = P.error;
      else if (!shown.length) {
        msg = isEmployer
          ? (needle ? `No loaded profile has the alias “${P.q.trim()}”.${P.page < P.totalPages ? " Show more to load the next profiles." : ""}` : P.mode === "saved" ? "You have not saved any talent yet. Use Save on the Talent page." : "There is no talent for this job yet.")
          : (P.q ? `No jobs found for “${P.q}”.` : P.mode === "saved" ? "You have no saved jobs yet. Use the bookmark button on a job to save it." : "There are no recommended jobs yet.");
      }
      msgEl.textContent = msg;
      moreEl.hidden = !(P.page < P.totalPages);
      moreEl.disabled = P.loading;
    }
    async function fetchPage(page) {
      const token = ++P.token;
      P.loading = true; P.error = "";
      renderList();
      try {
        let res;
        if (isEmployer) res = await api.recruiter.candidates.list({ jobId: st.jobId, view: P.mode, page, pageSize: size, sort: "best" });
        else if (P.q) res = await api.jobs.search({ q: P.q, page, pageSize: size, sort: "best" });
        else if (P.mode === "saved") res = await api.bookmarks.list({ page, pageSize: size, sort: "saved" });
        else res = await api.jobs.recommended({ page, pageSize: size, sort: "best" });
        if (token !== P.token || !box.isConnected) return;
        const rows = (res.items || []).map(norm);
        const fresh = page === 1 ? rows : rows.filter((r) => !P.items.some((x) => x.id === r.id));
        P.items = page === 1 ? rows : P.items.concat(fresh);
        P.page = res.page?.page || page;
        P.totalPages = res.page?.totalPages || 1;
        P.loading = false;
        renderList();
        // After "Show more", the focus goes to the first new row, so that a keyboard user can go on
        if (page > 1 && fresh[0]) listEl.querySelector(`[data-id="${CSS.escape(fresh[0].id)}"]`)?.focus();
        return;
      } catch (err) {
        if (token !== P.token || !box.isConnected) return;
        P.error = err.message || "We could not load the list. Try again.";
      }
      P.loading = false;
      renderList();
    }
    const reload = () => { P.items = []; P.page = 0; P.totalPages = 1; fetchPage(1); };

    function selectTab(v, focus) {
      P.mode = v; P.q = ""; searchEl.value = "";
      box.querySelectorAll("[data-tab]").forEach((t) => {
        const on = t.dataset.tab === v;
        t.setAttribute("aria-selected", String(on));
        t.tabIndex = on ? 0 : -1;
        if (on && focus) t.focus();
      });
      panelEl.setAttribute("aria-labelledby", `cmpTab-${uid}-${v}`);
      panelEl.removeAttribute("aria-label");
      reload();
    }
    box.addEventListener("click", (e) => {
      const tab = e.target.closest("[data-tab]");
      if (tab) { selectTab(tab.dataset.tab, false); return; }
      if (e.target.closest("[data-more]")) { fetchPage(P.page + 1); return; }
      const un = e.target.closest("[data-unpick]");
      if (un) { work.delete(un.dataset.unpick); renderChosen(true); refreshChecks(); }
    });
    box.addEventListener("keydown", (e) => {
      const tab = e.target.closest?.("[data-tab]");
      if (tab && ["ArrowRight", "ArrowLeft", "Home", "End"].includes(e.key)) {
        e.preventDefault();
        const vals = tabs.map((t) => t[0]);
        const i = vals.indexOf(tab.dataset.tab);
        const next = e.key === "Home" ? 0 : e.key === "End" ? vals.length - 1 : (i + (e.key === "ArrowRight" ? 1 : -1) + vals.length) % vals.length;
        selectTab(vals[next], true);
        return;
      }
      // Enter in the search box or on a check box must not send the form (this would close the dialog)
      if (e.key === "Enter" && (e.target === searchEl || e.target.matches?.(".cmp-pick-check"))) {
        e.preventDefault();
        if (e.target === searchEl) { clearTimeout(timer); applySearch(); }
      }
    });
    box.addEventListener("change", (e) => {
      const cb = e.target.closest(".cmp-pick-check");
      if (!cb) return;
      const it = P.items.find((x) => x.id === cb.dataset.id);
      if (cb.checked) {
        if (work.size >= COMPARE_MAX || !it) { cb.checked = false; return; }
        work.set(it.id, basketItem(it));
      } else work.delete(cb.dataset.id);
      renderChosen(false);
      refreshChecks();
    });
    let timer = 0;
    function applySearch() {
      const text = searchEl.value;
      if (isEmployer) { P.q = text; renderList(); return; }       // the list of one job is filtered here, by alias
      const t = text.trim();
      if (t.length >= 2) {
        P.q = t;
        box.querySelectorAll("[data-tab]").forEach((x) => { x.setAttribute("aria-selected", "false"); });
        panelEl.removeAttribute("aria-labelledby");
        panelEl.setAttribute("aria-label", "Search results");
        reload();
      } else if (P.q) selectTab(P.mode, false);                   // the text is gone: back to the tab
    }
    searchEl.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(applySearch, 300); });

    const dlg = openModal({
      title: isEmployer ? "Choose talent to compare" : "Choose jobs to compare",
      intro: `Choose ${MIN_ITEMS} to ${COMPARE_MAX}. Your choice stays in your compare list.`,
      content: [box],
      submitText: "Done",
      async onSubmit() {
        const items = [...work.values()].slice(0, COMPARE_MAX);
        const same = items.length === st.sel.length && items.every((x, i) => x.id === st.sel[i].id);
        if (!same) {
          const known = new Map(st.sel.map((x) => [x.id, x]));
          st.sel = items.map((x) => known.get(x.id) || x);
          changed(`${st.sel.length} ${plural(st.sel.length, noun.one, noun.many)} chosen.`);
        }
        return true;
      },
    });
    dlg.classList.add("cmp-picker-dialog");
    const onHash = () => dlg.close();
    window.addEventListener("hashchange", onHash);
    dlg.addEventListener("close", () => {
      clearTimeout(timer);
      window.removeEventListener("hashchange", onHash);
      st.pickerOpen = false;
      const back = trigger && trigger.isConnected && !trigger.disabled ? trigger : addBtn;
      if (live()) (back.isConnected && !back.disabled ? back : $("h1")).focus();
    });
    renderChosen(false);
    refreshChecks();
    fetchPage(1);
  }

  // ----- events -----
  page.addEventListener("click", (e) => {
    const rm = e.target.closest("[data-remove]");
    if (rm) { removeItem(rm.dataset.remove); return; }
    const add = e.target.closest("[data-add]");
    if (add) { if (!add.disabled) openPicker(add); return; }
    if (e.target.closest("[data-clear]")) { clearAll(); return; }
    if (e.target.closest("[data-retry]")) { load(); }
  });

  // ----- start -----
  const urlIds = parseIds(ctx.query?.ids);
  let ids = urlIds.length ? urlIds : compareStore.items(kind).map((x) => x.id);
  if (ids.length > COMPARE_MAX) { st.overflow = ids.length; ids = ids.slice(0, COMPARE_MAX); }
  const stored = new Map(compareStore.items(kind).map((x) => [x.id, x]));
  st.sel = ids.map((id) => stored.get(id) || { id, title: id });

  if (isEmployer) {
    // A Basic employer sees the locked page. No compare request, no talent request.
    let ent;
    bodyEl.innerHTML = `<div class="empty cmp-loading" role="status"><p>Loading…</p></div>`;
    try { ent = await api.entitlements.get(); } catch (err) { showError({ title: "We could not open Compare", message: err.message || "Something went wrong. Try again.", items: false, retry: false }); return; }
    if (!live()) return;
    if (!(ent.canCompare === true || ent.plan === "premium")) { showLocked(); return; }
    try {
      const res = await api.recruiter.jobs.list({ pageSize: 50, sort: "newest" });
      st.jobs = (res.items || []).map((j) => ({ id: j.id, title: j.title, closed: j.badge === "closed" }));
      const want = ctx.query?.jobId;
      if (want && !st.jobs.some((j) => j.id === want) && res.page?.totalPages > 1) {
        // The job is on a later page of the list: read this one job
        try { const j = await api.recruiter.jobs.get(want); st.jobs.push({ id: j.id, title: j.title, closed: j.badge === "closed" }); } catch { /* the job is not yours: it is ignored */ }
      }
    } catch (err) { showError({ title: "We could not load your jobs", message: err.message || "Something went wrong. Try again.", items: false, retry: false }); return; }
    if (!live()) return;
    const open = st.jobs.filter((j) => !j.closed);
    const last = sessionStorage.getItem(LAST_JOB_KEY(userId));
    const want = ctx.query?.jobId;
    st.jobId = (want && st.jobs.some((j) => j.id === want) && want) || (last && open.some((j) => j.id === last) && last) || open[0]?.id || "";
    if (!st.jobId) {
      bodyEl.innerHTML = `<section class="panel cmp-empty"><div class="empty"><div class="icon-tile accent">${iconHtml("briefcase")}</div>
        <h2>You have no open job</h2><p>Compare works for one of your jobs, because the match is for this job. Post a job first.</p>
        <a class="btn btn-primary" href="#/my-jobs/new">Post a job</a></div></section>`;
      return;
    }
    const shown = st.jobs.filter((j) => !j.closed || j.id === st.jobId);
    toolbarEl.innerHTML = `<div class="field cmp-job-field"><label for="cmpJob">For which job?</label>
      <select id="cmpJob" class="text-input select" data-job aria-describedby="cmpJobHint">${shown.map((j) => `<option value="${esc(j.id)}"${j.id === st.jobId ? " selected" : ""}>${esc(j.title)}${j.closed ? " (closed)" : ""}</option>`).join("")}</select>
      <p class="hint" id="cmpJobHint">The match is for this job. If you change the job, the comparison loads again.</p></div>`;
    toolbarEl.querySelector("[data-job]").addEventListener("change", (e) => {
      st.jobId = e.target.value;
      try { sessionStorage.setItem(LAST_JOB_KEY(userId), st.jobId); } catch { /* storage is blocked: the choice is not kept */ }
      persist();
      announce(`Now comparing for ${e.target.selectedOptions[0]?.textContent || "this job"}.`);
      load();
    });
    try { sessionStorage.setItem(LAST_JOB_KEY(userId), st.jobId); } catch { /* ignore */ }
  }

  persist();
  renderActions();
  await load();
  // Fewer than 2 items: the picker is open from the start
  if (live() && st.sel.length < MIN_ITEMS && bodyEl.dataset.mode === "empty") openPicker(addBtn);
}
