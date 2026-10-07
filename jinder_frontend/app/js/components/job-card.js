// Job card (Home, Jobs, Bookmarks, Similar jobs), bookmark toggle, skip and report actions (Feature 3).
// V2 adds: level, experience and work mode on the card (R2), a "Compare" check box (the compare basket, R9),
// and the helper for lists with a pager and a sort (R5, R6).
// All job data is internal Jinder data: every link opens a Jinder screen, never another site.
import { h, iconHtml as icon, esc, formatDate, announce } from "../core/dom.js";
import { api } from "../api/index.js";
import { CONFIG } from "../config.js";
import { compareStore, COMPARE_EVENT } from "../core/compare-store.js";
import { COMPARE_MAX, PAGE_SIZES } from "../data/levels.js";
import { pagerHtml, bindPager, loadPageSize } from "./pagination.js";
import { sortSelectHtml, bindSort } from "./sort-select.js";
import { coverageText } from "./status.js";
import { openModal, radioGroup, textArea } from "./modal.js";

const MAX_GAP_CHIPS = 4;

export const jobHref = (id) => `#/jobs/${encodeURIComponent(id)}`;

export function bookmarkButton(job, { withText = false } = {}) {
  const saved = !!job.bookmarked;
  const label = saved ? `Remove ${job.title} from bookmarks` : `Save ${job.title} to bookmarks`;
  return `<button type="button" class="btn ${withText ? "btn-secondary" : "btn-ghost btn-icon"} bookmark-btn" data-bookmark="${esc(job.id)}" data-title="${esc(job.title)}" aria-pressed="${saved}" aria-label="${esc(label)}" title="${saved ? "Saved" : "Save"}">${icon("bookmark")}${withText ? `<span data-bookmark-text>${saved ? "Saved" : "Save"}</span>` : ""}</button>`;
}

export function datesHtml(job) {
  if (job.status === "closed") return `<span class="chip chip-rose">Closed</span>${job.closesAt ? `<span class="hint">Closed ${esc(formatDate(job.closesAt))}</span>` : ""}`;
  return [job.postedAt && `Posted ${formatDate(job.postedAt)}`, job.closesAt && `Closes ${formatDate(job.closesAt)}`]
    .filter(Boolean).map((t) => `<span class="hint">${esc(t)}</span>`).join("");
}

export function gapChipsHtml(gaps) {
  if (!gaps.length) return `<span class="chip chip-green">No skill gaps found</span>`;
  const shown = gaps.slice(0, MAX_GAP_CHIPS).map((g) => `<span class="chip chip-yellow">${esc(g)}</span>`).join("");
  const more = gaps.length > MAX_GAP_CHIPS ? `<span class="hint">+${gaps.length - MAX_GAP_CHIPS} more</span>` : "";
  return shown + more;
}

// Coverage summary: the share of the job's skills that the candidate has (partial = half)
export function coverageHtml(m) {
  const has = m && m.coverage != null;
  const c = has ? Number(m.coverage) : 0;
  return `
    <span class="match-score">${has ? `${c}%` : "—"}</span>
    <span class="hint">skills covered</span>
    <div class="meter" role="img" aria-label="${has ? `${c}% of the skills covered` : "No skills listed"}"><span data-w="${c}"></span></div>
    <span class="hint coverage-text">${esc(coverageText(m))}</span>`;
}

// The fit score of the API (one decimal). Jobs seldom have the same number.
export const fitScoreHtml = (m) => (m && m.score != null ? `<span class="fit-score" title="Your skill match mixed with the feed score of Formula 5">Fit score <strong>${Number(m.score).toFixed(1)}</strong></span>` : "");

// ---------- Level, experience, work mode (R2) ----------
const isNum = (v) => v != null && v !== "" && Number.isFinite(Number(v));
const yearsText = (v) => String(Math.round(Number(v) * 10) / 10);

/** "5–9 years", "5+ years", "Up to 9 years", "5 years" or "" when the job has no experience data. */
export function experienceText(min, max) {
  const lo = isNum(min), hi = isNum(max);
  if (lo && hi) {
    const a = yearsText(min), b = yearsText(max);
    if (Number(max) < Number(min)) return `${a}+ years`;
    return a === b ? `${a} ${Number(min) === 1 ? "year" : "years"}` : `${a}–${b} years`;
  }
  if (lo) return `${yearsText(min)}+ years`;
  if (hi) return `Up to ${yearsText(max)} years`;
  return "";
}

/** The chips Level, Experience and Work mode. A fact that the job does not have (old data) is left out. Returns "" if there is none. */
export function jobFactsHtml(job) {
  const items = [];
  if (job.level) items.push(["Level", job.level, "chip-pink"]);
  const exp = experienceText(job.minYears, job.maxYears);
  if (exp) items.push(["Experience", exp, "chip-neutral"]);
  if (job.workMode) items.push(["Work mode", job.workMode, "chip-blue"]);
  if (!items.length) return "";
  return `<ul class="job-facts" aria-label="Level, experience and work mode">${items.map(([k, v, c]) => `<li><span class="chip ${c}" title="${k}"><span class="sr-only">${k}: </span>${esc(v)}</span></li>`).join("")}</ul>`;
}

// ---------- Compare basket (R8, R9): the check box on a card ----------
const COMPARE_FULL = `You can compare up to ${COMPARE_MAX} jobs.`;
export const compareAvailable = () => CONFIG.API_MODE === "http";

export function compareCheckHtml(job) {
  const on = compareStore.has("job", job.id);
  return `<label class="check check-sm compare-pick" title="Add to compare"><input type="checkbox" data-compare-job="${esc(job.id)}" data-title="${esc(job.title)}"${on ? " checked" : ""}><span>Compare<span class="sr-only"> ${esc(job.title)}</span></span></label><span class="hint compare-note" data-compare-note></span>`;
}

/** Add a job to the basket, or tell why not. Returns true when the job is in the basket. */
export function addJobToCompare(job) {
  if (compareStore.add("job", { id: job.id, title: job.title })) return true;
  announce(COMPARE_FULL);
  return false;
}

/**
 * One handler for the "Compare" check boxes inside `root`. A tick adds the job to the basket (the 6th is refused: the box
 * is cleared and a short text says why). A change of the basket from anywhere (the bar, another tab) updates the boxes.
 */
export function bindCompare(root) {
  if (!root || root.dataset.compareBound === "1") return;
  root.dataset.compareBound = "1";
  const sync = () => root.querySelectorAll("[data-compare-job]").forEach((c) => { c.checked = compareStore.has("job", c.dataset.compareJob); });
  root.addEventListener("change", (e) => {
    const box = e.target.closest("[data-compare-job]");
    if (!box || !root.contains(box)) return;
    const id = box.dataset.compareJob;
    const note = box.closest(".card-actions")?.querySelector("[data-compare-note]");
    if (note) note.textContent = "";
    if (box.checked) {
      if (!compareStore.add("job", { id, title: box.dataset.title || id })) {
        box.checked = false;
        if (note) note.textContent = COMPARE_FULL;
        announce(COMPARE_FULL);
      }
    } else {
      compareStore.remove("job", id);
    }
  });
  const onBasket = () => { if (!root.isConnected) return window.removeEventListener(COMPARE_EVENT, onBasket); sync(); };
  window.addEventListener(COMPARE_EVENT, onBasket);
}

/** @param {object} job JobCard from the API. @param {object} opts { compact, compare } */
export function jobCardHtml(job, { compact = false, compare = compareAvailable() } = {}) {
  const m = job.match || { coverage: null, skills: [], reasons: [], gaps: [], notes: [] };
  return `
    <li class="job-card${compact ? " job-card-compact" : ""}" data-card="${esc(job.id)}">
      <div class="job-main">
        <h3><a class="job-title-link" href="${jobHref(job.id)}">${esc(job.title)}</a></h3>
        <p class="job-meta">${esc(job.company)} · ${icon("map-pin")}${esc(job.area || job.location)} · ${esc(job.type)}${job.salary ? ` · ${esc(job.salary)}` : ""}</p>
        ${jobFactsHtml(job)}
        ${!compact && job.summary ? `<p class="job-summary">${esc(job.summary)}</p>` : ""}
        <div class="job-tags">
          ${job.applicationId ? `<a class="chip chip-green chip-link" href="#/applications/${esc(job.applicationId)}">${icon("check")}Applied · Track</a>` : ""}
          ${job.anzsco ? `<span class="chip chip-blue" title="Australian occupation code">ANZSCO ${esc(job.anzsco)}${job.occupation ? ` · ${esc(job.occupation)}` : ""}</span>` : ""}
          ${datesHtml(job)}
          ${job.similarity ? `<span class="chip chip-neutral similar-chip" title="How close this job is to the one you are reading">${esc(job.similarity.tier)} · ${Math.round(job.similarity.index)}% alike</span>` : ""}
        </div>
        <div class="skill-gap-row"><span class="skill-gap-label">Skill gaps</span>${gapChipsHtml(m.gaps || [])}</div>
        ${compact ? "" : `<ul class="why">
          ${(m.reasons || []).map((r) => `<li>${icon("check")}${esc(r)}</li>`).join("")}
          ${(m.notes || []).map((n) => `<li class="note">${icon("alert")}${esc(n)}</li>`).join("")}
        </ul>`}
      </div>
      <div class="job-score">
        <div class="job-score-top">${bookmarkButton(job)}</div>
        ${coverageHtml(m)}
        ${fitScoreHtml(m)}
      </div>
      <div class="card-foot">
        <div class="card-actions">${compare ? compareCheckHtml(job) : ""}${compact ? "" : `
          <button type="button" class="btn btn-ghost btn-sm" data-skip="${esc(job.id)}" data-title="${esc(job.title)}">${icon("eye-off-small")}Not for me</button>
          <button type="button" class="btn btn-ghost btn-sm" data-report="${esc(job.id)}" data-title="${esc(job.title)}">${icon("flag")}Report</button>`}
        </div>
        <a class="btn btn-secondary btn-sm job-link" href="${jobHref(job.id)}">Job detail<span class="sr-only"> for ${esc(job.title)}</span>${icon("arrow")}</a>
      </div>
    </li>`;
}

// Set meter widths with CSSOM (inline style attributes are blocked by the CSP)
export function paintMeters(root) {
  root.querySelectorAll("[data-w]").forEach((el) => (el.style.width = `${Math.max(0, Math.min(100, Number(el.dataset.w) || 0))}%`));
}

/**
 * Toggle bookmarks with event delegation. Optimistic: the button changes at once, and goes back on an error.
 * @param {Element} root
 * @param {Function} [onChange] (jobId, bookmarked) => void
 */
export function bindBookmarks(root, onChange) {
  root.addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-bookmark]");
    if (!btn || !root.contains(btn) || btn.disabled) return;
    const id = btn.dataset.bookmark;
    const title = btn.dataset.title;
    const next = btn.getAttribute("aria-pressed") !== "true";
    const set = (saved) => {
      root.querySelectorAll(`[data-bookmark="${CSS.escape(id)}"]`).forEach((b) => {
        b.setAttribute("aria-pressed", String(saved));
        b.setAttribute("aria-label", saved ? `Remove ${title} from bookmarks` : `Save ${title} to bookmarks`);
        b.title = saved ? "Saved" : "Save";
        const t = b.querySelector("[data-bookmark-text]");
        if (t) t.textContent = saved ? "Saved" : "Save";
      });
    };
    set(next);
    btn.disabled = true;
    try {
      await (next ? api.bookmarks.add(id) : api.bookmarks.remove(id));
      announce(next ? `${title} saved to bookmarks.` : `${title} removed from bookmarks.`);
      onChange && onChange(id, next);
    } catch (err) {
      set(!next);
      announce(err.message || "We couldn't update your bookmarks. Try again.");
    } finally {
      btn.disabled = false;
    }
  });
}

// ---------- Report (Feature 3 AC6) ----------
export function openReport(targetType, targetId, title) {
  const reasons = targetType === "job"
    ? [["not_relevant", "It does not match my skills or goals"], ["wrong_location_or_type", "Wrong location or work type"], ["misleading", "The job looks wrong or misleading"], ["other", "Other"]]
    : [["not_relevant", "Not relevant to my jobs"], ["misleading", "The profile looks wrong or misleading"], ["other", "Other"]];
  openModal({
    title: `Report ${targetType === "job" ? "this job" : "this profile"}`,
    intro: `${title}. Reports help us improve the recommendations. ${targetType === "job" ? "The employer does not see who reported." : "They do not see who reported."}`,
    content: [radioGroup("reason", "Why is this a wrong recommendation?", reasons), textArea("details", "More details (optional)", { max: 500 })],
    submitText: "Send report",
    async onSubmit(form) {
      const reason = form.querySelector("input[name=reason]:checked")?.value;
      if (!reason) throw new Error("Choose a reason.");
      await api.reports.create({ targetType, targetId, reason, details: form.details.value });
      announce("Thank you. Your report is sent.");
      return true;
    },
  });
}

/**
 * Skip and report with event delegation. Skip hides the card and shows "Undo" (Feature 3 AC4).
 * @param {Element} root
 */
export function bindJobActions(root) {
  root.addEventListener("click", async (e) => {
    const rep = e.target.closest("[data-report]");
    if (rep && root.contains(rep)) return openReport("job", rep.dataset.report, rep.dataset.title);
    const sk = e.target.closest("[data-skip]");
    if (!sk || !root.contains(sk)) return;
    const id = sk.dataset.skip;
    const title = sk.dataset.title;
    const cardEl = sk.closest(".job-card");
    sk.disabled = true;
    try {
      await api.jobs.skip(id);
    } catch (err) {
      sk.disabled = false;
      return announce(err.message || "We couldn't hide this job. Try again.");
    }
    const undo = h("button", { type: "button", class: "text-link link-btn", text: "Undo" });
    const placeholder = h("li", { class: "job-card job-card-hidden", role: "status" }, h("span", { text: `${title} is hidden. We show fewer jobs like this.` }), undo);
    cardEl.replaceWith(placeholder);
    announce(`${title} is hidden.`);
    undo.addEventListener("click", async () => {
      undo.disabled = true;
      try { await api.jobs.unskip(id); placeholder.replaceWith(cardEl); sk.disabled = false; cardEl.querySelector("[data-skip]")?.focus(); announce(`${title} is back.`); }
      catch (err) { undo.disabled = false; announce(err.message || "We couldn't undo. Try again."); }
    });
    undo.focus();
  });
}

// =====================================================================
// Lists with a pager and a sort (R5, R6)
// =====================================================================
/** Read page, pageSize and sort from the route query (#/jobs?page=2&pageSize=20&sort=newest). A bad value gives the default. */
export function readListQuery(query = {}, key, sortValues) {
  const page = Math.max(1, Math.floor(Number(query.page)) || 1);
  const size = Number(query.pageSize);
  return {
    page,
    pageSize: PAGE_SIZES.includes(size) ? size : loadPageSize(key),
    sort: sortValues.includes(query.sort) ? query.sort : sortValues[0],
  };
}

/** Write page, pageSize and sort into the address (the other query values stay). A new history entry makes the Back button work. */
function writeListUrl(state, push) {
  const [path, qs = ""] = location.hash.slice(1).split("?");
  const params = new URLSearchParams(qs);
  params.set("page", String(state.page));
  params.set("pageSize", String(state.pageSize));
  params.set("sort", state.sort);
  const next = `#${path}?${params}`;
  if (next === location.hash) return;
  // pushState and replaceState do not fire "hashchange", so the router does not draw the page again
  history[push ? "pushState" : "replaceState"](null, "", next);
}

/**
 * Controller for one list with a sort and a pager. It loads a page, draws it, keeps the address and tells screen readers about the change.
 * The pager and the sort are drawn again after each load. A sort or a page size change goes to page 1. The size is remembered (loadPageSize).
 *
 * @param {object} cfg
 *  key         name of the list, for the page size memory ("jobs", "bookmarks", "applications")
 *  query       ctx.query of the route
 *  sorts       [{ value, label }], the first one is the default
 *  sortId      id of the select (unique on the page)
 *  sortHost    element for the sort select (leave out for a list with no sort)
 *  pagerHost   element for the pager
 *  listHost    element with the list (it gets aria-busy while a new page loads)
 *  focusHost   element to focus after a page change (a heading with tabindex -1)
 *  fetchPage   async ({ page, pageSize, sort }) => { page: { page, pageSize, total, totalPages }, limitedTo?, ... }
 *  render      (res, state) => void   draws the list (and the count) for one page
 *  onLoading   () => void             the first load: draw "Loading…"
 *  onError     (err) => void
 */
export function createPagedList(cfg) {
  const sortValues = cfg.sorts.map((s) => s.value);
  const state = { ...readListQuery(cfg.query, cfg.key, sortValues), total: 0, totalPages: 1 };
  const sortLabel = (v) => cfg.sorts.find((s) => s.value === v)?.label || v;
  let token = 0;
  let firstDone = false;

  /** reason: "page" | "size" | "sort" | "" (first load or reload). It sets the URL entry, the focus and the announcement. */
  async function load({ reason = "", quiet = false } = {}) {
    const my = ++token;
    if (!firstDone && !quiet) cfg.onLoading?.();
    else if (!quiet) cfg.listHost?.setAttribute("aria-busy", "true");
    let res;
    try {
      res = await cfg.fetchPage({ page: state.page, pageSize: state.pageSize, sort: state.sort });
    } catch (err) {
      if (my !== token || !cfg.pagerHost.isConnected) return;
      cfg.listHost?.removeAttribute("aria-busy");
      cfg.pagerHost.innerHTML = "";
      firstDone = true;
      cfg.onError(err);
      return;
    }
    if (my !== token || !cfg.pagerHost.isConnected) return;   // an older answer, or the user left the page
    firstDone = true;
    const p = res.page || { page: 1, pageSize: state.pageSize, total: (res.items || []).length, totalPages: 1 };
    state.page = p.page;                   // the server moves a page past the end to the last page
    state.total = p.total;
    state.totalPages = p.totalPages;
    const urlPage = Number(new URLSearchParams(location.hash.split("?")[1] || "").get("page"));
    if (reason) writeListUrl(state, true);                                   // a change by the user: a new history entry
    else if (urlPage && urlPage !== state.page) writeListUrl(state, false);   // the server moved the page: the address tells the truth
    cfg.render(res, state);
    cfg.listHost?.removeAttribute("aria-busy");
    cfg.pagerHost.innerHTML = pagerHtml({ page: p.page, pageSize: res.limitedTo ? p.pageSize : state.pageSize, total: p.total, limitedTo: res.limitedTo });
    const where = `Page ${state.page} of ${state.totalPages}`;
    if (reason === "page") {
      announce(where);
      if (cfg.focusHost) { cfg.focusHost.scrollIntoView({ block: "start" }); cfg.focusHost.focus({ preventScroll: true }); }
    } else if (reason === "sort") {
      announce(`Sorted by ${sortLabel(state.sort)}. ${where}`);
    } else if (reason === "size") {
      announce(`${state.pageSize} rows per page. ${where}`);
      cfg.pagerHost.querySelector("[data-pager-size]")?.focus({ preventScroll: true });
    } else if (quiet && cfg.focusHost && document.activeElement === document.body) {
      cfg.focusHost.focus({ preventScroll: true });
    }
  }

  function drawSort() {
    if (!cfg.sortHost) return;
    cfg.sortHost.innerHTML = sortSelectHtml({ id: cfg.sortId, value: state.sort, options: cfg.sorts });
    bindSort(cfg.sortHost, cfg.sortId, (value) => { state.sort = value; state.page = 1; load({ reason: "sort" }); });
  }

  bindPager(cfg.pagerHost, {
    onPage: (n) => { state.page = n; load({ reason: "page" }); },
    onPageSize: (size) => { state.pageSize = size; state.page = 1; load({ reason: "size" }); },
    pageSizeKey: cfg.key,
  });
  drawSort();
  return { state, load, reload: (o = {}) => load({ quiet: true, ...o }), start: () => load() };
}
