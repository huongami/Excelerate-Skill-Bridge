import type {
  CandidateJobMatchGold,
  CandidateProfileSilver,
  CandidateSkillProfileGold,
  DecisionEvent,
  GapAnalysisGold,
  JobDescriptionSilver,
  ProfileReviewTask,
  RoleSkillFrequencyGold,
  TranslatedRoleSilver
} from "@/backend/schemas/artifacts";

export type ProfileSession = {
  profile: CandidateProfileSilver;
  reviewTasks: ProfileReviewTask[];
  rawText: string;
  targetRoleId?: string;
  translatedRoles?: TranslatedRoleSilver[];
  skillProfile?: CandidateSkillProfileGold;
  gaps?: GapAnalysisGold;
  frequencyContext?: RoleSkillFrequencyGold;
};

export type MatchSession = {
  match: CandidateJobMatchGold;
  jd: JobDescriptionSilver;
  decisions: DecisionEvent[];
  processedRequestIds: Set<string>;
};

export interface SessionRepository {
  getProfile(id: string): ProfileSession | undefined;
  putProfile(id: string, session: ProfileSession): void;
  getMatch(id: string): MatchSession | undefined;
  putMatch(id: string, session: MatchSession): void;
  clear(): void;
}
