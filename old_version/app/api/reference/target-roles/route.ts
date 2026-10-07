import { handle } from "@/backend/controllers/http";
import { listTargetRoles } from "@/backend/controllers/profiles";

export async function GET() { return handle("reference.targetRoles", listTargetRoles); }
