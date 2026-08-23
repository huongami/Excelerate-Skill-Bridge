import { handle } from "@/backend/controllers/http";
import { readFrequency } from "@/backend/controllers/profiles";
import { AppError } from "@/backend/errors";

export async function GET(request: Request) {
  return handle("reference.frequency", () => {
    const targetRoleId = new URL(request.url).searchParams.get("targetRoleId");
    if (!targetRoleId) throw new AppError("INVALID_REQUEST", "targetRoleId is required", 400);
    return readFrequency(targetRoleId);
  });
}
