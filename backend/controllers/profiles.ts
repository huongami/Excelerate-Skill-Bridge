import { parseProfile, buildReviewTasks, applyProfileEdits } from "@/backend/domain/profile";
import { aggregateFrequency } from "@/backend/domain/frequency";
import { identifyGaps, translateProfile } from "@/backend/domain/translation";
import { AppError } from "@/backend/errors";
import { ProfilePatchRequestSchema, TranslateRequestSchema } from "@/backend/schemas/api";
import { referenceRepository } from "@/backend/repositories/referenceRepository";
import { localMemorySession } from "@/infra/session/localMemory";

export async function createProfile(file: File | null, consentConfirmed: boolean) {
  const { profile, rawText } = await parseProfile(file, consentConfirmed);
  const reviewTasks = buildReviewTasks(profile);
  localMemorySession.putProfile(profile.profileId, { profile, reviewTasks, rawText });
  return { profileId: profile.profileId, revision: profile.revision, profile, reviewTasks };
}

export function readProfile(profileId: string) {
  const session = localMemorySession.getProfile(profileId);
  if (!session) throw new AppError("PROFILE_NOT_FOUND", "Profile does not exist in this session", 404);
  return { profile: session.profile, reviewTasks: session.reviewTasks, provenanceEvents: session.profile.provenanceEvents };
}

export function updateProfile(profileId: string, body: unknown) {
  const request = ProfilePatchRequestSchema.parse(body);
  const session = localMemorySession.getProfile(profileId);
  if (!session) throw new AppError("PROFILE_NOT_FOUND", "Profile does not exist in this session", 404);
  session.profile = applyProfileEdits(session.profile, request.revision, request.edits);
  session.reviewTasks = buildReviewTasks(session.profile);
  session.translatedRoles = undefined; session.skillProfile = undefined; session.gaps = undefined;
  localMemorySession.putProfile(profileId, session);
  return { revision: session.profile.revision, profile: session.profile, reviewTasks: session.reviewTasks };
}

export function translate(profileId: string, body: unknown) {
  const request = TranslateRequestSchema.parse(body);
  const session = localMemorySession.getProfile(profileId);
  if (!session) throw new AppError("PROFILE_NOT_FOUND", "Profile does not exist in this session", 404);
  if (session.profile.revision !== request.revision) throw new AppError("REVISION_CONFLICT", "Profile changed; reload before translating", 409);
  const { translatedRoles, skillProfile } = translateProfile(session.profile, request.targetRoleId);
  const frequencyContext = aggregateFrequency(request.targetRoleId, referenceRepository.jdsFor(request.targetRoleId));
  const gaps = identifyGaps(skillProfile, frequencyContext);
  Object.assign(session, { targetRoleId: request.targetRoleId, translatedRoles, skillProfile, gaps, frequencyContext });
  localMemorySession.putProfile(profileId, session);
  return { translatedRoles, skillProfile, gaps, frequencyContext };
}

export function listTargetRoles() { return { targetRoles: referenceRepository.listTargetRoles() }; }
export function readFrequency(targetRoleId: string) { return { roleSkillFrequency: aggregateFrequency(targetRoleId, referenceRepository.jdsFor(targetRoleId)) }; }
