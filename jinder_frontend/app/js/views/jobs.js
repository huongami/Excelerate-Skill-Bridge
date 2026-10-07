// Candidate job screens: Jobs ("/jobs"), Job detail ("/jobs/:id") and Bookmarks ("/bookmarks") — Feature 3.
// V2: lists have a sort and a pager (R5, R6). The detail shows level, experience, work mode, certifications, awards and
// the full job description in a scroll box (R2, R4). Compare goes through the basket and the page "#/compare" (R9).
import { iconHtml as icon, esc, announce } from "../core/dom.js";
import { api } from "../api/index.js";
import {
  jobCardHtml, paintMeters, bindBookmarks, bindJobActions, bindCompare, bookmarkButton, datesHtml, coverageHtml, fitScoreHtml, openReport,
  createPagedList, experienceText, compareAvailable, addJobToCompare,
} from "../components/job-card.js";
import { searchBarHtml, bindSearchBar } from "../components/search-bar.js";
import { skillMatchHtml } from "../components/status.js";
import { bridgeHtml } from "../components/bridge.js";
import { jdViewHtml } from "../components/jd-view.js";
import { compareStore, COMPARE_EVENT } from "../core/compare-store.js";
import { COMPARE_MAX } from "../data/levels.js";
import { AWARD_KINDS } from "../data/reference.js";

const loadingHtml = (text = "Loading jobs…") => `<div class="empty" role="status"><p>${esc(text)}</p></div>`;
const errorHtml = (text) => `<div class="empty" role="alert"><p>${esc(text)}</p></div>`;
const setText = (el, text) => { if (el && el.textContent !== text) el.textContent = text; };

// The sort values are the ones of the API (plan section 5.1). The first one of each list is the default.
export const JOB_SORTS = [{ value: "best", label: "Best match" }, { value: "newest", label: "Newest posted" }];
export const BOOKMARK_SORTS = [{ value: "saved", label: "Recently saved" }, { value: "best", label: "Best match" }, { value: "newest", label: "Newest posted" }];

// ---------- Jobs: search all open jobs ----------
export async function jobsView(root, ctx) {
  const q = (ctx.query.q || "").slice(0, 100);
  const location = ctx.query.location || "";
  root.innerHTML = `
    <div class="dash">
      <div class="dash-head"><div><h1>Jobs</h1><p class="dash-sub">Search all open jobs. Each job shows which of its skills you have.</p></div></div>
      ${searchBarHtml({ q, location })}
      <section class="panel recs" aria-labelledby="resultsTitle">
        <div class="panel-head"><div><h2 id="resultsTitle" tabindex="-1">Results</h2><p class="muted" data-count role="status"></p></div></div>
        <div class="list-toolbar" data-sort></div>
        <div data-list>${loadingHtml()}</div>
        <div data-pager></div>
      </section>
    </div>`;
  bindSearchBar(root, ctx.navigate);
  const list = root.querySelector("[data-list]");
  const count = root.querySelector("[data-count]");
  bindBookmarks(list);
  bindJobActions(list);
  bindCompare(list);

  const ctl = createPagedList({
    key: "jobs", query: ctx.query, sorts: JOB_SORTS, sortId: "jobs-sort",
    sortHost: root.querySelector("[data-sort]"), pagerHost: root.querySelector("[data-pager]"), listHost: list, focusHost: root.querySelector("#resultsTitle"),
    fetchPage: (p) => api.jobs.search({ q, location, ...p }),
    onLoading: () => { list.innerHTML = loadingHtml(); },
    onError: (err) => { setText(count, ""); list.innerHTML = errorHtml(err.message || "We couldn't load jobs. Try again later."); },
    render(res, st) {
      const total = res.page?.total ?? res.total ?? res.items.length;
      const where = [q && `for “${q}”`, location && `in ${location}`].filter(Boolean).join(" ");
      setText(count, `${total} open ${total === 1 ? "job" : "jobs"}${where ? ` ${where}` : ""}. ${st.sort === "newest" ? "Newest first." : "Best fit first."}`);
      if (!res.items.length) {
        list.innerHTML = `<div class="empty"><div class="icon-tile accent">${icon("search")}</div><p>No open jobs match your search. Try a different word or location.</p><a href="#/jobs" class="btn btn-secondary">Show all jobs</a></div>`;
        return;
      }
      list.innerHTML = `<ul class="job-list">${res.items.map((j) => jobCardHtml(j)).join("")}</ul>`;
      paintMeters(list);
    },
  });
  await ctl.start();
}

// ---------- Job detail (Feature 3 AC7, AC8, AC9, AC14) ----------
const awardLabel = (kind) => AWARD_KINDS.find((a) => a.kind === kind)?.label || String(kind);

// "Job facts": Level, Experience, Work mode, Place, Type, Salary and Education. A fact that the job does not have is left out.
function factsHtml(job) {
  const facts = [
    ["Level", job.level],
    ["Experience", experienceText(job.minYears, job.maxYears)],
    ["Work mode", job.workMode],
    ["Place", job.area || job.location],
    ["Type", job.type],
    ["Salary", job.salary],
    ["Education", job.educationMin],
  ].filter(([, v]) => v);
  return `<dl class="fact-grid">${facts.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join("")}</dl>`;
}

// Certifications (Required and Preferred) and Awards (Preferred). They show only for a job that has the V2 data.
function credentialsHtml(job) {
  const certs = job.certifications || {};
  const required = certs.required || [], preferred = certs.preferred || [], awards = (job.awards || {}).preferred || [];
  const hasData = !!(job.level || (job.skillRequirements || []).length || required.length || preferred.length || awards.length);
  if (!hasData) return "";
  const group = (label, items, fmt = (x) => x) => (items.length
    ? `<div class="cred-group"><p class="cred-label">${label}</p><ul class="cred-list">${items.map((x) => `<li><span class="chip chip-neutral">${esc(fmt(x))}</span></li>`).join("")}</ul></div>` : "");
  const none = (text) => `<p class="muted cred-none">${text}</p>`;
  return `
    <h3 class="jd-sub" id="certTitle">Certifications</h3>
    ${required.length || preferred.length ? group("Required", required) + group("Preferred", preferred) : none("This job does not ask for a certification.")}
    <h3 class="jd-sub" id="awardTitle">Awards</h3>
    ${awards.length ? group("Preferred", awards, awardLabel) : none("This job does not ask for an award.")}`;
}

export async function jobDetailView(root, ctx) {
  root.innerHTML = `<div class="dash"><button type="button" class="back-link" data-back>${icon("chevron-left")}Back</button><h1 class="sr-only">Job detail</h1>${loadingHtml("Loading job…")}</div>`;
  const back = () => (history.length > 1 ? history.back() : ctx.navigate("/jobs"));
  root.querySelector("[data-back]").addEventListener("click", back);

  let job;
  try {
    job = await api.jobs.get(ctx.params.id);
  } catch (err) {
    root.innerHTML = `<div class="dash"><div class="dash-head"><div><h1>We can't find this job</h1><p class="dash-sub">${esc(err.message || "This job does not exist or was removed.")}</p></div></div>
      <section class="panel"><div class="empty"><div class="icon-tile accent">${icon("search")}</div><a href="#/jobs" class="btn btn-primary">Browse jobs</a></div></section></div>`;
    return;
  }
  document.title = `${job.title} — Jinder`;
  const m = job.match || { coverage: null, skills: [], reasons: [], gaps: [], notes: [] };
  const hasProfile = !!(ctx.user.profile && ctx.user.onboarding === "done");
  const closed = job.status === "closed";
  const similar = job.similar || [];
  const canCompare = compareAvailable();

  // Apply action: open → the review step; applied → tracking; closed → disabled
  const apply = job.applicationId
    ? `<a class="btn btn-primary btn-lg" href="#/applications/${esc(job.applicationId)}">${icon("check")} Applied · Track status</a>`
    : closed
      ? `<button type="button" class="btn btn-primary btn-lg" disabled aria-describedby="applyHint">Apply</button><p class="hint" id="applyHint">This job is closed. You can't apply now.</p>`
      : `<a class="btn btn-primary btn-lg" href="#/jobs/${esc(job.id)}/apply">${icon("send")} Apply</a>`;

  root.innerHTML = `
    <div class="dash job-detail">
      <button type="button" class="back-link" data-back>${icon("chevron-left")}Back</button>
      <header class="jd-head">
        <div class="jd-title">
          <div class="job-tags">
            <span class="chip chip-neutral">${esc(job.category)}${job.specialisation ? ` · ${esc(job.specialisation)}` : ""}</span>
            ${job.anzsco ? `<span class="chip chip-blue" title="Australian occupation code">ANZSCO ${esc(job.anzsco)}${job.occupation ? ` · ${esc(job.occupation)}` : ""}</span>` : ""}
          </div>
          <h1>${esc(job.title)}</h1>
          <p class="job-meta">${esc(job.company)} · ${icon("map-pin")}${esc(job.area || job.location)} · ${esc(job.type)} · ${esc(job.salary)}</p>
          <div class="job-tags">${datesHtml(job)}</div>
        </div>
        <div class="jd-actions">
          ${apply}
          ${bookmarkButton(job, { withText: true })}
          ${canCompare ? `<button type="button" class="btn btn-secondary compare-btn" data-compare-detail aria-pressed="false" title="Add to compare">${icon("columns")}<span>Compare</span>${icon("check")}</button>` : ""}
          ${job.applicationId ? "" : `<button type="button" class="btn btn-ghost" data-skip-detail>${icon("eye-off-small")}Not for me</button>`}
          <button type="button" class="btn btn-ghost" data-report-detail>${icon("flag")}Report</button>
        </div>
      </header>

      <div class="jd-grid">
        <div class="jd-main">
          <section class="panel" aria-labelledby="factsTitle">
            <h2 id="factsTitle">Job facts</h2>
            ${factsHtml(job)}
            ${credentialsHtml(job)}
          </section>
          <section class="panel jd-about" aria-labelledby="aboutTitle">
            <h2 id="aboutTitle">About the role</h2>
            ${jdViewHtml(job.description || job.summary || "", { label: "Job description" })}
          </section>
        </div>

        <aside class="panel jd-match" aria-labelledby="matchTitle">
          <h2 id="matchTitle">Your skills for this job</h2>
          ${hasProfile ? `
            <div class="jd-score">${coverageHtml(m)}</div>
            <p class="jd-fit">${fitScoreHtml(m)}</p>
            <h3 class="jd-sub">Skill by skill</h3>
            ${skillMatchHtml(m.skills)}
            <h3 class="jd-sub">Why it fits</h3>
            ${(m.reasons || []).length || (m.notes || []).length ? `<ul class="why">${m.reasons.map((r) => `<li>${icon("check")}${esc(r)}</li>`).join("")}${(m.notes || []).map((n) => `<li class="note">${icon("alert")}${esc(n)}</li>`).join("")}</ul>` : `<p class="muted">This job is not close to your goals yet.</p>`}
          ` : `
            <div class="empty"><div class="icon-tile accent">${icon("target")}</div><p>Complete your profile to see how your skills match this job.</p><a href="#/home" class="btn btn-primary">Complete your profile</a></div>`}
        </aside>
      </div>

      ${hasProfile ? bridgeHtml(job.bridge) : ""}

      <section class="panel recs" aria-labelledby="similarTitle">
        <div class="panel-head"><h2 id="similarTitle">Similar jobs</h2>${canCompare && similar.length ? `<button type="button" class="btn btn-secondary btn-sm" data-compare-similar>${icon("columns")} Compare with these jobs</button>` : ""}</div>
        ${similar.length ? `<ul class="job-list">${similar.map((j) => jobCardHtml(j, { compact: true })).join("")}</ul>` : `<p class="muted">No similar open jobs right now.</p>`}
      </section>
    </div>`;
  root.querySelector("[data-back]").addEventListener("click", back);
  paintMeters(root);
  const detail = root.querySelector(".job-detail");
  bindBookmarks(detail);
  bindCompare(detail);
  root.querySelector("[data-report-detail]").addEventListener("click", () => openReport("job", job.id, job.title));
  root.querySelector("[data-skip-detail]")?.addEventListener("click", async (e) => {
    const btn = e.currentTarget;
    btn.disabled = true;
    try { await api.jobs.skip(job.id); announce(`${job.title} is hidden from your recommendations.`); ctx.navigate("/jobs"); }
    catch (err) { btn.disabled = false; announce(err.message); }
  });

  // Compare button: adds this job to the basket, or takes it out again
  const cmp = root.querySelector("[data-compare-detail]");
  if (cmp) {
    const paint = () => cmp.setAttribute("aria-pressed", String(compareStore.has("job", job.id)));
    paint();
    cmp.addEventListener("click", () => {
      if (compareStore.has("job", job.id)) { compareStore.remove("job", job.id); announce(`${job.title} is removed from compare.`); }
      else if (addJobToCompare(job)) announce(`${job.title} is added to compare.`);
      paint();
    });
    const onBasket = () => { if (!cmp.isConnected) return window.removeEventListener(COMPARE_EVENT, onBasket); paint(); };
    window.addEventListener(COMPARE_EVENT, onBasket);
  }
  // "Compare with these jobs": this job and the similar ones go to the basket (the most is 5), then the compare page opens
  root.querySelector("[data-compare-similar]")?.addEventListener("click", () => {
    const all = [job, ...similar].slice(0, COMPARE_MAX);
    let added = 0;
    for (const j of all) {
      if (compareStore.has("job", j.id) || compareStore.add("job", { id: j.id, title: j.title })) added += 1;
      else break;
    }
    if (added < all.length) announce(`${added} of ${all.length} jobs are in compare. You can compare up to ${COMPARE_MAX} jobs.`);
    ctx.navigate("/compare");
  });
}

// ---------- Bookmarks (Feature 3 AC10) ----------
export async function bookmarksView(root, ctx) {
  root.innerHTML = `
    <div class="dash">
      <div class="dash-head"><div><h1>Bookmarks</h1><p class="dash-sub">Jobs you saved for later.</p></div><a href="#/jobs" class="btn btn-secondary btn-lg">${icon("search")} Browse jobs</a></div>
      <section class="panel recs" aria-labelledby="savedTitle">
        <div class="panel-head"><div><h2 id="savedTitle" tabindex="-1">Saved jobs</h2><p class="muted" data-count role="status"></p></div></div>
        <div class="list-toolbar" data-sort></div>
        <div data-list>${loadingHtml()}</div>
        <div data-pager></div>
      </section>
    </div>`;
  const list = root.querySelector("[data-list]");
  const count = root.querySelector("[data-count]");
  const order = { saved: "Recently saved first.", best: "Best fit first.", newest: "Newest first." };

  const ctl = createPagedList({
    key: "bookmarks", query: ctx.query, sorts: BOOKMARK_SORTS, sortId: "bookmarks-sort",
    sortHost: root.querySelector("[data-sort]"), pagerHost: root.querySelector("[data-pager]"), listHost: list, focusHost: root.querySelector("#savedTitle"),
    fetchPage: (p) => api.bookmarks.list(p),
    onLoading: () => { list.innerHTML = loadingHtml(); },
    onError: (err) => { setText(count, ""); list.innerHTML = errorHtml(err.message || "We couldn't load your bookmarks. Try again later."); },
    render(res, st) {
      const total = res.page?.total ?? res.items.length;
      if (!res.items.length) {
        setText(count, "");
        list.innerHTML = `<div class="empty"><div class="icon-tile accent">${icon("bookmark")}</div><p>No saved jobs yet. Save a job to compare it later.</p><a href="#/jobs" class="btn btn-primary">Browse jobs</a></div>`;
        return;
      }
      setText(count, `${total} saved ${total === 1 ? "job" : "jobs"}. ${order[st.sort] || ""}`.trim());
      list.innerHTML = `<ul class="job-list">${res.items.map((j) => jobCardHtml(j)).join("")}</ul>`;
      paintMeters(list);
    },
  });

  // Removing a bookmark here removes the card. Then the page loads again, so that the next job moves up and the count is right.
  bindBookmarks(list, (id, saved) => {
    if (saved) return;
    list.querySelector(`[data-bookmark="${CSS.escape(id)}"]`)?.closest(".job-card")?.remove();
    ctl.reload();
  });
  bindJobActions(list);
  bindCompare(list);
  await ctl.start();
}
