// Employer screens (Jinder V2): Home, My jobs, job form, job overview, applicants of a job, review, talent list and talent detail.
// Employers see the allowlist profile only: alias, level, years, skills with levels, certifications and awards (names and years).
// They never see a name, an email, a country, the CV, the evidence lines or a score on a person.
// Lists have a pager and a sort (R5, R6). Compare uses the basket in the menu shell (R9). Premium features use the lock badge (R7).
import { iconHtml as icon, esc, formatDate, announce } from "../core/dom.js";
import { api } from "../api/index.js";
import { clearErrors, showAlert, applyFieldErrors } from "../core/forms.js";
import { paintMeters, openReport } from "../components/job-card.js";
import { ribbonHtml, stepperHtml, historyHtml, skillMatchHtml, slotText, coverageText } from "../components/status.js";
import { openModal, textArea } from "../components/modal.js";
import { barChartHtml } from "../components/charts.js";
import { createCombobox } from "../components/combobox.js";
import { pagerHtml, bindPager, loadPageSize } from "../components/pagination.js";
import { sortSelectHtml, bindSort } from "../components/sort-select.js";
import { jdViewHtml } from "../components/jd-view.js";
import { lockedBadgeHtml, bindPremiumLocks } from "../components/premium.js";
import { compareStore, COMPARE_EVENT } from "../core/compare-store.js";
import { LEVELS, SKILL_LEVELS, WORK_MODES, PAGE_SIZES, COMPARE_MAX, skillLevelLabel } from "../data/levels.js";
import { DOMAINS, SPECIALISATIONS, CITIES, WORK_TYPES, QUALIFICATIONS, CERTIFICATIONS, AWARD_KINDS, SKILLS } from "../data/reference.js";
import { CONFIG } from "../config.js";

const STAGE_LABEL = { applied: "Applied", contacted: "Contacted", review: "In review", interview: "Interview", accepted: "Accepted", offer: "Offer", confirmed: "Confirmed", rejected: "Not selected", declined: "Declined" };
const BADGE_CHIP = { open: "chip-green", closing: "chip-yellow", closed: "chip-rose" };
const BADGE_TEXT = { open: "Open", closing: "Closing soon", closed: "Closed" };
const MAX_DESCRIPTION = 10000;     // the same limit as the backend (catalogue.MAX_DESCRIPTION). The description is never cut.
const MAX_SKILLS = 12;
const MAX_CERTS = 10;              // for each list (required, preferred)
const MAX_AWARDS = 10;
const JOB_SORTS = [{ value: "newest", label: "Newest first" }];
const TALENT_SORTS = [{ value: "best", label: "Best fit for this job" }, { value: "updated", label: "Recently updated" }];

const loadingHtml = (t) => `<div class="empty" role="status"><p>${esc(t)}</p></div>`;
const backHtml = (href, text) => `<a class="back-link" href="${href}">${icon("chevron-left")}${esc(text)}</a>`;
const badgeHtml = (j) => `<span class="chip ${BADGE_CHIP[j.badge] || "chip-neutral"}">${esc(j.label)}</span>`;
const failHtml = (title, err, back) => `<div class="dash">${back}<div class="dash-head"><div><h1>${esc(title)}</h1><p class="dash-sub">${esc(err.message || "Try again later.")}</p></div></div></div>`;
const errorHtml = (err) => `<div class="empty" role="alert"><p>${esc(err.message || "Try again later.")}</p><button type="button" class="btn btn-secondary" data-retry>Try again</button></div>`;
const isRealBackend = () => CONFIG.API_MODE === "http";   // the mock keeps the old fields only (plan F9): the new inputs are hidden there
const key = (s) => String(s ?? "").trim().toLowerCase();

// A Premium feature that a Basic employer cannot use: the gold box with a lock badge. A click on the badge opens the Premium dialog.
const upgradeBoxHtml = (text, feature) => `
  <div class="upgrade">
    ${lockedBadgeHtml(feature)}
    <p>${esc(text)}</p>
    <a class="btn btn-secondary" href="#/settings?section=plan">See plans</a>
  </div>`;

// ---------- Small formatters ----------
const yearsText = (n) => `${n} ${Number(n) === 1 ? "year" : "years"}`;
function experienceText(min, max) {
  const lo = min == null || min === "" ? null : Number(min);
  const hi = max == null || max === "" ? null : Number(max);
  if (lo == null && hi == null) return "";
  if (hi == null) return `${yearsText(lo)} or more`;
  if (lo == null) return `Up to ${yearsText(hi)}`;
  return lo === hi ? yearsText(lo) : `${lo} to ${yearsText(hi)}`;
}
function updatedText(iso) {
  const t = Date.parse(iso);
  if (!t) return "";
  const days = Math.max(0, Math.floor((Date.now() - t) / 864e5));
  return days === 0 ? "Updated today" : `Updated ${days} ${days === 1 ? "day" : "days"} ago`;
}
const levelText = (n) => skillLevelLabel(n);
const reqsOf = (job) => (Array.isArray(job?.skillRequirements) ? job.skillRequirements.filter((r) => r && r.name) : []);
const levelMap = (list) => new Map((Array.isArray(list) ? list : []).map((s) => [key(s.name), s.level]));
const credText = (c) => `${c.name}${c.year ? ` (${c.year})` : ""}`;

// Coverage as a small meter + "4 of 6 skills"
const coverageMini = (c, matched, total) => `
  <div class="cov-mini"><span class="cov-num">${c != null ? `${c}%` : "—"}</span>
    <span class="meter meter-sm" role="img" aria-label="${c != null ? `${c}% of the job skills covered` : "No job chosen"}"><span data-w="${c || 0}"></span></span>
    <span class="hint">${total ? `${matched} of ${total} skills` : "Choose a job"}</span></div>`;

// Target applicants vs current (Feature 6 AC2)
const targetHtml = (j) => {
  const pct = j.targetApplicants ? Math.min(100, Math.round((j.applicantCount / j.targetApplicants) * 100)) : 0;
  return `<div class="cov-mini"><span class="cov-num">${j.applicantCount} / ${j.targetApplicants}</span>
    <span class="meter meter-sm" role="img" aria-label="${j.applicantCount} of ${j.targetApplicants} target applicants"><span data-w="${pct}"></span></span>
    <span class="hint">applicants vs target</span></div>`;
};

// ---------- Lists with a pager and a sort (R5, R6) ----------
// The URL keeps page, pageSize and sort (and the job). A change draws the list again in place and adds one history entry
// (history.pushState does not start the router, so there is no flash). The Back button starts the router, which reads the URL again.
function readListState(query, storeKey, sorts) {
  const size = Number(query.pageSize);
  return {
    page: Math.max(1, parseInt(query.page, 10) || 1),
    pageSize: PAGE_SIZES.includes(size) ? size : loadPageSize(storeKey),
    sort: sorts.some((s) => s.value === query.sort) ? query.sort : sorts[0].value,
  };
}
function listUrl(path, base, state, sorts) {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(base)) if (v) q.set(k, v);
  if (state.sort !== sorts[0].value) q.set("sort", state.sort);
  if (state.page > 1) q.set("page", String(state.page));
  if (state.pageSize !== PAGE_SIZES[0]) q.set("pageSize", String(state.pageSize));
  const s = q.toString();
  return s ? `${path}?${s}` : path;
}
const pageNote = (pg, noun) => `Page ${pg.page} of ${pg.totalPages}. Showing ${(pg.page - 1) * pg.pageSize + 1} to ${Math.min(pg.total, pg.page * pg.pageSize)} of ${pg.total} ${noun}.`;

/**
 * Draw a list and its pager. `load({ page, pageSize, sort })` gives the API answer ({ items, page, ... }). `render(res)` gives the HTML of the list.
 * `first` is an answer that was loaded already (it is drawn without a new request).
 * Returns { show(opts), state, sorts }. `show({ push, say, focus })`: push = add a history entry, say = text for the live region
 * (true = the page note), focus = "heading" | "size" | "".
 */
function mountPagedList({ listEl, pagerEl, headingEl, storeKey, state, sorts, path, base, load, render, after, noun, first = null }) {
  let seq = 0;
  async function show({ push = false, say = "", focus = "", res = null } = {}) {
    const mine = ++seq;
    if (push) {
      const url = `#${listUrl(path, typeof base === "function" ? base() : base, state, sorts)}`;
      if (location.hash !== url) history.pushState(null, "", url);
    }
    if (!res) {
      listEl.setAttribute("aria-busy", "true");
      listEl.innerHTML = loadingHtml(`Loading ${noun}…`);
      pagerEl.innerHTML = "";
      try { res = await load({ page: state.page, pageSize: state.pageSize, sort: state.sort }); }
      catch (err) {
        if (mine !== seq || !listEl.isConnected) return;
        listEl.removeAttribute("aria-busy");
        listEl.innerHTML = errorHtml(err);
        listEl.querySelector("[data-retry]")?.addEventListener("click", () => show({ focus: "heading" }));
        return;
      }
      if (mine !== seq || !listEl.isConnected) return;
    }
    const pg = res.page || { page: 1, pageSize: state.pageSize, total: res.items.length, totalPages: 1 };
    state.page = pg.page;
    listEl.removeAttribute("aria-busy");
    listEl.innerHTML = render(res);
    pagerEl.innerHTML = pagerHtml({ ...pg, limitedTo: res.limitedTo });
    paintMeters(listEl);
    after?.(res);
    if (say) announce(say === true ? pageNote(pg, noun) : `${say} ${pageNote(pg, noun)}`);
    if (focus === "heading") headingEl?.focus();
    else if (focus === "size") pagerEl.querySelector("[data-pager-size]")?.focus();
  }
  bindPager(pagerEl, {
    pageSizeKey: storeKey,
    onPage: (p) => { state.page = p; show({ push: true, say: true, focus: "heading" }); },
    onPageSize: (n) => { state.pageSize = n; state.page = 1; show({ push: true, say: true, focus: "size" }); },
  });
  return { show: (o = {}) => show(first && !o.reload ? { ...o, res: first } : o), state, sorts, reload: (o = {}) => show(o) };
}

// ---------- Recruiter Home (Feature 7 AC5, AC8) ----------
export async function recruiterHomeView(root, ctx) {
  const me = ctx.user;
  root.innerHTML = `
    <div class="dash">
      <div class="dash-head"><div><h1>Welcome, ${esc(me.name.split(" ")[0])}</h1><p class="dash-sub">Employer workspace · ${esc(me.company || "")}</p></div>
        <a class="btn btn-primary btn-lg" href="#/my-jobs/new">${icon("briefcase")} Post a job</a></div>
      <div class="grid-3" data-cards>${loadingHtml("Loading…")}</div>
      <div class="dash-grid dash-grid-even">
        <section class="panel" aria-labelledby="jobsTitle"><div class="panel-head"><h2 id="jobsTitle">My jobs</h2><a class="text-link" href="#/my-jobs">See all</a></div><div data-jobs>${loadingHtml("Loading jobs…")}</div></section>
        <section class="panel" aria-labelledby="topTitle"><div class="panel-head"><div><h2 id="topTitle">Top talent</h2><p class="muted" data-top-sub></p></div><a class="text-link" href="#/candidates">See all</a></div><div data-top>${loadingHtml("Loading talent…")}</div></section>
      </div>
      <section class="panel" aria-labelledby="chartsTitle"><h2 id="chartsTitle">Hiring activity</h2><div data-charts>${loadingHtml("Loading…")}</div></section>
    </div>`;
  bindPremiumLocks(root);
  const $ = (k) => root.querySelector(`[data-${k}]`);
  const [stats, jobs, cands] = await Promise.all([
    api.stats.get().catch(() => null),
    api.recruiter.jobs.list({ pageSize: 10 }).catch(() => ({ items: [], page: { total: 0 } })),
    api.recruiter.candidates.list({ pageSize: 3, sort: "best" }).catch(() => null),
  ]);
  if (!root.isConnected) return;
  const b = stats?.basic || { openJobs: 0, jobsAtTarget: 0, awaitingResponse: 0, totalJobs: 0 };
  $("cards").innerHTML = [
    ["Open jobs", "briefcase", b.openJobs, `${b.totalJobs} posted in total`],
    ["Jobs at target", "target", b.jobsAtTarget, "Jobs with enough applicants"],
    ["Waiting for you", "clock", b.awaitingResponse, b.awaitingResponse ? "Applications that need an answer" : "Nothing waiting on you"],
  ].map(([label, ic, n, meta]) => `<div class="report-card"><div class="report-head"><span class="label">${label}</span>${icon(ic)}</div><div class="num">${esc(n)}</div><div class="meta">${esc(meta)}</div></div>`).join("");

  $("jobs").innerHTML = jobs.items.length
    ? `<ul class="mini-list">${jobs.items.slice(0, 4).map((j) => `<li><div><a class="job-title-link" href="#/my-jobs/${esc(j.id)}/overview">${esc(j.title)}</a><p class="hint">${esc(j.location)} · ${j.awaitingCount ? `<a class="text-link" href="#/my-jobs/${esc(j.id)}?status=waiting">${j.awaitingCount} waiting for you</a>` : "Nothing waiting"}</p></div>${badgeHtml(j)}</li>`).join("")}</ul>`
    : `<div class="empty"><p>No jobs yet. Post a job to see matched talent.</p><a class="btn btn-primary" href="#/my-jobs/new">Post a job</a></div>`;

  if (cands?.job) {
    $("top-sub").textContent = `For ${cands.job.title}. Ordered by skill coverage.`;
    $("top").innerHTML = cands.items.length
      ? `<ul class="mini-list">${cands.items.slice(0, 3).map((c) => `<li><div><a class="job-title-link" href="#/candidates/${esc(c.id)}?jobId=${esc(cands.job.id)}">${esc(c.alias)}</a><p class="hint">${esc([c.level, ...c.roles.map((r) => r.title).slice(0, 2)].filter(Boolean).join(" · ") || "No roles listed")}</p></div>${coverageMini(c.coverage, c.matched, c.total)}</li>`).join("")}</ul>`
      : `<p class="muted">No talent matches this job yet.</p>`;
  } else {
    $("top-sub").textContent = "";
    $("top").innerHTML = `<p class="muted">Post a job to see anonymous talent ordered by skill coverage.</p>`;
  }

  const adv = stats?.advanced;
  const totalJobs = jobs.page?.total ?? jobs.items.length;
  $("charts").innerHTML = `
    <div class="charts-grid">
      <div>${barChartHtml(jobs.items.map((j) => ({ label: j.title, value: j.applicantCount })), { title: "Applicants per job", empty: "No jobs yet." })}${totalJobs > jobs.items.length ? `<p class="hint">Shows the newest ${jobs.items.length} of ${totalJobs} jobs.</p>` : ""}</div>
      ${adv ? barChartHtml(adv.pipeline.filter((p) => p.count).map((p) => ({ label: STAGE_LABEL[p.stage], value: p.count })), { title: "Pipeline by stage", empty: "No applications yet." }) : upgradeBoxHtml("See your pipeline by stage and how talent interacts with each job.", "Advanced charts")}
      ${adv ? `<figure class="chart"><figcaption>Interest per job</figcaption><div class="table-wrap"><table class="data-table"><thead><tr><th scope="col">Job</th><th scope="col">Shown</th><th scope="col">Opened</th><th scope="col">Saved</th><th scope="col">Applied</th></tr></thead>
        <tbody>${adv.jobs.map((j) => `<tr><th scope="row">${esc(j.title)}</th><td>${j.appear}</td><td>${j.watch}</td><td>${j.save}</td><td>${j.apply}</td></tr>`).join("")}</tbody></table></div><p class="hint">Totals per job. We never show what one talent did.</p></figure>` : ""}
    </div>`;
  paintMeters(root);
}

// ---------- My jobs (Feature 6 AC1–AC3; R5) ----------
const jobRowHtml = (j) => `
  <li class="app-row">
    <div class="app-main">
      <h3><a class="job-title-link" href="#/my-jobs/${esc(j.id)}/overview">${esc(j.title)}</a></h3>
      <p class="job-meta">${[j.category, j.level, j.location, j.type].filter(Boolean).map(esc).join(" · ")}</p>
      <p class="hint">Posted ${esc(formatDate(j.postedAt))} · Closes ${esc(formatDate(j.closesAt))}${j.contactedCount ? ` · ${j.contactedCount} invited` : ""}</p>
    </div>
    <div class="app-side">
      ${badgeHtml(j)}
      ${j.awaitingCount ? `<span class="chip chip-yellow">${icon("clock")}${j.awaitingCount} waiting for you</span>` : ""}
      ${targetHtml(j)}
      <a class="btn btn-ghost btn-sm" href="#/my-jobs/${esc(j.id)}">${icon("users")}Applicants<span class="sr-only"> for ${esc(j.title)}</span></a>
      <a class="btn btn-ghost btn-sm" href="#/my-jobs/${esc(j.id)}/edit">${icon("edit")}Edit<span class="sr-only"> ${esc(j.title)}</span></a>
    </div>
  </li>`;

export async function myJobsView(root, ctx) {
  const storeKey = "my-jobs";
  root.innerHTML = `
    <div class="dash">
      <div class="dash-head"><div><h1>My jobs</h1><p class="dash-sub">Post jobs and manage your hiring pipeline.</p></div><div class="panel-actions"><a class="btn btn-secondary btn-lg" href="#/my-jobs/new?from=file">${icon("upload")} Post from a PDF</a><a class="btn btn-primary btn-lg" href="#/my-jobs/new">${icon("briefcase")} Post a job</a></div></div>
      <section class="panel" aria-labelledby="myJobsTitle">
        <div class="panel-head"><h2 id="myJobsTitle" tabindex="-1">Your jobs</h2><p class="muted" data-sort-note>Newest first.</p></div>
        <div data-list aria-live="off">${loadingHtml("Loading jobs…")}</div>
        <div data-pager></div>
      </section>
    </div>`;
  const state = readListState(ctx.query, storeKey, JOB_SORTS);
  const list = mountPagedList({
    listEl: root.querySelector("[data-list]"), pagerEl: root.querySelector("[data-pager]"), headingEl: root.querySelector("#myJobsTitle"),
    storeKey, state, sorts: JOB_SORTS, path: "/my-jobs", base: {}, noun: "jobs",
    load: (p) => api.recruiter.jobs.list(p),
    render: (res) => (res.items.length
      ? `<ul class="app-list">${res.items.map(jobRowHtml).join("")}</ul>`
      : `<div class="empty"><div class="icon-tile accent">${icon("briefcase")}</div><p>No jobs yet. Post your first job. Jinder suggests the required skills.</p><a class="btn btn-primary" href="#/my-jobs/new">Post a job</a></div>`),
  });
  await list.show({ reload: true });
}

// ---------- Job form: new and edit (Feature 6 AC1, AC10, AC13; decision Q2; R2) ----------
const options = (list, value, placeholder = "Choose…") => {
  const all = value && !list.includes(value) ? [...list, value] : list;   // a value from older data stays in the list
  return `<option value="">${esc(placeholder)}</option>${all.map((o) => `<option${o === value ? " selected" : ""}>${esc(o)}</option>`).join("")}`;
};
const dateValue = (iso) => (iso ? new Date(iso).toISOString().slice(0, 10) : "");
const tomorrow = () => new Date(Date.now() + 864e5).toISOString().slice(0, 10);

// The job description template (F4). A new job starts with these headings. Empty bullets and empty sections are removed when the job is posted.
const JD_HEADINGS = ["About the role", "What you will do", "What you bring", "Nice to have", "Tech stack", "What we offer", "About the company", "How we hire"];
const JD_TEMPLATE = JD_HEADINGS.map((h) => `## ${h}\n- `).join("\n\n");
const isHeading = (line) => /^#{1,6}\s+\S/.test(line.trim());

/** The description as it is stored: no empty bullet, no heading without text under it, no extra blank lines. */
export function cleanJdText(text) {
  const lines = String(text ?? "").replace(/\r\n?/g, "\n").split("\n").filter((l) => !/^\s*[-*•]\s*$/.test(l));
  const out = [];
  lines.forEach((line, i) => {
    if (isHeading(line)) {
      let j = i + 1;
      while (j < lines.length && !lines[j].trim()) j++;
      if (j >= lines.length || isHeading(lines[j])) return;   // an empty section
    }
    out.push(line);
  });
  return out.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

// ---------- Post a job from a file: upload → read (poll) → fill the form → the employer checks ----------
const JD_TYPES = [".pdf", ".docx"];
const JD_MAX_BYTES = 10 * 1024 * 1024;
// The form field of each key that the file parser can fill. The label of the field gets the "From your file" or "Missing" marker.
const FIELD_IDS = {
  title: "jf-title", category: "jf-category", domain: "jf-category", specialisation: "jf-spec", level: "jf-level", minYears: "jf-minyears", maxYears: "jf-maxyears",
  workMode: "jf-workmode", educationMin: "jf-edu", location: "jf-location", type: "jf-type", salary: "jf-salary", description: "jf-desc",
};
const SELECT_KEYS = new Set(["category", "specialisation", "level", "workMode", "educationMin", "location", "type"]);

function bindImport(root, form, { fill, focus }) {
  const box = root.querySelector("[data-import]");
  const input = box.querySelector("#jf-file");
  const zone = box.querySelector("[data-drop]");
  const fileRow = box.querySelector("[data-file]");
  const errEl = box.querySelector("#jf-file-error");
  const status = box.querySelector("[data-import-status]");
  const read = box.querySelector("[data-read]");
  let file = null;

  const showFile = () => {
    read.disabled = !file;
    fileRow.innerHTML = file ? `<div class="file-chip">${icon("file")}<span class="file-name">${esc(file.name)}</span><span class="hint">${Math.max(1, Math.round(file.size / 1024))} KB</span><button type="button" class="btn btn-ghost btn-icon" data-remove-file aria-label="Remove ${esc(file.name)}">${icon("x")}</button></div>` : "";
    fileRow.querySelector("[data-remove-file]")?.addEventListener("click", () => { file = null; input.value = ""; showFile(); });
  };
  const pick = (f) => {
    errEl.textContent = "";
    if (!f) return;
    const ext = f.name.slice(f.name.lastIndexOf(".")).toLowerCase();
    if (!JD_TYPES.includes(ext)) { file = null; showFile(); errEl.textContent = "Use a PDF or DOCX file."; return; }
    if (f.size > JD_MAX_BYTES) { file = null; showFile(); errEl.textContent = "The file is larger than 10 MB. Use a smaller file."; return; }
    file = f;
    showFile();
  };
  input.addEventListener("change", () => pick(input.files[0]));
  zone.addEventListener("dragover", (e) => { e.preventDefault(); zone.classList.add("drag"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("drag"));
  zone.addEventListener("drop", (e) => { e.preventDefault(); zone.classList.remove("drag"); pick(e.dataTransfer.files[0]); });

  // "From your file" / "Missing" markers next to the labels. A change to a field removes its marker.
  const labelOf = (name) => {
    if (name === "skills" || name === "skillRequirements") return form.querySelector(".skills-editor legend");
    if (name === "certifications") return form.querySelector("[data-mark-for=certifications]");
    if (name === "awards") return form.querySelector("[data-mark-for=awards]");
    return FIELD_IDS[name] ? form.querySelector(`label[for="${FIELD_IDS[name]}"]`) : null;
  };
  const mark = (name, kind) => {
    const label = labelOf(name);
    if (!label) return;
    label.querySelector(".field-markers")?.remove();
    if (!kind) return;
    label.insertAdjacentHTML("beforeend", kind === "file"
      ? ` <span class="field-markers"><span class="chip chip-ai" title="Jinder read this from your file. Check it.">${icon("check")}From your file</span></span>`
      : ` <span class="field-markers"><span class="chip chip-yellow" title="Your file does not show this. Add it.">Missing</span></span>`);
  };
  Object.entries(FIELD_IDS).forEach(([name, id]) => form.querySelector(`#${id}`)?.addEventListener("input", () => mark(name, null)));

  read.addEventListener("click", async () => {
    read.disabled = true;
    errEl.textContent = "";
    status.innerHTML = `<div class="reading" role="status"><div class="progress-indeterminate" aria-hidden="true"><span></span></div><p>Reading your file…</p></div>`;
    let res;
    try {
      const up = await api.recruiter.jobs.importFile(file);
      const started = Date.now();
      do {
        await new Promise((r) => setTimeout(r, 600));
        res = await api.recruiter.jobs.importStatus(up.parse.id);
      } while (res.status === "parsing" && Date.now() - started < 30000);
    } catch (err) {
      res = { status: "failed", error: err.fields?.file || err.message };
    }
    if (!root.isConnected) return;
    if (res.status !== "done") {
      status.innerHTML = `<div class="form-alert show error" role="alert">${esc(res.error || "Reading the file took too long. Try again, or fill in the form yourself.")}</div>`;
      read.disabled = !file;
      return;
    }
    const { fields, detected = [], missing = [], sampleLabel } = res.result;
    const notFit = fill(fields);   // the keys whose value did not fit a list in the form (they are shown as "Missing")
    const domainFilled = form.querySelector("#jf-category").value !== "";   // the parser may give `domain` and no `category`
    detected.filter((n) => !notFit.includes(n)).forEach((n) => mark(n, "file"));
    [...missing.filter((n) => !(n === "category" && domainFilled)), ...notFit].forEach((n) => mark(n, "missing"));
    status.innerHTML = `
      ${CONFIG.API_MODE === "mock" && sampleLabel ? `<p class="demo-banner" role="note">${icon("alert")}<span>Demo mode: the mock API filled the form from a sample job description (${esc(sampleLabel)}), not from your file.</span></p>` : ""}
      <div class="form-alert show success" role="status">${icon("check")} We filled the form from your file. Check each field, add the close date and the target, then post the job.</div>`;
    announce("The form is filled from your file. Check each field.");
    read.disabled = !file;
    form.querySelector("#jf-title").focus();
  });
  if (focus) { box.scrollIntoView({ block: "start" }); input.focus(); }
}

// Show API field errors next to their fields. A group (skills, certifications, awards) has a hidden input and a visible control to focus.
const ERROR_FIELD = { skillRequirements: "skills" };
const FOCUS_CONTROL = { skills: "#jf-skill", certifications: "#jf-cert-req", awards: "[name=awardKind]" };
function showFieldErrors(form, fields = {}) {
  let shown = false;
  for (const [k, msg] of Object.entries(fields)) {
    const name = ERROR_FIELD[k] || k;
    const errEl = form.querySelector(`.field-error[data-for="${name}"]`);
    if (!errEl) continue;
    shown = true;
    errEl.id = `${name}-error`;
    errEl.textContent = msg;
    const ctl = form.querySelector(FOCUS_CONTROL[name] || `[name="${name}"]`);
    if (ctl && ctl.type !== "hidden") {
      if (ctl.dataset.hint === undefined) ctl.dataset.hint = ctl.getAttribute("aria-describedby") || "";
      ctl.classList.add("invalid");
      ctl.setAttribute("aria-invalid", "true");
      ctl.setAttribute("aria-describedby", [ctl.dataset.hint, errEl.id].filter(Boolean).join(" "));
    }
  }
  form.querySelector("[aria-invalid='true']")?.focus();
  return shown;
}

export async function jobFormView(root, ctx) {
  const editing = !!ctx.params.id;
  const v2 = isRealBackend();
  let job = {
    title: "", category: "", specialisation: "", level: v2 ? "Mid" : "", minYears: null, maxYears: null, workMode: "", educationMin: "",
    location: "", type: "", salary: "", description: JD_TEMPLATE, skills: [], skillRequirements: [],
    certifications: { required: [], preferred: [] }, awards: { preferred: [] },
    targetApplicants: 20, closesAt: new Date(Date.now() + 30 * 864e5).toISOString(),
  };
  if (editing) {
    root.innerHTML = `<div class="dash">${backHtml("#/my-jobs", "My jobs")}<h1 class="sr-only">Edit job</h1>${loadingHtml("Loading job…")}</div>`;
    try { job = { ...job, ...(await api.recruiter.jobs.get(ctx.params.id)) }; }
    catch (err) { root.innerHTML = failHtml("We can't find this job", err, backHtml("#/my-jobs", "My jobs")); return; }
  }
  // The skills of the form: { name, level 1 to 5, must }. A job from older data has names only: they start at level 3 and "Must have".
  const reqs = (reqsOf(job).length ? reqsOf(job) : (job.skills || []).map((name) => ({ name, level: 3, must: true }))).map((r) => ({ name: r.name, level: r.level || 3, must: r.must !== false }));
  const certs = { required: [...(job.certifications?.required || [])], preferred: [...(job.certifications?.preferred || [])] };
  const awardKinds = [...AWARD_KINDS, ...(job.awards?.preferred || []).filter((k) => !AWARD_KINDS.some((a) => a.kind === k)).map((k) => ({ kind: k, label: k }))];
  const awardsOn = new Set(job.awards?.preferred || []);
  const overviewHref = editing ? `#/my-jobs/${esc(job.id)}/overview` : "#/my-jobs";
  const hasV2 = (html) => (v2 ? html : "");

  root.innerHTML = `
    <div class="dash">
      ${backHtml(overviewHref, editing ? "Back to job" : "My jobs")}
      <div class="dash-head"><div><h1>${editing ? `Edit ${esc(job.title)}` : "Post a job"}</h1><p class="dash-sub">Talent is matched on the required skills. Do not ask for age, gender, nationality or visa status.</p></div></div>
      ${editing ? `<div class="form-alert show warning" role="note">${icon("alert")} When you save, everyone who applied gets a notification that the job changed.</div>` : `
      <section class="panel job-import" aria-labelledby="impTitle" data-import>
        <h2 id="impTitle">Start from a job description file</h2>
        <p class="muted">Upload the job description as a PDF or DOCX. Jinder reads it and fills the form. You check every field before you post.</p>
        <div class="field" data-import-field>
          <input type="file" id="jf-file" class="sr-only" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document">
          <label class="dropzone" for="jf-file" data-drop>
            <span class="icon-tile accent">${icon("upload")}</span>
            <strong>Drag and drop the file, or <span class="legal-link">browse</span></strong>
            <span class="hint">PDF or DOCX, up to 10 MB</span>
          </label>
          <div data-file></div>
          <div class="field-error" id="jf-file-error" role="alert"></div>
        </div>
        <div data-import-status></div>
        <div class="form-actions"><button type="button" class="btn btn-primary" data-read disabled>${icon("file")} Read file and fill the form</button></div>
      </section>
      <p class="or-line"><span>or fill in the form yourself</span></p>`}
      <form class="panel job-form" novalidate>
        <div class="form-alert" role="alert"></div>
        <div class="field"><label for="jf-title">Job title</label><input id="jf-title" name="title" class="text-input" maxlength="100" value="${esc(job.title)}" required><div class="field-error" data-for="title"></div></div>
        <div class="field-grid">
          <div class="field"><label for="jf-category">Domain</label><select id="jf-category" name="category" class="text-input">${options(DOMAINS, job.category)}</select><div class="field-error" data-for="category"></div></div>
          ${hasV2(`<div class="field"><label for="jf-spec">Specialisation</label><select id="jf-spec" name="specialisation" class="text-input">${options(SPECIALISATIONS[job.category] || [], job.specialisation)}</select><div class="field-error" data-for="specialisation"></div></div>
          <div class="field"><label for="jf-level">Level</label><select id="jf-level" name="level" class="text-input">${options(LEVELS, job.level)}</select><div class="field-error" data-for="level"></div></div>
          <div class="field"><label for="jf-minyears">Least years of experience</label><input id="jf-minyears" name="minYears" type="number" min="0" max="40" step="0.5" inputmode="decimal" class="text-input" value="${esc(job.minYears ?? "")}" aria-describedby="jf-years-hint"><div class="field-error" data-for="minYears"></div></div>
          <div class="field"><label for="jf-maxyears">Most years of experience</label><input id="jf-maxyears" name="maxYears" type="number" min="0" max="40" step="0.5" inputmode="decimal" class="text-input" value="${esc(job.maxYears ?? "")}" aria-describedby="jf-years-hint"><div class="field-error" data-for="maxYears"></div></div>
          <div class="field"><label for="jf-workmode">Work mode</label><select id="jf-workmode" name="workMode" class="text-input">${options(WORK_MODES, job.workMode)}</select><div class="field-error" data-for="workMode"></div></div>
          <div class="field"><label for="jf-edu">Education</label><select id="jf-edu" name="educationMin" class="text-input">${options(QUALIFICATIONS, job.educationMin)}</select><div class="field-error" data-for="educationMin"></div></div>`)}
          <div class="field"><label for="jf-location">Location</label><select id="jf-location" name="location" class="text-input">${options(CITIES, job.location)}</select><div class="field-error" data-for="location"></div></div>
          <div class="field"><label for="jf-type">Work type</label><select id="jf-type" name="type" class="text-input">${options(WORK_TYPES, job.type)}</select><div class="field-error" data-for="type"></div></div>
          <div class="field"><label for="jf-salary">Salary (optional)</label><input id="jf-salary" name="salary" class="text-input" maxlength="60" value="${esc(job.salary === "Market competitive" ? "" : job.salary)}" placeholder="For example: $90,000 – $105,000"><div class="field-error" data-for="salary"></div></div>
          <div class="field"><label for="jf-closes">Close date</label><input id="jf-closes" name="closesAt" type="date" class="text-input" min="${tomorrow()}" value="${dateValue(job.closesAt)}"><div class="field-error" data-for="closesAt"></div></div>
          <div class="field"><label for="jf-target">Target applicants</label><input id="jf-target" name="targetApplicants" type="number" min="1" max="10000" class="text-input" value="${esc(job.targetApplicants)}"><div class="field-error" data-for="targetApplicants"></div></div>
        </div>
        ${hasV2(`<p class="hint" id="jf-years-hint">Leave the most years empty to say "or more".</p>`)}
        <div class="field jd-editor">
          <div class="jd-editor-head"><label for="jf-desc">Description</label><span class="hint" id="jf-desc-count" aria-live="off"></span></div>
          <p class="hint hint-top" id="jf-desc-hint">Start a line with "## " for a section title and with "- " for a bullet. Leave a blank line between paragraphs. Empty sections are removed when you post.</p>
          <textarea id="jf-desc" name="description" class="text-input textarea jd-textarea" rows="14" maxlength="${MAX_DESCRIPTION}" aria-describedby="jf-desc-hint">${esc(job.description)}</textarea>
          <div class="field-error" data-for="description"></div>
          <div class="jd-editor-actions"><button type="button" class="btn btn-secondary btn-sm" data-preview aria-expanded="false" aria-controls="jf-preview">${icon("eye")}Preview</button></div>
          <div id="jf-preview" class="jd-preview" hidden></div>
        </div>
        <fieldset class="field skills-editor">
          <legend class="field-label">Skills (1 to ${MAX_SKILLS})</legend>
          <p class="hint" id="jf-skills-hint">Jinder suggests skills from the title and the description. Add, remove or change them.${v2 ? " Set the level that the job needs. Mark each skill as a must or nice to have." : ""}</p>
          <ul class="${v2 ? "skill-req-list" : "chip-edit"}" data-skills aria-live="polite"></ul>
          <div class="skill-add">
            <div class="skill-add-combo" data-skill-combo></div>
            <button type="button" class="btn btn-secondary" data-add>Add</button>
            <button type="button" class="btn btn-ghost" data-suggest>${icon("star")}Suggest skills</button>
          </div>
          <div class="suggest-row" data-suggestions></div>
          <input type="hidden" name="skills"><div class="field-error" data-for="skills"></div>
        </fieldset>
        ${hasV2(`
        <fieldset class="field cert-editor">
          <legend class="field-label" data-mark-for="certifications">Certifications <span class="optional">(optional)</span></legend>
          <p class="hint" id="jf-certs-hint">Pick a certification from the list, or type your own and press Enter. A talent shows the name and the year only.</p>
          <div class="cert-grid">
            <div class="cert-col">
              <label class="field-label" for="jf-cert-req">Required certifications</label>
              <div class="input-row"><div data-cert-combo="required"></div><button type="button" class="btn btn-secondary" data-cert-add="required">Add<span class="sr-only"> required certification</span></button></div>
              <ul class="chip-edit" data-cert-list="required" aria-live="polite"></ul>
            </div>
            <div class="cert-col">
              <label class="field-label" for="jf-cert-pref">Preferred certifications</label>
              <div class="input-row"><div data-cert-combo="preferred"></div><button type="button" class="btn btn-secondary" data-cert-add="preferred">Add<span class="sr-only"> preferred certification</span></button></div>
              <ul class="chip-edit" data-cert-list="preferred" aria-live="polite"></ul>
            </div>
          </div>
          <input type="hidden" name="certifications"><div class="field-error" data-for="certifications"></div>
        </fieldset>
        <fieldset class="field award-editor">
          <legend class="field-label" data-mark-for="awards">Preferred awards <span class="optional">(optional)</span></legend>
          <p class="hint" id="jf-awards-hint">Choose the kinds of award that help a talent stand out (up to ${MAX_AWARDS}).</p>
          <div class="award-grid">${awardKinds.map((a) => `<label class="check"><input type="checkbox" name="awardKind" value="${esc(a.kind)}"${awardsOn.has(a.kind) ? " checked" : ""} aria-describedby="jf-awards-hint"><span>${esc(a.label)}</span></label>`).join("")}</div>
          <input type="hidden" name="awards"><div class="field-error" data-for="awards"></div>
        </fieldset>`)}
        <div class="form-actions">
          <a class="btn btn-ghost" href="${overviewHref}">Cancel</a>
          <button type="submit" class="btn btn-primary btn-lg">${editing ? "Save changes" : "Post job"}</button>
        </div>
      </form>
    </div>`;
  const form = root.querySelector("form");
  const alertEl = form.querySelector(".form-alert");
  const chips = form.querySelector("[data-skills]");
  const sugg = form.querySelector("[data-suggestions]");
  const desc = form.querySelector("#jf-desc");

  // --- Domain and specialisation: the specialisation list depends on the domain ---
  const cat = form.querySelector("#jf-category");
  const spec = form.querySelector("#jf-spec");
  cat.addEventListener("change", () => {
    if (!spec) return;
    const list = SPECIALISATIONS[cat.value] || [];
    spec.innerHTML = options(list, list.includes(spec.value) ? spec.value : "");
    announce(list.length ? `${list.length} specialisations for ${cat.value}.` : "Choose a domain to pick a specialisation.");
  });

  // --- Description: counter, preview ---
  const count = form.querySelector("#jf-desc-count");
  const prev = form.querySelector("#jf-preview");
  const prevBtn = form.querySelector("[data-preview]");
  const paintDesc = () => {
    count.textContent = `${desc.value.length.toLocaleString("en-AU")} of ${MAX_DESCRIPTION.toLocaleString("en-AU")} characters`;
    if (!prev.hidden) prev.innerHTML = jdViewHtml(cleanJdText(desc.value), { label: "Job description preview" });
  };
  desc.addEventListener("input", paintDesc);
  prevBtn.addEventListener("click", () => {
    const open = prev.hidden;
    prev.hidden = !open;
    prevBtn.setAttribute("aria-expanded", String(open));
    prevBtn.lastChild.textContent = open ? "Hide preview" : "Preview";
    if (open) paintDesc();
  });
  paintDesc();

  // --- Skills with a level and must / nice ---
  const skillOptions = (r) => SKILL_LEVELS.map((l) => `<option value="${l.value}"${l.value === r.level ? " selected" : ""}>${l.value} - ${esc(l.label)}</option>`).join("");
  const paint = () => {
    chips.innerHTML = reqs.length ? reqs.map((r, i) => (v2
      ? `<li class="skill-req">
          <span class="skill-req-name">${esc(r.name)}</span>
          <label class="skill-req-level"><span class="sr-only">Level for ${esc(r.name)}</span><select class="text-input select" data-level="${i}">${skillOptions(r)}</select></label>
          <label class="check skill-req-must"><input type="checkbox" data-must="${i}"${r.must ? " checked" : ""}><span>Must have<span class="sr-only"> ${esc(r.name)}</span></span></label>
          <button type="button" class="btn btn-ghost btn-icon" data-remove="${i}" aria-label="Remove ${esc(r.name)}">${icon("x")}</button>
        </li>`
      : `<li class="chip chip-neutral">${esc(r.name)}<button type="button" class="chip-x" data-remove="${i}" aria-label="Remove ${esc(r.name)}">${icon("x")}</button></li>`)).join("")
      : `<li class="hint">No skills yet.</li>`;
  };
  const add = (name, level = 3, must = true) => {
    name = String(name).trim();
    if (!name || reqs.some((x) => key(x.name) === key(name))) return;
    if (reqs.length >= MAX_SKILLS) return showAlert(alertEl, `You can add up to ${MAX_SKILLS} skills.`, "error");
    reqs.push({ name, level, must });
    paint();
    announce(`${name} added.`);
  };
  const skillCombo = createCombobox({ id: "jf-skill", options: SKILLS, placeholder: "Add a skill", clearOnPick: true, exclude: () => reqs.map((r) => r.name), onPick: (v) => add(v) });
  skillCombo.input.setAttribute("aria-label", "Add a skill");
  skillCombo.input.setAttribute("aria-describedby", "jf-skills-hint");
  skillCombo.input.addEventListener("keydown", (e) => { if (e.key === "Enter") e.preventDefault(); });   // Enter in an empty box must not post the form
  form.querySelector("[data-skill-combo]").append(skillCombo.el);
  chips.addEventListener("click", (e) => {
    const b = e.target.closest("[data-remove]");
    if (!b) return;
    const [r] = reqs.splice(Number(b.dataset.remove), 1);
    paint();
    announce(`${r.name} removed.`);
    skillCombo.input.focus();
  });
  chips.addEventListener("change", (e) => {
    const lv = e.target.closest("[data-level]");
    const mu = e.target.closest("[data-must]");
    if (lv) reqs[Number(lv.dataset.level)].level = Number(lv.value);
    if (mu) reqs[Number(mu.dataset.must)].must = mu.checked;
  });
  form.querySelector("[data-add]").addEventListener("click", () => { add(skillCombo.value()); skillCombo.input.value = ""; skillCombo.input.focus(); });
  form.querySelector("[data-suggest]").addEventListener("click", async (e) => {
    const btn = e.currentTarget; // e.currentTarget is null after an await
    btn.disabled = true;
    try {
      const res = await api.recruiter.jobs.suggestSkills({ title: form.elements.title.value, description: cleanJdText(desc.value) });
      const fresh = res.skills.filter((s) => !reqs.some((r) => key(r.name) === key(s)));
      sugg.innerHTML = fresh.length ? `<span class="hint">Suggested:</span>${fresh.map((s) => `<button type="button" class="chip chip-blue chip-btn" data-pick="${esc(s)}">${icon("plus")}${esc(s)}</button>`).join("")}` : `<span class="hint">No new suggestions. Add more detail to the description.</span>`;
      announce(fresh.length ? `${fresh.length} skills suggested.` : "No new suggestions.");
    } catch (err) { showAlert(alertEl, err.message, "error"); }
    finally { btn.disabled = false; }
  });
  sugg.addEventListener("click", (e) => {
    const b = e.target.closest("[data-pick]");
    if (!b) return;
    add(b.dataset.pick);   // a suggested skill starts at level 3 and "Must have"
    b.remove();
  });
  paint();

  // --- Certifications: required and preferred (pick from the list, or type your own) ---
  const certNames = CERTIFICATIONS.map((c) => c.name);
  const paintCerts = (which) => {
    const ul = form.querySelector(`[data-cert-list="${which}"]`);
    if (!ul) return;
    ul.innerHTML = certs[which].map((n, i) => `<li class="chip chip-blue">${esc(n)}<button type="button" class="chip-x" data-cert-remove="${which}:${i}" aria-label="Remove ${esc(n)}">${icon("x")}</button></li>`).join("");
  };
  const certInputs = {};
  if (v2) {
    for (const which of ["required", "preferred"]) {
      const addCert = (name) => {
        name = String(name).trim();
        if (!name) return;
        if (certs.required.concat(certs.preferred).some((x) => key(x) === key(name))) return announce(`${name} is in the list already.`);
        if (certs[which].length >= MAX_CERTS) return showAlert(alertEl, `You can add up to ${MAX_CERTS} ${which} certifications.`, "error");
        certs[which].push(name);
        paintCerts(which);
        announce(`${name} added to ${which} certifications.`);
      };
      const combo = createCombobox({ id: which === "required" ? "jf-cert-req" : "jf-cert-pref", options: certNames, placeholder: "Search or type a certification", clearOnPick: true, exclude: () => certs.required.concat(certs.preferred), onPick: addCert });
      certInputs[which] = combo;
      combo.input.addEventListener("keydown", (e) => { if (e.key === "Enter") e.preventDefault(); });   // Enter in an empty box must not post the form
      form.querySelector(`[data-cert-combo="${which}"]`).append(combo.el);
      form.querySelector(`[data-cert-add="${which}"]`).addEventListener("click", () => { addCert(combo.value()); combo.input.value = ""; combo.input.focus(); });
      paintCerts(which);
    }
    form.querySelector(".cert-editor").addEventListener("click", (e) => {
      const b = e.target.closest("[data-cert-remove]");
      if (!b) return;
      const [which, i] = b.dataset.certRemove.split(":");
      const [name] = certs[which].splice(Number(i), 1);
      paintCerts(which);
      announce(`${name} removed.`);
      certInputs[which].input.focus();
    });
    // Preferred awards: at most MAX_AWARDS kinds
    form.querySelector(".award-editor").addEventListener("change", (e) => {
      const box = e.target.closest("[name=awardKind]");
      if (box?.checked && form.querySelectorAll("[name=awardKind]:checked").length > MAX_AWARDS) {
        box.checked = false;
        announce(`You can choose up to ${MAX_AWARDS} kinds of award.`);
      }
    });
  }

  // --- The file import fills the new fields too ---
  const fill = (fields) => {
    const notFit = [];
    const setField = (name, value) => {
      const el = form.querySelector(`#${FIELD_IDS[name]}`);
      if (!el || value == null) return;
      el.value = String(value);
      if (SELECT_KEYS.has(name) && value !== "" && el.value !== String(value)) { el.value = ""; notFit.push(name); }   // the value is not in the list
    };
    // The parser can send `domain` (one of the 3 domains) and `category`. The domain list is the one that this form has.
    const domainValue = fields.domain ?? fields.category;
    if (domainValue != null) { setField("category", domainValue); cat.dispatchEvent(new Event("change")); }   // the specialisation list follows
    for (const name of Object.keys(FIELD_IDS)) if (name !== "category" && name !== "domain" && name in fields) setField(name, fields[name]);
    const incoming = Array.isArray(fields.skillRequirements) && fields.skillRequirements.length
      ? fields.skillRequirements.map((r) => ({ name: r.name, level: r.level || 3, must: r.must !== false }))
      : Array.isArray(fields.skills) ? fields.skills.map((name) => ({ name, level: 3, must: true })) : null;
    if (incoming) { reqs.splice(0, reqs.length, ...incoming.slice(0, MAX_SKILLS)); paint(); }
    if (v2 && fields.certifications) {
      certs.required = [...(fields.certifications.required || [])].slice(0, MAX_CERTS);
      certs.preferred = [...(fields.certifications.preferred || [])].slice(0, MAX_CERTS);
      paintCerts("required");
      paintCerts("preferred");
    }
    if (v2 && fields.awards) {
      const on = new Set(fields.awards.preferred || []);
      form.querySelectorAll("[name=awardKind]").forEach((box) => { box.checked = on.has(box.value); });
    }
    paintDesc();
    return notFit;
  };
  if (!editing) bindImport(root, form, { fill, focus: ctx.query.from === "file" });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearErrors(form, alertEl);
    const body = {
      title: form.elements.title.value, category: form.elements.category.value, location: form.elements.location.value, type: form.elements.type.value,
      salary: form.elements.salary.value, description: cleanJdText(desc.value), skills: reqs.map((r) => r.name),
      targetApplicants: Number(form.elements.targetApplicants.value),
      closesAt: form.elements.closesAt.value ? new Date(`${form.elements.closesAt.value}T23:59:00`).toISOString() : "",
    };
    if (v2) {
      const num = (name) => (form.elements[name].value === "" ? null : Number(form.elements[name].value));
      Object.assign(body, {
        specialisation: form.elements.specialisation.value, minYears: num("minYears"), maxYears: num("maxYears"),
        workMode: form.elements.workMode.value || null, educationMin: form.elements.educationMin.value,
        skillRequirements: reqs.map((r) => ({ name: r.name, level: r.level, must: r.must })),
        certifications: { required: certs.required, preferred: certs.preferred },
        awards: { preferred: [...form.querySelectorAll("[name=awardKind]:checked")].map((b) => b.value) },
      });
      if (form.elements.level.value) body.level = form.elements.level.value;
      if (body.minYears != null && body.maxYears != null && body.minYears > body.maxYears) {
        showFieldErrors(form, { maxYears: "The most years must be the same as or more than the least years." });
        showAlert(alertEl, "Correct the fields that show an error.", "error");
        return;
      }
    }
    const btn = form.querySelector("[type=submit]");
    btn.disabled = true;
    try {
      const saved = editing ? await api.recruiter.jobs.update(job.id, body) : await api.recruiter.jobs.create(body);
      announce(editing ? "The job is saved. Applicants get a notification." : "The job is posted.");
      ctx.navigate(`/my-jobs/${saved.id}/overview`);
    } catch (err) {
      btn.disabled = false;
      if (!showFieldErrors(form, err.fields)) showAlert(alertEl, err.message, "error");
      else showAlert(alertEl, "Correct the fields that show an error.", "error");
    }
  });
}

// ---------- The skills of a job, and how a talent stands against them ----------
// Result of one skill: "meets", "below", "missing", "related" (or "has" when the level is not known). Text and an icon, not only colour.
const RESULT = {
  meets: { label: "Meets", icon: "check" }, below: { label: "Below", icon: "alert" }, missing: { label: "Missing", icon: "x" },
  related: { label: "Related", icon: "target" }, has: { label: "Has it", icon: "check" },
};
function resultOf(req, matchItem, level) {
  const status = matchItem?.status;
  if (status === "partial") return { key: "related", via: matchItem.via };
  if (status === "gap" || (!status && level == null)) return { key: "missing" };
  if (level == null) return { key: "has" };
  return { key: level >= req.level ? "meets" : "below" };
}
const needText = (r) => `${levelText(r.level) || `Level ${r.level}`} · ${r.must ? "Must have" : "Nice to have"}`;

/** The skill by skill table of a talent for a job (job needs, talent level, result). */
function skillTableHtml(reqs, match, levels) {
  const items = new Map((match?.skills || []).map((i) => [key(i.name), i]));
  const rows = reqs.map((r) => {
    const level = levels.get(key(r.name));
    const res = resultOf(r, items.get(key(r.name)), level);
    return { r, level, res };
  });
  const counts = Object.keys(RESULT).map((k) => [k, rows.filter((x) => x.res.key === k).length]).filter(([, n]) => n);
  const table = `
    <div class="table-wrap"><table class="data-table skill-table">
      <caption class="sr-only">Skill by skill: what the job needs and what this talent has</caption>
      <thead><tr><th scope="col">Skill</th><th scope="col">Job needs</th><th scope="col">Talent</th><th scope="col">Result</th></tr></thead>
      <tbody>${rows.map(({ r, level, res }) => `<tr class="res-${res.key}">
        <th scope="row">${esc(r.name)}</th>
        <td>${esc(needText(r))}</td>
        <td>${level != null ? esc(levelText(level) || `Level ${level}`) : "—"}</td>
        <td class="result-cell">${icon(RESULT[res.key].icon)}<span>${RESULT[res.key].label}</span>${res.via ? ` <span class="hint">via ${esc(res.via)}</span>` : ""}</td>
      </tr>`).join("")}</tbody></table></div>`;
  return { table, counts };
}

/** The "skills for this job" part of a talent screen: a side box and, when the job has levels, a wide table. */
function skillsViewHtml({ match, reqs, levels, hasLevels }) {
  const cov = `<p class="cov-line"><strong>${match.coverage != null ? `${match.coverage}%` : "—"}</strong> skills covered · ${esc(coverageText(match))}</p>`;
  if (reqs.length && hasLevels) {
    const { table, counts } = skillTableHtml(reqs, match, levels);
    return {
      aside: `${cov}<ul class="result-counts">${counts.map(([k, n]) => `<li class="res-${k}">${icon(RESULT[k].icon)}${n} ${RESULT[k].label.toLowerCase()}</li>`).join("")}</ul><p class="hint">The table below shows each skill.</p>`,
      wide: `<section class="panel skills-wide" aria-labelledby="skTableTitle"><h2 id="skTableTitle">Skill by skill</h2><p class="muted">What the job needs and what this talent has. This shows skills only. Use your own judgement for the decision.</p>${table}</section>`,
    };
  }
  return { aside: `${cov}${skillMatchHtml(match.skills, { you: false })}<p class="hint">This shows skills only. Use your own judgement for the decision.</p>`, wide: "" };
}

// ---------- The shared profile as an employer sees it ----------
function talentProfileHtml(p, { reqs = [], jobSkills = [] } = {}) {
  const has = (k) => p[k] !== undefined;
  const levels = levelMap(p.skillLevels);
  const reqMap = new Map(reqs.map((r) => [key(r.name), r]));
  const asked = new Set([...jobSkills, ...reqs.map((r) => r.name)].map(key));
  const chips = (list) => (list.length ? list.map((v) => `<span class="chip chip-neutral">${esc(v)}</span>`).join("") : `<span class="muted">Not given</span>`);
  const row = (label, inner) => `<div class="pf-row"><dt>${esc(label)}</dt><dd>${inner}</dd></div>`;
  const skill = (name) => {
    const lvl = levelText(levels.get(key(name)));
    const req = reqMap.get(key(name));
    const isAsked = asked.has(key(name));
    return `<span class="chip ${isAsked ? "chip-green" : "chip-neutral"}">${esc(name)}${lvl ? ` · ${esc(lvl)}` : ""}${req && levelText(req.level) ? `<span class="chip-need">needs ${esc(levelText(req.level))}</span>` : ""}${isAsked ? `<span class="sr-only"> (the job asks for this skill)</span>` : ""}</span>`;
  };
  const experience = has("yearsExperience") && p.yearsExperience != null ? yearsText(p.yearsExperience) : p.years;
  const credChips = (list, ic, what) => (list && list.length
    ? list.map((c) => `<span class="chip chip-neutral cred-chip">${icon(ic)}<span class="sr-only">${what}: </span>${esc(credText(c))}</span>`).join("")
    : `<span class="muted">Not given</span>`);
  return `
    <div class="profile-card">
      <p class="pf-alias"><span class="avatar avatar-sm" aria-hidden="true">${esc((p.alias || "?").split(/\s+/).map((w) => w[0]).join("").slice(0, 2))}</span><strong>${esc(p.alias || "Anonymous")}</strong></p>
      <dl class="pf-list">
        ${has("level") ? row("Level", p.level ? `<span class="chip chip-blue">${esc(p.level)}</span>` : `<span class="muted">Not given</span>`) : ""}
        ${experience ? row("Experience", chips([String(experience)])) : (has("yearsExperience") ? row("Experience", chips([])) : "")}
        ${row("Roles", chips((p.roles || []).map((r) => (r.anzsco ? `${r.title} (ANZSCO ${r.anzsco})` : r.title))))}
        ${row("Skills", (p.skills || []).length ? p.skills.map(skill).join("") : `<span class="muted">Not given</span>`)}
        ${has("certifications") ? row("Certifications", credChips(p.certifications, "graduation", "Certification")) : ""}
        ${has("awards") ? row("Awards", credChips(p.awards, "star", "Award")) : ""}
        ${row("Qualifications", chips(p.qualifications || []))}
        ${p.industries ? row("Domains", chips(p.industries)) : ""}
        ${p.targetRoles ? row("Target roles", chips(p.targetRoles)) : ""}
        ${p.locations ? row("Locations", chips(p.locations)) : ""}
        ${p.workTypes ? row("Work types", chips(p.workTypes)) : ""}
      </dl>
    </div>`;
}

// ---------- Job overview (R4, F3): the whole job for the employer ----------
function fact(label, value, { empty = "Not given" } = {}) {
  if (value === undefined) return "";   // the answer has no such key (the mock backend): leave the fact out
  return `<div><dt>${esc(label)}</dt><dd>${value === null || value === "" ? `<span class="muted fact-empty">${esc(empty)}</span>` : esc(value)}</dd></div>`;
}

export async function jobOverviewView(root, ctx) {
  const back = backHtml("#/my-jobs", "My jobs");
  root.innerHTML = `<div class="dash">${back}<h1 class="sr-only">Job overview</h1>${loadingHtml("Loading job…")}</div>`;
  let job;
  try { job = await api.recruiter.jobs.get(ctx.params.id); }
  catch (err) { root.innerHTML = failHtml("We can't find this job", err, back); return; }
  // Premium: the counts of interest for this job. The same numbers as "Interest per job" on Home (counts, never people).
  const stats = await api.stats.get().catch(() => null);
  if (!root.isConnected) return;
  const interest = stats?.advanced?.jobs?.find((j) => j.id === job.id) || null;
  const premium = !!stats?.advanced;
  const closed = job.badge === "closed";
  const reqs = reqsOf(job);
  const certs = job.certifications;
  const awards = job.awards;
  const id = esc(job.id);
  document.title = `${job.title} — Jinder`;

  const skillsPanel = reqs.length
    ? `<div class="table-wrap"><table class="data-table skill-table">
        <caption class="sr-only">Skills of this job</caption>
        <thead><tr><th scope="col">Skill</th><th scope="col">Level needed</th><th scope="col">Must or nice</th></tr></thead>
        <tbody>${[...reqs.filter((r) => r.must), ...reqs.filter((r) => !r.must)].map((r) => `<tr><th scope="row">${esc(r.name)}</th><td>${esc(levelText(r.level) || `Level ${r.level}`)}</td><td>${r.must ? "Must have" : "Nice to have"}</td></tr>`).join("")}</tbody></table></div>`
    : `<div class="job-tags">${(job.skills || []).map((s) => `<span class="chip chip-neutral">${esc(s)}</span>`).join("") || `<span class="muted">No skills listed.</span>`}</div>`;
  const list = (items) => (items && items.length ? `<ul class="chip-row">${items.map((n) => `<li class="chip chip-neutral">${esc(n)}</li>`).join("")}</ul>` : `<p class="muted">None listed.</p>`);
  const awardLabel = (kind) => AWARD_KINDS.find((a) => a.kind === kind)?.label || kind;

  root.innerHTML = `
    <div class="dash job-overview">
      ${back}
      <header class="dash-head jo-head">
        <div>
          <h1>${esc(job.title)}</h1>
          <p class="dash-sub">${[job.company, job.location, job.salary].filter(Boolean).map(esc).join(" · ")}</p>
          <div class="job-tags jo-chips">
            <span class="chip ${BADGE_CHIP[job.badge] || "chip-neutral"}"><span class="sr-only">Status: </span>${esc(BADGE_TEXT[job.badge] || job.label)}</span>
            ${job.badge === "closing" ? `<span class="hint">${esc(job.label)}</span>` : ""}
            ${job.level ? `<span class="chip chip-blue"><span class="sr-only">Level: </span>${esc(job.level)}</span>` : ""}
            ${job.workMode ? `<span class="chip chip-neutral"><span class="sr-only">Work mode: </span>${esc(job.workMode)}</span>` : ""}
          </div>
        </div>
        <div class="panel-actions">
          ${closed ? "" : `<a class="btn btn-primary" href="#/my-jobs/${id}/edit">${icon("edit")} Edit job</a>`}
          <a class="btn btn-secondary" href="#/candidates?jobId=${id}">${icon("search")} See talent</a>
          <a class="btn btn-secondary" href="#/my-jobs/${id}">${icon("users")} See applicants</a>
        </div>
      </header>
      ${closed ? `<div class="form-alert show warning jo-banner" role="note">${icon("alert")} This job is closed. You can read it, but you can't edit it. You can still review the applications.</div>` : ""}
      <div class="jo-stats">
        <div class="report-card"><div class="report-head"><span class="label">Applicants</span>${icon("users")}</div>${targetHtml(job)}</div>
        <div class="report-card"><div class="report-head"><span class="label">Waiting for you</span>${icon("clock")}</div><div class="num">${job.awaitingCount}</div><div class="meta">${job.awaitingCount ? "Applications that need an answer" : "Nothing waiting on you"}</div></div>
        <div class="report-card"><div class="report-head"><span class="label">Invited</span>${icon("send")}</div><div class="num">${job.contactedCount ?? 0}</div><div class="meta">Talent that you invited to apply</div></div>
        <div class="report-card jo-interest"><div class="report-head"><span class="label">Interest in this job</span>${icon("chart")}</div>
          ${interest
            ? `<dl class="interest-list"><div><dt>Shown</dt><dd>${interest.appear}</dd></div><div><dt>Opened</dt><dd>${interest.watch}</dd></div><div><dt>Saved</dt><dd>${interest.save}</dd></div><div><dt>Applied</dt><dd>${interest.apply}</dd></div></dl><div class="meta">Totals for this job. We never show what one talent did.</div>`
            : premium ? `<div class="meta">No numbers yet.</div>` : `<div class="jo-lock">${lockedBadgeHtml("Interest per job")}<div class="meta">See how often talent saw, opened and saved this job.</div></div>`}
        </div>
      </div>
      <div class="jd-grid jo-grid">
        <section class="panel" aria-labelledby="aboutTitle"><h2 id="aboutTitle">About the role</h2>${jdViewHtml(job.description, { label: "About the role" })}</section>
        <aside class="panel" aria-labelledby="factsTitle"><h2 id="factsTitle">Job facts</h2>
          <dl class="facts jo-facts">
            ${fact("Domain", job.category)}
            ${fact("Specialisation", job.specialisation)}
            ${fact("Level", job.level)}
            ${job.minYears !== undefined || job.maxYears !== undefined ? fact("Experience", experienceText(job.minYears, job.maxYears) || null) : ""}
            ${fact("Type", job.type)}
            ${fact("Work mode", job.workMode)}
            ${fact("Education", job.educationMin)}
            ${fact("Posted", formatDate(job.postedAt))}
            ${fact("Closes", `${formatDate(job.closesAt)}${job.badge === "closing" ? ` (${job.label.replace(/^Closes /, "")})` : ""}`)}
          </dl>
        </aside>
      </div>
      <div class="jd-grid jo-grid">
        <section class="panel" aria-labelledby="jobSkillsTitle"><h2 id="jobSkillsTitle">Skills</h2>${skillsPanel}</section>
        ${certs || awards ? `<aside class="panel" aria-labelledby="credsTitle"><h2 id="credsTitle">Certifications and awards</h2>
          <h3 class="jd-sub">Required certifications</h3>${list(certs?.required)}
          <h3 class="jd-sub">Preferred certifications</h3>${list(certs?.preferred)}
          <h3 class="jd-sub">Preferred awards</h3>${list((awards?.preferred || []).map(awardLabel))}
        </aside>` : ""}
      </div>
    </div>`;
  bindPremiumLocks(root);
  paintMeters(root);
}

// ---------- Applications for one job (Feature 6 AC4, AC5; R5) ----------
export async function jobApplicationsView(root, ctx) {
  const id = ctx.params.id;
  const storeKey = "applicants";
  root.innerHTML = `<div class="dash">${backHtml("#/my-jobs", "My jobs")}<h1 class="sr-only">Job</h1>${loadingHtml("Loading applications…")}</div>`;
  const state = readListState(ctx.query, storeKey, JOB_SORTS);
  const status = Object.keys(STAGE_LABEL).includes(ctx.query.status) || ctx.query.status === "waiting" ? ctx.query.status : "";
  // The API has no status filter. A filter reads every page (50 at a time), keeps the matches and pages them here.
  let everything = null;
  const loadAll = async () => {
    if (everything) return everything;
    let items = [], job = null;
    for (let page = 1; page <= 20; page++) {
      const r = await api.recruiter.jobs.applications(id, { page, pageSize: 50, sort: "newest" });
      job = r.job;
      items = items.concat(r.items);
      if (page >= (r.page?.totalPages || 1)) break;
    }
    everything = { job, items };
    return everything;
  };
  const load = async ({ page, pageSize }) => {
    if (!status) return api.recruiter.jobs.applications(id, { page, pageSize, sort: "newest" });
    const all = await loadAll();
    const rows = status === "waiting" ? all.items.filter((a) => a.awaiting) : all.items.filter((a) => a.status === status);
    const totalPages = Math.max(1, Math.ceil(rows.length / pageSize));
    const p = Math.min(Math.max(1, page), totalPages);
    return { job: all.job, items: rows.slice((p - 1) * pageSize, p * pageSize), page: { page: p, pageSize, total: rows.length, totalPages } };
  };
  let res;
  try { res = await load(state); }
  catch (err) { root.innerHTML = failHtml("We can't find this job", err, backHtml("#/my-jobs", "My jobs")); return; }
  const job = res.job;
  document.title = `${job.title} — Jinder`;
  root.innerHTML = `
    <div class="dash">
      ${backHtml("#/my-jobs", "My jobs")}
      <div class="dash-head"><div><h1>${esc(job.title)}</h1><p class="dash-sub">${esc(job.location)} · ${esc(job.type)} · Closes ${esc(formatDate(job.closesAt))} ${badgeHtml(job)}</p></div>
        <div class="panel-actions"><a class="btn btn-secondary" href="#/my-jobs/${esc(job.id)}/overview">${icon("file")} Job overview</a><a class="btn btn-secondary" href="#/candidates?jobId=${esc(job.id)}">${icon("users")} Find talent</a><a class="btn btn-primary" href="#/my-jobs/${esc(job.id)}/edit">${icon("edit")} Edit job</a></div></div>
      <div class="grid-3">
        <div class="report-card"><div class="report-head"><span class="label">Applicants</span>${icon("users")}</div>${targetHtml(job)}</div>
        <div class="report-card"><div class="report-head"><span class="label">Waiting for you</span>${icon("clock")}</div><div class="num">${job.awaitingCount}</div><div class="meta">Applications that need an answer</div></div>
        <div class="report-card"><div class="report-head"><span class="label">Required skills</span>${icon("target")}</div><div class="job-tags">${job.skills.map((s) => `<span class="chip chip-neutral">${esc(s)}</span>`).join("")}</div></div>
      </div>
      <section class="panel" aria-labelledby="appsTitle">
        <div class="panel-head"><div><h2 id="appsTitle" tabindex="-1">Applications</h2><p class="muted">Talent profiles are anonymous. You see the alias and the translated skills. Newest first.</p></div>
          <label class="inline-field"><span>Show</span><select class="text-input" data-filter>
            <option value="">All</option><option value="waiting"${status === "waiting" ? " selected" : ""}>Waiting for you</option>
            ${Object.entries(STAGE_LABEL).map(([s, label]) => `<option value="${s}"${status === s ? " selected" : ""}>${esc(label)}</option>`).join("")}</select></label></div>
        <div data-list>${loadingHtml("Loading applications…")}</div>
        <div data-pager></div>
      </section>
    </div>`;
  const list = mountPagedList({
    listEl: root.querySelector("[data-list]"), pagerEl: root.querySelector("[data-pager]"), headingEl: root.querySelector("#appsTitle"),
    storeKey, state, sorts: JOB_SORTS, path: `/my-jobs/${id}`, base: () => ({ status }), noun: "applications", first: res,
    load,
    render: (r) => (r.items.length ? `<ul class="app-list">${r.items.map((a) => `
          <li class="app-row">
            <div class="app-main"><h3><a class="job-title-link" href="#/review/${esc(a.id)}">${esc(a.alias)}</a></h3>
              <p class="hint">${a.origin === "contacted" ? "You sent an invitation" : "Applied"} ${esc(formatDate(a.createdAt))} · Updated ${esc(formatDate(a.updatedAt))}</p></div>
            <div class="app-side">${ribbonHtml(a.status, a.statusLabel)}${a.awaiting ? `<span class="chip chip-yellow">${icon("clock")}Waiting for you</span>` : ""}${coverageMini(a.coverage, a.matched, a.total)}
              <a class="btn btn-secondary btn-sm" href="#/review/${esc(a.id)}">Review<span class="sr-only"> ${esc(a.alias)}</span></a></div>
          </li>`).join("")}</ul>` : `<div class="empty"><p>${status ? "No applications with this status." : "No applications yet. Invite talent, or wait for applications."}</p></div>`),
  });
  await list.show();
  root.querySelector("[data-filter]").addEventListener("change", (e) => ctx.navigate(`/my-jobs/${job.id}${e.target.value ? `?status=${e.target.value}` : ""}`));
}

// ---------- Review one application (Feature 6 AC6–AC9, AC11, AC12, AC14) ----------
const localNow = () => { const d = new Date(Date.now() + 36e5); d.setMinutes(d.getMinutes() - d.getTimezoneOffset()); return d.toISOString().slice(0, 16); };

export async function reviewView(root, ctx) {
  root.innerHTML = `<div class="dash">${backHtml("#/my-jobs", "My jobs")}<h1 class="sr-only">Review</h1>${loadingHtml("Loading application…")}</div>`;
  let app;
  try { app = await api.recruiter.applications.get(ctx.params.id); }
  catch (err) { root.innerHTML = failHtml("We can't find this application", err, backHtml("#/my-jobs", "My jobs")); return; }
  // The levels that the job needs (for the skill by skill table). If the job has none, the old list stays.
  const jobFull = await api.recruiter.jobs.get(app.job.id).catch(() => null);
  const reqs = reqsOf(jobFull);

  const render = (a, focus) => {
    document.title = `${a.snapshot.alias} · ${a.job.title} — Jinder`;
    const view = skillsViewHtml({ match: a.match, reqs, levels: levelMap(a.snapshot.skillLevels), hasLevels: Array.isArray(a.snapshot.skillLevels) && a.snapshot.skillLevels.length > 0 });
    root.innerHTML = `
      <div class="dash app-detail">
        ${backHtml(`#/my-jobs/${esc(a.job.id)}`, a.job.title)}
        <header class="dash-head"><div><h1>${esc(a.snapshot.alias)}</h1><p class="dash-sub">${esc(a.job.title)} · ${a.origin === "contacted" ? "You sent an invitation" : `Applied ${esc(formatDate(a.createdAt))}`}</p></div>${ribbonHtml(a.status, a.statusLabel)}</header>
        <section class="panel" aria-label="Progress">${stepperHtml(a)}</section>
        <div data-action></div>
        <div class="jd-grid">
          <section class="panel" aria-labelledby="pTitle">
            <h2 id="pTitle">Talent profile</h2>
            ${a.identity
              ? `<div class="identity">${icon("user-check")}<div><strong>${esc(a.identity.name)}</strong><span>${esc(a.identity.email)}</span><span class="hint">They agreed to share this for the interview.</span></div></div>`
              : `<div class="identity identity-anon">${icon("eye-off-small")}<div><strong>Anonymous</strong><span class="hint">They can share their name and email when they choose an interview time.</span></div></div>`}
            ${a.note ? `<h3 class="jd-sub">Their note</h3><p class="note-text">${esc(a.note)}</p>` : ""}
            ${talentProfileHtml(a.snapshot, { reqs, jobSkills: a.match.skills.map((s) => s.name) })}
          </section>
          <aside class="panel jd-match" aria-labelledby="sTitle">
            <h2 id="sTitle">Skills for this job</h2>
            ${view.aside}
          </aside>
        </div>
        ${view.wide}
        <section class="panel" aria-labelledby="hTitle"><h2 id="hTitle">History</h2>${historyHtml(a.history, { you: "recruiter" })}</section>
      </div>`;
    renderAction(a, root.querySelector("[data-action]"));
    if (focus) root.querySelector("[data-action] h2")?.focus();
  };

  const act = async (el, fn, msg) => {
    const alertEl = el.querySelector(".form-alert");
    el.querySelectorAll("button").forEach((b) => (b.disabled = true));
    try { app = await fn(); announce(msg); render(app, true); }
    catch (err) {
      el.querySelectorAll("button").forEach((b) => (b.disabled = false));
      const form = el.querySelector("form");
      if (!(form && applyFieldErrors(form, err.fields))) showAlert(alertEl, err.fields?.form || err.fields?.slots || err.message, "error");
    }
  };
  const confirmReject = (a) => openModal({
    title: "Mark as not selected?", intro: `${a.snapshot.alias} gets a notification and an email. You can't undo this.`, submitText: "Not selected", danger: true,
    async onSubmit() { app = await api.recruiter.applications.setStatus(a.id, { to: "rejected" }); announce("The application is closed."); render(app, true); return true; },
  });

  function renderAction(a, el) {
    const panel = (title, body, tone = "") => `<section class="panel action-panel ${tone}" aria-labelledby="actTitle"><h2 id="actTitle" tabindex="-1">${esc(title)}</h2><div class="form-alert" role="alert"></div>${body}</section>`;
    const rejectBtn = a.allowedNext.includes("rejected") ? `<button type="button" class="btn btn-ghost" data-reject>Not selected</button>` : "";
    const slotsForm = (title, intro) => panel(title, `
      <p class="muted">${esc(intro)}</p>
      <form novalidate data-slots>
        <div class="slot-inputs">${[1, 2, 3].map((n) => `<div class="field"><label for="slot-${n}">Time ${n}${n > 1 ? " (optional)" : ""}</label><input id="slot-${n}" name="slot${n}" type="datetime-local" class="text-input" min="${localNow()}"></div>`).join("")}</div>
        <input type="hidden" name="slots"><div class="field-error" data-for="slots"></div>
        <div class="form-actions">${rejectBtn}<button type="submit" class="btn btn-primary">${icon("calendar")} Send interview times</button></div>
      </form>`);
    const slot = a.slots.find((s) => s.id === a.chosenSlotId);

    if (a.status === "applied") {
      el.innerHTML = panel("New application", `<p class="muted">Start the review when you are ready. After that, they can't change the application.</p>
        <div class="form-actions">${rejectBtn}<button type="button" class="btn btn-primary" data-to="review">Start review</button></div>`, "tone-blue");
    } else if (a.status === "review" || a.status === "contacted") {
      el.innerHTML = slotsForm(a.status === "review" ? "Invite to an interview" : "Waiting for a reply", a.status === "review" ? "Offer 1 to 3 interview times. They choose one." : "You sent an invitation. Offer interview times, or close the invitation.");
    } else if (a.status === "interview" && !a.chosenSlotId) {
      el.innerHTML = panel("Waiting for them to choose a time", `<ul class="slot-list">${a.slots.map((s) => `<li>${icon("calendar")}${esc(slotText(s.start))}</li>`).join("")}</ul><div class="form-actions">${rejectBtn}</div>`, "tone-yellow");
    } else if (a.status === "interview" && !a.slotConfirmed) {
      el.innerHTML = panel("Confirm the interview time", `<p class="slot-confirmed">${icon("calendar")}<strong>${esc(slot ? slotText(slot.start) : "")}</strong></p>
        <p class="muted">${a.identity ? "They shared their name and email for the interview." : "They stay anonymous. Contact them through Jinder."}</p>
        <div class="form-actions">${rejectBtn}<button type="button" class="btn btn-primary" data-confirm>${icon("check")} Confirm time</button></div>`, "tone-yellow");
    } else if (a.status === "interview") {
      el.innerHTML = panel("Record the interview result", `<p class="slot-confirmed">${icon("calendar")}Interview: <strong>${esc(slot ? slotText(slot.start) : "")}</strong></p>
        <div class="form-actions">${rejectBtn}<button type="button" class="btn btn-primary" data-to="accepted">${icon("check")} Accept</button></div>`, "tone-green");
    } else if (a.status === "accepted") {
      el.innerHTML = panel("Send an offer", `<form novalidate data-offer>${textArea("offer", "Offer details", { hint: "Role, start date, salary and the next steps. Do not add personal contact details.", max: 1000, rows: 4 }).outerHTML}
        <div class="field-error" data-for="offer"></div>
        <div class="form-actions">${rejectBtn}<button type="submit" class="btn btn-primary">${icon("send")} Send offer</button></div></form>`, "tone-green");
    } else if (a.status === "offer") {
      el.innerHTML = panel("Waiting for an answer to the offer", `<blockquote class="note-text">${esc(a.offer?.text || "")}</blockquote><p class="hint">Sent ${esc(formatDate(a.offer?.sentAt || a.updatedAt))}</p>`, "tone-green");
    } else if (a.final) {
      const end = { confirmed: "They accepted your offer.", rejected: "This application is closed.", declined: "They declined your invitation." }[a.status];
      const theirs = a.feedback.theirs?.toOther ? `<h3 class="jd-sub">Their feedback</h3><blockquote class="note-text">${esc(a.feedback.theirs.toOther)}</blockquote>` : "";
      el.innerHTML = a.feedback.mine
        ? panel("Application finished", `<p class="muted">${esc(end)}</p>${theirs}<p class="hint">You sent feedback on ${esc(formatDate(a.feedback.mine.at))}. Thank you.</p>`)
        : panel("Application finished", `<p class="muted">${esc(end)}</p>${theirs}
          <form novalidate data-feedback>
            ${textArea("toOther", "Feedback to the talent (optional)", { hint: "Help them improve. They see this.", max: 1000 }).outerHTML}<div class="field-error" data-for="toOther"></div>
            ${textArea("toTeam", "Feedback to the Jinder team (optional)", { hint: "Only the Jinder team sees this.", max: 1000 }).outerHTML}<div class="field-error" data-for="toTeam"></div>
            <div class="form-actions"><button type="submit" class="btn btn-primary">${icon("send")} Send feedback</button></div>
          </form>`);
    }
    el.querySelector("[data-reject]")?.addEventListener("click", () => confirmReject(a));
    el.querySelector("[data-to]")?.addEventListener("click", (e) => act(el, () => api.recruiter.applications.setStatus(a.id, { to: e.currentTarget.dataset.to }), "The status is changed."));
    el.querySelector("[data-confirm]")?.addEventListener("click", () => act(el, () => api.recruiter.applications.confirmSlot(a.id), "The interview time is confirmed."));
    el.querySelector("[data-slots]")?.addEventListener("submit", (e) => {
      e.preventDefault();
      const f = e.target;
      clearErrors(f, el.querySelector(".form-alert"));
      const slots = [f.slot1.value, f.slot2.value, f.slot3.value].filter(Boolean).map((v) => new Date(v).toISOString());
      act(el, () => api.recruiter.applications.setStatus(a.id, { to: "interview", slots }), "The interview times are sent.");
    });
    el.querySelector("[data-offer]")?.addEventListener("submit", (e) => {
      e.preventDefault();
      clearErrors(e.target, el.querySelector(".form-alert"));
      act(el, () => api.recruiter.applications.setStatus(a.id, { to: "offer", offer: e.target.offer.value }), "The offer is sent.");
    });
    el.querySelector("[data-feedback]")?.addEventListener("submit", (e) => {
      e.preventDefault();
      clearErrors(e.target, el.querySelector(".form-alert"));
      act(el, () => api.recruiter.applications.feedback(a.id, { toOther: e.target.toOther.value, toTeam: e.target.toTeam.value }), "Thank you. Your feedback is sent.");
    });
  }

  render(app);
}

// ---------- Contact (Premium) ----------
async function openContact(cand, jobs, done) {
  const open = jobs.filter((j) => j.badge !== "closed");
  const sel = document.createElement("div");
  sel.className = "field";
  sel.innerHTML = `<label for="ct-job">Job</label><select id="ct-job" name="jobId" class="text-input">${open.map((j) => `<option value="${esc(j.id)}">${esc(j.title)}</option>`).join("")}</select>`;
  openModal({
    title: `Invite ${cand.alias}`,
    intro: "They get your message in Jinder. They stay anonymous until they agree to share their identity.",
    content: [sel, textArea("message", "Message", { hint: "10 to 500 characters. Do not add email addresses or phone numbers.", max: 500, rows: 4 })],
    submitText: "Send invitation",
    async onSubmit(form) {
      if (!open.length) throw new Error("Post an open job first.");
      const res = await api.recruiter.candidates.contact(cand.id, { jobId: form.jobId.value, message: form.message.value });
      announce(`Invitation sent to ${cand.alias}.`);
      done && done(res);
      return true;
    },
  });
}

// ---------- Compare entry points (R9): a check box for Premium, a lock badge for Basic ----------
const COMPARE_LOCK = "Comparing talent";
const INVITE_LOCK = "Inviting talent who did not apply";
const compareControlHtml = (c, canCompare) => (canCompare
  ? `<label class="check check-sm"><input type="checkbox" data-compare-pick="${esc(c.id)}" data-alias="${esc(c.alias)}"${compareStore.has("talent", c.id) ? " checked" : ""}><span>Compare<span class="sr-only"> ${esc(c.alias)}</span></span></label>`
  : `<button type="button" class="btn btn-ghost btn-sm" data-premium-lock="${COMPARE_LOCK}">Compare ${lockedBadgeHtml(COMPARE_LOCK, { static: true })}</button>`);
const inviteButtonHtml = (c, canContact) => (canContact
  ? `<button type="button" class="btn btn-ghost btn-sm" data-contact="${esc(c.id)}">${icon("send")}Invite<span class="sr-only"> ${esc(c.alias)}</span></button>`
  : `<button type="button" class="btn btn-ghost btn-sm" data-premium-lock="${INVITE_LOCK}">${icon("send")}Invite ${lockedBadgeHtml(INVITE_LOCK, { static: true })}</button>`);

/**
 * One check box (or one toggle button) for each talent card: add to the basket, remove from it, keep it in step with the basket bar.
 * @param {Element} scope  the element that holds the controls
 * @param {{ jobId: string, note?: Element }} o
 */
function bindCompare(scope, { jobId, note }) {
  const refuse = () => {
    const text = `You can compare up to ${COMPARE_MAX} profiles.`;
    if (note) note.textContent = text;
    announce(text);
  };
  scope.addEventListener("change", (e) => {
    const box = e.target.closest("[data-compare-pick]");
    if (!box || !scope.contains(box)) return;
    const id = box.dataset.comparePick;
    const alias = box.dataset.alias;
    if (box.checked) {
      // The job goes with the item as a hint for the compare page. It is a short id, not a person's data.
      if (!compareStore.add("talent", { id, alias, jobId })) { box.checked = false; return refuse(); }
      if (note) note.textContent = "";
      announce(`${alias} added to compare. ${compareStore.count("talent")} of ${COMPARE_MAX}.`);
    } else {
      compareStore.remove("talent", id);
      if (note) note.textContent = "";
      announce(`${alias} removed from compare.`);
    }
  });
  // The basket can change somewhere else (the bar, another tab). Keep the check boxes right. Stop when the screen is gone.
  const sync = () => {
    if (!scope.isConnected) return window.removeEventListener(COMPARE_EVENT, sync);
    scope.querySelectorAll("[data-compare-pick]").forEach((box) => { box.checked = compareStore.has("talent", box.dataset.comparePick); });
    scope.querySelectorAll("[data-compare-toggle]").forEach((btn) => paintToggle(btn));
  };
  window.addEventListener(COMPARE_EVENT, sync);
  return refuse;
}
function paintToggle(btn) {
  const on = compareStore.has("talent", btn.dataset.compareToggle);
  btn.setAttribute("aria-pressed", String(on));
  btn.querySelector("span").textContent = on ? "In compare list" : "Add to compare";
}

// ---------- Anonymous talent (Feature 5; R2, R5, R6, R9) ----------
function talentCardHtml(c, { job, ent }) {
  const levels = levelMap(c.skillLevels);
  const asked = new Set((job.skills || []).map(key));
  const ordered = [...c.skills.filter((s) => asked.has(key(s))), ...c.skills.filter((s) => !asked.has(key(s)))];   // skills that the job asks for come first
  const shownSkills = ordered.slice(0, 6);
  const creds = [
    ...(c.certifications || []).map((x) => ({ ic: "graduation", what: "Certification", text: credText(x) })),
    ...(c.awards || []).map((x) => ({ ic: "star", what: "Award", text: credText(x) })),
  ];
  const years = c.yearsExperience != null ? yearsText(c.yearsExperience) : c.years;
  const meta = [c.roles.map((r) => r.title).slice(0, 2).join(", ") || "No roles listed", c.locations?.length ? c.locations.slice(0, 2).join(", ") : ""].filter(Boolean);
  return `
    <li class="cand-card" data-card="${esc(c.id)}">
      <div class="cand-main">
        <h3><a class="job-title-link" href="#/candidates/${esc(c.id)}?jobId=${esc(job.id)}">${esc(c.alias)}</a>${c.applicationId ? ` <a class="chip chip-green chip-link" href="#/review/${esc(c.applicationId)}">In your pipeline</a>` : ""}</h3>
        <div class="cand-facts">
          ${c.level ? `<span class="chip chip-blue"><span class="sr-only">Level: </span>${esc(c.level)}</span>` : ""}
          ${years ? `<span class="chip chip-neutral"><span class="sr-only">Experience: </span>${esc(years)}</span>` : ""}
          ${c.updatedAt ? `<span class="hint cand-updated">${esc(updatedText(c.updatedAt))}</span>` : ""}
        </div>
        <p class="job-meta">${meta.map(esc).join(" · ")}</p>
        <div class="job-tags">${shownSkills.map((s) => {
          const lvl = levelText(levels.get(key(s)));
          const on = asked.has(key(s));
          return `<span class="chip ${on ? "chip-green" : "chip-neutral"}">${esc(s)}${lvl ? ` · ${esc(lvl)}` : ""}${on ? `<span class="sr-only"> (the job asks for this skill)</span>` : ""}</span>`;
        }).join("")}${ordered.length > 6 ? `<span class="hint">+${ordered.length - 6} more</span>` : ""}</div>
        ${creds.length ? `<div class="cand-creds" role="list" aria-label="Certifications and awards">${creds.slice(0, 3).map((x) => `<span class="chip chip-neutral cred-chip" role="listitem">${icon(x.ic)}<span class="sr-only">${x.what}: </span>${esc(x.text)}</span>`).join("")}${creds.length > 3 ? `<span class="hint" role="listitem">+${creds.length - 3} more</span>` : ""}</div>` : ""}
        <div class="card-actions">
          <button type="button" class="btn btn-ghost btn-sm bookmark-btn" data-save="${esc(c.id)}" aria-pressed="${c.saved}">${icon("bookmark")}<span>${c.saved ? "Saved" : "Save"}</span><span class="sr-only"> ${esc(c.alias)}</span></button>
          <button type="button" class="btn btn-ghost btn-sm" data-skip="${esc(c.id)}">${icon("eye-off-small")}Not for this job<span class="sr-only"> ${esc(c.alias)}</span></button>
          <button type="button" class="btn btn-ghost btn-sm" data-report="${esc(c.id)}" data-alias="${esc(c.alias)}">${icon("flag")}Report</button>
          ${c.applicationId ? "" : inviteButtonHtml(c, ent.canContact)}
          ${compareControlHtml(c, ent.canCompare)}
        </div>
      </div>
      <div class="job-score">${coverageMini(c.coverage, c.matched, c.total)}</div>
    </li>`;
}

export async function candidatesView(root, ctx) {
  const view = ctx.query.view === "saved" ? "saved" : "all";
  const storeKey = view === "saved" ? "talent-saved" : "talent";
  root.innerHTML = `
    <div class="dash">
      <div class="dash-head"><div><h1>Talent</h1><p class="dash-sub">Anonymous talent matched to your jobs, skill by skill. No names, photos or nationality.</p></div></div>
      <div data-body>${loadingHtml("Loading talent…")}</div>
    </div>`;
  bindPremiumLocks(root);
  const body = root.querySelector("[data-body]");
  const state = readListState(ctx.query, storeKey, TALENT_SORTS);
  let jobs, first, ent;
  try {
    [{ items: jobs }, first, ent] = await Promise.all([
      api.recruiter.jobs.list({ pageSize: 50 }),
      api.recruiter.candidates.list({ jobId: ctx.query.jobId || "", view, page: state.page, pageSize: state.pageSize, sort: state.sort }),
      api.entitlements.get(),
    ]);
  } catch (err) { body.innerHTML = `<div class="empty" role="alert"><p>${esc(err.message)}</p></div>`; return; }
  if (!first.job) {
    body.innerHTML = `<section class="panel"><div class="empty"><div class="icon-tile accent">${icon("briefcase")}</div><p>Post a job first. Then we show talent whose skills fit it.</p><a class="btn btn-primary" href="#/my-jobs/new">Post a job</a></div></section>`;
    return;
  }
  const job = first.job;
  const jobId = job.id;
  const href = (o) => `#/candidates?${new URLSearchParams({ jobId, view, ...o })}`;

  body.innerHTML = `
    <div class="toolbar list-toolbar">
      <label class="inline-field"><span>Job</span><select class="text-input" data-job>${jobs.map((j) => `<option value="${esc(j.id)}"${j.id === jobId ? " selected" : ""}>${esc(j.title)}${j.badge === "closed" ? " (closed)" : ""}</option>`).join("")}</select></label>
      <a class="text-link job-overview-link" href="#/my-jobs/${esc(jobId)}/overview">${icon("file")} Job overview<span class="sr-only"> for ${esc(job.title)}</span></a>
      <div class="tabs" role="tablist" aria-label="Talent">
        <a role="tab" class="tab" href="${href({ view: "all" })}" aria-selected="${view === "all"}">All</a>
        <a role="tab" class="tab" href="${href({ view: "saved" })}" aria-selected="${view === "saved"}">Saved</a>
      </div>
      ${sortSelectHtml({ id: "talent-sort", value: state.sort, options: TALENT_SORTS })}
    </div>
    <p class="muted" role="status">Required skills: ${job.skills.map((s) => `<span class="chip chip-neutral">${esc(s)}</span>`).join(" ")}</p>
    <p class="hint compare-note" data-compare-note role="status"></p>
    <section class="panel" aria-labelledby="talentListTitle">
      <h2 class="sr-only" id="talentListTitle" tabindex="-1">${view === "saved" ? "Saved talent" : "Talent list"}</h2>
      <div data-list>${loadingHtml("Loading talent…")}</div>
      <div data-pager></div>
      <div data-foot></div>
    </section>`;
  const cardCtx = { job, ent };
  const listEl = body.querySelector("[data-list]");
  const foot = body.querySelector("[data-foot]");
  const list = mountPagedList({
    listEl, pagerEl: body.querySelector("[data-pager]"), headingEl: body.querySelector("#talentListTitle"),
    storeKey, state, sorts: TALENT_SORTS, path: "/candidates", base: { jobId, view: view === "saved" ? "saved" : "" }, noun: "talent profiles", first,
    load: (p) => api.recruiter.candidates.list({ jobId, view, ...p }),
    render: (res) => (res.items.length
      ? `<ul class="cand-list">${res.items.map((c) => talentCardHtml(c, cardCtx)).join("")}</ul>`
      : `<div class="empty"><p>${view === "saved" ? "No saved talent for this job." : "No talent matches this job yet."}</p></div>`),
    after: (res) => {
      // A Basic employer sees the top few only. The gold box says so and the lock badge opens the Premium dialog.
      foot.innerHTML = `${res.limitedTo && res.total > res.limitedTo ? upgradeBoxHtml(`You see the top ${res.limitedTo} of ${res.total} talent profiles. Premium shows all of them.`, "The full talent list") : ""}
        ${res.skippedCount ? `<p class="hint">${res.skippedCount} hidden ${res.skippedCount === 1 ? "profile" : "profiles"}. <button type="button" class="text-link link-btn" data-unskip>Show them again</button></p>` : ""}`;
    },
  });
  await list.show();

  body.querySelector("[data-job]").addEventListener("change", (e) => ctx.navigate(`/candidates?${new URLSearchParams({ jobId: e.target.value, view })}`));
  bindSort(body, "talent-sort", (value) => {
    state.sort = value;
    state.page = 1;
    list.reload({ push: true, say: `Sorted by ${TALENT_SORTS.find((s) => s.value === value).label.toLowerCase()}.` });
  });
  foot.addEventListener("click", async (e) => {
    if (!e.target.closest("[data-unskip]")) return;
    await api.recruiter.candidates.clearSkipped();
    state.page = 1;
    list.reload({ push: true });
  });
  if (ent.canCompare) bindCompare(body, { jobId, note: body.querySelector("[data-compare-note]") });

  body.addEventListener("click", async (e) => {
    const t = e.target.closest("[data-save],[data-skip],[data-report],[data-contact]");
    if (!t || !body.contains(t)) return;
    const id = t.dataset.save || t.dataset.skip || t.dataset.report || t.dataset.contact;
    const card = { id, alias: t.closest(".cand-card")?.querySelector("h3 a")?.textContent || "this profile" };
    if (t.dataset.report) return openReport("candidate", card.id, card.alias);
    if (t.dataset.contact) return openContact(card, jobs, () => ctx.navigate(`/candidates?${new URLSearchParams({ jobId, view })}`));
    t.disabled = true;
    try {
      if (t.dataset.save) {
        const on = t.getAttribute("aria-pressed") !== "true";
        await (on ? api.recruiter.candidates.save(card.id) : api.recruiter.candidates.unsave(card.id));
        t.setAttribute("aria-pressed", String(on));
        t.querySelector("span").textContent = on ? "Saved" : "Save";
        announce(on ? `${card.alias} saved.` : `${card.alias} removed from saved.`);
      } else {
        await api.recruiter.candidates.skip(card.id);
        t.closest(".cand-card").replaceWith(Object.assign(document.createElement("li"), { className: "job-card job-card-hidden", textContent: `${card.alias} is hidden for your jobs.` }));
        announce(`${card.alias} is hidden.`);
      }
    } catch (err) { announce(err.message); }
    finally { t.disabled = false; }
  });
}

// ---------- Talent detail (R2) ----------
export async function candidateDetailView(root, ctx) {
  const back = backHtml(`#/candidates${ctx.query.jobId ? `?jobId=${encodeURIComponent(ctx.query.jobId)}` : ""}`, "Talent");
  root.innerHTML = `<div class="dash">${back}<h1 class="sr-only">Talent profile</h1>${loadingHtml("Loading profile…")}</div>`;
  let c, jobs;
  try { [c, { items: jobs }] = await Promise.all([api.recruiter.candidates.get(ctx.params.id, ctx.query.jobId || ""), api.recruiter.jobs.list({ pageSize: 50 })]); }
  catch (err) { root.innerHTML = failHtml("We can't find this profile", err, back); return; }
  // The levels that the job needs. A job from older data has none: then the old skill list stays.
  const jobFull = c.job?.id ? await api.recruiter.jobs.get(c.job.id).catch(() => null) : null;
  if (!root.isConnected) return;
  const reqs = reqsOf(jobFull);
  const skillView = skillsViewHtml({ match: c.match, reqs, levels: levelMap(c.skillLevels), hasLevels: Array.isArray(c.skillLevels) && c.skillLevels.length > 0 });
  const jobId = c.job?.id || ctx.query.jobId || "";
  const canCompare = c.entitlements.canCompare;
  document.title = `${c.alias} — Jinder`;
  root.innerHTML = `
    <div class="dash">
      ${back}
      <header class="dash-head"><div><h1>${esc(c.alias)}</h1><p class="dash-sub">Anonymous profile${c.job ? ` · matched to ${esc(c.job.title)}` : ""}</p>${c.updatedAt ? `<p class="hint cand-updated">${esc(updatedText(c.updatedAt))}</p>` : ""}</div>
        <div class="panel-actions">
          <button type="button" class="btn btn-secondary bookmark-btn" data-save aria-pressed="${c.saved}">${icon("bookmark")}<span>${c.saved ? "Saved" : "Save"}</span></button>
          ${c.applicationId ? `<a class="btn btn-primary" href="#/review/${esc(c.applicationId)}">Review application</a>`
            : c.entitlements.canContact ? `<button type="button" class="btn btn-primary" data-contact>${icon("send")} Invite</button>`
              : `<button type="button" class="btn btn-primary" data-premium-lock="${INVITE_LOCK}">${icon("send")} Invite ${lockedBadgeHtml(INVITE_LOCK, { static: true })}</button>`}
          ${canCompare
            ? `<button type="button" class="btn btn-secondary" data-compare-toggle="${esc(c.id)}" aria-pressed="false">${icon("columns")}<span>Add to compare</span></button>`
            : `<button type="button" class="btn btn-secondary" data-premium-lock="${COMPARE_LOCK}">${icon("columns")} Compare ${lockedBadgeHtml(COMPARE_LOCK, { static: true })}</button>`}
          <button type="button" class="btn btn-ghost" data-report>${icon("flag")}Report</button>
        </div></header>
      <p class="hint compare-note" data-compare-note role="status"></p>
      <div class="jd-grid">
        <section class="panel" aria-labelledby="pfTitle"><h2 id="pfTitle">Profile</h2>
          ${talentProfileHtml(c, { reqs, jobSkills: c.job ? (jobFull?.skills || c.match.skills.map((s) => s.name)) : [] })}
          <p class="hint">${icon("shield")} Name, contact details, photo, nationality and the CV are never shown. They decide when to share their identity.</p>
        </section>
        <aside class="panel jd-match" aria-labelledby="smTitle"><h2 id="smTitle">Skills for ${esc(c.job?.title || "your job")}</h2>
          ${skillView.aside}</aside>
      </div>
      ${skillView.wide}
    </div>`;
  bindPremiumLocks(root);
  const save = root.querySelector("[data-save]");
  save.addEventListener("click", async () => {
    const on = save.getAttribute("aria-pressed") !== "true";
    save.disabled = true;
    try { await (on ? api.recruiter.candidates.save(c.id) : api.recruiter.candidates.unsave(c.id)); save.setAttribute("aria-pressed", String(on)); save.querySelector("span").textContent = on ? "Saved" : "Save"; announce(on ? "Saved." : "Removed from saved."); }
    catch (err) { announce(err.message); } finally { save.disabled = false; }
  });
  root.querySelector("[data-report]").addEventListener("click", () => openReport("candidate", c.id, c.alias));
  root.querySelector("[data-contact]")?.addEventListener("click", () => openContact(c, jobs, (app) => ctx.navigate(`/review/${app.id}`)));
  const toggle = root.querySelector("[data-compare-toggle]");
  if (toggle) {
    const note = root.querySelector("[data-compare-note]");
    paintToggle(toggle);
    toggle.addEventListener("click", () => {
      if (compareStore.has("talent", c.id)) { compareStore.remove("talent", c.id); note.textContent = ""; announce(`${c.alias} removed from compare.`); }
      else if (compareStore.add("talent", { id: c.id, alias: c.alias, jobId })) { note.textContent = ""; announce(`${c.alias} added to compare. ${compareStore.count("talent")} of ${COMPARE_MAX}.`); }
      else { const text = `You can compare up to ${COMPARE_MAX} profiles.`; note.textContent = text; announce(text); }
      paintToggle(toggle);
    });
    const sync = () => { if (!toggle.isConnected) return window.removeEventListener(COMPARE_EVENT, sync); paintToggle(toggle); };
    window.addEventListener(COMPARE_EVENT, sync);
  }
}
