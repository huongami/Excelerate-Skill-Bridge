import { handle } from "@/backend/controllers/http";
import { translate } from "@/backend/controllers/profiles";

export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  return handle("profiles.translate", async () => translate((await context.params).id, await request.json()));
}
