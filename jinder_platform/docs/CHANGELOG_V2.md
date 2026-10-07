# Jinder version 2: what changed

This list is for the people who use and judge the product. It follows the 12 feedback items (R1 to R12) of the second round.
For each item it says what you asked, what is true now, and where to see it.

To see the changes, run `python start.py --demo` in the folder `jinder_platform`, write down the two demo passwords, and open `http://localhost:8095/`.
Sign in as the demo talent (`candidate@demo.jinder.app`, alias Teal Heron) and as the demo employer (`recruiter@demo.jinder.app`, Bluebushworks).
Some features need the real backend. They do not work in the browser-only mock (`?mock=1`).

**All data in the demo is synthetic.** The 50 jobs, the 50 sample talent profiles and the 4 demo employer jobs were written for the demo. The companies are invented.
The demo covers three domains: **Software Engineering**, **AI & Machine Learning** and **Data**.

## R1. The CV scan did not read the current job title, the desired job and the current level

- **You asked:** the scan must read the current role, the desired role and the level.
- **Now:** the CV reader finds the **current role**, the **desired role**, the **level** (Intern, Junior, Mid, Senior, Lead, Principal), the **exact years of experience**, the **certifications** and the **awards**. It also gives each skill a level from 1 to 5 when the CV shows one.
  A field that the CV does not show is **left empty**. The reader does not guess. The screen then says "Not found. You can add it in the next steps." and each field can be changed.
  After a scan, the Education step starts with a summary "What we found in your CV". The new fields have the "AI-detected" tag and a hint "From your CV. Check it. Change it if it is wrong."
- **How good is it:** on 24 made-up CVs in different layouts (PDF and DOCX, one and two columns, LinkedIn export, Europass, LaTeX and others) every value that was found was right (24 of 24 CVs). The current role was found in 23 of 24 CVs, the level in 23, and the desired role in all 11 CVs that state one.
  Four more sets of CVs (124 CVs) that other writers made blind gave, on the first run: current role 85%, level 87%, desired role 94%, years 79%, certifications 57%, awards 58%. No set had a value where the CV shows none.
  For a new real CV, expect the current role and the level right in about 85 to 90 of 100 CVs. The lists of certifications and awards are the hard part (about 60 to 75 of 100 exactly right).
- **The own CV of the user (open item O1, now done).** The file that the scan could not read was found and tested. The reader gave these values: current role **Senior Data Analyst**, desired role **Data Analyst**, level **Senior**, years **7.8**, domain **Data**, **2 certifications found**, and **no award** (the CV shows none). Before the fix of defect D-1, the 2 certifications were not found (a page with a block of two columns inside one column); the reader now splits such a block, and the layout is a test fixture (cv24, with a made-up person). The file itself is private; its text is not copied into the project. The other numbers above come from made-up CVs.
- **Where to see it:** sign in as a new talent, upload a CV, and read the Education step. The test CVs are in `jinder_platform/tests/fixtures/cv`.

## R2. A job showed no experience, level, awards or certifications

- **You asked:** show the experience, the level, the awards and the certifications of a job, and of a talent.
- **Now:** every one of the 50 jobs has a **level**, an **experience range** (minimum and maximum years), **required and preferred certifications** and **preferred awards**.
  - The **job card** shows chips for the level, the experience and the work mode.
  - The **job detail** has a panel "Job facts" (level, experience, work mode, place, type, salary, education) and lists "Certifications" (required, preferred) and "Awards" (preferred).
  - The **employer job overview** page shows the same facts.
  - A **talent profile** has a level, exact years, certifications and awards. An employer sees them at once on the anonymous profile: the level, the years, the skill levels, and the **names and years** of certifications and awards. Never a name of a person. The talent is warned in the app not to write a name or contact details there.
- **Where to see it:** the Jobs list and any job detail (talent). The Talent list and a talent detail (employer). The step "Certifications and awards" in the onboarding.

## R3. Reduce the scope; fewer records; the overall fit of the jobs was the same

- **You asked:** use fewer records, normalised data, only software, AI and data, and make the fit different for each job. Give detail for each job and talent.
- **Now:** the product has **three domains only**. There are **50 new synthetic jobs** and **50 new synthetic talent profiles**, each with a level, years, skills with a level (1 to 5), certifications and awards. All other fields of work are removed from the data, the pick-lists, the job form and the translation library.
  One list of names, the **taxonomy** (`jinder_backend_engine/data/reference/ict_taxonomy.json`), is used by the data, the formulas, the CV reader and the pick-lists. It has 172 skills, 38 certifications, 12 award kinds, 20 specialisations and 53 role titles.
  The six formulas were rewritten (see R12) so that two jobs seldom have the same fit.
- **The numbers** (the test `test_differentiation`): for each talent, the top 20 jobs have **at least 18 different Fit scores** (formula level: min 19, mean 19.5; platform level: min 18, mean 19.49). The best job and the worst job are at least **45 points apart** (mean 55). No radar axis has the same value for all jobs. For each job, the order of the talent list has at most 1 exact tie in the top 10.
  The plan first asked for 19 different scores. The lead changed the target to 18, because a smooth score with a range of 40 points cannot promise 19 for every talent when the scores have one decimal.
- **Where to see it:** the Jobs list (the Fit scores are different), and the data in `jinder_backend_engine/data/synthetic`.

## R4. "About the role" was cut

- **You asked:** the full text, with the headings of the job description, and a scroll bar when the box is full. On the talent and the employer pages.
- **Now:** the job description is stored **in full** (1,400 to 3,500 characters, at least 6 headed sections, never cut; the limit is 10,000 characters and a longer text is refused with a message). It shows with its headings ("About the role", "What you will do", "What you bring", "Nice to have", "Tech stack", "Certifications and awards", "What we offer", "About the company", "How we hire") in a **box with a maximum height and a scroll bar**. The box takes the keyboard focus, so the keyboard can scroll it.
  - The talent sees it on the job detail. The employer sees it on the new **job overview** page (`#/my-jobs/:id/overview`).
  - The employer **job form** starts with the 8 headings as a template, has a counter and a **Preview** button.
- **Where to see it:** open any job (talent). As employer, open "My jobs" and click the title of a job.

## R5. Show a limited number of jobs or talent per page

- **You asked:** a number of items for each page, a way to go to the next page, and a choice of the number.
- **Now:** every list of jobs, bookmarks, applications, employer jobs, applicants and talent has a **pager**: "Rows per page" (**10, 20 or 50**; the default is 10), "Showing 11–20 of 134", Previous, Next and numbered buttons. The server cuts the list (`page` and `pageSize`). The choice is remembered in the browser for each list. The page, the size and the sort are in the address, so the Back button works. A Basic employer sees the top 5 talent and no pager.
- **Where to see it:** Jobs, Bookmarks, Applications (talent). My jobs, the applicants of a job and Talent (employer).

## R6. Add sort by fit and by posting time

- **You asked:** a sort by fit and by the time of posting.
- **Now:** a **Sort by** select on the lists. Jobs: **Best match** (the default) and **Newest posted**. Bookmarks also have **Recently saved** (the default). Applications: Recently updated, Best skill match, Newest application. The employer Talent list: **Best fit for this job** (the default) and **Recently updated** (the profile that changed last comes first; the 50 sample talent are updated over the last 60 days). Equal values are ordered by the id, so the order never jumps.
  My jobs and the applicants of a job have one sort only (newest first).
- **Where to see it:** the "Sort by" select above each list.

## R7. Settings in the user icon; a crown for Premium; highlight the Premium features

- **You asked:** Settings moves into the user icon. A Premium user has an own icon with a crown. Highlight the Premium features.
- **Now:** the left menu has **no "Settings" item**. The **user block** at the bottom (the initials, the name and the role) is one link that opens Settings. A **Premium user** has a **crown** on the avatar, a **gold ring** and a "Premium" chip.
  Settings starts with **"Your plan"**: a card that lists the Premium benefits. On Basic, each benefit has a lock and a gold "Premium" chip, and a button "Try Premium (demo)". On Premium, each benefit says **"Used"** (and how many times) or **"Not used yet"**.
  A **Basic** user sees a gold lock badge on every Premium feature (Invite, Compare, the full talent list, the advanced charts). A click on a lock opens "Premium feature". The crown and the locks change at once when the plan changes.
- **Where to see it:** the bottom of the left menu, and Settings. Switch the plan in Settings to see the change.

## R8. Compare was limited to 2

- **You asked:** compare more than 2.
- **Now:** you can compare **2 to 5** items, for both roles. The basket holds at most 5. The 6th item is refused in the screen ("You can compare up to 5 jobs.") and by the API (400).
- **Where to see it:** tick "Compare" on 2 to 5 job cards. The API: `GET /jobs/compare?ids=a,b,c,d,e`.

## R9. Compare as its own page; talent against talent, and job against job

- **You asked:** a Compare page of its own. Employers compare talent. Talent compares jobs.
- **Now:** a **"Compare" item in the left menu** and a **basket bar** at the bottom of the lists ("Compare (3/5)", "Open compare", "Clear"). The **Compare page** (`#/compare`) is a full page:
  - **Talent compares jobs (free):** one radar with a line for each job, a table of the numbers, "Skills side by side" (Meets, Below, Missing), a "Details" table (level, experience, work mode, salary, certifications, awards) and how close the jobs are to each other.
  - **Employers compare talent (Premium):** for one chosen job: one radar with a line for each profile, "Skills side by side", qualifications and recognition (names and years only), and "Where the profiles differ" (a position inside one area: "1st", "2nd", "Equal").
  - A Basic employer sees a locked page with a clearly marked sample picture.
  - There is **no total score and no ranking of people** on the page. Items can be added and removed on the page. The radar has 5 colours, 5 line styles and 5 marker shapes, so colour is not the only signal.
- **Where to see it:** the menu item "Compare".

## R10. "Your path to this job" was unclear

- **You asked:** say what fits and what is a gap. Show it as a spider chart.
- **Now:** the panel has a **radar with two layers** ("You have" filled, "Job requires" outline) over the skill groups, a table with a **status word** for each axis (Fit, Above, Gap), a **"Where you fit"** list and a **"Gaps to close"** list. Each gap says what you have, what the job needs, and the months to close it. Summary chips: "7 fit", "3 gaps", "about 5.5 months to close the gaps".
  **The 12-month line chart is removed.** The 8-number panel "How this job fits you" stays.
- **Where to see it:** any job detail, as the demo talent.

## R11. Analyse, plan, split the work, do not assume, ask when unclear

- **Now:** the work was planned in one document, `jinder_platform/docs/V2_PLAN.md`, with the decisions D1 to D9 that you gave and the defaults F1 to F12 that were applied. Each part of the work had one owner and wrote a note of its changes.
  The questions that were open are listed there as **O1** (the CV that the scan could not read) and **O2** (please confirm or change the defaults F1 to F12).
- **Where to see it:** `docs/V2_PLAN.md`, sections 1, 2 and 10.

## R12. Rewrite the formulas if needed

- **You asked:** rewrite the calculation if needed.
- **Now:** the six formula files in `jinder_backend_engine/intelligence_engine` were rewritten **in place**. They are smooth (no fixed steps) and use the level of the job and of the talent, exact years, the level of each skill, certifications, awards, work mode and the pay unit. The product **fit** is now defined in the engine. The score is still `0.55 × fit + 0.45 × FRS*`.
  The old legal block (AHPRA, CPA) and the 12-month projection are gone. A missing certification is a gap with months to prepare, not a block. The employer side reads the shared profile only and never the CV text. The math documents, the self-check (`run_verification.py`) and the tests agree with the code.
  A pay in a day rate or an hour rate is changed to a yearly pay in one place, in the engine (day × 220, hour × 1950). Education is a soft factor: it never gives 0.
- **Where to see it:** `docs/FORMULAS_IN_THE_PRODUCT.md` (where each formula runs and what the user sees) and `jinder_backend_engine/docs/02_FORMULAS_MATHEMATICAL_SPEC.md` (the math).

## Other changes you may notice

- **Database.** The schema is version 2. An old database is **kept as a backup** (`jinder.db.v1.bak`) at the first start, and a new one is made. Nothing is deleted. The sample data has a version (`SEED_VERSION` 2) and is made again when the old data is found. See `docs/DATABASE.md`.
- **Pay.** A job has a `salaryUnit` (year, day or hour). A day rate shows as "$900 per day".
- **Premium insights of the talent** are level-aware (the skills to learn next and the demand for your skills use the asked level).
- **Terms.** The word "Industry" is now **"Domain"**. The label "Licence readiness" is now **"Certification readiness"**.
- **Tests.** `python run_tests.py` runs **729 unit and API tests** in about 74 seconds. `python run_tests.py --browser` runs **7 browser stages** (about 1,055 checks, about 12 minutes). `--browser-quick` runs the two journeys only (about 2 minutes). See `Document/guides/01_GETTING_STARTED.md`.
- **Colours.** The chart colours are darker, so that a line on white has a contrast of 3:1 or more. The Premium gold has its own colour set (see `Docs/DESIGN.md`).

## Quality check (QA, 2026-10-07)

The QA step ran everything and checked R1 to R12 one by one. The details are in `docs/changes/QA.md`. The screenshots of the walk-through are in **`docs/changes/qa-shots/`** (51 files; they are not in the release zip).
Every QA run used a temporary data folder. Your own `var/jinder.db` and the port 8095 were not used.

| What | Result |
|---|---|
| Unit and API tests (`python run_tests.py`) | **729 tests, OK** (74 s) |
| Formula self-checks (`--formulas`) | 32 checks, all pass |
| Browser tests (`python run_tests.py --browser`) | **7 stages, all pass, 1,055 checks**: `e2e_demo` 74, `e2e_journey` 45, `check_fe_core` 179, `check_fe_talent` 279, `check_fe_employer` 205, `check_fe_compare` 192, `check_mock_ict` 81 |
| Walk-through R1 to R12 (`tests/browser/qa_acceptance.py`) | 142 steps, all pass (run twice) |
| Keyboard, names, focus and 390 px (`qa_a11y.py`) | 44 checks, all pass. One finding on colour contrast (D-2) |
| Response times (`qa_perf.py`) | 17 endpoints x 20 calls: the slowest call is 363 ms |
| Markup in text fields (`qa_xss.py`) | 18 checks on 15 screens, all pass |
| Privacy scan of every employer endpoint (`tests/test_privacy_v2.py`) | 15 tests, all pass. No score, no name, no e-mail, no evidence line, no country in any employer answer |
| Release zip | 2.9 MB, 375 entries, no `var`, no `.bak`; it starts and passes the tests |
| Defects | 12 fixed by QA (4 of them were test problems), the open ones are listed below |

### R1 to R12 one by one

| R | Result | Evidence (screens in `docs/changes/qa-shots/`) |
|---|---|---|
| R1 CV scan | **Pass** | 6 CVs (4 PDF, 2 DOCX) through the real onboarding: every field of "What we found in your CV" equals the expected value; a missing field shows "Not found. You can add it in the next steps."; the empty desired role has the hint. `r1-1-cv02-found.png` to `r1-6-cv18-found.png`, `r1-5-cv13-credentials.png`, `r1-6-cv18-goals.png`. The own CV of the user: see above |
| R2 level, experience, certifications, awards | **Pass** (note N-1) | All 53 open jobs have a level, years, work mode and education. Job cards, job detail, employer overview and anonymous talent cards show them (`r2-1-talent-job-cards.png` to `r2-5-employer-detail.png`). No person name next to an award |
| R3 different fit scores | **Pass** | The 20 best jobs of the demo talent have 20 different scores (77.7 down to 47.1). All 53 jobs: best 77.7, worst 29.2, 52 different values. No radar axis is constant. For the 50 talent: at least 19 different scores in the top 20 (mean 19.50), best minus worst at least 45.4. `r3-1-fit-panel-job1.png`, `r3-2-fit-panel-job5.png` |
| R4 full "About the role" | **Pass** | All 53 open jobs: no "…" cut, the headings of the JD, 2,311 to 3,153 characters. The box takes the keyboard focus, scrolls with the arrow keys, and ends at "How we hire". Talent and employer overview. `r4-1-talent-jd-end.png`, `r4-2-employer-overview-long.png` |
| R5 pager | **Pass** | 7 lists, 10, 20 and 50 rows, page 2 has other items, the last page has the right count, the size is remembered after a reload. A Basic employer sees 5 cards and no pager. `r5-1-jobs.png` to `r5-7-saved-talent.png` |
| R6 sort | **Pass** | The order on the screen equals the order of the API for every list and sort; ties by id; a bad sort is a 400. `r6-1-jobs-sort.png` to `r6-4-talent-sort.png` |
| R7 menu, user block, crown, benefits, locks | **Pass** | No Settings item; one user block link; the crown, the gold ring and the chip show at once after "Try Premium"; the benefits change from "Not used yet" to "Used 1 time" after the action; locks for Basic. `r7-1-employer-basic-settings.png` to `r7-4-talent-premium-used.png` |
| R8 2 to 5, the 6th refused | **Pass** | API: 2 to 5 give 1, 3, 6 and 10 pairs; 1 and 6 ids are a 400 with `fields.ids`. Screen: the 6th item is refused with the text. `r8-1-basket-5.png`, `r8-2-compare-5-jobs.png` |
| R9 Compare page | **Pass** | The basket keeps 5 jobs across 4 pages; 5 cards and 5 radar lines; remove and reload keep the same jobs; the picker; a Basic employer gets the locked page and the API gives 403; a Premium employer compares 5 profiles for a chosen job; no total, no score, no ranking. `r9-1-picker.png` to `r9-3-employer-compare-5.png` |
| R10 "Your path" | **Pass** | 5 jobs (one without a gap): a radar with 2 layers, the Fit list and the Gap list have the sizes of `summary`, the months equal the recomputed value, no 12-month chart. `r10-1-path-job1.png`, `r10-2-path-job4.png` |
| R11 process | Not a test | The plan lists O1 (done) and O2 (open) |
| R12 math docs and code | **Pass** | 4 worked examples of the math documents were recomputed with the code and agree (fit 77.6, SMF 67.4, JRS 42.2 and 10.2 months, JPI 68.1, FRS 71.2) |

### Open defects and notes (from QA)

| # | Severity | What | Status |
|---|---|---|---|
| **D-1** | major | The CV reader did not find the 2 certifications of the own CV of the user (a block of two columns inside a page of one column) | **Fixed** by the CV agent (fixture cv24; see R1 above) |
| **D-2** | minor to major (accessibility) | **Low contrast in the original design tokens.** 55 kinds of text on 10 screens are below 4.5:1: the token `--muted` (3.3:1 on white, 2.8 to 2.9:1 on tinted rows), accent text and links (4.1 to 4.3:1), white text on the accent colour (badges and the avatar, 3.7 to 3.8:1), and `.chip-yellow` (3.1:1). QA did not change the design tokens. A fix would darken `--muted` (for example `#6c757d`, 4.7:1), use a darker accent for text and links, and use dark text on yellow chips. It changes `Docs/DESIGN.md` and the look of the product | **Open. Decision for you:** change the design tokens, or keep them |
| **D-3** | minor | With 4 clients at the same time, a round of two calls (job detail and talent list) has a mean of 976 ms and a maximum of 1.9 s. There is no cache: each request runs the formulas for all jobs or all profiles | Open (a single client is under 0.4 s) |
| **D-4** | minor | One state of a skill has three words: "Related, via Python" on the job detail, "Missing" on the Compare page (a related skill does not count) and a gap "Missing" with a note on the path panel | Open (the notes explain it) |
| **D-5** | minor | `start.py` prints `http://localhost:PORT/`. A script on Windows that uses it waits 2 seconds for each request (the server listens on 127.0.0.1 only). A browser is not affected | Open (use `127.0.0.1` in scripts) |
| **D-6** | cosmetic | The employer talent list at 390 px: the card sits in a second box with a large left padding. No sideways scroll | Open |
| **N-1** | note on R2 | "Every one of the 50 jobs has all four": the four fields exist for every job (true), but 4 jobs list no certification and no award kind, and 34 jobs list no award kind. The page then says "This job does not ask for a certification (or an award)." | **The lead must say** if "all four fields are filled" is wanted |
| **N-2** | note on R5 | The pager is hidden when a list has one page and 10 items or fewer (the design of the shared pager). The plan says "a pager on all lists" | A short list without a pager is treated as correct |

Fixed by QA, among others: the Settings box "What employers see" now shows the level, years, skill levels, certifications and awards; the skill list says "Below level" and not "Related" for a skill below the asked level; the Compare page reads the `missing` list of an error; the error text for a wrong domain says "domain"; the wrong role card "Software Engineer" for a non-ICT title that ends with "Engineer" (a civil or a mechanical engineer title now gives no role card); a server log without a traceback for a closed connection; and the leftover words of other fields of work in the landing page, the placeholder text, `config.js`, `serve.ps1` and the two legacy documents.

## Known limits

- **The CV reader.** It is rule-based. Its numbers come from made-up CVs, so a real CV can fail where a test CV did not. It cannot read a scanned image, a password-protected PDF, a PDF font without a text map, or a skill bar that is only drawn. A table that another tool wrote column by column can give an empty or wrong value (empty is more common than wrong). A title in another language, or a title such as "Data Wizard", is not read. A wish for a role that is not in the role list gives an empty desired role. Years with a year but no month can be wrong by up to one year. A course or a short programme is not a certification.
  The built-in word lists (used only when the taxonomy file is missing) find fewer skills (18 of 30 test CVs against 30 of 30).
- **Demo values in the formulas.** The pay benchmarks for a Mid level (Software Engineering 130000, AI & Machine Learning 150000, Data 125000 AUD per year), the pay step of +22% for each level, the **220 working days** of a day rate, the 1950 hours of an hourly rate, the credit for a method or soft skill that a talent did not list, the city distances and the weights are **assumptions for the demo**. They are not statistics and not official data.
- **The taxonomy and the ANZSCO codes.** People made the taxonomy by hand. The ANZSCO-style codes are a **demo mapping**. They were **not checked against the official ANZSCO list**. Where no exact code exists, the nearest code is used (the field `approximate` is `true`).
- **The tuning.** The weights of the fit and of the feed were tuned on the 50 jobs and the 50 talents. With another data set, 2 to 4 talents can have 17 or 18 different scores in the top 20.
- **Formula slide decks.** `Presentation/formulas_presentation.html` (and `jinder_backend_engine/intelligence_engine/formulas_presentation.html`) presents the canonical Version 2 formulas (F-01 through F-06) with ASD-STE100 technical documentation, 100vh layout, and interactive parameter workbench.
- **Design debt (defect D-2).** The original design tokens have low contrast: 55 kinds of text on 10 screens are below 4.5:1 (see the table above). They were not changed, and the decision is open. The old rules `lc-*` of the removed 12-month chart were removed from `styles.css`.
- **Browsers and screen readers.** The screens were tested in **Chrome only** (also on a 390px wide window, but not on a real touch device). **Screen readers (NVDA, VoiceOver) were not tested**: names, roles and live messages were checked in the page code only. Edge, Firefox and Safari were not tested.
- **Lists.** The API has no filter for Active and Past applications and no filter for the status of the applicants of a job. The browser reads all pages and filters (at most 500 applications for a talent and 1,000 applicants for an employer filter). This is right for the demo data but slower for a very long list.
- **Compare.** One state of a skill has three words on three screens (defect D-4). The Compare page works with the real backend only.
- **The mock.** The browser-only mock (`?mock=1`) now has **ICT data only** (24 jobs, 10 sample talent, 5 sample CVs, 4 sample job descriptions, the same names as the taxonomy; the storage key is `jinder.mock.db.v2`). It has no formula engine and reads no real file (a file name chooses a sample). The Compare page, the plan card with benefits and "Your path to this job" need the real backend. The employer screens of the mock keep the old fields (no level, years, certifications or awards on a talent card, and no such fields in the job form).
- **Speed.** One client gets every answer in under 0.4 s. With 4 clients at the same time a round of two calls can take 1.9 s (defect D-3), because each request runs the formulas again. The server runs in one process.
- **What was not tested.** Screen readers; Edge, Firefox and Safari; real touch devices; a scanned CV, a password-protected PDF or a CV of more than 30 pages; more than 4 clients at the same time; a long run; a database with thousands of users; real e-mail sending (SMTP); and the server on port 8095 (it is yours).
- **Your old server and your old accounts.** A server that runs now on port 8095 keeps the old code in its memory and serves the new files: **stop it and start it again.** At the first start of this version, your old database `var/jinder.db` (schema version 1) is **renamed to `jinder.db.v1.bak`** (and `var/uploads` to `uploads.v1.bak`). Nothing is deleted. **The old accounts are in the backup, not in the new database** (decision F10): create a new account, or start with `--demo`.
- **Product limits (not new).** Sample jobs have no employer account, so nobody moves an application to a sample job. Payments are not built (Premium is a demo switch). Email needs SMTP settings. Password reset and email verification are not built.

## Open items for you

- **O1. Done.** The CV file that the scan could not read was found and tested (see R1). The defect that it showed (D-1) is fixed.
- **O2. Open.** The defaults F1 to F12 in `docs/V2_PLAN.md` section 2: please confirm or change them.
- **D-2. Open, decision for you:** change the low-contrast design tokens, or keep them.
- **N-1. Open, decision for the lead:** must every job list a certification and an award kind, or is "the four fields exist" enough?

## Source documents that are now out of date

The folder `spec` and the files in `jinder_frontend/Docs/` are the original specification. AI assistants must not change them (`AI_Rule.md` Rule 9). These statements no longer match the product:

| Statement in the spec | What is true now |
|---|---|
| "Comparing two profiles" (premium): Feature Specs (the scope and Definition of Done lists of Features 5 to 7); User Flow Spec 6.3 ("Compare two profiles side by side"); User Stories F7-S7b "Compare Two Profiles"; Technical Requirements TR-R-12 and TR-SYS-06 | An employer compares **2 to 5** talent profiles (Premium), and a talent compares **2 to 5 jobs** (free), on the Compare page |
| The navigation items per role include "settings" (Feature 1 AC8 and AC9; User Flow Spec 2.8; User Stories F1-S5 and F1-S6; Technical Requirements TR-JS-16) | There is no Settings item. The menu has a **Compare** item. Settings opens from the user block at the bottom of the menu |
| Seed data of "10 to 15 synthetic jobs across 2 to 3 industries" and "8 to 10 more anonymous talent profiles across 2 to 3 industries" (User Stories F3, F5 and seed stories) | **50 jobs and 50 talent profiles** in **3 domains**: Software Engineering, AI & Machine Learning, Data |
| "Seed a skill vocabulary and alias list for the demo industries" | The taxonomy `ict_taxonomy.json` (172 skills with aliases, 38 certifications, 12 award kinds, 20 specialisations, 53 roles) |
| Demo industry pairs for the translation (the PRD asks for "2–3 industries"; the examples Product Owner to Marketing, Business Analyst to Data Analyst; Feature 2 "mapping library of 20 pairs") | The translation library has 45 role pairs and about 40 skill pairs, all inside the three domains. The cross-border and cross-industry kinds stay (for example "BI Specialist" to "Data Engineer") |
| A job match shows a coverage and the gaps, "time to close" in months (Feature 3) | A job also has a **Fit score**, levels, and the new panel "Your path to this job". There is no projection and no 12-month chart |
| Skills have no level; a job has no level, years, certifications or awards (all features) | Skills have a level 1 to 5, jobs have a level, years, certifications and awards, and talent profiles have a level, exact years, certifications and awards |
| Lists show "the top N" or all items; the recommendation endpoint "with pagination" (Technical Requirements TR-JS-07) | Every list has a page size (10, 20, 50) and a sort. A Basic employer still sees only the top 5 |
| Licence or registration gaps for regulated jobs (the original examples) | There is no legal block. A missing certification is a gap with months to prepare |

## More details

- `docs/V2_PLAN.md`: the plan, the decisions and the defaults.
- `docs/DATABASE.md`, `docs/API_NOTES.md`, `docs/FORMULAS_IN_THE_PRODUCT.md`: the technical documents.
- `jinder_frontend/prompt.md`, `jinder_frontend/Docs/DESIGN.md`, `jinder_frontend/AI_Rule.md`: how to build the frontend, how it looks, and the rules.
- `docs/changes/*.md`: the notes of each part of the work.
