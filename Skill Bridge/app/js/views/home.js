// Talent Home ("/home"), inside the app shell. An employer gets the employer Home (views/recruiter.js).
import { iconHtml as icon, esc, toList, formatDate } from "../core/dom.js";
import { api } from "../api/index.js";
import { openOnboarding } from "../components/onboarding.js";
import { jobCardHtml, paintMeters, bindBookmarks, bindJobActions, bindCompare } from "../components/job-card.js";
import { barChartHtml, upgradeHtml } from "../components/charts.js";
import { searchBarHtml, bindSearchBar } from "../components/search-bar.js";
import { sharedFactsHtml, skillChipsHtml } from "../components/profile-card.js";
import { recruiterHomeView } from "./recruiter.js";
import { fetchAllApplications } from "./applications.js";

const RECS_SHOWN = 5;   // the widget shows the 5 best jobs and has no pager (the Jobs screen has the full list)

const STAGE_LABEL = { applied: "Applied", contacted: "Contacted", review: "In review", interview: "Interview", accepted: "Accepted", offer: "Offer" };
const MAX_SKILL_CHIPS = 8;

export async function homeView(root, ctx) {
  if (ctx.user.role === "recruiter") return recruiterHomeView(root, ctx);
  root.innerHTML = `
    <div class="dash">
      <div class="dash-head">
        <div>
          <h1 data-greeting></h1>
          <p class="dash-sub" data-subline></p>
        </div>
        <button type="button" class="btn btn-primary btn-lg" data-primary></button>
      </div>

      <section class="panel activity" aria-labelledby="actTitle">
        <div class="panel-head"><div><h2 id="actTitle">Your activity</h2><p class="muted">Your active applications and what employers see. Never a score on you.</p></div></div>
        <div class="activity-grid">
          <div data-active><div class="empty" role="status"><p>Loading…</p></div></div>
          <div data-shared><div class="empty" role="status"><p>Loading…</p></div></div>
        </div>
      </section>

      ${searchBarHtml()}

      <section class="panel recs" aria-labelledby="recsTitle">
        <div class="panel-head">
          <div>
            <h2 id="recsTitle">Recommended for you</h2>
            <p class="muted" data-recs-sub></p>
          </div>
          <div class="panel-actions">
            <span class="chip chip-neutral" data-recs-source>Loading jobs…</span>
            <button type="button" class="btn btn-secondary" data-edit-prefs>Edit preferences</button>
          </div>
        </div>
        <div data-recs-list></div>
      </section>

      <section class="panel" aria-labelledby="insTitle">
        <div class="panel-head"><div><h2 id="insTitle">Skill insights</h2><p class="muted">From the open jobs that fit you best.</p></div></div>
        <div data-insights><div class="empty" role="status"><p>Loading…</p></div></div>
      </section>

      <div class="dash-grid" data-setup>
        <section class="panel" aria-labelledby="stepsTitle">
          <h2 id="stepsTitle">Get set up</h2>
          <p class="muted" data-steps-sub></p>
          <ol class="steps" data-steps></ol>
        </section>
        <aside class="letter-card">
          <div class="icon-tile accent on-canvas">${icon("shield")}</div>
          <h2>Explainable by design</h2>
          <p>You'll see exactly why each job is recommended. We never use your nationality, age, gender or visa status to match you.</p>
        </aside>
      </div>
    </div>`;

  const $ = (k) => root.querySelector(`[data-${k}]`);
  bindSearchBar(root, ctx.navigate);
  bindBookmarks($("recs-list"));
  bindJobActions($("recs-list"));
  bindCompare($("recs-list"));

  // Recommendations: { items, source } or null while loading
  let recs = null;
  const open = (start) => openOnboarding({ user: ctx.user, start, done: refresh });

  async function refresh() {
    ctx.user = await api.me.get();
    if (!root.isConnected || !$("greeting")) return;   // the talent left the Home while the profile loaded
    recs = null;
    render();
    renderActivity();
    renderInsights();
    await loadRecs();
  }
  async function loadRecs() {
    try { recs = await api.jobs.recommended({ pageSize: RECS_SHOWN, sort: "best" }); }
    catch { recs = { items: [], source: null, error: true }; }
    if (root.isConnected) render();
  }

  function render() {
    const me = ctx.user;
    const p = me.profile || {};
    const targets = toList(p.targetRole).join(", ");
    const hasProfile = me.onboarding === "done" && !!targets;

    $("greeting").textContent = `Welcome, ${me.name.split(" ")[0]}`;
    $("subline").textContent = `Talent workspace · Employers see you as ${me.alias || "your alias"}`;
    const action = $("primary");
    action.innerHTML = `${icon("upload")} ${me.cv ? "Update CV" : "Upload CV"}`;
    action.onclick = () => open("cv");

    renderRecs(me, hasProfile, targets, recs?.items || []);
    renderSteps(me, hasProfile);
  }

  function renderRecs(me, hasProfile, targets, items) {
    const src = recs?.source;
    $("recs-source").textContent = !recs ? "Loading jobs…"
      : src ? `${src.openCount} open jobs${src.updatedAt ? ` · updated ${formatDate(src.updatedAt)}` : ""}` : "Jobs unavailable";
    const edit = $("edit-prefs");
    edit.onclick = () => open("goals");
    edit.hidden = !hasProfile;
    const list = $("recs-list");
    const sub = $("recs-sub");

    if (!hasProfile) {
      sub.textContent = "Tell us what you're looking for and we'll suggest jobs that fit.";
      list.innerHTML = `<div class="empty"><div class="icon-tile accent">${icon("target")}</div><p>No recommendations yet.</p><button type="button" class="btn btn-primary" data-recs-start>Complete your profile</button></div>`;
      list.querySelector("[data-recs-start]").onclick = () => open(me.cv ? "questions" : "cv");
    } else if (!recs) {
      sub.textContent = `For: ${targets}`;
      list.innerHTML = `<div class="empty" role="status"><p>Loading jobs…</p></div>`;
    } else if (recs.error) {
      sub.textContent = `For: ${targets}`;
      list.innerHTML = `<div class="empty" role="alert"><p>We couldn't load jobs. Try again later.</p></div>`;
    } else if (!items.length) {
      sub.textContent = `For: ${targets}`;
      list.innerHTML = `<div class="empty"><p>No jobs match your profile yet. Try more target roles, skills or locations.</p></div>`;
    } else {
      const total = recs.page?.total ?? items.length;
      sub.textContent = `${items.length} ${items.length === 1 ? "job" : "jobs"} for: ${targets}. Each one shows why it fits.`;
      list.innerHTML = `<ul class="job-list">${items.slice(0, RECS_SHOWN).map((j) => jobCardHtml(j)).join("")}</ul>${total > items.length ? `<p class="recs-more muted">Showing the ${items.length} best of ${total} recommended jobs. <a class="text-link" href="#/jobs">See all jobs</a></p>` : ""}`;
      paintMeters(list);
    }
  }

  // "Get set up" shows only until every step is done
  function renderSteps(me, hasProfile) {
    const steps = [
      ["Create your account", "Done", true],
      ["Upload your CV", me.cv ? `Added: ${me.cv.name}` : "PDF or DOCX — we translate titles and qualifications", !!me.cv, "cv"],
      ["Complete your career profile", hasProfile ? "Done — you can edit it at any time" : "Education, skills and the job you want", hasProfile, "questions"],
    ];
    const done = steps.filter((s) => s[2]).length;
    $("setup").hidden = done === steps.length;
    $("steps-sub").textContent = `${done} of ${steps.length} complete`;
    $("steps").innerHTML = steps
      .map(([t, d, ok, start], i) => `<li class="${ok ? "done" : ""}"><span class="step-dot">${ok ? icon("check") : i + 1}</span><div class="step-text"><strong>${esc(t)}</strong><span>${esc(d)}</span></div>${ok ? "" : `<button type="button" class="btn btn-secondary" data-start="${start}">Start</button>`}</li>`)
      .join("");
    $("steps").querySelectorAll("[data-start]").forEach((b) => (b.onclick = () => open(b.dataset.start)));
  }

  // Your activity: active applications (not finished) + "What employers see" (Feature 4, Feature 7)
  async function renderActivity() {
    // All the applications (not one page): the count of active ones needs the whole list
    const [apps, shared] = await Promise.all([fetchAllApplications().then((items) => ({ items })).catch(() => null), api.profile.shared().catch(() => null)]);
    if (!root.isConnected) return;
    const activeEl = $("active");
    if (!apps) activeEl.innerHTML = `<p class="muted" role="alert">We couldn't load your applications.</p>`;
    else {
      const active = apps.items.filter((a) => !a.final);
      const action = active.filter((a) => a.needsAction).length;
      const byStage = Object.entries(active.reduce((m, a) => ((m[a.status] = (m[a.status] || 0) + 1), m), {}))
        .map(([s, n]) => ({ label: STAGE_LABEL[s] || s, value: n }));
      activeEl.innerHTML = `
        <h3 class="act-title">${icon("inbox")} Active applications</h3>
        <p class="big-num">${active.length}${action ? `<span class="chip chip-yellow act-chip">${icon("alert")}${action} need${action === 1 ? "s" : ""} your action</span>` : ""}</p>
        ${active.length ? barChartHtml(byStage) : `<p class="muted">No active applications. Find a job below and apply.</p>`}
        <a class="text-link act-link" href="#/applications">See all applications</a>`;
    }
    const sharedEl = $("shared");
    if (!shared) { sharedEl.innerHTML = `<p class="muted" role="alert">We couldn't load your shared profile.</p>`; }
    else {
      const more = shared.skills.length - MAX_SKILL_CHIPS;
      sharedEl.innerHTML = `
        <h3 class="act-title">${icon("eye")} What employers see</h3>
        <p class="tr-preview-alias"><span class="alias-badge">${esc(shared.alias || "—")}</span></p>
        ${shared.roles.length ? `<p class="tr-preview-line"><strong>Roles:</strong> ${shared.roles.map((r) => `${esc(r.title)}${r.anzsco ? ` (ANZSCO ${esc(r.anzsco)})` : ""}`).join(", ")}</p>` : ""}
        ${sharedFactsHtml(shared)}
        ${shared.skills.length
          ? `<div class="tr-preview-skills">${skillChipsHtml(shared, MAX_SKILL_CHIPS)}${more > 0 ? `<span class="hint">+${more} more</span>` : ""}</div>`
          : `<p class="muted">Employers can't find you yet. Accept your translated skills to share them.</p>`}
        <p class="hint">Never your name, contact details, photo, nationality or CV.</p>
        <button type="button" class="btn btn-secondary btn-sm" data-edit-profile>${icon("edit")}${shared.skills.length ? "Edit profile" : "Review translated skills"}</button>`;
      sharedEl.querySelector("[data-edit-profile]").onclick = () => open(shared.skills.length ? "review" : "translation");
    }
    paintMeters(root.querySelector(".activity"));
  }

  // Skill insights (Feature 7 AC9) are Premium
  async function renderInsights() {
    const el = $("insights");
    let st;
    try { st = await api.stats.get(); } catch { el.innerHTML = `<p class="muted">We couldn't load your insights.</p>`; return; }
    if (!root.isConnected) return;
    const adv = st.advanced;
    el.innerHTML = adv
      ? `<div class="charts-grid">
          ${barChartHtml(adv.gapRanking.map((g) => ({ label: g.skill, value: g.count })), { title: `Skills to learn next (in ${adv.basis} best-fit jobs)`, unit: "jobs", empty: "No skill gaps found." })}
          ${barChartHtml(adv.demandForYourSkills.map((g) => ({ label: g.skill, value: g.count })), { title: "Demand for your skills", unit: "jobs", empty: "No data yet." })}
        </div>`
      : upgradeHtml("See which skills to learn next and the demand for your skills.");
    paintMeters(el);
  }

  render();
  renderActivity();
  renderInsights();
  // First visit of a talent account: open onboarding
  if (!ctx.user.onboarding) open("cv");
  await loadRecs();
}
