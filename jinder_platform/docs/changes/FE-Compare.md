# FE-Compare: what changed (Jinder V2, wave 3)

Owner: FE-Compare agent. This file is for the Docs agent (merge into `prompt.md`, `DESIGN.md`, `README.md`) and for the other agents.
All paths are in `Skill Bridge/app/` unless a path says otherwise. Text is written in simple English.

## 1. Files

| File | Change |
|---|---|
| `js/views/compare.js` | New (the FE-Core stub is replaced). Export `compareView(root, ctx)`. It uses `ctx.user.role`, `ctx.query.ids`, `ctx.query.jobId`. |
| `styles-compare.css` | New. The only CSS file of this work. Class names start with `cmp-`. Colours and spacing come from the tokens of `styles.css` and `styles-core.css`. |
| `tests/browser/check_fe_compare.py` (in `jinder_platform/`) | New browser check (section 9). |

No other file was changed. The old `jobCompareView` (`views/jobs.js`) and `compareView` (`views/recruiter.js`) are not used any more. FE-Talent and FE-Employer can remove them.

## 2. The page

Route: `#/compare` (both roles, `main.js` of FE-Core). The page is a full page in the app shell. The menu item "Compare" is the current item.
The page decides what to show by the role of the user.

| Role | What it compares | Data call | Plan |
|---|---|---|---|
| Talent (`candidate`) | 2 to 5 jobs | `api.jobs.compare(ids)` | Free |
| Employer (`recruiter`) | 2 to 5 anonymous talent profiles, for one chosen job | `api.recruiter.compare(ids, jobId)` | Premium |

There is no total score and no ranking of people anywhere. Every chart has a table with the same numbers.

### Address and basket

* Where the items come from: `?ids=a,b,c` in the address if it is there, else the compare basket (`compareStore`, kind `job` for talent and `talent` for an employer).
* Page and basket stay in step. A change on the page (add, remove, clear, the picker) writes the basket and the address. Example: `#/compare?ids=a,b,c` and for an employer `#/compare?ids=a,b,c&jobId=job-1`.
* The address is changed with `history.replaceState`. The router does not draw the page again, and no history entry is added.
* If the address has ids, the basket is **replaced** by these ids (so that a shared link and the basket do not differ).
* More than 5 ids: the page uses the first 5 and says so ("You chose 7 jobs. You can compare up to 5, so this page uses the first 5."). The note goes away at the next change.
* The titles of the items come from the answer. The page writes them to the basket, so that the tray and the picker show real names.

## 3. States

| State | `.cmp-body[data-mode]` | What the user sees |
|---|---|---|
| Loading | `loading` | "Comparing jobs…" (`role="status"`). |
| Updating | `results` | The old result stays, dimmed (`.cmp-panels.is-loading`, `aria-busy`), and the note "Updating the comparison…". |
| Results | `results` | Cards, then the panels (section 4 and 5). |
| Fewer than 2 items | `empty` | `.cmp-empty`: "Choose at least 2 jobs to compare" (employer: "talent profiles"), the chosen item (if one), and the button "Choose jobs". The picker is open when the user arrives (only then, not after a remove). No request is sent. |
| Error 404 | `error` | `.cmp-error` (`role="alert"`): the API message ("This job does not exist or was removed.") + "Remove the job that is not there any more, then try again." A "Remove" button for each chosen item. |
| Error 400 or other | `error` | The message of the API, a "Try again" button. |
| Locked (Basic employer) | `locked` | See below. |
| No open job (employer) | (no mode) | "You have no open job", button "Post a job" (`#/my-jobs/new`). |

The API does not tell which item failed. Thus the 404 page lists all items with a Remove button (see the report: "Needs from BE").

### The locked page (Basic employer)

* The page reads `GET /entitlements` (`canCompare` or `plan === "premium"`). It makes **no** compare, job or talent request.
* It shows the h1 "Compare talent", a gold lock badge (`lockedBadgeHtml`, opens the "Premium feature" dialog), a list of what Compare does, the `upgradeHtml` box ("See plans" to `#/settings?section=plan`), and a sample picture.
* The sample picture (`figure.cmp-example`) has the chip "Example" and the text "This picture is a sample. It does not show real people." The picture is a small table of "Profile A/B/C" and "Skill A/B/C" (`aria-hidden`).
* A 403 `PREMIUM_REQUIRED` from the compare call (the plan ended while the page was open) shows the same page with the line "Your plan does not include Compare now."

## 4. Talent page (`GET /jobs/compare`)

Header: h1 "Compare jobs", count text ("3 of 5 chosen", at 5: "5 of 5 chosen. That is the most you can compare."), "Clear all" and "Add to compare" (disabled at 5).

1. **Cards** (`ul.cmp-cards > li.cmp-card`, one for each job): a swatch (the line style of this job in the chart), the title (link to `#/jobs/:id`), a Remove button (`aria-label="Remove <title> from compare"`), company and place, a "Closed" chip when `status` is `closed`, a list of Level, Experience (min to max years), Work mode and Salary (middle) (`salaryMidpoint`), and "View job". An empty value shows a dash and the hidden text "Not listed".
2. **"How each job fits you"** (`#cmpFit`): ONE radar with one series for each job on the axes that all jobs have, and the numbers table: rows are the axes, the formula tag (F1, F2, F5) after the axis name, one decimal. The best value of a row has the text "Highest" (also if the row has ties; no mark when all values are equal). The text is only an extra cue.
3. **"Skills side by side"** (`#cmpSkills`): rows are the skills from `skillMatrix`. The first column has the skill and "You: Advanced (4)" or "You: —". Each cell: icon and word (Meets, Below, Missing) and "Needs Proficient (3) · Must have" or "Nice to have". A job that does not ask for the skill: "Not asked". The footer row "Skills you meet" shows "2 of 5 skills" for each job.
   * Meets: your level is the same or higher. Below: you have the skill at a lower level. Missing: you have no level (`yours` is `null`; a related skill does not count).
4. **"Details"** (`#cmpDetails`): Level, Specialisation, Experience, Work mode, Job type, Salary, Salary (middle), Education, Certifications required, Certifications preferred, Preferred awards. A row that no job has is hidden. If no row is left, the panel is not drawn.
5. **"How close the jobs are to each other"** (`#cmpPairs`): a matrix of jobs by jobs. Each cell has the overall number of Formula 3 (one decimal) and the tier word. The diagonal says "Same job". Under it, one `details.cmp-pair` for each pair: the parts (table), "Advice" and "Salary change, from the first job to the second".

## 5. Employer page (`GET /recruiter/compare`)

Header: h1 "Compare talent", the same count text, buttons and picker. Under it the select **"For which job?"** (`#cmpJob`).

* The select lists the own jobs that are not closed (`GET /recruiter/jobs?pageSize=50`). A closed job is added only if `?jobId=` names it (marked "(closed)").
* The default: `?jobId=` if it is an own job, else the last used job (`sessionStorage`, key `jinder.compare.lastJob.<userId>`), else the first open job.
* A change of the select writes the address and `sessionStorage` and loads again.

1. **Cards**: swatch, alias (link to `#/candidates/:id?jobId=<jobId>`), Remove (`aria-label="Remove <alias> from compare"`), Level, Experience (`yearsExperience` or the band `years`), Roles (first 2 titles), "Skills for this job" ("5 of 6 skills + 1 related", as on the talent card), and "View profile for this job".
2. **"Profiles on the same axes"** (`#cmpRadar`): ONE radar with one series for each profile (names are the aliases) and the numbers table. After the axis name a small note: F4 "merit model", F6 "fit to the job", `skills` "from the skills table". No "Highest" mark and no sort by value.
3. **"Skills side by side"** (`#cmpSkills`): rows are the skills of the job. The first column has the skill and "Job needs: Proficient (3) · Must have". Each cell: icon and word (Meets, Below, Related, Missing) and "Level: Advanced (4)", or "Related via <skill>", or "No level". A row "Other skills" (names, up to 8 and "+N more") and the footer "Skills that meet the job" ("5 of 6 skills").
4. **"Qualifications and recognition"** (`#cmpQuals`): rows Qualifications, Certifications and Awards. Names and years only ("Name (2023)"). No issuer. "None listed" when empty.
5. **"Where the profiles differ"** (`#cmpAreas`): rows are the `areas`. A cell says "1st", "2nd"… (position inside the area). Profiles with the same position also say "Equal". If all profiles have the same position in an area, every cell says "Equal". The muted line: "Jinder does not add the areas up and does not rank people. You decide."

## 6. The picker

* The button "Add to compare" (also "Choose jobs" in the empty state) opens a dialog made with `openModal` (class `cmp-picker-dialog`). Title "Choose jobs to compare" or "Choose talent to compare". The button "Done" applies the choice. "Cancel", the X and Esc close it without a change.
* The user changes a working copy of the choice. "Done" puts it into the basket and the address, and the page loads again. At 5 chosen, the other check boxes are disabled and the text says that 5 is the most.
* Parts: tabs (`role="tablist"`, arrow keys, Home and End), a search box, a count line (`aria-live="polite"`: "3 of 5 chosen. You can choose more."), the list "Chosen now" (chips with a remove button, so that an item that is not in the shown list can be removed), the list with check boxes, "Show more".
* A row has a check box, the title, short facts, and the chip "Chosen" when it is ticked. A closed job has a rose "Closed" chip.
* **Talent**: tabs "Saved jobs" (`api.bookmarks.list`, sort `saved`) and "Recommended" (`api.jobs.recommended`, sort `best`). The search box searches all jobs with `api.jobs.search` (after 300 ms, at least 2 characters). While a search text is there, no tab is selected. A page has 20 rows.
* **Employer**: tabs "Talent for this job" (`api.recruiter.candidates.list`, `view: "all"`, sort `best`, 50 rows a page) and "Saved talent" (`view: "saved"`). The search box filters the loaded rows by alias. Rows: alias, roles, level, years, "5 of 6 skills". No score.
* Focus: the dialog heading gets the focus when it opens (as in the other dialogs). When it closes, the focus goes back to the button that opened it (or to the heading if the button is disabled or gone). Enter in the search box or on a check box does not close the dialog. A change of the route closes it.

## 7. Accessibility

* Every table has a `caption` (hidden), `scope="col"` and `scope="row"`, and sits in `div.table-wrap.cmp-scroll[role="region"][tabindex="0"][aria-label="<name>. This table scrolls sideways on a small screen."]`.
* On narrow screens the tables scroll sideways inside this region. The first column is sticky (`position: sticky; left: 0`). The page itself does not scroll sideways. The cards also scroll sideways in a region at 768px or less.
* The radar legend names the series. Each series has its own colour, line style and marker (FE-Core). The swatch on a card and in a column head is the same swatch.
* Skill states always have an icon and a word. The colour pairs are: Meets (green pair), Below (gold pair of `styles-core.css`), Missing (rose pair), Related (blue pair). Secondary text uses `--cmp-muted` (a darker grey, 6.4:1 on white). Contrast of all state pairs is tested (4.5:1 or more).
* `announce()` says "<title> removed from compare. N jobs left.", "N jobs chosen." and "Compare list cleared."
* After a remove, the focus goes to the Remove button of the next card (or the Add button when no item is left). No focus is lost.
* The picker works with the keyboard (tabs with arrow keys, check boxes with Space, Esc to close).
* No inline style and no inline script (CSP). The `hidden` attribute is forced with `display: none !important` inside `.compare-page` and `.cmp-picker`.
* Lesson for other pages with a scroll region: a text with the class `sr-only` is `position: absolute`. If the scroll region is not a positioned box, such a text escapes the clip of the region and makes the whole page scroll sideways (found at 390px: 1261px wide). The scroll regions of this page (`.cmp-scroll`, `.cmp-cards-wrap`) have `position: relative`. Do the same for any `overflow-x: auto` box that holds `sr-only` texts.

## 8. CSS classes (`styles-compare.css`)

`compare-page`, `cmp-actions`, `cmp-count`, `cmp-toolbar`, `cmp-job-field`, `cmp-lockline`, `cmp-note`, `cmp-body`, `cmp-panels` (`is-loading`), `cmp-panel`, `cmp-cards-wrap`, `cmp-cards`, `cmp-card` (`cmp-card-min`), `cmp-card-head`, `cmp-card-title`, `cmp-card-meta`, `cmp-card-link`, `cmp-remove`, `cmp-swatch`, `cmp-facts`, `cmp-fit` (`cmp-fit-side`: radar and table side by side at 1240px or more and 3 items or fewer), `cmp-fit-table`, `cmp-scroll`, `cmp-table` (`cmp-n2` to `cmp-n5`, `cmp-skills-table`, `cmp-pairs-table`), `cmp-th`, `cmp-th-text`, `cmp-skill`, `cmp-sub`, `cmp-list`, `cmp-best`, `cmp-other`, `cmp-state`, `cmp-cell`, `cmp-meets`, `cmp-below`, `cmp-missing`, `cmp-related`, `cmp-none`, `cmp-none-text`, `cmp-self`, `cmp-index`, `cmp-pos`, `cmp-tie`, `cmp-pair-list`, `cmp-pair`, `cmp-pair-names`, `cmp-pair-body`, `cmp-sub-title`, `cmp-empty`, `cmp-loading`, `cmp-error`, `cmp-fix-list`, `cmp-fix-name`, `cmp-chip-list`, `cmp-locked`, `cmp-locked-head`, `cmp-locked-list`, `cmp-example` (`cmp-example-table`, `cmp-example-row`, `cmp-example-head`), `cmp-picker-dialog`, `cmp-picker`, `cmp-tabs`, `cmp-search`, `cmp-pick-count`, `cmp-pick-panel`, `cmp-pick-list`, `cmp-pick-item`, `cmp-pick-label`, `cmp-pick-check`, `cmp-pick-text`, `cmp-pick-title`, `cmp-pick-sub`, `cmp-pick-msg`.
Custom properties: `--cmp-muted`, `--cmp-col` (least width of a data column, 8.5rem), `--cmp-first` (width of the first column, 11rem).
It reuses classes of other files: `panel`, `dash`, `dash-head`, `panel-actions`, `data-table`, `table-wrap`, `chip*`, `btn*`, `tabs`, `tab`, `text-input`, `select`, `field`, `empty`, `icon-tile`, `check-list`, `upgrade`, `locked-badge`, `compare-chip`, `radar` (FE-Core), `series-1` to `series-5`, `rd-swatch*`.

## 9. API use and differences from the plan (section 5)

* Talent compare (`GET /jobs/compare`) and employer compare (`GET /recruiter/compare`) have the shapes of plan 5.2 and `BE.md`. The page read the real answers. Differences and details that the page depends on:
  * A job card has `salary` as text ("Market competitive") and `salaryMidpoint` as a number. For the old catalogue the midpoint is 130000 for "Market competitive". The page shows the midpoint on the card as "Salary (middle)".
  * `level`, `minYears`, `maxYears`, `workMode`, `educationMin`, `certifications`, `awards` are empty (`null`, `[]`) for the old catalogue. The page shows a dash and hides empty rows of the Details table. They fill when the new data arrives.
  * `pairs[].salaryChange` is a text like "+$0 AUD". The page does not read its sign. `pairs[].advice` has the words "The job seeker" (the API text). The UI rule says "Talent". See "Needs from BE".
  * `pairs` has only the pairs that the formula could compute. The matrix shows "No result" in a missing cell.
  * `radar.axes` of the employer compare has 7 axes today (skills, requirement fit, seniority fit, licence readiness, skill depth, experience, transferable skills). The page draws what the API sends. An axis may leave in wave 4 (the licence axis).
  * `areas[].ranks` has 4 areas. Positions can repeat (tie): 1, 1, 3.
  * `skillMatrix[].byCandidate[id].status` is `meets`, `below`, `related` or `missing`. For `related`, `level` is `null`. The page reads `candidates[].skills[].via` for the text "Related via …".
  * The 404 of the talent compare ("This job does not exist or was removed.") and of the employer compare ("We can't find one of the profiles.") do not say which id failed.
* Other calls: `api.entitlements.get()` (employer), `api.recruiter.jobs.list({ pageSize: 50 })` and `api.recruiter.jobs.get(id)` (a `?jobId=` on a later page), `api.bookmarks.list`, `api.jobs.recommended`, `api.jobs.search`, `api.recruiter.candidates.list` (picker).
* The page works with the real backend only. In mock mode the compare call fails with `NEEDS_REAL_BACKEND` and the page shows the message of the client ("… needs the real Jinder backend …") in the error panel.

## 10. Tests: `tests/browser/check_fe_compare.py`

* Run: `python tests/browser/check_fe_compare.py [--shots <folder>]`. It starts the platform on port 8150 with a temporary data folder (`--demo --reset-db`), Chrome with debugging port 9350, and stops both. If the platform does not start, it waits 180 seconds and tries again, up to 3 retries (`--retries`, `--retry-wait`). Or use `--base http://localhost:8150 --talent-pw X --employer-pw Y` for a running platform.
* It uses the real backend. The numbers on the page are compared with the numbers of the API (read with a token in Python): the fit table, the skill matrix (every cell), the pair matrix, the Details rows, the radar table of the employer, the areas and the qualifications.
* Talent: 2, 3 and 5 jobs from the basket (series count, tables), the empty page and the open picker, the refused 6th job (basket and address with 6 ids), remove (address, basket, focus, announcement, last remove sends nothing), the picker (tabs, Space, arrow keys, search, 5 limit, chosen marks, Esc, focus), an unknown job (message and Remove buttons), contrast, mobile at 390px (no sideways scroll of the page, tables scroll, sticky first column, no overlap).
* Employer Basic: the locked page, no compare, job or talent request, the "Example" picture, the badge dialog, mobile.
* Employer Premium: job select (default, change, last used job, `?jobId=`), 2, 3 and 5 talent, the refused 6th, remove, the picker (search by alias, saved tab), mobile, and a 403 during use.
* The test sets the employer plan with `PUT /entitlements` (Basic first, then Premium, and Basic at the end).
* Result of the last full run (old catalogue, backend of wave 1): **191 checks, all passed**. Screenshots of that run: 16 files (`01-talent-empty-picker.png` to `16-employer-plan-ended.png`) in the folder of `--shots` (default: the temp folder, `jinder-fe-compare-shots`).
* `--only talent` or `--only employer` runs one half.
* If the data has fewer than 6 open jobs for the talent or fewer than 2 open jobs for the employer, the test creates jobs with `POST /recruiter/jobs` and prints "DATA NOTE". It does not create talent profiles.

## 11. Not tested

* Screen readers (NVDA, VoiceOver, JAWS). Names, roles and live regions are tested in the DOM only.
* Edge, Firefox and Safari. Only Chrome. `color-mix` has a fallback (the plain `--body` colour for secondary text); the fallback was not looked at.
* Real touch devices. 390px is a narrow window in Chrome without touch.
* The compare buttons on the list pages (FE-Talent, FE-Employer) and the tray (FE-Core). The test fills the basket with `compareStore.add`.
* The new data (50 jobs, 50 talent, levels, certifications, awards). The page was tested with the old catalogue. Rows for level, experience, work mode, certifications and awards were tested for "hidden when empty" only. Check them again when wave 4 is in.
* A job with a very long title in the radar legend and the table head (the title is cut to 3 lines in the head and has the full text in `title`).
* A page opened by a link with ids of the other role (it gives the 404 error panel).
