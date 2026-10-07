// MOCK BACKEND — recruiter features: post and manage jobs, review applications, anonymous candidates (Features 5, 6).
// The real backend replaces this file. Recruiter responses use the allowlist view only (no name, contact, CV).
import { route, ApiError, newId, validation, requireRole, notify, track, nowIso, sharedProfileOf, scrubContact, entitlementsOf, requirePremium, list, clamp } from "./core.js";
import { loadJobs, findJob, isOpen, suggestSkills, skillMatch, namesFromList } from "./jobs.js";
import { TRANSITIONS, FINAL, STATUS_LABEL, addHistory, jobBrief, snapshotMatch } from "./routes-applications.js";
import { LOCATIONS, WORK_TYPES, JOB_CATEGORIES } from "../../data/reference.js";
import { jdSampleFor } from "./jd-samples.js";

const DAY = 864e5;
// Close badge (Feature 6 AC3): green open, yellow less than 7 days, red closed or overdue
export function badgeOf(job) {
  const left = Math.ceil((Date.parse(job.closesAt) - Date.now()) / DAY);
  if (left < 0) return { badge: "closed", label: "Closed", daysLeft: left };
  if (left < 7) return { badge: "closing", label: left <= 1 ? "Closes in 1 day" : `Closes in ${left} days`, daysLeft: left };
  return { badge: "open", label: "Open", daysLeft: left };
}

const ownJob = (ctx, u) => {
  const j = ctx.db.postedJobs.find((x) => x.id === ctx.params.id && x.ownerId === u.id);
  if (!j) throw new ApiError(404, "NOT_FOUND", "We can't find this job.");
  return j;
};
const appsFor = (db, jobId) => db.applications.filter((a) => a.jobId === jobId);
const awaiting = (a) => ["applied", "review"].includes(a.status) || (a.status === "interview" && a.chosenSlotId && !a.slotConfirmed);

function jobSummary(db, j) {
  const apps = appsFor(db, j.id);
  return {
    id: j.id, title: j.title, category: j.category, location: j.location, type: j.type, salary: j.salary,
    postedAt: j.postedAt, closesAt: j.closesAt, skills: j.skills, targetApplicants: j.targetApplicants,
    applicantCount: apps.filter((a) => a.origin === "applied").length, contactedCount: apps.filter((a) => a.origin === "contacted").length,
    awaitingCount: apps.filter(awaiting).length, ...badgeOf(j),
  };
}

function checkJob(body, partial = false) {
  const has = (k) => !partial || body[k] !== undefined;
  const skills = list(body.skills).map((s) => String(s).trim()).filter(Boolean);
  validation({
    title: !has("title") || String(body.title || "").trim().length >= 3 ? "" : "Enter a job title.",
    category: !has("category") || JOB_CATEGORIES.includes(body.category) ? "" : "Choose a category.",
    location: !has("location") || LOCATIONS.includes(body.location) ? "" : "Choose a location.",
    type: !has("type") || WORK_TYPES.includes(body.type) ? "" : "Choose a work type.",
    description: !has("description") || String(body.description || "").trim().length >= 30 ? "" : "Write a description of at least 30 characters.",
    skills: !has("skills") || (skills.length >= 1 && skills.length <= 12) ? "" : "Add 1 to 12 required skills.",
    targetApplicants: !has("targetApplicants") || (Number.isInteger(Number(body.targetApplicants)) && Number(body.targetApplicants) >= 1 && Number(body.targetApplicants) <= 10000) ? "" : "Enter a number from 1 to 10000.",
    // Feature 6 AC13: a close date in the past is rejected
    closesAt: !has("closesAt") ? "" : !Date.parse(body.closesAt) ? "Choose a close date." : Date.parse(body.closesAt) < Date.now() ? "The close date must be in the future." : "",
  });
  return skills;
}

// ---------- My jobs (Feature 6 AC1, AC2, AC3, AC10) ----------
route("GET", "/recruiter/jobs", (ctx) => {
  const u = requireRole(ctx, "recruiter");
  const items = ctx.db.postedJobs.filter((j) => j.ownerId === u.id).sort((a, b) => Date.parse(b.postedAt) - Date.parse(a.postedAt)).map((j) => jobSummary(ctx.db, j));
  return { items };
});

route("POST", "/recruiter/jobs/suggest-skills", (ctx) => {
  requireRole(ctx, "recruiter");
  return { skills: suggestSkills(`${ctx.body.title || ""} ${ctx.body.description || ""}`) };
});

// ---------- Post a job from a file (PDF or DOCX job description) ----------
const JD_MAX_BYTES = 10 * 1024 * 1024;
const JD_READ_MS = 1500; // the mock "reads" the file for this long
// The mock gets { name, size, type } (the http adapter sends multipart/form-data, field "file")
route("POST", "/recruiter/jobs/import", (ctx) => {
  const u = requireRole(ctx, "recruiter");
  const { name, size } = ctx.body;
  const ext = String(name || "").slice(String(name || "").lastIndexOf(".")).toLowerCase();
  validation({
    file: ![".pdf", ".docx"].includes(ext) ? "Use a PDF or DOCX file."
      : !(size > 0) ? "This file is empty. Choose a different file."
      : size > JD_MAX_BYTES ? "The file is larger than 10 MB. Use a smaller file." : "",
  });
  const id = newId();
  ctx.db.jobImports[id] = { userId: u.id, fileName: String(name), startedAt: Date.now() };
  return { parse: { id, status: "parsing" } };
});
route("GET", "/recruiter/jobs/import/:id", (ctx) => {
  const u = requireRole(ctx, "recruiter");
  const imp = ctx.db.jobImports[ctx.params.id];
  if (!imp || imp.userId !== u.id) throw new ApiError(404, "NOT_FOUND", "We can't find this file upload.");
  if (Date.now() - imp.startedAt < JD_READ_MS) return { id: ctx.params.id, status: "parsing" };
  const sample = jdSampleFor(imp.fileName);
  if (!sample) return { id: ctx.params.id, status: "failed", error: "We couldn't read this file. Try a different file, or fill in the form yourself." };
  const fields = { ...sample.fields, skills: suggestSkills(`${sample.fields.title} ${sample.fields.description}`) };
  // "detected" = the fields that the AI filled; "missing" = fields the file does not show
  return { id: ctx.params.id, status: "done", result: { fields, detected: Object.keys(fields), missing: sample.missing, sampleLabel: sample.label } };
});

route("POST", "/recruiter/jobs", async (ctx) => {
  const u = requireRole(ctx, "recruiter");
  await loadJobs();
  const skills = checkJob(ctx.body);
  const b = ctx.body;
  const job = {
    id: `job-${newId().slice(0, 8)}`, ownerId: u.id, title: b.title.trim(), company: u.company, category: b.category,
    location: b.location, area: b.location, type: b.type, salary: String(b.salary || "").trim() || "Market competitive",
    description: String(b.description).trim(), skills: [...new Set(skills)], targetApplicants: Number(b.targetApplicants),
    postedAt: nowIso(), closesAt: new Date(b.closesAt).toISOString(), anzsco: "", occupation: "",
  };
  ctx.db.postedJobs.push(job);
  return jobSummary(ctx.db, job);
});

route("GET", "/recruiter/jobs/:id", (ctx) => {
  const u = requireRole(ctx, "recruiter");
  const j = ownJob(ctx, u);
  return { ...jobSummary(ctx.db, j), description: j.description };
});

// Edit a job. Everyone who applied gets a notification (Feature 6 AC10, Feature 7 AC3).
route("PATCH", "/recruiter/jobs/:id", async (ctx) => {
  const u = requireRole(ctx, "recruiter");
  await loadJobs();
  const j = ownJob(ctx, u);
  const skills = checkJob(ctx.body, true);
  for (const k of ["title", "category", "location", "type", "salary", "description"]) if (ctx.body[k] !== undefined) j[k] = String(ctx.body[k]).trim();
  if (ctx.body.location !== undefined) j.area = j.location;
  if (ctx.body.skills !== undefined) j.skills = [...new Set(skills)];
  if (ctx.body.targetApplicants !== undefined) j.targetApplicants = Number(ctx.body.targetApplicants);
  if (ctx.body.closesAt !== undefined) j.closesAt = new Date(ctx.body.closesAt).toISOString();
  j.editedAt = nowIso();
  for (const a of appsFor(ctx.db, j.id)) {
    if (FINAL.includes(a.status)) continue;
    notify(ctx.db, a.candidateId, { type: "job_edited", title: `${j.title} was updated`, body: "The employer changed this job. Check the details.", link: `/applications/${a.id}` });
  }
  return { ...jobSummary(ctx.db, j), description: j.description };
});

// ---------- Applications for a job (Feature 6 AC4–AC9) ----------
route("GET", "/recruiter/jobs/:id/applications", async (ctx) => {
  const u = requireRole(ctx, "recruiter");
  await loadJobs();
  const j = ownJob(ctx, u);
  const items = appsFor(ctx.db, j.id).sort((a, b) => Date.parse(b.updatedAt) - Date.parse(a.updatedAt)).map((a) => ({
    id: a.id, alias: a.snapshot.alias, origin: a.origin, status: a.status, statusLabel: STATUS_LABEL[a.status],
    coverage: a.match.coverage, matched: a.match.skills.filter((s) => s.status === "match").length, total: a.match.skills.length,
    awaiting: awaiting(a), updatedAt: a.updatedAt, createdAt: a.createdAt,
  }));
  return { job: jobSummary(ctx.db, j), items };
});

function recruiterView(db, a) {
  const cand = db.users.find((x) => x.id === a.candidateId);
  const theirs = a.feedback?.candidate || null;
  // "accepted" is allowed only after the interview time is confirmed
  const next = TRANSITIONS[a.status].filter((s) => s !== "accepted" || a.slotConfirmed);
  return {
    id: a.id, job: jobBrief(db, a.jobId), origin: a.origin, status: a.status, statusLabel: STATUS_LABEL[a.status],
    note: a.note, history: a.history, slots: a.slots, chosenSlotId: a.chosenSlotId, slotConfirmed: a.slotConfirmed,
    // Anonymity ends only when the candidate agrees, when they choose an interview time (decision Q4)
    identity: a.identityShared && cand ? { name: cand.name, email: cand.email } : null,
    offer: a.offer, snapshot: a.snapshot, match: a.match,
    feedback: { mine: a.feedback?.recruiter || null, theirs: theirs ? { toOther: theirs.toOther, at: theirs.at } : null },
    allowedNext: next, canConfirmSlot: a.status === "interview" && !!a.chosenSlotId && !a.slotConfirmed, final: FINAL.includes(a.status),
    createdAt: a.createdAt, updatedAt: a.updatedAt,
  };
}
const ownApp = (ctx) => {
  const u = requireRole(ctx, "recruiter");
  const a = ctx.db.applications.find((x) => x.id === ctx.params.id && x.recruiterId === u.id);
  if (!a) throw new ApiError(404, "NOT_FOUND", "We can't find this application.");
  return { u, a };
};

route("GET", "/recruiter/applications/:id", async (ctx) => {
  const { a } = ownApp(ctx);
  await loadJobs();
  return recruiterView(ctx.db, a);
});

// Change the status. Only valid transitions (Feature 6 AC6, AC14). Moving to Review locks the candidate's edits (AC7).
route("POST", "/recruiter/applications/:id/status", async (ctx) => {
  const { a } = ownApp(ctx);
  await loadJobs();
  const { to, slots = [], offer = "" } = ctx.body;
  if (!TRANSITIONS[a.status].includes(to)) {
    throw new ApiError(409, "CONFLICT", `You can't move an application from ${STATUS_LABEL[a.status]} to ${STATUS_LABEL[to] || to}.`);
  }
  const job = findJob(ctx.db, a.jobId);
  const title = job ? job.title : "your application";
  if (to === "interview") {
    const times = list(slots).filter((s) => Date.parse(s));
    validation({ slots: times.length >= 1 && times.length <= 3 ? (times.every((s) => Date.parse(s) > Date.now()) ? "" : "Choose times in the future.") : "Offer 1 to 3 interview times." });
    a.slots = times.map((s) => ({ id: newId().slice(0, 8), start: new Date(s).toISOString() }));
    a.chosenSlotId = null;
    a.slotConfirmed = false;
    addHistory(a, "interview", "recruiter", `Offered ${a.slots.length} interview time${a.slots.length > 1 ? "s" : ""}`);
    notify(ctx.db, a.candidateId, { type: "interview_slots", title: `Interview times for ${title}`, body: "Choose a time that works for you.", link: `/applications/${a.id}` });
  } else if (to === "accepted") {
    if (!a.slotConfirmed) throw new ApiError(409, "CONFLICT", "Confirm the interview time first. Then record the result.");
    addHistory(a, "accepted", "recruiter");
    notify(ctx.db, a.candidateId, { type: "result", title: `Good news about ${title}`, body: "The employer accepted you after the interview. An offer can follow.", link: `/applications/${a.id}`, email: true });
  } else if (to === "offer") {
    validation({ offer: String(offer).trim().length >= 10 ? "" : "Write the offer details (at least 10 characters)." });
    a.offer = { text: scrubContact(offer).trim(), sentAt: nowIso() };
    addHistory(a, "offer", "recruiter");
    notify(ctx.db, a.candidateId, { type: "offer", title: `You have an offer for ${title}`, body: "Read it and answer.", link: `/applications/${a.id}`, email: true });
  } else if (to === "rejected") {
    addHistory(a, "rejected", "recruiter");
    notify(ctx.db, a.candidateId, { type: "result", title: `Update on ${title}`, body: "The employer did not select you this time. You can give feedback.", link: `/applications/${a.id}`, email: true });
  } else {
    addHistory(a, to, "recruiter");
    notify(ctx.db, a.candidateId, { type: "status", title: `${title}: ${STATUS_LABEL[to]}`, body: to === "review" ? "The employer is reviewing your application." : "", link: `/applications/${a.id}` });
  }
  track(ctx.db, { type: "job_respond", targetType: "application", targetId: a.id, actorId: a.recruiterId });
  return recruiterView(ctx.db, a);
});

route("POST", "/recruiter/applications/:id/confirm-slot", async (ctx) => {
  const { a } = ownApp(ctx);
  await loadJobs();
  if (!(a.status === "interview" && a.chosenSlotId && !a.slotConfirmed)) throw new ApiError(409, "CONFLICT", "There is no interview time to confirm.");
  a.slotConfirmed = true;
  a.updatedAt = nowIso();
  a.history.push({ status: "interview", at: a.updatedAt, by: "recruiter", note: "Confirmed the interview time" });
  const slot = a.slots.find((s) => s.id === a.chosenSlotId);
  notify(ctx.db, a.candidateId, { type: "slot_confirmed", title: "Your interview time is confirmed", body: slot ? new Date(slot.start).toLocaleString("en-AU", { dateStyle: "medium", timeStyle: "short" }) : "", link: `/applications/${a.id}` });
  return recruiterView(ctx.db, a);
});

route("POST", "/recruiter/applications/:id/feedback", async (ctx) => {
  const { u, a } = ownApp(ctx);
  await loadJobs();
  if (!FINAL.includes(a.status)) throw new ApiError(409, "CONFLICT", "You can give feedback when the application is finished.");
  const { toOther = "", toTeam = "" } = ctx.body;
  validation({
    toOther: String(toOther).length <= 1000 ? "" : "Use 1000 characters or fewer.",
    toTeam: String(toTeam).length <= 1000 ? "" : "Use 1000 characters or fewer.",
    form: String(toOther).trim() || String(toTeam).trim() ? "" : "Write feedback in at least one box.",
  });
  a.feedback.recruiter = { toOther: scrubContact(toOther).trim(), toTeam: String(toTeam).trim(), at: nowIso() };
  if (a.feedback.recruiter.toOther) notify(ctx.db, a.candidateId, { type: "feedback", title: `${u.company} sent you feedback`, link: `/applications/${a.id}` });
  return recruiterView(ctx.db, a);
});

// ---------- Anonymous candidates (Feature 5) ----------
const candidatePool = (db) => db.users.filter((x) => x.role === "candidate" && x.onboarding === "done" && sharedProfileOf(x).skills.length);
function candidateCard(db, recruiter, cand, job) {
  const shared = sharedProfileOf(cand);
  const sm = skillMatch(job ? job.skills : [], namesFromList(shared.skills));
  const app = job && db.applications.find((a) => a.jobId === job.id && a.candidateId === cand.id);
  return {
    id: cand.id, alias: shared.alias, roles: shared.roles, skills: shared.skills, qualifications: shared.qualifications,
    years: shared.years, industries: shared.industries, locations: shared.locations,
    coverage: sm.coverage, matched: sm.matched, partial: sm.partial, total: job ? job.skills.length : 0,
    saved: (db.savedCandidates[recruiter.id] || []).includes(cand.id),
    applicationId: app && app.recruiterId === recruiter.id ? app.id : null,
  };
}
function pickJob(ctx, u) {
  const own = ctx.db.postedJobs.filter((j) => j.ownerId === u.id);
  const id = ctx.query.jobId;
  const j = (id && own.find((x) => x.id === id)) || own.find((x) => isOpen({ closesAt: new Date(x.closesAt) })) || own[0] || null;
  return j ? findJob(ctx.db, j.id) : null;
}

// Shortlist ordered by the skill coverage for the chosen job. Basic: the top N only (Feature 5 AC7).
route("GET", "/recruiter/candidates", async (ctx) => {
  const u = requireRole(ctx, "recruiter");
  await loadJobs();
  const job = pickJob(ctx, u);
  const ent = entitlementsOf(ctx.db, u);
  const skipped = new Set(ctx.db.skippedCandidates[u.id] || []);
  const view = ctx.query.view === "saved" ? "saved" : "all";
  let all = candidatePool(ctx.db).filter((c) => !skipped.has(c.id)).map((c) => candidateCard(ctx.db, u, c, job));
  if (view === "saved") all = all.filter((c) => c.saved);
  all.sort((a, b) => (b.coverage ?? -1) - (a.coverage ?? -1) || b.matched - a.matched || a.alias.localeCompare(b.alias));
  const items = ent.topN ? all.slice(0, ent.topN) : all;
  items.forEach((c) => track(ctx.db, { type: "profile_appear", targetType: "candidate", targetId: c.id, actorId: u.id }));
  return { job: job ? { id: job.id, title: job.title, skills: job.skills } : null, items, total: all.length, limitedTo: ent.topN, plan: ent.plan, skippedCount: skipped.size };
});

route("GET", "/recruiter/candidates/:id", async (ctx) => {
  const u = requireRole(ctx, "recruiter");
  await loadJobs();
  const cand = candidatePool(ctx.db).find((c) => c.id === ctx.params.id);
  if (!cand) throw new ApiError(404, "NOT_FOUND", "We can't find this profile.");
  const job = pickJob(ctx, u);
  const card = candidateCard(ctx.db, u, cand, job);
  const sm = skillMatch(job ? job.skills : [], namesFromList(card.skills));
  track(ctx.db, { type: "profile_watch", targetType: "candidate", targetId: cand.id, actorId: u.id });
  return { ...card, job: job ? { id: job.id, title: job.title } : null, match: { coverage: sm.coverage, skills: sm.items }, targetRoles: sharedProfileOf(cand).targetRoles, workTypes: sharedProfileOf(cand).workTypes, fieldsOfStudy: sharedProfileOf(cand).fieldsOfStudy, entitlements: entitlementsOf(ctx.db, u) };
});

const toggleList = (obj, key, id, on) => {
  const l = obj[key] || (obj[key] = []);
  const has = l.includes(id);
  if (on && !has) l.push(id);
  if (!on && has) obj[key] = l.filter((x) => x !== id);
};
route("PUT", "/recruiter/candidates/:id/save", (ctx) => {
  const u = requireRole(ctx, "recruiter");
  toggleList(ctx.db.savedCandidates, u.id, ctx.params.id, true);
  track(ctx.db, { type: "profile_saved", targetType: "candidate", targetId: ctx.params.id, actorId: u.id });
  return { id: ctx.params.id, saved: true };
});
route("DELETE", "/recruiter/candidates/:id/save", (ctx) => {
  const u = requireRole(ctx, "recruiter");
  toggleList(ctx.db.savedCandidates, u.id, ctx.params.id, false);
  return { id: ctx.params.id, saved: false };
});
route("PUT", "/recruiter/candidates/:id/skip", (ctx) => {
  const u = requireRole(ctx, "recruiter");
  toggleList(ctx.db.skippedCandidates, u.id, ctx.params.id, true);
  track(ctx.db, { type: "profile_skip", targetType: "candidate", targetId: ctx.params.id, actorId: u.id });
  return { id: ctx.params.id, skipped: true };
});
route("DELETE", "/recruiter/candidates/skipped", (ctx) => {
  const u = requireRole(ctx, "recruiter");
  ctx.db.skippedCandidates[u.id] = [];
  return { ok: true };
});

// Premium: contact a candidate who did not apply (headhunting). Status "contacted".
route("POST", "/recruiter/candidates/:id/contact", async (ctx) => {
  const u = requireRole(ctx, "recruiter");
  requirePremium(ctx.db, u, "canContact");
  await loadJobs();
  const cand = candidatePool(ctx.db).find((c) => c.id === ctx.params.id);
  if (!cand) throw new ApiError(404, "NOT_FOUND", "We can't find this profile.");
  const posted = ctx.db.postedJobs.find((j) => j.id === ctx.body.jobId && j.ownerId === u.id);
  if (!posted) throw new ApiError(400, "VALIDATION_ERROR", "Choose one of your jobs.", { jobId: "Choose one of your jobs." });
  if (ctx.db.applications.some((a) => a.jobId === posted.id && a.candidateId === cand.id)) throw new ApiError(409, "CONFLICT", "This person is already in the pipeline for this job.");
  validation({ message: String(ctx.body.message || "").trim().length >= 10 && String(ctx.body.message).length <= 500 ? "" : "Write a message of 10 to 500 characters." });
  const job = findJob(ctx.db, posted.id);
  const snapshot = sharedProfileOf(cand);
  const a = {
    id: newId(), jobId: posted.id, candidateId: cand.id, recruiterId: u.id, origin: "contacted", status: "contacted",
    note: "", message: scrubContact(ctx.body.message).trim(), snapshot, match: snapshotMatch(job, snapshot),
    history: [], slots: [], chosenSlotId: null, slotConfirmed: false, identityShared: false, offer: null, feedback: {}, createdAt: nowIso(), updatedAt: nowIso(),
  };
  addHistory(a, "contacted", "recruiter", a.message);
  ctx.db.applications.push(a);
  notify(ctx.db, cand.id, { type: "contacted", title: `${u.company} invited you to apply for ${posted.title}`, body: a.message, link: `/applications/${a.id}` });
  return recruiterView(ctx.db, a);
});

// Premium: compare two profiles side by side, per skill. No combined score, no ranking of the two people.
route("GET", "/recruiter/compare", async (ctx) => {
  const u = requireRole(ctx, "recruiter");
  requirePremium(ctx.db, u, "canCompare");
  await loadJobs();
  const job = pickJob(ctx, u);
  const pool = candidatePool(ctx.db);
  const one = (id) => {
    const c = pool.find((x) => x.id === id);
    if (!c) throw new ApiError(404, "NOT_FOUND", "We can't find one of the profiles.");
    const s = sharedProfileOf(c);
    return { id: c.id, alias: s.alias, roles: s.roles, qualifications: s.qualifications, years: s.years, skills: skillMatch(job ? job.skills : [], namesFromList(s.skills)).items, otherSkills: s.skills.filter((x) => !(job ? job.skills : []).includes(x)) };
  };
  return { job: job ? { id: job.id, title: job.title, skills: job.skills } : null, a: one(ctx.query.a), b: one(ctx.query.b) };
});

export { recruiterView };
