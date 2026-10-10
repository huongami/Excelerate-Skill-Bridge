// Sign in ("/login") and Create account ("/signup"). Shared screens for both roles.
import { iconHtml as i, logoHtml, esc } from "../core/dom.js";
import { CONFIG } from "../config.js";
import { api, ApiError } from "../api/index.js";
import { isEmail, fieldError, clearErrors, focusFirstError, showAlert, applyFieldErrors, enhanceForm, safeNext } from "../core/forms.js";

const legalLine = `<p class="legal">© 2026 Jinder · <a href="#/privacy" class="legal-link" target="_blank" rel="noopener">Privacy</a> · <a href="#/terms" class="legal-link" target="_blank" rel="noopener">Terms</a></p>`;

function aside({ headline, points, quote, by }) {
  return `
    <aside class="auth-aside on-dark">
      ${logoHtml("#/")}
      <p class="slogan">Where skills meet their match.</p>
      <h2>${headline}</h2>
      <ul class="check-list">${points.map((p) => `<li>${i("check")}${p}</li>`).join("")}</ul>
      <div class="auth-quote">“${quote}”<strong>${by}</strong></div>
    </aside>`;
}

// ---------- Sign in ----------
export async function loginView(root, ctx) {
  root.innerHTML = `
  <div class="auth-split">
    ${aside({
      headline: "Welcome back to skills-based hiring",
      points: ["Your translated profile, ready for every role", "Ranked matches with plain-language reasons", "Your data stays yours — you choose who sees it"],
      quote: "We stopped losing great talent to keyword filters. Now we see the skills, not just the job title.",
      by: "Hiring manager, Sydney SME",
    })}
    <main class="auth-main">
      <div class="auth-top">
        ${logoHtml("#/")}
        <span>New to Jinder?</span>
        <a href="#/signup" class="btn btn-secondary">Create account</a>
      </div>
      <div class="auth-form-wrap">
        <h1>Sign in</h1>
        <p class="sub">Enter your details to access your workspace.</p>
        <div class="form-alert" role="alert" aria-live="polite" data-alert></div>
        <form novalidate>
          <div class="field">
            <label for="email">Work or personal email</label>
            <input id="email" name="email" type="email" class="text-input" placeholder="you@example.com" autocomplete="email" required />
            <div class="field-error" data-for="email"></div>
          </div>
          <div class="field">
            <div class="field-row">
              <label for="password">Password</label>
              <a href="#/login" class="text-link" data-forgot>Forgot password?</a>
            </div>
            <div class="input-wrap">
              <input id="password" name="password" type="password" class="text-input" autocomplete="current-password" required />
              <button type="button" class="toggle-pw" aria-label="Show password" aria-controls="password">${i("eye")}</button>
            </div>
            <div class="field-error" data-for="password"></div>
          </div>
          <label class="checkbox"><input type="checkbox" name="remember" /> Keep me signed in on this device</label>
          <button type="submit" class="btn btn-primary btn-lg btn-block">Sign in</button>
        </form>
        <p class="auth-foot">Don't have an account? <a href="#/signup" class="text-link">Create one</a></p>
        <div class="demo-box" style="margin-top:14px; padding:12px 14px; background:var(--surface-muted); border:1px solid var(--hairline); border-radius:var(--r-md);">
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:4px;">
            <p class="demo-title" style="font-weight:700; font-size:12.5px; margin:0; color:var(--ink);">⚡ Quick Demo Sign-In</p>
            <button type="button" class="btn btn-ghost btn-sm" id="btnResetDemoData" style="font-size:11px; padding:2px 8px; color:var(--accent); height:auto;" title="Reset demo application data to Interview stage">
              🔄 Reset Demo
            </button>
          </div>
          <p class="hint" style="font-size:11.5px; color:var(--muted); margin-bottom:8px;">Click to test each role live with verified sample data:</p>
          <div class="demo-actions" style="display:flex; gap:8px; flex-wrap:wrap;">
            <button type="button" class="btn btn-secondary btn-sm" data-quick-email="candidate@demo.jinder.app" data-quick-pw="z4CJiNScZXnU">
              👤 Talent Flow (Candidate)
            </button>
            <button type="button" class="btn btn-secondary btn-sm" data-quick-email="recruiter@demo.jinder.app" data-quick-pw="Jpr0N8Jtadqo">
              💼 Employer Flow (Recruiter)
            </button>
          </div>
        </div>
      </div>
      ${legalLine}
    </main>
  </div>`;

  const form = root.querySelector("form");
  const alertEl = root.querySelector("[data-alert]");

  // Reset demo data button on login page
  const resetBtn = root.querySelector("#btnResetDemoData");
  if (resetBtn) {
    let alertTimer = null;
    let btnTimer = null;
    resetBtn.addEventListener("click", async () => {
      resetBtn.disabled = true;
      resetBtn.textContent = "⏳ Resetting...";
      try {
        await api.demo.resetInterview({ mode: "interview" });
        const successMsg = "Demo data successfully reset to Interview stage! You can select an account below to sign in.";
        showAlert(alertEl, successMsg, "success");
        if (alertTimer) clearTimeout(alertTimer);
        alertTimer = setTimeout(() => {
          if (alertEl && alertEl.textContent === successMsg) {
            alertEl.className = "form-alert";
            alertEl.textContent = "";
          }
        }, 2000);
        resetBtn.textContent = "✓ Reset";
        if (btnTimer) clearTimeout(btnTimer);
        btnTimer = setTimeout(() => {
          resetBtn.disabled = false;
          resetBtn.textContent = "🔄 Reset Demo";
        }, 2000);
      } catch (err) {
        resetBtn.disabled = false;
        resetBtn.textContent = "🔄 Reset Demo";
        showAlert(alertEl, "Unable to reset demo data: " + (err.message || err), "error");
      }
    });
  }

  // Fill the form with 1-click quick demo accounts
  root.querySelectorAll("[data-quick-email]").forEach((b) => b.addEventListener("click", () => {
    form.email.value = b.dataset.quickEmail;
    form.password.value = b.dataset.quickPw;
    if (form.remember) form.remember.checked = false; // keep in sessionStorage so two tabs can run two roles
    form.requestSubmit();
  }));
  // Fill the form with legacy demo account if mock
  root.querySelectorAll("[data-demo]").forEach((b) => b.addEventListener("click", () => {
    form.email.value = b.dataset.demo;
    form.password.value = CONFIG.MOCK_DEMO_PASSWORD;
    form.requestSubmit();
  }));
  enhanceForm(root);
  if (ctx.query.registered) showAlert(alertEl, "Thanks! If this email is new to Jinder, your account is ready. Sign in to continue.", "success");
  if (ctx.query.expired) showAlert(alertEl, "Your session has ended. Sign in again to continue.", "error");
  root.querySelector("[data-forgot]").addEventListener("click", (e) => {
    e.preventDefault();
    showAlert(alertEl, "Password reset is not available yet.", "error");
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearErrors(form, alertEl);
    const email = form.email.value.trim();
    const password = form.password.value;
    let ok = true;
    if (!isEmail(email)) ok = fieldError(form, "email", "Enter a valid email address.");
    if (!password) ok = fieldError(form, "password", "Enter your password.");
    if (!ok) return focusFirstError(form);
    const btn = form.querySelector("[type=submit]");
    btn.disabled = true;
    try {
      await api.auth.login({ email, password, remember: form.remember.checked });
      ctx.navigate(safeNext(ctx.query.next), { replace: true });
    } catch (err) {
      btn.disabled = false;
      showAlert(alertEl, err instanceof ApiError ? err.message : "Something went wrong. Try again.", "error");
    }
  });
}

// ---------- Create account ----------
export async function signupView(root, ctx) {
  root.innerHTML = `
  <div class="auth-split">
    ${aside({
      headline: "Make the skills you already have visible",
      points: ["Translate overseas and cross-industry experience", "See your gaps against real Australian roles", "Free for talent and employers during the pilot"],
      quote: "For the first time, my experience back home was described in words employers here understood.",
      by: "Master's graduate, Melbourne",
    })}
    <main class="auth-main">
      <div class="auth-top">
        ${logoHtml("#/")}
        <span>Already have an account?</span>
        <a href="#/login" class="btn btn-secondary">Sign in</a>
      </div>
      <div class="auth-form-wrap">
        <h1>Create your account</h1>
        <p class="sub">Tell us how you'll use Jinder.</p>
        <div class="role-picker" role="radiogroup" aria-label="Account type">
          <button type="button" class="role-option" role="radio" aria-checked="true" data-role="candidate">
            ${i("globe")}<div><strong>I'm looking for work</strong><span>Student or skilled migrant</span></div>
          </button>
          <button type="button" class="role-option" role="radio" aria-checked="false" data-role="recruiter">
            ${i("briefcase")}<div><strong>I'm hiring</strong><span>Employer or hiring team</span></div>
          </button>
        </div>
        <div class="form-alert" role="alert" aria-live="polite" data-alert></div>
        <form novalidate>
          <div class="field">
            <label for="name">Full name</label>
            <input id="name" name="name" type="text" class="text-input" placeholder="Jane Nguyen" autocomplete="name" required />
            <div class="field-error" data-for="name"></div>
          </div>
          <div class="field" data-alias-field>
            <div class="field-row">
              <label for="alias">Alias <span class="optional">(optional)</span></label>
              <button type="button" class="text-link link-btn" data-suggest>Suggest one</button>
            </div>
            <input id="alias" name="alias" type="text" class="text-input" maxlength="30" autocomplete="off" placeholder="For example, Teal Heron" aria-describedby="aliasHint" />
            <div class="hint" id="aliasHint">Employers see this name, not your real name. Leave it empty and we choose one for you.</div>
            <div class="field-error" data-for="alias"></div>
          </div>
          <div class="field" data-company hidden>
            <label for="company">Company</label>
            <input id="company" name="company" type="text" class="text-input" placeholder="Acme Pty Ltd" autocomplete="organization" />
            <div class="field-error" data-for="company"></div>
          </div>
          <div class="field">
            <label for="email">Email</label>
            <input id="email" name="email" type="email" class="text-input" placeholder="you@example.com" autocomplete="email" required />
            <div class="field-error" data-for="email"></div>
          </div>
          <div class="field">
            <label for="password">Password</label>
            <div class="input-wrap">
              <input id="password" name="password" type="password" class="text-input" autocomplete="new-password" aria-describedby="pwHint" required />
              <button type="button" class="toggle-pw" aria-label="Show password" aria-controls="password">${i("eye")}</button>
            </div>
            <div class="hint" id="pwHint">At least 8 characters.</div>
            <div class="field-error" data-for="password"></div>
          </div>
          <div class="field">
            <label for="confirm">Confirm password</label>
            <input id="confirm" name="confirm" type="password" class="text-input" autocomplete="new-password" required />
            <div class="field-error" data-for="confirm"></div>
          </div>
          <label class="checkbox"><input type="checkbox" name="terms" /> <span>I agree to the <a href="#/terms" class="legal-link" target="_blank" rel="noopener">Terms<span class="sr-only"> (opens in a new tab)</span></a> and <a href="#/privacy" class="legal-link" target="_blank" rel="noopener">Privacy Policy<span class="sr-only"> (opens in a new tab)</span></a></span></label>
          <button type="submit" class="btn btn-primary btn-lg btn-block">Create account</button>
        </form>
      </div>
      ${legalLine}
    </main>
  </div>`;

  const form = root.querySelector("form");
  const alertEl = root.querySelector("[data-alert]");
  const companyField = root.querySelector("[data-company]");
  const options = root.querySelectorAll(".role-option");
  enhanceForm(root);

  const aliasField = root.querySelector("[data-alias-field]");
  let role = "candidate";
  const setRole = (next) => {
    role = next;
    options.forEach((o) => o.setAttribute("aria-checked", String(o.dataset.role === role)));
    companyField.hidden = role !== "recruiter";
    aliasField.hidden = role !== "candidate"; // Only candidates have an alias
  };

  // "Suggest one": a free "Colour Animal" alias from the API
  root.querySelector("[data-suggest]").addEventListener("click", async () => {
    try {
      const { alias } = await api.aliases.suggest();
      form.alias.value = alias;
      form.alias.focus();
    } catch { /* keep the field as it is */ }
  });
  // Show the alias that the API suggests for a taken alias, with a button to use it
  function showAliasTaken(err) {
    fieldError(form, "alias", err.fields?.alias || err.message);
    if (!err.suggestion) return;
    const box = form.querySelector('.field-error[data-for="alias"]');
    const use = document.createElement("button");
    use.type = "button";
    use.className = "text-link link-btn alias-use";
    use.textContent = `Use “${err.suggestion}”`;
    use.addEventListener("click", () => { form.alias.value = err.suggestion; clearErrors(form, alertEl); form.alias.focus(); });
    box.append(" ", use);
  }
  options.forEach((o) => o.addEventListener("click", () => setRole(o.dataset.role)));
  if (["recruiter", "employer"].includes(ctx.query.role)) setRole("recruiter");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearErrors(form, alertEl);
    const data = {
      role,
      name: form.name.value.trim(),
      company: role === "recruiter" ? form.company.value.trim() : undefined,
      alias: role === "candidate" && form.alias.value.trim() ? form.alias.value.trim().replace(/\s+/g, " ") : undefined,
      email: form.email.value.trim(),
      password: form.password.value,
    };
    let ok = true;
    if (!data.name) ok = fieldError(form, "name", "Enter your name.");
    if (data.alias && (data.alias.length < 3 || data.alias.length > 30)) ok = fieldError(form, "alias", "Use 3 to 30 characters.");
    if (role === "recruiter" && !data.company) ok = fieldError(form, "company", "Enter your company.");
    if (!isEmail(data.email)) ok = fieldError(form, "email", "Enter a valid email address.");
    if (data.password.length < 8) ok = fieldError(form, "password", "Use at least 8 characters.");
    if (form.confirm.value !== data.password) ok = fieldError(form, "confirm", "Passwords don't match.");
    if (!ok) return focusFirstError(form);
    if (!form.terms.checked) return showAlert(alertEl, "Please accept the Terms and Privacy Policy to continue.", "error");

    const btn = form.querySelector("[type=submit]");
    btn.disabled = true;
    try {
      await api.auth.signup(data);
      ctx.navigate("/login?registered=1");
    } catch (err) {
      btn.disabled = false;
      if (err instanceof ApiError && err.code === "ALIAS_TAKEN") { showAliasTaken(err); return focusFirstError(form); }
      if (err instanceof ApiError && err.code === "VALIDATION_ERROR" && applyFieldErrors(form, err.fields)) return focusFirstError(form);
      showAlert(alertEl, err instanceof ApiError ? err.message : "Something went wrong. Try again.", "error");
    }
  });
}
