// MOCK BACKEND — notifications, stats for charts, premium entitlements and demo data (Feature 7).
// The real backend replaces this file. Charts are about skills and process, never a score on a person.
import { route, ApiError, requireUser, entitlementsOf, list, validation } from "./core.js";
import { loadJobs, recommend } from "./jobs.js";
import { FINAL } from "./routes-applications.js";
import { resetDb } from "./db.js";

// ---------- Notifications (in-app; "Email sent (demo)" for email events) ----------
route("GET", "/notifications", (ctx) => {
  const u = requireUser(ctx);
  const items = ctx.db.notifications.filter((n) => n.userId === u.id).sort((a, b) => Date.parse(b.createdAt) - Date.parse(a.createdAt)).slice(0, 50)
    .map(({ userId, ...n }) => n);
  return { items, unread: items.filter((n) => !n.read).length };
});
route("POST", "/notifications/read", (ctx) => {
  const u = requireUser(ctx);
  const ids = new Set(list(ctx.body.ids));
  ctx.db.notifications.forEach((n) => { if (n.userId === u.id && (ids.size === 0 || ids.has(n.id))) n.read = true; });
  return { ok: true };
});

// ---------- Entitlements (premium demo toggle; real payments are out of scope) ----------
route("GET", "/entitlements", (ctx) => entitlementsOf(ctx.db, requireUser(ctx)));
route("PUT", "/entitlements", (ctx) => {
  const u = requireUser(ctx);
  validation({ plan: ["basic", "premium"].includes(ctx.body.plan) ? "" : "Choose Basic or Premium." });
  ctx.db.plans[u.id] = ctx.body.plan;
  return entitlementsOf(ctx.db, u);
});

// ---------- Stats (Feature 7 AC5, AC6, AC8, AC9) ----------
const STAGES = ["applied", "contacted", "review", "interview", "accepted", "offer", "confirmed", "rejected", "declined"];
const countBy = (arr, key) => arr.reduce((m, x) => ((m[key(x)] = (m[key(x)] || 0) + 1), m), {});

route("GET", "/stats", async (ctx) => {
  const u = requireUser(ctx);
  await loadJobs();
  const ent = entitlementsOf(ctx.db, u);
  const db = ctx.db;
  if (u.role === "candidate") {
    const apps = db.applications.filter((a) => a.candidateId === u.id);
    const ev = db.events.filter((e) => e.targetType === "candidate" && e.targetId === u.id);
    const basic = {
      applications: apps.length,
      // "Moved to the next step": beyond Applied (Feature 7 AC9)
      movedOn: apps.filter((a) => !["applied", "contacted"].includes(a.status)).length,
      confirmed: apps.filter((a) => a.status === "confirmed").length,
      byStage: STAGES.map((s) => ({ stage: s, count: apps.filter((a) => a.status === s).length })).filter((x) => x.count),
      // Own profile events, as counts (Feature 7 AC6). Skips are not shown (AC7).
      profile: { appear: ev.filter((e) => e.type === "profile_appear").length, watch: ev.filter((e) => e.type === "profile_watch").length, saved: ev.filter((e) => e.type === "profile_saved").length },
    };
    let advanced = null;
    if (ent.advancedCharts && u.profile) {
      // Skill gap ranking and demand: from the 20 best-fitting open jobs
      const jobs = recommend(db, u.profile, 20);
      const gaps = countBy(jobs.flatMap((j) => j.match.gaps), (g) => g);
      const have = countBy(jobs.flatMap((j) => j.match.matchedSkills), (g) => g);
      const top = (m) => Object.entries(m).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([skill, count]) => ({ skill, count }));
      advanced = { basis: jobs.length, gapRanking: top(gaps), demandForYourSkills: top(have) };
    }
    return { role: "candidate", basic, advanced, plan: ent.plan };
  }
  // Recruiter
  const own = db.postedJobs.filter((j) => j.ownerId === u.id);
  const ids = new Set(own.map((j) => j.id));
  const apps = db.applications.filter((a) => ids.has(a.jobId));
  const open = own.filter((j) => Date.parse(j.closesAt) >= Date.now());
  const awaiting = apps.filter((a) => ["applied", "review"].includes(a.status) || (a.status === "interview" && a.chosenSlotId && !a.slotConfirmed));
  const basic = {
    openJobs: open.length,
    jobsAtTarget: own.filter((j) => apps.filter((a) => a.jobId === j.id && a.origin === "applied").length >= j.targetApplicants).length,
    awaitingResponse: awaiting.length,
    totalJobs: own.length,
  };
  let advanced = null;
  if (ent.advancedCharts) {
    // Aggregate counts per job, never per candidate (Feature 7 privacy NFR)
    const ev = db.events.filter((e) => e.targetType === "job" && ids.has(e.targetId));
    advanced = {
      pipeline: STAGES.map((s) => ({ stage: s, count: apps.filter((a) => a.status === s).length })),
      jobs: own.map((j) => ({ id: j.id, title: j.title, appear: ev.filter((e) => e.targetId === j.id && e.type === "job_appear").length, watch: ev.filter((e) => e.targetId === j.id && e.type === "job_watch").length, save: ev.filter((e) => e.targetId === j.id && e.type === "job_save").length, apply: apps.filter((a) => a.jobId === j.id && a.origin === "applied").length })),
      finished: apps.filter((a) => FINAL.includes(a.status)).length,
    };
  }
  return { role: "recruiter", basic, advanced, plan: ent.plan };
});

// ---------- Demo data (mock only, not part of the real API) ----------
route("POST", "/demo/reset", (ctx) => {
  resetDb();
  ctx.skipSave = true; // do not write the old data back
  return { ok: true };
});
