// Hash router. Routes look like "#/jobs/123?tab=skills".
// A hash without a leading "/" (for example "#how") is an in-page anchor on the landing page.
import { api, isSignedIn } from "../api/index.js";
import { session } from "./session.js";
import { renderShell } from "../components/shell.js";

const routes = [];
let fallback = null;
let forbidden = null;
let renderId = 0;

/**
 * @param {string} pattern  "/jobs/:id"
 * @param {Function} view   async (root, ctx) => void
 * @param {object} meta     { title, auth, role, guestOnly, shell, nav, bodyClass }
 */
export function addRoute(pattern, view, meta = {}) {
  const keys = [];
  const re = new RegExp("^" + pattern.replace(/:(\w+)/g, (_, k) => { keys.push(k); return "([^/]+)"; }) + "/?$");
  routes.push({ pattern, re, keys, view, meta });
}
export const setNotFound = (view) => (fallback = view);
export const setForbidden = (view) => (forbidden = view);

export function navigate(to, { replace = false } = {}) {
  const hash = "#" + to;
  if (location.hash === hash) return resolve();
  if (replace) location.replace(hash);
  else location.hash = to;
}

export const currentPath = () => (location.hash.slice(1).startsWith("/") ? location.hash.slice(1) : "/");

function parse() {
  const raw = location.hash.slice(1);
  if (raw && !raw.startsWith("/")) return { path: "/", query: {}, full: "/", anchor: raw };
  const full = raw || "/";
  const [path, qs = ""] = full.split("?");
  return { path, query: Object.fromEntries(new URLSearchParams(qs)), full };
}

let lastPattern = null;

async function resolve() {
  const id = ++renderId;
  const loc = parse();
  const root = document.getElementById("app");

  // In-page anchor on the landing page
  if (loc.anchor) {
    if (lastPattern !== "/") await render(routes.find((r) => r.pattern === "/"), {}, loc, root, id);
    document.getElementById(loc.anchor)?.scrollIntoView({ behavior: "smooth", block: "start" });
    return;
  }

  let match = null, params = {};
  for (const r of routes) {
    const m = loc.path.match(r.re);
    if (m) { match = r; params = Object.fromEntries(r.keys.map((k, i) => [k, decodeURIComponent(m[i + 1])])); break; }
  }
  if (!match) return render({ view: fallback, meta: { title: "Page not found" } }, {}, loc, root, id);

  const { meta } = match;
  if (meta.guestOnly && isSignedIn()) return navigate("/home", { replace: true });
  if (meta.auth) {
    if (!isSignedIn()) return navigate(`/login?next=${encodeURIComponent(loc.full)}`, { replace: true });
    try {
      if (!session.user) await api.me.get();
    } catch {
      return; // 401 is handled by the "jinder:unauthorized" listener
    }
    if (id !== renderId) return;
    if (meta.role && session.user.role !== meta.role) {
      return render({ view: forbidden, meta: { title: "No access", shell: true } }, params, loc, root, id);
    }
  }
  return render(match, params, loc, root, id);
}

async function render(route, params, loc, root, id) {
  const { view, meta = {} } = route;
  lastPattern = route.pattern || null;
  document.title = meta.title ? `${meta.title} — Jinder` : "Jinder — Where skills meet their match.";
  document.body.className = meta.bodyClass || "";
  const ctx = { params, query: loc.query, path: loc.path, user: session.user, navigate };
  let target = root;
  if (meta.shell) target = renderShell(root, ctx, meta.nav);
  else root.replaceChildren();
  await view(target, ctx);
  if (id !== renderId) return;
  // Move focus to the page heading for screen readers, without scrolling
  window.scrollTo(0, 0);
  const heading = target.querySelector("h1");
  if (heading && loc.full !== "/") {
    heading.setAttribute("tabindex", "-1");
    heading.focus({ preventScroll: true });
  }
}

export function startRouter() {
  window.addEventListener("hashchange", resolve);
  // The API reports an ended session: go to sign-in and come back here after
  window.addEventListener("jinder:unauthorized", () => {
    navigate(`/login?expired=1&next=${encodeURIComponent(currentPath())}`, { replace: true });
  });
  resolve();
}
