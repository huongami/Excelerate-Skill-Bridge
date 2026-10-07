// Error from the API. The backend sends: { "error": { "code", "message", "fields"? } }
// An error can also have "suggestion" (for example, a free alias for an ALIAS_TAKEN conflict).
export class ApiError extends Error {
  constructor(status, code, message, fields, extra = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status; // HTTP status, for example 400, 401, 403, 404, 409
    this.code = code; // VALIDATION_ERROR, INVALID_CREDENTIALS, UNAUTHORIZED, FORBIDDEN, NOT_FOUND, ALIAS_TAKEN, CONFLICT, INTERNAL
    this.fields = fields || null; // { fieldName: "message" } for VALIDATION_ERROR and ALIAS_TAKEN
    this.suggestion = extra.suggestion || null;
    // The compare endpoints name the ids that cannot be compared: { error, missing: [id, ...] } (404: unknown ids. 400: ids above the limit)
    this.missing = Array.isArray(extra.missing) ? extra.missing.map(String) : [];
  }
}
