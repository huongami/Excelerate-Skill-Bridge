import { describe, expect, it } from "vitest";
import { CandidateJobMatchGoldSchema, DecisionEventSchema } from "@/backend/schemas/artifacts";

describe("employment decision invariants", () => {
  it("rejects an aggregate candidate score", () => {
    const parsed = CandidateJobMatchGoldSchema.safeParse({
      matchId: "m", profileId: "p", profileRevision: 1, jdId: "j", candidateScore: 92, skillMatches: []
    });
    expect(parsed.success).toBe(false);
  });

  it("rejects auto-approve and auto-reject actions", () => {
    const base = { eventId: "e", clientRequestId: "r", matchId: "m", profileRevision: 1, actorLabel: "Alex", note: null, createdAt: new Date().toISOString() };
    expect(DecisionEventSchema.safeParse({ ...base, action: "auto_reject" }).success).toBe(false);
    expect(DecisionEventSchema.safeParse({ ...base, action: "shortlist" }).success).toBe(true);
  });
});
