import { describe, expect, it } from "vitest";
import { aggregateFrequency } from "@/backend/domain/frequency";

describe("aggregateFrequency", () => {
  it("counts document occurrence and marks fewer than five JDs indicative", () => {
    const result = aggregateFrequency("role", [
      { jdId: "1", targetRoleId: "role", source: { producer: "test", sourceUrl: "test://1", capturedAt: "2026-08-23" }, skills: ["SQL", "SQL", "Communication"] },
      { jdId: "2", targetRoleId: "role", source: { producer: "test", sourceUrl: "test://2", capturedAt: "2026-08-23" }, skills: ["SQL"] }
    ]);
    expect(result.robustness).toBe("indicative");
    expect(result.skills[0]).toMatchObject({ label: "Sql", documentCount: 2, percentage: 100 });
  });
});
