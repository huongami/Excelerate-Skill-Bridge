import { beforeEach, describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { createProfile, translate, updateProfile } from "@/backend/controllers/profiles";
import { createDecision, createMatch } from "@/backend/controllers/matches";
import { parseJd } from "@/backend/controllers/jds";
import { localMemorySession } from "@/infra/session/localMemory";

describe("demo controller flow", () => {
  beforeEach(() => localMemorySession.clear());
  it("runs profile → confirmation → translation → match → append-only decision", async () => {
    const parsed = await createProfile(null, true);
    const updated = updateProfile(parsed.profileId, { revision: 1, edits: [{ fieldPath: "roles.0.title", value: "Operations Team Lead", action: "confirm" }] });
    const translated = translate(parsed.profileId, { revision: updated.revision, targetRoleId: "business-operations-coordinator" });
    expect(translated.skillProfile.groups.length).toBeGreaterThan(0);
    const matched = createMatch({ profileId: parsed.profileId, revision: updated.revision, jd: { text: "We require team operations, operational reporting and AI tool familiarity.", sourceLabel: "test" }, clientRequestId: "match-request" });
    expect(matched.match).not.toHaveProperty("candidateScore");
    const first = createDecision(matched.matchId, { clientRequestId: "decision-1", action: "shortlist", actorLabel: "Alex" });
    const second = createDecision(matched.matchId, { clientRequestId: "decision-2", action: "needs_more_info", actorLabel: "Alex" });
    expect(first.decisionEvents).toHaveLength(1);
    expect(second.decisionEvents).toHaveLength(2);
  });

  it("parses pasted JD text into weighted skills", async () => {
    const parsed = await parseJd(null, "Team operations are essential. Spreadsheet analysis is required. AI tool familiarity is preferred.", "test JD");
    expect(parsed.jd.skills.reduce((sum, skill) => sum + skill.weight, 0)).toBeCloseTo(100, 5);
    expect(parsed.jd.skills[0]).toHaveProperty("evidenceSpan");
  });

  it("translates the reviewed Phung Dang Khoa fixture for a data analyst target", async () => {
    const bytes = readFileSync(resolve("data/demo/[CV] Phung Dang Khoa.docx.pdf"));
    const file = new File([bytes], "[CV] Phung Dang Khoa.docx.pdf", { type: "application/pdf" });
    const parsed = await createProfile(file, true);
    const updated = updateProfile(parsed.profileId, { revision: 1, edits: [{ fieldPath: "roles.0.title", value: "Proxy Product Owner | Data Analyst", action: "confirm" }] });
    const result = translate(parsed.profileId, { revision: updated.revision, targetRoleId: "data-analyst" });
    expect(result.skillProfile.groups.flatMap((group) => group.skills).map((skill) => skill.label)).toContain("Data analysis");
  });
});
