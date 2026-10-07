#!/usr/bin/env python3
"""Check ict_taxonomy.json. Standard library only (Python 3.9 or newer).

Usage:   python validate_taxonomy.py [path-to-taxonomy.json]
Output:  the counts, then every problem that it finds (one line each).
Exit:    0 = the file is valid, 1 = there is at least one problem, 2 = the file cannot be read.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PATH = os.path.join(HERE, "ict_taxonomy.json")

DOMAINS = ["Software Engineering", "AI & Machine Learning", "Data"]
LEVELS = ["Intern", "Junior", "Mid", "Senior", "Lead", "Principal"]
SKILL_LEVEL_LABELS = ["Beginner", "Working", "Proficient", "Advanced", "Expert"]
GROUPS = {
    "languages": "Languages",
    "frameworks": "Frameworks & libraries",
    "cloud": "Cloud & DevOps",
    "data": "Data & storage",
    "ml": "ML & AI",
    "practices": "Engineering practices",
    "collab": "Collaboration",
}
KINDS = ("hard", "method", "soft")
TIERS = ("foundation", "associate", "professional", "specialty")
TOP_KEYS = ["version", "note", "levels", "skillLevels", "domains", "skillGroups", "skills", "occupations",
            "certifications", "awardKinds", "roles", "fieldsOfStudy", "cities", "workModes", "workTypes"]
WORK_TYPES = ["Full-time", "Part-time", "Contract", "Graduate / Internship"]
WORK_MODES = ["Onsite", "Hybrid", "Remote"]
FIRST_CITIES = ["Sydney", "Melbourne", "Brisbane", "Perth"]

SKILLS_MIN, SKILLS_MAX = 140, 180
PER_GROUP_MIN = 12
PER_DOMAIN_MIN = 40
OCC_MIN, OCC_MAX = 14, 20
CERT_MIN, CERT_MAX = 30, 40
AWARD_MIN, AWARD_MAX = 10, 14
ROLES_MIN, ROLES_MAX = 45, 60
FIELDS_MIN, FIELDS_MAX = 10, 14
RELATED_MIN, RELATED_MAX = 2, 5
CORE_MIN, CORE_MAX = 6, 10


class Report(object):
    def __init__(self):
        self.problems = []

    def add(self, where, text):
        self.problems.append("%s: %s" % (where, text))


def is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def is_text(x):
    return isinstance(x, str) and x.strip() != "" and x == x.strip()


def check_text_list(rep, where, value, lower=False, min_len=0, unique=True):
    """Return the list when it is a list of clean texts, else add problems and return []."""
    if not isinstance(value, list):
        rep.add(where, "must be a list")
        return []
    if len(value) < min_len:
        rep.add(where, "needs at least %d item(s)" % min_len)
    out = []
    seen = set()
    for item in value:
        if not is_text(item):
            rep.add(where, "item %r must be a non-empty text without spaces at the ends" % (item,))
            continue
        if lower and item != item.lower():
            rep.add(where, "item %r must be lower case" % item)
        key = item.lower()
        if unique and key in seen:
            rep.add(where, "duplicate item %r" % item)
        seen.add(key)
        out.append(item)
    return out


def load(path):
    with open(path, "rb") as f:
        raw = f.read()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("the file has a BOM. Save it as UTF-8 without BOM")
    if b"\x00" in raw:
        raise ValueError("the file has NUL bytes")
    if b"\r" in raw:
        raise ValueError("the file has CR characters. Use LF line endings")
    text = raw.decode("utf-8")
    return json.loads(text), text


def check_top(rep, data, text):
    if not isinstance(data, dict):
        rep.add("file", "the top level must be an object")
        return False
    for k in TOP_KEYS:
        if k not in data:
            rep.add("file", "missing key %r" % k)
    for k in data:
        if k not in TOP_KEYS:
            rep.add("file", "unknown top-level key %r" % k)
    if list(k for k in data if k in TOP_KEYS) != [k for k in TOP_KEYS if k in data]:
        rep.add("file", "top-level keys are not in the standard order")
    if data.get("version") != "2":
        rep.add("version", 'must be the text "2"')
    note = data.get("note")
    if not is_text(note) or "demo" not in note.lower():
        rep.add("note", 'must be a text that says this is a "demo" taxonomy')
    if not text.endswith("\n"):
        rep.add("file", "the file must end with a new line")
    return all(k in data for k in TOP_KEYS)


def check_levels(rep, data):
    levels = data["levels"]
    if not isinstance(levels, list) or [l.get("name") if isinstance(l, dict) else None for l in levels] != LEVELS:
        rep.add("levels", "must be exactly %s, in this order" % LEVELS)
        return
    words_seen = {}
    for i, lv in enumerate(levels):
        where = "levels[%s]" % lv["name"]
        if lv.get("rank") != i or isinstance(lv.get("rank"), bool):
            rep.add(where, "rank must be %d" % i)
        ty = lv.get("typicalYears")
        if (not isinstance(ty, list) or len(ty) != 2 or not all(is_num(x) for x in ty)
                or ty[0] < 0 or ty[1] < ty[0] or ty[1] > 60):
            rep.add(where, "typicalYears must be [min, max] with 0 <= min <= max <= 60")
        words = check_text_list(rep, where + ".titleWords", lv.get("titleWords"), lower=True, min_len=1)
        for w in words:
            if w in words_seen and words_seen[w] != lv["name"]:
                rep.add(where, "title word %r is also used by level %s" % (w, words_seen[w]))
            words_seen[w] = lv["name"]
    # Intern 0 years, Principal open-ended (a quick sanity check on the guide)
    if levels[0].get("typicalYears") != [0, 0]:
        rep.add("levels[Intern]", "typicalYears should be [0, 0]")


def check_skill_levels(rep, data):
    sl = data["skillLevels"]
    if not isinstance(sl, list) or len(sl) != 5:
        rep.add("skillLevels", "must have 5 items (levels 1 to 5)")
        return
    for i, item in enumerate(sl):
        where = "skillLevels[%d]" % (i + 1)
        if not isinstance(item, dict):
            rep.add(where, "must be an object")
            continue
        if item.get("level") != i + 1 or isinstance(item.get("level"), bool):
            rep.add(where, "level must be %d" % (i + 1))
        if item.get("label") != SKILL_LEVEL_LABELS[i]:
            rep.add(where, "label must be %r" % SKILL_LEVEL_LABELS[i])
        if not is_text(item.get("meaning")):
            rep.add(where, "meaning must be a text")


def check_domains(rep, data):
    doms = data["domains"]
    names = [d.get("name") if isinstance(d, dict) else None for d in doms] if isinstance(doms, list) else None
    if names != DOMAINS:
        rep.add("domains", "must be exactly %s, in this order" % DOMAINS)
        return {}
    specs_by_domain = {}
    seen = {}
    for d in doms:
        specs = check_text_list(rep, "domains[%s].specialisations" % d["name"], d.get("specialisations"), min_len=3)
        specs_by_domain[d["name"]] = specs
        for s in specs:
            if s.lower() in seen:
                rep.add("domains", "specialisation %r is in two domains" % s)
            seen[s.lower()] = d["name"]
    return specs_by_domain


def check_groups(rep, data):
    g = data["skillGroups"]
    if not isinstance(g, dict) or list(g.keys()) != list(GROUPS.keys()):
        rep.add("skillGroups", "must have exactly these keys, in this order: %s" % list(GROUPS.keys()))
        return
    for k, v in g.items():
        if not isinstance(v, dict) or v.get("label") != GROUPS[k]:
            rep.add("skillGroups.%s" % k, "label must be %r" % GROUPS[k])


def check_skills(rep, data, counts):
    skills = data["skills"]
    if not isinstance(skills, list):
        rep.add("skills", "must be a list")
        return {}
    n = len(skills)
    if not (SKILLS_MIN <= n <= SKILLS_MAX):
        rep.add("skills", "count is %d. It must be %d to %d" % (n, SKILLS_MIN, SKILLS_MAX))
    by_name = {}
    # pass 1: names
    for i, s in enumerate(skills):
        where = "skills[%d]" % i
        if not isinstance(s, dict):
            rep.add(where, "must be an object")
            continue
        name = s.get("name")
        if not is_text(name):
            rep.add(where, "name must be a non-empty text")
            continue
        where = "skill %r" % name
        key = name.lower()
        if key in by_name:
            rep.add(where, "duplicate name (case-insensitive)")
        by_name[key] = s
    # pass 2: details
    alias_owner = {}
    group_count = dict((k, 0) for k in GROUPS)
    domain_count = dict((d, 0) for d in DOMAINS)
    for s in skills:
        if not isinstance(s, dict) or not is_text(s.get("name")):
            continue
        name = s["name"]
        where = "skill %r" % name
        extra = set(s.keys()) - set(["name", "group", "domains", "aliases", "related", "monthsToLearn", "rarity", "kind"])
        missing = set(["name", "group", "domains", "aliases", "related", "monthsToLearn", "rarity", "kind"]) - set(s.keys())
        if extra:
            rep.add(where, "unknown key(s) %s" % sorted(extra))
        if missing:
            rep.add(where, "missing key(s) %s" % sorted(missing))
        grp = s.get("group")
        if grp not in GROUPS:
            rep.add(where, "group %r is not one of %s" % (grp, list(GROUPS.keys())))
        else:
            group_count[grp] += 1
        doms = check_text_list(rep, where + ".domains", s.get("domains"), min_len=1)
        for d in doms:
            if d not in DOMAINS:
                rep.add(where, "domain %r is not one of %s" % (d, DOMAINS))
            else:
                domain_count[d] += 1
        aliases = check_text_list(rep, where + ".aliases", s.get("aliases"), lower=True)
        for a in aliases:
            if a == name.lower():
                rep.add(where, "alias %r repeats the name" % a)
            if a in by_name and by_name[a] is not s:
                rep.add(where, "alias %r is the name of skill %r" % (a, by_name[a]["name"]))
            if a in alias_owner and alias_owner[a] != name:
                rep.add(where, "alias %r is also an alias of %r" % (a, alias_owner[a]))
            alias_owner[a] = name
        rel = check_text_list(rep, where + ".related", s.get("related"))
        if not (RELATED_MIN <= len(rel) <= RELATED_MAX):
            rep.add(where, "related has %d item(s). It must have %d to %d" % (len(rel), RELATED_MIN, RELATED_MAX))
        for r in rel:
            if r.lower() not in by_name:
                rep.add(where, "related skill %r does not exist" % r)
            elif r.lower() == name.lower():
                rep.add(where, "related list has the skill itself")
            elif by_name[r.lower()]["name"] != r:
                rep.add(where, "related skill %r has a different spelling. Use %r" % (r, by_name[r.lower()]["name"]))
        m = s.get("monthsToLearn")
        if not is_num(m) or not (0.5 <= m <= 12):
            rep.add(where, "monthsToLearn must be a number from 0.5 to 12 (it is %r)" % (m,))
        r = s.get("rarity")
        if not is_num(r) or not (1.0 <= r <= 3.0):
            rep.add(where, "rarity must be a number from 1.0 to 3.0 (it is %r)" % (r,))
        if s.get("kind") not in KINDS:
            rep.add(where, "kind must be one of %s" % (KINDS,))
    for g, c in group_count.items():
        if c < PER_GROUP_MIN:
            rep.add("skills", "group %r has %d skills. It needs at least %d" % (g, c, PER_GROUP_MIN))
    for d, c in domain_count.items():
        if c < PER_DOMAIN_MIN:
            rep.add("skills", "domain %r has %d skills. It needs at least %d" % (d, c, PER_DOMAIN_MIN))
    counts["skills"] = n
    counts["skills per group"] = ", ".join("%s %d" % (g, group_count[g]) for g in GROUPS)
    counts["skills per domain"] = ", ".join("%s %d" % (d, domain_count[d]) for d in DOMAINS)
    counts["aliases"] = len(alias_owner)
    return by_name


def check_occupations(rep, data, skills, specs_by_domain, counts):
    occ = data["occupations"]
    if not isinstance(occ, list):
        rep.add("occupations", "must be a list")
        return {}
    if not (OCC_MIN <= len(occ) <= OCC_MAX):
        rep.add("occupations", "count is %d. It must be %d to %d" % (len(occ), OCC_MIN, OCC_MAX))
    by_code = {}
    titles = set()
    covered = set()
    for i, o in enumerate(occ):
        if not isinstance(o, dict):
            rep.add("occupations[%d]" % i, "must be an object")
            continue
        code = o.get("code")
        where = "occupation %r" % (code,)
        if not isinstance(code, str) or not re.match(r"^\d{6}$", code):
            rep.add(where, "code must be a text of 6 digits")
            continue
        if code in by_code:
            rep.add(where, "duplicate code")
        by_code[code] = o
        title = o.get("title")
        if not is_text(title):
            rep.add(where, "title must be a text")
        elif title.lower() in titles:
            rep.add(where, "duplicate title %r" % title)
        else:
            titles.add(title.lower())
        dom = o.get("domain")
        if dom not in DOMAINS:
            rep.add(where, "domain %r is not one of %s" % (dom, DOMAINS))
        specs = check_text_list(rep, where + ".specialisations", o.get("specialisations"), min_len=1)
        for sp in specs:
            if dom in specs_by_domain and sp not in specs_by_domain[dom]:
                rep.add(where, "specialisation %r is not a specialisation of domain %r" % (sp, dom))
            covered.add(sp)
        if not isinstance(o.get("approximate"), bool):
            rep.add(where, "approximate must be true or false")
        core = o.get("coreSkills")
        if not isinstance(core, list) or not (CORE_MIN <= len(core) <= CORE_MAX):
            rep.add(where, "coreSkills must be a list of %d to %d items" % (CORE_MIN, CORE_MAX))
            core = core if isinstance(core, list) else []
        seen = set()
        must_count = 0
        for c in core:
            if not isinstance(c, dict) or set(c.keys()) != set(["name", "level", "must"]):
                rep.add(where, "coreSkills item %r must have exactly name, level, must" % (c,))
                continue
            nm = c["name"]
            if not isinstance(nm, str) or nm.lower() not in skills:
                rep.add(where, "core skill %r does not exist" % (nm,))
            elif skills[nm.lower()]["name"] != nm:
                rep.add(where, "core skill %r has a different spelling. Use %r" % (nm, skills[nm.lower()]["name"]))
            if isinstance(nm, str) and nm.lower() in seen:
                rep.add(where, "core skill %r is listed twice" % nm)
            seen.add(str(nm).lower())
            if isinstance(c["level"], bool) or not isinstance(c["level"], int) or not (1 <= c["level"] <= 5):
                rep.add(where, "core skill %r: level must be a whole number from 1 to 5" % (nm,))
            if not isinstance(c["must"], bool):
                rep.add(where, "core skill %r: must needs true or false" % (nm,))
            elif c["must"]:
                must_count += 1
        if core and must_count < 2:
            rep.add(where, "at least 2 core skills should be must=true")
        methods = check_text_list(rep, where + ".methods", o.get("methods"), min_len=1)
        for m in methods:
            if m.lower() not in skills:
                rep.add(where, "method %r does not exist" % m)
            elif skills[m.lower()].get("kind") not in ("method", "soft"):
                rep.add(where, "method %r has kind %r. It must be method or soft" % (m, skills[m.lower()].get("kind")))
    for dom, specs in specs_by_domain.items():
        for sp in specs:
            if sp not in covered:
                rep.add("occupations", "no occupation covers the specialisation %r (domain %r)" % (sp, dom))
    counts["occupations"] = len(occ)
    counts["occupations approximate"] = sum(1 for o in occ if isinstance(o, dict) and o.get("approximate") is True)
    return by_code


def check_certs(rep, data, skills, counts):
    certs = data["certifications"]
    if not isinstance(certs, list):
        rep.add("certifications", "must be a list")
        return
    if not (CERT_MIN <= len(certs) <= CERT_MAX):
        rep.add("certifications", "count is %d. It must be %d to %d" % (len(certs), CERT_MIN, CERT_MAX))
    names = set()
    aliases_seen = {}
    for i, c in enumerate(certs):
        if not isinstance(c, dict):
            rep.add("certifications[%d]" % i, "must be an object")
            continue
        name = c.get("name")
        where = "certification %r" % (name,)
        if not is_text(name):
            rep.add(where, "name must be a text")
            continue
        if name.lower() in names:
            rep.add(where, "duplicate name")
        names.add(name.lower())
        extra = set(c.keys()) - set(["name", "issuer", "domains", "tier", "prepMonths", "aliases", "evidences"])
        missing = set(["name", "issuer", "domains", "tier", "prepMonths", "evidences"]) - set(c.keys())
        if extra:
            rep.add(where, "unknown key(s) %s" % sorted(extra))
        if missing:
            rep.add(where, "missing key(s) %s" % sorted(missing))
        if not is_text(c.get("issuer")):
            rep.add(where, "issuer must be a text")
        doms = check_text_list(rep, where + ".domains", c.get("domains"), min_len=1)
        for d in doms:
            if d not in DOMAINS:
                rep.add(where, "domain %r is not one of %s" % (d, DOMAINS))
        if c.get("tier") not in TIERS:
            rep.add(where, "tier must be one of %s" % (TIERS,))
        p = c.get("prepMonths")
        if not is_num(p) or not (0.5 <= p <= 6):
            rep.add(where, "prepMonths must be a number from 0.5 to 6 (it is %r)" % (p,))
        for a in check_text_list(rep, where + ".aliases", c.get("aliases", []), lower=True):
            if a == name.lower():
                rep.add(where, "alias %r repeats the name" % a)
            if a in aliases_seen and aliases_seen[a] != name:
                rep.add(where, "alias %r is also an alias of %r" % (a, aliases_seen[a]))
            aliases_seen[a] = name
        ev = check_text_list(rep, where + ".evidences", c.get("evidences"), min_len=1)
        for e in ev:
            if e.lower() not in skills:
                rep.add(where, "evidence skill %r does not exist" % e)
            elif skills[e.lower()]["name"] != e:
                rep.add(where, "evidence skill %r has a different spelling. Use %r" % (e, skills[e.lower()]["name"]))
    for a, owner in aliases_seen.items():
        if a in names and owner.lower() != a:
            rep.add("certifications", "alias %r is the name of another certification" % a)
    tiers = dict((t, 0) for t in TIERS)
    for c in certs:
        if isinstance(c, dict) and c.get("tier") in tiers:
            tiers[c["tier"]] += 1
    for t, n in tiers.items():
        if n == 0:
            rep.add("certifications", "no certification has tier %r" % t)
    counts["certifications"] = len(certs)
    counts["certifications per tier"] = ", ".join("%s %d" % (t, tiers[t]) for t in TIERS)


def check_awards(rep, data, counts):
    aw = data["awardKinds"]
    if not isinstance(aw, list):
        rep.add("awardKinds", "must be a list")
        return
    if not (AWARD_MIN <= len(aw) <= AWARD_MAX):
        rep.add("awardKinds", "count is %d. It must be %d to %d" % (len(aw), AWARD_MIN, AWARD_MAX))
    kinds = set()
    examples = set()
    for i, a in enumerate(aw):
        if not isinstance(a, dict):
            rep.add("awardKinds[%d]" % i, "must be an object")
            continue
        kind = a.get("kind")
        where = "awardKind %r" % (kind,)
        if not isinstance(kind, str) or not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", kind):
            rep.add(where, "kind must be a slug (lower case letters, digits and hyphens)")
        elif kind in kinds:
            rep.add(where, "duplicate kind")
        kinds.add(kind)
        if not is_text(a.get("label")):
            rep.add(where, "label must be a text")
        ex = check_text_list(rep, where + ".examples", a.get("examples"))
        if len(ex) != 3:
            rep.add(where, "examples must have exactly 3 items")
        for e in ex:
            if e.lower() in examples:
                rep.add(where, "example %r is used twice" % e)
            examples.add(e.lower())
    counts["awardKinds"] = len(aw)


def check_roles(rep, data, level_words, by_code, counts):
    roles = data["roles"]
    if not isinstance(roles, list):
        rep.add("roles", "must be a list")
        return
    if not (ROLES_MIN <= len(roles) <= ROLES_MAX):
        rep.add("roles", "count is %d. It must be %d to %d" % (len(roles), ROLES_MIN, ROLES_MAX))
    titles = set()
    used_codes = set()
    per_domain = dict((d, 0) for d in DOMAINS)
    for i, r in enumerate(roles):
        if not isinstance(r, dict) or set(r.keys()) != set(["title", "domain", "occupationCode"]):
            rep.add("roles[%d]" % i, "must have exactly title, domain, occupationCode")
            continue
        title = r["title"]
        where = "role %r" % (title,)
        if not is_text(title):
            rep.add(where, "title must be a text")
            continue
        if title.lower() in titles:
            rep.add(where, "duplicate title")
        titles.add(title.lower())
        padded = " " + re.sub(r"[^a-z0-9.#+]+", " ", title.lower()).strip() + " "
        for w in level_words:
            if " " + w + " " in padded:
                rep.add(where, "the title has the level word %r. Keep the level out of the role" % w)
        if r["domain"] not in DOMAINS:
            rep.add(where, "domain %r is not one of %s" % (r["domain"], DOMAINS))
            continue
        per_domain[r["domain"]] += 1
        code = r["occupationCode"]
        if code not in by_code:
            rep.add(where, "occupationCode %r is not in occupations" % (code,))
        else:
            used_codes.add(code)
            if by_code[code].get("domain") != r["domain"]:
                rep.add(where, "domain %r is not the domain of occupation %s (%r)" % (r["domain"], code, by_code[code].get("domain")))
    for code in by_code:
        if code not in used_codes:
            rep.add("roles", "no role uses occupation %s" % code)
    for d, n in per_domain.items():
        if n < 8:
            rep.add("roles", "domain %r has only %d roles" % (d, n))
    counts["roles"] = len(roles)
    counts["roles per domain"] = ", ".join("%s %d" % (d, per_domain[d]) for d in DOMAINS)


def check_lists(rep, data, counts):
    f = data["fieldsOfStudy"]
    f_ok = check_text_list(rep, "fieldsOfStudy", f)
    if not (FIELDS_MIN <= len(f_ok) <= FIELDS_MAX):
        rep.add("fieldsOfStudy", "count is %d. It must be %d to %d" % (len(f_ok), FIELDS_MIN, FIELDS_MAX))
    cities = check_text_list(rep, "cities", data["cities"], min_len=5)
    if cities[:4] != FIRST_CITIES:
        rep.add("cities", "the first 4 cities must be %s" % FIRST_CITIES)
    if "Remote" not in cities:
        rep.add("cities", 'must include "Remote"')
    if data["workModes"] != WORK_MODES:
        rep.add("workModes", "must be %s" % WORK_MODES)
    if data["workTypes"] != WORK_TYPES:
        rep.add("workTypes", "must be %s" % WORK_TYPES)
    counts["fieldsOfStudy"] = len(f_ok)
    counts["cities"] = len(cities)


def main(argv):
    path = argv[1] if len(argv) > 1 else DEFAULT_PATH
    try:
        data, text = load(path)
    except (OSError, ValueError) as exc:
        print("Cannot read %s: %s" % (path, exc))
        return 2
    rep = Report()
    counts = {}
    if check_top(rep, data, text):
        check_levels(rep, data)
        check_skill_levels(rep, data)
        specs_by_domain = check_domains(rep, data)
        check_groups(rep, data)
        skills = check_skills(rep, data, counts)
        by_code = check_occupations(rep, data, skills, specs_by_domain, counts)
        check_certs(rep, data, skills, counts)
        check_awards(rep, data, counts)
        level_words = []
        for lv in data["levels"] if isinstance(data["levels"], list) else []:
            if isinstance(lv, dict) and isinstance(lv.get("titleWords"), list):
                level_words.extend(w for w in lv["titleWords"] if isinstance(w, str))
        check_roles(rep, data, level_words, by_code, counts)
        check_lists(rep, data, counts)
        counts["domains"] = len(data["domains"]) if isinstance(data["domains"], list) else 0
        counts["levels"] = len(data["levels"]) if isinstance(data["levels"], list) else 0
    print("File: %s" % path)
    for k in ["levels", "domains", "skills", "skills per group", "skills per domain", "aliases", "occupations",
              "occupations approximate", "certifications", "certifications per tier", "awardKinds", "roles",
              "roles per domain", "fieldsOfStudy", "cities"]:
        if k in counts:
            print("  %-26s %s" % (k, counts[k]))
    if rep.problems:
        print("")
        print("%d problem(s):" % len(rep.problems))
        for p in rep.problems:
            print("  - " + p)
        return 1
    print("")
    print("OK: the taxonomy is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
