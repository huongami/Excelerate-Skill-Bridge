// Small dialogs (report, contact, confirm). A native <dialog> made on demand and removed when it closes.
import { h, icon } from "../core/dom.js";

/**
 * @param {object} o { title, intro, content: Node[] , submitText, onSubmit: async (form) => true | false }
 * onSubmit returns true to close. It can throw an Error: its message shows in the dialog.
 */
export function openModal({ title, intro = "", content = [], submitText = "Send", danger = false, onSubmit }) {
  const id = `m-${Math.random().toString(36).slice(2, 8)}`;
  const alertEl = h("div", { class: "form-alert", role: "alert" });
  const submit = h("button", { type: "submit", class: `btn ${danger ? "btn-danger" : "btn-primary"}`, text: submitText });
  const cancel = h("button", { type: "button", class: "btn btn-ghost", text: "Cancel" });
  const form = h("form", { novalidate: true },
    h("div", { class: "modal-body" }, h("h2", { id: `${id}-t`, tabindex: "-1", text: title }), intro ? h("p", { class: "modal-sub", text: intro }) : null, alertEl, ...content),
    h("div", { class: "modal-foot" }, h("div"), h("div", { class: "modal-actions" }, cancel, submit)));
  const close = h("button", { type: "button", class: "btn btn-ghost btn-icon modal-x", "aria-label": "Close" }, icon("x"));
  const dlg = h("dialog", { class: "modal modal-small", "aria-labelledby": `${id}-t` }, close, form);
  document.body.append(dlg);
  const done = () => dlg.close();
  close.addEventListener("click", done);
  cancel.addEventListener("click", done);
  dlg.addEventListener("close", () => dlg.remove());
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    alertEl.className = "form-alert";
    submit.disabled = true;
    try {
      if (await onSubmit(form)) done();
    } catch (err) {
      alertEl.textContent = err.message || "Something went wrong. Try again.";
      alertEl.className = "form-alert show error";
    } finally {
      submit.disabled = false;
    }
  });
  dlg.showModal();
  dlg.querySelector("h2").focus();
  return dlg;
}

// Radio list for a set of reasons
export function radioGroup(name, legend, options) {
  return h("fieldset", { class: "radio-group" },
    h("legend", { class: "field-label", text: legend }),
    options.map(([value, label], i) => h("label", { class: "radio" }, h("input", { type: "radio", name, value, required: i === 0 }), h("span", { text: label }))));
}

export function textArea(name, label, { hint = "", max = 500, rows = 3, value = "" } = {}) {
  const ta = h("textarea", { id: `ta-${name}`, name, class: "text-input textarea", rows: String(rows), maxlength: String(max) });
  ta.value = value;
  return h("div", { class: "field" }, h("label", { for: ta.id, text: label }), ta, hint ? h("div", { class: "hint", text: hint }) : null);
}
