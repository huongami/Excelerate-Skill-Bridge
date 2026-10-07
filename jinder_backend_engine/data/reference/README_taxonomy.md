# ICT taxonomy (version 2)

`ict_taxonomy.json` is the one list of names for the Jinder demo. It covers three domains only:
**Software Engineering**, **AI & Machine Learning** and **Data**.

Data, formulas, CV parser, pick-lists and the translation library must use these names. Do not use another spelling.

> **Note:** This is a demo taxonomy. People made it by hand. It is not an official standard.

## Files

| File | Use |
|---|---|
| `ict_taxonomy.json` | The taxonomy. UTF-8, 2-space indent, LF line endings. |
| `validate_taxonomy.py` | The checker. Standard library only. |
| `README_taxonomy.md` | This file. |

Run the checker after each change:

```
python validate_taxonomy.py
```

The checker prints the counts and every problem. The exit code is 0 if the file is valid, and 1 if it has problems.

## Keys

| Key | Meaning |
|---|---|
| `version` | The text `"2"`. |
| `note` | A text that says this is a demo taxonomy. |
| `levels` | The 6 levels, in order: Intern, Junior, Mid, Senior, Lead, Principal. `rank` is 0 to 5. `typicalYears` is `[min, max]` and is a guide only. `titleWords` are lower-case words that show the level in a job title (for the CV parser). |
| `skillLevels` | Skill level 1 to 5: Beginner, Working, Proficient, Advanced, Expert. Each has a `label` and a `meaning`. |
| `domains` | The 3 domains. Each has a list of `specialisations`. |
| `skillGroups` | The 7 groups of skills. The keys are `languages`, `frameworks`, `cloud`, `data`, `ml`, `practices`, `collab`. Each has a `label`. |
| `skills` | The skills (see below). |
| `occupations` | The occupations (see below). |
| `certifications` | Well-known certifications (see below). |
| `awardKinds` | Kinds of recognition. `kind` is a slug. `examples` are 3 made-up award names. |
| `roles` | Job titles for the "role" pick-list. Each has a `domain` and an `occupationCode`. A role has no level word. The level is separate. |
| `fieldsOfStudy` | Fields of study for the pick-list. |
| `cities` | Cities for the pick-list. `Remote` is the last item. |
| `workModes` | Onsite, Hybrid, Remote. |
| `workTypes` | Full-time, Part-time, Contract, Graduate / Internship. |

## A skill

| Key | Meaning |
|---|---|
| `name` | The one canonical name. Show this name to people. |
| `group` | One of the 7 skill group keys. |
| `domains` | The domains where the skill matters. |
| `aliases` | Other spellings and short forms that appear in CVs and job ads. Lower case. One alias belongs to one skill only. |
| `related` | 2 to 5 other skills that give partial credit. Use exact names from the list. |
| `monthsToLearn` | Months that a new learner with a general IT background needs to reach level 3 (Proficient). From 0.5 to 12. |
| `rarity` | A weight from 1.0 (common) to 3.0 (rare). |
| `kind` | `hard` (a tool or technical skill), `method` (a way of working) or `soft` (a people skill). |

## An occupation

| Key | Meaning |
|---|---|
| `code` | A 6-digit ANZSCO code. It is the key. Each code is used once. |
| `title` | The title that Jinder shows. |
| `anzscoTitle` | The official title of the code. |
| `domain`, `specialisations` | The domain, and the specialisations that this occupation covers. |
| `coreSkills` | 6 to 10 skills. Each has the `level` (1 to 5) that the occupation needs and `must` (true or false). |
| `methods` | Skills of kind `method` or `soft` that this occupation needs. |
| `approximate` | `false` if the code and title are the real ANZSCO occupation. `true` if no exact code exists. Then `code` is the nearest real code. |

## A certification

| Key | Meaning |
|---|---|
| `name` | The official-style name. It uses a plain hyphen (`-`), not an en dash. A parser must treat both as the same. |
| `issuer` | Who gives the certification. |
| `domains` | The domains where it matters. |
| `tier` | `foundation`, `associate`, `professional` or `specialty`. |
| `prepMonths` | Months to prepare, from 0.5 to 6. |
| `aliases` | Optional. Lower-case short forms, for example exam codes. |
| `evidences` | The skills that the certification shows. |

## How to add a skill

1. Open `ict_taxonomy.json`.
2. Make sure that the skill is not in the list yet. Search the name and the aliases.
3. Copy one skill block in the `skills` list. Put the new block at the end of its group.
4. Write the canonical `name`. Use the usual spelling (for example `PostgreSQL`).
5. Set `group`, `domains` and `kind`.
6. Write the `aliases` in lower case. Do not use a common English word alone (for example `rest` or `spring`). A parser would find it in normal text.
7. Write 2 to 5 `related` skills. Use exact names. Also add the new skill to the `related` list of the skills that you chose, if they have room.
8. Set `monthsToLearn` and `rarity`.
9. Run `python validate_taxonomy.py`.
10. Fix each problem that the checker prints. Run the checker again until it prints `OK`.

Do not add a skill that means the same as a skill that exists. Add the new spelling to `aliases` of the old skill. For example, `ML` is an alias of `Machine learning`.

If you add a skill to an occupation, a certification or a role, use the exact skill name. The checker finds wrong names.

## Limits that the checker enforces

* Skills: 140 to 180. Each group has at least 12 skills. Each domain has at least 40 skills.
* Occupations: 14 to 20. Certifications: 30 to 40. Award kinds: 10 to 14. Roles: 45 to 60. Fields of study: 10 to 14.
* Names are unique, without regard to case. Names and aliases do not overlap.
