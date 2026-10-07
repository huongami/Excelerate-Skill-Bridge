// MOCK BACKEND — candidate job discovery: recommendations, search, detail, bookmarks, skip, report (Feature 3).
// The real backend replaces this file. Tracking events are written here, on the server side (Feature 7 AC4).
import { route, ApiError, validation, requireRole, requireUser, clamp, track, nowIso, newId } from "./core.js";
import { loadJobs, jobSource, recommend, searchJobs, jobDetail, findJob, isOpen } from "./jobs.js";

const savedIds = (db, u) => new Set(db.bookmarks[u.id] || []);
const skippedIds = (db, u) => new Set(db.skips[u.id] || []);
const appliedMap = (db, u) => new Map(db.applications.filter((a) => a.candidateId === u.id).map((a) => [a.jobId, a.id]));

// Add the candidate's own flags to a job
function flags(db, u) {
  const saved = savedIds(db, u), skipped = skippedIds(db, u), applied = appliedMap(db, u);
  return (job) => ({ ...job, bookmarked: saved.has(job.id), skipped: skipped.has(job.id), applicationId: applied.get(job.id) || null });
}
const appear = (db, u, items) => items.forEach((j) => track(db, { type: "job_appear", targetType: "job", targetId: j.id, actorId: u.id }));

route("GET", "/jobs/recommended", async (ctx) => {
  const u = requireRole(ctx, "candidate");
  await loadJobs();
  const exclude = new Set([...skippedIds(ctx.db, u), ...appliedMap(ctx.db, u).keys()]);
  const items = u.profile ? recommend(ctx.db, u.profile, clamp(ctx.query.limit, 5, 1, 20), exclude) : [];
  appear(ctx.db, u, items);
  return { items: items.map(flags(ctx.db, u)), source: jobSource(ctx.db) };
});

route("GET", "/jobs", async (ctx) => {
  const u = requireRole(ctx, "candidate");
  await loadJobs();
  const q = String(ctx.query.q || "").slice(0, 100);
  const location = String(ctx.query.location || "");
  const { total, items } = searchJobs(ctx.db, u.profile, { q, location, limit: clamp(ctx.query.limit, 50, 1, 100) }, skippedIds(ctx.db, u));
  appear(ctx.db, u, items);
  return { total, items: items.map(flags(ctx.db, u)), source: jobSource(ctx.db) };
});

route("GET", "/jobs/:id", async (ctx) => {
  const u = requireRole(ctx, "candidate");
  await loadJobs();
  const job = jobDetail(ctx.db, u.profile, ctx.params.id);
  if (!job) throw new ApiError(404, "NOT_FOUND", "This job does not exist or was removed.");
  track(ctx.db, { type: "job_watch", targetType: "job", targetId: job.id, actorId: u.id });
  const f = flags(ctx.db, u);
  return { ...f(job), similar: job.similar.map(f) };
});

// ---------- Skip (Feature 3 AC4). Skipped jobs leave the recommendations and the search. ----------
route("PUT", "/jobs/:id/skip", async (ctx) => {
  const u = requireRole(ctx, "candidate");
  await loadJobs();
  if (!findJob(ctx.db, ctx.params.id)) throw new ApiError(404, "NOT_FOUND", "This job does not exist or was removed.");
  const l = ctx.db.skips[u.id] || (ctx.db.skips[u.id] = []);
  if (!l.includes(ctx.params.id)) l.push(ctx.params.id);
  // Skip counts improve recommendations later. They are not shown to users (Feature 7 AC7).
  track(ctx.db, { type: "job_skip", targetType: "job", targetId: ctx.params.id, actorId: u.id });
  return { jobId: ctx.params.id, skipped: true };
});
route("DELETE", "/jobs/:id/skip", (ctx) => {
  const u = requireRole(ctx, "candidate");
  ctx.db.skips[u.id] = (ctx.db.skips[u.id] || []).filter((id) => id !== ctx.params.id);
  return { jobId: ctx.params.id, skipped: false };
});

// ---------- Bookmarks (Feature 3 AC5, AC10) ----------
route("GET", "/bookmarks", async (ctx) => {
  const u = requireRole(ctx, "candidate");
  await loadJobs();
  // Newest bookmark first. Removed jobs are skipped. Closed jobs stay, with status "closed".
  const ids = [...(ctx.db.bookmarks[u.id] || [])].reverse();
  const f = flags(ctx.db, u);
  const items = ids.map((id) => jobDetail(ctx.db, u.profile, id)).filter(Boolean).map(({ description, similar, ...j }) => f(j));
  return { items };
});
// Idempotent: saving a saved job again does nothing
route("PUT", "/bookmarks/:jobId", async (ctx) => {
  const u = requireRole(ctx, "candidate");
  await loadJobs();
  if (!findJob(ctx.db, ctx.params.jobId)) throw new ApiError(404, "NOT_FOUND", "This job does not exist or was removed.");
  const l = ctx.db.bookmarks[u.id] || (ctx.db.bookmarks[u.id] = []);
  if (!l.includes(ctx.params.jobId)) { l.push(ctx.params.jobId); track(ctx.db, { type: "job_save", targetType: "job", targetId: ctx.params.jobId, actorId: u.id }); }
  return { jobId: ctx.params.jobId, bookmarked: true };
});
route("DELETE", "/bookmarks/:jobId", (ctx) => {
  const u = requireRole(ctx, "candidate");
  ctx.db.bookmarks[u.id] = (ctx.db.bookmarks[u.id] || []).filter((id) => id !== ctx.params.jobId);
  return { jobId: ctx.params.jobId, bookmarked: false };
});

// ---------- Reports (Feature 3 AC6, Feature 5 AC6) ----------
const REPORT_REASONS = ["not_relevant", "wrong_location_or_type", "misleading", "other"];
route("POST", "/reports", (ctx) => {
  const u = requireUser(ctx);
  const { targetType, targetId, reason, details = "" } = ctx.body;
  validation({
    targetType: (u.role === "candidate" && targetType === "job") || (u.role === "recruiter" && targetType === "candidate") ? "" : "You can't report this.",
    reason: REPORT_REASONS.includes(reason) ? "" : "Choose a reason.",
    details: String(details).length <= 500 ? "" : "Use 500 characters or fewer.",
  });
  // Repeat reports of the same item by the same user do not make duplicates (Feature 3 NFR)
  const dup = ctx.db.reports.find((r) => r.userId === u.id && r.targetType === targetType && r.targetId === targetId);
  if (dup) { dup.reason = reason; dup.details = String(details); dup.at = nowIso(); }
  else ctx.db.reports.push({ id: newId(), userId: u.id, targetType, targetId, reason, details: String(details), at: nowIso() });
  return { ok: true };
});

