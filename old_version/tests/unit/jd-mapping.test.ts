import { describe, expect, it } from "vitest";
import { extractJd } from "@/backend/domain/matching";

describe("JD skill mapping and weighting", () => {
  it("maps evidence, assigns transparent priorities and normalises weights to 100", () => {
    const jd = extractJd(
      "Team operations and cross-functional coordination are essential. Operational reporting is required. AI tool familiarity is preferred.",
      "synthetic test JD"
    );
    expect(jd.skills.map((skill) => skill.label)).toContain("Team Operations");
    expect(jd.skills.find((skill) => skill.skillId === "team-operations")?.importance).toBe("essential");
    expect(jd.skills.find((skill) => skill.skillId === "ai-tool-familiarity")?.importance).toBe("supporting");
    expect(jd.skills.reduce((sum, skill) => sum + skill.weight, 0)).toBeCloseTo(100, 5);
    expect(jd.skills.every((skill) => skill.evidenceSpan.length > 10)).toBe(true);
  });

  it("maps technical data skills without using fallback skills", () => {
    const jd = extractJd(
      "SQL and data visualisation using Power BI are essential. Statistical analysis is required. Python is preferred.",
      "synthetic data analyst JD"
    );
    expect(jd.skills.map((skill) => skill.skillId)).toEqual(expect.arrayContaining(["sql", "data-visualisation", "statistical-analysis", "python"]));
    expect(jd.skills.map((skill) => skill.skillId)).not.toContain("team-operations");
    expect(jd.skills.reduce((sum, skill) => sum + skill.weight, 0)).toBeCloseTo(100, 5);
  });

  it("maps Product Owner skills with transparent weights", () => {
    const jd = extractJd(
      "Product backlog management is essential. Product discovery and user research are required. Stakeholder management and agile delivery are required. SQL is preferred.",
      "synthetic Product Owner JD"
    );
    expect(jd.skills.map((skill) => skill.label)).toEqual(expect.arrayContaining([
      "Backlog Management", "Product Discovery", "User Research", "Stakeholder Management", "Agile Delivery", "Sql"
    ]));
    expect(jd.skills.reduce((sum, skill) => sum + skill.weight, 0)).toBeCloseTo(100, 5);
  });
});
