const controls = [
  ["No aggregate score", "Enforced in Zod schemas and UI contracts", "Protected"],
  ["No automated decision", "Only HR-initiated actions are available", "Protected"],
  ["Evidence traceability", "Each translated skill retains source evidence", "Protected"],
  ["Reference data", "Synthetic provisional fixtures need external review", "Review needed"],
];

export function AdminDashboard() {
  return <><section className="hero dashboard-hero"><div><p className="eyebrow">Admin dashboard</p><h1>Demo governance at a glance.</h1><p>Understand what is ready, what is intentionally local, and which quality gates must pass before live AI or real hiring use.</p></div><div className="persona-chip admin"><span>Environment</span><strong>Deterministic demo</strong><small>No database · local session</small></div></section><div className="metric-grid four"><Metric label="Portals" value="3" detail="Candidate · HR · Admin"/><Metric label="Target roles" value="4" detail="Provisional demo scope"/><Metric label="Reference JDs" value="6" detail="Synthetic fixtures"/><Metric label="Automated decisions" value="0" detail="Structurally excluded"/></div><div className="grid admin-layout"><section className="card"><div className="section-head"><h2>Trust controls</h2><span>Zero-AI-Trust</span></div><div className="control-table">{controls.map(([name, detail, status]) => <div className="control-row" key={name}><div><strong>{name}</strong><span>{detail}</span></div><em className={status === "Protected" ? "ok" : "review"}>{status}</em></div>)}</div></section><section className="card"><p className="eyebrow">Build status</p><h2>Hackathon readiness</h2><div className="readiness"><div><span>Static stage demo</span><b>Ready</b></div><div><span>Deterministic coded flow</span><b>Ready</b></div><div><span>Live-model evaluation</span><b className="pending">Pending</b></div><div><span>Reviewed external seeds</span><b className="pending">Pending</b></div></div><p className="admin-note">Admin controls are informational in this no-auth, no-database prototype. Production permissions are roadmap scope.</p></section></div></>;
}

function Metric({ label, value, detail }: { label: string; value: string; detail: string }) { return <article className="metric admin-metric"><span>{label}</span><strong>{value}</strong><small>{detail}</small></article>; }
