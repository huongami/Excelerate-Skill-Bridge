// Candidate applications (Feature 4): apply review ("/jobs/:id/apply"), list ("/applications") and tracking ("/applications/:id").
import { iconHtml as icon, esc, formatDate, announce } from "../core/dom.js";
import { api } from "../api/index.js";
import { applyFieldErrors, clearErrors, showAlert, focusFirstError } from "../core/forms.js";
import { coverageHtml, paintMeters, createPagedList } from "../components/job-card.js";
import { ribbonHtml, stepperHtml, historyHtml, skillMatchHtml, slotText } from "../components/status.js";
import { sharedProfileHtml } from "../components/profile-card.js";
import { openModal } from "../components/modal.js";

const NOTE_MAX = 500;
const FEEDBACK_MAX = 1000;
const loadingHtml = (t) => `<div class="empty" role="status"><p>${esc(t)}</p></div>`;
const backHtml = (href, text) => `<a class="back-link" href="${href}">${icon("chevron-left")}${esc(text)}</a>`;

// Text area with a live character count
function noteFieldHtml(name, label, { value = "", max = NOTE_MAX, hint = "" } = {}) {
  return `
    <div class="field">
      <label for="f-${name}">${esc(label)}</label>
      <textarea id="f-${name}" name="${name}" class="text-input textarea" rows="4" maxlength="${max}" aria-describedby="f-${name}-hint f-${name}-count">${esc(value)}</textarea>
      <div class="field-foot"><span class="hint" id="f-${name}-hint">${esc(hint)}</span><span class="hint" id="f-${name}-count" data-count-for="${name}" aria-live="polite"></span></div>
      <div class="field-error" data-for="${name}"></div>
    </div>`;
}
function bindCounters(root) {
  root.querySelectorAll("[data-count-for]").forEach((out) => {
    const ta = root.querySelector(`[name="${out.dataset.countFor}"]`);
    const set = () => (out.textContent = `${ta.value.length} / ${ta.maxLength}`);
    ta.addEventListener("input", set);
    set();
  });
}
const PII_HINT = "Do not add your name, email or phone number. We remove contact details before the employer sees the note.";

// ---------- Apply: review what the employer will see (Feature 4 AC1, AC2, AC12, AC13) ----------
export async function applyView(root, ctx) {
  root.innerHTML = `<div class="dash">${backHtml(`#/jobs/${encodeURIComponent(ctx.params.id)}`, "Back to job")}<h1 class="sr-only">Apply</h1>${loadingHtml("Loading…")}</div>`;
  let job, shared;
  try {
    [job, shared] = await Promise.all([api.jobs.get(ctx.params.id), api.profile.shared()]);
  } catch (err) {
    root.innerHTML = `<div class="dash">${backHtml("#/jobs", "Back to jobs")}<div class="dash-head"><div><h1>We can't open this job</h1><p class="dash-sub">${esc(err.message)}</p></div></div></div>`;
    return;
  }
  if (job.applicationId) return ctx.navigate(`/applications/${job.applicationId}`, { replace: true });
  document.title = `Apply: ${job.title} — Jinder`;
  const head = `${backHtml(`#/jobs/${encodeURIComponent(job.id)}`, "Back to job")}
    <div class="dash-head"><div><h1>Apply for ${esc(job.title)}</h1><p class="dash-sub">${esc(job.company)} · ${esc(job.area || job.location)} · ${esc(job.type)}</p></div></div>`;

  if (job.status === "closed") {
    root.innerHTML = `<div class="dash">${head}<section class="panel"><div class="empty"><div class="icon-tile accent">${icon("clock")}</div><p>This job is closed. You can't apply now.</p><a class="btn btn-primary" href="#/jobs">Find open jobs</a></div></section></div>`;
    return;
  }
  if (!shared.skills.length) {
    root.innerHTML = `<div class="dash">${head}<section class="panel"><div class="empty"><div class="icon-tile accent">${icon("target")}</div><p>Accept at least one translated skill before you apply. Employers see only the skills that you accept.</p><a class="btn btn-primary" href="#/settings">Review translated skills</a></div></section></div>`;
    return;
  }

  const m = job.match || { skills: [] };
  root.innerHTML = `
    <div class="dash apply">
      ${head}
      <ol class="apply-steps" aria-label="Steps"><li class="step-current" aria-current="step">1. Review your profile</li><li>2. Send</li><li>3. Track</li></ol>
      <div class="jd-grid">
        <section class="panel" aria-labelledby="seeTitle">
          <div class="panel-head"><div><h2 id="seeTitle">What the employer sees</h2>
            <p class="muted">Your alias and your translated profile only. Your name, contact details and CV stay private until you agree to share them for an interview.</p></div>
            <a class="btn btn-secondary" href="#/settings">${icon("edit")} Edit profile</a></div>
          ${sharedProfileHtml(shared)}
        </section>
        <aside class="panel jd-match" aria-labelledby="fitTitle">
          <h2 id="fitTitle">Your skills for this job</h2>
          <div class="jd-score">${coverageHtml(m)}</div>
          ${skillMatchHtml(m.skills)}
        </aside>
      </div>
      <section class="panel" aria-labelledby="sendTitle">
        <h2 id="sendTitle">Send your application</h2>
        <form novalidate data-apply>
          <div class="form-alert" role="alert"></div>
          ${noteFieldHtml("note", "Note to the employer (optional)", { hint: PII_HINT })}
          <p class="hint">You can change the note until the employer starts the review.</p>
          <div class="form-actions">
            <a class="btn btn-ghost" href="#/jobs/${esc(job.id)}">Cancel</a>
            <button type="submit" class="btn btn-primary btn-lg">${icon("send")} Send application</button>
          </div>
        </form>
      </section>
    </div>`;
  paintMeters(root);
  const form = root.querySelector("[data-apply]");
  const alertEl = form.querySelector(".form-alert");
  bindCounters(form);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearErrors(form, alertEl);
    const btn = form.querySelector("[type=submit]");
    btn.disabled = true;
    try {
      const app = await api.applications.create({ jobId: job.id, note: form.note.value });
      ctx.navigate(`/applications/${app.id}?new=1`);
    } catch (err) {
      btn.disabled = false;
      if (!applyFieldErrors(form, err.fields)) showAlert(alertEl, err.message || "We couldn't send your application. Try again.", "error");
      focusFirstError(form);
    }
  });
}

// ---------- Applications list (Feature 4 AC4, AC5; decision Q5) ----------
// V2: a sort and a pager (R5, R6). The sort values are the ones of the API: updated (the default), best (skill coverage), newest.
export const APP_SORTS = [
  { value: "updated", label: "Recently updated" },
  { value: "best", label: "Best skill match" },
  { value: "newest", label: "Newest application" },
];
const MAX_ALL_PAGES = 10;

/**
 * All the applications of the talent, loaded page by page (50 on a page, up to 10 pages).
 * The API has no filter for "active" and "past" yet. The Home and the tabs need the whole list to count them.
 */
export async function fetchAllApplications({ sort = "updated" } = {}) {
  const items = [];
  let page = 1;
  let totalPages = 1;
  do {
    const res = await api.applications.list({ page, pageSize: 50, sort });
    items.push(...(res.items || []));
    totalPages = res.page?.totalPages || 1;
    page += 1;
  } while (page <= totalPages && page <= MAX_ALL_PAGES);
  return items;
}

const tabHref = (tab, sort) => {
  const params = new URLSearchParams();
  if (tab === "past") params.set("tab", "past");
  if (sort && sort !== APP_SORTS[0].value) params.set("sort", sort);
  const qs = params.toString();
  return `#/applications${qs ? `?${qs}` : ""}`;
};

export async function applicationsView(root, ctx) {
  const tab = ctx.query.tab === "past" ? "past" : "active";
  root.innerHTML = `
    <div class="dash">
      <div class="dash-head"><div><h1>Applications</h1><p class="dash-sub">Track every application and its status.</p></div><a href="#/jobs" class="btn btn-secondary btn-lg">${icon("search")} Find jobs</a></div>
      <div class="tabs" role="tablist" aria-label="Applications">
        <a role="tab" class="tab" href="${tabHref("active")}" aria-selected="${tab === "active"}" data-tab="active">Active <span class="tab-count" data-n="active"></span></a>
        <a role="tab" class="tab" href="${tabHref("past")}" aria-selected="${tab === "past"}" data-tab="past">Past <span class="tab-count" data-n="past"></span></a>
      </div>
      <section class="panel" role="tabpanel" aria-labelledby="appsTitle">
        <h2 id="appsTitle" class="sr-only" tabindex="-1">${tab === "past" ? "Past applications" : "Active applications"}</h2>
        <div class="list-toolbar" data-sort></div>
        <div data-list>${loadingHtml("Loading applications…")}</div>
        <div data-pager></div>
      </section>
    </div>`;
  const list = root.querySelector("[data-list]");
  let all = null;       // every application, in the order of the sort in `allSort`
  let allSort = null;

  const ctl = createPagedList({
    key: "applications", query: ctx.query, sorts: APP_SORTS, sortId: "apps-sort",
    sortHost: root.querySelector("[data-sort]"), pagerHost: root.querySelector("[data-pager]"), listHost: list, focusHost: root.querySelector("#appsTitle"),
    // The tab (active or past) is a filter in the browser, so the list is cut here and not by the server (see fetchAllApplications)
    async fetchPage({ page, pageSize, sort }) {
      if (!all || allSort !== sort) { all = await fetchAllApplications({ sort }); allSort = sort; }
      const rows = all.filter((a) => (tab === "past" ? a.final : !a.final));
      const totalPages = Math.max(1, Math.ceil(rows.length / pageSize));
      const p = Math.min(Math.max(1, page), totalPages);
      return { items: rows.slice((p - 1) * pageSize, p * pageSize), page: { page: p, pageSize, total: rows.length, totalPages } };
    },
    onLoading: () => { list.innerHTML = loadingHtml("Loading applications…"); },
    onError: (err) => { list.innerHTML = `<div class="empty" role="alert"><p>${esc(err.message)}</p></div>`; },
    render(res, st) {
      root.querySelector('[data-n="active"]').textContent = all.filter((a) => !a.final).length;
      root.querySelector('[data-n="past"]').textContent = all.filter((a) => a.final).length;
      root.querySelectorAll("[data-tab]").forEach((a) => { a.href = tabHref(a.dataset.tab, st.sort); });
      const shown = res.items;
      if (!shown.length) {
        list.innerHTML = tab === "past"
          ? `<div class="empty"><div class="icon-tile accent">${icon("inbox")}</div><p>No past applications. Finished applications move here.</p></div>`
          : `<div class="empty"><div class="icon-tile accent">${icon("inbox")}</div><p>No active applications. Find a job that fits your skills and apply.</p><a class="btn btn-primary" href="#/jobs">Browse jobs</a></div>`;
        return;
      }
      list.innerHTML = `<ul class="app-list">${shown.map((a) => `
    <li class="app-row">
      <div class="app-main">
        <h3><a class="job-title-link" href="#/applications/${esc(a.id)}">${esc(a.job.title)}</a></h3>
        <p class="job-meta">${esc(a.job.company)} · ${esc(a.job.area || a.job.location)}${a.origin === "contacted" ? " · Invitation from the employer" : ""}</p>
        <p class="hint">Applied ${esc(formatDate(a.createdAt))} · Updated ${esc(formatDate(a.updatedAt))}</p>
      </div>
      <div class="app-side">
        ${ribbonHtml(a.status, a.statusLabel)}
        ${a.needsAction ? `<span class="chip chip-yellow">${icon("alert")}${a.final ? "Give feedback" : "Action needed"}</span>` : ""}
        <span class="hint">${a.coverage != null ? `${a.coverage}% skills covered` : ""}</span>
      </div>
    </li>`).join("")}</ul>`;
    },
  });
  await ctl.start();
}

// ---------- Tracking (Feature 4 AC3, AC6–AC11, AC14, AC15) ----------
export async function applicationDetailView(root, ctx) {
  root.innerHTML = `<div class="dash">${backHtml("#/applications", "Applications")}<h1 class="sr-only">Application</h1>${loadingHtml("Loading application…")}</div>`;
  let app;
  try { app = await api.applications.get(ctx.params.id); }
  catch (err) {
    root.innerHTML = `<div class="dash">${backHtml("#/applications", "Applications")}<div class="dash-head"><div><h1>We can't find this application</h1><p class="dash-sub">${esc(err.message)}</p></div></div></div>`;
    return;
  }
  const isNew = ctx.query.new === "1";

  const render = (a, focusSel) => {
    document.title = `${a.job.title} · ${a.statusLabel} — Jinder`;
    root.innerHTML = `
      <div class="dash app-detail">
        ${backHtml(a.final ? "#/applications?tab=past" : "#/applications", "Applications")}
        ${isNew ? `<div class="form-alert show success" role="status">${icon("check")} Your application is sent. The employer sees your alias and translated profile only.</div>` : ""}
        <header class="dash-head">
          <div>
            <h1>${esc(a.job.title)}</h1>
            <p class="dash-sub">${esc(a.job.company)} · ${esc(a.job.area || a.job.location)} · <a class="text-link" href="#/jobs/${esc(a.job.id)}">Job detail</a></p>
          </div>
          ${ribbonHtml(a.status, a.statusLabel)}
        </header>
        <section class="panel" aria-label="Progress">${stepperHtml(a)}</section>
        <div data-action></div>
        <div class="jd-grid">
          <section class="panel" aria-labelledby="sentTitle">
            <h2 id="sentTitle">What you sent</h2>
            <p class="muted">A copy of your profile on ${esc(formatDate(a.createdAt))}. Later changes to your profile do not change it.</p>
            ${a.note ? `<h3 class="jd-sub">Your note</h3><p class="note-text">${esc(a.note)}</p>` : ""}
            ${sharedProfileHtml(a.snapshot)}
          </section>
          <aside class="panel jd-match" aria-labelledby="mTitle">
            <h2 id="mTitle">Your skills for this job</h2>
            <div class="jd-score">${coverageHtml(a.match)}</div>
            ${skillMatchHtml(a.match.skills)}
          </aside>
        </div>
        <section class="panel" aria-labelledby="histTitle"><h2 id="histTitle">History</h2>${historyHtml(a.history)}</section>
      </div>`;
    paintMeters(root);
    renderAction(a, root.querySelector("[data-action]"));
    if (focusSel) root.querySelector(focusSel)?.focus();
  };

  // Run an API call, show its error in the panel, and render the new state
  const act = async (panel, fn, okMsg) => {
    const alertEl = panel.querySelector(".form-alert");
    panel.querySelectorAll("button").forEach((b) => (b.disabled = true));
    try {
      app = await fn();
      announce(okMsg);
      render(app, "[data-action] h2");
    } catch (err) {
      panel.querySelectorAll("button").forEach((b) => (b.disabled = false));
      const form = panel.querySelector("form");
      if (!(form && applyFieldErrors(form, err.fields)) && alertEl) showAlert(alertEl, err.fields?.form || err.message, "error");
    }
  };

  function renderAction(a, el) {
    const panel = (title, body, tone = "") => `<section class="panel action-panel ${tone}" aria-labelledby="actTitle"><h2 id="actTitle" tabindex="-1">${esc(title)}</h2><div class="form-alert" role="alert"></div>${body}</section>`;
    const slot = a.slots.find((s) => s.id === a.chosenSlotId);

    if (a.status === "applied") {
      el.innerHTML = panel("Change your note", `
        <form novalidate data-edit>${noteFieldHtml("note", "Note to the employer", { value: a.note, hint: PII_HINT })}
          <div class="form-actions"><button type="submit" class="btn btn-secondary">Save note</button></div></form>`);
      bindCounters(el);
      el.querySelector("form").addEventListener("submit", (e) => { e.preventDefault(); act(el, () => api.applications.update(a.id, { note: e.target.note.value }), "Your note is saved."); });
    } else if (a.status === "review") {
      el.innerHTML = panel("The employer is reviewing your application", `<p class="muted">You can't change it now. We tell you when the status changes.</p>`);
    } else if (a.status === "contacted") {
      const msg = a.history.find((x) => x.status === "contacted")?.note;
      el.innerHTML = panel("The employer invited you", `
        ${msg ? `<blockquote class="note-text">${esc(msg)}</blockquote>` : ""}
        <p class="muted">The employer found your anonymous profile. They can offer interview times next. If you are not interested, decline the invitation.</p>
        <div class="form-actions"><button type="button" class="btn btn-ghost" data-decline>Decline invitation</button></div>`, "tone-blue");
      el.querySelector("[data-decline]").addEventListener("click", () => openModal({
        title: "Decline the invitation?", intro: "The employer sees that you declined. You can't undo this.", submitText: "Decline", danger: true,
        async onSubmit() { app = await api.applications.decline(a.id); announce("You declined the invitation."); render(app); return true; },
      }));
    } else if (a.status === "interview" && !a.slots.length) {
      el.innerHTML = panel("Interview", `<p class="muted">The employer will offer interview times.</p>`);
    } else if (a.status === "interview" && a.slotConfirmed) {
      el.innerHTML = panel("Your interview is confirmed", `<p class="slot-confirmed">${icon("calendar")}<strong>${esc(slot ? slotText(slot.start) : "")}</strong></p>
        <p class="muted">${a.identityShared ? "The employer can see your name and email for this interview." : "You did not share your name and email. The employer contacts you through Jinder."}</p>`, "tone-green");
    } else if (a.status === "interview") {
      const future = a.slots.filter((s) => Date.parse(s.start) > Date.now());
      el.innerHTML = panel(slot ? "Waiting for the employer to confirm" : "Choose an interview time", `
        ${slot ? `<p class="muted">You chose <strong>${esc(slotText(slot.start))}</strong>. You can change it until the employer confirms.</p>` : `<p class="muted">The employer offered ${a.slots.length} ${a.slots.length === 1 ? "time" : "times"}. Choose one.</p>`}
        <form novalidate data-slot>
          <fieldset class="radio-group slot-group"><legend class="sr-only">Interview times</legend>
            ${future.map((s) => `<label class="radio slot-option"><input type="radio" name="slotId" value="${esc(s.id)}"${s.id === a.chosenSlotId ? " checked" : ""}>${icon("calendar")}<span>${esc(slotText(s.start))}</span></label>`).join("") || `<p class="muted">All the times have passed. The employer can offer new times.</p>`}
          </fieldset>
          <label class="check consent"><input type="checkbox" name="shareIdentity"${a.identityShared ? " checked" : ""}><span>Share my name and email with this employer for the interview. <span class="hint">If you do not tick this, you stay anonymous.</span></span></label>
          <div class="form-actions"><button type="submit" class="btn btn-primary"${future.length ? "" : " disabled"}>${icon("calendar")} ${slot ? "Change time" : "Choose this time"}</button></div>
        </form>`, "tone-yellow");
      el.querySelector("form").addEventListener("submit", (e) => {
        e.preventDefault();
        const f = e.target;
        const slotId = f.querySelector("input[name=slotId]:checked")?.value;
        if (!slotId) return showAlert(el.querySelector(".form-alert"), "Choose a time.", "error");
        act(el, () => api.applications.chooseSlot(a.id, { slotId, shareIdentity: f.shareIdentity.checked }), "Your interview time is sent to the employer.");
      });
    } else if (a.status === "accepted") {
      el.innerHTML = panel("You passed the interview", `<p class="muted">The employer accepted you after the interview. An offer can follow.</p>`, "tone-green");
    } else if (a.status === "offer") {
      el.innerHTML = panel("You have an offer", `
        <blockquote class="note-text">${esc(a.offer?.text || "")}</blockquote>
        <p class="hint">Sent ${esc(formatDate(a.offer?.sentAt || a.updatedAt))}</p>
        <div class="form-actions"><button type="button" class="btn btn-ghost" data-no>Decline offer</button><button type="button" class="btn btn-primary" data-yes>${icon("check")} Accept offer</button></div>`, "tone-green");
      el.querySelector("[data-yes]").addEventListener("click", () => act(el, () => api.applications.replyOffer(a.id, true), "You accepted the offer."));
      el.querySelector("[data-no]").addEventListener("click", () => openModal({
        title: "Decline the offer?", intro: "The application ends. You can't undo this.", submitText: "Decline offer", danger: true,
        async onSubmit() { app = await api.applications.replyOffer(a.id, false); announce("You declined the offer."); render(app); return true; },
      }));
    } else if (a.final) {
      const end = { confirmed: "You accepted the offer. Congratulations!", rejected: "This application is finished. The employer did not select you this time, or you declined the offer.", declined: "You declined the invitation." }[a.status];
      const theirs = a.feedback.theirs?.toOther ? `<h3 class="jd-sub">Feedback from the employer</h3><blockquote class="note-text">${esc(a.feedback.theirs.toOther)}</blockquote>` : "";
      if (a.feedback.mine) {
        el.innerHTML = panel("Application finished", `<p class="muted">${esc(end)}</p>${theirs}<h3 class="jd-sub">Your feedback</h3>
          ${a.feedback.mine.toOther ? `<p class="note-text">${esc(a.feedback.mine.toOther)}</p>` : ""}<p class="hint">Sent ${esc(formatDate(a.feedback.mine.at))}. Thank you.</p>`, a.status === "confirmed" ? "tone-green" : "");
      } else {
        el.innerHTML = panel("Application finished", `<p class="muted">${esc(end)}</p>${theirs}
          <form novalidate data-feedback>
            ${noteFieldHtml("toOther", "Feedback to the employer (optional)", { max: FEEDBACK_MAX, hint: "The employer sees this with your alias." })}
            ${noteFieldHtml("toTeam", "Feedback to the Jinder team (optional)", { max: FEEDBACK_MAX, hint: "Only the Jinder team sees this." })}
            <div class="form-actions"><button type="submit" class="btn btn-primary">${icon("send")} Send feedback</button></div>
          </form>`, a.status === "confirmed" ? "tone-green" : "");
        bindCounters(el);
        el.querySelector("form").addEventListener("submit", (e) => {
          e.preventDefault();
          clearErrors(e.target, el.querySelector(".form-alert"));
          act(el, () => api.applications.feedback(a.id, { toOther: e.target.toOther.value, toTeam: e.target.toTeam.value }), "Thank you. Your feedback is sent.");
        });
      }
    }
  }

  render(app);
}
