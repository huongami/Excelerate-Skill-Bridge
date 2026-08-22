**FUTURA REMIX HACKATHON**

**Skill Bridge**

*Product Vision, Goal & Requirements Document*

Track 1 — Future of Work and International Talent

*How might we use AI, data and digital technology to help international students and skilled migrants access meaningful career opportunities, while helping Australian employers identify, develop and retain diverse talent?*

Team: \[Team name\] — Nicolas (Product/PO), Huong (Technical Build), Thuyen (Marketing/Design)

Date: 23 August 2026

**1. Product Vision**

> ***A world where a skill is recognised for what it is — regardless of which country, industry, or job title it was built in — so that no qualified person is filtered out, and no employer is left short of the talent standing right in front of them.***

Australia is not short on talent. It hosts over 680,000 international students, yet 69% of Australian employers still report difficulty finding skilled people. The gap is not scarcity — it is translation. Skills earned overseas, or in a different industry, are invisible to the systems and people meant to evaluate them.

Skill Bridge exists to close that translation gap. We believe the future of hiring is not about scoring candidates, but about making the skills that already exist — visible, comparable, and trustworthy — to the humans who make hiring decisions.

**2. Product Goal**

**2.1 Primary Goal (Hackathon Scope)**

Build a working prototype that translates a candidate's cross-border and cross-industry experience into skills an Australian employer can immediately recognise as relevant — supporting, not replacing, the recruiter's decision.

**2.2 Target User**

-   **Primary user:** Hiring managers / recruiters at Australian SMEs and mid-size companies, who feel the 69% skills-shortage pain most acutely and have the least internal capacity to solve it themselves.

-   **Secondary beneficiary:** International students and skilled migrants, whose existing skills become visible through the employer's use of the tool.

**2.3 Success Criteria for the Hackathon**

-   A demoable flow: upload a candidate CV + a job description → receive a ranked, explained skill match.

-   At least one cross-border AND one cross-industry translation shown live (e.g. Product Owner ↔ Marketing Executive).

-   Every recommendation is explainable in plain language — no black-box score.

-   Judges can articulate, unprompted, why this is a two-sided solution (talent + employer) and why it is realistic to build further.

**2.4 Goal Statement**

> *For Australian SME recruiters who cannot tell which international or cross-industry candidates are actually qualified, Skill Bridge is a decision-support tool that translates experience into recognisable, ranked, and explained skill matches — unlike keyword-based ATS filters, which discard qualified candidates before a human ever sees their real capability.*

**3. Problem Context & Evidence**

|                                                                                          |                                                |                                                                    |
|------------------------------------------------------------------------------------------|------------------------------------------------|--------------------------------------------------------------------|
| **Data point**                                                                           | **Source**                                     | **Why it matters**                                                 |
| 69% of Australian employers report difficulty finding skilled talent                     | ManpowerGroup, 2024                            | Confirms the shortage is perceived as real by employers            |
| 92% of tech executives believe AI capability will be essential within 5 years            | KPMG Global Tech Report, 2026                  | Employers are raising the bar on skill signalling, not lowering it |
| 680,582 international students in Australia (Jan–May 2026)                               | Australian Government Dept. of Education, 2026 | A large, visible, underused talent pool already exists             |
| Higher education enrolments +2% YoY, but overall international student numbers -6.9% YoY | Australian Government Dept. of Education, 2026 | Signals a possible drop-off between study and employment outcomes  |

**Root cause**

Employers named "identifying transferable skills" and "evaluating international experience and credentials" as explicit barriers. This is not a lack of talent — it is a failure to recognise the skills that are already present, because they arrive in an unfamiliar format: a foreign job title, a different industry's vocabulary, or a CV structure the local ATS was never built to parse.

**4. Stakeholders**

|                                               |                                                           |                                                                          |
|-----------------------------------------------|-----------------------------------------------------------|--------------------------------------------------------------------------|
| **Stakeholder**                               | **Role in the problem**                                   | **Value received from Skill Bridge**                                     |
| Hiring managers / recruiters (primary user)   | Screen candidates but cannot verify transferable skills   | Faster, explainable shortlisting; fewer false rejections                 |
| International students & skilled migrants     | Hold relevant skills that go unrecognised                 | Their real capability becomes visible to employers                       |
| Australian SMEs                               | Face the sharpest skills-shortage pain, least HR capacity | Lower-cost, adoptable tool vs. building internal capability              |
| Universities & training providers             | Support graduate employability outcomes                   | Better employment outcomes to report; potential integration partner      |
| Credential assessment bodies (e.g. VETASSESS) | Provide formal (slow) recognition today                   | Complementary, not competing — Skill Bridge handles fast informal signal |

**5. Feature Requirements**

Features are split by build horizon: what the team commits to demonstrating live in the hackathon, versus what is presented to judges as the product's roadmap and long-term defensibility (USP).

**5.1 MVP — Build for the Hackathon Demo**

|        |                                                |                                                                                                                                                                                                                                                             |              |
|--------|------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------|
| **\#** | **Feature**                                    | **Description**                                                                                                                                                                                                                                             | **Priority** |
| 1      | CV / Experience Parser                         | Ingests a candidate's CV or work history (including non-standard international formats) and extracts roles, responsibilities, and skills.                                                                                                                   | Must-have    |
| 2      | Cross-Border + Cross-Industry Skill Translator | Core engine. Maps overseas job titles/duties to local-market equivalents, and maps skills across industries where the underlying competency matches (e.g. Product Owner ↔ Marketing Executive; Business Analyst ↔ Data Analyst + business decision-making). | Must-have    |
| 3      | Transferable Skills Highlighter                | Shows which skills genuinely transfer, with a plain-language reason for each match (not a bare score).                                                                                                                                                      | Must-have    |
| 4      | JD-Frequency Skill Ranking                     | Ranks recommended skills by how often they appear across a sample set of real job descriptions for the target role.                                                                                                                                         | Should-have  |
| 5      | Honest Gap Flagging                            | Surfaces skills the candidate is missing, so the tool builds trust instead of overselling a candidate.                                                                                                                                                      | Should-have  |
| 6      | Skill-Level Matching Rate                      | Match rate is calculated and displayed per skill, not as a single score on the person — keeps hiring judgement with the human.                                                                                                                              | Must-have    |
| 7      | Human-in-the-Loop Review UI                    | The recruiter reviews and decides; the tool never auto-approves or auto-rejects a candidate.                                                                                                                                                                | Must-have    |

**5.2 Product Vision / Roadmap — Presented as USP, Not Built Live**

*These features require real usage data the team will not have within a two-day hackathon. They are presented to judges as the product's growth story and long-term moat.*

|        |                                          |                                                                                                                                                                                               |                                          |
|--------|------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------|
| **\#** | **Feature**                              | **Description**                                                                                                                                                                               | **Depends on**                           |
| 8      | Skill Combination Engine (co-occurrence) | Learns that people with skill A usually also hold skill B or C (from candidate profiles), and that employers who require skill A usually also require skill B or C (from JDs).                | Volume of candidate + JD data            |
| 9      | Outcome-Based Learning Loop              | Recruiters mark a submitted candidate as hired/not hired and vote on which skill(s) drove the decision. Skills are re-ranked by real hiring outcomes over time.                               | Live platform usage + recruiter feedback |
| 10     | Data-Driven Transferable Skill Detection | A skill that frequently appears across diverse job titles and industries is automatically flagged as "transferable," validated by real usage rather than manual curation.                     | Sufficient data volume across industries |
| 11     | Compounding Data Flywheel                | The more the platform is used, the more accurate its recommendations become — the core long-term defensibility story, since a static algorithm can be copied but a live feedback loop cannot. | Features 8–10 combined, at scale         |

**6. Constraints & Responsible AI Considerations**

**Privacy & data protection**

-   Candidate CVs and JDs used in the demo are either synthetic or consented sample data — no real personal data is processed without consent.

**Bias & fairness**

-   Skill matches are explained in plain language so a human can catch and challenge a biased or incorrect mapping.

-   The tool ranks skills, not people, to avoid encoding proxy bias into a single opaque score.

**Transparency**

-   Every recommendation shows its reasoning (source skill → mapped skill → why), not just a confidence percentage.

**Human oversight**

-   No feature in the MVP auto-accepts or auto-rejects a candidate. The recruiter always makes the final call.

**Accessibility & inclusion**

-   CV parsing must tolerate non-standard formats and translated documents, since candidates come from varied cultural, language, and educational backgrounds.

**Practical implementation**

-   Designed to be adoptable by an Australian SME or training provider without new infrastructure — a lightweight web tool or dashboard add-on, not a platform migration.

**7. Out of Scope (Hackathon)**

-   Automated hire/reject decisions of any kind.

-   Formal credential verification or legal equivalency (remains the role of bodies like VETASSESS).

-   Visa/work-rights eligibility checking.

-   Full-scale co-occurrence or outcome-based ranking requiring real production data (see Section 5.2).

**8. Open Questions for the Team**

-   What seed dataset will we use to demo cross-industry mapping live (manually curated list of 20–30 skill pairs)?

-   Which 2–3 industries give us the clearest, most relatable cross-industry translation examples for judges (e.g. Product ↔ Marketing, Business Analysis ↔ Data Analysis)?

-   Do we have access to a small real or realistic set of JDs to power the frequency ranking feature?

-   What is the simplest UI that shows skill-level matching without implying a single "candidate score"?
