**FUTURA REMIX HACKATHON**

**Jinder**

*Product Vision, Goal & Requirements Document*

Track 1 — Future of Work and International Talent

*How might we use AI, data and digital technology to help international
students and skilled migrants access meaningful career opportunities,
while helping Australian employers identify, develop and retain diverse
talent?*

Team: \[Team name\] — Nicolas (Product/PO), Huong (Technical Build),
Thuyen (Marketing/Design)

Date: 23 August 2026

**1. Product Vision**

> ***A world where a skill is recognised for what it is — regardless of
> which country, industry, or job title it was built in — so that no
> qualified person is filtered out, and no employer is left short of the
> talent standing right in front of them.***

Australia is not short on talent. It hosts over 680,000 international
students, yet 69% of Australian employers still report difficulty
finding skilled people. The gap is not scarcity — it is translation.
Skills earned overseas, or in a different industry, are invisible to the
systems and people meant to evaluate them.

Skill Bridge exists to close that translation gap. We believe the future
of hiring is not about scoring candidates, but about making the skills
that already exist — visible, comparable, and trustworthy — to the
humans who make hiring decisions.

**2. Product Goal**

**2.1 Primary Goal (Hackathon Scope)**

Build a working prototype that translates a candidate's cross-border and
cross-industry experience into skills an Australian employer can
immediately recognise as relevant — supporting, not replacing, the
recruiter's decision.

**2.2 Target User**

-   **Primary user (profile creation):** International students and
    skilled migrants, who use the tool directly to see their own
    experience translated, highlighted, and gap-checked against the
    Australian market — this is where the core skill-translation work
    happens (see PRD Section 5.1, Epics 1–2).

-   **Primary user (decision support):** Hiring managers / recruiters at
    Australian SMEs and mid-size companies, who consume the candidate's
    already-translated profile against a specific role, rank and review
    it, and make the final hiring call. They feel the 69%
    skills-shortage pain most acutely and have the least internal
    capacity to solve it themselves.

*Skill Bridge is deliberately a shared-engine product: the analysis is
generated once, by the candidate, and reused — never recreated — by the
recruiter. This is why the MVP has two primary users rather than one,
even though the business problem it is scoped to solve (the 69% employer
skills shortage) sits on the recruiter's side.*

**2.3 Success Criteria for the Hackathon**

-   A demoable flow: upload a candidate CV + a job description → receive
    a ranked, explained skill match.

-   At least one cross-border AND one cross-industry translation shown
    live (e.g. Product Owner ↔ Marketing Executive).

-   Every recommendation is explainable in plain language — no black-box
    score.

-   Judges can articulate, unprompted, why this is a two-sided solution
    (talent + employer) and why it is realistic to build further.

**2.4 Goal Statement**

> *For Australian SME recruiters who cannot tell which international or
> cross-industry candidates are actually qualified, Skill Bridge is a
> decision-support tool that translates experience into recognisable,
> ranked, and explained skill matches — unlike keyword-based ATS
> filters, which discard qualified candidates before a human ever sees
> their real capability.*

**3. Problem Context & Evidence**

|                                                                                          |                                                |                                                                    |
|------------------------------------------------------------------------------------------|------------------------------------------------|--------------------------------------------------------------------|
| **Data point**                                                                           | **Source**                                     | **Why it matters**                                                 |
| 69% of Australian employers report difficulty finding skilled talent                     | ManpowerGroup, 2024                            | Confirms the shortage is perceived as real by employers            |
| 92% of tech executives believe AI capability will be essential within 5 years            | KPMG Global Tech Report, 2026                  | Employers are raising the bar on skill signalling, not lowering it |
| 680,582 international students in Australia (Jan–May 2026)                               | Australian Government Dept. of Education, 2026 | A large, visible, underused talent pool already exists             |
| Higher education enrolments +2% YoY, but overall international student numbers -6.9% YoY | Australian Government Dept. of Education, 2026 | Signals a possible drop-off between study and employment outcomes  |

**Root cause**

Employers named "identifying transferable skills" and "evaluating
international experience and credentials" as explicit barriers. This is
not a lack of talent — it is a failure to recognise the skills that are
already present, because they arrive in an unfamiliar format: a foreign
job title, a different industry's vocabulary, or a CV structure the
local ATS was never built to parse.

**4. Stakeholders**

|                                                                             |                                                           |                                                                                                                            |
|-----------------------------------------------------------------------------|-----------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------|
| **Stakeholder**                                                             | **Role in the problem**                                   | **Value received from Skill Bridge**                                                                                       |
| Hiring managers / recruiters (primary user — decision support)              | Screen candidates but cannot verify transferable skills   | Faster, explainable shortlisting using the candidate's own translated profile; fewer false rejections                      |
| International students & skilled migrants (primary user — profile creation) | Hold relevant skills that go unrecognised                 | Directly create and view their own translated, explained skill profile; their real capability becomes visible to employers |
| Australian SMEs                                                             | Face the sharpest skills-shortage pain, least HR capacity | Lower-cost, adoptable tool vs. building internal capability                                                                |
| Universities & training providers                                           | Support graduate employability outcomes                   | Better employment outcomes to report; potential integration partner                                                        |
| Credential assessment bodies (e.g. VETASSESS)                               | Provide formal (slow) recognition today                   | Complementary, not competing — Skill Bridge handles fast informal signal                                                   |

**4.1 User Personas**

*One persona per primary user, both deliberately non-obvious: the
candidate is not a tech worker, and the recruiter is not at a large
enterprise with dedicated hiring infrastructure — these are the sharper,
less-served cases our evidence points to. Full illustrated one-pagers
are provided as companion files: Skill\_Bridge\_Persona\_Minh.html and
Skill\_Bridge\_Persona\_Sarah.html.*

**Minh Tran, 26 — Candidate Persona (Profile Creation)**

> *International graduate with a Business & Operations background, not a
> tech candidate. Three years managing operations and customer service
> teams in Ho Chi Minh City; now in Melbourne on a post-study work visa,
> targeting operations or business support roles that increasingly
> expect data/AI-tool familiarity he's never been taught.*

-   **Core frustrations:** silent rejection with no explanation; his
    experience doesn't map to local job titles; when he does see skill
    gaps, he has no sense of which to close first.

-   **Primary features used:** US-2 Skill Translator, US-3 Transferable
    Skills Highlighter, US-5 Honest Gap Flagging.

**Sarah Whitfield, 38 — Recruiter Persona (Decision Support)**

> *Sole Talent Acquisition Lead at a 60-person Australian tech/logistics
> SME, handling all screening, interviewing, and onboarding herself.
> Receives 200+ applications per role, increasingly from adjacent
> industries and niche/emerging skill areas she has no reliable way to
> evaluate.*

-   **Core frustrations:** application volume without clarity; can't
    tell which cross-industry skills genuinely transfer; no settled
    convention for evaluating niche/emerging skills like AI tools.

-   **Primary features used:** US-2 Cross-Industry Skill Translator,
    US-4 JD-Frequency Ranking, US-6 Skill-Level Matching Rate.

**5. Feature Requirements**

Features are split by build horizon: what the team commits to
demonstrating live in the hackathon, versus what is presented to judges
as the product's roadmap and long-term defensibility (USP).

**5.1 MVP — Build for the Hackathon Demo**

*Stakeholders are listed per feature, with the primary (acting) user
marked. The engine is shared: features 1, 2, 3, and 5 generate the
analysis, with the candidate as primary user; features 4, 6, and 7 apply
that same analysis to a specific role, with the recruiter as primary
user reusing — not recreating — the candidate's output.*

|        |                                                |                                                                                                                                                                                                                                                             |                                                                                                                 |              |
|--------|------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|--------------|
| **\#** | **Feature**                                    | **Description**                                                                                                                                                                                                                                             | **Stakeholders (primary user marked)**                                                                          | **Priority** |
| 1      | CV / Experience Parser                         | Ingests a candidate's CV or work history (including non-standard international formats) and extracts roles, responsibilities, and skills.                                                                                                                   | Candidate (primary user); Recruiter (later views the structured output)                                         | Must-have    |
| 2      | Cross-Border + Cross-Industry Skill Translator | Core engine. Maps overseas job titles/duties to local-market equivalents, and maps skills across industries where the underlying competency matches (e.g. Product Owner ↔ Marketing Executive; Business Analyst ↔ Data Analyst + business decision-making). | Candidate (primary user); Recruiter (later views the translated output)                                         | Must-have    |
| 3      | Transferable Skills Highlighter                | Shows which skills genuinely transfer, with a plain-language reason for each match (not a bare score).                                                                                                                                                      | Candidate (primary user); Recruiter (later views the highlighted output)                                        | Must-have    |
| 4      | JD-Frequency Skill Ranking                     | Ranks the candidate's already-translated skills by how often they appear across a sample set of real job descriptions for the target role.                                                                                                                  | Recruiter (primary user — inherits candidate profile); Employer/hiring team (indirectly, via the JD they wrote) | Should-have  |
| 5      | Honest Gap Flagging                            | Surfaces skills the candidate doesn't yet have evidence for, so they can address the gap or set realistic expectations.                                                                                                                                     | Candidate (primary user)                                                                                        | Should-have  |
| 6      | Skill-Level Matching Rate                      | Shows the candidate's already-translated profile against a specific role as a per-skill match rate, not a single score on the person — keeps hiring judgement with the human.                                                                               | Recruiter (primary user — inherits candidate profile)                                                           | Must-have    |
| 7      | Human-in-the-Loop Review UI                    | The recruiter reviews the candidate-generated profile and decides; the tool never auto-approves or auto-rejects a candidate.                                                                                                                                | Recruiter (primary user — inherits candidate profile); Candidate (affected by the decision)                     | Must-have    |

**5.2 Product Vision / Roadmap — Presented as USP, Not Built Live**

*These features require real usage data the team will not have within a
two-day hackathon, or extend the shared engine into a many-to-many
marketplace rather than today's one candidate-to-one role flow. They are
presented to judges as the product's growth story and long-term moat.*

|        |                                               |                                                                                                                                                                                                                                             |                                                                                                                      |                                                             |
|--------|-----------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| **\#** | **Feature**                                   | **Description**                                                                                                                                                                                                                             | **Stakeholders (primary user marked)**                                                                               | **Depends on**                                              |
| 8      | Skill Combination Engine (co-occurrence)      | Learns that people with skill A usually also hold skill B or C (from candidate profiles), and that employers who require skill A usually also require skill B or C (from JDs).                                                              | Recruiter (primary user); Candidate (data source)                                                                    | Volume of candidate + JD data                               |
| 9      | Outcome-Based Learning Loop                   | Recruiters mark a submitted candidate as hired/not hired and vote on which skill(s) drove the decision. Skills are re-ranked by real hiring outcomes over time.                                                                             | Recruiter (primary user); Candidate (subject of the outcome)                                                         | Live platform usage + recruiter feedback                    |
| 10     | Data-Driven Transferable Skill Detection      | A skill that frequently appears across diverse job titles and industries is automatically flagged as "transferable," validated by real usage rather than manual curation.                                                                   | Recruiter (primary user)                                                                                             | Sufficient data volume across industries                    |
| 11     | Compounding Data Flywheel                     | The more the platform is used, the more accurate its recommendations become — the core long-term defensibility story, since a static algorithm can be copied but a live feedback loop cannot.                                               | Recruiter (primary user); Candidate (indirect beneficiary)                                                           | Features 8–10 combined, at scale                            |
| 12     | Candidate Talent Pool / Discovery Marketplace | Aggregates individual candidate profiles (already built via features 1–3 in the MVP) into a searchable pool, so recruiters can proactively discover matching candidates instead of evaluating one CV against one job description at a time. | Recruiter (primary user — searches/discovers); Candidate (opt-in visibility across multiple employers, not just one) | Sufficient volume of candidate profiles created via the MVP |

**6. Constraints & Responsible AI Considerations**

**Privacy & data protection**

-   Candidate CVs and JDs used in the demo are either synthetic or
    consented sample data — no real personal data is processed without
    consent.

**Bias & fairness**

-   Skill matches are explained in plain language so a human can catch
    and challenge a biased or incorrect mapping.

-   The tool ranks skills, not people, to avoid encoding proxy bias into
    a single opaque score.

**Transparency**

-   Every recommendation shows its reasoning (source skill → mapped
    skill → why), not just a confidence percentage.

**Human oversight**

-   No feature in the MVP auto-accepts or auto-rejects a candidate. The
    recruiter always makes the final call.

**Accessibility & inclusion**

-   CV parsing must tolerate non-standard formats and translated
    documents, since candidates come from varied cultural, language, and
    educational backgrounds.

**Practical implementation**

-   Designed to be adoptable by an Australian SME or training provider
    without new infrastructure — a lightweight web tool or dashboard
    add-on, not a platform migration.

**7. Out of Scope (Hackathon)**

-   Automated hire/reject decisions of any kind.

-   Formal credential verification or legal equivalency (remains the
    role of bodies like VETASSESS).

-   Visa/work-rights eligibility checking.

-   Full-scale co-occurrence or outcome-based ranking requiring real
    production data (see Section 5.2).

**8. Open Questions for the Team**

-   What seed dataset will we use to demo cross-industry mapping live
    (manually curated list of 20–30 skill pairs)?

-   Which 2–3 industries give us the clearest, most relatable
    cross-industry translation examples for judges (e.g. Product ↔
    Marketing, Business Analysis ↔ Data Analysis)?

-   Do we have access to a small real or realistic set of JDs to power
    the frequency ranking feature?

-   What is the simplest UI that shows skill-level matching without
    implying a single "candidate score"?
