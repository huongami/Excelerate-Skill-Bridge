import { z } from "zod";
import { DecisionActionSchema } from "./artifacts";

export const ApiErrorSchema = z.object({
  error: z.object({
    code: z.string(),
    message: z.string(),
    retryable: z.boolean(),
    fieldPaths: z.array(z.string()).optional()
  }).strict()
}).strict();

export const ProfilePatchRequestSchema = z.object({
  revision: z.number().int().positive(),
  edits: z.array(z.object({
    fieldPath: z.string().min(1),
    value: z.string().min(1),
    action: z.enum(["edit", "confirm"])
  }).strict()).min(1)
}).strict();

export const TranslateRequestSchema = z.object({
  revision: z.number().int().positive(),
  targetRoleId: z.string().min(1),
  targetIndustryId: z.string().optional()
}).strict();

export const MatchRequestSchema = z.object({
  profileId: z.string().min(1),
  revision: z.number().int().positive(),
  jd: z.object({ text: z.string().min(20), sourceLabel: z.string().min(1) }).strict(),
  clientRequestId: z.string().min(1)
}).strict();

export const DecisionRequestSchema = z.object({
  clientRequestId: z.string().min(1),
  action: DecisionActionSchema,
  actorLabel: z.string().min(1),
  note: z.string().max(1000).optional()
}).strict();

export type ApiError = z.infer<typeof ApiErrorSchema>;
