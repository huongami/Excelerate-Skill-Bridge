// Onboarding dialog for candidate accounts (Feature 2: explainable cross-border skill translation).
// Path A (CV):   cv -> reading -> education -> experience -> skills -> credentials -> translation -> goals -> review
// Path B (skip): cv -> education -> experience -> skills -> credentials -> translation -> goals -> review
// The AI fills fields from the CV ("AI-detected"); fields it cannot find stay empty ("Missing").
// V2 (R1): the CV also gives the current role, the desired role, the level, the exact years, certifications and awards.
// Each one has a "from your CV" hint, or a muted hint when the CV does not show it. The talent can change every field.
// The candidate accepts, edits or removes each translated skill, and sets a level (1 to 5) for each skill. Only accepted skills reach employers.
// The data is used only to recommend jobs and to build the translated profile. See AI_Rule.md Rule 5 (PII).
import { h, icon, toList, announce } from "../core/dom.js";
import { api } from "../api/index.js";
import { CONFIG } from "../config.js";
import { createCombobox } from "./combobox.js";
import * as R from "../data/reference.js";
import { LEVELS, SKILL_LEVELS, skillLevelLabel } from "../data/levels.js";
import { experienceOf } from "./profile-card.js";

const MAX_CV_BYTES = 10 * 1024 * 1024; // Feature 2 AC1: proposed limit 10 MB
const CV_TYPES = [".pdf", ".docx"];
const POLL_MS = 600;
const POLL_LIMIT_MS = 30000;
const MAX_CREDENTIALS = 20;      // certifications and awards: the most rows in each list
const MIN_YEAR = 1990;
const PATHS = {
  cv: ["cv", "reading", "education", "experience", "skills", "credentials", "translation", "goals", "review"],
  skip: ["cv", "education", "experience", "skills", "credentials", "translation", "goals", "review"],
};
// What employers read next to these lists (decision D5): the names show at once, so no names of people or employers
const NAMES_HINT = "Employers see these names. Do not write your own name, your employer's name or contact details here.";
// What to tell when the CV does not show a field (R1, decision F11: the field stays empty, nothing is guessed)
const NOT_FOUND = {
  currentRole: "We could not find your current role in your CV. You can add it.",
  targetRole: "We could not find your desired role in your CV. You can add it.",
  level: "We could not find your level in your CV. You can choose it.",
  yearsExperience: "We could not find your years of experience in your CV. You can add them.",
  certifications: "We could not find certifications in your CV. You can add them.",
  awards: "We could not find awards in your CV. You can add them.",
};
const certByName = new Map(R.CERTIFICATIONS.map((c) => [c.name.toLowerCase(), c]));

let dialog, body, foot, stepLabel, bar, state, onDone;

const optionalTag = () => h("span", { class: "optional", text: " (optional)" });
const nextYear = () => new Date().getFullYear() + 1;

/** The band (the drop-down "Total years of work experience") for an exact number of years. The server uses the same rule. */
export function bandOf(years) {
  const y = Number(years);
  if (!Number.isFinite(y)) return "";
  return y < 1 ? R.YEARS[0] : y < 3 ? R.YEARS[1] : y < 6 ? R.YEARS[2] : y <= 10 ? R.YEARS[3] : R.YEARS[4];
}
// The level that the server gives a skill when the talent sets none (rule F8): Strong 4, Moderate 3, Limited 2
const evidenceLevel = (evidence) => ({ Strong: 4, Moderate: 3, Limited: 2 }[evidence] || 3);

// A year: a whole number from 1990 to next year, or null
const yearOrNull = (v) => {
  const n = Number(String(v ?? "").trim());
  return String(v ?? "").trim() !== "" && Number.isInteger(n) ? n : null;
};

// Clean the V2 keys of the profile (an old profile, a CV result or a draft may have them in odd shapes)
function normalizeProfile(d) {
  d.level = LEVELS.includes(d.level) ? d.level : "";
  const ye = d.yearsExperience === "" || d.yearsExperience == null ? NaN : Number(d.yearsExperience);
  d.yearsExperience = Number.isFinite(ye) && ye >= 0 && ye <= 40 ? ye : null;
  if (d.yearsExperience != null) d.years = bandOf(d.yearsExperience);
  const text = (v, n) => String(v ?? "").trim().slice(0, n);
  d.certifications = toList(d.certifications).map((c) => (typeof c === "string" ? { name: c } : c || {}))
    .map((c) => ({ name: text(c.name, 120), issuer: text(c.issuer, 120), year: yearOrNull(c.year) })).filter((c) => c.name).slice(0, MAX_CREDENTIALS);
  d.awards = toList(d.awards).map((a) => (typeof a === "string" ? { name: a } : a || {}))
    .map((a) => ({ name: text(a.name, 120), kind: R.AWARD_KINDS.some((k) => k.kind === a.kind) ? a.kind : "", year: yearOrNull(a.year) })).filter((a) => a.name).slice(0, MAX_CREDENTIALS);
}

const isEmptyValue = (v) => (Array.isArray(v) ? !v.length : v == null || v === "");

// ---------- "From your CV" hints (R1) ----------
function cvHint(name) {
  const el = h("p", { class: "hint cv-hint", "data-cv-hint": name });
  paintHint(el, name);
  return el;
}
function paintHint(el, name) {
  const found = state.detected.has(name);
  const notFound = !found && state.fromCv && state.found[name] === false && isEmptyValue(state.data[name]);
  el.className = `hint cv-hint${notFound ? " cv-hint-missing" : ""}`;
  el.replaceChildren(...(found ? [icon("check"), "From your CV. Check it. Change it if it is wrong."] : notFound ? [NOT_FOUND[name]] : []));
}

// ---------- "AI-detected" and "Missing" markers (Feature 2 AC2, AC6) ----------
function markerFor(name) {
  const box = h("span", { class: "field-markers", "data-marker": name });
  paintMarker(box, name);
  return box;
}
function paintMarker(box, name) {
  const empty = !toList(state.data[name]).length;
  box.replaceChildren(
    state.detected.has(name) ? h("span", { class: "chip chip-ai", title: "The AI found this in your CV. Check it." }, icon("check"), "AI-detected") : "",
    !state.detected.has(name) && state.missing.has(name) && empty ? h("span", { class: "chip chip-yellow", title: "Your CV does not show this. Add it if you can." }, "Missing") : "");
}
// The candidate changed a field: it is no longer only "AI-detected"
function touched(name) {
  state.detected.delete(name);
  body.querySelectorAll(`[data-marker="${name}"]`).forEach((b) => paintMarker(b, name));
  body.querySelectorAll(`[data-cv-hint="${name}"]`).forEach((e) => paintHint(e, name));
}

// `control` is a combobox ({ el, input }) or a plain element. `cv: true` adds the "from your CV" hint (R1).
function field(name, labelText, control, { optional, hint, cv } = {}) {
  const input = control.input || control;
  const hintId = hint ? `${name}-hint` : null;
  if (hintId) input.setAttribute("aria-describedby", hintId);
  return h("div", { class: "field", "data-field": name },
    h("div", { class: "field-row" }, h("label", { for: input.id }, labelText, optional ? optionalTag() : null), markerFor(name)),
    control.el || control,
    hint ? h("div", { class: "hint", id: hintId, text: hint }) : null,
    cv ? cvHint(name) : null,
    h("div", { class: "field-error", id: `${name}-error` }));
}
// Searchable dropdown. With allowCustom, the user can type a value that is not in the list.
function combo(name, options, placeholder, { allowCustom = true } = {}) {
  return createCombobox({ id: `ob-${name}`, options, value: state.data[name] || "", placeholder, allowCustom,
    onChange: (v) => { state.data[name] = v.trim(); touched(name); } });
}
// List field: searchable dropdown + "Add" button + removable chips. The user can pick
// several options and add values that are not in the list.
function multiCombo(name, labelText, options, { placeholder, hint, optional, max = 5, suggestions, custom = true, cv = false, notFoundText = "" } = {}) {
  state.data[name] = toList(state.data[name]);
  const values = () => state.data[name];
  const chips = h("ul", { class: "skill-list", "aria-label": labelText });
  const box = createCombobox({ id: `ob-${name}`, options, placeholder, clearOnPick: true, allowCustom: custom, onPick: (v) => add(v), exclude: values });
  const input = box.input;
  input.setAttribute("maxlength", "60");
  const hintId = `${name}-hint`;
  input.setAttribute("aria-describedby", hintId);
  const addBtn = h("button", { type: "button", class: "btn btn-secondary", "aria-label": `Add to ${labelText}`, onclick: () => add(input.value) }, icon("plus"), "Add");
  const suggest = suggestions ? h("div", { class: "suggestions" }) : null;
  const count = h("span", { class: "list-count", "aria-live": "polite" });

  function add(raw) {
    const v = String(raw).trim().replace(/\s+/g, " ");
    if (!v) return;
    const known = options.find((o) => o.toLowerCase() === v.toLowerCase());
    if (!known && !custom) {   // a list that takes only the listed values (the domains)
      error(name, notFoundText || "Choose a value from the list.");
      return input.focus();
    }
    clearFieldError(name);
    const match = known || v;
    if (!values().some((x) => x.toLowerCase() === match.toLowerCase()) && values().length < max) { values().push(match); touched(name); }
    input.value = "";
    paint();
    input.focus();
  }
  function paint() {
    chips.replaceChildren(...values().map((v) => h("li", { class: "skill-chip" }, v,
      h("button", { type: "button", "aria-label": `Remove ${v}`, onclick: () => { state.data[name] = values().filter((x) => x !== v); touched(name); paint(); input.focus(); } }, icon("x")))));
    const full = values().length >= max;
    input.disabled = full;
    addBtn.disabled = full;
    input.placeholder = full ? `Maximum ${max} reached` : placeholder;
    count.textContent = `${values().length} of ${max}`;
    if (suggest) {
      const ideas = suggestions().filter((s) => !values().some((x) => x.toLowerCase() === s.toLowerCase()));
      suggest.replaceChildren(...(ideas.length && !full ? [h("span", { class: "hint", text: "Suggestions:" }),
        ...ideas.map((s) => h("button", { type: "button", class: "choice", onclick: () => add(s) }, icon("plus"), s))] : []));
    }
  }
  // Text that is typed but not added yet is added when the user presses Continue
  state.flush.push(() => input.value.trim() && add(input.value));
  paint();
  return h("div", { class: "field", "data-field": name },
    h("div", { class: "field-row" }, h("label", { for: input.id }, labelText, optional ? optionalTag() : null), h("span", { class: "field-row-end" }, markerFor(name), count)),
    h("div", { class: "input-row" }, box.el, addBtn),
    h("div", { class: "hint", id: hintId, text: hint }),
    cv ? cvHint(name) : null,
    h("div", { class: "field-error", id: `${name}-error` }),
    chips, suggest);
}

// Toggle buttons for multi-select choices (aria-pressed)
function choices(name, labelText, options, { optional, hint, max } = {}) {
  const labelId = `ob-${name}-label`;
  const selected = new Set(state.data[name] || []);
  const group = h("div", { class: "choice-group", role: "group", "aria-labelledby": labelId, id: `ob-${name}` });
  options.forEach((o) => {
    const btn = h("button", { type: "button", class: "choice", "aria-pressed": String(selected.has(o)), text: o,
      onclick: () => {
        if (selected.has(o)) selected.delete(o);
        else if (!max || selected.size < max) selected.add(o);
        btn.setAttribute("aria-pressed", String(selected.has(o)));
        state.data[name] = [...selected];
      } });
    group.append(btn);
  });
  return h("div", { class: "field", "data-field": name },
    h("span", { class: "field-label", id: labelId }, labelText, optional ? optionalTag() : null),
    hint ? h("div", { class: "hint hint-top", text: hint }) : null,
    group,
    h("div", { class: "field-error", id: `${name}-error` }));
}

// Mock mode only: say that the fields come from a sample CV (AI_Rule.md Rule 4: no sample data shown as real)
function demoBanner() {
  if (CONFIG.API_MODE !== "mock" || !state.sampleLabel) return null;
  return h("p", { class: "demo-banner", role: "note" }, icon("alert"),
    h("span", { text: `Demo mode: the mock API filled these fields from a sample CV (${state.sampleLabel}), not from your file.` }));
}
// Path A: tell the candidate to check what the AI found
function checkNote() {
  if (!state.fromCv) return null;
  return h("p", { class: "privacy-note" }, icon("check"), h("span", { text: "Check what we found in your CV. Change anything that is wrong. Fields marked “Missing” were not in your CV." }));
}
// R1: what the CV showed, in one place. Each line is a field that the talent can change in the next steps.
// Only the V2 backend sends `found`. Without it (the mock, an old server) there is nothing to show.
function foundSummary() {
  if (!state.fromCv || !Object.keys(state.found).length) return null;
  const d = state.data;
  const items = [
    ["currentRole", "Current role", toList(d.currentRole)[0] || ""],
    ["targetRole", "Desired role", toList(d.targetRole)[0] || ""],
    ["level", "Level", d.level || ""],
    ["yearsExperience", "Years of experience", d.yearsExperience != null ? experienceOf(d) : ""],
    ["certifications", "Certifications", d.certifications.length ? `${d.certifications.length} found` : ""],
    ["awards", "Awards", d.awards.length ? `${d.awards.length} found` : ""],
  ].filter(([key]) => key in state.found);
  return h("div", { class: "cv-found", role: "note", "aria-labelledby": "cvFoundTitle" },
    h("h3", { id: "cvFoundTitle", class: "cv-found-title", text: "What we found in your CV" }),
    h("ul", { class: "cv-found-list" }, items.map(([key, label, value]) => {
      const ok = state.found[key] !== false && value;
      return h("li", { class: ok ? "is-found" : "is-missing" }, icon(ok ? "check" : "alert"),
        h("span", { class: "cv-found-label", text: `${label}: ` }),
        ok ? h("strong", { text: value }) : h("span", { class: "muted", text: "Not found. You can add it in the next steps." }));
    })),
    h("p", { class: "hint", text: "You can change every field in the next steps." }));
}

// ---------- Errors ----------
function clearErrors() {
  body.querySelectorAll(".field-error").forEach((e) => (e.textContent = ""));
  body.querySelectorAll("[aria-invalid]").forEach((e) => { e.removeAttribute("aria-invalid"); e.classList.remove("invalid"); });
  body.querySelector(".form-alert")?.remove();
}
function error(name, msg) {
  const box = body.querySelector(`[data-field="${name}"]`);
  box.querySelector(".field-error").textContent = msg;
  const control = box.querySelector("input, select, .choice-group, [data-focus]");
  control.setAttribute("aria-invalid", "true");
  control.classList.add("invalid");
  const described = [control.getAttribute("aria-describedby"), `${name}-error`].filter(Boolean);
  control.setAttribute("aria-describedby", [...new Set(described.join(" ").split(" "))].join(" "));
  return false;
}
function clearFieldError(name) {
  const box = body.querySelector(`[data-field="${name}"]`);
  if (!box) return;
  box.querySelector(".field-error").textContent = "";
  box.querySelectorAll("[aria-invalid]").forEach((e) => { e.removeAttribute("aria-invalid"); e.classList.remove("invalid"); });
}
// An error under one input of a row (certifications and awards). The input points to its message with aria-describedby.
function rowError(input, msg) {
  const err = input.closest(".field")?.querySelector(".field-error");
  if (!err) return false;
  err.textContent = msg;
  input.setAttribute("aria-invalid", "true");
  input.classList.add("invalid");
  input.setAttribute("aria-describedby", [...new Set([...(input.getAttribute("aria-describedby") || "").split(" "), err.id].filter(Boolean))].join(" "));
  return false;
}
function focusFirstError() {
  const first = body.querySelector("[aria-invalid='true']");
  (first?.matches(".choice-group") ? first.querySelector("button") : first)?.focus();
}
const inList = (name, list, msg) => (list.includes(state.data[name]) ? true : error(name, msg));
const atLeast = (name, n, msg) => ((state.data[name] || []).length >= n ? true : error(name, msg));
// The answers that a complete profile must have (the same rules as the steps)
const REQUIRED = ["qualification", "fieldOfStudy", "currentRole", "industry", "years", "skills", "translation", "targetRole", "locations", "workTypes"];
function filled(name) {
  const v = state.data[name];
  if (name === "translation") return (v || []).some(SHARED);
  if (name === "years") return R.YEARS.includes(v);
  return toList(v).length >= (name === "skills" ? 3 : 1);
}
const alertBox = (msg) => { body.querySelector(".form-alert")?.remove(); body.prepend(h("div", { class: "form-alert show error", role: "alert", text: msg })); };

// ---------- Translation step helpers ----------
const SHARED = (s) => s.status === "accepted" || s.status === "edited";
const KIND = { "cross-border": ["chip-pink", "Cross-border"], "cross-industry": ["chip-blue", "Cross-industry"], direct: ["chip-neutral", "Direct"] };
const EVIDENCE = { Strong: "chip-green", Moderate: "chip-yellow", Limited: "chip-neutral" };
const SOURCE = { role: "From your role", skill: "From your skills", qualification: "From your qualification" };

// A level (1 to 5) for one skill. Only the skills that the talent named have it; a skill from a role or a qualification has none.
// The first option leaves the level to the server, which uses the evidence (rule F8). The talent can set it at any time.
const levelFromCv = new WeakSet();   // skill cards whose level came from the CV and that the talent did not change
function levelPick(s, onLevel) {
  const id = `tr-level-${String(s.id).replace(/[^A-Za-z0-9_-]/g, "-")}`;
  const from = h("span", { class: "hint tr-level-from", hidden: !levelFromCv.has(s) }, icon("check"), "From your CV");
  const sel = h("select", { id, class: "text-input select tr-level-select", "data-level-for": s.id,
    onchange: () => { s.level = sel.value ? Number(sel.value) : null; state.levelTouched.add(s.id); levelFromCv.delete(s); from.hidden = true; onLevel && onLevel(); } },
    h("option", { value: "", text: `From the evidence (${skillLevelLabel(evidenceLevel(s.evidence))})` }),
    ...SKILL_LEVELS.map((l) => h("option", { value: String(l.value), text: `${l.value} · ${l.label}` })));
  sel.value = Number.isInteger(s.level) && s.level >= 1 && s.level <= 5 ? String(s.level) : "";
  return h("div", { class: "tr-level" }, h("label", { for: id }, "Level", h("span", { class: "sr-only", text: ` for ${s.mapped}` })), sel, from);
}

function translationCard(s, repaint, refreshPreview) {
  const [kindClass, kindText] = KIND[s.kind] || KIND.direct;
  const accepted = SHARED(s);
  const accept = h("button", { type: "button", class: "btn btn-secondary btn-sm tr-accept", "aria-pressed": String(accepted),
    "aria-label": `${accepted ? "Accepted" : "Accept"}: ${s.mapped}`,
    onclick: () => { s.status = accepted ? "suggested" : "accepted"; repaint(); announce(`${s.mapped} ${accepted ? "is not accepted" : "accepted"}.`); } },
    icon("check"), accepted ? "Accepted" : "Accept");
  const edit = h("button", { type: "button", class: "btn btn-ghost btn-sm", "aria-label": `Edit ${s.mapped}`, onclick: () => openEditor() }, "Edit");
  const remove = h("button", { type: "button", class: "btn btn-ghost btn-sm", "aria-label": `Remove ${s.mapped}`,
    onclick: () => { s.status = "removed"; repaint(); announce(`${s.mapped} removed. You can undo this below.`); } }, icon("x"), "Remove");
  const actions = h("div", { class: "tr-actions" }, accept, edit, remove);
  const card = h("li", { class: `tr-card${accepted ? " is-accepted" : ""}` },
    h("div", { class: "tr-tags" },
      h("span", { class: `chip ${kindClass}`, text: kindText }),
      h("span", { class: `chip ${EVIDENCE[s.evidence] || "chip-neutral"}`, title: "How much evidence supports this skill" }, `Evidence: ${s.evidence}`),
      s.status === "edited" ? h("span", { class: "chip chip-neutral", text: "Edited by you" }) : null),
    h("div", { class: "tr-map" },
      h("span", { class: "tr-from" }, h("span", { class: "sr-only", text: `${SOURCE[s.source] || "Original"}: ` }), s.original),
      icon("arrow"),
      h("strong", { class: "tr-to", text: s.mapped }),
      s.anzsco ? h("span", { class: "chip chip-blue tr-anzsco", title: "Australian occupation code" }, `ANZSCO ${s.anzsco}`) : null),
    h("p", { class: "tr-reason", text: s.reason }),
    s.evidenceText ? h("p", { class: "tr-evidence" }, h("span", { class: "tr-evidence-label", text: "From your CV: " }), `“${s.evidenceText}”`) : null,
    s.source === "skill" ? levelPick(s, refreshPreview) : null,
    actions);

  // Inline editor: change the Australian skill name (the candidate is in control)
  function openEditor() {
    const id = `tr-edit-${s.id}`;
    const box = createCombobox({ id, options: R.SKILLS, value: s.mapped, placeholder: "Skill name" });
    const save = h("button", { type: "button", class: "btn btn-primary btn-sm", text: "Save" });
    const cancel = h("button", { type: "button", class: "btn btn-ghost btn-sm", text: "Cancel", onclick: () => repaint() });
    const err = h("div", { class: "field-error", id: `${id}-error` });
    save.addEventListener("click", () => {
      const v = box.input.value.trim().replace(/\s+/g, " ");
      if (v.length < 2) { err.textContent = "Enter a skill name."; box.input.setAttribute("aria-invalid", "true"); box.input.setAttribute("aria-describedby", err.id); return box.input.focus(); }
      if (v !== s.mapped) { s.mapped = v; s.status = "edited"; } else s.status = "accepted";
      repaint();
      announce(`${v} saved.`);
    });
    box.input.addEventListener("keydown", (e) => { if (e.key === "Enter" && box.input.getAttribute("aria-expanded") !== "true") { e.preventDefault(); save.click(); } });
    actions.replaceWith(h("div", { class: "tr-editor" }, h("label", { for: id, class: "field-label", text: "Australian skill name" }), h("div", { class: "input-row" }, box.el, save, cancel), err));
    box.input.focus();
  }
  return card;
}

// "What employers see": built from the candidate's own decisions. The API builds the real view (GET /me/shared-profile).
function previewPanel() {
  const shared = (state.data.translation || []).filter(SHARED);
  const roles = shared.filter((s) => s.anzsco);
  const skills = [...new Set(shared.filter((s) => s.source !== "qualification").map((s) => s.mapped))];
  const quals = shared.filter((s) => s.source === "qualification").map((s) => s.mapped);
  const d = state.data;
  const exp = d.yearsExperience != null ? experienceOf(d) : d.years || "";
  const names = (items) => (items || []).map((x) => `${x.name}${x.year ? ` (${x.year})` : ""}`).join(", ");
  // A skill that the talent set a level for shows it: "Python · Advanced"
  const levelOf = (name) => skillLevelLabel(shared.find((s) => s.mapped === name && s.source === "skill")?.level);
  return h("aside", { class: "tr-preview", "aria-labelledby": "trPreviewTitle" },
    h("h3", { id: "trPreviewTitle", text: "What employers see" }),
    h("p", { class: "hint", text: "Your alias and the skills you accept. Never your name, contact details, photo, nationality, employer names or your CV." }),
    h("p", { class: "tr-preview-alias" }, h("span", { class: "alias-badge", text: state.alias || "Your alias" })),
    roles.length ? h("p", { class: "tr-preview-line" }, h("strong", { text: "Roles: " }), roles.map((r) => `${r.occupation || r.mapped} (ANZSCO ${r.anzsco})`).join(", ")) : null,
    d.level || exp ? h("p", { class: "tr-preview-line" }, h("strong", { text: "Level: " }), [d.level || "Not given", exp].filter(Boolean).join(" · ")) : null,
    h("div", { class: "tr-preview-skills" }, skills.length ? skills.map((x) => h("span", { class: "chip chip-green", text: levelOf(x) ? `${x} · ${levelOf(x)}` : x })) : h("span", { class: "hint", text: "No skills accepted yet." })),
    d.certifications.length ? h("p", { class: "tr-preview-line" }, h("strong", { text: "Certifications: " }), names(d.certifications)) : null,
    d.awards.length ? h("p", { class: "tr-preview-line" }, h("strong", { text: "Awards: " }), names(d.awards)) : null,
    quals.length ? h("p", { class: "tr-preview-line" }, h("strong", { text: "Qualifications: " }), quals.join(", ")) : null);
}

// ---------- Level and exact years (R1, F7) ----------
function levelField() {
  const sel = h("select", { id: "ob-level", class: "text-input select" },
    h("option", { value: "", text: "Not sure" }), ...LEVELS.map((l) => h("option", { value: l, text: l })));
  sel.value = state.data.level || "";
  sel.addEventListener("change", () => { state.data.level = sel.value; touched("level"); });
  return field("level", "Your level", sel, { optional: true, cv: true, hint: "The level of your current or latest role. Choose “Not sure” if you do not know." });
}
// An optional number. When it is set, the range of years is chosen for the talent (the server does the same).
function exactYearsField(yearsBox) {
  const input = h("input", { id: "ob-yearsExperience", type: "number", class: "text-input", min: "0", max: "40", step: "0.5", inputmode: "decimal",
    value: state.data.yearsExperience ?? "" });
  const lock = () => {
    const locked = state.data.yearsExperience != null;
    yearsBox.input.disabled = locked;
    yearsBox.el.querySelector(".combo-toggle")?.toggleAttribute("disabled", locked);
  };
  input.addEventListener("input", () => {
    const raw = input.value.trim();
    const n = Number(raw);
    state.data.yearsExperience = raw !== "" && Number.isFinite(n) && n >= 0 && n <= 40 ? n : null;
    if (state.data.yearsExperience != null) {
      state.data.years = bandOf(n);
      yearsBox.input.value = state.data.years;
      touched("years");
    }
    touched("yearsExperience");
    lock();
  });
  lock();
  return field("yearsExperience", "Exact years of experience", input, { optional: true, cv: true,
    hint: "A number from 0 to 40. Use 0.5 for half a year. If you add it, we choose the range below for you." });
}
function exactYearsOk() {
  const raw = (document.getElementById("ob-yearsExperience")?.value || "").trim();
  if (raw === "") return true;
  const n = Number(raw);
  return Number.isFinite(n) && n >= 0 && n <= 40 ? true : error("yearsExperience", "Enter a number from 0 to 40.");
}

// ---------- Certifications and awards (R1, R2): rows with a name, a few details and a year ----------
const credNames = (items) => (items || []).map((x) => `${x.name}${x.year ? ` (${x.year})` : ""}`).join(", ");
const yearIsOk = (raw) => raw === "" || (Number.isInteger(Number(raw)) && Number(raw) >= MIN_YEAR && Number(raw) <= nextYear());

// A list of rows. `makeRow(entry, i, onRemove)` returns { el, check, isEmpty }. The rows change `entry` directly.
function credentialList({ name, legend, addText, emptyText, blank, makeRow }) {
  const rows = h("ul", { class: "cred-rows" });
  const status = h("span", { class: "list-count", "aria-live": "polite" });
  const addBtn = h("button", { type: "button", class: "btn btn-secondary", id: `ob-${name}-add`, onclick: () => add() }, icon("plus"), addText);
  const none = h("p", { class: "muted cred-none", text: emptyText });
  let made = [];
  const items = () => state.data[name];

  function paint() {
    made = items().map((entry, i) => makeRow(entry, i, () => remove(i)));
    rows.replaceChildren(...made.map((r) => r.el));
    none.hidden = items().length > 0;
    const full = items().length >= MAX_CREDENTIALS;
    addBtn.disabled = full;
    status.textContent = full ? `Maximum ${MAX_CREDENTIALS} reached` : `${items().length} of ${MAX_CREDENTIALS}`;
  }
  function add() {
    if (items().length >= MAX_CREDENTIALS) return;
    items().push(blank());
    touched(name);
    paint();
    rows.querySelector(`#ob-${name}-${items().length - 1}-name`)?.focus();
  }
  function remove(i) {
    const label = items()[i]?.name || `${legend.toLowerCase().replace(/s$/, "")} ${i + 1}`;
    items().splice(i, 1);
    touched(name);
    paint();
    announce(`${label} removed.`);
    (rows.querySelector(`#ob-${name}-${Math.min(i, items().length - 1)}-name`) || addBtn).focus();
  }
  // Used by validate(): every row must be right. A row with nothing in it is dropped.
  state.rowChecks.push(() => {
    const ok = made.map((r) => r.check()).every(Boolean);
    if (ok) state.data[name] = items().filter((_, i) => !made[i].isEmpty());
    return ok;
  });
  paint();
  return h("fieldset", { class: "field cred-field", "data-field": name },
    h("legend", { class: "field-label" }, h("span", { class: "field-row-end" }, legend, markerFor(name), status)),
    h("p", { class: "hint cred-hint", id: `${name}-hint`, text: NAMES_HINT }),
    cvHint(name),
    none, rows,
    h("div", { class: "cred-add" }, addBtn),
    h("div", { class: "field-error", id: `${name}-error` }));
}
// A labelled cell of a row, with its own error line
function cell(cls, id, labelText, control, { optional } = {}) {
  return h("div", { class: `field ${cls}` },
    h("label", { for: id }, labelText, optional ? optionalTag() : null),
    control.el || control,
    h("div", { class: "field-error", id: `${id}-error` }));
}
function yearInput(id, entry, onTouch) {
  return h("input", { id, type: "number", class: "text-input", min: String(MIN_YEAR), max: String(nextYear()), step: "1", inputmode: "numeric",
    value: entry.year ?? "", oninput: (e) => { entry.year = yearOrNull(e.target.value); onTouch(); } });
}
const removeButton = (what, i, entry, onRemove) => h("button", { type: "button", class: "btn btn-ghost btn-sm cred-remove",
  "aria-label": `Remove ${what} ${i + 1}${entry.name ? `: ${entry.name}` : ""}`, onclick: onRemove }, icon("x"), "Remove");
const yearMessage = () => `Enter a year from ${MIN_YEAR} to ${nextYear()}.`;

function certificationRow(entry, i, onRemove) {
  const id = (k) => `ob-certifications-${i}-${k}`;
  const onTouch = () => touched("certifications");
  let auto = false;      // the issuer was set from the list of known certifications
  const issuer = h("input", { id: id("issuer"), type: "text", class: "text-input", maxlength: "120", value: entry.issuer || "", "aria-describedby": id("issuer-note"),
    oninput: () => { entry.issuer = issuer.value.trim(); onTouch(); } });
  const note = h("div", { class: "hint", id: id("issuer-note") });
  const remove = removeButton("certification", i, entry, onRemove);
  const sync = () => {
    const known = certByName.get(entry.name.toLowerCase());
    if (known) { entry.issuer = known.issuer; issuer.value = known.issuer; issuer.readOnly = true; auto = true; note.textContent = "From the list of known certifications."; }
    else { if (auto) { entry.issuer = ""; issuer.value = ""; auto = false; } issuer.readOnly = false; note.textContent = ""; }
    remove.setAttribute("aria-label", `Remove certification ${i + 1}${entry.name ? `: ${entry.name}` : ""}`);
  };
  const name = createCombobox({ id: id("name"), options: R.CERTIFICATIONS.map((c) => c.name), value: entry.name, placeholder: "Search or type the name",
    onChange: (v) => { entry.name = v.trim(); onTouch(); sync(); } });
  name.input.setAttribute("maxlength", "120");
  const year = yearInput(id("year"), entry, onTouch);
  sync();
  const el = h("li", { class: "cred-row", role: "group", "aria-label": `Certification ${i + 1}` },
    cell("cred-name", id("name"), "Name", name),
    cell("cred-year", id("year"), "Year", year, { optional: true }),
    h("div", { class: "field cred-issuer" }, h("label", { for: id("issuer") }, "Issuer", optionalTag()), issuer, note, h("div", { class: "field-error", id: `${id("issuer")}-error` })),
    remove);
  return {
    el,
    isEmpty: () => !entry.name && !entry.issuer && year.value.trim() === "",
    check() {
      let ok = true;
      const raw = year.value.trim();
      if (!entry.name && (entry.issuer || raw)) ok = rowError(name.input, "Enter the name, or remove this row.");
      if (!yearIsOk(raw)) ok = rowError(year, yearMessage());
      return ok;
    },
  };
}

function awardRow(entry, i, onRemove) {
  const id = (k) => `ob-awards-${i}-${k}`;
  const onTouch = () => touched("awards");
  const remove = removeButton("award", i, entry, onRemove);
  const name = h("input", { id: id("name"), type: "text", class: "text-input", maxlength: "120", value: entry.name || "", placeholder: "For example: Regional Hackathon Winner",
    oninput: (e) => { entry.name = e.target.value.trim(); onTouch(); remove.setAttribute("aria-label", `Remove award ${i + 1}${entry.name ? `: ${entry.name}` : ""}`); } });
  const kind = h("select", { id: id("kind"), class: "text-input select", onchange: (e) => { entry.kind = e.target.value; onTouch(); } },
    h("option", { value: "", text: "Choose a kind" }), ...R.AWARD_KINDS.map((k) => h("option", { value: k.kind, text: k.label })));
  kind.value = entry.kind || "";
  const year = yearInput(id("year"), entry, onTouch);
  const el = h("li", { class: "cred-row", role: "group", "aria-label": `Award ${i + 1}` },
    cell("cred-name", id("name"), "Name", name),
    cell("cred-year", id("year"), "Year", year, { optional: true }),
    cell("cred-kind", id("kind"), "Kind", kind),
    remove);
  return {
    el,
    isEmpty: () => !entry.name && !entry.kind && year.value.trim() === "",
    check() {
      let ok = true;
      const raw = year.value.trim();
      if (!entry.name && (entry.kind || raw)) ok = rowError(name, "Enter the name, or remove this row.");
      if (entry.name && !entry.kind) ok = rowError(kind, "Choose a kind.");
      if (!yearIsOk(raw)) ok = rowError(year, yearMessage());
      return ok;
    },
  };
}

// ---------- Steps ----------
const STEPS = {
  cv: {
    get title() { return state.edit ? "Update your CV" : "Add your CV"; },
    get sub() { return state.edit ? "We read the new CV and update your profile. You check every change before you save." : "We translate your job titles, qualifications and skills into terms Australian employers recognise."; },
    render() {
      const input = h("input", { type: "file", id: "ob-cv", class: "sr-only", accept: ".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        onchange: (e) => pickFile(e.target.files[0]) });
      const zone = h("label", { class: "dropzone", for: "ob-cv",
        ondragover: (e) => { e.preventDefault(); zone.classList.add("drag"); },
        ondragleave: () => zone.classList.remove("drag"),
        ondrop: (e) => { e.preventDefault(); zone.classList.remove("drag"); pickFile(e.dataTransfer.files[0]); } },
        h("span", { class: "icon-tile accent" }, icon("upload")),
        h("strong", {}, "Drag and drop your CV, or ", h("span", { class: "legal-link", text: "browse" })),
        h("span", { class: "hint", text: "PDF or DOCX, up to 10 MB" }));
      const fileRow = h("div", { id: "ob-file" });
      const wrap = h("div", { class: "field", "data-field": "cv" }, input, zone, fileRow, h("div", { class: "field-error", id: "cv-error", role: "alert" }));
      const note = h("p", { class: "privacy-note" }, icon("shield"),
        h("span", { text: "Employers never see your CV or your personal details. They see only your translated skills and experience, under an alias — not your name, contact details, photo or nationality." }));
      setTimeout(renderFile);
      return [wrap, note];
    },
    buttons: () => [
      state.edit ? null : h("button", { type: "button", class: "btn btn-ghost", text: "Skip for now", onclick: () => { state.fromCv = false; go("skip", 1); } }),
      h("button", { type: "submit", class: "btn btn-primary", id: "ob-cv-next", disabled: !state.file, text: "Upload and continue" }),
    ].filter(Boolean),
    validate: () => (state.file ? true : error("cv", "Choose a PDF or DOCX file.")),
    // Upload at once (POST /cv). The CV record is saved even if the user closes the dialog later.
    async next() {
      const btns = foot.querySelectorAll("button");
      btns.forEach((b) => (b.disabled = true));
      try {
        const res = await api.cv.upload(state.file);
        state.data.cv = res.cv;
        state.parseId = res.parse.id;
        state.parseError = "";
        if (state.edit) goPath(EDIT_PATHS.cv, 1);
        else go("cv", 1);
      } catch (err) {
        btns.forEach((b) => (b.disabled = false));
        renderFile();
        error("cv", err.fields?.file || err.message || "We couldn't upload this file. Try again.");
      }
    },
  },
  reading: {
    title: "Reading your CV",
    sub: "We look for your roles, skills and qualifications. This takes up to 15 seconds.",
    render() {
      if (state.parseError) {
        return [h("div", { class: "empty", role: "alert" },
          h("div", { class: "icon-tile accent" }, icon("alert")),
          h("p", { text: state.parseError }),
          h("p", { class: "hint", text: "Nothing is lost. You can try a different file, or enter your details yourself." }))];
      }
      setTimeout(poll);
      return [h("div", { class: "reading", role: "status" },
        h("div", { class: "progress-indeterminate", "aria-hidden": "true" }, h("span")),
        h("p", { text: "Reading your CV…" }))];
    },
    buttons: () => (state.parseError ? (state.edit ? [
      h("button", { type: "button", class: "btn btn-secondary", text: "Try a different file", onclick: () => { state.file = null; goPath(EDIT_PATHS.cv, 0); } }),
      h("button", { type: "button", class: "btn btn-primary", text: "Keep my current profile", onclick: () => goPath(EDIT_PATHS.review, 0) }),
    ] : [
      h("button", { type: "button", class: "btn btn-secondary", text: "Try a different file", onclick: () => { state.file = null; go("skip", 0); } }),
      h("button", { type: "button", class: "btn btn-primary", text: "Enter details myself", onclick: () => { state.fromCv = false; go("skip", 1); } }),
    ]) : []),
    validate: () => false,
  },
  education: {
    title: "Your education",
    sub: "Tell us about your qualifications. We show employers the Australian (AQF) level.",
    render: () => [demoBanner(), checkNote(), foundSummary(),
      multiCombo("qualification", "Qualifications", R.QUALIFICATIONS,
        { placeholder: "Search or type, e.g. Bachelor", hint: "Add all your qualifications, highest first." }),
      multiCombo("fieldOfStudy", "Fields of study", R.FIELDS_OF_STUDY,
        { placeholder: "Search or type, e.g. Computer science", hint: "Add one or more fields." }),
      multiCombo("studyCountry", "Countries where you studied", R.COUNTRIES,
        { placeholder: "Search or type a country", optional: true, max: 3, hint: "Used only to find the Australian equivalent (AQF level). It is never used to rank you." }),
    ],
    validate: () => [atLeast("qualification", 1, "Add at least one qualification."), atLeast("fieldOfStudy", 1, "Add at least one field of study.")].every(Boolean),
  },
  experience: {
    title: "Your experience",
    sub: "Tell us about the roles you have had, your level and where you worked.",
    render() {
      const yearsBox = combo("years", R.YEARS, "Choose a range", { allowCustom: false });
      return [demoBanner(),
        multiCombo("currentRole", "Current and past roles", R.ROLES,
          { placeholder: "Search or type a job title", cv: true, hint: "Start with your current or most recent role. Use the titles from your country — we translate them for you." }),
        multiCombo("industry", "Domains", R.DOMAINS,
          { placeholder: "Search or choose a domain", max: 3, custom: false, notFoundText: "Choose a domain from the list.", hint: "Add the domains you have worked in." }),
        levelField(),
        exactYearsField(yearsBox),
        field("years", "Total years of work experience", yearsBox),
      ];
    },
    validate: () => [atLeast("currentRole", 1, "Add at least one role."), atLeast("industry", 1, "Add at least one domain."),
      exactYearsOk(), inList("years", R.YEARS, "Choose a range from the list.")].every(Boolean),
  },
  skills: {
    title: "Your skills",
    sub: "Add the skills you use at work. Include tools, methods and languages. Use the words from your country — we translate them.",
    render: () => [demoBanner(),
      multiCombo("skills", "Skills", R.SKILLS, {
        placeholder: "Search or type a skill", max: 15,
        hint: "Add at least 3. Choose from the list, or type your own and press Enter.",
        // Suggestions come from all the domains the user chose (from all three domains if none is chosen)
        suggestions: () => {
          const doms = toList(state.data.industry).filter((i) => R.SKILL_SUGGESTIONS[i]);
          return [...new Set((doms.length ? doms : R.DOMAINS).flatMap((i) => R.SKILL_SUGGESTIONS[i]))].slice(0, 10);
        },
      }),
    ],
    validate: () => atLeast("skills", 3, "Add at least 3 skills."),
  },
  credentials: {
    title: "Certifications and awards",
    sub: "Add the certifications and awards that you have. This step is optional. You can skip it.",
    render: () => [
      demoBanner(),
      credentialList({
        name: "certifications", legend: "Certifications", addText: "Add a certification", emptyText: "No certifications added.",
        blank: () => ({ name: "", issuer: "", year: null }), makeRow: certificationRow,
      }),
      credentialList({
        name: "awards", legend: "Awards", addText: "Add an award", emptyText: "No awards added.",
        blank: () => ({ name: "", kind: "", year: null }), makeRow: awardRow,
      }),
    ],
    buttons: () => [h("button", { type: "submit", class: "btn btn-primary", text: "Continue" })],
    validate: () => state.rowChecks.map((c) => c()).every(Boolean),
  },
  translation: {
    title: "Your translated profile",
    sub: "This is how Australian employers will read your experience. Accept the skills that are right. Edit or remove the others. Only accepted skills are shared.",
    render() {
      const wrap = h("div", { class: "field", "data-field": "translation" },
        h("div", { class: "reading", role: "status" }, h("div", { class: "progress-indeterminate", "aria-hidden": "true" }, h("span")), h("p", { text: "Translating your experience…" })),
        h("div", { class: "field-error", id: "translation-error", role: "alert" }));
      loadTranslation(wrap);
      return [wrap];
    },
    validate: () => ((state.data.translation || []).some(SHARED) ? true : (alertBox("Accept at least one skill, so employers can find you."), false)),
  },
  goals: {
    title: "What are you looking for?",
    sub: "We use this to recommend jobs. You can change it at any time.",
    render: () => [
      multiCombo("targetRole", "Target roles", R.ROLES,
        { placeholder: "Search or type a role you want", max: 3, cv: true, hint: "Add up to 3 roles you want to apply for." }),
      choices("targetIndustries", "Target domains", R.DOMAINS, { optional: true, hint: "Choose up to 3.", max: 3 }),
      choices("locations", "Preferred locations", R.LOCATIONS),
      choices("workTypes", "Work type", R.WORK_TYPES),
    ],
    validate: () => [atLeast("targetRole", 1, "Add at least one role you want."), atLeast("locations", 1, "Choose at least one location."), atLeast("workTypes", 1, "Choose at least one work type.")].every(Boolean),
  },
  review: {
    // First time: "Check your answers". A done profile: "Your profile" — the start page of every edit.
    get title() { return state.edit ? "Your profile" : "Check your answers"; },
    get sub() { return state.edit ? "Edit any part of your profile. Then save your changes." : "Make sure everything is correct. Then we find jobs for you."; },
    render() {
      const d = state.data;
      const list = (a) => (toList(a).length ? toList(a).join(", ") : "—");
      const shared = (d.translation || []).filter(SHARED);
      // [step, label, value, field, required]
      const rows = [
        ["cv", "CV", d.cv ? d.cv.name : "No CV", "cv", false],
        ["education", "Qualifications", list(d.qualification), "qualification", true],
        ["education", "Fields of study", list(d.fieldOfStudy), "fieldOfStudy", true],
        ["education", "Countries", list(d.studyCountry), "studyCountry", false],
        ["experience", "Roles", list(d.currentRole), "currentRole", true],
        ["experience", "Domains", list(d.industry), "industry", true],
        ["experience", "Level", d.level || "—", "level", false],
        ["experience", "Exact years", d.yearsExperience != null ? experienceOf(d) : "—", "yearsExperience", false],
        ["experience", "Experience", d.years || "—", "years", true],
        ["skills", "Skills", list(d.skills), "skills", true],
        ["credentials", "Certifications", credNames(d.certifications) || "—", "certifications", false],
        ["credentials", "Awards", credNames(d.awards) || "—", "awards", false],
        ["translation", "Shared skills", shared.length ? `${shared.length}: ${shared.map((s) => s.mapped).join(", ")}` : "—", "translation", true],
        ["goals", "Target roles", list(d.targetRole), "targetRole", true],
        ["goals", "Target domains", list(d.targetIndustries), "targetIndustries", false],
        ["goals", "Locations", list(d.locations), "locations", true],
        ["goals", "Work type", list(d.workTypes), "workTypes", true],
      ];
      return [h("dl", { class: "review-list" }, rows.map(([step, k, v, name, required]) => {
        const missing = required && !filled(name);
        const marker = missing ? h("span", { class: "chip chip-yellow", text: "Missing" })
          : state.detected.has(name) ? h("span", { class: "chip chip-ai", title: "The AI found this in your CV. Check it." }, icon("check"), "From your CV") : null;
        return h("div", { class: `review-row${missing ? " is-missing" : ""}` },
          h("dt", {}, k, marker ? h("span", { class: "field-markers" }, marker) : null), h("dd", { text: v }),
          h("button", { type: "button", class: "legal-link link-btn", "aria-label": `${step === "cv" ? "Change" : "Edit"} ${k}`, text: step === "cv" ? "Change" : "Edit", onclick: () => jump(step) }));
      }))];
    },
    buttons: () => [h("button", { type: "submit", class: "btn btn-primary", text: state.edit ? "Save changes" : "Save and see jobs" })],
    // Every required answer must be there before the save (an updated CV can leave gaps)
    validate: () => (REQUIRED.every(filled) ? true : (alertBox("Some answers are missing. Edit the rows marked “Missing”."), false)),
    next: finish,
  },
};

// ---------- CV reading (poll GET /cv/parse/:id) ----------
async function poll() {
  const myRun = state.run;
  const started = Date.now();
  while (state.run === myRun && state.path[state.index] === "reading") {
    let res;
    try { res = await api.cv.parseStatus(state.parseId); }
    catch (err) { res = { status: "failed", error: err.message }; }
    if (state.run !== myRun || state.path[state.index] !== "reading") return;
    if (res.status === "done") {
      const r = res.result;
      // Replace the fields with what the AI found. Keep the goals, which a CV does not have.
      // A field that the CV does not show stays empty and is flagged "Missing" (Feature 2 AC6).
      // When a done profile gets a new CV, a field that the CV does not show keeps the old answer.
      Object.assign(state.data, r.fields);
      if (!state.edit) for (const k of r.missing || []) state.data[k] = k === "years" ? "" : [];
      // V2: the level, years, certifications and awards. `found` tells which of them the CV showed (R1).
      state.found = r.found && typeof r.found === "object" ? r.found : {};
      state.cvLevels = new Map((Array.isArray(r.skills) ? r.skills : []).filter((x) => x && x.name && Number.isInteger(x.level)).map((x) => [String(x.name).toLowerCase(), x.level]));
      normalizeProfile(state.data);
      state.detected = new Set(r.detected);
      state.missing = new Set(r.missing);
      // The V2 backend names the domain of the CV (one of the 3 domains). `fields.industry` holds up to 2 domains (the strongest first) and `result.domain`
      // is the first of them. The form starts with that one domain. The talent can add another. (The mock backend sends no `domain`.)
      if (R.DOMAINS.includes(r.domain)) {
        state.data.industry = [r.domain];
        state.detected.add("industry");
        state.missing.delete("industry");
      }
      state.data.evidence = r.evidence || [];
      state.sampleLabel = r.sampleLabel || "";
      state.fromCv = true;
      state.data.translation = state.data.translation || [];
      announce("Your CV is read. Check the fields we filled.");
      state.index += 1;
      return render();
    }
    if (res.status === "failed" || Date.now() - started > POLL_LIMIT_MS) {
      state.parseError = res.error || "Reading your CV took too long. Try again, or enter your details yourself.";
      return render();
    }
    await new Promise((r) => setTimeout(r, POLL_MS));
  }
}

// ---------- Translation (POST /profile/translate) ----------
async function loadTranslation(wrap) {
  const myRun = state.run;
  const { cv, evidence, ...profile } = state.data;
  let res;
  try {
    res = await api.profile.translate({ profile, evidence: evidence || [] });
  } catch (err) {
    if (state.run !== myRun) return;
    wrap.querySelector(".reading").replaceWith(h("div", { class: "empty", role: "alert" }, h("p", { text: err.message || "We couldn't translate your experience. Try again." })));
    return;
  }
  if (state.run !== myRun) return;
  state.data.translation = res.skills;
  state.gaps = res.gaps || [];
  // The CV can show a level for a skill (R1). It is the start value when the server set none, or only its default (the level of the
  // evidence, rule F8). A level that the talent changed in this dialog stays. The talent can change it at any time.
  for (const s of state.data.translation) {
    if (s.source !== "skill" || state.levelTouched.has(s.id)) continue;
    const lv = state.cvLevels.get(String(s.original).toLowerCase()) ?? state.cvLevels.get(String(s.mapped).toLowerCase());
    if (lv && (!Number.isInteger(s.level) || s.level === evidenceLevel(s.evidence))) { s.level = lv; levelFromCv.add(s); }
  }

  const listEl = h("ul", { class: "tr-list", "aria-label": "Translated skills" });
  const removedEl = h("div", { class: "tr-removed" });
  const previewSlot = h("div");
  const counter = h("p", { class: "tr-count", role: "status" });
  const acceptAll = h("button", { type: "button", class: "btn btn-secondary btn-sm", onclick: () => {
    state.data.translation.forEach((s) => { if (s.status === "suggested") s.status = "accepted"; });
    repaint();
    announce("All suggested skills accepted.");
  } }, icon("check"), "Accept all");

  function repaint() {
    const all = state.data.translation;
    const visible = all.filter((s) => s.status !== "removed");
    const removed = all.filter((s) => s.status === "removed");
    listEl.replaceChildren(...visible.map((s) => translationCard(s, repaint, () => previewSlot.replaceChildren(previewPanel()))));
    removedEl.replaceChildren(...(removed.length ? [h("p", { class: "hint", text: "Removed (not shared):" }),
      ...removed.map((s) => h("button", { type: "button", class: "choice", "aria-label": `Undo remove ${s.mapped}`,
        onclick: () => { s.status = "suggested"; repaint(); } }, icon("plus"), s.mapped))] : []));
    const n = all.filter(SHARED).length;
    counter.textContent = `${n} of ${visible.length} skills accepted.`;
    acceptAll.disabled = !visible.some((s) => s.status === "suggested");
    previewSlot.replaceChildren(previewPanel());
    body.querySelector(".form-alert")?.remove();
  }

  const content = [
    h("div", { class: "tr-head" }, counter, acceptAll),
    state.data.translation.length ? listEl : h("p", { class: "muted", text: "We found no skills to translate. Go back and add your roles and skills." }),
    removedEl,
    state.gaps.length ? h("div", { class: "tr-gaps" },
      h("h3", { text: "Things Australian employers may ask about" }),
      h("ul", { class: "why" }, state.gaps.map((g) => h("li", { class: "gap" }, icon("alert"), g)))) : null,
    previewSlot,
  ];
  wrap.querySelector(".reading").replaceWith(...content.filter(Boolean));
  repaint();
}

// ---------- File handling ----------
function pickFile(file) {
  clearErrors();
  if (!file) return;
  const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
  if (!CV_TYPES.includes(ext)) { state.file = null; renderFile(); return error("cv", "Use a PDF or DOCX file."); }
  if (file.size > MAX_CV_BYTES) { state.file = null; renderFile(); return error("cv", "The file is larger than 10 MB. Use a smaller file."); }
  state.file = file;
  renderFile();
}
function renderFile() {
  const row = document.getElementById("ob-file");
  const next = document.getElementById("ob-cv-next");
  if (next) next.disabled = !state.file;
  if (!row) return;
  const f = state.file;
  row.replaceChildren(...(f ? [h("div", { class: "file-chip" }, icon("file"),
    h("span", { class: "file-name", text: f.name }), h("span", { class: "hint", text: `${Math.max(1, Math.round(f.size / 1024))} KB` }),
    h("button", { type: "button", class: "btn btn-ghost btn-icon", "aria-label": `Remove ${f.name}`, onclick: () => { state.file = null; document.getElementById("ob-cv").value = ""; renderFile(); } }, icon("x")))] : []));
}

// ---------- Navigation ----------
function go(pathName, index) {
  state.path = PATHS[pathName];
  state.index = index;
  render();
}
// Short paths for a done profile: each edit starts and ends on "Your profile" (review).
// A change to roles, skills or education runs the translation again, so the shared skills stay correct.
const EDIT_PATHS = {
  review: ["review"],
  cv: ["cv", "reading", "translation", "review"],
  education: ["education", "translation", "review"],
  experience: ["experience", "translation", "review"],
  skills: ["skills", "translation", "review"],
  credentials: ["credentials", "review"],
  translation: ["translation", "review"],
  goals: ["goals", "review"],
};
function goPath(path, index) {
  state.path = path;
  state.index = index;
  render();
}
function jump(step) {
  if (state.edit) return goPath(EDIT_PATHS[step], 0);
  state.index = state.path.indexOf(step);
  render();
}
function render() {
  state.run += 1; // a newer render cancels pending polls and requests
  const key = state.path[state.index];
  const step = STEPS[key];
  const n = state.path.length;
  stepLabel.textContent = state.edit ? (n > 1 ? `Edit profile · Step ${state.index + 1} of ${n}` : "Edit profile") : `Step ${state.index + 1} of ${n}`;
  bar.style.width = `${((state.index + 1) / n) * 100}%`;
  const heading = h("h2", { id: "ob-title", tabindex: "-1", text: step.title });
  state.flush = [];
  state.rowChecks = [];
  body.replaceChildren(heading, h("p", { class: "modal-sub", text: step.sub }), ...step.render().filter(Boolean));
  // No "Back" from the reading step while it reads, and none to the reading step.
  // In edit mode the first step goes back to "Your profile".
  const prev = state.path[state.index - 1];
  const back = state.index > 0 && key !== "reading" && prev !== "reading"
    ? h("button", { type: "button", class: "btn btn-ghost", onclick: () => { state.index -= 1; render(); } }, icon("chevron-left"), "Back")
    : state.edit && state.index === 0 && key !== "review"
      ? h("button", { type: "button", class: "btn btn-ghost", onclick: () => goPath(EDIT_PATHS.review, 0) }, icon("chevron-left"), "Back to profile")
      : null;
  const buttons = step.buttons ? step.buttons() : [h("button", { type: "submit", class: "btn btn-primary", text: "Continue" })];
  foot.replaceChildren(h("div", {}, back), h("div", { class: "modal-actions" }, buttons));
  heading.focus();
}
function submit(e) {
  e.preventDefault();
  clearErrors();
  state.flush.forEach((f) => f());
  const step = STEPS[state.path[state.index]];
  if (!step.validate()) return focusFirstError();
  if (step.next) return step.next();
  state.index += 1;
  render();
}
// Save with PATCH /me. On an error, show it in the dialog and keep the answers.
async function save(patch) {
  const buttons = foot.querySelectorAll("button");
  buttons.forEach((b) => (b.disabled = true));
  try {
    await api.me.update(patch);
    return true;
  } catch (err) {
    alertBox(err.message || "We couldn't save your answers. Try again.");
    return false;
  } finally {
    buttons.forEach((b) => (b.disabled = false));
    renderFile();
  }
}

// The profile keeps the CV evidence lines (private to the candidate) so the translation can run again
const toPatch = (onboarding) => {
  const { cv, ...profile } = state.data;
  return { profile, cv: cv || null, onboarding };
};
async function finish() {
  if (!(await save(toPatch("done")))) return;
  state.finished = true;
  dialog.close();
}
// Close before the end: keep the answers as a draft for a new profile.
// For a completed profile, discard the unsaved edits.
async function onClose() {
  state.run += 1;
  if (!state.finished && state.onboarding !== "done") {
    try { await api.me.update(toPatch("dismissed")); } catch { /* keep going */ }
  }
  onDone && onDone();
}

// ---------- Public ----------
let bound = false;
function bind() {
  if (bound) return;
  bound = true;
  dialog = document.getElementById("onboarding");
  body = document.getElementById("obBody");
  foot = document.getElementById("obFoot");
  stepLabel = document.getElementById("obStep");
  bar = document.getElementById("obBar");
  document.getElementById("obForm").addEventListener("submit", submit);
  document.getElementById("obClose").addEventListener("click", () => dialog.close());
  dialog.addEventListener("close", onClose); // Also runs when the user presses Esc
}

/**
 * Open the dialog for the signed-in candidate.
 * @param {object} opts { user, start: "cv" | "questions" | "review" | "translation" | "goals", done }
 * A done profile opens in edit mode (short paths that end on "Your profile").
 * A new profile opens the full step-by-step flow.
 */
export function openOnboarding({ user, start = "cv", done } = {}) {
  bind();
  onDone = done;
  state = {
    data: { ...(user.profile || {}), cv: user.cv || undefined }, onboarding: user.onboarding, alias: user.alias,
    edit: user.onboarding === "done",
    file: null, path: PATHS.skip, index: 0, flush: [], rowChecks: [], run: 0,
    detected: new Set(), missing: new Set(), found: {}, cvLevels: new Map(), levelTouched: new Set(), fromCv: false, sampleLabel: "", parseId: null, parseError: "", gaps: [],
  };
  normalizeProfile(state.data);
  const at = (step) => PATHS.skip.indexOf(step);
  if (state.edit) goPath(EDIT_PATHS[start] || EDIT_PATHS.review, 0); // "questions" → "Your profile"
  else if (start === "questions" || start === "review") go("skip", at("education"));
  else if (start === "translation") go("skip", at("translation"));
  else if (start === "goals") go("skip", at("goals"));
  else go("skip", 0);
  if (!dialog.open) dialog.showModal();
}

// Close the dialog without saving (for example, when the user leaves the page)
export function closeOnboarding() {
  if (dialog?.open) { state.finished = true; onDone = null; dialog.close(); }
}
