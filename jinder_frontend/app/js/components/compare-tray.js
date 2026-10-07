// The compare basket bar: a fixed bar at the bottom of the main area. It shows only when the basket has 1 or more items.
// It has "Compare (n/5)", a chip with a remove button for each item, "Open compare" (a link to #/compare) and "Clear".
// The app shell mounts it on every signed-in page except #/compare, so the basket stays while the user browses.
// Lists only call compareStore.add / remove. They do not mount a second bar.
import { h, esc, iconHtml, announce } from "../core/dom.js";
import { compareStore, COMPARE_EVENT } from "../core/compare-store.js";
import { COMPARE_MAX } from "../data/levels.js";

const MIN_TO_COMPARE = 2;

const needText = (kind, n) => `Add ${n} more ${kind === "talent" ? "talent" : n === 1 ? "job" : "jobs"} to compare.`;

// Only one bar is on the page at a time: a new mount removes the listener of the old one
let active = null;

/**
 * Mount the tray in `host` (the main column of the shell). `shell` gets the class "has-compare-tray" while the bar is shown,
 * so that the page gets space at the bottom and the bar covers no content.
 * Returns the tray element. It updates itself on "jinder:compare-change" and removes its listener when it leaves the page.
 * @param {{ host: Element, shell?: Element, kind: "job" | "talent" }} o
 */
export function mountCompareTray({ host, shell = host, kind }) {
  const tray = h("aside", { class: "compare-tray", "aria-label": "Compare basket", "data-compare-tray": kind, hidden: true });
  host.append(tray);

  const sync = () => {
    // CSSOM, not a style attribute: the CSP blocks inline styles
    shell.style.setProperty("--tray-h", `${tray.hidden ? 0 : tray.offsetHeight}px`);
  };
  const observer = typeof ResizeObserver === "function" ? new ResizeObserver(sync) : null;
  observer?.observe(tray);

  function render() {
    const items = compareStore.items(kind);
    const n = items.length;
    tray.hidden = n === 0;
    shell.classList.toggle("has-compare-tray", n > 0);
    if (!n) { tray.replaceChildren(); sync(); return; }
    const ready = n >= MIN_TO_COMPARE;
    tray.innerHTML = `
      <div class="compare-tray-main">
        <strong class="compare-tray-title" id="compare-tray-title">Compare (${n}/${COMPARE_MAX})</strong>
        <ul class="compare-tray-chips" aria-labelledby="compare-tray-title">
          ${items.map((it) => `<li class="chip chip-neutral compare-chip"><span title="${esc(it.title)}">${esc(it.title)}</span>
            <button type="button" data-compare-remove="${esc(it.id)}" aria-label="Remove ${esc(it.title)} from compare">${iconHtml("x")}</button></li>`).join("")}
        </ul>
      </div>
      <div class="compare-tray-actions">
        ${ready
          ? `<a class="btn btn-primary btn-sm" href="#/compare">Open compare</a>`
          : `<button type="button" class="btn btn-primary btn-sm" aria-disabled="true" aria-describedby="compare-tray-hint" data-compare-open-disabled>Open compare</button>
             <span class="compare-tray-hint" id="compare-tray-hint">${needText(kind, MIN_TO_COMPARE - n)}</span>`}
        <button type="button" class="btn btn-ghost btn-sm" data-compare-clear>Clear</button>
      </div>`;
    sync();
  }

  tray.addEventListener("click", (e) => {
    const rm = e.target.closest("[data-compare-remove]");
    if (rm) {
      const it = compareStore.items(kind).find((x) => x.id === rm.dataset.compareRemove);
      compareStore.remove(kind, rm.dataset.compareRemove);
      announce(`${it ? it.title : "Item"} removed from compare.`);
      tray.querySelector("[data-compare-remove], [data-compare-clear]")?.focus();
      return;
    }
    if (e.target.closest("[data-compare-clear]")) {
      compareStore.clear(kind);
      announce("Compare list cleared.");
    }
  });

  const onChange = (e) => {
    if (!tray.isConnected) { window.removeEventListener(COMPARE_EVENT, onChange); observer?.disconnect(); return; }
    if (!e.detail || e.detail.kind === kind) render();
  };
  if (active) { window.removeEventListener(COMPARE_EVENT, active.onChange); active.observer?.disconnect(); }
  active = { onChange, observer };
  window.addEventListener(COMPARE_EVENT, onChange);
  render();
  return tray;
}
