import { describe, expect, it } from "vitest";
import { applyProfileEdits } from "@/backend/domain/profile";
import type { CandidateProfileSilver } from "@/backend/schemas/artifacts";

const field = (value: string) => ({ value, status: "extracted" as const, reason: null, sourceExcerpt: value });
const profile: CandidateProfileSilver = {
  profileId: "profile", revision: 1, name: field("Linh"), document: { rawHash: "a".repeat(64), sourceType: "demo", fileName: "demo.pdf", consentConfirmed: true },
  roles: [{ id: "role", title: { ...field("Product Owner"), status: "ambiguous" }, employer: field("Lotus"), country: field("Vietnam"), startDate: field("2021-01"), endDate: field("2025-08"), responsibilities: [{ id: "evidence", text: "Led a team", sourceExcerpt: "Led a team" }] }], provenanceEvents: []
};

describe("applyProfileEdits", () => {
  it("creates a new revision with provenance", () => {
    const updated = applyProfileEdits(profile, 1, [{ fieldPath: "roles.0.title", value: "Product Owner", action: "confirm" }]);
    expect(updated.revision).toBe(2);
    expect(updated.roles[0].title.status).toBe("candidate_confirmed");
    expect(updated.provenanceEvents).toHaveLength(1);
  });
});
