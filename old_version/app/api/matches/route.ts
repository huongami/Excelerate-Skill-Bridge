import { handle } from "@/backend/controllers/http";
import { createMatch } from "@/backend/controllers/matches";

export async function POST(request: Request) { return handle("matches.create", async () => createMatch(await request.json()), 201); }
