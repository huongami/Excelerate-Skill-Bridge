// MOCK BACKEND — implements the API contract (prompt.md) in the browser, for demos.
// The real backend must enforce the same rules on the server. This file is not secure.
import { CONFIG } from "../../config.js";
import { ApiError } from "../errors.js";
import { loadDb, saveDb } from "./db.js";
import { routes } from "./core.js";
import { seedDemo } from "./seed-demo.js";
// Route files register their endpoints on import
import "./routes-account.js";
import "./routes-jobs.js";
import "./routes-applications.js";
import "./routes-recruiter.js";
import "./routes-platform.js";

export async function mockAdapter(method, path, body, token) {
  if (CONFIG.MOCK_LATENCY_MS) await new Promise((r) => setTimeout(r, CONFIG.MOCK_LATENCY_MS));
  const [p, qs = ""] = path.split("?");
  for (const r of routes) {
    if (r.method !== method) continue;
    const m = p.match(r.re);
    if (!m) continue;
    const db = loadDb();
    if (CONFIG.MOCK_DEMO_DATA) seedDemo(db);
    const params = Object.fromEntries(r.keys.map((k, i) => [k, decodeURIComponent(m[i + 1])]));
    const ctx = { db, params, query: Object.fromEntries(new URLSearchParams(qs)), body: body ? structuredClone(body) : {}, token, skipSave: false };
    const result = await r.handler(ctx);
    if (!ctx.skipSave) saveDb(db);
    // Return a copy, as JSON over HTTP would (dates become ISO strings)
    return result == null ? null : JSON.parse(JSON.stringify(result));
  }
  throw new ApiError(404, "NOT_FOUND", "This endpoint does not exist.");
}
