import { NextResponse } from "next/server";
import { ZodError } from "zod";
import { AppError, errorBody } from "@/backend/errors";
import { recordError } from "@/infra/telemetry";

export async function handle<T>(scope: string, operation: () => T | Promise<T>, successStatus = 200) {
  try { return NextResponse.json(await operation(), { status: successStatus }); }
  catch (error) {
    recordError(scope, error);
    const normalized = error instanceof ZodError
      ? new AppError("VALIDATION_ERROR", "Request or output failed schema validation", 400, false, error.issues.map((issue) => issue.path.join(".")))
      : error;
    const result = errorBody(normalized);
    return NextResponse.json(result.body, { status: result.status });
  }
}
