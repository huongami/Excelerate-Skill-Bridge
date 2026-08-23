import { handle } from "@/backend/controllers/http";
import { createDecision } from "@/backend/controllers/matches";

export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  return handle("matches.decide", async () => createDecision((await context.params).id, await request.json()), 201);
}
