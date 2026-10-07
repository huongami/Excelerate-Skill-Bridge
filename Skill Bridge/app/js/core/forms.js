// Form helpers: inline errors (aria-invalid + aria-describedby), alerts and password toggles.

export const isEmail = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);

export function fieldError(form, name, msg) {
  const input = form.elements[name];
  const error = form.querySelector(`.field-error[data-for="${name}"]`);
  if (!input || !error) return false;
  error.id = `${name}-error`;
  error.textContent = msg;
  input.classList.add("invalid");
  input.setAttribute("aria-invalid", "true");
  input.setAttribute("aria-describedby", [input.dataset.hint, error.id].filter(Boolean).join(" "));
  return false;
}

export function clearErrors(form, alertEl) {
  form.querySelectorAll(".invalid").forEach((el) => {
    el.classList.remove("invalid");
    el.removeAttribute("aria-invalid");
    if (el.dataset.hint) el.setAttribute("aria-describedby", el.dataset.hint);
    else el.removeAttribute("aria-describedby");
  });
  form.querySelectorAll(".field-error").forEach((el) => (el.textContent = ""));
  if (alertEl) alertEl.className = "form-alert";
}

export const focusFirstError = (form) => form.querySelector(".invalid")?.focus();

export function showAlert(alertEl, msg, type) {
  alertEl.textContent = msg;
  alertEl.className = `form-alert show ${type}`;
}

// Show the field errors from an API VALIDATION_ERROR. Returns true if at least one field was shown.
export function applyFieldErrors(form, fields) {
  let shown = false;
  for (const [name, msg] of Object.entries(fields || {})) {
    if (!form.elements[name]) continue;
    fieldError(form, name, msg);
    shown = true;
  }
  return shown;
}

// Password show/hide buttons. Also remember each input's hint id for aria-describedby.
export function enhanceForm(root) {
  root.querySelectorAll("input[aria-describedby]").forEach((el) => (el.dataset.hint = el.getAttribute("aria-describedby")));
  root.querySelectorAll(".toggle-pw").forEach((btn) => {
    const input = root.querySelector(`#${btn.getAttribute("aria-controls")}`);
    btn.addEventListener("click", () => {
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.setAttribute("aria-label", show ? "Hide password" : "Show password");
      btn.querySelector("use").setAttribute("href", `icons.svg#${show ? "eye-off" : "eye"}`);
    });
  });
}

// Only allow in-app paths for ?next= (blocks open redirects and loops)
export const safeNext = (next) =>
  typeof next === "string" && next.startsWith("/") && !next.startsWith("//") && !/^\/(login|signup)\b/.test(next) ? next : "/home";
