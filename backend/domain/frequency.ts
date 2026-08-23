import { RoleSkillFrequencyGoldSchema, type RoleSkillFrequencyGold } from "@/backend/schemas/artifacts";
import type { ReferenceJd } from "@/backend/repositories/referenceRepository";

function slug(value: string) { return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, ""); }

export function aggregateFrequency(targetRoleId: string, jds: ReferenceJd[]): RoleSkillFrequencyGold {
  const counts = new Map<string, { label: string; jdIds: Set<string> }>();
  for (const jd of jds) {
    for (const label of new Set(jd.skills.map((skill) => skill.trim().toLowerCase()))) {
      const existing = counts.get(label) ?? { label, jdIds: new Set<string>() };
      existing.jdIds.add(jd.jdId);
      counts.set(label, existing);
    }
  }
  return RoleSkillFrequencyGoldSchema.parse({
    targetRoleId,
    jdCount: jds.length,
    robustness: jds.length < 5 ? "indicative" : "sample",
    skills: [...counts.values()].map((entry) => ({
      skillId: slug(entry.label),
      label: entry.label.replace(/\b\w/g, (character) => character.toUpperCase()),
      documentCount: entry.jdIds.size,
      percentage: jds.length ? Math.round((entry.jdIds.size / jds.length) * 100) : 0,
      sourceJdIds: [...entry.jdIds]
    })).sort((a, b) => b.documentCount - a.documentCount || a.label.localeCompare(b.label))
  });
}
