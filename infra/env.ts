import { z } from "zod";

const EnvironmentSchema = z.object({
  SKILL_BRIDGE_DEMO_MODE: z.enum(["true", "false"]).default("true"),
  OPENAI_API_KEY: z.string().optional(),
  OPENAI_MODEL: z.string().default("gpt-5-mini"),
  SESSION_SECRET: z.string().min(32).optional()
});

export function getEnvironment() {
  const parsed = EnvironmentSchema.parse(process.env);
  if (parsed.SKILL_BRIDGE_DEMO_MODE === "false" && !parsed.OPENAI_API_KEY) {
    throw new Error("OPENAI_API_KEY is required when SKILL_BRIDGE_DEMO_MODE=false");
  }
  return { ...parsed, demoMode: parsed.SKILL_BRIDGE_DEMO_MODE === "true" };
}
