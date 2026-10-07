#!/usr/bin/env python3
"""Check the synthetic job data of the Jinder demo.

Files that this script checks (in the same folder):
  jobs.json   the 50 synthetic job ads
  demo.json   the 4 jobs of the demo employer account

Rules: standard library only, Python 3.9 or newer.
Exit code 0 = valid. Exit code 1 = at least one problem.

Run:  python validate_jobs.py
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
TAXONOMY_PATH = os.path.join(HERE, "..", "reference", "ict_taxonomy.json")
JOBS_PATH = os.path.join(HERE, "jobs.json")
DEMO_PATH = os.path.join(HERE, "demo.json")

# Same values as WORK_TYPES and QUALIFICATIONS in jinder_platform/jinder/reference.py.
JOB_TYPES = ["Full-time", "Part-time", "Contract", "Graduate / Internship"]
INTERN_TYPE = "Graduate / Internship"
QUALIFICATIONS = [
    "High school", "Certificate III or IV", "Diploma", "Advanced diploma", "Associate degree",
    "Bachelor's degree", "Bachelor's degree (Honours)", "Graduate certificate", "Graduate diploma",
    "Master's degree", "MBA", "Doctorate (PhD)",
]

JOB_KEYS = [
    "key", "title", "company", "domain", "specialisation", "level", "minYears", "maxYears", "type", "workMode",
    "city", "area", "salary", "occupation", "skills", "certifications", "awards", "educationMin",
    "postedDaysAgo", "closesInDays", "description",
]

AREA_BY_CITY = {
    "Sydney": "Sydney NSW", "Melbourne": "Melbourne VIC", "Brisbane": "Brisbane QLD",
    "Perth": "Perth WA", "Adelaide": "Adelaide SA", "Canberra": "Canberra ACT",
}
REMOTE_AREA = "Remote (Australia)"

# Expected counts (the plan, section 3 of the task).
EXPECT_DOMAIN = {"Software Engineering": 20, "AI & Machine Learning": 14, "Data": 16}
EXPECT_SPEC = {
    "Backend": 6, "Frontend": 4, "Full-stack": 3, "Mobile": 2, "Platform and DevOps": 3,
    "Quality engineering": 1, "Software architecture": 1,
    "Machine learning engineering": 4, "Generative AI and LLM": 4, "Computer vision": 2,
    "Natural language processing": 1, "MLOps": 2, "Applied science and research": 1,
    "Data engineering": 6, "Data analytics": 3, "Analytics engineering": 2, "Business intelligence": 2,
    "Data science": 2, "Business analysis": 1,
}
EXPECT_LEVEL = {"Intern": 2, "Junior": 8, "Mid": 18, "Senior": 15, "Lead": 5, "Principal": 2}
RANGE_MODE = {"Hybrid": (24, 28), "Remote": (10, 14), "Onsite": (10, 14)}
RANGE_CITY = {"Sydney": (14, 18), "Melbourne": (12, 16), "Brisbane": (6, 9), "Perth": (3, 5)}
RANGE_ADELAIDE_CANBERRA = (3, 5)
RANGE_CONTRACT = (5, 7)
RANGE_REQUIRED_CERT_JOBS = (12, 18)    # about 30 percent
RANGE_PREFERRED_CERT_JOBS = (25, 35)   # about 60 percent
RANGE_NO_CERT_JOBS = (2, 9)            # the rest
RANGE_AWARD_JOBS = (14, 22)            # about 35 percent
RANGE_COMPANIES = (28, 32)
MAX_JOBS_PER_COMPANY = 4
MIN_COMPANIES_WITH_MANY_JOBS = 6
MAX_SAME_POSTED = 3

# Level rules: years, salary band (per year), day rate band, skill levels.
MIN_YEARS_RANGE = {"Intern": (0, 1), "Junior": (0, 3), "Mid": (2, 6), "Senior": (4, 10), "Lead": (6, 14),
                   "Principal": (8, 99)}
SALARY_BAND = {"Intern": (55000, 70000), "Junior": (80000, 105000), "Mid": (110000, 145000),
               "Senior": (145000, 195000), "Lead": (170000, 225000), "Principal": (200000, 260000)}
SALARY_TOLERANCE = 0.15
DAY_BAND = {"Intern": (650, 800), "Junior": (650, 800), "Mid": (650, 950), "Senior": (850, 1200),
            "Lead": (950, 1200), "Principal": (1050, 1200)}
DAY_RATE_RANGE = (650, 1200)

LEVEL_WORDS = {
    "Intern": ["intern"],
    "Junior": ["junior", "graduate", "early career", "early-career"],
    "Mid": ["mid-level", "mid level", "mid "],
    "Senior": ["senior"],
    "Lead": ["lead"],
    "Principal": ["principal"],
}
TITLE_LEVEL_WORDS = {"Intern": "intern", "Junior": "junior", "Senior": "senior", "Lead": "lead",
                     "Principal": "principal"}
ALL_LEVEL_TITLE_WORDS = ["intern", "junior", "senior", "lead", "principal", "graduate", "staff", "head of"]

JD_HEADINGS_BEFORE = ["About the role", "What you will do", "What you bring", "Nice to have", "Tech stack"]
JD_CERT_HEADING = "Certifications and awards"
JD_HEADINGS_AFTER = ["What we offer", "ABOUT_COMPANY", "How we hire"]
JD_BULLETS = {
    "What you will do": (5, 8), "What you bring": (5, 8), "Nice to have": (2, 5),
    "What we offer": (4, 6), "How we hire": (3, 4),
}
JD_LENGTH = (1400, 3500)
JD_ABOUT_SENTENCES = (3, 5)
JD_COMPANY_SENTENCES = (2, 3)
MAX_SHARED_SENTENCE_COMPANIES = 2   # a sentence of 6+ words may appear in the ads of 2 companies at most
STRUCTURED_LINES = ("preferred certification:", "required certification:", "preferred award kind:", "awards we value:")

FORBIDDEN_WORDS = [r"\bcandidates?\b", r"\brecruiters?\b", r"\bHR\b", r"\blog in\b", r"\bsign up\b"]
BLOCKED_COMPANY_WORDS = [
    "acme", "contoso", "fabrikam", "northwind", "initech", "globex", "atlassian", "canva", "xero", "seek",
    "afterpay", "linktree", "culture amp", "airtree", "google", "microsoft", "amazon", "oracle", "ibm",
    "telstra", "optus", "commonwealth bank", "westpac", "anz", "nab", "woolworths", "coles", "qantas",
]

URL_RE = re.compile(r"(https?://|www\.|\b[a-z0-9-]+\.(com|org|net|io|ai|au|gov|edu|co)\b)", re.I)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+|@")
PHONE_RE = re.compile(r"(?<![\d,$.])\+?\d[\d\s().-]{8,}\d(?![\d,])|\b1[38]00[\s-]?\d{3}[\s-]?\d{3}\b")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


class Report(object):
    def __init__(self):
        self.errors = []

    def add(self, where, text):
        self.errors.append("%s: %s" % (where, text))


def load_json(path, label, rep, strict=True):
    if not os.path.exists(path):
        rep.add(label, "file not found: %s" % path)
        return None
    raw = open(path, "rb").read()
    if raw.startswith(b"\xef\xbb\xbf"):
        rep.add(label, "file has a BOM")
    if b"\r" in raw:
        rep.add(label, "file has CR characters (use LF only)")
    try:
        text = raw.decode("utf-8")
        data = json.loads(text)
    except Exception as exc:  # noqa: BLE001 - report all read errors
        rep.add(label, "cannot read the file as UTF-8 JSON: %s" % exc)
        return None
    again = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if strict and again != text:
        rep.add(label, "file is not formatted with a 2-space indent, key order and a final newline")
    return data


class Taxonomy(object):
    def __init__(self, data):
        self.levels = [x["name"] for x in data["levels"]]
        self.level_words = dict((x["name"], x.get("titleWords", [])) for x in data["levels"])
        self.skills = dict((s["name"], s) for s in data["skills"])
        self.alias_to_skill = {}
        for s in data["skills"]:
            for a in s.get("aliases", []):
                self.alias_to_skill[a.lower()] = s["name"]
        self.certs = dict((c["name"], c) for c in data["certifications"])
        self.award_kinds = dict((a["kind"], a) for a in data["awardKinds"])
        self.occupations = dict((o["code"], o) for o in data["occupations"])
        self.domains = dict((d["name"], d["specialisations"]) for d in data["domains"])
        self.cities = list(data["cities"])
        self.work_modes = list(data["workModes"])


# ---------------------------------------------------------------------------
# Job description (JD)
# ---------------------------------------------------------------------------

def parse_jd(text, where, rep):
    """Return a list of (heading, kind, lines) in order. kind is 'paragraph' or 'bullets'."""
    if text != text.strip("\n") or text.endswith(" ") or "\t" in text:
        rep.add(where, "description has leading or trailing blank lines, a trailing space or a tab")
    blocks = text.strip("\n").split("\n\n")
    sections = []
    expect_heading = True
    heading = None
    for block in blocks:
        lines = block.split("\n")
        if any(not ln.strip() for ln in lines):
            rep.add(where, "description has a blank line inside a block or more than one blank line in a row")
            return sections
        if expect_heading:
            if len(lines) != 1 or not lines[0].startswith("## "):
                rep.add(where, "expected a single '## Heading' line, found: %r" % lines[0][:40])
                return sections
            heading = lines[0][3:].strip()
            if lines[0].startswith("### ") or not heading:
                rep.add(where, "bad heading line")
                return sections
            expect_heading = False
        else:
            if all(ln.startswith("- ") for ln in lines):
                sections.append((heading, "bullets", [ln[2:].strip() for ln in lines]))
            elif any(ln.startswith("- ") or ln.startswith("#") for ln in lines):
                rep.add(where, "heading '%s' has a block that mixes bullets and text" % heading)
                return sections
            elif len(lines) != 1:
                rep.add(where, "heading '%s': a paragraph must be one line" % heading)
                return sections
            else:
                sections.append((heading, "paragraph", lines))
            expect_heading = True
    if not expect_heading:
        rep.add(where, "the last heading '%s' has no content" % heading)
    return sections


def skill_in_text(name, text):
    """True if the skill name is a whole word (or phrase) in the text.

    Short names (3 letters or fewer, for example R, Go, Git) must match with the same case.
    """
    pattern = r"(?<![A-Za-z0-9+#.])%s(?![A-Za-z0-9+#])" % re.escape(name)
    flags = 0 if len(name) <= 3 else re.I
    return re.search(pattern, text, flags) is not None


LEVEL_WORD_VALUE = {"expert": 5, "advanced": 4, "proficient": 3, "working": 2, "beginner": 1}
LEVEL_PHRASE_RE = re.compile(
    r"\((\d)(?: to (\d))? of 5\)|\b(expert|advanced|proficient|working|beginner)\s+level\b"
    r"|\bat an? (expert|advanced|proficient|working|beginner)\b", re.I)


def mask_longer_skills(name, text, tax):
    """Hide longer skill names that contain this name (for example 'Azure' in 'Azure DevOps')."""
    for other in tax.skills:
        if other != name and len(other) > len(name) and name.lower() in other.lower():
            text = re.sub(re.escape(other), " ", text, flags=re.I)
    return text


def check_levels_in_text(job, by_head, tax, rep, where):
    """A level word or '(N of 5)' in a bullet must match the level of the skills named before it."""
    by_name = dict((s["name"], s) for s in job["skills"])
    for head in ("What you bring", "Nice to have"):
        for line in by_head[head][2]:
            pos = 0
            for m in LEVEL_PHRASE_RE.finditer(line):
                if m.group(1):
                    low, high = int(m.group(1)), int(m.group(2) or m.group(1))
                else:
                    low = high = LEVEL_WORD_VALUE[(m.group(3) or m.group(4)).lower()]
                seg = line[pos:m.start()]
                pos = m.end()
                if not m.group(1):
                    # A level word that is followed by '(N of 5)' or '(N to M of 5)': the number is the exact value.
                    tail = re.match(r"\s*(?:level\s*)?\((\d)(?: to (\d))? of 5\)", line[pos:])
                    if tail:
                        low, high = int(tail.group(1)), int(tail.group(2) or tail.group(1))
                        pos += tail.end()
                for name, sk in by_name.items():
                    if skill_in_text(name, mask_longer_skills(name, seg, tax)) and not (low <= sk["level"] <= high):
                        rep.add(where, "'%s' says level %s for '%s' but the data says %d" % (head, low if low == high else "%d to %d" % (low, high), name, sk["level"]))


def sentences_of(text):
    return [s.strip() for s in SENTENCE_SPLIT_RE.split(text.strip()) if s.strip()]


def check_jd(job, tax, rep, where):
    desc = job["description"]
    company = job["company"]
    level = job["level"]
    mode = job["workMode"]

    if not (JD_LENGTH[0] <= len(desc) <= JD_LENGTH[1]):
        rep.add(where, "description length %d is outside %d to %d" % (len(desc), JD_LENGTH[0], JD_LENGTH[1]))
    if "…" in desc or "..." in desc:
        rep.add(where, "description has an ellipsis (a cut text)")
    if not desc.rstrip().endswith("."):
        rep.add(where, "description does not end with a full stop")
    for pattern in FORBIDDEN_WORDS:
        if re.search(pattern, desc, re.I if pattern != r"\bHR\b" else 0):
            rep.add(where, "description uses a forbidden word (%s)" % pattern)

    sections = parse_jd(desc, where, rep)
    if not sections:
        return None
    headings = [s[0] for s in sections]

    has_cert_section = JD_CERT_HEADING in headings
    lists_cert_or_award = bool(job["certifications"]["required"] or job["certifications"]["preferred"]
                               or job["awards"]["preferred"])
    expected = list(JD_HEADINGS_BEFORE)
    if lists_cert_or_award:
        expected.append(JD_CERT_HEADING)
    for h in JD_HEADINGS_AFTER:
        expected.append("About " + company if h == "ABOUT_COMPANY" else h)
    if has_cert_section and not lists_cert_or_award:
        rep.add(where, "has a '%s' section but the job lists no certification or award" % JD_CERT_HEADING)
    if headings != expected:
        rep.add(where, "headings are %s, expected %s" % (headings, expected))
        return None

    by_head = dict((s[0], s) for s in sections)
    # kinds
    for h in JD_BULLETS:
        if by_head[h][1] != "bullets":
            rep.add(where, "'%s' must be bullet lines" % h)
            continue
        lo, hi = JD_BULLETS[h]
        n = len(by_head[h][2])
        if not (lo <= n <= hi):
            rep.add(where, "'%s' has %d bullets, expected %d to %d" % (h, n, lo, hi))
    for h in ["About the role", "Tech stack", "About " + company]:
        if by_head[h][1] != "paragraph":
            rep.add(where, "'%s' must be one paragraph" % h)
    if lists_cert_or_award and by_head[JD_CERT_HEADING][1] != "bullets":
        rep.add(where, "'%s' must be bullet lines" % JD_CERT_HEADING)

    if by_head["About the role"][1] == "paragraph":
        n = len(sentences_of(by_head["About the role"][2][0]))
        if not (JD_ABOUT_SENTENCES[0] <= n <= JD_ABOUT_SENTENCES[1]):
            rep.add(where, "'About the role' has %d sentences, expected %d to %d" % (n, JD_ABOUT_SENTENCES[0], JD_ABOUT_SENTENCES[1]))
    about_head = "About " + company
    if by_head[about_head][1] == "paragraph":
        n = len(sentences_of(by_head[about_head][2][0]))
        if not (JD_COMPANY_SENTENCES[0] <= n <= JD_COMPANY_SENTENCES[1]):
            rep.add(where, "'%s' has %d sentences, expected %d to %d" % (about_head, n, JD_COMPANY_SENTENCES[0], JD_COMPANY_SENTENCES[1]))

    body = " ".join(" ".join(s[2]) for s in sections)
    if len(re.findall(re.escape(company), body)) < 1 or len(re.findall(re.escape(company), desc)) < 2:
        rep.add(where, "the company name must appear in the text and in the 'About' heading")

    # work mode
    low = desc.lower()
    mode_word = mode.lower()
    if job["type"] == INTERN_TYPE and re.search(r"full-time|part-time", low):
        rep.add(where, "an internship description must not say full-time or part-time")
    if mode_word not in low:
        rep.add(where, "description does not say the work mode word '%s'" % mode)
    banned = {"Onsite": ["hybrid", "fully remote", "work from home", "from home"],
              "Hybrid": ["fully remote", "onsite"],
              "Remote": ["hybrid", "onsite"]}[mode]
    for word in banned:
        if word in low:
            rep.add(where, "description says '%s' but the work mode is %s" % (word, mode))
    if mode != "Remote" and job["city"] not in desc:
        rep.add(where, "description does not name the city %s" % job["city"])

    # level word
    words = LEVEL_WORDS[level]
    if not any(w in (low + " ") for w in words):
        rep.add(where, "description never says the level (%s)" % level)

    # years in 'What you bring'
    bring = " ".join(by_head["What you bring"][2])
    mn, mx = job["minYears"], job["maxYears"]
    if mx is not None:
        ok = re.search(r"\b%d\s*(to|-)\s*%d\s+years?\b" % (mn, mx), bring) is not None
        need = "'%d to %d years'" % (mn, mx)
    else:
        ok = re.search(r"\b%d\+?\s*(or more\s+)?years?\b" % mn, bring) is not None
        need = "'%d or more years' or '%d+ years'" % (mn, mn)
    if not ok:
        rep.add(where, "'What you bring' must say the experience as %s" % need)

    # salary text
    offer = " ".join(by_head["What we offer"][2])
    sal = job["salary"]
    a, b = "{:,}".format(sal["min"]), "{:,}".format(sal["max"])
    if ("$" + a) not in offer or ("$" + b) not in offer:
        rep.add(where, "'What we offer' must show the salary as $%s and $%s" % (a, b))
    if sal["unit"] == "day" and "day" not in offer.lower():
        rep.add(where, "'What we offer' must say that the rate is a day rate")
    if sal["unit"] == "year" and "a year" not in offer.lower():
        rep.add(where, "'What we offer' must say 'a year' for the salary")

    # skills in the text
    for sk in job["skills"]:
        if sk["must"]:
            if not skill_in_text(sk["name"], bring):
                rep.add(where, "must-have skill '%s' is not named in 'What you bring'" % sk["name"])
        elif not skill_in_text(sk["name"], body):
            rep.add(where, "skill '%s' is not named anywhere in the description" % sk["name"])

    check_levels_in_text(job, by_head, tax, rep, where)

    # certifications and awards
    if lists_cert_or_award:
        lines = by_head[JD_CERT_HEADING][2]
        joined = "\n".join(lines)
        for name in job["certifications"]["required"]:
            hit = [ln for ln in lines if name in ln and "required" in ln.lower()]
            if not hit:
                rep.add(where, "required certification '%s' is not shown with the word 'required'" % name)
        for name in job["certifications"]["preferred"]:
            hit = [ln for ln in lines if name in ln and "preferred" in ln.lower()]
            if not hit:
                rep.add(where, "preferred certification '%s' is not shown with the word 'preferred'" % name)
        for kind in job["awards"]["preferred"]:
            label = tax.award_kinds[kind]["label"] if kind in tax.award_kinds else kind
            hit = [ln for ln in lines if label in ln and "preferred" in ln.lower()]
            if not hit:
                rep.add(where, "preferred award '%s' is not shown with the word 'preferred'" % label)
        # every certification that the text names must be in the data
        for cname in tax.certs:
            if cname in joined and cname not in job["certifications"]["required"] \
                    and cname not in job["certifications"]["preferred"]:
                rep.add(where, "the text names certification '%s' that the data does not list" % cname)

    # contact data
    for label, regex in (("a URL", URL_RE), ("an e-mail address", EMAIL_RE), ("a phone number", PHONE_RE)):
        m = regex.search(desc)
        if m:
            rep.add(where, "description looks like it has %s: %r" % (label, m.group(0)[:30]))
    return sections


# ---------------------------------------------------------------------------
# One job
# ---------------------------------------------------------------------------

def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def check_ascii(value, where, rep, path=""):
    if isinstance(value, str):
        try:
            value.encode("ascii")
        except UnicodeEncodeError:
            rep.add(where, "non-ASCII character in %s" % (path or "text"))
    elif isinstance(value, dict):
        for k, v in value.items():
            check_ascii(v, where, rep, "%s.%s" % (path, k) if path else k)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            check_ascii(v, where, rep, "%s[%d]" % (path, i))


def check_job(job, tax, rep, demo=False):
    where = job.get("key", "<no key>") if isinstance(job, dict) else "<job>"
    if not isinstance(job, dict):
        rep.add(where, "a job must be an object")
        return False
    expected_keys = list(JOB_KEYS)
    if demo:
        expected_keys.insert(1, "ownerDemo")
    if list(job.keys()) != expected_keys:
        missing = [k for k in expected_keys if k not in job]
        extra = [k for k in job if k not in expected_keys]
        rep.add(where, "keys differ from the schema (missing %s, extra %s, or wrong order)" % (missing, extra))
        return False
    check_ascii(job, where, rep)
    if demo and job["ownerDemo"] is not True:
        rep.add(where, "ownerDemo must be true")

    if not (isinstance(job["key"], str) and re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", job["key"])):
        rep.add(where, "key must be a lower-case slug")
    for k in ("title", "company", "area", "description"):
        if not isinstance(job[k], str) or not job[k].strip():
            rep.add(where, "%s must be a non-empty text" % k)
            return False
    low_company = job["company"].lower()
    for word in BLOCKED_COMPANY_WORDS:
        if re.search(r"\b%s\b" % re.escape(word), low_company):
            rep.add(where, "company name '%s' is a known brand or a placeholder name" % job["company"])
    if re.search(r"\b(pty|ltd|inc|llc)\b", low_company):
        rep.add(where, "company name must not use a company form (Pty, Ltd, Inc)")

    domain = job["domain"]
    if domain not in tax.domains:
        rep.add(where, "domain '%s' is not in the taxonomy" % domain)
        return False
    if job["specialisation"] not in tax.domains[domain]:
        rep.add(where, "specialisation '%s' is not a specialisation of %s" % (job["specialisation"], domain))
    level = job["level"]
    if level not in tax.levels:
        rep.add(where, "level '%s' is not in the taxonomy" % level)
        return False

    # title and level
    tl = job["title"].lower()
    if level in TITLE_LEVEL_WORDS:
        if not re.search(r"\b%s\b" % TITLE_LEVEL_WORDS[level], tl):
            rep.add(where, "title '%s' does not say the level %s" % (job["title"], level))
    else:
        for w in ALL_LEVEL_TITLE_WORDS:
            if re.search(r"\b%s\b" % re.escape(w), tl):
                rep.add(where, "a Mid job title must not contain the level word '%s'" % w)
    for lv, word in TITLE_LEVEL_WORDS.items():
        if lv != level and re.search(r"\b%s\b" % word, tl):
            rep.add(where, "title has the level word '%s' but the level is %s" % (word, level))

    # years
    mn, mx = job["minYears"], job["maxYears"]
    if not is_num(mn) or mn < 0:
        rep.add(where, "minYears must be a number from 0")
    else:
        lo, hi = MIN_YEARS_RANGE[level]
        if not (lo <= mn <= hi):
            rep.add(where, "minYears %s is outside %s to %s for level %s" % (mn, lo, hi, level))
        if mx is not None and (not is_num(mx) or mx <= mn):
            rep.add(where, "maxYears must be null or a number above minYears")
        if mx is not None and is_num(mx) and mx > 40:
            rep.add(where, "maxYears is too high")

    # type, mode, city, area
    if job["type"] not in JOB_TYPES:
        rep.add(where, "type '%s' is not one of %s" % (job["type"], JOB_TYPES))
    elif (level == "Intern") != (job["type"] == INTERN_TYPE):
        rep.add(where, "type must be '%s' for Intern jobs, and only for them (found '%s')" % (INTERN_TYPE, job["type"]))
    if job["workMode"] not in tax.work_modes:
        rep.add(where, "workMode '%s' is not in the taxonomy" % job["workMode"])
    if job["city"] not in tax.cities:
        rep.add(where, "city '%s' is not in the taxonomy" % job["city"])
    if job["workMode"] == "Remote":
        if job["city"] != "Remote" or job["area"] != REMOTE_AREA:
            rep.add(where, "a Remote job needs city 'Remote' and area '%s'" % REMOTE_AREA)
    else:
        if job["city"] == "Remote":
            rep.add(where, "an %s job needs a real city" % job["workMode"])
        elif job["area"] != AREA_BY_CITY.get(job["city"]):
            rep.add(where, "area '%s' does not match city %s (expected '%s')" % (job["area"], job["city"], AREA_BY_CITY.get(job["city"])))

    # salary
    sal = job["salary"]
    if not (isinstance(sal, dict) and list(sal.keys()) == ["min", "max", "unit"]):
        rep.add(where, "salary must be {min, max, unit}")
    else:
        if sal["unit"] not in ("year", "day", "hour"):
            rep.add(where, "salary unit must be year, day or hour")
        if not (is_int(sal["min"]) and is_int(sal["max"]) and 0 < sal["min"] < sal["max"]):
            rep.add(where, "salary min and max must be whole numbers with min below max")
        else:
            if job["type"] == "Contract":
                if sal["unit"] != "day":
                    rep.add(where, "a Contract job must have a day rate")
                else:
                    if not (DAY_RATE_RANGE[0] <= sal["min"] and sal["max"] <= DAY_RATE_RANGE[1]):
                        rep.add(where, "day rate %s-%s is outside %s-%s" % (sal["min"], sal["max"], DAY_RATE_RANGE[0], DAY_RATE_RANGE[1]))
                    lo, hi = DAY_BAND[level]
                    if sal["min"] < lo or sal["max"] > hi:
                        rep.add(where, "day rate %s-%s does not fit level %s (%s-%s)" % (sal["min"], sal["max"], level, lo, hi))
            else:
                if sal["unit"] != "year":
                    rep.add(where, "a %s job must have a yearly salary" % job["type"])
                else:
                    lo, hi = SALARY_BAND[level]
                    if sal["min"] < lo * (1 - SALARY_TOLERANCE) or sal["max"] > hi * (1 + SALARY_TOLERANCE):
                        rep.add(where, "salary %s-%s is outside the %s band %s-%s (+/- 15 percent)" % (sal["min"], sal["max"], level, lo, hi))

    # education
    if job["educationMin"] not in QUALIFICATIONS:
        rep.add(where, "educationMin '%s' is not in QUALIFICATIONS" % job["educationMin"])

    # posting and closing
    if demo:
        pr, cr = (1, 60), (-30, 45)
    else:
        pr, cr = (1, 21), (7, 45)
    if not (is_int(job["postedDaysAgo"]) and pr[0] <= job["postedDaysAgo"] <= pr[1]):
        rep.add(where, "postedDaysAgo must be a whole number from %d to %d" % pr)
    if not (is_int(job["closesInDays"]) and cr[0] <= job["closesInDays"] <= cr[1]):
        rep.add(where, "closesInDays must be a whole number from %d to %d" % cr)

    # occupation
    occ = job["occupation"]
    if not (isinstance(occ, dict) and list(occ.keys()) == ["code", "title"]):
        rep.add(where, "occupation must be {code, title}")
    else:
        o = tax.occupations.get(occ["code"])
        if o is None:
            rep.add(where, "occupation code '%s' is not in the taxonomy" % occ["code"])
        else:
            if o["title"] != occ["title"]:
                rep.add(where, "occupation title '%s' does not match the code (%s)" % (occ["title"], o["title"]))
            if o["domain"] != domain:
                rep.add(where, "occupation %s belongs to %s, not %s" % (occ["code"], o["domain"], domain))
            if job["specialisation"] not in o["specialisations"]:
                rep.add(where, "occupation %s does not cover the specialisation %s" % (occ["code"], job["specialisation"]))

    # skills
    skills = job["skills"]
    if not isinstance(skills, list) or not (7 <= len(skills) <= 12):
        rep.add(where, "a job needs 7 to 12 skills")
        return False
    names = []
    for sk in skills:
        if not (isinstance(sk, dict) and list(sk.keys()) == ["name", "level", "must"]):
            rep.add(where, "each skill must be {name, level, must}")
            return False
        names.append(sk["name"])
        if sk["name"] not in tax.skills:
            hint = ""
            if sk["name"].lower() in tax.alias_to_skill:
                hint = " (it is an alias of '%s'; use the canonical name)" % tax.alias_to_skill[sk["name"].lower()]
            rep.add(where, "skill '%s' is not a canonical taxonomy skill%s" % (sk["name"], hint))
        if not (is_int(sk["level"]) and 1 <= sk["level"] <= 5):
            rep.add(where, "skill '%s' level must be 1 to 5" % sk["name"])
        if not isinstance(sk["must"], bool):
            rep.add(where, "skill '%s' must be true or false" % sk["name"])
    if len(set(names)) != len(names):
        rep.add(where, "a skill is listed twice")
    musts = [s for s in skills if s["must"] is True]
    if not (3 <= len(musts) <= 8):
        rep.add(where, "a job needs 3 to 8 must-have skills (has %d)" % len(musts))
    in_domain = [n for n in names if n in tax.skills and domain in tax.skills[n]["domains"]]
    if len(in_domain) < 0.6 * len(names):
        rep.add(where, "only %d of %d skills belong to the domain %s" % (len(in_domain), len(names), domain))
    levels = [s["level"] for s in skills if is_int(s["level"])]
    if levels:
        avg = sum(levels) / float(len(levels))
        top, share_mid = max(levels), sum(1 for x in levels if 2 <= x <= 4) / float(len(levels))
        share_high = sum(1 for x in levels if x >= 3) / float(len(levels))
        if level == "Intern" and (top > 3 or avg > 2.6):
            rep.add(where, "Intern skill levels must be 1 to 3 (average %.1f, max %d)" % (avg, top))
        if level == "Junior" and (top > 3 or avg > 2.8):
            rep.add(where, "Junior skill levels must be 1 to 3 (average %.1f, max %d)" % (avg, top))
        if level == "Mid" and (top > 4 or share_mid < 0.75 or not (2.4 <= avg <= 3.9)):
            rep.add(where, "Mid skill levels must be mostly 2 to 4 (average %.1f, max %d)" % (avg, top))
        if level == "Senior" and (share_high < 0.7 or avg < 3.3 or top < 4):
            rep.add(where, "Senior skill levels must be mostly 3 to 5 (average %.1f)" % avg)
        if level == "Lead" and (share_high < 0.7 or avg < 3.6 or top < 4):
            rep.add(where, "Lead skill levels must be mostly 3 to 5 and higher (average %.1f)" % avg)
        if level == "Principal" and (avg < 4.0 or top < 5):
            rep.add(where, "Principal skill levels must be mostly 4 to 5 (average %.1f)" % avg)

    # certifications
    certs = job["certifications"]
    if not (isinstance(certs, dict) and list(certs.keys()) == ["required", "preferred"]
            and isinstance(certs["required"], list) and isinstance(certs["preferred"], list)):
        rep.add(where, "certifications must be {required: [], preferred: []}")
        return False
    if len(certs["required"]) > 2 or len(certs["preferred"]) > 2:
        rep.add(where, "a job lists at most 2 required and 2 preferred certifications")
    if set(certs["required"]) & set(certs["preferred"]):
        rep.add(where, "a certification is both required and preferred")
    for name in certs["required"] + certs["preferred"]:
        if name not in tax.certs:
            rep.add(where, "certification '%s' is not in the taxonomy" % name)
        elif domain not in tax.certs[name]["domains"]:
            rep.add(where, "certification '%s' does not belong to the domain %s" % (name, domain))

    # awards
    awards = job["awards"]
    if not (isinstance(awards, dict) and list(awards.keys()) == ["preferred"] and isinstance(awards["preferred"], list)):
        rep.add(where, "awards must be {preferred: []}")
        return False
    if len(awards["preferred"]) > 2:
        rep.add(where, "a job lists at most 2 preferred award kinds")
    for kind in awards["preferred"]:
        if kind not in tax.award_kinds:
            rep.add(where, "award kind '%s' is not in the taxonomy" % kind)

    check_jd(job, tax, rep, where)
    return True


# ---------------------------------------------------------------------------
# The whole catalogue
# ---------------------------------------------------------------------------

def signature(job):
    return tuple(sorted((s["name"], s["level"], s["must"]) for s in job["skills"]))


def check_catalogue(jobs, tax, rep):
    n = len(jobs)
    if n != 50:
        rep.add("jobs.json", "expected 50 jobs, found %d" % n)

    def count(field):
        return Counter(j[field] for j in jobs)

    # counts
    for label, expect, got in (("domain", EXPECT_DOMAIN, count("domain")),
                               ("specialisation", EXPECT_SPEC, count("specialisation")),
                               ("level", EXPECT_LEVEL, count("level"))):
        for key in sorted(set(expect) | set(got)):
            if got.get(key, 0) != expect.get(key, 0):
                rep.add("jobs.json", "%s '%s': expected %d, found %d" % (label, key, expect.get(key, 0), got.get(key, 0)))
    modes = count("workMode")
    for mode, (lo, hi) in RANGE_MODE.items():
        if not (lo <= modes.get(mode, 0) <= hi):
            rep.add("jobs.json", "work mode %s: %d jobs, expected %d to %d" % (mode, modes.get(mode, 0), lo, hi))
    cities = count("city")
    for city, (lo, hi) in RANGE_CITY.items():
        if not (lo <= cities.get(city, 0) <= hi):
            rep.add("jobs.json", "city %s: %d jobs, expected %d to %d" % (city, cities.get(city, 0), lo, hi))
    ac = cities.get("Adelaide", 0) + cities.get("Canberra", 0)
    if not (RANGE_ADELAIDE_CANBERRA[0] <= ac <= RANGE_ADELAIDE_CANBERRA[1]):
        rep.add("jobs.json", "Adelaide and Canberra together: %d jobs, expected %d to %d" % (ac, RANGE_ADELAIDE_CANBERRA[0], RANGE_ADELAIDE_CANBERRA[1]))
    if cities.get("Remote", 0) != modes.get("Remote", 0):
        rep.add("jobs.json", "Remote city count (%d) and Remote work mode count (%d) differ" % (cities.get("Remote", 0), modes.get("Remote", 0)))
    contracts = sum(1 for j in jobs if j["type"] == "Contract")
    if not (RANGE_CONTRACT[0] <= contracts <= RANGE_CONTRACT[1]):
        rep.add("jobs.json", "Contract jobs: %d, expected %d to %d" % (contracts, RANGE_CONTRACT[0], RANGE_CONTRACT[1]))

    # certificates and awards
    req = sum(1 for j in jobs if j["certifications"]["required"])
    pref = sum(1 for j in jobs if j["certifications"]["preferred"])
    none = sum(1 for j in jobs if not j["certifications"]["required"] and not j["certifications"]["preferred"])
    aw = sum(1 for j in jobs if j["awards"]["preferred"])
    for label, val, (lo, hi) in (("jobs with a required certification", req, RANGE_REQUIRED_CERT_JOBS),
                                 ("jobs with a preferred certification", pref, RANGE_PREFERRED_CERT_JOBS),
                                 ("jobs with no certification", none, RANGE_NO_CERT_JOBS),
                                 ("jobs with a preferred award kind", aw, RANGE_AWARD_JOBS)):
        if not (lo <= val <= hi):
            rep.add("jobs.json", "%s: %d, expected %d to %d" % (label, val, lo, hi))

    # uniqueness
    keys = Counter(j["key"] for j in jobs)
    for k, c in keys.items():
        if c > 1:
            rep.add("jobs.json", "duplicate key '%s'" % k)
    sigs = defaultdict(list)
    for j in jobs:
        sigs[signature(j)].append(j["key"])
    for s, ks in sigs.items():
        if len(ks) > 1:
            rep.add("jobs.json", "same skill set (skill, level, must) in %s" % ks)
    sal = defaultdict(list)
    for j in jobs:
        sal[(j["salary"]["min"], j["salary"]["max"], j["salary"]["unit"])].append(j["key"])
    for s, ks in sal.items():
        if len(ks) > 1:
            rep.add("jobs.json", "same salary range %s in %s" % (s, ks))
    titles = Counter((j["company"], j["title"]) for j in jobs)
    for t, c in titles.items():
        if c > 1:
            rep.add("jobs.json", "duplicate company and title %s" % (t,))
    posted = Counter(j["postedDaysAgo"] for j in jobs)
    for v, c in posted.items():
        if c > MAX_SAME_POSTED:
            rep.add("jobs.json", "postedDaysAgo %s is used %d times (maximum %d)" % (v, c, MAX_SAME_POSTED))

    # companies
    companies = Counter(j["company"] for j in jobs)
    if not (RANGE_COMPANIES[0] <= len(companies) <= RANGE_COMPANIES[1]):
        rep.add("jobs.json", "%d companies, expected %d to %d" % (len(companies), RANGE_COMPANIES[0], RANGE_COMPANIES[1]))
    for c, k in companies.items():
        if k > MAX_JOBS_PER_COMPANY:
            rep.add("jobs.json", "company %s has %d jobs (maximum %d)" % (c, k, MAX_JOBS_PER_COMPANY))
    many = sum(1 for k in companies.values() if k >= 2)
    if many < MIN_COMPANIES_WITH_MANY_JOBS:
        rep.add("jobs.json", "only %d companies post 2 or more jobs (need %d)" % (many, MIN_COMPANIES_WITH_MANY_JOBS))

    # one company must keep the same facts: same founding year and size in its 'About' paragraphs
    facts = defaultdict(set)
    for j in jobs:
        m = re.search(r"founded in (\d{4})", j["description"])
        s = re.search(r"about (\d+) (people|staff)", j["description"])
        facts[j["company"]].add((m.group(1) if m else None, s.group(1) if s else None))
    for c, f in facts.items():
        if len(f) > 1:
            rep.add("jobs.json", "company %s gives different founding year or size in its ads: %s" % (c, sorted(f, key=str)))

    # the same sentence in the ads of several companies
    owners = defaultdict(set)
    for j in jobs:
        for line in j["description"].split("\n"):
            line = line.strip()
            if not line or line.startswith("## "):
                continue
            line = line[2:] if line.startswith("- ") else line
            for sentence in sentences_of(line):
                norm = re.sub(r"\s+", " ", sentence.lower())
                if len(norm.split()) >= 6 and not norm.startswith(STRUCTURED_LINES):
                    owners[norm].add(j["company"])
    shared = [(s, c) for s, c in owners.items() if len(c) > MAX_SHARED_SENTENCE_COMPANIES]
    for s, c in sorted(shared)[:25]:
        rep.add("jobs.json", "the sentence %r is used by %d companies" % (s[:70], len(c)))
    if len(shared) > 25:
        rep.add("jobs.json", "... and %d more shared sentences" % (len(shared) - 25))

    # differentiation facts
    by_skill = defaultdict(set)
    for j in jobs:
        for s in j["skills"]:
            by_skill[s["name"]].add(s["level"])
    for k, v in by_skill.items():
        uses = sum(1 for j in jobs if any(s["name"] == k for s in j["skills"]))
        if uses >= 8 and len(v) < 3:
            rep.add("jobs.json", "skill '%s' is used in %d jobs with fewer than 3 different levels" % (k, uses))
        elif uses >= 5 and len(v) < 2:
            rep.add("jobs.json", "skill '%s' is used in %d jobs with the same level in all of them" % (k, uses))
    twins = near_twins(jobs)
    if not twins:
        rep.add("jobs.json", "no near-twin pair (same stack, different levels) found")
    return {"skills_by_level": by_skill, "twins": twins, "required": req, "preferred": pref, "none": none,
            "awards": aw, "contracts": contracts, "companies": companies, "posted": posted}


def near_twins(jobs):
    out = []
    for i in range(len(jobs)):
        for k in range(i + 1, len(jobs)):
            a, b = jobs[i], jobs[k]
            if a["specialisation"] != b["specialisation"] or a["level"] != b["level"]:
                continue
            sa = set(s["name"] for s in a["skills"])
            sb = set(s["name"] for s in b["skills"])
            jac = len(sa & sb) / float(len(sa | sb))
            if jac >= 0.75 and signature(a) != signature(b):
                out.append((a["key"], b["key"], round(jac, 2)))
    return out


def check_demo(demo, jobs, tax, rep):
    if not isinstance(demo, dict) or list(demo.keys()) != ["synthetic", "employer", "jobs"]:
        rep.add("demo.json", "top level keys must be synthetic, employer, jobs")
        return
    if demo["synthetic"] is not True:
        rep.add("demo.json", "synthetic must be true")
    emp = demo["employer"]
    if not (isinstance(emp, dict) and list(emp.keys()) == ["name", "company"]):
        rep.add("demo.json", "employer must be {name, company}")
        return
    if emp["name"] != "Alex Morgan":
        rep.add("demo.json", "employer name must be 'Alex Morgan'")
    dj = demo["jobs"]
    if not isinstance(dj, list) or len(dj) != 4:
        rep.add("demo.json", "expected 4 jobs")
        return
    main_keys = set(j["key"] for j in jobs)
    main_companies = set(j["company"] for j in jobs)
    if emp["company"] in main_companies:
        rep.add("demo.json", "the demo company must not be one of the 50 job companies")
    for j in dj:
        ok = check_job(j, tax, rep, demo=True)
        if not ok:
            continue
        if j["company"] != emp["company"]:
            rep.add(j["key"], "company must be the demo employer company")
        if j["key"] in main_keys:
            rep.add(j["key"], "key is also used in jobs.json")
    keys = [j.get("key") for j in dj]
    if len(set(keys)) != 4:
        rep.add("demo.json", "duplicate keys")
    try:
        open_jobs = [j for j in dj if j["closesInDays"] >= 0]
        closed = [j for j in dj if j["closesInDays"] < 0]
        if len(open_jobs) != 3 or len(closed) != 1:
            rep.add("demo.json", "expected 3 open jobs and 1 closed job")
        else:
            def has(level, spec, kind=None):
                return [j for j in open_jobs if j["level"] == level and j["specialisation"] == spec
                        and (kind is None or j["type"] == kind)]
            if not has("Mid", "Data engineering"):
                rep.add("demo.json", "missing an open Mid Data Engineer job")
            if not has("Senior", "Backend"):
                rep.add("demo.json", "missing an open Senior Backend Engineer job")
            soon = [j for j in has("Mid", "Machine learning engineering") if j["closesInDays"] == 4]
            if not soon:
                rep.add("demo.json", "missing an open Mid Machine Learning Engineer job with closesInDays 4")
            c = closed[0]
            if not (c["type"] == "Contract" and c["specialisation"] == "Data engineering"
                    and c["closesInDays"] == -2 and c["postedDaysAgo"] == 40):
                rep.add("demo.json", "the closed job must be a Contract Data Engineer job with closesInDays -2 and postedDaysAgo 40")
    except (KeyError, TypeError):
        pass


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def table(title, rows, widths):
    print("")
    print(title)
    for row in rows:
        print("  " + "".join(str(c).ljust(w) for c, w in zip(row, widths)).rstrip())


def print_summary(jobs, info, tax):
    print("Summary of jobs.json (%d jobs)" % len(jobs))
    c = Counter(j["domain"] for j in jobs)
    table("By domain", [(d, "%d of %d" % (c.get(d, 0), EXPECT_DOMAIN[d])) for d in EXPECT_DOMAIN], (30, 12))
    c = Counter(j["specialisation"] for j in jobs)
    table("By specialisation", [(s, "%d of %d" % (c.get(s, 0), EXPECT_SPEC[s])) for s in EXPECT_SPEC], (34, 12))
    c = Counter(j["level"] for j in jobs)
    table("By level", [(lv, "%d of %d" % (c.get(lv, 0), EXPECT_LEVEL[lv])) for lv in EXPECT_LEVEL], (14, 12))
    c = Counter(j["workMode"] for j in jobs)
    table("By work mode", [(m, "%d (%d to %d)" % (c.get(m, 0), RANGE_MODE[m][0], RANGE_MODE[m][1])) for m in RANGE_MODE], (14, 16))
    c = Counter(j["city"] for j in jobs)
    rows = [(city, c.get(city, 0)) for city in tax.cities]
    table("By city", rows, (14, 8))
    c = Counter(j["type"] for j in jobs)
    table("By type", [(t, c.get(t, 0)) for t in JOB_TYPES], (26, 8))
    lens = [len(j["description"]) for j in jobs]
    print("")
    print("Description length: min %d, average %d, max %d (limit %d to %d)" % (min(lens), sum(lens) // len(lens), max(lens), JD_LENGTH[0], JD_LENGTH[1]))
    print("Jobs with a required certification: %d, preferred: %d, none: %d" % (info["required"], info["preferred"], info["none"]))
    print("Jobs with a preferred award kind: %d" % info["awards"])
    print("Contract jobs: %d. Companies: %d (most jobs for one company: %d)" % (info["contracts"], len(info["companies"]), max(info["companies"].values())))
    print("Posting age: %d different values, most used %d times" % (len(info["posted"]), max(info["posted"].values())))
    years = sorted(set((j["minYears"], j["maxYears"]) for j in jobs), key=lambda t: (t[0], 99 if t[1] is None else t[1]))
    print("Different years ranges: %d" % len(years))
    bylev = defaultdict(list)
    for j in jobs:
        s = j["salary"]
        if s["unit"] == "year":
            bylev[j["level"]].append((s["min"], s["max"]))
    rows = []
    for lv in EXPECT_LEVEL:
        v = bylev.get(lv, [])
        if v:
            rows.append((lv, len(v), "%d-%d" % (min(x[0] for x in v), max(x[1] for x in v))))
    table("Yearly salary by level (min-max)", rows, (12, 6, 20))
    days = [j["salary"] for j in jobs if j["salary"]["unit"] == "day"]
    if days:
        print("Day rates: %d to %d" % (min(d["min"] for d in days), max(d["max"] for d in days)))
    print("Near-twin pairs: %s" % ", ".join("%s / %s (%.2f)" % t for t in info["twins"]))
    print("Skills used: %d of %d taxonomy skills" % (len(info["skills_by_level"]), len(tax.skills)))


def main():
    rep = Report()
    tax_data = load_json(TAXONOMY_PATH, "taxonomy", rep, strict=False)
    if tax_data is None:
        print("PROBLEMS: cannot read the taxonomy")
        for e in rep.errors:
            print("  " + e)
        return 1
    tax = Taxonomy(tax_data)
    data = load_json(JOBS_PATH, "jobs.json", rep)
    demo = load_json(DEMO_PATH, "demo.json", rep)
    info = None
    jobs = []
    if isinstance(data, dict):
        if list(data.keys()) != ["synthetic", "note", "jobs"]:
            rep.add("jobs.json", "top level keys must be synthetic, note, jobs")
        if data.get("synthetic") is not True:
            rep.add("jobs.json", "synthetic must be true")
        if not isinstance(data.get("note"), str) or "synthetic" not in data.get("note", "").lower():
            rep.add("jobs.json", "note must say that the data is synthetic")
        jobs = data.get("jobs") if isinstance(data.get("jobs"), list) else []
        good = [j for j in jobs if check_job(j, tax, rep)]
        if len(good) == len(jobs):
            info = check_catalogue(jobs, tax, rep)
    elif data is not None:
        rep.add("jobs.json", "the file must be an object")
    if demo is not None:
        check_demo(demo, jobs, tax, rep)
    if info is not None:
        print_summary(jobs, info, tax)
    print("")
    if rep.errors:
        print("PROBLEMS (%d):" % len(rep.errors))
        for e in rep.errors:
            print("  " + e)
        return 1
    print("OK: jobs.json and demo.json are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
