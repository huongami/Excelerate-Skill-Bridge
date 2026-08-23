export function Status({ error, busy }: { error?: string; busy?: boolean }) {
  if (error) return <div className="status error" role="alert">{error}</div>;
  if (busy) return <div className="status">Working…</div>;
  return null;
}
