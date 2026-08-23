import { describe, expect, it } from "vitest";
import { CandidateJobMatchGoldSchema, DecisionEventSchema } from "@/backend/schemas/artifacts";

describe("employment decision invariants", () => {
  it("rejects an aggregate candidate score", () => {
    const parsed = CandidateJobMatchGoldSchema.safeParse({
      matchId: "m", profileId: "p", profileRevision: 1, jdId: "j", candidateScore: 92, skillMatches: []
    });
    expect(parsed.success).toBe(false);
  });

  it("allows JD priority weights but still rejects an overall candidate score", () => {
    const parsed = CandidateJobMatchGoldSchema.safeParse({
      matchId: "m", profileId: "p", profileRevision: 1, jdId: "j",
      skillMatches: [{ jdSkillId: "s", label: "Operations", importance: "essential", weight: 60, matchRate: "high", reason: "Evidence-backed", jdEvidence: "Required operations", candidateEvidenceIds: ["e"] }]
    });
    expect(parsed.success).toBe(true);
  });

  it("rejects auto-approve and auto-reject actions", () => {
    const base = { eventId: "e", clientRequestId: "r", matchId: "m", profileRevision: 1, actorLabel: "Alex", note: null, createdAt: new Date().toISOString() };
    expect(DecisionEventSchema.safeParse({ ...base, action: "auto_reject" }).success).toBe(false);
    expect(DecisionEventSchema.safeParse({ ...base, action: "shortlist" }).success).toBe(true);
  });
});
