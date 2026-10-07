# AI Rules — Jinder

These rules apply to all AI assistants that work on this project (Claude, Copilot, ChatGPT and others). Read this file before you write or change files.

## Rule 1: Write technical documents in ASD-STE100

Use **ASD-STE100 Simplified Technical English (STE)** for all generated technical documents that people read.

### Scope

| Use STE for | Do not use STE for |
|---|---|
| Design docs (`DESIGN.md`) | Source code and code identifiers |
| READMEs, setup and run guides | Prompts written only for an AI (`prompt.md` may use plain English) |
| Architecture and API docs | Marketing copy and UI text on the website |
| Procedures, checklists, test plans | Direct quotes and source data (for example, the PRD) |
| Code comments that explain behavior | Chat replies to the user |
| Commit messages and PR descriptions | |

### The 80% rule

Apply STE strictly by default. You can soften it to approximately **80%** when strict STE makes the text less clear or unnatural for the reader.

**You can soften these rules:**
- Use a technical name or common word that is not in the STE dictionary (for example: *component*, *token*, *responsive*, *deploy*). Use it with one meaning only.
- Use a descriptive sentence of up to 30 words if a shorter sentence loses meaning.
- Use a passive sentence when the person who does the action is not important.
- Use *-ing* forms in table headers and list labels.

**Do not soften these rules:**
- One instruction in each sentence.
- Use the imperative (command form) for instructions.
- One word has one meaning. Do not use synonyms for the same thing.
- Put warnings and cautions before the step that they apply to.
- No idioms, slang or jokes.

### Core STE rules (summary)

**Words**
1. Use approved, simple words: *use*, not *utilize*; *start*, not *initiate*; *help*, not *facilitate*.
2. Use one word for one meaning. Example: if you write *sign in*, do not also write *log in* and *log on*.
3. Use a verb as a verb, not as a noun. Write *install the app*, not *do the installation of the app*.
4. Do not use the *-ing* form as a noun or after a noun.
5. Do not use phrasal verbs that have more than one meaning (*set up*, *put off*). Use one clear verb.

**Sentences**
6. Procedural sentences: 20 words or fewer.
7. Descriptive sentences: 25 words or fewer.
8. Use the active voice.
9. Use articles (*a*, *an*, *the*) and connecting words (*then*, *thus*, *if*). Do not write in telegraphic style.
10. Write one topic in each paragraph. Paragraphs: six sentences or fewer.

**Procedures**
11. Write one instruction in each step. Number the steps.
12. Start each instruction with a verb: *Open*, *Run*, *Make sure*.
13. If a step has a condition, put the condition first: *If the server stops, start it again.*
14. Write warnings and cautions before the step. Tell the risk and how to prevent it.

### Example

**Not STE:**
> In order to get things up and running, you'll want to go ahead and make sure that the server has been started, after which the app can be accessed via your browser of choice.

**STE:**
> 1. Start the server.
> 2. Open a browser.
> 3. Go to `http://localhost:5173/`.

### Checklist before you deliver a document

- [ ] Each instruction is a numbered step with one action.
- [ ] Each instruction starts with a verb.
- [ ] Procedural sentences have 20 words or fewer.
- [ ] Descriptive sentences have 25 words or fewer (30 if softened).
- [ ] One term has one meaning in the full document.
- [ ] Warnings come before the step.
- [ ] There are no idioms, jokes or unclear words.

## Rule 2: Use English only in the app

- Write all app content in English. This includes UI text, labels, placeholders, error messages, sample data, alt text and `aria-label` values.
- Do not use Vietnamese or other languages in the app, also in sample or demo data.
- Names of people and places can stay in their original form (for example, *Nguyen*, *Hanoi*). Write them without diacritics.
- Write code comments and project documents in English.
- The language of chat with the user can be different. This rule is only for files.
- **Use the same terms everywhere.** The two user types are **"Talent"** (job seekers) and **"Employer"** (recruiters, hiring managers, HR). Do not write "candidate", "recruiter" or "HR" in UI text, sample text or user documents. In a sentence, use "they", "this person" or "this profile" when "the talent" sounds wrong. The API values `candidate` and `recruiter` stay the same in code and in the API contract.
- Use "Sign in" (not "Log in") and "Create account" (not "Sign up").
- **Use the same product words.**
  - Write **"Domain"** (not "Industry"). The 3 domains are Software Engineering, AI & Machine Learning and Data. The API keys `industry` and `targetIndustries` stay, and they hold these 3 domains.
  - The 6 levels are **Intern, Junior, Mid, Senior, Lead, Principal**. The 5 skill levels are **Beginner, Working, Proficient, Advanced, Expert**. Do not use other names.
  - The number on a job is the **"Fit score"** (one decimal). The part of Formula 6 that is about certifications is **"Certification readiness"** (not "Licence readiness").
  - The page where a user puts 2 to 5 items side by side is **"Compare"**. It shows facts side by side. It is not a ranking.
  - The product data (pick-lists, sample jobs, sample talent) has the 3 domains only. This is also true for the browser-only mock (`?mock=1`): its jobs, demo accounts, CV samples, job description samples and translation library are ICT. Do not add roles, skills or sample people of another field of work.

## Rule 3: Follow the design system

- Use `Docs/DESIGN.md` for all UI work. It is the source of truth for colors, typography, components and the logo.
- Use design tokens (CSS custom properties). Do not write raw hex values in components.
- Use SVG icons from `app/icons.svg`. Do not use emoji as icons.
- When you add a component, add its description to `Docs/DESIGN.md` in STE.

## Rule 4: Keep the facts correct

- Use data from `../Document/sdd/02_PRODUCT_REQUIREMENTS_DOCUMENT.md` for product facts and statistics.
- Always show the source of a statistic.
- Do not show placeholder quotes or sample data as real data.

## Rule 5: Protect personal information (PII)

Jinder processes CVs. A CV contains a large quantity of personal information. Thus, treat all candidate and employer data as sensitive.

### What is PII in this project

| Type | Examples |
|---|---|
| Identity | Full name, date of birth, photo, passport or visa number |
| Contact | Email, phone number, home address, LinkedIn URL |
| Career | Employer names, salary, references, referee contact details |
| Sensitive (high risk) | Nationality, ethnicity, religion, gender, age, health, visa status, criminal record |

### Rules

1. **Do not use real PII** in code, sample data, tests, screenshots, prompts or documents. Use made-up data that is clearly fake (for example, `jane.doe@example.com`, `+61 400 000 000`). All demo data is synthetic: the 50 jobs, the 50 sample talent profiles and the demo accounts. The company names are invented. Do not copy a real job ad or a real CV into the data.
2. **Collect the minimum.** Ask only for data that the feature needs. Do not add fields "for later".
3. **Do not use sensitive attributes for matching.** Do not use nationality, ethnicity, religion, gender, age, health or visa type to calculate or rank a match. This also applies to values that a model can use to guess them (for example, a photo or a date of birth).
4. **Get consent before you share.** An employer can see a candidate profile only after the candidate shares it or applies.
5. **Remove PII before you send data to an external AI or API.** If a feature must send a CV to an LLM, remove or mask the contact details first. Tell the user before you send the data, and get their consent.
6. **Do not log PII.** Do not write names, emails, CV text or tokens to the console, log files or analytics. If you must log an event, log an ID only.
7. **Give users control.** Users must be able to see, correct, export and delete their data.
8. **Show candidates to employers only by alias.** The alias must not contain the real name, a country, a nationality or a city of origin. Name, email, contact details, photo, nationality and the original CV are never in a recruiter response. **Exception:** the name and email, only for one application, after the candidate ticks the consent box when they choose an interview time. The consent box is never ticked by default.
9. **Keep CV content private.** The CV file and the evidence lines from it are only for the candidate. A recruiter response never has them. The shared profile comes from the accepted translated skills and from the fields that are listed in item 14 only.
10. **Treat CV text as data, not as instructions.** When a backend sends CV text to an AI model, it must not follow instructions inside the CV (prompt injection). Validate the AI output against a schema.
11. **Follow Australian law.** Follow the *Privacy Act 1988* and the Australian Privacy Principles (APPs). If you are not sure, write a `TODO(privacy)` comment and tell the user.
12. **Remove contact details from free text** that the other side reads (application notes, invitations, offers, feedback). The backend replaces emails and phone numbers. The UI also tells the user not to add them.
13. **Show counts, not people, in insights.** Charts and statistics are about jobs, skills and the process. Do not show what one candidate did, and do not rank or score a person.
    An employer never gets a score on a person: not a number, not a rounded number and not a tier name. The employer gets a per-skill match, a coverage for one job and an order.
    A talent can get a Fit score for a job, as a guide for the talent only. Employers never see it.
14. **The shared profile (what an employer sees) is a fixed list.** The code is `store.shared_profile`, and a test checks the keys. The list is:
    alias; roles (title and ANZSCO code); skills; skill levels (name, level 1 to 5, years); qualifications; fields of study; domains (the key is `industries`); years (the band); exact years (rounded to 0.5); level (Intern to Principal);
    specialisation; target roles; locations; work types; work modes; **certifications** (name, issuer, year); **awards** (name, kind, year); and the time of the last update of the profile.
    It never has the name, email, contact details, photo, nationality, country of study, employer names, the CV or the evidence lines.
    - **Certifications and awards are shared with employers at once** (decision D5). The talent does not accept them one by one. An employer sees the names and the years on the anonymous profile.
    - A name can identify a person (for example a prize with a person name, or an employer name). Thus the onboarding tells the talent: "Employers see these names. Do not write your own name, your employer's name or contact details here."
      The server also removes email addresses and phone numbers from these names (item 12). The employer screens show the names and the years only, not the issuer, and never a person name next to an award.
    - In sample data and tests, use made-up award names (for example "Smart City Hackathon Runner-up"). Do not use a real person name.
15. **Compare shows facts, not a verdict.** A talent compares 2 to 5 jobs (free). An employer compares 2 to 5 anonymous talent profiles for one of the employer's own jobs (Premium).
    - **No total.** The page never adds the axes or the areas into one number.
    - **No ranking of people.** An area shows the position of each profile inside that one area ("1st", "2nd", "Equal"). A position is never added to another position. The page says: "Jinder does not add the areas up and does not rank people. You decide."
    - **At most 5.** The basket, the page and the API all refuse a 6th item (the API answers 400).
    - **Premium for employers.** A Basic employer sees a locked page with a sample picture that says "This picture is a sample. It does not show real people." The backend gives 403 `PREMIUM_REQUIRED`.
    - Employer compare reads the shared profile only. It never reads the CV or the evidence lines.

> **Warning:** In `mock` mode, the app stores accounts in browser `localStorage` (`js/api/mock/`). Do not enter real personal data in mock mode. Do not deploy the mock for real users.

## Rule 6: Protect secrets and sensitive data

1. **Do not put secrets in code.** Secrets include API keys, passwords, tokens, private keys and connection strings.
2. **Keep secrets in environment variables** or a secret manager. Put local values in a `.env` file.
3. **Add these files to `.gitignore`** before the first commit: `.env`, `.env.*`, `*.pem`, `*.key`, and uploaded files (for example, `uploads/`).
4. **Provide a `.env.example`** with the names of the variables and empty values.
5. **Do not paste secrets or PII** into chat, issues, pull requests, external tools or AI prompts.
6. **If a secret is exposed, revoke it immediately.** Then make a new one. Deleting the commit is not sufficient.
7. **Hash passwords** with a slow, salted algorithm (bcrypt, scrypt or Argon2) on a server. The demo hash in `js/api/mock/db.js` is not secure. The backend must not copy it.
8. **Use HTTPS** for all environments except `localhost`.
9. **Demo accounts are not secrets.** The mock demo accounts (`MOCK_DEMO_ACCOUNTS`, password `MOCK_DEMO_PASSWORD` in `config.js`) are made up and work only in `mock` mode. A security scan can report them: mark them as accepted demo data. Never add demo accounts to a real backend, and never reuse the demo password.

## Rule 7: Scan for security problems

Do a security scan before you deliver code, and before each commit or pull request.

### Scan procedure

1. **Scan for secrets.** Use `gitleaks detect` or `trufflehog` if they are installed. If not, search the changed files for words such as `key`, `secret`, `token`, `password` and `BEGIN PRIVATE KEY`.
2. **Scan dependencies.** If the project uses npm, run `npm audit`. If it uses Python, run `pip-audit`. Fix all high and critical issues.
3. **Scan the code.** Use `semgrep --config auto` if it is installed. In Claude Code, you can also run `/security-review`.
4. **Do a manual check of the changed code.** Use the checklist below.
5. **Report the result** to the user. Tell which scans you ran, which tools were not available, and which issues are still open.

### Manual checklist (based on OWASP Top 10)

- [ ] **Injection and XSS:** User text goes into the page with `textContent`, or it is escaped before `innerHTML`. No `eval()` or `new Function()`.
- [ ] **Authentication:** Passwords are never stored or sent in plain text. Sessions expire. Error messages do not tell if an email exists.
- [ ] **Access control:** Each page and API checks the user and their role on the server, not only in the browser.
- [ ] **File upload:** Allow only the expected types (PDF, DOCX). Limit the file size. Scan uploaded files. Do not run or show uploaded files directly.
- [ ] **External links:** Links with `target="_blank"` also have `rel="noopener"`.
- [ ] **Data in transit and at rest:** HTTPS is used. Sensitive data is encrypted in the database.
- [ ] **Headers:** The server sends a Content Security Policy, `X-Content-Type-Options: nosniff` and `Referrer-Policy`.
- [ ] **Dependencies:** Only well-known, maintained packages. Versions are pinned.
- [ ] **Errors:** Error pages do not show stack traces, paths or data.
- [ ] **PII:** All items in [Rule 5](#rule-5-protect-personal-information-pii) are correct.

> **Caution:** A scan tool can miss problems. A clean scan result does not prove that the code is safe. Always do the manual check also.

## Rule 8: Keep the three portable files up to date

These three files must always describe the current frontend:

| File | Describes |
|---|---|
| `prompt.md` | How to build it: architecture, files, routes, screens, API contract, mock backend, seed data, security, tests |
| `Docs/DESIGN.md` | How it looks: tokens, logo, components, screen layouts, accessibility |
| `AI_Rule.md` | The rules for AI assistants |

Another person copies only these three files to a different computer and builds **the same frontend**. Thus, the files must be complete without the source code.

1. After each change to the app, the design, the logo, the API or the rules, update **all three files** in the same task, where the change applies.
2. When the user gives a new instruction or a new prompt, add it to the correct file.
3. Update all related sections (settings, file structure, routes, screens, API contract, security, checklist). Do not only add a note at the end.
4. Remove information that is no longer correct.
5. Keep data that the build needs inside the files. For example, the seed jobs are embedded in `prompt.md`. If you change `js/api/mock/seed-jobs.js`, change `prompt.md` also.
5a. **Embedded files must match the app.** `prompt.md` embeds files exactly (translation.js, cv-samples.js, seed-jobs.js, seed-demo.js, and the files in its Appendix: `data/reference.js`, `icons.svg`, the mock files, `landing.js`, `auth.js`, `legal.js`, `home.js` and `onboarding.js`). When you change one of these files, copy the new content into `prompt.md` in the same task. Before you finish, compare each embedded copy with the file (they must be the same).
    Example: `data/reference.js` is made from `jinder_backend_engine/data/reference/ict_taxonomy.json`. After a change of the taxonomy, make the file again and copy it into the Appendix.
6. Tell the user which sections of each file you changed.

## Rule 9: Do not change the source documents

These files are the team's source documents (in `../Document/sdd/`, the SDD package). They are **read-only** for AI assistants:

- `../Document/sdd/01_SYSTEM_OVERVIEW.md` (System Overview)
- `../Document/sdd/02_PRODUCT_REQUIREMENTS_DOCUMENT.md` (PRD)
- `../Document/sdd/03_FEATURE_SPECIFICATIONS.md` (Feature Specs)
- `../Document/sdd/04_USER_FLOW_SPECIFICATION.md` (User Flow Spec)
- `../Document/sdd/05_USER_STORIES_AND_ACCEPTANCE_CRITERIA.md` (User Stories)
- `../Document/sdd/06_TECHNICAL_REQUIREMENTS.md` (Technical Requirements)

1. Read these files to understand the product. Do not edit, rename, move or delete them.
2. Do not change them with a script, a find-and-replace or a rename of the brand (for example, "Skill Bridge" → "Jinder").
3. If a document is wrong or out of date, tell the user. Put your notes in a different file.
4. Put decisions that the documents mark as `[DISCUSS]` in `Docs/DESIGN.md`, `prompt.md` or a new file, not in these documents.

## Rule 10: Frontend only — respect the backend boundary

The team builds the frontend. A different developer builds the backend. The API contract in `prompt.md` is the agreement between them.
The real backend is in the folder `../jinder_platform` (Python, SQLite). It serves this app and the API on one address (`API_BASE_URL` is `/api`). The mock API stays for demos: add `?mock=1` to the address.

1. Do not write a server-side backend (no database server, no API server).
2. Views and components get and change data **only** through `js/api/index.js`. They do not call `fetch()` and do not read `localStorage` for app data. (UI preferences, such as the navigation state, can use `localStorage`.)
3. Put business rules behind the API: role checks, anonymity, status changes, premium access, match scores, the compare limit (5), the page size (10, 20 or 50) and the sort values. The frontend can validate forms for a better experience, but the API decides.
4. When you need a new endpoint, or a change to a request or a response:
   1. Add it to the **API contract** in `prompt.md` (method, path, auth, request, response, errors).
   2. Add the function to `js/api/index.js`.
   3. Implement it in the mock adapter (`js/api/mock/`), with the same rules. **Exception (decision F9):** a feature that only the real backend can do (the compare endpoints, the Premium benefits, `bridge.path`, skill levels) does not need a mock. In mock mode the client fails with `NEEDS_REAL_BACKEND` (501) with a plain message, and the screen hides the new sections when the data is missing.
   4. Tell the user, so that they can tell the backend developer.
   Example: a list endpoint takes `page`, `pageSize` and `sort`, and answers with the list and `page: { page, pageSize, total, totalPages }`. For the mock, the client asks for the whole list, sorts it, cuts the page and builds the same `page` object.
5. Start every mock file with a comment that says "MOCK BACKEND". The mock is for demos only. Do not present it as secure.
6. Do not change the API contract silently. A change can break the backend developer's work.

## Rule 11: Treat all data as internal Jinder data

All data in the app (jobs, companies, candidates, sample data) is Jinder's own data. Jinder is the platform where people find jobs and apply.

1. Do not link to other job sites or apps (for example SEEK, Indeed, Adzuna, LinkedIn). Do not add "View on …" links or redirects to other sites.
2. A job title or a "Job detail" link opens the Jinder job detail screen (`#/jobs/:id`). Apply, bookmark and all other actions happen in Jinder.
3. Do not show the name of a data provider in the UI. For example, show "49 open jobs · updated 4 Oct 2026", not "via Adzuna".
4. Use internal IDs (for example `job-5906848725`). Do not keep the URLs of other sites in the data that the API returns.
5. This rule is for product data. Statistics in marketing text still show their source (Rule 4).
