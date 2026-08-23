export function recordError(scope: string, error: unknown): void {
  const message = error instanceof Error ? error.message : "Unknown error";
  console.error(JSON.stringify({ level: "error", scope, message }));
}

export function recordTiming(scope: string, elapsedMs: number): void {
  console.info(JSON.stringify({ level: "info", scope, elapsedMs }));
}
