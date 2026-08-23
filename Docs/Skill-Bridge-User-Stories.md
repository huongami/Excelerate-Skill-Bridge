# FUTURA REMIX HACKATHON â€” SKILL BRIDGE

## MVP User Stories & Acceptance Criteria

**Scope:** the must-have / should-have features committed for the hackathon build (Section 5.1 of the PRD), decomposed into implementation-sized user stories. Each story follows the standard "As a / I want / So that" format with testable acceptance criteria.

**Actor note:** stories tagged **[CANDIDATE]** describe the core skill-translation work, generated once from the candidate's own profile. Stories tagged **[RECRUITER â€” inherits]** reuse that same output against a specific role, rather than re-parsing or re-translating anything.

**Story structure:** All items are user stories and use whole-number IDs. When a story is decomposed from another story, it is placed immediately after its predecessor and explicitly identifies that predecessor. The predecessor remains the broader product requirement; the following stories make it smaller and more precise for implementation and testing.

---

# Epic: CV & Experience Understanding

Before any translation or matching can happen, the system needs a reliable structured picture of who the candidate is and what they've done â€” even when their CV doesn't follow a standard local format. This epic is the foundation the other two epics depend on: if parsing is wrong or incomplete, every downstream skill match inherits that error.

## US-1 CV / Experience Parser [Must-have] [CANDIDATE]

**As a candidate, I want to upload my CV or work history and have it automatically structured into a clear profile, so that I can see my experience the way the system â€” and eventually employers â€” will interpret it.**

### Acceptance Criteria
- Given a candidate uploads a CV (PDF or DOCX), when parsing completes, then they see a structured summary of their roles, employers, durations, and responsibilities.
- Given a CV that does not follow a standard Western resume layout (e.g. different section order, non-English headers), when parsed, then the system still correctly identifies role, duration, and responsibility fields at least 80% of the time on the test sample set.
- Given a field is unclear or missing, when parsing completes, then the candidate is prompted to confirm or complete it, rather than the system silently guessing.
- Given parsing is complete, when the candidate reviews their profile, then they can edit or correct any field before it is used for translation.

---

## US-2 Upload CV [Must] [CANDIDATE]

**Predecessor:** US-1 â€” CV / Experience Parser [Must-have] [CANDIDATE]

**As a** candidate, **I want** to upload my CV, **so that** Skill Bridge can begin building my structured profile.

### Acceptance criteria
- Given I am on profile creation, when I select a supported PDF or DOCX file, then the system accepts it and starts processing.
- Given the file cannot be read or is unsupported, when upload is attempted, then I receive a clear error and can try another file.
- Given processing is in progress, then the UI communicates that state and does not imply parsing has completed.

### Output
`CV document available for parsing`

---

## US-3 Extract Work Experience Entries [Must] [CANDIDATE]

**Predecessor:** US-1 â€” CV / Experience Parser [Must-have] [CANDIDATE]

**As a** candidate, **I want** my work-history entries extracted, **so that** I do not have to manually recreate my CV.

### Acceptance criteria
- Given a readable CV, when parsing completes, then identifiable work-history entries are separated into individual roles.
- Each extracted role can contain employer, role/title, start/end dates or duration, location if present, and responsibility text.
- Information not present in the CV is not silently fabricated.
- Non-standard section order or non-English headers do not by themselves prevent extraction.

### Output
`raw_experience[]`

---

## US-4 Structure Responsibilities by Role [Must] [CANDIDATE]

**Predecessor:** US-1 â€” CV / Experience Parser [Must-have] [CANDIDATE]

**As a** candidate, **I want** responsibilities associated with the correct role, **so that** later skill claims are grounded in the right experience.

### Acceptance criteria
- Given multiple roles are extracted, when responsibilities are structured, then each responsibility is linked to its source role.
- Given the parser cannot confidently associate text with a role, then that content is marked for candidate confirmation rather than assigned silently.
- The original evidence text remains available for downstream explanations.

### Output
`structured_experience[]` with source evidence

---

## US-5 Flag Ambiguous or Missing Fields [Must] [CANDIDATE]

**Predecessor:** US-1 â€” CV / Experience Parser [Must-have] [CANDIDATE]

**As a** candidate, **I want** unclear profile information identified, **so that** I can correct it before Skill Bridge interprets my experience.

### Acceptance criteria
- Given a required/important field is unclear or missing, when parsing finishes, then the field is visibly marked for review.
- The system distinguishes extracted information from information requiring confirmation.
- The system does not fill an ambiguous field as fact without candidate confirmation.

### Output
`review_required_fields[]`

---

## US-6 Review and Correct Parsed Profile [Must] [CANDIDATE]

**Predecessor:** US-1 â€” CV / Experience Parser [Must-have] [CANDIDATE]

**As a** candidate, **I want** to review and edit the parsed profile, **so that** translation uses information I have verified.

### Acceptance criteria
- Given parsing is complete, when I review my profile, then I can edit extracted fields before translation runs.
- Given I save a correction, then downstream translation uses the corrected value.
- The reviewed structured profile becomes the canonical input to Epic 2.

### Output
`candidate_verified_profile`

---

# Epic: Skill Translation

This is the core value engine of Skill Bridge. It takes the structured profile from Epic 1 and answers the central product question: does this candidate's experience â€” regardless of country or industry of origin â€” actually translate into skills a local employer would recognise, and why? Every story here produces an explainable answer, generated once from the candidate's profile.

## US-7 Cross-Border + Cross-Industry Skill Translator [Must-have] [CANDIDATE]

**As a candidate, I want my overseas or cross-industry experience translated into the language used in the Australian job market, so that I understand how my background is likely to be read by local employers and can describe it more confidently myself.**

### Acceptance Criteria
- Given a structured candidate profile, when translation runs, then each role is mapped to one or more local-market equivalent skill terms and shown to the candidate.
- Given the candidate's most recent role is from a different country, when translation runs, then the candidate sees the explicit local-market equivalent job title or function (e.g. "Product Owner (Vietnam) â†’ equivalent to Product Manager, AU market").
- Given the candidate's background is from a different industry than a role they're interested in, when a genuine underlying competency match exists, then the system surfaces and explains it to the candidate (e.g. Business Analyst â†’ Data Analyst, via shared competency "data-informed decision-making").
- Given no reasonable translation exists for part of their experience, when translation runs, then it is omitted from the profile rather than shown as a false match.

## US-8 Identify Competencies from Evidence [Must] [CANDIDATE]

**Predecessor:** US-7 â€” Cross-Border + Cross-Industry Skill Translator [Must-have] [CANDIDATE]

**As a** candidate, **I want** competencies inferred from my verified responsibilities, **so that** my capability is represented beyond my job title.

### Acceptance criteria
- Given a verified responsibility, when analysis runs, then the system may derive one or more competency claims supported by that responsibility.
- Every competency claim retains a reference to the source role/responsibility.
- A competency without supporting candidate evidence is not added as if the candidate possesses it.

### Output
`evidence_backed_competencies[]`

---

## US-9 Translate Cross-Border Role Language [Must] [CANDIDATE]

**Predecessor:** US-7 â€” Cross-Border + Cross-Industry Skill Translator [Must-have] [CANDIDATE]

**As a** candidate with overseas experience, **I want** unfamiliar role language mapped to Australian-market terminology, **so that** local employers can understand the function I performed.

### Acceptance criteria
- Given a role/function from another market, when a defensible Australian-market equivalent exists, then the equivalent is displayed alongside the original.
- The original title is retained; translation does not rewrite the candidate's employment history.
- Given no defensible equivalent exists, then the system does not invent one.

### Output
`cross_border_role_mapping[]`

---

## US-10 Translate Skills into Local-Market Terms [Must] [CANDIDATE]

**Predecessor:** US-7 â€” Cross-Border + Cross-Industry Skill Translator [Must-have] [CANDIDATE]

**As a** candidate, **I want** my evidence-backed competencies expressed using recognisable Australian-market skill terms, **so that** equivalent capability is not hidden by vocabulary differences.

### Acceptance criteria
- Each translated skill is connected to at least one evidence-backed competency.
- The mapping retains the source experience and original competency.
- Unsupported mappings are omitted rather than forced.

### Output
`local_skill_mapping[]`

---

## US-11 Detect Cross-Industry Transfer [Must] [CANDIDATE]

**Predecessor:** US-7 â€” Cross-Border + Cross-Industry Skill Translator [Must-have] [CANDIDATE]

**As a** candidate moving across industries, **I want** genuine transferable competencies identified, **so that** relevant capability is visible even when my previous industry differs from my target industry.

### Acceptance criteria
- Given source and target contexts differ, when the underlying competency is genuinely shared, then the system can surface the translated skill.
- The mapping explains the shared competency connecting the two contexts.
- Similar wording alone is not sufficient evidence of transferability.
- Given no reasonable transfer exists, then no match is shown.

### Output
`cross_industry_skill_mapping[]`

---

## US-12 Preserve Translation Provenance [Must] [CANDIDATE]

**Predecessor:** US-7 â€” Cross-Border + Cross-Industry Skill Translator [Must-have] [CANDIDATE]

**As a** candidate, **I want** every translated skill traceable to my actual experience, **so that** I can understand and challenge the AI's interpretation.

### Acceptance criteria
- Each translated skill stores its source role/responsibility.
- Each translated skill stores the inferred/shared competency used to justify the mapping.
- Candidate-facing and recruiter-facing explanations reference the same underlying translation record.

### Output
`translated_skill_profile` with provenance

---

## US-13 Transferable Skills Highlighter [Must-have] [CANDIDATE]

**As a candidate, I want to see which of my skills are genuinely transferable, with a plain-language reason for each, so that I can present my experience with confidence instead of guessing what's actually relevant.**

### Acceptance Criteria
- Given a completed skill translation, when the candidate views their profile, then each transferable skill is shown with a one-sentence, plain-language justification (not just a label).
- Given a justification is shown, when reviewed, then it references the specific past experience it was derived from (e.g. "Managed a 12-person retail team in Manila â†’ demonstrates team leadership").
- Given the candidate has multiple relevant past roles, when skills are highlighted, then they are grouped by relevance rather than listed as a flat, unordered list.

---

## US-14 Generate Plain-Language Skill Explanation [Must] [CANDIDATE]

**Predecessor:** US-13 â€” Transferable Skills Highlighter [Must-have] [CANDIDATE]

**As a** candidate, **I want** a simple explanation for each transferable skill, **so that** I understand why Skill Bridge believes it transfers.

### Acceptance criteria
- Every displayed transferable skill has a concise plain-language justification.
- The explanation references specific source experience rather than generic statements about the candidate.
- A bare skill label or confidence percentage is not considered an explanation.

### Output
`skill_explanation`

---

## US-15 Group Skills by Relevance [Must] [CANDIDATE]

**Predecessor:** US-13 â€” Transferable Skills Highlighter [Must-have] [CANDIDATE]

**As a** candidate, **I want** translated skills organised meaningfully, **so that** I can understand my strongest transferable areas without reading a flat list.

### Acceptance criteria
- Given multiple translated skills, when the profile is displayed, then skills are grouped or ordered by relevance.
- The grouping does not imply a person-level hiring score.
- Each skill remains independently explainable.

### Output
`candidate_skill_profile_view`

---

## US-16 Inspect Source Evidence [Must] [CANDIDATE]

**Predecessor:** US-13 â€” Transferable Skills Highlighter [Must-have] [CANDIDATE]

**As a** candidate, **I want** to inspect where a translated skill came from, **so that** I can verify the interpretation before employers use it.

### Acceptance criteria
- Given a displayed skill, when I inspect its explanation, then I can see the source role/responsibility used as evidence.
- The displayed source matches the provenance stored during translation.
- The system does not create a new explanation independently of the stored mapping.

---

# Epic: Ranking & Human-Centred Decisioning

Translating skills is only useful if a recruiter can quickly prioritise what matters and stay confidently in control of the final call. This epic takes the profile candidates already built for themselves in Epics 1â€“2 and applies it against a specific role â€” no story here re-parses a CV or re-runs translation; each one consumes, ranks, or presents output generated once, then adds the ranking and human review a hiring decision actually needs.

## US-17 JD-Frequency Skill Ranking [Should-have] [RECRUITER â€” inherits]

**As a recruiter, I want the candidate's already-translated and highlighted skills ranked by how often they appear across similar job descriptions, so that I can prioritise reviewing the most in-demand skills first, without redoing any of the underlying analysis myself.**

### Acceptance Criteria
- Given a candidate's existing translated skill profile (from US-1â€“US-13) and a set of sample job descriptions for the target role, when a skill appears across them, then the system displays how frequently that skill appears (e.g. "appears in 6 of 10 similar JDs").
- Given multiple matched skills, when displayed to the recruiter, then they are sorted from highest to lowest JD frequency by default.
- Given the sample JD set is small (fewer than 5 JDs), when frequency is shown, then the system labels the ranking as "indicative" rather than presenting it as statistically robust.

## US-18 Ingest Target Job Description(s) [Should] [RECRUITER â€” inherits]

**Predecessor:** US-17 â€” JD-Frequency Skill Ranking [Should-have] [RECRUITER â€” inherits]

**As a** recruiter, **I want** to provide a target JD and/or sample JDs, **so that** Skill Bridge can evaluate which skills are relevant to the role.

### Acceptance criteria
- The JD input is processed separately from the candidate's already-generated skill profile.
- Adding a JD does not trigger CV re-parsing or candidate skill re-translation.
- The system extracts/normalises skill terms needed for role-side comparison.

### Output
`target_role_skill_requirements`

---

## US-19 Count Skill Frequency Across Similar JDs [Should] [RECRUITER â€” inherits]

**Predecessor:** US-17 â€” JD-Frequency Skill Ranking [Should-have] [RECRUITER â€” inherits]

**As a** recruiter, **I want** to know how frequently a skill appears across similar JDs, **so that** I can distinguish commonly requested skills from occasional ones.

### Acceptance criteria
- Given a sample JD set, when a candidate skill matches a skill in those JDs, then the number of JDs containing it is counted.
- The UI can express the result as `X of Y similar JDs`.
- Duplicate mentions inside one JD do not incorrectly imply multiple JDs require the skill.

### Output
`jd_skill_frequency`

---

## US-20 Rank Candidate Skills by JD Frequency [Should] [RECRUITER â€” inherits]

**Predecessor:** US-17 â€” JD-Frequency Skill Ranking [Should-have] [RECRUITER â€” inherits]

**As a** recruiter, **I want** matching candidate skills ordered by market/role frequency, **so that** I can review commonly requested skills first.

### Acceptance criteria
- Candidate skills are ranked using the JD-frequency result, not by regenerating the candidate analysis.
- Highest-frequency relevant skills appear first by default.
- Each ranked skill retains its candidate evidence and explanation.

---

## US-21 Label Small-Sample Ranking [Should] [RECRUITER â€” inherits]

**Predecessor:** US-17 â€” JD-Frequency Skill Ranking [Should-have] [RECRUITER â€” inherits]

**As a** recruiter, **I want** weak evidence clearly labelled, **so that** I do not mistake a tiny JD sample for robust market evidence.

### Acceptance criteria
- Given fewer than five JDs are used, when frequency ranking is shown, then it is labelled **Indicative**.
- The number of JDs underlying the frequency remains visible.

---

## US-22 Honest Gap Flagging [Should-have] [CANDIDATE]

**As a candidate, I want to see which skills commonly expected in my target roles I don't yet have evidence for, so that I can address the gap, upskill, or set realistic expectations before I apply.**

### Acceptance Criteria
- Given a candidate profile and a target role or industry, when the gap view is generated, then any commonly expected skill not found in the candidate's profile is listed clearly, separate from their matched skills.
- Given a gap is shown, when the candidate views it, then it is described in plain language, not as a penalty or rejection signal.
- Given a candidate has no notable gaps, when they view this section, then the system explicitly confirms "No major gaps identified" rather than showing nothing.

## US-23 Identify Expected Skills Without Candidate Evidence [Should] [CANDIDATE]

**Predecessor:** US-22 â€” Honest Gap Flagging [Should-have] [CANDIDATE]

**As a** candidate, **I want** expected target-role skills that lack evidence in my profile identified, **so that** I can distinguish genuine gaps from translation problems.

### Acceptance criteria
- Compare target-role skill requirements with the existing translated candidate profile.
- A gap means Skill Bridge found no evidence-backed candidate skill corresponding to the expected skill.
- Lack of evidence is not phrased as proof that the candidate is incapable of the skill.

### Output
`candidate_skill_gaps[]`

---

## US-24 Explain Gaps Neutrally [Should] [CANDIDATE]

**Predecessor:** US-22 â€” Honest Gap Flagging [Should-have] [CANDIDATE]

**As a** candidate, **I want** gaps described neutrally, **so that** I can decide whether to provide evidence, upskill, or adjust expectations.

### Acceptance criteria
- Gaps are displayed separately from matched skills.
- Gap language describes missing evidence/expected capability rather than a rejection or penalty.
- The view does not assign an overall candidate penalty score.

---

## US-25 Confirm When No Major Gaps Are Found [Should] [CANDIDATE]

**Predecessor:** US-22 â€” Honest Gap Flagging [Should-have] [CANDIDATE]

**As a** candidate, **I want** explicit confirmation when no major gaps are identified, **so that** an empty screen is not ambiguous.

### Acceptance criteria
- Given no notable expected skill is missing from the available evidence, then the UI explicitly displays **No major gaps identified**.

---

## US-26 Skill-Level Matching Rate [Must-have] [RECRUITER â€” inherits]

**As a recruiter, I want the candidate's already-translated skill profile shown against my specific role as a per-skill match rate, so that I can act directly on work already done during candidate discovery, without my hiring judgement being replaced by one opaque overall score.**

### Acceptance Criteria
- Given a candidate's existing skill profile and a specific job description, when the recruiter views the match, then no single overall "candidate score" is shown anywhere in the UI.
- Given a completed match, when results are displayed, then each individual skill shows its own match rate or confidence indicator, tied to the justification already generated for the candidate in US-3.
- Given a recruiter hovers or taps on a skill's match rate, when viewed, then the underlying reasoning (source experience + translation logic) is visible, reusing the same explanation the candidate already saw.

## US-27 Compare Existing Candidate Skills with a Specific Role [Must] [RECRUITER â€” inherits]

**Predecessor:** US-26 â€” Skill-Level Matching Rate [Must-have] [RECRUITER â€” inherits]

**As a** recruiter, **I want** the candidate's existing translated skills compared with my role, **so that** I can evaluate relevant capability without rerunning candidate analysis.

### Acceptance criteria
- Input is the existing translated candidate profile plus the target role/JD.
- CV parsing and cross-border/cross-industry translation are not rerun.
- Matching is calculated and presented at individual skill level.

### Output
`role_skill_matches[]`

---

## US-28 Display Per-Skill Match Indicator [Must] [RECRUITER â€” inherits]

**Predecessor:** US-26 â€” Skill-Level Matching Rate [Must-have] [RECRUITER â€” inherits]

**As a** recruiter, **I want** a match indicator for each relevant skill, **so that** I can see where evidence is stronger or weaker without receiving an automated verdict on the person.

### Acceptance criteria
- Each relevant skill can display its own match rate/confidence indicator.
- The indicator is tied to the existing evidence and translation explanation.
- No overall candidate score is calculated or displayed in the UI.

---

## US-29 Reveal Match Reasoning [Must] [RECRUITER â€” inherits]

**Predecessor:** US-26 â€” Skill-Level Matching Rate [Must-have] [RECRUITER â€” inherits]

**As a** recruiter, **I want** to inspect why a skill was matched, **so that** I can judge whether the mapping is credible.

### Acceptance criteria
- Given a skill match, when I inspect it, then I can see source candidate experience plus the translation logic.
- The explanation reuses the same provenance/explanation available to the candidate.
- The recruiter can distinguish candidate evidence from Skill Bridge's interpretation of that evidence.

---

## US-30 Prevent Person-Level Scoring [Must] [RECRUITER â€” inherits]

**Predecessor:** US-26 â€” Skill-Level Matching Rate [Must-have] [RECRUITER â€” inherits]

**As a** recruiter, **I want** the interface to avoid reducing a person to one score, **so that** hiring judgement remains mine.

### Acceptance criteria
- No overall percentage, star rating, grade, ranking number, or equivalent candidate-level score is shown.
- Per-skill indicators are not aggregated into an implicit hiring verdict.
- The UI does not label the candidate automatically as suitable/unsuitable based on the matching engine.

---

## US-31 Human-in-the-Loop Review UI [Must-have] [RECRUITER â€” inherits]

**As a recruiter, I want to review the candidate-generated skill profile and matching output and make my own shortlisting decision, so that the tool supports my judgement instead of making the hiring decision for me.**

### Acceptance Criteria
- Given any candidate match result, when displayed, then there is no "auto-approve" or "auto-reject" action available anywhere in the product.
- Given a recruiter views a match, when they take an action, then the only available actions are recruiter-initiated (e.g. "Shortlist," "Not a fit," "Needs more info") â€” never an automated status change.
- Given the product is demoed, when a judge asks how a hiring decision is made, then the answer is verifiably "the recruiter decides, using the candidate's own translated profile â€” the tool only explains," consistent with what the UI shows.

## US-32 Review Candidate Skill Profile and Role Match [Must] [RECRUITER â€” inherits]

**Predecessor:** US-31 â€” Human-in-the-Loop Review UI [Must-have] [RECRUITER â€” inherits]

**As a** recruiter, **I want** the translated candidate evidence and role-specific matching in one review experience, **so that** I can make an informed decision.

### Acceptance criteria
- The recruiter can review the candidate's translated skills, evidence, explanations, gaps where applicable, and role-specific match indicators.
- Candidate analysis remains traceable to the candidate-generated profile.
- The UI clearly presents information as decision support rather than a decision.

---

## US-33 Provide Recruiter-Initiated Review Actions [Must] [RECRUITER â€” inherits]

**Predecessor:** US-31 â€” Human-in-the-Loop Review UI [Must-have] [RECRUITER â€” inherits]

**As a** recruiter, **I want** to record my own review action, **so that** Skill Bridge supports rather than replaces my hiring workflow.

### Acceptance criteria
- Available actions may include **Shortlist**, **Not a fit**, and **Needs more info**.
- An action only occurs after explicit recruiter input.
- No matching result automatically changes candidate status.

---

## US-34 Prohibit Automated Hire/Reject Decisions [Must] [RECRUITER â€” inherits]

**Predecessor:** US-31 â€” Human-in-the-Loop Review UI [Must-have] [RECRUITER â€” inherits]

**As a** recruiter, **I want** final hiring judgement to remain human-controlled, **so that** Skill Bridge never acts as an autonomous hiring decision-maker.

### Acceptance criteria
- No auto-approve or auto-reject action exists.
- No threshold on a skill match automatically triggers a recruiter action.
- The demo visibly supports the statement: **the recruiter decides; Skill Bridge explains**.

---

---

> **Traceability note:** The original PRD stories remain identifiable as US-1, US-7, US-13, US-17, US-22, US-26, US-31. The stories immediately following each original requirement are its implementation-sized successors and explicitly identify their predecessor. Actor tags continue to show which stories generate the core analysis (candidate) versus which consume it (recruiter).