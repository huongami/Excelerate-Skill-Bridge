"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { CandidateProfile, DecisionEvent, Frequency, GapAnalysis, Match, SkillProfile } from "@/shared/contracts";

type AppSession = {
  profile?: CandidateProfile;
  skillProfile?: SkillProfile;
  gaps?: GapAnalysis;
  frequency?: Frequency;
  match?: Match;
  decisions: DecisionEvent[];
  setProfile: (profile: CandidateProfile) => void;
  setTranslation: (skillProfile: SkillProfile, gaps: GapAnalysis, frequency: Frequency) => void;
  setMatch: (match: Match) => void;
  setDecisions: (decisions: DecisionEvent[]) => void;
  reset: () => void;
};

export const useSessionStore = create<AppSession>()(persist((set) => ({
  decisions: [],
  setProfile: (profile) => set({ profile }),
  setTranslation: (skillProfile, gaps, frequency) => set({ skillProfile, gaps, frequency }),
  setMatch: (match) => set({ match }),
  setDecisions: (decisions) => set({ decisions }),
  reset: () => set({ profile: undefined, skillProfile: undefined, gaps: undefined, frequency: undefined, match: undefined, decisions: [] })
}), { name: "skill-bridge-demo" }));
