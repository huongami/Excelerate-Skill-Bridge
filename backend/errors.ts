export class AppError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly status = 400,
    public readonly retryable = false,
    public readonly fieldPaths?: string[]
  ) {
    super(message);
  }
}

export function errorBody(error: unknown) {
  const appError = error instanceof AppError
    ? error
    : new AppError("INTERNAL_ERROR", "Unexpected server error", 500, true);
  return {
    status: appError.status,
    body: {
      error: {
        code: appError.code,
        message: appError.message,
        retryable: appError.retryable,
        ...(appError.fieldPaths ? { fieldPaths: appError.fieldPaths } : {})
      }
    }
  };
}
