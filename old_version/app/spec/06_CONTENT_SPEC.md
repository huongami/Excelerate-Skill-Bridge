# 06 — Legal Content, Microcopy & Static Assets Specification

Source of truth for the complete text of the **Terms and Conditions** (REQ-A03, REQ-A04), Privacy Notice, Landing Page copy, Score Explanations, and Interface Microcopy.

---

## 1. Terms and Conditions (Full Statutory Agreement Text)

*Display in the interactive Terms & Conditions Modal (REQ-A04) on sign-up and footer.*

```markdown
# SKILL BRIDGE PLATFORM TERMS AND CONDITIONS
**Version:** v2026.1  
**Effective Date:** 1 October 2026  
**Governing Jurisdiction:** New South Wales, Australia  

Please read these Terms and Conditions ("Terms") carefully before accessing or using the Skill Bridge platform ("Platform", "we", "us", or "our"). By registering an account, uploading a Curriculum Vitae (CV) or Job Description (JD), or checking the agreement box, you agree to be bound by these Terms and our Privacy Policy under the laws of the Commonwealth of Australia and the State of New South Wales.

---

### 1. Platform Purpose & Occupational Alignment Disclaimer
1.1 Skill Bridge is an analytical talent-matching and capability-translation gateway operating across Australian industry sectors.  
1.2 The Platform utilizes the Australian and New Zealand Standard Classification of Occupations (ANZSCO), published by the Australian Bureau of Statistics (ABS), to benchmark international qualifications and work experience against domestic competency frameworks.  
1.3 **Statutory Registration Acknowledgment:** You acknowledge that a high Match Percentage or Job Readiness Score on this Platform does **not** constitute official government skills assessment, visa sponsorship, migration approval, or statutory occupational registration. Statutory professions in Australia—including but not limited to Nursing and Healthcare (AHPRA), Chartered Accounting (CPA Australia / CA ANZ), Professional Engineering (Engineers Australia / NER), and Electrical/Building Trades—require direct formal application to and credential recognition from the relevant statutory authority.

---

### 2. Candidate Privacy & Zero-PII Identity Protection
2.1 To eliminate unconscious bias in hiring, Candidate profiles submitted to recruiters are presented under a pseudonymized **Candidate Alias** with Personally Identifiable Information (PII) scrubbed from initial recruiter viewports.  
2.2 Your legal name, private residential address, and direct telephone number will only be disclosed to an employer after you explicitly accept an interview invitation or formal assessment checkpoint.  
2.3 You warrant that all employment history, educational credentials, certifications, and licensing claims provided in your CV upload are truthful, accurate, and capable of independent documentary verification.

---

### 3. Employer & Recruiter Obligations
3.1 Employers accessing this Platform warrant that all posted vacancies represent genuine, currently open employment opportunities compliant with the *Fair Work Act 2009 (Cth)* and relevant Modern Awards or Enterprise Agreements.  
3.2 Employers agree not to discriminate against candidates on the basis of race, colour, sex, sexual orientation, age, physical or mental disability, marital status, family or carer's responsibilities, pregnancy, religion, political opinion, national extraction, or social origin, in accordance with the *Australian Human Rights Commission Act 1986 (Cth)*.  
3.3 Salary ranges posted on the Platform must adhere to the *Fair Work Ombudsman* national minimum wage standards.

---

### 4. Artificial Intelligence & Automated Scoring Transparency
4.1 The Platform applies transparent mathematical formulas (Formulas 1 through 6) to rank job suitability, calculate learnability duration for skill gaps, and benchmark candidates.  
4.2 Candidates and Employers retain the right to review, edit, or override any capability, requirement, or gap automatically extracted by AI models.  
4.3 Platform ranking models are de-biased: scores rest 100% on verifiable technical capability, statutory prerequisites, experience tenure, and transparent objective criteria.

---

### 5. Job Discrepancy Reporting & Moderation
5.1 Users may submit a report against any job vacancy displaying inaccurate requirements, misleading compensation, expired status, or improper ANZSCO taxonomy mapping.  
5.2 Listings receiving multiple verified user reports will be temporarily suspended from the public feed pending employer review and correction.

---

### 6. Intellectual Property & User Data Licensing
6.1 You retain full ownership of all original documents, CVs, and job descriptions uploaded to the Platform.  
6.2 By uploading content, you grant Skill Bridge a non-exclusive, royalty-free license to analyze, tokenize, extract competencies from, and process your content solely for the purpose of delivering talent matching and recommendation services.

---

### 7. Limitation of Liability
7.1 To the maximum extent permitted by the *Competition and Consumer Act 2010 (Cth)* (Australian Consumer Law), Skill Bridge shall not be liable for any indirect, incidental, special, or consequential damages resulting from employment hiring decisions, interview outcomes, or upskilling choices made on the basis of Platform metrics.

---

### 8. Contact & Dispute Resolution
For inquiries regarding these Terms or Platform governance, contact:  
**Skill Bridge Legal & Compliance:** `compliance@skillbridge.org.au`  
Level 14, 175 Pitt Street, Sydney NSW 2000, Australia.
```

---

## 2. Privacy Notice (Australian Privacy Principles Compliant)

```markdown
# PRIVACY NOTICE & DATA HANDLING PROTOCOL
**Under the Privacy Act 1988 (Cth) & Australian Privacy Principles (APPs)**

1. **What We Collect:**  
   - Contact details (Email, Phone, Legal Name for account verification).  
   - Employment background (Curriculum Vitae text, Job Descriptions, Skill sets, Education).  
   - Platform interaction logs (Saved jobs, ignored jobs, application statuses).

2. **How We Protect Your Identity (Zero-PII Mode):**  
   Recruiters searching for talent do not see your legal name or contact info. They see your chosen **Alias** (e.g., "Pacific Triage Pro"), your target ANZSCO occupation, years of experience, and verified competency excerpts. Direct contact details are shared only when an application reaches the Interview checkpoint with your mutual consent.

3. **Data Sovereignty:**  
   All databases and file storage are securely hosted in Australian data center zones complying with the *Privacy Act 1988 (Cth)*.
```

---

## 3. Landing Page Copy & FAQs (REQ-L01)

### 3.1 Hero Section
- **Badge:** `🇦🇺 AUSTRALIAN CAPABILITY ALIGNMENT`
- **Headline:** `Cross-Industry Experience, Recognised in Australia.`
- **Sub-headline:** `Translates international careers in Healthcare, Engineering, Finance, and Technology into Australian Bureau of Statistics (ANZSCO) standards. Real vacancies. Verified competencies. Zero demographic bias.`
- **Seeker CTA Button:** `I'm Looking for Work →` (Links to `/signup/seeker`)
- **HR CTA Button:** `I'm Hiring Talent` (Links to `/signup/hr`)

### 3.2 Live Stats Strip
- Stat 1: **461** `Live Australian Vacancies`
- Stat 2: **287** `Verified Employers`
- Stat 3: **320** `Sanitized International CVs`
- Stat 4: **17** `ANZSCO Occupations Covered`

### 3.3 Frequently Asked Questions (FAQ) Accordion
1. **What is an ANZSCO code and why does it matter?**  
   *The Australian and New Zealand Standard Classification of Occupations (ANZSCO) is the official framework used by Australian employers, immigration authorities, and industry bodies to define job roles and skill levels. Skill Bridge maps your global experience directly to these standard definitions.*
2. **How does Skill Bridge protect candidate privacy?**  
   *You choose an Alias during sign-up. Employers only see your professional capabilities, skill depth, and experience duration. Your real name, phone number, and address are hidden until an interview is mutually confirmed.*
3. **What is the difference between Match Percentage and Overall Score?**  
   *Match Percentage (Formula 1 SMF) measures your raw competency overlap with the Australian occupational definition. Overall Score (Formula 5 FRS) also factors in salary growth upside, location alignment, and job posting freshness.*
4. **Can I correct skills if the AI extraction makes a mistake?**  
   *Yes. You have full control in your Skills dashboard to edit skill labels, change categories from direct to transferable, add missing competencies, or delete misidentified items.*
5. **Does this replace official AHPRA or Engineers Australia licensing?**  
   *No. Statutory licenses require direct assessment from regulatory boards. Skill Bridge identifies statutory gaps early and estimates the bridging months needed so you are never caught unprepared.*
6. **How does the behavioural feed ranking work?**  
   *When you save a job, the algorithm increases your affinity for that employer and industry. When you ignore a job, similar vacancies are demoted, ensuring your feed stays fresh and relevant.*

---

## 4. Score Driver Rationale Templates (REQ-S11)

Used in `/seeker/jobs/{id}` to provide plain-English explanations:

| Score Metric | High Value Rationale (≥ 80%) | Moderate Value Rationale (50–79%) | Low Value Rationale (< 50%) |
| :--- | :--- | :--- | :--- |
| **Capability Fit ($S_{\text{cap}}$)** | "Your international background exhibits strong direct alignment with core ANZSCO competencies for this occupation." | "You have strong transferable problem-solving skills but will require brief onboarding for local protocols." | "Role involves significant technical divergence from your primary occupational background." |
| **Wage Upside ($S_{\text{wage}}$)** | "Compensation offers above-average growth compared to the standard sector benchmark." | "Compensation is strictly aligned with the Australian market midpoint for this skill level." | "Remuneration sits below typical senior benchmark rates for this discipline." |
| **Location Fit ($S_{\text{loc}}$)** | "Located within your preferred metropolitan region (Sydney) or offers remote flexibility." | "Located within the same Australian state; daily commute or regional relocation may apply." | "Interstate position requiring interstate relocation or regional transit." |
| **Posting Recency ($S_{\text{rec}}$)** | "Fresh vacancy published within the last 72 hours with maximum recruiter response velocity." | "Active listing published between 1 and 3 weeks ago." | "Mature listing active for more than 30 days." |

---

## 5. Curated Candidate Alias Suggestions (REQ-A07)

Pre-generated, respectful, professional aliases for random suggestions:
- *Healthcare:* "Pacific Triage Pro", "Southern Care Specialist", "Harbour Clinical Lead", "Equator Health Nurse", "Alpine Triage Coordinator"
- *Technology:* "Highland Data Engineer", "Summit Cloud Architect", "Solomon Code Specialist", "Coastal ETL Lead", "Verdant DevOps Engineer"
- *Finance:* "Meridian Financial Analyst", "Cascade Ledger Auditor", "Beacon Capital Advisor", "Apex Forensic Accountant"
- *Engineering:* "Pinnacle Structural Lead", "Vanguard Civil Engineer", "Kestrel Site Specialist", "Oasis Project Director"
- *Operations:* "Frontier Operations Lead", "Equinox Logistics Specialist", "Compass Dispatch Coordinator"
