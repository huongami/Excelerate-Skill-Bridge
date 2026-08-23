import Link from "next/link";
import type { Route } from "next";

const roles: Array<{ href: Route; code: string; eyebrow: string; title: string; copy: string; action: string }> = [
  { href: "/candidate", code: "C", eyebrow: "Job seeker", title: "Candidate", copy: "Build a reviewed profile, translate experience into Australian-market skills, and understand honest gaps.", action: "Enter candidate portal" },
  { href: "/hr", code: "HR", eyebrow: "Recruitment team", title: "HR", copy: "Paste a job description, compare requirements skill by skill, inspect evidence, and keep the final decision human.", action: "Enter HR workspace" },
  { href: "/admin", code: "A", eyebrow: "Demo governance", title: "Admin", copy: "Monitor demo readiness, reference-data status, trust controls, and the boundaries of this no-database prototype.", action: "Open admin dashboard" },
];

export function RoleSelectorScreen() {
  return <><section className="hero role-hero"><div><p className="eyebrow">Choose a workspace</p><h1>One bridge. Three human roles.</h1><p>Explore the Skill Bridge prototype from the perspective of a candidate, an HR reviewer, or the demo administrator.</p></div><div className="hero-mark">SB</div></section><section className="role-grid">{roles.map((role) => <Link href={role.href} className="role-card" key={role.href}><span className="role-code">{role.code}</span><p className="eyebrow">{role.eyebrow}</p><h2>{role.title}</h2><p>{role.copy}</p><strong>{role.action} →</strong></Link>)}</section><section className="trust-strip"><div><b>Evidence first</b><span>Every skill maps back to candidate experience.</span></div><div><b>No candidate score</b><span>Requirements are reviewed skill by skill.</span></div><div><b>Human decision</b><span>The system never accepts or rejects a person.</span></div></section></>;
}
