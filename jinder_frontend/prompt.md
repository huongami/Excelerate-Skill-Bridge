# Prompt — Build the Jinder frontend

## How to use this file

These three files are enough to build the same frontend on a different computer:

| File | Contains |
|---|---|
| `prompt.md` (this file) | How to build: architecture, files, routes, screens, **API contract**, mock backend, embedded seed data, security, tests |
| `Docs/DESIGN.md` | How it looks: tokens, logo, components, screen layouts, accessibility |
| `AI_Rule.md` | Rules for the AI: STE, English only, PII, security, frontend/backend boundary, keep the 3 files in sync |

1. Copy the three files to the new computer. Keep the folder names (`Docs/DESIGN.md`, `AI_Rule.md`, `prompt.md`).
2. The mock API needs no data file. It has its own 24 ICT jobs, its demo data and its samples, embedded in this file. (The folder `Sample_data/` has the old CSV files of the earlier prototype. The app does not read them. Do not copy them.)
3. Open your AI coding assistant (for example, Claude Code) in the project folder.
4. Tell the assistant: "Read `prompt.md`, `AI_Rule.md` and `Docs/DESIGN.md` fully, then follow everything below the line **PROMPT STARTS HERE** in `prompt.md`." (The file is large because of the embedded files, so ask the assistant to read it; do not paste it.)

> **Read-only documents:** do not edit `../Document/sdd/01_SYSTEM_OVERVIEW.md`, `../Document/sdd/02_PRODUCT_REQUIREMENTS_DOCUMENT.md`, `../Document/sdd/03_FEATURE_SPECIFICATIONS.md`, `../Document/sdd/04_USER_FLOW_SPECIFICATION.md`, `../Document/sdd/05_USER_STORIES_AND_ACCEPTANCE_CRITERIA.md` or `../Document/sdd/06_TECHNICAL_REQUIREMENTS.md` (see `AI_Rule.md` Rule 9). Read them only.

---

## PROMPT STARTS HERE

You are building the **frontend** of a web app. Another developer builds the backend. Read `AI_Rule.md` and `Docs/DESIGN.md` first, then follow every section below. `DESIGN.md` is the source for visual details; this file is the source for behaviour, files and the API. The **Appendix** at the end has files to create exactly (reference data, icons, the full mock backend, landing, sign in / create account, legal, Home and onboarding). An embedded file wins over the prose. Write the other files from the descriptions.

### Project settings

| Setting | Value |
|---|---|
| App name | Jinder (Job + Tinder) |
| Wordmark | "Jinder" ("J" in accent color) |
| Slogan | Where skills meet their match. |
| One-line value | Translates overseas and cross-industry experience into skills Australian employers recognise. |
| Role A (API `candidate`, UI "Talent") | International students and skilled migrants — "I'm looking for work" |
| Role B (API `recruiter`, UI "Employer") | Employers (recruiters and hiring teams) at Australian SMEs — "I'm hiring" |
| **UI terms (use the same words everywhere)** | **"Talent"** for role A and **"Employer"** for role B in all UI text, docs and sample text. Never "candidate", "recruiter" or "HR" in UI text. In a sentence, use "they" / "this person" / "this profile" when "the talent" reads badly. The API values `candidate` and `recruiter` (roles, paths such as `/recruiter/*`, `/candidates`) do not change: they are the backend contract. Use "Sign in" (not "Log in") and "Create account" (not "Sign up"). Use **"Domain"** (not "Industry"): the API keys `industry` and `targetIndustries` stay and hold the 3 domains. Other fixed words: **"Fit score"**, **"Certification readiness"**, **"Compare"** |
| Core principle | Every match is explained in plain language. No black-box scores. People make the decision. |
| Stats (with sources) | 680,582 international students in Australia (Dept. of Education, Jan–May 2026); 69% of employers struggle to find skilled talent (ManpowerGroup, 2024) |
| Output folder | `app/` |
| Port | 5173 |
| API mode | `http` (the real backend in `jinder_platform`, same address as the app, `API_BASE_URL` `/api`). `mock` (data in the browser) only with `?mock=1` in the address. |
| Scope (version 2) | **Three domains only:** Software Engineering, AI & Machine Learning, Data. All data is synthetic: 50 jobs, 50 sample talent profiles, 4 demo employer jobs. Six levels: **Intern, Junior, Mid, Senior, Lead, Principal**. Five skill levels: **Beginner, Working, Proficient, Advanced, Expert**. The real backend (`jinder_platform`) serves this data. The browser-only mock (`?mock=1`) has its own smaller ICT data (24 jobs, 10 sample talent, 5 CV samples, 4 job file samples; storage key `jinder.mock.db.v2`). It has no formula engine, and no Compare, benefits or "Your path" |

### Constraints

- **Frontend only.** Do not build a server-side backend in this folder. All data goes through the API layer (`js/api/index.js`). The real backend is the separate folder `jinder_platform` (it also serves this app). With `?mock=1` in the address, a mock API in the browser plays the backend.
- Plain **HTML, CSS and vanilla JavaScript ES modules** (`<script type="module">`). No framework, no build step, no npm packages.
- **One HTML file** (`index.html`). Every screen is a view rendered by a hash router.
- The target computer may not have Node or Python. Provide a static server in **PowerShell** (`serve.ps1`). See [Security](#security).
- **No inline code:** no `<script>` blocks, no `style="..."` attributes, no `onclick=` attributes in HTML or in HTML strings. Put JS in `.js` files and styles in the CSS files (`styles.css` and the four `styles-*.css` files; helper classes such as `.meter-86`). Set dynamic sizes with `element.style.width` in JS (CSSOM is allowed by the CSP). Exception: the logo `<symbol>` in `icons.svg` uses inline `style` (see [Logo](#logo)).
- **English only** in every file: UI text, placeholders, errors, sample data, `aria-label`s, comments. Names of people and places can stay (for example Nguyen, Hanoi), without diacritics.
- Write code comments in ASD-STE100 Simplified Technical English (short, active, one idea per sentence).

### Architecture

```
index.html ── js/main.js (registers routes, starts the router)
                 │
                 ├── core/router.js ── views/*.js (one function per screen: async (root, ctx) => void)
                 │        └── components/shell.js (left navigation for signed-in screens)
                 │
                 └── api/index.js  ◄── the ONLY way views read or write data
                          ├── api/http.js          (API_MODE "http": fetch to API_BASE_URL)
                          └── api/mock/adapter.js  (API_MODE "mock": same contract, in the browser)
```

- **Views** never call `fetch()` and never read `localStorage` (except UI preferences such as the navigation state). They call `api.*` functions and show what the API returns.
- **Rules belong to the backend.** Role checks, anonymity, status changes, premium access and match scores are decided by the API. The frontend also validates forms for a better experience, then shows the API errors.
- The mock adapter implements the same rules **only for demos**. It is not secure.

### File structure

```
app/
  index.html                 The only HTML file: skip link, #app root, #announcer live region, onboarding <dialog>, the 5 CSS links (in this order), module script
  styles.css                 Base styles and the design tokens as CSS custom properties
  styles-core.css            Version 2, shared parts: tokens that styles.css does not have (--orange-strong, gold, series colours), Premium markers, pager, sort select, JD box, compare tray, radar series, the user block and the Compare menu item, the plan card in Settings
  styles-talent.css          Version 2, talent parts: facts and compare box on the job card, job detail (facts, certifications, awards, JD panel), "Your path to this job", onboarding (found summary, hints, credential rows, skill level select), profile card
  styles-employer.css        Version 2, employer parts: lists, talent card and detail, skill table, job form (JD editor, skill rows, certification and award editors), job overview page
  styles-compare.css         Version 2, the Compare page. All class names start with cmp-
  icons.svg                  SVG sprite: logo symbol + UI icons (41 symbols, with i-crown and i-lock)
  logo.svg                   Standalone logo (favicon)
  serve.ps1                  Static server with security headers and an allow-listed data route
  js/
    main.js                  Routes table and router start
    config.js                API_MODE ("http", or "mock" when the address has ?mock=1), API_BASE_URL ("/api"), MOCK_LATENCY_MS, MOCK_DEMO_DATA, MOCK_DEMO_ACCOUNTS, MOCK_DEMO_PASSWORD
    core/
      router.js              Hash router, auth and role guards, focus management
      session.js             Session token storage + cached user
      dom.js                 h(), icon(), iconHtml(), esc(), toList(), formatDate(), announce(), logoHtml()
      forms.js               Inline errors, alerts, password toggle, safeNext()
      compare-store.js       The compare basket: compareStore.items / count / has / add / remove / clear / kindForRole. At most 5 items for each kind ("job" for a talent, "talent" for an employer). Stored in localStorage under jinder.compare.{userId}.{kind}. Event jinder:compare-change
    api/
      index.js               api.auth, me, aliases, cv, profile, jobs, reports, applications, recruiter.{jobs, applications, candidates, compare}, notifications, stats, entitlements, demo, bookmarks (one function per endpoint). A list method takes { page, pageSize, sort }. In mock mode it builds the page object in the browser
      errors.js              ApiError(status, code, message, fields, { suggestion, missing }). `missing` is the list of ids that a compare endpoint names (404: unknown ids. 400: ids above the limit)
      http.js                Real backend adapter
      mock/                  MOCK BACKEND (every file). The real backend replaces this folder. It is not changed for version 2, except that entitlementsOf in core.js adds crown and compareMax
        adapter.js           mockAdapter(): latency, load db, seed demo data, find the route, run it, save db
        core.js              route(), validation, requireUser/requireRole, publicUser, sharedProfileOf (allowlist), scrubContact, notify, entitlementsOf (with crown and compareMax), requirePremium, track, TOP_N = 5
        db.js                Data store in localStorage, resetDb(), demoHash(), newId()
        routes-account.js    /auth/*, /aliases/*, /me, /me/password, /cv, /cv/parse/:id, /profile/translate, /me/shared-profile; exports translateKeeping()
        routes-jobs.js       /jobs/recommended, /jobs, /jobs/:id, /jobs/:id/skip, /bookmarks, /reports
        routes-applications.js  /applications/* (candidate side), the state machine (TRANSITIONS, FINAL, STATUS_LABEL)
        routes-recruiter.js  /recruiter/jobs/*, /recruiter/applications/*, /recruiter/candidates/*, /recruiter/compare (the old two-profile form)
        routes-platform.js   /notifications, /entitlements, /stats, /demo/reset
        seed-demo.js         Demo accounts, 10 anonymous ICT sample talent, the 4 jobs of the demo employer, 7 applications (embedded below)
        aliases.js           Alias generator ("Colour Animal") and alias rules
        translation.js       Skill translation engine: 33 role pairs and 37 skill pairs of the taxonomy, evidence levels, skill levels, AQF levels (embedded below)
        cv-samples.js        5 ICT sample CV parse results and parseResultOf() (the mock cannot read a file; embedded below)
        jobs.js              Job catalogue (the 24 embedded jobs + posted jobs), skill table of the taxonomy, per-skill match, recommend(), searchJobs(), jobDetail(), suggestSkills(). No CSV, no fetch (embedded in the Appendix)
        seed-jobs.js         24 embedded ICT jobs, a copy of 24 of the 50 synthetic jobs (embedded below)
        jd-samples.js        4 ICT sample job-description read results for "Post from a PDF" (embedded in the Appendix)
    data/
      reference.js           Pick-lists made from the taxonomy `ict_taxonomy.json` (domains, specialisations, roles, fields of study, cities, certifications, award kinds, skills, ...). Embedded in the Appendix
      levels.js              Shared lists: LEVELS, SKILL_LEVELS, WORK_MODES, PAGE_SIZES ([10, 20, 50]), COMPARE_MAX (5), levelRank(), skillLevelLabel()
    components/
      shell.js               Left navigation pane (fixed, hideable, state saved), the user block (a link to Settings, with the crown for Premium), the Compare item (a lock for a Basic employer), unread badge, mobile bell, the compare tray
      combobox.js            Searchable dropdown (WAI-ARIA combobox)
      onboarding.js          Talent onboarding dialog (9 steps with a CV; see screen 6)
      job-card.js            Job card (facts, compare check box), coverage, bookmark button + toggle, skip ("Not for me") + undo, report dialog, dates, meters, and createPagedList() (a list with a sort and a pager that keeps the address)
      search-bar.js          Job search bar (keyword + location) → /jobs?q=&location=
      modal.js               Small dialog: openModal(), radioGroup(), textArea()
      status.js              Status ribbon, stepper, history, per-skill match list, coverageText(), slotText()
      profile-card.js        Shared (anonymous) profile card: sharedProfileHtml(), sharedFactsHtml(), skillChipsHtml(), experienceOf()
      charts.js              CSS bar charts barChartHtml(), Premium prompt upgradeHtml() (a gold chip with a lock)
      bridge.js              "How this job fits you" (fitHtml: one radar of 8 numbers) and "Your path to this job" (pathHtml: a radar with two layers, a Fit list and a Gap list): bridgeHtml(bridge). No line chart
      radar.js               Radar (spider) chart in SVG for 1 to 5 series on the same axes (0 to 100): radarHtml() (also a two-layer mode), and the same numbers as a table: radarTableHtml()
      pagination.js          The pager: pagerHtml({ page, pageSize, total, limitedTo }), bindPager(), loadPageSize(key), savePageSize(key, size)
      sort-select.js         The sort select: sortSelectHtml({ id, value, options }), bindSort()
      jd-view.js             The job description box: jdViewHtml(description, { label }), a scroll region that shows "## Heading" and "- bullet" lines
      premium.js             crownIconHtml(), premiumChipHtml(), lockedBadgeHtml(), bindPremiumLocks(), openPremiumDialog()
      compare-tray.js        The compare basket bar at the bottom of the main area: mountCompareTray()
    views/
      landing.js             "/"
      auth.js                "/login", "/signup"
      legal.js               "/terms", "/privacy"
      home.js                "/home" (candidate; a recruiter gets recruiterHomeView)
      jobs.js                "/jobs", "/jobs/:id", "/bookmarks" (candidate)
      applications.js        "/jobs/:id/apply", "/applications", "/applications/:id" (candidate); fetchAllApplications()
      recruiter.js           Recruiter Home, "/my-jobs", "/my-jobs/new", "/my-jobs/:id", "/my-jobs/:id/edit", "/my-jobs/:id/overview" (jobOverviewView), "/review/:id", "/candidates", "/candidates/:id"
      compare.js             "/compare" (both roles): compareView(root, ctx)
      notifications.js       "/notifications" (both roles)
      settings.js            "/settings" (both roles; it opens from the user block)
      system.js              Placeholder, no access, page not found
Sample_data/                 Old CSV files of the earlier prototype. Neither the app nor serve.ps1 reads them (they are not part of the build)
```

### Routes

The router reads `location.hash`. A hash that starts with `/` is a route (`#/jobs?x=1`). A hash without `/` (`#how`) is an in-page anchor on the landing page: render the landing page if needed, then scroll to the element.

| Route | View | Access | Shell nav item |
|---|---|---|---|
| `/` | Landing | Public. If signed in, the nav shows "Go to my workspace" | — |
| `/login` | Sign in | Guests only (signed in → `/home`) | — |
| `/signup` | Create account | Guests only | — |
| `/terms` | Terms of Use | Public | — |
| `/privacy` | Privacy Policy | Public | — |
| `/home` | Home | Signed in, both roles | Home |
| `/settings?section=plan` | Settings. `section=plan` scrolls to "Your plan". There is **no Settings item** in the menu: the user block at the bottom of the menu links here | Signed in, both roles | — (the user block is the current item) |
| `/compare?ids=a,b,c&jobId=` | **Compare** (real backend only). A talent compares 2 to 5 jobs. An employer compares 2 to 5 talent profiles for one own job (`jobId`), Premium. The page decides by the role. No role check in the route | Signed in, both roles | Compare |
| `/notifications` | Notifications | Signed in, both roles | Notifications |
| `/jobs?q=&location=&page=&pageSize=&sort=` | Jobs (search results). `sort` is `best` or `newest` | Candidate | Jobs |
| `/jobs/compare?ids=a,b,c` | **Redirects** (replace, no history entry) to `/compare?ids=a,b,c`. Register before `/jobs/:id` | Signed in | — |
| `/jobs/:id` | Job detail | Candidate | Jobs |
| `/jobs/:id/apply` | Apply (review and send) | Candidate | Jobs |
| `/bookmarks?page=&pageSize=&sort=` | Bookmarks. `sort` is `saved`, `best` or `newest` | Candidate | Bookmarks |
| `/applications?tab=past&page=&pageSize=&sort=` | Applications (Active / Past). `sort` is `updated`, `best` or `newest` | Candidate | Applications |
| `/applications/:id?new=1` | Application tracking | Candidate | Applications |
| `/candidates?jobId=&view=all\|saved&page=&pageSize=&sort=` | Talent (anonymous list). `sort` is `best` or `updated` | Employer (role `recruiter`) | Talent |
| `/candidates/compare?a=&b=&jobId=` | **Redirects** to `/compare?ids=a,b&jobId=`. Register before `/candidates/:id` | Signed in | — |
| `/candidates/:id?jobId=` | Talent profile detail | Employer | Talent |
| `/my-jobs?page=&pageSize=` | My jobs | Recruiter | My jobs |
| `/my-jobs/new` | Post a job. Register before `/my-jobs/:id` | Recruiter | My jobs |
| `/my-jobs/:id?status=&page=&pageSize=` | Applications for one job | Recruiter | My jobs |
| `/my-jobs/:id/overview` | **Job overview** (the full job description and facts). The app opens it after "Post job" and "Save changes". The route is loaded with a dynamic `import()` of `recruiter.js` | Recruiter | My jobs |
| `/my-jobs/:id/edit` | Edit a job | Recruiter | My jobs |
| `/review/:id` | Review one application | Recruiter | My jobs |
| anything else | Page not found | Public | — |

**Query values in the address.** After a change by the user (a page, a page size or a sort), a list screen writes `page`, `pageSize` and `sort` to the address (the employer lists leave out a value that is the default: `page` 1, `pageSize` 10, the first `sort`). It uses `history.pushState`, which does not start the router, so the list changes in place and the Back button still works. Other query values (`q`, `location`, `jobId`, `view`, `status`) stay. A bad `sort` in the address gives the default sort. A `pageSize` that the address does not have comes from the size that the user chose before (see the pager).

Router behaviour:
- `addRoute(pattern, view, meta)` with `meta = { title, auth, role, guestOnly, shell, nav, bodyClass }`. Patterns can have params (`/jobs/:id`).
- **Not signed in** on an `auth` route → `/login?next={current path}` (replace). After sign-in, go to `safeNext(next)`: only paths that start with one `/` and are not `/login` or `/signup`; else `/home`.
- Signed in but the user is not cached → call `api.me.get()` first.
- **Wrong role** → the "no access" view inside the shell (h1 "You don't have access to this page", button "Go to Home").
- **Session ended:** when any API call returns 401 (not on `/auth/*`), `api/index.js` clears the session and fires `window` event `jinder:unauthorized`. The router goes to `/login?expired=1&next={current path}`. The sign-in page shows "Your session has ended. Sign in again to continue."
- Each render: set `document.title` = "{title} — Jinder" (landing: "Jinder — Where skills meet their match."), set `document.body.className` = `meta.bodyClass`, scroll to top, give the page `h1` `tabindex="-1"` and focus it with `preventScroll` (not on the landing page). Ignore a render that a newer navigation replaced (render id).
- Close the onboarding dialog on `hashchange`.

### Visual style

Flat, minimal, professional and trustworthy. Warm sand page background (`--sand`) with white cards, navy ink, small doses of color through pastel tint chips. Almost no shadows. No gradients, no glassmorphism, no emoji. Full details: `Docs/DESIGN.md`.

### Design tokens (put all of them in `:root`)

**Colors**
```
primary/ink #151531   ink-deep #0d131b   ink-soft #2a2a63
body #343a40   muted #868e96   muted-soft #adb5bd   disabled #ced4da
canvas #ffffff   surface-soft #fafafa   surface-subtle #f8f9fa
page background (option B "warm sand"): sand #fdfbf8 (body, app main, auth form side, landing hero, market block, footer)   sand-strong #f8f4ed (landing audience band)   sand-line #f2ece3 (hairlines on sand: top nav, market, footer)
surface-muted #f6f8f9   surface-strong #edf0f2   surface-dark #151531
hairline #e9ecef   separator #e6ecf0
accent #6868f7   accent-tint #f0f0fe   orange #ffa340
tint pairs (background / ink):
  pink   #f9e2fb / #560059   — translation, talent
  blue   #c9f0ff / #003d5a   — employers, roles
  green  #daf9d4 / #005900   — matches, success, done
  yellow #fff5c7 / #a68716   — gaps, to improve
  rose   #ffd2e1 / #800000   — errors, risk
success #32ae47   error #f53d3d
Version 2 tokens (defined in styles-core.css, because styles.css does not have them):
  orange-strong #f27c0d
  gold #ffa340 (= orange)   gold-tint #fff5c7 (= tint-yellow)   gold-ink #7a651e (tint-yellow-ink mixed 70% with ink; 5.2:1 on gold-tint)
  chart series: series-1 #6868f7 (accent)   series-2 #c66714 (orange-strong 80% + ink)   series-3 #003d5a (tint-blue-ink)
                series-4 #298040 (success 70% + ink)   series-5 #560059 (tint-pink-ink)
```
Always pair a tint background with its own ink. Never use #000. The mixed colours use `color-mix()` inside `@supports`; a browser without it uses the plain tokens. A line on white needs 3:1 or more, so the series use the darker mixes (contrast on white: 4.3, 3.9, 11.6, 4.9 and 13.6 to 1).
**Known design debt (low contrast):** `.chip-yellow` (3.1:1 on its tint) and `--muted` text (3.3:1 on white) are below 4.5:1. They exist from version 1 and were not changed. Do not use them for new text (see `Docs/DESIGN.md`).

**Typography** — display: `"Plain Black", Inter, -apple-system, "Segoe UI", Roboto, sans-serif` (Plain Black is not public; Inter 500 with negative letter-spacing is the substitute). Body/UI: `Inter`. Load Inter 400/500/600 from Google Fonts with `@import` in `styles.css`.

| Token | Size / weight / line-height / tracking | Use |
|---|---|---|
| display-xl | 72 / 500 / 1.0 / -2.5px | Hero h1 |
| display-lg | 56 / 500 / 1.05 / -2px | Section heads |
| display-md | 40 / 500 / 1.1 / -1px | Dark band, home h1, stats |
| display-sm | 32 / 500 / 1.15 / -0.5px | Auth h1, card titles, metric numbers |
| title-lg | 24 / 600 / 1.3 / -0.3px | Card titles (Inter) |
| lead | 18 / 400 / 1.55 | Hero sub-line |
| body-md | 16 / 400 / 1.55 | Body |
| label/caption | 13 / 500 / 1.4 | Chips, labels |
| caption-uppercase | 12 / 600 / 1.4 / +1.5px | Eyebrow labels |
| nav-link | 14 / 500 | Nav (Inter) |
| button | 14 / 600 | Buttons (Inter) |

Display weight never goes above 500.

**Spacing** (4px base): 4, 8, 12, 16, 24, 32, 48, 64, section 96.
**Radius:** xs 6 (chips), sm 8 (inputs), md 10 (buttons, nav items), lg 12 (frames, small cards), xl 20 (cards), xxl 24 (dark band), pill 9999.
**Shadows:** xs `0 1px 2px rgba(0,0,0,.05)` on buttons; sm `0 1px 3px rgba(0,0,0,.1), 0 1px 2px rgba(0,0,0,.06)` on floating frames; popover `0 2px 10px rgba(13,19,27,.1), 0 0 2px rgba(13,19,27,.2)`; key `0 0 1px rgba(13,19,27,.25), 0 2px 1px rgba(13,19,27,.05)`.
**Container:** max-width 1200px, 24px side padding.

### Logo

Name meaning: **Jinder = Job + Tinder** — talent and jobs "match". Keep it professional: no hearts or dating symbols.

The mark: two swiped cards on a navy rounded square, with a check badge where they overlap. Left card (accent, turned -12°) = talent profile. Right card (orange, turned +12°) = job. White badge with a navy check = the match. Use this exact SVG as `logo.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" fill="none">
  <rect width="40" height="40" rx="10" fill="#151531"/>
  <rect x="8.5" y="9" width="13" height="18" rx="3" fill="#6868f7" transform="rotate(-12 15 18)"/>
  <rect x="18.5" y="9" width="13" height="18" rx="3" fill="#ffa340" transform="rotate(12 25 18)"/>
  <circle cx="20" cy="27" r="6" fill="#fff" stroke="#151531" stroke-width="1.5"/>
  <path d="M17.4 27.1l1.8 1.8 3.4-3.6" stroke="#151531" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
```

In the sprite version (`<symbol id="logo">` in `icons.svg`), set colors as **inline `style` attributes** with custom-property fallbacks: background rect `fill: var(--lm-bg, #151531)`; cards `fill: #6868f7` / `#ffa340`; badge `fill: var(--lm-line, #fff); stroke: var(--lm-bg, #151531)`; check `fill: none; stroke: var(--lm-bg, #151531)`. Do not use classes for these colors: page CSS does not apply inside an external sprite, so the mark renders wrong. Custom properties inherit from the `<use>` host: `.logo-mark { --lm-bg: var(--primary); --lm-line: #fff }` and `.on-dark .logo-mark { --lm-bg: #fff; --lm-line: var(--primary) }`.

Wordmark: `<span class="logo-word"><span>J</span>inder</span>` — display font, 18px / 600, -0.4px; "J" in accent (on dark: `#b7b7fb`), "inder" in ink (on dark: white); 10px gap after the 32px mark. `logoHtml(href, label)` in `dom.js` returns `<a href class="logo" aria-label>` + mark + wordmark.

### Icons

Lucide-style line icons as `<symbol>`s in `icons.svg`: 24px viewBox, `stroke: currentColor`, stroke-width 2, round caps/joins, no fill (the `.icon` class sets these). Use them as `<svg class="icon" aria-hidden="true"><use href="icons.svg#name"/></svg>`. Needed: logo, upload, target, user-check, arrow, check, alert, globe, briefcase, eye, eye-off, log-out, file, eye-view, users, clock, shield, x, map-pin, graduation, chevron-left, plus, chevron-down, **home, search, bookmark, inbox, settings, panel-left, menu, flag, bell, calendar, chart, send, star, columns, edit, eye-off-small**, and for Premium **i-crown** and **i-lock** (41 symbols).

New paths: home `M3 10.5 12 3l9 7.5` + `M5 9.5V21h14V9.5` + `M10 21v-6h4v6`; search `circle 11,11 r8` + `m21 21-4.3-4.3`; bookmark `m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z`; inbox `M22 12h-6l-2 3h-4l-2-3H2` + `M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z`; settings `M21 4h-7M10 4H3M21 12h-9M8 12H3M21 20h-5M12 20H3` + `M14 2v4M8 10v4M16 18v4`; panel-left `rect 3,3 18×18 rx2` + `M9 3v18`; menu `M4 6h16M4 12h16M4 18h16`; flag `M4 22V4a1 1 0 0 1 1-1h11l-1.5 4L16 11H5`; bell `M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9` + `M10.3 21a1.94 1.94 0 0 0 3.4 0`; calendar `rect 3,4 18×18 rx2` + `M16 2v4M8 2v4M3 10h18`; chart `M3 3v18h18` + `M7 16v-4M12 16V8M17 16v-7`; send `m22 2-7 20-4-9-9-4z` + `M22 2 11 13`; star `m12 2 3.1 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.8 21l1.2-6.8-5-4.9 6.9-1z`; columns `rect 3,3 18×18 rx2` + `M12 3v18`; edit `M12 20h9` + `M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z`; eye-off-small `M2 2l20 20` + `M6.7 6.7C3.9 8.4 2 12 2 12s3 7 10 7c1.9 0 3.6-.5 5-1.3M10 4.2c.7-.1 1.3-.2 2-.2 7 0 10 7 10 7a17 17 0 0 1-2.3 3.5`; i-crown `m3 7 5 4 4-7 4 7 5-4-2 11H5z` + `M5 21.5h14`; i-lock `rect 4,11 16×10 rx2` + `M8 11V7a4 4 0 0 1 8 0v4`.

### Components

- **Buttons:** 36px tall, 8×14 padding, radius 10, Inter 14/600, shadow xs. Primary = navy bg, white text, hover ink-soft. Secondary = white, hairline border. On-dark = white. Ghost/icon variant (36×36). Large = 44px. Pressed = translateY(1px). Disable buttons while a request runs.
- **Text link (all inline links: "Forgot password?", "Create one", "Sign in", Terms, Privacy, "Edit", "browse"):** accent color, weight 600, **no underline**, hover ink-soft. `.text-link` and `.legal-link` share this style.
- **Legal links** go to `#/terms` and `#/privacy`. On the auth screens they open in a new tab (`target="_blank" rel="noopener"`, sr-only "(opens in a new tab)").
- **Tint chip:** 4×8 padding, radius 6, 13/500, tint pair colors. **Icon tile:** 44px square, radius 12.
- **Text input:** 40px, radius 8, hairline border; focus = accent border + 3px accent-tint ring; error = error border.
- **App shell (`components/shell.js`)** — for every signed-in route (`meta.shell`):
  - Grid: left pane `--sidebar-w` 248px (72px when collapsed) + main. Main background sand (`body.page-soft` → `--sand`). Cards, panels, the left pane and the mobile top bar stay white. The page content (`.dash`) is max 1200px, centered.
  - Pane (white, hairline right border, sticky full height): top row = logo + "panel-left" icon button (`aria-controls="sidebar"`, `aria-expanded`, label "Hide navigation"/"Show navigation"); `<nav aria-label="Main">` list of nav items; bottom (hairline top) = the **user block** and a "Sign out" nav item. The user block is **one link** (`a#shellUser.sidebar-user-link`) to `#/settings`. Its accessible name is "Account settings, {name}". It has the initials avatar (wrapped in `.avatar-wrap`), the name, a role chip (pink "Talent" / blue "Employer") and, for candidates, a 12px muted line "Alias: {alias}" with the alias in pink ink 600 (`data-shell-alias`, `title="Employers see you by this alias"`). On the Settings page it is the current page (`aria-current="page"`).
  - **Premium user (the "Highlight Premium" rule, a/b/c):** (a) the link has the class `is-premium`: a crown (`i-crown`, `.avatar-crown`) at the top right of the avatar, a gold ring round the avatar (2px gap, 2px `--gold`) and a small gold chip "Premium" after the role chip; a hidden text "Premium plan" (`#shellPlanNote`) describes the link; the crown also shows when the pane is collapsed. (b) The account area (Settings) lists the benefits, used or not used yet. (c) A Basic user sees a lock and a gold badge on Premium features.
  - The plan comes from `api.entitlements.get()` (`crown` or `plan === "premium"`) and is cached in memory. The window event `jinder:plan-change` (detail = the entitlements) updates the crown and the lock at once. `api.entitlements.set` fires it. `shell.js` exports `NAV`, `initials(name)` and `updateShellUser(user)` (call it after a name change in Settings).
  - Nav items: icon 20px + label, 10×12 padding, radius 10, 14/500 body color; hover surface-muted; active (`aria-current="page"`) accent-tint background, ink 600 text, accent icon. Talent: Home, Jobs, Bookmarks, Applications, **Compare**, Notifications (6 items). Employer: Home, Talent (`#/candidates`), My jobs, **Compare**, Notifications (5 items). **There is no "Settings" item.** For a Basic employer, the Compare item shows a small gold lock chip "Premium" (a lock at the top right of the icon when the pane is collapsed; `title` "Compare (Premium feature)"). The item still opens `#/compare`, which explains the feature. The compare basket bar (`components/compare-tray.js`) is mounted by the shell on every signed-in page except `#/compare`.
  - **Unread badge:** the Notifications item has a `<span class="nav-badge" data-unread hidden>` at the right (error red pill, white 11/700 text, min 20px; "99+" above 99). Collapsed pane: a 16px badge at the top right of the icon. The mobile top bar has a ghost icon link "bell" (`#/notifications`, `aria-label` "Notifications" or "Notifications, {n} unread") with the same badge, at the right end. After render, the shell calls `api.notifications.list()` and sets the count. It also listens to the `window` event `jinder:notifications` (`detail.unread`), which the Notifications screen fires; remove the listener when the shell is gone.
  - **Collapse** saves `localStorage["jinder.ui.nav"] = "collapsed" | "expanded"` and keeps it across routes and reloads. Collapsed: icons only (labels and wordmark hidden), items centred, each item has `title`.
  - **≤768px:** the pane is fixed off-canvas (264px, `translateX(-100%)`, popover shadow). A sticky top bar (56px, white, hairline bottom) shows a "menu" icon button (`aria-label="Open navigation"`, `aria-expanded`) and the logo. Open = class `nav-open` on the shell + a scrim (`rgba(13,19,27,.45)`); click the scrim, a nav link, or press Esc to close. The collapse button is hidden on mobile.
  - Sign out: `await api.auth.logout()` then go to `/login` (a "Sign out" nav item under the user block, and a button in Settings).
- **Skip link:** first element in `<body>`: "Skip to content" (`href="#app"`), hidden above the page until focused. **The hash is the route**, so `main.js` handles its click: `preventDefault()`, then focus `#main` (or `#app main`, or `#app`) with `tabindex="-1"`. The route does not change.
- **Announcer:** `<div id="announcer" class="sr-only" role="status" aria-live="polite">` in `index.html`. `announce(msg)` (dom.js) clears it and sets the text 50 ms later, so repeated messages are read.
- **Search bar (`components/search-bar.js`)** — `searchBarHtml({ q, location })` + `bindSearchBar(root, navigate)`. A white card (hairline, radius 20, 16px padding) with a 3-column grid `1fr 200px auto`: a search input (44px, search icon inside at the left, placeholder "Search jobs by title, skill or company", `maxlength=100`, sr-only label "Search jobs"), a location `<select>` ("All locations" + `LOCATIONS`, sr-only label "Location"), and a large primary "Search" button. `<form role="search" aria-label="Search jobs">`. Submit → `/jobs?q=…&location=…` (omit empty params). ≤768px: one column.
- **Job card (`components/job-card.js`, `jobCardHtml(job, { compact, compare })`)** — the same card on Home, Jobs, Bookmarks and Similar jobs. Two columns (content : 140px):
  - Title = link to `#/jobs/{id}` (ink, hover accent, no underline).
  - Meta: company · map-pin + area · type · salary (13px muted).
  - **Summary** (not in compact): `job.summary`, 14px body.
  - **Facts row (`ul.job-facts`, in all cards, also the compact ones):** chips for the **Level** (pink), the **Experience** (neutral: "5–9 years", "5+ years", "Up to 6 years", "2 years" from `minYears` and `maxYears`; `experienceText(min, max)`) and the **Work mode** (blue). A fact that is `null` (old data, the mock) has no chip. Without any fact there is no row. Each chip has a hidden word for screen readers ("Level: Senior") and a `title`.
  - Tags: if the job has `similarity` (a similar job on Job detail), a neutral chip "{tier} · {index}% alike" (the Formula 3 label); if the candidate applied, a green chip link "✓ Applied · Track" (`#/applications/{applicationId}`); blue chip "ANZSCO {code} · {occupation}"; dates ("Posted d MMM yyyy", "Closes d MMM yyyy"; a closed job shows a rose "Closed" chip + "Closed {date}").
  - **Skill gaps row:** uppercase label "SKILL GAPS" (12/600, +1.5px, muted) + up to 4 yellow chips (12px) and "+N more"; no gaps → green chip "No skill gaps found". Gaps = job skills with status `gap` (a `partial` skill is not a gap).
  - Reasons (green checks) and notes (muted alert icon) — not in compact. With levels, a reason reads "You meet 6 of the 11 skills (1 below the asked level, 3 related)".
  - Right column (right aligned): **bookmark icon button** at the top, then `coverageHtml(match)`: the coverage (display 32px, "{c}%" or "—"), hint "skills covered", accent meter (`data-w`, painted by `paintMeters(root)`), hint `coverageText(match)` ("{m} of {n} skills" + " + {p} related"). When `match.score` exists, a line under the coverage text: "Fit score {score}" (12px muted, the number in 14px ink, one decimal).
  - **Card foot** (`.card-foot`, across both columns, hairline top, 12px top padding, flex space-between): at the left the **card actions** (not in compact): small ghost buttons "Not for me" (eye-off-small icon, `data-skip`) and "Report" (flag icon, `data-report`), muted text, and the **"Compare" check box** (`label.check.compare-pick` with `input[type=checkbox][data-compare-job][data-title]`; accessible name "Compare {job title}"; on **every** card, also the compact ones; only with the real backend; `jobCardHtml(job, { compact, compare: false })` leaves it out). `bindCompare(root)` (one handler): a tick calls `compareStore.add("job", { id, title })`. The 6th job is refused: the box is cleared, the text "You can compare up to 5 jobs." shows next to it (`span.compare-note`) and the polite announcement says it. The boxes follow the basket (the bar, another tab). Do not mount a second basket bar; **at the bottom right a small secondary button "Job detail →"** (`a.btn.btn-secondary.btn-sm.job-link`, arrow icon, `#/jobs/{id}`, sr-only " for {title}"), also on compact cards. **No links to other sites.**
- **Skip and report (`bindJobActions(root)`)** — event delegation. "Not for me" → `api.jobs.skip(id)` → the card is replaced by a dashed placeholder `<li class="job-card job-card-hidden" role="status">` "{title} is hidden. We show fewer jobs like this." + link-button "Undo" (focused). Undo → `api.jobs.unskip(id)` → the card comes back and its skip button gets focus. "Report" → `openReport("job", id, title)`: a small dialog "Report this job", intro "{title}. Reports help us improve the recommendations. The employer does not see who reported.", radio group "Why is this a wrong recommendation?" (It does not match my skills or goals = `not_relevant`; Wrong location or work type = `wrong_location_or_type`; The job looks wrong or misleading = `misleading`; Other = `other`), text area "More details (optional)" (max 500), submit "Send report" → `api.reports.create({ targetType, targetId, reason, details })` → announce "Thank you. Your report is sent." No reason → "Choose a reason." in the dialog. For a talent profile (employer side) the title is "Report this profile", reasons not_relevant ("Not relevant to my jobs"), misleading ("The profile looks wrong or misleading"), other; intro ends "They do not see who reported."
- **Small dialog (`components/modal.js`)** — `openModal({ title, intro, content: Node[], submitText, danger, onSubmit })` makes a native `<dialog class="modal modal-small">` (width min(520px, 100% − 32px)), appends it to `<body>`, `showModal()`, focuses the h2 (24px, `tabindex="-1"`), and removes it on close. Close X (ghost icon, top right, `aria-label="Close"`), body (h2, muted intro, `role="alert"` error box, content), foot (ghost "Cancel" + primary or **danger** (error red) submit). `onSubmit(form)` returns true to close; a thrown `Error` shows its message in the error box. `radioGroup(name, legend, [[value, label]])` and `textArea(name, label, { hint, max, rows, value })` build fields.
- **Status components (`components/status.js`)** — text always carries the meaning, colour only helps:
  - `ribbonHtml(status, label)`: pill 6×12, 13/600, sr-only "Status: ". Tones: applied/declined neutral (surface-strong), contacted/review blue, interview yellow, accepted/offer/confirmed green, rejected rose.
  - `stepperHtml(app)`: `<ol class="stepper" aria-label="Application progress">` with 6 steps Applied (or "Contacted" when `origin` is contacted) · In review · Interview · Accepted · Offer · Confirmed. Dot 28px: done = green with a check, current = accent + 4px accent-tint ring + `aria-current="step"`, to-do = grey number. A 2px line joins the dots (green after a done step). An ended application (rejected/declined) adds a rose step "Not selected" / "Declined" with an x, after the last step that was reached.
  - `historyHtml(history, { you })`: newest first; rows `170px | 1fr` with date-time (en-AU, medium + short) and "**{who}** — {note or status text}"; who = "You" for your own side, else "Employer" / "Talent" / "Jinder".
  - `skillMatchHtml(items, { you })`: one row per job skill, tint by status: match green "You have it" (recruiter: "Has it", check icon), partial blue "Related" (target icon) + "via {skill}" (a partial skill with `fitStatus` "below" says "Below level" + "You: {level} · Needs: {level}", recruiter: "Has: …"), gap yellow "Gap" (alert icon).
  - `coverageText(match)`, `slotText(iso)` ("Wed 9 Oct, 11:00 am").
- **Shared profile card (`components/profile-card.js`)** — `sharedProfileHtml(p)`: avatar (pink, initials of the alias) + alias, then a `<dl>` of rows (130px label : chips): Roles ("{title} (ANZSCO {code})"), **Level**, **Experience** (the exact years first, "7.5 years", else the range), Skills (green chips with the level as a word: "Python · Advanced"), **Certifications** and **Awards** (names and years only, "Name (2023)": no issuer, no kind), Qualifications, **Domains**, Target roles, Locations, Work types; empty → muted "Not given". A row for a version 2 key (Level, Certifications, Awards) shows only when the key is in the object (the snapshot of an old application has none). It shows only allowlist fields. Other exports: `sharedFactsHtml(p)` (short lines "Level: Senior · 7.5 years", "Certifications: …", "Awards: …", the first 3 names and "+N more"; used on Home), `skillChipsHtml(p, max)` and `experienceOf(p)`.
- **Charts (`components/charts.js`)** — `barChartHtml(rows, { title, empty, unit })`: `<figure class="chart">` + `<figcaption>`, rows `label | 10px bar track | value` (the number is always shown as text; bar width = value / max, set by `paintMeters`). `upgradeHtml(text)`: yellow dashed box with a gold chip "Premium" with a lock icon, the text and a secondary "See plans" (`#/settings?section=plan`).
- **Pager (`components/pagination.js`)** — used by every list of jobs, bookmarks, applications and talent.
  - `pagerHtml({ page, pageSize, total, limitedTo })` returns `div.pager[data-pager]` with: `.pager-size` (label "Rows per page" + `select.pager-select[data-pager-size]` with 10, 20 and 50), `p.pager-range` ("Showing 11–20 of 134", `aria-live="polite"`), and `nav.pager-nav[aria-label="Pagination"]` > `ul.pager-list` > `button.pager-btn` (`.pager-step` for Previous and Next, `.pager-num` for a page; the current page has `.is-current` and `aria-current="page"`; `data-pager-page="{n}"`) and `li.pager-gap` ("…"). The row has at most 7 items.
  - It returns `""` when `total` is 0, when `limitedTo` is set (a Basic employer sees 5 talent), or when there is one page and `total` is 10 or less. A list with one page but more than 10 items still shows the size select.
  - `bindPager(root, { onPage(page), onPageSize(size), pageSizeKey })`: one click handler and one change handler on `root`. The pager can be drawn again at any time. `onPageSize` must load page 1. With `pageSizeKey`, the size is saved before `onPageSize` runs. `loadPageSize(key)` gives the saved size (10, 20 or 50; default 10; a broken value gives 10). `savePageSize(key, size)` ignores a size that is not in `PAGE_SIZES`. The storage key is `jinder.pagesize.{key}.{userId}` (the key is the list name, for example `jobs`, `bookmarks`, `applications`, `my-jobs`, `applicants`, `talent`, `talent-saved`).
  - After a page change: the polite announcement "Page 2 of 7" and the focus goes to the list heading (`h2`, `tabindex="-1"`). After a size change: "20 rows per page. Page 1 of 3" and the select keeps the focus. While a page loads, the list has `aria-busy="true"` (half transparent). An old answer that comes late is dropped. On 768px or less, the buttons and the select are 44px high.
- **Sort select (`components/sort-select.js`)** — `sortSelectHtml({ id, value, options: [{ value, label }], label = "Sort by" })` returns `div.sort-select` with a visible label and a native `select.sort-select-input#{id}`. An unknown value selects the first option (the default). `bindSort(root, id, onChange(value))` adds one change handler. A change of the sort or of the page size goes to page 1.
- **Job description box (`components/jd-view.js`)** — `jdViewHtml(description, { label = "Job description" })` returns `section.jd-view[tabindex="0"][role="region"][aria-label]`. The text uses a small markup: `## Heading` = `h3`; `- item` (also `* ` and a bullet sign) = `li` in a `ul`; a blank line ends a paragraph; other lines = `p` (a line break inside a paragraph stays). A text with no heading shows as paragraphs; no text gives "There is no description for this job." All text is escaped. CSS: maximum height 32rem, `overflow-y: auto`, a visible focus ring, and a soft scroll shadow at the top and the bottom (CSS only). `parseJd(description)` is also exported.
- **Premium markers (`components/premium.js`)** — `crownIconHtml({ decorative, label = "Premium" })` (`span.crown[role="img"]`, or `aria-hidden` when `decorative`); `premiumChipHtml(text = "Premium")` (`span.chip.chip-gold.premium-chip`); `lockedBadgeHtml(featureLabel, { static })` (a gold chip with a lock and the text "Premium"; by default a `button.locked-badge[data-premium-lock="{label}"]`; with `{ static: true }` a plain `span`, for use inside a button or a link); `bindPremiumLocks(root)` (a click on any `[data-premium-lock]` opens the dialog); `openPremiumDialog(featureLabel)` (title "Premium feature", text "{label} is part of Premium. In this demo you can switch your plan in Settings.", button "Go to Settings" → `#/settings?section=plan`). Rule: a Basic user sees the lock badge on a Premium feature. A Premium user sees the feature as normal. The crown is for the account area only.
- **Compare basket (`core/compare-store.js`, `components/compare-tray.js`)** — `compareStore.items(kind)` (`[{ id, title, … }]`, oldest first), `.count`, `.has(kind, id)`, `.add(kind, item)` (returns `false` at 5 items, for a wrong kind or for an item without id; the same id twice gives `true` and no copy), `.remove`, `.clear`, `.kindForRole(role)` (`candidate` → `"job"`, `recruiter` → `"talent"`). An item is `{ id, title }` for a job and `{ id, alias }` for talent. Storage: `localStorage["jinder.compare.{userId}.{kind}"]`. A broken value gives an empty list; more than 5 stored items are cut to 5. The event `jinder:compare-change` on `window` has `detail = { kind, items, action: "add"|"remove"|"clear"|"sync", id }` (`sync` = another browser tab).
  The bar (`aside.compare-tray[data-compare-tray]`) shows only when the basket has 1 or more items: `strong.compare-tray-title` "Compare (n/5)", a chip with a remove button for each item (`aria-label="Remove {title} from compare"`), a primary "Open compare" (a link to `#/compare` when n is 2 or more; with 1 item a button with `aria-disabled="true"` and the text "Add 1 more job to compare." or "Add 1 more talent to compare.") and a ghost "Clear". It is fixed at the bottom of the main area. Its left edge follows the pane (248px, 72px collapsed, 0 on small screens). The shell gets the class `has-compare-tray` and the main area gets bottom padding of the bar height (`--tray-h`).
- **Radar chart (`components/radar.js`)** — `radarHtml({ axes: [{ label }], series: [{ name, values }], layers? }, { caption?, layers? })` returns `""` for fewer than 3 axes or no series. **Up to 5 series** on 3 to 10 axes. Each series has its own colour class (`series-1` … `series-5`, see the version 2 tokens), line style and marker: 1 solid, circle; 2 dashed, square; 3 dotted, diamond; 4 dash-dot, triangle; 5 long-dash, cross. `layers: true` (**two-layer mode**): series 1 ("You have") is a filled shape, the other series are outlines only, and series 2 ("Job requires") has a thicker line; the figure gets `radar-layers`. The SVG is 560 × 470. An axis label wraps to at most 3 lines of 14 characters (`wrapLabel`) and has the full text in a `title`. `role="img"` and an `aria-label` with all values. `radarTableHtml({ axes, series }, { note })` gives the same numbers as a table (one decimal; "—" for no value). The chart never adds the axes up.
- **Shared lists (`data/levels.js`)** — `LEVELS`, `SKILL_LEVELS` (`[{ value: 1, label: "Beginner" }, … { value: 5, label: "Expert" }]`), `WORK_MODES`, `PAGE_SIZES = [10, 20, 50]`, `COMPARE_MAX = 5`, `levelRank(name)` (0 to 5, or -1) and `skillLevelLabel(value)`.
- **Bookmark button** — `bookmarkButton(job, { withText })`: icon button (or secondary button with "Save"/"Saved" text on the detail screen) with `data-bookmark="{id}"`, `data-title`, `aria-pressed`, `aria-label` "Save {title} to bookmarks" / "Remove {title} from bookmarks", `title` "Save"/"Saved". Pressed: accent color and the bookmark icon filled with accent. `bindBookmarks(root, onChange)` uses event delegation on `root`: change all buttons for that job at once (optimistic), call `api.bookmarks.add/remove`, `announce()` "{title} saved to bookmarks." / "{title} removed from bookmarks.", go back and announce the error message if the call fails. Disable the button during the call.
- **Back link** — `<button class="back-link">` with chevron-left + "Back" (accent 14/600). `history.back()` if there is history, else `/jobs`. On screens with a fixed parent, it is an `<a class="back-link" href>` with the parent name ("Applications", "My jobs", the job title, "Candidates"); no underline.
- **Searchable dropdown (`components/combobox.js`, `createCombobox`)** — use it for every free-text answer in onboarding. WAI-ARIA 1.2 combobox: `<input role="combobox" aria-autocomplete="list" aria-expanded aria-controls aria-activedescendant>` + `<ul role="listbox">` of `<li role="option" aria-selected>` + a chevron toggle button (`tabindex="-1"`) + an sr-only `role="status"` result count.
  - Typing filters (case-insensitive "contains"; options that start with the query first; max 50). The matched part is bold (`<mark>`, built with text nodes).
  - ArrowDown/ArrowUp move the active option, Enter picks it, Tab closes. **Esc closes only the list** (`preventDefault` + `stopPropagation`), not the dialog.
  - `allowCustom` (default true): when the text is not an exact option, the last row is `+ Use "{text}"` in accent color; Enter with no active option keeps the typed text. With `allowCustom: false`, show "No matches. Choose an option from the list." and validate that the value is in the list.
  - On blur, a case-insensitive exact match is replaced with the option's spelling. Options: `mousedown` → `preventDefault` (keep focus), `click` → pick.
  - Style: input with 40px right padding; list absolute under the input, white, hairline, radius 8, popover shadow, max-height 240px, 4px padding; option 8×10 padding, radius 6, 14px; active/hover = accent-tint.
- **Focus:** `:focus-visible` 2px accent outline, 2px offset. Page headings focused by the router have no outline (`h1[tabindex="-1"]:focus { outline: none }`).
- **Motion:** 150ms `cubic-bezier(0.2,0,0,1)` on colors/borders only (the shell column width animates 200ms). Turn off with `prefers-reduced-motion`.

### Screens

**1. Landing — `/` (`views/landing.js`)**
1. Sticky top nav (sand at 92% + blur, sand-line bottom): logo (`#/`) · links (How it works `#how`, For talent `#talent`, For employers `#employers`) · "Sign in" (`#/login`) + primary "Get started" (`#/signup`). If signed in: one primary button "Go to my workspace" (`#/home`).
2. `<main>`: centered hero: eyebrow pill "Skills-based hiring for **Australia**" (`.hero-eyebrow`: white pill, hairline, shadow xs; "Australia" is an `.au-chip` inside it — orange-tint pill, map-pin icon in orange, ink 700 text); h1 "Every skill, *recognised* — wherever it was built" (the key word in accent); lead; buttons "Create free account →" (`#/signup`, primary, large) and "See how it works" (`#how`, secondary, large); note "Free for talent and employers during the pilot."
3. Product preview in a browser frame (3 gray dots, fake URL "jinder.app / talent / translation"). Panels: a translation table ("Product Owner, Hanoi → Agile delivery lead", "BI Specialist, HCMC → Data Analyst", "Informatica developer → ETL and ELT pipelines", "B.Econ (VNU) → AQF Level 7 equivalent") and a match card ("Data Analyst · Sydney", "Strong match" green chip, "86%", accent meter `.meter-86`, 2 green check reasons ("Built Power BI dashboards for 6 teams", "SQL and Python for weekly reporting"), 1 yellow gap ("Gap: Apache Airflow, about 1 month to learn")). `role="img"` + descriptive `aria-label`.
4. **Australian market block** (`section.market`, centred, hairline bottom): eyebrow with a map-pin icon "The Australian job market", h2 (display 32px, 26px ≤768px) "Skilled talent is here. Employers can't find it.", then **2 highlight cards** side by side (max 420px each, 1 column ≤768px; radius 20, 24px padding; icon tile on white at the left): pink card (graduation icon) "680,582" (display 48px) / "international students in Australia" / "Source: Dept. of Education, Jan–May 2026"; blue card (briefcase icon) "69%" / "of employers struggle to find skilled talent" / "Source: ManpowerGroup, 2024". Do not add a third stat (no "black-box" stat).
5. "How it works" (`id="how"`, white band — the only white section, so the step cards read as one group): 3 step cards (01 Translate experience / 02 Check the gaps / 03 Decide with context), icon tiles pink / yellow / blue.
6. Two audience cards on a sand-strong band: "For international talent" (`id="talent"`, button "Create my profile" → `#/signup?role=candidate`) and "For Australian employers" (`id="employers"`, button "Start hiring" → `#/signup?role=recruiter`).
7. Dark navy CTA band: "No qualified person filtered out" + white button (`#/signup`).
8. Footer on sand (sand-line top border): logo + slogan + mission line; columns Product (anchors), Account (`#/login`, `#/signup`), Company (About `#/`, Privacy `#/privacy`, Terms `#/terms`); copyright row.

**2. Sign in — `/login` (`views/auth.js`)**
Split layout, 5 : 7 columns, full height.
- Left (navy, `on-dark`): logo, slogan (15px, white 70%), headline "Welcome back to skills-based hiring", check list of 3 benefits (orange checks), a quote at the bottom above a thin white line (placeholder content).
- Right: top row "New to Jinder?" + "Create account" (`#/signup`); form (max 400px): h1 "Sign in", sub-line, alert (`role="alert"`), email ("Work or personal email"), password with show/hide button, "Forgot password?" (shows "Password reset is not available yet."), "Keep me signed in on this device" (`remember`), primary "Sign in", "Don't have an account? Create one"; legal line at the bottom.
- **Demo box (only when `API_MODE` is "mock", `MOCK_DEMO_DATA` is true and `MOCK_DEMO_ACCOUNTS` is not empty):** under "Create one", a dashed accent box (accent-tint, radius 12): title "Try the demo" (14/600), hint "Demo accounts with sample jobs and applications. The data stays in this browser.", one small secondary button per account (label from config). A click fills the email and `MOCK_DEMO_PASSWORD`, then submits the form.
- `?registered=1` → green alert "Thanks! If this email is new to Jinder, your account is ready. Sign in to continue." `?expired=1` → rose alert "Your session has ended. Sign in again to continue."
- Submit: validate (email format, password not empty) → `api.auth.login({ email, password, remember })` → `navigate(safeNext(query.next), { replace: true })`. API error → show its `message` in the alert.
- ≤1024px: hide the left column, show the logo in the top row.

**3. Create account — `/signup` (`views/auth.js`)**
Same split layout (headline "Make the skills you already have visible"). Role picker (`radiogroup`): "I'm looking for work / Student or skilled migrant" (`data-role="candidate"`, globe) and "I'm hiring / Employer or hiring team" (`data-role="recruiter"`, briefcase). `?role=recruiter` (or the old `?role=employer`) preselects the recruiter card. Fields: full name, company (recruiters only), email, password (hint "At least 8 characters."), confirm password, terms checkbox. Validate in the form, then `api.auth.signup({ role, name, company, email, password })` → `/login?registered=1`. On `VALIDATION_ERROR`, show `error.fields` under the fields.
- **Alias field (candidates only; hidden for recruiters)** between full name and company/email: label "Alias (optional)", a "Suggest one" link-button at the right of the label (fills the field from `api.aliases.suggest()`), input (`maxlength=30`, placeholder "For example, Teal Heron"), hint "Employers see this name, not your real name. Leave it empty and we choose one for you." Form check: 3–30 characters when filled. Send `alias` only when filled. On `ALIAS_TAKEN` (409): show `fields.alias` under the field plus a link-button **"Use “{suggestion}”"** that fills the field and clears the error. On `VALIDATION_ERROR` for `alias`, show the API message (real name, origin word, format).

**4. Terms — `/terms`, Privacy — `/privacy` (`views/legal.js`)**
Top nav with logo and a link to the other page; `<main class="legal-page">` with eyebrow "Legal", h1, "Last updated: 5 October 2026", a yellow placeholder note, numbered sections; small footer. Use the exact text in the embedded `js/views/legal.js` (Appendix).

**5. Home — `/home` (`views/home.js`, inside the shell)**
A recruiter gets the **Recruiter Home** (screen 17). The rest of this section is the candidate Home.
- Header: h1 "Welcome, {first name}", sub-line "Talent workspace · Employers see you as {alias}", primary button "Upload CV" / "Update CV" (opens onboarding at the CV step).
- **No KPI / stat cards** on the Talent Home.
- Order of the page: header → **"Your activity"** → search bar → "Recommended for you" → "Skill insights" → "Get set up" (only while a setup step is open).
- **"Your activity" panel (top):** h2 + muted "Your active applications and what employers see. Never a score on you." Two bordered boxes (`.activity-grid`, 2 columns, 1 column ≤1024px):
  1. **Active applications** (inbox icon): data from **all** the pages of the applications list (`fetchAllApplications()` in `views/applications.js`: pages of 50, up to 10 pages), so that the count is right; only items that are not `final`. Big number = the count + a yellow chip "{n} need(s) your action" when `needsAction`; a bar chart by status (Applied, Contacted, In review, Interview, Accepted, Offer); none → "No active applications. Find a job below and apply."; text link "See all applications".
  2. **What employers see** (eye icon): data `api.profile.shared()`: alias badge, "Roles: {title} (ANZSCO {code})", `sharedFactsHtml(shared)` (a line "Level: Senior · 7.5 years", then "Certifications: …" and "Awards: …" with the first 3 names and "+N more"; names and years only), up to 8 green skill chips with the level as a word ("Python · Advanced") + "+N more", hint "Never your name, contact details, photo, nationality or CV.", small secondary "Edit profile" (opens onboarding at `review`). No shared skills → "Employers can't find you yet. Accept your translated skills to share them." + "Review translated skills" (onboarding at `translation`).
- **"Skill insights" panel** (after the recommendations): muted "From the open jobs that fit you best." Premium: "Skills to learn next (in {basis} best-fit jobs)" (unit "jobs", empty "No skill gaps found.") and "Demand for your skills" bar charts (`api.stats.get().advanced`). Basic → `upgradeHtml("See which skills to learn next and the demand for your skills.")`.
- Recommendation cards also get `bindJobActions` (skip, report).
- **Candidate only — search bar** directly under the header (see [Components](#components)). It goes to the Jobs screen.
- **Candidate only — "Recommended for you"** panel: sub-line, a neutral **source chip** ("Loading jobs…" → "{openCount} open jobs · updated {d MMM yyyy}" or "Jobs unavailable"; never the name of a data provider), "Edit preferences" (opens onboarding at the goals step; hidden until the profile is done). Data: `api.jobs.recommended({ pageSize: 5, sort: "best" })` (the widget has **no pager**; the Jobs screen has the full list). Bookmarks are bound on the list (`bindBookmarks`).
  - No profile → empty state with icon tile, "No recommendations yet.", button "Complete your profile". Loading → "Loading jobs…" (`role="status"`). API error → "We couldn't load jobs. Try again later." (`role="alert"`). No results → "No jobs match your profile yet. Try more target roles, skills or locations."
  - Results → sub-line "{N} job(s) for: {target roles}. Each one shows why it fits." and up to 5 **job cards** (`jobCardHtml`, with the "Compare" check box), then `paintMeters`. When there are more recommended jobs than cards, a line "Showing the {n} best of {N} recommended jobs. See all jobs" with a text link to `#/jobs`.
- Two columns (2 : 1): "Get set up" panel (numbered steps; done = green check) and an accent-tint card "Explainable by design" with the role text. Candidate steps: "Create your account" (done) · "Upload your CV" (done: "Added: {file name}") · "Complete your career profile". Each open step has a "Start" button that opens onboarding ("Upload your CV" → `cv`; "Complete your career profile" → `questions`). The "Complete your profile" empty-state button opens `questions` if a CV exists, else `cv`.
- **First visit of a candidate** (`user.onboarding` is null): open onboarding at the CV step.
- After onboarding closes: `api.me.get()`, reset the recommendations to loading, render, then load them again.
- Use `textContent` or `esc()` for every value from the API.

**6. Onboarding dialog (`components/onboarding.js`, the `<dialog id="onboarding">` in `index.html`) — Feature 2: explainable cross-border skill translation**
Purpose: build the candidate's **translated profile** and collect goals for job recommendations. Native `<dialog>` with `showModal()`. API: `openOnboarding({ user, start: "cv" | "questions" | "translation" | "goals", done })`, `closeOnboarding()`. Layout: head (uppercase "Step X of N" + 4px accent meter + close X), scrollable body, foot on surface-subtle (Back at left, actions at right). Width `min(600px, 100% - 32px)`, radius xl, popover shadow, backdrop `rgba(13,19,27,.45)`. Each step: h2 (display-sm, `tabindex="-1"`, focused on render) + muted sub-line. Each render increases a run counter; a poll or a request from an older render does nothing.

Two paths:
- **Path A — with CV (9 steps):** CV → Reading → Education → Experience → Skills → **Certifications and awards** → **Translation** → Goals → Review.
- **Path B — skip CV (8 steps):** CV → Education → Experience → Skills → **Certifications and awards** → **Translation** → Goals → Review.
- The step keys are `cv, reading, education, experience, skills, credentials, translation, goals, review`. The word for a field of work is **"Domain"** on every step ("Domains", "Target domains", "Add at least one domain."). The keys `industry` and `targetIndustries` do not change.
- `start`: "cv" = step 1; "questions" / "review" = Education (Path B); "translation" / "goals" = that step (Path B). No "Back" button on the Reading step, and none on the step after it.
- **Edit mode (a done profile, `user.onboarding === "done"`)** — short paths that start and end on **"Your profile"** (the review step). The head shows "Edit profile" (one step) or "Edit profile · Step X of N".
  - `start` "questions" / "review" → `[review]`; "cv" → `[cv, reading, translation, review]`; "translation" → `[translation, review]`; "goals" → `[goals, review]`.
  - "Edit" on a row of "Your profile" → education / experience / skills → `[that step, translation, review]` (the translation runs again, so the shared skills stay correct); the Certifications and Awards rows → `[credentials, review]`; goals → `[goals, review]`; translation → `[translation, review]`; the CV row ("Change") → the cv path.
  - The first step of an edit path has a ghost "Back to profile" button (back to `[review]`).
  - CV step in edit mode: title "Update your CV", sub "We read the new CV and update your profile. You check every change before you save.", **no "Skip for now"**. After reading, a field that the new CV does not show **keeps the old answer** (it is not cleared). A failed read offers "Try a different file" and "Keep my current profile" (→ `[review]`).

1. **CV** — "Add your CV". Dashed drop zone (a `<label>` for a hidden file input, plus drag-and-drop) with an upload icon tile, "Drag and drop your CV, or browse", "PDF or DOCX, up to 10 MB". Validate type (`.pdf`, `.docx`; "Use a PDF or DOCX file.") and size (≤ 10 MB; "The file is larger than 10 MB. Use a smaller file."). A chosen file shows as a chip (file icon, name, size, remove X). Privacy note (accent-tint, shield icon), exact text: "Employers never see your CV or your personal details. They see only your translated skills and experience, under an alias — not your name, contact details, photo or nationality." Style the zone with `.field .dropzone` (flex column, centred) — a plain `.dropzone` loses to `.field label { display: block }`. Buttons: ghost **"Skip for now"** (→ Path B, step 2) and primary **"Upload and continue"** (disabled until a file is chosen) → `api.cv.upload(file)` (disable the buttons; API error → under the drop zone: `fields.file` or the message) → keep `cv` and `parse.id` → Path A, step 2.
2. **Reading** (Path A) — "Reading your CV", sub "We look for your roles, skills and qualifications. This takes up to 15 seconds." Body: indeterminate progress bar (240×6px, accent segment moving; static with `prefers-reduced-motion`) + "Reading your CV…" (`role="status"`), no buttons. Poll `api.cv.parseStatus(id)` every 600 ms, up to 30 s.
   - `done` → `Object.assign(data, result.fields)`; set every `result.missing` field to empty (`[]`, or `""` for `years`) — **AC6: a field that the CV does not show stays empty and flagged**; keep `result.detected` and `result.missing` as sets, `data.evidence = result.evidence`, `sampleLabel = result.sampleLabel`; announce "Your CV is read. Check the fields we filled."; go to Education.
   - **New keys of the CV result (version 2):** `result.fields` also has `targetRole` (a list), `level`, `yearsExperience`, `certifications` and `awards`, and they merge in the same way. The new keys are never in `missing`: the screen reads `result.found` (`{ currentRole, targetRole, level, yearsExperience, certifications, awards }`, booleans). `result.domain` (one of the 3 domains) is the domain of the CV: the screen sets the profile domains to `[result.domain]` and marks them "AI-detected" (`fields.industry` also holds domains only, at most 2, but the screen does not use it when `result.domain` is set). `result.skills` is `[{ name, level }]` (`level` 1 to 5, or `null` when the CV gives no evidence) and gives the start level of a skill card in the translation step. A field that the CV does not show is **empty, not guessed**. The screen shows each new field with the "AI-detected" tag and a `cv-hint` line (see below).
   - `failed` or timeout → empty state (`role="alert"`, alert icon tile): the API error ("We couldn't read this CV. Try a different file, or enter your details yourself.") + hint "Nothing is lost. You can try a different file, or enter your details yourself." Buttons: secondary "Try a different file" (→ step 1) and primary "Enter details myself" (→ Path B, Education). **AC9: no data is lost.**
3. **Education** — sub "Tell us about your qualifications. We show employers the Australian (AQF) level." Qualifications (`QUALIFICATIONS`, max 5, ≥1, hint "Add all your qualifications, highest first.") · Fields of study (`FIELDS_OF_STUDY`, max 5, ≥1) · Countries where you studied (optional, `COUNTRIES`, max 3, hint "Used only to find the Australian equivalent (AQF level). It is never used to rank you.").
4. **Experience** — sub "Tell us about the roles you have had, your level and where you worked." Current and past roles (`ROLES`, max 5, ≥1, hint "Start with your current or most recent role. Use the titles from your country — we translate them for you.") · **Domains** (`DOMAINS`, the 3 domains, **no custom value** — "Choose a domain from the list.", max 3, ≥1, hint "Add the domains you have worked in.") · **Your level** (a `select`: "Not sure" and the 6 levels of `LEVELS`; optional; hint "The level of your current or latest role. Choose “Not sure” if you do not know.") · **Exact years of experience** (an optional number 0 to 40, step 0.5; a valid number sets the band below with the same rule as the server — under 1 "Less than 1 year", under 3 "1–2 years", under 6 "3–5 years", up to 10 "6–10 years", above 10 "More than 10 years" — and locks the band drop-down; a number outside 0 to 40 gives "Enter a number from 0 to 40.") · Total years of work experience (single dropdown, **no custom values**, `YEARS`; error "Choose a range from the list.").
5. **Skills** — sub "… Use the words from your country — we translate them." `SKILLS`, max 15, ≥3; suggestion chips "+ skill" = the `SKILL_SUGGESTIONS` of all chosen domains (first 10; from all 3 domains if none is chosen). Hint "Add at least 3. Choose from the list, or type your own and press Enter."
5b. **Certifications and awards** (`credentials`) — sub "Add the certifications and awards that you have. This step is optional. You can skip it." Two lists, each a `fieldset` with a legend ("Certifications", "Awards"), an "Add a certification" / "Add an award" button, the empty text "No certifications added." / "No awards added.", at most **20 rows** in each list ("Maximum 20 reached") and a Remove button on each row. Under each list: "Employers see these names. Do not write your own name, your employer's name or contact details here." (the server removes e-mail addresses and phone numbers without a message). **Certification row:** Name (a combo box over the 38 `CERTIFICATIONS`; free text is allowed), Year (optional) and Issuer (optional; a known name fills the issuer and locks it: "From the list of known certifications."). **Award row:** Name, Kind (a `select` of the 12 `AWARD_KINDS`, required: "Choose a kind.") and Year (optional). A year must be from 1990 to next year. A row with nothing in it is dropped. Errors are under the field (`aria-invalid`, `aria-describedby`) and the first error takes the focus. Removing a row announces it and moves the focus to the next row or to the Add button. The primary button is "Continue".
6. **Translation** — "Your translated profile", sub "This is how Australian employers will read your experience. Accept the skills that are right. Edit or remove the others. Only accepted skills are shared." See [Translation step](#translation-step).
7. **Goals** — Target roles (`ROLES`, max 3, ≥1) · Target domains (optional toggle chips of `DOMAINS`, max 3) · Preferred locations (toggle chips `LOCATIONS`, ≥1) · Work type (toggle chips `WORK_TYPES`, ≥1). Toggle chips: `<button aria-pressed>` in a labelled `role="group"`.
8. **Review** — "Check your answers" (edit mode: **"Your profile"**, sub "Edit any part of your profile. Then save your changes."): bordered list, one row per answer (**17 rows**: CV, Qualifications, Fields of study, Countries, Roles, Domains, **Level**, **Exact years**, Experience, Skills, **Certifications**, **Awards**, **Shared skills** "{N}: {names}", Target roles, Target domains, Locations, Work type) — always all rows; "—" if empty; "Edit" link-button per row ("Change" for the CV). Markers under the label: yellow "Missing" when a required answer is empty (the value text is yellow-ink), else "From your CV" (AI chip) when the CV filled it. Primary "Save and see jobs" (edit mode: "Save changes"). The save checks every required answer (qualification, field of study, role, domain, years, ≥3 skills, ≥1 shared skill, target role, location, work type); a gap → rose alert "Some answers are missing. Edit the rows marked “Missing”."

**On the Education, Experience and Skills steps (after a CV):**
- **Field markers** at the right of each label: an "AI-detected" chip (accent-tint, ink-soft text, small accent check icon, 11px, `title` "The AI found this in your CV. Check it.") while the value came from the CV and the candidate has not changed it (AC2); a yellow "Missing" chip (`title` "Your CV does not show this. Add it if you can.") when the CV did not have it and the field is empty (AC6). Any add, remove or change removes "AI-detected".
- Education starts with a note (privacy-note style, check icon): "Check what we found in your CV. Change anything that is wrong. Fields marked “Missing” were not in your CV."
- **Mock mode only:** a yellow banner (`role="note"`, alert icon) at the top of these 3 steps: "Demo mode: the mock API filled these fields from a sample CV ({sampleLabel}), not from your file." (AI_Rule.md Rule 4.) Never show it with `API_MODE: "http"`.

**List fields.** Most answers are lists. One helper, `multiCombo(name, label, options, { placeholder, hint, optional, max = 5, suggestions })`: label row (label at left; markers + live counter "N of MAX" at right), input row (searchable dropdown with `clearOnPick` and `exclude` = values already added, + secondary "Add" button `aria-label="Add to {label}"`), hint, error line, values as pink removable chips (`aria-label="Remove {value}"`). Picking or Enter adds a value; a typed value that matches an option (any case) uses the option's spelling; no duplicates; when full, disable the input and the button ("Maximum N reached"). **Typed text that is not added yet is added when the user presses Continue.** Convert old string answers with `toList()`.

<a id="translation-step"></a>**Translation step**
- While loading: progress bar + "Translating your experience…". Call `api.profile.translate({ profile: data without cv/evidence, evidence })`. The request includes the current `profile.translation`, so the API keeps the candidate's decisions. Error → `role="alert"` empty state with the message.
- Head row: "{N} of {M} skills accepted." (`role="status"`) + secondary small "Accept all" (check icon; disabled when nothing is "suggested").
- **Translation card** (one per Australian skill; white, hairline, radius 12, 16px padding; **accepted = green border + 3px green inset bar at the left**):
  - Tags: kind chip (pink "Cross-border", blue "Cross-industry", neutral "Direct"), evidence chip "Evidence: Strong" (green) / "Moderate" (yellow) / "Limited" (neutral) with `title` "How much evidence supports this skill", and "Edited by you" when edited.
  - Map row: original text (muted; sr-only prefix "From your role:" / "From your skills:" / "From your qualification:") → arrow icon → **Australian skill** (ink 600) + blue ANZSCO chip when there is a code.
  - Reason (13px). Evidence quote (13px ink-soft on surface-subtle, radius 8): "From your CV: “{line}”" when there is one.
  - Actions (small buttons): **Accept** (secondary; `aria-pressed`; pressed = green tint "Accepted"; `aria-label` "Accept: {skill}" / "Accepted: {skill}"), **Edit** (ghost; replaces the actions with an inline editor: label "Australian skill name", searchable dropdown over `SKILLS` with the current name, primary "Save", ghost "Cancel"; empty → "Enter a skill name."; a new name → status "edited"; the same name → "accepted"), **Remove** (ghost, x icon; status "removed").
  - Every change announces it ("{skill} accepted.", "{skill} removed. You can undo this below.", "{skill} saved.").
- Under the list: "Removed (not shared):" + a chip button per removed skill ("+ {skill}", `aria-label` "Undo remove {skill}") that sets it back to "suggested".
- **"Things Australian employers may ask about"** box (surface-subtle, radius 12) when the API returns `gaps` (yellow alert list). PRD "honest gap flagging".
- **"What employers see"** preview (dashed accent border, accent-tint, radius 12): hint "Your alias and the skills you accept. Never your name, contact details, photo, nationality, employer names or your CV.", the **alias badge**, "Roles: {occupation} (ANZSCO {code})", green chips of the accepted skills (not qualifications) or "No skills accepted yet.", "Qualifications: {AQF levels}". It is built on the screen from the candidate's own decisions; the real recruiter view comes from `GET /me/shared-profile`.
- Continue needs at least one accepted or edited skill: else a rose alert at the top "Accept at least one skill, so employers can find you."

Rules: validate on Continue (errors below fields, `aria-invalid`, `aria-describedby`, focus the first invalid control). Save with `api.me.update({ profile, cv, onboarding: "done" })` — `profile` includes `translation` (each skill card with its `level` 1 to 5 or `null`) and the private `evidence` lines, and the version 2 keys `level`, `yearsExperience` (a number or `null`), `certifications` (`[{ name, issuer, year }]`) and `awards` (`[{ name, kind, year }]`); an old profile is cleaned when the dialog opens (`normalizeProfile`); on an API error show a rose alert at the top of the body and keep the answers. Closing early on a new profile saves a draft with `onboarding: "dismissed"` (it does not open again by itself). Closing a done profile discards unsaved edits (the CV upload is already saved). Build dialog content with DOM nodes, not `innerHTML`.

**7. Jobs — `/jobs?q=&location=&page=&pageSize=&sort=` (`views/jobs.js`, inside the shell)**
- Header: h1 "Jobs", sub-line "Search all open jobs. Each job shows which of its skills you have."
- The search bar, filled with `q` and `location` from the route.
- Panel "Results" (`h2#resultsTitle`, `tabindex="-1"`): status line (`role="status"`) "{N} open job(s) for “{q}” in {location}. Best fit first." or "… Newest first." (omit the parts that are empty), then a **sort select** (`sort-select`, id `jobs-sort`: **Best match** `best` (default) and **Newest posted** `newest`), then the job cards with `bindBookmarks` + `bindJobActions` + `bindCompare`, then the **pager** (list name `jobs`). Data: `api.jobs.search({ q, location, page, pageSize, sort })` (skipped jobs are left out by the API). `total` comes from `page.total`.
- **Lists with a pager and a sort (shared helper `createPagedList(cfg)` in `job-card.js`):** it returns `{ state, start, load, reload }`. It reads `page`, `pageSize` and `sort` from the route query, loads a page with `cfg.fetchPage`, draws it with `cfg.render`, draws the sort select and the pager, and keeps the address (see [Routes](#routes)). A sort or page size change goes to page 1. The size is saved for each list and user. Screen readers: after a page change the polite announcement "Page 2 of 7" and the focus goes to the heading of the list; after a sort change "Sorted by Newest posted. Page 1 of 7"; after a size change "20 rows per page. Page 1 of 3" and the select keeps the focus. While a page loads, the list has `aria-busy="true"`. A page past the end is moved to the last page by the server, and the address is corrected with `replaceState`.
- No results → empty state (search icon tile) "No open jobs match your search. Try a different word or location." + "Show all jobs" (`#/jobs`). Loading and error states as on Home.

**8. Job detail — `/jobs/:id` (`views/jobs.js`, inside the shell; nav item "Jobs")**
- While loading: back link + "Loading job…". Set `document.title` to "{job title} — Jinder".
- Back link, then the head (one column): tags (neutral chip = category and, when there is one, the specialisation: "Data · Data analytics"; blue ANZSCO chip), h1 = title (display-md, 32px ≤768px), meta line (company · area · type · salary), dates row; **actions row, left aligned:**
  - Apply: not applied and open → primary large link **"Apply"** (send icon) to `#/jobs/{id}/apply`; applied → primary large link "✓ Applied · Track status" to `#/applications/{applicationId}`; closed → a disabled "Apply" with `aria-describedby` → hint "This job is closed. You can't apply now."
  - Bookmark button with text ("Save"/"Saved"); **"Compare"** (`button.compare-btn[data-compare-detail]`, secondary, columns icon, `aria-pressed`, a check mark when the job is in the basket; real backend only) adds or removes this job in the basket; ghost "Not for me" (not shown after applying) → `api.jobs.skip(id)`, announce "{title} is hidden from your recommendations.", go to `/jobs`; ghost "Report" (flag) → `openReport("job", …)`.
- Two columns (2 : 1, one column ≤1024px):
  - **Left column, two panels:**
    - Panel **"Job facts"** (`dl.fact-grid`): Level, Experience (`experienceText(minYears, maxYears)`), Work mode, Place (`area`), Type, Salary, Education (`educationMin`). A fact that the job does not have is left out. For a job that has version 2 data (a level, skill levels, a certification or an award): h3 **"Certifications"** with the groups "Required" and "Preferred" (neutral chips), and h3 **"Awards"** with the group "Preferred" (the label of the award kind from `AWARD_KINDS`, for example "Hackathon"). An empty list says "This job does not ask for a certification." (or "an award"). A job with no version 2 data shows neither section.
    - Panel **"About the role"** (`.jd-about`): `jdViewHtml(job.description || job.summary, { label: "Job description" })`. This is the **full description with its headings, never cut** ("About the role", "What you will do", "What you bring", …). It scrolls inside the box (`role="region"`, `tabindex="0"`, maximum height `min(32rem, 70vh)`) and the keyboard can scroll it.
  - Panel **"Your skills for this job"**: `coverageHtml(match)` (40px number), the "Fit score" line, h3 "Skill by skill" + `skillMatchHtml(match.skills)`, h3 "Why it fits" + reasons and notes (or "This job is not close to your goals yet."). No profile → empty state "Complete your profile to see how your skills match this job." + button to Home.
- Panel **"How this job fits you"** (`components/bridge.js`, `fitHtml`; **kept, not changed**; only with `job.bridge.axes`): h2, a muted line "Eight numbers from 0 to 100. A higher number is a better fit. Jinder does not add them up into one verdict.", a blue chip "Fit score {score}" at the right of the head, and two columns: a radar chart (`radarHtml`, one series "This job") and a table of the same numbers (`radarTableHtml`, with the formula F1, F2 or F5 after each axis name) with a hint line for each formula. The axes: Occupation fit, Skills, Work methods (Formula 1); Readiness (Formula 2); Capability, Pay upside, Location, Freshness (Formula 5).
- Panel **"Your path to this job"** (**new**, `pathHtml(bridge.path)` in `components/bridge.js`; only when the talent has a profile; the mock does not send it). `section.panel.bridge.path[aria-labelledby=pathTitle]`:
  - Head: h2 "Your path to this job" and the muted line "What you already have for this job, and what is still missing. This is a guide for you. Employers never see it."
  - Summary chips (`ul.path-summary`): "7 fit" (green, check icon), "3 gaps" (yellow, alert icon; "1 gap"), "about 5.5 months to close the gaps" (neutral; only when there is a gap) and the readiness tier (blue, with a hidden word "Readiness:").
  - Two columns (`.path-grid`, one column at 1024px or less). **Left:** a **radar with two layers** (`radarHtml(…, { layers: true })`): series 1 "You have" (filled) and series 2 "Job requires" (outline), over `path.axes` (the skill groups Languages, Frameworks & libraries, Cloud & DevOps, Data & storage, ML & AI, Engineering practices, Collaboration, and the axes Experience, Level and Certifications when the job has them), and a table "Skill group (0 to 100)" with the columns Job requires, You have and **Status**. The status is an icon and a word: **Fit** (check), **Above** (star), **Gap** (alert). **Right:** two lists. **"Where you fit"** (`path.fit`): each item has a check, the label in bold, a small chip for the kind when it is not a skill (Experience, Level, Certification, Award), "You: Advanced · Needs: Proficient" and the note. **"Gaps to close"** (`path.gaps`): each item has the kind chip (**Missing**, **Below level**, **Experience**, **Level**, **Certification**), the label, a **"Required"** chip when `must` is true, "You: None · Needs: Proficient", the months ("about 3.5 months", "less than 1 month") and the note.
  - An empty fit list: "Nothing in your profile meets a requirement of this job yet." An empty gap list: "No gaps: you meet every requirement." Last line: "These are estimates from the type of each gap. They are not a promise and not a decision about you."
  - A missing or empty `path` (the mock, an old job): the panel has only the head and "A detailed path is not available for this job." No crash. All text is escaped.
  - **Removed in version 2:** the 12-month line chart, the facts list ("Occupation fit", "Gaps", "Time to close the gaps") and `bridge.projection`. There is no line chart in the app.
- Panel "Similar jobs": a head with h2 and (real backend, when there are similar jobs) a small secondary button **"Compare with these jobs"** (columns icon, `data-compare-similar`): this job and the similar jobs go into the basket (at most 5; jobs that are in already stay), then `#/compare` opens. If the basket is full, a polite announcement says how many jobs are in. Up to 3 compact job cards (each with the `similarity` chip and the "Compare" check box), or "No similar open jobs right now."
- Unknown id (404) → h1 "We can't find this job", the API message, button "Browse jobs".

**9. Bookmarks — `/bookmarks?page=&pageSize=&sort=` (`views/jobs.js`, inside the shell)**
- Header: h1 "Bookmarks", sub-line "Jobs you saved for later.", secondary large button "Browse jobs" (search icon, `#/jobs`).
- Panel "Saved jobs" (`h2#savedTitle`): count "{N} saved job(s)" (`role="status"`), a **sort select** (**Recently saved** `saved` (default), **Best match** `best`, **Newest posted** `newest`), the job cards (closed jobs stay and show "Closed") and the **pager** (list name `bookmarks`). Data: `api.bookmarks.list({ page, pageSize, sort })`.
- Removing a bookmark on this screen removes its card at once and updates the count, then the page loads again quietly, so that the next job moves up. If the page is then empty, the server gives the last page. Cards also get `bindJobActions` and `bindCompare`. No bookmarks → empty state (bookmark icon tile) "No saved jobs yet. Save a job to compare it later." + primary "Browse jobs". The old compare picker ("Compare jobs (n/3)") is **removed**: the "Compare" check box on each card and the compare tray replace it.

**10. Settings — `/settings` (`views/settings.js`, inside the shell, both roles)**
Feature 1 AC9. Settings has **no menu item**: it opens from the **user block** at the bottom of the menu (a link to `#/settings`). `#/settings?section=plan` scrolls to the plan. h1 "Settings", sub-line (candidate: "Your account, alias, career profile, plan and password."; recruiter: "Your account, plan and password."). Sections are panels with two columns (280px intro : form; one column ≤1024px). Intro = h2 (Inter 18/600) + muted text. Forms are max 480px wide, `novalidate`, with their own alert (`role="alert"`) and actions aligned right. Every save disables its button, shows a green alert and `announce()`s the message; API field errors go under the fields.
1. **Your plan** (`id="plan"`; **the first section**) — the account area: it lists the Premium benefits, used and not used. Intro (with the real backend) "See which features your plan includes, and which Premium features you used."; without `benefits` (the mock) "Demo only: switch the plan to try the Premium features. There is no payment.". Load with `api.entitlements.get()`.
   - **The plan card** (`.plan-card`; only when `entitlements.benefits` has items). Head: an icon tile and "Your current plan: **Basic**" (neutral chip) or "Your current plan: **Premium**" (gold chip, the crown tile, a 2px gold border); a muted line ("Premium adds the features below." / "You can use all of these features."). Then `ul.benefit-list`: one row for each benefit (`li.benefit[data-benefit]`: an icon, the label, the description and a status).
     - **Basic:** each benefit has a lock icon and a gold chip "Premium" (a benefit with `available: true` shows a check and a neutral "Included"). Primary button **"Try Premium (demo)"**: it sets the plan, the crown shows in the menu, the focus moves to the card title and the message says "Your plan is now Premium."
     - **Premium:** each benefit has a check and a green chip **"Used"** with "N times" (from `usedCount`; "1 time") or a neutral chip **"Not used yet"**.
     - The benefits (from the API): employer — "See every talent profile, not only the top 5", "Invite talent to apply", "Compare up to 5 talent profiles", "Pipeline by stage and interest per job"; talent — "Skills to learn next", "Demand for your skills".
   - **The demo switch** (under the card): the text "Demo only: switch the plan to try the Premium features. There is no payment." and a 2-column radio group of cards (`.plan-option`; checked = accent border + accent-tint): **Basic** (candidate: "Recommendations, applications and basic charts."; recruiter: "Post jobs, review applications, the top talent for each job and basic charts.") and **Premium** + gold "Premium" chip (candidate: "Also: skills to learn next and the demand for your skills."; recruiter: "Also: all talent, invite talent, compare up to 5 profiles and advanced charts."). Change → `api.entitlements.set(plan)` → green alert "Your plan is now Premium." / "… Basic." and the card is drawn again. The menu updates by itself (the crown and the lock; event `jinder:plan-change`). A failed change (for example `ALLOW_PLAN_SWITCH` off: 403) shows the message and sets the switch back to the real plan. Without `benefits` (the mock) only the switch shows, as in version 1.
2. **Profile details** — intro (candidate: "Only you can see your name and email. Employers see your alias."; employer: "Talent sees your company name on your jobs."). Full name (required), Company (recruiters, required), Email (read-only, surface-subtle; hint "You can't change your email in this version."). "Save details" → `api.me.update({ name, company? })` → "Your details are saved." Then update the name and the initials in the user block (`updateShellUser`).
3. **Alias** (candidates) — intro "Employers see you only by this name, until you agree to share your identity. Use a neutral name: not your real name, country or city." Row "Employers see you as" + **alias badge** (pill, pink tint, display font 16/600). Field "New alias" with a "Suggest another" link-button, hint "3 to 30 letters. Every alias on Jinder is different." Checks: 3–30 characters; not the same as the current alias ("This is your alias now. Enter a different one."). "Save alias" → `api.me.update({ alias })` → "Your alias is now {alias}."; clear the field; update the badge and `[data-shell-alias]`. `ALIAS_TAKEN` → error + "Use “{suggestion}”" link-button.
4. **Career profile** (candidates) — intro "We use your answers to recommend jobs and to show your skill gaps." A review list (2 columns: label, value): CV (file name or "No CV"), Target roles, Skills ("{N} skills: …"), **Shared skills** ("{N} accepted" or "None yet. Review your translated skills."), Locations, Work type. Buttons: secondary "Update CV" (upload icon; onboarding at `cv`), secondary **"Review translated skills"** (onboarding at `translation`), primary "Edit answers" (onboarding at `questions`). After the dialog closes, reload the user, the list and the preview.
   - **"What employers see"** box under the buttons (same style as the translation preview): title, hint "This is your profile as employers see it. It never shows your name, contact details, photo, nationality, employer names or your CV.", then the data from **`api.profile.shared()`** (`GET /me/shared-profile`): alias badge, "Roles: {title} (ANZSCO {code})", `sharedFactsHtml(shared)` (a line "Level: Mid · 4.5 years", then "Certifications: …" and "Awards: …" with the first 3 names), "Skills:" green chips with the level as a word ("Python · Advanced"; or "None yet"), "Qualifications: {AQF} · {fields of study}", "Domains: {domains}". Loading "Loading…" (`role="status"`); error → the message (`role="alert"`). The box shows the same facts as the Home panel and the onboarding preview.
5. **Password** — intro "When you change your password, you are signed out on your other devices." Current password, New password (hint "At least 8 characters."), Confirm new password; show/hide buttons on the first two. Checks: current not empty ("Enter your current password."), new ≥ 8, confirm equal ("Passwords don't match."). "Change password" → `api.me.changePassword({ currentPassword, newPassword })` → "Your password is changed." and reset the form.
6. **Your data** (only when `API_MODE` is "http"; between Password and Session) — intro "Download a copy of the data that Jinder keeps about you, or delete your account and all of its data. You can't undo a delete." A `form-alert` and two buttons: secondary "Download my data" (file icon) → `api.me.export()` → the browser saves `jinder-my-data.json`, then a green "Your data is downloaded."; danger "Delete my account" → a dialog ("Delete your account?"; talent: "This deletes your profile, your CV and your applications. You can't undo this."; employer: "This deletes your jobs and the applications for them. You can't undo this."; a Password field; danger "Delete account") → `api.me.deleteAccount(password)` → clear the session and go to `#/`. A wrong password shows "Your password is not correct." in the dialog.
7. **Session** — intro "Sign out of Jinder on this device." Secondary button "Sign out" (log-out icon) → `api.auth.logout()` → `/login`.
8. **Demo data** (only when `API_MODE` is "mock") — intro "The demo keeps all data in this browser. Reset deletes all local accounts and data, and writes the demo data again." Danger button "Reset demo data" → confirm dialog ("Reset the demo data?", "This deletes all accounts and data in this browser, and writes the demo data again. You are signed out.", danger "Reset") → `api.demo.reset()`, clear the session, go to `#/login`.

**11. System views (`views/system.js`)**
- **Placeholder** (inside the shell): h1 = section name, sub-line, panel with empty state (clock icon tile, "This section is coming soon.", "Back to Home").
- **No access** (inside the shell): see [Routes](#routes).
- **Page not found:** top nav with logo, eyebrow "Error 404", h1 "We can't find this page", text "The link may be old, or the page may have moved.", button "Go to Home" (signed in) or "Go to the home page".

**Shared rules for screens 12–24:** loading = back link + `role="status"` "Loading …"; an API error on load = h1 "We can't find this …" + the API message. Action buttons are disabled while their request runs. After an action, render the new state that the API returns, `announce()` a short message and focus the action panel h2. API field errors go under the fields (`applyFieldErrors`); other errors go into the panel alert (`fields.form` first, then `message`). Long texts have a live counter "{n} / {max}" (`aria-live="polite"`).

**12. Apply — `/jobs/:id/apply` (`views/applications.js`) — Feature 4 AC1, AC2, AC12, AC13**
- Load `api.jobs.get(id)` and `api.profile.shared()` together. Already applied → replace the route with `/applications/{applicationId}`. Title "Apply: {job title} — Jinder".
- Back link "Back to job"; h1 "Apply for {title}"; sub-line company · area · type.
- Closed job → empty state (clock) "This job is closed. You can't apply now." + "Find open jobs". No shared skills → empty state (target) "Accept at least one translated skill before you apply. Employers see only the skills that you accept." + "Review translated skills" (`#/settings`).
- Steps line `<ol class="apply-steps">`: "1. Review your profile" (current) · "2. Send" · "3. Track".
- Two columns: panel **"What the employer sees"** (muted "Your alias and your translated profile only. Your name, contact details and CV stay private until you agree to share them for an interview." + secondary "Edit profile" → `#/settings`) with `sharedProfileHtml(shared)`; side panel "Your skills for this job" (coverage + `skillMatchHtml`).
- Panel "Send your application": form with text area "Note to the employer (optional)" (max 500, counter, hint "Do not add your name, email or phone number. We remove contact details before the employer sees the note."), hint "You can change the note until the employer starts the review.", ghost "Cancel" (to the job) + primary large "Send application" (send icon) → `api.applications.create({ jobId, note })` → `/applications/{id}?new=1`.

**13. Applications — `/applications?tab=&page=&pageSize=&sort=` (`views/applications.js`) — Feature 4 AC4, AC5**
- h1 "Applications", sub-line "Track every application and its status.", secondary large "Find jobs".
- Tabs (`role="tablist"`, links with `aria-selected`): "Active {n}" (`#/applications`) and "Past {n}" (`#/applications?tab=past`). Past = `final` (confirmed, rejected, declined). The tab links keep the sort.
- Data: the API has no filter for Active and Past, so the screen reads **all** the applications (`fetchAllApplications({ sort })`: pages of 50, up to 10 pages; `api.applications.list({ page, pageSize, sort })`), filters the tab in the browser and cuts the page. The tab counts and the Home count are right. The panel has a **sort select** (**Recently updated** `updated` (default), **Best skill match** `best`, **Newest application** `newest`; the server does the sort) and the **pager** (list name `applications`). Row (`.app-row`, bordered, radius 12): title link → `#/applications/{id}`, meta "{company} · {area}" (+ " · Invitation from the employer" when `origin` is contacted), hint "Applied {date} · Updated {date}"; right side: ribbon, yellow chip "Action needed" (or "Give feedback" when final) when `needsAction`, hint "{coverage}% skills covered".
- Empty: Active "No active applications. Find a job that fits your skills and apply." + "Browse jobs"; Past "No past applications. Finished applications move here."

**14. Application tracking — `/applications/:id` (`views/applications.js`) — Feature 4 AC3, AC6–AC11, AC14, AC15**
- `?new=1` → green alert (`role="status"`, check) "Your application is sent. The employer sees your alias and translated profile only."
- Back link "Applications" (final → `?tab=past`); h1 job title; sub-line company · area · text link "Job detail"; ribbon at the right. Title "{job} · {status label} — Jinder".
- Panel with `stepperHtml(app)`.
- **Action panel** (`.action-panel`, 2px border; tone blue / yellow / green), by status:
  - `applied` → "Change your note": note text area (value = current note) + secondary "Save note" → `api.applications.update(id, { note })` → "Your note is saved."
  - `review` → "The employer is reviewing your application" + "You can't change it now. We tell you when the status changes."
  - `contacted` (blue) → "The employer invited you": the invitation message as a quote, muted "The employer found your anonymous profile. They can offer interview times next. If you are not interested, decline the invitation.", ghost "Decline invitation" → confirm dialog ("Decline the invitation?", "The employer sees that you declined. You can't undo this.", danger "Decline") → `api.applications.decline(id)`.
  - `interview`, no slots → "Interview" + "The employer will offer interview times."
  - `interview`, slots, not confirmed (yellow) → h2 "Choose an interview time" (or "Waiting for the employer to confirm" + "You chose **{slot}**. You can change it until the employer confirms."). Radio cards for the future slots (calendar icon, `slotText`; checked = accent). Consent check box (surface-subtle box): "Share my name and email with this employer for the interview." + hint "If you do not tick this, you stay anonymous." Primary "Choose this time" / "Change time" → `api.applications.chooseSlot(id, { slotId, shareIdentity })`. No choice → "Choose a time." All slots passed → "All the times have passed. The employer can offer new times." and a disabled button.
  - `interview`, confirmed (green) → "Your interview is confirmed" + calendar + the time + whether the identity is shared.
  - `accepted` (green) → "You passed the interview" + "The employer accepted you after the interview. An offer can follow."
  - `offer` (green) → "You have an offer": offer text quote, "Sent {date}", ghost "Decline offer" (confirm dialog "Decline the offer?", "The application ends. You can't undo this.") and primary "Accept offer" → `api.applications.replyOffer(id, true|false)`.
  - final → "Application finished" + the end text (confirmed "You accepted the offer. Congratulations!", rejected "This application is finished. The employer did not select you this time, or you declined the offer.", declined "You declined the invitation.") + the employer's feedback (if any). No own feedback yet → form: "Feedback to the employer (optional)" (hint "The employer sees this with your alias.") and "Feedback to the Jinder team (optional)" (hint "Only the Jinder team sees this."), max 1000 each, primary "Send feedback" → `api.applications.feedback(id, { toOther, toTeam })`. Both empty → API `fields.form` "Write feedback in at least one box.". After → "Your feedback" + "Sent {date}. Thank you."
- Two columns: panel "What you sent" (muted "A copy of your profile on {date}. Later changes to your profile do not change it.", "Your note" quote, `sharedProfileHtml(snapshot)`) and side panel "Your skills for this job" (`match` of the snapshot).
- Panel "History" (`historyHtml`).

**15. Notifications — `/notifications` (`views/notifications.js`, both roles) — Feature 7**
- h1 "Notifications", sub-line "Changes to your applications and jobs.", secondary "Mark all as read" (only when there are unread items) → `api.notifications.markRead([])`, announce "All notifications are marked as read.", reload.
- List (newest first, max 50): icon tile by type (offer = star, slots = calendar, feedback/contacted = send, edited job = edit, new application = inbox, else bell), title (a link when `link` is set: click → `markRead([id])` → then go to the link), body, hint "{date-time}" + " · Email sent (demo)" when `email` + " · Unread". Unread rows: accent border + accent-tint background. After each load, fire `jinder:notifications` with the unread count. Empty: bell tile "No notifications yet."

**16. My jobs — `/my-jobs?page=&pageSize=` (`views/recruiter.js`) — Feature 6 AC1–AC3**
- h1 "My jobs", sub-line "Post jobs and manage your hiring pipeline.", secondary large **"Post from a PDF"** (upload icon, `#/my-jobs/new?from=file`) + primary large "Post a job" (`#/my-jobs/new`).
- Panel "Your jobs" (`h2#myJobsTitle`, `tabindex="-1"`): the muted text "Newest first." (**one sort only**: no sort select), the rows and the **pager** (list name `my-jobs`). `api.recruiter.jobs.list({ page, pageSize })`.
- Rows: title link → `#/my-jobs/{id}/overview` (the **job overview**, screen 18b), meta "{category} · {level} · {location} · {type}", hint "Posted {date} · Closes {date}" (+ " · {n} invited"); right: close badge chip (green "Open", yellow "Closes in {n} days" when < 7 days, rose "Closed"), yellow chip "{n} waiting for you" (clock), target meter "{applicants} / {target}" + "applicants vs target", ghost small **"Applicants"** (→ `#/my-jobs/{id}`) and ghost small "Edit".
- Empty: "No jobs yet. Post your first job. Jinder suggests the required skills." + "Post a job".

**17. Recruiter Home — `/home` for a recruiter (`recruiterHomeView` in `views/recruiter.js`) — Feature 7 AC5, AC8**
- h1 "Welcome, {first name}", sub-line "Employer workspace · {company}", primary large "Post a job".
- 3 stat cards from `api.stats.get()`: "Open jobs" ("{total} posted in total"), "Jobs at target" ("Jobs with enough applicants"), "Waiting for you" ("Applications that need an answer" / "Nothing waiting on you").
- Two equal columns: panel "My jobs" (up to 4 rows: title link → the job overview, "{location} · {n} waiting for you" / "Nothing waiting", badge; "See all") and panel "Top talent" ("For {job}. Ordered by skill coverage.", up to 3 rows: alias link → candidate detail, roles, coverage mini meter "{m} of {n} skills"; "See all"). No jobs → "Post a job to see anonymous talent ordered by skill coverage." Home asks for the newest 10 jobs and for 3 talent (so a Premium employer who opens Home does not mark "See every talent profile" as used).
- Panel "Hiring activity": "Applicants per job" bar chart (when there are more than 10 jobs: "Shows the newest 10 of {N} jobs."); Premium: "Pipeline by stage" bar chart and "Interest per job" table (Job, Shown, Opened, Saved, Applied; hint "Totals per job. We never show what one talent did."); Basic: the gold upgrade box (`upgradeBoxHtml`: a lock badge that opens the Premium dialog, the text "See your pipeline by stage and how talent interacts with each job." and "See plans"). Opening the Home of a Premium employer counts as using "Pipeline by stage and interest per job" (the backend writes `advanced_charts_view` for each `GET /stats` of an employer).

**18. Post / edit a job — `/my-jobs/new`, `/my-jobs/:id/edit` — Feature 6 AC1, AC10, AC13 (decision Q2)**
- h1 "Post a job" / "Edit {title}", sub-line "Talent is matched on the required skills. Do not ask for age, gender, nationality or visa status." Edit shows a yellow warning (`role="note"`): "When you save, everyone who applied gets a notification that the job changed."
- **Post from a file (new jobs only)** — panel "Start from a job description file" (max 880px), muted "Upload the job description as a PDF or DOCX. Jinder reads it and fills the form. You check every field before you post.", a drop zone (same style as the CV drop zone: "Drag and drop the file, or browse", "PDF or DOCX, up to 10 MB"), a file chip with a remove button, an error line, a status area and primary "Read file and fill the form" (disabled until a file is chosen). Then a divider line "or fill in the form yourself". `?from=file` scrolls to the panel and focuses the file input.
  - Checks in the browser: type ("Use a PDF or DOCX file."), size ("The file is larger than 10 MB. Use a smaller file.").
  - Read → `api.recruiter.jobs.importFile(file)` → poll `importStatus(id)` every 600 ms (max 30 s) with an indeterminate bar "Reading your file…".
  - Done → fill title, **domain** (the result has `domain` and `category`; the form uses `domain` first), **specialisation**, location, type, salary, **level, minimum and maximum years, work mode, education, `skillRequirements` (or `skills`), `certifications` and `awards`**, and the description (max 12 skills); put an AI chip "From your file" after the label of each `detected` field and a yellow "Missing" chip for each `missing` field or for a value that is not in a list of the form; a change to a field removes its marker. Mock mode: yellow demo banner "Demo mode: the mock API filled the form from a sample job description ({sampleLabel}), not from your file." Green alert "We filled the form from your file. Check each field, add the close date and the target, then post the job."; focus the title. The close date and the target stay with the employer.
  - Failed or timeout → rose alert with the API error ("We couldn't read this file. Try a different file, or fill in the form yourself.").
- Form (panel, max 880px; field names are the API keys; error text goes to `.field-error[data-for=name]`): Job title (≤100); a 3-column grid (2 ≤1024px, 1 ≤768px): **Domain** (`<select>`, name `category`, the 3 `DOMAINS`; a value from older data stays as an extra option), **Specialisation** (`<select>`, `SPECIALISATIONS[domain]`; it changes with the domain and a value of another domain is cleared), **Level** (`<select>` of `LEVELS`, "Mid" for a new job), **Minimum years** and **Maximum years** (numbers 0 to 40, step 0.5; an empty maximum means "or more", with a hint; the browser checks maximum below minimum), **Work mode** (`WORK_MODES`), **Education** (`QUALIFICATIONS`), Location (`LOCATIONS`), Work type (`WORK_TYPES`), Salary (optional, placeholder "For example: $90,000 – $105,000"), Close date (`type="date"`, `min` = tomorrow; default +30 days), Target applicants (number 1–10000, default 20).
- **Job description (`jd-editor`)**: a text area (`name="description"`, `maxlength` 10000 — the backend limit —, a counter "n of 10,000 characters"). A **new** job starts with the 8 headings "## About the role", "## What you will do", "## What you bring", "## Nice to have", "## Tech stack", "## What we offer", "## About the company", "## How we hire", each with one empty bullet ("- "). The hint says what "## " and "- " do. **When the form is sent**, `cleanJdText` removes empty bullets, headings without text and extra blank lines; a form with the untouched template gets the API error "Write a description of at least 30 characters." on the description. A **Preview** button (`aria-expanded`, text "Preview" / "Hide preview") shows `jdViewHtml(cleanJdText(text))` and follows the text while it is open.
- **Required skills (1 to 12)** fieldset (`skill-req`): hint "Jinder suggests skills from the title and the description. Add, remove or change them.", one row for each skill: the name, a **level select** ("1 - Beginner" … "5 - Expert") and a check box **"Must have"** (the level select and the check box have the skill name as a hidden label), and a remove button (`aria-label` "Remove {skill}"). Input "Add a skill" (a combo box over `SKILLS`; free text is allowed) + secondary "Add" (Enter adds), ghost "Suggest skills" (star) → `api.recruiter.jobs.suggestSkills({ title, description, category })` → "Suggested:" blue chip buttons "+ {skill}" (click adds the skill at **level 3 and Must have** and removes the chip) or "No new suggestions. Add more detail to the description." No duplicates (any case); 13th → "You can add up to 12 skills." A job from older data has names only: its skills start at level 3 and "Must have". The form sends `skillRequirements` and `skills`.
- **Certifications** (`cert-editor`): two lists, "Required certifications" and "Preferred certifications": a combo box over the 38 `CERTIFICATIONS` (or free text), chips with a remove button, at most 10 in each list, a name is in one list only. Sent as `certifications: { required, preferred }`.
- **Awards** (`award-editor`): "Preferred awards": 12 check boxes (`AWARD_KINDS`), at most 10. Sent as `awards: { preferred: [kind] }`.
- Submit "Post job" / "Save changes" → `create` / `update` with `closesAt` = the date at 23:59 local time (ISO) → **`/my-jobs/{id}/overview`**. Field errors from the API (for example "The close date must be in the future.") are written next to the field (`aria-invalid`, `aria-describedby`); the focus goes to the first field with an error (a group focuses its first control); alert "Correct the fields that show an error." Enter in an empty combo box does not send the form.
- **Mock mode:** the fields that the mock does not keep are not drawn (specialisation, level, years, work mode, education, skill level and must, certifications, awards). Skills are chips as before; the template, the counter and the preview stay. The Domain select checks the 3 domains.

**18b. Job overview — `/my-jobs/:id/overview` (`jobOverviewView` in `views/recruiter.js`) — R4, F3** (new)
- Data: `api.recruiter.jobs.get(id)` and `api.stats.get()` (only for the interest card). Back link "My jobs".
- Header: h1 title; company · place · salary; chips (`.jo-chips`): status ("Open", "Closing soon" + the label "Closes in {n} days", "Closed"), level, work mode. Actions: primary **"Edit job"** (not for a closed job), secondary "See talent" (`#/candidates?jobId=`), secondary "See applicants" (`#/my-jobs/{id}`).
- A closed job: a banner (`.jo-banner`, `role="note"`) and no Edit button; the page is read-only.
- Small stats (`.jo-stats`, `report-card`): Applicants (with the target meter), Waiting for you, Invited, Interest in this job (Premium: Shown, Opened, Saved, Applied for this job, from `stats.advanced.jobs`; Basic: a gold lock badge "Interest per job").
- Panel **"About the role"**: the **full description** in `jdViewHtml(description, { label: "About the role" })` (the scroll box: `tabindex="0"`, `role="region"`; reachable by keyboard).
- Panel **"Job facts"** (`dl.facts.jo-facts`): Domain, Specialisation, Level, Experience ("5 to 9 years", "6 years or more", "Up to 9 years"), Type, Work mode, Education, Posted, Closes. A key that the answer does not have is left out; a `null` shows "Not given".
- Panel **"Skills"**: a table Skill | Level needed | Must or nice (Must first). A job without levels shows chips. Panel **"Certifications and awards"**: required, preferred, preferred awards (labels from `AWARD_KINDS`); left out when the answer has neither key.

**19. Applications for a job — `/my-jobs/:id?status=&page=&pageSize=` — Feature 6 AC4, AC5**
- Back link "My jobs"; h1 job title; sub-line "{location} · {type} · Closes {date}" + badge; secondary "Job overview" (`#/my-jobs/{id}/overview`), secondary "Find talent" (`#/candidates?jobId=`) + primary "Edit job".
- 3 cards: Applicants (target meter), Waiting for you (number), Required skills (chips).
- Panel "Applications" (`h2#appsTitle`; "Talent profiles are anonymous. You see the alias and the translated skills. Newest first." — **one sort only**) with a "Show" `<select>`: All, Waiting for you, and each of the 9 statuses (a fixed list; the "All (n)" counts are gone because one page does not know the real counts) → `?status=`. The list has the **pager** (list name `applicants`). The API has no status filter: with a filter the screen reads all pages (50 at a time, up to 20 pages) and cuts the pages in the browser; without a filter the paging is real. Rows: alias link → `#/review/{id}`, hint "Applied {date}" / "You sent an invitation {date}" · "Updated {date}"; ribbon, "Waiting for you" chip, coverage mini meter, secondary small "Review". Empty: "No applications yet. Invite talent, or wait for applications." / "No applications with this status."

**20. Review — `/review/:id` — Feature 6 AC6–AC9, AC11, AC12, AC14 (decision Q4)**
- Back link = the job title (→ `/my-jobs/{jobId}`); h1 = alias; sub-line "{job} · Applied {date}" (or "You sent an invitation"); ribbon; stepper.
- **Action panel** by status; "Not selected" (ghost) is in every panel where `allowedNext` has `rejected` → confirm dialog "Mark as not selected?" ("{alias} gets a notification and an email. You can't undo this.", danger "Not selected"):
  - `applied` (blue) → "New application" + "Start the review when you are ready. After that, they can't change the application." + primary "Start review" (`to: "review"`).
  - `review` → "Invite to an interview" / `contacted` → "Waiting for a reply": 3 `datetime-local` inputs "Time 1", "Time 2 (optional)", "Time 3 (optional)" (`min` = now + 1 hour) + primary "Send interview times" (`to: "interview", slots: ISO[]`). API error "Offer 1 to 3 interview times." / "Choose times in the future." under the slots.
  - `interview`, no choice yet (yellow) → "Waiting for them to choose a time" + the slot list.
  - `canConfirmSlot` (yellow) → "Confirm the interview time" + the chosen time + identity text + primary "Confirm time" → `confirmSlot(id)`.
  - `interview`, confirmed (green) → "Record the interview result" + primary "Accept" (`to: "accepted"`).
  - `accepted` (green) → "Send an offer": text area "Offer details" (hint "Role, start date, salary and the next steps. Do not add personal contact details.", max 1000) + primary "Send offer" (`to: "offer", offer`).
  - `offer` → "Waiting for an answer to the offer" + the offer quote.
  - final → "Application finished" + end text (confirmed "They accepted your offer.", rejected "This application is closed.", declined "They declined your invitation.") + the candidate's feedback + feedback form (to the candidate / to the Jinder team) or "You sent feedback on {date}. Thank you."
- Two columns: panel "Talent profile": **identity box** — shared → green box (user-check) name + email + "They agreed to share this for the interview."; else → "Anonymous" + "They can share their name and email when they choose an interview time."; their note ("Their note"); the profile rows of the snapshot (`talentProfileHtml`, see screen 22). Side panel "Skills for this job": "{c}% skills covered · {m} of {n} skills" + `skillMatchHtml(skills, { you: false })` + hint "This shows skills only. Use your own judgement for the decision."
- **Skill by skill table** (`skill-table`, full width under the two columns): when the job has skill levels (`skillRequirements` from `GET /recruiter/jobs/:id`) and the snapshot has `skillLevels`, the side box shows the coverage line and a text count, and the table shows the result for each skill (see screen 22). The snapshot of an old application has no `level`, `skillLevels`, `certifications` or `awards`; then these rows are left out and the old list stays.
- Panel "History" (`historyHtml(history, { you: "recruiter" })`).

**21. Talent (anonymous list) — `/candidates?jobId=&view=&page=&pageSize=&sort=` — Feature 5**
- h1 "Talent", sub-line "Anonymous talent matched to your jobs, skill by skill. No names, photos or nationality."
- Load `recruiter.jobs.list({ pageSize: 50 })`, `recruiter.candidates.list({ jobId, view, page, pageSize, sort })`, `entitlements.get()`. No job → empty state "Post a job first. Then we show talent whose skills fit it." + "Post a job".
- Toolbar (`list-toolbar`): "Job" `<select>` (all own jobs; closed ones end with " (closed)") → navigate; a text link **"Job overview"** (→ `#/my-jobs/{jobId}/overview`); tabs All / Saved; the **sort select** (`#talent-sort`: **Best fit for this job** `best` (default) and **Recently updated** `updated`). Line "Required skills:" + neutral chips.
- Card (`.cand-card`, 2 columns): alias link → `#/candidates/{id}?jobId=`, green chip link "In your pipeline" (→ `#/review/{applicationId}`) when there is an application; a **facts row** (`.cand-facts`): the **level** chip (blue, only when known), the years (the exact `yearsExperience` when known, else the band) and "Updated {n} days ago" (`.cand-updated`; "Updated today"); roles and up to 2 locations; up to 6 skill chips **with the level as text** ("Python · Advanced"; green when the job asks for it, with a hidden "(the job asks for this skill)"; the skills that the job asks for come first) + "+N more"; then up to 3 chips for **certifications and awards together** (`.cand-creds`, `.cred-chip`: a graduation icon is a certification, a star icon is an award, a hidden word "Certification:" or "Award:"; **names and years only**, for example "AWS Certified Cloud Practitioner (2024)") and "+N more"; actions: "Save"/"Saved" (`aria-pressed`, bookmark), "Not for this job" (→ `skip`, the card becomes a dashed "{alias} is hidden for your jobs."), "Report", "Invite" (+ a gold lock badge on Basic; hidden when in the pipeline) and the **compare control**. Right: coverage mini meter. **No score on the card.**
- **Compare control:** a Premium employer has a check box "Compare" on each card (`input[data-compare-pick]`; label "Compare" + the hidden alias). A tick calls `compareStore.add("talent", { id, alias, jobId })`; the `jobId` is a hint for the Compare page. The 6th is refused: the check box is cleared, a visible note (`[data-compare-note]`, `role="status"`) and the live region say "You can compare up to 5 profiles." The check boxes follow the basket (event `jinder:compare-change`). A Basic employer has a ghost button with a static lock badge (`data-premium-lock="Comparing talent"`); Invite has the same (`data-premium-lock="Inviting talent who did not apply"`); each opens the "Premium feature" dialog.
- The panel has a heading (`h2#talentListTitle`, `sr-only`, `tabindex="-1"`), the list and the **pager** (list names `talent` and `talent-saved`). A page, size or sort change draws the list in place (history `pushState`, no screen flash); after a page change the live region says "Page 2 of 5. Showing 11 to 20 of 47 talent profiles." and the focus goes to the heading; after a sort change "Sorted by recently updated. Page 1 of …". An old answer that comes late is dropped. An error shows the message and a "Try again" button.
- Under the list: if `limitedTo` and `total > limitedTo` (a **Basic** employer sees **5 cards and no pager**) → the gold upgrade box "You see the top {N} of {total} talent profiles. Premium shows all of them."; if `skippedCount` → "{n} hidden profile(s). Show them again" (→ `clearSkipped`, reload).
- **Invite (Premium):** dialog "Invite {alias}", intro "They get your message in Jinder. They stay anonymous until they agree to share their identity.", "Job" select (own jobs that are not closed), text area "Message" (hint "10 to 500 characters. Do not add email addresses or phone numbers.", max 500), "Send invitation" → `contact(id, { jobId, message })`. On Basic, Invite and Compare open a dialog "Premium feature" ("{feature} is part of Premium. In this demo you can switch your plan in Settings.", "Go to Settings" → `#/settings?section=plan`).

**22. Talent detail — `/candidates/:id?jobId=`**
- Back link "Talent"; h1 alias; sub-line "Anonymous profile · matched to {job}" and "Updated {n} days ago"; actions: secondary Save/Saved, primary "Review application" (when in the pipeline) or "Invite" (Premium gate), a **Compare toggle** (Premium: `[data-compare-toggle]`, `aria-pressed`, text "Add to compare" / "In compare list") or a lock badge (Basic), ghost "Report".
- Two columns: panel "Profile" (`talentProfileHtml`: rows Level, Experience (exact years or band), Roles, Skills (chips with the level as text; green when the job asks for it; plus "needs Proficient" (`.chip-need`) when the job lists a level), **Certifications**, **Awards** (names and years only, no issuer), Qualifications, Domains, Target roles, Locations, Work types; a row is left out when the answer has no such key; a `null` shows "Not given"; plus a hint with shield "Name, contact details, photo, nationality and the CV are never shown. They decide when to share their identity.") and a side panel "Skills for {job}" (coverage line + a text count, and the skill table below). Invite success → `/review/{new application id}`.
- **Skill by skill table** (`skill-table`, class `skills-wide`; full width): columns **Skill**, **Job needs** ("Advanced · Must have" or "Nice to have"), **Talent** (the level as text, or "—") and **Result**. The result is an icon and a word, and the cell has a tint: **Meets** (check, green), **Below** (alert, gold pair with contrast 4.5:1 or more), **Missing** (x, rose), **Related** (target, blue, "via {skill}"), or **Has it** when the talent has the skill but the level is not known. The browser works the result out from three API values: the status of the skill (`match.skills`), the levels of the talent (`skillLevels`) and the levels of the job (`GET /recruiter/jobs/:id`, key `skillRequirements`). There is no number and no score. The table shows only when the job has `skillRequirements` and the talent has `skillLevels`; otherwise the old `skill-match` list stays.
- **Privacy:** the screen shows only keys of the shared profile. The issuer of a certification is not shown (names and years only). A test scans the employer pages for e-mail text, the words "score", "nationality:", "visa status:", "date of birth", "gender:" and for the words candidate, recruiter and HR.

**23. Compare — `/compare?ids=a,b,c,d,e&jobId=` (`views/compare.js`, both roles; real backend only)** — replaces the old "compare 3 jobs" and "compare two profiles" screens. The page is a full page in the shell; the menu item "Compare" is the current item. It decides by the role: a **talent** compares 2 to 5 **jobs** (free, `api.jobs.compare(ids)`); an **employer** compares 2 to 5 **talent profiles for one chosen job** (Premium, `api.recruiter.compare(ids, jobId)`). **There is no total score and no ranking of people anywhere.** Every chart has a table with the same numbers.
- **Items and address.** The ids come from `?ids=` in the address, else from the basket (`compareStore`, kind `job` or `talent`). The page and the basket stay in step: a change on the page (add, remove, clear, the picker) writes the basket and the address with `history.replaceState` (no router run, no history entry). If the address has ids, the basket is **replaced** by them. More than 5 ids: the page uses the first 5 and says "You chose 7 jobs. You can compare up to 5, so this page uses the first 5." The titles come from the answer and are written to the basket.
- **Header:** h1 "Compare jobs" / "Compare talent", a sub-line (talent: "Put 2 to 5 jobs side by side. See how each job fits you, skill by skill. There is no total score: you decide."; employer: "Put 2 to 5 anonymous profiles side by side for one of your jobs, skill by skill. There is no total score and no ranking of people."), a count text ("3 of 5 chosen"; at 5: "5 of 5 chosen. That is the most you can compare."), ghost "Clear all" and primary **"Add to compare"** (disabled at 5). The employer page has the select **"For which job?"** (`#cmpJob`): the own jobs that are not closed (`api.recruiter.jobs.list({ pageSize: 50 })`; a closed job only if `?jobId=` names it, marked "(closed)"). Default: `?jobId=` if it is an own job, else the last used job (`sessionStorage` key `jinder.compare.lastJob.{userId}`), else the first open job. A change writes the address and loads again.
- **Cards** (`ul.cmp-cards`): a swatch (the line style of the item in the chart), the title (link to `#/jobs/:id`) or alias (link to `#/candidates/:id?jobId=`), a Remove button (`aria-label="Remove {title} from compare"`), and facts. Job: company and place, a "Closed" chip, Level, Experience, Work mode, Salary (middle) (`salaryMidpoint`), "View job"; an empty value shows a dash and the hidden text "Not listed". Talent: Level, Experience, Roles (first 2), "Skills for this job" ("5 of 6 skills + 1 related"), "View profile for this job".
- **Talent page panels:** (1) **"How each job fits you"** (`#cmpFit`): ONE radar with a series for each job on the axes that all jobs have, and the numbers table (the formula tag F1, F2 or F5 after the axis name; one decimal; the best value of a row has the text "Highest", no mark when all are equal). (2) **"Skills side by side"** (`#cmpSkills`): rows from `skillMatrix`; the first column has the skill and "You: Advanced (4)" or "You: —"; each cell has an icon and a word (**Meets**: your level is the same or higher, **Below**, **Missing**: `yours` is `null`; a related skill does not count) and "Needs Proficient (3) · Must have" or "Nice to have"; a job that does not ask for the skill says "Not asked"; the footer row "Skills you meet" ("2 of 5 skills"). (3) **"Details"** (`#cmpDetails`): Level, Specialisation, Experience, Work mode, Job type, Salary, Salary (middle), Education, Certifications required, Certifications preferred, Preferred awards; a row that no job has is hidden. (4) **"How close the jobs are to each other"** (`#cmpPairs`): a matrix of jobs by jobs with the Formula 3 number (one decimal) and the tier word ("Same job" on the diagonal, "No result" when a pair is missing), and under it one `details` for each pair (the parts, "Advice", "Salary change, from the first job to the second").
- **Employer page panels:** (1) **"Profiles on the same axes"** (`#cmpRadar`): ONE radar with a series for each profile (named by the alias) and the numbers table; after each axis name a small note ("merit model" for F4, "fit to the job" for F6, "from the skills table"); no "Highest" mark and no sort by value. The axes are the ones that the API sends (up to 9: Skills for this job, Requirement fit, Seniority fit, **Certification readiness**, Skill depth, Experience, Transferable skills, Level standing, Evidence). (2) **"Skills side by side"**: rows are the skills of the job; the first column has the skill and "Job needs: Proficient (3) · Must have"; each cell has an icon and a word (**Meets**, **Below**, **Related**, **Missing**) and "Level: Advanced (4)", "Related via {skill}" or "No level"; a row "Other skills" (up to 8 names and "+N more") and the footer "Skills that meet the job". (3) **"Qualifications and recognition"** (`#cmpQuals`): rows Qualifications, Certifications and Awards; names and years only ("Name (2023)"); no issuer; "None listed" when empty. (4) **"Where the profiles differ"** (`#cmpAreas`): rows are the `areas` (up to 8); a cell says "1st", "2nd", … (the position inside that one area); profiles with the same position also say "Equal"; if all profiles have the same position, every cell says "Equal". Muted line: "One area at a time. 1st is the highest place in that area. Jinder does not add the areas up and does not rank people. You decide."
- **The picker:** the button "Add to compare" (also "Choose jobs" in the empty state) opens a dialog (`openModal`, class `cmp-picker-dialog`) "Choose jobs to compare" / "Choose talent to compare". It works on a copy; "Done" puts the choice into the basket and the address and loads again; "Cancel", the X and Esc close it without a change. Parts: tabs (`role="tablist"`, arrow keys, Home and End), a search box, a count line (`aria-live="polite"`: "3 of 5 chosen. You can choose more."), the list "Chosen now" (chips with a remove button) and the list with check boxes + "Show more". At 5 chosen, the other check boxes are disabled. A row has a check box, the title, short facts and the chip "Chosen"; a closed job has a rose "Closed" chip. **Talent tabs:** "Saved jobs" (`api.bookmarks.list`, sort `saved`) and "Recommended" (`api.jobs.recommended`, sort `best`); the search box searches all jobs with `api.jobs.search` (after 300 ms, at least 2 characters). **Employer tabs:** "Talent for this job" (`api.recruiter.candidates.list`, `view: "all"`, sort `best`, 50 rows a page) and "Saved talent"; the search box filters the loaded rows by alias; a row shows alias, roles, level, years and "5 of 6 skills" and **no score**.
- **States:** loading "Comparing jobs…" (employer: "Comparing profiles…", `role="status"`); updating (the old result stays, dimmed, with `aria-busy`, and the note "Updating the comparison…"); fewer than 2 items (`.cmp-empty`: "Choose at least 2 jobs to compare" / "talent profiles", the chosen item, a button "Choose jobs"; the picker opens when the user arrives; no request is sent); error 404 (`.cmp-error`, `role="alert"`: the API message "This job does not exist or was removed." and a Remove button for each chosen item. The page reads the list `missing` of the error (`ApiError.missing`): the items that it names are listed first, have a rose chip "Not found" (`.cmp-fix-flag`) and are named in the message: "These jobs are not there any more: {titles}. Remove them, then try again."; without `missing` the message says "Remove the job that is not there any more, then try again."); error 400 (the message `fields.ids`; items in `missing` have the chip "Over the limit"); other errors (the message and "Try again"); no open job (employer): "You have no open job" + "Post a job".
- **Locked page (a Basic employer):** the page makes **no** compare, job or talent request. It shows h1 "Compare talent", a gold lock badge, the headline "Compare 2 to 5 talent profiles side by side" with "This is a Premium feature.", a list of what Compare does, `upgradeHtml("Compare is part of Premium. In this demo you can switch your plan in Settings.")` and a sample picture (`figure.cmp-example`, `aria-hidden` table of "Profile A/B/C" and "Skill A/B/C") with the chip "Example" and the text "This picture is a sample. It does not show real people." A 403 `PREMIUM_REQUIRED` during use shows the same page with the line "Your plan does not include Compare now."
- **Accessibility:** every table has a hidden `caption`, `scope="col"` and `scope="row"`, in a scroll region (`div.table-wrap.cmp-scroll[role="region"][tabindex="0"][aria-label="{name}. This table scrolls sideways on a small screen."]`); on narrow screens the tables scroll inside the region, the first column is sticky and the page does not scroll sideways; skill states always have an icon and a word (Meets green, Below gold, Missing rose, Related blue; contrast 4.5:1 or more); `announce()` says "{title} removed from compare. N jobs left.", "N jobs chosen." and "Compare list cleared."; after a remove the focus goes to the Remove button of the next card (or to the Add button). The scroll regions have `position: relative`, because a text with `sr-only` (position absolute) would escape the clip and widen the page.
- In mock mode the compare calls fail with `ApiError(501, "NEEDS_REAL_BACKEND", "Compare jobs needs the real Jinder backend. Start the platform (python start.py) and open the app without ?mock=1.")` ("Compare talent …" for an employer) and the page shows the message in the error panel.

**24. Legal and system text:** do not say "prototype" anywhere in the UI. The legal placeholder notes say "This is placeholder text. …".

### Reference lists (`js/data/reference.js`)

Static, owned by the frontend. The lists of names come from the taxonomy `jinder_backend_engine/data/reference/ict_taxonomy.json` **version 2**: the file starts with the line "from ict_taxonomy.json version 2", and a test compares every list with the taxonomy file. Use the same spelling as the taxonomy. Do not add a name that is not in the taxonomy. Do not add lists for sensitive data. The full file is in the Appendix. Exports:
- `DOMAINS` (3): Software Engineering, AI & Machine Learning, Data. `INDUSTRIES` and `JOB_CATEGORIES` are the old names of the same list. `SPECIALISATIONS`: an object, domain → list (Software Engineering: Backend, Frontend, Full-stack, Mobile, Platform and DevOps, Quality engineering, Security engineering, Software architecture; AI & Machine Learning: Machine learning engineering, Generative AI and LLM, Computer vision, Natural language processing, MLOps, Applied science and research; Data: Data engineering, Data analytics, Analytics engineering, Business intelligence, Data science, Business analysis).
- `LEVELS`, `SKILL_LEVELS` and `WORK_MODES` are written in `data/levels.js` and exported here too.
- `CITIES` (also `LOCATIONS`): Sydney, Melbourne, Brisbane, Perth, Adelaide, Canberra, Remote. `WORK_TYPES`: Full-time, Part-time, Contract, Graduate / Internship.
- `YEARS`: Less than 1 year, 1–2 years, 3–5 years, 6–10 years, More than 10 years.
- `QUALIFICATIONS` (12): High school … Doctorate (PhD). `FIELDS_OF_STUDY` (12). `COUNTRIES` (41). `ROLES` (53 job titles, with no level word: the level is separate).
- `CERTIFICATIONS` (38 items `{ name, issuer, domains, tier }`). `AWARD_KINDS` (12 items `{ kind, label }`; `kind` is the value that the API stores, for example `hackathon` with the label "Hackathon").
- `SKILL_NAMES` (the 172 skill names of the taxonomy), `SKILL_SUGGESTIONS` (9 names for each domain) and `SKILLS` (the names and the suggestions, unique).
- Every industry, role and field of study of another field of work is gone from this file.

`config.js` demo values: `MOCK_DEMO_DATA: true`, `MOCK_DEMO_ACCOUNTS: [{ label: "Talent demo (Teal Heron)", email: "candidate@demo.jinder.app" }, { label: "Employer demo (Bluebushworks)", email: "recruiter@demo.jinder.app" }]`, `MOCK_DEMO_PASSWORD: "demo1234"`. These are made-up demo accounts, not secrets. They are used only in mock mode.

## API contract (frontend ↔ backend)

The backend developer implements this contract. The mock adapter implements it in the browser. **When you add or change an endpoint, update this section in the same task** (AI_Rule.md Rule 10).

### Conventions

- Base URL: `CONFIG.API_BASE_URL` (default `/api`, the same address as the app; the real backend in `jinder_platform` serves both). JSON request and response bodies (`Content-Type: application/json`).
- Auth: `Authorization: Bearer {token}` on every request after sign-in. The token comes from `POST /auth/login`.
- Dates: ISO 8601 strings (`2026-10-04T03:45:04Z`).
- Errors: HTTP status + body `{ "error": { "code": "…", "message": "…", "fields": { "name": "message" }, "suggestion": "…" } }`. `message` is shown to the user, so it must be plain English. `fields` is for `VALIDATION_ERROR` and `ALIAS_TAKEN`. `suggestion` is only for `ALIAS_TAKEN` (a free alias). `ApiError` has `status, code, message, fields, suggestion`.
- **The key `missing` (compare only).** The two compare endpoints add a list next to `error` that names the ids that cannot be compared: `{ "error": { "code", "message", "fields": { "ids": "…" } }, "missing": [ids] }`. For an unknown id: 404 and `missing` has the unknown ids. For a wrong number of ids: 400 and `missing` has the ids above the limit (it is `[]` when there are too few). A good answer has no `missing`. `error.code` and `error.message` are the same as for other errors. The current frontend does not read `missing`.
- **Lists: page and sort.** Every list endpoint takes `page` (from 1, default 1), `pageSize` (1 to 50, default 10; the frontend offers 10, 20 and 50) and `sort`. The answer keeps the old list key (`items`) and adds `page: Page` and `sort`. `Page = { page, pageSize, total, totalPages }`. A bad `page` gives page 1; a page above the last page gives the last page (`page.page` tells which); a bad `pageSize` gives 10 (a number is set to 1–50); a bad `sort` is a **400** with `fields.sort` ("Use one of these: best, newest."). Equal values are ordered by `id`, so a list never changes order between two requests. An empty list has one empty page (`totalPages` 1). **`limit` is removed** from these endpoints (the server ignores it): use `pageSize`.

| Status | Code | When |
|---|---|---|
| 400 | `VALIDATION_ERROR` | A field is missing or not valid (`fields` lists them) |
| 401 | `INVALID_CREDENTIALS` | Wrong email or password (login only). Message: "Incorrect email or password." |
| 401 | `UNAUTHORIZED` | No token, or the session ended. The frontend sends the user to sign in |
| 403 | `FORBIDDEN` | The user's role cannot do this |
| 403 | `PREMIUM_REQUIRED` | The feature needs Premium. Message: "This feature is part of Premium. Upgrade in Settings to use it." |
| 404 | `NOT_FOUND` | The item or endpoint does not exist |
| 409 | `ALIAS_TAKEN` | The alias is used by another candidate (case-insensitive). `fields.alias` + `suggestion` |
| 409 | `CONFLICT` | The action conflicts with the current state (for example a closed job, a second application, a status change that is not allowed). `message` says why |
| 429 | `RATE_LIMITED` | Too many failed sign-ins. Message: "Too many sign-in attempts. Try again in a few minutes." |
| 413 · 503 · 500 | `TOO_LARGE` · `BUSY` · `INTERNAL` | The request is too large · the database is busy · an unexpected error (no stack trace in the body) |
| 501 | `NEEDS_REAL_BACKEND` | Frontend only: a feature that only the real backend has (Compare) was used in mock mode. `ApiError(501, "NEEDS_REAL_BACKEND", "Compare jobs needs the real Jinder backend. …")` |
| 0 | `NETWORK_ERROR` | Frontend only: the server cannot be reached |

### Data models

```ts
type Role = "candidate" | "recruiter";

interface User {               // GET /me. Never includes the password hash.
  id: string;
  role: Role;
  name: string;
  email: string;
  company: string | null;      // recruiters only
  alias: string | null;        // candidates only, always set (chosen, or "Colour Animal" from the system). Unique, case-insensitive
  profile: Profile | null;     // candidates only
  cv: CvRecord | null;         // candidates only
  onboarding: "done" | "dismissed" | null;
  createdAt: string;
}

interface Profile {            // all lists; older data may have a string — read with toList()
  qualification: string[]; fieldOfStudy: string[]; studyCountry: string[];
  currentRole: string[];
  industry: string[];          // DOMAINS: "Software Engineering" | "AI & Machine Learning" | "Data". Any other value is dropped when the profile is saved. The UI word is "Domain"
  years: string;               // the band, "Less than 1 year" … "More than 10 years". It is set from yearsExperience when that is a number (under 1, under 3, under 6, up to 10, above 10)
  yearsExperience: number | null;   // exact years, 0 to 40, one decimal (6.57 → 6.6). Any other value (text, a boolean, 41, -1) becomes null
  level: "" | "Intern" | "Junior" | "Mid" | "Senior" | "Lead" | "Principal";   // any other value becomes ""
  specialisation: string;      // one of the 20 specialisations of the taxonomy, else ""
  workModes: ("Onsite" | "Hybrid" | "Remote")[];
  certifications: { name: string; issuer: string; year: number | null }[];   // at most 20; name required (≤ 120); issuer ≤ 120 or ""; year 1990 to next year, else null; a copy is dropped; text goes through scrubContact
  awards: { name: string; kind: string; year: number | null }[];             // at most 20; kind = an award kind of the taxonomy (the slug "hackathon" or the label "Hackathon" is accepted, the slug is stored), else ""
  skills: string[]; targetRole: string[]; targetIndustries: string[];   // targetIndustries holds domains too
  locations: string[]; workTypes: string[];
  translation: TranslatedSkill[];   // the candidate's decisions (Feature 2)
  evidence: string[];          // CV evidence lines. PRIVATE: never in a recruiter response
}

interface CvRecord { name: string; size: number; addedAt: string; }

interface TranslatedSkill {
  id: string;                  // stable: "{mapped-slug}--{original-slug}" (AQF: "aqf--{slug}")
  source: "role" | "skill" | "qualification";
  original: string;            // what the candidate wrote; "A; B" when two sources map to the same skill
  mapped: string;              // the Australian skill (or the AQF level)
  kind: "cross-border" | "cross-industry" | "direct";
  anzsco: string; occupation: string;   // for some role mappings, else ""
  reason: string;              // plain language
  evidence: "Strong" | "Moderate" | "Limited";
  evidenceText: string;        // a CV line, or ""
  status: "suggested" | "accepted" | "edited" | "removed";   // only accepted and edited are shared
  level: 1 | 2 | 3 | 4 | 5 | null;   // the skill level (1 Beginner, 2 Working, 3 Proficient, 4 Advanced, 5 Expert). Skill cards only; a role or qualification card has null. Text ("4"), 2.5, 0, 6 and booleans become null
  years?: number | null;       // the years that the talent used the skill (0 to 40, one decimal). Skill cards only
}
// A skill with no level of its own gets the level of its evidence in the shared profile (rule F8): Strong 4, Moderate 3, Limited 2.
// A role card is not a skill: the shared `skills` list has skill cards only. A role card gives `roles` (title and ANZSCO code).
// POST /profile/translate keeps the level and the years that the talent set, and the decisions. A new card has level null.

interface ParseResult {        // GET /cv/parse/:id when status is "done"
  fields: Partial<Profile>;    // only the detected fields. Old keys: qualification, fieldOfStudy, studyCountry, currentRole, industry (domains only, at most 2, the strongest first), years, skills (names). New keys: targetRole (a list of roles of the role list), level, yearsExperience, certifications, awards
  detected: string[];          // field names the AI filled ("AI-detected"): the keys of fields
  missing: string[];           // only the OLD field names that the CV did not have ("Missing"). The new keys are never here: use `found`
  evidence: string[];
  // version 2, plain values for the UI. A field that the CV does not show is empty ("", [], null): the reader does not guess
  currentRole: string; targetRole: string; level: string;   // "Senior Data Engineer" | "Data Engineer" | "Senior", or ""
  yearsExperience: number | null;
  certifications: Profile["certifications"]; awards: Profile["awards"];
  skills: { name: string; level: number | null }[];   // level 1 to 5, or null when the CV gives no evidence. fields.skills is the list of the names only
  found: { currentRole: boolean; targetRole: boolean; level: boolean; yearsExperience: boolean; certifications: boolean; awards: boolean };   // for the "Not found" hints
  sources: Record<string, string>;   // how each value was found (the name of the rule). For tests and hints
  domain: string;              // the first domain of fields.industry, or ""
  sampleLabel?: string;        // mock only, for the "Demo mode" banner
}

interface SharedProfile {      // GET /me/shared-profile — exactly what recruiters see (allowlist)
  alias: string;
  roles: { title: string; anzsco: string }[];   // from accepted role mappings with a code
  skills: string[];            // accepted + edited, not qualifications, unique
  qualifications: string[];    // accepted AQF levels
  fieldsOfStudy: string[]; industries: string[];   // industries = the domains
  years: string | null;        // the band
  targetRoles: string[]; locations: string[]; workTypes: string[];
  // version 2 (real backend). A snapshot of an application made before version 2 does not have these keys
  level: string | null;        // Intern … Principal
  yearsExperience: number | null;   // the exact years rounded to 0.5 (6.6 → 6.5)
  skillLevels: { name: string; level: number; years: number | null }[];   // one for each name in `skills`, same order; a skill with no level of its own gets the level of its evidence
  specialisation: string | null; workModes: string[];
  certifications: { name: string; issuer: string; year: number | null }[];   // shared AT ONCE, no accept step (decision D5). The screens show names and years only
  awards: { name: string; kind: string; year: number | null }[];             // the same
  updatedAt: string | null;    // the time of the last save of the profile ("Updated N days ago", sort "Recently updated")
  // NEVER: name, email, contact details, photo, nationality, country of study, employer names, CV, evidence
}

interface Job {                // the card fields. All job data is internal Jinder data.
  id: string;                  // internal id, e.g. "job-5906848725"
  title: string; company: string;
  category: string;            // the DOMAIN: "Software Engineering" | "AI & Machine Learning" | "Data" (the API key stays `category`; the UI word is "Domain")
  location: string;            // city or "Remote"
  area: string;                // full location text, e.g. "Sydney NSW"
  type: string;                // "Full-time", …
  anzsco: string; occupation: string;   // "261313", "Software Engineer" (a demo mapping from the taxonomy, not checked against the official ANZSCO list)
  salary: string;              // display text, e.g. "$150,000 – $170,000 per year", "$900 per day" or "Market competitive"
  salaryUnit: "year" | "day" | "hour";   // the unit of the numbers behind `salary`. The numbers (salaryMin, salaryMax) stay private. The platform never converts; only the formula engine turns a day or hour rate into a yearly pay
  postedAt: string | null; closesAt: string | null;
  status: "open" | "closed";
  summary: string;             // at most 200 characters: the first whole sentences; ends with "…" only if the first sentence alone is longer. Headings and bullets are left out
  // version 2 facts. A job without a value has null / [] / { required: [], preferred: [] } / { preferred: [] }. The API never invents a value
  level: "Intern" | "Junior" | "Mid" | "Senior" | "Lead" | "Principal" | null;
  specialisation: string | null;   // e.g. "Backend", "Data engineering". It must belong to the domain
  minYears: number | null; maxYears: number | null;   // the experience that the job asks for. A minimum with no maximum means "or more"
  workMode: "Onsite" | "Hybrid" | "Remote" | null;
  educationMin: string | null; // e.g. "Bachelor's degree"
  skillRequirements: { name: string; level: number; must: boolean }[];   // level 1 to 5. Empty for a job with no skill levels: then use `skills` (level 3, must)
  certifications: { required: string[]; preferred: string[] };
  awards: { preferred: string[] };   // award kinds of the taxonomy (slugs, e.g. "hackathon")
  skills: string[];            // the names of the skills that the job asks for (the same names as skillRequirements)
  match: JobMatch;             // for the signed-in candidate
  bookmarked: boolean;         // for the signed-in candidate
  skipped: boolean;            // the candidate chose "Not for me"
  applicationId: string | null;   // the candidate's application for this job
}

interface SkillResult {        // one required skill of a job, against one person's skills (real backend: from the formula, with levels)
  name: string;                // the job's skill
  status: "match" | "partial" | "gap";   // meets → match, below → partial, related → partial, missing → gap
  fitStatus?: "meets" | "below" | "related" | "missing";   // the word of the formula. Use it when you need the level difference
  required?: number;           // the level that the job asks for (1 to 5)
  level?: number | null;       // the level of the person (1 to 5). null if the person does not have the skill (also for "related")
  must?: boolean;              // true for a must-have skill
  via?: string;                // related: the name of the related skill that the person has
  reason: string;              // "Has this skill." / "Has {via}, which is related." / "No evidence of this skill yet."
}

interface JobMatch {           // decision Q1: per-skill result + coverage. Computed by the backend
  coverage: number | null;     // mock: round((matches + 0.5 × partials) / required skills × 100). Real backend: the level-aware skill coverage of the formula, rounded to a whole number. null if the job has no skills
  skills: SkillResult[];       // in the order of job.skills
  matchedSkills: string[]; partialSkills: string[];
  gaps: string[];              // skills with status "gap"
  reasons: string[];           // plain-language reasons
  notes: string[];             // for example "This role is Full-time", "Location: Sydney"
  rank: number;                // ordering only; never shown as a number
  score?: number;              // real backend only: the Fit score with one decimal (0 to 100) = round(0.55 × fit + 0.45 × FRS*, 1). Shown as "Fit score". The same number in a list and on the page of the job
  recommended: boolean;        // true if the job is good enough to recommend (real backend: score is 45 or more)
}

type AppStatus = "applied" | "contacted" | "review" | "interview" | "accepted" | "offer" | "confirmed" | "rejected" | "declined";
// Labels: Applied, Contacted, In review, Interview, Accepted, Offer, Confirmed, Not selected, Declined
// FINAL = confirmed, rejected, declined

interface Application {        // candidate view: GET /applications/:id
  id: string; jobId: string;
  job: { id, title, company, location, area, type, status: "open" | "closed", skills: string[], ownedOnJinder: boolean };
  origin: "applied" | "contacted";      // contacted = a recruiter invited the candidate (Premium)
  status: AppStatus; statusLabel: string;
  note: string;                // ≤ 500, contact details removed by the API
  canEdit: boolean;            // status is "applied"
  final: boolean;
  history: { status: AppStatus; at: string; by: "candidate" | "recruiter" | "system"; note: string }[];
  slots: { id: string; start: string }[];   // 1–3 interview times
  chosenSlotId: string | null; slotConfirmed: boolean;
  identityShared: boolean;     // the candidate agreed to share name + email (when choosing a slot)
  offer: { text: string; sentAt: string } | null;
  snapshot: SharedProfile;     // frozen copy of the shared profile when applying. Never the CV
  match: { coverage: number | null; skills: SkillResult[] };   // against the snapshot
  feedback: { mine: { toOther, toTeam, at } | null; theirs: { toOther, at } | null };   // never the other side's toTeam
  createdAt: string; updatedAt: string;
}

interface ApplicationListItem { id, job, status, statusLabel, origin, final, coverage, createdAt, updatedAt, needsAction: boolean }
// needsAction: interview without a chosen slot, offer, contacted, or final without the candidate's feedback

interface RecruiterApplication {   // GET /recruiter/applications/:id — like Application, plus:
  identity: { name: string; email: string } | null;   // ONLY when identityShared is true
  allowedNext: AppStatus[];    // the state machine (below); "accepted" only after the slot is confirmed
  canConfirmSlot: boolean;     // interview + chosen slot + not confirmed
  // no canEdit; feedback.mine = the recruiter's, feedback.theirs = the candidate's toOther
}

interface RecruiterJob {       // GET /recruiter/jobs, /recruiter/jobs/:id, POST, PATCH
  id, title, category /* a domain */, location, type, salary, salaryUnit, postedAt, closesAt, skills: string[], targetApplicants: number,
  level, specialisation, minYears, maxYears, workMode, educationMin, skillRequirements, certifications, awards,   // the same keys as Job (version 2)
  applicantCount: number;      // origin "applied"
  contactedCount: number; awaitingCount: number;   // awaiting = applied, review, or a chosen slot to confirm (contacted waits for the candidate)
  badge: "open" | "closing" | "closed"; label: "Open" | "Closes in {n} days" | "Closes in 1 day" | "Closed"; daysLeft: number;
  description?: string;        // detail and edit only: the full text, never cut (up to 10,000 characters). Also `summary` and `company`
}

interface CandidateCard {      // GET /recruiter/candidates — allowlist only
  id, alias, roles, skills, qualifications, years, industries, locations,
  coverage: number | null; matched: number; partial: number; total: number;   // against the chosen job
  saved: boolean; applicationId: string | null;    // an application of this candidate to the chosen job
  // version 2 (from the shared profile only; no score on the person)
  level: string | null; yearsExperience: number | null; certifications: SharedProfile["certifications"]; awards: SharedProfile["awards"];
  skillLevels: SharedProfile["skillLevels"]; updatedAt: string | null;
}

interface Notification { id, type, title, body, link /* an app path, e.g. "/applications/{id}" */, email: boolean, read: boolean, createdAt }
// types: new_application, interview_slots, slot_chosen, slot_confirmed, result, offer, offer_reply, status, feedback, contacted, contact_declined, job_edited

interface Entitlements { plan: "basic" | "premium"; topN: number | null; canContact: boolean; canCompare: boolean; advancedCharts: boolean;
  crown: boolean;              // true when the plan is Premium (the crown and the gold ring in the menu)
  compareMax: number;          // 5, for both roles
  benefits?: { key: string; label: string; description: string; available: boolean; used: boolean; usedCount: number }[];   // real backend only
}
// recruiter basic: topN 5; recruiter premium: topN null + contact + compare; advancedCharts = premium (both roles). canCompare stays employer-only: a talent compares jobs for free
// benefits: `available` = the plan allows it (Premium). `used` = the user did it at least once. `usedCount` = how many times. A user who goes back to Basic keeps used and usedCount; available becomes false. A user sees only their own counts.
//   employer keys: all_talent ("See every talent profile, not only the top 5"; event talent_list_full), invite ("Invite talent to apply"; invite), compare ("Compare up to 5 talent profiles"; compare_view), advanced_charts ("Pipeline by stage and interest per job"; advanced_charts_view)
//   talent keys: skills_to_learn ("Skills to learn next"), skill_demand ("Demand for your skills"); both use the event insights_view, so they change together
// The mock has no `benefits` (it adds crown and compareMax only). Settings then shows the old plan section.

interface JobDetail extends Job {
  description: string;         // full text
  similar: (Job & { similarity?: { index: number; tier: string; salaryChange: string | null } })[];   // up to 3 open jobs, closest first (Formula 3). similarity: real backend only
  bridge?: Bridge | null;      // the talent's own path to this job (Formulas 1 and 2). Real backend only. Never sent to an employer. null when the talent has no profile
}
// GET /recruiter/jobs/:id (the own job) has the same job keys and `description`, but no bridge.

interface Bridge {
  score?: number;              // the same as JobMatch.score
  axes?: { key: string; label: string; formula: "F1" | "F2" | "F5"; value: number }[];   // "How this job fits you": 8 radar values, 0 to 100, in this order: occupation, skills, methods, readiness, capability, pay, location, freshness. Not changed in version 2
  occupation: { anzsco: string; title: string; alignment: number; tier: string; tierCode: string };   // tier: "Direct Industry Alignment" | "Transferable Cross-Sector Capability" | "Emerging Career Bridge"
  readiness: { gapSeverity: number; readiness: number; months: number; tier: string; tierCode: string; statutoryBlocker: boolean };   // statutoryBlocker is always false (the legal block of AHPRA and CPA is gone). months can be 0 when the job has no gaps
  gaps: { name: string; category: "CAT-1" | "CAT-2" | "CAT-3" | "CAT-4"; categoryName: string; months: number; blocker: boolean }[];   // kept for compatibility. CAT-1 certification, CAT-2 required skill, CAT-3 nice-to-have skill, CAT-4 experience or level. blocker is always false
  path: Path;                  // "Your path to this job". NEW in version 2
  // projection (the 12-month chart) is REMOVED
}

interface Path {               // Formula 2, evaluate_path. Plain JSON
  axes: { key: string; label: string; group: string; required: number; have: number; status: "fit" | "above" | "gap" }[];
  //  the skill groups: languages, frameworks, cloud, data, ml, practices, collab (labels: Languages, Frameworks & libraries, Cloud & DevOps, Data & storage, ML & AI, Engineering practices, Collaboration)
  //  plus the axes "experience", "level" and "certifications" (only when the job lists a certification); for these three `group` has the same text as `key`
  //  required and have are 0 to 100. For a skill group: the mean of (level ÷ 5 × 100) over the job's skills in that group, weighted by must (2×) and rarity; have uses min(have, 5) ÷ 5 × 100.
  //  status: "above" when have is 15 points or more over required, "fit" when have ≥ required, else "gap"
  fit: { kind: "skill" | "experience" | "level" | "certification" | "award"; label: string; have: string; need: string; note: string }[];
  gaps: { kind: "missing" | "below_level" | "experience" | "level" | "certification"; label: string; have: string; need: string; months: number; must: boolean; note: string }[];
  summary: { fitCount: number; gapCount: number; monthsToClose: number; readinessTier: string };
  // have and need are plain words: "Advanced", "Proficient", "none", "2 years or more". months of a skill gap come from the taxonomy (monthsToLearn), the level difference and a learner factor. Gaps close in parallel: monthsToClose = the largest + 0.18 × the rest
}

interface Page { page: number; pageSize: number; total: number; totalPages: number; }   // in every list answer, next to `items` and `sort`

interface CompareJobs {        // GET /jobs/compare?ids=a,b,c,d,e (talent, free; 2 to 5 ids)
  jobs: (Job & { axes: { key: string; label: string; formula: string; value: number }[]; salaryMidpoint: number })[];   // the job card + the 8 radar values for this talent + the yearly middle of the pay
  axes: { key: string; label: string; formula: string }[];
  pairs: { a: string; b: string; index: number; tier: string; advice: string; salaryChange: string; parts: { key: string; label: string; value: number | null }[] }[];   // Formula 3 for each pair of jobs (1, 3, 6 or 10). `parts` has 6 parts; the sixth is `level`
  skillMatrix: { skill: string; yours: number | null; byJob: Record<string, { required: number; must: boolean } | null> }[];   // one row for each skill that at least one job asks for, in the order of first appearance. yours = the talent's level 1 to 5, or null (a related skill does not count); a talent skill with no card is level 3. A job without skill levels gives { required: 3, must: true }; a job that does not ask for the skill gives null
}

interface CompareTalent {      // GET /recruiter/compare?ids=a,b,c,d,e&jobId= (employer, PREMIUM; 2 to 5 ids; jobId is one of the employer's own jobs)
  job: { id: string; title: string; skills: string[] };
  candidates: { id: string; alias: string; level: string | null; years: string | null; yearsExperience: number | null; roles: SharedProfile["roles"]; qualifications: string[];
                certifications: SharedProfile["certifications"]; awards: SharedProfile["awards"]; coverage: number | null; skills: SkillResult[]; otherSkills: string[] }[];
  radar: { axes: { key: string; label: string; formula: "skills" | "F4" | "F6" }[]; series: { id: string; alias: string; values: number[] }[] };
  //  up to 9 axes, each 0 to 100: coverage "Skills for this job"; requirement "Requirement fit" (F6); seniority "Seniority fit" (F6); statutory "Certification readiness" (F6; the key stays "statutory");
  //  depth "Skill depth", experience "Experience", transferable "Transferable skills", level "Level standing", evidence "Evidence" (F4). An axis stays only if all profiles have a value for it.
  areas: { area: string; ranks: { id: string; position: number }[] }[];
  //  up to 8 areas: Skill depth, Experience, Level standing, Evidence, Transferable skills, Certifications, Awards, Qualification level (Formula 4). position 1 = the highest.
  //  Profiles within 3 points of the first profile of a group share its position; the next group follows the group before it (90, 89, 70 give 1, 1, 3). Positions are NEVER added up.
  skillMatrix: { skill: string; required: number; must: boolean; byCandidate: Record<string, { level: number | null; status: "meets" | "below" | "related" | "missing" }> }[];
  //  related and missing have level null. The levels are the shared levels.
  // NO total, NO score and NO overall ranking of people. A test scans the answer for these words. Only the shared profile goes into the formulas.
}

interface JobSource { openCount: number; updatedAt: string | null; }   // shown as "{openCount} open jobs · updated {date}"
```

### Endpoints

| Method & path | Auth | Request | Response | Errors |
|---|---|---|---|---|
| `POST /auth/signup` | — | `{ role, name, email, password, company?, alias? }` (company required for recruiters; password ≥ 8; `alias` optional, candidates only — empty → the system gives one) | `201 { ok: true }` — **the same answer for a new or an existing email** (no account enumeration; the backend may email the owner) | 400 `VALIDATION_ERROR` (also bad alias), 409 `ALIAS_TAKEN` |
| `GET /aliases/suggest` | — | — | `200 { alias }` — a free "Colour Animal" alias | — |
| `GET /aliases/check?alias=&name=` | — | `alias`, optional `name` (to block the real name) | `200 { alias, available, reason?, suggestion? }` | — |
| `POST /auth/login` | — | `{ email, password, remember }` | `200 { token, expiresAt, user: User }`. Session length: 8 hours, or 30 days with `remember` | 401 `INVALID_CREDENTIALS` |
| `POST /auth/logout` | Bearer | — | `204` | — (the frontend signs out locally anyway) |
| `GET /me` | Bearer | — | `200 User` | 401 |
| `PATCH /me` | Bearer | Any of `{ name, company, alias, profile, cv, onboarding }`. `company`: recruiters only. `alias`, `profile`, `cv`, `onboarding`: candidates only. Other keys are ignored. `profile` takes the version 2 keys (see `Profile`); the server cleans all of them (domains only, level from the list, years 0–40, at most 20 certifications and 20 awards, skill level 1–5) | `200 User` | 400 (empty name/company, bad alias, recruiter alias "Only talent accounts have an alias.", bad `onboarding`/`cv`), 409 `ALIAS_TAKEN`, 401 |
| `GET /me/export` | Bearer | — | `200 { exportedAt, account, notifications, reports, … }`. A copy of the user's own data (talent: bookmarks, skipped jobs, applications, shared profile; employer: jobs and applications in the anonymous employer view). No password hash and no data of other people. Real backend only (the mock does not have it) | 401 |
| `POST /me/delete` | Bearer | `{ password }` | `204`. Deletes the account, the CV file and the data (an employer's jobs and their applications too). Real backend only | 400 `fields.password` "Your password is not correct.", 401 |
| `POST /me/password` | Bearer | `{ currentPassword, newPassword }` | `204`. Ends the user's other sessions; this session stays | 400 `fields.currentPassword` "Your current password is not correct.", `fields.newPassword` "Use at least 8 characters." / "Use a password that is different from your current one.", 401 |
| `POST /cv` | Bearer, candidate | `multipart/form-data`, field `file` (PDF or DOCX, ≤ 10 MB). The mock gets `{ name, size, type }` | `202 { cv: CvRecord, parse: { id, status: "parsing" } }`. The file is stored privately; parsing starts | 400 `fields.file` ("Use a PDF or DOCX file.", "This file is empty. Choose a different file.", "The file is larger than 10 MB. Use a smaller file."), 401, 403 |
| `GET /cv/parse/:id` | Bearer, candidate (own upload) | — | `200 { id, status: "parsing" }`, `{ id, status: "done", result: ParseResult }` (with the version 2 keys: `currentRole`, `targetRole`, `level`, `yearsExperience`, `certifications`, `awards`, `skills[].level`, `found`, `sources`, `domain`) or `{ id, status: "failed", error }` | 401, 403, 404 |
| `POST /profile/translate` | Bearer, candidate | `{ profile, evidence }` (a draft; `profile.translation` carries the decisions) | `200 { skills: TranslatedSkill[], gaps: string[] }`. Keeps `status` (and an edited `mapped`), the `level` and the `years` of skills with the same `id`. A skill card has `level` from the profile (`skillLevels` or `{ name, level }`), else from its evidence (Strong 4, Moderate 3, Limited 2). Every name is a name of the taxonomy; a title that is not an ICT title gives no role card. Never scores the person | 401, 403 |
| `GET /me/shared-profile` | Bearer, candidate | — | `200 SharedProfile` (with level, exact years, skill levels, certifications, awards and `updatedAt`) | 401, 403 |
| `GET /jobs/recommended?page=&pageSize=&sort=` | Bearer, candidate | `page`, `pageSize` (1–50, default 10), `sort` = `best` (default) or `newest` | `200 { items: Job[], page: Page, sort, source: JobSource }`. Open jobs with `match.recommended`, in the order of `sort`. **Leaves out skipped jobs and jobs the candidate applied for** (Feature 3 AC2). The page of a list has the same Fit score as the page of the job. `items` is empty when the user has no profile. Tracks `job_appear` for the jobs of the page only. The Home widget asks for `pageSize=5` | 400 `fields.sort`, 401, 403 |
| `GET /jobs?q=&location=&page=&pageSize=&sort=` | Bearer, candidate | `q` (≤ 100 chars; every word must appear in title, company, occupation, category, skills or area), `location` (a city or "Remote"), `page`, `pageSize`, `sort` = `best` (default) or `newest` | `200 { total, items: Job[], page: Page, sort, source: JobSource }`. Open jobs that are not skipped (`total` = `page.total`) | 400 `fields.sort`, 401, 403 |
| `GET /jobs/compare?ids=a,b,c,d,e` | Bearer, candidate | `ids`: **2 to 5** different job ids. Register before `/jobs/:id`. Real backend only. Free | `200 CompareJobs` = `{ jobs, axes, pairs, skillMatrix }`. `jobs[]` = the job card + `axes` (the 8 radar values for this talent) + `salaryMidpoint`. `pairs` = Formula 3 for each pair of jobs (all pairs: 1, 3, 6 or 10). `skillMatrix` = one row for each skill that a job asks for | 400 `fields.ids` "Choose 2 to 5 jobs to compare." (+ `missing`), 404 (+ `missing`), 401, 403 |
| `GET /jobs/:id` | Bearer, candidate | — | `200 JobDetail` (also closed jobs, with `status: "closed"`). The job keys of version 2 and the **full `description`** (never cut), and `bridge` with `path`. Tracks `job_watch` | 401, 403, 404 "This job does not exist or was removed." |
| `PUT /jobs/:id/skip` · `DELETE /jobs/:id/skip` | Bearer, candidate | — | `200 { jobId, skipped }`. Idempotent. Tracks `job_skip` (never shown to users) | 401, 403, 404 |
| `POST /reports` | Bearer | `{ targetType: "job" (candidates) \| "candidate" (recruiters), targetId, reason: "not_relevant" \| "wrong_location_or_type" \| "misleading" \| "other", details ≤ 500 }` | `200 { ok: true }`. A repeat report by the same user updates the old one (no duplicates) | 400 `fields.targetType` "You can't report this.", `fields.reason` "Choose a reason." |
| `POST /applications` | Bearer, candidate | `{ jobId, note? }` (note ≤ 500) | `200 Application` (status "applied"). Snapshot = the shared profile now. Contact details in the note are replaced with "[email removed]" / "[phone removed]". Notifies the job owner | 404, 409 "This job is closed. You can't apply now." / "You have already applied for this job." / "Accept at least one translated skill before you apply. …", 400 |
| `GET /applications?page=&pageSize=&sort=` | Bearer, candidate | `sort` = `updated` (default, the old order: last updated first), `best` (the skill coverage) or `newest` (the date of the application) | `200 { items: ApplicationListItem[], page: Page, sort }`. There is no filter for Active and Past: the frontend reads all pages and filters | 400 `fields.sort`, 401, 403 |
| `GET /applications/:id` | Bearer, candidate (own) | — | `200 Application` | 404 |
| `PATCH /applications/:id` | Bearer, candidate (own) | `{ note }` | `200 Application`. Only while "applied" (Feature 4 AC6, AC14) | 409 "The employer is reviewing your application. You can't change it now." |
| `POST /applications/:id/slot` | Bearer, candidate (own) | `{ slotId, shareIdentity: boolean }` | `200 Application`. Can change until the recruiter confirms. Adds a history row; notifies the recruiter | 409 "This application has no interview to book." / "The employer has confirmed your interview time." / "This time is no longer available. Choose another time." / "This time has passed. Choose another time." |
| `POST /applications/:id/offer-reply` | Bearer, candidate (own) | `{ accept: boolean }` | `200 Application` → "confirmed" or "rejected" | 409 "There is no offer to answer." |
| `POST /applications/:id/decline` | Bearer, candidate (own) | — | `200 Application` → "declined" (only from "contacted") | 409 |
| `POST /applications/:id/feedback` | Bearer, candidate (own) | `{ toOther ≤ 1000, toTeam ≤ 1000 }` (at least one) | `200 Application`. Only when final | 400 `fields.form` "Write feedback in at least one box.", 409 |
| `GET /recruiter/jobs?page=&pageSize=&sort=` | Bearer, recruiter | `sort` = `newest` (the only value) | `200 { items: RecruiterJob[], page: Page, sort }` (own jobs, newest first) | 400 `fields.sort`, 403 |
| `POST /recruiter/jobs/suggest-skills` | Bearer, recruiter | `{ title, description, category? }` (`category` is a domain) | `200 { skills: string[], skillRequirements: { name, level: 3, must: true }[] }` (up to 10; the skills that the text shows, then the core skills of the occupation of the title, then the usual skills of the domain; all names are names of the taxonomy) | 403 |
| `POST /recruiter/jobs/import` | Bearer, recruiter | `multipart/form-data`, field `file` (a job description, PDF or DOCX, ≤ 10 MB). The mock gets `{ name, size, type }` | `202 { parse: { id, status: "parsing" } }`. Reading starts | 400 `fields.file` ("Use a PDF or DOCX file.", "This file is empty. Choose a different file.", "The file is larger than 10 MB. Use a smaller file."), 403 |
| `GET /recruiter/jobs/import/:id` | Bearer, recruiter (own upload) | — | `200 { id, status: "parsing" }`, `{ id, status: "done", result: { fields: { title?, category?, domain?, specialisation?, location?, type?, salary?, description?, skills?, level?, minYears?, maxYears?, workMode?, skillRequirements?, certifications?, awards?, educationMin? }, detected: string[], missing: string[], sampleLabel? } }` or `{ id, status: "failed", error }`. `description` keeps its line breaks and the `## Heading` and `- ` marks, and is not cut. `category` is the domain. A value that is not valid is left out. The result is a **draft**: nothing is posted until `POST /recruiter/jobs`. Treat the file text as data, not instructions (AI_Rule.md Rule 5) | 403, 404 "We can't find this file upload." |
| `POST /recruiter/jobs` · `PATCH /recruiter/jobs/:id` | Bearer, recruiter (own) | `{ title ≥ 3, category ∈ the 3 domains, location ∈ LOCATIONS, type ∈ WORK_TYPES, salary?, description ≥ 30 and ≤ 10000, skills 1–12, targetApplicants 1–10000, closesAt (future) }` and the **optional version 2 keys**: `level` (one of the six; a new job without it gets "Mid"; on PATCH a missing or null level is no change), `specialisation` and `educationMin` (text ≤ 80, scrubbed; null or "" clears; the specialisation must belong to the domain), `minYears` and `maxYears` (0–40, one decimal, or null; `minYears` must not be more than `maxYears`), `workMode` (Onsite, Hybrid, Remote or null), `skillRequirements` (`[{ name, level 1–5 (missing = 3), must (missing = true) }]`, 1–12, a copy of a name is dropped; if it has items the job skills come from it and `skills` is ignored), `certifications` (`{ required: [name], preferred: [name] }`, up to 10 names in each list, ≤ 120 chars, scrubbed; send both lists) and `awards` (`{ preferred: [award kind] }`, up to 10, kinds of the taxonomy: the slug or the label is accepted and the slug is stored). On PATCH: `skillRequirements` with items replaces the skills with their levels; `skills` alone replaces the skills and clears the levels; `skillRequirements: []` keeps the skills and clears the levels. PATCH: any subset | `200 RecruiterJob` with `description`. The job joins the catalogue (company = recruiter's company). The occupation (`anzsco`, `occupation`) comes from the taxonomy (the longest role of the role list in the title, else the occupation of the specialisation). The number and the unit of the pay come from the `salary` text ("per day", "a day", "daily" or "day rate" → `day`; "per hour", "an hour" or "hourly" → `hour`; else `year`). PATCH notifies every candidate with a non-final application ("{title} was updated") | 400 fields: "Enter a job title.", "Choose a category." (the domain), "Choose a location.", "Choose a work type.", "Write a description of at least 30 characters." (a description over 10,000 characters is refused with a message; it is never cut), "Add 1 to 12 required skills.", "Enter a number from 1 to 10000.", "Choose a close date.", "The close date must be in the future.", "Choose a level." (`level`), "Choose a specialisation from the list." / "Choose a specialisation of this domain." (`specialisation`), `maxYears` (minimum above maximum), "Choose a work mode." (`workMode`), "Choose a skill level from 1 to 5." (`skillRequirements`), "Choose award kinds from the list." (`awards`), `certifications` (too many) |
| `GET /recruiter/jobs/:id` | Bearer, recruiter (own) | — | `200 RecruiterJob` with the full `description`, `summary` and `company` and the version 2 job keys (no `bridge`) | 404 |
| `GET /recruiter/jobs/:id/applications?page=&pageSize=&sort=` | Bearer, recruiter (own) | `sort` = `newest` (the only value: the date of the application; before version 2 the order was "last change first") | `200 { job: RecruiterJob, items: { id, alias, origin, status, statusLabel, coverage, matched, total, awaiting, createdAt, updatedAt }[], page: Page, sort }`. No status filter | 400 `fields.sort`, 404 |
| `GET /recruiter/applications/:id` | Bearer, recruiter (own job) | — | `200 RecruiterApplication` | 404 |
| `POST /recruiter/applications/:id/status` | Bearer, recruiter (own job) | `{ to, slots?, offer? }` | `200 RecruiterApplication`. See the state machine. Notifies the candidate (accepted, offer, rejected also "email") | 409 "You can't move an application from {A} to {B}." / "Confirm the interview time first. Then record the result.", 400 `fields.slots` "Offer 1 to 3 interview times." / "Choose times in the future.", `fields.offer` "Write the offer details (at least 10 characters)." |
| `POST /recruiter/applications/:id/confirm-slot` | Bearer, recruiter (own job) | — | `200 RecruiterApplication` | 409 "There is no interview time to confirm." |
| `POST /recruiter/applications/:id/feedback` | Bearer, recruiter (own job) | `{ toOther, toTeam }` | `200 RecruiterApplication`. Only when final | 400, 409 |
| `GET /recruiter/candidates?jobId=&view=all\|saved&page=&pageSize=&sort=` | Bearer, recruiter | `jobId` (default: the first open own job, else the first own job), `sort` = `best` (default: the order of the fit to the job, Formula 6 on the shared profile, `0.6 × coverage + 0.4 × TSS`, never sent) or `updated` (the profile that changed last first) | `200 { job: { id, title, skills } \| null, items: CandidateCard[], page: Page, sort, total, limitedTo: number \| null, plan, skippedCount }`. Candidates with a done profile and ≥ 1 shared skill, not skipped by this recruiter. **Basic:** the first `topN` (5) only: `limitedTo` 5, `page = { page: 1, pageSize: 5, total: <the real total>, totalPages: 1 }`, `page` and `pageSize` are ignored. **Premium:** all, page by page. No score on a person. Tracks `profile_appear` for the items of the page, and `talent_list_full` when a Premium page has more than 5 items | 400 `fields.sort`, 403 |
| `GET /recruiter/candidates/:id?jobId=` | Bearer, recruiter | — | `200 CandidateCard + { job, match: { coverage, skills }, targetRoles, workTypes, fieldsOfStudy, entitlements }`. The skills have the version 2 result keys (`fitStatus`, `required`, `level`, `must`). Tracks `profile_watch` | 404 |
| `PUT` · `DELETE /recruiter/candidates/:id/save` | Bearer, recruiter | — | `200 { id, saved }`. PUT tracks `profile_saved` | 403 |
| `PUT /recruiter/candidates/:id/skip` · `DELETE /recruiter/candidates/skipped` | Bearer, recruiter | — | `200 { id, skipped: true }` · `200 { ok }` (show all again) | 403 |
| `POST /recruiter/candidates/:id/contact` | Bearer, recruiter, **Premium** | `{ jobId (own), message 10–500 }` | `200 RecruiterApplication` with `origin: "contacted"`, status "contacted". Message scrubbed. Notifies the candidate. Tracks `invite` | 403 `PREMIUM_REQUIRED`, 400 `fields.jobId`, `fields.message`, 409 "This person is already in the pipeline for this job." |
| `GET /recruiter/compare?ids=a,b,c,d,e&jobId=` | Bearer, recruiter, **Premium** | `ids`: **2 to 5** different talent ids. `jobId`: one of the employer's own jobs (required: the match is "for this job"). **The old `?a=&b=` form is removed** (it gives 400 for `ids`) | `200 CompareTalent` = `{ job, candidates, radar, areas, skillMatrix }`. **No total, no score, no ranking of people.** Order of the checks: sign-in and role, Premium, `ids`, `jobId`, the job, the profiles. Tracks `compare_view` after a good answer | 403 `PREMIUM_REQUIRED`, 400 `fields.ids` "Choose 2 to 5 profiles to compare." (+ `missing`), 400 `fields.jobId` "Choose one of your jobs.", 404 "We can't find this job." (not your job), 404 "We can't find one of the profiles." (+ `missing`) |
| `GET /notifications` | Bearer | — | `200 { items: Notification[] (newest first, max 50), unread }` | 401 |
| `POST /notifications/read` | Bearer | `{ ids: string[] }` (empty = all) | `200 { ok }` | 401 |
| `GET /entitlements` · `PUT /entitlements` | Bearer | PUT `{ plan: "basic" \| "premium" }` (**demo toggle**; a real backend changes the plan through billing) | `200 Entitlements` (with `crown`, `compareMax` and `benefits`) | 400 "Choose Basic or Premium.", 403 when the switch is off |
| `GET /stats` | Bearer | — | Candidate: `{ role, plan, basic: { applications, movedOn, confirmed, byStage: { stage, count }[], profile: { appear, watch, saved } }, advanced: null \| { basis, gapRanking: { skill, count, needLevel, yourLevel, missing, below }[5], demandForYourSkills: { skill, count, needLevel, yourLevel }[5] } }`. The Premium insights are level-aware, from the skills of the 20 best jobs: a skill is in `gapRanking` when it is missing or below the asked level (`count = missing + below`) and in `demandForYourSkills` when the talent meets the asked level; `needLevel` is the mean level that the jobs ask for (one decimal), `yourLevel` the talent's level (`null` for a missing skill). Recruiter: `{ role, plan, basic: { openJobs, jobsAtTarget, awaitingResponse, totalJobs }, advanced: null \| { pipeline: { stage, count }[], jobs: { id, title, appear, watch, save, apply }[], finished } }`. Counts only, never per person (Feature 7). The `advanced` part writes the event `insights_view` (talent) or `advanced_charts_view` (employer) | 401 |
| `POST /demo/reset` | — | — | `200 { ok }`. **Mock only, not part of the real API** | — |
| `GET /bookmarks?page=&pageSize=&sort=` | Bearer, candidate | `sort` = `saved` (default: the job saved last first), `best` or `newest` (posting date) | `200 { items: Job[], page: Page, sort }`. Removed jobs are left out; closed jobs stay | 400 `fields.sort`, 401, 403 |
| `PUT /bookmarks/:jobId` | Bearer, candidate | — | `200 { jobId, bookmarked: true }`. Idempotent | 401, 403, 404 |
| `DELETE /bookmarks/:jobId` | Bearer, candidate | — | `200 { jobId, bookmarked: false }`. Idempotent | 401, 403 |

### Frontend API layer (`js/api/index.js`)

```js
api.auth.signup(body)                 // POST /auth/signup
api.auth.login({ email, password, remember })   // stores { token, expiresAt } (localStorage if remember, else sessionStorage) under "jinder.session"; caches user
api.auth.logout()                     // POST /auth/logout, then clears the session even if the call fails
api.me.get()                          // GET /me, caches user (session.user)
api.me.update(patch)                  // PATCH /me, caches user
api.me.changePassword({ currentPassword, newPassword })   // POST /me/password
api.me.export() / deleteAccount(password)   // GET /me/export, POST /me/delete (real backend only)
api.aliases.suggest()                 // GET /aliases/suggest
api.aliases.check(alias, name)        // GET /aliases/check
api.cv.upload(file)                   // POST /cv — http: FormData; mock: { name, size, type }
api.cv.parseStatus(id)                // GET /cv/parse/:id
api.profile.translate({ profile, evidence })   // POST /profile/translate
api.profile.shared()                  // GET /me/shared-profile
api.jobs.recommended(arg)            // GET /jobs/recommended?page&pageSize&sort. arg = a number (the old call: the page size) or { page, pageSize, sort, limit? } (limit means pageSize)
api.jobs.search({ q, location, page, pageSize, sort, limit? })   // GET /jobs?…
api.jobs.get(id)                      // GET /jobs/:id
api.jobs.compare(ids)                 // GET /jobs/compare?ids=a,b,… (2 to 5 ids; real backend only)
api.bookmarks.list({ page, pageSize, sort })   // GET /bookmarks
api.bookmarks.add(jobId)              // PUT /bookmarks/:jobId
api.bookmarks.remove(jobId)           // DELETE /bookmarks/:jobId
api.jobs.skip(id) / api.jobs.unskip(id)   // PUT / DELETE /jobs/:id/skip
api.reports.create(body)              // POST /reports
api.applications.create({ jobId, note }) / list({ page, pageSize, sort }) / get(id) / update(id, { note })
api.applications.chooseSlot(id, { slotId, shareIdentity }) / replyOffer(id, accept) / decline(id) / feedback(id, { toOther, toTeam })
api.recruiter.jobs.list({ page, pageSize, sort }) / get(id) / create(body) / update(id, body) / suggestSkills({ title, description }) / applications(id, { page, pageSize, sort })
api.recruiter.jobs.importFile(file) / importStatus(id)   // POST /recruiter/jobs/import (http: FormData; mock: { name, size, type }), GET /recruiter/jobs/import/:id
api.recruiter.applications.get(id) / setStatus(id, { to, slots, offer }) / confirmSlot(id) / feedback(id, body)
api.recruiter.candidates.list({ jobId, view, page, pageSize, sort }) / get(id, jobId) / save(id) / unsave(id) / skip(id) / clearSkipped() / contact(id, { jobId, message }) / compare(a, b, jobId)   // compare(a, b, jobId) is kept for old code: it calls api.recruiter.compare([a, b], jobId)
api.recruiter.compare(ids, jobId)     // GET /recruiter/compare?ids=a,b,…&jobId= (Premium; 2 to 5 ids; real backend only)
api.notifications.list() / markRead(ids)
api.stats.get()
api.entitlements.get() / set(plan)    // GET / PUT /entitlements. get() fills crown and compareMax (5) if the backend does not send them; benefits only if it sends them. set() fires the window event jinder:plan-change
api.demo.reset()                      // mock only
isSignedIn()                          // a token exists and is not expired
```

**State machine (the backend enforces it; the frontend shows only `allowedNext`):**

| From | Allowed next (recruiter) | Candidate actions |
|---|---|---|
| applied | review, rejected | edit the note |
| contacted (Premium invite) | interview, rejected | decline → declined |
| review | interview (with 1–3 slots), rejected | — |
| interview | accepted (only after the slot is confirmed), rejected; confirm-slot when a slot is chosen | choose / change the slot (+ share identity) until confirmed |
| accepted | offer (with text), rejected | — |
| offer | — | accept → confirmed, decline → rejected |
| confirmed, rejected, declined | — (final; feedback from both sides) | feedback |

The system never changes a status by itself (Feature 6 AC12). Every change adds a history row and a notification for the other side.
**Lists (version 2).** Every list method takes `{ page, pageSize, sort }`. The real backend answers with `page: { page, pageSize, total, totalPages }` and `sort`. **For the mock**, the client asks for the whole list, sorts it (`best` = the rank or the coverage, `newest` = `postedAt` or `createdAt`, `updated` = `updatedAt`; `saved` and unknown values keep the mock order), cuts the page, and builds the same `page` object. Without page parameters the whole list comes back with `page: { page: 1, pageSize: <count>, total: <count>, totalPages: 1 }`. A list with `limitedTo` (a Basic employer) always has one page and keeps its `total`.
**Compare calls.** With fewer than 2 or more than 5 distinct ids the client sends nothing and fails with `ApiError(400, "VALIDATION_ERROR", "Choose 2 to 5 to compare.", { ids: "Choose 2 to 5 to compare." })` (the backend gives the same shape). In mock mode the promise fails with `ApiError(501, "NEEDS_REAL_BACKEND", "<Compare jobs|Compare talent> needs the real Jinder backend. Start the platform (python start.py) and open the app without ?mock=1.")` and the screen shows `err.message`. A Basic employer gets 403 `PREMIUM_REQUIRED` from the backend.
`request(method, path, body)` calls the adapter for `CONFIG.API_MODE` with the token. `http.js` sends a `FormData` body as it is (no JSON, no Content-Type, so the browser sets the multipart boundary). On 401 outside `/auth/*` it clears the session and fires `jinder:unauthorized`. `http.js` maps a non-2xx response to `ApiError(status, error.code, error.message, error.fields)`, `204` to `null`, and a `fetch` failure to `NETWORK_ERROR` ("We can't reach the server. Check your connection and try again.").

## Mock backend (API_MODE "mock")

All mock files start with a comment "MOCK BACKEND — … The real backend replaces this file." The mock is for demos and is not secure.

- **Store (`mock/db.js`):** `localStorage["jinder.mock.db.v2"]` = `{ users, sessions: { [token]: { userId, expiresAt } }, bookmarks: { [userId]: jobId[] }, parses: { [id]: { userId, fileName, startedAt } }, skips: { [userId]: jobId[] }, reports: [], applications: [], notifications: [], events: [], postedJobs: [], jobImports: { [id]: { userId, fileName, startedAt } }, savedCandidates: { [recruiterId]: id[] }, skippedCandidates: { [recruiterId]: id[] }, plans: { [userId]: "basic" | "premium" }, seeded: false }`. `loadDb()` merges the stored data over this empty shape. `resetDb()` deletes the key. On load, remove the keys of the old versions (`sb_users`, `sb_session` and `jinder.mock.db.v1`, the old mock data of other fields of work), so that a browser with old data starts clean. `demoHash()` is a djb2 hash with a "q" prefix (not secure; comment that the backend must use bcrypt or Argon2). IDs and tokens: `crypto.randomUUID()`.
- **Adapter (`mock/adapter.js`) + `core.js`:** route files register endpoints with `route(method, pattern, handler)` (`:params`; register `/jobs/recommended` before `/jobs/:id`). `mockAdapter(method, path, body, token)`: wait `MOCK_LATENCY_MS` (150); load the db; if `MOCK_DEMO_DATA`, run `seedDemo(db)` (writes once, `db.seeded`); run the handler with `ctx = { db, params, query, body (structured clone), token, skipSave: false }`; save the db unless `ctx.skipSave`; return a JSON copy (dates become strings). Unknown endpoint → 404 `NOT_FOUND`. Helpers: `requireUser` (401 if no or expired session; an expired session is deleted), `requireRole` (403 "You don't have access to this."), `validation(fields)` (400 with only the bad fields), `publicUser` (allow-list of User fields), `sharedProfileOf(user)` (the `SharedProfile` allowlist), `scrubContact(text)` (emails → "[email removed]", phone numbers `\+?\d[\d\s().-]{7,}\d` → "[phone removed]"), `notify(db, userId, { type, title, body, link, email })`, `entitlementsOf(db, user)`, `requirePremium(db, user, feature)`, `track(db, { type, targetType, targetId, actorId })` (keep the last 5000 events). Every job in a candidate response gets `bookmarked`, `skipped` and `applicationId`.
- **Event types (Feature 7 AC4):** `job_appear`, `job_watch`, `job_save`, `job_skip`, `job_apply`, `job_respond`, `profile_appear`, `profile_watch`, `profile_saved`, `profile_skip`. They are counted on the server. Skip counts are never shown to users.
- **Seed users cannot sign in:** a user with `seed: true` (the 10 sample talent) gets "Incorrect email or password.".
- **What works only with the real backend (version 2).** The mock does not implement: the pager and sort on the server (the client does it, see above), the Compare endpoints (`GET /jobs/compare`, `GET /recruiter/compare?ids=…`: the client fails with `NEEDS_REAL_BACKEND`; the old two-profile route `GET /recruiter/compare?a=&b=&jobId=` is still in `routes-recruiter.js` but no screen calls it), `entitlements.benefits` (only `crown` and `compareMax` are added), `bridge.path` ("Your path to this job" shows "A detailed path is not available for this job."), the formula engine (the "fit" is the simple rank below and no number is shown), and the talent facts on the **employer** screens (the employer job form has no level, years, work mode, education, skill level, certification or award field, and the talent cards and the review page of an employer have no level, years, certifications, awards or skill levels). A CV file or a job file gives one of the samples by its name; the mock reads no real file.
  What the mock **does** have (version 2): the new job fields on the talent screens (level, years, work mode, skill levels, certifications, awards, full description with headings), the CV result keys (`domain`, `skills[].level`, `found`) so that the onboarding shows "What we found in your CV" and the hints, skill `level` and `years` in the translation, and the V2 facts in `GET /me/shared-profile` (level, exact years, specialisation, skill levels, certifications, awards). **All mock data is ICT only** (the 3 domains); a title of another field of work gives no role card. It is a browser-only prototype for demos.
- **Posted jobs** (`db.postedJobs`, ISO dates) join the catalogue in `jobs.js` (`catalogue(db)`); a posted job has `ownerId`, `targetApplicants` and the recruiter's company. A card never includes `description`, `ownerId`, `targetApplicants` or `editedAt`. Catalogue jobs have no owner, so applications to them notify nobody.
- **Signup validation messages:** role "Choose an account type.", name "Enter your name.", company "Enter your company.", email "Enter a valid email address.", password "Use at least 8 characters." Emails are stored trimmed and lower case.
- **Aliases (`mock/aliases.js`):** a candidate always has an alias. Recruiters see a candidate only by alias (Feature 1 AC6, AC13).
  - `suggestAlias(db)`: random "{Colour} {Animal}" that is free; after 40 tries, "Amber Badger {n}". Neutral words only — no personality adjectives, no colours that describe skin or hair. Colours: Amber, Azure, Cobalt, Coral, Cyan, Indigo, Jade, Lilac, Lime, Mint, Plum, Saffron, Sage, Slate, Teal, Violet. Animals: Badger, Crane, Dolphin, Falcon, Finch, Fox, Gecko, Heron, Kestrel, Koala, Llama, Lynx, Otter, Owl, Panda, Puffin, Robin, Seal, Swift, Wombat.
  - `aliasProblem(alias, realName)` → message or "": "Use 3 to 30 characters."; "Use letters, spaces, hyphens and apostrophes only." (`^[A-Za-z][A-Za-z '-]*[A-Za-z]$`); "Do not use your real name. Employers must not know who you are." (any part of the name with ≥ 3 letters is a word of the alias); "Do not use a country, nationality or city. Use a neutral alias." (any word or phrase from `COUNTRIES` + about 35 nationalities + about 15 big cities of origin, for example Vietnamese, Indian, Hanoi, Manila).
  - `isTaken(db, alias, exceptUserId)`: case-insensitive, spaces collapsed. Taken → 409 `ALIAS_TAKEN` "This alias is taken. Try “{suggestion}”." with `fields.alias` and `suggestion`.
  - A candidate without an alias (older data) gets one the next time the session is read.
  - Recruiters: `alias` is always `null`; `PATCH /me { alias }` → 400 "Only talent accounts have an alias."
- **Password (`POST /me/password`):** check the current hash, set the new one, delete the user's other sessions.
- **Jobs (`mock/jobs.js`):** the catalogue is the 24 jobs of `SEED_JOBS` (`seed-jobs.js`) plus the jobs that employers post. There is **no CSV file and no `fetch`**: `loadJobs()` only returns a resolved promise, because the routes wait for it. `jobSource()` returns `{ openCount, updatedAt }` (open jobs; newest `postedAt`). Exports: `loadJobs`, `catalogue`, `jobSource`, `isOpen`, `findJob`, `recommend`, `searchJobs`, `jobDetail`, `suggestSkills`, `namesFromProfile`, `namesFromList`, `skillMatch`, `skillsIn`, `canonicalSkillName`, `salaryText`.

- **CV upload and parsing (mock):** `POST /cv` checks the type and size, saves `user.cv` and creates `db.parses[id] = { userId, fileName, startedAt }`. `GET /cv/parse/:id` answers `parsing` for the first **1800 ms**, then `parseResultOf(sampleFor(fileName))` from `cv-samples.js`. The file name (lower case) chooses the sample: "fail" or "corrupt" → `failed`; "ml", "machine", "research", "scientist" or "ai" → the machine learning CV; "software", "developer", "backend", "java" or "swe" → the software CV; "devops", "admin", "infra", "cloud" or "platform" → the systems administrator CV; "data" → the data analyst CV; "analyst" or "business" → the business analyst CV; **any other name → the data analyst CV** (it is the CV of the demo talent). `parseResultOf` gives `fields` (only what the CV shows), `detected`, `missing`, `evidence`, `sampleLabel` and the version 2 keys `domain`, `skills [{ name, level }]` and `found { currentRole, targetRole, level, yearsExperience, certifications, awards }`. A field that the sample does not show is not in `fields` and is `false` in `found` (the machine learning CV has no desired role and no certification; the business analyst CV has no years, no certification and no award).
- **Translation (mock):** `POST /profile/translate` calls `translateKeeping(profile, evidence)` (exported from `routes-account.js`; `seed-demo.js` uses it too): it runs `translate(profile, evidence)` from `translation.js`, then keeps the old `status`, the edited `mapped`, and the `level` and `years` that the talent set, for skills with the same `id` from `profile.translation`. A skill card has `level` (the level that the talent gave, else from the evidence: Strong 4, Moderate 3, Limited 2) and `years`. A title that is not an ICT title gives no role card.
- **Matching uses the translation:** in `jobs.js` the candidate's skills = `profile.skills` + the `mapped` names of accepted and edited translated skills of kind skill, each also expanded through the skill table of the taxonomy.
- **`GET /me/shared-profile`** = `sharedProfileOf(user)` in `core.js` (allowlist, see `SharedProfile`). The shared `skills` list has the skill cards only (a role card is a role, not a skill). The route adds the version 2 facts of the talent (level, `yearsExperience` rounded to 0.5, `specialisation`, `skillLevels`, `certifications`, `awards`). The applications and the talent cards that an employer reads in the mock keep the old shape.

### Translation engine (`js/api/mock/translation.js`)

Create this file exactly. It is a simpler copy of `jinder_platform/jinder/translation.py`: 33 role pairs and 37 skill pairs, all ICT, with the names of the taxonomy (53 role titles, 172 skills). A role card has a title of the role list, the ANZSCO code and occupation of the taxonomy, and a kind (`cross-border`, `cross-industry` or `direct`); a title is read without level words, company and place in brackets, and two titles that give the same role make one card ("BI Specialist; MIS Executive"). A title that is not an ICT title (a nurse, an accountant, a chef, a teacher, a mechanical engineer) gives **no** role card. A skill card uses the name or alias of the taxonomy first ("spreadsheets" gives "Microsoft Excel"), then a pair ("Informatica", "Qlik", "ER diagrams"), then the name as it is, and has `level` (1 to 5) and `years`:

```js
// MOCK BACKEND — the cross-border and cross-industry skill translation engine. The real backend replaces this file.
// A simpler copy of jinder_platform/jinder/translation.py. ICT only: every name is a name of ict_taxonomy.json (a role of the role list, a skill of the skill list).
// Input: the candidate's profile (roles, skills, qualifications, countries) and the CV evidence lines.
// Output: translated skills with a plain-language reason, an evidence level and a skill level (1 to 5). No score on the person.
// A title that is not an ICT title gives no role card. A skill that the taxonomy does not know keeps its name.
// It never uses nationality, ethnicity, gender, age or visa status. Country of study is used only for
// the AQF note on qualifications and for the word "cross-border" (Feature 2; PRD: no formal credential verification).
import { canonicalSkillName, skillsIn } from "./jobs.js";

const lower = (s) => String(s || "").toLowerCase();
const list = (v) => (Array.isArray(v) ? v : v ? [v] : []);
const escRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

// A skill with no level of its own gets the level of its evidence (rule F8)
const EVIDENCE_LEVEL = { Strong: 4, Moderate: 3, Limited: 2 };

// The occupations and the role list of the taxonomy. A role title gives an ANZSCO code, and the code gives the occupation title.
const OCCUPATIONS = {
  "261313": "Software Engineer",
  "261312": "Developer Programmer",
  "261212": "Web Developer",
  "261316": "DevOps Engineer",
  "261314": "Software Tester",
  "263211": "ICT Quality Assurance Engineer",
  "261315": "Cyber Security Engineer",
  "261112": "Solutions Architect",
  "261399": "Machine Learning Engineer",
  "261311": "Generative AI Engineer",
  "263111": "MLOps Engineer",
  "224112": "AI Research Scientist",
  "224115": "Data Scientist",
  "224114": "Data Analyst",
  "262111": "Data Engineer",
  "261111": "ICT Business Analyst",
  "224113": "Statistician",
};
const ROLE_CODES = {
  "Software Engineer": "261313",
  "Software Developer": "261312",
  "Backend Engineer": "261313",
  "Frontend Engineer": "261212",
  "Full-stack Engineer": "261312",
  "Web Developer": "261212",
  "Mobile Developer": "261312",
  "Android Developer": "261312",
  "iOS Developer": "261312",
  "Java Developer": "261312",
  ".NET Developer": "261312",
  "Python Developer": "261312",
  "Platform Engineer": "261316",
  "DevOps Engineer": "261316",
  "Site Reliability Engineer": "261316",
  "Cloud Engineer": "261316",
  "Cloud Architect": "261112",
  "Solutions Architect": "261112",
  "Software Architect": "261112",
  "QA Engineer": "263211",
  "Test Automation Engineer": "263211",
  "Software Tester": "261314",
  "Security Engineer": "261315",
  "Application Security Engineer": "261315",
  "Machine Learning Engineer": "261399",
  "Computer Vision Engineer": "261399",
  "NLP Engineer": "261399",
  "Deep Learning Engineer": "261399",
  "AI Engineer": "261311",
  "Generative AI Engineer": "261311",
  "LLM Engineer": "261311",
  "MLOps Engineer": "263111",
  "ML Platform Engineer": "263111",
  "Applied Scientist": "224112",
  "AI Research Scientist": "224112",
  "AI Research Engineer": "224112",
  "Data Engineer": "262111",
  "Analytics Engineer": "262111",
  "Big Data Engineer": "262111",
  "Data Platform Engineer": "262111",
  "ETL Developer": "262111",
  "Data Warehouse Engineer": "262111",
  "Database Administrator": "262111",
  "Data Architect": "262111",
  "Data Analyst": "224114",
  "Business Intelligence Analyst": "224114",
  "BI Developer": "224114",
  "Reporting Analyst": "224114",
  "Product Analyst": "224114",
  "Data Scientist": "224115",
  "Statistician": "224113",
  "Business Analyst": "261111",
  "Business Systems Analyst": "261111",
};
const ROLE_BY_LOWER = new Map(Object.keys(ROLE_CODES).map((t) => [lower(t), t]));
const occupationOf = (mapped) => ({ anzsco: ROLE_CODES[mapped], occupation: OCCUPATIONS[ROLE_CODES[mapped]] });

// Mapping library (about 25 role pairs and 30 skill pairs). "test" runs on one role title (without level words) or on one skill, in lower case.
// kind: "cross-border" (an overseas title, tool or standard), "cross-industry" (the same competency in a different field of work)
// or "direct" (a common name for the same thing).
// overseas: the pair is used only if the talent studied overseas, or the title has a place in brackets ("Software Developer (Vietnam)").
// weak: the last choice, when no other pair fits.
const role = (test, mapped, kind, reason, extra = {}) => ({ test: new RegExp(test), mapped, kind, reason, ...occupationOf(mapped), ...extra });
const ROLE_PAIRS = [
  role("\\b(sde|swe|software development engineer)\\b", "Software Engineer", "cross-border", "SDE and SWE are common overseas titles. In Australia the same work is a Software Engineer role."),
  role("^software developer\\b", "Software Engineer", "cross-border", "Software Developer is a common title overseas for what Australian employers call a Software Engineer.", { overseas: true }),
  role("analyst[- ]programmer|application programmer|applications developer|^(computer |web |application )?programmer$|^coder$", "Software Developer", "cross-border",
    "Programmer titles overseas match the Australian Software Developer role: you design, write and test code."),
  role("j2ee|java (developer|engineer|programmer)", "Java Developer", "direct", "Java Developer has the same meaning in Australia."),
  role("\\.net|dotnet|c# (developer|engineer)", ".NET Developer", "direct", ".NET Developer has the same meaning in Australia."),
  role("(front[- ]?end|ui|react|angular|vue) (developer|engineer)", "Frontend Engineer", "direct", "Front-end work has the same meaning in Australia. Australian ads call the role Frontend Engineer."),
  role("(back[- ]?end|server[- ]side|api) (developer|engineer)", "Backend Engineer", "direct", "Back-end work has the same meaning in Australia. Australian ads call the role Backend Engineer."),
  role("full[- ]?stack", "Full-stack Engineer", "direct", "Full-stack work has the same meaning in Australia."),
  role("(android|ios|mobile|flutter|react native)( app| application)? (developer|engineer)", "Mobile Developer", "direct", "Mobile development has the same meaning in Australia."),
  role("(system|systems|network|infrastructure|it infrastructure) (administrator|admin|engineer)|sysadmin", "Platform Engineer", "cross-industry",
    "Running servers and networks is close to platform engineering in Australia, where teams also write code to run the platform.",
    { gaps: ["Infrastructure as code (for example Terraform)"] }),
  role("devops|release engineer|build (and release )?engineer", "DevOps Engineer", "direct", "DevOps Engineer has the same meaning in Australia."),
  role("\\bsre\\b|site reliability|reliability engineer", "Site Reliability Engineer", "direct", "Site Reliability Engineer has the same meaning in Australia."),
  role("(solution|solutions|enterprise|technical) architect|solution designer", "Solutions Architect", "direct", "Solutions Architect has the same meaning in Australia."),
  role("test automation|automation (test )?(engineer|tester)|\\bsdet\\b", "Test Automation Engineer", "direct", "Test automation work has the same meaning in Australia."),
  role("(qa|quality assurance|quality) (engineer|analyst|specialist)|test engineer", "QA Engineer", "direct", "QA Engineer has the same meaning in Australia."),
  role("\\btester\\b|testing engineer|software tester", "Software Tester", "direct", "Software Tester has the same meaning in Australia."),
  role("(information|cyber|network|application|it) security (engineer|analyst|specialist|officer)|infosec|soc analyst", "Security Engineer", "cross-border",
    "Security analyst and officer titles overseas match the Australian Security Engineer role."),
  role("machine learning (engineer|developer)|\\bml engineer\\b", "Machine Learning Engineer", "direct", "Machine Learning Engineer has the same meaning in Australia."),
  role("(gen(erative)? ?ai|llm|prompt|chatbot|conversational ai) (engineer|developer)", "Generative AI Engineer", "direct", "Generative AI work has the same meaning in Australia."),
  role("applied scientist|research scientist|ai researcher|research engineer", "Applied Scientist", "cross-industry",
    "Research roles in machine learning match the Australian Applied Scientist role: you test ideas and build models that ship."),
  role("etl (developer|engineer)|informatica|datastage|ssis developer|talend", "ETL Developer", "cross-border",
    "ETL titles and tools overseas match the Australian ETL Developer and Data Engineer roles."),
  role("(big data|hadoop|spark) (engineer|developer)", "Big Data Engineer", "direct", "Big data work has the same meaning in Australia."),
  role("data (engineer|developer|pipeline engineer|integration engineer)", "Data Engineer", "direct", "Data Engineer has the same meaning in Australia."),
  role("database (administrator|admin|developer|engineer)|\\bdba\\b|sql developer", "Database Administrator", "direct",
    "Database work has the same meaning in Australia. Many teams ask for data engineering skills in the same role.",
    { gaps: ["Cloud data platforms (for example Snowflake or Databricks)"] }),
  role("\\bbi (specialist|executive|officer|consultant)|business intelligence (specialist|executive|officer|consultant)", "Data Analyst", "cross-border",
    "BI Specialist and BI Executive are common overseas titles. In Australia the same work (reports, dashboards, finding answers in data) is a Data Analyst role."),
  role("\\bmis (executive|analyst|officer|specialist|developer)|management information", "Data Analyst", "cross-border",
    "MIS titles overseas describe reporting and analysis of company data. In Australia this is a Data Analyst role."),
  role("(business intelligence|\\bbi) (analyst|developer)|power bi developer|tableau developer|report(ing)? (developer|analyst|specialist)", "Business Intelligence Analyst", "direct",
    "Business Intelligence Analyst has the same meaning in Australia."),
  role("data (analyst|analytics (specialist|executive))|analytics (analyst|executive|specialist)", "Data Analyst", "direct", "Data Analyst has the same meaning in Australia."),
  role("quantitative (analyst|researcher|developer)|\\bquant\\b", "Data Scientist", "cross-industry",
    "Quantitative work uses statistics and models on data. Australian Data Scientist roles ask for the same skills."),
  role("data scien(tist|ce (executive|specialist|engineer))|machine learning scientist", "Data Scientist", "direct", "Data Scientist has the same meaning in Australia."),
  role("business systems? analyst|(system|systems|functional|it business) analyst", "Business Systems Analyst", "cross-border",
    "Systems Analyst is a common overseas title. In Australia the same work is a Business Systems Analyst role."),
  role("business analyst|requirements analyst|\\bba\\b", "Business Analyst", "direct", "Business Analyst has the same meaning in Australia."),
  // The last choice: "Engineer", "Developer", "Staff Engineer" and "Software ..." titles. "Mechanical Engineer" is not an ICT title and gives no card.
  role("^(software |application |applications |systems )?(engineer|developer)$|^software ", "Software Engineer", "direct", "Software work has the same meaning in Australia.", { weak: true }),
];

// Skills that need a pair: another word or an overseas tool for a skill of the taxonomy. A name or alias of the taxonomy needs no pair.
const skill = (test, mapped, kind, reason) => ({ test: new RegExp(test), mapped, kind, reason });
const SKILL_PAIRS = [
  skill("spreadsheets?|google sheets|advanced excel|excel macros?", "Microsoft Excel", "direct", "Spreadsheet skills are listed as Microsoft Excel in most Australian job ads."),
  skill("kanban|sprint|backlog|stand-?ups?|scrum master|jira", "Agile delivery", "direct", "Backlogs, sprints and Kanban boards are part of agile delivery."),
  skill("qlik(view|sense)?|cognos|microstrategy|business objects|crystal reports|bi tools|reporting tools", "Data visualisation", "cross-border",
    "Overseas reporting and dashboard tools match the data visualisation skills that Australian job ads list as Power BI or Tableau."),
  skill("data (cleaning|cleansing|wrangling|preparation|munging)", "Data analysis", "direct", "Cleaning and preparing data is part of data analysis."),
  skill("predictive (model(l)?ing|analytics)|ml models?|machine-learning models?", "Machine learning", "direct", "Predictive models are what Australian job ads call machine learning."),
  skill("shell scripts?|unix scripting|linux administration|unix administration", "Linux", "direct", "Linux and Unix administration is listed as Linux in Australian job ads."),
  skill("web services|web apis?", "API design", "direct", "Building web services is what Australian job ads call API design."),
  skill("regression testing|test cases?|test plans?|test scripts?", "Manual testing", "direct", "Writing and running test cases by hand is manual testing."),
  skill("copilot|prompt writing|chatgpt prompts?", "Prompt engineering", "direct", "Writing prompts for AI models is called prompt engineering."),
  skill("leetcode|competitive programming", "Data structures and algorithms", "direct", "This is the skill that Australian job ads list as data structures and algorithms."),
  skill("solid principles|clean code", "Object-oriented design", "direct", "Design patterns and clean code are listed as object-oriented design."),
  skill("build automation|release management|deployment automation|ci ?/ ?cd|continuous (delivery|deployment)", "CI/CD", "direct", "Automated builds and releases are listed as CI/CD."),
  skill("container orchestration|openshift|helm", "Kubernetes", "direct", "Container orchestration is listed as Kubernetes."),
  skill("infrastructure automation|infrastructure[- ]as[- ]code", "Infrastructure as code", "direct", "Automating infrastructure is listed as infrastructure as code."),
  skill("alerting|splunk|datadog|new relic", "Observability", "direct", "Monitoring, logging and alerting are listed as observability."),
  skill("team management|managing (a )?team|line management|supervis(ing|ion)|people (and|&) team leadership", "Team leadership", "cross-industry",
    "Leading people transfers to any Australian role that leads a team, also in technology."),
  skill("training (junior|new)|onboarding (new|junior)|knowledge transfer", "Mentoring", "cross-industry", "Coaching and training colleagues is called mentoring."),
  skill("client communication|report writing", "Communication", "direct", "Communication has the same meaning in Australia."),
  skill("customer management|vendor management|supplier management|cross[- ](department|functional)", "Stakeholder management", "cross-industry",
    "Working with clients, vendors and other teams is what Australian employers call stakeholder management."),
  skill("project (coordination|planning|delivery)|\\bpmo\\b|prince2|waterfall", "Project management", "direct", "Planning and delivering projects is project management."),
  skill("root cause|incident (debugging|analysis)|bug fixing", "Debugging and troubleshooting", "direct", "Finding and fixing faults is listed as debugging and troubleshooting."),
  skill("escalation|issue resolution|problem resolution", "Problem solving", "direct", "Fixing escalated issues shows problem solving."),
  skill("process mapping|use cases?|business requirements|\\bbrd\\b", "Requirements analysis", "direct", "These are standard requirements analysis tasks."),
  skill("documentation|confluence|api docs", "Technical documentation", "direct", "Writing guides and specifications is technical documentation."),
  skill("hypothesis testing|regression analysis|\\bspss\\b|\\bstata\\b|\\bsas\\b", "Statistics", "cross-border",
    "Statistical analysis and tools such as SPSS or SAS are listed as statistics in Australian job ads."),
  skill("data integration|pentaho|ssis|informatica|datastage|talend", "ETL and ELT pipelines", "cross-border",
    "Overseas integration tools and data pipelines match the ETL and ELT skills of Australian job ads."),
  skill("star schema|dimensional model", "Data warehousing", "direct", "Data warehouse design has the same meaning in Australia."),
  skill("er diagrams?|schema design|database schema|entity[- ]relationship", "Data modelling", "direct", "Designing schemas is data modelling."),
  skill("database tuning|performance tuning|indexing", "Database design and tuning", "direct", "Tuning queries and indexes is database design and tuning."),
  skill("data protection|privacy compliance", "Data privacy and compliance", "cross-border",
    "Data protection rules overseas (for example GDPR) match the privacy and compliance skills that Australian employers ask for."),
  skill("pen[- ]?tests?|vulnerability (assessment|scanning)", "Penetration testing", "direct", "Testing systems for weak points is penetration testing."),
  skill("ldap|active directory|single sign[- ]on|identity management", "Authentication and authorisation", "direct", "Identity and access work is listed as authentication and authorisation."),
  skill("\\bcnn\\b|\\brnn\\b|deep nets?", "Deep learning", "direct", "Neural networks are deep learning."),
  skill("image (processing|recognition|classification)", "Computer vision", "direct", "Working with images is computer vision."),
  skill("sentiment analysis|chatbots?", "Natural language processing", "direct", "Working with text is natural language processing."),
  skill("collaborative filtering", "Recommender systems", "direct", "Recommendation engines are recommender systems."),
  skill("ml pipelines?|machine learning pipelines?", "MLOps", "direct", "Deploying and running models is MLOps."),
];

// Indicative AQF levels. Not a formal assessment (PRD: formal credential verification is out of scope).
const AQF = [
  [/doctor|phd/, "AQF Level 10 (Doctoral degree)"], [/master|mba/, "AQF Level 9 (Masters degree)"],
  [/graduate (certificate|diploma)/, "AQF Level 8 (Graduate certificate or diploma)"], [/honours/, "AQF Level 8 (Bachelor honours degree)"],
  [/bachelor/, "AQF Level 7 (Bachelor degree)"], [/advanced diploma|associate degree/, "AQF Level 6"],
  [/\bdiploma\b/, "AQF Level 5 (Diploma)"], [/certificate (iii|iv)/, "AQF Level 3–4 (Certificate III or IV)"],
];
export const aqfOf = (q) => (AQF.find(([re]) => re.test(lower(q))) || [])[1] || "";

// A short id part from letters and digits. "C#" and "C++" give the same letters, so the caller adds a hash when two names collide.
const slug = (s) => lower(s).replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const hash = (s) => { let h = 5381; for (const c of String(s)) h = ((h << 5) + h + c.charCodeAt(0)) | 0; return (h >>> 0).toString(16).slice(0, 6); };

// Words that show a level in a title. They are not part of the role.
const LEVEL_WORDS = /\b(intern(ship)?|trainee|junior|jr|jnr|graduate|grad|senior|sr|snr|lead|principal|staff|mid[- ]?level|ii|iii|iv)\b\.?/g;
// "Senior Data Engineer, Lakehouse (Vietnam)" gives "data engineer": no place in brackets, no company, no level word
const roleBase = (title) => lower(title).replace(/\([^)]*\)/g, " ").split(/\s[-–—@|]\s|,|\sat\s/)[0].replace(LEVEL_WORDS, " ").replace(/\s+/g, " ").trim().replace(/^-+|-+$/g, "").replace(/\.+$/, "");

// The typed skills: a name, or { name, level, years }. The level and the years that the talent gave are kept (key: lower case name).
function typedSkills(p) {
  const out = new Map();
  for (const s of [...list(p.skillLevels), ...list(p.skills)]) {
    if (!s || typeof s !== "object" || !s.name) continue;
    const level = Number.isInteger(s.level) && s.level >= 1 && s.level <= 5 ? s.level : null;
    const years = typeof s.years === "number" && s.years >= 0 && s.years <= 40 ? s.years : null;
    out.set(lower(s.name), { level, years });
    const canon = canonicalSkillName(s.name);
    if (canon) out.set(lower(canon), { level, years });
  }
  return out;
}
const skillNames = (p) => [...new Set(list(p.skills).map((s) => String(s && typeof s === "object" ? s.name : s || "").trim()).filter(Boolean))];

/**
 * @param {object} profile  Profile (lists). `skills` can be names or { name, level, years }.
 * @param {string[]} evidence  CV evidence lines (private to the candidate)
 * @returns {{ skills: TranslatedSkill[], gaps: string[] }}
 */
export function translate(profile, evidence = []) {
  const p = profile || {};
  const ev = list(evidence).map(String);
  const fromCv = ev.length > 0;
  const overseas = list(p.studyCountry).some((c) => c && c !== "Australia");
  const typed = typedSkills(p);
  const out = new Map();
  const gaps = new Set();

  const RANK = { Limited: 0, Moderate: 1, Strong: 2 };
  // The first evidence line that shows this skill or role: by the pattern of the pair, by the taxonomy name, or by the words of the talent
  const lineFor = (re, mapped, original) => ev.find((line) => {
    const low = lower(line);
    if (re && re.test(low)) return true;
    if (skillsIn(line).includes(mapped)) return true;
    return [mapped, original].some((w) => lower(w).length > 3 && new RegExp(`(?:^|[^a-z0-9])${escRe(lower(w))}(?![a-z0-9])`).test(low));
  });

  const add = (item, original, source, re = null) => {
    let id = `${slug(item.mapped)}--${slug(original)}`;
    if (out.has(id) && out.get(id).mapped !== item.mapped) id += `-${hash(`${item.mapped}|${original}`)}`;
    const line = lineFor(re, item.mapped, original);
    // Evidence: Strong = a CV line shows it; Moderate = a role or a skill that the candidate gave; Limited = only a title
    const evidenceLevel = line ? "Strong" : source === "skill" ? "Moderate" : fromCv ? "Moderate" : "Limited";
    const own = source === "skill" ? typed.get(lower(item.mapped)) || typed.get(lower(original)) || null : null;
    // One card for each taxonomy name. A second source can make the evidence stronger.
    const same = [...out.values()].find((s) => s.mapped === item.mapped && s.source === source);
    if (same) {
      if (RANK[evidenceLevel] > RANK[same.evidence]) {
        same.evidence = evidenceLevel;
        same.evidenceText = line || same.evidenceText;
        if (source === "skill" && !(own && own.level)) same.level = EVIDENCE_LEVEL[evidenceLevel];
      }
      if (own && own.level && own.level > (same.level || 0)) same.level = own.level;
      if (own && own.years != null && own.years > (same.years || 0)) same.years = own.years;
      if (!same.original.includes(original)) same.original += `; ${original}`;
      return;
    }
    out.set(id, {
      id, source, original, mapped: item.mapped, kind: item.kind,
      anzsco: item.anzsco || "", occupation: item.occupation || "",
      reason: item.reason, evidence: evidenceLevel, evidenceText: line || "",
      status: "suggested",
      level: source === "skill" ? (own && own.level) || EVIDENCE_LEVEL[evidenceLevel] : null,
      years: source === "skill" && own ? own.years : null,
    });
    list(item.gaps).forEach((g) => gaps.add(g));
  };

  // ----- roles: a pair for an overseas title, a title of the role list, the other pairs, a general pair -----
  for (const original of list(p.currentRole).map(String)) {
    const base = roleBase(original);
    if (!base) continue;
    const hasPlace = /\([^)]*\)/.test(original);
    let found = ROLE_PAIRS.find((i) => i.overseas && (hasPlace || overseas) && i.test.test(base));
    if (found) found = { ...found, kind: "cross-border" };
    if (!found && ROLE_BY_LOWER.has(base)) {
      const exact = ROLE_BY_LOWER.get(base);
      found = { mapped: exact, kind: "direct", ...occupationOf(exact), reason: `${exact} has the same meaning in Australia.` };
    }
    if (!found) found = ROLE_PAIRS.find((i) => !i.overseas && !i.weak && i.test.test(base));
    if (!found) { const weak = ROLE_PAIRS.find((i) => i.weak && i.test.test(base)); if (weak) found = { ...weak, kind: "direct" }; }
    if (found) add(found, original, "role", found.test || null);
  }

  // ----- skills: the name or alias of the taxonomy, a pair of the library, or the name as it is -----
  for (const name of skillNames(p)) {
    const canon = canonicalSkillName(name);
    if (canon) {
      add({ mapped: canon, kind: "direct", reason: lower(canon) === lower(name) ? `${canon} has the same name in Australia.` : `Australian job ads list this skill as ${canon}.` }, name, "skill");
      continue;
    }
    const hit = SKILL_PAIRS.find((i) => i.test.test(lower(name)));
    if (hit) { add(hit, name, "skill", hit.test); continue; }
    const shown = skillsIn(name);
    // A skill with no translation keeps its name, so the candidate can still choose to share it
    if (shown.length === 1) add({ mapped: shown[0], kind: "direct", reason: `Australian job ads list this skill as ${shown[0]}.` }, name, "skill");
    else add({ mapped: name, kind: "direct", reason: "Australian employers use the same name for this skill." }, name, "skill", new RegExp(escRe(lower(name))));
  }

  // ----- qualifications: indicative AQF level -----
  for (const q of list(p.qualification)) {
    const level = aqfOf(q);
    if (!level) continue;
    const id = `aqf--${slug(q)}`;
    out.set(id, {
      id, source: "qualification", original: q + (overseas ? " (overseas)" : ""), mapped: level, kind: overseas ? "cross-border" : "direct",
      anzsco: "", occupation: "", reason: overseas
        ? "Qualifications of this type from overseas are usually close to this Australian (AQF) level. This is a guide, not a formal assessment."
        : "This is the Australian Qualifications Framework (AQF) level of this qualification.",
      evidence: fromCv ? "Moderate" : "Limited", evidenceText: "", status: "suggested", level: null, years: null,
    });
  }
  return { skills: [...out.values()], gaps: [...gaps] };
}
```

### Sample CV parse results (`js/api/mock/cv-samples.js`)

Create this file exactly. It has 5 ICT samples (data analyst, software developer, machine learning researcher, business analyst, systems administrator), each with a domain, a level, exact years, certifications and awards (some on purpose left out), a desired role, skills with levels and evidence lines, and the function `parseResultOf(sample)`. All people are made up:

```js
// MOCK BACKEND — sample CV parse results. The mock cannot read a real file, so it returns one of these.
// The UI shows a "Demo mode" banner in mock mode. All people here are made up (no real PII). All samples are ICT (3 domains only).
// File name rules (lower case): "fail" or "corrupt" → a parse failure; "ml", "machine", "research", "scientist" or "ai" → machine learning;
// "software", "developer", "backend", "java" or "swe" → software; "devops", "admin", "infra", "cloud" or "platform" → systems administrator;
// "analyst" or "business" (and not "data") → business analyst; any other name → the data analyst.
// A field that the CV does not show is not in `fields` and is not in `found` (the same as the real CV reader, plan R1 and F11).
// skills: the names as the person wrote them. skillLevels: the level (1 to 5) that the CV gives to a skill.
export const CV_SAMPLES = {
  data: {
    label: "Data analyst (BI Specialist), Vietnam",
    domain: "Data",
    fields: {
      qualification: ["Bachelor's degree"], fieldOfStudy: ["Information systems"], studyCountry: ["Vietnam"],
      currentRole: ["BI Specialist", "MIS Executive"], industry: ["Data"], years: "3–5 years", yearsExperience: 4.5, level: "Mid",
      skills: ["SQL", "Python", "Power BI", "Spreadsheets", "Data analysis", "Dashboards", "Informatica", "ER diagrams"],
      targetRole: ["Data Engineer"],
      certifications: [{ name: "Microsoft Certified: Power BI Data Analyst Associate", issuer: "Microsoft", year: 2024 }],
      awards: [{ name: "Smart City Hackathon Runner-up", kind: "hackathon", year: 2023 }],
    },
    skillLevels: [
      { name: "SQL", level: 4 }, { name: "Python", level: 3 }, { name: "Power BI", level: 4 }, { name: "Spreadsheets", level: 4 },
      { name: "Data analysis", level: 4 }, { name: "Dashboards", level: 3 }, { name: "Informatica", level: 2 }, { name: "ER diagrams", level: 3 },
    ],
    evidence: [
      "Built the weekly sales and stock dashboards in Power BI for 6 regional teams, replacing 14 manual spreadsheets.",
      "Wrote SQL queries and Python scripts to clean and join data from 5 source systems before each monthly report.",
      "Designed the report data model (ER diagrams) for the company data warehouse together with two engineers.",
      "Started to load data with Informatica jobs for the monthly reports.",
    ],
    missing: [],
  },
  software: {
    label: "Software developer (Java), India",
    domain: "Software Engineering",
    fields: {
      qualification: ["Bachelor's degree"], fieldOfStudy: ["Computer science"], studyCountry: ["India"],
      currentRole: ["Java Developer"], industry: ["Software Engineering"], years: "3–5 years", yearsExperience: 4.2, level: "Mid",
      skills: ["Java", "Spring Boot", "PostgreSQL", "REST APIs", "Docker", "Git", "Unit testing"],
      targetRole: ["Backend Engineer"],
      certifications: [{ name: "AWS Certified Developer - Associate", issuer: "Amazon Web Services", year: 2023 }],
      awards: [{ name: "Regional Hackathon Winner", kind: "hackathon", year: 2022 }],
    },
    skillLevels: [
      { name: "Java", level: 4 }, { name: "Spring Boot", level: 4 }, { name: "PostgreSQL", level: 3 }, { name: "REST APIs", level: 4 },
      { name: "Docker", level: 3 }, { name: "Git", level: 4 }, { name: "Unit testing", level: 3 },
    ],
    evidence: [
      "Built 12 REST endpoints in Java and Spring Boot for an order tracking service used by 3 internal teams.",
      "Designed the PostgreSQL schema and tuned 6 slow queries; the slowest page fell from 4 seconds to 600 ms.",
      "Wrote unit tests for the pricing rules with JUnit and ran them in a Jenkins pipeline on every commit.",
      "Packaged the service with Docker and shared the code in Git with pull request reviews.",
    ],
    missing: [],
  },
  ml: {
    label: "Machine learning researcher, Germany",
    domain: "AI & Machine Learning",
    // This CV does not state a desired role: the field stays empty and the screen shows a hint (plan F11).
    fields: {
      qualification: ["Master's degree"], fieldOfStudy: ["Mathematics"], studyCountry: ["Germany"],
      currentRole: ["Research Scientist"], industry: ["AI & Machine Learning"], years: "6–10 years", yearsExperience: 7, level: "Senior",
      skills: ["Python", "PyTorch", "Deep learning", "Statistics", "scikit-learn", "Model evaluation", "Feature engineering"],
      awards: [{ name: "Open Data Prediction Cup Gold Tier", kind: "data-science-competition", year: 2024 }],
    },
    skillLevels: [
      { name: "Python", level: 5 }, { name: "PyTorch", level: 4 }, { name: "Deep learning", level: 4 }, { name: "Statistics", level: 5 },
      { name: "scikit-learn", level: 4 }, { name: "Model evaluation", level: 4 }, { name: "Feature engineering", level: 3 },
    ],
    evidence: [
      "Trained and compared 6 deep learning models in PyTorch to predict equipment faults; the best model found 91% of the faults.",
      "Built the model evaluation set-up (cross-validation and error analysis) and ran the statistics tests for each paper.",
      "Used scikit-learn pipelines and feature engineering to cut the training time of the baseline model by 60%.",
      "Presented the results to 3 product teams and wrote the project documentation.",
    ],
    missing: [],
  },
  analyst: {
    label: "Business analyst, Philippines",
    domain: "Data",
    // This CV has no dates, so it shows no years of experience. It has no certification and no award.
    fields: {
      qualification: ["Bachelor's degree"], fieldOfStudy: ["Information technology"], studyCountry: ["Philippines"],
      currentRole: ["Business Analyst"], industry: ["Data"], years: "1–2 years", level: "Junior",
      skills: ["Requirements gathering", "SQL", "Power BI", "Dashboards", "Process mapping", "UAT", "Jira"],
      targetRole: ["Data Analyst"],
    },
    skillLevels: [
      { name: "Requirements gathering", level: 3 }, { name: "SQL", level: 3 }, { name: "Power BI", level: 3 }, { name: "Dashboards", level: 2 },
      { name: "Process mapping", level: 3 }, { name: "UAT", level: 3 }, { name: "Jira", level: 3 },
    ],
    evidence: [
      "Led requirements gathering workshops with 4 business teams and wrote 60 user stories for a customer portal.",
      "Wrote SQL queries and Power BI dashboards that showed the weekly ticket numbers to 3 managers.",
      "Mapped 9 business processes and ran UAT with 12 testers before each release.",
      "Tracked the backlog in Jira with a 2-week sprint plan.",
    ],
    missing: ["years"],
  },
  devops: {
    label: "Systems administrator, Brazil",
    domain: "Software Engineering",
    fields: {
      qualification: ["Bachelor's degree"], fieldOfStudy: ["Information technology"], studyCountry: ["Brazil"],
      currentRole: ["Systems Administrator"], industry: ["Software Engineering"], years: "6–10 years", yearsExperience: 8, level: "Senior",
      skills: ["Linux", "Bash scripting", "Ansible", "Docker", "Networking fundamentals", "Monitoring", "AWS"],
      targetRole: ["DevOps Engineer"],
      certifications: [{ name: "AWS Certified Solutions Architect - Associate", issuer: "Amazon Web Services", year: 2022 }],
    },
    skillLevels: [
      { name: "Linux", level: 5 }, { name: "Bash scripting", level: 4 }, { name: "Ansible", level: 3 }, { name: "Docker", level: 3 },
      { name: "Networking fundamentals", level: 4 }, { name: "Monitoring", level: 3 }, { name: "AWS", level: 3 },
    ],
    evidence: [
      "Ran 60 Linux servers for 3 teams and wrote Bash scripts that cut the patch time from 2 days to 3 hours.",
      "Moved the server set-up to Ansible playbooks, so that a new server took 20 minutes instead of 1 day.",
      "Set up monitoring and alerts that cut the number of night calls by half.",
      "Moved two internal tools to Docker containers on AWS.",
    ],
    missing: [],
  },
};

export function sampleFor(fileName) {
  const n = String(fileName || "").toLowerCase();
  if (/fail|corrupt/.test(n)) return null;
  if (/machine|(^|[^a-z])ml([^a-z]|$)|research|scientist|(^|[^a-z])ai([^a-z]|$)/.test(n)) return CV_SAMPLES.ml;
  if (/software|developer|backend|java|swe/.test(n)) return CV_SAMPLES.software;
  if (/devops|admin|infra|cloud|platform/.test(n)) return CV_SAMPLES.devops;
  if (/data/.test(n)) return CV_SAMPLES.data;
  if (/analyst|business/.test(n)) return CV_SAMPLES.analyst;
  return CV_SAMPLES.data;
}

// The answer of GET /cv/parse/:id when the read is done. It has the shape of the real answer:
// fields (only what the CV shows), detected, missing, evidence, domain, skills [{ name, level }] and found (the V2 fields that the CV showed).
export function parseResultOf(sample) {
  const detected = Object.keys(sample.fields).filter((k) => !sample.missing.includes(k));
  const fields = Object.fromEntries(detected.map((k) => [k, sample.fields[k]]));
  const filled = (k) => k in fields && !(Array.isArray(fields[k]) && !fields[k].length);
  return {
    fields, detected, missing: sample.missing, evidence: sample.evidence, sampleLabel: sample.label, domain: sample.domain, skills: sample.skillLevels,
    found: { currentRole: filled("currentRole"), targetRole: filled("targetRole"), level: filled("level"), yearsExperience: filled("yearsExperience"),
      certifications: filled("certifications"), awards: filled("awards") },
  };
}
```

### Job catalogue and recommendation (mock)

> This section describes the **browser-only mock** (`?mock=1`). Its data is ICT only (24 jobs, 10 sample talent, 5 CV samples, 4 job file samples), taken from the same taxonomy and synthetic data as the real backend, in a smaller form. It has **no formula engine**: its match is the simple rank below, and no number is shown to the user. The real backend (`jinder_platform`) uses the 50 jobs, the 50 talent and the six rewritten formulas: the Fit score is `0.55 × fit + 0.45 × FRS*`, and a job is recommended when the score is 45 or more. Do not copy the mock rules into the real backend.

**All job data is internal Jinder data** (AI_Rule.md Rule 11): no links to other sites, no provider names in the UI, internal ids.

**Catalogue (`seed-jobs.js`, embedded below).** No CSV file, no `fetch`. The job fields of the file: `key, title, company, domain, specialisation, level, minYears, maxYears, type, workMode, city, area, salary { min, max, unit }, occupation { code, title }, skills [{ name, level, must }], certifications { required, preferred }, awards { preferred }, education, postedDaysAgo, closesInDays, description`.

**Row mapping (`jobs.js`):**
- `id` = `job-` + `key`. `category` = the domain (one of the 3). `location` = the city ("Remote" for a remote job); `area` = the area text. `anzsco` and `occupation` come from `occupation.code` and `occupation.title` (a demo mapping from the taxonomy).
- `salary` = `salaryText(...)`: "$a – $b per year", "$a per day" for a day rate (`salaryUnit` is `year` or `day`); no amount → "Market competitive".
- `postedAt` = now − `postedDaysAgo` days; `closesAt` = now + `closesInDays` days (so every catalogue job is open). `status` = "open" while `closesAt` ≥ now.
- `description` = the full text with its line breaks (never cut). `summary` = the first whole sentences that fit in 200 characters (headings and bullets left out).
- `skills` = the names of `skills`; `skillRequirements` = `[{ name, level, must }]`; also `level`, `specialisation`, `minYears`, `maxYears`, `workMode`, `educationMin`, `certifications`, `awards`. A posted job (`db.postedJobs`) has the old fields only.

**Skills (`SKILL_TABLE`).** The 172 skills of the taxonomy, each `[name, aliases separated by "|", related skills separated by "|"]`. The patterns are built from it when the file loads. `skillsIn(text)` gives the names that a text shows, in order of place. `canonicalSkillName(text)` gives the taxonomy name of a text that is a name or an alias ("golang" gives "Go"). Word-safe rules, as in the real backend: `C#`, `C++`, `.NET`, `Node.js` and `CI/CD` are found as whole words; `R`, `C` and `Go` count only inside a list ("Python, R, SQL"); `Swift`, `Rust`, `Ruby` and `Spark` count only with a capital letter; a word inside another word never counts ("java" is not in "javascript", "js" is not in "node.js"); a short alias ("js", "ml", "k8s") counts only when it is the whole text of a skill. `RELATED` is a map of the related skills of the taxonomy (both ways). `CATEGORY_MAP` has the 3 domains only.

**Per-skill match (`skillMatch(jobSkills, names)`)** — decision Q1:
- `names` = a map (lower case → display name) of the person's skills: `profile.skills` (a name, or an object with a `name`) + the `mapped` names of accepted and edited translated skills (kind skill), each also expanded through `skillsIn`. For an employer view the names come from the shared skills only (`namesFromList`).
- For each job skill: in `names` → `match`; else, if the person has a skill that the taxonomy lists as related → `partial` with `via`; else `gap`.
- `coverage = round((matches + 0.5 × partials) / job skills × 100)`, `null` when the job has no skills. Coverage summarises the skills of **one job**; it is not a score on a person.

**Rank (`matcher(profile)(job)` → `JobMatch`)** — for ordering and recommendations only, never shown as a number:
- `rank = round(coverage × 0.4) + role + domain 15 + location 10 + work type 5 + level`.
- **Role:** the closeness of a role to the job: 3 = the same role phrase or the same occupation ("Senior Data Engineer, Lakehouse" has the role phrase "data engineer"), 2 = the same field and the same kind of role, 1 = the same field only, 0.5 = only a role noun such as "engineer", 0 = nothing. A target role gives 30, 22, 14, 8, 0 points; a past role gives 18, 13, 8, 4, 0. The larger one counts.
- **Domain** (the job domain is in the target domains or the domains worked in): 15. **Location** (the city is chosen, or the job is Remote): 10. **Work type** (no work types chosen also counts): 5. **Level:** the same level 8, one step apart 4, more than one step 0. Work type is not a filter; a mismatch is a note.
- `reasons`, in order: "Matches your target role (ANZSCO: {occupation})" / "Close to a role you have had" / "Similar type of role ({title})", "You have {m} of the {n} skills" (+ ", and {p} related"), "In a domain you chose: …", "Level fits: {level}", "Remote role: you can work from anywhere in Australia" / "Location you prefer: …". `notes`: "This role is {type}", "This role is {level} level", "Location: {city}" (only when the user chose locations), "This job lists no skills yet".
- `recommended` = rank ≥ 45 and the level is not 2 or more steps away and (more than one reason, or a strong target-role match).
- **Never** use nationality, ethnicity, gender, age, visa status or country of study. Write this in a code comment.
- The demo talent gets 7 recommended jobs. Each of the 5 CV samples gets 3 to 8.

**Functions** (all take `db` first, so posted jobs are included):
- `recommend(db, profile, limit, exclude)`: open jobs not in `exclude` (skipped + applied), with `match.recommended`, sorted by rank, then newest, then id.
- `searchJobs(db, profile, { q, location, limit }, exclude)`: open jobs not skipped; `location` must equal the city; every lower-case word of `q` must appear in "title company occupation domain specialisation level skills area". Sorted by rank. Returns `{ total, items }`.
- `jobDetail(db, profile, id)`: the job (open or closed) + `description` + `similar` = up to 3 open jobs with the same ANZSCO code or 3 or more shared skills, sorted by rank.
- `suggestSkills(text)`: the skill names that `skillsIn` finds in the text (max 10).

**Applications, recruiter, platform (mock):** follow the endpoint table and the state machine exactly. The snapshot match is `skillMatch(job.skills, namesFromList(snapshot.skills))`. `TOP_N` = 5. Entitlements default to "basic".

### Demo data (`js/api/mock/seed-demo.js`)

Written once into the store when `CONFIG.MOCK_DEMO_DATA` is true (decision Q8). All people are made up. Recruiters see the sample talent only by alias. It is the story of the real seed in a smaller form:
- **10 sample talent** with ICT profiles (Jade Koala, Plum Heron, Amber Finch, Cyan Puffin, Lime Kestrel, Coral Fox, Mint Fox, Cyan Falcon, Sage Lynx, Slate Seal): level, exact years, domain, skills with level and years, certifications, awards, locations, work modes and private evidence lines. They cannot sign in.
- **Talent demo Teal Heron** (Linh Nguyen, `candidate@demo.jinder.app`): a Mid data analyst who studied in Vietnam and wants to be a Data Engineer. 8 skills with levels, one certification, one award. Her two overseas titles are one cross-border Data Analyst card. She is in interview for the Data Engineer job and has the alert with 3 interview times.
- **Employer demo Alex Morgan, Bluebushworks** (`recruiter@demo.jinder.app`) with 4 jobs: Data Engineer, Solar Analytics (open); Senior Backend Engineer, Installer Platform (open); Machine Learning Engineer, Solar Forecasting (closes in 4 days); Contract Data Engineer, Billing Migration (closed 2 days ago, a day rate). 7 applications: Data Engineer 3 (Jade Koala in review, Teal Heron in interview, Plum Heron applied with a note), Backend 2 (Amber Finch applied, Cyan Puffin in review), Machine Learning 1 (Lime Kestrel applied), the closed contract 1 (Coral Fox confirmed, offer sent, name shared). The employer has 3 alerts. The jobs have activity events (the same numbers at each start) for the Premium charts. The password of both demo accounts is `demo1234`.
Create the file exactly:

```js
// MOCK BACKEND — demo data, written once into the mock store. The real backend replaces this file.
// All people and companies are made up. It tells the same story as the real seed (jinder_platform/jinder/seed.py), in a smaller form:
//   - 10 sample talents with ICT profiles (aliases, skills and certifications from the synthetic talent file). Employers see them only by alias.
//   - Talent demo Teal Heron (Linh Nguyen): a Mid data analyst who studied in Vietnam and wants to become a Data Engineer. She is in interview.
//   - Employer demo Alex Morgan (Bluebushworks) with 4 jobs (from the synthetic demo file), applications, alerts and some activity for the charts.
// The demo accounts are listed in config.js (MOCK_DEMO_ACCOUNTS). The password of both is "demo1234".
import { newId, sharedProfileOf, notify } from "./core.js";
import { demoHash } from "./db.js";
import { translateKeeping } from "./routes-account.js";
import { skillMatch, namesFromList, salaryText } from "./jobs.js";
import { YEARS } from "../../data/reference.js";

export const DEMO_PASSWORD = "demo1234"; // same as CONFIG.MOCK_DEMO_PASSWORD

const DAY = 864e5;
const at = (days) => new Date(Date.now() + days * DAY).toISOString();
// The band of "Total years of work experience" for an exact number of years (the same rule as the server and the onboarding)
const bandOf = (y) => (y < 1 ? YEARS[0] : y < 3 ? YEARS[1] : y < 6 ? YEARS[2] : y <= 10 ? YEARS[3] : YEARS[4]);

// Anonymous sample talents (no names, no countries in what employers see). skills: [name, level 1 to 5, years]
const SAMPLE_CANDIDATES = [
  { alias: "Jade Koala", currentRole: ["Data Warehouse Engineer"], level: "Senior", yearsExperience: 7.1, industry: ["Data"], specialisation: "Data engineering",
    qualification: ["Bachelor's degree"], fieldOfStudy: ["Information systems"], studyCountry: ["Philippines"],
    skills: [
      ["Snowflake", 5, 5.0], ["SQL", 5, 7.0], ["Data warehousing", 5, 7.0], ["dbt", 5, 3.5], ["Data modelling", 5, 6.0],
      ["ETL and ELT pipelines", 4, 6.0], ["Python", 4, 4.0], ["Google BigQuery", 3, 1.5], ["Database design and tuning", 4, 5.0],
      ["Data governance", 3, 3.0], ["Stakeholder management", 3, 4.0],
    ],
    certifications: [{ name: "SnowPro Core Certification", issuer: "Snowflake", year: 2021 }], awards: [],
    targetRole: ["Data Warehouse Engineer", "Data Engineer"], targetIndustries: ["Data"], locations: ["Melbourne"], workModes: ["Hybrid"], workTypes: ["Full-time"],
    evidence: [
      "Own a Snowflake data warehouse of 900 tables for billing and sales; query cost fell by 33% after clustering and data warehouse sizing.",
      "Moved the sales mart from an older data warehouse to Snowflake with no gaps in reporting.",
      "Introduced dbt tests and Data modelling standards; tickets about wrong numbers fell from 22 to 4 a quarter.",
      "Wrote Data governance rules for the data owners and Technical documentation for the key tables.",
    ] },
  { alias: "Plum Heron", currentRole: ["Data Engineer"], level: "Mid", yearsExperience: 4.6, industry: ["Data"], specialisation: "Data engineering",
    qualification: ["Bachelor's degree"], fieldOfStudy: ["Information technology"], studyCountry: ["India"],
    skills: [
      ["SQL", 4, 4.6], ["Python", 4, 4.6], ["Apache Spark", 4, 3.5], ["Apache Airflow", 4, 3.5], ["AWS", 4, 4.0], ["Amazon S3", 4, 4.0],
      ["ETL and ELT pipelines", 4, 4.6], ["Data modelling", 3, 3.0], ["Data warehousing", 3, 3.0], ["Amazon Redshift", 3, 3.0], ["Git", 3, 4.6],
      ["Apache Kafka", 2, 1.0], ["Data quality", 3, 2.5], ["AWS Lambda", 3, 2.0],
    ],
    certifications: [{ name: "AWS Certified Data Engineer - Associate", issuer: "Amazon Web Services", year: 2025 }], awards: [],
    targetRole: ["Data Engineer", "Data Platform Engineer"], targetIndustries: ["Data"], locations: ["Sydney"], workModes: ["Hybrid"], workTypes: ["Full-time"],
    evidence: [
      "Run the sales data lake on Amazon S3 and Apache Spark: 3 TB loads each day in 70 minutes, down from 4 hours.",
      "Own 60 Apache Airflow DAGs; on-time delivery of the morning reports rose from 88% to 99%.",
      "Added Data quality checks (row counts and null rates) to the core tables and found many upstream issues in the first month.",
      "Modelled the Amazon Redshift sales mart, tuned its SQL and wrote small AWS Lambda functions that trigger the loads.",
    ] },
  { alias: "Amber Finch", currentRole: ["Software Engineer"], level: "Senior", yearsExperience: 8.6, industry: ["Software Engineering"], specialisation: "Backend",
    qualification: ["Master's degree"], fieldOfStudy: ["Computer science"], studyCountry: ["India", "Australia"],
    skills: [
      ["Go", 5, 6.0], ["PostgreSQL", 5, 8.0], ["SQL", 5, 8.5], ["Apache Kafka", 4, 4.5], ["System design", 5, 6.0],
      ["Microservices architecture", 5, 5.5], ["API design", 5, 7.0], ["Docker", 4, 6.0], ["Python", 3, 4.0], ["ETL and ELT pipelines", 3, 2.0],
      ["Apache Airflow", 2, 1.0], ["Apache Spark", 2, 0.8], ["AWS", 4, 4.0], ["Technical leadership", 4, 3.0],
    ],
    certifications: [{ name: "Confluent Certified Developer for Apache Kafka", issuer: "Confluent", year: 2023 }], awards: [],
    targetRole: ["Data Engineer", "Big Data Engineer"], targetIndustries: ["Data", "Software Engineering"], locations: ["Melbourne"], workModes: ["Hybrid", "Remote"], workTypes: ["Full-time", "Contract"],
    evidence: [
      "Designed an event pipeline on Apache Kafka that moves 2.4 million order events a day into PostgreSQL reporting tables.",
      "Cut the p95 latency of the order search API from 1.8 seconds to 240 ms with new PostgreSQL indexes and a result cache.",
      "Moved nightly Python batch exports to Apache Airflow and built a first Apache Spark job for the billing team.",
      "Split a monolith into Go services using a Microservices architecture and shared API design guidelines.",
    ] },
  { alias: "Cyan Puffin", currentRole: ["Full-stack Engineer"], level: "Mid", yearsExperience: 3.4, industry: ["Software Engineering"], specialisation: "Full-stack",
    qualification: ["Master's degree"], fieldOfStudy: ["Computer science"], studyCountry: ["Germany"],
    skills: [
      ["Python", 5, 3.4], ["Django", 4, 3.0], ["React", 4, 2.5], ["PostgreSQL", 4, 3.0], ["JavaScript", 3, 3.0], ["TypeScript", 4, 2.0],
      ["API design", 4, 2.5], ["Git", 4, 3.4], ["LLM APIs", 3, 1.2], ["Prompt engineering", 3, 1.2], ["Retrieval-augmented generation", 2, 0.7],
      ["Product thinking", 3, 2.0], ["SQL", 3, 3.0], ["Unit and integration testing", 4, 2.5],
    ],
    certifications: [{ name: "NVIDIA-Certified Associate: Generative AI LLMs", issuer: "NVIDIA", year: 2025 }], awards: [{ name: "Applied AI Hackathon Finalist", kind: "hackathon", year: 2025 }],
    targetRole: ["Generative AI Engineer", "AI Engineer"], targetIndustries: ["AI & Machine Learning"], locations: ["Sydney"], workModes: ["Hybrid"], workTypes: ["Full-time"],
    evidence: [
      "Built a Django and React support portal for 2,500 customers and own the API design for its 30 endpoints.",
      "Added an LLM APIs assistant that drafts replies for agents; it cut the average reply time by 22% in a 6-week pilot.",
      "Wrote the Prompt engineering guide and a test set for the assistant.",
      "Prototyped Retrieval-augmented generation over the help articles with a first search index.",
    ] },
  { alias: "Lime Kestrel", currentRole: ["Data Scientist"], level: "Senior", yearsExperience: 8.5, industry: ["Data"], specialisation: "Data science",
    qualification: ["Master's degree"], fieldOfStudy: ["Statistics"], studyCountry: ["Australia"],
    skills: [
      ["Python", 5, 8.0], ["Statistics", 5, 8.5], ["Machine learning", 5, 7.0], ["scikit-learn", 3, 7.0], ["XGBoost", 4, 5.0],
      ["Experimentation and A/B testing", 5, 6.0], ["Time series forecasting", 4, 5.0], ["SQL", 4, 8.0], ["Feature engineering", 3, 6.0],
      ["Data storytelling", 4, 5.0], ["PyTorch", 2, 1.5], ["R", 3, 6.0], ["Model evaluation", 4, 5.0], ["Stakeholder management", 4, 5.0],
    ],
    certifications: [], awards: [{ name: "Speaker, Applied Statistics Meetup", kind: "conference-talk", year: 2024 }, { name: "National Forecasting Challenge Top 10", kind: "data-science-competition", year: 2023 }],
    targetRole: ["Machine Learning Engineer"], targetIndustries: ["AI & Machine Learning"], locations: ["Brisbane"], workModes: ["Hybrid"], workTypes: ["Full-time"],
    evidence: [
      "Built the Time series forecasting model that sets weekly stock for 1,200 products; the error fell from 19% to 11%.",
      "Run Experimentation and A/B testing for pricing; a 5-week test lifted the revenue per visit by 3.4%.",
      "Trained XGBoost and scikit-learn models for lead scoring that the sales team uses every day.",
      "Started to move models to production with PyTorch; I want a Machine learning engineering role.",
    ] },
  { alias: "Coral Fox", currentRole: ["Data Engineer"], level: "Mid", yearsExperience: 3.8, industry: ["Data"], specialisation: "Data engineering",
    qualification: ["Master's degree"], fieldOfStudy: ["Information technology"], studyCountry: ["Australia"],
    skills: [
      ["Azure Data Factory", 4, 3.0], ["Azure", 4, 3.5], ["Databricks", 4, 2.5], ["Apache Spark", 4, 2.5], ["Microsoft Fabric", 3, 1.2],
      ["Python", 4, 3.8], ["SQL", 4, 3.8], ["Data lakehouse", 3, 2.0], ["ETL and ELT pipelines", 4, 3.5], ["Git", 3, 3.5],
      ["Machine learning", 3, 1.0], ["scikit-learn", 3, 0.8], ["MLflow", 1, 0.4], ["Feature engineering", 2, 0.5],
    ],
    certifications: [{ name: "Microsoft Certified: Fabric Data Engineer Associate", issuer: "Microsoft", year: 2025 }, { name: "Databricks Certified Data Engineer Associate", issuer: "Databricks", year: 2024 }], awards: [],
    targetRole: ["Machine Learning Engineer"], targetIndustries: ["AI & Machine Learning"], locations: ["Adelaide", "Melbourne"], workModes: ["Hybrid"], workTypes: ["Full-time"],
    evidence: [
      "Built a lakehouse on Databricks and Azure Data Factory for a online shop with 180 tables and a nightly refresh in 55 minutes.",
      "Converted legacy SQL jobs into Apache Spark notebooks and cut the run cost.",
      "Trained a scikit-learn churn model on the lakehouse tables and logged the runs in MLflow as my first hands-on Machine learning project.",
      "Moved the billing reports to Microsoft Fabric as a pilot for 2 teams.",
    ] },
  { alias: "Mint Fox", currentRole: ["Data Engineer"], level: "Junior", yearsExperience: 1.9, industry: ["Data"], specialisation: "Data engineering",
    qualification: ["Advanced diploma"], fieldOfStudy: ["Information technology"], studyCountry: ["Australia"],
    skills: [
      ["SQL", 4, 1.9], ["Python", 3, 1.5], ["Apache Airflow", 2, 1.0], ["ETL and ELT pipelines", 3, 1.5], ["PostgreSQL", 3, 1.7], ["Git", 3, 1.8],
      ["Pandas", 3, 1.5], ["Amazon S3", 2, 1.0], ["Data modelling", 2, 1.0], ["AWS", 2, 1.0], ["Microsoft Excel", 3, 1.5], ["Data analysis", 3, 1.2],
    ],
    certifications: [], awards: [],
    targetRole: ["Data Engineer"], targetIndustries: ["Data"], locations: ["Melbourne"], workModes: ["Onsite", "Hybrid"], workTypes: ["Full-time"],
    evidence: [
      "Built 12 ETL and ELT pipelines in Python and SQL that load sales data into PostgreSQL every night.",
      "Moved 4 pipelines to Apache Airflow with retries and alerts; failed nightly loads fell from 9 a month to 1.",
      "Stored raw files in Amazon S3 and drew the first star schema with Data modelling guidance from a senior engineer.",
      "Checked vendor files with Pandas before each load and used Git branches for every pipeline change.",
    ] },
  { alias: "Cyan Falcon", currentRole: ["Machine Learning Engineer"], level: "Mid", yearsExperience: 4.2, industry: ["AI & Machine Learning"], specialisation: "Machine learning engineering",
    qualification: ["Master's degree"], fieldOfStudy: ["Computer science"], studyCountry: ["India"],
    skills: [
      ["Python", 5, 4.2], ["PyTorch", 3, 3.0], ["XGBoost", 4, 3.5], ["Machine learning", 5, 4.0], ["scikit-learn", 4, 4.0],
      ["Model evaluation", 4, 3.0], ["Docker", 4, 3.0], ["AWS", 3, 2.5], ["MLflow", 4, 2.0], ["Amazon SageMaker", 2, 1.2], ["Kubernetes", 2, 0.8],
      ["CI/CD", 2, 1.2], ["Git", 3, 4.0], ["MLOps", 3, 1.2],
    ],
    certifications: [{ name: "AWS Certified Machine Learning Engineer - Associate", issuer: "Amazon Web Services", year: 2025 }], awards: [],
    targetRole: ["MLOps Engineer", "ML Platform Engineer"], targetIndustries: ["AI & Machine Learning"], locations: ["Sydney"], workModes: ["Hybrid"], workTypes: ["Full-time"],
    evidence: [
      "Built and shipped an XGBoost model that scores 90,000 insurance quotes a day and lifted conversions by 6%.",
      "Packaged the Python scoring service with Docker and deployed it on AWS behind a low-latency API.",
      "Track experiments in MLflow and trained a PyTorch model for document triage using a Model evaluation checklist.",
      "Want to move to MLOps: set up a first Amazon SageMaker pipeline and CI/CD checks for 2 models.",
    ] },
  { alias: "Sage Lynx", currentRole: ["Site Reliability Engineer"], level: "Senior", yearsExperience: 8.2, industry: ["Software Engineering"], specialisation: "Platform and DevOps",
    qualification: ["Bachelor's degree (Honours)"], fieldOfStudy: ["Electrical and computer engineering"], studyCountry: ["New Zealand"],
    skills: [
      ["Kubernetes", 5, 6.0], ["Prometheus", 3, 5.0], ["Grafana", 3, 5.0], ["Observability", 5, 5.5], ["Site reliability engineering", 5, 6.0],
      ["Linux", 5, 8.0], ["Go", 4, 4.0], ["Terraform", 4, 5.0], ["AWS", 3, 6.0], ["Incident response", 4, 6.0], ["Docker", 3, 7.0], ["CI/CD", 4, 5.0],
      ["Networking fundamentals", 3, 6.0], ["Technical leadership", 4, 3.0],
    ],
    certifications: [{ name: "Certified Kubernetes Administrator", issuer: "Cloud Native Computing Foundation", year: 2022 }, { name: "AWS Certified DevOps Engineer - Professional", issuer: "Amazon Web Services", year: 2023 }, { name: "HashiCorp Certified: Terraform Associate", issuer: "HashiCorp", year: 2021 }], awards: [],
    targetRole: ["Site Reliability Engineer", "Platform Engineer"], targetIndustries: ["Software Engineering"], locations: ["Melbourne"], workModes: ["Remote", "Hybrid"], workTypes: ["Full-time"],
    evidence: [
      "On-call lead for Incident response on a platform with 120 services; cut the mean time to recover from 52 to 14 minutes.",
      "Defined service level objectives with Site reliability engineering practice; error-budget reports go to every team each week.",
      "Built the Prometheus and Grafana stack and the Observability dashboards; alert noise fell by 65%.",
      "Wrote a Go operator that scales Kubernetes jobs and saves about a third of the node hours.",
    ] },
  { alias: "Slate Seal", currentRole: ["Data Analyst"], level: "Mid", yearsExperience: 4.9, industry: ["Data"], specialisation: "Data analytics",
    qualification: ["Master's degree"], fieldOfStudy: ["Data science"], studyCountry: ["Australia"],
    skills: [
      ["SQL", 5, 4.9], ["Python", 4, 3.5], ["Pandas", 4, 3.5], ["Data analysis", 4, 4.9], ["Data visualisation", 5, 4.5], ["Statistics", 3, 3.0],
      ["Experimentation and A/B testing", 3, 2.0], ["scikit-learn", 2, 1.0], ["Machine learning", 3, 1.5], ["Tableau", 4, 3.0],
      ["Microsoft Excel", 4, 4.9], ["Data storytelling", 4, 3.5], ["Looker", 3, 2.0], ["Stakeholder management", 3, 2.0],
    ],
    certifications: [{ name: "Tableau Certified Data Analyst", issuer: "Salesforce", year: 2023 }], awards: [{ name: "Open Data Prediction Cup, Silver Tier", kind: "data-science-competition", year: 2024 }],
    targetRole: ["Data Scientist"], targetIndustries: ["Data", "AI & Machine Learning"], locations: ["Sydney"], workModes: ["Hybrid", "Remote"], workTypes: ["Full-time"],
    evidence: [
      "Own the SQL model behind the weekly growth report for 4 product teams and replaced 18 manual spreadsheets.",
      "Designed and read out 12 Experimentation and A/B testing results; 3 changes shipped with a combined 7% sign-up lift.",
      "Built a first scikit-learn churn model on Pandas features as a Machine learning side project.",
      "Teach Tableau and Looker basics in a monthly workshop for colleagues.",
    ] },
];

// The demo talent: a Mid data analyst who studied in Vietnam and wants to become a Data Engineer. Her titles are overseas titles, so the
// translation shows the cross-border step ("BI Specialist" and "MIS Executive" become one Data Analyst card). She has 8 skills with levels,
// one certification and one award. She is a strong fit for data analyst jobs, a medium fit for data engineering jobs, and a weak fit for backend jobs.
const DEMO_TALENT = {
  alias: "Teal Heron", currentRole: ["BI Specialist", "MIS Executive"], level: "Mid", yearsExperience: 4.5, industry: ["Data"], specialisation: "Data analytics",
  qualification: ["Bachelor's degree"], fieldOfStudy: ["Information systems"], studyCountry: ["Vietnam"],
  skills: [["SQL", 4, 4.5], ["Python", 3, 2.5], ["Power BI", 4, 3.5], ["spreadsheets", 4, 4.5], ["Data analysis", 4, 4.0], ["dashboards", 3, 3.5], ["Informatica", 2, 0.8], ["ER diagrams", 3, 2.0]],
  certifications: [{ name: "Microsoft Certified: Power BI Data Analyst Associate", issuer: "Microsoft", year: 2024 }],
  awards: [{ name: "Smart City Hackathon Runner-up", kind: "hackathon", year: 2023 }],
  targetRole: ["Data Engineer"], targetIndustries: ["Data"], locations: ["Melbourne", "Sydney"], workModes: ["Hybrid", "Remote"], workTypes: ["Full-time"],
  evidence: [
    "Built the weekly sales and stock dashboards in Power BI for 6 regional teams, replacing 14 manual spreadsheets.",
    "Wrote SQL queries and Python scripts to clean and join data from 5 source systems before each monthly report.",
    "Designed the report data model (ER diagrams) for the company data warehouse together with two engineers.",
    "Started to load data with Informatica jobs for the monthly reports.",
  ],
};

// The 4 jobs of the demo employer. The new fields (level, years, work mode, skill levels, certifications, awards) are only for the job pages of talent:
// the employer screens of the mock keep the old fields (plan F9).
const DEMO_JOBS = [
  {
    key: "demo-data-engineer-mid", title: "Data Engineer, Solar Analytics", company: "Bluebushworks",
    domain: "Data", specialisation: "Data engineering", level: "Mid", minYears: 3, maxYears: 6,
    type: "Full-time", workMode: "Hybrid", city: "Sydney", area: "Sydney NSW",
    salary: { min: 118000, max: 138000, unit: "year" }, occupation: { code: "262111", title: "Data Engineer" },
    skills: [
      { name: "SQL", level: 4, must: true }, { name: "Python", level: 4, must: true }, { name: "ETL and ELT pipelines", level: 3, must: true },
      { name: "Data modelling", level: 3, must: true }, { name: "Apache Airflow", level: 3, must: false },
      { name: "Snowflake", level: 3, must: false }, { name: "dbt", level: 3, must: false }, { name: "AWS", level: 3, must: false },
      { name: "Git", level: 3, must: false }, { name: "Data quality", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["SnowPro Core Certification"] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 6, closesInDays: 30,
    description: `## About the role

Bluebushworks helps solar and battery installers quote, plan and track their jobs, and every installed system reports its output back to us every five minutes. The Solar Analytics team of five turns those readings into reports for installers and homeowners. We need a mid-level data engineer to take over the pipelines that load, clean and join this data. This is a Hybrid role in our Sydney office, close to the installers' product team.

## What you will do

- Run and improve the pipelines that load system readings and weather data into Snowflake.
- Schedule the jobs in Apache Airflow and handle retries and late data.
- Model tables for systems, sites and installers, so that reports stay quick.
- Move older SQL scripts into dbt models with tests.
- Add checks that catch a dead inverter feed before a homeowner does.
- Answer data questions from the product and support teams.

## What you bring

- 3 to 6 years in data engineering or a data-heavy developer role.
- SQL and Python at an advanced level (4 of 5), with tests for both.
- ETL and ELT pipelines at a proficient level (3 of 5): loads, retries and backfills.
- Data modelling at a proficient level, with clean keys and clear names.
- A habit of writing short notes so that others can run your jobs.

## Nice to have

- Apache Airflow, Snowflake or dbt in production.
- AWS basics, and Git habits for team work.
- Data quality tools or tests that you built.

## Tech stack

Python, SQL, Apache Airflow, Snowflake and dbt on AWS, with Git for all code.

## Certifications and awards

- Preferred certification: SnowPro Core Certification.

## What we offer

- $118,000 to $138,000 a year, plus 12% superannuation.
- Hybrid work: three days a week in our Sydney office and two at home.
- Four weeks of annual leave, plus two extra days to spend with family.
- A learning budget of $2,000 a year.
- A small team where your pipelines reach customers within days.

## About Bluebushworks

Bluebushworks makes planning and quoting software for solar and battery installers. It was founded in 2019 and has about 90 people, with its head office in Sydney. Its software is used on thousands of home installations each year.

## How we hire

- A 30-minute call with the data lead.
- A SQL and Python exercise that you do live with one engineer.
- A talk with two teammates about a pipeline that you built.
- An answer within a week.`,
  },
  {
    key: "demo-backend-senior", title: "Senior Backend Engineer, Installer Platform", company: "Bluebushworks",
    domain: "Software Engineering", specialisation: "Backend", level: "Senior", minYears: 6, maxYears: 11,
    type: "Full-time", workMode: "Hybrid", city: "Sydney", area: "Sydney NSW",
    salary: { min: 165000, max: 185000, unit: "year" }, occupation: { code: "261313", title: "Software Engineer" },
    skills: [
      { name: "Python", level: 5, must: true }, { name: "Django", level: 4, must: true }, { name: "PostgreSQL", level: 4, must: true },
      { name: "AWS", level: 4, must: true }, { name: "System design", level: 4, must: true }, { name: "API design", level: 4, must: true },
      { name: "Docker", level: 4, must: false }, { name: "Redis", level: 3, must: false },
      { name: "Unit and integration testing", level: 4, must: false }, { name: "Mentoring", level: 3, must: false },
      { name: "Code review", level: 4, must: false }, { name: "Observability", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["AWS Certified Solutions Architect - Associate"] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 3, closesInDays: 26,
    description: `## About the role

The Installer Platform is the backend that 2,500 solar and battery installers use to quote jobs, order equipment and book inspections. It is a Django application with a PostgreSQL database, and it has doubled in size twice in three years. We are hiring a senior backend engineer to guide its next stage: faster quotes, safer integrations with equipment suppliers and a design that more engineers can work in at once. This is a Hybrid role in Sydney.

## What you will do

- Design and build new parts of the platform in Python and Django, from quotes to orders.
- Split the largest Django app into clear modules with strong boundaries.
- Build integrations with equipment suppliers and keep them safe when a supplier is slow.
- Speed up PostgreSQL queries and plan schema changes that do not lock tables.
- Run the platform on AWS and improve the logs, traces and alerts.
- Review code and coach three engineers.
- Write design notes for the choices that last.

## What you bring

- 6 to 11 years of backend work, with Python at an expert level (5 of 5).
- Django and PostgreSQL at an advanced level (4 of 5), including migrations at scale.
- AWS at an advanced level: queues, storage, networking and cost.
- System design and API design at an advanced level, shown in live systems.
- A habit of writing and talking in plain words about trade-offs.

## Nice to have

- Redis and Observability tools at a proficient level, and Docker at an advanced level.
- Strong Unit and integration testing habits.
- Code review and Mentoring that people thank you for.

## Tech stack

Python, Django, PostgreSQL, Redis and Docker on AWS. Tests use pytest, and the team uses Git with short reviews.

## Certifications and awards

- Preferred certification: AWS Certified Solutions Architect - Associate.

## What we offer

- $165,000 to $185,000 a year, plus 12% superannuation.
- Hybrid work: three days a week in our Sydney office and two at home.
- Four weeks of annual leave and an extra day off when you finish a big release.
- A $3,000 yearly budget for books, courses and conferences.
- A light on-call rota of one week in seven.

## About Bluebushworks

Bluebushworks makes planning and quoting software for solar and battery installers. It was founded in 2019 and has about 90 people, with its head office in Sydney. Its software is used on thousands of home installations each year.

## How we hire

- A call with the head of engineering.
- A design talk about a platform that you built, with two engineers.
- A pairing session on a Django and SQL problem.
- A decision within five working days.`,
  },
  {
    key: "demo-ml-engineer-mid", title: "Machine Learning Engineer, Solar Forecasting", company: "Bluebushworks",
    domain: "AI & Machine Learning", specialisation: "Machine learning engineering", level: "Mid", minYears: 2, maxYears: 5,
    type: "Full-time", workMode: "Hybrid", city: "Sydney", area: "Sydney NSW",
    salary: { min: 126000, max: 148000, unit: "year" }, occupation: { code: "261399", title: "Machine Learning Engineer" },
    skills: [
      { name: "Python", level: 4, must: true }, { name: "Machine learning", level: 4, must: true },
      { name: "Time series forecasting", level: 3, must: true }, { name: "scikit-learn", level: 4, must: true },
      { name: "Feature engineering", level: 3, must: true }, { name: "XGBoost", level: 3, must: false },
      { name: "Model evaluation", level: 3, must: false }, { name: "MLflow", level: 3, must: false }, { name: "Docker", level: 3, must: false },
      { name: "SQL", level: 3, must: false }, { name: "Git", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["AWS Certified Machine Learning Engineer - Associate"] }, awards: { preferred: ["data-science-competition"] },
    educationMin: "Bachelor's degree", postedDaysAgo: 17, closesInDays: 4,
    description: `## About the role

Bluebushworks tells installers how much power a home system will make on each day of the year, and its customers hold us to that number. The Forecasting team of four builds the models behind it, using weather, roof shape and the past output of thousands of live systems. We need a mid-level machine learning engineer to improve those forecasts and to move the training from notebooks to a scheduled pipeline. This is a Hybrid role in our Sydney office.

## What you will do

- Improve the solar output forecasts with Time series forecasting methods and better features.
- Train and compare models in scikit-learn and XGBoost, and keep the best ones.
- Build tests that show how each model behaves on cloudy weeks and on new roof types.
- Track runs in MLflow and package models in Docker for the serving team.
- Explain forecast errors to installers and to the customer support team.
- Query system data with SQL to find new signals.

## What you bring

- 2 to 5 years of applied machine learning, with Python and scikit-learn at an advanced level (4 of 5).
- Machine learning at an advanced level, with a focus on tabular and time series data.
- Time series forecasting and Feature engineering at a proficient level (3 of 5).
- Honest checking of results: you separate the training data from the test data with care.
- Clear writing and a calm voice when a number is wrong.

## Nice to have

- XGBoost, Model evaluation and MLflow in daily work.
- Docker, SQL and Git habits for shared code.
- A result in a data science competition.

## Tech stack

Python, scikit-learn, XGBoost, MLflow, Docker and SQL on a cloud data warehouse, with Git for all code.

## Certifications and awards

- Preferred certification: AWS Certified Machine Learning Engineer - Associate.
- Preferred award kind: Data science competition.

## What we offer

- $126,000 to $148,000 a year, plus 12% superannuation.
- Hybrid work: three days a week in our Sydney office and two at home.
- Four weeks of annual leave and a short break between Christmas and New Year.
- A learning budget of $2,500 a year.
- Access to live solar data from thousands of homes, with private details removed.

## About Bluebushworks

Bluebushworks makes planning and quoting software for solar and battery installers. It was founded in 2019 and has about 90 people, with its head office in Sydney. Its software is used on thousands of home installations each year.

## How we hire

- A 30-minute call with the forecasting lead.
- A small modelling task on sample data, about two hours.
- A talk with the team about your solution.
- An offer within five working days.`,
  },
  {
    key: "demo-data-engineer-contract-closed", title: "Contract Data Engineer, Billing Migration", company: "Bluebushworks",
    domain: "Data", specialisation: "Data engineering", level: "Mid", minYears: 3, maxYears: 8,
    type: "Contract", workMode: "Hybrid", city: "Sydney", area: "Sydney NSW",
    salary: { min: 760, max: 840, unit: "day" }, occupation: { code: "262111", title: "Data Engineer" },
    skills: [
      { name: "SQL", level: 4, must: true }, { name: "ETL and ELT pipelines", level: 4, must: true },
      { name: "Azure Data Factory", level: 4, must: true }, { name: "Python", level: 3, must: true },
      { name: "Data warehousing", level: 3, must: true }, { name: "Microsoft SQL Server", level: 3, must: false },
      { name: "Azure", level: 3, must: false }, { name: "Git", level: 3, must: false }, { name: "Data quality", level: 3, must: false },
      { name: "Power BI", level: 2, must: false },
    ],
    certifications: { required: [], preferred: ["Microsoft Certified: Azure Fundamentals"] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 40, closesInDays: -2,
    description: `## About the role

Bluebushworks is moving its billing and invoicing data from an old SQL Server system to a new cloud data warehouse, and it needs a contract data engineer for four months. The work covers 45 pipelines in Azure Data Factory, plus the checks that prove the new numbers match the old ones. As a mid-level contractor, you will join a billing data team of four who are tired of month-end surprises. This is a Hybrid contract in our Sydney office.

## What you will do

- Rebuild the billing and invoice pipelines in Azure Data Factory.
- Write SQL that returns the same totals as the old system, and prove it with checks.
- Load the data into the new data warehouse with clear logs and retries.
- Report the migration status each week to the billing team.
- Build a simple Power BI page that compares old and new totals.
- Hand over the pipelines with short guides.

## What you bring

- 3 to 8 years in data engineering, with SQL and ETL and ELT pipelines at an advanced level (4 of 5).
- Azure Data Factory at an advanced level, shown by a past migration.
- Python at a proficient level (3 of 5), and Data warehousing at the same level.
- Calm communication with billing teams, who care about every cent.
- Clear weekly status notes for the billing lead and the project owner.

## Nice to have

- Microsoft SQL Server and Azure depth.
- Git habits and Data quality checks that you built.
- Power BI basics.

## Tech stack

Azure Data Factory, Microsoft SQL Server as the old source, a cloud data warehouse as the target, Python for checks and Git for code.

## Certifications and awards

- Preferred certification: Microsoft Certified: Azure Fundamentals.

## What we offer

- A day rate of $760 to $840, paid through your company or an agency.
- A four-month contract in a Hybrid pattern: three days in our Sydney office.
- A clear scope and a friendly billing team.
- Quick onboarding, with access ready on day one.

## About Bluebushworks

Bluebushworks makes planning and quoting software for solar and battery installers. It was founded in 2019 and has about 90 people, with its head office in Sydney. Its software is used on thousands of home installations each year.

## How we hire

- A 30-minute call about the contract.
- A technical chat on Azure Data Factory and SQL.
- An answer within two working days.`,
  },
];
const TARGET_APPLICANTS = [10, 8, 5, 5];

function candidateUser(c, extra = {}) {
  const typed = c.skills.map(([name, level, years]) => ({ name, level, years }));
  const profile = {
    qualification: c.qualification, fieldOfStudy: c.fieldOfStudy, studyCountry: c.studyCountry, currentRole: c.currentRole, industry: c.industry,
    years: bandOf(c.yearsExperience), yearsExperience: c.yearsExperience, level: c.level, specialisation: c.specialisation,
    skills: typed.map((s) => s.name), certifications: c.certifications, awards: c.awards,
    targetRole: c.targetRole, targetIndustries: c.targetIndustries, locations: c.locations, workModes: c.workModes, workTypes: c.workTypes,
    evidence: c.evidence, translation: [],
  };
  // The levels and years that the talent gave stay on the cards of the skills
  profile.translation = translateKeeping({ ...profile, skills: typed }, c.evidence).skills.map((s) => ({ ...s, status: "accepted" }));
  return { id: newId(), role: "candidate", name: extra.name || `Sample candidate ${c.alias}`, email: extra.email || `${c.alias.toLowerCase().replace(/\s+/g, ".")}@sample.jinder.app`,
    company: null, alias: c.alias, pw: extra.pw || demoHash(newId()), seed: !extra.pw, profile, cv: extra.cv || null, onboarding: "done", createdAt: at(-30) };
}

function application(job, cand, status, history, extra = {}) {
  const snapshot = sharedProfileOf(cand);
  const sm = skillMatch(job.skills, namesFromList(snapshot.skills));
  return {
    id: newId(), jobId: job.id, candidateId: cand.id, recruiterId: job.ownerId, origin: "applied", status, note: extra.note || "",
    snapshot, match: { coverage: sm.coverage, skills: sm.items }, history, slots: extra.slots || [], chosenSlotId: extra.chosenSlotId || null,
    slotConfirmed: !!extra.slotConfirmed, identityShared: !!extra.identityShared, offer: extra.offer || null, feedback: extra.feedback || {},
    createdAt: history[0].at, updatedAt: history[history.length - 1].at,
  };
}
const h = (status, days, by, note = "") => ({ status, at: at(days), by, note });

export function seedDemo(db) {
  if (db.seeded) return;
  db.seeded = true;
  const sample = Object.fromEntries(SAMPLE_CANDIDATES.map((c) => [c.alias, candidateUser(c)]));
  db.users.push(...Object.values(sample));

  const recruiter = { id: newId(), role: "recruiter", name: "Alex Morgan", email: "recruiter@demo.jinder.app", company: "Bluebushworks", alias: null,
    pw: demoHash(DEMO_PASSWORD), profile: null, cv: null, onboarding: null, createdAt: at(-60) };
  const demoCand = candidateUser(DEMO_TALENT,
    { name: "Linh Nguyen", email: "candidate@demo.jinder.app", pw: demoHash(DEMO_PASSWORD), cv: { name: "linh-nguyen-cv.pdf", size: 182344, addedAt: at(-12) } });
  db.users.push(recruiter, demoCand);

  const jobs = Object.fromEntries(DEMO_JOBS.map((j, i) => [j.key, {
    id: `job-${j.key}`, ownerId: recruiter.id, title: j.title, company: recruiter.company, category: j.domain, specialisation: j.specialisation,
    location: j.city, area: j.area, type: j.type, salary: salaryText(j.salary), salaryUnit: j.salary.unit, description: j.description,
    skills: j.skills.map((s) => s.name), skillRequirements: j.skills.map((s) => ({ name: s.name, level: s.level, must: s.must })),
    level: j.level, minYears: j.minYears, maxYears: j.maxYears, workMode: j.workMode, educationMin: j.educationMin,
    certifications: j.certifications, awards: j.awards, targetApplicants: TARGET_APPLICANTS[i % 4],
    postedAt: at(-j.postedDaysAgo), closesAt: at(j.closesInDays), anzsco: j.occupation.code, occupation: j.occupation.title,
  }]));
  db.postedJobs.push(...Object.values(jobs));

  // The story: Teal Heron is in interview for the data engineer job. One profile waits in review. One waits for an answer.
  // The machine learning job closes soon and has an application. A finished contract job has an accepted offer.
  const de = jobs["demo-data-engineer-mid"], be = jobs["demo-backend-senior"], ml = jobs["demo-ml-engineer-mid"], closed = jobs["demo-data-engineer-contract-closed"];
  const slots = [1, 2, 3].map((d) => ({ id: newId().slice(0, 8), start: new Date(new Date(at(d + 2)).setHours(10 + d, 0, 0, 0)).toISOString() }));
  const apps = [
    application(de, sample["Jade Koala"], "review", [h("applied", -5, "candidate"), h("review", -3, "recruiter")]),
    application(de, demoCand, "interview", [h("applied", -5, "candidate"), h("review", -4, "recruiter"), h("interview", -2, "recruiter", "Offered 3 interview times")], { slots }),
    application(de, sample["Plum Heron"], "applied", [h("applied", -1, "candidate")], { note: "I build and run data pipelines every day and I like your stack." }),
    application(be, sample["Amber Finch"], "applied", [h("applied", -2, "candidate")]),
    application(be, sample["Cyan Puffin"], "review", [h("applied", -3, "candidate"), h("review", -2, "recruiter")]),
    application(ml, sample["Lime Kestrel"], "applied", [h("applied", -6, "candidate")]),
    application(closed, sample["Coral Fox"], "confirmed",
      [h("applied", -35, "candidate"), h("review", -33, "recruiter"), h("interview", -30, "recruiter", "Offered 2 interview times"), h("accepted", -25, "recruiter"), h("offer", -24, "recruiter"), h("confirmed", -22, "candidate", "Accepted the offer")],
      { slots: [{ id: "past1", start: at(-28) }], chosenSlotId: "past1", slotConfirmed: true, identityShared: true, offer: { text: "6-month contract at $820 per day, starting next month.", sentAt: at(-24) } }),
  ];
  db.applications.push(...apps);
  const [, interview, waiting, beApplied, , mlApplied] = apps;
  notify(db, recruiter.id, { type: "new_application", title: `New application for ${de.title}`, body: "Plum Heron applied.", link: `/review/${waiting.id}` });
  notify(db, recruiter.id, { type: "new_application", title: `New application for ${be.title}`, body: "Amber Finch applied.", link: `/review/${beApplied.id}` });
  notify(db, recruiter.id, { type: "new_application", title: `New application for ${ml.title}`, body: "Lime Kestrel applied.", link: `/review/${mlApplied.id}` });
  notify(db, demoCand.id, { type: "interview_slots", title: `Interview times for ${de.title}`, body: "Choose a time that works for you.", link: `/applications/${interview.id}` });

  // Some activity for the charts of Premium: counts of what talent did with the jobs (no person is named). The numbers are the same at each start.
  let seed = 7;
  const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  for (const job of Object.values(jobs)) {
    for (const [type, n] of [["job_appear", 24], ["job_watch", 9], ["job_save", 3]]) {
      for (let i = 0, count = n + Math.floor(rnd() * 5); i < count; i++) db.events.push({ type, targetType: "job", targetId: job.id, actorId: null, at: at(-rnd() * 20) });
    }
  }
}
```

### Seed jobs (`js/api/mock/seed-jobs.js`)

24 of the 50 synthetic jobs of `jinder_backend_engine/data/synthetic/jobs.json` (Data 9, Software Engineering 9, AI & Machine Learning 6; levels Intern 2, Junior 4, Mid 11, Senior 3, Lead 3, Principal 1; types Full-time 18, Contract 4 with a day rate, Graduate / Internship 2; 21 list certifications and 9 list preferred awards). Each job has the full description with the JD markup (`## Heading`, `- bullet`), never cut and never flattened. The text is the same as in the synthetic file, with two small edits so that no word of another field of work stays in the app: "warehouse" got the word "data" before it ("cloud data warehouse"), and "retail", "finance" and "marketing" became "shop", "billing" and "campaign" in the talent and demo texts. The job ids are `job-<key>`, as in the real backend; `postedDaysAgo` and `closesInDays` count from the day when the app starts, so every catalogue job is open. Create the file exactly as shown (a JavaScript file that exports `SEED_JOBS`):

```js
// MOCK BACKEND — the embedded ICT job catalogue: 24 of the 50 synthetic jobs of jinder_backend_engine/data/synthetic/jobs.json.
// All jobs and companies are made up. The mock API (jobs.js) reads this list. Keep it the same as prompt.md.
// Each job has: key, title, company, domain (one of the 3 domains), specialisation, level (Intern to Principal), minYears, maxYears,
// type, workMode, city, area, salary { min, max, unit: "year" or "day" }, occupation { code, title } (ANZSCO), skills [{ name, level 1 to 5, must }],
// certifications { required, preferred }, awards { preferred }, educationMin, postedDaysAgo, closesInDays and description.
// The description is never cut. It uses a small markup: a line "## Heading", a line "- bullet", and plain paragraphs.
// postedDaysAgo and closesInDays count from the day when the app starts, so that the jobs are always open.
export const SEED_JOBS = [
  {
    key: "data-eng-senior-02", title: "Senior Data Engineer, Lakehouse", company: "Mallee Mesh",
    domain: "Data", specialisation: "Data engineering", level: "Senior", minYears: 5, maxYears: 9,
    type: "Full-time", workMode: "Remote", city: "Remote", area: "Remote (Australia)",
    salary: { min: 150000, max: 168000, unit: "year" }, occupation: { code: "262111", title: "Data Engineer" },
    skills: [
      { name: "Databricks", level: 4, must: true }, { name: "Apache Spark", level: 4, must: true }, { name: "Data lakehouse", level: 4, must: true },
      { name: "Python", level: 4, must: true }, { name: "SQL", level: 4, must: true }, { name: "Azure Data Factory", level: 3, must: false },
      { name: "Azure", level: 3, must: false }, { name: "Data governance", level: 3, must: false }, { name: "Data modelling", level: 4, must: false },
      { name: "CI/CD", level: 3, must: false }, { name: "Infrastructure as code", level: 2, must: false },
    ],
    certifications: { required: ["Databricks Certified Data Engineer Associate"], preferred: ["Databricks Certified Data Engineer Professional"] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 15, closesInDays: 34,
    description: `## About the role

Mallee Mesh builds a data platform for water utilities and regional councils, and it is moving from a patchwork of databases to one lakehouse on Databricks. The Platform Data team of seven builds the bronze, silver and gold layers, and the rules that keep meter and flow data trustworthy. We need a senior data engineer to set the standards for those layers and to onboard the first six customers. The role is fully Remote and open to people anywhere in Australia.

## What you will do

- Design the lakehouse layers and the naming, testing and release rules for each one.
- Build Spark pipelines in Databricks that handle late and messy meter data.
- Bring in data from customer systems with Azure Data Factory.
- Set up access rules and lineage so that each council sees only its own data.
- Add CI/CD for notebooks and jobs, with tests before each release.
- Help customers' own analysts use the gold tables.
- Review pull requests and guide two mid-level engineers.

## What you bring

- 5 to 9 years in data engineering, with Databricks and Apache Spark at an advanced level (4 of 5).
- Data lakehouse design at an advanced level: layers, partitioning and table formats.
- Python and SQL at an advanced level.
- A good sense of cost: you can predict what a job will cost before you run it.
- A Databricks data engineer certification, as listed below.

## Nice to have

- Azure and Azure Data Factory experience.
- Data modelling at an advanced level, and Data governance at a proficient level.
- CI/CD for data, and a first look at Infrastructure as code with Terraform.

## Tech stack

Databricks and Apache Spark on Azure, Delta tables, Azure Data Factory, Python and SQL, with Terraform for the environments and GitHub for CI/CD.

## Certifications and awards

- Required certification: Databricks Certified Data Engineer Associate.
- Preferred certification: Databricks Certified Data Engineer Professional.

## What we offer

- $150,000 to $168,000 a year, plus 12% superannuation.
- Fully Remote work in Australia, with a team week in Adelaide twice a year.
- $2,000 for your home office and a yearly co-working pass.
- Four weeks of annual leave and a paid winter shutdown week in July.
- Exam fees for Databricks and Azure certifications.

## About Mallee Mesh

Mallee Mesh makes data software for water utilities and regional councils. It was founded in 2017 and has about 85 people who work from many towns and cities. Its customers manage water for more than two million homes.

## How we hire

- A video call with the head of data.
- A talk about a lakehouse or Spark system that you built.
- A design exercise on a late-data problem, with two engineers.
- A decision within a week.`,
  },
  {
    key: "data-science-mid-01", title: "Data Scientist, Product Analytics", company: "Gumnutlabs",
    domain: "Data", specialisation: "Data science", level: "Mid", minYears: 3, maxYears: 6,
    type: "Full-time", workMode: "Remote", city: "Remote", area: "Remote (Australia)",
    salary: { min: 124000, max: 146000, unit: "year" }, occupation: { code: "224115", title: "Data Scientist" },
    skills: [
      { name: "Python", level: 4, must: true }, { name: "Pandas", level: 4, must: true }, { name: "scikit-learn", level: 3, must: true },
      { name: "Statistics", level: 3, must: true }, { name: "SQL", level: 3, must: true }, { name: "Data visualisation", level: 3, must: false },
      { name: "Machine learning", level: 3, must: false }, { name: "Feature engineering", level: 3, must: false },
      { name: "NumPy", level: 3, must: false }, { name: "Git", level: 3, must: false }, { name: "Communication", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["PCAP: Certified Associate in Python Programming"] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 19, closesInDays: 20,
    description: `## About the role

Gumnutlabs makes a language-learning app that about 400,000 people open each week, and the Product Analytics team works out which lessons keep learners coming back. The team of five data scientists and analysts studies behaviour, builds churn and recommendation models and helps product teams run experiments. We want a mid-level data scientist who likes to turn a vague question into a clear answer. This role is fully Remote in Australia.

## What you will do

- Study how learners move through lessons, and find where they drop out.
- Build churn and next-lesson models, and check that they help real learners.
- Help product teams plan and read experiments.
- Prepare data with Pandas and SQL, and keep the notebooks tidy and reusable.
- Share results in short write-ups and a monthly talk.
- Review a colleague's analysis each week.

## What you bring

- 3 to 6 years as a data scientist or analyst who builds models.
- Python and Pandas at an advanced level (4 of 5), with clean, tested code.
- scikit-learn, Statistics and SQL at a proficient level (3 of 5).
- Good judgement: you can say what a result does and does not prove.
- A calm voice in remote meetings and clear writing.

## Nice to have

- Machine learning and Feature engineering for behaviour data.
- NumPy, Data visualisation and Git habits.
- Strong Communication with product managers and designers.

## Tech stack

Python with Pandas, NumPy and scikit-learn, SQL on a cloud data warehouse, Jupyter notebooks, Git and a shared experiment platform.

## Certifications and awards

- Preferred certification: PCAP: Certified Associate in Python Programming.

## What we offer

- $124,000 to $146,000 a year, plus 12% superannuation.
- Remote work from anywhere in Australia, with a team week in Sydney each year.
- A one-off $1,000 for your home desk, plus a monthly internet payment.
- Four weeks of annual leave and a Monday off at the end of each quarter.
- A free subscription for you and your family to the app, in any language.

## About Gumnutlabs

Gumnutlabs builds language-learning apps. It was founded in 2018 and has about 100 people, most of whom work from home. Its data team is one of the oldest teams in the company.

## How we hire

- A video call with the head of data.
- A short analysis task on a sample of learner data, about three hours.
- A talk with two team members about the choices in your analysis.
- An answer within a week.`,
  },
  {
    key: "data-bi-mid-01", title: "Business Intelligence Developer", company: "Blackbutt Relay",
    domain: "Data", specialisation: "Business intelligence", level: "Mid", minYears: 4, maxYears: 8,
    type: "Full-time", workMode: "Onsite", city: "Melbourne", area: "Melbourne VIC",
    salary: { min: 112000, max: 130000, unit: "year" }, occupation: { code: "224114", title: "Data Analyst" },
    skills: [
      { name: "Power BI", level: 4, must: true }, { name: "SQL", level: 4, must: true }, { name: "Data modelling", level: 3, must: true },
      { name: "Microsoft SQL Server", level: 3, must: true }, { name: "Data visualisation", level: 4, must: true },
      { name: "Data warehousing", level: 3, must: false }, { name: "Microsoft Excel", level: 3, must: false },
      { name: "Requirements analysis", level: 3, must: false }, { name: "Stakeholder management", level: 3, must: false },
      { name: "Data quality", level: 3, must: false },
    ],
    certifications: { required: ["Microsoft Certified: Power BI Data Analyst Associate"], preferred: [] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 13, closesInDays: 24,
    description: `## About the role

Blackbutt Relay makes payroll and workforce software, and its customers' managers use the reporting pages to see hours, costs and leave. The BI team of five builds the reports for 2,000 employers on Power BI and SQL Server, and it needs a mid-level developer to rebuild the oldest reports. You will work Onsite in our Melbourne office, next to the product and support teams who know what customers ask for. Most of your reports will be used by people who are not data experts.

## What you will do

- Rebuild the 40 oldest customer reports in Power BI with clean models and fast queries.
- Write SQL Server queries and views that feed the reports.
- Design star-schema models that make new reports quick to build.
- Sit with customers' managers to learn what they need to see, and then simplify the page.
- Check the numbers against payroll results and fix differences.
- Document each report for the support team.

## What you bring

- 4 to 8 years in business intelligence or reporting.
- Power BI and Data visualisation at an advanced level (4 of 5): clear pages, good filters and quick refreshes.
- SQL at an advanced level, and Microsoft SQL Server at a proficient level (3 of 5).
- Data modelling at a proficient level, with star schemas and clean keys.
- A current Power BI Data Analyst certification, as listed below.
- Calm, helpful Stakeholder management when a manager says that a number is wrong.

## Nice to have

- Data warehousing and Microsoft Excel depth.
- Requirements analysis and workshop skills.
- Data quality habits, such as reconciliation checks for money.

## Tech stack

Power BI, SQL Server with views and stored procedures, a small data warehouse and Microsoft Excel exports for some customers.

## Certifications and awards

- Required certification: Microsoft Certified: Power BI Data Analyst Associate.

## What we offer

- $112,000 to $130,000 a year, plus 12% superannuation.
- Onsite work in our Melbourne office, five days a week, with a central location.
- Four weeks of annual leave and a day off for your birthday.
- Exam fees and study days for Microsoft certifications.
- A team lunch each fortnight.

## About Blackbutt Relay

Blackbutt Relay builds payroll, rostering and workforce reporting software for employers. It was founded in 2010 and has about 190 people in Melbourne. Its customers range from cafes to hospital groups.

## How we hire

- A short call with the BI lead.
- A Power BI exercise that you do in the office, about two hours.
- A chat with the product manager and a support lead.
- An answer within five working days.`,
  },
  {
    key: "data-analytics-mid-01", title: "Data Analyst, Growth", company: "Stringybark Data",
    domain: "Data", specialisation: "Data analytics", level: "Mid", minYears: 2, maxYears: 5,
    type: "Full-time", workMode: "Hybrid", city: "Melbourne", area: "Melbourne VIC",
    salary: { min: 108000, max: 126000, unit: "year" }, occupation: { code: "224114", title: "Data Analyst" },
    skills: [
      { name: "SQL", level: 4, must: true }, { name: "Data analysis", level: 4, must: true }, { name: "Data visualisation", level: 4, must: true },
      { name: "Power BI", level: 3, must: true }, { name: "Microsoft Excel", level: 4, must: false }, { name: "Python", level: 2, must: false },
      { name: "Apache Airflow", level: 1, must: false }, { name: "ETL and ELT pipelines", level: 2, must: false },
      { name: "Data quality", level: 3, must: false }, { name: "Stakeholder management", level: 3, must: false },
      { name: "Data storytelling", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["Microsoft Certified: Power BI Data Analyst Associate"] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 18, closesInDays: 38,
    description: `## About the role

Stringybark Data makes booking and membership software for fitness studios, and the Growth team uses data to find out why members join, stay or leave. The team of five analysts and one engineer needs a mid-level data analyst who is strong in SQL and who wants to grow toward data engineering. You will spend most of your time on analysis and dashboards, and some of it building the pipelines behind them, with a data engineer as your coach. You will work in Melbourne on a Hybrid schedule.

## What you will do

- Answer questions such as why trial members do not join, using SQL and clear charts.
- Build and own the Power BI dashboards for the Growth and Studio Success teams.
- Run a monthly review of membership trends with the studio owners' success managers.
- Check the quality of the data behind your reports and report problems at the source.
- Build one new pipeline each quarter with the data engineer, step by step.
- Tell the story of each analysis in a short note that a studio owner can read in two minutes.

## What you bring

- 2 to 5 years as a data or business analyst.
- SQL and Data analysis at an advanced level (4 of 5): window functions, cohorts and funnels.
- Data visualisation at an advanced level, and Power BI at a proficient level (3 of 5).
- Curiosity about data engineering: you want to learn how the tables get built.
- Good habits with stakeholders: you ask what decision a number will support.

## Nice to have

- Python, ETL and ELT pipelines and Apache Airflow at a beginner level (1 to 2 of 5). This is the skill that we will help you grow.
- Microsoft Excel at an advanced level and Data quality habits.
- Data storytelling and Stakeholder management with non-technical people.

## Tech stack

SQL on a cloud data warehouse, Power BI and Microsoft Excel for reporting, a little Python, and Apache Airflow for the pipelines that the data engineer owns. Your first pipeline will be small.

## Certifications and awards

- Preferred certification: Microsoft Certified: Power BI Data Analyst Associate.

## What we offer

- $108,000 to $126,000 a year, plus 12% superannuation.
- Hybrid work: two days a week in our Melbourne office and three at home.
- Four weeks of annual leave and the Friday before Easter as a bonus day.
- A clear path to a data engineer role, with a learning plan and a coach.
- A $2,000 yearly budget for courses and exam fees.

## About Stringybark Data

Stringybark Data builds booking, payment and membership software for fitness studios. It was founded in 2016 and has about 130 people in Melbourne. Its analysts sit next to the product teams.

## How we hire

- A 30-minute call with the analytics lead about your recent analyses.
- A SQL and chart exercise that you do at home in about two hours.
- A talk with the analysts and the data engineer about your work.
- An answer within a week.`,
  },
  {
    key: "data-eng-junior-01", title: "Junior Data Engineer, Farm Data", company: "Saltbushworks",
    domain: "Data", specialisation: "Data engineering", level: "Junior", minYears: 0, maxYears: 2,
    type: "Full-time", workMode: "Onsite", city: "Brisbane", area: "Brisbane QLD",
    salary: { min: 90000, max: 104000, unit: "year" }, occupation: { code: "262111", title: "Data Engineer" },
    skills: [
      { name: "SQL", level: 3, must: true }, { name: "Python", level: 3, must: true }, { name: "ETL and ELT pipelines", level: 2, must: true },
      { name: "Git", level: 2, must: false }, { name: "Apache Airflow", level: 2, must: false }, { name: "Microsoft Excel", level: 2, must: false },
      { name: "Data quality", level: 2, must: false }, { name: "PostgreSQL", level: 2, must: false },
      { name: "Data modelling", level: 2, must: false }, { name: "Communication", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["AWS Certified Cloud Practitioner"] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 11, closesInDays: 37,
    description: `## About the role

Saltbushworks collects sensor and drone data from thousands of paddocks, and the Farm Data team turns it into tables that agronomists and apps can trust. The team of four wants a junior data engineer, and it welcomes an analyst who knows SQL and Microsoft Excel and wants to start building pipelines. You will learn how data moves from a soil probe to a farm dashboard and take over one pipeline in your first six months. This is an Onsite role in Brisbane.

## What you will do

- Run and watch the daily pipelines that load sensor readings into PostgreSQL.
- Write SQL to answer questions from agronomists, then turn the best ones into saved tables.
- Fix small pipeline bugs with a senior engineer, and write down what you learned.
- Add simple data quality checks, such as a soil reading that is out of range.
- Move one spreadsheet process into a scheduled pipeline.
- Share your results in the weekly team meeting.

## What you bring

- 0 to 2 years of experience in data work, or a degree project with a real data set.
- SQL at a proficient level (3 of 5): joins, grouping and window functions.
- Python at a proficient level (3 of 5), for scripts that read, clean and write data.
- A first look at ETL and ELT pipelines (2 of 5): you know the idea of extract, transform and load.
- Care for details and a wish to ask why a number looks odd.

## Nice to have

- Apache Airflow, PostgreSQL or Data modelling from a course or a project.
- Microsoft Excel skill, which helps you talk with agronomists.
- Git basics, Data quality curiosity and clear Communication.

## Tech stack

Python and SQL, PostgreSQL, Apache Airflow for scheduling and Git. Raw files sit in AWS cloud storage, and a small dashboard tool shows results to farm staff.

## Certifications and awards

- Preferred certification: AWS Certified Cloud Practitioner.

## What we offer

- $90,000 to $104,000 a year, plus 12% superannuation.
- Onsite work in our Brisbane office, five days a week.
- Four weeks of annual leave and paid time to attend one industry meetup each month.
- A mentor, a learning plan and a review every quarter.
- A farm visit each year to see where the data comes from.

## About Saltbushworks

Saltbushworks builds sensors, drone imaging and apps for farms. It was founded in 2019 and has about 90 people, with a head office in Brisbane and a field team in regional Queensland. Its customers grow grain, cotton and fruit.

## How we hire

- A short call with the data team lead.
- A small SQL and Python exercise in the office.
- A chat with two teammates about what you want to learn first.
- A reply within a week, with feedback that you can use even if the answer is no.`,
  },
  {
    key: "data-eng-mid-02", title: "Contract Data Engineer, Fabric Migration", company: "Banksiapath",
    domain: "Data", specialisation: "Data engineering", level: "Mid", minYears: 3, maxYears: 8,
    type: "Contract", workMode: "Hybrid", city: "Sydney", area: "Sydney NSW",
    salary: { min: 720, max: 800, unit: "day" }, occupation: { code: "262111", title: "Data Engineer" },
    skills: [
      { name: "Microsoft Fabric", level: 4, must: true }, { name: "Azure Data Factory", level: 4, must: true }, { name: "SQL", level: 4, must: true },
      { name: "Python", level: 3, must: true }, { name: "Data warehousing", level: 3, must: true },
      { name: "ETL and ELT pipelines", level: 4, must: false }, { name: "Power BI", level: 3, must: false }, { name: "Azure", level: 3, must: false },
      { name: "Git", level: 3, must: false }, { name: "Data modelling", level: 3, must: false },
    ],
    certifications: { required: ["Microsoft Certified: Fabric Data Engineer Associate"], preferred: [] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 2, closesInDays: 13,
    description: `## About the role

A mid-size insurer has asked Banksiapath to move its reporting from an old SQL Server data warehouse to Microsoft Fabric. You will join a team of five as the mid-level engineer on a five-month contract to rebuild 60 pipelines in Azure Data Factory and Fabric, check that the numbers match and retire the old servers. The client is friendly, the scope is clear and the end date is fixed. This is a Hybrid contract in Sydney.

## What you will do

- Rebuild the claims and policy pipelines in Microsoft Fabric and Azure Data Factory.
- Move the data warehouse tables and write SQL that returns the same results as the old system.
- Write comparison checks that prove each migrated table matches.
- Connect the new tables to the Power BI reports that the business uses.
- Keep a clear log of each pipeline: status, owner and test result.
- Hand over to the client's team with short guides and a recorded demo.

## What you bring

- 3 to 8 years in data engineering, with Microsoft Fabric and Azure Data Factory at an advanced level (4 of 5).
- SQL at an advanced level and Python at a proficient level (3 of 5).
- Data warehousing at a proficient level, and ETL and ELT pipelines experience from at least one migration.
- A current Fabric data engineer certification, as listed below.
- Clear daily notes: you tell the team what you finished and what is blocked.

## Nice to have

- Power BI and Azure skills.
- Data modelling and Git habits for a shared workspace.
- A past data warehouse migration that finished on time.

## Tech stack

Microsoft Fabric, Azure Data Factory, SQL Server as the old source, Power BI for reports, Python for checks and Git for code.

## Certifications and awards

- Required certification: Microsoft Certified: Fabric Data Engineer Associate.

## What we offer

- A day rate of $720 to $800, paid through your company or an agency.
- A five-month contract, with a possible extension.
- Hybrid work: three days a week on the client site in Sydney and two at home.
- A friendly client with a clear plan.
- Fast onboarding: access is ready on your first day.

## About Banksiapath

Banksiapath is a data migration and reporting consultancy. It was founded in 2015 and has about 60 people in Sydney. Contractors and staff work in the same teams.

## How we hire

- A 30-minute call about the project and your dates.
- A technical chat on Fabric, Data Factory and SQL.
- An answer within two working days of the call.`,
  },
  {
    key: "data-analytics-junior-01", title: "Junior Data Analyst, Operations", company: "Pinkgum Analytics",
    domain: "Data", specialisation: "Data analytics", level: "Junior", minYears: 1, maxYears: 2,
    type: "Full-time", workMode: "Hybrid", city: "Perth", area: "Perth WA",
    salary: { min: 76000, max: 88000, unit: "year" }, occupation: { code: "224114", title: "Data Analyst" },
    skills: [
      { name: "Microsoft Excel", level: 3, must: true }, { name: "SQL", level: 3, must: true }, { name: "Data analysis", level: 3, must: true },
      { name: "Data visualisation", level: 3, must: true }, { name: "Tableau", level: 2, must: false }, { name: "Statistics", level: 2, must: false },
      { name: "Communication", level: 3, must: false }, { name: "Data quality", level: 2, must: false }, { name: "Teamwork", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["Tableau Certified Data Analyst"] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 21, closesInDays: 25,
    description: `## About the role

Pinkgum Analytics helps ports, rail operators and haulage companies in Western Australia see where their time and money go. The Operations Insights team of eight turns messy logs and spreadsheets into reports that planners use each morning. We are hiring a junior data analyst who is good with spreadsheets and wants to get strong in SQL and dashboards. This is a Hybrid role in Perth, with three days in the office and two at home.

## What you will do

- Build and refresh the daily reports on truck turnaround, queue times and rail delays.
- Write SQL queries that join messy gate, weighbridge and rail data.
- Clean spreadsheets that customers send, and flag the odd rows to the sender.
- Make charts and simple dashboards in Tableau, with help from a senior analyst.
- Present one finding each month to a customer planning team.
- Write down your steps so that anyone can repeat your analysis.

## What you bring

- 1 to 2 years in an analyst role, or a degree with a strong data project.
- Microsoft Excel at a proficient level (3 of 5): lookups, pivot tables and clean formulas.
- SQL and Data analysis at a proficient level (3 of 5): you can answer a question with a query and explain the result.
- Data visualisation at a proficient level, with charts that are simple and honest.
- Teamwork: you ask questions and you share your drafts early.

## Nice to have

- Tableau practice from a course or a job, and basic Statistics.
- Data quality instincts: you notice when a number is too good.
- Clear Communication with people who work in trucks and on rail lines.

## Tech stack

SQL on a cloud database, Microsoft Excel, Tableau for dashboards, and shared drives for the customer files. We are slowly moving the manual steps to scheduled jobs.

## Certifications and awards

- Preferred certification: Tableau Certified Data Analyst.

## What we offer

- $76,000 to $88,000 a year, plus 12% superannuation.
- Hybrid work: three days a week in our Perth office and two at home.
- Four weeks of annual leave, with no need to explain a sick day.
- A senior analyst as your coach, with a check-in each week.
- Support for the Tableau exam and for evening courses.

## About Pinkgum Analytics

Pinkgum Analytics makes operations reports and planning tools for the resources and transport industries. It was founded in 2019 and has about 40 people in Perth. Its analysts work close to the customers.

## How we hire

- A short call to hear what you enjoy about data.
- A spreadsheet and SQL exercise of about 90 minutes.
- A friendly chat with two analysts.
- We reply within a week and we always give feedback.`,
  },
  {
    key: "data-analytics-intern-01", title: "Data Analyst Intern, Summer Program", company: "Coolibah Ridge Software",
    domain: "Data", specialisation: "Data analytics", level: "Intern", minYears: 0, maxYears: 1,
    type: "Graduate / Internship", workMode: "Onsite", city: "Sydney", area: "Sydney NSW",
    salary: { min: 58000, max: 68000, unit: "year" }, occupation: { code: "224114", title: "Data Analyst" },
    skills: [
      { name: "Microsoft Excel", level: 3, must: true }, { name: "SQL", level: 2, must: true }, { name: "Data visualisation", level: 2, must: true },
      { name: "Communication", level: 3, must: true }, { name: "Data analysis", level: 2, must: false }, { name: "Power BI", level: 1, must: false },
      { name: "Continuous learning", level: 3, must: false }, { name: "Teamwork", level: 3, must: false }, { name: "Python", level: 1, must: false },
    ],
    certifications: { required: [], preferred: ["Microsoft Certified: Azure Fundamentals"] }, awards: { preferred: ["scholarship"] },
    educationMin: "Diploma", postedDaysAgo: 16, closesInDays: 38,
    description: `## About the role

Coolibah Ridge Software makes grants and reporting software for councils and community groups, and each summer it takes four interns for ten weeks. The data analyst intern joins the Insights team to help answer questions such as which community programs reach the most people. You will work on real data sets, build your first dashboards and present them to the whole company in the last week. This is an Onsite internship in our Sydney office, five days a week.

## What you will do

- Clean and combine program data from spreadsheets and databases.
- Write simple SQL queries to answer questions from the Insights team.
- Build a first dashboard on program reach and share it with a council customer.
- Check numbers with a buddy before you share them.
- Present your project to the company in the final week.

## What you bring

- 0 to 1 years of work experience. You are studying for a diploma or a degree in IT, business, maths or a related field.
- Microsoft Excel at a proficient level (3 of 5), including pivot tables.
- SQL and Data visualisation at a working level (2 of 5).
- Friendly, clear Communication, in writing and in person.
- A wish to learn fast and to ask when you are unsure.

## Nice to have

- Data analysis projects from your course, a club or a volunteer job.
- A first look at Power BI or Python.
- Continuous learning habits and good Teamwork.

## Tech stack

Microsoft Excel, SQL on a cloud database and Power BI for dashboards. A little Python is used for data cleaning.

## Certifications and awards

- Preferred certification: Microsoft Certified: Azure Fundamentals.
- Preferred award kind: Scholarship.

## What we offer

- $58,000 to $68,000 a year pro rata, which is paid for the ten weeks of the program, plus 12% superannuation.
- Onsite work in our Sydney office, five days a week, with a desk, a laptop and a buddy.
- A weekly lunch with leaders from different parts of the company.
- A reference letter and a chance to apply for our graduate program.
- Free fruit and coffee, and a short walk from the station.

## About Coolibah Ridge Software

Coolibah Ridge Software builds grants, reporting and community program software for councils and community groups. It was founded in 2014 and has about 70 people in Sydney. It takes four summer interns each year.

## How we hire

- A short online form about your course.
- A 20-minute call with the Insights lead.
- A small Excel task that we do together.
- An answer by the end of the following week, so that you can plan your holidays.`,
  },
  {
    key: "data-ba-mid-01", title: "Business Analyst (Contract), Digital Services", company: "Mulgawire Technologies",
    domain: "Data", specialisation: "Business analysis", level: "Mid", minYears: 4, maxYears: 9,
    type: "Contract", workMode: "Onsite", city: "Canberra", area: "Canberra ACT",
    salary: { min: 680, max: 750, unit: "day" }, occupation: { code: "261111", title: "ICT Business Analyst" },
    skills: [
      { name: "Requirements analysis", level: 4, must: true }, { name: "Stakeholder management", level: 4, must: true },
      { name: "SQL", level: 3, must: true }, { name: "Data analysis", level: 3, must: true },
      { name: "Technical documentation", level: 4, must: true }, { name: "Data visualisation", level: 3, must: false },
      { name: "Microsoft Excel", level: 4, must: false }, { name: "Facilitation", level: 4, must: false },
      { name: "Agile delivery", level: 3, must: false }, { name: "Project management", level: 3, must: false },
      { name: "Data modelling", level: 2, must: false },
    ],
    certifications: { required: ["Professional Scrum Master I"], preferred: [] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 12, closesInDays: 15,
    description: `## About the role

A state agency has asked Mulgawire Technologies to improve its online licence renewal service, and the project needs a business analyst for a six-month contract. As a mid-level analyst, you will run workshops with agency staff, write the requirements for new features and use data from the current service to show where people get stuck. The delivery team of ten works in short sprints with a product owner from the agency. This is an Onsite contract in Canberra.

## What you will do

- Run workshops with agency staff and turn their ideas into clear requirements.
- Write user stories and acceptance criteria that developers and testers can use.
- Query the service data in SQL to find where applicants leave the renewal form.
- Show the findings in simple charts and in a short report for the steering group.
- Keep the backlog in order with the product owner and join the sprint ceremonies.
- Write the process and data documents that the agency needs for its records.

## What you bring

- 4 to 9 years as a business analyst on software or digital projects.
- Requirements analysis and Stakeholder management at an advanced level (4 of 5).
- SQL and Data analysis at a proficient level (3 of 5), to check your ideas against real data.
- Technical documentation at an advanced level: process maps, data dictionaries and clear specifications.
- A current Professional Scrum Master I certificate, as listed below.
- Availability for Onsite work in Canberra, five days a week.

## Nice to have

- Facilitation of workshops with many voices.
- Agile delivery and Project management experience on public sector projects.
- Data visualisation, Microsoft Excel and a first view of Data modelling.

## Tech stack

SQL on the agency's reporting database, Microsoft Excel and a work tracking tool for the backlog. Charts are made in Power BI or in Excel.

## Certifications and awards

- Required certification: Professional Scrum Master I.

## What we offer

- A day rate of $680 to $750, paid through your company or an agency.
- Onsite work at our Canberra office and at the agency, with parking or a transport pass.
- A six-month contract, with a likely extension.
- A clear project, an engaged product owner and no weekend work.

## About Mulgawire Technologies

Mulgawire Technologies delivers IT services for federal and state agencies. It was founded in 2009 and has about 400 people, with its head office in Canberra. Most of its projects run for several years.

## How we hire

- A 30-minute call about the contract and your availability.
- A conversation about two projects where you were the analyst.
- An answer within three working days.`,
  },
  {
    key: "swe-platform-mid-01", title: "DevOps Engineer, Client Delivery", company: "Tallowbridge Cloud",
    domain: "Software Engineering", specialisation: "Platform and DevOps", level: "Mid", minYears: 3, maxYears: 5,
    type: "Full-time", workMode: "Onsite", city: "Melbourne", area: "Melbourne VIC",
    salary: { min: 122000, max: 140000, unit: "year" }, occupation: { code: "261316", title: "DevOps Engineer" },
    skills: [
      { name: "Azure", level: 4, must: true }, { name: "Azure DevOps", level: 4, must: true }, { name: "Terraform", level: 3, must: true },
      { name: "Docker", level: 3, must: true }, { name: "CI/CD", level: 4, must: true }, { name: "Kubernetes", level: 3, must: false },
      { name: "PowerShell", level: 3, must: false }, { name: "Linux", level: 3, must: false }, { name: "Shell scripting", level: 3, must: false },
      { name: "Cloud security", level: 3, must: false },
    ],
    certifications: { required: ["HashiCorp Certified: Terraform Associate"], preferred: ["Microsoft Certified: DevOps Engineer Expert"] }, awards: { preferred: [] },
    educationMin: "Diploma", postedDaysAgo: 13, closesInDays: 24,
    description: `## About the role

Tallowbridge Cloud helps banks, utilities and councils move their systems to the cloud, and the Client Delivery team builds the pipelines and environments for each project. This mid-level role puts you on two or three client projects at a time, mostly on Azure, with a lead who reviews your designs. Each project has a new setup, so the work stays fresh. This is an Onsite role in our Melbourne office, with client site visits when needed.

## What you will do

- Build Azure environments with Terraform that pass the client's security review.
- Set up Azure DevOps pipelines that build, test and deploy applications in one flow.
- Package applications in Docker and deploy them to Kubernetes or to app services.
- Write PowerShell and shell scripts that remove manual steps for the client's staff.
- Check cloud security settings and fix the findings that you can.
- Hand each project over with clear diagrams and a short training session.

## What you bring

- 3 to 5 years of DevOps or cloud work, with a diploma or a degree in IT, or equal experience.
- Azure and Azure DevOps at an advanced level (4 of 5).
- CI/CD at an advanced level: you design pipelines, not just edit them.
- Terraform and Docker at a proficient level (3 of 5).
- A Terraform certification, as listed below.
- Easy, clear conversation with client engineers who know their systems better than you.

## Nice to have

- Kubernetes at a proficient level.
- PowerShell, Linux and Shell scripting skills.
- Cloud security knowledge, such as network rules, identity and secret storage.

## Tech stack

Azure with Azure DevOps, Terraform, Docker, Kubernetes on Azure, PowerShell and Linux. Some clients also use AWS.

## Certifications and awards

- Required certification: HashiCorp Certified: Terraform Associate.
- Preferred certification: Microsoft Certified: DevOps Engineer Expert.

## What we offer

- $122,000 to $140,000 a year, plus 12% superannuation.
- Onsite work in our Melbourne office, five days a week, with a travel allowance for client sites.
- Four weeks of annual leave and one paid day each year to volunteer for a cause that you choose.
- Exam fees and study days for Azure and Terraform certifications.
- A lead who spends time on your growth plan.

## About Tallowbridge Cloud

Tallowbridge Cloud is a cloud consultancy for banks, utilities and councils. It was founded in 2013 and has about 200 people in Sydney and Melbourne. Its engineers move between client projects every few months.

## How we hire

- A 30-minute call about your projects.
- A technical interview on pipelines and Terraform.
- A conversation with the delivery lead.
- An offer within five working days.`,
  },
  {
    key: "swe-backend-lead-01", title: "Lead Backend Engineer, Streaming Services", company: "Bunyipstream",
    domain: "Software Engineering", specialisation: "Backend", level: "Lead", minYears: 8, maxYears: 14,
    type: "Full-time", workMode: "Hybrid", city: "Melbourne", area: "Melbourne VIC",
    salary: { min: 190000, max: 215000, unit: "year" }, occupation: { code: "261313", title: "Software Engineer" },
    skills: [
      { name: "Kotlin", level: 4, must: true }, { name: "Microservices architecture", level: 5, must: true },
      { name: "System design", level: 5, must: true }, { name: "Technical leadership", level: 4, must: true },
      { name: "Team leadership", level: 4, must: true }, { name: "AWS", level: 4, must: true }, { name: "Amazon DynamoDB", level: 3, must: false },
      { name: "Apache Kafka", level: 3, must: false }, { name: "Observability", level: 4, must: false }, { name: "Mentoring", level: 4, must: false },
      { name: "Estimation and planning", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["AWS Certified Solutions Architect - Associate"] }, awards: { preferred: ["employer-recognition"] },
    educationMin: "Bachelor's degree", postedDaysAgo: 17, closesInDays: 14,
    description: `## About the role

During a grand final, Bunyipstream sends live video to more than 400,000 viewers at once, and the backend must not blink. The Streaming Services group owns the session, entitlement and playback-start services, written in Kotlin on AWS. We are looking for a lead engineer to run a team of six, set its technical direction and keep the services calm on the loudest weekends of the year. The role is Hybrid and based in Melbourne.

## What you will do

- Lead six engineers: plan the quarter, split the work and clear the blockers.
- Set the design of the playback-start path so that it stays fast when traffic jumps tenfold.
- Decide where to cut services apart and where to keep them together.
- Review the designs of other teams that depend on your services.
- Run the pre-event checklist and lead the calm, blame-free review afterwards.
- Grow two senior engineers toward lead roles.
- Agree budgets and risks with the head of platform every month.

## What you bring

- 8 to 14 years of backend work, with Kotlin at an advanced level (4 of 5).
- Expert Microservices architecture and System design skills (5 of 5), proved by systems that survived real peaks.
- Technical leadership at an advanced level: other teams ask you for design advice.
- Team leadership at an advanced level: you have managed or led a team of five or more.
- AWS at an advanced level (4 of 5), including cost and failure planning.
- Calm communication with product managers and executives.

## Nice to have

- Amazon DynamoDB and Apache Kafka at a proficient level.
- Strong Observability practice: service levels, alerts that matter and clear dashboards.
- Hands-on Estimation and planning with an agile team, and Mentoring that people thank you for.

## Tech stack

Kotlin on the JVM, AWS with Amazon DynamoDB and Apache Kafka, containers on AWS Fargate and a shared Observability stack built on OpenTelemetry.

## Certifications and awards

- Preferred certification: AWS Certified Solutions Architect - Associate.
- Preferred award kind: Employer recognition.

## What we offer

- $190,000 to $215,000 a year, plus 12% superannuation.
- Hybrid work: two days a week in our Melbourne office, with a quiet room for calls.
- Five weeks of annual leave and a recovery day after each major live event.
- Free season passes to the sport that we stream.
- A $4,000 yearly budget for leadership courses and conferences.

## About Bunyipstream

Bunyipstream streams live sport and events to browsers, phones and television apps. It was founded in 2015 and has about 180 people in Melbourne. Its engineers are on call for the events that they build.

## How we hire

- A conversation with the head of platform about the team and its goals.
- A design review of a real streaming problem, with two engineers.
- A leadership session with the product lead and one of your future reports.
- A decision within a week of the leadership session.`,
  },
  {
    key: "swe-architect-principal-01", title: "Principal Solutions Architect, Cloud Practice", company: "Tallowbridge Cloud",
    domain: "Software Engineering", specialisation: "Software architecture", level: "Principal", minYears: 12, maxYears: null,
    type: "Full-time", workMode: "Hybrid", city: "Sydney", area: "Sydney NSW",
    salary: { min: 225000, max: 255000, unit: "year" }, occupation: { code: "261112", title: "Solutions Architect" },
    skills: [
      { name: "System design", level: 5, must: true }, { name: "Microservices architecture", level: 5, must: true },
      { name: "API design", level: 5, must: true }, { name: "AWS", level: 5, must: true }, { name: "Technical leadership", level: 5, must: true },
      { name: "Stakeholder management", level: 5, must: true }, { name: "Authentication and authorisation", level: 4, must: false },
      { name: "Cloud security", level: 4, must: false }, { name: "Database design and tuning", level: 4, must: false },
      { name: "Networking fundamentals", level: 3, must: false }, { name: "Communication", level: 5, must: false },
      { name: "Estimation and planning", level: 4, must: false },
    ],
    certifications: { required: ["AWS Certified Solutions Architect - Associate"], preferred: ["AWS Certified Security - Specialty"] }, awards: { preferred: ["conference-talk", "security-competition"] },
    educationMin: "Bachelor's degree", postedDaysAgo: 5, closesInDays: 44,
    description: `## About the role

Tallowbridge Cloud designs cloud systems for banks, utilities and councils, and its biggest projects run for years and cost millions. The Principal Solutions Architect shapes the technical design of those projects, signs off the key decisions and speaks for the practice in front of clients. You will mentor eight architects, review designs across the whole practice and be the person who says where a design will hurt in two years. This is a Hybrid role based in Sydney, with client travel.

## What you will do

- Own the target design of three large client programs and keep it simple.
- Run design reviews for every major project and write clear decisions.
- Join sales talks to explain the approach, the risks and the cost in plain words.
- Set patterns for Microservices architecture, API design and data design across the practice.
- Mentor architects and lead engineers, and help them grow into the next level.
- Work with the security team on identity, network and data rules for regulated clients.
- Write papers and give talks that show the practice's thinking.

## What you bring

- 12 or more years in software and cloud work, with at least five years as an architect of large systems.
- System design, Microservices architecture and API design at an expert level (5 of 5).
- AWS at an expert level, from landing zones to data and messaging services.
- Technical leadership that other architects follow without being told.
- Stakeholder management at an expert level (5 of 5): you can calm an angry steering committee.
- The AWS Solutions Architect certification, as listed below.

## Nice to have

- Authentication and authorisation, Cloud security and Networking fundamentals at a deep level.
- Database design and tuning for very large systems.
- Strong Communication and Estimation and planning skills for client proposals.

## Tech stack

AWS as the main platform, with Azure for some clients. Typical designs use microservices on Kubernetes, event streaming, managed databases and infrastructure as code.

## Certifications and awards

- Required certification: AWS Certified Solutions Architect - Associate.
- Preferred certification: AWS Certified Security - Specialty.
- Awards we value: Conference talk or paper and Security competition or bug bounty. They are preferred, not required.

## What we offer

- $225,000 to $255,000 a year, plus 12% superannuation.
- Hybrid work: two days a week in our Sydney office, and the rest at home or with clients.
- Five weeks of annual leave and a paid sabbatical week after three years.
- A $5,000 yearly budget for conferences, writing and courses.
- A share in the practice bonus pool.

## About Tallowbridge Cloud

Tallowbridge Cloud is a cloud consultancy for banks, utilities and councils. It was founded in 2013 and has about 200 people in Sydney and Melbourne. Architects sit in the centre of its projects, not at the edge.

## How we hire

- A conversation with the head of the practice.
- A review of a design that you led, which you present to three architects.
- A panel on how you work with clients and with engineers.
- A decision within a week of the panel.`,
  },
  {
    key: "swe-platform-lead-01", title: "Lead Site Reliability Engineer (Contract)", company: "Numbatforge",
    domain: "Software Engineering", specialisation: "Platform and DevOps", level: "Lead", minYears: 9, maxYears: 14,
    type: "Contract", workMode: "Remote", city: "Remote", area: "Remote (Australia)",
    salary: { min: 1080, max: 1200, unit: "day" }, occupation: { code: "261316", title: "DevOps Engineer" },
    skills: [
      { name: "Site reliability engineering", level: 5, must: true }, { name: "Kubernetes", level: 4, must: true },
      { name: "Observability", level: 5, must: true }, { name: "Incident response", level: 5, must: true },
      { name: "Terraform", level: 4, must: true }, { name: "Technical leadership", level: 4, must: true }, { name: "Linux", level: 4, must: false },
      { name: "Go", level: 3, must: false }, { name: "Prometheus", level: 4, must: false }, { name: "Grafana", level: 3, must: false },
      { name: "Mentoring", level: 4, must: false },
    ],
    certifications: { required: ["AWS Certified DevOps Engineer - Professional"], preferred: [] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 10, closesInDays: 9,
    description: `## About the role

Numbatforge hosts build pipelines for thousands of software teams, and an outage stops them all. The company wants a lead reliability engineer for a six-month contract to set up service levels, tidy the alerts and teach two teams how to run incident reviews. You will work with the head of engineering and have a free hand in how to get there. The work is fully Remote in Australia, with one planning week in Melbourne.

## What you will do

- Define service levels and error budgets with the product teams, and publish them.
- Rebuild the alert rules so that each page tells the on-call person what to do next.
- Run two live game days where we break things on purpose, then fix the gaps.
- Lead incident reviews and train two teams to run them without you.
- Review the Kubernetes and Terraform setup for single points of failure.
- Leave a runbook library and a short plan for the next 12 months.

## What you bring

- 9 to 14 years of operations, platform or reliability work.
- Site reliability engineering, Observability and Incident response at an expert level (5 of 5).
- Kubernetes and Terraform at an advanced level (4 of 5).
- Technical leadership across teams that you do not manage.
- A current AWS DevOps professional certification, as listed below.

## Nice to have

- Linux depth and Go for small tools.
- Prometheus at an advanced level and Grafana at a proficient level.
- Mentoring of on-call engineers who are new to incident work.

## Tech stack

Kubernetes and Terraform on Linux hosts, Prometheus and Grafana for metrics, and Go services. The monitoring is largely open source.

## Certifications and awards

- Required certification: AWS Certified DevOps Engineer - Professional.

## What we offer

- A day rate of $1,080 to $1,200, paid through your company or an agency.
- A six-month contract that can extend by agreement.
- Fully Remote work, with one planning week in Melbourne and travel paid.
- A small, senior team and direct access to the head of engineering.
- No on-call duty beyond the game days, unless you choose it.

## About Numbatforge

Numbatforge is a remote-first company with about 70 people across Australia. It started in 2020 around an open-source build tool. Today the company sells hosted pipelines to software teams.

## How we hire

- A video call with the head of engineering.
- A conversation about a reliability project that you led.
- A reference check, then a decision within three working days.`,
  },
  {
    key: "swe-backend-mid-01", title: "Backend Engineer (Go), Developer Tools", company: "Numbatforge",
    domain: "Software Engineering", specialisation: "Backend", level: "Mid", minYears: 3, maxYears: 6,
    type: "Full-time", workMode: "Remote", city: "Remote", area: "Remote (Australia)",
    salary: { min: 125000, max: 145000, unit: "year" }, occupation: { code: "261313", title: "Software Engineer" },
    skills: [
      { name: "Go", level: 4, must: true }, { name: "gRPC", level: 3, must: true }, { name: "PostgreSQL", level: 3, must: true },
      { name: "Docker", level: 3, must: true }, { name: "API design", level: 3, must: true }, { name: "Redis", level: 2, must: false },
      { name: "Linux", level: 3, must: false }, { name: "CI/CD", level: 3, must: false },
      { name: "Unit and integration testing", level: 3, must: false }, { name: "Technical documentation", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["Certified Kubernetes Application Developer"] }, awards: { preferred: ["open-source"] },
    educationMin: "Bachelor's degree", postedDaysAgo: 5, closesInDays: 33,
    description: `## About the role

Numbatforge makes the build and deploy tools that thousands of developers use every day. The Pipelines team runs the service that schedules those builds and streams logs back to the browser. The team has five engineers in three time zones, and it needs a mid-level Go engineer to take over the log streaming and queue work. You will ship to production in your first fortnight and own a service by the end of your first quarter.

## What you will do

- Build and maintain the Go services that schedule builds and stream logs to users.
- Add gRPC endpoints and keep their contracts stable for the web app and the command line tool.
- Move build metadata into PostgreSQL tables that stay fast at 50 million rows.
- Use Redis for short-lived queues and tune the expiry rules.
- Write the tests and the runbook for each change that you ship.
- Answer questions from open-source users in our public issue tracker twice a week.
- Hand work to teammates in other time zones with short, clear written notes.

## What you bring

- 3 to 6 years of backend work, with Go at an advanced level (4 of 5).
- gRPC and API design skills at a proficient level (3 of 5), including versioning and error design.
- Proficient PostgreSQL skills and everyday Docker use.
- Comfort on Linux, and CI/CD pipelines that you can fix when they break.
- Unit and integration testing as a habit, not a chore.
- Clear Technical documentation: you leave notes that a stranger could follow.

## Nice to have

- Redis experience beyond a simple cache.
- A merged contribution to an open-source project of any size.
- Experience with build systems or container runtimes.

## Tech stack

Go, gRPC with Protocol Buffers, PostgreSQL, Redis and Docker on Linux hosts. We build Numbatforge with Numbatforge, so the team also lives in the product's own CI/CD pipelines.

## Certifications and awards

- Preferred certification: Certified Kubernetes Application Developer.
- Preferred award kind: Open source contribution.

## What we offer

- $125,000 to $145,000 a year, plus 12% superannuation.
- Remote work from anywhere in Australia, with a team week in a different city twice a year.
- $1,500 for your home office and a monthly internet allowance.
- Four weeks of annual leave and a company-wide shutdown between Christmas and New Year.
- A learning budget of $2,000 a year.

## About Numbatforge

Numbatforge is a remote-first company with about 70 people across Australia. It started in 2020 around an open-source build tool. Today the company sells hosted pipelines to software teams.

## How we hire

- A video call with the engineering manager and a team member.
- A take-home task of about two hours, which we pay you for.
- A paired session on the code that you wrote, with two future teammates.
- An offer within a week of the final conversation.`,
  },
  {
    key: "swe-backend-senior-01", title: "Senior Backend Engineer, Payments", company: "Quokkawave Systems",
    domain: "Software Engineering", specialisation: "Backend", level: "Senior", minYears: 5, maxYears: 10,
    type: "Full-time", workMode: "Hybrid", city: "Sydney", area: "Sydney NSW",
    salary: { min: 175000, max: 195000, unit: "year" }, occupation: { code: "261313", title: "Software Engineer" },
    skills: [
      { name: "Java", level: 5, must: true }, { name: "Spring Boot", level: 4, must: true }, { name: "Apache Kafka", level: 4, must: true },
      { name: "PostgreSQL", level: 4, must: true }, { name: "Kubernetes", level: 4, must: true }, { name: "System design", level: 4, must: true },
      { name: "API design", level: 4, must: false }, { name: "Docker", level: 4, must: false },
      { name: "Unit and integration testing", level: 4, must: false }, { name: "Observability", level: 3, must: false },
      { name: "Mentoring", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["Confluent Certified Developer for Apache Kafka"] }, awards: { preferred: ["conference-talk"] },
    educationMin: "Bachelor's degree", postedDaysAgo: 2, closesInDays: 28,
    description: `## About the role

Quokkawave Systems runs the card and bank-transfer rails behind about 40,000 small shops across Australia. The Payments squad owns the service that approves each sale and settles it the next morning. Volume doubled last year, and the settlement service now needs a senior engineer to split it into clean domains. You will join six engineers and shape how money moves through the platform.

## What you will do

- Design and build the Java services that approve, capture and settle card payments.
- Split the settlement monolith into smaller services without dropping a single transaction.
- Model payment events on Kafka topics and make every consumer safe to replay.
- Tune PostgreSQL queries and schemas for tables that grow by millions of rows each week.
- Run your services on Kubernetes and share the on-call rota with the squad.
- Review code, write design notes and coach two mid-level engineers.
- Work with the risk and billing teams to turn new scheme rules into working software.

## What you bring

- 5 to 10 years of backend work, with Java at an expert level (5 of 5) and Spring Boot at an advanced level (4 of 5).
- Advanced Apache Kafka skills: partitioning, idempotent consumers and schema changes with no downtime.
- Advanced PostgreSQL skills, including indexing, locking and safe migrations.
- Advanced Kubernetes skills: you ship manifests, tune resource limits and debug a failing pod on your own.
- Advanced System design skills, shown in real systems that carry money.
- Strong API design, Docker and Unit and integration testing habits, with Observability in mind from day one.

## Nice to have

- Knowledge of card scheme rules or open banking standards.
- A talk or write-up about a payments or messaging design.
- A record of Mentoring people who later became tech leads.

## Tech stack

Java 21 with Spring Boot, Apache Kafka, PostgreSQL, Docker and Kubernetes on AWS. Builds run in GitHub Actions, and dashboards run on Prometheus and Grafana.

## Certifications and awards

- Preferred certification: Confluent Certified Developer for Apache Kafka.
- Preferred award kind: Conference talk or paper.

## What we offer

- $175,000 to $195,000 a year, plus 12% superannuation.
- Hybrid work: three days a week in our Sydney office and two at home.
- Four weeks of annual leave, ten days of personal leave and 18 weeks of paid parental leave.
- A learning budget of $3,000 a year and two conference days.
- An on-call rota of one week in six, with time back in lieu.

## About Quokkawave Systems

Quokkawave Systems builds payment and point-of-sale software for small merchants. It was founded in 2017 and has about 260 people, most of them in Sydney. Every product team runs its own services and ships to production daily.

## How we hire

- A 30-minute chat with the hiring manager about your recent work.
- A 90-minute pairing session on a small Java and Kafka exercise.
- A system design talk with two engineers, then a values chat with the squad lead.
- You hear back within a week of each step, and offers go out within three weeks.`,
  },
  {
    key: "swe-fullstack-intern-01", title: "Software Engineering Intern, Web Platform", company: "Rosellaworks",
    domain: "Software Engineering", specialisation: "Full-stack", level: "Intern", minYears: 0, maxYears: 1,
    type: "Graduate / Internship", workMode: "Hybrid", city: "Sydney", area: "Sydney NSW",
    salary: { min: 56000, max: 64000, unit: "year" }, occupation: { code: "261312", title: "Developer Programmer" },
    skills: [
      { name: "JavaScript", level: 2, must: true }, { name: "HTML and CSS", level: 2, must: true }, { name: "Git", level: 2, must: true },
      { name: "Teamwork", level: 3, must: true }, { name: "React", level: 2, must: false }, { name: "SQL", level: 1, must: false },
      { name: "Node.js", level: 1, must: false }, { name: "Communication", level: 2, must: false },
      { name: "Continuous learning", level: 3, must: false },
    ],
    certifications: { required: [], preferred: [] }, awards: { preferred: [] },
    educationMin: "High school", postedDaysAgo: 16, closesInDays: 38,
    description: `## About the role

Rosellaworks builds classroom tools for primary and secondary schools, and each year it runs a paid internship for students who want to build real software. This six-month internship sits in the Web Platform team and fits around your studies, with two or three days a week. You will work on the teacher dashboard with a mentor and ship at least one feature to real schools. We choose people for curiosity and teamwork first, and for skill second.

## What you will do

- Build small screens in the teacher dashboard with a mentor beside you.
- Fix bugs that teachers report, starting with the easy ones.
- Write simple SQL queries to answer questions from the support team.
- Learn how code moves from your laptop to a live school.
- Present your work to the whole company at the end of the internship.

## What you bring

- Enrolment in a computer science, software engineering or similar course. You do not need a finished degree.
- 0 to 1 years of experience, or a few small projects that you built yourself.
- JavaScript, HTML and CSS at a working level (2 of 5).
- Git basics: you have made a commit and opened a pull request.
- Teamwork and the courage to ask for help early.

## Nice to have

- A first look at React, Node.js or SQL.
- Clear Communication in writing and in meetings.
- Continuous learning habits: a course, a club or a weekend project.

## Tech stack

JavaScript and React in the browser, a Node.js API, a PostgreSQL database and Git with pull requests. You learn the rest on the job.

## What we offer

- $56,000 to $64,000 a year for a full working week, paid pro rata for two or three days a week, plus 12% superannuation.
- Hybrid work: one day a week in our Sydney office and the rest at home.
- Flexible days around exams and study weeks.
- A mentor, a buddy and a review every month.
- A strong chance of a graduate offer if the internship goes well.

## About Rosellaworks

Rosellaworks makes planning and assessment tools for schools. It was founded in 2018 and has about 45 people in Sydney. Teachers and former teachers work next to the engineers.

## How we hire

- A short online form about your projects and your course.
- A 30-minute chat with two people from the team.
- A small, friendly coding exercise that we do together.
- An answer within a week.`,
  },
  {
    key: "swe-backend-junior-01", title: "Junior Backend Developer, Node.js", company: "Moretonbyte",
    domain: "Software Engineering", specialisation: "Backend", level: "Junior", minYears: 0, maxYears: 2,
    type: "Full-time", workMode: "Hybrid", city: "Brisbane", area: "Brisbane QLD",
    salary: { min: 82000, max: 96000, unit: "year" }, occupation: { code: "261312", title: "Developer Programmer" },
    skills: [
      { name: "TypeScript", level: 3, must: true }, { name: "Node.js", level: 3, must: true }, { name: "SQL", level: 3, must: true },
      { name: "Git", level: 3, must: true }, { name: "NestJS", level: 2, must: false }, { name: "API design", level: 2, must: false },
      { name: "Jest", level: 2, must: false }, { name: "Docker", level: 1, must: false }, { name: "Teamwork", level: 2, must: false },
    ],
    certifications: { required: [], preferred: [] }, awards: { preferred: ["competitive-programming"] },
    educationMin: "Bachelor's degree", postedDaysAgo: 12, closesInDays: 40,
    description: `## About the role

Moretonbyte runs the booking and ticketing system for ferries and tour operators around Moreton Bay and the Queensland coast. The backend is a set of Node.js services, and the team of five wants a junior developer who writes tidy TypeScript and asks good questions. You will pair with a senior engineer every week and ship small features in your first month. This is a Hybrid role in Brisbane, with two days a week at home.

## What you will do

- Build small features in our Node.js services, such as a new fare rule or a booking reminder.
- Write SQL queries and migrations for booking and passenger tables.
- Add tests with Jest for every change that you make.
- Fix bugs that support staff report, and explain the cause in the ticket.
- Join code reviews as both author and reviewer.
- Learn how a request moves from the mobile app to the database and back.

## What you bring

- 0 to 2 years of experience, or a strong final-year project or work placement.
- TypeScript and Node.js at a proficient level (3 of 5): you can build a small service from a blank folder.
- SQL at a proficient level (3 of 5), including joins and simple indexes.
- Git at a proficient level: branches, pull requests and merge conflicts do not scare you.
- Teamwork: you say what you are stuck on early.

## Nice to have

- NestJS, Jest or API design practice from a course or a side project.
- A first look at Docker.
- A result in a coding contest or a hackathon.

## Tech stack

TypeScript on Node.js with NestJS, PostgreSQL, Jest and Docker. Services run on AWS, and the team uses GitHub for code and reviews.

## Certifications and awards

- Preferred award kind: Competitive programming.

## What we offer

- $82,000 to $96,000 a year, plus 12% superannuation.
- Hybrid work: three days in our Brisbane office and two at home.
- A named mentor and a 12-month learning plan that you write with your lead.
- Four weeks of annual leave and ten days of personal leave.
- Free ferry passes when you travel with the team to the islands for our yearly offsite.

## About Moretonbyte

Moretonbyte builds booking and ticketing software for ferries, tours and marinas in Queensland. It was founded in 2017 and has about 55 people in Brisbane. Its small teams ship every week.

## How we hire

- A 20-minute call about the projects that you built.
- A friendly coding session where we write a small API together.
- A chat with two teammates about how you like to learn.
- Feedback on the day of the coding session, and an answer within the week.`,
  },
  {
    key: "swe-frontend-mid-02", title: "Frontend Engineer (Angular), Merchant Portal", company: "Quokkawave Systems",
    domain: "Software Engineering", specialisation: "Frontend", level: "Mid", minYears: 3, maxYears: 7,
    type: "Full-time", workMode: "Onsite", city: "Sydney", area: "Sydney NSW",
    salary: { min: 112000, max: 128000, unit: "year" }, occupation: { code: "261212", title: "Web Developer" },
    skills: [
      { name: "Angular", level: 4, must: true }, { name: "TypeScript", level: 4, must: true }, { name: "HTML and CSS", level: 3, must: true },
      { name: "Cypress", level: 3, must: true }, { name: "API design", level: 3, must: false }, { name: "Git", level: 3, must: false },
      { name: "Unit and integration testing", level: 3, must: false }, { name: "Data visualisation", level: 3, must: false },
      { name: "Web accessibility", level: 2, must: false }, { name: "Agile delivery", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["Professional Scrum Master I"] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 19, closesInDays: 16,
    description: `## About the role

Merchants use the Quokkawave Systems portal to check sales, refunds and payouts, and about 60,000 people sign in each week. The portal is an Angular application that has grown over six years, and the team is now cleaning up its structure and its charts. The work is Onsite at our Sydney office, where the portal team of seven sits together with design and support. As a mid-level engineer, you will own the reports pages and bring them up to the standard of the new payment screens.

## What you will do

- Refactor the reports pages in Angular and TypeScript into small, tested parts.
- Build new charts and tables, with Data visualisation that a shop owner can read at a glance.
- Write end-to-end tests with Cypress for the most used merchant flows.
- Agree API changes with backend engineers and keep the contracts clear.
- Fix accessibility problems that support staff report.
- Take part in planning, demos and the retrospective each fortnight.

## What you bring

- 3 to 7 years of frontend work, with Angular and TypeScript at an advanced level (4 of 5).
- HTML and CSS at a proficient level (3 of 5), including responsive tables.
- Cypress at a proficient level: you write tests that do not flake.
- Good API design sense, and Git habits that keep the history clear.
- Comfort with Unit and integration testing in Angular.

## Nice to have

- Web accessibility knowledge at a working level.
- Agile delivery experience in a squad with a product owner.
- Experience with dashboards that show money, such as payouts and fees.

## Tech stack

Angular and TypeScript, Cypress, a REST API built in Java, Git with pull requests, and a design system shared with the mobile apps.

## Certifications and awards

- Preferred certification: Professional Scrum Master I.

## What we offer

- $112,000 to $128,000 a year, plus 12% superannuation.
- Onsite work in our Sydney office, five days a week, with a standing desk and a quiet room.
- Four weeks of annual leave and half-day Fridays in January.
- A $2,500 learning budget and a yearly conference day.
- Free fruit, coffee and a monthly team lunch.

## About Quokkawave Systems

Quokkawave Systems builds payment and point-of-sale software for small merchants. It was founded in 2017 and has about 260 people, most of them in Sydney. Product teams sit together and ship to production every day.

## How we hire

- A 30-minute call with the hiring manager.
- A technical talk about an Angular app that you built.
- A pairing session on a small reports page, with two teammates.
- An answer within a week.`,
  },
  {
    key: "ai-mle-lead-01", title: "Lead Machine Learning Engineer, Foundation Models", company: "Dingocreek Labs",
    domain: "AI & Machine Learning", specialisation: "Machine learning engineering", level: "Lead", minYears: 7, maxYears: 13,
    type: "Full-time", workMode: "Remote", city: "Remote", area: "Remote (Australia)",
    salary: { min: 200000, max: 228000, unit: "year" }, occupation: { code: "261399", title: "Machine Learning Engineer" },
    skills: [
      { name: "Python", level: 5, must: true }, { name: "Deep learning", level: 5, must: true }, { name: "PyTorch", level: 5, must: true },
      { name: "Model evaluation", level: 4, must: true }, { name: "Distributed training and GPU computing", level: 4, must: true },
      { name: "Technical leadership", level: 4, must: true }, { name: "Team leadership", level: 4, must: true },
      { name: "Machine learning", level: 5, must: false }, { name: "Mentoring", level: 4, must: false }, { name: "MLflow", level: 3, must: false },
      { name: "Statistics", level: 4, must: false }, { name: "Responsible AI", level: 3, must: false },
    ],
    certifications: { required: [], preferred: [] }, awards: { preferred: ["conference-talk"] },
    educationMin: "Master's degree", postedDaysAgo: 20, closesInDays: 22,
    description: `## About the role

Dingocreek Labs is an independent research lab that trains language and vision models for Australian science and industry, and it publishes most of its work. The Foundation Models group of nine trains models on a cluster of 256 GPUs and needs a lead who can keep the research ambitious and the training runs reliable. You will set the technical plan, manage a team of five and stay close to the code. The role is fully Remote in Australia.

## What you will do

- Plan and run large training jobs, from data pipeline to checkpoint and restart.
- Design the evaluation suite that tells us if a new model is really better.
- Lead five engineers and researchers: set goals, remove blockers and give honest feedback.
- Speed up training with better parallelism, mixed precision and smarter data loading.
- Work with the safety group on tests for harmful or biased output.
- Write papers and technical reports with the team.
- Represent the lab at partner meetings and at one or two conferences a year.

## What you bring

- 7 to 13 years in machine learning, with Python, Deep learning and PyTorch at an expert level (5 of 5).
- Distributed training and GPU computing at an advanced level (4 of 5): sharding, memory limits and failure recovery.
- Model evaluation at an advanced level, including benchmarks that can be gamed and how to avoid them.
- Technical leadership and Team leadership at an advanced level, shown by teams that you led.
- A master's degree or a PhD in a related field, or equal research work.

## Nice to have

- Responsible AI practice, with real red-team or bias testing work.
- MLflow and Statistics skills for careful experiments.
- Mentoring of researchers who are new to engineering.

## Tech stack

Python and PyTorch with a Slurm GPU cluster, an experiment tracker built on MLflow, Linux nodes with fast storage and a small set of internal tools for data processing.

## Certifications and awards

- Preferred award kind: Conference talk or paper.

## What we offer

- $200,000 to $228,000 a year, plus 12% superannuation.
- Fully Remote work in Australia, with two lab weeks a year in Canberra.
- A fair share of compute for your own research ideas, every month.
- Five weeks of annual leave and a $6,000 yearly budget for conferences and travel.
- Time to publish: one day a fortnight for papers.

## About Dingocreek Labs

Dingocreek Labs is an independent AI research lab. It was founded in 2021 and has about 40 people who work from home across Australia. It publishes its papers and releases some models to the public.

## How we hire

- A call with the research director.
- A technical talk about a training project that you led.
- A session with two researchers on evaluation and design.
- A decision within eight working days.`,
  },
  {
    key: "ai-genai-junior-01", title: "Junior AI Engineer, Prompt and Evaluation", company: "Gidgeebyte",
    domain: "AI & Machine Learning", specialisation: "Generative AI and LLM", level: "Junior", minYears: 0, maxYears: 2,
    type: "Full-time", workMode: "Onsite", city: "Perth", area: "Perth WA",
    salary: { min: 88000, max: 102000, unit: "year" }, occupation: { code: "261311", title: "Generative AI Engineer" },
    skills: [
      { name: "Python", level: 3, must: true }, { name: "Prompt engineering", level: 3, must: true }, { name: "LLM APIs", level: 2, must: true },
      { name: "Generative AI", level: 2, must: true }, { name: "Git", level: 2, must: false }, { name: "FastAPI", level: 2, must: false },
      { name: "SQL", level: 2, must: false }, { name: "Retrieval-augmented generation", level: 1, must: false },
      { name: "Teamwork", level: 3, must: false }, { name: "Continuous learning", level: 3, must: false },
      { name: "Communication", level: 3, must: false },
    ],
    certifications: { required: ["AWS Certified AI Practitioner"], preferred: [] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 13, closesInDays: 34,
    description: `## About the role

Gidgeebyte checks every answer that its assistants send, and the Prompt and Evaluation team writes the tests that do the checking. As a junior AI engineer you will write prompts, build test sets and run reports that tell the product team when an update makes the assistant better or worse. You will learn how large language models behave when they meet messy, real messages. This is an Onsite role in our Perth office, with a mentor at the next desk.

## What you will do

- Write and improve prompts for new assistant features with your mentor.
- Build test sets of customer messages, with private details removed.
- Run the evaluation suite on every release and write a short report.
- Call LLM APIs from small Python scripts and FastAPI endpoints.
- Query conversation data with SQL to find where the assistant struggles.
- Share what you learn in a short note every week.

## What you bring

- 0 to 2 years of experience, or a university or bootcamp project that used an LLM.
- Python at a proficient level (3 of 5), including reading and writing files and calling web APIs.
- Prompt engineering at a proficient level: clear instructions, examples and checks.
- LLM APIs and Generative AI basics (2 of 5): you know tokens, temperature and why models make things up.
- The AWS AI Practitioner certificate, as listed below.
- Good Teamwork and honest Communication.

## Nice to have

- Git, FastAPI or SQL from your own projects.
- A first project with Retrieval-augmented generation.
- Continuous learning: you follow the field and try new ideas.

## Tech stack

Python, FastAPI, hosted LLM APIs, a SQL database, a small evaluation tool that we wrote ourselves and Git.

## Certifications and awards

- Required certification: AWS Certified AI Practitioner.

## What we offer

- $88,000 to $102,000 a year, plus 12% superannuation.
- Onsite work in our Perth office, five days a week, with a desk next to your mentor.
- Four weeks of annual leave and ten days of personal leave.
- Exam fees paid for the next AWS certification.
- Lunch on Fridays and a team walk along the river each month.

## About Gidgeebyte

Gidgeebyte is a young company with about 25 people. It was founded in 2024, with its main office in Perth. It builds AI assistants for small service businesses.

## How we hire

- A 20-minute call with the team lead about your first LLM project.
- A short exercise on writing and testing a prompt.
- A visit to the Perth office and a chat with two engineers.
- A decision within five working days of your visit.`,
  },
  {
    key: "ai-genai-mid-01", title: "Generative AI Engineer, Customer Assistants", company: "Gidgeebyte",
    domain: "AI & Machine Learning", specialisation: "Generative AI and LLM", level: "Mid", minYears: 2, maxYears: 4,
    type: "Full-time", workMode: "Remote", city: "Remote", area: "Remote (Australia)",
    salary: { min: 135000, max: 158000, unit: "year" }, occupation: { code: "261311", title: "Generative AI Engineer" },
    skills: [
      { name: "Prompt engineering", level: 4, must: true }, { name: "LLM APIs", level: 4, must: true }, { name: "Python", level: 4, must: true },
      { name: "Retrieval-augmented generation", level: 3, must: true }, { name: "FastAPI", level: 3, must: true },
      { name: "Vector databases", level: 3, must: false }, { name: "LangChain", level: 3, must: false },
      { name: "Generative AI", level: 3, must: false }, { name: "Git", level: 3, must: false },
      { name: "Experimentation and A/B testing", level: 2, must: false }, { name: "Product thinking", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["Databricks Certified Generative AI Engineer Associate"] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 6, closesInDays: 27,
    description: `## About the role

Gidgeebyte builds AI assistants for trade and field-service businesses: plumbers, electricians and cleaners who answer customer messages between jobs. The assistants read the question, check the job calendar and draft a reply that the owner approves with one tap. We are a team of 25 and the product is only two years old, so each engineer shapes it. This Remote role suits a mid-level engineer who likes to ship small improvements every week.

## What you will do

- Write and test prompts for quoting, booking and follow-up messages.
- Build retrieval over each business's price list and past jobs, so that quotes stay accurate.
- Add new tools to the assistant, such as a calendar check or a parts lookup.
- Run small A/B tests on reply quality and measure how often owners accept a draft.
- Watch real conversations (with private details removed) to learn what to fix next.
- Keep the FastAPI services fast and cheap to run.

## What you bring

- 2 to 4 years of software or machine learning work, with Python at an advanced level (4 of 5).
- Prompt engineering and LLM APIs at an advanced level: you know how to make a model follow a format.
- Retrieval-augmented generation and FastAPI at a proficient level (3 of 5).
- Judgement about quality: you can tell a good reply from one that only sounds good.
- Willingness to work in a small team that decides fast.

## Nice to have

- Vector databases, LangChain and Generative AI projects that you finished.
- Experimentation and A/B testing habits.
- Product thinking and good Git manners.

## Tech stack

Python, FastAPI, hosted LLM APIs, LangChain for some flows, a vector database and Git. Everything runs on a managed cloud with simple deploys.

## Certifications and awards

- Preferred certification: Databricks Certified Generative AI Engineer Associate.

## What we offer

- $135,000 to $158,000 a year, plus 12% superannuation.
- Remote work from anywhere in Australia, with a team week in Perth each year.
- A model budget for your own experiments and $1,500 for your home office.
- Four weeks of annual leave and a company shutdown between Christmas and New Year.
- Share options that vest over four years.

## About Gidgeebyte

Gidgeebyte is a young company with about 25 people. It was founded in 2024, with its main office in Perth and most staff working from home. It builds AI assistants for small service businesses.

## How we hire

- A short video call with a founder.
- A two-hour paid task on a prompt and retrieval problem.
- A talk with two engineers about your solution.
- An offer within five working days.`,
  },
  {
    key: "ai-mlops-mid-01", title: "MLOps Engineer (Contract), Azure", company: "Tallowbridge Cloud",
    domain: "AI & Machine Learning", specialisation: "MLOps", level: "Mid", minYears: 2, maxYears: 6,
    type: "Contract", workMode: "Hybrid", city: "Sydney", area: "Sydney NSW",
    salary: { min: 760, max: 840, unit: "day" }, occupation: { code: "263111", title: "MLOps Engineer" },
    skills: [
      { name: "MLOps", level: 3, must: true }, { name: "Azure Machine Learning", level: 4, must: true }, { name: "Docker", level: 3, must: true },
      { name: "Python", level: 3, must: true }, { name: "Azure DevOps", level: 3, must: true }, { name: "CI/CD", level: 3, must: false },
      { name: "Kubernetes", level: 2, must: false }, { name: "MLflow", level: 3, must: false }, { name: "Git", level: 3, must: false },
      { name: "Terraform", level: 2, must: false }, { name: "Observability", level: 2, must: false },
    ],
    certifications: { required: ["Microsoft Certified: Azure Data Scientist Associate"], preferred: [] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 4, closesInDays: 8,
    description: `## About the role

A large utility client of Tallowbridge Cloud has built 14 machine learning models in notebooks and now wants them to run as a reliable service. You will join a client team of six as the mid-level MLOps engineer on a four-month contract to move the models to Azure Machine Learning, with pipelines, tests and monitoring. The client's data scientists will learn from you as you build. This is a Hybrid contract in Sydney, with two days a week on the client site.

## What you will do

- Turn notebooks into Python packages with tests and clear inputs.
- Build Azure Machine Learning pipelines for training, scoring and retraining.
- Package models in Docker and deploy them to managed endpoints.
- Set up Azure DevOps pipelines with approvals before each release.
- Add checks and alerts for bad data and drifting predictions.
- Teach two data scientists how to run the pipelines themselves.

## What you bring

- 2 to 6 years of software, data or machine learning engineering.
- Azure Machine Learning at an advanced level (4 of 5), and MLOps at a proficient level (3 of 5).
- Docker, Python and Azure DevOps at a proficient level.
- A clear way of explaining pipelines to people who build models, not software.
- The Azure Data Scientist Associate certificate, as listed below.

## Nice to have

- CI/CD design, Git branching and MLflow tracking.
- Kubernetes and Terraform at a working level (2 of 5).
- Observability practice for model services.

## Tech stack

Azure Machine Learning, Azure DevOps, Docker, Python, MLflow for tracking and Terraform for environments. Some models run on Kubernetes.

## Certifications and awards

- Required certification: Microsoft Certified: Azure Data Scientist Associate.

## What we offer

- A day rate of $760 to $840, paid through your company or an agency.
- A four-month contract, with a good chance of extension.
- Hybrid work: two days a week on the client site in Sydney and the rest at home.
- A client team that is keen to learn.
- Fast start: we aim to finish onboarding in two working days.

## About Tallowbridge Cloud

Tallowbridge Cloud is a cloud consultancy for banks, utilities and councils. It was founded in 2013 and has about 200 people in Sydney and Melbourne. Contractors work in the same teams as staff.

## How we hire

- A 30-minute call about the contract.
- A technical chat on Azure Machine Learning and pipelines.
- An answer within two working days of the technical chat.`,
  },
  {
    key: "ai-vision-senior-01", title: "Senior Computer Vision Engineer, Maritime Sensing", company: "Torrensline Systems",
    domain: "AI & Machine Learning", specialisation: "Computer vision", level: "Senior", minYears: 6, maxYears: 12,
    type: "Full-time", workMode: "Onsite", city: "Adelaide", area: "Adelaide SA",
    salary: { min: 150000, max: 172000, unit: "year" }, occupation: { code: "261399", title: "Machine Learning Engineer" },
    skills: [
      { name: "Computer vision", level: 5, must: true }, { name: "PyTorch", level: 4, must: true }, { name: "Deep learning", level: 4, must: true },
      { name: "C++", level: 4, must: true }, { name: "Python", level: 4, must: true }, { name: "Model evaluation", level: 4, must: true },
      { name: "Distributed training and GPU computing", level: 3, must: false }, { name: "Docker", level: 3, must: false },
      { name: "Linux", level: 3, must: false }, { name: "Git", level: 3, must: false }, { name: "Technical documentation", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["Microsoft Certified: Azure AI Engineer Associate"] }, awards: { preferred: ["patent"] },
    educationMin: "Bachelor's degree (Honours)", postedDaysAgo: 10, closesInDays: 45,
    description: `## About the role

Torrensline Systems builds camera and sensor systems that watch the water: ports, ships and coastlines. The vision team of nine trains models that find small boats and floating objects in video at long range, and then ships them to edge computers on vessels. We are hiring a senior computer vision engineer to improve detection in rough weather and at night. This is an Onsite role in Adelaide, where the lab and the test tank are.

## What you will do

- Improve the detection and tracking models for small objects in noisy video.
- Write the C++ inference code that runs the models on edge hardware in real time.
- Train models on multi-GPU machines and manage the labelled data sets.
- Build test rigs and field trials that show how models behave in rain, glare and darkness.
- Prepare clear reports and demos for customers and for the review board.
- Help two junior engineers with their experiments and their code.

## What you bring

- 6 to 12 years in computer vision or a related field, with Computer vision at an expert level (5 of 5).
- PyTorch and Deep learning at an advanced level (4 of 5), including detection and tracking models.
- C++ and Python at an advanced level: you have shipped real-time code.
- Model evaluation at an advanced level, with sound test design and honest numbers.
- A bachelor's degree with honours in engineering, computer science or physics, or more.

## Nice to have

- Distributed training and GPU computing for large video data sets.
- Docker, Linux and Git for repeatable builds on edge devices.
- Strong Technical documentation, because customers audit our work.
- A patent or a published paper in vision or sensing.

## Tech stack

Python and PyTorch for training, C++ with CUDA for inference, Docker and Linux on edge computers, and Git. The lab has a 16-GPU server and a water test tank.

## Certifications and awards

- Preferred certification: Microsoft Certified: Azure AI Engineer Associate.
- Preferred award kind: Patent.

## What we offer

- $150,000 to $172,000 a year, plus 12% superannuation.
- Onsite work in our Adelaide lab, five days a week, with sea trials a few times a year.
- Four weeks of annual leave and extra days off after each sea trial.
- Support for conference trips and for your own patent filings.
- A modern lab with a quiet room and a coffee machine that works.

## About Torrensline Systems

Torrensline Systems builds sensing and vision systems for ports, vessels and coastal monitoring. It was founded in 2012 and has about 120 people in Adelaide. Much of its work is for customers in the maritime industry.

## How we hire

- A call with the vision lead.
- A technical talk about a vision system that you built.
- A day in the lab, with a short design exercise and lunch with the team.
- A decision within a week of your visit.`,
  },
  {
    key: "ai-mle-mid-01", title: "Machine Learning Engineer, Personalisation", company: "Lyrebirdlogic",
    domain: "AI & Machine Learning", specialisation: "Machine learning engineering", level: "Mid", minYears: 2, maxYears: 5,
    type: "Full-time", workMode: "Hybrid", city: "Sydney", area: "Sydney NSW",
    salary: { min: 128000, max: 150000, unit: "year" }, occupation: { code: "261399", title: "Machine Learning Engineer" },
    skills: [
      { name: "Python", level: 4, must: true }, { name: "Machine learning", level: 4, must: true }, { name: "PyTorch", level: 3, must: true },
      { name: "Feature engineering", level: 3, must: true }, { name: "Model evaluation", level: 3, must: true },
      { name: "scikit-learn", level: 4, must: false }, { name: "Docker", level: 3, must: false }, { name: "Git", level: 3, must: false },
      { name: "MLflow", level: 2, must: false }, { name: "SQL", level: 3, must: false }, { name: "Statistics", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["Machine Learning Specialization"] }, awards: { preferred: ["data-science-competition"] },
    educationMin: "Bachelor's degree", postedDaysAgo: 2, closesInDays: 29,
    description: `## About the role

Lyrebirdlogic builds search and recommendation tools for online marketplaces, and its models decide which of 4 million listings a shopper sees first. The Personalisation team of seven trains and ships the ranking models behind the home page and the email digests. We are hiring a mid-level machine learning engineer to own the first-stage retrieval models and to bring new ideas from notebook to production. You will work with a data scientist, a backend engineer and a product manager on one goal: more relevant clicks.

## What you will do

- Train and tune ranking and retrieval models in PyTorch and scikit-learn.
- Build features from clicks, searches and listing data, and keep them fresh each day.
- Check each model with offline tests and a careful online experiment before it ships.
- Package models in Docker and hand them to the serving team with clear tests.
- Track experiments in MLflow so that anyone can reproduce a result.
- Look into odd results, such as a drop in clicks on a single category, and find the cause.

## What you bring

- 2 to 5 years of applied machine learning, with Python and Machine learning at an advanced level (4 of 5).
- PyTorch at a proficient level (3 of 5): you have trained and debugged a neural model.
- Feature engineering and Model evaluation at a proficient level, including bias in click data.
- Good SQL and Statistics, so that you can read an experiment result for yourself.
- Clean Git history and tests for your data code.

## Nice to have

- scikit-learn depth, with gradient boosting and calibration.
- MLflow or a similar tracker in daily use.
- A result in a data science competition, such as a top finish.

## Tech stack

Python, PyTorch, scikit-learn, Docker, MLflow and Git. Data sits in a data warehouse that you query with SQL, and models are served by a Go service owned by the serving team.

## Certifications and awards

- Preferred certification: Machine Learning Specialization.
- Preferred award kind: Data science competition.

## What we offer

- $128,000 to $150,000 a year, plus 12% superannuation.
- Hybrid work: in our Sydney office on three days that the team picks together, and at home on two.
- Four weeks of annual leave and a company shutdown in the first week of January.
- A GPU workstation in the office and cloud credits for your own experiments.
- A $3,000 yearly budget for papers, courses and conferences.

## About Lyrebirdlogic

Lyrebirdlogic makes search and recommendation software for online marketplaces. It was founded in 2017 and has about 110 people in Sydney. Its research reading group meets every Thursday.

## How we hire

- A 30-minute chat about your recent models.
- A take-home task on a small ranking data set, about three hours long.
- A talk with the team about your solution and the trade-offs.
- An answer within a week.`,
  },
];
```

## Form behaviour (`js/core/forms.js`)

- `isEmail`, `fieldError(form, name, msg)`, `clearErrors(form, alertEl)`, `focusFirstError(form)`, `showAlert(alertEl, msg, type)`, `applyFieldErrors(form, fields)` (API `VALIDATION_ERROR`), `enhanceForm(root)` (password show/hide + remember hint ids), `safeNext(next)`.
- Show each error directly below its field. Set `aria-invalid="true"` and link the message with `aria-describedby` (keep the hint id). Focus the first invalid field.
- Alerts use `role="alert"` (rose = error, green = success). Forms have `novalidate`.
- **Do not reveal if an email exists:** sign-up always goes to `/login?registered=1`.

## Responsive

- ≤1024px: 3-column grids become 2; hero h1 56px; auth aside hidden; home columns and the job detail columns stack; footer 2 columns.
- ≤768px: nav links hidden; hero h1 36px; section heads 36px; all grids 1 column; role picker 1 column; search bar 1 column; job card score column left aligned; job detail h1 32px; buttons and inputs at least 44px tall; the shell becomes the mobile top bar + off-canvas pane. Long chips in panel heads wrap (`.panel-actions` wraps; its chips use `white-space: normal`), so nothing scrolls sideways.
- Version 2 parts: ≤1024px "Your path to this job" (`path-grid`) and the job overview columns are one column. ≤768px the pager buttons, the sort and page size selects, the "Compare" check box and the level selects are 44px tall; the "Showing a–b of n" text moves above the pager; the compare tray starts at the left edge (it follows the pane at 248px or 72px on a wide screen); the credential rows (`cred-row`) and the skill rows of the job form are one column; the benefit status moves under its text. On the Compare page the tables scroll inside their own box (`role="region"`, `tabindex="0"`) with a sticky first column, and the cards scroll sideways in their own box; the page never scrolls sideways. A long chip wraps (`.job-main .chip { white-space: normal }`).
- New screens: ≤1024px charts and the recruiter Home columns stack, the job form grid has 2 columns. ≤768px application and job rows stack (side info left aligned), candidate cards are 1 column, the job form, slot inputs and plan cards are 1 column, history and profile rows are 1 column, stepper steps are 72px minimum (the stepper scrolls inside its panel only).

## Security

Follow `AI_Rule.md` Rules 5–7 and 10. Minimum requirements:

**`serve.ps1`** (`param([int]$Port = 5173, [string]$ApiOrigin = "")`)
- `-ApiOrigin` must match `^https?://[A-Za-z0-9.-]+(:\d{1,5})?$`, else exit with an error. It is added to `connect-src`.
- Serve only an allow-list of file types (`.html .css .js .svg .png .jpg .ico .json`). Everything else returns 404, so `serve.ps1` itself is never served. `/` maps to `index.html`.
- **No data route.** The server serves files of `app/` only. The mock has its jobs inside the code, so there is no `data/` path (a request for `/data/...` returns 404).
- Block path traversal: the full path must start with the app folder path **plus a trailing backslash** (case-insensitive).
- Allow only `GET` and `HEAD` (405 for others).
- Headers on every response:
  - `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self' {ApiOrigin}; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'`
  - For `.svg` only: `default-src 'none'; style-src 'unsafe-inline'`.
  - `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy: camera=(), microphone=(), geolocation=()`, `Cache-Control: no-cache`.

**App code**
- Put API data in the page with `textContent` or `esc()`. No `eval()`, no `new Function()`.
- Links with `target="_blank"` have `rel="noopener"`. **No links to other sites** for product data (AI_Rule.md Rule 11): job titles and "Job detail" open `#/jobs/:id`.
- `?next=` goes through `safeNext()` (no open redirects).
- No real PII in sample data. Do not log user data to the console.
- Do not use nationality, ethnicity, gender, age or visa status in any match logic.
- Recruiter screens show only what recruiter endpoints return (allowlist). The frontend never builds a recruiter view from candidate data. Identity (name + email) appears only when `identity` is not null (the candidate consented). The allowlist of version 2 also has the level, the exact years (rounded to 0.5), the skill levels, the certifications and the awards (shared at once; the screens show names and years only), but never a score on the person.
- The employer pages that show a talent are scanned by a test for e-mail text, the words "score", "nationality:", "visa status:", "date of birth", "gender:" and for the words candidate, recruiter and HR.
- Free text that the other side reads (notes, messages, offers, feedback) is scrubbed for emails and phone numbers by the API. The UI also warns the user not to add contact details.
- With the real backend, the app and the API have one address, so `connect-src 'self'` is enough and no CORS is needed. The backend sends the same security headers as `serve.ps1`.
- The token lives in `localStorage`/`sessionStorage` in this build. The backend team may change to an HttpOnly cookie; then `http.js` sends `credentials: "include"` and the API drops the Bearer header.

## Do not

- Do not use emoji, gradients, large soft shadows or pure black.
- Do not use more than 2 tint colors in one card.
- Do not show a score without reasons. Do not show one combined score or a ranking of a person: show coverage per job, skill by skill. An employer never gets a score on a person. In Compare, never add the axes or the areas up, and never rank people.
- Do not hide the privacy text of the certifications and awards step: employers see these names and years at once, so the app tells the talent not to write a name or contact details there.
- Do not draw a line chart of a projection. The 12-month chart is removed.
- Do not ask for sensitive data in onboarding (no nationality, visa status, age, date of birth, gender or photo).
- Do not present placeholder quotes or sample data as real.
- Do not put business rules in views. Put them behind the API.
- Do not link to other job sites or show the name of a data provider. All data is internal Jinder data.

## Build phases (roadmap)

Source: `../Document/sdd/03_FEATURE_SPECIFICATIONS.md` and `../Document/sdd/04_USER_FLOW_SPECIFICATION.md` (read-only). Decisions taken: match = per-skill result + coverage % (backend computes it); job skills = suggested by the API, edited by the recruiter; top N = from the API (mock 5); anonymity ends only with the candidate's consent; rejected applications go to "Past applications"; mock seed data is embedded in this file. Decisions of version 2 (the file `jinder_platform/docs/V2_PLAN.md`): D1 new synthetic data (50 jobs, 50 talent); D2 three domains only; D4 six levels; D5 certifications and awards are shared with employers at once (names and years only); D6 "time" sort = the profile updated most recently (talent list) and the posting date (jobs); D7 "Your path to this job" = a radar with two layers + a Fit list + a Gap list, and the 12-month chart is removed; D8 the user block opens Settings and Premium is highlighted; D9 a Compare menu item, a basket of up to 5, and a full page for both roles. Defaults F1 to F12 (page sizes 10, 20, 50; sort only; the JD markup; the basket in `localStorage`; "Domain" instead of "Industry"; optional exact years; skill levels 1 to 5; new features with the real backend only; the old database is renamed to a backup file; an unstated desired role stays empty; sample profiles are updated over 60 days) are defaults that the user can change (open item O2 in `V2_PLAN.md`). The CV that the scan could not read is still needed (open item O1).

| Phase | Status | Scope |
|---|---|---|
| 0. Restructure | **Done** | One `index.html`, hash router, app shell with hideable left nav, API layer (mock + http), current screens moved without visual change |
| 1. Accounts & roles (F1) | **Done** | Alias at sign-up (own or "Colour Animal", unique, suggest another, no real name or origin words), alias in the shell and on Home, Settings (details, alias, career profile, password, sign out). Return to the page after an ended session was done in Phase 0 |
| 2. Skill translation (F2) | **Done** | CV upload (PDF/DOCX ≤ 10 MB) → reading (poll) → AI pre-fill with "AI-detected" / "Missing" (demo samples in mock mode) → edit → translated profile (original → Australian skill → reason → evidence; cross-border / cross-industry / direct; accept / edit / remove / undo; accept all) → "What employers see" preview → parse-failure fallback. Matching uses accepted skills. Settings shows the shared profile from the API |
| 3. Job matching (F3) | **Done** | Search bar, Jobs results, job card (summary, skill gaps, dates, coverage), Job detail (per-skill match, Apply states, skip, report, similar jobs), bookmarks, skip with undo, report dialog, per-skill coverage formula |
| 4. Applications (F4) | **Done** | Apply review (shared profile + skills) → send → success, Applications Active/Past with ribbons, tracking (stepper, history, edit until Review, slot choice + identity consent, invitation decline, offer reply, feedback) |
| 5. Recruiter (F5 + F6) | **Done** | Recruiter Home, My jobs (badges, target), post/edit job with suggested skills, applications per job, review with the state machine (slots, confirm, accept, offer, not selected, feedback), anonymous top-N candidates, save/skip/report, candidate detail, invite + compare (Premium) |
| 6. Alerts, insights, premium (F7) | **Done** | In-app notifications + unread badge + "Email sent (demo)", charts on both Homes (basic + Premium), server-side tracking events, plan toggle in Settings, demo data + demo sign-in + reset |
| 7. Rebuild check | **Done** | Built again from only the 3 files: all tested flows passed. The gaps it found are fixed (Appendix with embedded files) |
| 8. Feedback round 1 | **Done** | Landing market block (2 stats + icons), terms "Talent" / "Employer" everywhere, Talent Home without KPI cards ("Your activity" first, "What employers see"), "Job detail" button at the bottom right, onboarding edit mode, "Post from a PDF" |
| 9. Feedback round 2 (version 2) | **Done** | 3 domains only (Software Engineering, AI & Machine Learning, Data) with 50 synthetic jobs and 50 synthetic talent; levels (Intern to Principal), exact years, skill levels, certifications and awards; the CV reader finds the current role, the desired role, the level, the exact years, the certifications and the awards; the full job description in a scroll box (talent and employer, and the employer job overview page); pager (10, 20, 50) and sort on every list; no Settings item (the user block opens Settings), the crown and gold ring for Premium, the plan card with benefits, locks on Premium features; "Your path to this job" (a radar with two layers, a Fit list and a Gap list; the 12-month chart is removed); the Compare page for both roles (2 to 5 jobs for talent, 2 to 5 talent profiles for Premium employers) with a basket; the six formulas rewritten |

## When you finish

1. Start the server: `powershell -ExecutionPolicy Bypass -File app/serve.ps1`.
2. Check that `/`, `/js/main.js`, `/icons.svg` return 200, that a missing file and `/serve.ps1` return 404, and that `/data/australian_jobs_dataset.csv` returns 404 (the app has no data route and needs no CSV).
3. Open `http://localhost:5173/`. Open the browser console: there must be no errors and no CSP errors.
4. Test these flows (a headless browser test page is fine; delete it after):
   1. `#/` shows the landing page; `#how` scrolls to "How it works".
   2. `#/home` when signed out → `#/login?next=%2Fhome`.
   3. Sign up as a candidate → `#/login?registered=1` with the neutral message. A second sign-up with the same email gives the same answer. Bad input shows field errors.
   4. Wrong password → "Incorrect email or password." Correct sign-in → `#/home`, the shell shows 6 nav items (Home active), the onboarding dialog opens.
   5. Close the dialog → `onboarding` = "dismissed", "1 of 3 complete", the source chip shows the job count ("{openCount} open jobs · updated {date}").
   6. `#/candidates` as a candidate → "You don't have access to this page".
   7. Collapse the pane → it stays collapsed after a route change and a reload.
   8. Complete a profile → up to 5 job cards with reasons and an ANZSCO chip.
   9. Sign out → `#/login`, no session. Sign in with `?next=%2Fjobs` → `#/jobs`.
   10. Make the session expire → `#/login?expired=1&next=…` with the message.
   11. Sign up and sign in as a recruiter → 5 nav items, the recruiter Home, `GET /jobs/recommended` → 403.
   12. `#/nope` → page not found. `#/login` when signed in → `#/home`.
   13. Mobile width: menu button opens the pane; nothing scrolls sideways.
   14. Home (candidate) shows the search bar. Search "data engineer" → `#/jobs?q=data+engineer` with "{N} open jobs for “data engineer”." Search "zzzz" → the empty state. Location only (for example Perth) → "{N} open jobs in Perth."
   15. A job card shows the summary, "SKILL GAPS" chips, posted and close dates, a bookmark button and a "Job detail" button at the bottom right. The page has **no** `a[href^="http"]` links.
   16. Bookmark a job on Home → the button is pressed and the announcer says "… saved to bookmarks." Job detail of that job shows "Saved"; click it → "Save".
   17. Job detail shows "Job facts", "About the role" (the full description in the scroll box), "Your skills for this job" (coverage, skill-by-skill list), up to 3 similar jobs, and the Apply action (open → link to apply; the closed demo job `job-demo-data-engineer-contract-closed` → disabled with "This job is closed. You can't apply now."). `#/jobs/does-not-exist` → "We can't find this job".
   18. Bookmarks lists saved jobs (newest first); removing one removes the card; the last one shows the empty state.
   19. The onboarding CV step shows the drop zone centred (icon, text, hint on separate lines) and the employer privacy note.
   20. The skip link moves focus to the main content and does not change the route.
   21. Sign up as a candidate without an alias → the user gets a "Colour Animal" alias. "Suggest one" fills the field. A taken alias (any case) → "This alias is taken. Try “…”." + "Use “…”" fills it. An alias with the real name, a country or nationality, or digits → the matching message. The alias field is hidden for recruiters.
   22. The shell shows "Alias: {alias}" and Home says "Employers see you as {alias}".
   23. Settings (candidate) has 7 sections (mock mode). Save a new name → the shell name and initials change. Save the same alias → error; a taken alias → error + "Use …"; a good alias → badge, shell and success message change. "Edit answers" opens onboarding.
   24. Password: wrong current → "Your current password is not correct."; mismatch → "Passwords don't match."; success → message, form reset; the old password no longer works.
   25. Settings (recruiter) has 5 sections (no alias, no career profile; mock mode); an empty company shows "Enter your company.".
   26. Onboarding CV step: the hint says 10 MB; an 11 MB file and a .txt file show their errors. Upload "minh-cv.pdf" (no keyword: the default sample, the data analyst CV "Data analyst (BI Specialist), Vietnam") → "Reading your CV" (no Back) → Education starts with "What we found in your CV" (current role BI Specialist, desired role Data Engineer, level Mid, 4.5 years, one certification, one award), with "AI-detected" markers, the check note and the mock "Demo mode" banner that names the sample. The Experience step has the domain Data, the level Mid and the exact years 4.5. Changing a field removes its marker.
   27. Translation (data analyst sample): one cross-border Data Analyst card (ANZSCO 224114; "BI Specialist" and "MIS Executive" make one card), Microsoft Excel (from "Spreadsheets"), Data visualisation (from "Dashboards"), Data modelling (from "ER diagrams"), the ETL skill (from "Informatica"), and an AQF card (the overseas bachelor is level 7, cross-border). The skill cards have a level select that starts at the level of the CV ("From your CV"). Continue with nothing accepted → "Accept at least one skill, so employers can find you." Accept, Remove + Undo, Edit (→ "Edited by you"), Accept all work and update the count and the preview.
   28. Save → `GET /me/shared-profile` has the alias, roles with ANZSCO, the level, the exact years, the skill levels, the certifications, the awards and the accepted skills, and **no** name, email or country. Home recommends jobs (data jobs first); Settings shows "Shared skills {N} accepted" and the "What employers see" box.
   29. Upload "business-cv.pdf" (the business analyst sample) → "What we found in your CV" says "Not found. You can add it in the next steps." for the years, the certifications and the awards; Years is empty with a "Missing" marker and must be chosen. Upload "ml-research-cv.pdf" (the machine learning sample) → the desired role is empty with the hint "We could not find your desired role in your CV. You can add it." (plan F11).
   30. Upload "corrupt-file.pdf" → the failure message with "Try a different file" and "Enter details myself"; the second goes to Education (Path B) and keeps the data.
   31. Demo sign-in (talent, Teal Heron): Home has **no** stat cards; the first panel is "Your activity" with "Active applications" (1, "1 needs your action") and "What employers see" (alias, "Level: Mid · 4.5 years", green skill chips with levels, the certification and the award); "Skill insights" shows the Premium prompt; the Notifications nav item has an unread badge; "Get set up" is hidden.
   32. "Not for me" on a card → dashed placeholder + "Undo"; the job leaves the recommendations; Undo brings it back. "Report" → the dialog; no reason → "Choose a reason."; send → "Thank you. Your report is sent."
   33. Apply for the demo job `job-demo-backend-senior` with a note that has an email → `#/applications/{id}?new=1`, ribbon "Applied", the note shows "[email removed]". Change the note → saved. Apply again → the Job detail shows "Applied · Track status".
   34. Applications: Active has 2 rows (Interview with "Action needed", Applied); Past is empty.
   35. Tracking of the interview: the stepper current step is Interview; choose a slot + tick the consent → "Waiting for the employer to confirm".
   36. Notifications: "Mark all as read" → no unread rows, the badge is hidden.
   37. Demo sign-in (employer, Alex Morgan, Bluebushworks): Home shows 3 stat cards, My jobs, Top talent and "Hiring activity". My jobs: Data Engineer, Solar Analytics "Open"; Senior Backend Engineer, Installer Platform "Open"; Machine Learning Engineer, Solar Forecasting "Closes in 4 days"; Contract Data Engineer, Billing Migration "Closed".
   38. Post a job: "Suggest skills" shows suggestions; add one; post → `#/my-jobs/job-…/overview` (the job overview). Edit with a past close date → "The close date must be in the future."
   39. Review Teal Heron (Data Engineer job): the identity box shows the name and email only after the talent consented. Confirm time → Accept → Send offer → "Waiting for an answer to the offer". Plum Heron (applied): Start review → send no times → "Offer 1 to 3 interview times." → one future time → "Waiting for them to choose a time".
   40. Talent (Basic): 5 cards + "You see the top 5 of {N} talent profiles…"; Invite opens "Premium feature". Switch to Premium in Settings → all cards (the 10 sample talent, Teal Heron and every talent who signed up; with the pager when there are more than 10); tick the "Compare" check box on 2 cards → the compare bar → "Open compare" → in mock mode the Compare page says that it needs the real backend (with the real backend: the Compare page, see check 55). Invite → dialog → sent.
   41. No candidate name, email or country appears on any recruiter screen unless the candidate consented (check the DOM of `#app`). The candidate's CV and evidence lines never appear.
   42. Settings: "Your plan" shows the current plan; "Reset demo data" (mock) → signed out, demo data written again.
   43. Landing: the market block has exactly 2 stat cards with icons (680,582 and 69%) and no "black-box" text.
   44. UI terms: no visible "candidate", "recruiter" or "HR" text on the talent or the employer screens (`#app` innerText). The employer nav is Home, Talent, My jobs, Compare, Notifications (no Settings item).
   45. Edit mode (done profile): "Edit profile" opens "Your profile" (17 rows, label "Edit profile"). Edit Skills → "Edit profile · Step 1 of 3" with "Back to profile" → Continue → translation → "Your profile" → "Save changes" closes the dialog.
   46. "Update CV" (done profile): "Edit profile · Step 1 of 4", no "Skip for now"; upload "analyst-cv.pdf" (the business analyst sample: no years, no certification, no award) → reading → translation → "Your profile" with "From your CV" markers and no "Missing" rows (old answers kept) → save.
   47. My jobs has "Post from a PDF" → `#/my-jobs/new?from=file`. A .txt file → "Use a PDF or DOCX file.". "data-analyst.pdf" → "Read file and fill the form" → the form has title "Data Analyst (Contract)", domain Data, type Contract, salary "$700 per day", the job description with its headings, the skills of the taxonomy, "From your file" chips, a "Missing" chip on Location (this sample has no place) and the demo banner; "backend-engineer.pdf" gives the Backend Engineer sample (Software Engineering, Sydney); "ml.pdf" the machine learning sample (no salary) and "devops.pdf" the DevOps sample (Remote). Post → `#/my-jobs/job-…/overview`. "corrupt.pdf" → "We couldn't read this file. Try a different file, or fill in the form yourself."
   48. "Suggest skills" is enabled again after the suggestions show.
   48b. **The mock has only ICT data (`?mock=1`).** The browser storage has `jinder.mock.db.v2` and not `jinder.mock.db.v1`. The job list has the 24 catalogue jobs and the 3 open demo jobs (27 in pages of 10). No screen, no job and no sample has a word of another field of work. The page makes no request for a CSV file (`australian_`) and no `fetch` of a data file. A title that is not an ICT title (a nurse, an accountant, a chef) gives no role card in the translation.
   **Version 2 checks (real backend: start the platform with `python start.py --demo`, open the app without `?mock=1`):**
   49. **Menu and user block.** Talent: Home, Jobs, Bookmarks, Applications, Compare, Notifications. Employer: Home, Talent, My jobs, Compare, Notifications. **No "Settings" item.** The user block at the bottom is one link (name "Account settings, {name}") that opens `#/settings` and is the current page there. It is one keyboard stop.
   50. **Premium marks.** As a Premium user: a crown on the avatar, a gold ring, a "Premium" chip, and the crown stays when the menu is hidden. As a Basic employer: a gold lock chip "Premium" on the Compare item, and lock badges on Invite, Compare and the advanced charts; a click on a lock opens "Premium feature" with "Go to Settings". The crown and the lock change at once when the plan changes in Settings.
   51. **Plan card.** Settings: "Your plan" is the first section. Basic: the 4 (employer) or 2 (talent) benefits with a lock and a gold chip, and "Try Premium (demo)" → "Your plan is now Premium.", the crown shows, and each benefit says "Not used yet" (or "Used" and "N times" after the user did it: for example open the Talent list as Premium, send an invitation, open Compare, open the advanced charts). Without `benefits` (mock) only the radio switch shows.
   52. **Pager.** Jobs, Bookmarks, Applications, My jobs, the applicants of a job and the Talent list have "Rows per page" (10, 20, 50; default 10), "Showing a–b of n", Previous, Next and numbered buttons (`aria-current="page"`). Page 2 shows other items; the total is right; the address has `page`, `pageSize` and `sort` (not the defaults); the Back button goes to the old page; the size is remembered after a reload and for each list and user; after a page change the focus is on the list heading and the live region says "Page 2 of N". A Basic employer sees 5 talent cards, no pager and the gold box "You see the top 5 of {N} talent profiles…". `GET /jobs?pageSize=51` gives 50 items; `sort=bad` is a 400 with `fields.sort`.
   53. **Sort.** Jobs: "Best match" and "Newest posted" (the order changes; ties by id). Bookmarks: "Recently saved" is the default. Applications: "Recently updated", "Best skill match", "Newest application". Talent: "Best fit for this job" and "Recently updated". My jobs and the applicants of a job have no sort select ("Newest first.").
   54. **Job card and job detail.** Every card shows Level, Experience and Work mode chips and a "Compare" check box. The job detail has "Job facts" (Level, Experience, Work mode, Place, Type, Salary, Education), "Certifications" (Required, Preferred) and "Awards" (Preferred), and "About the role" with the **full description** with its headings (no "…" cut) in a box that scrolls and takes the keyboard focus. "How this job fits you" (8 numbers) is still there. **"Your path to this job"** has a radar with two layers ("You have", "Job requires"), the status words Fit, Above and Gap, a "Where you fit" list and a "Gaps to close" list with the months, and **no line chart** (no `.line-chart` in the DOM, no "projection").
   55. **Compare (talent).** Tick 2 cards → the bar "Compare (2/5)" → "Open compare" → `#/compare?ids=…`. 3 and 5 jobs work. The 6th tick is refused with "You can compare up to 5 jobs." (the API gives 400 for 6 ids). The page has the radar with one line for each job (5 different line styles and markers), "Skills side by side" (Meets, Below, Missing), "Details" and "How close the jobs are to each other". "Remove" and "Clear all" work and keep the address and the basket in step. `#/jobs/compare?ids=a,b` redirects to `#/compare?ids=a,b`. There is **no total and no ranking**.
   56. **Compare (employer).** As Premium: the job select "For which job?", the radar, "Skills side by side" (Meets, Below, Related, Missing), "Qualifications and recognition" (names and years only) and "Where the profiles differ" ("1st", "2nd", "Equal"; the muted line says Jinder does not add the areas up). As Basic: the locked page with the sample picture ("This picture is a sample. It does not show real people."), and the page sends no compare, job or talent request. `GET /recruiter/compare?a=&b=` gives 400. A 403 during use shows "Your plan does not include Compare now."
   57. **Onboarding with a CV.** After "Upload and continue" the Education step starts with "What we found in your CV" (current role, desired role, level, years, certifications, awards; a found field has a check and its value, a missing one says "Not found. You can add it in the next steps."). The new fields have the "AI-detected" tag and the hint "From your CV. Check it. Change it if it is wrong." The desired role is **empty and hinted** when the CV does not state it. The Experience step has "Domains" (3 values, no custom), "Your level" and "Exact years of experience" (a number sets and locks the band). The step "Certifications and awards" has the privacy text, the limit of 20 rows, "Choose a kind." for an award without a kind, and a year check (1990 to next year). Each skill card has a level select. "Your profile" has 17 rows. The preview "What employers see" shows the level, years, skill levels, certifications and awards.
   58. **Employer job form and overview.** The new job form has the Domain, Specialisation, Level, years, Work mode and Education fields, the 8-heading description template, a counter ("n of 10,000 characters"), "Preview", skill rows with a level and "Must have", the certification lists and the award check boxes. Post a description of about 3,800 characters → `#/my-jobs/{id}/overview` shows it **in full** in the scroll box, with "Job facts", "Skills", and "Certifications and awards". "Edit job" gives all values back. A closed job has the banner and no "Edit job".
   59. **Talent list (employer).** Each card has the level, years, "Updated N days ago", skill chips with level text, and up to 3 certification and award chips with "+N more" (names and years only, no issuer). No card, no detail and no review page shows a score. The detail has the skill table (Meets, Below, Missing, Related). No employer page has the words "score", "candidate", "recruiter" or "HR", and none shows an e-mail text.
   60. **Mock mode** (`?mock=1`): the old screens work; the lists have the pager and sort that the client builds; Compare shows "… needs the real Jinder backend …"; "Your path to this job" shows "A detailed path is not available for this job."; Settings shows only the radio switch for the plan.
   61. **Contrast and errors.** The five radar series colours have 3:1 or more on white (4.3, 3.9, 11.6, 4.9, 13.6). The gold chip text has 5.2:1. The skill result cells have 4.5:1 or more. (Open design debt: `.chip-yellow` 3.1:1 and `--muted` 3.3:1.) The console has no errors and no CSP errors on every screen. No `style=` attribute and no inline script.
   62. **Phone width (390px):** no sideways scroll of the page on the job card, the job detail, the Compare page (its tables scroll inside their own box and the first column is sticky), the pager and the forms; the buttons, the selects and the check boxes are 44px tall.
5. Run the security scan in `AI_Rule.md` Rule 7 (or the manual checklist).
6. Report what you tested, which scans you ran, and what you did not test.

## Appendix: embedded files (create exactly)

Create each file below exactly as shown. Where the prose above and an embedded file differ, **the embedded file wins**. Together with the files embedded earlier (translation.js, cv-samples.js, seed-jobs.js, seed-demo.js) this makes the mock backend, the reference data, the icons and the public text identical to the reference build.
In version 2, `data/levels.js` is new and five other files changed. All six are embedded: `data/levels.js` (the levels, the skill levels, the work modes, the page sizes and the compare limit), `data/reference.js` (made from the taxonomy: 3 domains, certifications, award kinds, 172 skills; it imports `levels.js`), `icons.svg` (`i-crown` and `i-lock`), `mock/core.js` (`entitlementsOf` adds `crown` and `compareMax`), `views/home.js` (5 recommended jobs with no pager, the compare box, "What employers see" with level, certifications and awards) and `components/onboarding.js` (the step "Certifications and awards", the level, exact years and skill level fields, the "What we found" summary). The mock files were also changed to ICT-only data and embedded again (`seed-jobs.js`, `jobs.js`, `translation.js`, `seed-demo.js`, `cv-samples.js`, `jd-samples.js`, `routes-account.js`, `core.js`, `db.js`), and `landing.js` and `onboarding.js` had small word changes. Each embedded copy (23 files) is the same as the file in `app/` (compared at the end of the version 2 work). The other new or changed files (`compare-store.js`, `pagination.js`, `sort-select.js`, `jd-view.js`, `premium.js`, `compare-tray.js`, `radar.js`, `bridge.js`, `job-card.js`, `profile-card.js`, `shell.js`, `jobs.js`, `applications.js`, `recruiter.js`, `compare.js`, `settings.js`, the four `styles-*.css` files and `api/index.js`) are **not embedded**: write them from the descriptions in this file and in `Docs/DESIGN.md`.

### `app/js/data/levels.js`

```js
// Shared lists for levels, skill levels, work modes, page sizes and the compare basket (Jinder V2 plan, sections 4 and 7).
// Other files import these. Do not write the same lists again.

/** Job and talent levels, from the lowest (rank 0) to the highest (rank 5). */
export const LEVELS = ["Intern", "Junior", "Mid", "Senior", "Lead", "Principal"];

/** Skill levels 1 to 5. `value` is the number that the API uses. */
export const SKILL_LEVELS = [
  { value: 1, label: "Beginner" },
  { value: 2, label: "Working" },
  { value: 3, label: "Proficient" },
  { value: 4, label: "Advanced" },
  { value: 5, label: "Expert" },
];

/** How the work is done. `location` of a job stays a city or "Remote". */
export const WORK_MODES = ["Onsite", "Hybrid", "Remote"];

/** The numbers of rows that a list can show on one page. The first one is the default. */
export const PAGE_SIZES = [10, 20, 50];

/** The most items in one compare basket (one basket for each kind). */
export const COMPARE_MAX = 5;

/** The rank of a level name (0 to 5), or -1 if the name is not a level. */
export const levelRank = (name) => LEVELS.indexOf(name);

/** The label of a skill level number (1 to 5), or "" if there is none. Also takes "3" or 3.0. */
export function skillLevelLabel(value) {
  const n = Math.round(Number(value));
  const found = SKILL_LEVELS.find((s) => s.value === n);
  return found ? found.label : "";
}
```

### `app/js/data/reference.js`

```js
// Reference lists for forms (dropdowns, chips). Frontend-owned, static.
// The lists of names come from ict_taxonomy.json version 2 (jinder_backend_engine/data/reference).
// Use the same spelling as the taxonomy. Do not add a name that is not in the taxonomy.
// Users can also type their own value where the form allows it (not for YEARS and LEVELS).
// Do not add lists for sensitive data (nationality, visa status, age, gender). See AI_Rule.md Rule 5.

// Levels, skill levels and work modes live in levels.js (one place). They are exported here too.
export { LEVELS, SKILL_LEVELS, WORK_MODES } from "./levels.js";

// from ict_taxonomy.json version 2: domains and their specialisations
export const DOMAINS = ["Software Engineering", "AI & Machine Learning", "Data"];
export const SPECIALISATIONS = {
  "Software Engineering": [
    "Backend", "Frontend", "Full-stack", "Mobile", "Platform and DevOps", "Quality engineering",
    "Security engineering", "Software architecture",
  ],
  "AI & Machine Learning": [
    "Machine learning engineering", "Generative AI and LLM", "Computer vision", "Natural language processing",
    "MLOps", "Applied science and research",
  ],
  "Data": [
    "Data engineering", "Data analytics", "Analytics engineering", "Business intelligence", "Data science",
    "Business analysis",
  ],
};
// Old names. The UI word is "Domain" now (plan F6). The profile keys `industry` and `targetIndustries` do not change.
export const INDUSTRIES = DOMAINS;
export const JOB_CATEGORIES = DOMAINS;

// from ict_taxonomy.json version 2: cities. "Remote" is the last item.
export const CITIES = ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Canberra", "Remote"];
export const LOCATIONS = CITIES;
export const WORK_TYPES = ["Full-time", "Part-time", "Contract", "Graduate / Internship"];

// from ict_taxonomy.json version 2: role titles (a title has no level word; the level is separate)
export const ROLES = [
  "Software Engineer", "Software Developer", "Backend Engineer", "Frontend Engineer", "Full-stack Engineer",
  "Web Developer", "Mobile Developer", "Android Developer", "iOS Developer", "Java Developer", ".NET Developer",
  "Python Developer", "Platform Engineer", "DevOps Engineer", "Site Reliability Engineer", "Cloud Engineer",
  "Cloud Architect", "Solutions Architect", "Software Architect", "QA Engineer", "Test Automation Engineer",
  "Software Tester", "Security Engineer", "Application Security Engineer", "Machine Learning Engineer",
  "Computer Vision Engineer", "NLP Engineer", "Deep Learning Engineer", "AI Engineer", "Generative AI Engineer",
  "LLM Engineer", "MLOps Engineer", "ML Platform Engineer", "Applied Scientist", "AI Research Scientist",
  "AI Research Engineer", "Data Engineer", "Analytics Engineer", "Big Data Engineer", "Data Platform Engineer",
  "ETL Developer", "Data Warehouse Engineer", "Database Administrator", "Data Architect", "Data Analyst",
  "Business Intelligence Analyst", "BI Developer", "Reporting Analyst", "Product Analyst", "Data Scientist",
  "Statistician", "Business Analyst", "Business Systems Analyst",
];

// from ict_taxonomy.json version 2: fields of study
export const FIELDS_OF_STUDY = [
  "Computer science", "Software engineering", "Information technology", "Information systems", "Data science",
  "Artificial intelligence", "Statistics", "Mathematics", "Electrical and computer engineering", "Cyber security",
  "Physics", "Economics",
];

// from ict_taxonomy.json version 2: certifications. `tier` is foundation, associate, professional or specialty.
export const CERTIFICATIONS = [
  { name: "AWS Certified Cloud Practitioner", issuer: "Amazon Web Services", domains: ["Software Engineering", "AI & Machine Learning", "Data"], tier: "foundation" },
  { name: "AWS Certified AI Practitioner", issuer: "Amazon Web Services", domains: ["AI & Machine Learning"], tier: "foundation" },
  { name: "AWS Certified Solutions Architect - Associate", issuer: "Amazon Web Services", domains: ["Software Engineering"], tier: "associate" },
  { name: "AWS Certified Developer - Associate", issuer: "Amazon Web Services", domains: ["Software Engineering"], tier: "associate" },
  { name: "AWS Certified Data Engineer - Associate", issuer: "Amazon Web Services", domains: ["Data"], tier: "associate" },
  { name: "AWS Certified Machine Learning Engineer - Associate", issuer: "Amazon Web Services", domains: ["AI & Machine Learning"], tier: "associate" },
  { name: "AWS Certified DevOps Engineer - Professional", issuer: "Amazon Web Services", domains: ["Software Engineering"], tier: "professional" },
  { name: "AWS Certified Security - Specialty", issuer: "Amazon Web Services", domains: ["Software Engineering"], tier: "specialty" },
  { name: "Microsoft Certified: Azure Fundamentals", issuer: "Microsoft", domains: ["Software Engineering", "AI & Machine Learning", "Data"], tier: "foundation" },
  { name: "Microsoft Certified: Azure Developer Associate", issuer: "Microsoft", domains: ["Software Engineering"], tier: "associate" },
  { name: "Microsoft Certified: Azure AI Engineer Associate", issuer: "Microsoft", domains: ["AI & Machine Learning"], tier: "associate" },
  { name: "Microsoft Certified: Azure Data Scientist Associate", issuer: "Microsoft", domains: ["AI & Machine Learning", "Data"], tier: "associate" },
  { name: "Microsoft Certified: Fabric Data Engineer Associate", issuer: "Microsoft", domains: ["Data"], tier: "associate" },
  { name: "Microsoft Certified: Power BI Data Analyst Associate", issuer: "Microsoft", domains: ["Data"], tier: "associate" },
  { name: "Microsoft Certified: DevOps Engineer Expert", issuer: "Microsoft", domains: ["Software Engineering"], tier: "professional" },
  { name: "Google Cloud Associate Cloud Engineer", issuer: "Google Cloud", domains: ["Software Engineering"], tier: "associate" },
  { name: "Google Cloud Professional Data Engineer", issuer: "Google Cloud", domains: ["Data"], tier: "professional" },
  { name: "Google Cloud Professional Machine Learning Engineer", issuer: "Google Cloud", domains: ["AI & Machine Learning"], tier: "professional" },
  { name: "Certified Kubernetes Application Developer", issuer: "Cloud Native Computing Foundation", domains: ["Software Engineering"], tier: "associate" },
  { name: "Certified Kubernetes Administrator", issuer: "Cloud Native Computing Foundation", domains: ["Software Engineering"], tier: "professional" },
  { name: "HashiCorp Certified: Terraform Associate", issuer: "HashiCorp", domains: ["Software Engineering"], tier: "associate" },
  { name: "Databricks Certified Data Engineer Associate", issuer: "Databricks", domains: ["Data"], tier: "associate" },
  { name: "Databricks Certified Data Engineer Professional", issuer: "Databricks", domains: ["Data"], tier: "professional" },
  { name: "Databricks Certified Generative AI Engineer Associate", issuer: "Databricks", domains: ["AI & Machine Learning"], tier: "associate" },
  { name: "SnowPro Core Certification", issuer: "Snowflake", domains: ["Data"], tier: "associate" },
  { name: "dbt Analytics Engineering Certification", issuer: "dbt Labs", domains: ["Data"], tier: "associate" },
  { name: "Confluent Certified Developer for Apache Kafka", issuer: "Confluent", domains: ["Software Engineering", "Data"], tier: "associate" },
  { name: "Tableau Certified Data Analyst", issuer: "Salesforce", domains: ["Data"], tier: "associate" },
  { name: "Machine Learning Specialization", issuer: "DeepLearning.AI and Stanford Online", domains: ["AI & Machine Learning"], tier: "associate" },
  { name: "NVIDIA-Certified Associate: Generative AI LLMs", issuer: "NVIDIA", domains: ["AI & Machine Learning"], tier: "associate" },
  { name: "Professional Scrum Master I", issuer: "Scrum.org", domains: ["Software Engineering", "AI & Machine Learning", "Data"], tier: "associate" },
  { name: "ISTQB Certified Tester Foundation Level", issuer: "ISTQB", domains: ["Software Engineering"], tier: "foundation" },
  { name: "ISTQB Certified Tester Test Automation Engineer", issuer: "ISTQB", domains: ["Software Engineering"], tier: "professional" },
  { name: "CompTIA Security+", issuer: "CompTIA", domains: ["Software Engineering"], tier: "associate" },
  { name: "Certified Ethical Hacker", issuer: "EC-Council", domains: ["Software Engineering"], tier: "associate" },
  { name: "Offensive Security Certified Professional", issuer: "OffSec", domains: ["Software Engineering"], tier: "professional" },
  { name: "Oracle Certified Professional: Java SE 17 Developer", issuer: "Oracle", domains: ["Software Engineering"], tier: "professional" },
  { name: "PCAP: Certified Associate in Python Programming", issuer: "Python Institute", domains: ["Software Engineering", "AI & Machine Learning", "Data"], tier: "associate" },
];

// from ict_taxonomy.json version 2: award kinds. `kind` is the value that the API stores. `label` is the text for people.
export const AWARD_KINDS = [
  { kind: "competitive-programming", label: "Competitive programming" },
  { kind: "hackathon", label: "Hackathon" },
  { kind: "data-science-competition", label: "Data science competition" },
  { kind: "open-source", label: "Open source contribution" },
  { kind: "conference-talk", label: "Conference talk or paper" },
  { kind: "employer-recognition", label: "Employer recognition" },
  { kind: "scholarship", label: "Scholarship" },
  { kind: "academic-excellence", label: "Academic excellence" },
  { kind: "patent", label: "Patent" },
  { kind: "community-leadership", label: "Community leadership" },
  { kind: "security-competition", label: "Security competition or bug bounty" },
  { kind: "innovation-award", label: "Innovation award" },
];

// Skill suggestions for each domain (quick-add chips). From the core skills of the occupations in the taxonomy.
export const SKILL_SUGGESTIONS = {
  "Software Engineering": ["Git", "API design", "Debugging and troubleshooting", "Docker", "Unit and integration testing", "SQL", "CI/CD", "JavaScript", "System design"],
  "AI & Machine Learning": ["Python", "Machine learning", "Deep learning", "PyTorch", "Model evaluation", "Statistics", "scikit-learn", "Feature engineering", "Generative AI"],
  "Data": ["SQL", "Python", "Data visualisation", "Statistics", "Data modelling", "Data analysis", "Microsoft Excel", "Power BI", "ETL and ELT pipelines"],
};

// from ict_taxonomy.json version 2: skill names (the one spelling). Sorted for the skills dropdown.
export const SKILL_NAMES = [
  ".NET", "AI agents", "API design", "AWS", "AWS CloudFormation", "AWS Lambda", "Agile delivery", "Amazon DynamoDB",
  "Amazon Redshift", "Amazon S3", "Amazon SageMaker", "Android development", "Angular", "Ansible", "Apache Airflow",
  "Apache Cassandra", "Apache Flink", "Apache Hadoop", "Apache Kafka", "Apache Spark", "Application security",
  "Authentication and authorisation", "Azure", "Azure Data Factory", "Azure DevOps", "Azure Functions",
  "Azure Machine Learning", "C", "C#", "C++", "CI/CD", "Cloud security", "Code review", "Communication",
  "Computer vision", "Continuous learning", "Cypress", "Data analysis", "Data governance", "Data lakehouse",
  "Data modelling", "Data privacy and compliance", "Data quality", "Data storytelling",
  "Data structures and algorithms", "Data visualisation", "Data warehousing", "Database design and tuning",
  "Databricks", "Debugging and troubleshooting", "Deep learning", "Distributed training and GPU computing", "Django",
  "Docker", "ETL and ELT pipelines", "Elasticsearch", "Estimation and planning", "Experimentation and A/B testing",
  "Facilitation", "FastAPI", "Feature engineering", "Flask", "Flutter", "Generative AI", "Git", "GitHub Actions",
  "GitLab CI/CD", "Go", "Google BigQuery", "Google Cloud Platform", "Grafana", "GraphQL", "HTML and CSS",
  "Hugging Face Transformers", "Incident response", "Infrastructure as code", "JUnit", "Java", "JavaScript",
  "Jenkins", "Jest", "Kotlin", "Kubernetes", "LLM APIs", "LLM fine-tuning", "LangChain", "Laravel", "Linux", "Looker",
  "MATLAB", "MLOps", "MLflow", "Machine learning", "Manual testing", "Mentoring", "Microservices architecture",
  "Microsoft Excel", "Microsoft Fabric", "Microsoft SQL Server", "Model evaluation", "MongoDB", "MySQL",
  "Natural language processing", "NestJS", "Networking fundamentals", "Next.js", "Node.js", "NumPy",
  "Object-oriented design", "Observability", "Oracle Database", "PHP", "Pandas", "Penetration testing",
  "Performance testing", "Playwright", "PostgreSQL", "Power BI", "PowerShell", "Problem solving", "Product thinking",
  "Project management", "Prometheus", "Prompt engineering", "PyTorch", "Python", "R", "React", "React Native",
  "Recommender systems", "Redis", "Reinforcement learning", "Requirements analysis", "Responsible AI",
  "Retrieval-augmented generation", "Ruby", "Ruby on Rails", "Rust", "SQL", "Scala", "Selenium", "Shell scripting",
  "Site reliability engineering", "Snowflake", "Spring Boot", "Stakeholder management", "Statistics", "Swift",
  "System design", "Tableau", "Tailwind CSS", "Team leadership", "Teamwork", "Technical documentation",
  "Technical leadership", "TensorFlow", "Terraform", "Test automation", "Threat modelling", "Time series forecasting",
  "TypeScript", "Unit and integration testing", "Vector databases", "Vertex AI", "Vue.js", "Web accessibility",
  "XGBoost", "dbt", "gRPC", "iOS development", "pytest", "scikit-learn",
];

// All skills for the skills dropdown (the taxonomy skills, sorted)
export const SKILLS = [...new Set([...SKILL_NAMES, ...Object.values(SKILL_SUGGESTIONS).flat()])]
  .sort((a, b) => a.localeCompare(b));

export const QUALIFICATIONS = [
  "High school", "Certificate III or IV", "Diploma", "Advanced diploma", "Associate degree",
  "Bachelor's degree", "Bachelor's degree (Honours)", "Graduate certificate", "Graduate diploma",
  "Master's degree", "MBA", "Doctorate (PhD)",
];

// Countries where qualifications are often earned. Used only for AQF equivalence, never for ranking.
export const COUNTRIES = [
  "Australia", "Bangladesh", "Brazil", "Canada", "Chile", "China", "Colombia", "Egypt", "France", "Germany",
  "Ghana", "Hong Kong", "India", "Indonesia", "Iran", "Ireland", "Italy", "Japan", "Kenya", "Malaysia",
  "Mexico", "Nepal", "Netherlands", "New Zealand", "Nigeria", "Pakistan", "Peru", "Philippines", "Singapore",
  "South Africa", "South Korea", "Spain", "Sri Lanka", "Taiwan", "Thailand", "Turkey", "United Arab Emirates",
  "United Kingdom", "United States", "Vietnam", "Zimbabwe",
];

export const YEARS = ["Less than 1 year", "1–2 years", "3–5 years", "6–10 years", "More than 10 years"];
```

### `app/icons.svg`

```svg
<svg xmlns="http://www.w3.org/2000/svg">
  <!-- Brand mark (Jinder): two swiped cards — talent profile (accent, left) and job (orange, right) —
       with a check badge where they overlap: the match. -->
  <!-- Colors are inline styles. Page CSS does not reach into an external sprite. -->
  <!-- The custom properties inherit from the <use> host, so .on-dark can invert the mark. -->
  <symbol id="logo" viewBox="0 0 40 40">
    <rect width="40" height="40" rx="10" style="fill: var(--lm-bg, #151531)"/>
    <rect x="8.5" y="9" width="13" height="18" rx="3" transform="rotate(-12 15 18)" style="fill: #6868f7"/>
    <rect x="18.5" y="9" width="13" height="18" rx="3" transform="rotate(12 25 18)" style="fill: #ffa340"/>
    <circle cx="20" cy="27" r="6" stroke-width="1.5" style="fill: var(--lm-line, #fff); stroke: var(--lm-bg, #151531)"/>
    <path d="M17.4 27.1l1.8 1.8 3.4-3.6" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="fill: none; stroke: var(--lm-bg, #151531)"/>
  </symbol>

  <!-- UI icons (Lucide-style, 24px grid, stroke = currentColor via .icon) -->
  <symbol id="upload" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m17 8-5-5-5 5"/><path d="M12 3v12"/></symbol>
  <symbol id="target" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></symbol>
  <symbol id="user-check" viewBox="0 0 24 24"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="m16 11 2 2 4-4"/></symbol>
  <symbol id="arrow" viewBox="0 0 24 24"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></symbol>
  <symbol id="check" viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></symbol>
  <symbol id="alert" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></symbol>
  <symbol id="globe" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></symbol>
  <symbol id="briefcase" viewBox="0 0 24 24"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></symbol>
  <symbol id="eye" viewBox="0 0 24 24"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></symbol>
  <symbol id="eye-off" viewBox="0 0 24 24"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.4 10.4 0 0 1 12 5c7 0 10 7 10 7a13.2 13.2 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.5 13.5 0 0 0 2 12s3 7 10 7a9.7 9.7 0 0 0 5.39-1.61"/><path d="M2 2l20 20"/></symbol>
  <symbol id="log-out" viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/></symbol>
  <symbol id="file" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/></symbol>
  <symbol id="eye-view" viewBox="0 0 24 24"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></symbol>
  <symbol id="users" viewBox="0 0 24 24"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></symbol>
  <symbol id="clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></symbol>
  <symbol id="shield" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/><path d="m9 12 2 2 4-4"/></symbol>

  <symbol id="x" viewBox="0 0 24 24"><path d="M18 6 6 18M6 6l12 12"/></symbol>
  <symbol id="map-pin" viewBox="0 0 24 24"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></symbol>
  <symbol id="graduation" viewBox="0 0 24 24"><path d="M22 10 12 5 2 10l10 5 10-5Z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/><path d="M22 10v6"/></symbol>
  <symbol id="chevron-left" viewBox="0 0 24 24"><path d="m15 18-6-6 6-6"/></symbol>
  <symbol id="plus" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></symbol>
  <symbol id="chevron-down" viewBox="0 0 24 24"><path d="m6 9 6 6 6-6"/></symbol>

  <symbol id="home" viewBox="0 0 24 24"><path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/><path d="M10 21v-6h4v6"/></symbol>
  <symbol id="search" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></symbol>
  <symbol id="bookmark" viewBox="0 0 24 24"><path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></symbol>
  <symbol id="inbox" viewBox="0 0 24 24"><path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></symbol>
  <symbol id="settings" viewBox="0 0 24 24"><path d="M21 4h-7M10 4H3M21 12h-9M8 12H3M21 20h-5M12 20H3"/><path d="M14 2v4M8 10v4M16 18v4"/></symbol>
  <symbol id="panel-left" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 3v18"/></symbol>
  <symbol id="menu" viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h16"/></symbol>

  <symbol id="flag" viewBox="0 0 24 24"><path d="M4 22V4a1 1 0 0 1 1-1h11l-1.5 4L16 11H5"/></symbol>
  <symbol id="bell" viewBox="0 0 24 24"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></symbol>
  <symbol id="calendar" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></symbol>
  <symbol id="chart" viewBox="0 0 24 24"><path d="M3 3v18h18"/><path d="M7 16v-4M12 16V8M17 16v-7"/></symbol>
  <symbol id="send" viewBox="0 0 24 24"><path d="m22 2-7 20-4-9-9-4z"/><path d="M22 2 11 13"/></symbol>
  <symbol id="star" viewBox="0 0 24 24"><path d="m12 2 3.1 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.8 21l1.2-6.8-5-4.9 6.9-1z"/></symbol>
  <symbol id="columns" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M12 3v18"/></symbol>
  <symbol id="edit" viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></symbol>
  <!-- Premium: crown (three peaks and a base band, readable at 16px) and lock. 24px grid, stroke 2, like the icons above. -->
  <symbol id="i-crown" viewBox="0 0 24 24"><path d="m3 7 5 4 4-7 4 7 5-4-2 11H5z"/><path d="M5 21.5h14"/></symbol>
  <symbol id="i-lock" viewBox="0 0 24 24"><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></symbol>
  <symbol id="eye-off-small" viewBox="0 0 24 24"><path d="M2 2l20 20"/><path d="M6.7 6.7C3.9 8.4 2 12 2 12s3 7 10 7c1.9 0 3.6-.5 5-1.3M10 4.2c.7-.1 1.3-.2 2-.2 7 0 10 7 10 7a17 17 0 0 1-2.3 3.5"/></symbol>
</svg>
```

### `app/js/api/mock/db.js`

```js
// MOCK BACKEND — data store in browser localStorage. The real backend replaces this file.
// v2: the demo data is ICT only (decision D2). The data of v1 had other fields of work and is removed.
const KEY = "jinder.mock.db.v2";

// Remove data from the old multi-page prototype (decision Q8: start with clean data) and the old mock data
["sb_users", "sb_session", "jinder.mock.db.v1"].forEach((k) => localStorage.removeItem(k));

const empty = () => ({
  users: [], sessions: {}, bookmarks: {}, parses: {},
  skips: {}, reports: [], applications: [], notifications: [], events: [],
  postedJobs: [], jobImports: {}, savedCandidates: {}, skippedCandidates: {}, plans: {}, seeded: false,
});

export function loadDb() {
  try { return { ...empty(), ...JSON.parse(localStorage.getItem(KEY) || "{}") }; }
  catch { return empty(); }
}
export function saveDb(db) {
  localStorage.setItem(KEY, JSON.stringify(db));
}
export function resetDb() {
  localStorage.removeItem(KEY);
}

// Not secure. Only so that passwords are not plain text in localStorage. The backend must use bcrypt or Argon2.
export function demoHash(text) {
  let h = 5381;
  for (let i = 0; i < text.length; i++) h = ((h << 5) + h + text.charCodeAt(i)) | 0;
  return "q" + (h >>> 0).toString(16);
}

export const newId = () => crypto.randomUUID();
```

### `app/js/api/mock/core.js`

```js
// MOCK BACKEND — route table and shared helpers for the mock route files. The real backend replaces this file.
import { ApiError } from "../errors.js";
import { newId } from "./db.js";
import { suggestAlias } from "./aliases.js";

export { ApiError, newId };

// ---------- Routing ----------
export const routes = [];
export function route(method, pattern, handler) {
  const keys = [];
  const re = new RegExp("^" + pattern.replace(/:(\w+)/g, (_, k) => { keys.push(k); return "([^/]+)"; }) + "$");
  routes.push({ method, re, keys, handler });
}

// ---------- Helpers ----------
export const list = (v) => (Array.isArray(v) ? v : v ? [v] : []);
export const clamp = (v, def, min, max) => Math.min(Math.max(parseInt(v, 10) || def, min), max);
export const isEmail = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(v || ""));
export const nowIso = () => new Date().toISOString();

export function validation(fields) {
  const bad = Object.fromEntries(Object.entries(fields).filter(([, msg]) => msg));
  if (Object.keys(bad).length) throw new ApiError(400, "VALIDATION_ERROR", "Some fields are not valid.", bad);
}
export const notFound = (msg) => { throw new ApiError(404, "NOT_FOUND", msg); };
export const conflict = (msg) => { throw new ApiError(409, "CONFLICT", msg); };

export function currentUser(ctx) {
  const s = ctx.token && ctx.db.sessions[ctx.token];
  if (!s) return null;
  if (Date.parse(s.expiresAt) < Date.now()) { delete ctx.db.sessions[ctx.token]; return null; }
  const u = ctx.db.users.find((x) => x.id === s.userId) || null;
  // Candidates made before aliases existed get one now
  if (u && u.role === "candidate" && !u.alias) u.alias = suggestAlias(ctx.db);
  return u;
}
export function requireUser(ctx) {
  const u = currentUser(ctx);
  if (!u) throw new ApiError(401, "UNAUTHORIZED", "Your session has ended. Sign in again.");
  return u;
}
export function requireRole(ctx, role) {
  const u = requireUser(ctx);
  if (u.role !== role) throw new ApiError(403, "FORBIDDEN", "You don't have access to this.");
  return u;
}

// Fields that GET /me returns (allowlist). The password hash is never returned.
export const publicUser = (u) => ({
  id: u.id, role: u.role, name: u.name, email: u.email, company: u.company || null, alias: u.alias || null,
  profile: u.profile || null, cv: u.cv || null, onboarding: u.onboarding || null, createdAt: u.createdAt,
});

// ---------- Recruiter-safe candidate view (allowlist; Feature 5 AC3, AC4) ----------
// It never has: name, email, contact details, photo, country, employer names, the CV or the evidence lines.
export const isShared = (s) => s.status === "accepted" || s.status === "edited";
export function sharedProfileOf(user) {
  const p = user.profile || {};
  const shared = list(p.translation).filter(isShared);
  return {
    alias: user.alias,
    roles: shared.filter((s) => s.anzsco).map((s) => ({ title: s.occupation || s.mapped, anzsco: s.anzsco })),
    // A role card gives a role, not a skill (plan: the shared skills list has the skill cards only)
    skills: [...new Set(shared.filter((s) => s.source === "skill").map((s) => s.mapped))],
    qualifications: shared.filter((s) => s.source === "qualification").map((s) => s.mapped),
    fieldsOfStudy: list(p.fieldOfStudy),
    industries: list(p.industry),
    years: p.years || null,
    targetRoles: list(p.targetRole),
    locations: list(p.locations),
    workTypes: list(p.workTypes),
  };
}
// Words that must never reach a recruiter in free text (Feature 5 NFR): emails and phone numbers
export const scrubContact = (text) => String(text || "")
  .replace(/[^\s@]+@[^\s@]+\.[^\s@]+/g, "[email removed]")
  .replace(/\+?\d[\d\s().-]{7,}\d/g, "[phone removed]");

// ---------- Notifications (Feature 7) ----------
// In-app. "email: true" adds a line "Email sent (demo)" — the mock does not send email.
export function notify(db, userId, { type, title, body = "", link = "", email = false }) {
  db.notifications.push({ id: newId(), userId, type, title, body, link, email, read: false, createdAt: nowIso() });
}

// ---------- Entitlements (Feature 7: premium, demo toggle) ----------
export const TOP_N = 5;
export function entitlementsOf(db, user) {
  const plan = db.plans[user.id] === "premium" ? "premium" : "basic";
  const premium = plan === "premium";
  return {
    plan,
    topN: user.role === "recruiter" ? (premium ? null : TOP_N) : null,
    canContact: user.role === "recruiter" && premium,
    canCompare: user.role === "recruiter" && premium,
    advancedCharts: premium,
    // V2 keys. The mock has no `benefits` list: Settings then shows the plain plan section.
    crown: premium,
    compareMax: 5,
  };
}
export function requirePremium(db, user, feature) {
  const e = entitlementsOf(db, user);
  if (!e[feature]) throw new ApiError(403, "PREMIUM_REQUIRED", "This feature is part of Premium. Upgrade in Settings to use it.");
  return e;
}

// ---------- Tracking events (Feature 7 AC4) ----------
export function track(db, { type, targetType, targetId, actorId }) {
  db.events.push({ type, targetType, targetId, actorId, at: nowIso() });
  if (db.events.length > 5000) db.events.splice(0, db.events.length - 5000);
}
```

### `app/js/api/mock/adapter.js`

```js
// MOCK BACKEND — implements the API contract (prompt.md) in the browser, for demos.
// The real backend must enforce the same rules on the server. This file is not secure.
import { CONFIG } from "../../config.js";
import { ApiError } from "../errors.js";
import { loadDb, saveDb } from "./db.js";
import { routes } from "./core.js";
import { seedDemo } from "./seed-demo.js";
// Route files register their endpoints on import
import "./routes-account.js";
import "./routes-jobs.js";
import "./routes-applications.js";
import "./routes-recruiter.js";
import "./routes-platform.js";

export async function mockAdapter(method, path, body, token) {
  if (CONFIG.MOCK_LATENCY_MS) await new Promise((r) => setTimeout(r, CONFIG.MOCK_LATENCY_MS));
  const [p, qs = ""] = path.split("?");
  for (const r of routes) {
    if (r.method !== method) continue;
    const m = p.match(r.re);
    if (!m) continue;
    const db = loadDb();
    if (CONFIG.MOCK_DEMO_DATA) seedDemo(db);
    const params = Object.fromEntries(r.keys.map((k, i) => [k, decodeURIComponent(m[i + 1])]));
    const ctx = { db, params, query: Object.fromEntries(new URLSearchParams(qs)), body: body ? structuredClone(body) : {}, token, skipSave: false };
    const result = await r.handler(ctx);
    if (!ctx.skipSave) saveDb(db);
    // Return a copy, as JSON over HTTP would (dates become ISO strings)
    return result == null ? null : JSON.parse(JSON.stringify(result));
  }
  throw new ApiError(404, "NOT_FOUND", "This endpoint does not exist.");
}
```

### `app/js/api/mock/aliases.js`

```js
// MOCK BACKEND — candidate aliases. The real backend replaces this file.
// Recruiters see a candidate only by alias. An alias must not show a real name or where a person is from.
import { COUNTRIES } from "../../data/reference.js";

// Neutral words only (Feature 1 backlog): no personality adjectives, no colours that describe skin or hair.
const COLOURS = ["Amber", "Azure", "Cobalt", "Coral", "Cyan", "Indigo", "Jade", "Lilac", "Lime", "Mint", "Plum", "Saffron", "Sage", "Slate", "Teal", "Violet"];
const ANIMALS = ["Badger", "Crane", "Dolphin", "Falcon", "Finch", "Fox", "Gecko", "Heron", "Kestrel", "Koala", "Llama", "Lynx", "Otter", "Owl", "Panda", "Puffin", "Robin", "Seal", "Swift", "Wombat"];

// Words that show origin. An alias with one of these words is not accepted.
const ORIGIN_WORDS = [
  ...COUNTRIES,
  "Aboriginal", "African", "American", "Arab", "Asian", "Australian", "Brazilian", "British", "Chinese", "Colombian",
  "Egyptian", "English", "Filipino", "French", "German", "Indian", "Indonesian", "Iranian", "Irish", "Italian",
  "Japanese", "Kenyan", "Korean", "Latino", "Malaysian", "Mexican", "Nepali", "Nigerian", "Pakistani", "Persian",
  "Russian", "Spanish", "Sri Lankan", "Thai", "Turkish", "Vietnamese", "Hanoi", "Saigon", "Beijing", "Shanghai",
  "Delhi", "Mumbai", "Manila", "Jakarta", "Lagos", "Nairobi", "Kathmandu", "Dhaka", "Karachi", "Bangkok",
].map((w) => w.toLowerCase());

export const norm = (a) => String(a || "").trim().replace(/\s+/g, " ");
const key = (a) => norm(a).toLowerCase();

export function isTaken(db, alias, exceptUserId = null) {
  const k = key(alias);
  return db.users.some((u) => u.id !== exceptUserId && u.alias && key(u.alias) === k);
}

// Random "Colour Animal". If all of them are taken, add a number.
export function suggestAlias(db) {
  for (let i = 0; i < 40; i++) {
    const a = `${COLOURS[Math.floor(Math.random() * COLOURS.length)]} ${ANIMALS[Math.floor(Math.random() * ANIMALS.length)]}`;
    if (!isTaken(db, a)) return a;
  }
  let n = 2;
  const base = `${COLOURS[0]} ${ANIMALS[0]}`;
  while (isTaken(db, `${base} ${n}`)) n++;
  return `${base} ${n}`;
}

/**
 * Check the format and the content of an alias. Returns an error message, or "" if the alias is good.
 * @param {string} alias
 * @param {string} realName  the user's name, so that the alias does not contain it
 */
export function aliasProblem(alias, realName = "") {
  const a = norm(alias);
  if (a.length < 3 || a.length > 30) return "Use 3 to 30 characters.";
  if (!/^[A-Za-z][A-Za-z '-]*[A-Za-z]$/.test(a)) return "Use letters, spaces, hyphens and apostrophes only.";
  const words = a.toLowerCase().split(/[\s'-]+/);
  const nameParts = String(realName).toLowerCase().split(/\s+/).filter((p) => p.length >= 3);
  if (nameParts.some((p) => words.includes(p))) return "Do not use your real name. Employers must not know who you are.";
  const lower = ` ${words.join(" ")} `;
  if (ORIGIN_WORDS.some((w) => lower.includes(` ${w} `))) return "Do not use a country, nationality or city. Use a neutral alias.";
  return "";
}
```

### `app/js/api/mock/jobs.js`

```js
// MOCK BACKEND — the Jinder job catalogue and recommendations. The real backend replaces this file.
// Data: the 24 embedded ICT jobs of seed-jobs.js (copied from the synthetic job file of the backend data) and the jobs that employers post.
// There is no CSV file and no network call. All job data is internal Jinder data. The three domains are the only categories.
// Skill names, the words that show a skill and the related skills come from jinder_backend_engine/data/reference/ict_taxonomy.json.
// The match uses only skills, roles, domains, level, locations and work types.
// It never uses nationality, ethnicity, gender, age, visa status or country of study.
import { SEED_JOBS } from "./seed-jobs.js";
import { levelRank } from "../../data/levels.js";

// A job category is one of the 3 domains. The domain of a profile is stored in `industry` and `targetIndustries` (plan F6).
// The map keeps the old shape of this file: category -> the profile domains that fit it.
const CATEGORY_MAP = {
  "Software Engineering": ["Software Engineering"],
  "AI & Machine Learning": ["AI & Machine Learning"],
  "Data": ["Data"],
};

// The skills of the taxonomy: [name, words that show the skill (aliases, separated by "|"), related skills (separated by "|")].
// Made from ict_taxonomy.json (172 skills). Change the taxonomy first, then this table.
const SKILL_TABLE = [
  ["Python", "py|python3|python 3|python programming", "R|Ruby|Shell scripting|Go|MATLAB"],
  ["Java", "java se|java ee|j2ee|jdk|java programming", "Kotlin|C#|Scala|Spring Boot|Go"],
  ["JavaScript", "js|javascript es6|es6|ecmascript|vanilla js|vanilla javascript", "TypeScript|Node.js|React|HTML and CSS|PHP"],
  ["TypeScript", "ts|typed javascript", "JavaScript|Node.js|Angular|React|Next.js"],
  ["C#", "csharp|c sharp|c-sharp", "Java|.NET|Kotlin|C++|Azure Functions"],
  ["C++", "cpp|c plus plus|cplusplus", "C|Rust|C#|Distributed training and GPU computing|Data structures and algorithms"],
  ["C", "c language|ansi c|c programming", "C++|Rust|Go"],
  ["Go", "golang|go lang|go programming", "Rust|Java|Python|C"],
  ["Rust", "rust lang|rustlang", "C++|Go|C|Swift"],
  ["Kotlin", "kotlin multiplatform", "Java|Android development|Swift|Scala|C#"],
  ["Swift", "swiftui|swift ui", "iOS development|Kotlin|Rust"],
  ["PHP", "php 8|php7|php programming", "Laravel|JavaScript|Ruby"],
  ["Ruby", "ruby programming|ruby lang", "Ruby on Rails|Python|PHP"],
  ["Scala", "scala 3|scala lang", "Java|Kotlin|Apache Spark"],
  ["R", "r language|r programming|rstudio|r studio|tidyverse", "Python|Statistics|MATLAB"],
  ["SQL", "structured query language|t-sql|tsql|pl/sql|plsql|sql queries|ansi sql", "PostgreSQL|MySQL|Microsoft SQL Server|Database design and tuning|Oracle Database"],
  ["Shell scripting", "bash|zsh|bash scripting|unix shell", "Linux|PowerShell|Python|Ansible"],
  ["PowerShell", "powershell core|pwsh", "Shell scripting|Azure|Ansible"],
  ["MATLAB", "matlab simulink|simulink|octave", "Python|R|NumPy"],
  ["HTML and CSS", "html|css|html5|css3|html/css|sass|scss|responsive design|responsive web design", "JavaScript|Tailwind CSS|Web accessibility"],
  ["React", "reactjs|react.js|react hooks|redux", "JavaScript|TypeScript|Next.js|React Native|Vue.js"],
  ["Angular", "angularjs|angular 2|rxjs|angular cli", "TypeScript|React|Vue.js"],
  ["Vue.js", "vue|vuejs|vue 3|nuxt|nuxt.js", "React|JavaScript|Angular"],
  ["Next.js", "nextjs|next js", "React|Node.js|TypeScript|Tailwind CSS"],
  ["Node.js", "nodejs|node js|express.js|expressjs", "JavaScript|TypeScript|NestJS|API design|Next.js"],
  ["NestJS", "nest.js|nest js", "Node.js|TypeScript|Spring Boot"],
  ["Spring Boot", "spring framework|spring mvc|spring cloud|spring boot 3", "Java|Kotlin|Microservices architecture|.NET|NestJS"],
  [".NET", ".net core|dotnet|asp.net|asp.net core|entity framework|.net framework|.net 8", "C#|Spring Boot|Azure"],
  ["Django", "django rest framework|drf", "Python|Flask|FastAPI|Ruby on Rails|Laravel"],
  ["Flask", "flask framework|flask api", "Python|Django|FastAPI"],
  ["FastAPI", "fast api|pydantic", "Python|Flask|Django"],
  ["Ruby on Rails", "rails|ruby rails|ror", "Ruby|Django|Laravel"],
  ["Laravel", "laravel framework|laravel php", "PHP|Ruby on Rails|Django"],
  ["React Native", "react-native|reactnative|expo", "React|Flutter|Android development|iOS development"],
  ["Flutter", "dart|flutter dart|dart language", "React Native|Android development|iOS development"],
  ["Android development", "android|android sdk|android studio|jetpack compose|android app development", "Kotlin|Java|Flutter|React Native"],
  ["iOS development", "ios|ios app development|uikit|xcode|apple development", "Swift|Flutter|React Native"],
  ["GraphQL", "graph ql|apollo|apollo graphql", "API design|gRPC|Node.js"],
  ["gRPC", "protocol buffers|protobuf", "API design|GraphQL|Microservices architecture"],
  ["Tailwind CSS", "tailwind|tailwindcss", "HTML and CSS|React|Next.js"],
  ["Pandas", "pandas library|pandas dataframe|dataframes", "NumPy|Python|Data analysis|scikit-learn|Feature engineering"],
  ["NumPy", "numpy arrays|scipy|numerical python", "Pandas|Python|MATLAB"],
  ["Selenium", "selenium webdriver|webdriver|selenium grid", "Playwright|Cypress|Test automation"],
  ["Playwright", "playwright test", "Cypress|Selenium|Test automation"],
  ["Cypress", "cypress.io|cypress e2e", "Playwright|Selenium|Jest|Test automation"],
  ["Jest", "jest testing|vitest|react testing library|mocha|jasmine", "JavaScript|Cypress|Unit and integration testing"],
  ["pytest", "py.test|unittest|python unittest", "Python|Unit and integration testing|JUnit"],
  ["JUnit", "junit 5|testng|mockito", "Java|Unit and integration testing|pytest"],
  ["AWS", "amazon web services|aws cloud|ec2|amazon ec2|amazon rds|cloudwatch|amazon sqs|sqs|sns|amazon sns", "Azure|Google Cloud Platform|AWS Lambda|Amazon S3|AWS CloudFormation"],
  ["Azure", "microsoft azure|azure cloud|azure active directory|azure ad|entra id|azure vm|azure app service|azure blob storage", "AWS|Google Cloud Platform|Azure Functions|Azure DevOps|PowerShell"],
  ["Google Cloud Platform", "gcp|google cloud|google cloud services|cloud run|gcs|google cloud storage", "AWS|Azure|Google BigQuery|Vertex AI"],
  ["AWS Lambda", "lambda|aws serverless|serverless|serverless functions|aws api gateway", "Azure Functions|AWS|Amazon S3|Microservices architecture"],
  ["Amazon S3", "s3|aws s3|s3 bucket|object storage|simple storage service", "AWS|Data lakehouse|Azure|AWS Lambda"],
  ["Azure Functions", "azure function apps|function apps|durable functions", "AWS Lambda|Azure|C#"],
  ["Docker", "docker compose|dockerfile|containers|containerisation|containerization|docker containers|container images", "Kubernetes|Linux|CI/CD|MLflow|MLOps"],
  ["Kubernetes", "k8s|kube|eks|aks|gke|openshift|helm|helm charts|argo cd|argocd|gitops|container orchestration", "Docker|Terraform|Observability|Site reliability engineering|Prometheus"],
  ["Terraform", "terraform cloud|hcl|opentofu|terragrunt", "Infrastructure as code|AWS CloudFormation|Ansible|Kubernetes"],
  ["Ansible", "ansible playbooks|puppet|configuration management", "Terraform|Infrastructure as code|Linux|Shell scripting|PowerShell"],
  ["AWS CloudFormation", "cloudformation|aws cdk|cdk", "Terraform|Infrastructure as code|AWS"],
  ["Infrastructure as code", "iac|pulumi|bicep|azure bicep|arm templates|infrastructure-as-code", "Terraform|AWS CloudFormation|Ansible"],
  ["Jenkins", "jenkinsfile|jenkins pipelines", "CI/CD|GitHub Actions|GitLab CI/CD|Azure DevOps"],
  ["GitHub Actions", "github workflows|gh actions", "CI/CD|Jenkins|GitLab CI/CD|Git|Azure DevOps"],
  ["GitLab CI/CD", "gitlab ci|gitlab pipelines|gitlab-ci", "CI/CD|GitHub Actions|Jenkins"],
  ["Azure DevOps", "azure pipelines|azure repos|vsts|tfs|azure boards", "CI/CD|GitHub Actions|Azure|Jenkins"],
  ["CI/CD", "ci cd|cicd|ci/cd pipelines|continuous integration|continuous delivery|continuous deployment|build pipelines|deployment pipelines", "Jenkins|GitHub Actions|GitLab CI/CD|Azure DevOps|Docker"],
  ["Linux", "ubuntu|red hat|rhel|centos|debian|unix|linux administration|linux server", "Shell scripting|Networking fundamentals|Docker|Ansible|Site reliability engineering"],
  ["Prometheus", "promql|prometheus monitoring|alertmanager", "Grafana|Observability|Kubernetes"],
  ["Grafana", "grafana dashboards|grafana loki", "Prometheus|Observability|Data visualisation"],
  ["Observability", "monitoring|logging|opentelemetry|otel|distributed tracing|datadog|new relic|splunk|application monitoring|apm", "Prometheus|Grafana|Site reliability engineering|Incident response|Kubernetes"],
  ["Site reliability engineering", "sre|site reliability|reliability engineering|slo|error budgets", "Observability|Incident response|Kubernetes|Linux"],
  ["Networking fundamentals", "computer networking|tcp/ip|tcp ip|dns|load balancing|load balancers|vpc|firewalls|subnets|vpn|network security basics", "Linux|Cloud security|Azure|Penetration testing"],
  ["Cloud security", "cloud security posture|aws security|azure security|iam policies|identity and access management|iam|kms|secrets management|hashicorp vault|zero trust", "Authentication and authorisation|Application security|Networking fundamentals|AWS|Threat modelling"],
  ["PostgreSQL", "postgres|psql|pgsql", "MySQL|SQL|Microsoft SQL Server|Database design and tuning|Oracle Database"],
  ["MySQL", "mariadb|mysql database|aurora mysql", "PostgreSQL|SQL|Microsoft SQL Server"],
  ["Microsoft SQL Server", "sql server|mssql|ms sql|ssms|ssis|ssrs|azure sql", "SQL|PostgreSQL|Oracle Database|Azure Data Factory|MySQL"],
  ["Oracle Database", "oracle|oracle db|oracle rdbms", "SQL|Microsoft SQL Server|PostgreSQL"],
  ["MongoDB", "mongo|mongo db|mongoose|nosql|document database|document databases", "Amazon DynamoDB|Redis|Apache Cassandra|Elasticsearch"],
  ["Redis", "redis cache|caching|in-memory cache|memcached", "MongoDB|Amazon DynamoDB|System design|Elasticsearch"],
  ["Amazon DynamoDB", "dynamodb|dynamo db|aws dynamodb", "MongoDB|Apache Cassandra|AWS|Redis"],
  ["Apache Cassandra", "cassandra|scylladb|datastax", "Amazon DynamoDB|MongoDB|Apache Kafka"],
  ["Elasticsearch", "elastic search|opensearch|kibana|elk|elastic stack|solr", "MongoDB|Observability|Redis|Vector databases"],
  ["Snowflake", "snowflake data cloud|snowpark|snowflake sql|snowpipe", "Google BigQuery|Amazon Redshift|Databricks|Data warehousing|Microsoft Fabric"],
  ["Google BigQuery", "bigquery|big query|bq", "Snowflake|Amazon Redshift|Google Cloud Platform|Data warehousing|Looker"],
  ["Amazon Redshift", "redshift|aws redshift|redshift spectrum", "Snowflake|Google BigQuery|AWS|Data warehousing"],
  ["Databricks", "databricks lakehouse|unity catalog|delta live tables|databricks sql|databricks workflows", "Apache Spark|Data lakehouse|Snowflake|Microsoft Fabric"],
  ["Microsoft Fabric", "azure synapse|synapse analytics|azure synapse analytics|onelake|synapse", "Azure Data Factory|Power BI|Databricks|Snowflake"],
  ["Apache Spark", "spark|pyspark|spark sql|spark streaming|spark structured streaming", "Databricks|Apache Hadoop|Scala|Apache Flink|Apache Kafka"],
  ["Apache Kafka", "kafka|confluent|kafka streams|kafka connect|ksql|event streaming|kinesis|amazon kinesis|azure event hubs|event hubs|rabbitmq|message queues|pub/sub", "Apache Flink|Apache Spark|Microservices architecture|Apache Cassandra"],
  ["Apache Flink", "flink|flink sql|stream processing|apache beam", "Apache Kafka|Apache Spark|Java"],
  ["Apache Airflow", "airflow|airflow dags|dags|dagster|prefect|workflow orchestration|data orchestration|mwaa|cloud composer", "ETL and ELT pipelines|dbt|Azure Data Factory|Python"],
  ["dbt", "dbt core|dbt cloud|data build tool|dbt models", "SQL|Data modelling|ETL and ELT pipelines|Apache Airflow|Data quality"],
  ["Azure Data Factory", "adf|data factory|synapse pipelines", "ETL and ELT pipelines|Microsoft Fabric|Azure|Apache Airflow|Microsoft SQL Server"],
  ["Apache Hadoop", "hadoop|hdfs|hive|apache hive|mapreduce|hbase|big data", "Apache Spark|Data lakehouse|Data warehousing"],
  ["Data lakehouse", "lakehouse|data lake|data lakes|delta lake|apache iceberg|iceberg|apache hudi|hudi|parquet|medallion architecture", "Databricks|Amazon S3|Apache Spark|Data warehousing|Apache Hadoop"],
  ["Data modelling", "data modeling|dimensional modelling|dimensional modeling|kimball|star schema|data vault|entity relationship|er diagrams|erd|conceptual data model|logical data model", "Data warehousing|Database design and tuning|dbt|SQL|Data governance"],
  ["Data warehousing", "data warehouse|dwh|edw|enterprise data warehouse|olap|data marts|data mart", "Data modelling|Snowflake|ETL and ELT pipelines|SQL|Google BigQuery"],
  ["ETL and ELT pipelines", "etl|elt|data pipelines|data pipeline|data integration|data ingestion|aws glue|informatica|talend|fivetran|airbyte|batch processing", "Apache Airflow|dbt|Apache Spark|Azure Data Factory|Data warehousing"],
  ["Data quality", "data validation|great expectations|data testing|data profiling|data cleansing|data cleaning|data observability|deequ", "Data governance|dbt|ETL and ELT pipelines"],
  ["Data governance", "data catalog|data catalogue|data lineage|master data management|mdm|data stewardship|collibra|data management", "Data quality|Data privacy and compliance|Data modelling|Responsible AI"],
  ["Database design and tuning", "database design|schema design|query optimisation|query optimization|query tuning|database indexing|indexing|normalisation|normalization|performance tuning|database administration|dba|stored procedures|database migration", "SQL|PostgreSQL|Data modelling|Microsoft SQL Server|System design"],
  ["Power BI", "powerbi|power bi desktop|dax|power query|power bi service|microsoft power bi", "Tableau|Looker|Data visualisation|Microsoft Excel|Microsoft Fabric"],
  ["Tableau", "tableau desktop|tableau server|tableau prep|tableau public", "Power BI|Looker|Data visualisation"],
  ["Looker", "looker studio|lookml|google data studio|data studio", "Power BI|Tableau|Data visualisation|Google BigQuery"],
  ["Microsoft Excel", "excel|spreadsheets|ms excel|vba|excel vba|pivot tables|google sheets|vlookup|xlookup", "Data analysis|Power BI|Data visualisation"],
  ["Data visualisation", "data visualization|dashboards|dashboarding|charts|matplotlib|seaborn|plotly|d3|d3.js|bokeh|streamlit|visual analytics", "Power BI|Tableau|Data storytelling|Data analysis|Grafana"],
  ["Data analysis", "data analytics|exploratory data analysis|eda|data mining|ad hoc analysis|business analytics", "SQL|Statistics|Data visualisation|Microsoft Excel|Pandas"],
  ["Machine learning", "ml|machine-learning|ml models|predictive modelling|predictive modeling|supervised learning|unsupervised learning|classical ml|applied machine learning|statistical learning|predictive analytics|ai/ml", "Deep learning|scikit-learn|Statistics|Feature engineering|Model evaluation"],
  ["Deep learning", "dl|neural networks|neural network|cnns|rnns|lstm|convolutional neural networks|gans|autoencoders", "Machine learning|PyTorch|TensorFlow|Computer vision|Natural language processing"],
  ["scikit-learn", "sklearn|scikit learn|scikitlearn", "Machine learning|Python|Pandas|XGBoost|Feature engineering"],
  ["PyTorch", "torch|pytorch lightning|torchvision", "TensorFlow|Deep learning|Hugging Face Transformers|Computer vision|Reinforcement learning"],
  ["TensorFlow", "tf|keras|tensorflow keras|tf.keras|tensorflow lite|tflite|tensorflow serving", "PyTorch|Deep learning|Machine learning|Computer vision"],
  ["XGBoost", "lightgbm|catboost|gradient boosting|gradient boosted trees|gbm|random forest|random forests|decision trees", "scikit-learn|Machine learning|Feature engineering"],
  ["Hugging Face Transformers", "hugging face|huggingface|transformers|hf transformers|bert|sentence transformers|huggingface transformers", "PyTorch|Natural language processing|Generative AI|LLM fine-tuning"],
  ["Natural language processing", "nlp|text mining|text classification|spacy|nltk|named entity recognition|ner|sentiment analysis|text analytics", "Hugging Face Transformers|Machine learning|Deep learning|Generative AI"],
  ["Computer vision", "image recognition|image classification|object detection|opencv|image processing|yolo|image segmentation|video analytics|ocr", "Deep learning|PyTorch|Machine learning|TensorFlow"],
  ["Generative AI", "genai|gen ai|gen-ai|large language models|large language model|llm|llms|foundation models|generative models|chatgpt|gpt|gpt-4|llm applications|generative artificial intelligence|diffusion models", "Prompt engineering|Retrieval-augmented generation|LLM APIs|LLM fine-tuning|Natural language processing"],
  ["Prompt engineering", "prompt design|prompting|prompt optimisation|prompt optimization|prompt templates|few-shot prompting|chain of thought", "Generative AI|LLM APIs|Retrieval-augmented generation|AI agents"],
  ["Retrieval-augmented generation", "rag|retrieval augmented generation|rag pipelines|rag systems|semantic search|knowledge retrieval|embeddings", "Vector databases|LangChain|Generative AI|LLM APIs|Prompt engineering"],
  ["LangChain", "langgraph|llamaindex|llama index|llm orchestration|semantic kernel|langsmith", "Retrieval-augmented generation|LLM APIs|AI agents|Generative AI"],
  ["LLM APIs", "openai api|openai|azure openai|anthropic api|claude api|gemini api|amazon bedrock|bedrock|llm integration|chat completions|function calling", "Generative AI|Prompt engineering|Retrieval-augmented generation|LangChain|AI agents"],
  ["Vector databases", "vector database|vector db|pinecone|weaviate|chroma|chromadb|milvus|qdrant|faiss|pgvector|vector search|vector stores|embedding stores", "Retrieval-augmented generation|Elasticsearch|PostgreSQL|Generative AI"],
  ["LLM fine-tuning", "fine-tuning|fine tuning|finetuning|lora|qlora|peft|rlhf|instruction tuning|model distillation|parameter-efficient fine-tuning|llm training", "Hugging Face Transformers|Deep learning|Generative AI|Distributed training and GPU computing"],
  ["AI agents", "agentic ai|agentic workflows|llm agents|agent frameworks|tool calling|tool use|multi-agent systems|multi-agent|model context protocol|mcp servers|autonomous agents|agent orchestration|crewai|autogen", "LangChain|Generative AI|LLM APIs|Prompt engineering"],
  ["Responsible AI", "ai ethics|ai governance|ai safety|ethical ai|fairness and bias|model fairness|bias mitigation|guardrails|ai guardrails|explainability|explainable ai|xai|trustworthy ai|model interpretability", "Data privacy and compliance|Model evaluation|Data governance|Generative AI"],
  ["MLflow", "ml flow|experiment tracking|weights and biases|weights & biases|wandb|w&b|neptune|comet ml|model registry", "MLOps|Machine learning|Docker"],
  ["Amazon SageMaker", "sagemaker|aws sagemaker|sagemaker studio|sagemaker pipelines|sagemaker endpoints", "Azure Machine Learning|Vertex AI|MLOps|AWS"],
  ["Azure Machine Learning", "azure ml|azureml|azure ml studio|azure ai studio|azure ai foundry|ai foundry", "Amazon SageMaker|Vertex AI|MLOps|Azure"],
  ["Vertex AI", "google vertex ai|vertex ai pipelines|vertex ai studio", "Amazon SageMaker|Azure Machine Learning|Google Cloud Platform|MLOps"],
  ["MLOps", "ml ops|machine learning operations|model deployment|model serving|ml pipelines|ml pipeline|kubeflow|model monitoring|feature store|feature stores|bentoml|seldon|ml platform|llmops", "MLflow|Docker|CI/CD|Machine learning|Kubernetes"],
  ["Feature engineering", "feature selection|feature extraction|feature design|feature creation|dimensionality reduction|pca|data preprocessing|data preparation", "Machine learning|Pandas|Data analysis|scikit-learn|XGBoost"],
  ["Time series forecasting", "time series|time-series|forecasting|demand forecasting|arima|facebook prophet|sarima|forecast models|anomaly detection", "Statistics|Machine learning|Data analysis"],
  ["Recommender systems", "recommendation systems|recommendation engines|recommender engines|recsys|collaborative filtering|personalisation models|ranking models|learning to rank", "Machine learning|Deep learning|Feature engineering"],
  ["Reinforcement learning", "rl|deep reinforcement learning|q-learning|policy gradients", "Deep learning|Machine learning|PyTorch"],
  ["Statistics", "stats|statistical analysis|statistical modelling|statistical modeling|hypothesis testing|regression analysis|bayesian statistics|bayesian methods|probability|inferential statistics|descriptive statistics|statistical inference", "Data analysis|Machine learning|R|Experimentation and A/B testing|Time series forecasting"],
  ["Experimentation and A/B testing", "a/b testing|ab testing|a/b tests|split testing|experiment design|experimentation|controlled experiments|causal inference|multivariate testing", "Statistics|Data analysis|Product thinking"],
  ["Model evaluation", "model validation|cross-validation|cross validation|model metrics|precision and recall|evaluation metrics|model testing|llm evaluation|llm evals|evals|model performance|hyperparameter tuning|hyperparameter optimisation|model selection", "Machine learning|Statistics|scikit-learn|Responsible AI"],
  ["Distributed training and GPU computing", "cuda|gpu computing|gpu programming|gpu|distributed training|deepspeed|horovod|multi-gpu training|nvidia gpus|triton inference server|model parallelism|model optimisation|onnx|tensorrt", "PyTorch|Deep learning|LLM fine-tuning|C++"],
  ["Agile delivery", "agile|scrum|kanban|sprint planning|agile methodologies|agile methodology|scrum master|jira|scaled agile|sprints|agile development", "Project management|Estimation and planning|Teamwork|Facilitation"],
  ["Git", "github|gitlab|bitbucket|version control|source control|gitflow|git flow|branching strategies|git workflow|svn", "CI/CD|Code review|GitHub Actions"],
  ["Unit and integration testing", "unit testing|integration testing|unit tests|tdd|test-driven development|test driven development|bdd|behaviour-driven development|behavior-driven development|mocking|automated tests|contract testing|code coverage", "Test automation|pytest|JUnit|Jest|Code review"],
  ["Test automation", "automated testing|qa automation|test automation framework|sdet|e2e testing|end-to-end testing|api testing|regression testing|ui automation|test frameworks|postman|rest assured", "Selenium|Playwright|Cypress|Unit and integration testing|Performance testing"],
  ["Manual testing", "manual qa|exploratory testing|test cases|test case design|test planning|uat|user acceptance testing|regression test cases|test scripts|bug reporting|defect management|functional testing|test execution|qa testing|quality assurance", "Test automation|Requirements analysis|Debugging and troubleshooting|Web accessibility"],
  ["Performance testing", "load testing|stress testing|jmeter|apache jmeter|k6|gatling|locust|performance test|soak testing|capacity testing|performance engineering", "Test automation|Observability|System design"],
  ["Code review", "peer review|code reviews|pull request reviews|pr reviews|reviewing code|code quality", "Git|Mentoring|Unit and integration testing|Teamwork"],
  ["System design", "software architecture|solution architecture|solutions architecture|architecture design|scalable systems|high-level design|hld|low-level design|lld|distributed systems|scalability|system architecture|technical design|design documents|architecture patterns", "Microservices architecture|API design|Object-oriented design|Database design and tuning|Redis"],
  ["Microservices architecture", "microservices|microservice|service-oriented architecture|soa|event-driven architecture|event driven architecture|event-driven systems|service mesh|api gateway", "System design|API design|Docker|Kubernetes|Apache Kafka"],
  ["Object-oriented design", "oop|object oriented programming|object-oriented programming|design patterns|solid principles|domain-driven design|ddd|clean architecture|clean code|oo design|uml", "System design|Java|C#|Unit and integration testing|Data structures and algorithms"],
  ["Data structures and algorithms", "dsa|algorithms|data structures|algorithm design|competitive programming|leetcode|algorithmic problem solving|complexity analysis|big o", "Problem solving|C++|Object-oriented design"],
  ["API design", "restful|rest api|rest apis|restful api|restful apis|openapi|swagger|api development|web services|web apis|api design and development|json apis|soap|api versioning|api documentation", "GraphQL|gRPC|Microservices architecture|Authentication and authorisation|Node.js"],
  ["Technical documentation", "technical writing|architecture decision records|adr|runbooks|api docs|confluence|design docs|readme|knowledge base articles", "Communication|Requirements analysis|System design"],
  ["Debugging and troubleshooting", "debugging|troubleshooting|root cause analysis|rca|bug fixing|issue diagnosis|production support|problem diagnosis|fault finding|log analysis", "Problem solving|Incident response|Observability|Unit and integration testing|Manual testing"],
  ["Application security", "appsec|owasp|owasp top 10|secure coding|devsecops|secure software development|sast|dast|dependency scanning|code security|security best practices|xss|web application security|vulnerability scanning", "Authentication and authorisation|Threat modelling|Penetration testing|Cloud security|Data privacy and compliance"],
  ["Authentication and authorisation", "authentication|authorisation|authorization|oauth|oauth2|oauth 2.0|openid connect|oidc|jwt|json web tokens|sso|single sign-on|saml|identity management|identity and access|keycloak|okta|auth0|rbac|mfa|passkeys", "Application security|Cloud security|API design"],
  ["Penetration testing", "pen testing|pentesting|pentest|ethical hacking|red teaming|red team|burp suite|metasploit|vulnerability assessment|security testing|offensive security|bug bounty|ctf|capture the flag|nmap|kali linux", "Application security|Threat modelling|Networking fundamentals|Linux"],
  ["Threat modelling", "threat modeling|stride threat model|attack trees|security architecture|security design reviews|risk assessment|security risk assessment|mitre att&ck|attack surface analysis", "Application security|Cloud security|Penetration testing|System design"],
  ["Incident response", "incident management|on-call|on call|oncall|postmortems|post-mortems|post-incident reviews|security incident response|incident handling|pagerduty|opsgenie|outage response", "Observability|Site reliability engineering|Debugging and troubleshooting"],
  ["Web accessibility", "accessibility|a11y|wcag|wcag 2.1|wcag 2.2|wai-aria|accessible design|inclusive design|screen reader testing", "HTML and CSS|React|Manual testing"],
  ["Data privacy and compliance", "data privacy|privacy act|gdpr|pii|pii handling|data protection|privacy by design|soc 2|soc2|iso 27001|australian privacy principles|regulatory compliance", "Data governance|Responsible AI|Application security|Cloud security"],
  ["Communication", "communication skills|written communication|verbal communication|presentation skills|presenting|public speaking|clear communication|technical communication|written and verbal communication|interpersonal skills", "Stakeholder management|Technical documentation|Data storytelling|Teamwork|Facilitation"],
  ["Stakeholder management", "stakeholder engagement|stakeholder communication|client management|client relationships|customer management|expectation management|relationship management|business partnering", "Communication|Product thinking|Requirements analysis|Project management|Team leadership"],
  ["Mentoring", "coaching|mentorship|mentoring juniors|coaching engineers|onboarding new starters|knowledge sharing|training others|peer coaching|developing others", "Team leadership|Code review|Technical leadership|Continuous learning"],
  ["Team leadership", "leading teams|team lead|people management|people leadership|line management|engineering management|managing engineers|managing teams|team management|direct reports", "Mentoring|Technical leadership|Stakeholder management|Project management"],
  ["Technical leadership", "tech lead|technical lead|technical direction|technical strategy|architecture leadership|leading technical decisions|engineering leadership|technical mentoring|staff engineering|technical ownership|engineering excellence", "Team leadership|System design|Mentoring|Stakeholder management|Estimation and planning"],
  ["Problem solving", "analytical thinking|analytical skills|critical thinking|logical thinking|creative problem solving|solution oriented|problem-solving|analytical problem solving|structured thinking|analytical mindset", "Debugging and troubleshooting|Data structures and algorithms|Continuous learning"],
  ["Teamwork", "collaboration|team player|cross-functional collaboration|cross functional teams|working in teams|pair programming|team collaboration|collaborative working|working with designers|partnering with product", "Communication|Agile delivery|Code review|Continuous learning"],
  ["Project management", "project delivery|program management|programme management|delivery management|project planning|pmp|project coordination|release management|roadmap delivery|prince2", "Agile delivery|Stakeholder management|Estimation and planning|Team leadership"],
  ["Product thinking", "product management|product sense|product mindset|roadmapping|product roadmap|product strategy|user-centred thinking|customer-centric thinking|product discovery|product ownership|product owner|okrs", "Stakeholder management|Requirements analysis|Experimentation and A/B testing"],
  ["Data storytelling", "data story telling|insight communication|communicating insights|presenting data|presenting insights|analytics storytelling|executive reporting|reporting to executives|insight storytelling|data communication", "Data visualisation|Communication|Stakeholder management"],
  ["Facilitation", "workshop facilitation|facilitating workshops|running workshops|retrospectives|meeting facilitation|design thinking|design sprints|stakeholder workshops|scrum ceremonies|event storming|requirements workshops", "Communication|Agile delivery|Stakeholder management|Requirements analysis"],
  ["Continuous learning", "self-learning|self learning|quick learner|fast learner|learning agility|lifelong learning|self-taught|adaptability|growth mindset|learning new technologies|upskilling", "Problem solving|Mentoring|Teamwork"],
  ["Estimation and planning", "estimation|story points|sprint estimation|planning poker|capacity planning|delivery planning|effort estimation|timeline planning|backlog refinement|backlog grooming|roadmap planning|task breakdown", "Agile delivery|Project management|Technical leadership"],
  ["Requirements analysis", "business analysis|requirements gathering|requirements elicitation|user stories|acceptance criteria|functional requirements|non-functional requirements|use cases|bpmn|process mapping|process modelling|process modeling|business requirements|brd|functional specifications|gap analysis", "Stakeholder management|Technical documentation|Product thinking|Facilitation|Manual testing"],
];

// ---------- Helpers ----------
const norm = (s) => String(s || "").toLowerCase().trim();
const list = (v) => (Array.isArray(v) ? v : v ? [v] : []);
const escRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

// One letter names count only inside a list ("Python, R, SQL"). Four names that are also common words count only with a capital letter.
// A word that is a part of a longer word never counts: "java" is not in "javascript", and "js" is not in "node.js".
const LIST_ONLY = new Set(["c", "r", "go"]);
const CAPITAL_ONLY = new Set(["swift", "rust", "ruby", "spark"]);
const LEFT = "(?:^|[^a-z0-9.])";
const RIGHT = "(?![a-z0-9])";

const NAME_OF = new Map();   // lower case name or alias -> name (for a text that is the whole skill)
const RELATED = new Map();   // lower case name -> Set of lower case names (both ways)
const FINDERS = [];          // [name, (raw, lower) => index of the first hit, or -1]

const relate = (a, b) => { if (!RELATED.has(a)) RELATED.set(a, new Set()); RELATED.get(a).add(b); };
for (const [name, aliasText, relatedText] of SKILL_TABLE) {
  const key = norm(name);
  const terms = [...new Set([key, ...aliasText.split("|").filter(Boolean).map(norm)])];
  for (const t of terms) NAME_OF.set(t, name);
  for (const r of relatedText.split("|").filter(Boolean).map(norm)) { relate(key, r); relate(r, key); }

  // A short alias ("js", "ml", "k8s") is not searched in a text: it is too easy to find by chance. It still counts when it is the whole text.
  const plain = terms.filter((t) => (t.length >= 3 || /[#+.]/.test(t)) && !CAPITAL_ONLY.has(t) && !LIST_ONLY.has(t)).sort((a, b) => b.length - a.length);
  const capital = terms.filter((t) => CAPITAL_ONLY.has(t));
  const listOnly = terms.filter((t) => LIST_ONLY.has(t));
  const tests = [];
  if (plain.length) {
    const re = new RegExp(`${LEFT}(?:${plain.map(escRe).join("|")})${RIGHT}`, "m");
    tests.push((raw, low) => { const m = re.exec(low); return m ? m.index : -1; });
  }
  for (const t of capital) {
    const re = new RegExp(`(?:^|[^A-Za-z0-9.])(?:${t[0].toUpperCase()}${t.slice(1)}|${t.toUpperCase()})(?![A-Za-z0-9])`, "m");
    tests.push((raw) => { const m = re.exec(raw); return m ? m.index : -1; });
  }
  for (const t of listOnly) {
    const re = new RegExp(`(?:^|[,;:/|•(\\-]\\s*|\\band\\s+|&\\s*)${escRe(t)}(?=\\s*(?:[,;/|•)]|\\band\\b|&\\s|$))`, "m");
    tests.push((raw, low) => { const m = re.exec(low); return m ? m.index : -1; });
  }
  FINDERS.push([name, (raw, low) => tests.reduce((best, f) => { const i = f(raw, low); return i >= 0 && (best < 0 || i < best) ? i : best; }, -1)]);
}

/** The skill names that a text shows, in the order of their first place in the text. */
export function skillsIn(text) {
  const raw = String(text || "");
  const low = raw.toLowerCase();
  const found = [];
  for (const [name, find] of FINDERS) { const i = find(raw, low); if (i >= 0) found.push([i, name]); }
  return found.sort((a, b) => a[0] - b[0]).map(([, name]) => name);
}
/** The taxonomy name of a text that is the whole skill (a name or an alias, any case), or "". "golang" gives "Go". */
export const canonicalSkillName = (text) => NAME_OF.get(norm(text).replace(/\s+/g, " ").replace(/[.,;]+$/, "")) || "";

// Words of a role title. A level word is not part of the role.
const STOP = new Set(["and", "the", "for", "with", "remote", "senior", "junior", "intern", "internship", "graduate", "contract", "mid", "lead", "principal", "staff", "head", "office", "anzsco"]);
// Role nouns that are in many roles. A match on only these words is weak.
const GENERIC = new Set(["engineer", "engineering", "developer", "analyst", "specialist", "architect", "scientist", "administrator", "manager", "officer", "consultant", "executive", "programmer", "designer", "researcher", "tester", "expert"]);
const words = (s) => norm(s).split(/[^a-z0-9+#]+/).filter((w) => w.length > 1 && !STOP.has(w));
const LEVEL_WORDS = /\b(intern(ship)?|junior|jr|graduate|senior|sr|lead|principal|staff|mid[- ]?level|contract)\b/g;
// "Senior Data Engineer, Lakehouse" -> "data engineer"
const rolePhrase = (t) => norm(t).replace(/\([^)]*\)/g, " ").split(/\s[-–—|@]\s|,/)[0].replace(LEVEL_WORDS, " ").replace(/\s+/g, " ").trim();

// ---------- The catalogue ----------
const DAY = 864e5;
export function salaryText(s) {
  if (!s || !s.min) return "Market competitive";
  const money = (n) => `$${Number(n).toLocaleString("en-AU")}`;
  const unit = s.unit === "day" ? "per day" : s.unit === "hour" ? "per hour" : "per year";
  return s.max && s.max !== s.min ? `${money(s.min)} – ${money(s.max)} ${unit}` : `${money(s.min)} ${unit}`;
}
// The short text of a job: the first whole sentences of the description that fit in 200 characters. Headings and bullets are left out.
// The description itself is never cut and keeps its line breaks (the "## Heading" and "- bullet" markup).
function summaryOf(text, max = 200) {
  const flat = String(text || "").split("\n").map((l) => l.trim()).filter((l) => l && !l.startsWith("#") && !/^[-*•]\s/.test(l)).join(" ").replace(/\s+/g, " ");
  if (flat.length <= max) return flat;
  let out = "";
  for (const s of flat.match(/[^.!?]+[.!?]+(?:\s|$)/g) || []) { if ((out + s).trim().length > max) break; out += s; }
  if (out.trim()) return out.trim();
  const cut = flat.slice(0, max);
  return cut.slice(0, cut.lastIndexOf(" ")).replace(/[,.;:]$/, "") + "…";
}

// All job data is Jinder's own data. IDs are internal ("job-<key>", as in the real backend). No links to other sites are kept.
// The new V2 fields (level, years, work mode, skill levels, certifications, awards) are added where the seed has them.
function fromSeed(r) {
  const now = Date.now();
  return {
    id: `job-${r.key}`,
    title: r.title,
    company: r.company,
    category: r.domain,
    specialisation: r.specialisation,
    location: r.city,
    area: r.area,
    type: r.type,
    anzsco: r.occupation.code,
    occupation: r.occupation.title,
    salary: salaryText(r.salary),
    salaryUnit: r.salary.unit,
    postedAt: new Date(now - r.postedDaysAgo * DAY),
    closesAt: new Date(now + r.closesInDays * DAY),
    summary: summaryOf(r.description),
    description: r.description,
    skills: r.skills.map((s) => s.name),
    skillRequirements: r.skills.map((s) => ({ name: s.name, level: s.level, must: s.must })),
    level: r.level,
    minYears: r.minYears,
    maxYears: r.maxYears,
    workMode: r.workMode,
    educationMin: r.educationMin,
    certifications: { required: [...r.certifications.required], preferred: [...r.certifications.preferred] },
    awards: { preferred: [...r.awards.preferred] },
  };
}

const jobs = SEED_JOBS.map(fromSeed);

// The catalogue is embedded, so there is nothing to load. The function stays because the routes wait for it.
export const loadJobs = () => Promise.resolve();

// Jobs that employers post on Jinder (db.postedJobs) join the catalogue. Dates are ISO strings in the db.
function fromPosted(p) {
  const description = String(p.description || "").replace(/\r\n?/g, "\n").trim();
  return { ...p, postedAt: new Date(p.postedAt), closesAt: new Date(p.closesAt), summary: summaryOf(description), description, anzsco: p.anzsco || "", occupation: p.occupation || "" };
}
export const catalogue = (db) => [...jobs, ...((db && db.postedJobs) || []).map(fromPosted)];
export const isOpen = (j) => !j.closesAt || j.closesAt.getTime() >= Date.now();
export const findJob = (db, id) => catalogue(db).find((j) => j.id === id) || null;
export function jobSource(db) {
  const all = catalogue(db);
  const latest = all.reduce((m, j) => (j.postedAt && (!m || j.postedAt > m) ? j.postedAt : m), null);
  return { openCount: all.filter(isOpen).length, updatedAt: latest ? latest.toISOString() : null };
}
// Skill names found in a text (for employers: "Suggest skills from the description")
export const suggestSkills = (text) => skillsIn(text).slice(0, 10);

// ---------- Per-skill match (Feature 3) ----------
// Each required skill of a job is "match", "partial" or "gap", with a reason.
// coverage = (matches + 0.5 × partials) / required skills × 100. It summarises the skills of one job.
// It is not a score on the person (PRD: per-skill matching, no single score on a person).
// Related skills: the candidate has a skill that the taxonomy lists as related → "partial".

// The candidate's skills as names: their own, the taxonomy names that they map to, and accepted translations
function mySkillNames(p) {
  const shared = list(p.translation).filter((s) => (s.status === "accepted" || s.status === "edited") && s.source === "skill").map((s) => s.mapped);
  const names = new Map();
  for (const s of [...list(p.skills).map((x) => (x && typeof x === "object" ? x.name : x)), ...shared].filter(Boolean)) {
    names.set(norm(s), canonicalSkillName(s) || s);
    for (const c of skillsIn(s)) names.set(norm(c), c);
  }
  return names; // key: lower case, value: display name
}
export const namesFromProfile = (p) => mySkillNames(p || {});
// For employers: the skills of a shared profile (already taxonomy names)
export const namesFromList = (skills) => mySkillNames({ skills });

export function skillMatch(jobSkills, names) {
  const items = jobSkills.map((s) => {
    const k = norm(s);
    if (names.has(k)) return { name: s, status: "match", reason: "Has this skill." };
    const group = RELATED.get(k);
    const via = group && [...names.keys()].find((n) => group.has(n));
    if (via) return { name: s, status: "partial", via: names.get(via), reason: `Has ${names.get(via)}, which is related.` };
    return { name: s, status: "gap", reason: "No evidence of this skill yet." };
  });
  const m = items.filter((i) => i.status === "match").length;
  const p = items.filter((i) => i.status === "partial").length;
  return { items, coverage: items.length ? Math.round(((m + 0.5 * p) / items.length) * 100) : null, matched: m, partial: p };
}

// How close a list of roles is to a job: 3 = the same role or the same occupation, 2 = the same field and the same kind of role,
// 1 = the same field only, 0.5 = only a role noun like "engineer", 0 = nothing.
function roleCloseness(roles, job) {
  const jobPhrase = rolePhrase(job.title);
  const occupation = norm(job.occupation);
  const jobWords = words(`${job.title} ${job.occupation || ""}`);
  let best = 0;
  for (const role of roles) {
    const phrase = rolePhrase(role);
    if (!phrase) continue;
    if (phrase === jobPhrase || phrase === occupation || jobPhrase.includes(phrase)) return 3;
    const mine = new Set(words(role));
    const hits = jobWords.filter((w) => mine.has(w));
    const field = hits.some((w) => !GENERIC.has(w)), noun = hits.some((w) => GENERIC.has(w));
    best = Math.max(best, field && noun ? 2 : field ? 1 : noun ? 0.5 : 0);
  }
  return best;
}
const TARGET_POINTS = { 0: 0, 0.5: 8, 1: 14, 2: 22, 3: 30 };
const PAST_POINTS = { 0: 0, 0.5: 4, 1: 8, 2: 13, 3: 18 };
const RECOMMEND_MIN = 45;   // a job with a lower rank is not recommended (it is still in the search)

// Fit to the candidate's goals. Used to rank and to choose recommendations, never shown as a number.
// rank = coverage × 0.4 + target role (up to 30) or past role (up to 18) + domain 15 + location 10 + work type 5 + level (up to 8)
function matcher(profile) {
  const p = profile || {};
  const names = mySkillNames(p);
  const targetRoles = list(p.targetRole);
  const pastRoles = list(p.currentRole);
  const domains = new Set([...list(p.targetIndustries), ...list(p.industry)]);
  const locations = new Set(list(p.locations));
  const types = new Set(list(p.workTypes));
  const myLevel = levelRank(p.level);

  return (job) => {
    const reasons = [];
    const notes = [];
    const target = roleCloseness(targetRoles, job);
    const past = roleCloseness(pastRoles, job);
    const sm = skillMatch(job.skills, names);
    const jobDomains = CATEGORY_MAP[job.category] || [job.category];
    const domainHit = jobDomains.find((d) => domains.has(d));
    const remote = job.location === "Remote" || job.workMode === "Remote";
    const locationHit = locations.has(job.location) || remote;
    const typeHit = types.size === 0 || types.has(job.type);
    const jobLevel = levelRank(job.level);
    const gap = myLevel >= 0 && jobLevel >= 0 ? Math.abs(myLevel - jobLevel) : -1;
    const levelPoints = gap === 0 ? 8 : gap === 1 ? 4 : 0;
    const roleScore = Math.max(TARGET_POINTS[target], PAST_POINTS[past]);
    const rank = Math.round((sm.coverage ?? 0) * 0.4 + roleScore + (domainHit ? 15 : 0) + (locationHit ? 10 : 0) + (typeHit ? 5 : 0) + levelPoints);

    if (target >= 2) reasons.push(job.occupation ? `Matches your target role (ANZSCO: ${job.occupation})` : "Matches your target role");
    else if (past >= 2) reasons.push("Close to a role you have had");
    else if (target || past) reasons.push(`Similar type of role (${job.title})`);
    if (sm.matched) reasons.push(`You have ${sm.matched} of the ${job.skills.length} skills${sm.partial ? `, and ${sm.partial} related` : ""}`);
    if (domainHit) reasons.push(`In a domain you chose: ${domainHit}`);
    if (gap >= 0 && gap <= 1) reasons.push(`Level fits: ${job.level}`);
    if (remote && !locations.has(job.location)) reasons.push("Remote role: you can work from anywhere in Australia");
    else if (locationHit) reasons.push(`Location you prefer: ${job.location}`);
    if (!typeHit) notes.push(`This role is ${job.type}`);
    if (gap >= 2) notes.push(`This role is ${job.level} level`);
    if (locations.size && !locationHit) notes.push(`Location: ${job.location}`);
    if (!job.skills.length) notes.push("This job lists no skills yet");

    return {
      coverage: sm.coverage, skills: sm.items,
      matchedSkills: sm.items.filter((i) => i.status === "match").map((i) => i.name),
      partialSkills: sm.items.filter((i) => i.status === "partial").map((i) => i.name),
      gaps: sm.items.filter((i) => i.status === "gap").map((i) => i.name),
      // A job that is 2 or more levels away from the level of the candidate is not recommended (it is still in the search)
      reasons, notes, rank, recommended: rank >= RECOMMEND_MIN && gap < 2 && (reasons.length > 1 || target >= 2),
    };
  };
}

// The card fields (no full description; no owner or internal fields)
const card = (job, match) => {
  const { description, ownerId, targetApplicants, editedAt, ...rest } = job;
  return { ...rest, status: isOpen(job) ? "open" : "closed", match };
};
const byRank = (a, b) => b.match.rank - a.match.rank || (b.postedAt || 0) - (a.postedAt || 0) || String(a.id).localeCompare(String(b.id));

// Feature 3 AC2: closed, skipped and applied jobs are not recommended
export function recommend(db, profile, limit = 5, exclude = new Set()) {
  if (!profile) return [];
  const m = matcher(profile);
  return catalogue(db).filter((j) => isOpen(j) && !exclude.has(j.id))
    .map((j) => card(j, m(j)))
    .filter((j) => j.match.recommended)
    .sort(byRank)
    .slice(0, limit);
}

// Keyword search over title, company, occupation, domain, specialisation, level and skills. Open jobs that are not skipped.
export function searchJobs(db, profile, { q = "", location = "", limit = 50 } = {}, exclude = new Set()) {
  const terms = norm(q).split(/\s+/).filter(Boolean);
  const m = matcher(profile);
  const hits = catalogue(db).filter((j) => {
    if (!isOpen(j) || exclude.has(j.id)) return false;
    if (location && j.location !== location) return false;
    const hay = norm(`${j.title} ${j.company} ${j.occupation} ${j.category} ${j.specialisation || ""} ${j.level || ""} ${j.skills.join(" ")} ${j.area}`);
    return terms.every((t) => hay.includes(t));
  }).map((j) => card(j, m(j))).sort(byRank);
  return { total: hits.length, items: hits.slice(0, limit) };
}

export function jobDetail(db, profile, id) {
  const job = findJob(db, id);
  if (!job) return null;
  const m = matcher(profile);
  // Similar jobs: same ANZSCO occupation, or 3+ shared skills. Open jobs only.
  const similar = catalogue(db).filter((j) => j.id !== id && isOpen(j) &&
    ((job.anzsco && j.anzsco === job.anzsco) || j.skills.filter((s) => job.skills.includes(s)).length >= 3))
    .map((j) => card(j, m(j))).sort(byRank).slice(0, 3);
  return { ...card(job, m(job)), description: job.description, similar };
}
```

### `app/js/api/mock/jd-samples.js`

```js
// MOCK BACKEND — sample results for "post a job from a file". The mock cannot read a PDF or DOCX file,
// so it returns one of these made-up job descriptions. The real backend reads the file. The real backend replaces this file.
// All samples are ICT (3 domains only). A description uses the JD markup: "## Heading" lines, "- bullet" lines and plain paragraphs.
// A job description file rarely has a close date or a target number of applicants, so those stay with the employer.
export const JD_SAMPLES = {
  backend: {
    label: "Backend Engineer",
    fields: {
      title: "Backend Engineer, Payments API",
      category: "Software Engineering",
      location: "Sydney",
      type: "Full-time",
      salary: "$130,000 – $150,000 per year",
      description: `## About the role

We are looking for a Backend Engineer to build and run the payments API of our online platform. You will work in a team of six in our Sydney office, with two days at home each week.

## What you will do

- Build and test REST APIs in Python and Django.
- Design PostgreSQL tables and keep the queries fast.
- Review code from other engineers and fix problems in production.
- Add monitoring and alerts for each new service.

## What you bring

- 3 to 6 years of backend work.
- Python and PostgreSQL at an advanced level.
- API design and unit tests for all your code.

## Nice to have

- Docker, Redis or AWS in production.

## Tech stack

Python, Django, PostgreSQL, Redis, Docker and AWS, with Git and CI/CD for all code.`,
    },
    missing: [],
  },
  data: {
    label: "Data Analyst",
    fields: {
      title: "Data Analyst (Contract)",
      category: "Data",
      type: "Contract",
      salary: "$700 per day",
      description: `## About the role

A 6-month contract for a Data Analyst. You will help the product team to make decisions with data.

## What you will do

- Build dashboards in Power BI and share them with business teams.
- Write SQL queries and clean data with Python.
- Explain the results to people who are not data experts.

## What you bring

- 2 to 5 years as a data analyst or a reporting analyst.
- SQL and Power BI at a proficient level.
- Clear written and spoken communication.

## Nice to have

- Data modelling, dbt or Microsoft Excel with large files.

## Tech stack

SQL, Python, Power BI and Microsoft Excel.`,
    },
    missing: ["location"],
  },
  ml: {
    label: "Machine Learning Engineer",
    fields: {
      title: "Machine Learning Engineer, Demand Forecasting",
      category: "AI & Machine Learning",
      location: "Melbourne",
      type: "Full-time",
      description: `## About the role

Join our forecasting team to build and run machine learning models that predict how many orders we will get each week. The team has four engineers and one data scientist.

## What you will do

- Train and compare models in Python with scikit-learn and XGBoost.
- Build features from order and calendar data.
- Track experiments with MLflow and move the best model to production.
- Check each model with clear tests and share the results.

## What you bring

- 2 to 5 years in machine learning or data science.
- Python, machine learning and time series forecasting at an advanced level.
- A habit of writing short notes so that others can repeat your work.

## Nice to have

- Docker, SQL and Git for team work.

## Tech stack

Python, scikit-learn, XGBoost, MLflow, Docker and SQL.`,
    },
    missing: ["salary"],
  },
  devops: {
    label: "DevOps Engineer",
    fields: {
      title: "DevOps Engineer, Cloud Platform",
      category: "Software Engineering",
      location: "Remote",
      type: "Full-time",
      salary: "$140,000 – $160,000 per year",
      description: `## About the role

We run one cloud platform for 12 product teams, and we want a DevOps Engineer to make it faster and safer. This role is fully Remote and open to people anywhere in Australia.

## What you will do

- Build and improve CI/CD pipelines with GitHub Actions.
- Write Terraform code for AWS and keep it tested.
- Run Kubernetes clusters and fix problems at night in turns with the team.
- Add monitoring with Prometheus and Grafana.

## What you bring

- 4 to 8 years of work with Linux, AWS and containers.
- Terraform, Docker and Kubernetes at a proficient level or better.
- Good habits for incident response and for writing runbooks.

## Nice to have

- Python or Go for tools, and an AWS certification.

## Tech stack

AWS, Terraform, Kubernetes, Docker, GitHub Actions, Prometheus and Grafana.`,
    },
    missing: [],
  },
};

// Choose a sample from the file name. "fail" or "corrupt" in the name → the read fails (to test the error path).
export function jdSampleFor(fileName) {
  const n = String(fileName || "").toLowerCase();
  if (/fail|corrupt/.test(n)) return null;
  if (/machine|(^|[^a-z])ml([^a-z]|$)|(^|[^a-z])ai([^a-z]|$)|scientist/.test(n)) return JD_SAMPLES.ml;
  if (/devops|cloud|platform|infra|sre/.test(n)) return JD_SAMPLES.devops;
  if (/data|analyst|bi([^a-z]|$)/.test(n)) return JD_SAMPLES.data;
  return JD_SAMPLES.backend;
}
```

### `app/js/api/mock/routes-account.js`

```js
// MOCK BACKEND — auth, aliases, the user record, password, CV upload and skill translation.
// The real backend replaces this file. It must enforce the same rules on the server.
import { route, ApiError, newId, validation, isEmail, requireUser, requireRole, publicUser, sharedProfileOf, list, nowIso } from "./core.js";
import { demoHash } from "./db.js";
import { suggestAlias, aliasProblem, isTaken, norm } from "./aliases.js";
import { translate } from "./translation.js";
import { sampleFor, parseResultOf } from "./cv-samples.js";

const ROLES = ["candidate", "recruiter"];
const SESSION_HOURS = 8;
const REMEMBER_DAYS = 30;

// 409 ALIAS_TAKEN with a free alias to suggest (Feature 1 AC13)
function assertAliasFree(db, alias, exceptUserId = null) {
  if (!isTaken(db, alias, exceptUserId)) return;
  const suggestion = suggestAlias(db);
  throw new ApiError(409, "ALIAS_TAKEN", `This alias is taken. Try “${suggestion}”.`, { alias: `This alias is taken. Try “${suggestion}”.` }, { suggestion });
}

// ---------- Auth ----------
route("POST", "/auth/signup", ({ db, body }) => {
  const role = body.role;
  const wantsAlias = role === "candidate" && norm(body.alias);
  validation({
    role: ROLES.includes(role) ? "" : "Choose an account type.",
    name: String(body.name || "").trim() ? "" : "Enter your name.",
    company: role === "recruiter" && !String(body.company || "").trim() ? "Enter your company." : "",
    email: isEmail(body.email) ? "" : "Enter a valid email address.",
    password: String(body.password || "").length >= 8 ? "" : "Use at least 8 characters.",
    alias: wantsAlias ? aliasProblem(body.alias, body.name) : "",
  });
  if (wantsAlias) assertAliasFree(db, body.alias);
  const email = body.email.trim().toLowerCase();
  // Same answer for a new or an existing email (no account enumeration)
  if (!db.users.some((u) => u.email === email)) {
    db.users.push({
      id: newId(), role, name: body.name.trim(), email, company: role === "recruiter" ? body.company.trim() : null,
      // Candidates always have an alias. If they do not choose one, the system gives one (Feature 1 AC6).
      alias: role === "candidate" ? (wantsAlias ? norm(body.alias) : suggestAlias(db)) : null,
      pw: demoHash(body.password), profile: null, cv: null, onboarding: null, createdAt: nowIso(),
    });
  }
  return { ok: true };
});

route("POST", "/auth/login", ({ db, body }) => {
  const user = db.users.find((u) => u.email === String(body.email || "").trim().toLowerCase());
  if (!user || user.seed || user.pw !== demoHash(String(body.password || ""))) {
    throw new ApiError(401, "INVALID_CREDENTIALS", "Incorrect email or password.");
  }
  const token = newId();
  const ms = body.remember ? REMEMBER_DAYS * 864e5 : SESSION_HOURS * 36e5;
  const expiresAt = new Date(Date.now() + ms).toISOString();
  db.sessions[token] = { userId: user.id, expiresAt };
  return { token, expiresAt, user: publicUser(user) };
});

route("POST", "/auth/logout", (ctx) => {
  if (ctx.token) delete ctx.db.sessions[ctx.token];
  return null;
});

// ---------- Aliases (public, used on the sign-up form) ----------
route("GET", "/aliases/suggest", ({ db }) => ({ alias: suggestAlias(db) }));

route("GET", "/aliases/check", ({ db, query }) => {
  const alias = norm(query.alias);
  const problem = aliasProblem(alias, query.name || "");
  if (problem) return { alias, available: false, reason: problem };
  if (isTaken(db, alias)) return { alias, available: false, reason: "This alias is taken.", suggestion: suggestAlias(db) };
  return { alias, available: true };
});

// ---------- Me ----------
route("GET", "/me", (ctx) => publicUser(requireUser(ctx)));

route("PATCH", "/me", (ctx) => {
  const user = requireUser(ctx);
  const { profile, cv, onboarding, name, company, alias } = ctx.body;
  const isCandidate = user.role === "candidate";
  validation({
    onboarding: onboarding === undefined || ["done", "dismissed"].includes(onboarding) ? "" : "Not a valid onboarding state.",
    cv: cv === undefined || cv === null || (typeof cv.name === "string" && Number.isFinite(cv.size)) ? "" : "Not a valid CV record.",
    name: name === undefined || String(name).trim() ? "" : "Enter your name.",
    company: company === undefined || user.role !== "recruiter" || String(company).trim() ? "" : "Enter your company.",
    alias: alias === undefined ? "" : !isCandidate ? "Only talent accounts have an alias." : aliasProblem(alias, name ?? user.name),
  });
  if (alias !== undefined) assertAliasFree(ctx.db, alias, user.id);
  if (name !== undefined) user.name = String(name).trim();
  if (company !== undefined && user.role === "recruiter") user.company = String(company).trim();
  if (alias !== undefined) user.alias = norm(alias);
  if (isCandidate && profile !== undefined) user.profile = profile;
  if (isCandidate && cv !== undefined) user.cv = cv;
  if (isCandidate && onboarding !== undefined) user.onboarding = onboarding;
  return publicUser(user);
});

// Change the password. Other sessions of this user end; this session stays.
route("POST", "/me/password", (ctx) => {
  const user = requireUser(ctx);
  const { currentPassword, newPassword } = ctx.body;
  validation({
    currentPassword: user.pw === demoHash(String(currentPassword || "")) ? "" : "Your current password is not correct.",
    newPassword: String(newPassword || "").length >= 8 ? "" : "Use at least 8 characters.",
  });
  if (currentPassword === newPassword) validation({ newPassword: "Use a password that is different from your current one." });
  user.pw = demoHash(newPassword);
  for (const [t, s] of Object.entries(ctx.db.sessions)) if (s.userId === user.id && t !== ctx.token) delete ctx.db.sessions[t];
  return null;
});

// ---------- CV and translation (candidates) ----------
const CV_MAX_BYTES = 10 * 1024 * 1024; // Feature 2 AC1: proposed limit 10 MB
const PARSE_MS = 1800; // the mock "reads" a CV for this long

// The mock gets { name, size, type } (the http adapter sends the file as multipart/form-data, field "file")
route("POST", "/cv", (ctx) => {
  const user = requireRole(ctx, "candidate");
  const { name, size } = ctx.body;
  const ext = String(name || "").slice(String(name || "").lastIndexOf(".")).toLowerCase();
  validation({
    file: ![".pdf", ".docx"].includes(ext) ? "Use a PDF or DOCX file."
      : !(size > 0) ? "This file is empty. Choose a different file."
      : size > CV_MAX_BYTES ? "The file is larger than 10 MB. Use a smaller file." : "",
  });
  const cv = { name: String(name), size: Number(size), addedAt: nowIso() };
  user.cv = cv;
  const id = newId();
  ctx.db.parses[id] = { userId: user.id, fileName: cv.name, startedAt: Date.now() };
  return { cv, parse: { id, status: "parsing" } };
});

route("GET", "/cv/parse/:id", (ctx) => {
  const user = requireRole(ctx, "candidate");
  const job = ctx.db.parses[ctx.params.id];
  if (!job || job.userId !== user.id) throw new ApiError(404, "NOT_FOUND", "We can't find this CV upload.");
  if (Date.now() - job.startedAt < PARSE_MS) return { id: ctx.params.id, status: "parsing" };
  const sample = sampleFor(job.fileName);
  if (!sample) return { id: ctx.params.id, status: "failed", error: "We couldn't read this CV. Try a different file, or enter your details yourself." };
  // The fields that the "AI" filled are "detected"; the fields it could not find are "missing". `found` tells which V2 fields the CV showed.
  return { id: ctx.params.id, status: "done", result: parseResultOf(sample) };
});

// Run the translation engine on a draft profile. Decisions (accepted / edited / removed), and the level and years that the talent set, are kept.
export function translateKeeping(profile, evidence) {
  const result = translate(profile, evidence);
  const before = new Map(list(profile.translation).map((s) => [s.id, s]));
  const skills = result.skills.map((s) => {
    const old = before.get(s.id);
    if (!old) return s;
    const isSkill = s.source === "skill";
    const level = isSkill && Number.isInteger(old.level) && old.level >= 1 && old.level <= 5 ? old.level : s.level;
    const years = isSkill && typeof old.years === "number" && old.years >= 0 && old.years <= 40 ? old.years : s.years;
    return { ...s, status: old.status, mapped: old.status === "edited" ? old.mapped : s.mapped, level, years };
  });
  return { skills, gaps: result.gaps };
}
route("POST", "/profile/translate", (ctx) => {
  requireRole(ctx, "candidate");
  const { profile = {}, evidence = [] } = ctx.body;
  return translateKeeping(profile, evidence);
});

// The preview of the talent ("What employers see"). It adds the V2 facts that the talent gave (level, exact years, skill levels, certifications, awards),
// so that the preview matches the profile. The employer screens of the mock do not keep these facts (plan F9): applications and talent cards have the old keys only.
route("GET", "/me/shared-profile", (ctx) => {
  const user = requireRole(ctx, "candidate");
  const p = user.profile || {};
  const shared = sharedProfileOf(user);
  const EVIDENCE_LEVEL = { Strong: 4, Moderate: 3, Limited: 2 };
  const cards = list(p.translation).filter((s) => (s.status === "accepted" || s.status === "edited") && s.source === "skill");
  const skillLevels = shared.skills.map((name) => {
    const c = cards.find((x) => x.mapped === name);
    return { name, level: (c && c.level) || EVIDENCE_LEVEL[c && c.evidence] || 3, years: c && typeof c.years === "number" ? c.years : null };
  });
  const years = Number(p.yearsExperience);
  return {
    ...shared, level: p.level || null, yearsExperience: Number.isFinite(years) && p.yearsExperience !== null && p.yearsExperience !== "" ? Math.round(years * 2) / 2 : null,
    specialisation: p.specialisation || "", skillLevels, certifications: list(p.certifications), awards: list(p.awards),
  };
});
```

### `app/js/api/mock/routes-jobs.js`

```js
// MOCK BACKEND — candidate job discovery: recommendations, search, detail, bookmarks, skip, report (Feature 3).
// The real backend replaces this file. Tracking events are written here, on the server side (Feature 7 AC4).
import { route, ApiError, validation, requireRole, requireUser, clamp, track, nowIso, newId } from "./core.js";
import { loadJobs, jobSource, recommend, searchJobs, jobDetail, findJob, isOpen } from "./jobs.js";

const savedIds = (db, u) => new Set(db.bookmarks[u.id] || []);
const skippedIds = (db, u) => new Set(db.skips[u.id] || []);
const appliedMap = (db, u) => new Map(db.applications.filter((a) => a.candidateId === u.id).map((a) => [a.jobId, a.id]));

// Add the candidate's own flags to a job
function flags(db, u) {
  const saved = savedIds(db, u), skipped = skippedIds(db, u), applied = appliedMap(db, u);
  return (job) => ({ ...job, bookmarked: saved.has(job.id), skipped: skipped.has(job.id), applicationId: applied.get(job.id) || null });
}
const appear = (db, u, items) => items.forEach((j) => track(db, { type: "job_appear", targetType: "job", targetId: j.id, actorId: u.id }));

route("GET", "/jobs/recommended", async (ctx) => {
  const u = requireRole(ctx, "candidate");
  await loadJobs();
  const exclude = new Set([...skippedIds(ctx.db, u), ...appliedMap(ctx.db, u).keys()]);
  const items = u.profile ? recommend(ctx.db, u.profile, clamp(ctx.query.limit, 5, 1, 20), exclude) : [];
  appear(ctx.db, u, items);
  return { items: items.map(flags(ctx.db, u)), source: jobSource(ctx.db) };
});

route("GET", "/jobs", async (ctx) => {
  const u = requireRole(ctx, "candidate");
  await loadJobs();
  const q = String(ctx.query.q || "").slice(0, 100);
  const location = String(ctx.query.location || "");
  const { total, items } = searchJobs(ctx.db, u.profile, { q, location, limit: clamp(ctx.query.limit, 50, 1, 100) }, skippedIds(ctx.db, u));
  appear(ctx.db, u, items);
  return { total, items: items.map(flags(ctx.db, u)), source: jobSource(ctx.db) };
});

route("GET", "/jobs/:id", async (ctx) => {
  const u = requireRole(ctx, "candidate");
  await loadJobs();
  const job = jobDetail(ctx.db, u.profile, ctx.params.id);
  if (!job) throw new ApiError(404, "NOT_FOUND", "This job does not exist or was removed.");
  track(ctx.db, { type: "job_watch", targetType: "job", targetId: job.id, actorId: u.id });
  const f = flags(ctx.db, u);
  return { ...f(job), similar: job.similar.map(f) };
});

// ---------- Skip (Feature 3 AC4). Skipped jobs leave the recommendations and the search. ----------
route("PUT", "/jobs/:id/skip", async (ctx) => {
  const u = requireRole(ctx, "candidate");
  await loadJobs();
  if (!findJob(ctx.db, ctx.params.id)) throw new ApiError(404, "NOT_FOUND", "This job does not exist or was removed.");
  const l = ctx.db.skips[u.id] || (ctx.db.skips[u.id] = []);
  if (!l.includes(ctx.params.id)) l.push(ctx.params.id);
  // Skip counts improve recommendations later. They are not shown to users (Feature 7 AC7).
  track(ctx.db, { type: "job_skip", targetType: "job", targetId: ctx.params.id, actorId: u.id });
  return { jobId: ctx.params.id, skipped: true };
});
route("DELETE", "/jobs/:id/skip", (ctx) => {
  const u = requireRole(ctx, "candidate");
  ctx.db.skips[u.id] = (ctx.db.skips[u.id] || []).filter((id) => id !== ctx.params.id);
  return { jobId: ctx.params.id, skipped: false };
});

// ---------- Bookmarks (Feature 3 AC5, AC10) ----------
route("GET", "/bookmarks", async (ctx) => {
  const u = requireRole(ctx, "candidate");
  await loadJobs();
  // Newest bookmark first. Removed jobs are skipped. Closed jobs stay, with status "closed".
  const ids = [...(ctx.db.bookmarks[u.id] || [])].reverse();
  const f = flags(ctx.db, u);
  const items = ids.map((id) => jobDetail(ctx.db, u.profile, id)).filter(Boolean).map(({ description, similar, ...j }) => f(j));
  return { items };
});
// Idempotent: saving a saved job again does nothing
route("PUT", "/bookmarks/:jobId", async (ctx) => {
  const u = requireRole(ctx, "candidate");
  await loadJobs();
  if (!findJob(ctx.db, ctx.params.jobId)) throw new ApiError(404, "NOT_FOUND", "This job does not exist or was removed.");
  const l = ctx.db.bookmarks[u.id] || (ctx.db.bookmarks[u.id] = []);
  if (!l.includes(ctx.params.jobId)) { l.push(ctx.params.jobId); track(ctx.db, { type: "job_save", targetType: "job", targetId: ctx.params.jobId, actorId: u.id }); }
  return { jobId: ctx.params.jobId, bookmarked: true };
});
route("DELETE", "/bookmarks/:jobId", (ctx) => {
  const u = requireRole(ctx, "candidate");
  ctx.db.bookmarks[u.id] = (ctx.db.bookmarks[u.id] || []).filter((id) => id !== ctx.params.jobId);
  return { jobId: ctx.params.jobId, bookmarked: false };
});

// ---------- Reports (Feature 3 AC6, Feature 5 AC6) ----------
const REPORT_REASONS = ["not_relevant", "wrong_location_or_type", "misleading", "other"];
route("POST", "/reports", (ctx) => {
  const u = requireUser(ctx);
  const { targetType, targetId, reason, details = "" } = ctx.body;
  validation({
    targetType: (u.role === "candidate" && targetType === "job") || (u.role === "recruiter" && targetType === "candidate") ? "" : "You can't report this.",
    reason: REPORT_REASONS.includes(reason) ? "" : "Choose a reason.",
    details: String(details).length <= 500 ? "" : "Use 500 characters or fewer.",
  });
  // Repeat reports of the same item by the same user do not make duplicates (Feature 3 NFR)
  const dup = ctx.db.reports.find((r) => r.userId === u.id && r.targetType === targetType && r.targetId === targetId);
  if (dup) { dup.reason = reason; dup.details = String(details); dup.at = nowIso(); }
  else ctx.db.reports.push({ id: newId(), userId: u.id, targetType, targetId, reason, details: String(details), at: nowIso() });
  return { ok: true };
});

```

### `app/js/api/mock/routes-applications.js`

```js
// MOCK BACKEND — applications and the hiring lifecycle (Features 4 and 6). The real backend replaces this file.
// The state machine is enforced here (server side). The system never changes a status on its own (Feature 6 AC12).
import { route, ApiError, newId, validation, requireRole, notify, track, nowIso, sharedProfileOf, scrubContact, list } from "./core.js";
import { loadJobs, findJob, isOpen, skillMatch, namesFromList } from "./jobs.js";

// Flow: applied → review → interview → accepted | rejected → offer → confirmed (candidate rejects offer → rejected).
// Recruiter-initiated (premium): contacted → interview → same flow. The candidate can decline: contacted → declined.
export const TRANSITIONS = {
  applied: ["review", "rejected"],
  contacted: ["interview", "rejected"],
  review: ["interview", "rejected"],
  interview: ["accepted", "rejected"],
  accepted: ["offer", "rejected"],
  offer: [],          // the candidate answers the offer
  confirmed: [], rejected: [], declined: [],
};
export const FINAL = ["confirmed", "rejected", "declined"];
export const STATUS_LABEL = {
  applied: "Applied", contacted: "Contacted", review: "In review", interview: "Interview", accepted: "Accepted",
  offer: "Offer", confirmed: "Confirmed", rejected: "Not selected", declined: "Declined",
};

export function addHistory(app, status, by, note = "") {
  app.status = status;
  app.updatedAt = nowIso();
  app.history.push({ status, at: app.updatedAt, by, note });
}

// The job a recruiter owns (posted on Jinder). Catalogue jobs have no owner in the mock.
export const ownerOf = (db, job) => (job && job.ownerId ? db.users.find((u) => u.id === job.ownerId) : null);

export function jobBrief(db, jobId) {
  const j = findJob(db, jobId);
  return j ? { id: j.id, title: j.title, company: j.company, location: j.location, area: j.area, type: j.type, status: isOpen(j) ? "open" : "closed", skills: j.skills, ownedOnJinder: !!j.ownerId } : { id: jobId, title: "Removed job", company: "", location: "", area: "", type: "", status: "closed", skills: [], ownedOnJinder: false };
}

// The match that the recruiter and the candidate see: per skill of the job, against the shared skills only
export function snapshotMatch(job, snapshot) {
  const sm = skillMatch(job ? job.skills : [], namesFromList(snapshot.skills));
  return { coverage: sm.coverage, skills: sm.items };
}

// ---------- Candidate view of an application ----------
function candidateView(db, a) {
  const theirs = a.feedback?.recruiter || null;
  return {
    id: a.id, jobId: a.jobId, job: jobBrief(db, a.jobId), origin: a.origin, status: a.status, statusLabel: STATUS_LABEL[a.status],
    note: a.note, canEdit: a.status === "applied", final: FINAL.includes(a.status),
    history: a.history, slots: a.slots, chosenSlotId: a.chosenSlotId, slotConfirmed: a.slotConfirmed, identityShared: a.identityShared,
    offer: a.offer, snapshot: a.snapshot, match: a.match,
    feedback: { mine: a.feedback?.candidate || null, theirs: theirs ? { toOther: theirs.toOther, at: theirs.at } : null },
    createdAt: a.createdAt, updatedAt: a.updatedAt,
  };
}
const mine = (ctx) => {
  const u = requireRole(ctx, "candidate");
  const a = ctx.db.applications.find((x) => x.id === ctx.params.id && x.candidateId === u.id);
  if (!a) throw new ApiError(404, "NOT_FOUND", "We can't find this application.");
  return { u, a };
};
const mustBe = (a, statuses, msg) => { if (!statuses.includes(a.status)) throw new ApiError(409, "CONFLICT", msg); };

// ---------- Apply (Feature 4 AC1, AC2, AC12, AC13) ----------
route("POST", "/applications", async (ctx) => {
  const u = requireRole(ctx, "candidate");
  await loadJobs();
  const { jobId, note = "" } = ctx.body;
  const job = findJob(ctx.db, jobId);
  if (!job) throw new ApiError(404, "NOT_FOUND", "This job does not exist or was removed.");
  if (!isOpen(job)) throw new ApiError(409, "CONFLICT", "This job is closed. You can't apply now.");
  if (ctx.db.applications.some((a) => a.candidateId === u.id && a.jobId === jobId)) throw new ApiError(409, "CONFLICT", "You have already applied for this job.");
  validation({ note: String(note).length <= 500 ? "" : "Use 500 characters or fewer." });
  const snapshot = sharedProfileOf(u);
  if (!snapshot.skills.length) throw new ApiError(409, "CONFLICT", "Accept at least one translated skill before you apply. Go to Settings › Review translated skills.");
  // A frozen copy of the translated profile as submitted (Feature 4 NFR). Never the original CV.
  const a = {
    id: newId(), jobId, candidateId: u.id, recruiterId: job.ownerId || null, origin: "applied",
    status: "applied", note: scrubContact(note).trim(), snapshot, match: snapshotMatch(job, snapshot),
    history: [], slots: [], chosenSlotId: null, slotConfirmed: false, identityShared: false, offer: null,
    feedback: {}, createdAt: nowIso(), updatedAt: nowIso(),
  };
  addHistory(a, "applied", "candidate");
  ctx.db.applications.push(a);
  track(ctx.db, { type: "job_apply", targetType: "job", targetId: jobId, actorId: u.id });
  const owner = ownerOf(ctx.db, job);
  if (owner) notify(ctx.db, owner.id, { type: "new_application", title: `New application for ${job.title}`, body: `${u.alias} applied.`, link: `/review/${a.id}` });
  return candidateView(ctx.db, a);
});

route("GET", "/applications", async (ctx) => {
  const u = requireRole(ctx, "candidate");
  await loadJobs();
  const items = ctx.db.applications.filter((a) => a.candidateId === u.id)
    .sort((x, y) => Date.parse(y.updatedAt) - Date.parse(x.updatedAt))
    .map((a) => { const v = candidateView(ctx.db, a); return { id: v.id, job: v.job, status: v.status, statusLabel: v.statusLabel, origin: v.origin, final: v.final, coverage: v.match.coverage, createdAt: v.createdAt, updatedAt: v.updatedAt, needsAction: (a.status === "interview" && !a.chosenSlotId) || a.status === "offer" || a.status === "contacted" || (FINAL.includes(a.status) && !a.feedback?.candidate) }; });
  return { items };
});

route("GET", "/applications/:id", async (ctx) => {
  const { a } = mine(ctx);
  await loadJobs();
  return candidateView(ctx.db, a);
});

// Edit until the recruiter moves it to Review (Feature 4 AC6, AC14)
route("PATCH", "/applications/:id", async (ctx) => {
  const { a } = mine(ctx);
  await loadJobs();
  mustBe(a, ["applied"], "The employer is reviewing your application. You can't change it now.");
  validation({ note: String(ctx.body.note ?? "").length <= 500 ? "" : "Use 500 characters or fewer." });
  a.note = scrubContact(ctx.body.note ?? "").trim();
  a.updatedAt = nowIso();
  return candidateView(ctx.db, a);
});

// Pick an interview slot (Feature 4 AC8, AC15). The candidate can agree to share their identity (decision Q4).
route("POST", "/applications/:id/slot", async (ctx) => {
  const { u, a } = mine(ctx);
  await loadJobs();
  mustBe(a, ["interview"], "This application has no interview to book.");
  if (a.slotConfirmed) throw new ApiError(409, "CONFLICT", "The employer has confirmed your interview time.");
  const slot = a.slots.find((s) => s.id === ctx.body.slotId);
  if (!slot) throw new ApiError(409, "CONFLICT", "This time is no longer available. Choose another time.");
  if (Date.parse(slot.start) < Date.now()) throw new ApiError(409, "CONFLICT", "This time has passed. Choose another time.");
  a.chosenSlotId = slot.id;
  a.identityShared = !!ctx.body.shareIdentity;
  a.updatedAt = nowIso();
  a.history.push({ status: "interview", at: a.updatedAt, by: "candidate", note: "Chose an interview time" + (a.identityShared ? " and shared their name and email" : "") });
  const job = findJob(ctx.db, a.jobId);
  if (a.recruiterId) notify(ctx.db, a.recruiterId, { type: "slot_chosen", title: `${u.alias} chose an interview time`, body: job ? job.title : "", link: `/review/${a.id}` });
  return candidateView(ctx.db, a);
});

// Answer an offer (Feature 4 AC10). A rejected offer ends in "rejected".
route("POST", "/applications/:id/offer-reply", async (ctx) => {
  const { u, a } = mine(ctx);
  await loadJobs();
  mustBe(a, ["offer"], "There is no offer to answer.");
  const accept = ctx.body.accept === true;
  addHistory(a, accept ? "confirmed" : "rejected", "candidate", accept ? "Accepted the offer" : "Declined the offer");
  if (a.recruiterId) notify(ctx.db, a.recruiterId, { type: "offer_reply", title: `${u.alias} ${accept ? "accepted" : "declined"} your offer`, link: `/review/${a.id}` });
  track(ctx.db, { type: "job_respond", targetType: "job", targetId: a.jobId, actorId: u.id });
  return candidateView(ctx.db, a);
});

// Decline a recruiter's contact (premium path)
route("POST", "/applications/:id/decline", async (ctx) => {
  const { u, a } = mine(ctx);
  await loadJobs();
  mustBe(a, ["contacted"], "You can decline only an invitation.");
  addHistory(a, "declined", "candidate", "Declined the invitation");
  if (a.recruiterId) notify(ctx.db, a.recruiterId, { type: "contact_declined", title: `${u.alias} declined your invitation`, link: `/review/${a.id}` });
  return candidateView(ctx.db, a);
});

// Feedback at the final stage (Feature 4 AC11): to the other side and to the Jinder team
route("POST", "/applications/:id/feedback", async (ctx) => {
  const { u, a } = mine(ctx);
  await loadJobs();
  mustBe(a, FINAL, "You can give feedback when the application is finished.");
  const { toOther = "", toTeam = "" } = ctx.body;
  validation({
    toOther: String(toOther).length <= 1000 ? "" : "Use 1000 characters or fewer.",
    toTeam: String(toTeam).length <= 1000 ? "" : "Use 1000 characters or fewer.",
    form: String(toOther).trim() || String(toTeam).trim() ? "" : "Write feedback in at least one box.",
  });
  a.feedback.candidate = { toOther: scrubContact(toOther).trim(), toTeam: String(toTeam).trim(), at: nowIso() };
  if (a.recruiterId && a.feedback.candidate.toOther) notify(ctx.db, a.recruiterId, { type: "feedback", title: `${u.alias} sent you feedback`, link: `/review/${a.id}` });
  return candidateView(ctx.db, a);
});

export { candidateView };
```

### `app/js/api/mock/routes-recruiter.js`

```js
// MOCK BACKEND — recruiter features: post and manage jobs, review applications, anonymous candidates (Features 5, 6).
// The real backend replaces this file. Recruiter responses use the allowlist view only (no name, contact, CV).
import { route, ApiError, newId, validation, requireRole, notify, track, nowIso, sharedProfileOf, scrubContact, entitlementsOf, requirePremium, list, clamp } from "./core.js";
import { loadJobs, findJob, isOpen, suggestSkills, skillMatch, namesFromList } from "./jobs.js";
import { TRANSITIONS, FINAL, STATUS_LABEL, addHistory, jobBrief, snapshotMatch } from "./routes-applications.js";
import { LOCATIONS, WORK_TYPES, JOB_CATEGORIES } from "../../data/reference.js";
import { jdSampleFor } from "./jd-samples.js";

const DAY = 864e5;
// Close badge (Feature 6 AC3): green open, yellow less than 7 days, red closed or overdue
export function badgeOf(job) {
  const left = Math.ceil((Date.parse(job.closesAt) - Date.now()) / DAY);
  if (left < 0) return { badge: "closed", label: "Closed", daysLeft: left };
  if (left < 7) return { badge: "closing", label: left <= 1 ? "Closes in 1 day" : `Closes in ${left} days`, daysLeft: left };
  return { badge: "open", label: "Open", daysLeft: left };
}

const ownJob = (ctx, u) => {
  const j = ctx.db.postedJobs.find((x) => x.id === ctx.params.id && x.ownerId === u.id);
  if (!j) throw new ApiError(404, "NOT_FOUND", "We can't find this job.");
  return j;
};
const appsFor = (db, jobId) => db.applications.filter((a) => a.jobId === jobId);
const awaiting = (a) => ["applied", "review"].includes(a.status) || (a.status === "interview" && a.chosenSlotId && !a.slotConfirmed);

function jobSummary(db, j) {
  const apps = appsFor(db, j.id);
  return {
    id: j.id, title: j.title, category: j.category, location: j.location, type: j.type, salary: j.salary,
    postedAt: j.postedAt, closesAt: j.closesAt, skills: j.skills, targetApplicants: j.targetApplicants,
    applicantCount: apps.filter((a) => a.origin === "applied").length, contactedCount: apps.filter((a) => a.origin === "contacted").length,
    awaitingCount: apps.filter(awaiting).length, ...badgeOf(j),
  };
}

function checkJob(body, partial = false) {
  const has = (k) => !partial || body[k] !== undefined;
  const skills = list(body.skills).map((s) => String(s).trim()).filter(Boolean);
  validation({
    title: !has("title") || String(body.title || "").trim().length >= 3 ? "" : "Enter a job title.",
    category: !has("category") || JOB_CATEGORIES.includes(body.category) ? "" : "Choose a category.",
    location: !has("location") || LOCATIONS.includes(body.location) ? "" : "Choose a location.",
    type: !has("type") || WORK_TYPES.includes(body.type) ? "" : "Choose a work type.",
    description: !has("description") || String(body.description || "").trim().length >= 30 ? "" : "Write a description of at least 30 characters.",
    skills: !has("skills") || (skills.length >= 1 && skills.length <= 12) ? "" : "Add 1 to 12 required skills.",
    targetApplicants: !has("targetApplicants") || (Number.isInteger(Number(body.targetApplicants)) && Number(body.targetApplicants) >= 1 && Number(body.targetApplicants) <= 10000) ? "" : "Enter a number from 1 to 10000.",
    // Feature 6 AC13: a close date in the past is rejected
    closesAt: !has("closesAt") ? "" : !Date.parse(body.closesAt) ? "Choose a close date." : Date.parse(body.closesAt) < Date.now() ? "The close date must be in the future." : "",
  });
  return skills;
}

// ---------- My jobs (Feature 6 AC1, AC2, AC3, AC10) ----------
route("GET", "/recruiter/jobs", (ctx) => {
  const u = requireRole(ctx, "recruiter");
  const items = ctx.db.postedJobs.filter((j) => j.ownerId === u.id).sort((a, b) => Date.parse(b.postedAt) - Date.parse(a.postedAt)).map((j) => jobSummary(ctx.db, j));
  return { items };
});

route("POST", "/recruiter/jobs/suggest-skills", (ctx) => {
  requireRole(ctx, "recruiter");
  return { skills: suggestSkills(`${ctx.body.title || ""} ${ctx.body.description || ""}`) };
});

// ---------- Post a job from a file (PDF or DOCX job description) ----------
const JD_MAX_BYTES = 10 * 1024 * 1024;
const JD_READ_MS = 1500; // the mock "reads" the file for this long
// The mock gets { name, size, type } (the http adapter sends multipart/form-data, field "file")
route("POST", "/recruiter/jobs/import", (ctx) => {
  const u = requireRole(ctx, "recruiter");
  const { name, size } = ctx.body;
  const ext = String(name || "").slice(String(name || "").lastIndexOf(".")).toLowerCase();
  validation({
    file: ![".pdf", ".docx"].includes(ext) ? "Use a PDF or DOCX file."
      : !(size > 0) ? "This file is empty. Choose a different file."
      : size > JD_MAX_BYTES ? "The file is larger than 10 MB. Use a smaller file." : "",
  });
  const id = newId();
  ctx.db.jobImports[id] = { userId: u.id, fileName: String(name), startedAt: Date.now() };
  return { parse: { id, status: "parsing" } };
});
route("GET", "/recruiter/jobs/import/:id", (ctx) => {
  const u = requireRole(ctx, "recruiter");
  const imp = ctx.db.jobImports[ctx.params.id];
  if (!imp || imp.userId !== u.id) throw new ApiError(404, "NOT_FOUND", "We can't find this file upload.");
  if (Date.now() - imp.startedAt < JD_READ_MS) return { id: ctx.params.id, status: "parsing" };
  const sample = jdSampleFor(imp.fileName);
  if (!sample) return { id: ctx.params.id, status: "failed", error: "We couldn't read this file. Try a different file, or fill in the form yourself." };
  const fields = { ...sample.fields, skills: suggestSkills(`${sample.fields.title} ${sample.fields.description}`) };
  // "detected" = the fields that the AI filled; "missing" = fields the file does not show
  return { id: ctx.params.id, status: "done", result: { fields, detected: Object.keys(fields), missing: sample.missing, sampleLabel: sample.label } };
});

route("POST", "/recruiter/jobs", async (ctx) => {
  const u = requireRole(ctx, "recruiter");
  await loadJobs();
  const skills = checkJob(ctx.body);
  const b = ctx.body;
  const job = {
    id: `job-${newId().slice(0, 8)}`, ownerId: u.id, title: b.title.trim(), company: u.company, category: b.category,
    location: b.location, area: b.location, type: b.type, salary: String(b.salary || "").trim() || "Market competitive",
    description: String(b.description).trim(), skills: [...new Set(skills)], targetApplicants: Number(b.targetApplicants),
    postedAt: nowIso(), closesAt: new Date(b.closesAt).toISOString(), anzsco: "", occupation: "",
  };
  ctx.db.postedJobs.push(job);
  return jobSummary(ctx.db, job);
});

route("GET", "/recruiter/jobs/:id", (ctx) => {
  const u = requireRole(ctx, "recruiter");
  const j = ownJob(ctx, u);
  return { ...jobSummary(ctx.db, j), description: j.description };
});

// Edit a job. Everyone who applied gets a notification (Feature 6 AC10, Feature 7 AC3).
route("PATCH", "/recruiter/jobs/:id", async (ctx) => {
  const u = requireRole(ctx, "recruiter");
  await loadJobs();
  const j = ownJob(ctx, u);
  const skills = checkJob(ctx.body, true);
  for (const k of ["title", "category", "location", "type", "salary", "description"]) if (ctx.body[k] !== undefined) j[k] = String(ctx.body[k]).trim();
  if (ctx.body.location !== undefined) j.area = j.location;
  if (ctx.body.skills !== undefined) j.skills = [...new Set(skills)];
  if (ctx.body.targetApplicants !== undefined) j.targetApplicants = Number(ctx.body.targetApplicants);
  if (ctx.body.closesAt !== undefined) j.closesAt = new Date(ctx.body.closesAt).toISOString();
  j.editedAt = nowIso();
  for (const a of appsFor(ctx.db, j.id)) {
    if (FINAL.includes(a.status)) continue;
    notify(ctx.db, a.candidateId, { type: "job_edited", title: `${j.title} was updated`, body: "The employer changed this job. Check the details.", link: `/applications/${a.id}` });
  }
  return { ...jobSummary(ctx.db, j), description: j.description };
});

// ---------- Applications for a job (Feature 6 AC4–AC9) ----------
route("GET", "/recruiter/jobs/:id/applications", async (ctx) => {
  const u = requireRole(ctx, "recruiter");
  await loadJobs();
  const j = ownJob(ctx, u);
  const items = appsFor(ctx.db, j.id).sort((a, b) => Date.parse(b.updatedAt) - Date.parse(a.updatedAt)).map((a) => ({
    id: a.id, alias: a.snapshot.alias, origin: a.origin, status: a.status, statusLabel: STATUS_LABEL[a.status],
    coverage: a.match.coverage, matched: a.match.skills.filter((s) => s.status === "match").length, total: a.match.skills.length,
    awaiting: awaiting(a), updatedAt: a.updatedAt, createdAt: a.createdAt,
  }));
  return { job: jobSummary(ctx.db, j), items };
});

function recruiterView(db, a) {
  const cand = db.users.find((x) => x.id === a.candidateId);
  const theirs = a.feedback?.candidate || null;
  // "accepted" is allowed only after the interview time is confirmed
  const next = TRANSITIONS[a.status].filter((s) => s !== "accepted" || a.slotConfirmed);
  return {
    id: a.id, job: jobBrief(db, a.jobId), origin: a.origin, status: a.status, statusLabel: STATUS_LABEL[a.status],
    note: a.note, history: a.history, slots: a.slots, chosenSlotId: a.chosenSlotId, slotConfirmed: a.slotConfirmed,
    // Anonymity ends only when the candidate agrees, when they choose an interview time (decision Q4)
    identity: a.identityShared && cand ? { name: cand.name, email: cand.email } : null,
    offer: a.offer, snapshot: a.snapshot, match: a.match,
    feedback: { mine: a.feedback?.recruiter || null, theirs: theirs ? { toOther: theirs.toOther, at: theirs.at } : null },
    allowedNext: next, canConfirmSlot: a.status === "interview" && !!a.chosenSlotId && !a.slotConfirmed, final: FINAL.includes(a.status),
    createdAt: a.createdAt, updatedAt: a.updatedAt,
  };
}
const ownApp = (ctx) => {
  const u = requireRole(ctx, "recruiter");
  const a = ctx.db.applications.find((x) => x.id === ctx.params.id && x.recruiterId === u.id);
  if (!a) throw new ApiError(404, "NOT_FOUND", "We can't find this application.");
  return { u, a };
};

route("GET", "/recruiter/applications/:id", async (ctx) => {
  const { a } = ownApp(ctx);
  await loadJobs();
  return recruiterView(ctx.db, a);
});

// Change the status. Only valid transitions (Feature 6 AC6, AC14). Moving to Review locks the candidate's edits (AC7).
route("POST", "/recruiter/applications/:id/status", async (ctx) => {
  const { a } = ownApp(ctx);
  await loadJobs();
  const { to, slots = [], offer = "" } = ctx.body;
  if (!TRANSITIONS[a.status].includes(to)) {
    throw new ApiError(409, "CONFLICT", `You can't move an application from ${STATUS_LABEL[a.status]} to ${STATUS_LABEL[to] || to}.`);
  }
  const job = findJob(ctx.db, a.jobId);
  const title = job ? job.title : "your application";
  if (to === "interview") {
    const times = list(slots).filter((s) => Date.parse(s));
    validation({ slots: times.length >= 1 && times.length <= 3 ? (times.every((s) => Date.parse(s) > Date.now()) ? "" : "Choose times in the future.") : "Offer 1 to 3 interview times." });
    a.slots = times.map((s) => ({ id: newId().slice(0, 8), start: new Date(s).toISOString() }));
    a.chosenSlotId = null;
    a.slotConfirmed = false;
    addHistory(a, "interview", "recruiter", `Offered ${a.slots.length} interview time${a.slots.length > 1 ? "s" : ""}`);
    notify(ctx.db, a.candidateId, { type: "interview_slots", title: `Interview times for ${title}`, body: "Choose a time that works for you.", link: `/applications/${a.id}` });
  } else if (to === "accepted") {
    if (!a.slotConfirmed) throw new ApiError(409, "CONFLICT", "Confirm the interview time first. Then record the result.");
    addHistory(a, "accepted", "recruiter");
    notify(ctx.db, a.candidateId, { type: "result", title: `Good news about ${title}`, body: "The employer accepted you after the interview. An offer can follow.", link: `/applications/${a.id}`, email: true });
  } else if (to === "offer") {
    validation({ offer: String(offer).trim().length >= 10 ? "" : "Write the offer details (at least 10 characters)." });
    a.offer = { text: scrubContact(offer).trim(), sentAt: nowIso() };
    addHistory(a, "offer", "recruiter");
    notify(ctx.db, a.candidateId, { type: "offer", title: `You have an offer for ${title}`, body: "Read it and answer.", link: `/applications/${a.id}`, email: true });
  } else if (to === "rejected") {
    addHistory(a, "rejected", "recruiter");
    notify(ctx.db, a.candidateId, { type: "result", title: `Update on ${title}`, body: "The employer did not select you this time. You can give feedback.", link: `/applications/${a.id}`, email: true });
  } else {
    addHistory(a, to, "recruiter");
    notify(ctx.db, a.candidateId, { type: "status", title: `${title}: ${STATUS_LABEL[to]}`, body: to === "review" ? "The employer is reviewing your application." : "", link: `/applications/${a.id}` });
  }
  track(ctx.db, { type: "job_respond", targetType: "application", targetId: a.id, actorId: a.recruiterId });
  return recruiterView(ctx.db, a);
});

route("POST", "/recruiter/applications/:id/confirm-slot", async (ctx) => {
  const { a } = ownApp(ctx);
  await loadJobs();
  if (!(a.status === "interview" && a.chosenSlotId && !a.slotConfirmed)) throw new ApiError(409, "CONFLICT", "There is no interview time to confirm.");
  a.slotConfirmed = true;
  a.updatedAt = nowIso();
  a.history.push({ status: "interview", at: a.updatedAt, by: "recruiter", note: "Confirmed the interview time" });
  const slot = a.slots.find((s) => s.id === a.chosenSlotId);
  notify(ctx.db, a.candidateId, { type: "slot_confirmed", title: "Your interview time is confirmed", body: slot ? new Date(slot.start).toLocaleString("en-AU", { dateStyle: "medium", timeStyle: "short" }) : "", link: `/applications/${a.id}` });
  return recruiterView(ctx.db, a);
});

route("POST", "/recruiter/applications/:id/feedback", async (ctx) => {
  const { u, a } = ownApp(ctx);
  await loadJobs();
  if (!FINAL.includes(a.status)) throw new ApiError(409, "CONFLICT", "You can give feedback when the application is finished.");
  const { toOther = "", toTeam = "" } = ctx.body;
  validation({
    toOther: String(toOther).length <= 1000 ? "" : "Use 1000 characters or fewer.",
    toTeam: String(toTeam).length <= 1000 ? "" : "Use 1000 characters or fewer.",
    form: String(toOther).trim() || String(toTeam).trim() ? "" : "Write feedback in at least one box.",
  });
  a.feedback.recruiter = { toOther: scrubContact(toOther).trim(), toTeam: String(toTeam).trim(), at: nowIso() };
  if (a.feedback.recruiter.toOther) notify(ctx.db, a.candidateId, { type: "feedback", title: `${u.company} sent you feedback`, link: `/applications/${a.id}` });
  return recruiterView(ctx.db, a);
});

// ---------- Anonymous candidates (Feature 5) ----------
const candidatePool = (db) => db.users.filter((x) => x.role === "candidate" && x.onboarding === "done" && sharedProfileOf(x).skills.length);
function candidateCard(db, recruiter, cand, job) {
  const shared = sharedProfileOf(cand);
  const sm = skillMatch(job ? job.skills : [], namesFromList(shared.skills));
  const app = job && db.applications.find((a) => a.jobId === job.id && a.candidateId === cand.id);
  return {
    id: cand.id, alias: shared.alias, roles: shared.roles, skills: shared.skills, qualifications: shared.qualifications,
    years: shared.years, industries: shared.industries, locations: shared.locations,
    coverage: sm.coverage, matched: sm.matched, partial: sm.partial, total: job ? job.skills.length : 0,
    saved: (db.savedCandidates[recruiter.id] || []).includes(cand.id),
    applicationId: app && app.recruiterId === recruiter.id ? app.id : null,
  };
}
function pickJob(ctx, u) {
  const own = ctx.db.postedJobs.filter((j) => j.ownerId === u.id);
  const id = ctx.query.jobId;
  const j = (id && own.find((x) => x.id === id)) || own.find((x) => isOpen({ closesAt: new Date(x.closesAt) })) || own[0] || null;
  return j ? findJob(ctx.db, j.id) : null;
}

// Shortlist ordered by the skill coverage for the chosen job. Basic: the top N only (Feature 5 AC7).
route("GET", "/recruiter/candidates", async (ctx) => {
  const u = requireRole(ctx, "recruiter");
  await loadJobs();
  const job = pickJob(ctx, u);
  const ent = entitlementsOf(ctx.db, u);
  const skipped = new Set(ctx.db.skippedCandidates[u.id] || []);
  const view = ctx.query.view === "saved" ? "saved" : "all";
  let all = candidatePool(ctx.db).filter((c) => !skipped.has(c.id)).map((c) => candidateCard(ctx.db, u, c, job));
  if (view === "saved") all = all.filter((c) => c.saved);
  all.sort((a, b) => (b.coverage ?? -1) - (a.coverage ?? -1) || b.matched - a.matched || a.alias.localeCompare(b.alias));
  const items = ent.topN ? all.slice(0, ent.topN) : all;
  items.forEach((c) => track(ctx.db, { type: "profile_appear", targetType: "candidate", targetId: c.id, actorId: u.id }));
  return { job: job ? { id: job.id, title: job.title, skills: job.skills } : null, items, total: all.length, limitedTo: ent.topN, plan: ent.plan, skippedCount: skipped.size };
});

route("GET", "/recruiter/candidates/:id", async (ctx) => {
  const u = requireRole(ctx, "recruiter");
  await loadJobs();
  const cand = candidatePool(ctx.db).find((c) => c.id === ctx.params.id);
  if (!cand) throw new ApiError(404, "NOT_FOUND", "We can't find this profile.");
  const job = pickJob(ctx, u);
  const card = candidateCard(ctx.db, u, cand, job);
  const sm = skillMatch(job ? job.skills : [], namesFromList(card.skills));
  track(ctx.db, { type: "profile_watch", targetType: "candidate", targetId: cand.id, actorId: u.id });
  return { ...card, job: job ? { id: job.id, title: job.title } : null, match: { coverage: sm.coverage, skills: sm.items }, targetRoles: sharedProfileOf(cand).targetRoles, workTypes: sharedProfileOf(cand).workTypes, fieldsOfStudy: sharedProfileOf(cand).fieldsOfStudy, entitlements: entitlementsOf(ctx.db, u) };
});

const toggleList = (obj, key, id, on) => {
  const l = obj[key] || (obj[key] = []);
  const has = l.includes(id);
  if (on && !has) l.push(id);
  if (!on && has) obj[key] = l.filter((x) => x !== id);
};
route("PUT", "/recruiter/candidates/:id/save", (ctx) => {
  const u = requireRole(ctx, "recruiter");
  toggleList(ctx.db.savedCandidates, u.id, ctx.params.id, true);
  track(ctx.db, { type: "profile_saved", targetType: "candidate", targetId: ctx.params.id, actorId: u.id });
  return { id: ctx.params.id, saved: true };
});
route("DELETE", "/recruiter/candidates/:id/save", (ctx) => {
  const u = requireRole(ctx, "recruiter");
  toggleList(ctx.db.savedCandidates, u.id, ctx.params.id, false);
  return { id: ctx.params.id, saved: false };
});
route("PUT", "/recruiter/candidates/:id/skip", (ctx) => {
  const u = requireRole(ctx, "recruiter");
  toggleList(ctx.db.skippedCandidates, u.id, ctx.params.id, true);
  track(ctx.db, { type: "profile_skip", targetType: "candidate", targetId: ctx.params.id, actorId: u.id });
  return { id: ctx.params.id, skipped: true };
});
route("DELETE", "/recruiter/candidates/skipped", (ctx) => {
  const u = requireRole(ctx, "recruiter");
  ctx.db.skippedCandidates[u.id] = [];
  return { ok: true };
});

// Premium: contact a candidate who did not apply (headhunting). Status "contacted".
route("POST", "/recruiter/candidates/:id/contact", async (ctx) => {
  const u = requireRole(ctx, "recruiter");
  requirePremium(ctx.db, u, "canContact");
  await loadJobs();
  const cand = candidatePool(ctx.db).find((c) => c.id === ctx.params.id);
  if (!cand) throw new ApiError(404, "NOT_FOUND", "We can't find this profile.");
  const posted = ctx.db.postedJobs.find((j) => j.id === ctx.body.jobId && j.ownerId === u.id);
  if (!posted) throw new ApiError(400, "VALIDATION_ERROR", "Choose one of your jobs.", { jobId: "Choose one of your jobs." });
  if (ctx.db.applications.some((a) => a.jobId === posted.id && a.candidateId === cand.id)) throw new ApiError(409, "CONFLICT", "This person is already in the pipeline for this job.");
  validation({ message: String(ctx.body.message || "").trim().length >= 10 && String(ctx.body.message).length <= 500 ? "" : "Write a message of 10 to 500 characters." });
  const job = findJob(ctx.db, posted.id);
  const snapshot = sharedProfileOf(cand);
  const a = {
    id: newId(), jobId: posted.id, candidateId: cand.id, recruiterId: u.id, origin: "contacted", status: "contacted",
    note: "", message: scrubContact(ctx.body.message).trim(), snapshot, match: snapshotMatch(job, snapshot),
    history: [], slots: [], chosenSlotId: null, slotConfirmed: false, identityShared: false, offer: null, feedback: {}, createdAt: nowIso(), updatedAt: nowIso(),
  };
  addHistory(a, "contacted", "recruiter", a.message);
  ctx.db.applications.push(a);
  notify(ctx.db, cand.id, { type: "contacted", title: `${u.company} invited you to apply for ${posted.title}`, body: a.message, link: `/applications/${a.id}` });
  return recruiterView(ctx.db, a);
});

// Premium: compare two profiles side by side, per skill. No combined score, no ranking of the two people.
route("GET", "/recruiter/compare", async (ctx) => {
  const u = requireRole(ctx, "recruiter");
  requirePremium(ctx.db, u, "canCompare");
  await loadJobs();
  const job = pickJob(ctx, u);
  const pool = candidatePool(ctx.db);
  const one = (id) => {
    const c = pool.find((x) => x.id === id);
    if (!c) throw new ApiError(404, "NOT_FOUND", "We can't find one of the profiles.");
    const s = sharedProfileOf(c);
    return { id: c.id, alias: s.alias, roles: s.roles, qualifications: s.qualifications, years: s.years, skills: skillMatch(job ? job.skills : [], namesFromList(s.skills)).items, otherSkills: s.skills.filter((x) => !(job ? job.skills : []).includes(x)) };
  };
  return { job: job ? { id: job.id, title: job.title, skills: job.skills } : null, a: one(ctx.query.a), b: one(ctx.query.b) };
});

export { recruiterView };
```

### `app/js/api/mock/routes-platform.js`

```js
// MOCK BACKEND — notifications, stats for charts, premium entitlements and demo data (Feature 7).
// The real backend replaces this file. Charts are about skills and process, never a score on a person.
import { route, ApiError, requireUser, entitlementsOf, list, validation } from "./core.js";
import { loadJobs, recommend } from "./jobs.js";
import { FINAL } from "./routes-applications.js";
import { resetDb } from "./db.js";

// ---------- Notifications (in-app; "Email sent (demo)" for email events) ----------
route("GET", "/notifications", (ctx) => {
  const u = requireUser(ctx);
  const items = ctx.db.notifications.filter((n) => n.userId === u.id).sort((a, b) => Date.parse(b.createdAt) - Date.parse(a.createdAt)).slice(0, 50)
    .map(({ userId, ...n }) => n);
  return { items, unread: items.filter((n) => !n.read).length };
});
route("POST", "/notifications/read", (ctx) => {
  const u = requireUser(ctx);
  const ids = new Set(list(ctx.body.ids));
  ctx.db.notifications.forEach((n) => { if (n.userId === u.id && (ids.size === 0 || ids.has(n.id))) n.read = true; });
  return { ok: true };
});

// ---------- Entitlements (premium demo toggle; real payments are out of scope) ----------
route("GET", "/entitlements", (ctx) => entitlementsOf(ctx.db, requireUser(ctx)));
route("PUT", "/entitlements", (ctx) => {
  const u = requireUser(ctx);
  validation({ plan: ["basic", "premium"].includes(ctx.body.plan) ? "" : "Choose Basic or Premium." });
  ctx.db.plans[u.id] = ctx.body.plan;
  return entitlementsOf(ctx.db, u);
});

// ---------- Stats (Feature 7 AC5, AC6, AC8, AC9) ----------
const STAGES = ["applied", "contacted", "review", "interview", "accepted", "offer", "confirmed", "rejected", "declined"];
const countBy = (arr, key) => arr.reduce((m, x) => ((m[key(x)] = (m[key(x)] || 0) + 1), m), {});

route("GET", "/stats", async (ctx) => {
  const u = requireUser(ctx);
  await loadJobs();
  const ent = entitlementsOf(ctx.db, u);
  const db = ctx.db;
  if (u.role === "candidate") {
    const apps = db.applications.filter((a) => a.candidateId === u.id);
    const ev = db.events.filter((e) => e.targetType === "candidate" && e.targetId === u.id);
    const basic = {
      applications: apps.length,
      // "Moved to the next step": beyond Applied (Feature 7 AC9)
      movedOn: apps.filter((a) => !["applied", "contacted"].includes(a.status)).length,
      confirmed: apps.filter((a) => a.status === "confirmed").length,
      byStage: STAGES.map((s) => ({ stage: s, count: apps.filter((a) => a.status === s).length })).filter((x) => x.count),
      // Own profile events, as counts (Feature 7 AC6). Skips are not shown (AC7).
      profile: { appear: ev.filter((e) => e.type === "profile_appear").length, watch: ev.filter((e) => e.type === "profile_watch").length, saved: ev.filter((e) => e.type === "profile_saved").length },
    };
    let advanced = null;
    if (ent.advancedCharts && u.profile) {
      // Skill gap ranking and demand: from the 20 best-fitting open jobs
      const jobs = recommend(db, u.profile, 20);
      const gaps = countBy(jobs.flatMap((j) => j.match.gaps), (g) => g);
      const have = countBy(jobs.flatMap((j) => j.match.matchedSkills), (g) => g);
      const top = (m) => Object.entries(m).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([skill, count]) => ({ skill, count }));
      advanced = { basis: jobs.length, gapRanking: top(gaps), demandForYourSkills: top(have) };
    }
    return { role: "candidate", basic, advanced, plan: ent.plan };
  }
  // Recruiter
  const own = db.postedJobs.filter((j) => j.ownerId === u.id);
  const ids = new Set(own.map((j) => j.id));
  const apps = db.applications.filter((a) => ids.has(a.jobId));
  const open = own.filter((j) => Date.parse(j.closesAt) >= Date.now());
  const awaiting = apps.filter((a) => ["applied", "review"].includes(a.status) || (a.status === "interview" && a.chosenSlotId && !a.slotConfirmed));
  const basic = {
    openJobs: open.length,
    jobsAtTarget: own.filter((j) => apps.filter((a) => a.jobId === j.id && a.origin === "applied").length >= j.targetApplicants).length,
    awaitingResponse: awaiting.length,
    totalJobs: own.length,
  };
  let advanced = null;
  if (ent.advancedCharts) {
    // Aggregate counts per job, never per candidate (Feature 7 privacy NFR)
    const ev = db.events.filter((e) => e.targetType === "job" && ids.has(e.targetId));
    advanced = {
      pipeline: STAGES.map((s) => ({ stage: s, count: apps.filter((a) => a.status === s).length })),
      jobs: own.map((j) => ({ id: j.id, title: j.title, appear: ev.filter((e) => e.targetId === j.id && e.type === "job_appear").length, watch: ev.filter((e) => e.targetId === j.id && e.type === "job_watch").length, save: ev.filter((e) => e.targetId === j.id && e.type === "job_save").length, apply: apps.filter((a) => a.jobId === j.id && a.origin === "applied").length })),
      finished: apps.filter((a) => FINAL.includes(a.status)).length,
    };
  }
  return { role: "recruiter", basic, advanced, plan: ent.plan };
});

// ---------- Demo data (mock only, not part of the real API) ----------
route("POST", "/demo/reset", (ctx) => {
  resetDb();
  ctx.skipSave = true; // do not write the old data back
  return { ok: true };
});
```

### `app/js/views/legal.js`

```js
// Terms of Use ("/terms") and Privacy Policy ("/privacy"). Placeholder text.
import { logoHtml } from "../core/dom.js";

function page({ title, other, otherHref, note, body }) {
  return `
  <nav class="top-nav" aria-label="Main">
    <div class="container">
      ${logoHtml("#/")}
      <div class="nav-right"><a href="${otherHref}" class="legal-link">${other}</a></div>
    </div>
  </nav>
  <main class="legal-page">
    <span class="eyebrow">Legal</span>
    <h1>${title}</h1>
    <p class="updated">Last updated: 5 October 2026</p>
    <div class="legal-note" role="note">${note}</div>
    ${body}
  </main>
  <footer class="footer">
    <div class="container footer-bottom plain">© 2026 Jinder — Where skills meet their match. · <a href="${otherHref}" class="legal-link">${other}</a></div>
  </footer>`;
}

export async function termsView(root) {
  root.innerHTML = page({
    title: "Terms of Use", other: "Privacy Policy", otherHref: "#/privacy",
    note: "This is placeholder text. It is not a legal agreement. Replace it with terms reviewed by a lawyer before launch.",
    body: `
    <h2>1. About Jinder</h2>
    <p>Jinder helps international talent show their skills in terms that Australian employers recognise. It helps employers review talent with clear, explained matches.</p>
    <h2>2. Your account</h2>
    <ul>
      <li>Give correct information when you create an account.</li>
      <li>Keep your password private. You are responsible for activity on your account.</li>
      <li>You can close your account at any time.</li>
    </ul>
    <h2>3. How you can use the service</h2>
    <ul>
      <li>Upload only documents that you have the right to share.</li>
      <li>Do not upload false or misleading information.</li>
      <li>Do not use the service to discriminate against talent.</li>
    </ul>
    <h2>4. Decisions stay with people</h2>
    <p>Jinder gives decision support, not decisions. Employers make all hiring decisions. Match scores and skill translations are suggestions, and each one comes with its reasons.</p>
    <h2>5. Your content</h2>
    <p>You own the CVs, profiles and job descriptions that you upload. You give Jinder permission to process them only to provide the service to you.</p>
    <h2>6. Changes to these terms</h2>
    <p>We will tell you before we make important changes to these terms.</p>
    <h2>7. Contact</h2>
    <p>For questions about these terms, contact the Jinder team.</p>`,
  });
}

export async function privacyView(root) {
  root.innerHTML = page({
    title: "Privacy Policy", other: "Terms of Use", otherHref: "#/terms",
    note: "This is placeholder text. In this version, account data stays in your browser only and is not sent to a server. Replace this page with a reviewed policy before launch.",
    body: `
    <h2>1. Information we collect</h2>
    <ul>
      <li><strong>Account details:</strong> name, email, account type and, for employers, company name.</li>
      <li><strong>Profile content:</strong> CVs, work history and qualifications that you upload.</li>
      <li><strong>Role content:</strong> job descriptions that employers add.</li>
    </ul>
    <h2>2. How we use it</h2>
    <ul>
      <li>To translate experience into recognised skills.</li>
      <li>To compare profiles with roles and explain each match.</li>
      <li>To operate and improve the service.</li>
    </ul>
    <h2>3. Who can see your profile</h2>
    <p>You control who sees your profile. An employer sees your translated profile only after you share it or apply for their role.</p>
    <h2>4. Fairness</h2>
    <p>We do not use nationality, ethnicity, age, gender or visa type to score a match. Every score shows the skills and evidence behind it.</p>
    <h2>5. Your rights</h2>
    <p>You can ask to see, correct or delete your data at any time. We handle personal information in line with the Australian Privacy Principles.</p>
    <h2>6. Contact</h2>
    <p>For privacy questions, contact the Jinder team.</p>`,
  });
}
```

### `app/js/views/landing.js`

```js
// Landing page (route "/"). Static markup only.
import { iconHtml as i, logoHtml } from "../core/dom.js";
import { isSignedIn } from "../api/index.js";

export async function landingView(root) {
  const signedIn = isSignedIn();
  root.innerHTML = `
  <nav class="top-nav" aria-label="Main">
    <div class="container">
      ${logoHtml("#/")}
      <div class="nav-links">
        <a href="#how">How it works</a>
        <a href="#talent">For talent</a>
        <a href="#employers">For employers</a>
      </div>
      <div class="nav-right">
        ${signedIn
          ? `<a href="#/home" class="btn btn-primary">Go to my workspace</a>`
          : `<a href="#/login" class="nav-login">Sign in</a><a href="#/signup" class="btn btn-primary">Get started</a>`}
      </div>
    </div>
  </nav>

  <main>
    <header class="hero">
      <span class="eyebrow hero-eyebrow">Skills-based hiring for <span class="au-chip">${i("map-pin")}Australia</span></span>
      <h1>Every skill, <em>recognised</em> — wherever it was built</h1>
      <p class="lead">
        Jinder translates overseas and cross-industry experience into the skills
        Australian employers look for — ranked, explained in plain language, and never a black box.
      </p>
      <div class="btn-row">
        <a href="#/signup" class="btn btn-primary btn-lg">Create free account ${i("arrow")}</a>
        <a href="#how" class="btn btn-secondary btn-lg">See how it works</a>
      </div>
      <p class="hero-note">Free for talent and employers during the pilot.</p>

      <div class="screenshot-frame" role="img" aria-label="Preview: a talent profile with overseas experience translated into Australian skill terms, with an 86% explained match for a Data Analyst role">
        <div class="frame-bar" aria-hidden="true"><i></i><i></i><i></i><span>jinder.app / talent / translation</span></div>
        <div class="frame-body" aria-hidden="true">
          <div>
            <div class="panel-title">Experience translation <span class="chip chip-pink">Cross-border</span></div>
            <div class="map-row"><span class="from">Product Owner, Hanoi</span>${i("arrow")}<span class="to">Agile delivery lead</span></div>
            <div class="map-row"><span class="from">BI Specialist, HCMC</span>${i("arrow")}<span class="to">Data Analyst</span></div>
            <div class="map-row"><span class="from">Informatica developer</span>${i("arrow")}<span class="to">ETL and ELT pipelines</span></div>
            <div class="map-row"><span class="from">B.Econ (VNU)</span>${i("arrow")}<span class="to">AQF Level 7 equivalent</span></div>
          </div>
          <div class="match-card">
            <div class="panel-title">Data Analyst · Sydney <span class="chip chip-green">Strong match</span></div>
            <div class="match-score">86%</div>
            <div class="meter"><span class="meter-86"></span></div>
            <div class="why">
              <div>${i("check")}Built Power BI dashboards for 6 teams</div>
              <div>${i("check")}SQL and Python for weekly reporting</div>
              <div class="gap">${i("alert")}Gap: Apache Airflow, about 1 month to learn</div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <section class="container market" aria-labelledby="marketTitle">
      <p class="eyebrow market-eyebrow">${i("map-pin")}The Australian job market</p>
      <h2 class="market-title" id="marketTitle">Skilled talent is here. Employers can't find it.</h2>
      <div class="stats">
        <div class="stat stat-talent">
          <span class="icon-tile pink">${i("graduation")}</span>
          <div><div class="stat-num">680,582</div><div class="stat-label">international students in Australia</div><div class="stat-src">Source: Dept. of Education, Jan–May 2026</div></div>
        </div>
        <div class="stat stat-employer">
          <span class="icon-tile blue">${i("briefcase")}</span>
          <div><div class="stat-num">69%</div><div class="stat-label">of employers struggle to find skilled talent</div><div class="stat-src">Source: ManpowerGroup, 2024</div></div>
        </div>
      </div>
    </section>

    <section class="band" id="how">
      <div class="container">
        <div class="section-intro">
          <span class="eyebrow">How it works</span>
          <h2 class="section-head">From overseas experience to a confident hire</h2>
        </div>
        <div class="grid-3">
          <article class="feature-card">
            <span class="step-num">01</span>
            <div class="icon-tile pink">${i("upload")}</div>
            <h3>Translate experience</h3>
            <p>Upload a CV. We map overseas job titles, qualifications and industry vocabulary to skills the Australian market recognises.</p>
          </article>
          <article class="feature-card">
            <span class="step-num">02</span>
            <div class="icon-tile yellow">${i("target")}</div>
            <h3>Check the gaps</h3>
            <p>Compare a translated profile against a real job description and see exactly which skills to strengthen.</p>
          </article>
          <article class="feature-card">
            <span class="step-num">03</span>
            <div class="icon-tile blue">${i("user-check")}</div>
            <h3>Decide with context</h3>
            <p>Employers see ranked matches with plain-language reasons. The analysis supports the decision — people make it.</p>
          </article>
        </div>
      </div>
    </section>

    <section class="band band-soft">
      <div class="container grid-2">
        <article class="audience-card" id="talent">
          <div class="icon-tile accent">${i("globe")}</div>
          <h3>For international talent</h3>
          <ul class="check-list">
            <li>${i("check")}See your experience in the language local employers use</li>
            <li>${i("check")}Know your gaps before you apply</li>
            <li>${i("check")}Build one profile, reuse it for every role</li>
          </ul>
          <a href="#/signup?role=candidate" class="btn btn-primary btn-lg">Create my profile</a>
        </article>
        <article class="audience-card" id="employers">
          <div class="icon-tile green">${i("briefcase")}</div>
          <h3>For Australian employers</h3>
          <ul class="check-list">
            <li>${i("check")}Find qualified talent that keyword filters miss</li>
            <li>${i("check")}Explainable, ranked matches for every role</li>
            <li>${i("check")}Built for SMEs without large hiring teams</li>
          </ul>
          <a href="#/signup?role=recruiter" class="btn btn-secondary btn-lg">Start hiring</a>
        </article>
      </div>
    </section>

    <div class="container">
      <section class="cta-band-dark">
        <h2>No qualified person filtered out</h2>
        <p>Join as international talent or as an employer looking for skills that are already here.</p>
        <a href="#/signup" class="btn btn-on-dark btn-lg">Get started — it's free</a>
      </section>
    </div>
  </main>

  <footer class="footer">
    <div class="container">
      <div class="footer-grid">
        <div>
          ${logoHtml("#/")}
          <p class="slogan">Where skills meet their match.</p>
          <p>Making skills visible, comparable and trustworthy — for the people who make hiring decisions.</p>
        </div>
        <div><h4>Product</h4><ul><li><a href="#how">How it works</a></li><li><a href="#talent">For talent</a></li><li><a href="#employers">For employers</a></li></ul></div>
        <div><h4>Account</h4><ul><li><a href="#/login">Sign in</a></li><li><a href="#/signup">Create account</a></li></ul></div>
        <div><h4>Company</h4><ul><li><a href="#/">About</a></li><li><a href="#/privacy" class="legal-link">Privacy</a></li><li><a href="#/terms" class="legal-link">Terms</a></li></ul></div>
      </div>
      <div class="footer-bottom">© 2026 Jinder. All rights reserved.</div>
    </div>
  </footer>`;
}
```

### `app/js/views/auth.js`

```js
// Sign in ("/login") and Create account ("/signup"). Shared screens for both roles.
import { iconHtml as i, logoHtml, esc } from "../core/dom.js";
import { CONFIG } from "../config.js";
import { api, ApiError } from "../api/index.js";
import { isEmail, fieldError, clearErrors, focusFirstError, showAlert, applyFieldErrors, enhanceForm, safeNext } from "../core/forms.js";

const legalLine = `<p class="legal">© 2026 Jinder · <a href="#/privacy" class="legal-link" target="_blank" rel="noopener">Privacy</a> · <a href="#/terms" class="legal-link" target="_blank" rel="noopener">Terms</a></p>`;

function aside({ headline, points, quote, by }) {
  return `
    <aside class="auth-aside on-dark">
      ${logoHtml("#/")}
      <p class="slogan">Where skills meet their match.</p>
      <h2>${headline}</h2>
      <ul class="check-list">${points.map((p) => `<li>${i("check")}${p}</li>`).join("")}</ul>
      <div class="auth-quote">“${quote}”<strong>${by}</strong></div>
    </aside>`;
}

// ---------- Sign in ----------
export async function loginView(root, ctx) {
  root.innerHTML = `
  <div class="auth-split">
    ${aside({
      headline: "Welcome back to skills-based hiring",
      points: ["Your translated profile, ready for every role", "Ranked matches with plain-language reasons", "Your data stays yours — you choose who sees it"],
      quote: "We stopped losing great talent to keyword filters. Now we see the skills, not just the job title.",
      by: "Hiring manager, Sydney SME",
    })}
    <main class="auth-main">
      <div class="auth-top">
        ${logoHtml("#/")}
        <span>New to Jinder?</span>
        <a href="#/signup" class="btn btn-secondary">Create account</a>
      </div>
      <div class="auth-form-wrap">
        <h1>Sign in</h1>
        <p class="sub">Enter your details to access your workspace.</p>
        <div class="form-alert" role="alert" aria-live="polite" data-alert></div>
        <form novalidate>
          <div class="field">
            <label for="email">Work or personal email</label>
            <input id="email" name="email" type="email" class="text-input" placeholder="you@example.com" autocomplete="email" required />
            <div class="field-error" data-for="email"></div>
          </div>
          <div class="field">
            <div class="field-row">
              <label for="password">Password</label>
              <a href="#/login" class="text-link" data-forgot>Forgot password?</a>
            </div>
            <div class="input-wrap">
              <input id="password" name="password" type="password" class="text-input" autocomplete="current-password" required />
              <button type="button" class="toggle-pw" aria-label="Show password" aria-controls="password">${i("eye")}</button>
            </div>
            <div class="field-error" data-for="password"></div>
          </div>
          <label class="checkbox"><input type="checkbox" name="remember" /> Keep me signed in on this device</label>
          <button type="submit" class="btn btn-primary btn-lg btn-block">Sign in</button>
        </form>
        <p class="auth-foot">Don't have an account? <a href="#/signup" class="text-link">Create one</a></p>
        ${CONFIG.API_MODE === "mock" && CONFIG.MOCK_DEMO_DATA && CONFIG.MOCK_DEMO_ACCOUNTS.length ? `
        <div class="demo-box">
          <p class="demo-title">Try the demo</p>
          <p class="hint">Demo accounts with sample jobs and applications. The data stays in this browser.</p>
          <div class="demo-actions">${CONFIG.MOCK_DEMO_ACCOUNTS.map((a) => `<button type="button" class="btn btn-secondary btn-sm" data-demo="${esc(a.email)}">${esc(a.label)}</button>`).join("")}</div>
        </div>` : ""}
      </div>
      ${legalLine}
    </main>
  </div>`;

  const form = root.querySelector("form");
  // Fill the form with a demo account (mock only)
  root.querySelectorAll("[data-demo]").forEach((b) => b.addEventListener("click", () => {
    form.email.value = b.dataset.demo;
    form.password.value = CONFIG.MOCK_DEMO_PASSWORD;
    form.requestSubmit();
  }));
  const alertEl = root.querySelector("[data-alert]");
  enhanceForm(root);
  if (ctx.query.registered) showAlert(alertEl, "Thanks! If this email is new to Jinder, your account is ready. Sign in to continue.", "success");
  if (ctx.query.expired) showAlert(alertEl, "Your session has ended. Sign in again to continue.", "error");
  root.querySelector("[data-forgot]").addEventListener("click", (e) => {
    e.preventDefault();
    showAlert(alertEl, "Password reset is not available yet.", "error");
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearErrors(form, alertEl);
    const email = form.email.value.trim();
    const password = form.password.value;
    let ok = true;
    if (!isEmail(email)) ok = fieldError(form, "email", "Enter a valid email address.");
    if (!password) ok = fieldError(form, "password", "Enter your password.");
    if (!ok) return focusFirstError(form);
    const btn = form.querySelector("[type=submit]");
    btn.disabled = true;
    try {
      await api.auth.login({ email, password, remember: form.remember.checked });
      ctx.navigate(safeNext(ctx.query.next), { replace: true });
    } catch (err) {
      btn.disabled = false;
      showAlert(alertEl, err instanceof ApiError ? err.message : "Something went wrong. Try again.", "error");
    }
  });
}

// ---------- Create account ----------
export async function signupView(root, ctx) {
  root.innerHTML = `
  <div class="auth-split">
    ${aside({
      headline: "Make the skills you already have visible",
      points: ["Translate overseas and cross-industry experience", "See your gaps against real Australian roles", "Free for talent and employers during the pilot"],
      quote: "For the first time, my experience back home was described in words employers here understood.",
      by: "Master's graduate, Melbourne",
    })}
    <main class="auth-main">
      <div class="auth-top">
        ${logoHtml("#/")}
        <span>Already have an account?</span>
        <a href="#/login" class="btn btn-secondary">Sign in</a>
      </div>
      <div class="auth-form-wrap">
        <h1>Create your account</h1>
        <p class="sub">Tell us how you'll use Jinder.</p>
        <div class="role-picker" role="radiogroup" aria-label="Account type">
          <button type="button" class="role-option" role="radio" aria-checked="true" data-role="candidate">
            ${i("globe")}<div><strong>I'm looking for work</strong><span>Student or skilled migrant</span></div>
          </button>
          <button type="button" class="role-option" role="radio" aria-checked="false" data-role="recruiter">
            ${i("briefcase")}<div><strong>I'm hiring</strong><span>Employer or hiring team</span></div>
          </button>
        </div>
        <div class="form-alert" role="alert" aria-live="polite" data-alert></div>
        <form novalidate>
          <div class="field">
            <label for="name">Full name</label>
            <input id="name" name="name" type="text" class="text-input" placeholder="Jane Nguyen" autocomplete="name" required />
            <div class="field-error" data-for="name"></div>
          </div>
          <div class="field" data-alias-field>
            <div class="field-row">
              <label for="alias">Alias <span class="optional">(optional)</span></label>
              <button type="button" class="text-link link-btn" data-suggest>Suggest one</button>
            </div>
            <input id="alias" name="alias" type="text" class="text-input" maxlength="30" autocomplete="off" placeholder="For example, Teal Heron" aria-describedby="aliasHint" />
            <div class="hint" id="aliasHint">Employers see this name, not your real name. Leave it empty and we choose one for you.</div>
            <div class="field-error" data-for="alias"></div>
          </div>
          <div class="field" data-company hidden>
            <label for="company">Company</label>
            <input id="company" name="company" type="text" class="text-input" placeholder="Acme Pty Ltd" autocomplete="organization" />
            <div class="field-error" data-for="company"></div>
          </div>
          <div class="field">
            <label for="email">Email</label>
            <input id="email" name="email" type="email" class="text-input" placeholder="you@example.com" autocomplete="email" required />
            <div class="field-error" data-for="email"></div>
          </div>
          <div class="field">
            <label for="password">Password</label>
            <div class="input-wrap">
              <input id="password" name="password" type="password" class="text-input" autocomplete="new-password" aria-describedby="pwHint" required />
              <button type="button" class="toggle-pw" aria-label="Show password" aria-controls="password">${i("eye")}</button>
            </div>
            <div class="hint" id="pwHint">At least 8 characters.</div>
            <div class="field-error" data-for="password"></div>
          </div>
          <div class="field">
            <label for="confirm">Confirm password</label>
            <input id="confirm" name="confirm" type="password" class="text-input" autocomplete="new-password" required />
            <div class="field-error" data-for="confirm"></div>
          </div>
          <label class="checkbox"><input type="checkbox" name="terms" /> <span>I agree to the <a href="#/terms" class="legal-link" target="_blank" rel="noopener">Terms<span class="sr-only"> (opens in a new tab)</span></a> and <a href="#/privacy" class="legal-link" target="_blank" rel="noopener">Privacy Policy<span class="sr-only"> (opens in a new tab)</span></a></span></label>
          <button type="submit" class="btn btn-primary btn-lg btn-block">Create account</button>
        </form>
      </div>
      ${legalLine}
    </main>
  </div>`;

  const form = root.querySelector("form");
  const alertEl = root.querySelector("[data-alert]");
  const companyField = root.querySelector("[data-company]");
  const options = root.querySelectorAll(".role-option");
  enhanceForm(root);

  const aliasField = root.querySelector("[data-alias-field]");
  let role = "candidate";
  const setRole = (next) => {
    role = next;
    options.forEach((o) => o.setAttribute("aria-checked", String(o.dataset.role === role)));
    companyField.hidden = role !== "recruiter";
    aliasField.hidden = role !== "candidate"; // Only candidates have an alias
  };

  // "Suggest one": a free "Colour Animal" alias from the API
  root.querySelector("[data-suggest]").addEventListener("click", async () => {
    try {
      const { alias } = await api.aliases.suggest();
      form.alias.value = alias;
      form.alias.focus();
    } catch { /* keep the field as it is */ }
  });
  // Show the alias that the API suggests for a taken alias, with a button to use it
  function showAliasTaken(err) {
    fieldError(form, "alias", err.fields?.alias || err.message);
    if (!err.suggestion) return;
    const box = form.querySelector('.field-error[data-for="alias"]');
    const use = document.createElement("button");
    use.type = "button";
    use.className = "text-link link-btn alias-use";
    use.textContent = `Use “${err.suggestion}”`;
    use.addEventListener("click", () => { form.alias.value = err.suggestion; clearErrors(form, alertEl); form.alias.focus(); });
    box.append(" ", use);
  }
  options.forEach((o) => o.addEventListener("click", () => setRole(o.dataset.role)));
  if (["recruiter", "employer"].includes(ctx.query.role)) setRole("recruiter");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearErrors(form, alertEl);
    const data = {
      role,
      name: form.name.value.trim(),
      company: role === "recruiter" ? form.company.value.trim() : undefined,
      alias: role === "candidate" && form.alias.value.trim() ? form.alias.value.trim().replace(/\s+/g, " ") : undefined,
      email: form.email.value.trim(),
      password: form.password.value,
    };
    let ok = true;
    if (!data.name) ok = fieldError(form, "name", "Enter your name.");
    if (data.alias && (data.alias.length < 3 || data.alias.length > 30)) ok = fieldError(form, "alias", "Use 3 to 30 characters.");
    if (role === "recruiter" && !data.company) ok = fieldError(form, "company", "Enter your company.");
    if (!isEmail(data.email)) ok = fieldError(form, "email", "Enter a valid email address.");
    if (data.password.length < 8) ok = fieldError(form, "password", "Use at least 8 characters.");
    if (form.confirm.value !== data.password) ok = fieldError(form, "confirm", "Passwords don't match.");
    if (!ok) return focusFirstError(form);
    if (!form.terms.checked) return showAlert(alertEl, "Please accept the Terms and Privacy Policy to continue.", "error");

    const btn = form.querySelector("[type=submit]");
    btn.disabled = true;
    try {
      await api.auth.signup(data);
      ctx.navigate("/login?registered=1");
    } catch (err) {
      btn.disabled = false;
      if (err instanceof ApiError && err.code === "ALIAS_TAKEN") { showAliasTaken(err); return focusFirstError(form); }
      if (err instanceof ApiError && err.code === "VALIDATION_ERROR" && applyFieldErrors(form, err.fields)) return focusFirstError(form);
      showAlert(alertEl, err instanceof ApiError ? err.message : "Something went wrong. Try again.", "error");
    }
  });
}
```

### `app/js/views/home.js`

```js
// Talent Home ("/home"), inside the app shell. An employer gets the employer Home (views/recruiter.js).
import { iconHtml as icon, esc, toList, formatDate } from "../core/dom.js";
import { api } from "../api/index.js";
import { openOnboarding } from "../components/onboarding.js";
import { jobCardHtml, paintMeters, bindBookmarks, bindJobActions, bindCompare } from "../components/job-card.js";
import { barChartHtml, upgradeHtml } from "../components/charts.js";
import { searchBarHtml, bindSearchBar } from "../components/search-bar.js";
import { sharedFactsHtml, skillChipsHtml } from "../components/profile-card.js";
import { recruiterHomeView } from "./recruiter.js";
import { fetchAllApplications } from "./applications.js";

const RECS_SHOWN = 5;   // the widget shows the 5 best jobs and has no pager (the Jobs screen has the full list)

const STAGE_LABEL = { applied: "Applied", contacted: "Contacted", review: "In review", interview: "Interview", accepted: "Accepted", offer: "Offer" };
const MAX_SKILL_CHIPS = 8;

export async function homeView(root, ctx) {
  if (ctx.user.role === "recruiter") return recruiterHomeView(root, ctx);
  root.innerHTML = `
    <div class="dash">
      <div class="dash-head">
        <div>
          <h1 data-greeting></h1>
          <p class="dash-sub" data-subline></p>
        </div>
        <button type="button" class="btn btn-primary btn-lg" data-primary></button>
      </div>

      <section class="panel activity" aria-labelledby="actTitle">
        <div class="panel-head"><div><h2 id="actTitle">Your activity</h2><p class="muted">Your active applications and what employers see. Never a score on you.</p></div></div>
        <div class="activity-grid">
          <div data-active><div class="empty" role="status"><p>Loading…</p></div></div>
          <div data-shared><div class="empty" role="status"><p>Loading…</p></div></div>
        </div>
      </section>

      ${searchBarHtml()}

      <section class="panel recs" aria-labelledby="recsTitle">
        <div class="panel-head">
          <div>
            <h2 id="recsTitle">Recommended for you</h2>
            <p class="muted" data-recs-sub></p>
          </div>
          <div class="panel-actions">
            <span class="chip chip-neutral" data-recs-source>Loading jobs…</span>
            <button type="button" class="btn btn-secondary" data-edit-prefs>Edit preferences</button>
          </div>
        </div>
        <div data-recs-list></div>
      </section>

      <section class="panel" aria-labelledby="insTitle">
        <div class="panel-head"><div><h2 id="insTitle">Skill insights</h2><p class="muted">From the open jobs that fit you best.</p></div></div>
        <div data-insights><div class="empty" role="status"><p>Loading…</p></div></div>
      </section>

      <div class="dash-grid" data-setup>
        <section class="panel" aria-labelledby="stepsTitle">
          <h2 id="stepsTitle">Get set up</h2>
          <p class="muted" data-steps-sub></p>
          <ol class="steps" data-steps></ol>
        </section>
        <aside class="letter-card">
          <div class="icon-tile accent on-canvas">${icon("shield")}</div>
          <h2>Explainable by design</h2>
          <p>You'll see exactly why each job is recommended. We never use your nationality, age, gender or visa status to match you.</p>
        </aside>
      </div>
    </div>`;

  const $ = (k) => root.querySelector(`[data-${k}]`);
  bindSearchBar(root, ctx.navigate);
  bindBookmarks($("recs-list"));
  bindJobActions($("recs-list"));
  bindCompare($("recs-list"));

  // Recommendations: { items, source } or null while loading
  let recs = null;
  const open = (start) => openOnboarding({ user: ctx.user, start, done: refresh });

  async function refresh() {
    ctx.user = await api.me.get();
    if (!root.isConnected || !$("greeting")) return;   // the talent left the Home while the profile loaded
    recs = null;
    render();
    renderActivity();
    renderInsights();
    await loadRecs();
  }
  async function loadRecs() {
    try { recs = await api.jobs.recommended({ pageSize: RECS_SHOWN, sort: "best" }); }
    catch { recs = { items: [], source: null, error: true }; }
    if (root.isConnected) render();
  }

  function render() {
    const me = ctx.user;
    const p = me.profile || {};
    const targets = toList(p.targetRole).join(", ");
    const hasProfile = me.onboarding === "done" && !!targets;

    $("greeting").textContent = `Welcome, ${me.name.split(" ")[0]}`;
    $("subline").textContent = `Talent workspace · Employers see you as ${me.alias || "your alias"}`;
    const action = $("primary");
    action.innerHTML = `${icon("upload")} ${me.cv ? "Update CV" : "Upload CV"}`;
    action.onclick = () => open("cv");

    renderRecs(me, hasProfile, targets, recs?.items || []);
    renderSteps(me, hasProfile);
  }

  function renderRecs(me, hasProfile, targets, items) {
    const src = recs?.source;
    $("recs-source").textContent = !recs ? "Loading jobs…"
      : src ? `${src.openCount} open jobs${src.updatedAt ? ` · updated ${formatDate(src.updatedAt)}` : ""}` : "Jobs unavailable";
    const edit = $("edit-prefs");
    edit.onclick = () => open("goals");
    edit.hidden = !hasProfile;
    const list = $("recs-list");
    const sub = $("recs-sub");

    if (!hasProfile) {
      sub.textContent = "Tell us what you're looking for and we'll suggest jobs that fit.";
      list.innerHTML = `<div class="empty"><div class="icon-tile accent">${icon("target")}</div><p>No recommendations yet.</p><button type="button" class="btn btn-primary" data-recs-start>Complete your profile</button></div>`;
      list.querySelector("[data-recs-start]").onclick = () => open(me.cv ? "questions" : "cv");
    } else if (!recs) {
      sub.textContent = `For: ${targets}`;
      list.innerHTML = `<div class="empty" role="status"><p>Loading jobs…</p></div>`;
    } else if (recs.error) {
      sub.textContent = `For: ${targets}`;
      list.innerHTML = `<div class="empty" role="alert"><p>We couldn't load jobs. Try again later.</p></div>`;
    } else if (!items.length) {
      sub.textContent = `For: ${targets}`;
      list.innerHTML = `<div class="empty"><p>No jobs match your profile yet. Try more target roles, skills or locations.</p></div>`;
    } else {
      const total = recs.page?.total ?? items.length;
      sub.textContent = `${items.length} ${items.length === 1 ? "job" : "jobs"} for: ${targets}. Each one shows why it fits.`;
      list.innerHTML = `<ul class="job-list">${items.slice(0, RECS_SHOWN).map((j) => jobCardHtml(j)).join("")}</ul>${total > items.length ? `<p class="recs-more muted">Showing the ${items.length} best of ${total} recommended jobs. <a class="text-link" href="#/jobs">See all jobs</a></p>` : ""}`;
      paintMeters(list);
    }
  }

  // "Get set up" shows only until every step is done
  function renderSteps(me, hasProfile) {
    const steps = [
      ["Create your account", "Done", true],
      ["Upload your CV", me.cv ? `Added: ${me.cv.name}` : "PDF or DOCX — we translate titles and qualifications", !!me.cv, "cv"],
      ["Complete your career profile", hasProfile ? "Done — you can edit it at any time" : "Education, skills and the job you want", hasProfile, "questions"],
    ];
    const done = steps.filter((s) => s[2]).length;
    $("setup").hidden = done === steps.length;
    $("steps-sub").textContent = `${done} of ${steps.length} complete`;
    $("steps").innerHTML = steps
      .map(([t, d, ok, start], i) => `<li class="${ok ? "done" : ""}"><span class="step-dot">${ok ? icon("check") : i + 1}</span><div class="step-text"><strong>${esc(t)}</strong><span>${esc(d)}</span></div>${ok ? "" : `<button type="button" class="btn btn-secondary" data-start="${start}">Start</button>`}</li>`)
      .join("");
    $("steps").querySelectorAll("[data-start]").forEach((b) => (b.onclick = () => open(b.dataset.start)));
  }

  // Your activity: active applications (not finished) + "What employers see" (Feature 4, Feature 7)
  async function renderActivity() {
    // All the applications (not one page): the count of active ones needs the whole list
    const [apps, shared] = await Promise.all([fetchAllApplications().then((items) => ({ items })).catch(() => null), api.profile.shared().catch(() => null)]);
    if (!root.isConnected) return;
    const activeEl = $("active");
    if (!apps) activeEl.innerHTML = `<p class="muted" role="alert">We couldn't load your applications.</p>`;
    else {
      const active = apps.items.filter((a) => !a.final);
      const action = active.filter((a) => a.needsAction).length;
      const byStage = Object.entries(active.reduce((m, a) => ((m[a.status] = (m[a.status] || 0) + 1), m), {}))
        .map(([s, n]) => ({ label: STAGE_LABEL[s] || s, value: n }));
      activeEl.innerHTML = `
        <h3 class="act-title">${icon("inbox")} Active applications</h3>
        <p class="big-num">${active.length}${action ? `<span class="chip chip-yellow act-chip">${icon("alert")}${action} need${action === 1 ? "s" : ""} your action</span>` : ""}</p>
        ${active.length ? barChartHtml(byStage) : `<p class="muted">No active applications. Find a job below and apply.</p>`}
        <a class="text-link act-link" href="#/applications">See all applications</a>`;
    }
    const sharedEl = $("shared");
    if (!shared) { sharedEl.innerHTML = `<p class="muted" role="alert">We couldn't load your shared profile.</p>`; }
    else {
      const more = shared.skills.length - MAX_SKILL_CHIPS;
      sharedEl.innerHTML = `
        <h3 class="act-title">${icon("eye")} What employers see</h3>
        <p class="tr-preview-alias"><span class="alias-badge">${esc(shared.alias || "—")}</span></p>
        ${shared.roles.length ? `<p class="tr-preview-line"><strong>Roles:</strong> ${shared.roles.map((r) => `${esc(r.title)}${r.anzsco ? ` (ANZSCO ${esc(r.anzsco)})` : ""}`).join(", ")}</p>` : ""}
        ${sharedFactsHtml(shared)}
        ${shared.skills.length
          ? `<div class="tr-preview-skills">${skillChipsHtml(shared, MAX_SKILL_CHIPS)}${more > 0 ? `<span class="hint">+${more} more</span>` : ""}</div>`
          : `<p class="muted">Employers can't find you yet. Accept your translated skills to share them.</p>`}
        <p class="hint">Never your name, contact details, photo, nationality or CV.</p>
        <button type="button" class="btn btn-secondary btn-sm" data-edit-profile>${icon("edit")}${shared.skills.length ? "Edit profile" : "Review translated skills"}</button>`;
      sharedEl.querySelector("[data-edit-profile]").onclick = () => open(shared.skills.length ? "review" : "translation");
    }
    paintMeters(root.querySelector(".activity"));
  }

  // Skill insights (Feature 7 AC9) are Premium
  async function renderInsights() {
    const el = $("insights");
    let st;
    try { st = await api.stats.get(); } catch { el.innerHTML = `<p class="muted">We couldn't load your insights.</p>`; return; }
    if (!root.isConnected) return;
    const adv = st.advanced;
    el.innerHTML = adv
      ? `<div class="charts-grid">
          ${barChartHtml(adv.gapRanking.map((g) => ({ label: g.skill, value: g.count })), { title: `Skills to learn next (in ${adv.basis} best-fit jobs)`, unit: "jobs", empty: "No skill gaps found." })}
          ${barChartHtml(adv.demandForYourSkills.map((g) => ({ label: g.skill, value: g.count })), { title: "Demand for your skills", unit: "jobs", empty: "No data yet." })}
        </div>`
      : upgradeHtml("See which skills to learn next and the demand for your skills.");
    paintMeters(el);
  }

  render();
  renderActivity();
  renderInsights();
  // First visit of a talent account: open onboarding
  if (!ctx.user.onboarding) open("cv");
  await loadRecs();
}
```

### `app/js/components/onboarding.js`

```js
// Onboarding dialog for candidate accounts (Feature 2: explainable cross-border skill translation).
// Path A (CV):   cv -> reading -> education -> experience -> skills -> credentials -> translation -> goals -> review
// Path B (skip): cv -> education -> experience -> skills -> credentials -> translation -> goals -> review
// The AI fills fields from the CV ("AI-detected"); fields it cannot find stay empty ("Missing").
// V2 (R1): the CV also gives the current role, the desired role, the level, the exact years, certifications and awards.
// Each one has a "from your CV" hint, or a muted hint when the CV does not show it. The talent can change every field.
// The candidate accepts, edits or removes each translated skill, and sets a level (1 to 5) for each skill. Only accepted skills reach employers.
// The data is used only to recommend jobs and to build the translated profile. See AI_Rule.md Rule 5 (PII).
import { h, icon, toList, announce } from "../core/dom.js";
import { api } from "../api/index.js";
import { CONFIG } from "../config.js";
import { createCombobox } from "./combobox.js";
import * as R from "../data/reference.js";
import { LEVELS, SKILL_LEVELS, skillLevelLabel } from "../data/levels.js";
import { experienceOf } from "./profile-card.js";

const MAX_CV_BYTES = 10 * 1024 * 1024; // Feature 2 AC1: proposed limit 10 MB
const CV_TYPES = [".pdf", ".docx"];
const POLL_MS = 600;
const POLL_LIMIT_MS = 30000;
const MAX_CREDENTIALS = 20;      // certifications and awards: the most rows in each list
const MIN_YEAR = 1990;
const PATHS = {
  cv: ["cv", "reading", "education", "experience", "skills", "credentials", "translation", "goals", "review"],
  skip: ["cv", "education", "experience", "skills", "credentials", "translation", "goals", "review"],
};
// What employers read next to these lists (decision D5): the names show at once, so no names of people or employers
const NAMES_HINT = "Employers see these names. Do not write your own name, your employer's name or contact details here.";
// What to tell when the CV does not show a field (R1, decision F11: the field stays empty, nothing is guessed)
const NOT_FOUND = {
  currentRole: "We could not find your current role in your CV. You can add it.",
  targetRole: "We could not find your desired role in your CV. You can add it.",
  level: "We could not find your level in your CV. You can choose it.",
  yearsExperience: "We could not find your years of experience in your CV. You can add them.",
  certifications: "We could not find certifications in your CV. You can add them.",
  awards: "We could not find awards in your CV. You can add them.",
};
const certByName = new Map(R.CERTIFICATIONS.map((c) => [c.name.toLowerCase(), c]));

let dialog, body, foot, stepLabel, bar, state, onDone;

const optionalTag = () => h("span", { class: "optional", text: " (optional)" });
const nextYear = () => new Date().getFullYear() + 1;

/** The band (the drop-down "Total years of work experience") for an exact number of years. The server uses the same rule. */
export function bandOf(years) {
  const y = Number(years);
  if (!Number.isFinite(y)) return "";
  return y < 1 ? R.YEARS[0] : y < 3 ? R.YEARS[1] : y < 6 ? R.YEARS[2] : y <= 10 ? R.YEARS[3] : R.YEARS[4];
}
// The level that the server gives a skill when the talent sets none (rule F8): Strong 4, Moderate 3, Limited 2
const evidenceLevel = (evidence) => ({ Strong: 4, Moderate: 3, Limited: 2 }[evidence] || 3);

// A year: a whole number from 1990 to next year, or null
const yearOrNull = (v) => {
  const n = Number(String(v ?? "").trim());
  return String(v ?? "").trim() !== "" && Number.isInteger(n) ? n : null;
};

// Clean the V2 keys of the profile (an old profile, a CV result or a draft may have them in odd shapes)
function normalizeProfile(d) {
  d.level = LEVELS.includes(d.level) ? d.level : "";
  const ye = d.yearsExperience === "" || d.yearsExperience == null ? NaN : Number(d.yearsExperience);
  d.yearsExperience = Number.isFinite(ye) && ye >= 0 && ye <= 40 ? ye : null;
  if (d.yearsExperience != null) d.years = bandOf(d.yearsExperience);
  const text = (v, n) => String(v ?? "").trim().slice(0, n);
  d.certifications = toList(d.certifications).map((c) => (typeof c === "string" ? { name: c } : c || {}))
    .map((c) => ({ name: text(c.name, 120), issuer: text(c.issuer, 120), year: yearOrNull(c.year) })).filter((c) => c.name).slice(0, MAX_CREDENTIALS);
  d.awards = toList(d.awards).map((a) => (typeof a === "string" ? { name: a } : a || {}))
    .map((a) => ({ name: text(a.name, 120), kind: R.AWARD_KINDS.some((k) => k.kind === a.kind) ? a.kind : "", year: yearOrNull(a.year) })).filter((a) => a.name).slice(0, MAX_CREDENTIALS);
}

const isEmptyValue = (v) => (Array.isArray(v) ? !v.length : v == null || v === "");

// ---------- "From your CV" hints (R1) ----------
function cvHint(name) {
  const el = h("p", { class: "hint cv-hint", "data-cv-hint": name });
  paintHint(el, name);
  return el;
}
function paintHint(el, name) {
  const found = state.detected.has(name);
  const notFound = !found && state.fromCv && state.found[name] === false && isEmptyValue(state.data[name]);
  el.className = `hint cv-hint${notFound ? " cv-hint-missing" : ""}`;
  el.replaceChildren(...(found ? [icon("check"), "From your CV. Check it. Change it if it is wrong."] : notFound ? [NOT_FOUND[name]] : []));
}

// ---------- "AI-detected" and "Missing" markers (Feature 2 AC2, AC6) ----------
function markerFor(name) {
  const box = h("span", { class: "field-markers", "data-marker": name });
  paintMarker(box, name);
  return box;
}
function paintMarker(box, name) {
  const empty = !toList(state.data[name]).length;
  box.replaceChildren(
    state.detected.has(name) ? h("span", { class: "chip chip-ai", title: "The AI found this in your CV. Check it." }, icon("check"), "AI-detected") : "",
    !state.detected.has(name) && state.missing.has(name) && empty ? h("span", { class: "chip chip-yellow", title: "Your CV does not show this. Add it if you can." }, "Missing") : "");
}
// The candidate changed a field: it is no longer only "AI-detected"
function touched(name) {
  state.detected.delete(name);
  body.querySelectorAll(`[data-marker="${name}"]`).forEach((b) => paintMarker(b, name));
  body.querySelectorAll(`[data-cv-hint="${name}"]`).forEach((e) => paintHint(e, name));
}

// `control` is a combobox ({ el, input }) or a plain element. `cv: true` adds the "from your CV" hint (R1).
function field(name, labelText, control, { optional, hint, cv } = {}) {
  const input = control.input || control;
  const hintId = hint ? `${name}-hint` : null;
  if (hintId) input.setAttribute("aria-describedby", hintId);
  return h("div", { class: "field", "data-field": name },
    h("div", { class: "field-row" }, h("label", { for: input.id }, labelText, optional ? optionalTag() : null), markerFor(name)),
    control.el || control,
    hint ? h("div", { class: "hint", id: hintId, text: hint }) : null,
    cv ? cvHint(name) : null,
    h("div", { class: "field-error", id: `${name}-error` }));
}
// Searchable dropdown. With allowCustom, the user can type a value that is not in the list.
function combo(name, options, placeholder, { allowCustom = true } = {}) {
  return createCombobox({ id: `ob-${name}`, options, value: state.data[name] || "", placeholder, allowCustom,
    onChange: (v) => { state.data[name] = v.trim(); touched(name); } });
}
// List field: searchable dropdown + "Add" button + removable chips. The user can pick
// several options and add values that are not in the list.
function multiCombo(name, labelText, options, { placeholder, hint, optional, max = 5, suggestions, custom = true, cv = false, notFoundText = "" } = {}) {
  state.data[name] = toList(state.data[name]);
  const values = () => state.data[name];
  const chips = h("ul", { class: "skill-list", "aria-label": labelText });
  const box = createCombobox({ id: `ob-${name}`, options, placeholder, clearOnPick: true, allowCustom: custom, onPick: (v) => add(v), exclude: values });
  const input = box.input;
  input.setAttribute("maxlength", "60");
  const hintId = `${name}-hint`;
  input.setAttribute("aria-describedby", hintId);
  const addBtn = h("button", { type: "button", class: "btn btn-secondary", "aria-label": `Add to ${labelText}`, onclick: () => add(input.value) }, icon("plus"), "Add");
  const suggest = suggestions ? h("div", { class: "suggestions" }) : null;
  const count = h("span", { class: "list-count", "aria-live": "polite" });

  function add(raw) {
    const v = String(raw).trim().replace(/\s+/g, " ");
    if (!v) return;
    const known = options.find((o) => o.toLowerCase() === v.toLowerCase());
    if (!known && !custom) {   // a list that takes only the listed values (the domains)
      error(name, notFoundText || "Choose a value from the list.");
      return input.focus();
    }
    clearFieldError(name);
    const match = known || v;
    if (!values().some((x) => x.toLowerCase() === match.toLowerCase()) && values().length < max) { values().push(match); touched(name); }
    input.value = "";
    paint();
    input.focus();
  }
  function paint() {
    chips.replaceChildren(...values().map((v) => h("li", { class: "skill-chip" }, v,
      h("button", { type: "button", "aria-label": `Remove ${v}`, onclick: () => { state.data[name] = values().filter((x) => x !== v); touched(name); paint(); input.focus(); } }, icon("x")))));
    const full = values().length >= max;
    input.disabled = full;
    addBtn.disabled = full;
    input.placeholder = full ? `Maximum ${max} reached` : placeholder;
    count.textContent = `${values().length} of ${max}`;
    if (suggest) {
      const ideas = suggestions().filter((s) => !values().some((x) => x.toLowerCase() === s.toLowerCase()));
      suggest.replaceChildren(...(ideas.length && !full ? [h("span", { class: "hint", text: "Suggestions:" }),
        ...ideas.map((s) => h("button", { type: "button", class: "choice", onclick: () => add(s) }, icon("plus"), s))] : []));
    }
  }
  // Text that is typed but not added yet is added when the user presses Continue
  state.flush.push(() => input.value.trim() && add(input.value));
  paint();
  return h("div", { class: "field", "data-field": name },
    h("div", { class: "field-row" }, h("label", { for: input.id }, labelText, optional ? optionalTag() : null), h("span", { class: "field-row-end" }, markerFor(name), count)),
    h("div", { class: "input-row" }, box.el, addBtn),
    h("div", { class: "hint", id: hintId, text: hint }),
    cv ? cvHint(name) : null,
    h("div", { class: "field-error", id: `${name}-error` }),
    chips, suggest);
}

// Toggle buttons for multi-select choices (aria-pressed)
function choices(name, labelText, options, { optional, hint, max } = {}) {
  const labelId = `ob-${name}-label`;
  const selected = new Set(state.data[name] || []);
  const group = h("div", { class: "choice-group", role: "group", "aria-labelledby": labelId, id: `ob-${name}` });
  options.forEach((o) => {
    const btn = h("button", { type: "button", class: "choice", "aria-pressed": String(selected.has(o)), text: o,
      onclick: () => {
        if (selected.has(o)) selected.delete(o);
        else if (!max || selected.size < max) selected.add(o);
        btn.setAttribute("aria-pressed", String(selected.has(o)));
        state.data[name] = [...selected];
      } });
    group.append(btn);
  });
  return h("div", { class: "field", "data-field": name },
    h("span", { class: "field-label", id: labelId }, labelText, optional ? optionalTag() : null),
    hint ? h("div", { class: "hint hint-top", text: hint }) : null,
    group,
    h("div", { class: "field-error", id: `${name}-error` }));
}

// Mock mode only: say that the fields come from a sample CV (AI_Rule.md Rule 4: no sample data shown as real)
function demoBanner() {
  if (CONFIG.API_MODE !== "mock" || !state.sampleLabel) return null;
  return h("p", { class: "demo-banner", role: "note" }, icon("alert"),
    h("span", { text: `Demo mode: the mock API filled these fields from a sample CV (${state.sampleLabel}), not from your file.` }));
}
// Path A: tell the candidate to check what the AI found
function checkNote() {
  if (!state.fromCv) return null;
  return h("p", { class: "privacy-note" }, icon("check"), h("span", { text: "Check what we found in your CV. Change anything that is wrong. Fields marked “Missing” were not in your CV." }));
}
// R1: what the CV showed, in one place. Each line is a field that the talent can change in the next steps.
// Only the V2 backend sends `found`. Without it (the mock, an old server) there is nothing to show.
function foundSummary() {
  if (!state.fromCv || !Object.keys(state.found).length) return null;
  const d = state.data;
  const items = [
    ["currentRole", "Current role", toList(d.currentRole)[0] || ""],
    ["targetRole", "Desired role", toList(d.targetRole)[0] || ""],
    ["level", "Level", d.level || ""],
    ["yearsExperience", "Years of experience", d.yearsExperience != null ? experienceOf(d) : ""],
    ["certifications", "Certifications", d.certifications.length ? `${d.certifications.length} found` : ""],
    ["awards", "Awards", d.awards.length ? `${d.awards.length} found` : ""],
  ].filter(([key]) => key in state.found);
  return h("div", { class: "cv-found", role: "note", "aria-labelledby": "cvFoundTitle" },
    h("h3", { id: "cvFoundTitle", class: "cv-found-title", text: "What we found in your CV" }),
    h("ul", { class: "cv-found-list" }, items.map(([key, label, value]) => {
      const ok = state.found[key] !== false && value;
      return h("li", { class: ok ? "is-found" : "is-missing" }, icon(ok ? "check" : "alert"),
        h("span", { class: "cv-found-label", text: `${label}: ` }),
        ok ? h("strong", { text: value }) : h("span", { class: "muted", text: "Not found. You can add it in the next steps." }));
    })),
    h("p", { class: "hint", text: "You can change every field in the next steps." }));
}

// ---------- Errors ----------
function clearErrors() {
  body.querySelectorAll(".field-error").forEach((e) => (e.textContent = ""));
  body.querySelectorAll("[aria-invalid]").forEach((e) => { e.removeAttribute("aria-invalid"); e.classList.remove("invalid"); });
  body.querySelector(".form-alert")?.remove();
}
function error(name, msg) {
  const box = body.querySelector(`[data-field="${name}"]`);
  box.querySelector(".field-error").textContent = msg;
  const control = box.querySelector("input, select, .choice-group, [data-focus]");
  control.setAttribute("aria-invalid", "true");
  control.classList.add("invalid");
  const described = [control.getAttribute("aria-describedby"), `${name}-error`].filter(Boolean);
  control.setAttribute("aria-describedby", [...new Set(described.join(" ").split(" "))].join(" "));
  return false;
}
function clearFieldError(name) {
  const box = body.querySelector(`[data-field="${name}"]`);
  if (!box) return;
  box.querySelector(".field-error").textContent = "";
  box.querySelectorAll("[aria-invalid]").forEach((e) => { e.removeAttribute("aria-invalid"); e.classList.remove("invalid"); });
}
// An error under one input of a row (certifications and awards). The input points to its message with aria-describedby.
function rowError(input, msg) {
  const err = input.closest(".field")?.querySelector(".field-error");
  if (!err) return false;
  err.textContent = msg;
  input.setAttribute("aria-invalid", "true");
  input.classList.add("invalid");
  input.setAttribute("aria-describedby", [...new Set([...(input.getAttribute("aria-describedby") || "").split(" "), err.id].filter(Boolean))].join(" "));
  return false;
}
function focusFirstError() {
  const first = body.querySelector("[aria-invalid='true']");
  (first?.matches(".choice-group") ? first.querySelector("button") : first)?.focus();
}
const inList = (name, list, msg) => (list.includes(state.data[name]) ? true : error(name, msg));
const atLeast = (name, n, msg) => ((state.data[name] || []).length >= n ? true : error(name, msg));
// The answers that a complete profile must have (the same rules as the steps)
const REQUIRED = ["qualification", "fieldOfStudy", "currentRole", "industry", "years", "skills", "translation", "targetRole", "locations", "workTypes"];
function filled(name) {
  const v = state.data[name];
  if (name === "translation") return (v || []).some(SHARED);
  if (name === "years") return R.YEARS.includes(v);
  return toList(v).length >= (name === "skills" ? 3 : 1);
}
const alertBox = (msg) => { body.querySelector(".form-alert")?.remove(); body.prepend(h("div", { class: "form-alert show error", role: "alert", text: msg })); };

// ---------- Translation step helpers ----------
const SHARED = (s) => s.status === "accepted" || s.status === "edited";
const KIND = { "cross-border": ["chip-pink", "Cross-border"], "cross-industry": ["chip-blue", "Cross-industry"], direct: ["chip-neutral", "Direct"] };
const EVIDENCE = { Strong: "chip-green", Moderate: "chip-yellow", Limited: "chip-neutral" };
const SOURCE = { role: "From your role", skill: "From your skills", qualification: "From your qualification" };

// A level (1 to 5) for one skill. Only the skills that the talent named have it; a skill from a role or a qualification has none.
// The first option leaves the level to the server, which uses the evidence (rule F8). The talent can set it at any time.
const levelFromCv = new WeakSet();   // skill cards whose level came from the CV and that the talent did not change
function levelPick(s, onLevel) {
  const id = `tr-level-${String(s.id).replace(/[^A-Za-z0-9_-]/g, "-")}`;
  const from = h("span", { class: "hint tr-level-from", hidden: !levelFromCv.has(s) }, icon("check"), "From your CV");
  const sel = h("select", { id, class: "text-input select tr-level-select", "data-level-for": s.id,
    onchange: () => { s.level = sel.value ? Number(sel.value) : null; state.levelTouched.add(s.id); levelFromCv.delete(s); from.hidden = true; onLevel && onLevel(); } },
    h("option", { value: "", text: `From the evidence (${skillLevelLabel(evidenceLevel(s.evidence))})` }),
    ...SKILL_LEVELS.map((l) => h("option", { value: String(l.value), text: `${l.value} · ${l.label}` })));
  sel.value = Number.isInteger(s.level) && s.level >= 1 && s.level <= 5 ? String(s.level) : "";
  return h("div", { class: "tr-level" }, h("label", { for: id }, "Level", h("span", { class: "sr-only", text: ` for ${s.mapped}` })), sel, from);
}

function translationCard(s, repaint, refreshPreview) {
  const [kindClass, kindText] = KIND[s.kind] || KIND.direct;
  const accepted = SHARED(s);
  const accept = h("button", { type: "button", class: "btn btn-secondary btn-sm tr-accept", "aria-pressed": String(accepted),
    "aria-label": `${accepted ? "Accepted" : "Accept"}: ${s.mapped}`,
    onclick: () => { s.status = accepted ? "suggested" : "accepted"; repaint(); announce(`${s.mapped} ${accepted ? "is not accepted" : "accepted"}.`); } },
    icon("check"), accepted ? "Accepted" : "Accept");
  const edit = h("button", { type: "button", class: "btn btn-ghost btn-sm", "aria-label": `Edit ${s.mapped}`, onclick: () => openEditor() }, "Edit");
  const remove = h("button", { type: "button", class: "btn btn-ghost btn-sm", "aria-label": `Remove ${s.mapped}`,
    onclick: () => { s.status = "removed"; repaint(); announce(`${s.mapped} removed. You can undo this below.`); } }, icon("x"), "Remove");
  const actions = h("div", { class: "tr-actions" }, accept, edit, remove);
  const card = h("li", { class: `tr-card${accepted ? " is-accepted" : ""}` },
    h("div", { class: "tr-tags" },
      h("span", { class: `chip ${kindClass}`, text: kindText }),
      h("span", { class: `chip ${EVIDENCE[s.evidence] || "chip-neutral"}`, title: "How much evidence supports this skill" }, `Evidence: ${s.evidence}`),
      s.status === "edited" ? h("span", { class: "chip chip-neutral", text: "Edited by you" }) : null),
    h("div", { class: "tr-map" },
      h("span", { class: "tr-from" }, h("span", { class: "sr-only", text: `${SOURCE[s.source] || "Original"}: ` }), s.original),
      icon("arrow"),
      h("strong", { class: "tr-to", text: s.mapped }),
      s.anzsco ? h("span", { class: "chip chip-blue tr-anzsco", title: "Australian occupation code" }, `ANZSCO ${s.anzsco}`) : null),
    h("p", { class: "tr-reason", text: s.reason }),
    s.evidenceText ? h("p", { class: "tr-evidence" }, h("span", { class: "tr-evidence-label", text: "From your CV: " }), `“${s.evidenceText}”`) : null,
    s.source === "skill" ? levelPick(s, refreshPreview) : null,
    actions);

  // Inline editor: change the Australian skill name (the candidate is in control)
  function openEditor() {
    const id = `tr-edit-${s.id}`;
    const box = createCombobox({ id, options: R.SKILLS, value: s.mapped, placeholder: "Skill name" });
    const save = h("button", { type: "button", class: "btn btn-primary btn-sm", text: "Save" });
    const cancel = h("button", { type: "button", class: "btn btn-ghost btn-sm", text: "Cancel", onclick: () => repaint() });
    const err = h("div", { class: "field-error", id: `${id}-error` });
    save.addEventListener("click", () => {
      const v = box.input.value.trim().replace(/\s+/g, " ");
      if (v.length < 2) { err.textContent = "Enter a skill name."; box.input.setAttribute("aria-invalid", "true"); box.input.setAttribute("aria-describedby", err.id); return box.input.focus(); }
      if (v !== s.mapped) { s.mapped = v; s.status = "edited"; } else s.status = "accepted";
      repaint();
      announce(`${v} saved.`);
    });
    box.input.addEventListener("keydown", (e) => { if (e.key === "Enter" && box.input.getAttribute("aria-expanded") !== "true") { e.preventDefault(); save.click(); } });
    actions.replaceWith(h("div", { class: "tr-editor" }, h("label", { for: id, class: "field-label", text: "Australian skill name" }), h("div", { class: "input-row" }, box.el, save, cancel), err));
    box.input.focus();
  }
  return card;
}

// "What employers see": built from the candidate's own decisions. The API builds the real view (GET /me/shared-profile).
function previewPanel() {
  const shared = (state.data.translation || []).filter(SHARED);
  const roles = shared.filter((s) => s.anzsco);
  const skills = [...new Set(shared.filter((s) => s.source !== "qualification").map((s) => s.mapped))];
  const quals = shared.filter((s) => s.source === "qualification").map((s) => s.mapped);
  const d = state.data;
  const exp = d.yearsExperience != null ? experienceOf(d) : d.years || "";
  const names = (items) => (items || []).map((x) => `${x.name}${x.year ? ` (${x.year})` : ""}`).join(", ");
  // A skill that the talent set a level for shows it: "Python · Advanced"
  const levelOf = (name) => skillLevelLabel(shared.find((s) => s.mapped === name && s.source === "skill")?.level);
  return h("aside", { class: "tr-preview", "aria-labelledby": "trPreviewTitle" },
    h("h3", { id: "trPreviewTitle", text: "What employers see" }),
    h("p", { class: "hint", text: "Your alias and the skills you accept. Never your name, contact details, photo, nationality, employer names or your CV." }),
    h("p", { class: "tr-preview-alias" }, h("span", { class: "alias-badge", text: state.alias || "Your alias" })),
    roles.length ? h("p", { class: "tr-preview-line" }, h("strong", { text: "Roles: " }), roles.map((r) => `${r.occupation || r.mapped} (ANZSCO ${r.anzsco})`).join(", ")) : null,
    d.level || exp ? h("p", { class: "tr-preview-line" }, h("strong", { text: "Level: " }), [d.level || "Not given", exp].filter(Boolean).join(" · ")) : null,
    h("div", { class: "tr-preview-skills" }, skills.length ? skills.map((x) => h("span", { class: "chip chip-green", text: levelOf(x) ? `${x} · ${levelOf(x)}` : x })) : h("span", { class: "hint", text: "No skills accepted yet." })),
    d.certifications.length ? h("p", { class: "tr-preview-line" }, h("strong", { text: "Certifications: " }), names(d.certifications)) : null,
    d.awards.length ? h("p", { class: "tr-preview-line" }, h("strong", { text: "Awards: " }), names(d.awards)) : null,
    quals.length ? h("p", { class: "tr-preview-line" }, h("strong", { text: "Qualifications: " }), quals.join(", ")) : null);
}

// ---------- Level and exact years (R1, F7) ----------
function levelField() {
  const sel = h("select", { id: "ob-level", class: "text-input select" },
    h("option", { value: "", text: "Not sure" }), ...LEVELS.map((l) => h("option", { value: l, text: l })));
  sel.value = state.data.level || "";
  sel.addEventListener("change", () => { state.data.level = sel.value; touched("level"); });
  return field("level", "Your level", sel, { optional: true, cv: true, hint: "The level of your current or latest role. Choose “Not sure” if you do not know." });
}
// An optional number. When it is set, the range of years is chosen for the talent (the server does the same).
function exactYearsField(yearsBox) {
  const input = h("input", { id: "ob-yearsExperience", type: "number", class: "text-input", min: "0", max: "40", step: "0.5", inputmode: "decimal",
    value: state.data.yearsExperience ?? "" });
  const lock = () => {
    const locked = state.data.yearsExperience != null;
    yearsBox.input.disabled = locked;
    yearsBox.el.querySelector(".combo-toggle")?.toggleAttribute("disabled", locked);
  };
  input.addEventListener("input", () => {
    const raw = input.value.trim();
    const n = Number(raw);
    state.data.yearsExperience = raw !== "" && Number.isFinite(n) && n >= 0 && n <= 40 ? n : null;
    if (state.data.yearsExperience != null) {
      state.data.years = bandOf(n);
      yearsBox.input.value = state.data.years;
      touched("years");
    }
    touched("yearsExperience");
    lock();
  });
  lock();
  return field("yearsExperience", "Exact years of experience", input, { optional: true, cv: true,
    hint: "A number from 0 to 40. Use 0.5 for half a year. If you add it, we choose the range below for you." });
}
function exactYearsOk() {
  const raw = (document.getElementById("ob-yearsExperience")?.value || "").trim();
  if (raw === "") return true;
  const n = Number(raw);
  return Number.isFinite(n) && n >= 0 && n <= 40 ? true : error("yearsExperience", "Enter a number from 0 to 40.");
}

// ---------- Certifications and awards (R1, R2): rows with a name, a few details and a year ----------
const credNames = (items) => (items || []).map((x) => `${x.name}${x.year ? ` (${x.year})` : ""}`).join(", ");
const yearIsOk = (raw) => raw === "" || (Number.isInteger(Number(raw)) && Number(raw) >= MIN_YEAR && Number(raw) <= nextYear());

// A list of rows. `makeRow(entry, i, onRemove)` returns { el, check, isEmpty }. The rows change `entry` directly.
function credentialList({ name, legend, addText, emptyText, blank, makeRow }) {
  const rows = h("ul", { class: "cred-rows" });
  const status = h("span", { class: "list-count", "aria-live": "polite" });
  const addBtn = h("button", { type: "button", class: "btn btn-secondary", id: `ob-${name}-add`, onclick: () => add() }, icon("plus"), addText);
  const none = h("p", { class: "muted cred-none", text: emptyText });
  let made = [];
  const items = () => state.data[name];

  function paint() {
    made = items().map((entry, i) => makeRow(entry, i, () => remove(i)));
    rows.replaceChildren(...made.map((r) => r.el));
    none.hidden = items().length > 0;
    const full = items().length >= MAX_CREDENTIALS;
    addBtn.disabled = full;
    status.textContent = full ? `Maximum ${MAX_CREDENTIALS} reached` : `${items().length} of ${MAX_CREDENTIALS}`;
  }
  function add() {
    if (items().length >= MAX_CREDENTIALS) return;
    items().push(blank());
    touched(name);
    paint();
    rows.querySelector(`#ob-${name}-${items().length - 1}-name`)?.focus();
  }
  function remove(i) {
    const label = items()[i]?.name || `${legend.toLowerCase().replace(/s$/, "")} ${i + 1}`;
    items().splice(i, 1);
    touched(name);
    paint();
    announce(`${label} removed.`);
    (rows.querySelector(`#ob-${name}-${Math.min(i, items().length - 1)}-name`) || addBtn).focus();
  }
  // Used by validate(): every row must be right. A row with nothing in it is dropped.
  state.rowChecks.push(() => {
    const ok = made.map((r) => r.check()).every(Boolean);
    if (ok) state.data[name] = items().filter((_, i) => !made[i].isEmpty());
    return ok;
  });
  paint();
  return h("fieldset", { class: "field cred-field", "data-field": name },
    h("legend", { class: "field-label" }, h("span", { class: "field-row-end" }, legend, markerFor(name), status)),
    h("p", { class: "hint cred-hint", id: `${name}-hint`, text: NAMES_HINT }),
    cvHint(name),
    none, rows,
    h("div", { class: "cred-add" }, addBtn),
    h("div", { class: "field-error", id: `${name}-error` }));
}
// A labelled cell of a row, with its own error line
function cell(cls, id, labelText, control, { optional } = {}) {
  return h("div", { class: `field ${cls}` },
    h("label", { for: id }, labelText, optional ? optionalTag() : null),
    control.el || control,
    h("div", { class: "field-error", id: `${id}-error` }));
}
function yearInput(id, entry, onTouch) {
  return h("input", { id, type: "number", class: "text-input", min: String(MIN_YEAR), max: String(nextYear()), step: "1", inputmode: "numeric",
    value: entry.year ?? "", oninput: (e) => { entry.year = yearOrNull(e.target.value); onTouch(); } });
}
const removeButton = (what, i, entry, onRemove) => h("button", { type: "button", class: "btn btn-ghost btn-sm cred-remove",
  "aria-label": `Remove ${what} ${i + 1}${entry.name ? `: ${entry.name}` : ""}`, onclick: onRemove }, icon("x"), "Remove");
const yearMessage = () => `Enter a year from ${MIN_YEAR} to ${nextYear()}.`;

function certificationRow(entry, i, onRemove) {
  const id = (k) => `ob-certifications-${i}-${k}`;
  const onTouch = () => touched("certifications");
  let auto = false;      // the issuer was set from the list of known certifications
  const issuer = h("input", { id: id("issuer"), type: "text", class: "text-input", maxlength: "120", value: entry.issuer || "", "aria-describedby": id("issuer-note"),
    oninput: () => { entry.issuer = issuer.value.trim(); onTouch(); } });
  const note = h("div", { class: "hint", id: id("issuer-note") });
  const remove = removeButton("certification", i, entry, onRemove);
  const sync = () => {
    const known = certByName.get(entry.name.toLowerCase());
    if (known) { entry.issuer = known.issuer; issuer.value = known.issuer; issuer.readOnly = true; auto = true; note.textContent = "From the list of known certifications."; }
    else { if (auto) { entry.issuer = ""; issuer.value = ""; auto = false; } issuer.readOnly = false; note.textContent = ""; }
    remove.setAttribute("aria-label", `Remove certification ${i + 1}${entry.name ? `: ${entry.name}` : ""}`);
  };
  const name = createCombobox({ id: id("name"), options: R.CERTIFICATIONS.map((c) => c.name), value: entry.name, placeholder: "Search or type the name",
    onChange: (v) => { entry.name = v.trim(); onTouch(); sync(); } });
  name.input.setAttribute("maxlength", "120");
  const year = yearInput(id("year"), entry, onTouch);
  sync();
  const el = h("li", { class: "cred-row", role: "group", "aria-label": `Certification ${i + 1}` },
    cell("cred-name", id("name"), "Name", name),
    cell("cred-year", id("year"), "Year", year, { optional: true }),
    h("div", { class: "field cred-issuer" }, h("label", { for: id("issuer") }, "Issuer", optionalTag()), issuer, note, h("div", { class: "field-error", id: `${id("issuer")}-error` })),
    remove);
  return {
    el,
    isEmpty: () => !entry.name && !entry.issuer && year.value.trim() === "",
    check() {
      let ok = true;
      const raw = year.value.trim();
      if (!entry.name && (entry.issuer || raw)) ok = rowError(name.input, "Enter the name, or remove this row.");
      if (!yearIsOk(raw)) ok = rowError(year, yearMessage());
      return ok;
    },
  };
}

function awardRow(entry, i, onRemove) {
  const id = (k) => `ob-awards-${i}-${k}`;
  const onTouch = () => touched("awards");
  const remove = removeButton("award", i, entry, onRemove);
  const name = h("input", { id: id("name"), type: "text", class: "text-input", maxlength: "120", value: entry.name || "", placeholder: "For example: Regional Hackathon Winner",
    oninput: (e) => { entry.name = e.target.value.trim(); onTouch(); remove.setAttribute("aria-label", `Remove award ${i + 1}${entry.name ? `: ${entry.name}` : ""}`); } });
  const kind = h("select", { id: id("kind"), class: "text-input select", onchange: (e) => { entry.kind = e.target.value; onTouch(); } },
    h("option", { value: "", text: "Choose a kind" }), ...R.AWARD_KINDS.map((k) => h("option", { value: k.kind, text: k.label })));
  kind.value = entry.kind || "";
  const year = yearInput(id("year"), entry, onTouch);
  const el = h("li", { class: "cred-row", role: "group", "aria-label": `Award ${i + 1}` },
    cell("cred-name", id("name"), "Name", name),
    cell("cred-year", id("year"), "Year", year, { optional: true }),
    cell("cred-kind", id("kind"), "Kind", kind),
    remove);
  return {
    el,
    isEmpty: () => !entry.name && !entry.kind && year.value.trim() === "",
    check() {
      let ok = true;
      const raw = year.value.trim();
      if (!entry.name && (entry.kind || raw)) ok = rowError(name, "Enter the name, or remove this row.");
      if (entry.name && !entry.kind) ok = rowError(kind, "Choose a kind.");
      if (!yearIsOk(raw)) ok = rowError(year, yearMessage());
      return ok;
    },
  };
}

// ---------- Steps ----------
const STEPS = {
  cv: {
    get title() { return state.edit ? "Update your CV" : "Add your CV"; },
    get sub() { return state.edit ? "We read the new CV and update your profile. You check every change before you save." : "We translate your job titles, qualifications and skills into terms Australian employers recognise."; },
    render() {
      const input = h("input", { type: "file", id: "ob-cv", class: "sr-only", accept: ".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        onchange: (e) => pickFile(e.target.files[0]) });
      const zone = h("label", { class: "dropzone", for: "ob-cv",
        ondragover: (e) => { e.preventDefault(); zone.classList.add("drag"); },
        ondragleave: () => zone.classList.remove("drag"),
        ondrop: (e) => { e.preventDefault(); zone.classList.remove("drag"); pickFile(e.dataTransfer.files[0]); } },
        h("span", { class: "icon-tile accent" }, icon("upload")),
        h("strong", {}, "Drag and drop your CV, or ", h("span", { class: "legal-link", text: "browse" })),
        h("span", { class: "hint", text: "PDF or DOCX, up to 10 MB" }));
      const fileRow = h("div", { id: "ob-file" });
      const wrap = h("div", { class: "field", "data-field": "cv" }, input, zone, fileRow, h("div", { class: "field-error", id: "cv-error", role: "alert" }));
      const note = h("p", { class: "privacy-note" }, icon("shield"),
        h("span", { text: "Employers never see your CV or your personal details. They see only your translated skills and experience, under an alias — not your name, contact details, photo or nationality." }));
      setTimeout(renderFile);
      return [wrap, note];
    },
    buttons: () => [
      state.edit ? null : h("button", { type: "button", class: "btn btn-ghost", text: "Skip for now", onclick: () => { state.fromCv = false; go("skip", 1); } }),
      h("button", { type: "submit", class: "btn btn-primary", id: "ob-cv-next", disabled: !state.file, text: "Upload and continue" }),
    ].filter(Boolean),
    validate: () => (state.file ? true : error("cv", "Choose a PDF or DOCX file.")),
    // Upload at once (POST /cv). The CV record is saved even if the user closes the dialog later.
    async next() {
      const btns = foot.querySelectorAll("button");
      btns.forEach((b) => (b.disabled = true));
      try {
        const res = await api.cv.upload(state.file);
        state.data.cv = res.cv;
        state.parseId = res.parse.id;
        state.parseError = "";
        if (state.edit) goPath(EDIT_PATHS.cv, 1);
        else go("cv", 1);
      } catch (err) {
        btns.forEach((b) => (b.disabled = false));
        renderFile();
        error("cv", err.fields?.file || err.message || "We couldn't upload this file. Try again.");
      }
    },
  },
  reading: {
    title: "Reading your CV",
    sub: "We look for your roles, skills and qualifications. This takes up to 15 seconds.",
    render() {
      if (state.parseError) {
        return [h("div", { class: "empty", role: "alert" },
          h("div", { class: "icon-tile accent" }, icon("alert")),
          h("p", { text: state.parseError }),
          h("p", { class: "hint", text: "Nothing is lost. You can try a different file, or enter your details yourself." }))];
      }
      setTimeout(poll);
      return [h("div", { class: "reading", role: "status" },
        h("div", { class: "progress-indeterminate", "aria-hidden": "true" }, h("span")),
        h("p", { text: "Reading your CV…" }))];
    },
    buttons: () => (state.parseError ? (state.edit ? [
      h("button", { type: "button", class: "btn btn-secondary", text: "Try a different file", onclick: () => { state.file = null; goPath(EDIT_PATHS.cv, 0); } }),
      h("button", { type: "button", class: "btn btn-primary", text: "Keep my current profile", onclick: () => goPath(EDIT_PATHS.review, 0) }),
    ] : [
      h("button", { type: "button", class: "btn btn-secondary", text: "Try a different file", onclick: () => { state.file = null; go("skip", 0); } }),
      h("button", { type: "button", class: "btn btn-primary", text: "Enter details myself", onclick: () => { state.fromCv = false; go("skip", 1); } }),
    ]) : []),
    validate: () => false,
  },
  education: {
    title: "Your education",
    sub: "Tell us about your qualifications. We show employers the Australian (AQF) level.",
    render: () => [demoBanner(), checkNote(), foundSummary(),
      multiCombo("qualification", "Qualifications", R.QUALIFICATIONS,
        { placeholder: "Search or type, e.g. Bachelor", hint: "Add all your qualifications, highest first." }),
      multiCombo("fieldOfStudy", "Fields of study", R.FIELDS_OF_STUDY,
        { placeholder: "Search or type, e.g. Computer science", hint: "Add one or more fields." }),
      multiCombo("studyCountry", "Countries where you studied", R.COUNTRIES,
        { placeholder: "Search or type a country", optional: true, max: 3, hint: "Used only to find the Australian equivalent (AQF level). It is never used to rank you." }),
    ],
    validate: () => [atLeast("qualification", 1, "Add at least one qualification."), atLeast("fieldOfStudy", 1, "Add at least one field of study.")].every(Boolean),
  },
  experience: {
    title: "Your experience",
    sub: "Tell us about the roles you have had, your level and where you worked.",
    render() {
      const yearsBox = combo("years", R.YEARS, "Choose a range", { allowCustom: false });
      return [demoBanner(),
        multiCombo("currentRole", "Current and past roles", R.ROLES,
          { placeholder: "Search or type a job title", cv: true, hint: "Start with your current or most recent role. Use the titles from your country — we translate them for you." }),
        multiCombo("industry", "Domains", R.DOMAINS,
          { placeholder: "Search or choose a domain", max: 3, custom: false, notFoundText: "Choose a domain from the list.", hint: "Add the domains you have worked in." }),
        levelField(),
        exactYearsField(yearsBox),
        field("years", "Total years of work experience", yearsBox),
      ];
    },
    validate: () => [atLeast("currentRole", 1, "Add at least one role."), atLeast("industry", 1, "Add at least one domain."),
      exactYearsOk(), inList("years", R.YEARS, "Choose a range from the list.")].every(Boolean),
  },
  skills: {
    title: "Your skills",
    sub: "Add the skills you use at work. Include tools, methods and languages. Use the words from your country — we translate them.",
    render: () => [demoBanner(),
      multiCombo("skills", "Skills", R.SKILLS, {
        placeholder: "Search or type a skill", max: 15,
        hint: "Add at least 3. Choose from the list, or type your own and press Enter.",
        // Suggestions come from all the domains the user chose (from all three domains if none is chosen)
        suggestions: () => {
          const doms = toList(state.data.industry).filter((i) => R.SKILL_SUGGESTIONS[i]);
          return [...new Set((doms.length ? doms : R.DOMAINS).flatMap((i) => R.SKILL_SUGGESTIONS[i]))].slice(0, 10);
        },
      }),
    ],
    validate: () => atLeast("skills", 3, "Add at least 3 skills."),
  },
  credentials: {
    title: "Certifications and awards",
    sub: "Add the certifications and awards that you have. This step is optional. You can skip it.",
    render: () => [
      demoBanner(),
      credentialList({
        name: "certifications", legend: "Certifications", addText: "Add a certification", emptyText: "No certifications added.",
        blank: () => ({ name: "", issuer: "", year: null }), makeRow: certificationRow,
      }),
      credentialList({
        name: "awards", legend: "Awards", addText: "Add an award", emptyText: "No awards added.",
        blank: () => ({ name: "", kind: "", year: null }), makeRow: awardRow,
      }),
    ],
    buttons: () => [h("button", { type: "submit", class: "btn btn-primary", text: "Continue" })],
    validate: () => state.rowChecks.map((c) => c()).every(Boolean),
  },
  translation: {
    title: "Your translated profile",
    sub: "This is how Australian employers will read your experience. Accept the skills that are right. Edit or remove the others. Only accepted skills are shared.",
    render() {
      const wrap = h("div", { class: "field", "data-field": "translation" },
        h("div", { class: "reading", role: "status" }, h("div", { class: "progress-indeterminate", "aria-hidden": "true" }, h("span")), h("p", { text: "Translating your experience…" })),
        h("div", { class: "field-error", id: "translation-error", role: "alert" }));
      loadTranslation(wrap);
      return [wrap];
    },
    validate: () => ((state.data.translation || []).some(SHARED) ? true : (alertBox("Accept at least one skill, so employers can find you."), false)),
  },
  goals: {
    title: "What are you looking for?",
    sub: "We use this to recommend jobs. You can change it at any time.",
    render: () => [
      multiCombo("targetRole", "Target roles", R.ROLES,
        { placeholder: "Search or type a role you want", max: 3, cv: true, hint: "Add up to 3 roles you want to apply for." }),
      choices("targetIndustries", "Target domains", R.DOMAINS, { optional: true, hint: "Choose up to 3.", max: 3 }),
      choices("locations", "Preferred locations", R.LOCATIONS),
      choices("workTypes", "Work type", R.WORK_TYPES),
    ],
    validate: () => [atLeast("targetRole", 1, "Add at least one role you want."), atLeast("locations", 1, "Choose at least one location."), atLeast("workTypes", 1, "Choose at least one work type.")].every(Boolean),
  },
  review: {
    // First time: "Check your answers". A done profile: "Your profile" — the start page of every edit.
    get title() { return state.edit ? "Your profile" : "Check your answers"; },
    get sub() { return state.edit ? "Edit any part of your profile. Then save your changes." : "Make sure everything is correct. Then we find jobs for you."; },
    render() {
      const d = state.data;
      const list = (a) => (toList(a).length ? toList(a).join(", ") : "—");
      const shared = (d.translation || []).filter(SHARED);
      // [step, label, value, field, required]
      const rows = [
        ["cv", "CV", d.cv ? d.cv.name : "No CV", "cv", false],
        ["education", "Qualifications", list(d.qualification), "qualification", true],
        ["education", "Fields of study", list(d.fieldOfStudy), "fieldOfStudy", true],
        ["education", "Countries", list(d.studyCountry), "studyCountry", false],
        ["experience", "Roles", list(d.currentRole), "currentRole", true],
        ["experience", "Domains", list(d.industry), "industry", true],
        ["experience", "Level", d.level || "—", "level", false],
        ["experience", "Exact years", d.yearsExperience != null ? experienceOf(d) : "—", "yearsExperience", false],
        ["experience", "Experience", d.years || "—", "years", true],
        ["skills", "Skills", list(d.skills), "skills", true],
        ["credentials", "Certifications", credNames(d.certifications) || "—", "certifications", false],
        ["credentials", "Awards", credNames(d.awards) || "—", "awards", false],
        ["translation", "Shared skills", shared.length ? `${shared.length}: ${shared.map((s) => s.mapped).join(", ")}` : "—", "translation", true],
        ["goals", "Target roles", list(d.targetRole), "targetRole", true],
        ["goals", "Target domains", list(d.targetIndustries), "targetIndustries", false],
        ["goals", "Locations", list(d.locations), "locations", true],
        ["goals", "Work type", list(d.workTypes), "workTypes", true],
      ];
      return [h("dl", { class: "review-list" }, rows.map(([step, k, v, name, required]) => {
        const missing = required && !filled(name);
        const marker = missing ? h("span", { class: "chip chip-yellow", text: "Missing" })
          : state.detected.has(name) ? h("span", { class: "chip chip-ai", title: "The AI found this in your CV. Check it." }, icon("check"), "From your CV") : null;
        return h("div", { class: `review-row${missing ? " is-missing" : ""}` },
          h("dt", {}, k, marker ? h("span", { class: "field-markers" }, marker) : null), h("dd", { text: v }),
          h("button", { type: "button", class: "legal-link link-btn", "aria-label": `${step === "cv" ? "Change" : "Edit"} ${k}`, text: step === "cv" ? "Change" : "Edit", onclick: () => jump(step) }));
      }))];
    },
    buttons: () => [h("button", { type: "submit", class: "btn btn-primary", text: state.edit ? "Save changes" : "Save and see jobs" })],
    // Every required answer must be there before the save (an updated CV can leave gaps)
    validate: () => (REQUIRED.every(filled) ? true : (alertBox("Some answers are missing. Edit the rows marked “Missing”."), false)),
    next: finish,
  },
};

// ---------- CV reading (poll GET /cv/parse/:id) ----------
async function poll() {
  const myRun = state.run;
  const started = Date.now();
  while (state.run === myRun && state.path[state.index] === "reading") {
    let res;
    try { res = await api.cv.parseStatus(state.parseId); }
    catch (err) { res = { status: "failed", error: err.message }; }
    if (state.run !== myRun || state.path[state.index] !== "reading") return;
    if (res.status === "done") {
      const r = res.result;
      // Replace the fields with what the AI found. Keep the goals, which a CV does not have.
      // A field that the CV does not show stays empty and is flagged "Missing" (Feature 2 AC6).
      // When a done profile gets a new CV, a field that the CV does not show keeps the old answer.
      Object.assign(state.data, r.fields);
      if (!state.edit) for (const k of r.missing || []) state.data[k] = k === "years" ? "" : [];
      // V2: the level, years, certifications and awards. `found` tells which of them the CV showed (R1).
      state.found = r.found && typeof r.found === "object" ? r.found : {};
      state.cvLevels = new Map((Array.isArray(r.skills) ? r.skills : []).filter((x) => x && x.name && Number.isInteger(x.level)).map((x) => [String(x.name).toLowerCase(), x.level]));
      normalizeProfile(state.data);
      state.detected = new Set(r.detected);
      state.missing = new Set(r.missing);
      // The V2 backend names the domain of the CV (one of the 3 domains). `fields.industry` holds up to 2 domains (the strongest first) and `result.domain`
      // is the first of them. The form starts with that one domain. The talent can add another. (The mock backend sends no `domain`.)
      if (R.DOMAINS.includes(r.domain)) {
        state.data.industry = [r.domain];
        state.detected.add("industry");
        state.missing.delete("industry");
      }
      state.data.evidence = r.evidence || [];
      state.sampleLabel = r.sampleLabel || "";
      state.fromCv = true;
      state.data.translation = state.data.translation || [];
      announce("Your CV is read. Check the fields we filled.");
      state.index += 1;
      return render();
    }
    if (res.status === "failed" || Date.now() - started > POLL_LIMIT_MS) {
      state.parseError = res.error || "Reading your CV took too long. Try again, or enter your details yourself.";
      return render();
    }
    await new Promise((r) => setTimeout(r, POLL_MS));
  }
}

// ---------- Translation (POST /profile/translate) ----------
async function loadTranslation(wrap) {
  const myRun = state.run;
  const { cv, evidence, ...profile } = state.data;
  let res;
  try {
    res = await api.profile.translate({ profile, evidence: evidence || [] });
  } catch (err) {
    if (state.run !== myRun) return;
    wrap.querySelector(".reading").replaceWith(h("div", { class: "empty", role: "alert" }, h("p", { text: err.message || "We couldn't translate your experience. Try again." })));
    return;
  }
  if (state.run !== myRun) return;
  state.data.translation = res.skills;
  state.gaps = res.gaps || [];
  // The CV can show a level for a skill (R1). It is the start value when the server set none, or only its default (the level of the
  // evidence, rule F8). A level that the talent changed in this dialog stays. The talent can change it at any time.
  for (const s of state.data.translation) {
    if (s.source !== "skill" || state.levelTouched.has(s.id)) continue;
    const lv = state.cvLevels.get(String(s.original).toLowerCase()) ?? state.cvLevels.get(String(s.mapped).toLowerCase());
    if (lv && (!Number.isInteger(s.level) || s.level === evidenceLevel(s.evidence))) { s.level = lv; levelFromCv.add(s); }
  }

  const listEl = h("ul", { class: "tr-list", "aria-label": "Translated skills" });
  const removedEl = h("div", { class: "tr-removed" });
  const previewSlot = h("div");
  const counter = h("p", { class: "tr-count", role: "status" });
  const acceptAll = h("button", { type: "button", class: "btn btn-secondary btn-sm", onclick: () => {
    state.data.translation.forEach((s) => { if (s.status === "suggested") s.status = "accepted"; });
    repaint();
    announce("All suggested skills accepted.");
  } }, icon("check"), "Accept all");

  function repaint() {
    const all = state.data.translation;
    const visible = all.filter((s) => s.status !== "removed");
    const removed = all.filter((s) => s.status === "removed");
    listEl.replaceChildren(...visible.map((s) => translationCard(s, repaint, () => previewSlot.replaceChildren(previewPanel()))));
    removedEl.replaceChildren(...(removed.length ? [h("p", { class: "hint", text: "Removed (not shared):" }),
      ...removed.map((s) => h("button", { type: "button", class: "choice", "aria-label": `Undo remove ${s.mapped}`,
        onclick: () => { s.status = "suggested"; repaint(); } }, icon("plus"), s.mapped))] : []));
    const n = all.filter(SHARED).length;
    counter.textContent = `${n} of ${visible.length} skills accepted.`;
    acceptAll.disabled = !visible.some((s) => s.status === "suggested");
    previewSlot.replaceChildren(previewPanel());
    body.querySelector(".form-alert")?.remove();
  }

  const content = [
    h("div", { class: "tr-head" }, counter, acceptAll),
    state.data.translation.length ? listEl : h("p", { class: "muted", text: "We found no skills to translate. Go back and add your roles and skills." }),
    removedEl,
    state.gaps.length ? h("div", { class: "tr-gaps" },
      h("h3", { text: "Things Australian employers may ask about" }),
      h("ul", { class: "why" }, state.gaps.map((g) => h("li", { class: "gap" }, icon("alert"), g)))) : null,
    previewSlot,
  ];
  wrap.querySelector(".reading").replaceWith(...content.filter(Boolean));
  repaint();
}

// ---------- File handling ----------
function pickFile(file) {
  clearErrors();
  if (!file) return;
  const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
  if (!CV_TYPES.includes(ext)) { state.file = null; renderFile(); return error("cv", "Use a PDF or DOCX file."); }
  if (file.size > MAX_CV_BYTES) { state.file = null; renderFile(); return error("cv", "The file is larger than 10 MB. Use a smaller file."); }
  state.file = file;
  renderFile();
}
function renderFile() {
  const row = document.getElementById("ob-file");
  const next = document.getElementById("ob-cv-next");
  if (next) next.disabled = !state.file;
  if (!row) return;
  const f = state.file;
  row.replaceChildren(...(f ? [h("div", { class: "file-chip" }, icon("file"),
    h("span", { class: "file-name", text: f.name }), h("span", { class: "hint", text: `${Math.max(1, Math.round(f.size / 1024))} KB` }),
    h("button", { type: "button", class: "btn btn-ghost btn-icon", "aria-label": `Remove ${f.name}`, onclick: () => { state.file = null; document.getElementById("ob-cv").value = ""; renderFile(); } }, icon("x")))] : []));
}

// ---------- Navigation ----------
function go(pathName, index) {
  state.path = PATHS[pathName];
  state.index = index;
  render();
}
// Short paths for a done profile: each edit starts and ends on "Your profile" (review).
// A change to roles, skills or education runs the translation again, so the shared skills stay correct.
const EDIT_PATHS = {
  review: ["review"],
  cv: ["cv", "reading", "translation", "review"],
  education: ["education", "translation", "review"],
  experience: ["experience", "translation", "review"],
  skills: ["skills", "translation", "review"],
  credentials: ["credentials", "review"],
  translation: ["translation", "review"],
  goals: ["goals", "review"],
};
function goPath(path, index) {
  state.path = path;
  state.index = index;
  render();
}
function jump(step) {
  if (state.edit) return goPath(EDIT_PATHS[step], 0);
  state.index = state.path.indexOf(step);
  render();
}
function render() {
  state.run += 1; // a newer render cancels pending polls and requests
  const key = state.path[state.index];
  const step = STEPS[key];
  const n = state.path.length;
  stepLabel.textContent = state.edit ? (n > 1 ? `Edit profile · Step ${state.index + 1} of ${n}` : "Edit profile") : `Step ${state.index + 1} of ${n}`;
  bar.style.width = `${((state.index + 1) / n) * 100}%`;
  const heading = h("h2", { id: "ob-title", tabindex: "-1", text: step.title });
  state.flush = [];
  state.rowChecks = [];
  body.replaceChildren(heading, h("p", { class: "modal-sub", text: step.sub }), ...step.render().filter(Boolean));
  // No "Back" from the reading step while it reads, and none to the reading step.
  // In edit mode the first step goes back to "Your profile".
  const prev = state.path[state.index - 1];
  const back = state.index > 0 && key !== "reading" && prev !== "reading"
    ? h("button", { type: "button", class: "btn btn-ghost", onclick: () => { state.index -= 1; render(); } }, icon("chevron-left"), "Back")
    : state.edit && state.index === 0 && key !== "review"
      ? h("button", { type: "button", class: "btn btn-ghost", onclick: () => goPath(EDIT_PATHS.review, 0) }, icon("chevron-left"), "Back to profile")
      : null;
  const buttons = step.buttons ? step.buttons() : [h("button", { type: "submit", class: "btn btn-primary", text: "Continue" })];
  foot.replaceChildren(h("div", {}, back), h("div", { class: "modal-actions" }, buttons));
  heading.focus();
}
function submit(e) {
  e.preventDefault();
  clearErrors();
  state.flush.forEach((f) => f());
  const step = STEPS[state.path[state.index]];
  if (!step.validate()) return focusFirstError();
  if (step.next) return step.next();
  state.index += 1;
  render();
}
// Save with PATCH /me. On an error, show it in the dialog and keep the answers.
async function save(patch) {
  const buttons = foot.querySelectorAll("button");
  buttons.forEach((b) => (b.disabled = true));
  try {
    await api.me.update(patch);
    return true;
  } catch (err) {
    alertBox(err.message || "We couldn't save your answers. Try again.");
    return false;
  } finally {
    buttons.forEach((b) => (b.disabled = false));
    renderFile();
  }
}

// The profile keeps the CV evidence lines (private to the candidate) so the translation can run again
const toPatch = (onboarding) => {
  const { cv, ...profile } = state.data;
  return { profile, cv: cv || null, onboarding };
};
async function finish() {
  if (!(await save(toPatch("done")))) return;
  state.finished = true;
  dialog.close();
}
// Close before the end: keep the answers as a draft for a new profile.
// For a completed profile, discard the unsaved edits.
async function onClose() {
  state.run += 1;
  if (!state.finished && state.onboarding !== "done") {
    try { await api.me.update(toPatch("dismissed")); } catch { /* keep going */ }
  }
  onDone && onDone();
}

// ---------- Public ----------
let bound = false;
function bind() {
  if (bound) return;
  bound = true;
  dialog = document.getElementById("onboarding");
  body = document.getElementById("obBody");
  foot = document.getElementById("obFoot");
  stepLabel = document.getElementById("obStep");
  bar = document.getElementById("obBar");
  document.getElementById("obForm").addEventListener("submit", submit);
  document.getElementById("obClose").addEventListener("click", () => dialog.close());
  dialog.addEventListener("close", onClose); // Also runs when the user presses Esc
}

/**
 * Open the dialog for the signed-in candidate.
 * @param {object} opts { user, start: "cv" | "questions" | "review" | "translation" | "goals", done }
 * A done profile opens in edit mode (short paths that end on "Your profile").
 * A new profile opens the full step-by-step flow.
 */
export function openOnboarding({ user, start = "cv", done } = {}) {
  bind();
  onDone = done;
  state = {
    data: { ...(user.profile || {}), cv: user.cv || undefined }, onboarding: user.onboarding, alias: user.alias,
    edit: user.onboarding === "done",
    file: null, path: PATHS.skip, index: 0, flush: [], rowChecks: [], run: 0,
    detected: new Set(), missing: new Set(), found: {}, cvLevels: new Map(), levelTouched: new Set(), fromCv: false, sampleLabel: "", parseId: null, parseError: "", gaps: [],
  };
  normalizeProfile(state.data);
  const at = (step) => PATHS.skip.indexOf(step);
  if (state.edit) goPath(EDIT_PATHS[start] || EDIT_PATHS.review, 0); // "questions" → "Your profile"
  else if (start === "questions" || start === "review") go("skip", at("education"));
  else if (start === "translation") go("skip", at("translation"));
  else if (start === "goals") go("skip", at("goals"));
  else go("skip", 0);
  if (!dialog.open) dialog.showModal();
}

// Close the dialog without saving (for example, when the user leaves the page)
export function closeOnboarding() {
  if (dialog?.open) { state.finished = true; onDone = null; dialog.close(); }
}
```
