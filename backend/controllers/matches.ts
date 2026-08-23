import { extractJd, matchCandidate } from "@/backend/domain/matching";
import { appendDecision } from "@/backend/domain/decisions";
import { AppError } from "@/backend/errors";
import { DecisionRequestSchema, MatchRequestSchema } from "@/backend/schemas/api";
import { localMemorySession } from "@/infra/session/localMemory";

export function createMatch(body: unknown) {
  const request = MatchRequestSchema.parse(body);
  const profileSession = localMemorySession.getProfile(request.profileId);
  if (!profileSession?.skillProfile) throw new AppError("SKILL_PROFILE_REQUIRED", "Translate the candidate profile before matching", 409);
  if (profileSession.profile.revision !== request.revision) throw new AppError("REVISION_CONFLICT", "Candidate profile has changed", 409);
  const jd = extractJd(request.jd.text, request.jd.sourceLabel);
  const match = matchCandidate(profileSession.skillProfile, jd);
  localMemorySession.putMatch(match.matchId, { match, jd, decisions: [], processedRequestIds: new Set() });
  return { matchId: match.matchId, match, humanReviewCopy: "The recruiter decides; Skill Bridge only explains." };
}

export function createDecision(matchId: string, body: unknown) {
  const request = DecisionRequestSchema.parse(body);
  const session = localMemorySession.getMatch(matchId);
  if (!session) throw new AppError("MATCH_NOT_FOUND", "Match does not exist in this session", 404);
  const event = appendDecision(session, request);
  localMemorySession.putMatch(matchId, session);
  return { event, decisionEvents: [...session.decisions] };
}
