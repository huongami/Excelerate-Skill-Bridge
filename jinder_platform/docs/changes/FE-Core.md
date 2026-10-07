# FE-Core: what changed (Jinder V2, wave 1)

Owner: FE-Core agent. This file is for the Docs agent (merge into `prompt.md`, `DESIGN.md`, `README.md`) and for the other frontend agents (they call the shared components).
All paths are in `jinder_frontend/app/`. Text is written in simple English.

## 1. Files

| File | Change |
|---|---|
| `index.html` | Links `styles-core.css`, `styles-talent.css`, `styles-employer.css`, `styles-compare.css` after `styles.css`. |
| `styles-core.css` | New. All CSS of this work (see section 9). |
| `styles-talent.css`, `styles-employer.css`, `styles-compare.css` | New, empty. One line: `/* owned by <agent> */`. |
| `icons.svg` | New symbols `i-crown` and `i-lock`. |
| `js/data/levels.js` | New. Shared lists. |
| `js/core/compare-store.js` | New. The compare basket. |
| `js/components/pagination.js`, `sort-select.js`, `jd-view.js`, `premium.js`, `compare-tray.js` | New. |
| `js/components/radar.js` | Rewritten. Up to 5 series, two-layer mode. The old call still works. |
| `js/components/shell.js` | New menu, new user block, crown, lock, basket bar. |
| `js/components/charts.js` | `upgradeHtml` uses the gold chip with a lock. |
| `js/main.js` | Route `#/compare`. The old compare routes redirect. |
| `js/views/compare.js` | A stub. FE-Compare replaces the whole file. |
| `js/views/settings.js` | The plan section is the Premium card. |
| `js/api/index.js` | List parameters, compare methods, entitlements. |
| `js/api/mock/core.js` | `entitlementsOf` adds `crown` and `compareMax`. |
| `js/config.js` | No change. |
| `tests/browser/check_fe_core.py` | New browser check (section 11). |

## 2. Shared lists: `js/data/levels.js`

```js
LEVELS       = ["Intern","Junior","Mid","Senior","Lead","Principal"]   // rank 0 to 5
SKILL_LEVELS = [{ value: 1, label: "Beginner" }, { value: 2, label: "Working" }, { value: 3, label: "Proficient" },
                { value: 4, label: "Advanced" }, { value: 5, label: "Expert" }]
WORK_MODES   = ["Onsite","Hybrid","Remote"]
PAGE_SIZES   = [10, 20, 50]     // the first one is the default
COMPARE_MAX  = 5
levelRank(name)            // 0 to 5, or -1
skillLevelLabel(value)     // "Proficient" for 3, or ""
```

## 3. Pager: `js/components/pagination.js`

| Function | Meaning |
|---|---|
| `pagerHtml({ page, pageSize, total, limitedTo? })` | Returns the HTML. Returns `""` when `total` is 0, when `limitedTo` is set (a Basic employer sees 5 talent), or when there is one page and `total` is 10 or less. A list with one page but more than 10 items still shows the size select. |
| `bindPager(root, { onPage(page), onPageSize(size), pageSizeKey? })` | One click handler and one change handler on `root`. The pager can be drawn again at any time. A second call on the same `root` replaces the callbacks. `onPageSize` must reload from page 1. With `pageSizeKey`, the size is saved before `onPageSize` runs. |
| `loadPageSize(key)` | The saved size (10, 20 or 50). Default 10. A broken or unknown stored value gives 10. |
| `savePageSize(key, size)` | Saves the size. A size that is not in `PAGE_SIZES` is ignored. |
| `pageSlots(page, totalPages)` | The numbers in the row (a number is a page, `null` is a gap). |

* `key` is the name of the list, for example `"jobs"`. The user id is added for you: the storage key is `jinder.pagesize.<key>.<userId>`. If you add the user id yourself, it is not added twice.
* The row has at most 7 items. With more pages it shows gaps (an ellipsis).
* Markup: `div.pager[data-pager]` > `.pager-size` (label "Rows per page" + `select.pager-select[data-pager-size]`), `p.pager-range` ("Showing 11–20 of 134", `aria-live="polite"`), `nav.pager-nav[aria-label="Pagination"]` > `ul.pager-list` > `button.pager-btn` (`.pager-step` for Previous and Next, `.pager-num` for a page, `.is-current` and `aria-current="page"` for the current page, `data-pager-page="<n>"`), `li.pager-gap`.
* Touch screens (768px or less): buttons and select are 44px high.

## 4. Sort select: `js/components/sort-select.js`

* `sortSelectHtml({ id, value, options: [{ value, label }], label = "Sort by" })` returns `div.sort-select` with a visible `label` and a native `select.sort-select-input#<id>`. An unknown `value` selects the first option.
* `bindSort(root, id, onChange(value))` adds one change handler (a second call on the same select does nothing).
* Sort values and their order are in the API contract (plan section 5.1). The first option is the default.

## 5. Job description box: `js/components/jd-view.js`

* `jdViewHtml(description, { label = "Job description" })` returns `section.jd-view[tabindex="0"][role="region"][aria-label]`.
* Markup of the text: `## Heading` = `h3`. `- item` (also `* ` and a bullet sign) = `li` in a `ul`. A blank line ends a paragraph. Other lines = `p` (a line break inside a paragraph stays: `white-space: pre-line`). Any `#` heading is shown. A text with no headings is shown as paragraphs. No text gives "There is no description for this job."
* All text is escaped. No `innerHTML` with raw text.
* CSS: maximum height 32rem, `overflow-y: auto`, visible focus ring (2px accent), a soft shadow at the top and bottom that tells that there is more text (CSS only).
* `parseJd(description)` is also exported (blocks `{type: "h"|"ul"|"p"}`).

## 6. Premium markers: `js/components/premium.js`

| Function | Meaning |
|---|---|
| `crownIconHtml({ decorative?, label = "Premium" })` | The crown. Default: `span.crown[role="img"][aria-label="Premium"]`. With `decorative: true`: `aria-hidden` (use it when the text next to it says Premium). |
| `premiumChipHtml(text = "Premium")` | `span.chip.chip-gold.premium-chip`. |
| `lockedBadgeHtml(featureLabel, { static? })` | Gold chip with a lock and the text "Premium" (screen readers also read "Premium feature: <label>"). By default a `button.locked-badge[data-premium-lock="<label>"]`. With `{ static: true }` a plain `span` (use it inside a button or a link). |
| `bindPremiumLocks(root)` | Call once on a parent element. A click on any `[data-premium-lock]` inside opens the "Premium feature" dialog. Safe to call many times. |
| `openPremiumDialog(featureLabel)` | The dialog: title "Premium feature", text "<label> is part of Premium. In this demo you can switch your plan in Settings.", button "Go to Settings" (opens `#/settings?section=plan`). Same text as before. |

Rule: a Basic user sees the lock badge on a Premium feature. A Premium user sees the feature as normal. The crown is only for the account area.

## 7. Compare basket

### `js/core/compare-store.js`

```js
import { compareStore, COMPARE_EVENT } from "../core/compare-store.js";
compareStore.items(kind)        // [{ id, title, ...short text or number fields }], oldest first
compareStore.count(kind), compareStore.has(kind, id)
compareStore.add(kind, item)    // true; false at 5 items, for a wrong kind or an item without id. The same id twice gives true and no copy.
compareStore.remove(kind, id), compareStore.clear(kind)
compareStore.kindForRole(role)  // "candidate" -> "job", "recruiter" -> "talent"
```

* `kind` is `"job"` (talent compares jobs) or `"talent"` (employer compares talent).
* An item is `{ id, title }` for a job and `{ id, alias }` for talent. `title` is filled from `alias` or `name` if missing. The store keeps only strings (cut at 200), numbers and booleans (12 keys at most). The label cut is 120 characters.
* Storage key: `jinder.compare.<userId>.<kind>` in `localStorage`. The user id comes from `session.user.id`. Corrupted storage gives an empty list (not an error). More than 5 stored items are cut to 5.
* Event on `window`: `jinder:compare-change`, `detail = { kind, items, action: "add"|"remove"|"clear"|"sync", id }`. "sync" comes from another browser tab.

### `js/components/compare-tray.js`

* The app shell mounts the bar on every signed-in page, except `#/compare` (that page has its own list). **Lists must not mount a second bar.** They only call `compareStore.add` and `compareStore.remove`.
* `mountCompareTray({ host, shell, kind })` is exported if a page ever needs it.
* The bar (`aside.compare-tray[data-compare-tray]`) shows only when the basket has 1 or more items. It has: `strong.compare-tray-title` "Compare (n/5)"; a chip for each item with a remove button (`aria-label="Remove <title> from compare"`); "Open compare" (a link to `#/compare` when n is 2 or more; with 1 item a button with `aria-disabled="true"` and the visible text "Add 1 more job to compare." / "Add 1 more talent to compare."); "Clear".
* It is fixed at the bottom of the main area. Its left edge follows the menu (248px, 72px when hidden, 0 on small screens). The shell gets the class `has-compare-tray` and the main area gets bottom padding of the bar height (the height is measured, `--tray-h`), so the bar covers no content.

## 8. Radar: `js/components/radar.js`

* `radarHtml({ axes: [{ label }], series: [{ name, values }], layers? }, { caption?, layers? })`. The old call `radarHtml({ axes, series })` works. Returns `""` for fewer than 3 axes or no series.
* Up to 5 series (more are ignored in the chart and in the table). 3 to 10 axes (more still draw).
* Each series has its own colour class `series-1` … `series-5` **and** line style **and** marker shape: 1 solid, circle; 2 dashed, square; 3 dotted, diamond; 4 dash-dot, triangle; 5 long-dash, cross. The legend swatches use the same classes, so they match.
* `layers: true` (in the data or in the options): series 1 ("You have") is a filled shape, the other series are outlines only; series 2 ("Job requires") has a thicker line. The legend names are the series names. The figure gets the class `radar-layers`.
* Axis labels wrap to at most 3 lines of 14 characters (`wrapLabel`, also exported). The full text is in a `title` element. The chart is 560 × 470 and has room for labels of 3 to 10 axes.
* `role="img"` and `aria-label` with all values: "<series>: <axis> <value>, …". `radarTableHtml({ axes, series }, { note })` gives the same numbers as a table (one decimal; "—" for no value).
* Figure classes: `chart radar [radar-layers] [radar-many]`. SVG classes: `rd-svg`, `rd-ring`, `rd-spoke`, `rd-num`, `rd-label`, `rd-series`, `rd-shape`, `rd-dot` (`rd-dot-cross`). Legend: `rd-legend`, `rd-swatch`, `rd-swatch-fill`, `rd-swatch-line`.

## 9. Design tokens and contrast (`styles-core.css`)

The file adds these custom properties. All come from tokens of `styles.css`, except `--orange-strong`, which is a token of `Docs/DESIGN.md` that `styles.css` did not define (`#f27c0d`).

| Property | Value | Used for |
|---|---|---|
| `--gold` | `--orange` | crown fill, ring, borders of Premium |
| `--gold-tint` | `--tint-yellow` | gold chip background |
| `--gold-ink` | `--tint-yellow-ink` mixed 70% with `--ink` | gold chip text: **5.2:1** on `--gold-tint` (the plain `--tint-yellow-ink` has 3.1:1) |
| `--series-1` | `--accent` | 4.3:1 on white |
| `--series-2` | `--orange-strong` mixed 80% with `--ink` | 3.9:1 |
| `--series-3` | `--tint-blue-ink` | 11.6:1 |
| `--series-4` | `--success` mixed 70% with `--ink` | 4.9:1 |
| `--series-5` | `--tint-pink-ink` | 13.6:1 |

The plain tokens `--orange` (2.0:1) and `--success` (2.9:1) are below 3:1 for lines on white, so the series use the darker mixes. The mix uses `color-mix` inside `@supports`; a browser without it uses the plain tokens.
Contrast of the series colours and the gold chip is checked in `check_fe_core.py`.

Two findings about existing styles (not changed): `.chip-yellow` (`--tint-yellow-ink` on `--tint-yellow`) has 3.1:1, and `--muted` text (`.hint`) has 3.3:1 on white. Both are below 4.5:1.

CSS class names added: `chip-gold`, `premium-chip`, `locked-badge`, `crown`, `pager*`, `sort-select*`, `jd-view*`, `compare-tray*`, `compare-chip`, `series-1`…`series-5`, `radar-layers`, `radar-many`, `rd-swatch*`, `nav-premium`, `nav-premium-text`, `sidebar-user-link`, `avatar-wrap`, `avatar-crown`, `sidebar-chips`, `is-premium`, `has-compare-tray`, `plan-card`, `plan-card-head`, `benefit-list`, `benefit*`, `plan-demo`, `plan-section`, `icon-tile.gold`.

## 10. Shell, routes, Settings

### Menu
* Talent: Home, Jobs, Bookmarks, Applications, **Compare**, Notifications. Employer: Home, Talent, My jobs, **Compare**, Notifications. There is no "Settings" item.
* A Basic employer sees a gold lock and "Premium" on Compare (a small lock icon when the menu is hidden). The item still opens `#/compare`. The link title is "Compare (Premium feature)".
* **User block** at the bottom: ONE link (`a#shellUser.sidebar-user-link`) to `#/settings`. Accessible name: "Account settings, <name>". It has the avatar (initials), the name, the role chip (and the alias line for talent). It is the current page (`aria-current="page"`) on Settings. A "Sign out" button is under it (`.nav-signout`), and also in Settings.
* **Premium user:** the link gets `.is-premium`: a crown on the avatar (`.avatar-crown`), a gold ring, a small "Premium" chip. A hidden text "Premium plan" (`#shellPlanNote`) is the description of the link. The crown also shows when the menu is hidden. Small screens: the same block is in the opened menu.
* The plan is read from `api.entitlements.get()` (`crown` or `plan === "premium"`). It is cached in memory. The window event `jinder:plan-change` (detail = entitlements) updates the crown and the lock at once; `api.entitlements.set` sends it.
* `shell.js` exports `NAV`, `initials(name)` and `updateShellUser(user)` (call after a name change).

### Routes (`main.js`)
* `#/compare`: both roles, no role check, `nav: "compare"`. It loads `views/compare.js` and calls `compareView(root, ctx)` (`ctx.user.role`, `ctx.query.ids`, `ctx.query.jobId`). The stub shows h1 "Compare" and "Coming next.".
* `#/jobs/compare` and `#/candidates/compare` redirect (replace, no extra history entry) to `#/compare`. `?ids=a,b` stays. The old employer form `?a=&b=&jobId=` becomes `?ids=a,b&jobId=`.
* `#/settings` stays (the user block links to it). `#/settings?section=plan` scrolls to the plan section.
* `main.js` no longer imports `jobCompareView` and `compareView` of `jobs.js` and `recruiter.js`. Those functions still exist in the files of the other agents. They can be removed there.

### Settings (`views/settings.js`)
* The first section is **Your plan** (`#plan`). Backend with `entitlements.benefits`: a card (`.plan-card`) and under it the demo switch (text "Demo only: switch the plan to try the Premium features. There is no payment.").
  * Basic: head "Your current plan: Basic"; each benefit has a lock, label, description and a gold "Premium" chip; primary button "Try Premium (demo)" (sets the plan, the crown shows, focus moves to the card title, message "Your plan is now Premium."). 
  * Premium: crown tile, "Your current plan: Premium" with a gold chip, gold border; each benefit has a check and a chip "Used" (green) with "N times" when `usedCount` is more than 0, or "Not used yet" (neutral).
  * A benefit with `available: true` for a Basic user shows a check and "Included".
* No `benefits` (the mock backend): only the old plan section (the radio switch), in the same place.
* The demo switch text of Premium now says "compare up to 5 profiles".
* A failed plan change (for example `ALLOW_PLAN_SWITCH` off: 403) shows the message and sets the switch back to the real plan.

## 11. API client (`js/api/index.js`)

Every list method takes `{ page, pageSize, sort }`. The real backend answers with `page: { page, pageSize, total, totalPages }` and `sort`. For the mock, the client asks for the whole list, sorts it (`best` = rank or coverage, `newest` = `postedAt`/`createdAt`, `updated` = `updatedAt`; `saved` and unknown values keep the mock order) and cuts it, and builds the same `page` object. Without page parameters the whole list is returned with `page: { page: 1, pageSize: <count>, total: <count>, totalPages: 1 }`. A list with `limitedTo` (Basic employer) always has one page and keeps its `total`.

| Method | Request | Notes |
|---|---|---|
| `api.jobs.recommended(arg)` | `GET /jobs/recommended?page&pageSize&sort` | `arg` is a number (old call: the page size) or `{ page, pageSize, sort, limit? }`. `limit` means `pageSize`. Sort: `best`, `newest`. |
| `api.jobs.search({ q, location, page, pageSize, sort, limit? })` | `GET /jobs` | Sort: `best`, `newest`. |
| `api.bookmarks.list({ page, pageSize, sort })` | `GET /bookmarks` | Sort: `saved`, `best`, `newest`. |
| `api.applications.list({ page, pageSize, sort })` | `GET /applications` | Sort: `updated`, `best`, `newest`. |
| `api.recruiter.jobs.list({ page, pageSize, sort })` | `GET /recruiter/jobs` | Sort: `newest`. |
| `api.recruiter.jobs.applications(id, { page, pageSize, sort })` | `GET /recruiter/jobs/:id/applications` | Sort: `newest`. |
| `api.recruiter.candidates.list({ jobId, view, page, pageSize, sort })` | `GET /recruiter/candidates` | Sort: `best`, `updated`. A Basic employer: 5 items, `limitedTo: 5`, `page.totalPages: 1`, real `page.total`. |
| `api.jobs.compare(ids)` | `GET /jobs/compare?ids=a,b,…` | 2 to 5 ids. |
| `api.recruiter.compare(ids, jobId)` | `GET /recruiter/compare?ids=…&jobId=` | Premium. 2 to 5 ids. |
| `api.recruiter.candidates.compare(a, b, jobId)` | (old) | Kept: calls `api.recruiter.compare([a, b], jobId)`. The answer has the new shape. |
| `api.entitlements.get()` | `GET /entitlements` | Returns all keys of the backend. Fills `crown` and `compareMax` (5) if missing. `benefits` is only there if the backend sends it. |
| `api.entitlements.set(plan)` | `PUT /entitlements` | Same shape. Sends `jinder:plan-change`. |

All other client methods are unchanged (same name, same request).

Compare calls:
* Fewer than 2 or more than 5 distinct ids: nothing is sent. The promise fails with `ApiError(400, "VALIDATION_ERROR", "Choose 2 to 5 to compare.", { ids: "Choose 2 to 5 to compare." })`. The backend gives the same error shape.
* Mock mode: the promise fails with `ApiError(501, "NEEDS_REAL_BACKEND", "<Compare jobs|Compare talent> needs the real Jinder backend. Start the platform (python start.py) and open the app without ?mock=1.")`. The screen can show `err.message`.
* A Basic employer gets 403 `PREMIUM_REQUIRED` from the backend.

## 12. Tests: `tests/browser/check_fe_core.py`

* Run: `python tests/browser/check_fe_core.py [--shots <folder>]` (starts the platform on port 8120 with a temporary data folder, Chrome debugging port 9320, and stops both). Or `--base http://localhost:8120 --talent-pw X --employer-pw Y` for a running platform.
* Result of the last run: **179 checks, all passed** (with the backend of wave 1 at that time: it already had `page`, `sort`, `benefits`, `crown` and both compare endpoints).
* It tests: the static files; every shared component by importing the real modules in the page (pager, sort, JD box, premium, store, tray, radar with 3 to 10 axes); the menu, user block (one focusable link, keyboard order, current page), crown and lock, Compare route and the redirects, Settings plan card (Basic and Premium, with a stub and with the real backend), collapsed menu, mobile layout; list pages and compare calls against the real backend; mock mode (page object, sort, errors, old screens, plan section without card).
* The plan card is drawn from a clearly marked stub in the Basic and Premium checks ("stub" in the check name), because the stub gives a known `usedCount`. The real card is checked for the count of rows (Basic) and for "Used" with a count and "Not used yet" (Premium).
* Errors from a browser extension (`chrome-extension://`) in the console are skipped (this PC has an extension that throws an error on every page). The 404 of the optional mock file `data/australian_jobs_dataset.csv` is skipped in mock mode (known mock behaviour).

### Not tested
* The values of the real `GET /jobs/compare` and `GET /recruiter/compare` answers. Only the top keys are checked (and that the talent compare has no name and no email). FE-Compare tests the page.
* The exact text "1 time" (singular) with the real backend. It is only tested with the stub ("3 times").
* Screen readers (NVDA, VoiceOver). Names and roles are checked in the DOM only.
* Edge and Firefox. Only Chrome is used. `color-mix` has a fallback, but the fallback colours were not looked at.
* The pager, sort, JD box and basket buttons on the real list pages: those pages belong to FE-Talent and FE-Employer.
* The old browser journeys `e2e_demo.py` and `e2e_journey.py` were not changed. `e2e_demo.py` stops at the old job compare screen (`.job-compare`): the old route now redirects to `#/compare`, which is a stub until FE-Compare delivers.

## 13. How other agents use this

* **FE-Talent / FE-Employer (lists):** keep `const key = "jobs"`; `let size = loadPageSize(key)`; call the API with `{ page, pageSize: size, sort }`; draw `sortSelectHtml(...)` in the toolbar and `pagerHtml({ ...res.page, limitedTo: res.limitedTo })` under the list; call `bindSort` and `bindPager(root, { onPage, onPageSize, pageSizeKey: key })` once. After `onPageSize`, load page 1.
* **Compare buttons:** `compareStore.add("job", { id, title })` (talent) or `compareStore.add("talent", { id, alias })` (employer). If it returns `false`, tell the user "You can compare up to 5." The bar shows itself.
* **Premium locks:** call `bindPremiumLocks(root)`; for a Basic user put `lockedBadgeHtml("Invite talent", { static: true })` inside the button and `data-premium-lock="Invite talent"` on the button.
* **JD:** `jdViewHtml(job.description, { label: "Job description" })`.
* **Radar of "Your path":** `radarHtml({ axes, series: [{ name: "You have", values }, { name: "Job requires", values }], layers: true })`.
