// MOCK BACKEND — route table and shared helpers for the mock route files. The real backend replaces this file.
import { ApiError } from "../errors.js";
import { newId } from "./db.js";
import { suggestAlias } from "./aliases.js";

export { ApiError, newId };

// ---------- Routing ----------
export const routes = [];
export function route(method, pattern, handler) {
  const keys = [];
  const re = new RegExp("^" + pattern.replace(/:(\w+)/g, (_, k) => { keys.push(k); return "([^/]+)"; }) + "$");
  routes.push({ method, re, keys, handler });
}

// ---------- Helpers ----------
export const list = (v) => (Array.isArray(v) ? v : v ? [v] : []);
export const clamp = (v, def, min, max) => Math.min(Math.max(parseInt(v, 10) || def, min), max);
export const isEmail = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(v || ""));
export const nowIso = () => new Date().toISOString();

export function validation(fields) {
  const bad = Object.fromEntries(Object.entries(fields).filter(([, msg]) => msg));
  if (Object.keys(bad).length) throw new ApiError(400, "VALIDATION_ERROR", "Some fields are not valid.", bad);
}
export const notFound = (msg) => { throw new ApiError(404, "NOT_FOUND", msg); };
export const conflict = (msg) => { throw new ApiError(409, "CONFLICT", msg); };

export function currentUser(ctx) {
  const s = ctx.token && ctx.db.sessions[ctx.token];
  if (!s) return null;
  if (Date.parse(s.expiresAt) < Date.now()) { delete ctx.db.sessions[ctx.token]; return null; }
  const u = ctx.db.users.find((x) => x.id === s.userId) || null;
  // Candidates made before aliases existed get one now
  if (u && u.role === "candidate" && !u.alias) u.alias = suggestAlias(ctx.db);
  return u;
}
export function requireUser(ctx) {
  const u = currentUser(ctx);
  if (!u) throw new ApiError(401, "UNAUTHORIZED", "Your session has ended. Sign in again.");
  return u;
}
export function requireRole(ctx, role) {
  const u = requireUser(ctx);
  if (u.role !== role) throw new ApiError(403, "FORBIDDEN", "You don't have access to this.");
  return u;
}

// Fields that GET /me returns (allowlist). The password hash is never returned.
export const publicUser = (u) => ({
  id: u.id, role: u.role, name: u.name, email: u.email, company: u.company || null, alias: u.alias || null,
  profile: u.profile || null, cv: u.cv || null, onboarding: u.onboarding || null, createdAt: u.createdAt,
});

// ---------- Recruiter-safe candidate view (allowlist; Feature 5 AC3, AC4) ----------
// It never has: name, email, contact details, photo, country, employer names, the CV or the evidence lines.
export const isShared = (s) => s.status === "accepted" || s.status === "edited";
export function sharedProfileOf(user) {
  const p = user.profile || {};
  const shared = list(p.translation).filter(isShared);
  return {
    alias: user.alias,
    roles: shared.filter((s) => s.anzsco).map((s) => ({ title: s.occupation || s.mapped, anzsco: s.anzsco })),
    // A role card gives a role, not a skill (plan: the shared skills list has the skill cards only)
    skills: [...new Set(shared.filter((s) => s.source === "skill").map((s) => s.mapped))],
    qualifications: shared.filter((s) => s.source === "qualification").map((s) => s.mapped),
    fieldsOfStudy: list(p.fieldOfStudy),
    industries: list(p.industry),
    years: p.years || null,
    targetRoles: list(p.targetRole),
    locations: list(p.locations),
    workTypes: list(p.workTypes),
  };
}
// Words that must never reach a recruiter in free text (Feature 5 NFR): emails and phone numbers
export const scrubContact = (text) => String(text || "")
  .replace(/[^\s@]+@[^\s@]+\.[^\s@]+/g, "[email removed]")
  .replace(/\+?\d[\d\s().-]{7,}\d/g, "[phone removed]");

// ---------- Notifications (Feature 7) ----------
// In-app. "email: true" adds a line "Email sent (demo)" — the mock does not send email.
export function notify(db, userId, { type, title, body = "", link = "", email = false }) {
  db.notifications.push({ id: newId(), userId, type, title, body, link, email, read: false, createdAt: nowIso() });
}

// ---------- Entitlements (Feature 7: premium, demo toggle) ----------
export const TOP_N = 5;
export function entitlementsOf(db, user) {
  const plan = db.plans[user.id] === "premium" ? "premium" : "basic";
  const premium = plan === "premium";
  return {
    plan,
    topN: user.role === "recruiter" ? (premium ? null : TOP_N) : null,
    canContact: user.role === "recruiter" && premium,
    canCompare: user.role === "recruiter" && premium,
    advancedCharts: premium,
    // V2 keys. The mock has no `benefits` list: Settings then shows the plain plan section.
    crown: premium,
    compareMax: 5,
  };
}
export function requirePremium(db, user, feature) {
  const e = entitlementsOf(db, user);
  if (!e[feature]) throw new ApiError(403, "PREMIUM_REQUIRED", "This feature is part of Premium. Upgrade in Settings to use it.");
  return e;
}

// ---------- Tracking events (Feature 7 AC4) ----------
export function track(db, { type, targetType, targetId, actorId }) {
  db.events.push({ type, targetType, targetId, actorId, at: nowIso() });
  if (db.events.length > 5000) db.events.splice(0, db.events.length - 5000);
}
