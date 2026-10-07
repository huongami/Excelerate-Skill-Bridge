// Settings ("/settings") for both roles: the plan (Premium benefits), profile details, alias (candidate), career profile (candidate),
// password and sign out. Feature 1 AC9: the user can edit their information from the settings menu.
// V2: there is no "Settings" item in the menu. The user block at the bottom of the menu links here. "#/settings?section=plan" scrolls to the plan.
import { h, iconHtml as icon, esc, toList, announce } from "../core/dom.js";
import { api, ApiError } from "../api/index.js";
import { fieldError, clearErrors, focusFirstError, showAlert, applyFieldErrors, enhanceForm } from "../core/forms.js";
import { openOnboarding } from "../components/onboarding.js";
import { openModal } from "../components/modal.js";
import { updateShellUser } from "../components/shell.js";
import { crownIconHtml, premiumChipHtml } from "../components/premium.js";
import { sharedFactsHtml, skillChipsHtml } from "../components/profile-card.js";
import { session } from "../core/session.js";
import { CONFIG } from "../config.js";

const timesText = (n) => `${n} ${n === 1 ? "time" : "times"}`;

// "Your plan" card. It needs `benefits` from the backend. Basic: each benefit is locked. Premium: each benefit is Used or Not used yet.
function planCardHtml(ent) {
  const premium = ent.plan === "premium";
  const rows = ent.benefits.map((b) => {
    const open = premium || b.available === true; // the user can use it now
    const status = !open
      ? premiumChipHtml("Premium")
      : premium
        ? (b.used
          ? `<span class="chip chip-green">Used</span>${b.usedCount > 0 ? `<span class="benefit-count">${esc(timesText(b.usedCount))}</span>` : ""}`
          : `<span class="chip chip-neutral">Not used yet</span>`)
        : `<span class="chip chip-neutral">Included</span>`;
    return `
      <li class="benefit" data-benefit="${esc(b.key)}">
        <span class="benefit-icon">${open ? icon("check").replace('class="icon"', 'class="icon icon-ok"') : icon("i-lock")}</span>
        <div><div class="benefit-label">${esc(b.label)}</div><p class="benefit-desc">${esc(b.description)}</p></div>
        <div class="benefit-status">${status}</div>
      </li>`;
  }).join("");
  return `
    <div class="plan-card${premium ? " is-premium" : ""}" data-plan-now="${premium ? "premium" : "basic"}">
      <div class="plan-card-head">
        <span class="icon-tile ${premium ? "gold" : "accent"}">${premium ? crownIconHtml({ decorative: true }) : icon("i-lock")}</span>
        <div>
          <h3 tabindex="-1" data-plan-title>Your current plan: ${premium ? premiumChipHtml("Premium") : `<span class="chip chip-neutral">Basic</span>`}</h3>
          <p class="muted">${premium ? "You can use all of these features." : "Premium adds the features below."}</p>
        </div>
      </div>
      <ul class="benefit-list" aria-label="${premium ? "Premium features" : "Features in Premium"}">${rows}</ul>
      ${premium ? "" : `<button type="button" class="btn btn-primary" data-try-premium>Try Premium (demo)</button>`}
    </div>`;
}

export async function settingsView(root, ctx) {
  const isCandidate = ctx.user.role === "candidate";
  root.innerHTML = `
    <div class="dash settings">
      <div class="dash-head"><div><h1>Settings</h1><p class="dash-sub">Your account, ${isCandidate ? "alias, career profile, " : ""}plan and password.</p></div></div>

      <section class="panel settings-section plan-section" aria-labelledby="planTitle" id="plan">
        <div class="settings-intro"><h2 id="planTitle">Your plan</h2><p class="muted" data-plan-intro>Demo only: switch the plan to try the Premium features. There is no payment.</p></div>
        <div>
          <div data-plan-card></div>
          <div class="plan-demo">
            <p class="muted" data-plan-demo-text hidden>Demo only: switch the plan to try the Premium features. There is no payment.</p>
            <div class="form-alert" role="alert" data-plan-alert></div>
            <fieldset class="plan-group" data-plans><legend class="sr-only">Plan</legend>
              <label class="plan-option"><input type="radio" name="plan" value="basic"><span><strong>Basic</strong><span class="hint">${isCandidate ? "Recommendations, applications and basic charts." : `Post jobs, review applications, the top talent for each job and basic charts.`}</span></span></label>
              <label class="plan-option"><input type="radio" name="plan" value="premium"><span><strong>Premium <span class="chip chip-gold">Premium</span></strong><span class="hint">${isCandidate ? "Also: skills to learn next and the demand for your skills." : "Also: all talent, invite talent, compare up to 5 profiles and advanced charts."}</span></span></label>
            </fieldset>
          </div>
        </div>
      </section>

      <section class="panel settings-section" aria-labelledby="detailsTitle">
        <div class="settings-intro"><h2 id="detailsTitle">Profile details</h2><p class="muted">${isCandidate ? "Only you can see your name and email. Employers see your alias." : "Talent sees your company name on your jobs."}</p></div>
        <form class="settings-form" data-details novalidate>
          <div class="form-alert" role="alert" aria-live="polite" data-alert></div>
          <div class="field">
            <label for="s-name">Full name</label>
            <input id="s-name" name="name" type="text" class="text-input" autocomplete="name" required />
            <div class="field-error" data-for="name"></div>
          </div>
          ${isCandidate ? "" : `
          <div class="field">
            <label for="s-company">Company</label>
            <input id="s-company" name="company" type="text" class="text-input" autocomplete="organization" required />
            <div class="field-error" data-for="company"></div>
          </div>`}
          <div class="field">
            <label for="s-email">Email</label>
            <input id="s-email" name="email" type="email" class="text-input" readonly aria-describedby="s-email-hint" />
            <div class="hint" id="s-email-hint">You can't change your email in this version.</div>
          </div>
          <div class="settings-actions"><button type="submit" class="btn btn-primary">Save details</button></div>
        </form>
      </section>

      ${isCandidate ? `
      <section class="panel settings-section" aria-labelledby="aliasTitle">
        <div class="settings-intro">
          <h2 id="aliasTitle">Alias</h2>
          <p class="muted">Employers see you only by this name, until you agree to share your identity. Use a neutral name: not your real name, country or city.</p>
        </div>
        <form class="settings-form" data-alias-form novalidate>
          <div class="form-alert" role="alert" aria-live="polite" data-alert></div>
          <div class="alias-current"><span class="hint">Employers see you as</span><span class="alias-badge" data-alias-now></span></div>
          <div class="field">
            <div class="field-row">
              <label for="s-alias">New alias</label>
              <button type="button" class="text-link link-btn" data-suggest>Suggest another</button>
            </div>
            <input id="s-alias" name="alias" type="text" class="text-input" maxlength="30" autocomplete="off" aria-describedby="s-alias-hint" />
            <div class="hint" id="s-alias-hint">3 to 30 letters. Every alias on Jinder is different.</div>
            <div class="field-error" data-for="alias"></div>
          </div>
          <div class="settings-actions"><button type="submit" class="btn btn-primary">Save alias</button></div>
        </form>
      </section>

      <section class="panel settings-section" aria-labelledby="careerTitle">
        <div class="settings-intro"><h2 id="careerTitle">Career profile</h2><p class="muted">We use your answers to recommend jobs and to show your skill gaps.</p></div>
        <div>
          <dl class="review-list" data-career></dl>
          <div class="settings-actions">
            <button type="button" class="btn btn-secondary" data-edit-cv>${icon("upload")} Update CV</button>
            <button type="button" class="btn btn-secondary" data-edit-translation>Review translated skills</button>
            <button type="button" class="btn btn-primary" data-edit-answers>Edit answers</button>
          </div>
          <div class="tr-preview shared-panel" aria-labelledby="sharedTitle" data-shared>
            <h3 id="sharedTitle">What employers see</h3>
            <p class="hint">This is your profile as employers see it. It never shows your name, contact details, photo, nationality, employer names or your CV.</p>
            <div data-shared-body><p class="hint" role="status">Loading…</p></div>
          </div>
        </div>
      </section>` : ""}

      <section class="panel settings-section" aria-labelledby="pwTitle">
        <div class="settings-intro"><h2 id="pwTitle">Password</h2><p class="muted">When you change your password, you are signed out on your other devices.</p></div>
        <form class="settings-form" data-password novalidate>
          <div class="form-alert" role="alert" aria-live="polite" data-alert></div>
          <div class="field">
            <label for="s-current">Current password</label>
            <div class="input-wrap">
              <input id="s-current" name="currentPassword" type="password" class="text-input" autocomplete="current-password" required />
              <button type="button" class="toggle-pw" aria-label="Show password" aria-controls="s-current">${icon("eye")}</button>
            </div>
            <div class="field-error" data-for="currentPassword"></div>
          </div>
          <div class="field">
            <label for="s-new">New password</label>
            <div class="input-wrap">
              <input id="s-new" name="newPassword" type="password" class="text-input" autocomplete="new-password" aria-describedby="s-new-hint" required />
              <button type="button" class="toggle-pw" aria-label="Show password" aria-controls="s-new">${icon("eye")}</button>
            </div>
            <div class="hint" id="s-new-hint">At least 8 characters.</div>
            <div class="field-error" data-for="newPassword"></div>
          </div>
          <div class="field">
            <label for="s-confirm">Confirm new password</label>
            <input id="s-confirm" name="confirm" type="password" class="text-input" autocomplete="new-password" required />
            <div class="field-error" data-for="confirm"></div>
          </div>
          <div class="settings-actions"><button type="submit" class="btn btn-primary">Change password</button></div>
        </form>
      </section>

      ${CONFIG.API_MODE === "http" ? `
      <section class="panel settings-section" aria-labelledby="dataTitle">
        <div class="settings-intro"><h2 id="dataTitle">Your data</h2><p class="muted">Download a copy of the data that Jinder keeps about you, or delete your account and all of its data. You can't undo a delete.</p></div>
        <div>
          <div class="form-alert" role="alert" data-data-alert></div>
          <div class="settings-actions settings-actions-start">
            <button type="button" class="btn btn-secondary" data-export>${icon("file")} Download my data</button>
            <button type="button" class="btn btn-danger" data-delete>Delete my account</button>
          </div>
        </div>
      </section>` : ""}

      <section class="panel settings-section" aria-labelledby="sessionTitle">
        <div class="settings-intro"><h2 id="sessionTitle">Session</h2><p class="muted">Sign out of Jinder on this device.</p></div>
        <div class="settings-actions settings-actions-start"><button type="button" class="btn btn-secondary" data-signout>${icon("log-out")} Sign out</button></div>
      </section>

      ${CONFIG.API_MODE === "mock" ? `
      <section class="panel settings-section" aria-labelledby="demoTitle">
        <div class="settings-intro"><h2 id="demoTitle">Demo data</h2><p class="muted">The demo keeps all data in this browser. Reset deletes all local accounts and data, and writes the demo data again.</p></div>
        <div class="settings-actions settings-actions-start"><button type="button" class="btn btn-danger" data-reset>Reset demo data</button></div>
      </section>` : ""}
    </div>`;
  enhanceForm(root);

  // Run a save: disable the button, show success or the API errors
  async function submitWith(form, action, success) {
    const alertEl = form.querySelector("[data-alert]");
    const btn = form.querySelector("[type=submit]");
    btn.disabled = true;
    try {
      await action();
      showAlert(alertEl, success, "success");
      announce(success);
      return true;
    } catch (err) {
      if (err instanceof ApiError && ["VALIDATION_ERROR", "ALIAS_TAKEN"].includes(err.code) && applyFieldErrors(form, err.fields)) {
        if (err.suggestion) addUseSuggestion(form, err.suggestion);
        focusFirstError(form);
      } else {
        showAlert(alertEl, err.message || "We couldn't save. Try again.", "error");
      }
      return false;
    } finally {
      btn.disabled = false;
    }
  }
  function addUseSuggestion(form, suggestion) {
    const box = form.querySelector('.field-error[data-for="alias"]');
    const use = document.createElement("button");
    use.type = "button";
    use.className = "text-link link-btn alias-use";
    use.textContent = `Use “${suggestion}”`;
    use.addEventListener("click", () => { form.alias.value = suggestion; clearErrors(form, form.querySelector("[data-alert]")); form.alias.focus(); });
    box.append(" ", use);
  }

  // ---------- Profile details ----------
  const details = root.querySelector("[data-details]");
  details.name.value = ctx.user.name;
  details.email.value = ctx.user.email;
  if (!isCandidate) details.company.value = ctx.user.company || "";
  details.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearErrors(details, details.querySelector("[data-alert]"));
    const patch = { name: details.name.value.trim() };
    if (!isCandidate) patch.company = details.company.value.trim();
    let ok = true;
    if (!patch.name) ok = fieldError(details, "name", "Enter your name.");
    if (!isCandidate && !patch.company) ok = fieldError(details, "company", "Enter your company.");
    if (!ok) return focusFirstError(details);
    if (await submitWith(details, async () => { ctx.user = await api.me.update(patch); }, "Your details are saved.")) refreshShellName();
  });
  // The user block in the menu shows the name, the initials and the name of the link. Update it after a save.
  function refreshShellName() { updateShellUser(ctx.user); }

  if (!isCandidate) return bindCommon();

  // ---------- Alias ----------
  const aliasForm = root.querySelector("[data-alias-form]");
  const showAlias = () => {
    root.querySelector("[data-alias-now]").textContent = ctx.user.alias || "—";
    document.querySelectorAll("[data-shell-alias]").forEach((el) => (el.textContent = ctx.user.alias || ""));
  };
  showAlias();
  aliasForm.querySelector("[data-suggest]").addEventListener("click", async () => {
    try { aliasForm.alias.value = (await api.aliases.suggest()).alias; aliasForm.alias.focus(); } catch { /* no change */ }
  });
  aliasForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearErrors(aliasForm, aliasForm.querySelector("[data-alert]"));
    const alias = aliasForm.alias.value.trim().replace(/\s+/g, " ");
    if (alias.length < 3 || alias.length > 30) { fieldError(aliasForm, "alias", "Use 3 to 30 characters."); return focusFirstError(aliasForm); }
    if (alias.toLowerCase() === String(ctx.user.alias || "").toLowerCase()) { fieldError(aliasForm, "alias", "This is your alias now. Enter a different one."); return focusFirstError(aliasForm); }
    const saved = await submitWith(aliasForm, async () => { ctx.user = await api.me.update({ alias }); }, `Your alias is now ${alias}.`);
    if (saved) { aliasForm.alias.value = ""; showAlias(); }
  });

  // ---------- Career profile ----------
  const renderCareer = () => {
    const p = ctx.user.profile || {};
    const list = (v) => (toList(v).length ? toList(v).join(", ") : "—");
    const rows = [
      ["CV", ctx.user.cv ? ctx.user.cv.name : "No CV"],
      ["Target roles", list(p.targetRole)],
      ["Skills", toList(p.skills).length ? `${toList(p.skills).length} skills: ${list(p.skills)}` : "—"],
      ["Shared skills", (() => { const n = toList(p.translation).filter((s) => s.status === "accepted" || s.status === "edited").length; return n ? `${n} accepted` : "None yet. Review your translated skills."; })()],
      ["Locations", list(p.locations)],
      ["Work type", list(p.workTypes)],
    ];
    root.querySelector("[data-career]").innerHTML = rows.map(([k, v]) => `<div class="review-row review-row-2"><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join("");
    renderShared();
  };
  // "What employers see" comes from the API (GET /me/shared-profile), not from the screen
  async function renderShared() {
    const box = root.querySelector("[data-shared-body]");
    try {
      const s = await api.profile.shared();
      // Level, years, certifications, awards and skill levels: the same lines as the Home panel (sharedFactsHtml), so that the talent sees what employers see
      box.innerHTML = `
        <p class="tr-preview-alias"><span class="alias-badge">${esc(s.alias || "—")}</span></p>
        ${s.roles.length ? `<p class="tr-preview-line"><strong>Roles:</strong> ${s.roles.map((r) => `${esc(r.title)} (ANZSCO ${esc(r.anzsco)})`).join(", ")}</p>` : ""}
        ${sharedFactsHtml(s)}
        <p class="tr-preview-line"><strong>Skills:</strong></p><div class="tr-preview-skills">${s.skills.length ? skillChipsHtml(s) : `<span class="hint">None yet</span>`}</div>
        ${s.qualifications.length ? `<p class="tr-preview-line"><strong>Qualifications:</strong> ${esc(s.qualifications.join(", "))}${s.fieldsOfStudy.length ? ` · ${esc(s.fieldsOfStudy.join(", "))}` : ""}</p>` : ""}
        ${(s.industries || []).length ? `<p class="tr-preview-line"><strong>Domains:</strong> ${esc(s.industries.join(", "))}</p>` : ""}`;
    } catch (err) {
      box.innerHTML = `<p class="hint" role="alert">${esc(err.message || "We couldn't load this view.")}</p>`;
    }
  }
  renderCareer();
  const reopen = (start) => openOnboarding({ user: ctx.user, start, done: async () => { ctx.user = await api.me.get(); renderCareer(); } });
  root.querySelector("[data-edit-cv]").addEventListener("click", () => reopen("cv"));
  root.querySelector("[data-edit-translation]").addEventListener("click", () => reopen("translation"));
  root.querySelector("[data-edit-answers]").addEventListener("click", () => reopen("questions"));

  bindCommon();

  function bindCommon() {
    // ---------- Password ----------
    const pw = root.querySelector("[data-password]");
    pw.addEventListener("submit", async (e) => {
      e.preventDefault();
      clearErrors(pw, pw.querySelector("[data-alert]"));
      const body = { currentPassword: pw.currentPassword.value, newPassword: pw.newPassword.value };
      let ok = true;
      if (!body.currentPassword) ok = fieldError(pw, "currentPassword", "Enter your current password.");
      if (body.newPassword.length < 8) ok = fieldError(pw, "newPassword", "Use at least 8 characters.");
      if (pw.confirm.value !== body.newPassword) ok = fieldError(pw, "confirm", "Passwords don't match.");
      if (!ok) return focusFirstError(pw);
      if (await submitWith(pw, () => api.me.changePassword(body), "Your password is changed.")) pw.reset();
    });
    // ---------- Session ----------
    root.querySelector("[data-signout]").addEventListener("click", async () => {
      await api.auth.logout();
      ctx.navigate("/login");
    });
    // ---------- Plan: the Premium card (needs `benefits` from the backend) and the demo switch ----------
    const plans = root.querySelector("[data-plans]");
    const planAlert = root.querySelector("[data-plan-alert]");
    const cardBox = root.querySelector("[data-plan-card]");
    const demoText = root.querySelector("[data-plan-demo-text]");
    const planIntro = root.querySelector("[data-plan-intro]");
    function renderPlan(ent) {
      const radio = plans.querySelector(`[value="${ent.plan}"]`);
      if (radio) radio.checked = true;
      // The mock backend has no `benefits`: then only the demo switch shows, as before
      const withCard = Array.isArray(ent.benefits) && ent.benefits.length > 0;
      cardBox.innerHTML = withCard ? planCardHtml(ent) : "";
      demoText.hidden = !withCard;
      planIntro.textContent = withCard ? "See which features your plan includes, and which Premium features you used." : "Demo only: switch the plan to try the Premium features. There is no payment.";
    }
    // Change the plan, show the result, and draw the card again. The menu updates itself (event jinder:plan-change).
    async function changePlan(plan, { moveFocus = false } = {}) {
      plans.disabled = true;
      const tryBtn = cardBox.querySelector("[data-try-premium]");
      if (tryBtn) tryBtn.disabled = true;
      try {
        let ent = await api.entitlements.set(plan);
        if (!Array.isArray(ent.benefits)) ent = await api.entitlements.get().catch(() => ent); // the answer of the switch can lack the list
        renderPlan(ent);
        const msg = `Your plan is now ${ent.plan === "premium" ? "Premium" : "Basic"}.`;
        showAlert(planAlert, msg, "success");
        announce(msg);
        if (moveFocus) cardBox.querySelector("[data-plan-title]")?.focus();
      } catch (err) {
        showAlert(planAlert, err.message || "We couldn't change the plan. Try again.", "error");
        api.entitlements.get().then(renderPlan).catch(() => {}); // the switch must show the real plan
        if (tryBtn) tryBtn.disabled = false;
      } finally { plans.disabled = false; }
    }
    api.entitlements.get().then(renderPlan).catch(() => {});
    plans.addEventListener("change", (e) => changePlan(e.target.value));
    cardBox.addEventListener("click", (e) => { if (e.target.closest("[data-try-premium]")) changePlan("premium", { moveFocus: true }); });
    if (ctx.query.section === "plan") root.querySelector("#plan").scrollIntoView({ block: "start" });
    // ---------- Your data (real backend only) ----------
    const dataAlert = root.querySelector("[data-data-alert]");
    root.querySelector("[data-export]")?.addEventListener("click", async (e) => {
      const btn = e.currentTarget;
      btn.disabled = true;
      try {
        const data = await api.me.export();
        const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
        const a = document.createElement("a");
        a.href = url;
        a.download = "jinder-my-data.json";
        document.body.append(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        showAlert(dataAlert, "Your data is downloaded.", "success");
        announce("Your data is downloaded.");
      } catch (err) { showAlert(dataAlert, err.message || "We couldn't download your data. Try again.", "error"); }
      finally { btn.disabled = false; }
    });
    root.querySelector("[data-delete]")?.addEventListener("click", () => {
      const field = h("div", { class: "field" },
        h("label", { for: "del-pw", text: "Your password" }),
        h("input", { id: "del-pw", name: "password", type: "password", class: "text-input", autocomplete: "current-password", required: true }));
      openModal({
        title: "Delete your account?",
        intro: isCandidate ? "This deletes your profile, your CV and your applications. You can't undo this." : "This deletes your jobs and the applications for them. You can't undo this.",
        content: [field], submitText: "Delete account", danger: true,
        async onSubmit(form) {
          if (!form.password.value) throw new Error("Enter your password.");
          try { await api.me.deleteAccount(form.password.value); }
          catch (err) { throw new Error(err.fields?.password || err.message); }
          session.clear();
          location.hash = "#/";
          return true;
        },
      });
    });
    // ---------- Demo data (mock only) ----------
    root.querySelector("[data-reset]")?.addEventListener("click", () => openModal({
      title: "Reset the demo data?", intro: "This deletes all accounts and data in this browser, and writes the demo data again. You are signed out.", submitText: "Reset", danger: true,
      async onSubmit() { await api.demo.reset(); session.clear(); location.hash = "#/login"; return true; },
    }));
  }
}
