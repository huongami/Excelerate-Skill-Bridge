// HTTP adapter for the real backend. It follows the API contract in prompt.md.
import { CONFIG } from "../config.js";
import { ApiError } from "./errors.js";

export async function httpAdapter(method, path, body, token) {
  let res;
  try {
    res = await fetch(CONFIG.API_BASE_URL + path, {
      method,
      headers: {
        Accept: "application/json",
        // FormData (file upload): the browser sets the multipart Content-Type
        ...(body !== undefined && !(body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body instanceof FormData ? body : body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, "NETWORK_ERROR", "We can't reach the server. Check your connection and try again.");
  }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const e = (data && data.error) || {};
    throw new ApiError(res.status, e.code || "HTTP_ERROR", e.message || `Request failed (${res.status}).`, e.fields, { suggestion: e.suggestion, missing: data && data.missing });
  }
  return data;
}
