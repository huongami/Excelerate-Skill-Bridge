// The compare basket. It holds up to 5 items for each kind: "job" (talent compares jobs) or "talent" (employer compares talent).
// It is kept in the browser (localStorage), for each signed-in user and kind, so it stays while the user browses and after a reload.
// This is a UI preference (a list of ids and titles), not app data from the API.
// Every change sends the window event "jinder:compare-change" with detail { kind, items, action, id }.
import { session } from "./session.js";
import { COMPARE_MAX } from "../data/levels.js";

export const COMPARE_EVENT = "jinder:compare-change";
const KINDS = ["job", "talent"];
const PREFIX = "jinder.compare.";

const storageKey = (kind) => `${PREFIX}${session.user?.id || "guest"}.${kind}`;
const validKind = (kind) => KINDS.includes(kind);

// Keep only small, plain values. A stored item has an id and short text, nothing else.
function cleanItem(raw) {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
  const id = raw.id == null ? "" : String(raw.id).trim();
  if (!id || id.length > 100) return null;
  const out = { id };
  let n = 0;
  for (const [k, v] of Object.entries(raw)) {
    if (k === "id" || n >= 12) continue;
    if (typeof v === "string") { out[k] = v.slice(0, 200); n++; }
    else if (typeof v === "number" && Number.isFinite(v)) { out[k] = v; n++; }
    else if (typeof v === "boolean") { out[k] = v; n++; }
  }
  // The label that the basket shows: the title of a job, or the alias of a talent
  out.title = String(out.title || out.alias || out.name || id).slice(0, 120);
  return out;
}

function read(kind) {
  if (!validKind(kind)) return [];
  let data;
  try { data = JSON.parse(localStorage.getItem(storageKey(kind)) || "[]"); } catch { return []; }
  if (!Array.isArray(data)) return [];
  const seen = new Set();
  const items = [];
  for (const raw of data) {
    const item = cleanItem(raw);
    if (!item || seen.has(item.id)) continue;
    seen.add(item.id);
    items.push(item);
    if (items.length >= COMPARE_MAX) break;
  }
  return items;
}

function write(kind, items) {
  try { localStorage.setItem(storageKey(kind), JSON.stringify(items)); } catch { /* storage is full or blocked: the basket lives until the next read */ }
}

function emit(kind, action, id = null) {
  window.dispatchEvent(new CustomEvent(COMPARE_EVENT, { detail: { kind, items: read(kind), action, id } }));
}

export const compareStore = {
  /** The items of one basket, oldest first. A broken stored value gives an empty list. */
  items: (kind) => read(kind),
  count: (kind) => read(kind).length,
  has: (kind, id) => read(kind).some((x) => x.id === String(id)),
  /**
   * Add an item: { id, title } for a job, { id, alias } for talent (more short text or number fields are allowed).
   * Returns true when the item is in the basket (also if it was there before). Returns false when the basket has 5 items already
   * or the item is not valid.
   */
  add(kind, item) {
    if (!validKind(kind)) return false;
    const clean = cleanItem(item);
    if (!clean) return false;
    const items = read(kind);
    if (items.some((x) => x.id === clean.id)) return true;
    if (items.length >= COMPARE_MAX) return false;
    items.push(clean);
    write(kind, items);
    emit(kind, "add", clean.id);
    return true;
  },
  remove(kind, id) {
    if (!validKind(kind)) return;
    const items = read(kind);
    const next = items.filter((x) => x.id !== String(id));
    if (next.length === items.length) return;
    write(kind, next);
    emit(kind, "remove", String(id));
  },
  clear(kind) {
    if (!validKind(kind)) return;
    if (!read(kind).length && localStorage.getItem(storageKey(kind)) == null) return;
    try { localStorage.removeItem(storageKey(kind)); } catch { /* ignore */ }
    emit(kind, "clear");
  },
  /** The basket kind for a role: "job" for talent (candidate), "talent" for an employer (recruiter). */
  kindForRole: (role) => (role === "recruiter" ? "talent" : "job"),
  max: COMPARE_MAX,
};

// Another tab changed a basket: tell this page too
window.addEventListener("storage", (e) => {
  if (!e.key || !e.key.startsWith(PREFIX)) return;
  const kind = e.key.slice(e.key.lastIndexOf(".") + 1);
  if (validKind(kind)) emit(kind, "sync");
});
