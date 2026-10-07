# 08 — Quality Assurance, Acceptance Criteria & End-to-End Test Matrix

Source: [`app/spec/01_REQUIREMENTS_TRACEABILITY.md`](01_REQUIREMENTS_TRACEABILITY.md) through [`app/spec/07_TASK_BREAKDOWN.md`](07_TASK_BREAKDOWN.md)
Document standard: Strict test criteria, end-to-end journey validation, edge cases, and compliance verification.

---

## 1. Quality Assurance Framework

Skill Bridge 2.0 must pass 100% of the verification checkpoints defined in this document before production deployment. No requirement (`REQ-*`) may be considered complete without passing its corresponding acceptance test.

### Acceptance Hierarchy
```
Level 1: Unit & Formula Verification (Math correctness, zero formula tampering)
Level 2: API Contract Verification (Schemas, status codes, payload shapes)
Level 3: Component & State Verification (Design tokens, a11y, state stores)
Level 4: End-to-End User Journey Verification (Interactive flows, lifecycle persistence)
Level 5: Visual, Privacy & Compliance Verification (PII redaction, contrast, responsiveness)
```

---

## 2. Requirements Acceptance Matrix

### 2.1 Global Architecture & Design (`REQ-G01` to `REQ-G06`)

| Req ID | Test Procedure | Expected Outcome | Status Check |
| :--- | :--- | :--- | :--- |
| `REQ-G01` | Inspect browser network tab and application shell. Verify Next.js App Router on port 3000, Python Product API on port 8095. | Port 3000 serves App Router HTML/RSC; `/api/*` proxies to 8095 seamlessly without CORS errors. | [ ] PASS |
| `REQ-G02` | Audit computed CSS styles on all elements across all viewports. | Background matches rice paper `#FDFCF8`, text matches loam `#2C2C24`, accents use moss `#5D7052`, terracotta `#C18C5D`, timber `#DED8CF`. Noise overlay visible at 3.5% opacity. Zero sharp 90° corners on cards/buttons. | [ ] PASS |
| `REQ-G03` | Inspect typography using Chrome DevTools font inspection. | Display headings render in `Fraunces` serif; UI/body text renders in `Nunito` sans; metrics/chips/ANZSCO codes render in `JetBrains Mono`. | [ ] PASS |
| `REQ-G04` | Execute audit for non-English strings across entire codebase and rendered DOM. | 100% of user-facing strings, tooltips, buttons, labels, and documentation are in Australian/UK English. | [ ] PASS |
| `REQ-G05` | Query SQLite database at `product_api/var/app.db`. | Database contains exactly 461 real jobs from `australian_jobs.json` and 320 real candidates from `australian_candidates.json`. Zero placeholder data. | [ ] PASS |
| `REQ-G06` | Call `/api/scores/formula/*` with test candidate and job pairs. | Outputs match `intelligence_engine/` formulas 1 to 6 bit-for-bit. No client-side recalculation or altered weights. | [ ] PASS |

---

### 2.2 Landing & Authentication (`REQ-L01` to `REQ-A07`)

| Req ID | Test Procedure | Expected Outcome | Status Check |
| :--- | :--- | :--- | :--- |
| `REQ-L01` | Navigate to `/` as unauthenticated user. | Landing page renders Hero with live platform statistics (total jobs, active candidates, median match), value propositions, and role CTA cards. | [ ] PASS |
| `REQ-L02` | Click "Sign In" and "Sign Up" links on landing page. | Routes to `/signin` and `/signup` with role selector (Job Seeker / Employer). | [ ] PASS |
| `REQ-A01` | At `/signup/seeker`, upload a PDF/DOCX/TXT resume file. | Extraction engine triggers with animated parsing progress, extracting Full Name, Email, Phone, Experience, Education, and Skills. | [ ] PASS |
| `REQ-A02` | Review parsed resume data on `/signup/seeker/review`. | All extracted fields are editable. Extracted skills display an "AI" badge. Seeker can confirm, edit, or delete items. | [ ] PASS |
| `REQ-A03` | Attempt to submit registration without checking "I agree to Terms & Conditions". | Submit button remains disabled or triggers validation alert: "You must accept the Terms and Conditions to proceed". | [ ] PASS |
| `REQ-A04` | Click the "Terms and Conditions" hyperlink. | Pop-up modal opens cleanly displaying the full 8-section legal agreement without navigating away from the signup page. Close button dismisses modal. | [ ] PASS |
| `REQ-A05` | Click "Continue with Google" on `/signin` or `/signup/seeker`. | Redirects to RFC 7636 PKCE local authorization endpoint, returns authorization code, exchanges token, and logs in user without external Google dependencies. | [ ] PASS |
| `REQ-A06` | Log in via Google account with no CV uploaded yet. | User is redirected to `/seeker` showing an empty-state screen with a prominent circular **+** button inviting CV upload. | [ ] PASS |
| `REQ-A07` | Navigate to Seeker profile setup or `/seeker/account`. | Seeker can choose or customize their public **Alias** (e.g., "SilverKangaroo84"). System validates that HR views ONLY display this Alias, never the legal name. | [ ] PASS |

---

### 2.3 Job Seeker Portal (`REQ-S01` to `REQ-S27`)

| Req ID | Test Procedure | Expected Outcome | Status Check |
| :--- | :--- | :--- | :--- |
| `REQ-S01` | Enter keywords into search bar at `/seeker`. | Search bar features debounced input (300ms) with search icon, clear button, and immediate feed filtering. | [ ] PASS |
| `REQ-S02` | Observe default order of job cards in `/seeker`. | Jobs are sorted descending by Formula 5 FRS★ (suitability score). | [ ] PASS |
| `REQ-S03` | Inspect metric badge on top-right of job card. | Overall suitability score gauge displayed prominently (0–100) with color coding (Green $\ge 75$, Amber 50–74, Slate $< 50$). | [ ] PASS |
| `REQ-S04` | Inspect job card text content. | Short description is clean, informative, and strictly truncated to $\le 160$ characters with ellipsis ("..."). | [ ] PASS |
| `REQ-S05` | Inspect ANZSCO match indicator on card. | Displays Formula 1 SMF score as "ANZSCO Match: XX%" with matching unit code. | [ ] PASS |
| `REQ-S06` | Inspect skill gap indicator on card. | Displays gap severity level (Formula 2 GSI) and estimated months to close (e.g., "Skill Gap: Moderate • ~2.5 mos"). | [ ] PASS |
| `REQ-S07` | Inspect posting date badge on card. | Displays human relative date calibrated against reference date (e.g., "Posted 3 days ago", "1 week ago"). | [ ] PASS |
| `REQ-S08` | Click on any job card. | Opens `/seeker/jobs/[id]` detail view with breadcrumbs, full job overview, and analytical projections. | [ ] PASS |
| `REQ-S09` | Inspect Match Percentage Projection chart in detail view. | Interactive line chart renders Formula 1 progression over time ($SMF(t)$), projecting readiness improvement. | [ ] PASS |
| `REQ-S10` | Inspect Skill Gap Reduction chart in detail view. | Interactive line/area chart renders Formula 2 gap reduction over time ($GSI(t)$), demonstrating trajectory to zero deficit. | [ ] PASS |
| `REQ-S11` | Read plain-English explanation card below charts. | Contextual summary explains why the candidate fits, highlights key matching competencies, and outlines specific missing skills. | [ ] PASS |
| `REQ-S12` | Click "Apply for Role" button in job detail view. | Opens confirmation drawer, records application in database with initial status `submitted`, and updates button to "Applied". | [ ] PASS |
| `REQ-S13` | Click "Ignore" button on job card in feed. | Job card animates out (opacity/scale down), is immediately removed from feed view, and toast displays "Job removed from feed" with "Undo" action. | [ ] PASS |
| `REQ-S14` | Click "Save to Favourites" button on job card. | Bookmark icon fills, count increments, job is added to `/seeker/saved`, and toast confirms "Saved to favourites". | [ ] PASS |
| `REQ-S15` | Click "Report Job" button on job card. | Modal opens with report reason dropdown (Misleading, Expired, Discriminatory, Spam) and optional text note. Submitting logs report to database. | [ ] PASS |
| `REQ-S16` | Trigger behavioural feedback: Save 2 jobs from an employer, ignore 3 jobs from another employer. | Jobs from saved employer receive $+10\%$ affinity boost in feed; jobs from ignored employer receive $-25\%$ demotion penalty. Reported job is hidden. | [ ] PASS |
| `REQ-S17` | Click "Ignore" from job detail view. | User is redirected back to `/seeker` feed with the job marked as ignored. | [ ] PASS |
| `REQ-S18` | Use search filters (ANZSCO sector, location, gap difficulty, minimum score). | Feed filters dynamically in real-time without page reload. | [ ] PASS |
| `REQ-S19` | Inspect left sidebar navigation on desktop and mobile drawer. | Left sidebar is sticky, collapsible, containing Navigation links (Feed, Saved, Applications, Compare) and Account links (Profile, CV, Skills). | [ ] PASS |
| `REQ-S20` | Navigate to `/seeker/account`. | User can view and update personal contact information, public alias, and notification preferences. | [ ] PASS |
| `REQ-S21` | Navigate to `/seeker/account/cv`. | User can preview current CV text, upload a new version, and view extracted summary diffs. | [ ] PASS |
| `REQ-S22` | Navigate to `/seeker/account/skills`. | Lists all skills categorized by domain. Seeker can add new skills or adjust proficiency levels. | [ ] PASS |
| `REQ-S23` | Inspect AI-extracted skills in skills view. | Skills extracted by AI carry an "AI Suggested" badge. Seeker can click "Confirm" to verify or "Edit/Remove". | [ ] PASS |
| `REQ-S24` | Navigate to `/seeker/saved`. | Displays grid of all saved favourite jobs with unsave and apply quick actions. | [ ] PASS |
| `REQ-S25` | Navigate to `/seeker/applications`. | Lists all active and past applications with current status badges, employer details, and application dates. | [ ] PASS |
| `REQ-S26` | Inspect application card in `/seeker/applications`. | Visual interactive 8-stage timeline bar displays current progress checkpoint: `Submitted` → `CV scanning` → `Under review` → `Shortlisted` → `Interview` → `Final assessment` → `Offer` → `Hired`. | [ ] PASS |
| `REQ-S27` | Select 2 to 4 jobs and click "Compare Roles" (`/seeker/compare`). | Renders multi-job comparison dashboard with overlaid spider-web (radar) chart comparing match, gap, salary, and requirements + Formula 3 proximity delta. | [ ] PASS |

---

### 2.4 Recruiter / HR Portal (`REQ-H01` to `REQ-H12`)

| Req ID | Test Procedure | Expected Outcome | Status Check |
| :--- | :--- | :--- | :--- |
| `REQ-H01` | At `/signup/hr`, sign up with an optional Job Description (upload file or paste text). | Extraction engine extracts Title, ANZSCO code, Requirements, Salary Range, and Experience level. | [ ] PASS |
| `REQ-H02` | Sign up as HR without uploading a JD. | HR lands on `/hr` homepage displaying an empty state with a prominent circular **+** button inviting them to add their first JD. | [ ] PASS |
| `REQ-H03` | Navigate to `/hr` dashboard. | Top KPI section displays 5 operational cards: Total Jobs, Active, Expired, Hired Candidates, and Rejected. | [ ] PASS |
| `REQ-H04` | Navigate to `/hr/jobs`. | Displays table/cards of all managed vacancies with columns: Job Title, Company, Short Description, Posted Date, Appearances (impressions), Views (clicks), and Applicants count. | [ ] PASS |
| `REQ-H05` | Trigger seeker interactions on a job (seeker views card, clicks detail, applies). | Real-time database metrics update: Appearances increments on feed load, Views increments on detail open, Applicants increments on apply. | [ ] PASS |
| `REQ-H06` | Inspect HR left sidebar navigation. | Left navigation contains links to Dashboard, My Jobs, Candidate Shortlist, Job Editor, and Company Account Settings. | [ ] PASS |
| `REQ-H07` | Navigate to `/hr/account`. | Recruiter can update company profile, industry, office location, logo, and recruiter personal details. | [ ] PASS |
| `REQ-H08` | Open `/hr/jobs/[id]/edit`. | Recruiter can edit job description, adjust AI-extracted requirements, add must-have/nice-to-have skills, and publish updates. | [ ] PASS |
| `REQ-H09` | Navigate to `/hr/candidates`. | Displays candidate board sorted by Formula 6 TSS score. Each card shows candidate **Alias** (zero PII), Target Title, Experience, ANZSCO Match %, Skill Gap, Overall Score, and Status. | [x] PASS |
| `REQ-H10` | Click candidate card on shortlist board. | Card expands accordion to reveal PII-redacted profile (skills breakdown, education, anonymized employment history). Legal name, email, and phone are strictly redacted. | [x] PASS |
| `REQ-H11` | In expanded candidate view, click lifecycle action buttons ("Advance to Interview", "Send Offer", "Reject"). | Application status updates in database and reflects immediately on both the HR board and the Seeker's 8-stage timeline. | [x] PASS |
| `REQ-H12` | Select 2 to 4 candidates and click "Compare Candidates" (`/hr/compare`). | Displays multi-candidate comparison dashboard with overlaid spider-web (radar) chart across skills, experience, ANZSCO alignment, and Formula 4 Head-to-Head delta. | [x] PASS |

---

## 3. End-to-End User Journey Checklists

### Journey 1: Job Seeker End-to-End Flow
```
[ ] Step 1: Open http://localhost:3000/
    - Verify Hero section with live job count (> 400), seeker count (> 300).
    - Verify "Find Your Capability Alignment" call to action.
[ ] Step 2: Click "Sign Up as Job Seeker" -> /signup/seeker
    - Upload sample resume from `data/real_resumes_dataset.csv` or sample CV file.
    - Verify extraction stage: name, email, skills extracted.
    - Check "I agree to Terms & Conditions" checkbox.
    - Click "Terms and Conditions" modal link -> verify full 8-section legal text pop-up -> close modal.
    - Submit form -> redirected to alias selection -> select "AzureEchidna42".
[ ] Step 3: Enter Seeker Feed (/seeker)
    - Verify jobs ranked by Formula 5 FRS★ score.
    - Test search input with debounced keyword query (e.g., "Data Engineer").
    - Test filter chip (e.g., "Minimal Gap").
[ ] Step 4: Card Actions
    - Click "Save" on Job #1 -> verify favourite icon updates and toast appears.
    - Click "Ignore" on Job #2 -> verify card animates out; click "Undo" -> card returns.
    - Click "Report" on Job #3 -> select "Expired listing" -> submit -> card is hidden.
[ ] Step 5: Detail View & Projections (/seeker/jobs/[id])
    - Click on Job #1.
    - Verify Recharts line chart for Match % Projection ($SMF(t)$).
    - Verify Recharts line chart for Skill Gap Reduction ($GSI(t)$).
    - Verify plain-English analytical explanation card.
    - Click "Apply for Role" -> verify application state changes to `submitted`.
[ ] Step 6: Application Tracker (/seeker/applications)
    - Open Applications tab from left sidebar.
    - Verify Job #1 is listed with 8-stage timeline bar with checkpoint at `Submitted`.
[ ] Step 7: Multi-Job Compare (/seeker/compare)
    - Select Job #1 and Job #4 -> click "Compare Roles".
    - Verify overlaid spider-web radar chart displaying both roles simultaneously.
[ ] Step 8: Skills AI-Correction (/seeker/account/skills)
    - Navigate to Skills view via sidebar.
    - Verify skills with "AI Suggested" badges. Click "Confirm" -> badge transforms to "Verified".
```

---

### Journey 2: Protocol Google Sign-In & Empty State Flow
```
[ ] Step 1: Open /signin -> Click "Continue with Google".
[ ] Step 2: Complete mock OAuth2 PKCE authorization flow.
[ ] Step 3: Land on /seeker as a new user with no CV uploaded.
    - Verify empty state illustration / message: "No CV uploaded yet".
    - Verify prominent circular **+** button is displayed.
[ ] Step 4: Click circular **+** button -> modal / upload drawer opens.
[ ] Step 5: Upload resume -> parse -> select alias -> feed populates with ranked vacancies.
```

---

### Journey 3: Recruiter / HR End-to-End Flow
```
[ ] Step 1: Open /signup/hr -> register without JD.
[ ] Step 2: Land on /hr dashboard.
    - Verify empty state message: "No active vacancies posted".
    - Verify prominent circular **+ Add Job** button is displayed.
[ ] Step 3: Click circular **+** button -> add a Job Description (paste text).
    - Extracted requirements and ANZSCO unit code displayed. Save job.
[ ] Step 4: Verify HR KPI Dashboard (/hr)
    - Total Jobs = 1, Active = 1, Expired = 0, Hired = 0, Rejected = 0.
[ ] Step 5: Navigate to Managed Jobs (/hr/jobs)
    - Verify job is listed with Appearances = 0, Views = 0, Applicants = 0.
[ ] Step 6: Simulate Seeker activity on that job (view & apply).
    - Refresh /hr/jobs -> verify Appearances, Views, and Applicants counters incremented.
[x] Step 7: Navigate to Candidate Shortlist (/hr/candidates)
    - Verify applicants listed sorted by Formula 6 TSS score.
    - Verify PII protection: legal name and email are REDACTED; only candidate Alias is visible.
[x] Step 8: Expand Candidate Card
    - Review skills, experience, and ANZSCO alignment.
    - Click "Advance to Shortlisted" -> status updates.
    - Click "Schedule Interview" -> status updates to `interview`.
[x] Step 9: Multi-Candidate Compare (/hr/compare)
    - Select 2 applicants -> click "Compare Candidates".
    - Verify overlaid radar chart comparing skills and experience across both applicants.
[ ] Step 10: Switch to Seeker view -> verify 8-stage timeline bar now shows `Interview` checkpoint active!
```

---

## 4. Edge Case & Failure Mode Matrix

| Scenario | Input Condition | Expected System Behavior |
| :--- | :--- | :--- |
| **Long Job Descriptions** | Job description exceeds 2,000 characters | Card cleanly truncates text to $\le 160$ chars with ellipsis; detail view displays full formatted text with expandable sections. |
| **Zero Skill Matches** | Candidate has 0 overlapping skills with job | Formula 1 SMF outputs 0.0%; Formula 2 GSI outputs 100.0%; UI handles gracefully with "Foundational Transition Needed" tag without division by zero. |
| **Missing Salary Data** | Schema A jobs with null `salary_min` | System applies ANZSCO benchmark median with label "Estimated market range (ANZSCO benchmark)". |
| **PII Leakage Prevention** | HR inspects DOM or network response | Network response for `/api/hr/candidates` strips `legal_name`, `email`, `phone`, and `address`. Only `alias`, `anonymized_experience`, and `skills` are sent. |
| **Network Disconnection** | Offline API or 500 error | Next.js displays warm wabi-sabi error card with retry button; no blank screen or raw crash dumps. |
| **Rapid Filter Changes** | User types rapidly in search box | Debounce (300ms) prevents query storms; previous pending requests are cancelled via `AbortController`. |
| **Ignore Undo Timeout** | Seeker ignores card, waits 6 seconds | Undo toast dismisses after 5s; card removal is permanently committed to behavioural preferences database. |
| **Report Threshold** | 3 distinct seekers report the same job | Job status automatically switches to `under_review`; removed from public seeker feed pending HR re-verification. |

---

## 5. UI/UX Pro Max & Accessibility Audit Checklist

```
Visual & Design Integrity:
[ ] Zero 90° corners on cards, badges, and buttons (radii conform to spec).
[ ] Palette matches rice paper (#FDFCF8), loam (#2C2C24), moss (#5D7052), terracotta (#C18C5D), timber (#DED8CF).
[ ] Paper noise texture overlay present at 3.5% opacity with multiply blend mode.
[ ] No generic emojis used for UI controls (100% Lucide React SVG icons).

Accessibility (WCAG 2.1 AA):
[ ] All body text meets minimum contrast ratio of 4.5:1 against background.
[ ] Large text (headings $\ge 24$px) meets minimum contrast ratio of 3.0:1.
[ ] Interactive elements have visible focus rings (`focus-visible:ring-2 ring-moss-500`).
[ ] All touch targets on mobile viewports meet minimum dimensions of 44x44px.
[ ] `prefers-reduced-motion` media query respected (disables blob float animations and smooth transitions).
[ ] Screen reader labels (`aria-label`) present on icon-only buttons (Save, Ignore, Report, Close).

Responsive Viewports:
[ ] 375px (Mobile Portrait): Single-column layout, bottom bar / hamburger drawer, horizontal scroll on charts with fallback summary.
[ ] 768px (Tablet): Responsive 2-column grid, compact sidebar.
[ ] 1440px (Desktop): Two-column detail view, sticky navigation, full radar and dual line charts rendered with crisp vectors.
```
