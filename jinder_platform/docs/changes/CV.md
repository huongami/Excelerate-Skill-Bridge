# CV agent: changes for item R1 (the CV scan reads the role, the wish, the level, the years)

Files: `jinder/cv_parser.py`, `jinder/jd_parser.py`, `jinder/textextract.py`, and a new helper `jinder/cv_lexicon.py` (the word lists).
Tests: `tests/test_cv_rules.py`, `tests/test_cv_fields.py`, `tests/test_cv_holdout.py`, `tests/test_jd_v2.py`, `tests/test_textextract.py`.
Test data: `tests/fixtures/cv/` (24 PDF and DOCX files, `expected.json`), `tests/fixtures/cv_holdout*/` (text CVs that other writers made blind), `tests/fixtures/make_cv_fixtures.py` (makes the 24 files).

The user's own CV that failed (open item O1) is **still needed**. All numbers below come from made-up CVs.

## 1. The result of `parse_cv(text)` (what `GET /cv/parse/:id` gives in `result`)

All old keys stay. New keys are added. `parse_cv(text, today=None)`: `today` is only for tests (the day that "Present" means).

```
fields      the profile keys that the CV shows (only the keys that were found)
  old keys  qualification, fieldOfStudy, studyCountry, currentRole (a LIST: the current role first), industry (now DOMAINS, see below), years (the band), skills (names)
  new keys  targetRole    list of roles of the role list (the first one is the target)
            level         Intern | Junior | Mid | Senior | Lead | Principal
            yearsExperience   number 0 to 40, one decimal (the band `years` is set from it)
            certifications    [{name, issuer, year}]
            awards            [{name, kind, year}]   kind is a kind of the taxonomy or ""
detected    the keys of `fields` (the old test "detected == keys of fields" still holds)
missing     only the OLD keys that were not found (the new keys are never in `missing`, use `found`)
evidence    as before (private lines of the talent)
currentRole "Senior Data Engineer" or ""        the same values as plain values, for the UI
targetRole  "Data Engineer" or ""
level       "Senior" or ""
yearsExperience  7.5 or null
certifications, awards   same lists as in `fields` ([] when none)
skills      [{name, level}]   level 1 to 5, or null when the CV gives no evidence. `fields.skills` is the list of the names only
found       {currentRole, targetRole, level, yearsExperience, certifications, awards}   booleans, for the "not found" hints
sources     how each value was found (the name of the rule, section 2). For tests and for hints like "from your latest job"
domain      the first of fields.industry: Software Engineering | AI & Machine Learning | Data | ""
```

A field that cannot be read is empty (`""`, `[]`, `null`). The reader does not guess.

**`fields.industry` holds domains (Wave 4).** The platform keeps only the three domains (`R.DOMAINS`), so the CV result gives only those: at most 2, the strongest first, and the key is
missing (`missing` has `industry`) when nothing fits (a CV of a nurse gives none). Points: the current role 10 (the other roles of the past 3), a role that the person wants 6, the headline 4,
each skill 1 (shared between the domains that the taxonomy gives that skill: `skills[].domains`), the words of the specialisations in the text up to 1.5 for each specialisation. The role gets its
domain from `roles[].domain` and `occupations[].domain` of the taxonomy (also for "Senior Data Engineer"), else from the words of the specialisations, else "Software Engineering" for a general
IT title (developer, administrator, help desk). The first domain needs 2.5 points; the second needs half of the points of the first. `result.domain` is the first domain.
The old industries (Technology, Healthcare, Retail, ...) are gone from `_INDUSTRY_WORDS`; `_INDUSTRY_RE` (used by the category fallback of `jd_parser`) has the three domains only.
The field-of-study map has only names of the platform list (taxonomy `fieldsOfStudy`) and a few words that point to them ("computing", "informatics", "electrical engineering"). A degree that is
not in the list is not mapped to another name; it stays as the free text that was written ("Bachelor of Nursing" gives "Nursing", as before), and the profile cleaning decides what to keep.

## 2. The rules, in order (the first rule that gives a value wins)

**Current role** (`sources.currentRole`)
1. `open-position`: the job with an open end (Present, Current, Now, to date, ongoing, today, "since 2019"). Two open jobs: the one that started later.
2. `latest-end`: the job with the latest end date.
   If the newest job has dates but no title, there is no answer (an older title is not the current job). The next rules are tried.
3. `headline`: the job title under the name, above the name, or on the name line ("Name | Title", "Title at Company | skills"). "Aspiring ..." is a wish, not a role.
4. `label`: "Current position: ...", "Occupation or position held: ..." outside the top of the CV.
5. `summary`: a sentence like "Data analyst with 6 years of experience", "I am a ...", "Working as a ...".
6. `first-listed`: the first title when no job has dates.

How a job is found: a job is a line with a date range. The title is in the same line, or in the lines just before it (Title / Company / Dates),
or just after it (Dates / Title / Company). The reader picks the order that pairs most dates with a title. The date formats:
`Jan 2021 – Present`, `03/2020 – now`, `2019–2022`, `01/03/2022 – 28/02/2023`, `2020-03`, `Sept-2018`, `Sep2018`, `Jun '19`, `Jan/2021`, `Mar-21 to Jun-24`, `Q1 2024 - now`, `since June 2023`, `2024 – to date`.
A title keeps its level code and tag words: "Level 2 Service Desk Analyst" (Mid), "Head of IT" (Principal), "Scrum Master", "Junior Data Steward". A title in capitals or in small letters only gets normal capitals ("LEAD GAME DEVELOPER" gives "Lead Game Developer").
When the dates are in a block of their own and the jobs have none (a template with a "Timeline" in the sidebar), the first date range goes to the first job, the second to the second, and so on, if there are at least as many ranges as jobs.
A year without a month is the middle of the year. Lines about a career break, a gap year, a sabbatical or care are not work. Education, volunteering and side projects are not jobs.
A research assistant, teaching assistant or tutor whose dates are inside the years of a degree is study, not a job (a PhD student with only such roles has no current role and no years).
A CV with no heading for its experience is read from its top and from parts with an unknown heading, but not from volunteering, community, hobbies, references or publications.

The parts of the CV are found by their headings. Names that people use are known: "Working experience", "Contract and employment history", "Research experience", "Trainings and certifications",
"Professional development and certificates", "Patents and awards", "Awards and fellowships", "Honors-Awards", "Selected publications", "Open source". A row of a form where the label and the value share a line
("Certifications<tab>Oracle Certified Professional ...", the Europass layout) is a heading and its list. A line of a Markdown file (`## Heading`, `**bold**`, `` `code` ``, `---`) loses its signs.
A bullet that is a private-use character of a symbol font (Wingdings) is a bullet.

**Level** (`sources.level`) - Lead and Principal come only from title words.
1. `title`: the level words of the title of the current role (taxonomy `levels[].titleWords`; the highest word wins; "II" is Mid, "III" Senior, "IV" Lead).
2. `headline`: the level words of the headline.
3. `student` or `graduate`: no job (or under 1 year) and the words "student", "currently studying", "final year" (Intern) or "recent graduate", "entry-level" (Junior).
4. `years`: under 2 years Junior, 2 to under 5 Mid, 5 and more Senior.

**Target role** (`sources.targetRole`) - only a role of the role list (taxonomy `roles` and a few more titles). Else empty.
1. `label`: "Desired role: ...", "JOB APPLIED FOR" (and the next line), "Preferred job", "Position sought".
2. `sentence`: a wish sentence in the top, summary, objective or other parts (not in jobs, school or lists): seeking, looking for, open to, interested in, aiming, aspiring,
   hoping, my next step is, would like, ideally, keen to, grow into, next role. The role must have a word of job after it ("... Engineer roles") or an article before it ("a Data Scientist"),
   or stand right after "Next role:". A level word is dropped ("Senior MLOps Engineer" gives "MLOps Engineer").
3. `headline`: "Aspiring Data Scientist".
   Not a wish: "Looking after a team", "Looking forward to hearing from you", "open to feedback", "interested in data science" (a field), "Head of AI" (not in the list), "Staff Engineer" (a level, not a role).

**Years** (`sources.yearsExperience`) - the bigger of two numbers, at most 40.
1. `dates`: the years of all job ranges, overlaps counted once, up to today.
2. `statement`: "8+ years of experience", "eight years in insurance", "3 years 6 months of experience", "a decade of experience", "Experience: 7 years", "working in software since 2016".
   Years with one skill ("5 years of Python experience", "3 years with Docker") are for the skill and are not the total.

**Certifications** - the names and aliases of the taxonomy are found in any line (not in jobs and skills), also when a long name is cut over two lines ("Google Cloud Professional" / "Machine Learning Engineer, 2024").
The name is the taxonomy name and the issuer too. Other entries of a list of certifications, and lines that start with "Certified ...", are kept as written, with the abbreviation in capitals ("Certified Scrum Master (CSM)").
A piece after a comma or a dash that goes on with the name is part of the name ("Oracle Certified Professional, Java SE 8 Programmer", "ISTQB Certified Tester Advanced Level - Test Automation Engineer"); a piece that is an issuer is not ("..., Scrum Alliance").
A bracket in the middle of a name stays ("HackerRank SQL (Advanced) Certificate"). A name may start with a small letter when it is a brand ("freeCodeCamp ...", "dbt Fundamentals").
The lines under an entry ("Issued Mar 2021 · Expires Mar 2024", "Scrum.org", "2022") give the year. The year of expiry is never the year. Not a certification: a degree or a diploma, a course ("Course: ...", "Udemy course", a certificate of attendance or completion statement),
a language test (IELTS, TOEIC, JLPT, Cambridge English), a seminar or webinar, mandatory training, a security clearance, a rank on a learning platform, a driving licence, a Working With Children Check, a sentence, a job title, a line of a list of publications.
A certification that the person does not hold (yet) is left out, also when the taxonomy knows it: "exam booked", "planned for 2027", "in progress", "studying", "not yet taken", "lapsed", "part qualified".
A short name in brackets stays when it is part of the written name ("(CCNP Enterprise)", "(DP-300)", "(PSPO I)") for a name that the taxonomy does not know; for a name that it knows, the name of the taxonomy is given.

**Awards** - every line of an Awards, Honours, Recognition, Prizes, Papers, Talks, Patents, Scholarships or Fellowships part that is shaped like an award; a line of an Achievements or Publications part (or of a part called Open source) that has an award word
(winner, prize, best paper, speaker, maintainer, "of the year", ...); and a line anywhere else that names a prize, a win or a place AND a kind of the taxonomy (or the word award, prize, medal, scholarship) and has no date range (a range is an activity).
A part about the community, volunteering or activities (and a list of achievements) counts only with dated entries that have a kind ("Organiser, DevFest Nairobi 2023", "Top Contributor, Open Apex Utilities (open source), 2024"); a line with a prize word counts anywhere.
In a list that is only about awards ("Awards", "Honours and Prizes") a short entry with no year and no kind is an award ("Perfect attendance"); in a mixed list ("Extra-curricular activities and awards") it is not ("Captain of the badminton team").
Not an award: a citation (`[C6] A. Author, B. Author. "Title." Venue 2024.`, "et al"), a degree class ("Graduated June 2026 with First Class Honours"), the name, the headline or the place of the person (the end of a LinkedIn sidebar), an identifier, a sentence about a job or a hobby ("Maintainer of a small library"), "award-winning".
`kind` comes from the keywords of the line, or the first word before a colon ("Patent: ..."), or the heading when the heading names a kind ("Patents", "Hackathons"). A general heading ("Awards and Scholarships") gives no kind.
The place of a prize is not its kind ("Innovation Award, NZ Data & Analytics Summit" is innovation-award, not conference-talk): words such as conference, workshop, summit and meetup count last. Unknown kind: "".
The name has no year and no former employer ("Excellence in Delivery Award, Kestrel Analytics, 2023" gives "Excellence in Delivery Award"; the employer is found in the lines of the jobs, also the line under the title): the shared profile shows award names to employers.

**Skill levels** (`skills[].level`)
1. words, dots or a score next to the skill: "(Expert)" 5, "Advanced" 4, "Proficient" 3, "Working knowledge" 2, "Basic" or "Familiar" 1; "●●●●○" 4; "4/5"; "80%"; a line label "Expert: Python, SQL".
2. years next to the skill ("Python (8 yrs)", "5+ years with Python"): under 1 year 1, then 2, 3, 4, from 7 years 5.
3. the jobs that name the skill: under 1 year of use 2, 1 to 3 years 3, more 4. One level lower when the last use ended more than 3 years ago, two levels when more than 6 years ago. Never 5 from jobs only.
4. no evidence: `null`. (The BE gives such a skill 3 from its evidence, F8.)

**Which skills are listed** (`fields.skills`, at most 25): the items of the skills part first, then the tools of the taxonomy that the text shows, then the methods and soft skills of the taxonomy that the text shows
("Agile delivery" from "Scrum team", "Code review" from "code reviews", "Mentoring", "Incident response"): their words in the taxonomy are phrases, and they come last and with level `null`. "Excel" counts when it is written with a capital ("kept in Excel"), not "excel at teamwork".
The built-in list (used only when the taxonomy file is missing) is small, so it finds fewer skills.

## 3. Changes in `textextract.py` (the text of PDF and DOCX files)

| Problem | Fix |
|---|---|
| Two columns: the lines of the two columns were mixed | Text is collected as runs with a position. The page is read in visual order. A gutter (an empty vertical strip) splits the page into columns. A full-width line (name, title) comes first. |
| A sidebar that is written first, the name in the other column | The column with the biggest text (the name) is read first. |
| A page of ONE column that has a block of two columns in it (the end of page 1 has CERTIFICATIONS and LANGUAGES side by side, the top of page 2 goes on with the same two columns; defect D-1 of QA, found on the own CV of the user). No gutter for the whole page: most lines cross the middle, so the columns were mixed line by line ("Microsoft Certified: Power BI Data Analyst Vietnamese - native") and the certifications were lost | `_find_bands`: a **band** is 3 lines or more that share a free vertical strip (seed: a line with two cells and a gap of 16 points or more; the strip is cut by each line that is added, and the band stops at a line that crosses the strip). The band must have 2 cells of real text on each side, on 2 lines or more, long (18 characters on average, so a table of short cells stays line by line), starting at the same x (so a margin of right-aligned places does not count), and neither side is only a margin of dates of the other (a timeline stays line by line). Lines at the edge of the band that have text on one side only are cut off when they look like the next part (a bigger heading, text that starts left of the column, a gap of more than a line). The left column of the band is read, then the right column; the text before and after stays in place. A band that touches the bottom of a page and a band that touches the top of the next page with a strip that overlaps are **one band**: the left columns are read together, then the right columns, so a list that goes on over the page break stays together. A page with a gutter for the whole page is read as before |
| Dates in a margin (a timeline), headings in a margin, a table of short cells | These are not columns: the cells of a line stay on the line. |
| Bold text drawn twice, a flipped page (`cm`), text in a form XObject, a title that is drawn last | Duplicates are dropped. `q`, `Q`, `cm` and `Do` are handled. The order is the order on the page. |
| Words with no space glyph, a gap as a TJ number, a font with no `/Widths` | The gap between words gives the space. A standard font uses the widths of Helvetica. A long gap in one string cuts the string into two cells. |
| Ligatures (ﬁ, ﬂ), a bullet that is a private-use character, a non-breaking space, zero-width marks, letters with separate marks | `_tidy` makes plain letters, a bullet "•", a space; letters are composed (NFC). |
| A word cut with a hyphen at the end of a line | The word is joined ("engi-" "neering"). "full-" "stack" keeps its hyphen. |
| Odd font encodings | `/Encoding /MacRomanEncoding` and `/Differences` lists (glyph names such as bullet, endash, eacute, uni1EC5) are read. |
| DOCX: the name in the header part, a text box that is stored twice (Choice and Fallback), a table with the name in the right cell, a Symbol bullet | Header parts are read first and once (6 at most). The Fallback copy is dropped. In a table row the cell with the biggest text comes first. `w:sym`, soft and hard hyphens are read. |

## 4. Changes in `jd_parser.py` (job description import)

New keys in `fields` (only when the text shows them): `level`, `minYears`, `maxYears`, `workMode`, `skillRequirements` [{name, level, must}], `certifications` {required, preferred},
`awards` {preferred: [kind]}, `educationMin`, `specialisation`, and `domain`. They are in `detected`. `missing` is unchanged. Old keys are unchanged
(`category` is the domain when the platform has the domains as categories, else the old category).

| Key | Rule |
|---|---|
| `minYears`, `maxYears` | "5+ years" is 5 and null. "3-5 years", "3 to 5 years" is 3 and 5. "12 or more", "at least four", "up to 2 years". Years with one skill ("3 years with Kubernetes", "3+ years in Python") are not the job. "5 years in machine learning" is the job. The part "What you bring" is read first. |
| `level` | The title words, then "Seniority: ...", then "a senior-level role", then the years (under 2 Junior, 2 to 4 Mid, 5 and more Senior). A word about another person ("lead engineer") is not the level. |
| `workMode` | Hybrid wins. Then the first of Remote or Onsite. "Two days a week in the office" is Hybrid. |
| `skillRequirements` | Skills of the taxonomy (all kinds). A skill in "What you bring" is a must. In "Nice to have", "Tech stack", the tasks, or with "preferred" or "a plus" it is not. The level: "(4 of 5)", "at an advanced level", "5+ years of Python"; else 3. At most 12. |
| `certifications` | Names and aliases of the taxonomy. "Required certification: ...", "must", or the part "What you bring" make it required. Else preferred. |
| `awards.preferred` | Kinds. "Preferred award kind: Conference talk or paper", "Awards we value: A and B", "Kaggle ... is a plus". |
| `educationMin` | The lowest of the choices ("a master's degree or a PhD" is the master's degree). Same words as the profile qualification list. A degree that is only preferred, or in the company part, is not read. |
| `specialisation`, `domain` | The specialisation of the taxonomy that the title (first) and the text show. |
| `description` | **Not cut, no size limit in the reader** (the server refuses a text of more than 10,000 characters). It keeps the line breaks. `## Heading` lines (any `##` line, a known heading in any case, a short line that ends with a colon, a short line in capitals, a short line before a list of bullets), `- ` bullet lines, a blank line between the blocks. A text with no heading gets no heading. The title line is not in the description. |

## 5. Word lists (`cv_lexicon.py`)

The lists come from `jinder_backend_engine/data/reference/ict_taxonomy.json`: level words, roles, skills and aliases, certifications and aliases, award kinds, domains and specialisations.
Where the file is looked for: the environment variable `JINDER_TAXONOMY_PATH`, then `config.TAXONOMY_PATH` (if the platform has it), then `config.DATA_DIR / "reference" / "ict_taxonomy.json"`.
If the file is missing or broken, built-in lists are used (same names, a smaller list). The tests run with both.

## 6. The fixtures (`tests/fixtures/cv`, 24 files, made by `make_cv_fixtures.py`)

All people, employers, e-mails and phones are made up. The tests read each file "as of" 2026-10-06.

| File | Layout |
|---|---|
| cv01 PDF | One column, caps headings, `Title | Company | Mon YYYY – Present`, bullets, skills with years |
| cv02 PDF | Header over two columns. The file alternates a left line and a right line. A certification is cut over two lines |
| cv03 PDF | Narrow sidebar written first, the name in the wide column |
| cv04 PDF | `Name | Title`, Career objective "Seeking a ... position", dates "to date" |
| cv05 PDF | Title ABOVE the name, Vietnamese diacritics (Type0 font), jobs with no title, "Open to ... roles" |
| cv06 PDF | All-caps job lines, bullets ▪ ● – •, `MM/YYYY – now`, skill ratings with dots |
| cv07 PDF | LinkedIn export: sidebar first, headline `Title at Company | ...`, company / title / dates, two roles in one company |
| cv08 PDF | Europass-like: "JOB APPLIED FOR" label, `DD/MM/YYYY – Present Title` |
| cv09 DOCX | One column, title under the name, a tab and the date at the right, Symbol bullets, "I aspire to grow into a ... role" |
| cv10 DOCX | Two columns made with a table, the sidebar cell first |
| cv11 DOCX | Name and title in the page header, contact details in a text box (stored twice), `Sr.` |
| cv12 PDF | Student: the current role is an internship that ended, "Looking for a graduate ... role" |
| cv13 PDF | No wish. "Looking after a team" and "Looking forward to hearing from you" are traps. Awards of three kinds. Lead |
| cv14 PDF | Principal. "Open to Head of AI roles" (not in the role list: the target stays empty) |
| cv15 PDF | Jobs from the oldest to the newest |
| cv16 PDF | Ligatures, private-use bullets, hyphenated words, no space glyphs, TJ spaces |
| cv17 PDF | No dates: role and years from a summary sentence |
| cv18 PDF | Almost empty: every field must stay empty |
| cv19 DOCX | Stacked jobs (company / title / dates), "Open to A or B roles" |
| cv20 PDF | Flipped y axis (Cairo), the header in a form XObject, `Staff` |
| cv21 PDF | `Title at Company (YYYY–YYYY)`, "looking for roles in MLOps" (a skill, not a role), `Label: items` skills |
| cv22 PDF | LaTeX (moderncv): dates in the left column, headings in the margin, `/Differences` encoding |
| cv23 PDF | Two equal columns, the right column written first, headline `Title | skills` |
| cv24 PDF | A replica of the layout of the own CV of the user (defect D-1): one column on two pages, with a band of two columns (CERTIFICATIONS and LANGUAGES) at the end of page 1 that goes on at the top of page 2 (more certifications on the left, WORK RIGHTS AND AVAILABILITY on the right). A name cut over two lines with a code in the second line, a year on a line of its own, a course in the list. Made-up person and employers |

## 7. How good is it (made-up CVs; run `python run_tests.py`)

The 24 fixtures: current role, level, target role, years, certifications and awards are right in 24 of 24 CVs, with both word lists.
Found (not empty): current role 23 of 24, level 23, target role 11 (11 CVs state one), years 23, certifications 11, awards 8. The plan asks for current role and level in 10 of 14, and the target role in every CV that states one: met.
No field is filled when the CV shows nothing (tests: `test_a_field_that_the_cv_does_not_show_is_empty_not_wrong`).

**The own CV of the user (open item O1), after defect D-1.** The file is private and is not in the repository; a throw-away script read it. Current role, desired role, level, years and domain were right before the fix. The 2 certifications are now found with their years (2023 and 2021), the first one as the name of the taxonomy. The CV shows no award, so the awards stay empty. The skills show their levels where the CV gives words or the jobs show use (an item that the page broke in two, "Data" and "modelling", is one item now). The layout of the file is copied (made-up person and employers) in fixture `cv24_two_page_band.pdf`, with tests in `tests/test_textextract.py` and `tests/test_cv_fields.py`.

The fixtures were made by the same person as the reader, so they are not proof. Four sets of CVs that other writers made **blind** (the writers did not see the reader; text files in `tests/fixtures/cv_holdout`, `cv_holdout2`, `cv_holdout3`, `cv_holdout4`; 124 CVs; 5 of 32 CVs in set 1 and set 2 are deliberately garbled two-column texts).
Sets 3 and 4 are in the styles of real templates and countries (LaTeX, Word, LinkedIn export, Europass, Indian, Vietnamese, Philippine, Nigerian, Kenyan, Ghanaian, South African, Brazilian, German, French, UK graduate, NHS, US federal, military, academic, bootcamp, Markdown, contractor, fresh graduate).

| Set | current role | level | target role | years (±1) | certifications | awards | skills |
|---|---|---|---|---|---|---|---|
| Set 1 (32 CVs), first run, before any fix | 29 | 31 | 32 | 26 | 23 | 23 | 26 |
| Set 1, after the fixes (tuned on it) | 32 | 31 | 32 | 30 | 32 | 30 | 29 |
| Set 2 (32 CVs), first run | 26 | 27 | 26 | 21 | 19 | 18 | 29 |
| Set 2, after the fixes (tuned on it) | 31 | 32 | 30 | 32 | 30 | 28 | 32 |
| Set 3 (30 CVs), first run | 28 | 26 | 30 | 26 | 21 | 14 | 27 |
| Set 3, after the fixes (tuned on it) | 30 | 30 | 30 | 30 | 30 | 30 | 29 |
| Set 4 (30 CVs), first run (built-in lists) | 24 | 26 | 30 | 26 | 9 | 18 | 14 |
| Set 4, after the fixes (tuned on it), taxonomy lists | 30 | 30 | 30 | 30 | 30 | 30 | 30 |
| Set 4, after the fixes, built-in lists | 30 | 30 | 30 | 30 | 30 | 30 | 18 |

"Skills" is strict: all 6 to 8 skills that the writer named must be in the result (the writers of set 4 named methods and soft skills that the CV shows in a sentence, which only the taxonomy has).
Each set was used once as a blind test and then to improve general rules (every rule has a test in `tests/test_cv_rules.py`; nothing is made for a single file). The first run of the next set is the honest number for the reader as it was then.
Adding up the four first runs (124 CVs): current role 85%, level 87%, target role 94%, years 79%, certifications 57%, awards 58%, skills 76%. No set has a value where the CV shows none (0 invented values in 124 CVs).
The failures that were left in sets 1 and 2 are garbled extractions (a table read column by column, lost spaces, interleaved columns) and two awards where the writer and the taxonomy disagree on the kind ("Best Paper": the taxonomy examples say conference-talk).
The two titles of set 4 that the writer kept in capitals or in small letters are written with normal capitals by the reader (a choice, see the limits).
For a new real CV, expect the current role and the level right in about 85 to 90 of 100 CVs, the years in about 80, and the lists of certifications and awards exactly right in about 60 to 75 (the lists are the hard part: a course, a booked exam or a hobby that looks like a prize).

Sample jobs (the 50 job descriptions of the data agent, with their own fields; the reader never saw the fields): level 100%, years 100%, work mode 100%, domain 100%, specialisation 96%,
certifications 100%, award kinds 98%, skill names recall 97% and precision 91%. The description of each job comes back exactly as it went in (all `##` headings and `- ` bullets).

## 8. Limits (what the reader cannot do)

- A scanned CV (an image) has no text. A PDF font with no ToUnicode map and a CID encoding gives no letters. A password-protected PDF cannot be read.
- Text that another tool wrote in a bad order (columns read line by line, a table read column by column) can still give a wrong or empty value. The values are then empty more often than wrong.
- A job title that has no word of a role at its end ("Data Wizard", "Prompt Ninja") is not read. A title in another language is not read.
- The current role is the newest job by date. A CV with no dates and no summary sentence gives the first title in the file.
- Years with a year but no month can be wrong by up to one year. Part-time work counts as full time.
- A certification that the taxonomy does not know is read by its shape. Odd names can be missed, and a name that looks like a certification can be added.
- The kind of an award is from keywords. A name can still have a venue in it ("Best Paper Award, Workshop on Efficient NLP").
- A wish for a role that is not in the role list gives an empty target.
- A title that was written in capitals or in small letters only is returned with normal capitals. A title is kept as written otherwise (with a level code such as "Level 2", "II").
- A course, a short programme, a bootcamp without the word certificate or certification, and a certificate that is only a statement of attendance are not certifications. A person who thinks of an online course as a certification will not see it listed.
- The domains (`fields.industry`) are a guess from the role, the skills and the words of the text; a CV of a person who works in another field (nursing, law) gives none.
- The built-in lists (only when the taxonomy file is missing) are a small copy: they find fewer skills (18 of 30 CVs of set 4 against 30 of 30 with the taxonomy) and fewer domains.
- The timeline pairing (dates in a block of their own) goes by order. It is wrong when the template lists the jobs in another order than the dates.
- Skill levels from jobs are a rough guide. Without evidence the level is null.
- Skill bars that are drawn (not written) have no text.
- A block of two columns inside a page of one column is found when it has 3 lines or more, a gap of 16 points or more between the columns, and long cells on both sides. A block of 2 lines, or a block of short cells (a table), is read line by line. Two columns that are drawn over each other or with no gap are not split.

## 9. Needs from BE

- Nothing is needed to keep the old flow: `parse_cv(text)` returns the old keys. `parsing.py` can pass `result` as it is (it is JSON).
- The new keys of `result.fields` use the key names of `PATCH /me` (`targetRole` list, `level`, `yearsExperience`, `certifications`, `awards`). The onboarding can send `fields` as it is.
- `result.skills` is a list of `{name, level}` (the plan says `skills[].level`). `fields.skills` stays a list of names (the translation needs names).
- `fields.industry` now holds domains (the three of the platform, at most 2, the strongest first, missing when nothing fits), and `result.domain` is the first one. `store.py` can keep its domain filter; it will not drop anything.
- `config.TAXONOMY_PATH` is already there. The reader uses the environment variable `JINDER_TAXONOMY_PATH` first, then `config.TAXONOMY_PATH`, then `DATA_DIR / "reference" / "ict_taxonomy.json"`.
- `parse_jd` returns `category` from the old list when the platform has the old categories. With the three domains in `JOB_CATEGORIES` it returns the domain. `catalogue.clean_import_fields` can keep its checks.
- The awards in `awards.preferred` are the kinds (`hackathon`, `conference-talk`), not the labels.
- Old tests that used nurse CVs or JDs and old categories (`test_post_from_a_file`, `test_word_boundaries_in_patterns` with "Registered nurse") need ICT texts now; the reader still reads any job title.
