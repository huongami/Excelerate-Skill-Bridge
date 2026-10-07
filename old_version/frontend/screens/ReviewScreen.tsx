"use client";

import Link from "next/link";
import { useState } from "react";
import { createMatch, decide, parseJd } from "@/frontend/api/client";
import { Status } from "@/frontend/components/Status";
import { useSessionStore } from "@/frontend/state/sessionStore";

const defaultJd = "Product backlog management and prioritisation are essential. You must demonstrate product discovery, user research and requirements management. Stakeholder management and agile delivery are required. SQL, data analysis and dashboard development experience are preferred.";

export function ReviewScreen() {
  const { profile, skillProfile, frequency, jd, match, decisions, setJd, setMatch, setDecisions } = useSessionStore();
  const [text, setText] = useState(defaultJd);
  const [file, setFile] = useState<File>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();

  async function analyseJd() {
    setBusy(true); setError(undefined);
    try { const result = await parseJd(file, text); setText(result.rawText); setJd(result.jd); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to parse JD"); }
    finally { setBusy(false); }
  }

  async function runMatch() {
    if (!profile || !skillProfile || !jd) return;
    setBusy(true); setError(undefined);
    try { const result = await createMatch(profile.profileId, profile.revision, text); setMatch(result.match); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to match JD"); }
    finally { setBusy(false); }
  }

  async function act(action: "shortlist" | "needs_more_info" | "not_a_fit") {
    if (!match) return;
    setBusy(true);
    try { const result = await decide(match.matchId, action); setDecisions(result.decisionEvents); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to record decision"); }
    finally { setBusy(false); }
  }

  const candidateLabels = new Set(skillProfile?.groups.flatMap((group) => group.skills.map((skill) => skill.label.toLowerCase())) ?? []);
  const rankedCandidateSkills = (frequency?.skills ?? []).filter((skill) => candidateLabels.has(skill.label.toLowerCase()));

  return <>
    <section className="hero"><p className="eyebrow">Step 3 · Sarah recruiter review</p><h1>Upload a JD. Map priorities. Compare skills.</h1><p>JD priority weights explain what the role values; they never become an overall candidate score or automated decision.</p></section>
    <Status error={error} busy={busy}/>
    <div className="grid two">
      <section className="card"><h2>1. Job description input</h2><label className="upload jd-upload"><strong>Upload JD</strong><input type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={(event) => { setFile(event.target.files?.[0]); setJd(undefined); }}/><span>{file?.name ?? "PDF or DOCX, maximum 10 MB"}</span></label><label>Or paste JD text<textarea value={text} onChange={(event) => { setText(event.target.value); setFile(undefined); setJd(undefined); }} rows={8}/></label><button className="primary" onClick={analyseJd} disabled={busy}>Parse & map JD skills</button></section>
      <section className="card"><div className="section-head"><h2>2. Skill priority map</h2><span>{jd ? `${jd.skills.length} skills · 100%` : "Waiting for JD"}</span></div>{jd ? <div className="weight-list">{jd.skills.map((skill) => <article className="weight-row" key={skill.skillId}><div><strong>{skill.label}</strong><small>{skill.importance} · {skill.requirement}</small></div><div className="weight-bar"><i style={{width: `${skill.weight}%`}}/><span>{skill.weight}%</span></div><p>{skill.evidenceSpan}</p></article>)}</div> : <p className="muted">Upload or paste a JD, then parse it to see normalised skills, evidence and transparent priority weights.</p>}<div className="candidate-match-gate">{profile && skillProfile ? <p><strong>Candidate ready:</strong> {profile.name.value}</p> : <p><strong>JD analysis is available now.</strong> Add a candidate only when you are ready to compare. <Link href="/profile">Build candidate profile →</Link></p>}</div><button className="primary match-cta" onClick={runMatch} disabled={busy || !jd || !profile || !skillProfile}>3. Create per-skill candidate match</button></section>
    </div>
    <section className="card"><h2>Recruiter decision</h2><p>No automatic action is available. Decision buttons activate after a match is created.</p><div className="decisions"><button disabled={!match || busy} onClick={() => act("shortlist")}>Shortlist</button><button disabled={!match || busy} onClick={() => act("needs_more_info")}>Needs more info</button><button disabled={!match || busy} onClick={() => act("not_a_fit")}>Not a fit</button></div><div className="event-log">{decisions.length ? decisions.map((event) => <p key={event.eventId}><strong>{event.action.replaceAll("_", " ")}</strong> · {new Date(event.createdAt).toLocaleString()}</p>) : "No decision recorded."}</div></section>
    {rankedCandidateSkills.length > 0 && <section className="card"><div className="section-head"><h2>{profile?.name.value}&apos;s translated skills across similar JDs</h2><span>{frequency?.robustness}</span></div>{rankedCandidateSkills.map((skill) => <article className="match" key={skill.skillId}><div><strong>{skill.label}</strong><span>{skill.documentCount} of {frequency?.jdCount} JDs</span></div></article>)}</section>}
    {match && <section className="card"><div className="section-head"><h2>Per-skill results</h2><span>No overall candidate score</span></div>{match.skillMatches.map((item) => <article className={`match ${item.matchRate}`} key={item.jdSkillId}><div><strong>{item.label} · {item.weight}% JD priority</strong><span>{item.matchRate}</span></div><p>{item.reason}</p><small>{item.importance} · JD evidence: {item.jdEvidence}</small></article>)}</section>}
  </>;
}
