"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { parseProfile, patchProfile, translateProfile } from "@/frontend/api/client";
import { Status } from "@/frontend/components/Status";
import { useSessionStore } from "@/frontend/state/sessionStore";

export function ProfileScreen() {
  const router = useRouter();
  const { profile, setProfile, setTranslation } = useSessionStore();
  const [file, setFile] = useState<File>(); const [busy, setBusy] = useState(false); const [error, setError] = useState<string>();
  const [targetRoleId, setTargetRoleId] = useState("marketing-operations-manager");

  async function load() { setBusy(true); setError(undefined); try { const result = await parseProfile(file); setProfile(result.profile); } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to parse profile"); } finally { setBusy(false); } }
  async function confirmAndTranslate() {
    if (!profile) return;
    setBusy(true); setError(undefined);
    try {
      const role = profile.roles[0];
      const updated = role.title.status === "ambiguous" ? await patchProfile(profile.profileId, profile.revision, [{ fieldPath: "roles.0.title", value: role.title.value ?? "Product Owner", action: "confirm" }]) : { profile };
      setProfile(updated.profile);
      const result = await translateProfile(updated.profile.profileId, updated.profile.revision, targetRoleId);
      setTranslation(result.skillProfile, result.gaps, result.frequencyContext);
      router.push("/skills");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to translate profile"); } finally { setBusy(false); }
  }

  return <><section className="hero"><p className="eyebrow">Step 1 · Candidate profile</p><h1>Make experience readable before judging it.</h1><p>Upload a CV or load the synthetic demo persona. Ambiguous fields must be confirmed before translation.</p></section><Status error={error} busy={busy}/>
    <div className="grid two"><section className="card"><h2>CV input</h2><label className="upload">PDF or DOCX<input type="file" accept=".pdf,.docx" onChange={(event) => setFile(event.target.files?.[0])}/><span>{file?.name ?? "No file selected — demo persona will be used"}</span></label><button className="primary" onClick={load} disabled={busy}>Parse profile</button></section>
    <section className="card"><h2>Profile review</h2>{profile ? <><Field label="Name" value={profile.name.value}/><Field label="Title" value={profile.roles[0].title.value} flag={profile.roles[0].title.status}/><Field label="Employer" value={profile.roles[0].employer.value}/><Field label="Country" value={profile.roles[0].country.value}/><label>Target role<select value={targetRoleId} onChange={(event) => setTargetRoleId(event.target.value)}><option value="marketing-operations-manager">Marketing Operations Manager</option><option value="product-manager">Product Manager</option><option value="data-analyst">Data Analyst</option></select></label><button className="primary" onClick={confirmAndTranslate} disabled={busy}>Confirm and translate →</button></> : <p className="muted">Parse a profile to review its extracted fields.</p>}</section></div></>;
}

function Field({ label, value, flag }: { label: string; value: string | null; flag?: string }) { return <div className="field"><span>{label}</span><strong>{value ?? "Missing"}</strong>{flag && <em>{flag.replace("candidate_", "")}</em>}</div>; }
