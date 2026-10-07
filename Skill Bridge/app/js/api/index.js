// The only way views talk to the backend. Views must not read localStorage or call fetch() directly.
// Each function maps to one endpoint in the API contract (prompt.md).
//
// Lists (V2): a list method takes { page, pageSize, sort }. The real backend answers with
//   { items | <list key>, page: { page, pageSize, total, totalPages }, sort }.
// The mock backend does not know these parameters. For the mock, this file slices and sorts the list in the browser
// and builds the same `page` object (see withPage). If no page parameter is given, the whole list comes back with page 1.
import { CONFIG } from "../config.js";
import { session } from "../core/session.js";
import { ApiError } from "./errors.js";
import { httpAdapter } from "./http.js";
import { mockAdapter } from "./mock/adapter.js";
import { COMPARE_MAX } from "../data/levels.js";

export { ApiError };

const adapter = CONFIG.API_MODE === "http" ? httpAdapter : mockAdapter;
const isMock = () => CONFIG.API_MODE !== "http";

async function request(method, path, body) {
  try {
    return await adapter(method, path, body, session.token());
  } catch (e) {
    // An expired or invalid session: clear it and let the router send the user to sign in
    if (e instanceof ApiError && e.status === 401 && !path.startsWith("/auth/")) {
      session.clear();
      window.dispatchEvent(new CustomEvent("jinder:unauthorized"));
    }
    throw e;
  }
}

// ---------- Helpers for lists, compare and entitlements ----------

/** "?a=1&b=2" from an object. Empty values (undefined, null, "") are left out. */
function query(params = {}) {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== null && v !== "") sp.set(k, String(v));
  const s = sp.toString();
  return s ? `?${s}` : "";
}

const hasPaging = (o) => o.page != null || o.pageSize != null || o.sort != null;
const time = (v) => (v ? Date.parse(v) || 0 : 0);

// How the mock list is ordered for each sort value. The first value of a list in the contract is its default (the mock order).
const SORTERS = {
  best: (a, b) => (b.match?.rank ?? b.match?.coverage ?? b.coverage ?? 0) - (a.match?.rank ?? a.match?.coverage ?? a.coverage ?? 0),
  newest: (a, b) => time(b.postedAt || b.createdAt) - time(a.postedAt || a.createdAt),
  updated: (a, b) => time(b.updatedAt || b.createdAt) - time(a.updatedAt || a.createdAt),
};

/**
 * Make a list response have a `page` object. A response that has one (the real backend) is not changed.
 * Otherwise (the mock backend, or a list that is an array) the list is sorted and cut here.
 * @param {object|Array} res   the response
 * @param {{page?: number, pageSize?: number, sort?: string}} want  what the caller asked for
 * @param {string} key   the name of the list in the response (default "items")
 */
function withPage(res, want = {}, key = "items") {
  if (res && !Array.isArray(res) && res.page && typeof res.page === "object") return res;
  const all = Array.isArray(res) ? res : Array.isArray(res?.[key]) ? res[key] : [];
  const base = Array.isArray(res) ? {} : { ...res };
  let rows = all;
  if (want.sort && SORTERS[want.sort]) {
    const sorter = SORTERS[want.sort];
    // Stable: the same sort value gives the same order. Ties keep the order of the mock (then the id).
    rows = all.map((x, i) => [x, i]).sort((p, q) => sorter(p[0], q[0]) || p[1] - q[1] || String(p[0]?.id).localeCompare(String(q[0]?.id))).map((p) => p[0]);
  }
  // A list that the mock limits itself (for example the top 5 for a Basic employer) has one page
  const limited = base.limitedTo != null && base.limitedTo !== false;
  const paged = hasPaging(want) && !limited;
  const pageSize = paged ? Math.min(Math.max(1, Number(want.pageSize) || 10), 50) : Math.max(1, rows.length);
  const total = limited && Number.isFinite(base.total) ? base.total : rows.length;
  const totalPages = limited || !paged ? 1 : Math.max(1, Math.ceil(rows.length / pageSize));
  const page = paged ? Math.min(Math.max(1, Number(want.page) || 1), totalPages) : 1;
  return { ...base, [key]: paged ? rows.slice((page - 1) * pageSize, page * pageSize) : rows, page: { page, pageSize, total, totalPages }, sort: want.sort || base.sort || null };
}

// The mock cannot sort or cut a list on the server, so ask it for the whole list and do it here
const MOCK_ALL = 100;

// Client check for the compare calls (the server checks again: 400 with fields.ids)
function checkCompareIds(ids) {
  const list = [...new Set((Array.isArray(ids) ? ids : String(ids || "").split(",")).map((x) => String(x).trim()).filter(Boolean))];
  if (list.length < 2 || list.length > COMPARE_MAX) {
    const msg = `Choose 2 to ${COMPARE_MAX} to compare.`;
    throw new ApiError(400, "VALIDATION_ERROR", msg, { ids: msg });
  }
  return list;
}
// Compare works on the real backend only. The mock answers with this error, and the screen can show its message.
const needsBackend = (what) => new ApiError(501, "NEEDS_REAL_BACKEND", `${what} needs the real Jinder backend. Start the platform (python start.py) and open the app without ?mock=1.`);

// Entitlements: the V2 keys (crown, benefits, compareMax) are passed on when the backend has them. The two simple keys are filled in if not.
const normalizeEntitlements = (e) => ({ crown: e?.plan === "premium", compareMax: COMPARE_MAX, ...e });

export const api = {
  auth: {
    // POST /auth/signup -> 201 { ok: true }. The same answer for a new or an existing email.
    signup: (body) => request("POST", "/auth/signup", body),
    // POST /auth/login -> 200 { token, expiresAt, user }
    async login({ email, password, remember }) {
      const res = await request("POST", "/auth/login", { email, password, remember });
      session.set(res, remember);
      session.user = res.user;
      return res;
    },
    // POST /auth/logout -> 204
    async logout() {
      try { await request("POST", "/auth/logout"); } catch { /* sign out locally anyway */ }
      session.clear();
    },
  },
  me: {
    // GET /me -> 200 User
    async get() {
      const user = await request("GET", "/me");
      session.user = user;
      return user;
    },
    // PATCH /me -> 200 User. Allowed keys: name, company (recruiter), alias, profile, cv, onboarding (candidate).
    async update(patch) {
      const user = await request("PATCH", "/me", patch);
      session.user = user;
      return user;
    },
    // POST /me/password { currentPassword, newPassword } -> 204
    changePassword: (body) => request("POST", "/me/password", body),
    // GET /me/export -> 200 { exportedAt, account, … } a copy of the user's data (real backend only)
    export: () => request("GET", "/me/export"),
    // POST /me/delete { password } -> 204. Deletes the account and its data (real backend only)
    deleteAccount: (password) => request("POST", "/me/delete", { password }),
  },
  cv: {
    // POST /cv (multipart/form-data, field "file") -> 202 { cv: CvRecord, parse: { id, status: "parsing" } }
    // The mock cannot take a file, so it gets the file's name, size and type.
    upload(file) {
      if (CONFIG.API_MODE === "http") {
        const form = new FormData();
        form.append("file", file);
        return request("POST", "/cv", form);
      }
      return request("POST", "/cv", { name: file.name, size: file.size, type: file.type });
    },
    // GET /cv/parse/:id -> 200 { id, status: "parsing" | "done" | "failed", result?, error? }
    parseStatus: (id) => request("GET", `/cv/parse/${encodeURIComponent(id)}`),
  },
  profile: {
    // POST /profile/translate { profile, evidence } -> 200 { skills: TranslatedSkill[], gaps: string[] }
    translate: (body) => request("POST", "/profile/translate", body),
    // GET /me/shared-profile -> 200 SharedProfile (what employers see)
    shared: () => request("GET", "/me/shared-profile"),
  },
  aliases: {
    // GET /aliases/suggest -> 200 { alias }
    suggest: () => request("GET", "/aliases/suggest"),
    // GET /aliases/check?alias=&name= -> 200 { alias, available, reason?, suggestion? }
    check: (alias, name = "") => request("GET", `/aliases/check?${new URLSearchParams({ alias, name })}`),
  },
  jobs: {
    // GET /jobs/recommended?page=&pageSize=&sort=best|newest -> 200 { items: JobCard[], page, sort, source: JobSource }. Candidates only.
    // Old call recommended(5) still works: the number is the page size (the mock gets it as `limit`).
    async recommended(arg = {}) {
      const o = typeof arg === "number" ? { pageSize: arg } : { ...arg };
      if (o.limit != null && o.pageSize == null) o.pageSize = o.limit;
      const want = { page: o.page, pageSize: o.pageSize, sort: o.sort };
      if (isMock()) return withPage(await request("GET", `/jobs/recommended${query({ limit: hasPaging(want) ? 20 : want.pageSize })}`), want);
      return request("GET", `/jobs/recommended${query(want)}`);
    },
    // GET /jobs?q=&location=&page=&pageSize=&sort=best|newest -> 200 { total, items: JobCard[], page, sort, source }. Open jobs only. Candidates only.
    // Old keyword `limit` still works: it is the page size.
    async search({ q = "", location = "", limit, page, pageSize, sort } = {}) {
      const want = { page, pageSize: pageSize ?? limit, sort };
      if (isMock()) return withPage(await request("GET", `/jobs${query({ q, location, limit: hasPaging(want) ? MOCK_ALL : want.pageSize ?? 50 })}`), want);
      return request("GET", `/jobs${query({ q, location, ...want })}`);
    },
    // GET /jobs/:id -> 200 JobDetail
    get: (id) => request("GET", `/jobs/${encodeURIComponent(id)}`),
    // GET /jobs/compare?ids=a,b,c,d,e -> 200 { jobs: (JobCard + { axes, salaryMidpoint })[], axes, pairs, skillMatrix } (2 to 5 jobs; real backend only).
    // Fewer than 2 or more than 5 ids: the call is not sent. It fails with a 400 error that has fields.ids.
    // The mock fails with the code NEEDS_REAL_BACKEND (501) and a message that the screen can show.
    async compare(ids) {
      const list = checkCompareIds(ids);
      if (isMock()) throw needsBackend("Compare jobs");
      return request("GET", `/jobs/compare${query({ ids: list.join(",") })}`);
    },
    // PUT / DELETE /jobs/:id/skip -> 200 { jobId, skipped }
    skip: (id) => request("PUT", `/jobs/${encodeURIComponent(id)}/skip`),
    unskip: (id) => request("DELETE", `/jobs/${encodeURIComponent(id)}/skip`),
  },
  reports: {
    // POST /reports { targetType: "job" | "candidate", targetId, reason, details } -> 200 { ok }
    create: (body) => request("POST", "/reports", body),
  },
  applications: {
    // Candidate side (Feature 4)
    create: (body) => request("POST", "/applications", body),
    // GET /applications?page=&pageSize=&sort=updated|best|newest -> 200 { items, page, sort }
    async list({ page, pageSize, sort } = {}) {
      const want = { page, pageSize, sort };
      if (isMock()) return withPage(await request("GET", "/applications"), want);
      return request("GET", `/applications${query(want)}`);
    },
    get: (id) => request("GET", `/applications/${encodeURIComponent(id)}`),
    update: (id, body) => request("PATCH", `/applications/${encodeURIComponent(id)}`, body),
    chooseSlot: (id, body) => request("POST", `/applications/${encodeURIComponent(id)}/slot`, body),
    replyOffer: (id, accept) => request("POST", `/applications/${encodeURIComponent(id)}/offer-reply`, { accept }),
    decline: (id) => request("POST", `/applications/${encodeURIComponent(id)}/decline`),
    feedback: (id, body) => request("POST", `/applications/${encodeURIComponent(id)}/feedback`, body),
  },
  recruiter: {
    // Recruiter side (Features 5 and 6)
    jobs: {
      // GET /recruiter/jobs?page=&pageSize=&sort=newest -> 200 { items, page, sort }
      async list({ page, pageSize, sort } = {}) {
        const want = { page, pageSize, sort };
        if (isMock()) return withPage(await request("GET", "/recruiter/jobs"), want);
        return request("GET", `/recruiter/jobs${query(want)}`);
      },
      get: (id) => request("GET", `/recruiter/jobs/${encodeURIComponent(id)}`),
      create: (body) => request("POST", "/recruiter/jobs", body),
      update: (id, body) => request("PATCH", `/recruiter/jobs/${encodeURIComponent(id)}`, body),
      suggestSkills: (body) => request("POST", "/recruiter/jobs/suggest-skills", body),
      // POST /recruiter/jobs/import (multipart/form-data, field "file": PDF or DOCX ≤ 10 MB) -> 202 { parse: { id, status: "parsing" } }
      // The mock cannot take a file, so it gets the file's name, size and type.
      importFile(file) {
        if (CONFIG.API_MODE === "http") {
          const form = new FormData();
          form.append("file", file);
          return request("POST", "/recruiter/jobs/import", form);
        }
        return request("POST", "/recruiter/jobs/import", { name: file.name, size: file.size, type: file.type });
      },
      // GET /recruiter/jobs/import/:id -> 200 { id, status: "parsing" | "done" | "failed", result?: { fields, detected, missing, sampleLabel? }, error? }
      importStatus: (id) => request("GET", `/recruiter/jobs/import/${encodeURIComponent(id)}`),
      // GET /recruiter/jobs/:id/applications?page=&pageSize=&sort=newest -> 200 { job, items, page, sort }
      async applications(id, { page, pageSize, sort } = {}) {
        const want = { page, pageSize, sort };
        const path = `/recruiter/jobs/${encodeURIComponent(id)}/applications`;
        if (isMock()) return withPage(await request("GET", path), want);
        return request("GET", `${path}${query(want)}`);
      },
    },
    applications: {
      get: (id) => request("GET", `/recruiter/applications/${encodeURIComponent(id)}`),
      setStatus: (id, body) => request("POST", `/recruiter/applications/${encodeURIComponent(id)}/status`, body),
      confirmSlot: (id) => request("POST", `/recruiter/applications/${encodeURIComponent(id)}/confirm-slot`),
      feedback: (id, body) => request("POST", `/recruiter/applications/${encodeURIComponent(id)}/feedback`, body),
    },
    candidates: {
      // GET /recruiter/candidates?jobId=&view=all|saved&page=&pageSize=&sort=best|updated
      //   -> 200 { job, items, total, limitedTo, plan, page, sort, skippedCount }. A Basic employer gets 5 items and one page (limitedTo 5).
      async list({ jobId = "", view = "all", page, pageSize, sort } = {}) {
        const want = { page, pageSize, sort };
        if (isMock()) return withPage(await request("GET", `/recruiter/candidates${query({ jobId, view })}`), want);
        return request("GET", `/recruiter/candidates${query({ jobId, view, ...want })}`);
      },
      get: (id, jobId = "") => request("GET", `/recruiter/candidates/${encodeURIComponent(id)}?${new URLSearchParams({ jobId })}`),
      save: (id) => request("PUT", `/recruiter/candidates/${encodeURIComponent(id)}/save`),
      unsave: (id) => request("DELETE", `/recruiter/candidates/${encodeURIComponent(id)}/save`),
      skip: (id) => request("PUT", `/recruiter/candidates/${encodeURIComponent(id)}/skip`),
      clearSkipped: () => request("DELETE", "/recruiter/candidates/skipped"),
      contact: (id, body) => request("POST", `/recruiter/candidates/${encodeURIComponent(id)}/contact`, body),
      // Old two-talent call. It is kept so that old code runs, and it calls api.recruiter.compare([a, b], jobId).
      compare: (a, b, jobId = "") => api.recruiter.compare([a, b], jobId),
    },
    // GET /recruiter/compare?ids=a,b,c,d,e&jobId= -> 200 { job, candidates, radar, areas, skillMatrix } (Premium; 2 to 5 talent; jobId is required)
    // A Basic employer gets 403 PREMIUM_REQUIRED. The mock fails with the code NEEDS_REAL_BACKEND (501).
    async compare(ids, jobId = "") {
      const list = checkCompareIds(ids);
      if (isMock()) throw needsBackend("Compare talent");
      return request("GET", `/recruiter/compare${query({ ids: list.join(","), jobId })}`);
    },
  },
  notifications: {
    list: () => request("GET", "/notifications"),
    markRead: (ids = []) => request("POST", "/notifications/read", { ids }),
  },
  stats: { get: () => request("GET", "/stats") },
  entitlements: {
    // GET /entitlements -> 200 { plan, topN, canContact, canCompare, advancedCharts, crown, compareMax, benefits?: [{ key, label, description, available, used, usedCount }] }
    // `benefits` is only in the real backend. The mock has no `benefits`: screens must hide what they need it for.
    async get() { return normalizeEntitlements(await request("GET", "/entitlements")); },
    // PUT /entitlements { plan } -> same as get. Demo toggle: a real backend changes the plan through billing, not through this call.
    // After a change, the window event "jinder:plan-change" (detail = the entitlements) tells the menu to update the crown.
    async set(plan) {
      const ent = normalizeEntitlements(await request("PUT", "/entitlements", { plan }));
      window.dispatchEvent(new CustomEvent("jinder:plan-change", { detail: ent }));
      return ent;
    },
  },
  demo: {
    // Mock only: delete all mock data and write the demo data again
    reset: () => request("POST", "/demo/reset"),
  },
  bookmarks: {
    // GET /bookmarks?page=&pageSize=&sort=saved|best|newest -> 200 { items: JobCard[], page, sort }
    async list({ page, pageSize, sort } = {}) {
      const want = { page, pageSize, sort };
      if (isMock()) return withPage(await request("GET", "/bookmarks"), want);
      return request("GET", `/bookmarks${query(want)}`);
    },
    // PUT /bookmarks/:jobId -> 200 { jobId, bookmarked: true } (idempotent)
    add: (jobId) => request("PUT", `/bookmarks/${encodeURIComponent(jobId)}`),
    // DELETE /bookmarks/:jobId -> 200 { jobId, bookmarked: false }
    remove: (jobId) => request("DELETE", `/bookmarks/${encodeURIComponent(jobId)}`),
  },
};

export const isSignedIn = () => !!session.token();
