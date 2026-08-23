import { createHash, randomUUID } from "node:crypto";
import {
  CandidateJobMatchGoldSchema,
  JobDescriptionSilverSchema,
  type CandidateJobMatchGold,
  type CandidateSkillProfileGold,
  type JobDescriptionSilver
} from "@/backend/schemas/artifacts";

const SKILL_CATALOG = [
  { label: "team operations", aliases: ["team operations", "team coordination", "team leadership", "workforce coordination"] },
  { label: "cross-functional coordination", aliases: ["cross-functional coordination", "cross functional coordination", "coordinate across", "multiple departments"] },
  { label: "operational reporting", aliases: ["operational reporting", "operations reports", "weekly reports", "status reports", "management reporting"] },
  { label: "spreadsheet analysis", aliases: ["spreadsheet analysis", "excel", "google sheets", "spreadsheets"] },
  { label: "ai tool familiarity", aliases: ["ai tool familiarity", "ai tools", "generative ai", "automation tools"] },
  { label: "customer service operations", aliases: ["customer service operations", "customer support operations", "service delivery", "customer issues"] },
  { label: "stakeholder alignment", aliases: ["stakeholder alignment", "align stakeholders"] },
  { label: "stakeholder communication", aliases: ["stakeholder communication", "communicate with stakeholders", "stakeholder updates"] },
  { label: "performance analytics", aliases: ["performance analytics", "performance metrics", "kpis", "key performance indicators"] },
  { label: "process improvement", aliases: ["process improvement", "continuous improvement", "workflow improvement", "improve processes"] },
  { label: "project coordination", aliases: ["project coordination", "project tracking", "project support"] },
  { label: "vendor coordination", aliases: ["vendor coordination", "supplier coordination", "vendor management"] },
  { label: "schedule management", aliases: ["schedule management", "scheduling", "calendar coordination", "roster"] },
  { label: "documentation management", aliases: ["documentation management", "document control", "standard operating procedures", "sops"] },
  { label: "risk and issue management", aliases: ["risk and issue management", "risk register", "issue log", "escalation management"] },
  { label: "crm administration", aliases: ["crm administration", "crm system", "salesforce", "hubspot"] },
  { label: "paid media operations", aliases: ["paid media operations", "paid media"] },
  { label: "marketing automation tools", aliases: ["marketing automation tools", "marketing automation"] },
  { label: "campaign planning", aliases: ["campaign planning", "campaign coordination"] },
  { label: "data-informed decisions", aliases: ["data-informed decisions", "data driven decisions", "data-informed decision-making"] },
  { label: "backlog management", aliases: ["backlog management", "product backlog", "backlog ownership", "backlog prioritisation", "backlog prioritization"] },
  { label: "product discovery", aliases: ["product discovery", "discovery workshops", "problem framing"] },
  { label: "user research", aliases: ["user research", "customer interviews", "user interviews"] },
  { label: "requirements management", aliases: ["requirements management", "requirements definition", "clarify requirements", "business requirements"] },
  { label: "stakeholder management", aliases: ["stakeholder management", "stakeholder engagement", "business stakeholders"] },
  { label: "dashboard development", aliases: ["dashboard development", "enterprise dashboards", "build dashboards"] },
  { label: "sql", aliases: ["sql", "structured query language"] }
  ,{ label: "python", aliases: ["python", "pyspark"] }
  ,{ label: "data visualisation", aliases: ["data visualisation", "data visualization", "power bi", "tableau", "looker"] }
  ,{ label: "statistical analysis", aliases: ["statistical analysis", "statistics", "hypothesis testing", "regression analysis"] }
  ,{ label: "data modelling", aliases: ["data modelling", "data modeling", "dimensional modelling", "star schema"] }
  ,{ label: "etl pipelines", aliases: ["etl pipelines", "etl", "elt", "data pipelines", "pipeline orchestration"] }
  ,{ label: "data warehousing", aliases: ["data warehousing", "data warehouse", "snowflake", "bigquery", "redshift"] }
  ,{ label: "cloud platforms", aliases: ["cloud platforms", "aws", "azure", "google cloud", "gcp"] }
  ,{ label: "database design", aliases: ["database design", "database administration", "postgresql", "mysql", "nosql"] }
  ,{ label: "api development", aliases: ["api development", "rest api", "restful api", "graphql"] }
  ,{ label: "frontend development", aliases: ["frontend development", "front-end development", "react", "next.js", "typescript"] }
  ,{ label: "backend development", aliases: ["backend development", "back-end development", "node.js", "java", ".net"] }
  ,{ label: "software testing", aliases: ["software testing", "automated testing", "test automation", "unit testing", "integration testing"] }
  ,{ label: "ci/cd", aliases: ["ci/cd", "continuous integration", "continuous delivery", "github actions", "gitlab ci"] }
  ,{ label: "container orchestration", aliases: ["container orchestration", "kubernetes", "docker", "containers"] }
  ,{ label: "infrastructure as code", aliases: ["infrastructure as code", "terraform", "cloudformation"] }
  ,{ label: "cybersecurity monitoring", aliases: ["cybersecurity monitoring", "security monitoring", "siem", "incident detection"] }
  ,{ label: "identity and access management", aliases: ["identity and access management", "iam", "access control"] }
  ,{ label: "machine learning", aliases: ["machine learning", "ml models", "predictive models", "scikit-learn"] }
  ,{ label: "mlops", aliases: ["mlops", "model deployment", "model monitoring", "feature store"] }
  ,{ label: "data governance", aliases: ["data governance", "data quality", "data lineage", "metadata management"] }
  ,{ label: "agile delivery", aliases: ["agile delivery", "scrum", "kanban", "sprint planning"] }
];

function slug(value: string) { return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, ""); }

export function extractJd(text: string, sourceLabel: string, targetRoleId = "business-operations-coordinator"): JobDescriptionSilver {
  const normalized = text.toLowerCase();
  const sentences = text.split(/(?<=[.!?])\s+|\n+/).map((line) => line.trim()).filter(Boolean);
  const detected = SKILL_CATALOG.flatMap((skill) => {
    const evidence = sentences.find((sentence) => skill.aliases.some((alias) => sentence.toLowerCase().includes(alias)));
    if (!evidence) return [];
    const evidenceLower = evidence.toLowerCase();
    const preferred = /preferred|desirable|nice to have|advantage/.test(evidenceLower);
    const essential = /must|required|essential|critical|mandatory/.test(evidenceLower);
    return [{
      skillId: slug(skill.label),
      label: skill.label.replace(/\b\w/g, (character) => character.toUpperCase()),
      requirement: preferred ? "preferred" as const : "required" as const,
      importance: essential ? "essential" as const : preferred ? "supporting" as const : "important" as const,
      evidenceSpan: evidence
    }];
  });
  const base = detected.length ? detected : [
    { skillId: "team-operations", label: "Team Operations", requirement: "required" as const, importance: "important" as const, evidenceSpan: "Illustrative requirement: team operations" },
    { skillId: "operational-reporting", label: "Operational Reporting", requirement: "required" as const, importance: "important" as const, evidenceSpan: "Illustrative requirement: operational reporting" },
    { skillId: "ai-tool-familiarity", label: "AI Tool Familiarity", requirement: "preferred" as const, importance: "supporting" as const, evidenceSpan: "Illustrative preference: AI tool familiarity" }
  ];
  const points = { essential: 5, important: 3, supporting: 1 } as const;
  const totalPoints = base.reduce((sum, skill) => sum + points[skill.importance], 0);
  const skills = base.map((skill, index) => ({
    ...skill,
    weight: index === base.length - 1
      ? Number((100 - base.slice(0, -1).reduce((sum, item) => sum + Number(((points[item.importance] / totalPoints) * 100).toFixed(1)), 0)).toFixed(1))
      : Number(((points[skill.importance] / totalPoints) * 100).toFixed(1))
  })).sort((a, b) => b.weight - a.weight || a.label.localeCompare(b.label));
  return JobDescriptionSilverSchema.parse({
    jdId: randomUUID(),
    rawHash: createHash("sha256").update(text).digest("hex"),
    targetRoleId,
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
      const related = candidateSkills.find((skill) =>
        (skill.label.toLowerCase().includes("data") && ["analytics", "reporting", "spreadsheet"].some((term) => jdSkill.label.toLowerCase().includes(term))) ||
        (skill.label.toLowerCase().includes("cross-functional") && jdSkill.label.toLowerCase().includes("coordination"))
      );
      const matched = exact ?? related;
      return {
        jdSkillId: jdSkill.skillId,
        label: jdSkill.label,
        importance: jdSkill.importance,
        weight: jdSkill.weight,
        matchRate: exact ? "high" : related ? "medium" : "low",
        reason: matched ? matched.whyItTransfers : "No matching or related evidence appears in the confirmed candidate profile.",
        jdEvidence: jdSkill.evidenceSpan,
        candidateEvidenceIds: matched?.sourceEvidenceIds ?? []
      };
    })
  });
}
