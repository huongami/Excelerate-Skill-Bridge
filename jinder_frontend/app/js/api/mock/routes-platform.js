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

route("POST", "/demo/reset-interview", (ctx) => {
  const db = ctx.db;
  const mode = ctx.body?.mode || "interview";
  const aid = ctx.body?.id;
  const cand = db.users.find((u) => u.email === "candidate@demo.jinder.app") || db.users.find((u) => u.role === "candidate");
  const rec = db.users.find((u) => u.email === "recruiter@demo.jinder.app") || db.users.find((u) => u.role === "recruiter");
  const app = aid ? db.applications.find((a) => a.id === aid) : db.applications.find((a) => a.candidateId === cand?.id);
  if (!app) return { ok: false, message: "Demo application not found." };

  const DAY = 864e5;
  const at = (days) => new Date(Date.now() + days * DAY).toISOString();
  if (mode === "review") {
    app.status = "review";
    app.slots = [];
    app.chosenSlotId = null;
    app.slotConfirmed = false;
    app.identityShared = false;
    app.offer = null;
    app.history = [
      { status: "applied", at: at(-5), by: "candidate", note: "" },
      { status: "review", at: at(-3), by: "recruiter", note: "" },
    ];
  } else {
    app.status = "interview";
    app.slots = [1, 2, 3].map((d) => ({
      id: Math.random().toString(36).slice(2, 10),
      start: new Date(new Date(at(d + 2)).setHours(10 + d, 0, 0, 0)).toISOString(),
    }));
    app.chosenSlotId = null;
    app.slotConfirmed = false;
    app.identityShared = false;
    app.offer = null;
    app.history = [
      { status: "applied", at: at(-5), by: "candidate", note: "" },
      { status: "review", at: at(-4), by: "recruiter", note: "" },
      { status: "interview", at: at(-2), by: "recruiter", note: "Offered 3 interview times" },
    ];
  }

  // Wipe leftover notifications from previous demo runs and re-seed baseline
  if (cand && rec) {
    db.notifications = (db.notifications || []).filter((n) => n.userId !== cand.id && n.userId !== rec.id);
    const otherApps = (db.applications || []).filter((a) => a.recruiterId === rec.id && a.candidateId !== cand.id && a.status === "applied");
    for (const oa of otherApps) {
      const j = (db.jobs || []).find((x) => x.id === oa.jobId);
      const c = (db.users || []).find((x) => x.id === oa.candidateId);
      db.notifications.push({
        id: Math.random().toString(36).slice(2, 10),
        userId: rec.id,
        type: "new_application",
        title: `New application for ${j?.title || "Role"}`,
        body: `${c?.alias || "Candidate"} applied.`,
        link: `/review/${oa.id}`,
        read: false,
        createdAt: new Date().toISOString(),
      });
    }
    if (mode === "review") {
      const j = (db.jobs || []).find((x) => x.id === app.jobId);
      db.notifications.push({
        id: Math.random().toString(36).slice(2, 10),
        userId: rec.id,
        type: "new_application",
        title: `New application for ${j?.title || "Role"}`,
        body: "Teal Heron applied.",
        link: `/review/${app.id}`,
        read: false,
        createdAt: new Date().toISOString(),
      });
    } else {
      const j = (db.jobs || []).find((x) => x.id === app.jobId);
      db.notifications.push({
        id: Math.random().toString(36).slice(2, 10),
        userId: cand.id,
        type: "interview_slots",
        title: `Interview times for ${j?.title || "Role"}`,
        body: "Choose a time that works for you.",
        link: `/applications/${app.id}`,
        read: false,
        createdAt: new Date().toISOString(),
      });
    }
  }
  return { ok: true, applicationId: app.id, status: app.status };
});
