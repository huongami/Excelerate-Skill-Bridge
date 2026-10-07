// Application status: ribbon, timeline and per-skill match list (Features 4, 5, 6).
import { iconHtml as icon, esc, formatDate } from "../core/dom.js";
import { skillLevelLabel } from "../data/levels.js";

// Status ribbon: text always shows (no colour-only meaning; Feature 4 NFR)
const TONE = { applied: "neutral", contacted: "blue", review: "blue", interview: "yellow", accepted: "green", offer: "green", confirmed: "green", rejected: "rose", declined: "neutral" };
export const ribbonHtml = (status, label) => `<span class="ribbon ribbon-${TONE[status] || "neutral"}"><span class="sr-only">Status: </span>${esc(label)}</span>`;

// The main path of the lifecycle, for the stepper
const PATH = [["applied", "Applied"], ["review", "In review"], ["interview", "Interview"], ["accepted", "Accepted"], ["offer", "Offer"], ["confirmed", "Confirmed"]];
const ORDER = { contacted: 0, applied: 0, review: 1, interview: 2, accepted: 3, offer: 4, confirmed: 5 };

export function stepperHtml(app) {
  const ended = app.status === "rejected" || app.status === "declined";
  // The last step that was reached before an end
  const reached = ended ? Math.max(...app.history.map((h) => ORDER[h.status] ?? -1)) : ORDER[app.status];
  const steps = PATH.map(([key, label], i) => {
    const state = i < reached || (i === reached && app.status === "confirmed") ? "done" : i === reached && !ended ? "current" : "todo";
    const lbl = i === 0 && app.origin === "contacted" ? "Contacted" : label;
    return `<li class="step-${state}"${state === "current" ? ' aria-current="step"' : ""}><span class="stepper-dot">${state === "done" ? icon("check") : i + 1}</span><span class="stepper-label">${esc(lbl)}</span></li>`;
  }).join("");
  const end = ended ? `<li class="step-ended"><span class="stepper-dot">${icon("x")}</span><span class="stepper-label">${app.status === "declined" ? "Declined" : "Not selected"}</span></li>` : "";
  return `<ol class="stepper" aria-label="Application progress">${steps}${end}</ol>`;
}

const WHO = { candidate: "Talent", recruiter: "Employer", system: "Jinder" };
export function historyHtml(history, { you = "candidate" } = {}) {
  return `<ol class="history">${[...history].reverse().map((h) => `
    <li><span class="history-when">${esc(new Date(h.at).toLocaleString("en-AU", { dateStyle: "medium", timeStyle: "short" }))}</span>
      <span class="history-what"><strong>${esc(WHO[h.by] === WHO[you] ? "You" : WHO[h.by] || h.by)}</strong> — ${esc(h.note || statusText(h.status))}</span></li>`).join("")}</ol>`;
}
const statusText = (s) => ({ applied: "Applied", contacted: "Sent an invitation", review: "Started the review", interview: "Interview", accepted: "Accepted after the interview", offer: "Sent an offer", confirmed: "Accepted the offer", rejected: "Not selected", declined: "Declined" }[s] || s);

// Per-skill match list (match / partial / gap) with text, not only colour
export function skillMatchHtml(items, { you = true } = {}) {
  if (!items || !items.length) return `<p class="muted">This job lists no skills yet.</p>`;
  const LABEL = { match: you ? "You have it" : "Has it", partial: "Related", gap: "Gap" };
  const ICON = { match: "check", partial: "target", gap: "alert" };
  // The status "partial" is two things: the skill is held below the asked level (`fitStatus` "below"), or a related skill is held. Say which.
  const below = (i) => i.status === "partial" && i.fitStatus === "below";
  const detail = (i) => {
    if (i.via) return `<span class="sm-via">via ${esc(i.via)}</span>`;
    if (below(i) && skillLevelLabel(i.level) && skillLevelLabel(i.required)) return `<span class="sm-via">${you ? "You" : "Has"}: ${esc(skillLevelLabel(i.level))} · Needs: ${esc(skillLevelLabel(i.required))}</span>`;
    return "";
  };
  return `<ul class="skill-match">${items.map((i) => `
    <li class="sm-${i.status}">${icon(ICON[i.status])}<span class="sm-name">${esc(i.name)}</span><span class="sm-state">${below(i) ? "Below level" : LABEL[i.status]}</span>${detail(i)}</li>`).join("")}</ul>`;
}

// "4 of 6 skills" summary text (coverage is a summary of skills for one job, not a score on a person)
export function coverageText(match) {
  const items = match?.skills || [];
  if (!items.length) return "No skills listed";
  const m = items.filter((i) => i.status === "match").length;
  const p = items.filter((i) => i.status === "partial").length;
  return `${m} of ${items.length} skills${p ? ` + ${p} related` : ""}`;
}

export const slotText = (iso) => new Date(iso).toLocaleString("en-AU", { weekday: "short", day: "numeric", month: "short", hour: "numeric", minute: "2-digit" });
export { formatDate };
