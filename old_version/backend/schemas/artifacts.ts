import { z } from "zod";

export const FieldStatusSchema = z.enum([
  "extracted",
  "missing",
  "ambiguous",
  "candidate_confirmed",
  "candidate_edited"
]);

export const ReviewableFieldSchema = z.object({
  value: z.string().nullable(),
  status: FieldStatusSchema,
  reason: z.string().nullable(),
  sourceExcerpt: z.string().nullable()
}).strict();

export const ResponsibilitySchema = z.object({
  id: z.string().min(1),
  text: z.string().min(1),
  sourceExcerpt: z.string().min(1)
}).strict();

export const ProvenanceEventSchema = z.object({
  id: z.string().min(1),
  fieldPath: z.string().min(1),
  previousValue: z.string().nullable(),
  newValue: z.string(),
  action: z.enum(["confirm", "edit"]),
  actor: z.literal("candidate"),
  createdAt: z.string().datetime()
}).strict();

export const CandidateRoleSchema = z.object({
  id: z.string().min(1),
  title: ReviewableFieldSchema,
  employer: ReviewableFieldSchema,
  country: ReviewableFieldSchema,
  startDate: ReviewableFieldSchema,
  endDate: ReviewableFieldSchema,
  responsibilities: z.array(ResponsibilitySchema).min(1)
}).strict();

export const CandidateProfileSilverSchema = z.object({
  profileId: z.string().min(1),
  revision: z.number().int().positive(),
  name: ReviewableFieldSchema,
  document: z.object({
    rawHash: z.string().min(16),
    sourceType: z.enum(["pdf", "docx", "demo"]),
    fileName: z.string().min(1),
    consentConfirmed: z.literal(true)
  }).strict(),
  roles: z.array(CandidateRoleSchema).min(1),
  provenanceEvents: z.array(ProvenanceEventSchema)
}).strict();

export const ProfileReviewTaskSchema = z.object({
  fieldPath: z.string().min(1),
  sourceExcerpt: z.string().nullable(),
  reason: z.string().min(1),
  resolutionStatus: z.enum(["open", "resolved"])
}).strict();

export const SkillGroupSchema = z.enum(["direct", "transferable", "supporting"]);

export const TranslatedSkillSchema = z.object({
  skillId: z.string().min(1),
  label: z.string().min(1),
  group: SkillGroupSchema,
  sharedCompetency: z.string().nullable(),
  sourceEvidenceIds: z.array(z.string().min(1)).min(1),
  sourceQuote: z.string().min(1),
  whyItTransfers: z.string().min(1)
}).strict();

export const TranslatedRoleSilverSchema = z.object({
  sourceRoleId: z.string().min(1),
  originalTitle: z.string().min(1),
  originalCountry: z.string().min(1),
  auEquivalentFunction: z.string().nullable(),
  skills: z.array(TranslatedSkillSchema),
  omissions: z.array(z.object({
    sourceEvidenceId: z.string().min(1),
    reason: z.string().min(1)
  }).strict())
}).strict();

export const CandidateSkillProfileGoldSchema = z.object({
  profileId: z.string().min(1),
  revision: z.number().int().positive(),
  targetRoleId: z.string().min(1),
  groups: z.array(z.object({
    kind: SkillGroupSchema,
    skills: z.array(TranslatedSkillSchema)
  }).strict())
}).strict();

export const JdSkillSchema = z.object({
  skillId: z.string().min(1),
  label: z.string().min(1),
  requirement: z.enum(["required", "preferred"]),
  importance: z.enum(["essential", "important", "supporting"]),
  weight: z.number().positive().max(100),
  evidenceSpan: z.string().min(1)
}).strict();

export const JobDescriptionSilverSchema = z.object({
  jdId: z.string().min(1),
  rawHash: z.string().min(16),
  targetRoleId: z.string().nullable(),
  source: z.object({
    producer: z.string().min(1),
    sourceUrl: z.string().min(1),
    capturedAt: z.string().min(1)
  }).strict(),
  skills: z.array(JdSkillSchema)
}).strict();

export const RoleSkillFrequencyGoldSchema = z.object({
  targetRoleId: z.string().min(1),
  jdCount: z.number().int().nonnegative(),
  robustness: z.enum(["indicative", "sample"]),
  skills: z.array(z.object({
    skillId: z.string().min(1),
    label: z.string().min(1),
    documentCount: z.number().int().positive(),
    percentage: z.number().min(0).max(100),
    sourceJdIds: z.array(z.string().min(1)).min(1)
  }).strict())
}).strict();

export const GapAnalysisGoldSchema = z.object({
  targetRoleId: z.string().min(1),
  referenceRobustness: z.enum(["indicative", "sample"]),
  gaps: z.array(z.object({
    skillId: z.string().min(1),
    label: z.string().min(1),
    description: z.string().min(1)
  }).strict()),
  summary: z.string().min(1)
}).strict();

export const CandidateJobMatchGoldSchema = z.object({
  matchId: z.string().min(1),
  profileId: z.string().min(1),
  profileRevision: z.number().int().positive(),
  jdId: z.string().min(1),
  skillMatches: z.array(z.object({
    jdSkillId: z.string().min(1),
    label: z.string().min(1),
    importance: z.enum(["essential", "important", "supporting"]),
    weight: z.number().positive().max(100),
    matchRate: z.enum(["high", "medium", "low"]),
    reason: z.string().min(1),
    jdEvidence: z.string().min(1),
    candidateEvidenceIds: z.array(z.string().min(1))
  }).strict())
}).strict();

export const DecisionActionSchema = z.enum(["shortlist", "needs_more_info", "not_a_fit"]);

export const DecisionEventSchema = z.object({
  eventId: z.string().min(1),
  clientRequestId: z.string().min(1),
  matchId: z.string().min(1),
  profileRevision: z.number().int().positive(),
  action: DecisionActionSchema,
  actorLabel: z.string().min(1),
  note: z.string().nullable(),
  createdAt: z.string().datetime()
}).strict();

export type CandidateProfileSilver = z.infer<typeof CandidateProfileSilverSchema>;
export type ProfileReviewTask = z.infer<typeof ProfileReviewTaskSchema>;
export type TranslatedRoleSilver = z.infer<typeof TranslatedRoleSilverSchema>;
export type CandidateSkillProfileGold = z.infer<typeof CandidateSkillProfileGoldSchema>;
export type JobDescriptionSilver = z.infer<typeof JobDescriptionSilverSchema>;
export type RoleSkillFrequencyGold = z.infer<typeof RoleSkillFrequencyGoldSchema>;
export type GapAnalysisGold = z.infer<typeof GapAnalysisGoldSchema>;
export type CandidateJobMatchGold = z.infer<typeof CandidateJobMatchGoldSchema>;
export type DecisionEvent = z.infer<typeof DecisionEventSchema>;
