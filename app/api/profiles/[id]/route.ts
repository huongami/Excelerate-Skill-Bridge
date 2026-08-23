import { handle } from "@/backend/controllers/http";
import { readProfile, updateProfile } from "@/backend/controllers/profiles";

export async function GET(_: Request, context: { params: Promise<{ id: string }> }) {
  return handle("profiles.read", async () => readProfile((await context.params).id));
}

export async function PATCH(request: Request, context: { params: Promise<{ id: string }> }) {
  return handle("profiles.update", async () => updateProfile((await context.params).id, await request.json()));
}
