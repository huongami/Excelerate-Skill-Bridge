**FUTURA REMIX HACKATHON — SKILL BRIDGE**

**MVP User Stories & Acceptance Criteria**

*Scope: the 7 must-have / should-have features committed for the hackathon build (Section 5.1 of the PRD). Each story follows the standard "As a / I want / So that" format with testable acceptance criteria.*

> *Actor note: stories tagged \[CANDIDATE\] describe the core skill-translation work, generated once from the candidate's own profile. Stories tagged \[RECRUITER — inherits\] reuse that same output against a specific role, rather than re-parsing or re-translating anything.*

**Epic: CV & Experience Understanding**

*Before any translation or matching can happen, the system needs a reliable structured picture of who the candidate is and what they've done — even when their CV doesn't follow a standard local format. This epic is the foundation the other two epics depend on: if parsing is wrong or incomplete, every downstream skill match inherits that error.*

**US-1 CV / Experience Parser** *\[Must-have\]* **\[CANDIDATE\]**

> *As a candidate, I want to upload my CV or work history and have it automatically structured into a clear profile, so that I can see my experience the way the system — and eventually employers — will interpret it.*

**Acceptance Criteria:**

-   Given a candidate uploads a CV (PDF or DOCX), when parsing completes, then they see a structured summary of their roles, employers, durations, and responsibilities.

-   Given a CV that does not follow a standard Western resume layout (e.g. different section order, non-English headers), when parsed, then the system still correctly identifies role, duration, and responsibility fields at least 80% of the time on the test sample set.

-   Given a field is unclear or missing, when parsing completes, then the candidate is prompted to confirm or complete it, rather than the system silently guessing.

-   Given parsing is complete, when the candidate reviews their profile, then they can edit or correct any field before it is used for translation.

**Epic: Skill Translation**

*This is the core value engine of Skill Bridge. It takes the structured profile from Epic 1 and answers the central product question: does this candidate's experience — regardless of country or industry of origin — actually translate into skills a local employer would recognise, and why? Every story here produces an explainable answer, generated once from the candidate's profile.*

**US-2 Cross-Border + Cross-Industry Skill Translator** *\[Must-have\]* **\[CANDIDATE\]**

> *As a candidate, I want my overseas or cross-industry experience translated into the language used in the Australian job market, so that I understand how my background is likely to be read by local employers and can describe it more confidently myself.*

**Acceptance Criteria:**

-   Given a structured candidate profile, when translation runs, then each role is mapped to one or more local-market equivalent skill terms and shown to the candidate.

-   Given the candidate's most recent role is from a different country, when translation runs, then the candidate sees the explicit local-market equivalent job title or function (e.g. "Product Owner (Vietnam) → equivalent to Product Manager, AU market").

-   Given the candidate's background is from a different industry than a role they're interested in, when a genuine underlying competency match exists, then the system surfaces and explains it to the candidate (e.g. Business Analyst → Data Analyst, via shared competency "data-informed decision-making").

-   Given no reasonable translation exists for part of their experience, when translation runs, then it is omitted from the profile rather than shown as a false match.

**US-3 Transferable Skills Highlighter** *\[Must-have\]* **\[CANDIDATE\]**

> *As a candidate, I want to see which of my skills are genuinely transferable, with a plain-language reason for each, so that I can present my experience with confidence instead of guessing what's actually relevant.*

**Acceptance Criteria:**

-   Given a completed skill translation, when the candidate views their profile, then each transferable skill is shown with a one-sentence, plain-language justification (not just a label).

-   Given a justification is shown, when reviewed, then it references the specific past experience it was derived from (e.g. "Managed a 12-person retail team in Manila → demonstrates team leadership").

-   Given the candidate has multiple relevant past roles, when skills are highlighted, then they are grouped by relevance rather than listed as a flat, unordered list.

**Epic: Ranking & Human-Centred Decisioning**

*Translating skills is only useful if a recruiter can quickly prioritise what matters and stay confidently in control of the final call. This epic takes the profile candidates already built for themselves in Epics 1–2 and applies it against a specific role — no story here re-parses a CV or re-runs translation; each one consumes, ranks, or presents output generated once, then adds the ranking and human review a hiring decision actually needs.*

**US-4 JD-Frequency Skill Ranking** *\[Should-have\]* **\[RECRUITER — inherits\]**

> *As a recruiter, I want the candidate's already-translated and highlighted skills ranked by how often they appear across similar job descriptions, so that I can prioritise reviewing the most in-demand skills first, without redoing any of the underlying analysis myself.*

**Acceptance Criteria:**

-   Given a candidate's existing translated skill profile (from US-1–US-3) and a set of sample job descriptions for the target role, when a skill appears across them, then the system displays how frequently that skill appears (e.g. "appears in 6 of 10 similar JDs").

-   Given multiple matched skills, when displayed to the recruiter, then they are sorted from highest to lowest JD frequency by default.

-   Given the sample JD set is small (fewer than 5 JDs), when frequency is shown, then the system labels the ranking as "indicative" rather than presenting it as statistically robust.

**US-5 Honest Gap Flagging** *\[Should-have\]* **\[CANDIDATE\]**

> *As a candidate, I want to see which skills commonly expected in my target roles I don't yet have evidence for, so that I can address the gap, upskill, or set realistic expectations before I apply.*

**Acceptance Criteria:**

-   Given a candidate profile and a target role or industry, when the gap view is generated, then any commonly expected skill not found in the candidate's profile is listed clearly, separate from their matched skills.

-   Given a gap is shown, when the candidate views it, then it is described in plain language, not as a penalty or rejection signal.

-   Given a candidate has no notable gaps, when they view this section, then the system explicitly confirms "No major gaps identified" rather than showing nothing.

**US-6 Skill-Level Matching Rate** *\[Must-have\]* **\[RECRUITER — inherits\]**

> *As a recruiter, I want the candidate's already-translated skill profile shown against my specific role as a per-skill match rate, so that I can act directly on work already done during candidate discovery, without my hiring judgement being replaced by one opaque overall score.*

**Acceptance Criteria:**

-   Given a candidate's existing skill profile and a specific job description, when the recruiter views the match, then no single overall "candidate score" is shown anywhere in the UI.

-   Given a completed match, when results are displayed, then each individual skill shows its own match rate or confidence indicator, tied to the justification already generated for the candidate in US-3.

-   Given a recruiter hovers or taps on a skill's match rate, when viewed, then the underlying reasoning (source experience + translation logic) is visible, reusing the same explanation the candidate already saw.

**US-7 Human-in-the-Loop Review UI** *\[Must-have\]* **\[RECRUITER — inherits\]**

> *As a recruiter, I want to review the candidate-generated skill profile and matching output and make my own shortlisting decision, so that the tool supports my judgement instead of making the hiring decision for me.*

**Acceptance Criteria:**

-   Given any candidate match result, when displayed, then there is no "auto-approve" or "auto-reject" action available anywhere in the product.

-   Given a recruiter views a match, when they take an action, then the only available actions are recruiter-initiated (e.g. "Shortlist," "Not a fit," "Needs more info") — never an automated status change.

-   Given the product is demoed, when a judge asks how a hiring decision is made, then the answer is verifiably "the recruiter decides, using the candidate's own translated profile — the tool only explains," consistent with what the UI shows.

*Note: Story numbering (US-1 to US-7) and epic grouping match Section 5.1 of the Skill Bridge PRD for traceability. Actor tags show which stories generate the core analysis (candidate) versus which consume it (recruiter).*
