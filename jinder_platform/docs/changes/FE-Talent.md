# FE-Talent: what changed (Jinder V2, wave 3)

Owner: FE-Talent agent. This file is for the Docs agent (merge into `prompt.md`, `DESIGN.md`, `README.md`).
All paths are in `jinder_frontend/app/`. Text is written in simple English. The plan is `docs/V2_PLAN.md`.

## 1. Files

| File | Change |
|---|---|
| `js/data/reference.js` | Rewritten from `ict_taxonomy.json` version 2 (section 2). |
| `js/components/job-card.js` | Level, experience and work mode chips. A "Compare" check box on each card. The helper for lists with a pager and a sort. |
| `js/views/jobs.js` | Jobs and Bookmarks with sort and pager. The job detail has the facts, certifications, awards, the full description in a scroll box and the Compare buttons. The old `jobCompareView` and the old compare picker are removed. |
| `js/views/home.js` | The recommendations widget asks for `pageSize` 5 and has no pager. The activity panel reads all the applications. "What employers see" shows level, years, certifications and awards. |
| `js/views/applications.js` | Applications list with sort and pager. New export `fetchAllApplications`. |
| `js/components/bridge.js` | New `pathHtml(path)`. The 12-month line chart is removed. `fitHtml` ("How this job fits you") is not changed. |
| `js/components/onboarding.js` | "Domain" instead of "Industry". New fields and a new step (section 7). |
| `js/components/profile-card.js` | Shows level, years, skill levels, certifications and awards. New exports `experienceOf`, `skillChipsHtml`, `sharedFactsHtml`. |
| `js/views/notifications.js`, `js/components/search-bar.js`, `js/components/combobox.js` | Not changed (the notification list has no pager in the plan). |
| `styles-talent.css` | All the CSS of this work (section 9). |
| `tests/browser/check_fe_talent.py`, `tests/browser/fixtures_path.json` | New browser check and the fixtures of `bridge.path`. |

## 2. Pick-lists: `js/data/reference.js`

The file starts with the line "from ict_taxonomy.json version 2". The test compares every list with the taxonomy file.

| Export | Meaning |
|---|---|
| `DOMAINS` | The 3 domains: Software Engineering, AI & Machine Learning, Data. |
| `SPECIALISATIONS` | Object: domain to a list of specialisations. |
| `ROLES` | The 53 role titles (no level word). |
| `FIELDS_OF_STUDY` | The 12 fields. |
| `CITIES` | The 7 cities. `LOCATIONS` is the same list (old name). |
| `WORK_MODES` | Re-exported from `data/levels.js`. `WORK_TYPES`, `QUALIFICATIONS`, `YEARS`, `COUNTRIES` are as before. |
| `LEVELS`, `SKILL_LEVELS` | Re-exported from `data/levels.js`. |
| `CERTIFICATIONS` | 38 items `{ name, issuer, domains, tier }`. |
| `AWARD_KINDS` | 12 items `{ kind, label }`. `kind` is the value that the API stores. |
| `SKILLS`, `SKILL_NAMES` | The 172 skill names of the taxonomy. `SKILL_SUGGESTIONS` has 9 names for each domain. |
| `INDUSTRIES`, `JOB_CATEGORIES` | Old names. They are the 3 domains now. |

All non-ICT industries, roles and fields are gone from this file.

## 3. Lists with a pager and a sort (R5, R6)

Screens: Jobs (and search results), Bookmarks, Applications. The Home widget has no pager.

| Screen | Sort values (the first is the default) | List name for the page size memory |
|---|---|---|
| Jobs | `best` "Best match", `newest` "Newest posted" | `jobs` |
| Bookmarks | `saved` "Recently saved", `best` "Best match", `newest` "Newest posted" | `bookmarks` |
| Applications | `updated` "Recently updated", `best` "Best skill match", `newest` "Newest application" | `applications` |

* **Helper** (in `job-card.js`): `createPagedList(cfg)` returns `{ state, start, load, reload }`. It reads `page`, `pageSize` and `sort` from the route query (`readListQuery`), loads a page with `cfg.fetchPage`, draws it with `cfg.render`, draws the sort select and the pager, and keeps the address.
* **Address.** After a change by the user the address gets `page`, `pageSize` and `sort` (other values, for example `q`, stay). The new entry is made with `history.pushState`. It does not send `hashchange`, so the router does not draw the page again. The Back button goes to the old address, and the router draws the page from it. A page past the end is moved to the last page by the server. Then the address is corrected with `replaceState`. A bad `sort` in the address gives the default sort.
* **A sort or page size change** goes to page 1. The size is saved per list and user by the pager of FE-Core.
* **Screen readers.** After a page change: the polite announcement "Page 2 of 7", and the focus goes to the heading of the list (`h2`, `tabindex="-1"`, scrolled into view). After a sort change: "Sorted by Newest posted. Page 1 of 7". After a size change: "20 rows per page. Page 1 of 3", and the size select keeps the focus. While a page loads, the list has `aria-busy="true"` (half transparent).
* **Bookmarks:** removing a bookmark removes its card at once, then the page loads again (quiet), so the next job moves up and the count is right. If the page is empty then, the server gives the last page. The old compare picker ("Compare jobs (n/3)") is removed.
* **Applications:** the API has no filter for Active and Past. So the list loads all the applications (`fetchAllApplications`: pages of 50, up to 10 pages) in the order of the chosen sort, and the browser filters the tab and cuts the page. The tab counts and the Home count are right. The sort is still done by the server. The tab links keep the sort.
* **Home:** `api.jobs.recommended({ pageSize: 5, sort: "best" })`, 5 cards and no pager. A line "Showing the 5 best of N recommended jobs. See all jobs" links to `#/jobs`.

## 4. Job card (R2) and the compare box (R9)

`jobCardHtml(job, { compact, compare })`:

* `ul.job-facts` with the chips **Level** (`chip-pink`), **Experience** (`chip-neutral`, "5–9 years", "5+ years", "Up to 6 years", "2 years") and **Work mode** (`chip-blue`). A fact that is `null` (old data, mock) has no chip. Without any fact there is no row. Each chip has a hidden word for screen readers ("Level: Senior") and a `title`.
* `label.check.check-sm.compare-pick` with `input[type=checkbox][data-compare-job][data-title]`. The name for a screen reader is "Compare <job title>". It is on every card (also the compact cards of "Similar jobs"), only with the real backend (`compare: false` leaves it out; the mock has no compare page).
* `bindCompare(root)`: one handler. A tick calls `compareStore.add("job", { id, title })`. The 6th job is refused: the box is cleared, a text "You can compare up to 5 jobs." shows next to the box (`span.compare-note`) and the polite announcement says it. The boxes follow the basket (the bar, another tab). Do not mount a second basket bar: the shell has it.
* Other exports: `experienceText(min, max)`, `jobFactsHtml(job)`, `compareCheckHtml(job)`, `addJobToCompare(job)`, `compareAvailable()`.

## 5. Job detail (R2, R4)

Order: head, then two columns (one column on a small screen), "Your path" panels, "Similar jobs".

* Left column: panel **Job facts** (`dl.fact-grid`: Level, Experience, Work mode, Place, Type, Salary, Education; a fact that the job does not have is left out). In the same panel, for a job that has V2 data: h3 **Certifications** with the groups "Required" and "Preferred" (chips), and h3 **Awards** with the group "Preferred" (the label of the award kind, for example "Hackathon"). A list that is empty says "This job does not ask for a certification." (or "an award"). A job with no V2 data shows neither section.
* Left column: panel **About the role** (`.jd-about`) with `jdViewHtml(job.description || job.summary, { label: "Job description" })`: the full text, the headings of the JD, a scroll box (`role="region"`, `tabindex="0"`). The maximum height is `min(32rem, 70vh)`. The panel keeps its place in the page.
* The category chip also shows the specialisation ("Data · Data analytics").
* Header buttons: **Compare** (`button.compare-btn[data-compare-detail]`, `aria-pressed`, a check mark when it is in the basket). In the panel "Similar jobs": **Compare with these jobs** (`[data-compare-similar]`): this job and the similar jobs go to the basket (at most 5; the jobs that are in already stay), then `#/compare` opens. If the basket is full, a polite announcement says how many jobs are in. Both buttons show only with the real backend.
* Removed: `jobCompareView`, `bindComparePicker` and the links to `#/jobs/compare`.

## 6. "Your path to this job" (R10, D7): `components/bridge.js`

* `pathHtml(path)`: `path` is `bridge.path` (plan section 5.3). `bridgeHtml(b)` = `fitHtml(b)` ("How this job fits you", not changed) + `pathHtml(b.path)`.
* The panel is `section.panel.bridge.path[aria-labelledby=pathTitle]`:
  * Head: h2 "Your path to this job" and the muted line "What you already have for this job, and what is still missing. This is a guide for you. Employers never see it."
  * Summary chips (`ul.path-summary`): "7 fit" (green, check), "3 gaps" (yellow, alert; "1 gap"), "about 5.5 months to close the gaps" (only when there is a gap), and the readiness tier (blue, with a hidden word "Readiness:").
  * Two columns (`.path-grid`, one column at 1024px or less). Left: the two-layer radar (`radarHtml(..., { layers: true })`, "You have" filled, "Job requires" outline) and a table "Skill group (0 to 100)" with the columns Job requires, You have and Status. The status is an icon and a word: **Fit** (check), **Above** (star), **Gap** (alert). Right: "Where you fit" and "Gaps to close" (`ul.path-list`, `li.path-item.path-fit` / `.path-gap`).
  * A fit item: check, the label (bold), a small chip for the kind when it is not a skill (Experience, Level, Certification, Award), "You: Advanced · Needs: Proficient", and the note.
  * A gap item: the kind chip (**Missing**, **Below level**, **Experience**, **Level**, **Certification**), the label, a **Required** chip when `must` is true, "You: None · Needs: Proficient", the months ("about 3.5 months", "less than 1 month") and the note.
  * An empty fit list: "Nothing in your profile meets a requirement of this job yet." An empty gap list: "No gaps: you meet every requirement."
  * Last line: "These are estimates from the type of each gap. They are not a promise and not a decision about you."
* A missing or empty `path` (the mock, an old job, a wrong value): the panel has only the head and "A detailed path is not available for this job." No crash.
* Removed: `lineChartHtml`, the 12-month chart, the facts list (occupation tier, "Time to close the gaps") and `bridge.projection`. The CSS classes `lc-*` in `styles.css` are not used any more (see "Needs").
* All text is escaped (the test checks that `<b>` in a note shows as text).

## 7. Onboarding and the profile fields (R1 UI)

Steps now: `cv, reading, education, experience, skills, credentials, translation, goals, review` (the new step is **credentials**). Edit paths: `credentials: ["credentials", "review"]` is new. "Edit" on the rows Certifications and Awards of "Your profile" opens it.

| Where | What |
|---|---|
| All steps | The word is **Domain** ("Domains", "Target domains", "Add at least one domain."). The keys `industry` and `targetIndustries` do not change. The domain list takes only the 3 domains (no custom value: "Choose a domain from the list."). The skill suggestions come from the chosen domains. |
| Experience | New: **Your level** (select: "Not sure" and the 6 levels) and **Exact years of experience** (optional number 0 to 40, step 0.5). A valid exact number sets the band ("Total years of work experience", same rule as the server) and locks the band drop-down. A number outside 0 to 40 gives "Enter a number from 0 to 40." |
| Credentials | **Certifications**: rows with Name (a combo box with the 38 known certifications; free text is allowed), Year (optional) and Issuer (optional). A known name fills the issuer and locks it ("From the list of known certifications."). **Awards**: rows with Name, Kind (select of the 12 kinds, required: "Choose a kind."), Year (optional). At most 20 rows in each list ("Maximum 20 reached"). Add and Remove buttons. A year must be from 1990 to next year. A row with nothing in it is dropped. The text under each list: "Employers see these names. Do not write your own name, your employer's name or contact details here." (the server removes e-mail addresses and phone numbers without a message). |
| Translation (skill review) | Each card of a skill that the talent named has a **Level** select (`select.tr-level-select`): "From the evidence (Advanced)" (the server uses the evidence, rule F8) and "1 · Beginner" to "5 · Expert". A card from a role or a qualification has no level. The level that the CV gave starts selected (it replaces the default of the server, the level of the evidence), with the tag "From your CV" until the talent changes it. A level that the talent changed stays. The preview "What employers see" shows level, years, certifications, awards and skill levels. |
| After a CV scan | The education step starts with the summary **What we found in your CV** (`div.cv-found`): current role, desired role, level, years, certifications, awards. A found field has a check mark and its value. A field that is not found has an alert icon and "Not found. You can add it in the next steps." The summary shows only when the server sends `result.found` (the V2 server). |
| After a CV scan, on the fields | Each new field (current role, level, exact years, certifications, awards, desired role) has the "AI-detected" tag and a hint line "From your CV. Check it. Change it if it is wrong.". When `result.found.<field>` is false and the field is empty the hint says "We could not find your desired role in your CV. You can add it." (and the same for current role, level, years, certifications, awards). The hint goes away when the talent adds a value. |
| CV result | `result.fields` is merged as before (it has the new keys). `result.domain` (one of the 3 domains) replaces `fields.industry`, which still has the old words. `result.skills[{name, level}]` gives the start level of a skill card. |
| Review | New rows: Level, Exact years, Certifications, Awards. Labels "Domains" and "Target domains". |

Profile keys sent with `PATCH /me`: `level`, `yearsExperience` (number or null), `certifications [{name, issuer, year}]`, `awards [{name, kind, year}]` and `translation[].level` (1 to 5 or null). The dialog cleans an old profile when it opens (`normalizeProfile`).

Exports added: `bandOf(years)`.

## 8. Profile card: `components/profile-card.js`

`sharedProfileHtml(p)` has the rows Roles, **Level**, **Experience** (the exact years first, then the range), Skills (with the level word: "Python · Advanced"), **Certifications**, **Awards** (name and year only; no issuer, no kind), Qualifications and the optional rows (Domains, Target roles, Locations, Work types). A row for a V2 key shows only when the key is in the object (a snapshot of an old application has none). `sharedFactsHtml(p)` gives short lines for small panels (the Home panel). `skillChipsHtml(p, max)`, `experienceOf(p)`.

## 9. CSS: `styles-talent.css`

Only design tokens of `styles.css` and `styles-core.css` are used for colour and space. Class names:

* Lists: `list-toolbar`, `recs-more`; `[data-list][aria-busy]`.
* Card: `job-facts`, `compare-pick`, `compare-note`. A long chip wraps (`.job-main .chip { white-space: normal }`), so the card does not run out of the page at 390px (this was a problem before).
* Detail: `jd-main`, `jd-about`, `fact-grid`, `cred-group`, `cred-label`, `cred-list`, `cred-none`, `compare-btn`.
* Path: `path-summary`, `path-grid`, `path-chart`, `path-table`, `path-status` (`-fit`, `-above`, `-gap`), `path-lists`, `path-col`, `path-list`, `path-item` (`path-fit`, `path-gap`), `path-icon`, `path-body`, `path-title`, `path-kind`, `path-required`, `path-detail`, `path-months`, `path-note`, `path-empty`, `path-empty-note`.
* Onboarding: `cv-hint` (`cv-hint-missing`), `cv-found` (`cv-found-title`, `cv-found-list`, `cv-found-label`), `cred-field`, `cred-hint`, `cred-rows`, `cred-row`, `cred-name`, `cred-year`, `cred-issuer`, `cred-kind`, `cred-remove`, `cred-add`, `cred-none`, `tr-level`, `tr-level-select`, `tr-level-from`.
* Profile card: `pf-skill-level`.

Colour tokens used: `--tint-green-ink`, `--tint-blue-ink`, `--tint-rose-ink`, `--tint-yellow-ink`, `--success`, `--ink`, `--body`, `--hairline`, `--accent`, `--accent-tint`, `--surface-subtle`. The small text of the new hints uses `--body` (not `--muted`, which has 3.3:1 on white).

## 10. Accessibility notes

* Every sort and size control is a native select with a visible label. Touch targets are 44px at 768px or less (the compare box too).
* The status of a path axis is an icon and a word. The kind of a gap is a word in a chip. "Required" is a word.
* The radar has a text table with the same numbers (`radarTableHtml` is used for "How this job fits you"; the path has its own table with the status).
* The description box is a labelled region and takes the focus (Tab, and the arrow keys scroll it). The focus ring shows.
* Errors in the new rows are under their field, with `aria-invalid` and `aria-describedby` (the id of the error). The first error takes the focus. Removing a row announces it and moves the focus to the next row or the Add button.
* Page, sort, size and basket changes are announced with the polite live region `#announcer`.

## 11. Differences between the real API and the plan (section 5), seen in this work

* `GET /jobs`: the answer has `total` and `page.total`, and `source`. `GET /jobs/recommended` has `source { openCount, updatedAt }`.
* The CV result has the new keys in `fields` (`targetRole` is a list there) and also as plain values at the top (`currentRole` text, `targetRole` text). `result.skills` is `[{name, level}]`. `fields.skills` stays a list of names. `fields.industry` still has the old words. Use `result.domain`.
* The shared profile rounds the exact years to 0.5 (7.3 shows as 7.5 for the employer). The talent sees the exact value in the dialog.
* `bridge.projection` is gone (as in the plan). `bridge.path` is there in the current backend. The `fit` item of kind `experience` has `need` "2 years or more" (text).
* A page past the last page gives the last page (`page.page`). The UI reads `page.page`.

## 12. Tests: `tests/browser/check_fe_talent.py`

* Run: `python tests/browser/check_fe_talent.py [--shots <folder>] [--skip components,lists,detail,onboarding,mock]`. It starts the platform on port 8130 with a temporary data folder and Chrome on debugging port 9330, and stops both. If the platform does not start (other agents edit the backend), it waits 180 seconds and tries again, up to 3 times. Or use `--base http://localhost:8130 --talent-pw X` for a running platform.
* Parts: the pick-lists against the taxonomy file; the job card, the profile card and `pathHtml` with the real modules and the fixtures (3, 6, 8, 10 axes, empty fit, empty gap, long labels, both empty, a missing path, the old answer); the real backend: Home, Jobs (page 2, Back, page past the end, page size and its memory, sort, search words in the address, empty state, error state, small screen), Bookmarks, Applications, the compare basket (add, remove, the 6th is refused, page 2), the job detail (real data; a stub for the V2 keys; keyboard; small screen); the onboarding with real CV files (found summary, hints, level, exact years, certification and award rows, errors, limit 20, skill levels, save, the stored profile, the Home panel, the apply review, edit mode); `?mock=1` for the old screens.
* A check with "stub" in its name uses the real answer of the server with V2 keys added in the page (`window.fetch`), or a fixture.
* The screenshots go to the folder of `--shots`.
* **Result of the last run** (real backend with the V2 data of wave 4, fresh database): **279 checks, all passed**. The run also ended with no console error and no CSP error on every part (components, lists, detail, onboarding, mock).
* The check "the search 'manager' has one page only" is skipped with an INFO line when the search has one page only (50 jobs).

### Not tested
* NVDA, VoiceOver and other screen readers. Names, roles and the live region text are checked in the DOM.
* Edge and Firefox. Only Chrome.
* More than 50 applications (the loop over pages of `fetchAllApplications`). The test has 12.
* A job with a full basket when "Compare with these jobs" is used (the partial add and its announcement).
* The employer side and `#/compare` (other agents).
* Drag and drop of the CV file (the test sets the file in the input).
* The 12 CV fixtures other than cv01, cv07 and cv13 (the CV agent tests the parser).

## 13. Needs from other agents

* **FE-Core:** `views/settings.js` ("What employers see", line 287) can call `sharedFactsHtml(s)` and `skillChipsHtml(s)` from `components/profile-card.js`, so that it shows level, certifications, awards and skill levels too. `styles.css` still has the unused `lc-*`, `line-chart` rules (the 12-month chart is gone).
* **BE:** a filter on `GET /applications` (`tab=active|past` or `final`) would let the list use a server pager. Until then the browser filters. `fields.industry` of the CV result should hold a domain.
* **Docs:** `prompt.md` embeds `reference.js` (appendix) and describes the screens 5 to 9 and 13; `DESIGN.md` needs the new components (list toolbar, chip row, compare box, path panel, credential rows, found summary).
