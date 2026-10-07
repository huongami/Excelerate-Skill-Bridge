"use client";

import Link from "next/link";
import { useSessionStore } from "@/frontend/state/sessionStore";

export function SkillsScreen() {
  const { skillProfile, gaps, frequency } = useSessionStore();
  if (!skillProfile || !gaps || !frequency) return <section className="card empty"><h1>No translated profile yet</h1><p>Complete profile review first.</p><Link className="primary link" href="/profile">Go to profile</Link></section>;
  return <><section className="hero"><p className="eyebrow">Step 2 · Candidate skill profile</p><h1>Skills that travel with the candidate.</h1><p>Evidence-backed groups and honest gaps — never one candidate score.</p></section>
    {skillProfile.groups.map((group) => <section className="card" key={group.kind}><div className="section-head"><h2>{group.kind}</h2><span>{group.skills.length} skill(s)</span></div><div className="grid three">{group.skills.map((skill) => <article className="skill" key={skill.skillId}><h3>{skill.label}</h3><p>{skill.whyItTransfers}</p><small>Evidence: {skill.sourceQuote}</small></article>)}</div></section>)}
    <div className="grid two"><section className="card"><h2>Honest gaps</h2><p className="muted">Reference set: {frequency.jdCount} JDs · {frequency.robustness}</p>{gaps.gaps.length ? gaps.gaps.map((gap) => <article className="gap" key={gap.skillId}><strong>{gap.label}</strong><p>{gap.description}</p></article>) : <p>{gaps.summary}</p>}</section><section className="card next-card"><h2>Ready for recruiter review</h2><p>The confirmed profile is reused; it is not parsed or translated again.</p><Link className="primary link" href="/review">Match one job description →</Link></section></div></>;
}
