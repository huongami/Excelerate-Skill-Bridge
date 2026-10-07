#!/usr/bin/env python3
"""Check talents.json (50 synthetic talent profiles).

Standard library only. Exit code 0 = valid, 1 = problems.

Run:  python validate_talents.py

What it checks:
* the schema of each talent (keys, types, limits);
* every name against data/reference/ict_taxonomy.json (case-sensitive, canonical names);
* the distributions that the V2 plan asks for (domain, specialisation, level, city, bridge talents);
* uniqueness (alias, skill signature), years against level, skill years against total years;
* no URL, email, phone, non-ASCII text, or well-known real employer or university name;
* aliases come from the pool in jinder_platform/jinder/aliases.py and are not "Teal Heron".
"""
import ast
import json
import os
import re
import statistics
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
TAXONOMY_PATH = os.path.join(HERE, "..", "reference", "ict_taxonomy.json")
TALENTS_PATH = os.path.join(HERE, "talents.json")
PLATFORM_DIR = os.path.join(HERE, "..", "..", "..", "jinder_platform", "jinder")

# Fallback copies. The real values are read from the platform files when they exist.
_QUALIFICATIONS = [
    "High school", "Certificate III or IV", "Diploma", "Advanced diploma", "Associate degree",
    "Bachelor's degree", "Bachelor's degree (Honours)", "Graduate certificate", "Graduate diploma",
    "Master's degree", "MBA", "Doctorate (PhD)",
]
_WORK_TYPES = ["Full-time", "Part-time", "Contract", "Graduate / Internship"]
_COLOURS = ["Amber", "Azure", "Cobalt", "Coral", "Cyan", "Indigo", "Jade", "Lilac", "Lime", "Mint", "Plum",
            "Saffron", "Sage", "Slate", "Teal", "Violet"]
_ANIMALS = ["Badger", "Crane", "Dolphin", "Falcon", "Finch", "Fox", "Gecko", "Heron", "Kestrel", "Koala", "Llama",
            "Lynx", "Otter", "Owl", "Panda", "Puffin", "Robin", "Seal", "Swift", "Wombat"]
_COUNTRIES = [
    "Australia", "Bangladesh", "Brazil", "Canada", "Chile", "China", "Colombia", "Egypt", "France", "Germany",
    "Ghana", "Hong Kong", "India", "Indonesia", "Iran", "Ireland", "Italy", "Japan", "Kenya", "Malaysia",
    "Mexico", "Nepal", "Netherlands", "New Zealand", "Nigeria", "Pakistan", "Peru", "Philippines", "Singapore",
    "South Africa", "South Korea", "Spain", "Sri Lanka", "Taiwan", "Thailand", "Turkey", "United Arab Emirates",
    "United Kingdom", "United States", "Vietnam", "Zimbabwe",
]

RESERVED_ALIASES = {"Teal Heron"}

# --- the targets from the plan (section 3 R3 and the task brief) -----------------------------------
TARGET_DOMAIN = {"Software Engineering": 20, "AI & Machine Learning": 14, "Data": 16}
TARGET_SPEC = {
    "Backend": 6, "Frontend": 4, "Full-stack": 3, "Mobile": 2, "Platform and DevOps": 3,
    "Quality engineering": 1, "Software architecture": 1,
    "Machine learning engineering": 4, "Generative AI and LLM": 4, "Computer vision": 2,
    "Natural language processing": 1, "MLOps": 2, "Applied science and research": 1,
    "Data engineering": 6, "Data analytics": 3, "Analytics engineering": 2, "Business intelligence": 2,
    "Data science": 2, "Business analysis": 1,
}
TARGET_LEVEL = {"Intern": 3, "Junior": 10, "Mid": 17, "Senior": 13, "Lead": 5, "Principal": 2}
YEARS_RANGE = {
    "Intern": (0.0, 0.5), "Junior": (0.5, 2.5), "Mid": (2.0, 5.5),
    "Senior": (5.0, 10.0), "Lead": (7.0, 13.0), "Principal": (10.0, 20.0),
}
CITY_RANGE = {"Sydney": (15, 19), "Melbourne": (12, 16), "Brisbane": (6, 9), "Perth": (3, 5), "Remote": (2, 4)}
ADELAIDE_CANBERRA_RANGE = (3, 5)
BRIDGE_RANGE = (10, 14)          # "about 12"
CERT_SHARE = (0.40, 0.52)        # "about 45%"
AWARD_SHARE = (0.30, 0.40)       # "about 35%"
METRIC_SHARE = (0.40, 0.65)      # "numbers in about half of the evidence lines"

# Skill level against years of use (levels follow experience).
MIN_YEARS_FOR_LEVEL = {3: 0.3, 4: 1.5, 5: 3.0}
MAX_SKILL_LEVEL = {"Intern": 3, "Junior": 4, "Mid": 5, "Senior": 5, "Lead": 5, "Principal": 5}
MAX_FIVES = {"Intern": 0, "Junior": 0, "Mid": 2}
MAX_FOURS_JUNIOR = 3
MAX_HIGH_SHARE = 0.82    # most skills at 4 or 5 is allowed for a deep specialist, but never all

# Which specialisations a role title fits. Used for the "bridge talent" count and for consistency.
ROLE_SPECS = {
    "Software Engineer": {"Backend", "Full-stack"},
    "Software Developer": {"Backend", "Frontend", "Full-stack", "Mobile"},
    "Backend Engineer": {"Backend"},
    "Frontend Engineer": {"Frontend"},
    "Full-stack Engineer": {"Full-stack"},
    "Web Developer": {"Frontend", "Full-stack"},
    "Mobile Developer": {"Mobile"},
    "Android Developer": {"Mobile"},
    "iOS Developer": {"Mobile"},
    "Java Developer": {"Backend"},
    ".NET Developer": {"Backend"},
    "Python Developer": {"Backend"},
    "Platform Engineer": {"Platform and DevOps"},
    "DevOps Engineer": {"Platform and DevOps"},
    "Site Reliability Engineer": {"Platform and DevOps"},
    "Cloud Engineer": {"Platform and DevOps"},
    "Cloud Architect": {"Software architecture"},
    "Solutions Architect": {"Software architecture"},
    "Software Architect": {"Software architecture"},
    "QA Engineer": {"Quality engineering"},
    "Test Automation Engineer": {"Quality engineering"},
    "Software Tester": {"Quality engineering"},
    "Security Engineer": {"Security engineering"},
    "Application Security Engineer": {"Security engineering"},
    "Machine Learning Engineer": {"Machine learning engineering"},
    "Computer Vision Engineer": {"Computer vision"},
    "NLP Engineer": {"Natural language processing"},
    "Deep Learning Engineer": {"Machine learning engineering", "Computer vision", "Natural language processing"},
    "AI Engineer": {"Generative AI and LLM", "Machine learning engineering"},
    "Generative AI Engineer": {"Generative AI and LLM"},
    "LLM Engineer": {"Generative AI and LLM"},
    "MLOps Engineer": {"MLOps"},
    "ML Platform Engineer": {"MLOps"},
    "Applied Scientist": {"Applied science and research"},
    "AI Research Scientist": {"Applied science and research"},
    "AI Research Engineer": {"Applied science and research"},
    "Data Engineer": {"Data engineering"},
    "Analytics Engineer": {"Analytics engineering"},
    "Big Data Engineer": {"Data engineering"},
    "Data Platform Engineer": {"Data engineering"},
    "ETL Developer": {"Data engineering"},
    "Data Warehouse Engineer": {"Data engineering"},
    "Database Administrator": {"Data engineering"},
    "Data Architect": {"Data engineering"},
    "Data Analyst": {"Data analytics"},
    "Business Intelligence Analyst": {"Business intelligence"},
    "BI Developer": {"Business intelligence"},
    "Reporting Analyst": {"Business intelligence", "Data analytics"},
    "Product Analyst": {"Data analytics"},
    "Data Scientist": {"Data science"},
    "Statistician": {"Data science"},
    "Business Analyst": {"Business analysis"},
    "Business Systems Analyst": {"Business analysis"},
}

# Real employers, universities and brands that must not appear in evidence or award names.
# (Tool vendors such as Amazon, Microsoft or Google are allowed: they are skills and certifications.)
REAL_NAME_DENYLIST = [
    "Atlassian", "Canva", "Telstra", "Optus", "Woolworths", "Coles", "Qantas", "Westpac", "Commonwealth Bank",
    "CBA", "NAB", "ANZ", "Macquarie", "SEEK", "REA Group", "Xero", "Afterpay", "Deloitte", "Accenture",
    "KPMG", "PwC", "Capgemini", "Infosys", "Wipro", "TCS", "Cognizant", "Uber", "Netflix", "Spotify", "Meta",
    "Facebook", "Tesla", "Apple", "IBM", "SAP", "Salesforce", "Adobe", "Cochlear", "ResMed", "Woodside", "BHP",
    "Vodafone", "LinkedIn", "Indeed", "Adzuna", "Seek",
    "UNSW", "Monash", "RMIT", "Deakin", "QUT", "Curtin", "Stanford", "MIT", "Oxford", "Cambridge", "Harvard",
    "ANU", "UTS", "Griffith", "Swinburne", "Melbourne University", "Sydney University",
]

URL_RE = re.compile(r"(https?://|www\.)|\b[\w-]+\.(com|org|io|au|edu|gov|dev|ai|co|app)\b", re.I)
EMAIL_RE = re.compile(r"[\w.+-]*@[\w-]*", re.I)
PHONE_RE = re.compile(r"(?:\+?\d[\s().-]?){9,}")
ALIAS_RE = re.compile(r"^[A-Z][a-z]+ [A-Z][a-z]+$")

TALENT_KEYS = [
    "alias", "currentRole", "level", "yearsExperience", "domain", "specialisation", "targetRole",
    "targetIndustries", "qualification", "fieldOfStudy", "studyCountry", "skills", "certifications", "awards",
    "locations", "workModes", "workTypes", "updatedDaysAgo", "evidence",
]


def read_platform_list(filename, name, fallback):
    """Read a list constant from a platform file without importing it."""
    path = os.path.join(PLATFORM_DIR, filename)
    try:
        with open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                    and isinstance(node.targets[0], ast.Name) and node.targets[0].id == name:
                value = ast.literal_eval(node.value)
                if isinstance(value, list) and value:
                    return value
    except (OSError, SyntaxError, ValueError):
        pass
    return list(fallback)


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def one_decimal(value):
    return abs(value * 10 - round(value * 10)) < 1e-9


def word_pattern(text):
    return re.compile(r"(?<![A-Za-z0-9])" + re.escape(text) + r"(?![A-Za-z0-9])", re.I)


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def err(self, who, msg):
        self.errors.append(f"{who}: {msg}")

    def warn(self, who, msg):
        self.warnings.append(f"{who}: {msg}")


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main():
    rep = Report()
    taxonomy = load_json(TAXONOMY_PATH)
    qualifications = read_platform_list("reference.py", "QUALIFICATIONS", _QUALIFICATIONS)
    countries = read_platform_list("reference.py", "COUNTRIES", _COUNTRIES)
    colours = read_platform_list("aliases.py", "COLOURS", _COLOURS)
    animals = read_platform_list("aliases.py", "ANIMALS", _ANIMALS)

    levels = [lv["name"] for lv in taxonomy["levels"]]
    domains = {d["name"]: d["specialisations"] for d in taxonomy["domains"]}
    skills_by_name = {s["name"]: s for s in taxonomy["skills"]}
    skill_patterns = {}
    for s in taxonomy["skills"]:
        # An evidence line must name a skill of the talent by its canonical name (case does not matter).
        skill_patterns[s["name"]] = [word_pattern(s["name"])]
    certs_by_name = {c["name"]: c for c in taxonomy["certifications"]}
    award_kinds = {a["kind"] for a in taxonomy["awardKinds"]}
    roles = {r["title"] for r in taxonomy["roles"]}
    fields = set(taxonomy["fieldsOfStudy"])
    cities = list(taxonomy["cities"])
    work_modes = list(taxonomy["workModes"])
    work_types = list(taxonomy["workTypes"])

    # The taxonomy and the platform must agree on the shared pick-lists.
    if sorted(work_types) != sorted(read_platform_list("reference.py", "WORK_TYPES", _WORK_TYPES)):
        rep.err("setup", "taxonomy workTypes differ from WORK_TYPES in the platform")
    if set(ROLE_SPECS) != roles:
        rep.err("setup", "ROLE_SPECS and the taxonomy roles differ: "
                         f"missing {sorted(roles - set(ROLE_SPECS))}, extra {sorted(set(ROLE_SPECS) - roles)}")
    all_specs = {s for specs in domains.values() for s in specs}
    for role, specs in ROLE_SPECS.items():
        if not specs <= all_specs:
            rep.err("setup", f"ROLE_SPECS for {role} has an unknown specialisation: {sorted(specs - all_specs)}")

    with open(TALENTS_PATH, "rb") as fh:
        raw = fh.read()
    if raw.startswith(b"\xef\xbb\xbf"):
        rep.err("file", "talents.json has a BOM")
    if b"\r" in raw:
        rep.err("file", "talents.json has CR characters (use LF)")
    if b"\x00" in raw or b"\x08" in raw:
        rep.err("file", "talents.json has NUL or backspace characters")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        print("FAIL: talents.json is not valid UTF-8:", exc)
        return 1
    if any(ord(ch) > 127 for ch in text):
        rep.err("file", "talents.json has non-ASCII characters (AI_Rule 2: write names without diacritics)")
    data = json.loads(text)

    if data.get("synthetic") is not True:
        rep.err("file", 'top-level "synthetic" must be true')
    if not isinstance(data.get("note"), str) or not data["note"]:
        rep.err("file", 'top-level "note" must be a text')
    if set(data.keys()) != {"synthetic", "note", "talents"}:
        rep.err("file", f"top-level keys must be synthetic, note, talents (found {sorted(data.keys())})")
    talents = data.get("talents")
    if not isinstance(talents, list) or len(talents) != 50:
        rep.err("file", f"talents must be a list of 50 objects (found {len(talents) if isinstance(talents, list) else 'none'})")
        talents = talents if isinstance(talents, list) else []

    aliases = Counter()
    signatures = {}
    years_counter = Counter()
    days_counter = Counter()
    metric_lines = 0
    total_lines = 0
    cert_holders = 0
    award_holders = 0
    bridge_count = 0
    used_skills = Counter()
    level_skill_levels = {lv: [] for lv in levels}
    skill_sets = {}
    domain_counter = Counter()
    spec_counter = Counter()
    level_counter = Counter()
    city_counter = Counter()
    skill_count_counter = Counter()

    for index, t in enumerate(talents, 1):
        who = f"talent {index}"
        if not isinstance(t, dict):
            rep.err(who, "not an object")
            continue
        alias = t.get("alias")
        who = f"talent {index} ({alias})"
        keys = list(t.keys())
        if set(keys) != set(TALENT_KEYS):
            rep.err(who, f"keys differ: missing {sorted(set(TALENT_KEYS) - set(keys))}, extra {sorted(set(keys) - set(TALENT_KEYS))}")
            continue

        # alias
        if not isinstance(alias, str) or not ALIAS_RE.match(alias):
            rep.err(who, "alias must look like '<Colour> <Animal>'")
        else:
            colour, animal = alias.split(" ")
            if colour not in colours or animal not in animals:
                rep.err(who, "alias is not from the COLOURS and ANIMALS pool")
            if alias in RESERVED_ALIASES:
                rep.err(who, "alias is reserved for the demo account")
            aliases[alias] += 1

        # role, level, years
        role = t["currentRole"]
        if role not in roles:
            rep.err(who, f"currentRole not in the taxonomy roles: {role!r}")
        level = t["level"]
        if level not in levels:
            rep.err(who, f"level not in the taxonomy: {level!r}")
        years = t["yearsExperience"]
        if not is_number(years) or not one_decimal(years):
            rep.err(who, f"yearsExperience must be a number with one decimal: {years!r}")
            years = None
        elif level in YEARS_RANGE:
            lo, hi = YEARS_RANGE[level]
            if not (lo <= years <= hi) or (level == "Intern" and years <= 0):
                rep.err(who, f"yearsExperience {years} is outside the range {lo} to {hi} for level {level}")
        if years is not None:
            years_counter[years] += 1

        # domain and specialisation
        domain, spec = t["domain"], t["specialisation"]
        if domain not in domains:
            rep.err(who, f"domain not in the taxonomy: {domain!r}")
        elif spec not in domains[domain]:
            rep.err(who, f"specialisation {spec!r} does not belong to domain {domain!r}")
        if role in ROLE_SPECS and spec not in ROLE_SPECS[role]:
            rep.err(who, f"currentRole {role!r} does not fit specialisation {spec!r}")
        domain_counter[domain] += 1
        spec_counter[spec] += 1
        level_counter[level] += 1

        # target roles and industries
        targets = t["targetRole"]
        if not isinstance(targets, list) or not 1 <= len(targets) <= 2 or len(set(targets)) != len(targets):
            rep.err(who, "targetRole must be a list of 1 or 2 different roles")
        else:
            for tr in targets:
                if tr not in roles:
                    rep.err(who, f"targetRole not in the taxonomy roles: {tr!r}")
            if all(tr in ROLE_SPECS and spec not in ROLE_SPECS[tr] for tr in targets):
                bridge_count += 1
        inds = t["targetIndustries"]
        if not isinstance(inds, list) or len(set(inds)) != len(inds) or any(i not in domains for i in inds):
            rep.err(who, f"targetIndustries must be a list of domains without repeats: {inds!r}")

        # study
        qual = t["qualification"]
        if not isinstance(qual, list) or len(qual) != 1 or qual[0] not in qualifications:
            rep.err(who, f"qualification must be a list with one QUALIFICATIONS value: {qual!r}")
        fos = t["fieldOfStudy"]
        if not isinstance(fos, list) or len(fos) > 2 or len(set(fos)) != len(fos) or any(f not in fields for f in fos):
            rep.err(who, f"fieldOfStudy must be a list of 0 to 2 taxonomy fields: {fos!r}")
        elif not fos and qual != ["High school"]:
            rep.err(who, "fieldOfStudy may be empty only when the qualification is High school")
        sc = t["studyCountry"]
        if not isinstance(sc, list) or len(sc) > 2 or len(set(sc)) != len(sc) or any(c not in countries for c in sc):
            rep.err(who, f"studyCountry must be a list of 0 to 2 known countries: {sc!r}")

        # skills
        sk = t["skills"]
        names_in_talent = []
        if not isinstance(sk, list) or not 7 <= len(sk) <= 14:
            rep.err(who, f"skills must have 7 to 14 items (found {len(sk) if isinstance(sk, list) else 'none'})")
            sk = sk if isinstance(sk, list) else []
        skill_count_counter[len(sk)] += 1
        sig = []
        fours_fives = 0
        fives = 0
        fours = 0
        for s in sk:
            if not isinstance(s, dict) or set(s.keys()) != {"name", "level", "years"}:
                rep.err(who, f"a skill needs exactly name, level, years: {s!r}")
                continue
            name, lv, yrs = s["name"], s["level"], s["years"]
            if name not in skills_by_name:
                rep.err(who, f"skill not in the taxonomy (canonical name, case-sensitive): {name!r}")
                continue
            if name in names_in_talent:
                rep.err(who, f"skill listed twice: {name}")
            names_in_talent.append(name)
            used_skills[name] += 1
            if not isinstance(lv, int) or isinstance(lv, bool) or not 1 <= lv <= 5:
                rep.err(who, f"skill level of {name} must be an integer 1 to 5: {lv!r}")
                continue
            if not is_number(yrs) or not one_decimal(yrs) or yrs <= 0:
                rep.err(who, f"skill years of {name} must be a positive number with one decimal: {yrs!r}")
                continue
            if years is not None and yrs > years + 1e-9:
                rep.err(who, f"skill years of {name} ({yrs}) is more than the total years ({years})")
            for need_level, need_years in MIN_YEARS_FOR_LEVEL.items():
                if lv >= need_level and yrs + 1e-9 < need_years:
                    rep.err(who, f"{name}: level {lv} needs at least {need_years} years of use (found {yrs})")
            sig.append((name, lv))
            level_skill_levels.get(level, []).append(lv)
            if lv >= 4:
                fours_fives += 1
            if lv == 5:
                fives += 1
            if lv == 4:
                fours += 1
        if sk:
            levels_list = [s["level"] for s in sk if isinstance(s, dict) and isinstance(s.get("level"), int)]
            if levels_list:
                if sum(1 for lv in levels_list if lv <= 3) < 2:
                    rep.err(who, "no talent may have (almost) all skills at level 4 or 5: at least 2 skills must be 3 or lower")
                if fours_fives > MAX_HIGH_SHARE * len(levels_list):
                    rep.err(who, f"too many skills at 4 or 5 ({fours_fives} of {len(levels_list)})")
                top = max(levels_list)
                if level in MAX_SKILL_LEVEL and top > MAX_SKILL_LEVEL[level]:
                    rep.err(who, f"a {level} may not have a skill at level {top}")
                if level in MAX_FIVES and fives > MAX_FIVES[level]:
                    rep.err(who, f"a {level} may have at most {MAX_FIVES[level]} skill(s) at level 5 (found {fives})")
                if level == "Junior" and fours > MAX_FOURS_JUNIOR:
                    rep.err(who, f"a Junior may have at most {MAX_FOURS_JUNIOR} skills at level 4 (found {fours})")
                if level in ("Senior", "Lead", "Principal") and top < 4:
                    rep.err(who, f"a {level} needs at least one skill at level 4 or 5")
                if level in ("Lead", "Principal") and top < 5:
                    rep.err(who, f"a {level} needs at least one skill at level 5")
        frozen = frozenset(sig)
        if frozen in signatures:
            rep.err(who, f"same set of (skill, level) as {signatures[frozen]}")
        signatures[frozen] = alias
        skill_sets[alias] = set(names_in_talent)

        # certifications
        certs = t["certifications"]
        if not isinstance(certs, list) or len(certs) > 3:
            rep.err(who, "certifications must be a list of at most 3 items")
            certs = certs if isinstance(certs, list) else []
        if certs:
            cert_holders += 1
        seen_certs = set()
        for c in certs:
            if not isinstance(c, dict) or set(c.keys()) != {"name", "issuer", "year"}:
                rep.err(who, f"a certification needs exactly name, issuer, year: {c!r}")
                continue
            cname = c["name"]
            if cname not in certs_by_name:
                rep.err(who, f"certification not in the taxonomy: {cname!r}")
                continue
            if cname in seen_certs:
                rep.err(who, f"certification listed twice: {cname}")
            seen_certs.add(cname)
            tax = certs_by_name[cname]
            if c["issuer"] != tax["issuer"]:
                rep.err(who, f"issuer of {cname} must be {tax['issuer']!r} (found {c['issuer']!r})")
            if not isinstance(c["year"], int) or isinstance(c["year"], bool) or not 2019 <= c["year"] <= 2026:
                rep.err(who, f"certification year must be an integer 2019 to 2026: {c['year']!r}")
            elif years is not None and c["year"] < 2026 - years - 3:
                rep.warn(who, f"certification {cname} ({c['year']}) is early for {years} years of experience")
            if not set(tax.get("evidences", [])) & set(names_in_talent):
                rep.err(who, f"certification {cname} shows skills ({', '.join(tax.get('evidences', []))}) and the talent has none of them")

        # awards
        awards = t["awards"]
        if not isinstance(awards, list) or len(awards) > 2:
            rep.err(who, "awards must be a list of at most 2 items")
            awards = awards if isinstance(awards, list) else []
        if awards:
            award_holders += 1
        for a in awards:
            if not isinstance(a, dict) or set(a.keys()) != {"name", "kind", "year"}:
                rep.err(who, f"an award needs exactly name, kind, year: {a!r}")
                continue
            if not isinstance(a["name"], str) or not 8 <= len(a["name"]) <= 80:
                rep.err(who, f"award name must be a text of 8 to 80 characters: {a['name']!r}")
            elif a["name"].rstrip().endswith(str(a["year"])):
                rep.err(who, f"award name repeats the year: {a['name']!r}")
            if a["kind"] not in award_kinds:
                rep.err(who, f"award kind not in the taxonomy: {a['kind']!r}")
            if not isinstance(a["year"], int) or isinstance(a["year"], bool) or not 2000 <= a["year"] <= 2026:
                rep.err(who, f"award year must be an integer 2000 to 2026: {a['year']!r}")
            for bad in REAL_NAME_DENYLIST:
                if word_pattern(bad).search(str(a["name"])):
                    rep.err(who, f"award name has a real name ({bad}): {a['name']!r}")

        # locations, modes, types
        locs = t["locations"]
        if not isinstance(locs, list) or not 1 <= len(locs) <= 2 or len(set(locs)) != len(locs) or any(c not in cities for c in locs):
            rep.err(who, f"locations must be 1 or 2 different taxonomy cities: {locs!r}")
        else:
            city_counter[locs[0]] += 1
        modes = t["workModes"]
        if not isinstance(modes, list) or not 1 <= len(modes) <= 2 or len(set(modes)) != len(modes) or any(m not in work_modes for m in modes):
            rep.err(who, f"workModes must be 1 or 2 different values from {work_modes}: {modes!r}")
        elif isinstance(locs, list) and locs and locs[0] == "Remote" and "Remote" not in modes:
            rep.err(who, "first location is Remote, so workModes must include Remote")
        elif isinstance(locs, list) and locs and locs[0] == "Remote" and "Onsite" in modes:
            rep.err(who, "first location is Remote, so workModes must not include Onsite")
        wtypes = t["workTypes"]
        if not isinstance(wtypes, list) or not 1 <= len(wtypes) <= 3 or len(set(wtypes)) != len(wtypes) or any(w not in work_types for w in wtypes):
            rep.err(who, f"workTypes must be 1 to 3 different values from {work_types}: {wtypes!r}")
        elif level == "Intern" and "Graduate / Internship" not in wtypes:
            rep.err(who, "an Intern must list Graduate / Internship in workTypes")

        # recency
        days = t["updatedDaysAgo"]
        if not isinstance(days, int) or isinstance(days, bool) or not 0 <= days <= 60:
            rep.err(who, f"updatedDaysAgo must be an integer 0 to 60: {days!r}")
        else:
            days_counter[days] += 1

        # evidence
        ev = t["evidence"]
        if not isinstance(ev, list) or not 2 <= len(ev) <= 4:
            rep.err(who, "evidence must have 2 to 4 lines")
            ev = ev if isinstance(ev, list) else []
        seen_lines = set()
        for line in ev:
            if not isinstance(line, str) or not 30 <= len(line) <= 300:
                rep.err(who, f"an evidence line must be a text of 30 to 300 characters: {line!r}")
                continue
            if line in seen_lines:
                rep.err(who, f"evidence line repeated: {line!r}")
            seen_lines.add(line)
            total_lines += 1
            if re.search(r"\d", line):
                metric_lines += 1
            if URL_RE.search(line) or EMAIL_RE.search(line) or PHONE_RE.search(line):
                rep.err(who, f"evidence line has a URL, email or phone number: {line!r}")
            for bad in REAL_NAME_DENYLIST:
                if word_pattern(bad).search(line):
                    rep.err(who, f"evidence line has a real name ({bad}): {line!r}")
            if not any(p.search(line) for n in names_in_talent for p in skill_patterns.get(n, [])):
                rep.err(who, f"evidence line mentions no skill from the skills list: {line!r}")
            if re.match(r"^(The (candidate|talent|person)|This (candidate|talent|person)|He|She|They)\b", line):
                rep.err(who, f"evidence must be a first-person CV line, not a third-person text: {line!r}")
        if any(not isinstance(x, str) for x in ev):
            rep.err(who, "evidence must be a list of texts")

        # free text must carry no URL, email or phone (alias too)
        for field in ("alias", "currentRole"):
            if isinstance(t[field], str) and (URL_RE.search(t[field]) or EMAIL_RE.search(t[field]) or PHONE_RE.search(t[field])):
                rep.err(who, f"{field} looks like a URL, email or phone number")

    # ----- cross-talent checks -------------------------------------------------------------------
    for alias, n in aliases.items():
        if n > 1:
            rep.err("aliases", f"alias used {n} times: {alias}")
    for value, n in years_counter.items():
        if n > 2:
            rep.err("years", f"yearsExperience {value} is used by {n} talents (maximum 2)")
    for value, n in days_counter.items():
        if n > 2:
            rep.err("updatedDaysAgo", f"value {value} is used by {n} talents (maximum 2)")

    for name, expected in TARGET_DOMAIN.items():
        if domain_counter.get(name, 0) != expected:
            rep.err("distribution", f"domain {name}: expected {expected}, found {domain_counter.get(name, 0)}")
    for name, expected in TARGET_SPEC.items():
        if spec_counter.get(name, 0) != expected:
            rep.err("distribution", f"specialisation {name}: expected {expected}, found {spec_counter.get(name, 0)}")
    for name in spec_counter:
        if name not in TARGET_SPEC:
            rep.err("distribution", f"specialisation {name} is not in the plan")
    for name, expected in TARGET_LEVEL.items():
        if level_counter.get(name, 0) != expected:
            rep.err("distribution", f"level {name}: expected {expected}, found {level_counter.get(name, 0)}")
    for name, (lo, hi) in CITY_RANGE.items():
        if not lo <= city_counter.get(name, 0) <= hi:
            rep.err("distribution", f"first location {name}: expected {lo} to {hi}, found {city_counter.get(name, 0)}")
    ac = city_counter.get("Adelaide", 0) + city_counter.get("Canberra", 0)
    if not ADELAIDE_CANBERRA_RANGE[0] <= ac <= ADELAIDE_CANBERRA_RANGE[1]:
        rep.err("distribution", f"first location Adelaide + Canberra: expected {ADELAIDE_CANBERRA_RANGE[0]} to {ADELAIDE_CANBERRA_RANGE[1]}, found {ac}")
    if talents and sum(city_counter.values()) != len(talents):
        rep.err("distribution", "some first locations are missing or wrong")

    n = len(talents) or 1
    if not BRIDGE_RANGE[0] <= bridge_count <= BRIDGE_RANGE[1]:
        rep.err("distribution", f"bridge talents (target in another specialisation): expected {BRIDGE_RANGE[0]} to {BRIDGE_RANGE[1]}, found {bridge_count}")
    if not CERT_SHARE[0] <= cert_holders / n <= CERT_SHARE[1]:
        rep.err("distribution", f"talents with certifications: {cert_holders} of {n} is outside {CERT_SHARE[0]:.0%} to {CERT_SHARE[1]:.0%}")
    if not AWARD_SHARE[0] <= award_holders / n <= AWARD_SHARE[1]:
        rep.err("distribution", f"talents with awards: {award_holders} of {n} is outside {AWARD_SHARE[0]:.0%} to {AWARD_SHARE[1]:.0%}")
    metric_share = metric_lines / total_lines if total_lines else 0
    if not METRIC_SHARE[0] <= metric_share <= METRIC_SHARE[1]:
        rep.err("distribution", f"evidence lines with a number: {metric_share:.0%} is outside {METRIC_SHARE[0]:.0%} to {METRIC_SHARE[1]:.0%}")

    # near-twins and similarity (information)
    pairs = []
    names = list(skill_sets)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = skill_sets[names[i]], skill_sets[names[j]]
            if a or b:
                pairs.append((len(a & b) / len(a | b), names[i], names[j]))
    pairs.sort(reverse=True)

    # ----- summary ---------------------------------------------------------------------------------
    print(f"File       {os.path.abspath(TALENTS_PATH)}")
    print(f"Talents    {len(talents)}")
    print(f"Domain     " + ", ".join(f"{k} {domain_counter.get(k, 0)}" for k in TARGET_DOMAIN))
    print("Specialis. " + ", ".join(f"{k} {spec_counter.get(k, 0)}" for k in TARGET_SPEC))
    print("Level      " + ", ".join(f"{k} {level_counter.get(k, 0)}" for k in TARGET_LEVEL))
    print("City       " + ", ".join(f"{k} {city_counter.get(k, 0)}" for k in ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Canberra", "Remote"]))
    print(f"Bridge     {bridge_count} talents with a target in another specialisation")
    print(f"Certs      {cert_holders} talents ({cert_holders / n:.0%}); Awards {award_holders} talents ({award_holders / n:.0%})")
    print(f"Evidence   {total_lines} lines, {metric_share:.0%} with a number")
    print(f"Skills     {sum(skill_count_counter.values())} talents; skills per talent " +
          ", ".join(f"{k}:{v}" for k, v in sorted(skill_count_counter.items())))
    avg_by_level = []
    for lv in levels:
        vals = level_skill_levels.get(lv, [])
        if vals:
            avg_by_level.append(f"{lv} {statistics.mean(vals):.2f}")
    print("Avg skill level by talent level: " + ", ".join(avg_by_level))
    print(f"Taxonomy skills used by at least one talent: {len(used_skills)} of {len(skills_by_name)}")
    unused = [s for s in skills_by_name if s not in used_skills]
    if unused:
        print(f"Skills no talent uses ({len(unused)}): " + ", ".join(unused))
    if pairs:
        print("Most similar skill sets (Jaccard): " + "; ".join(f"{a} / {b} {j:.2f}" for j, a, b in pairs[:3]))
    print(f"Distinct years values {len(years_counter)}; distinct updatedDaysAgo values {len(days_counter)}")

    if rep.warnings:
        print(f"\nWarnings ({len(rep.warnings)}):")
        for w in rep.warnings:
            print("  -", w)
    if rep.errors:
        print(f"\nFAIL: {len(rep.errors)} problem(s):")
        for e in rep.errors:
            print("  -", e)
        return 1
    print("\nOK: talents.json is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
