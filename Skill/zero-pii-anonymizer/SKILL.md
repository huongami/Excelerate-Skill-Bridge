---
name: zero-pii-anonymizer
description: Strip personally identifiable information (PII) from candidate profiles and assign deterministic Australian Wildlife Animal Aliases.
---

# Skill: Zero-PII Anonymizer

## Overview
This skill implements the privacy boundary required by **Australian Privacy Principles (APP 3 & APP 6)** and **AI Rule Rule 1**. It strips sensitive demographic identifiers from candidate data before employers can view the profile, mitigating unconscious recruitment bias.

## Protected Attributes Stripped (De-identification)
The following attributes are strictly purged:
1. Full Name & First/Last Names
2. Contact Information: Email addresses, phone numbers, postal addresses
3. Personal Media: Profile photos, video introductions, social media handles
4. Demographics: Date of birth, age, gender, marital status, nationality, visa subclass
5. University Alma Mater Names (replaced with AQF qualification level e.g., "Master's Degree in Data Science")

## Animal Alias Assignment System
Candidates are represented to employers by a unique, memorable Australian animal alias generated deterministically from the candidate's anonymous ID:

### Deterministic Adjective + Wildlife Fauna
- **Adjectives:** *Silver, Azure, Emerald, Golden, Solar, Ocean, Alpine, Coastal, Desert, Amber, Velvet, Cobalt, Coral, Onyx, Quartz, Mystic, Royal, Sage, Crimson, Frost.*
- **Fauna:** *Koala, Kangaroo, Platypus, Wombat, Echidna, Wallaby, Quokka, Dingo, Kookaburra, Cassowary, Bilby, Possum, Glider, Bandicoot, Cockatoo, Thorny Devil, Numbat, Pademelon, Rosella, Lyrebird.*

### Example Output
- `Candidate #104` -> **"Azure Platypus"**
- `Candidate #215` -> **"Emerald Quokka"**
- `Candidate #389` -> **"Silver Koala"**

## Privacy Guarantees
- Unlinkable by third parties.
- Consistency: An employer reviewing the same candidate sees the same animal alias.
- De-anonymization only occurs when an employer requests an interview and the candidate explicitly consents to release their contact details.
