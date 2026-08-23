import targetRoles from "@/data/reference/target-roles.json";
import roleMappings from "@/data/reference/role-mappings.reference.json";
import jdSkills from "@/data/reference/jd-skills.reference.json";

export type TargetRole = (typeof targetRoles)[number];
export type RoleMapping = (typeof roleMappings)[number];
export type ReferenceJd = (typeof jdSkills)[number];

export const referenceRepository = {
  listTargetRoles: () => targetRoles,
  mappingsFor: (targetRoleId: string) => roleMappings.filter((mapping) => mapping.targetRoleId === targetRoleId),
  jdsFor: (targetRoleId: string) => jdSkills.filter((jd) => jd.targetRoleId === targetRoleId)
};
