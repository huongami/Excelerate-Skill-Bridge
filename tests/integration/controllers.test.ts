import { beforeEach, describe, expect, it } from "vitest";
import { createProfile, translate, updateProfile } from "@/backend/controllers/profiles";
import { createDecision, createMatch } from "@/backend/controllers/matches";
import { localMemorySession } from "@/infra/session/localMemory";

describe("demo controller flow", () => {
  beforeEach(() => localMemorySession.clear());
  it("runs profile → confirmation → translation → match → append-only decision", async () => {
    const parsed = await createProfile(null, true);
    const updated = updateProfile(parsed.profileId, { revision: 1, edits: [{ fieldPath: "roles.0.title", value: "Product Owner", action: "confirm" }] });
    const translated = translate(parsed.profileId, { revision: updated.revision, targetRoleId: "marketing-operations-manager" });
    expect(translated.skillProfile.groups.length).toBeGreaterThan(0);
    const matched = createMatch({ profileId: parsed.profileId, revision: updated.revision, jd: { text: "We require stakeholder alignment and performance analytics for campaign planning.", sourceLabel: "test" }, clientRequestId: "match-request" });
    expect(matched.match).not.toHaveProperty("candidateScore");
    const first = createDecision(matched.matchId, { clientRequestId: "decision-1", action: "shortlist", actorLabel: "Alex" });
    const second = createDecision(matched.matchId, { clientRequestId: "decision-2", action: "needs_more_info", actorLabel: "Alex" });
    expect(first.decisionEvents).toHaveLength(1);
    expect(second.decisionEvents).toHaveLength(2);
  });
});
