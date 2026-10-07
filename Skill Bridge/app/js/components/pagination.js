// Pager for lists of jobs and talent (R5): "Rows per page", "Showing 11–20 of 134", Previous, numbered pages, Next.
// Use: put pagerHtml(...) in the page, call bindPager(root, { onPage, onPageSize }) once, and draw the pager again after each load.
// All text is escaped. Colour is not the only signal: the current page has aria-current="page" and a bold, filled button.
import { esc } from "../core/dom.js";
import { session } from "../core/session.js";
import { PAGE_SIZES } from "../data/levels.js";

const STORAGE_PREFIX = "jinder.pagesize.";
const MAX_SLOTS = 7; // the most page buttons (and gaps) in the row
let counter = 0;

const intOr = (v, d) => (Number.isFinite(Number(v)) ? Math.floor(Number(v)) : d);

// The key for a list and the signed-in user, for example "jobs.u-123". If the caller added the user id already, do not add it twice.
function fullKey(key) {
  const k = String(key || "list");
  const uid = session.user?.id;
  if (!uid || k.endsWith(`.${uid}`)) return k;
  return `${k}.${uid}`;
}

/** The saved page size for a list. Returns the default (the first of PAGE_SIZES) if there is none or it is not valid. */
export function loadPageSize(key) {
  let v;
  try { v = Number(localStorage.getItem(STORAGE_PREFIX + fullKey(key))); } catch { v = NaN; }
  return PAGE_SIZES.includes(v) ? v : PAGE_SIZES[0];
}

/** Save the page size for a list. A size that is not in PAGE_SIZES is ignored. Returns the size that is now in use. */
export function savePageSize(key, size) {
  const n = Number(size);
  if (!PAGE_SIZES.includes(n)) return loadPageSize(key);
  try { localStorage.setItem(STORAGE_PREFIX + fullKey(key), String(n)); } catch { /* storage is blocked: the size lasts until the page closes */ }
  return n;
}

/** The page numbers to show. A number is a page. null is a gap ("…"). At most 7 items. */
export function pageSlots(page, totalPages) {
  if (totalPages <= MAX_SLOTS) return Array.from({ length: totalPages }, (_, i) => i + 1);
  if (page <= 4) return [1, 2, 3, 4, 5, null, totalPages];
  if (page >= totalPages - 3) return [1, null, totalPages - 4, totalPages - 3, totalPages - 2, totalPages - 1, totalPages];
  return [1, null, page - 1, page, page + 1, null, totalPages];
}

/**
 * @param {{ page: number, pageSize: number, total: number, limitedTo?: number|null }} p
 *   limitedTo: pass `limitedTo` of the response. A list that the plan limits (a Basic employer sees 5 talent) has no pager.
 * Returns "" when the total is 0, when the list is limited, or when there is one page and the total is not above the smallest page size.
 */
export function pagerHtml({ page = 1, pageSize = PAGE_SIZES[0], total = 0, limitedTo = null } = {}) {
  total = Math.max(0, intOr(total, 0));
  if (!total || (limitedTo != null && limitedTo !== false)) return "";
  pageSize = Math.max(1, intOr(pageSize, PAGE_SIZES[0]));
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  if (totalPages === 1 && total <= Math.min(...PAGE_SIZES)) return "";
  page = Math.min(Math.max(1, intOr(page, 1)), totalPages);
  const first = (page - 1) * pageSize + 1;
  const last = Math.min(total, page * pageSize);
  const uid = `pager-size-${++counter}`;
  // A saved size that is not in the list (for example 5) is still shown, so the select never lies
  const sizes = PAGE_SIZES.includes(pageSize) ? PAGE_SIZES : [...PAGE_SIZES, pageSize].sort((a, b) => a - b);

  const pages = pageSlots(page, totalPages).map((n) => n == null
    ? `<li class="pager-gap" aria-hidden="true">…</li>`
    : `<li><button type="button" class="pager-btn pager-num${n === page ? " is-current" : ""}" data-pager-page="${n}" aria-label="Page ${n}"${n === page ? ' aria-current="page"' : ""}>${n}</button></li>`).join("");

  return `
    <div class="pager" data-pager data-pager-page-now="${page}" data-pager-total-pages="${totalPages}">
      <div class="pager-size">
        <label for="${uid}">Rows per page</label>
        <select id="${uid}" class="text-input select pager-select" data-pager-size>
          ${sizes.map((s) => `<option value="${s}"${s === pageSize ? " selected" : ""}>${s}</option>`).join("")}
        </select>
      </div>
      <p class="pager-range" aria-live="polite">Showing ${first}–${last} of ${total}</p>
      <nav class="pager-nav" aria-label="Pagination">
        <ul class="pager-list">
          <li><button type="button" class="pager-btn pager-step" data-pager-page="${page - 1}"${page <= 1 ? " disabled" : ""}>Previous<span class="sr-only"> page</span></button></li>
          ${pages}
          <li><button type="button" class="pager-btn pager-step" data-pager-page="${page + 1}"${page >= totalPages ? " disabled" : ""}>Next<span class="sr-only"> page</span></button></li>
        </ul>
      </nav>
    </div>`;
}

// One handler set for each root. A later call to bindPager on the same root replaces the handlers. The listeners are added once.
const handlers = new WeakMap();

/**
 * Handle clicks and size changes inside root. The pager markup can be drawn again at any time.
 * @param {Element} root
 * @param {{ onPage?: (page: number) => void, onPageSize?: (size: number) => void, pageSizeKey?: string }} cb
 *   onPageSize is called with the new size. The list must go to page 1 then (this function does not draw anything).
 *   If pageSizeKey is given, the new size is also saved with savePageSize(pageSizeKey, size) before onPageSize is called.
 */
export function bindPager(root, { onPage = () => {}, onPageSize = () => {}, pageSizeKey = "" } = {}) {
  if (!root) return;
  const set = { onPage, onPageSize, pageSizeKey };
  if (handlers.has(root)) { handlers.set(root, set); return; }
  handlers.set(root, set);
  root.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-pager-page]");
    if (!btn || !root.contains(btn) || btn.disabled) return;
    const n = Number(btn.dataset.pagerPage);
    if (Number.isInteger(n) && n >= 1) handlers.get(root).onPage(n);
  });
  root.addEventListener("change", (e) => {
    const sel = e.target.closest("[data-pager-size]");
    if (!sel || !root.contains(sel)) return;
    const n = Number(sel.value);
    if (!Number.isInteger(n) || n < 1) return;
    const h = handlers.get(root);
    if (h.pageSizeKey) savePageSize(h.pageSizeKey, n);
    h.onPageSize(n);
  });
}
