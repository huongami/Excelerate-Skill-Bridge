// Entry point: register the routes and start the router.
import { addRoute, setNotFound, setForbidden, startRouter } from "./core/router.js";
import { landingView } from "./views/landing.js";
import { loginView, signupView } from "./views/auth.js";
import { termsView, privacyView } from "./views/legal.js";
import { homeView } from "./views/home.js";
import { jobsView, jobDetailView, bookmarksView } from "./views/jobs.js";
import { settingsView } from "./views/settings.js";
import { applyView, applicationsView, applicationDetailView } from "./views/applications.js";
import { myJobsView, jobFormView, jobApplicationsView, reviewView, candidatesView, candidateDetailView } from "./views/recruiter.js";
import { compareView } from "./views/compare.js";
import { notificationsView } from "./views/notifications.js";
import { forbiddenView, notFoundView } from "./views/system.js";
import { closeOnboarding } from "./components/onboarding.js";

const app = { auth: true, shell: true, bodyClass: "page-soft" };

// Public
addRoute("/", landingView, {});
addRoute("/login", loginView, { title: "Sign in", guestOnly: true });
addRoute("/signup", signupView, { title: "Create account", guestOnly: true });
addRoute("/terms", termsView, { title: "Terms of Use" });
addRoute("/privacy", privacyView, { title: "Privacy Policy" });

// Both roles. Settings has no menu item: the user block at the bottom of the menu links to it (nav: "settings" marks that link).
addRoute("/home", homeView, { ...app, title: "Home", nav: "home" });
addRoute("/settings", settingsView, { ...app, title: "Settings", nav: "settings" });
// Compare: a talent compares jobs, an employer compares talent (Premium). The page decides by the role.
addRoute("/compare", compareView, { ...app, title: "Compare", nav: "compare" });

// The old compare routes go to "#/compare". The ids stay: "?ids=a,b" (and "?a=&b=&jobId=" of the old employer link becomes ids + jobId).
// They have no role check, so that the right page can explain a wrong role. Registered before "/jobs/:id" and "/candidates/:id".
function redirectToCompare(root, ctx) {
  const q = ctx.query || {};
  const ids = q.ids || [q.a, q.b].filter(Boolean).join(",");
  const params = new URLSearchParams();
  if (ids) params.set("ids", ids);
  if (q.jobId) params.set("jobId", q.jobId);
  const qs = params.toString();
  ctx.navigate(`/compare${qs ? `?${qs}` : ""}`, { replace: true });
}
addRoute("/jobs/compare", redirectToCompare, { auth: true, title: "Compare" });
addRoute("/candidates/compare", redirectToCompare, { auth: true, title: "Compare" });

// Candidate
addRoute("/notifications", notificationsView, { ...app, title: "Notifications", nav: "notifications" });

// Candidate
const cand = { ...app, role: "candidate" };
addRoute("/jobs", jobsView, { ...cand, title: "Jobs", nav: "jobs" });
addRoute("/jobs/:id", jobDetailView, { ...cand, title: "Job detail", nav: "jobs" });
addRoute("/jobs/:id/apply", applyView, { ...cand, title: "Apply", nav: "jobs" });
addRoute("/bookmarks", bookmarksView, { ...cand, title: "Bookmarks", nav: "bookmarks" });
addRoute("/applications", applicationsView, { ...cand, title: "Applications", nav: "applications" });
addRoute("/applications/:id", applicationDetailView, { ...cand, title: "Application", nav: "applications" });

// Recruiter
const rec = { ...app, role: "recruiter" };
addRoute("/candidates", candidatesView, { ...rec, title: "Candidates", nav: "candidates" });
addRoute("/candidates/:id", candidateDetailView, { ...rec, title: "Candidate", nav: "candidates" });
addRoute("/my-jobs", myJobsView, { ...rec, title: "My jobs", nav: "my-jobs" });
addRoute("/my-jobs/new", jobFormView, { ...rec, title: "Post a job", nav: "my-jobs" });
addRoute("/my-jobs/:id", jobApplicationsView, { ...rec, title: "Job", nav: "my-jobs" });
addRoute("/my-jobs/:id/edit", jobFormView, { ...rec, title: "Edit job", nav: "my-jobs" });
addRoute("/my-jobs/:id/overview", (root, ctx) => import("./views/recruiter.js").then((m) => m.jobOverviewView(root, ctx)), { ...rec, title: "Job overview", nav: "my-jobs" });
addRoute("/review/:id", reviewView, { ...rec, title: "Review", nav: "my-jobs" });

setForbidden(forbiddenView);
setNotFound(notFoundView);

// Close an open dialog when the route changes
window.addEventListener("hashchange", closeOnboarding);

// Skip link: move focus to the main content without changing the route (the hash is the route)
document.querySelector(".skip-link").addEventListener("click", (e) => {
  e.preventDefault();
  const target = document.querySelector("#main") || document.querySelector("#app main") || document.getElementById("app");
  target.setAttribute("tabindex", "-1");
  target.focus();
});

startRouter();
