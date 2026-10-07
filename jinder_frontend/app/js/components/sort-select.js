// Sort control for lists (R6): a native select with a visible label.
import { esc } from "../core/dom.js";

/**
 * @param {{ id: string, value?: string, options: {value: string, label: string}[], label?: string }} o
 *   id must be unique on the page (it joins the label and the select). The first option is the default.
 */
export function sortSelectHtml({ id, value, options = [], label = "Sort by" }) {
  const current = options.some((o) => o.value === value) ? value : options[0]?.value;
  return `
    <div class="sort-select">
      <label for="${esc(id)}">${esc(label)}</label>
      <select id="${esc(id)}" class="text-input select sort-select-input" data-sort-select>
        ${options.map((o) => `<option value="${esc(o.value)}"${o.value === current ? " selected" : ""}>${esc(o.label)}</option>`).join("")}
      </select>
    </div>`;
}

/**
 * Call onChange(value) when the user picks another sort. The select can be drawn again: call bindSort again after that.
 * @param {Element} root  an element that contains the select
 * @param {string} id     the same id as in sortSelectHtml
 */
export function bindSort(root, id, onChange) {
  const sel = root?.querySelector(`#${CSS.escape(id)}`);
  if (!sel || sel.dataset.sortBound === "1") return;
  sel.dataset.sortBound = "1";
  sel.addEventListener("change", () => onChange(sel.value));
}
