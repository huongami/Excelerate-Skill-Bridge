import { createHash, randomUUID } from "node:crypto";
import {
  CandidateJobMatchGoldSchema,
  JobDescriptionSilverSchema,
  type CandidateJobMatchGold,
  type CandidateSkillProfileGold,
  type JobDescriptionSilver
} from "@/backend/schemas/artifacts";

const KNOWN_SKILLS = [
  "stakeholder alignment",
  "performance analytics",
  "paid media operations",
  "marketing automation tools",
  "campaign planning",
  "stakeholder communication",
  "data-informed decisions"
];

function slug(value: string) { return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, ""); }

export function extractJd(text: string, sourceLabel: string): JobDescriptionSilver {
  const normalized = text.toLowerCase();
  const detected = KNOWN_SKILLS.filter((skill) => normalized.includes(skill));
  const skills = (detected.length ? detected : ["stakeholder alignment", "performance analytics", "paid media operations"]).map((label) => ({
    skillId: slug(label), label: label.replace(/\b\w/g, (character) => character.toUpperCase()), requirement: "required" as const, evidenceSpan: normalized.includes(label) ? label : `Illustrative requirement: ${label}`
  }));
  return JobDescriptionSilverSchema.parse({
    jdId: randomUUID(),
    rawHash: createHash("sha256").update(text).digest("hex"),
    targetRoleId: "marketing-operations-manager",
    source: { producer: sourceLabel, sourceUrl: "session://recruiter-jd", capturedAt: new Date().toISOString() },
    skills
  });
}

export function matchCandidate(profile: CandidateSkillProfileGold, jd: JobDescriptionSilver): CandidateJobMatchGold {
  const candidateSkills = profile.groups.flatMap((group) => group.skills);
  return CandidateJobMatchGoldSchema.parse({
    matchId: randomUUID(), profileId: profile.profileId, profileRevision: profile.revision, jdId: jd.jdId,
    skillMatches: jd.skills.map((jdSkill) => {
      const exact = candidateSkills.find((skill) => skill.skillId === jdSkill.skillId || skill.label.toLowerCase() === jdSkill.label.toLowerCase());
      const related = candidateSkills.find((skill) => skill.label.toLowerCase().includes("data") && jdSkill.label.toLowerCase().includes("analytics"));
      const matched = exact ?? related;
      return {
        jdSkillId: jdSkill.skillId,
        label: jdSkill.label,
        matchRate: exact ? "high" : related ? "medium" : "low",
        reason: matched ? matched.whyItTransfers : "No matching or related evidence appears in the confirmed candidate profile.",
        jdEvidence: jdSkill.evidenceSpan,
        candidateEvidenceIds: matched?.sourceEvidenceIds ?? []
      };
    })
  });
}
