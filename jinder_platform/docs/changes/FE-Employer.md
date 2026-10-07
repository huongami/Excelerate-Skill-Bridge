# FE-Employer: what changed (Jinder V2, wave 3)

Owner: FE-Employer agent. This file is for the Docs agent (merge into `prompt.md`, `DESIGN.md`, `README.md`) and for the lead.
All paths are in `jinder_frontend/app/` unless it says otherwise. Text is written in simple English.

## 1. Files

| File | Change |
|---|---|
| `js/views/recruiter.js` | Rewritten. All employer screens. One new export: `jobOverviewView`. `cleanJdText` is exported too (tests use it). |
| `styles-employer.css` | All CSS of this work. Tokens only (no raw colour). |
| `js/main.js` | ONE new line: the route `/my-jobs/:id/overview` (see section 2). |
| `tests/browser/check_fe_employer.py` (in `jinder_platform/`) | New browser check (section 9). |

## 2. Routes

| Route | Screen | Query |
|---|---|---|
| `#/my-jobs` | My jobs (pager) | `page`, `pageSize` |
| `#/my-jobs/new`, `#/my-jobs/new?from=file` | Post a job | |
| `#/my-jobs/:id/overview` | **New.** Job overview | |
| `#/my-jobs/:id` | Applicants of one job (pager, status filter) | `status` (`waiting` or a status), `page`, `pageSize` |
| `#/my-jobs/:id/edit` | Edit a job | |
| `#/candidates` | Talent list (All or Saved) | `jobId`, `view` (`saved`), `sort` (`best` or `updated`), `page`, `pageSize` |
| `#/candidates/:id` | Talent detail | `jobId` |
| `#/review/:id` | Review one application | |

* The plan says "`#/my-jobs/:id` for example" for the overview. That route is the applicants page already (links from notifications, Home and the review page use it). The overview is `#/my-jobs/:id/overview`. It is one additive line in `main.js`. It uses a dynamic `import()` of `recruiter.js`, so that `main.js` needs no second edit (the module is loaded already, so there is no extra request). The lead can change it to a named import.
* After "Post job" and "Save changes" the app opens the overview. The job title in My jobs and on Home opens the overview. My jobs has an "Applicants" button for the old target.
* `main.js` still redirects `#/candidates/compare` to `#/compare` (FE-Core). `recruiter.js` has no compare view any more.
* A query value is written to the URL only when it is not the default (`sort` not the first one, `page` above 1, `pageSize` not 10). `pageSize` also comes from the saved size when the URL has none.

## 3. Lists with pager and sort (R5, R6)

Used on My jobs, Applicants, Talent (All) and Talent (Saved). Components: `pagerHtml/bindPager/loadPageSize`, `sortSelectHtml/bindSort`.

* Page size is remembered for each list: keys `my-jobs`, `applicants`, `talent`, `talent-saved` (FE-Core adds the user id).
* A page, size or sort change draws the list in place (no full screen reload). The URL is updated with `history.pushState`. This does not start the router, so there is no flash. The Back button starts the router, which reads the URL again.
* A size change goes to page 1. A sort change goes to page 1.
* After a page change: the live region says "Page 2 of 5. Showing 11 to 20 of 47 talent profiles." and the focus moves to the list heading (`h2`, `tabindex="-1"`: `#myJobsTitle`, `#appsTitle`, `#talentListTitle`, the last one is `sr-only`). After a size change the focus goes to the "Rows per page" select. After a sort change the focus stays on the sort select and the live region says "Sorted by recently updated. Page 1 of ...".
* While a page loads, the list shows "Loading …" and `aria-busy="true"`. An old answer that comes late is dropped (a counter). An error shows the message and a "Try again" button (`role="alert"`). Empty states did not change.
* **My jobs** and **Applicants** have one sort only (newest first, plan 5.1). There is no sort select: the text "Newest first." tells the order.
* **Talent**: sort select (`#talent-sort`, label "Sort by"): "Best fit for this job" (default) and "Recently updated".
* **Basic employer**: 5 cards, no pager (`limitedTo`), and the gold upgrade box "You see the top 5 of N talent profiles. Premium shows all of them." (class `upgrade`) with a lock badge that is a button and opens the Premium dialog.
* **Applicants: status filter.** The API has no status filter. With a filter, the screen reads all pages (50 at a time, at most 20 pages) and pages the matches in the browser. Without a filter the paging is real (server side). The "All (n)" counts are gone, because the real counts are not known from one page. The list of statuses is fixed (all 9).
* **Home** asks for 10 jobs (chart "Applicants per job" says "Shows the newest 10 of N jobs." when there are more) and for 3 talent. A Premium employer that opens Home does not mark "See every talent profile" as used, because Home asks for 3.

## 4. Talent cards and detail (R2)

**Card** (`.cand-card`): alias link; "In your pipeline" chip; a facts row (`.cand-facts`): level chip (blue, only when known), years (exact `yearsExperience` when known, else the band), "Updated N days ago" (`.cand-updated`); roles and locations; up to 6 skill chips with the level as text ("Python · Advanced"). Skills that the job asks for come first and are green (a screen reader hears "(the job asks for this skill)"). Then up to 3 certification and award chips together (`.cand-creds`, `.cred-chip`: graduation icon = certification, star icon = award, a hidden "Certification:" or "Award:" before the text; names and years only, for example "AWS Certified Cloud Practitioner (2024)") and "+N more". Then the actions. At the right: coverage per job (`cov-mini`). **No score.**

**Detail**: head with alias, "Anonymous profile · matched to {job}", "Updated N days ago", and the buttons Save, Invite (or Review application), Compare toggle (Premium) or lock (Basic), Report. Profile panel (own markup `talentProfileHtml`, classes of `profile-card`): Level, Experience (exact years or band), Roles, Skills (chips with level text; green when the job asks for it, plus "needs Proficient" (`.chip-need`) when the job lists a level), Certifications, Awards, Qualifications, Domains, Target roles, Locations, Work types. A row is left out when the answer has no such key (the mock backend and old application snapshots). A key with the value `null` shows "Not given".

**Skill by skill table** (`.skills-wide`, `.skill-table`): Skill | Job needs ("Advanced · Must have" or "Nice to have") | Talent (level text or "—") | Result. Result is icon plus text: Meets (check), Below (alert), Missing (x), Related (target, "via {skill}"), or "Has it" when the talent has the skill but the level is not known. The result cell has a tint (green, gold, rose, blue). The side box has the coverage line and a text count ("1 meets", "1 missing"). The table is shown only when the job has `skillRequirements` and the talent has `skillLevels`. Otherwise the old list (`skill-match`) stays. The same table is on the **review** screen (the snapshot of the application must have `skillLevels`).

The browser computes the result from three things that the API gives: the status of the skill (`match.skills`, from the skill match), the levels of the talent (`skillLevels`) and the levels of the job (`GET /recruiter/jobs/:id`, key `skillRequirements`). There is no number and no score.

**Privacy**: the screens show only keys of the shared profile. The test scans the employer pages for e-mail text, the word "score", "nationality:", "visa status:", "date of birth", "gender:" and for the words candidate, recruiter, HR. The issuer of a certification is not shown (names and years only).

## 5. Compare entry points (R9) and Premium locks (R7)

* Premium employer: a check box on each card (`input[data-compare-pick]`, label "Compare" + hidden alias). On the detail: a toggle button (`[data-compare-toggle]`, `aria-pressed`, text "Add to compare" / "In compare list").
* `compareStore.add("talent", { id, alias, jobId })`. The basket bar is the one of the shell. The `jobId` is a hint for the compare page (the job that was chosen in the list). FE-Compare can use it or ignore it.
* The 6th item is refused: the check box is cleared, a visible note (`[data-compare-note]`, `role="status"`) and the live region say "You can compare up to 5 profiles.". The check boxes follow the basket (event `jinder:compare-change`: the bar, another tab). The listener ends when the screen is gone.
* Basic employer: the check box is replaced by `lockedBadgeHtml("Comparing talent", { static: true })` inside a ghost button with `data-premium-lock="Comparing talent"`. Invite has the same: `data-premium-lock="Inviting talent who did not apply"`. The gold upgrade box (`upgradeBoxHtml` in `recruiter.js`: `lockedBadgeHtml` button + text + "See plans") is used for the full list, the advanced charts on Home and "Interest per job" on the overview. Every lock opens the "Premium feature" dialog (`bindPremiumLocks(root)` on each screen).
* Removed: `compareView`, `premiumModal`, `radarPanelHtml`, `areasHtml`, the "Compare (n/2)" button and the two-profile check box flow, the `radar.js` import, and the use of `sharedProfileHtml` and `upgradeHtml` (replaced by `talentProfileHtml` and `upgradeBoxHtml`).

## 6. Job form (R2)

Route `#/my-jobs/new` and `#/my-jobs/:id/edit`. Field names are the API keys (`form.elements[name]`); error text goes to `.field-error[data-for=name]`.

| Field (id) | Name | Control | Notes |
|---|---|---|---|
| `jf-title` | `title` | text | |
| `jf-category` | `category` | select "Domain" | `DOMAINS`. The API key stays `category`. A value from older data stays as an extra option. |
| `jf-spec` | `specialisation` | select | `SPECIALISATIONS[domain]`. It changes with the domain; a value of another domain is cleared. |
| `jf-level` | `level` | select | `LEVELS`. "Mid" for a new job. |
| `jf-minyears`, `jf-maxyears` | `minYears`, `maxYears` | number 0 to 40, step 0.5 | An empty maximum means "or more" (hint). The browser checks maximum below minimum. |
| `jf-workmode` | `workMode` | select | `WORK_MODES` |
| `jf-edu` | `educationMin` | select | `QUALIFICATIONS` |
| `jf-location`, `jf-type`, `jf-salary`, `jf-closes`, `jf-target` | as before | | |
| `jf-desc` | `description` | textarea | `maxlength` 10000 (the backend limit; see section 8). Counter "n of 10,000 characters". |
| `jf-skill` + `[data-skills]` | `skills` (hidden), sent as `skillRequirements` and `skills` | skill rows | Combobox over `SKILLS` (free text allowed). Each row: name, level select (1 - Beginner … 5 - Expert) and check box "Must have", remove button. "Suggest skills" adds with level 3 and Must. Max 12. |
| `jf-cert-req`, `jf-cert-pref` | `certifications` (hidden) | two combobox lists | Pick from `CERTIFICATIONS` or type text. Chips with remove. Max 10 each; a name is in one list only. Sent as `{ required, preferred }`. |
| `[name=awardKind]` | `awards` (hidden) | 12 check boxes | `AWARD_KINDS`. Max 10. Sent as `{ preferred: [kind] }`. |

* **JD template**: a NEW job starts with the 8 headings "## About the role", "## What you will do", "## What you bring", "## Nice to have", "## Tech stack", "## What we offer", "## About the company", "## How we hire", each with one empty bullet ("- "). The hint says what "## " and "- " do. **When the form is sent**, `cleanJdText` removes empty bullets, headings without text and extra blank lines. A form with the untouched template gets the API error "Write a description of at least 30 characters." on the description.
* **Preview** button (`[data-preview]`, `aria-expanded`, text "Preview" / "Hide preview"): shows `jdViewHtml(cleanJdText(text))` and follows the text live while it is open.
* **JD import** works as before. The fields that the parser gives are filled: level, specialisation, years, work mode, education, `skillRequirements` (or `skills`), `certifications`, `awards`. The parser sends `domain` and `category`: the form uses `domain` first. A value that is not in a list of the form is left empty and marked "Missing". Every filled field has the "From your file" marker; a change removes it.
* **Errors**: API field errors (`fields`) are written next to the field with `aria-invalid` and `aria-describedby`; the focus goes to the first field with an error; a group (skills, certifications, awards) focuses its first control. The alert above says "Correct the fields that show an error." Enter in an empty combobox does not send the form.
* **Mock mode** (`?mock=1`): the fields the mock does not keep are not drawn (specialisation, level, years, work mode, education, skill level and must, certifications, awards). Skills are chips as before. The template, the counter and the preview stay.
* Edit: all values come back (also skill levels and the check boxes). A job from older data has names only: its skills start at level 3 and "Must have".

## 7. Job overview page (R4, F3)

`jobOverviewView` at `#/my-jobs/:id/overview`. Data: `api.recruiter.jobs.get(id)` and `api.stats.get()` (only for the interest card).

* Header: h1 title; company · place · salary; chips `.jo-chips`: status ("Open", "Closing soon" + the label "Closes in N days", "Closed"), level, work mode. Actions: **Edit job** (primary, not for a closed job), **See talent** (`#/candidates?jobId=`), **See applicants** (`#/my-jobs/:id`). Back link "My jobs".
* Closed job: banner (`.jo-banner`, `role="note"`) and no Edit button. The page is read-only.
* Small stats (`.jo-stats`, `report-card`): Applicants with the target meter, Waiting for you, Invited, Interest in this job (Premium: Shown, Opened, Saved, Applied for this job, from `stats.advanced.jobs`; Basic: gold lock badge "Interest per job"). Opening the page as a Premium employer counts as using "Pipeline by stage and interest per job" (the BE writes `advanced_charts_view` for each `GET /stats`).
* "About the role" panel: the full description in `jdViewHtml(description, { label: "About the role" })` (scroll box, `tabindex="0"`, `role="region"`).
* "Job facts" (`dl.facts.jo-facts`): Domain, Specialisation, Level, Experience ("5 to 9 years", "6 years or more", "Up to 9 years"), Type, Work mode, Education, Posted, Closes. A key that the answer does not have is left out; a `null` shows "Not given".
* "Skills" table: Skill | Level needed | Must or nice (Must first). A job without levels shows chips.
* "Certifications and awards": required, preferred, preferred awards (labels from `AWARD_KINDS`). The panel is left out when the answer has neither key.

## 8. Differences between the real API and plan section 5

1. **JD limit is 10000**, not 6000 (`catalogue.MAX_DESCRIPTION`). The form uses 10000. It is not below 4000.
2. **`category` and the domains.** The form sends the domain ("Software Engineering", "AI & Machine Learning", "Data") as `category` (plan 4.4). At the start of this work the backend had the old list of 8 categories and answered "Choose a category.". The BE agent then set `JOB_CATEGORIES = DOMAINS` (wave 4), and the last full run posts a job with a domain without a problem. If the old list comes back, the test shows one failing check, and goes on with an old value (marked WORKAROUND in the output). The seed data of the jobs still has old categories in this build (`'jobs': 384`), so the Domain select of an old job has its old value as an extra option.
3. `GET /recruiter/jobs/:id/applications` has no status filter. The status filter reads all pages (see section 3).
4. `GET /recruiter/candidates/:id` has no per-skill level table (only `match.skills` status). The screen needs `GET /recruiter/jobs/:id` (`skillRequirements`) and `skillLevels` and computes Meets / Below. (`/recruiter/compare` has a `skillMatrix`; FE-Compare uses that.)
5. The JD parser sends `domain` and `specialisation` next to `category` (not in plan 5.4).
6. An old application snapshot has no `level`, `skillLevels`, `certifications` or `awards`. The review screen leaves these rows out for it.
7. The overview route is `#/my-jobs/:id/overview` (section 2).

## 9. Accessibility

* Every list has a heading that takes focus after a page change, and a polite live message. The pager component has its own `aria-live` range text.
* Result text is never only colour: every result has an icon and a word. The compare note, the lock badge text ("Premium feature: …") and the "job asks for this skill" text are readable by a screen reader.
* The job form: labels for every control (the level select and the "Must have" check box have a hidden skill name), `fieldset` and `legend` for the skills, the certifications and the awards, errors tied to fields, the first error gets focus, `aria-expanded` on Preview. The JD box is a focusable region.
* Touch screens (768px or less): `.btn` and `.text-input` are 44px high (styles.css rule). The skill row and the certification columns stack.
* Contrast: result cells use the dark pairs of the design (green, blue, rose) and the gold-ink on gold-tint pair of FE-Core (5.2:1) for "Below".

## 10. Tests: `tests/browser/check_fe_employer.py`

Run: `python tests/browser/check_fe_employer.py [--shots <folder>]` (starts the platform on port 8140 with a temp data folder and `--demo --reset-db`, Chrome debugging port 9340, and stops both; the platform start is tried 3 times with 3 minutes between tries). Or `--base http://localhost:8140 --employer-pw X --talent-pw Y` for a platform that runs already (the demo talent applies for the posted job, so the review checks have a real application).

It checks, with the real backend as the demo employer: Home as Basic and as Premium (links to the overview, the lock on the advanced charts, the interest table); talent cards and detail with a level, exact years, certifications and awards (3 chips and "+2 more", names and years only, no issuer, no person name); the static files (CSS owner line, no raw colour, no inline style, old compare code gone, the route line); `cleanJdText`; the Basic talent list (5 cards, no pager, the gold box, locks on Compare and Invite, the lock dialogs, sort select, level text on skill chips, "Updated N days ago"); the talent detail as Basic; the real JD import from a made DOCX file; the job form (all fields, domain and specialisation, template, hint, counter, preview, 3 skill rows with level and must, suggestions at level 3, certifications from the list and free text, awards, posting a JD of about 3,800 characters); the overview (full text, the box scrolls and takes focus, facts, skills table, certifications and awards, actions, stats, lock, Premium interest); the edit form (values come back, change one value, an empty maximum means "or more", maximum below minimum error); the API errors on an empty form; My jobs with 16 jobs (pager, page 2, Back, size 20, size remembered after reload, announcement and focus); the Premium talent list (real total, page 2 differs, URL, last page, sort "Recently updated", reload keeps the sort, size 20 and memory, Saved tab); the compare basket (5 in the bar, the 6th refused with the text, check boxes follow the bar, Clear); the invite; the talent detail with the table and as Premium (the compare toggle); the applicants page (filters, empty text) and the review (profile rows, the table); phone width (no sideways scroll); console errors and CSP reports; and `?mock=1` (Home, My jobs, the closed demo job overview, the Basic talent list, the old profile rows, the form without the new fields, mock import, posting and editing a job, applicants, review).

Result of the last full run (real backend, fresh database, then `?mock=1`): **205 checks passed, 0 failed**. The platform did not start at the first try (the BE agent was editing `engine_bridge.py`); the test waited 3 minutes and started it at the second try. Screenshots are written to the `--shots` folder (files `01-…` to `22-…`).

The three talent profiles with a level, exact years, certifications and awards are made by the test through the REST API (`ensure_talent`, `RICH_TALENT`), because the seed data at that time had `level: null` and no certifications. With the 50 new talent the same checks run on made-up people that the test adds, and they do not depend on the seed.

### Not tested
* The applicants list with more than 10 applications (it uses the same code as My jobs and Talent, which are tested with more than 10 rows).
* The "Below" result with live data (the table text is checked to be one of the 5 allowed results; the colour cell for "Below" is only seen in the style file).
* A closed job overview with the real backend (the backend does not accept a past close date, so the test uses the closed demo job of the mock).
* Screen readers (NVDA, VoiceOver): names, roles and live text are checked in the DOM only.
* Edge and Firefox. Only Chrome.
* The form with the keyboard only (the controls are native or the existing combobox).
* The compare page itself (FE-Compare).
* The pager checks do not depend on the size of the seed data: if the talent list has fewer than 24 profiles, the test makes made-up talent through the REST API (`ensure_talent`). The made-up people are in the temp database only.

## 11. Needs from other agents

* **BE:** optional: a `status` filter on `GET /recruiter/jobs/:id/applications` (today the browser reads all pages when a status filter is on). When wave 4 brings the 50 jobs and 50 talent, run `check_fe_employer.py` again (the checks adapt to the data size).
* **FE-Core / Data (mock):** the mock demo jobs have old categories. Editing one of them in `?mock=1` asks the employer to choose a domain, because the mock now checks the 3 domains.
* **Docs:** describe the new routes and components in `prompt.md` (screens 16 to 23) and `DESIGN.md` (Employer screens): `cand-facts`, `cand-creds`, `cred-chip`, `chip-need`, `skill-table` with the result cell, `skill-req` rows, `cert-editor`, `award-editor`, `jd-editor`, `jd-preview`, `job-overview` with `jo-stats`, `jo-grid`, `jo-facts`, `jo-banner`.

## 12. Class names added (`styles-employer.css`)

`list-toolbar`, `job-overview-link`, `compare-note`, `cand-facts`, `cand-updated`, `cand-creds`, `cred-chip`, `chip-need`, `skills-wide`, `skill-table`, `result-cell`, `result-counts`, `res-meets`, `res-has`, `res-related`, `res-below`, `res-missing`, `jd-editor`, `jd-editor-head`, `jd-textarea`, `jd-editor-actions`, `jd-preview`, `skill-add-combo`, `skill-req-list`, `skill-req`, `skill-req-name`, `skill-req-level`, `skill-req-must`, `cert-editor`, `cert-grid`, `cert-col`, `award-editor`, `award-grid`, `job-overview`, `jo-head`, `jo-chips`, `jo-banner`, `jo-stats`, `jo-interest`, `jo-grid`, `jo-facts`, `jo-lock`, `interest-list`, `chip-row`, `fact-empty`.
