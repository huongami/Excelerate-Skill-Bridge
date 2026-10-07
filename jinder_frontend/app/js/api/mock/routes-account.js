// MOCK BACKEND — auth, aliases, the user record, password, CV upload and skill translation.
// The real backend replaces this file. It must enforce the same rules on the server.
import { route, ApiError, newId, validation, isEmail, requireUser, requireRole, publicUser, sharedProfileOf, list, nowIso } from "./core.js";
import { demoHash } from "./db.js";
import { suggestAlias, aliasProblem, isTaken, norm } from "./aliases.js";
import { translate } from "./translation.js";
import { sampleFor, parseResultOf } from "./cv-samples.js";

const ROLES = ["candidate", "recruiter"];
const SESSION_HOURS = 8;
const REMEMBER_DAYS = 30;

// 409 ALIAS_TAKEN with a free alias to suggest (Feature 1 AC13)
function assertAliasFree(db, alias, exceptUserId = null) {
  if (!isTaken(db, alias, exceptUserId)) return;
  const suggestion = suggestAlias(db);
  throw new ApiError(409, "ALIAS_TAKEN", `This alias is taken. Try “${suggestion}”.`, { alias: `This alias is taken. Try “${suggestion}”.` }, { suggestion });
}

// ---------- Auth ----------
route("POST", "/auth/signup", ({ db, body }) => {
  const role = body.role;
  const wantsAlias = role === "candidate" && norm(body.alias);
  validation({
    role: ROLES.includes(role) ? "" : "Choose an account type.",
    name: String(body.name || "").trim() ? "" : "Enter your name.",
    company: role === "recruiter" && !String(body.company || "").trim() ? "Enter your company." : "",
    email: isEmail(body.email) ? "" : "Enter a valid email address.",
    password: String(body.password || "").length >= 8 ? "" : "Use at least 8 characters.",
    alias: wantsAlias ? aliasProblem(body.alias, body.name) : "",
  });
  if (wantsAlias) assertAliasFree(db, body.alias);
  const email = body.email.trim().toLowerCase();
  // Same answer for a new or an existing email (no account enumeration)
  if (!db.users.some((u) => u.email === email)) {
    db.users.push({
      id: newId(), role, name: body.name.trim(), email, company: role === "recruiter" ? body.company.trim() : null,
      // Candidates always have an alias. If they do not choose one, the system gives one (Feature 1 AC6).
      alias: role === "candidate" ? (wantsAlias ? norm(body.alias) : suggestAlias(db)) : null,
      pw: demoHash(body.password), profile: null, cv: null, onboarding: null, createdAt: nowIso(),
    });
  }
  return { ok: true };
});

route("POST", "/auth/login", ({ db, body }) => {
  const user = db.users.find((u) => u.email === String(body.email || "").trim().toLowerCase());
  if (!user || user.seed || user.pw !== demoHash(String(body.password || ""))) {
    throw new ApiError(401, "INVALID_CREDENTIALS", "Incorrect email or password.");
  }
  const token = newId();
  const ms = body.remember ? REMEMBER_DAYS * 864e5 : SESSION_HOURS * 36e5;
  const expiresAt = new Date(Date.now() + ms).toISOString();
  db.sessions[token] = { userId: user.id, expiresAt };
  return { token, expiresAt, user: publicUser(user) };
});

route("POST", "/auth/logout", (ctx) => {
  if (ctx.token) delete ctx.db.sessions[ctx.token];
  return null;
});

// ---------- Aliases (public, used on the sign-up form) ----------
route("GET", "/aliases/suggest", ({ db }) => ({ alias: suggestAlias(db) }));

route("GET", "/aliases/check", ({ db, query }) => {
  const alias = norm(query.alias);
  const problem = aliasProblem(alias, query.name || "");
  if (problem) return { alias, available: false, reason: problem };
  if (isTaken(db, alias)) return { alias, available: false, reason: "This alias is taken.", suggestion: suggestAlias(db) };
  return { alias, available: true };
});

// ---------- Me ----------
route("GET", "/me", (ctx) => publicUser(requireUser(ctx)));

route("PATCH", "/me", (ctx) => {
  const user = requireUser(ctx);
  const { profile, cv, onboarding, name, company, alias } = ctx.body;
  const isCandidate = user.role === "candidate";
  validation({
    onboarding: onboarding === undefined || ["done", "dismissed"].includes(onboarding) ? "" : "Not a valid onboarding state.",
    cv: cv === undefined || cv === null || (typeof cv.name === "string" && Number.isFinite(cv.size)) ? "" : "Not a valid CV record.",
    name: name === undefined || String(name).trim() ? "" : "Enter your name.",
    company: company === undefined || user.role !== "recruiter" || String(company).trim() ? "" : "Enter your company.",
    alias: alias === undefined ? "" : !isCandidate ? "Only talent accounts have an alias." : aliasProblem(alias, name ?? user.name),
  });
  if (alias !== undefined) assertAliasFree(ctx.db, alias, user.id);
  if (name !== undefined) user.name = String(name).trim();
  if (company !== undefined && user.role === "recruiter") user.company = String(company).trim();
  if (alias !== undefined) user.alias = norm(alias);
  if (isCandidate && profile !== undefined) user.profile = profile;
  if (isCandidate && cv !== undefined) user.cv = cv;
  if (isCandidate && onboarding !== undefined) user.onboarding = onboarding;
  return publicUser(user);
});

// Change the password. Other sessions of this user end; this session stays.
route("POST", "/me/password", (ctx) => {
  const user = requireUser(ctx);
  const { currentPassword, newPassword } = ctx.body;
  validation({
    currentPassword: user.pw === demoHash(String(currentPassword || "")) ? "" : "Your current password is not correct.",
    newPassword: String(newPassword || "").length >= 8 ? "" : "Use at least 8 characters.",
  });
  if (currentPassword === newPassword) validation({ newPassword: "Use a password that is different from your current one." });
  user.pw = demoHash(newPassword);
  for (const [t, s] of Object.entries(ctx.db.sessions)) if (s.userId === user.id && t !== ctx.token) delete ctx.db.sessions[t];
  return null;
});

// ---------- CV and translation (candidates) ----------
const CV_MAX_BYTES = 10 * 1024 * 1024; // Feature 2 AC1: proposed limit 10 MB
const PARSE_MS = 1800; // the mock "reads" a CV for this long

// The mock gets { name, size, type } (the http adapter sends the file as multipart/form-data, field "file")
route("POST", "/cv", (ctx) => {
  const user = requireRole(ctx, "candidate");
  const { name, size } = ctx.body;
  const ext = String(name || "").slice(String(name || "").lastIndexOf(".")).toLowerCase();
  validation({
    file: ![".pdf", ".docx"].includes(ext) ? "Use a PDF or DOCX file."
      : !(size > 0) ? "This file is empty. Choose a different file."
      : size > CV_MAX_BYTES ? "The file is larger than 10 MB. Use a smaller file." : "",
  });
  const cv = { name: String(name), size: Number(size), addedAt: nowIso() };
  user.cv = cv;
  const id = newId();
  ctx.db.parses[id] = { userId: user.id, fileName: cv.name, startedAt: Date.now() };
  return { cv, parse: { id, status: "parsing" } };
});

route("GET", "/cv/parse/:id", (ctx) => {
  const user = requireRole(ctx, "candidate");
  const job = ctx.db.parses[ctx.params.id];
  if (!job || job.userId !== user.id) throw new ApiError(404, "NOT_FOUND", "We can't find this CV upload.");
  if (Date.now() - job.startedAt < PARSE_MS) return { id: ctx.params.id, status: "parsing" };
  const sample = sampleFor(job.fileName);
  if (!sample) return { id: ctx.params.id, status: "failed", error: "We couldn't read this CV. Try a different file, or enter your details yourself." };
  // The fields that the "AI" filled are "detected"; the fields it could not find are "missing". `found` tells which V2 fields the CV showed.
  return { id: ctx.params.id, status: "done", result: parseResultOf(sample) };
});

// Run the translation engine on a draft profile. Decisions (accepted / edited / removed), and the level and years that the talent set, are kept.
export function translateKeeping(profile, evidence) {
  const result = translate(profile, evidence);
  const before = new Map(list(profile.translation).map((s) => [s.id, s]));
  const skills = result.skills.map((s) => {
    const old = before.get(s.id);
    if (!old) return s;
    const isSkill = s.source === "skill";
    const level = isSkill && Number.isInteger(old.level) && old.level >= 1 && old.level <= 5 ? old.level : s.level;
    const years = isSkill && typeof old.years === "number" && old.years >= 0 && old.years <= 40 ? old.years : s.years;
    return { ...s, status: old.status, mapped: old.status === "edited" ? old.mapped : s.mapped, level, years };
  });
  return { skills, gaps: result.gaps };
}
route("POST", "/profile/translate", (ctx) => {
  requireRole(ctx, "candidate");
  const { profile = {}, evidence = [] } = ctx.body;
  return translateKeeping(profile, evidence);
});

// The preview of the talent ("What employers see"). It adds the V2 facts that the talent gave (level, exact years, skill levels, certifications, awards),
// so that the preview matches the profile. The employer screens of the mock do not keep these facts (plan F9): applications and talent cards have the old keys only.
route("GET", "/me/shared-profile", (ctx) => {
  const user = requireRole(ctx, "candidate");
  const p = user.profile || {};
  const shared = sharedProfileOf(user);
  const EVIDENCE_LEVEL = { Strong: 4, Moderate: 3, Limited: 2 };
  const cards = list(p.translation).filter((s) => (s.status === "accepted" || s.status === "edited") && s.source === "skill");
  const skillLevels = shared.skills.map((name) => {
    const c = cards.find((x) => x.mapped === name);
    return { name, level: (c && c.level) || EVIDENCE_LEVEL[c && c.evidence] || 3, years: c && typeof c.years === "number" ? c.years : null };
  });
  const years = Number(p.yearsExperience);
  return {
    ...shared, level: p.level || null, yearsExperience: Number.isFinite(years) && p.yearsExperience !== null && p.yearsExperience !== "" ? Math.round(years * 2) / 2 : null,
    specialisation: p.specialisation || "", skillLevels, certifications: list(p.certifications), awards: list(p.awards),
  };
});
