// App configuration.
// "http": the real backend (the jinder_platform folder). It serves this app and the API on the same address.
// "mock": the mock API in js/api/mock (data in browser localStorage). Add ?mock=1 to the address to use it,
// for example http://localhost:5173/?mock=1 (static server only, no backend).
const useMock = new URLSearchParams(location.search).get("mock") === "1";

export const CONFIG = {
  API_MODE: useMock ? "mock" : "http",
  // The same address as the app. If the API runs on another address, write it here and allow this origin on the server (JINDER_CORS_ORIGINS).
  API_BASE_URL: "/api",

  // Mock only: wait this many milliseconds for each request, so loading states are visible.
  MOCK_LATENCY_MS: 150,
  // Mock only: write demo accounts, jobs and applications the first time (see prompt.md "Demo data").
  MOCK_DEMO_DATA: true,
  // Mock only: shown on the sign-in screen so that people can try the demo. Password for both: demo1234.
  MOCK_DEMO_ACCOUNTS: [
    { label: "Talent demo (Teal Heron)", email: "candidate@demo.jinder.app" },
    { label: "Employer demo (Bluebushworks)", email: "recruiter@demo.jinder.app" },
  ],
  MOCK_DEMO_PASSWORD: "demo1234",
};
