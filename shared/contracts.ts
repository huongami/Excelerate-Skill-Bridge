export type ReviewableField = { value: string | null; status: string; reason: string | null; sourceExcerpt: string | null };
export type CandidateProfile = {
  profileId: string; revision: number; name: ReviewableField;
  roles: Array<{ id: string; title: ReviewableField; employer: ReviewableField; country: ReviewableField; startDate: ReviewableField; endDate: ReviewableField; responsibilities: Array<{ id: string; text: string; sourceExcerpt: string }> }>;
  provenanceEvents: Array<{ id: string; fieldPath: string; previousValue: string | null; newValue: string; action: string; createdAt: string }>;
};
export type ReviewTask = { fieldPath: string; sourceExcerpt: string | null; reason: string; resolutionStatus: string };
export type Skill = { skillId: string; label: string; group: "direct" | "transferable" | "supporting"; sharedCompetency: string | null; sourceEvidenceIds: string[]; sourceQuote: string; whyItTransfers: string };
export type SkillProfile = { profileId: string; revision: number; targetRoleId: string; groups: Array<{ kind: string; skills: Skill[] }> };
export type Frequency = { targetRoleId: string; jdCount: number; robustness: "indicative" | "sample"; skills: Array<{ skillId: string; label: string; documentCount: number; percentage: number; sourceJdIds: string[] }> };
export type GapAnalysis = { targetRoleId: string; referenceRobustness: string; gaps: Array<{ skillId: string; label: string; description: string }>; summary: string };
export type Match = { matchId: string; profileId: string; profileRevision: number; jdId: string; skillMatches: Array<{ jdSkillId: string; label: string; matchRate: "high" | "medium" | "low"; reason: string; jdEvidence: string; candidateEvidenceIds: string[] }> };
export type DecisionEvent = { eventId: string; clientRequestId: string; matchId: string; profileRevision: number; action: "shortlist" | "needs_more_info" | "not_a_fit"; actorLabel: string; note: string | null; createdAt: string };
