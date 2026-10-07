# Synthetic jobs for the Jinder demo

All data in this folder is **synthetic**. It was written by hand for the demo.

* The companies are invented. They are not real brands.
* The job ads are new text. They are not copies of real ads.
* No file has a real person, a real URL, an e-mail address or a phone number.

Any match with a real organisation is by chance.

## Files

| File | Use |
|---|---|
| `jobs.json` | The 50 job ads for the Australian ICT market. |
| `demo.json` | The 4 jobs of the demo employer account. They are separate from the 50. |
| `validate_jobs.py` | The checker for `jobs.json` and `demo.json`. Standard library only. |
| `README.md` | This file. |

The talent files in this folder have their own notes.

## Names come from the taxonomy

Every skill, certification, award kind, specialisation, level, occupation code, city and work mode
is written exactly as in `../reference/ict_taxonomy.json`. Names are case-sensitive.
Use the canonical names. Do not use aliases.

## Format of the files

* UTF-8 without a BOM. LF line endings. 2-space indent. One final new line.
* Use ASCII characters only.

## jobs.json

The file is an object with three keys: `synthetic` (always `true`), `note` and `jobs` (the list of 50 jobs).

## Job object

Each job has exactly these keys, in this order.

| Key | Type | Meaning |
|---|---|---|
| `key` | text | A unique slug, for example `swe-backend-senior-01`. |
| `title` | text | The title of the ad. It can have a product area. A level word shows the level, except for Mid. |
| `company` | text | An invented company name. 30 companies post the 50 jobs. |
| `domain` | text | One of the 3 domains. |
| `specialisation` | text | A specialisation of that domain. |
| `level` | text | Intern, Junior, Mid, Senior, Lead or Principal. |
| `minYears` | number | The least experience that the job asks for. |
| `maxYears` | number or null | The most experience. `null` means open-ended. |
| `type` | text | `Full-time`, `Part-time`, `Contract` or `Graduate / Internship`. Every Intern job uses `Graduate / Internship`, and no other job does. |
| `workMode` | text | `Onsite`, `Hybrid` or `Remote`. |
| `city` | text | A city of the taxonomy. A Remote job uses `Remote`. |
| `area` | text | The location text, for example `Sydney NSW`. A Remote job uses `Remote (Australia)`. |
| `salary` | object | `min`, `max` and `unit`. The unit is `year` or `day` (a Contract job has a day rate). The amounts are in AUD. |
| `occupation` | object | `code` and `title` of one taxonomy occupation that fits the specialisation. |
| `skills` | list | 7 to 12 skills. Each skill has `name`, `level` (1 to 5) and `must` (`true` or `false`). 3 to 8 skills are must-haves. |
| `certifications` | object | `required` and `preferred`. Each is a list of taxonomy certification names. |
| `awards` | object | `preferred`: a list of taxonomy award kinds. |
| `educationMin` | text | A value of QUALIFICATIONS, for example `Bachelor's degree`. |
| `postedDaysAgo` | whole number | 1 to 21. |
| `closesInDays` | whole number | 7 to 45. |
| `description` | text | The full job description. It is never cut. |

The skill level is the level that the job needs. The same skill has different levels in different jobs.
The levels follow the level of the job: an Intern or Junior job asks mostly for levels 1 to 3, and a Senior job mostly for levels 3 to 5.

## Description markup

The `description` uses only this markup:

* A heading line: `## Heading`.
* A bullet line: `- text`.
* A paragraph: one plain line.
* One blank line between blocks (also after each heading).

The headings come in this order:

1. `About the role` (one paragraph of 3 to 5 sentences).
2. `What you will do` (5 to 8 bullets).
3. `What you bring` (5 to 8 bullets).
4. `Nice to have` (2 to 5 bullets).
5. `Tech stack` (one paragraph).
6. `Certifications and awards` (bullets). This heading is only in jobs that list a certification or an award.
7. `What we offer` (4 to 6 bullets).
8. `About <company name>` (one paragraph of 2 to 3 sentences).
9. `How we hire` (3 to 4 bullets).

The text is 1,400 to 3,500 characters long. The facts in the text agree with the fields (level, years, work mode, city, salary, skills, certifications).

## demo.json

The file has these keys: `synthetic`, `employer` (`name` and `company`) and `jobs`.
Each of the 4 jobs has the same keys as a job in `jobs.json`, and also `ownerDemo` (`true`) after `key`.

| Key | Job |
|---|---|
| `demo-data-engineer-mid` | Open. Mid Data Engineer. |
| `demo-backend-senior` | Open. Senior Backend Engineer. |
| `demo-ml-engineer-mid` | Open. Mid Machine Learning Engineer. It closes in 4 days. |
| `demo-data-engineer-contract-closed` | Closed. Contract Data Engineer. It closed 2 days ago (`closesInDays` is -2) and was posted 40 days ago. |

## How to check the data

1. Open a terminal in this folder.
2. Run `python validate_jobs.py`.
3. Read the summary table and the list of problems.
4. Fix each problem. Run the checker again until it prints `OK`.

The exit code is 0 if the data is valid and 1 if there are problems.

The checker tests the schema, all names against the taxonomy, the counts (domains, specialisations, levels,
work modes, cities, contracts), the certifications and awards, the uniqueness (keys, skill sets, salary ranges),
the description (headings, length, sentence counts, work mode, salary, skills, level words) and the consistency
(years, salary band and skill levels for each level). It also tests that no description has a URL, an e-mail address or a phone number.
Run `python ../reference/validate_taxonomy.py` to check the taxonomy.

## Counts in jobs.json

| Item | Count |
|---|---|
| Domains | Software Engineering 20, AI & Machine Learning 14, Data 16 |
| Levels | Intern 2, Junior 8, Mid 18, Senior 15, Lead 5, Principal 2 |
| Work modes | Hybrid 27, Onsite 12, Remote 11 |
| Cities | Sydney 15, Melbourne 12, Brisbane 6, Perth 3, Adelaide 1, Canberra 2, Remote 11 |
| Types | Full-time 42, Contract 6, Graduate / Internship 2 (no Part-time job) |

## Talents (talents.json)

`talents.json` holds 50 synthetic talent profiles (sample profiles that cannot sign in). Each profile has these fields:
alias, currentRole, level, yearsExperience, domain, specialisation, targetRole, targetIndustries, qualification, fieldOfStudy,
studyCountry, skills (name, level, years), certifications (name, issuer, year), awards (name, kind, year), locations, workModes,
workTypes, updatedDaysAgo and evidence.

The evidence lines and `studyCountry` are private. An employer never sees them.
Award names carry no year; the year is its own field.

Run `python validate_talents.py` to check the file. Run `python check_pairing.py` to check that every job has at least 3 talents
and every talent has at least 3 jobs with must-have coverage of 0.6 or more (a rough data check, not the platform score).
If you change a must-have skill in `jobs.json`, run `check_pairing.py` again.
