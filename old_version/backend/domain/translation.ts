import { AppError } from "@/backend/errors";
import { referenceRepository } from "@/backend/repositories/referenceRepository";
import {
  CandidateSkillProfileGoldSchema,
  GapAnalysisGoldSchema,
  TranslatedRoleSilverSchema,
  type CandidateProfileSilver,
  type CandidateSkillProfileGold,
  type GapAnalysisGold,
  type RoleSkillFrequencyGold,
  type TranslatedRoleSilver
} from "@/backend/schemas/artifacts";

export function translateProfile(profile: CandidateProfileSilver, targetRoleId: string): { translatedRoles: TranslatedRoleSilver[]; skillProfile: CandidateSkillProfileGold } {
  const mappings = referenceRepository.mappingsFor(targetRoleId);
  if (!mappings.length) throw new AppError("REFERENCE_MAPPING_UNAVAILABLE", "No reviewed mapping exists for this target role", 422);

  const translatedRoles = profile.roles.map((role) => {
    const mapping = mappings.find((candidate) => candidate.sourceTitle.toLowerCase() === role.title.value?.toLowerCase());
    if (!mapping) {
      return TranslatedRoleSilverSchema.parse({
        sourceRoleId: role.id,
        originalTitle: role.title.value ?? "Unresolved role",
        originalCountry: role.country.value ?? "Unresolved country",
        auEquivalentFunction: null,
        skills: [],
        omissions: role.responsibilities.map((responsibility) => ({ sourceEvidenceId: responsibility.id, reason: "No reviewed mapping exists; omitted rather than forced" }))
      });
    }
    return TranslatedRoleSilverSchema.parse({
      sourceRoleId: role.id,
      originalTitle: role.title.value,
      originalCountry: role.country.value,
      auEquivalentFunction: mapping.auEquivalentFunction,
      skills: mapping.skills.map((skill, index) => {
        const evidence = role.responsibilities[index % role.responsibilities.length];
        return {
          skillId: skill.id,
          label: skill.label,
          group: skill.group,
          sharedCompetency: skill.sharedCompetency,
          sourceEvidenceIds: [evidence.id],
          sourceQuote: evidence.text,
          whyItTransfers: skill.rationale
        };
      }),
      omissions: []
    });
  });

  const allSkills = translatedRoles.flatMap((role) => role.skills);
  const groups = (["direct", "transferable", "supporting"] as const).map((kind) => ({
    kind,
    skills: allSkills.filter((skill) => skill.group === kind).sort((a, b) => a.label.localeCompare(b.label))
  })).filter((group) => group.skills.length);
  const skillProfile = CandidateSkillProfileGoldSchema.parse({ profileId: profile.profileId, revision: profile.revision, targetRoleId, groups });
  return { translatedRoles, skillProfile };
}

export function identifyGaps(skillProfile: CandidateSkillProfileGold, frequency: RoleSkillFrequencyGold): GapAnalysisGold {
  const candidateTerms = new Set(skillProfile.groups.flatMap((group) => group.skills.flatMap((skill) => [skill.label.toLowerCase(), skill.skillId])));
  const mappings = referenceRepository.mappingsFor(skillProfile.targetRoleId);
  for (const mapping of mappings) for (const skill of mapping.skills) for (const alias of skill.aliases) {
    if (candidateTerms.has(skill.label.toLowerCase())) candidateTerms.add(alias.toLowerCase());
  }
  const gaps = frequency.skills.filter((skill) => skill.percentage >= 30 && !candidateTerms.has(skill.label.toLowerCase())).map((skill) => ({
    skillId: skill.skillId,
    label: skill.label,
    description: `${skill.label} appears in ${skill.documentCount} of ${frequency.jdCount} reference JDs, but no evidence appears in the confirmed profile. Consider upskilling or provide more information.`
  }));
  return GapAnalysisGoldSchema.parse({
    targetRoleId: skillProfile.targetRoleId,
    referenceRobustness: frequency.robustness,
    gaps,
    summary: gaps.length ? `${gaps.length} evidence gap${gaps.length === 1 ? "" : "s"} identified` : "No major gaps identified"
  });
}
