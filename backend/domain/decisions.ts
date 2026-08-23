import { randomUUID } from "node:crypto";
import { DecisionEventSchema, type DecisionEvent } from "@/backend/schemas/artifacts";
import type { MatchSession } from "@/backend/repositories/sessionRepository";

export function appendDecision(
  session: MatchSession,
  input: { clientRequestId: string; action: "shortlist" | "needs_more_info" | "not_a_fit"; actorLabel: string; note?: string }
): DecisionEvent {
  const existing = session.decisions.find((event) => event.clientRequestId === input.clientRequestId);
  if (existing) return existing;
  const event = DecisionEventSchema.parse({
    eventId: randomUUID(), clientRequestId: input.clientRequestId, matchId: session.match.matchId,
    profileRevision: session.match.profileRevision, action: input.action, actorLabel: input.actorLabel,
    note: input.note ?? null, createdAt: new Date().toISOString()
  });
  session.decisions.push(event);
  session.processedRequestIds.add(input.clientRequestId);
  return event;
}
