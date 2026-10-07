# Skill Bridge: Story Breakdown

**Created:** 2026-10-06
**Companion to:** Skill_Bridge_User_Stories.md

## What changed

I reviewed all 44 stories and broke down the 8 that bundled more than one deliverable or hid a technical risk. The 8 parent stories are replaced by 23 sub-stories. The other 36 stories are single deliverables of 1 to 3 points with no hidden unknowns, so they are unchanged.

| Parent story | Why it was broken down | Sub-stories | Points (before → after) |
|---|---|---|---|
| F2-S2 AI Parsing and Form Pre-fill | Text extraction, LLM parsing and UI are separate risks | 3 | 3 → 4 |
| F2-S4 Translated Profile at Information Input | Engine integration, display and the recruiter-safe copy are separate | 3 | 3 → 4 |
| F3-S1 Per-Skill Matching Service | Skill vocabulary, comparison and the summary have different unknowns | 3 | 3 → 5 |
| F4-S1 Review Step and Submit | Review screen, snapshot logic and success screen are separate | 3 | 3 → 4 |
| F5-S1 Anonymization Layer | The filter and its test can be built and checked separately | 2 | 3 → 3 |
| F6-S1 Post a Job | Form, AI skill extraction and seed data are separate | 3 | 3 → 4 |
| F6-S4 Status Updates and Edit Lock | Rules, lock and recruiter controls are separate | 3 | 3 → 4 |
| F7-S7 Premium Recruiter Tools | Three independent premium capabilities | 3 | 5 → 6 |

## Revised totals

| | Before | After |
|---|---|---|
| Stories | 44 | 59 |
| Story points | 109 | 117 |
| Demo slice stories | 24 | 37 |
| Demo slice points | 60 | 67 (about 22 developer-days) |

The extra 8 points are real work that the larger estimates hid (integration, tests and data setup), not new scope. The 3 F7-S7 sub-stories are not part of the demo slice.

**Same conventions as the main file.** Standard Definition of Done applies to every sub-story, and each lists only what it adds. Decisions still open are named with a default to build with, which is an assumption and not an agreed decision.

---

# F2-S2: AI Parsing and Form Pre-fill

### F2-S2a: Extract Text from CV

**As a** candidate, **I want** my CV file read into text, **so that** the AI can analyse it.

**Acceptance criteria**
- Given a PDF or DOCX, when it is processed, then the text is extracted in reading order, with sections kept in sequence.
- Given a multi-column or table layout, then the text is still extracted in a readable order (best effort).
- Given a file with no extractable text, such as a scanned image, then it is reported as unreadable and the candidate goes to the manual-entry fallback (F2-S5). OCR is out of scope.

**Technical tasks**
- [ ] Choose text extraction libraries for PDF and DOCX
- [ ] Normalise whitespace and remove page headers and footers where possible
- [ ] Test with 3 sample CVs, including one with columns

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F2-S1

### F2-S2b: Parse Text into a Structured Profile

**As a** candidate, **I want** my CV's content organised into profile fields, **so that** I don't have to type it.

**Acceptance criteria**
- Given extracted text, when parsed, then the output contains roles, employers, dates, responsibilities, education and skills, and matches the profile schema.
- Given information not in the CV, then the field is left empty and flagged, and never invented.
- Given invalid output, when parsing runs, then the system retries once, then reports a failure (handled by F2-S5).
- Given CV text that contains instructions (for example "ignore previous instructions"), then it is treated as data and does not change the system's behaviour.

**Technical tasks**
- [ ] Define the JSON schema for the profile
- [ ] Write the parsing prompt with low temperature, and add a timeout
- [ ] Validate the output against the schema, with one retry
- [ ] Make sure CV text is never written to logs

**Definition of Done:** standard, plus a prompt-injection test case.
**Priority:** High | **Complexity:** Medium | **Effort:** 2 pts / S | **Demo slice:** Yes
**Dependencies:** Story: F2-S2a. System: LLM API. Data: profile schema.

### F2-S2c: Pre-fill Form with Markers and Progress

**As a** candidate, **I want** to see the fields filled in and know which came from the AI, **so that** I know what to check.

**Acceptance criteria**
- Given parsing in progress, then a progress state is shown (target about 15 seconds for a typical CV).
- Given the result, then the form is pre-filled and each AI-filled field is marked "AI-detected".
- Given the candidate edits a field, then the marker clears for that field (proposed behaviour).

**Technical tasks**
- [ ] Progress and error states
- [ ] Map the parsed JSON to the form fields
- [ ] Track which fields are AI-detected

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F2-S2b, F2-S3

---

# F2-S4: Translated Profile at Information Input

### F2-S4a: Translation Service Wrapper

**As a** candidate, **I want** my experience run through the translation engine, **so that** I get skills an Australian employer recognises.

**Acceptance criteria**
- Given a saved profile with experience items, when translation runs, then the national round MVP engine is called and returns translated skills.
- Given an engine error or timeout, then the candidate still sees their profile and can retry.
- Given the same input, then the same output is returned (low temperature and caching).

**Technical tasks**
- [ ] Put the existing engine behind one service interface, so the design can change later
- [ ] Store the results per experience item
- [ ] Add caching and a timeout

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Medium | **Effort:** 2 pts / S | **Demo slice:** Yes
**Dependencies:** Story: F2-S3. Decision (blocks the output format only): translation design. Default: reuse the national MVP engine as is.

### F2-S4b: Show Translated Profile at Information Input

**As a** candidate, **I want** to see my translated profile when I finish entering my information, **so that** I can see how employers will read it.

**Acceptance criteria**
- Given translation is complete, then the translated profile is shown at this step.
- Given the output, then it contains no personality, suitability or overall quality score.
- Given translation is still running or has failed, then a loading or error state is shown.

**Technical tasks**
- [ ] Display component for the translated profile
- [ ] Loading and error states

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F2-S4a

### F2-S4c: Recruiter-Safe Translated Snapshot

**As a** platform owner, **I want** the translated profile stored apart from the original CV, **so that** recruiters and applications only ever use the translated version.

**Acceptance criteria**
- Given a saved translated profile, then it is stored as a separate record with no original CV fields.
- Given an application, then this record is what is frozen into the application (F4-S1b).
- Given a recruiter view, then it reads only this record, through the anonymization layer.

**Technical tasks**
- [ ] Data model for the translated profile and its versions
- [ ] Migration
- [ ] Read access for the application and recruiter code paths

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F2-S4a

---

# F3-S1: Per-Skill Matching Service

### F3-S1a: Normalise Job Required Skills

**As a** candidate, **I want** a job's skills described in the same terms as my profile, **so that** the comparison is fair.

**Acceptance criteria**
- Given a job's required skills, then they are stored in the same vocabulary as candidate skills.
- Given a skill written differently (for example "MS Excel" and "Excel"), then both map to one skill through a simple alias list.
- Given an unknown skill, then it is kept as typed.

**Technical tasks**
- [ ] Seed a skill vocabulary and alias list for the demo industries
- [ ] Normalisation function
- [ ] Unit tests

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F6-S1. Decision (non-blocking): how job skills are produced. Default: AI-extracted and editable.

### F3-S1b: Per-Skill Comparison with Reasons

**As a** candidate, **I want** each required skill marked as a match, partial match or gap with a reason, **so that** I understand where I fit.

**Acceptance criteria**
- Given a translated profile and a job's required skills, when the match runs, then each required skill is returned as match, partial or gap.
- Given each result, then it includes a plain-language reason that refers to the candidate's evidence (original skill and mapped skill).
- Given the same input, then the result is the same.
- Given any input, then the alias, origin and other protected attributes are never used.

**Technical tasks**
- [ ] Reuse the national MVP matcher
- [ ] Define the result contract: skill, status, evidence, reason
- [ ] Unit tests with seeded jobs and sample profiles, including a gap and a partial match

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Medium (High if the national MVP matcher cannot be reused) | **Effort:** 3 pts / S-M | **Demo slice:** Yes
**Dependencies:** Story: F3-S1a, F2-S4c. Decision (non-blocking): matching formula. Default: the national MVP matcher.

### F3-S1c: Match Summary and Replaceable Interface

**As a** candidate, **I want** a simple summary of my match, **so that** I can scan jobs quickly.

**Acceptance criteria**
- Given per-skill results, then a summary percentage is shown as required skills covered divided by required skills, with the list of gaps.
- Given the matcher, then it sits behind one interface so the formula can change without changing the code that calls it.
- Given a job with no required skills, then no percentage is shown.

**Technical tasks**
- [ ] Summary function
- [ ] Interface and contract
- [ ] Short note on the placeholder formula

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F3-S1b. Decision (non-blocking): per-skill versus aggregate percentage. Default: coverage percentage as a summary only.

---

# F4-S1: Review Step and Submit Application

### F4-S1a: Review Screen

**As a** candidate, **I want** to see exactly what I'm sending before I apply, **so that** I stay in control.

**Acceptance criteria**
- Given the apply action, when clicked, then a review step shows the translated profile that will be sent.
- Given the review step, then the original CV is neither shown nor sent.
- Given the candidate wants to change something, then they can go back to edit before submitting.

**Technical tasks**
- [ ] Review screen reading the translated snapshot record (F2-S4c)
- [ ] Back to edit navigation

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F2-S4c, F3-S4

### F4-S1b: Submit with Frozen Snapshot and Guards

**As a** candidate, **I want** my application recorded exactly as I reviewed it, **so that** nothing changes after I submit.

**Acceptance criteria**
- Given the review step, when the candidate submits, then an application is created with status Applied and a frozen copy of the translated profile.
- Given a job the candidate already applied to, or a closed job, then the system blocks it with a clear message.
- Given a double click on submit, then only one application is created.

**Technical tasks**
- [ ] Application table with the snapshot stored on it
- [ ] Unique constraint on job and candidate
- [ ] Single transaction for the create
- [ ] Tests for duplicate and closed-job cases

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Medium | **Effort:** 2 pts / S | **Demo slice:** Yes
**Dependencies:** Story: F4-S1a. Data: application table.

### F4-S1c: Success Screen with Tracking Link

**As a** candidate, **I want** confirmation that my application went through, **so that** I know it worked.

**Acceptance criteria**
- Given a successful submit, then a success screen prompts the candidate to track the status and links to the tracking view for this application.
- Given a failed submit, then an error is shown, never the success screen.

**Technical tasks**
- [ ] Success screen
- [ ] Link to the tracking view (F4-S3)

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F4-S1b, F4-S3

---

# F5-S1: Anonymization Layer

### F5-S1a: Recruiter-Safe Candidate Projection

**As a** recruiter, **I want** candidates shown without identifying details, **so that** I judge on skills alone.

**Acceptance criteria**
- Given any recruiter-facing candidate response, then it is built from an allowlist: alias, translated role, translated skills and the match.
- Given any recruiter response, then name, origin, ethnicity, nationality, gender and contact details are never included, and the original CV is never returned.
- Given free text in the translated profile, then emails and phone numbers are removed (proposed pattern check).

**Technical tasks**
- [ ] Projection function used by every recruiter candidate endpoint
- [ ] Pattern check for emails and phone numbers in free text
- [ ] Unit tests

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Medium | **Effort:** 2 pts / S | **Demo slice:** Yes
**Dependencies:** Story: F1-S2, F2-S4c. Decision (non-blocking): whether to also hide employer and university names, age and photos. Default: not in the allowlist.

### F5-S1b: Automated Personal-Data Test

**As a** platform owner, **I want** a test that catches personal data leaking to recruiters, **so that** the anonymity promise is verified.

**Acceptance criteria**
- Given a seeded candidate with known personal values, when every recruiter endpoint is called, then the test fails if any of those values appear in any response.
- Given the build, then this test runs on every build.

**Technical tasks**
- [ ] Seed a candidate with known personal values
- [ ] Test that loops over all recruiter endpoints
- [ ] Add it to the build pipeline

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F5-S1a

---

# F6-S1: Post a Job

### F6-S1a: Post-a-Job Form and Validation

**As a** recruiter, **I want** to post a job with a target and a close date, **so that** candidates can find it.

**Acceptance criteria**
- Given a signed-in recruiter, when they post a job with a title, description, target number of applicants and close date, then the job is created as Open.
- Given a close date in the past or a target that isn't a positive number, then the form shows a clear error.

**Technical tasks**
- [ ] Form and validation
- [ ] Job table and create endpoint

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F1-S4

### F6-S1b: AI Required-Skill Extraction

**As a** recruiter, **I want** the required skills drawn from my description, **so that** matching works without extra typing.

**Acceptance criteria**
- Given a job description, when the recruiter saves it, then required skills are proposed.
- Given the proposed skills, then the recruiter can edit, add or remove them before the job goes live.
- Given extraction fails, then the recruiter can enter the skills manually.

**Technical tasks**
- [ ] Extraction prompt with a schema and validation
- [ ] Editable skills list
- [ ] Manual fallback

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Medium | **Effort:** 2 pts / S | **Demo slice:** Yes
**Dependencies:** Story: F6-S1a. System: LLM API. Decision (non-blocking): AI-extracted or recruiter-tagged. Default: AI-extracted and editable.

### F6-S1c: Seed Demo Jobs

**As a** team member, **I want** realistic jobs ready for the demo, **so that** recommendations and badges can be shown.

**Acceptance criteria**
- Given the seed script, when it runs, then 10 to 15 synthetic jobs are created across 2 to 3 industries, each with required skills and a target.
- Given the seeded jobs, then close dates vary so the demo shows open, closing within a week, and closed jobs.
- Given the script runs twice, then it creates no duplicates.

**Technical tasks**
- [ ] Seed data file
- [ ] Idempotent seed script

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F6-S1b

---

# F6-S4: Status Updates and Edit Lock

### F6-S4a: Status Transition Rules and History

**As a** recruiter, **I want** only valid status moves, **so that** the process stays consistent.

**Acceptance criteria**
- Given an application, when the recruiter moves it, then only these transitions are accepted: Applied to Review, Review to Interview, Interview to Accepted or Rejected, Accepted to Offer, Offer to Confirmed, and Offer to Rejected when the candidate rejects it. Anything else returns a clear error.
- Given any change, then it is logged with who made it and when.
- Given any application, then the system never changes its status on its own.

**Technical tasks**
- [ ] Transition table in one place
- [ ] Status history table
- [ ] Tests for every valid and invalid pair

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Medium | **Effort:** 2 pts / S | **Demo slice:** Yes
**Dependencies:** Story: F6-S3. Data: application status history.

### F6-S4b: Edit Lock on Review

**As a** candidate, **I want** to know when I can no longer edit, **so that** I'm not surprised.

**Acceptance criteria**
- Given the recruiter moves an application to Review, then the candidate's edit window locks.
- Given a locked application, when the candidate tries to edit, then the server rejects it with a clear message (see F4-S4).
- Given an edit already in progress, then it is rejected at save time with an explanation.

**Technical tasks**
- [ ] Lock check on the edit endpoint
- [ ] Version check for edits in progress
- [ ] Test the race case

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F6-S4a, F4-S4

### F6-S4c: Recruiter Status Controls

**As a** recruiter, **I want** clear controls for the next step, **so that** I move candidates through quickly and safely.

**Acceptance criteria**
- Given an application in the applications view, then only the allowed next actions are shown.
- Given a Reject action, then the recruiter confirms before it is applied.
- Given a status change, then the new status is shown immediately.

**Technical tasks**
- [ ] Action buttons driven by the transition table
- [ ] Confirmation for rejection
- [ ] Immediate UI update

**Definition of Done:** standard.
**Priority:** High | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** Yes
**Dependencies:** Story: F6-S4a

---

# F7-S7: Premium Recruiter Tools

### F7-S7a: Full Candidate List

**As a** premium recruiter, **I want** the full candidate list, **so that** I'm not limited to the top N.

**Acceptance criteria**
- Given a premium recruiter, then the shortlist shows the full list.
- Given a basic recruiter, then the shortlist shows only the top N, with an upgrade prompt.
- Given any request, then the plan is checked on the server.

**Technical tasks**
- [ ] Plan check in the shortlist endpoint
- [ ] Upgrade prompt

**Definition of Done:** standard.
**Priority:** Low | **Complexity:** Low | **Effort:** 1 pt / XS | **Demo slice:** No
**Dependencies:** Story: F7-S6, F5-S2

### F7-S7b: Compare Two Profiles

**As a** premium recruiter, **I want** two candidates side by side, **so that** I can assess them on their skills.

**Acceptance criteria**
- Given two candidates for the same job, when the recruiter compares them, then a side-by-side per-skill view is shown.
- Given the comparison, then there is no combined score and no ranking of the two people, and both appear by alias.
- Given a basic recruiter, then the action shows an upgrade prompt.

**Technical tasks**
- [ ] Selection of two candidates
- [ ] Comparison view reusing the matcher output
- [ ] Access tests for basic and premium

**Definition of Done:** standard.
**Priority:** Low | **Complexity:** Medium | **Effort:** 3 pts / S-M | **Demo slice:** No
**Dependencies:** Story: F7-S6, F5-S3, F3-S1b

### F7-S7c: Direct Contact Through the Platform

**As a** premium recruiter, **I want** to contact a candidate who didn't apply, **so that** I can approach strong matches.

**Acceptance criteria**
- Given a premium recruiter, when they contact a candidate, then the request goes through the platform, a Contacted record is created, and contact details stay hidden.
- Given a basic recruiter, then the action is blocked with an upgrade prompt.
- Given the candidate's side (accept or decline and what they see), then it is not part of this story.

**Technical tasks**
- [ ] Contact request record with the Contacted status
- [ ] Plan check on the server

**Definition of Done:** standard.
**Priority:** Low | **Complexity:** Low | **Effort:** 2 pts / S | **Demo slice:** No
**Dependencies:** Story: F7-S6, F5-S3. Decision (blocks the candidate side only): how the candidate accepts or declines, and whether candidates opt in to appear in recommendations.

---

## Updated implementation order (changes only)

- **Candidate input:** F2-S2a, then F2-S2b, then F2-S2c, with F2-S4a to S4c after F2-S3.
- **Matching:** F6-S1a to S1c first, then F3-S1a to S1c.
- **Application loop:** F4-S1a to S1c, F5-S1a and S1b, and F6-S4a to S4c.
- **Premium:** F7-S7a to S7c after F7-S6.

All other stories keep their position in the main file.
