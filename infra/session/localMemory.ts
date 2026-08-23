import type { MatchSession, ProfileSession, SessionRepository } from "@/backend/repositories/sessionRepository";

class LocalMemorySessionRepository implements SessionRepository {
  private readonly profiles = new Map<string, ProfileSession>();
  private readonly matches = new Map<string, MatchSession>();

  getProfile(id: string) { return this.profiles.get(id); }
  putProfile(id: string, session: ProfileSession) { this.profiles.set(id, session); }
  getMatch(id: string) { return this.matches.get(id); }
  putMatch(id: string, session: MatchSession) { this.matches.set(id, session); }
  clear() { this.profiles.clear(); this.matches.clear(); }
}

const globalStore = globalThis as typeof globalThis & { skillBridgeSession?: LocalMemorySessionRepository };
export const localMemorySession = globalStore.skillBridgeSession ?? new LocalMemorySessionRepository();
if (process.env.NODE_ENV !== "production") globalStore.skillBridgeSession = localMemorySession;
