import { parseJd } from "@/backend/controllers/jds";
import { handle } from "@/backend/controllers/http";

export async function POST(request: Request) {
  return handle("jds.parse", async () => {
    const form = await request.formData();
    const candidate = form.get("file");
    const file = candidate instanceof File && candidate.size > 0 ? candidate : null;
    return parseJd(file, String(form.get("text") ?? ""), String(form.get("sourceLabel") ?? "Recruiter JD"));
  }, 201);
}
