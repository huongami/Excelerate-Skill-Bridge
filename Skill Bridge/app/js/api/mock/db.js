// MOCK BACKEND — data store in browser localStorage. The real backend replaces this file.
// v2: the demo data is ICT only (decision D2). The data of v1 had other fields of work and is removed.
const KEY = "jinder.mock.db.v2";

// Remove data from the old multi-page prototype (decision Q8: start with clean data) and the old mock data
["sb_users", "sb_session", "jinder.mock.db.v1"].forEach((k) => localStorage.removeItem(k));

const empty = () => ({
  users: [], sessions: {}, bookmarks: {}, parses: {},
  skips: {}, reports: [], applications: [], notifications: [], events: [],
  postedJobs: [], jobImports: {}, savedCandidates: {}, skippedCandidates: {}, plans: {}, seeded: false,
});

export function loadDb() {
  try { return { ...empty(), ...JSON.parse(localStorage.getItem(KEY) || "{}") }; }
  catch { return empty(); }
}
export function saveDb(db) {
  localStorage.setItem(KEY, JSON.stringify(db));
}
export function resetDb() {
  localStorage.removeItem(KEY);
}

// Not secure. Only so that passwords are not plain text in localStorage. The backend must use bcrypt or Argon2.
export function demoHash(text) {
  let h = 5381;
  for (let i = 0; i < text.length; i++) h = ((h << 5) + h + text.charCodeAt(i)) | 0;
  return "q" + (h >>> 0).toString(16);
}

export const newId = () => crypto.randomUUID();
