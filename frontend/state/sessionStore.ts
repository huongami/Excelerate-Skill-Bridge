"use client";

import { create } from "zustand";
import type { CandidateProfile, DecisionEvent, Frequency, GapAnalysis, JobDescription, Match, SkillProfile } from "@/shared/contracts";

type AppSession = {
  profile?: CandidateProfile;
  skillProfile?: SkillProfile;
  gaps?: GapAnalysis;
  frequency?: Frequency;
  match?: Match;
  jd?: JobDescription;
  decisions: DecisionEvent[];
  setProfile: (profile: CandidateProfile) => void;
  setTranslation: (skillProfile: SkillProfile, gaps: GapAnalysis, frequency: Frequency) => void;
  setMatch: (match: Match) => void;
  setJd: (jd: JobDescription | undefined) => void;
  setDecisions: (decisions: DecisionEvent[]) => void;
  reset: () => void;
};

export const useSessionStore = create<AppSession>()((set) => ({
  decisions: [],
  setProfile: (profile) => set({ profile }),
  setTranslation: (skillProfile, gaps, frequency) => set({ skillProfile, gaps, frequency }),
  setMatch: (match) => set({ match }),
  setJd: (jd) => set({ jd, match: undefined }),
  setDecisions: (decisions) => set({ decisions }),
  reset: () => set({ profile: undefined, skillProfile: undefined, gaps: undefined, frequency: undefined, jd: undefined, match: undefined, decisions: [] })
}));
