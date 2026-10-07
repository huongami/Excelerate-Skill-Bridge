// System views: placeholder for sections that are not built yet, no access, and page not found.
import { iconHtml as i, logoHtml, esc } from "../core/dom.js";
import { isSignedIn } from "../api/index.js";

// A section in the navigation that a later phase builds
export const placeholderView = (title, text) => async (root) => {
  root.innerHTML = `
    <div class="dash">
      <div class="dash-head"><div><h1>${esc(title)}</h1><p class="dash-sub">${esc(text)}</p></div></div>
      <section class="panel">
        <div class="empty"><div class="icon-tile accent">${i("clock")}</div><p>This section is coming soon.</p><a href="#/home" class="btn btn-secondary">Back to Home</a></div>
      </section>
    </div>`;
};

export async function forbiddenView(root) {
  root.innerHTML = `
    <div class="dash">
      <div class="dash-head"><div><h1>You don't have access to this page</h1><p class="dash-sub">This page is for a different account type.</p></div></div>
      <section class="panel"><div class="empty"><div class="icon-tile accent">${i("shield")}</div><a href="#/home" class="btn btn-primary">Go to Home</a></div></section>
    </div>`;
}

export async function notFoundView(root) {
  root.innerHTML = `
  <nav class="top-nav" aria-label="Main"><div class="container">${logoHtml("#/")}</div></nav>
  <main class="legal-page">
    <span class="eyebrow">Error 404</span>
    <h1>We can't find this page</h1>
    <p class="updated">The link may be old, or the page may have moved.</p>
    <p class="btn-row btn-row-left"><a href="${isSignedIn() ? "#/home" : "#/"}" class="btn btn-primary">${isSignedIn() ? "Go to Home" : "Go to the home page"}</a></p>
  </main>`;
}
