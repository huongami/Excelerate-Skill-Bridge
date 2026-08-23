import OpenAI from "openai";
import { z } from "zod";
import { getEnvironment } from "@/infra/env";
import { AppError } from "@/backend/errors";
import { PROMPTS, type PromptName } from "@/backend/prompts";

type GuardedGenerateInput<T> = {
  promptName: PromptName;
  input: unknown;
  schema: z.ZodType<T>;
  demoFactory?: () => T;
};

function parseJson(content: string): unknown {
  try { return JSON.parse(content); }
  catch { throw new AppError("AI_INVALID_JSON", "Model returned invalid JSON", 502, true); }
}

export async function guardedGenerate<T>({ promptName, input, schema, demoFactory }: GuardedGenerateInput<T>): Promise<T> {
  const environment = getEnvironment();
  if (environment.demoMode) {
    if (!demoFactory) throw new AppError("DEMO_FIXTURE_MISSING", `No deterministic fixture for ${promptName}`, 500);
    return schema.parse(demoFactory());
  }

  const client = new OpenAI({ apiKey: environment.OPENAI_API_KEY });
  const jsonSchema = z.toJSONSchema(schema, { target: "draft-7" });
  let validationMessage = "";

  for (let attempt = 0; attempt < 2; attempt += 1) {
    const completion = await client.chat.completions.create({
      model: environment.OPENAI_MODEL,
      messages: [
        { role: "system", content: PROMPTS[promptName] },
        { role: "user", content: JSON.stringify({ input, validationMessage }) }
      ],
      response_format: {
        type: "json_schema",
        json_schema: { name: promptName.toLowerCase(), strict: true, schema: jsonSchema }
      }
    });
    const content = completion.choices[0]?.message.content;
    if (!content) throw new AppError("AI_EMPTY_RESPONSE", "Model returned no content", 502, true);
    const result = schema.safeParse(parseJson(content));
    if (result.success) return result.data;
    validationMessage = result.error.message;
  }

  throw new AppError("AI_SCHEMA_VALIDATION_FAILED", `Model failed ${promptName} schema validation after one retry`, 502, false);
}
