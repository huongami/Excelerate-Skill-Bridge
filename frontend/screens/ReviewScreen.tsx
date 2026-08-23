"use client";

import Link from "next/link";
import { useState } from "react";
import { createMatch, decide } from "@/frontend/api/client";
import { Status } from "@/frontend/components/Status";
import { useSessionStore } from "@/frontend/state/sessionStore";

const defaultJd = "We need stakeholder alignment, performance analytics, paid media operations and marketing automation tools. The role coordinates campaign planning across teams.";

export function ReviewScreen() {
  const { profile, skillProfile, match, decisions, setMatch, setDecisions } = useSessionStore();
  const [text, setText] = useState(defaultJd); const [busy, setBusy] = useState(false); const [error, setError] = useState<string>();
  if (!profile || !skillProfile) return <section className="card empty"><h1>No candidate skill profile</h1><Link className="primary link" href="/profile">Start with profile</Link></section>;
  async function runMatch() { if (!profile) return; setBusy(true); setError(undefined); try { const result = await createMatch(profile.profileId, profile.revision, text); setMatch(result.match); } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to match JD"); } finally { setBusy(false); } }
  async function act(action: "shortlist" | "needs_more_info" | "not_a_fit") { if (!match) return; setBusy(true); try { const result = await decide(match.matchId, action); setDecisions(result.decisionEvents); } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to record decision"); } finally { setBusy(false); } }
  return <><section className="hero"><p className="eyebrow">Step 3 · Recruiter review</p><h1>Compare skills. Keep the decision human.</h1><p>Each JD requirement receives its own match level and evidence chain.</p></section><Status error={error} busy={busy}/><div className="grid two"><section className="card"><h2>Job description</h2><textarea value={text} onChange={(event) => setText(event.target.value)} rows={9}/><button className="primary" onClick={runMatch} disabled={busy}>Create per-skill match</button></section><section className="card"><h2>Recruiter decision</h2><p>No automatic action is available.</p><div className="decisions"><button onClick={() => act("shortlist")}>Shortlist</button><button onClick={() => act("needs_more_info")}>Needs more info</button><button onClick={() => act("not_a_fit")}>Not a fit</button></div><div className="event-log">{decisions.length ? decisions.map((event) => <p key={event.eventId}><strong>{event.action.replaceAll("_", " ")}</strong> · {new Date(event.createdAt).toLocaleString()}</p>) : "No decision recorded."}</div></section></div>
    {match && <section className="card"><div className="section-head"><h2>Per-skill results</h2><span>No overall candidate score</span></div>{match.skillMatches.map((item) => <article className={`match ${item.matchRate}`} key={item.jdSkillId}><div><strong>{item.label}</strong><span>{item.matchRate}</span></div><p>{item.reason}</p><small>JD evidence: {item.jdEvidence}</small></article>)}</section>}</>;
}
