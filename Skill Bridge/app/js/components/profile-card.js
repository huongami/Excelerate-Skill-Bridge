// The shared (anonymous) profile: what an employer sees. Allowlist fields only — no name, contact or CV (Feature 5 NFR).
// V2 adds: level, exact years, skill levels, certifications and awards (names and years only). A snapshot of an older
// application does not have these keys, and then the rows are left out.
import { esc } from "../core/dom.js";
import { skillLevelLabel } from "../data/levels.js";

const MAX_NAMES = 3;

const row = (label, values) => {
  const list = (values || []).filter(Boolean);
  return `<div class="pf-row"><dt>${esc(label)}</dt><dd>${list.length ? list.map((v) => `<span class="chip chip-neutral">${esc(v)}</span>`).join("") : `<span class="muted">Not given</span>`}</dd></div>`;
};

const yearText = (v) => String(Math.round(Number(v) * 10) / 10);
const hasKey = (p, k) => p && p[k] !== undefined;
/** "Cloud Cert (2023)": the name and the year only. An employer sees nothing else of a certification or an award. */
const named = (items) => (Array.isArray(items) ? items : []).map((x) => {
  const name = typeof x === "string" ? x : x?.name;
  const year = typeof x === "object" && x?.year ? ` (${x.year})` : "";
  return name ? `${name}${year}` : "";
}).filter(Boolean);

/** The experience as the employer reads it: the exact years when the talent gave them, else the range. */
export function experienceOf(p) {
  if (p?.yearsExperience != null && p.yearsExperience !== "" && Number.isFinite(Number(p.yearsExperience))) {
    const y = yearText(p.yearsExperience);
    return `${y} ${Number(y) === 1 ? "year" : "years"}`;
  }
  return p?.years != null && p.years !== "" ? String(p.years) : "";
}

/** Skill chips (green). With `skillLevels` each chip has the level as a word: "Python · Advanced". */
export function skillChipsHtml(p, max = Infinity) {
  const levels = new Map((Array.isArray(p?.skillLevels) ? p.skillLevels : []).map((s) => [String(s.name).toLowerCase(), s.level]));
  return (p?.skills || []).slice(0, max).map((s) => {
    const lvl = skillLevelLabel(levels.get(String(s).toLowerCase()));
    return `<span class="chip chip-green">${esc(s)}${lvl ? `<span class="pf-skill-level"> · ${esc(lvl)}</span>` : ""}</span>`;
  }).join("");
}

/** Short lines for small panels (Home): level and years, then certifications and awards (the first 3 names). */
export function sharedFactsHtml(p) {
  const lines = [];
  const exp = experienceOf(p);
  if (p?.level || exp) lines.push(`<strong>Level:</strong> ${esc(p.level || "Not given")}${exp ? ` · ${esc(exp)}` : ""}`);
  const list = (label, items) => {
    const names = named(items);
    if (!names.length) return;
    const more = names.length - MAX_NAMES;
    lines.push(`<strong>${label}:</strong> ${esc(names.slice(0, MAX_NAMES).join(", "))}${more > 0 ? ` +${more} more` : ""}`);
  };
  list("Certifications", p?.certifications);
  list("Awards", p?.awards);
  return lines.map((l) => `<p class="tr-preview-line">${l}</p>`).join("");
}

/** @param {object} p SharedProfile or a snapshot of it */
export function sharedProfileHtml(p, { title = "" } = {}) {
  const exp = experienceOf(p);
  const skills = (p.skills || []).length
    ? `<div class="pf-row"><dt>Skills</dt><dd>${skillChipsHtml(p)}</dd></div>`
    : row("Skills", []);
  return `
    <div class="profile-card">
      ${title ? `<h3 class="pf-title">${esc(title)}</h3>` : ""}
      <p class="pf-alias"><span class="avatar avatar-sm" aria-hidden="true">${esc((p.alias || "?").split(/\s+/).map((w) => w[0]).join("").slice(0, 2))}</span><strong>${esc(p.alias || "Anonymous")}</strong></p>
      <dl class="pf-list">
        ${row("Roles", (p.roles || []).map((r) => (r.anzsco ? `${r.title} (ANZSCO ${r.anzsco})` : r.title)))}
        ${hasKey(p, "level") ? row("Level", p.level ? [p.level] : []) : ""}
        ${exp ? row("Experience", [exp]) : ""}
        ${skills}
        ${hasKey(p, "certifications") ? row("Certifications", named(p.certifications)) : ""}
        ${hasKey(p, "awards") ? row("Awards", named(p.awards)) : ""}
        ${row("Qualifications", p.qualifications)}
        ${p.industries ? row("Domains", p.industries) : ""}
        ${p.targetRoles ? row("Target roles", p.targetRoles) : ""}
        ${p.locations ? row("Locations", p.locations) : ""}
        ${p.workTypes ? row("Work types", p.workTypes) : ""}
      </dl>
    </div>`;
}
