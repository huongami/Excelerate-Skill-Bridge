import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { applyProfileEdits, parseProfile } from "@/backend/domain/profile";
import type { CandidateProfileSilver } from "@/backend/schemas/artifacts";

const field = (value: string) => ({ value, status: "extracted" as const, reason: null, sourceExcerpt: value });
const profile: CandidateProfileSilver = {
  profileId: "profile", revision: 1, name: field("Minh"), document: { rawHash: "a".repeat(64), sourceType: "demo", fileName: "demo.pdf", consentConfirmed: true },
  roles: [{ id: "role", title: { ...field("Operations Team Lead"), status: "ambiguous" }, employer: field("Saigon Service Group"), country: field("Vietnam"), startDate: field("2021-01"), endDate: field("2025-08"), responsibilities: [{ id: "evidence", text: "Led a team", sourceExcerpt: "Led a team" }] }], provenanceEvents: []
};

describe("applyProfileEdits", () => {
  it("creates a new revision with provenance", () => {
    const updated = applyProfileEdits(profile, 1, [{ fieldPath: "roles.0.title", value: "Operations Team Lead", action: "confirm" }]);
    expect(updated.revision).toBe(2);
    expect(updated.roles[0].title.status).toBe("candidate_confirmed");
    expect(updated.provenanceEvents).toHaveLength(1);
  });
});

describe("deterministic CV fixtures", () => {
  it("selects Phung Dang Khoa from the reviewed uploaded filename", async () => {
    const bytes = readFileSync(resolve("data/demo/[CV] Phung Dang Khoa.docx.pdf"));
    const file = new File([bytes], "[CV] Phung Dang Khoa.docx.pdf", { type: "application/pdf" });
    const { profile } = await parseProfile(file, true);
    expect(profile.name.value).toBe("Phung Dang Khoa");
    expect(profile.roles).toHaveLength(3);
    expect(profile.roles[0].title.value).toBe("Proxy Product Owner | Data Analyst");
  });

  it("rejects an unknown upload in demo mode instead of returning Minh Tran", async () => {
    const file = new File(["unknown CV"], "unknown.pdf", { type: "application/pdf" });
    await expect(parseProfile(file, true)).rejects.toMatchObject({ code: "LIVE_CV_PARSING_DISABLED" });
  });
});
