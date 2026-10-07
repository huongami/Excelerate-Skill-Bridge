"use client";

import Link from "next/link";
import type { Route } from "next";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const portals = [
  { href: "/candidate", label: "Candidate", icon: "C" },
  { href: "/hr", label: "HR workspace", icon: "H" },
  { href: "/admin", label: "Admin", icon: "A" },
] as const;

type NavLink = { href: Route; label: string; icon: string };

function contextLinks(pathname: string): NavLink[] {
  if (["/candidate", "/profile", "/skills"].includes(pathname)) return [
    { href: "/candidate", label: "Overview", icon: "1" },
    { href: "/profile", label: "Build profile", icon: "2" },
    { href: "/skills", label: "My skills", icon: "3" },
  ];
  if (["/hr", "/review"].includes(pathname)) return [
    { href: "/hr", label: "Overview", icon: "1" },
    { href: "/review", label: "Match candidate", icon: "2" },
  ];
  return [];
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const links = contextLinks(pathname);
  return <div className="app-shell">
    <aside className="sidebar"><Link className="brand" href="/"><span>SB</span><div><strong>Skill Bridge</strong><small>Capability, made visible.</small></div></Link><nav className="portal-nav">{portals.map((portal) => <Link key={portal.href} className={pathname === portal.href || (portal.href === "/candidate" && ["/profile", "/skills"].includes(pathname)) || (portal.href === "/hr" && pathname === "/review") ? "active" : ""} href={portal.href}><b>{portal.icon}</b>{portal.label}</Link>)}</nav>{links.length > 0 && <><div className="nav-label">Current workspace</div><nav className="context-nav">{links.map((link) => <Link key={link.href} className={pathname === link.href ? "active" : ""} href={link.href}><b>{link.icon}</b>{link.label}</Link>)}</nav></>}<p><strong>Zero-AI-Trust demo</strong><br/>No overall score. No automated decision. Demo mode uses deterministic fixtures.</p></aside>
    <main>{children}<footer>Live scaffold · synthetic data only · local session storage</footer></main>
  </div>;
}
