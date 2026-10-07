// Job search bar (Home and Jobs). It goes to "/jobs?q=…&location=…".
import { iconHtml as icon, esc } from "../core/dom.js";
import { LOCATIONS } from "../data/reference.js";

export function searchBarHtml({ q = "", location = "" } = {}) {
  return `
    <form class="search-bar" role="search" aria-label="Search jobs" data-search novalidate>
      <div class="search-field">
        <label class="sr-only" for="job-q">Search jobs</label>
        ${icon("search")}
        <input id="job-q" name="q" type="search" class="text-input" maxlength="100" autocomplete="off"
          placeholder="Search jobs by title, skill or company" value="${esc(q)}" />
      </div>
      <div class="search-location">
        <label class="sr-only" for="job-location">Location</label>
        <select id="job-location" name="location" class="text-input select">
          <option value="">All locations</option>
          ${LOCATIONS.map((l) => `<option value="${esc(l)}"${l === location ? " selected" : ""}>${esc(l)}</option>`).join("")}
        </select>
      </div>
      <button type="submit" class="btn btn-primary btn-lg">Search</button>
    </form>`;
}

export function bindSearchBar(root, navigate) {
  const form = root.querySelector("[data-search]");
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const params = new URLSearchParams();
    const q = form.q.value.trim();
    if (q) params.set("q", q);
    if (form.location.value) params.set("location", form.location.value);
    const qs = params.toString();
    navigate(`/jobs${qs ? `?${qs}` : ""}`);
  });
}
