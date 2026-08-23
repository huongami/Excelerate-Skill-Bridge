import type { DecisionResponse, MatchResponse, ParseProfileResponse, ProfileResponse, TranslationResponse } from "@/frontend/types/contracts";

async function parseResponse<T>(response: Response): Promise<T> {
  const body = await response.json();
  if (!response.ok) throw new Error(body.error?.message ?? "Request failed");
  return body as T;
}

export async function parseProfile(file?: File): Promise<ParseProfileResponse> {
  const form = new FormData();
  form.set("consentConfirmed", "true");
  form.set("clientRequestId", crypto.randomUUID());
  if (file) form.set("file", file);
  return parseResponse(await fetch("/api/profiles/parse", { method: "POST", body: form }));
}

export async function getProfile(profileId: string): Promise<ProfileResponse> {
  return parseResponse(await fetch(`/api/profiles/${profileId}`));
}

export async function patchProfile(profileId: string, revision: number, edits: Array<{ fieldPath: string; value: string; action: "edit" | "confirm" }>): Promise<ParseProfileResponse> {
  return parseResponse(await fetch(`/api/profiles/${profileId}`, { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify({ revision, edits }) }));
}

export async function translateProfile(profileId: string, revision: number, targetRoleId: string): Promise<TranslationResponse> {
  return parseResponse(await fetch(`/api/profiles/${profileId}/translate`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ revision, targetRoleId }) }));
}

export async function createMatch(profileId: string, revision: number, text: string): Promise<MatchResponse> {
  return parseResponse(await fetch("/api/matches", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ profileId, revision, jd: { text, sourceLabel: "Recruiter-entered demo JD" }, clientRequestId: crypto.randomUUID() }) }));
}

export async function decide(matchId: string, action: "shortlist" | "needs_more_info" | "not_a_fit"): Promise<DecisionResponse> {
  return parseResponse(await fetch(`/api/matches/${matchId}/decisions`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ clientRequestId: crypto.randomUUID(), action, actorLabel: "Alex Morgan" }) }));
}
