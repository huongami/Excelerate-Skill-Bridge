import { createProfile } from "@/backend/controllers/profiles";
import { handle } from "@/backend/controllers/http";

export async function POST(request: Request) {
  return handle("profiles.parse", async () => {
    const form = await request.formData();
    const candidate = form.get("file");
    const file = candidate instanceof File && candidate.size > 0 ? candidate : null;
    return createProfile(file, form.get("consentConfirmed") === "true");
  }, 201);
}
