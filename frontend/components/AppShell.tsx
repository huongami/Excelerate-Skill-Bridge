"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const steps = [{ href: "/profile", label: "Build profile" }, { href: "/skills", label: "See your skills" }, { href: "/review", label: "Review match" }] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return <div className="app-shell">
    <aside className="sidebar"><div className="brand"><span>SB</span><div><strong>Skill Bridge</strong><small>Capability, made visible.</small></div></div><nav>{steps.map((step, index) => <Link key={step.href} className={pathname === step.href ? "active" : ""} href={step.href}><b>{index + 1}</b>{step.label}</Link>)}</nav><p><strong>Zero-AI-Trust demo</strong><br/>No overall score. No automated decision. Demo mode uses deterministic fixtures.</p></aside>
    <main>{children}<footer>Live scaffold · synthetic data only · local session storage</footer></main>
  </div>;
}
