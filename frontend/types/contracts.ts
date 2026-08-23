import type { CandidateProfile, DecisionEvent, Frequency, GapAnalysis, Match, ReviewTask, SkillProfile } from "@/shared/contracts";

export type ParseProfileResponse = {
  profileId: string;
  revision: number;
  profile: CandidateProfile;
  reviewTasks: ReviewTask[];
};

export type ProfileResponse = {
  profile: CandidateProfile;
  reviewTasks: ReviewTask[];
  provenanceEvents: CandidateProfile["provenanceEvents"];
};

export type TranslationResponse = {
  translatedRoles: unknown[];
  skillProfile: SkillProfile;
  gaps: GapAnalysis;
  frequencyContext: Frequency;
};

export type MatchResponse = {
  matchId: string;
  match: Match;
  humanReviewCopy: string;
};

export type DecisionResponse = { event: DecisionEvent; decisionEvents: DecisionEvent[] };
