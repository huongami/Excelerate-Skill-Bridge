// MOCK BACKEND — applications and the hiring lifecycle (Features 4 and 6). The real backend replaces this file.
// The state machine is enforced here (server side). The system never changes a status on its own (Feature 6 AC12).
import { route, ApiError, newId, validation, requireRole, notify, track, nowIso, sharedProfileOf, scrubContact, list } from "./core.js";
import { loadJobs, findJob, isOpen, skillMatch, namesFromList } from "./jobs.js";

// Flow: applied → review → interview → accepted | rejected → offer → confirmed (candidate rejects offer → rejected).
// Recruiter-initiated (premium): contacted → interview → same flow. The candidate can decline: contacted → declined.
export const TRANSITIONS = {
  applied: ["review", "rejected"],
  contacted: ["interview", "rejected"],
  review: ["interview", "rejected"],
  interview: ["accepted", "rejected"],
  accepted: ["offer", "rejected"],
  offer: [],          // the candidate answers the offer
  confirmed: [], rejected: [], declined: [],
};
export const FINAL = ["confirmed", "rejected", "declined"];
export const STATUS_LABEL = {
  applied: "Applied", contacted: "Contacted", review: "In review", interview: "Interview", accepted: "Accepted",
  offer: "Offer", confirmed: "Confirmed", rejected: "Not selected", declined: "Declined",
};

export function addHistory(app, status, by, note = "") {
  app.status = status;
  app.updatedAt = nowIso();
  app.history.push({ status, at: app.updatedAt, by, note });
}

// The job a recruiter owns (posted on Jinder). Catalogue jobs have no owner in the mock.
export const ownerOf = (db, job) => (job && job.ownerId ? db.users.find((u) => u.id === job.ownerId) : null);

export function jobBrief(db, jobId) {
  const j = findJob(db, jobId);
  return j ? { id: j.id, title: j.title, company: j.company, location: j.location, area: j.area, type: j.type, status: isOpen(j) ? "open" : "closed", skills: j.skills, ownedOnJinder: !!j.ownerId } : { id: jobId, title: "Removed job", company: "", location: "", area: "", type: "", status: "closed", skills: [], ownedOnJinder: false };
}

// The match that the recruiter and the candidate see: per skill of the job, against the shared skills only
export function snapshotMatch(job, snapshot) {
  const sm = skillMatch(job ? job.skills : [], namesFromList(snapshot.skills));
  return { coverage: sm.coverage, skills: sm.items };
}

// ---------- Candidate view of an application ----------
function candidateView(db, a) {
  const theirs = a.feedback?.recruiter || null;
  return {
    id: a.id, jobId: a.jobId, job: jobBrief(db, a.jobId), origin: a.origin, status: a.status, statusLabel: STATUS_LABEL[a.status],
    note: a.note, canEdit: a.status === "applied", final: FINAL.includes(a.status),
    history: a.history, slots: a.slots, chosenSlotId: a.chosenSlotId, slotConfirmed: a.slotConfirmed, identityShared: a.identityShared,
    offer: a.offer, snapshot: a.snapshot, match: a.match,
    feedback: { mine: a.feedback?.candidate || null, theirs: theirs ? { toOther: theirs.toOther, at: theirs.at } : null },
    createdAt: a.createdAt, updatedAt: a.updatedAt,
  };
}
const mine = (ctx) => {
  const u = requireRole(ctx, "candidate");
  const a = ctx.db.applications.find((x) => x.id === ctx.params.id && x.candidateId === u.id);
  if (!a) throw new ApiError(404, "NOT_FOUND", "We can't find this application.");
  return { u, a };
};
const mustBe = (a, statuses, msg) => { if (!statuses.includes(a.status)) throw new ApiError(409, "CONFLICT", msg); };

// ---------- Apply (Feature 4 AC1, AC2, AC12, AC13) ----------
route("POST", "/applications", async (ctx) => {
  const u = requireRole(ctx, "candidate");
  await loadJobs();
  const { jobId, note = "" } = ctx.body;
  const job = findJob(ctx.db, jobId);
  if (!job) throw new ApiError(404, "NOT_FOUND", "This job does not exist or was removed.");
  if (!isOpen(job)) throw new ApiError(409, "CONFLICT", "This job is closed. You can't apply now.");
  if (ctx.db.applications.some((a) => a.candidateId === u.id && a.jobId === jobId)) throw new ApiError(409, "CONFLICT", "You have already applied for this job.");
  validation({ note: String(note).length <= 500 ? "" : "Use 500 characters or fewer." });
  const snapshot = sharedProfileOf(u);
  if (!snapshot.skills.length) throw new ApiError(409, "CONFLICT", "Accept at least one translated skill before you apply. Go to Settings › Review translated skills.");
  // A frozen copy of the translated profile as submitted (Feature 4 NFR). Never the original CV.
  const a = {
    id: newId(), jobId, candidateId: u.id, recruiterId: job.ownerId || null, origin: "applied",
    status: "applied", note: scrubContact(note).trim(), snapshot, match: snapshotMatch(job, snapshot),
    history: [], slots: [], chosenSlotId: null, slotConfirmed: false, identityShared: false, offer: null,
    feedback: {}, createdAt: nowIso(), updatedAt: nowIso(),
  };
  addHistory(a, "applied", "candidate");
  ctx.db.applications.push(a);
  track(ctx.db, { type: "job_apply", targetType: "job", targetId: jobId, actorId: u.id });
  const owner = ownerOf(ctx.db, job);
  if (owner) notify(ctx.db, owner.id, { type: "new_application", title: `New application for ${job.title}`, body: `${u.alias} applied.`, link: `/review/${a.id}` });
  return candidateView(ctx.db, a);
});

route("GET", "/applications", async (ctx) => {
  const u = requireRole(ctx, "candidate");
  await loadJobs();
  const items = ctx.db.applications.filter((a) => a.candidateId === u.id)
    .sort((x, y) => Date.parse(y.updatedAt) - Date.parse(x.updatedAt))
    .map((a) => { const v = candidateView(ctx.db, a); return { id: v.id, job: v.job, status: v.status, statusLabel: v.statusLabel, origin: v.origin, final: v.final, coverage: v.match.coverage, createdAt: v.createdAt, updatedAt: v.updatedAt, needsAction: (a.status === "interview" && !a.chosenSlotId) || a.status === "offer" || a.status === "contacted" || (FINAL.includes(a.status) && !a.feedback?.candidate) }; });
  return { items };
});

route("GET", "/applications/:id", async (ctx) => {
  const { a } = mine(ctx);
  await loadJobs();
  return candidateView(ctx.db, a);
});

// Edit until the recruiter moves it to Review (Feature 4 AC6, AC14)
route("PATCH", "/applications/:id", async (ctx) => {
  const { a } = mine(ctx);
  await loadJobs();
  mustBe(a, ["applied"], "The employer is reviewing your application. You can't change it now.");
  validation({ note: String(ctx.body.note ?? "").length <= 500 ? "" : "Use 500 characters or fewer." });
  a.note = scrubContact(ctx.body.note ?? "").trim();
  a.updatedAt = nowIso();
  return candidateView(ctx.db, a);
});

// Pick an interview slot (Feature 4 AC8, AC15). The candidate can agree to share their identity (decision Q4).
route("POST", "/applications/:id/slot", async (ctx) => {
  const { u, a } = mine(ctx);
  await loadJobs();
  mustBe(a, ["interview"], "This application has no interview to book.");
  if (a.slotConfirmed) throw new ApiError(409, "CONFLICT", "The employer has confirmed your interview time.");
  const slot = a.slots.find((s) => s.id === ctx.body.slotId);
  if (!slot) throw new ApiError(409, "CONFLICT", "This time is no longer available. Choose another time.");
  if (Date.parse(slot.start) < Date.now()) throw new ApiError(409, "CONFLICT", "This time has passed. Choose another time.");
  a.chosenSlotId = slot.id;
  a.identityShared = !!ctx.body.shareIdentity;
  a.updatedAt = nowIso();
  a.history.push({ status: "interview", at: a.updatedAt, by: "candidate", note: "Chose an interview time" + (a.identityShared ? " and shared their name and email" : "") });
  const job = findJob(ctx.db, a.jobId);
  if (a.recruiterId) notify(ctx.db, a.recruiterId, { type: "slot_chosen", title: `${u.alias} chose an interview time`, body: job ? job.title : "", link: `/review/${a.id}` });
  return candidateView(ctx.db, a);
});

// Answer an offer (Feature 4 AC10). A rejected offer ends in "rejected".
route("POST", "/applications/:id/offer-reply", async (ctx) => {
  const { u, a } = mine(ctx);
  await loadJobs();
  mustBe(a, ["offer"], "There is no offer to answer.");
  const accept = ctx.body.accept === true;
  addHistory(a, accept ? "confirmed" : "rejected", "candidate", accept ? "Accepted the offer" : "Declined the offer");
  if (a.recruiterId) notify(ctx.db, a.recruiterId, { type: "offer_reply", title: `${u.alias} ${accept ? "accepted" : "declined"} your offer`, link: `/review/${a.id}` });
  track(ctx.db, { type: "job_respond", targetType: "job", targetId: a.jobId, actorId: u.id });
  return candidateView(ctx.db, a);
});

// Decline a recruiter's contact (premium path)
route("POST", "/applications/:id/decline", async (ctx) => {
  const { u, a } = mine(ctx);
  await loadJobs();
  mustBe(a, ["contacted"], "You can decline only an invitation.");
  addHistory(a, "declined", "candidate", "Declined the invitation");
  if (a.recruiterId) notify(ctx.db, a.recruiterId, { type: "contact_declined", title: `${u.alias} declined your invitation`, link: `/review/${a.id}` });
  return candidateView(ctx.db, a);
});

// Feedback at the final stage (Feature 4 AC11): to the other side and to the Jinder team
route("POST", "/applications/:id/feedback", async (ctx) => {
  const { u, a } = mine(ctx);
  await loadJobs();
  mustBe(a, FINAL, "You can give feedback when the application is finished.");
  const { toOther = "", toTeam = "" } = ctx.body;
  validation({
    toOther: String(toOther).length <= 1000 ? "" : "Use 1000 characters or fewer.",
    toTeam: String(toTeam).length <= 1000 ? "" : "Use 1000 characters or fewer.",
    form: String(toOther).trim() || String(toTeam).trim() ? "" : "Write feedback in at least one box.",
  });
  a.feedback.candidate = { toOther: scrubContact(toOther).trim(), toTeam: String(toTeam).trim(), at: nowIso() };
  if (a.recruiterId && a.feedback.candidate.toOther) notify(ctx.db, a.recruiterId, { type: "feedback", title: `${u.alias} sent you feedback`, link: `/review/${a.id}` });
  return candidateView(ctx.db, a);
});

export { candidateView };
