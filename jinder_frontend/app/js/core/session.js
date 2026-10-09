// Session token storage. "Keep me signed in" uses localStorage. Otherwise sessionStorage (one tab).
const KEY = "jinder.session";

let cachedUser = null;

export const session = {
  token() {
    const urlToken = new URLSearchParams(window.location.search).get("demo_token");
    if (urlToken) return urlToken;
    const raw = sessionStorage.getItem(KEY) || localStorage.getItem(KEY);
    if (!raw) return null;
    try {
      const { token, expiresAt } = JSON.parse(raw);
      if (expiresAt && Date.parse(expiresAt) < Date.now()) { this.clear(); return null; }
      return token;
    } catch { this.clear(); return null; }
  },
  set({ token, expiresAt }, remember) {
    this.clear();
    (remember ? localStorage : sessionStorage).setItem(KEY, JSON.stringify({ token, expiresAt }));
  },
  clear() {
    sessionStorage.removeItem(KEY);
    localStorage.removeItem(KEY);
    cachedUser = null;
  },
  // The signed-in user from the last GET /me (or login). Views read it; api.me.get() refreshes it.
  get user() { return cachedUser; },
  set user(u) { cachedUser = u; },
};
