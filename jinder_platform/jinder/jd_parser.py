"""Read a job description text and pre-fill the "Post a job" form (Feature 6; version 2: item R1).

The result is a DRAFT. Nothing is posted until the employer sends the form. The text is DATA:
nothing in it is followed as an instruction (AI_Rule Rule 5, item 10).

Version 2 adds (each key only when the text shows it): level, minYears, maxYears, workMode, skillRequirements [{name, level, must}],
certifications {required, preferred}, awards {preferred: [award kind]}, educationMin, specialisation. And the key domain (one of the
3 domains). The description keeps its line breaks and uses the markup of the platform: "## Heading" lines and "- " bullet lines.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

from . import cv_lexicon
from . import reference as R
from .cv_parser import _INDUSTRY_RE, _QUAL_ORDER, _QUAL_RULES, level_from_skill_years

_CATEGORY_OF_INDUSTRY = getattr(R, "INDUSTRY_TO_CATEGORY", {})
# The description is never cut here. The server refuses a text that is longer than 10,000 characters (the employer can shorten it).
# This number only limits the text that goes to the skill finder.
_SKILL_FINDER_CHARS = 10000


def suggest_skills(title: str, text: str) -> List[str]:
    """The skill names for the form field "skills" (the finder of the catalogue, which the employer button "Suggest skills" also uses).
    The catalogue is loaded when it is needed. If it cannot be loaded, the skills of the taxonomy that the text shows are used."""
    try:
        from .catalogue import suggest_skills as finder
        return finder(title, text)
    except Exception:  # noqa: BLE001 - the reader must not stop because another part of the platform is not ready
        return [name for _, name in cv_lexicon.get().skills_in(f"{title} {text}")][:10]

_LABELLED_TITLE = re.compile(r"^(?:position|job title|role title|role|title|vacancy)\s*[:\-–]\s*(.{3,80})$", re.I)
_SALARY_RE = re.compile(
    r"\$\s?(\d[\d,]*(?:\.\d+)?)\s*(k)?\s*(?:-|–|—|to)\s*\$?\s?(\d[\d,]*(?:\.\d+)?)\s*(k)?(?:\s*(?:per|a|/|p\.?)\s*(year|annum|yr|hour|hr|day|week)\b)?", re.I)
_SINGLE_SALARY_RE = re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?)\s*(k)?\s*(?:per|a|/|p\.?)\s*(year|annum|yr|hour|hr|day|week)\b", re.I)


def _number(text: str, k: Optional[str]) -> float:
    value = float(text.replace(",", ""))
    return value * 1000 if k else value


def _unit(value: float, unit: Optional[str]) -> str:
    u = (unit or "").lower()
    if u in ("hour", "hr"):
        return "per hour"
    if u == "day":
        return "per day"
    if u == "week":
        return "per week"
    if u in ("year", "annum", "yr"):
        return "per year"
    return "per hour" if value < 1000 else "per year"


def _money(n: float) -> str:
    return f"${n:,.0f}"


def read_salary(text: str) -> str:
    m = _SALARY_RE.search(text)
    if m:
        a, b = _number(m.group(1), m.group(2)), _number(m.group(3), m.group(4) or m.group(2))
        if m.group(4) and not m.group(2) and a < 1000 <= b:
            a *= 1000   # "$80-100k": the "k" is for both numbers
        if 10 <= a <= b <= 2_000_000:
            span = _money(a) if a == b else f"{_money(a)} – {_money(b)}"
            return f"{span} {_unit(b, m.group(5))}"
    m = _SINGLE_SALARY_RE.search(text)
    if m:
        a = _number(m.group(1), m.group(2))
        if 10 <= a <= 2_000_000:
            return f"{_money(a)} {_unit(a, m.group(3))}"
    return ""


def read_type(text: str) -> str:
    low = text.lower()
    if re.search(r"\b(graduate program|graduate role|internship|intern\b|traineeship)", low):
        return "Graduate / Internship"
    if re.search(r"\b(contract|fixed[- ]term|temporary)\b", low):
        return "Contract"
    if re.search(r"\b(part[- ]time|casual)\b", low):
        return "Part-time"
    if re.search(r"\b(full[- ]time|permanent)\b", low):
        return "Full-time"
    return ""


def read_location(text: str) -> str:
    cities = [(m.start(), c) for c in R.LOCATIONS if c != "Remote" for m in [re.search(rf"\b{c}\b", text)] if m]
    if cities:
        return min(cities)[1]
    if re.search(r"\bremote\b|work from home|work-from-home", text, re.I):
        return "Remote"
    return ""


def read_category(title: str, text: str) -> str:
    """The category of the job. A domain of the taxonomy (Software Engineering, AI & Machine Learning, Data) when the platform has it as a category.
    Else the category of the old list."""
    domain = read_domain(title, text)[0]
    if domain and domain in getattr(R, "JOB_CATEGORIES", []):
        return domain
    scores: Dict[str, int] = {}
    for industry, rx in _INDUSTRY_RE.items():
        cat = _CATEGORY_OF_INDUSTRY.get(industry)
        if not cat:
            continue
        hits = len(rx.findall(title)) * 3 + len(set(m.group(0).lower() for m in rx.finditer(text)))
        if hits:
            scores[cat] = scores.get(cat, 0) + hits
    return max(scores, key=lambda c: (scores[c], c)) if scores else ""


def read_domain(title: str, text: str) -> Tuple[str, str]:
    """(domain, specialisation) of the job: the specialisation of the taxonomy that the title and the text show best."""
    return cv_lexicon.get().domain_and_specialisation(title, text)


def read_title(lines: List[str]) -> str:
    for line in lines[:12]:
        m = _LABELLED_TITLE.match(line)
        if m:
            return m.group(1).strip(" .")
    for line in lines[:6]:
        words = line.split()
        if line.startswith("#"):
            continue
        if 1 < len(words) <= 10 and len(line) <= 90 and not line.endswith((".", ":")) and not re.search(r"@|https?://|^\W*(about|we are|our|join)\b", line, re.I):
            return re.sub(r"\s+", " ", line).strip(" -–—|")
    return ""


# =====================================================================
# The parts of a job description
# =====================================================================
_PARTS = [
    ("do", r"what you will do|what you'll do|responsibilities|key responsibilities|the role|about the role|your role|duties|day to day|about the team|the team|"
           r"role overview|position summary|job description|overview|summary|about the position|about the job"),
    ("must", r"what you bring|what you'll bring|requirements|key requirements|minimum requirements|qualifications|must have|essential|required|required skills|"
            r"about you|who you are|skills and experience|skills|what we are looking for|what we're looking for|what you'll need|what you will need|you have|"
            r"your profile|experience and skills|your skills|what you need|selection criteria"),
    ("nice", r"nice to have|preferred|preferred qualifications|preferred skills|bonus|bonus points|desirable|advantageous|a plus|pluses|extras|additional skills|it would be great if"),
    ("stack", r"tech stack|technology stack|our stack|tech we use|technologies|tools and technologies|the stack|our tech"),
    ("certs", r"certifications and awards|certifications|awards"),
    ("offer", r"what we offer|benefits|perks|why join us|compensation|what's in it for you|salary and benefits|what you get|our offer"),
    ("hire", r"how we hire|how to apply|our hiring process|our process|application process|interview process|next steps"),
    ("company", r"about the company|about us|who we are|our story|our mission|our company|about [a-z][\w&.' -]{2,40}"),
]
_PART_RE = [(kind, re.compile(rf"^(?:{rx})$")) for kind, rx in _PARTS]


_BULLET_LINE = re.compile(r"^\s*(?:[-•·▪●○◦‣*–—]|\d{1,2}[.)])\s+(\S.*)$")
_SMALL_WORDS = {"of", "in", "and", "for", "the", "a", "an", "to", "on", "at", "or", "with", "you", "we", "our", "your", "is", "are"}


def _jd_raw_lines(text: str) -> List[str]:
    """The lines of a job description. The blank lines stay (one for a run of blank lines). No line is cut."""
    out: List[str] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "").split("\n")[:6000]:
        line = re.sub(r"[ \t\f\v]+", " ", raw).strip()
        if line or (out and out[-1]):
            out.append(line)
    while out and not out[-1]:
        out.pop()
    return out


def _heading_of(line: str, next_line: str = "") -> Optional[Tuple[str, str]]:
    """(part kind, heading text) if the line is a heading of a job description, else None.
    A line of the markup ("## ...") is a heading, with any name. A line with a known name (also in capitals, with a colon) is a heading.
    A short line that ends with a colon, or a short line in capitals, or a short line in title case that has a bullet or a long paragraph under it,
    is a heading too. A heading that is not a known one has the kind "other"."""
    text = line.strip()
    marked = re.match(r"^#{1,6}\s+(.+?)\s*#*$", text)
    bold = re.match(r"^\*\*(.+?)\*\*:?$", text)
    raw = (marked or bold).group(1).strip() if (marked or bold) else text
    if not raw:
        return None
    if not (marked or bold):
        if _BULLET_LINE.match(text) or len(raw) > 60 or len(raw.split()) > 7 or raw.endswith((".", ",", ";", "!", "?")) or re.search(r"[$%@]|https?:", raw):
            return None
    key = re.sub(r"\s+", " ", re.sub(r"[^a-z' ]", " ", raw.lower().replace("&", " and "))).strip()
    if not key:
        return ("other", raw.rstrip(":")) if marked or bold else None
    words = raw.split()
    letters = re.sub(r"[^A-Za-z]", "", raw)
    shown = raw.rstrip(":").strip()
    if not (marked or bold) and len(letters) >= 4 and shown == shown.upper():
        shown = shown.capitalize()                  # a heading in capitals is written in normal letters
    for kind, rx in _PART_RE:
        if rx.match(key):
            return kind, shown
    if marked or bold:
        return "other", shown
    if raw.endswith(":") and len(words) <= 6 and ":" not in raw[:-1]:
        return "other", shown
    if len(letters) >= 4 and raw == raw.upper() and len(words) <= 6 and not re.search(r"\d", raw):
        return "other", shown
    nxt = next_line.strip()
    if re.search(r"\d", raw) or not raw[:1].isupper():
        return None
    if 2 <= len(words) <= 6 and _BULLET_LINE.match(nxt):
        return "other", shown                       # a short line right before a list of bullets
    if 2 <= len(words) <= 5 and all(w[:1].isupper() or w.lower() in _SMALL_WORDS for w in words) and len(nxt) > 70:
        return "other", shown                       # a short line in title case before a paragraph
    return None


def _next_text(lines: List[str], i: int) -> str:
    for j in range(i + 1, min(i + 4, len(lines))):
        if lines[j].strip():
            return lines[j]
    return ""


def _parts(lines: List[str]) -> List[Tuple[str, str]]:
    """Each line with the kind of the part that it is in: [(kind, line)]. A heading line has the kind "heading:<kind>"."""
    out: List[Tuple[str, str]] = []
    kind = "do"
    for i, line in enumerate(lines):
        h = _heading_of(line, _next_text(lines, i))
        if h:
            kind = h[0]
            out.append(("heading:" + kind, h[1]))
        else:
            out.append((kind, line))
    return out


def _description_markup(raw_lines: List[str]) -> str:
    """The text of the job in the markup of the platform: "## Heading" lines, "- " bullet lines, a blank line between the blocks.
    The paragraphs stay as lines. Nothing is cut and nothing is added: a text that has no headings gets no headings."""
    items: List[Tuple[str, str]] = []
    for i, line in enumerate(raw_lines):
        if not line.strip():
            items.append(("blank", ""))
            continue
        h = _heading_of(line, _next_text(raw_lines, i))
        if h:
            items.append(("heading", h[1]))
            continue
        bullet = _BULLET_LINE.match(line)
        items.append(("bullet", bullet.group(1).strip()) if bullet else ("para", line.strip()))
    out: List[str] = []
    prev = "blank"
    for kind, text in items:
        if kind == "blank":
            if out and out[-1] != "":
                out.append("")
            prev = "blank"
            continue
        if out and out[-1] != "" and (kind == "heading" or prev == "heading" or {prev, kind} == {"para", "bullet"}):
            out.append("")
        out.append("## " + text if kind == "heading" else "- " + text if kind == "bullet" else text)
        prev = kind
    return "\n".join(out).strip()


# =====================================================================
# Years of experience
# =====================================================================
_NUMWORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
             "fifteen": 15, "twenty": 20}
_NUM = r"(\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty)"
_YEARS = r"(?:years?|yrs?)"
_YR_RANGE = re.compile(rf"\b{_NUM}\s*(?:to|-|–|—)\s*{_NUM}\s*\+?\s*{_YEARS}\b", re.I)
_YR_MIN_PLUS = re.compile(rf"\b{_NUM}\s*(?:\+|or more|plus|or above)\s*{_YEARS}\b", re.I)
_YR_MIN_WORD = re.compile(rf"\b(?:at least|minimum(?: of)?|min\.?|over|more than|no less than)\s+{_NUM}\s*{_YEARS}\b", re.I)
_YR_PLAIN = re.compile(rf"\b{_NUM}\s*{_YEARS}\b(?!\s*(?:old|ago|warranty))", re.I)
_YR_MAX = re.compile(rf"\b(?:up to|no more than|maximum(?: of)?|under|less than|fewer than)\s+{_NUM}\s*{_YEARS}\b", re.I)
_EXPERIENCE_WORDS = re.compile(r"^\s*(?:of\s+|in\s+|as\s+|working|with\s+|using\s+|on\s+|doing\s+|within\s+|building\s+|[a-z-]+\s+(?:work|experience))", re.I)


def _n(token: str) -> int:
    return int(token) if token.isdigit() else _NUMWORDS.get(token.lower(), 0)


def read_years(text_lines: List[Tuple[str, str]], lex: cv_lexicon.Lexicon) -> Tuple[Optional[int], Optional[int]]:
    """(minYears, maxYears) of the job: "5+ years" gives (5, None), "3-5 years" gives (3, 5), "up to 2 years" gives (None, 2).
    Years with one skill ("3 years with Kubernetes") are for the skill, not for the job. The lines of the part "What you bring" come first."""
    order = ["must", "do", "other", "nice", "certs", "stack"]
    for wanted in order:
        for kind, line in text_lines:
            if kind != wanted:
                continue
            for rx, mode in ((_YR_MAX, "max"), (_YR_RANGE, "range"), (_YR_MIN_PLUS, "min"), (_YR_MIN_WORD, "min"), (_YR_PLAIN, "min")):
                for m in rx.finditer(line):
                    after = line[m.end():m.end() + 60]
                    if not _EXPERIENCE_WORDS.match(after) and not re.search(r"experience", line, re.I):
                        continue
                    tail = re.match(r"\s*(?:of\s+)?(?:experience\s+)?(?:(in)\s+|(with|using|on)\s+)?(.{0,40})", after, re.I)
                    hit = lex.skills_in(tail.group(3))[:1] if tail else []
                    about_work = re.match(r"^\S+(?:\s\S+)?\s+(?:work|development|delivery|engineering|projects?|programming)\b", tail.group(3)) if tail else None
                    if hit and hit[0][0] < 2 and lex.skill_kind(hit[0][1]) == "hard" and (tail.group(2) or lex.is_tool(hit[0][1])) and not about_work:
                        continue            # "3 years with Kubernetes", "3 years in Python": a skill, not the job. "5 years in machine learning", "4 years of .NET work" are the job.
                    if mode == "range":
                        a, b = _n(m.group(1)), _n(m.group(2))
                        if 0 <= a <= b <= 40:
                            return a, b
                    elif mode == "max":
                        if 0 < _n(m.group(1)) <= 40:
                            return None, _n(m.group(1))
                    elif 0 <= _n(m.group(1)) <= 40:
                        return _n(m.group(1)), None
    return None, None


# =====================================================================
# Level, work mode, education
# =====================================================================
_LEVEL_LABEL = re.compile(r"\b(?:level|seniority|experience level|career level)\s*[:\-–]\s*([A-Za-z -]{3,30})", re.I)
# Only phrases that name the level of THIS job ("a senior-level role"). A word like "lead engineer" can be about another person.
_LEVEL_PHRASES = [
    ("Intern", r"\b(?:paid internship|internship program|work experience placement|traineeship|cadetship)\b"),
    ("Principal", r"\b(?:an?|this is an?) principal[- ](?:level )?(?:role|position|opportunity)\b"),
    ("Lead", r"\b(?:an?|this is an?) (?:lead|staff)[- ](?:level )?(?:role|position|opportunity)\b"),
    ("Senior", r"\b(?:an?|this is an?) senior[- ](?:level )?(?:role|position|opportunity)\b|\bsenior[- ]level (?:role|position)\b"),
    ("Mid", r"\b(?:an?|this is an?) (?:mid|intermediate)[- ](?:level )?(?:role|position|opportunity)\b"),
    ("Junior", r"\b(?:an?|this is an?) (?:junior|entry|graduate)[- ](?:level )?(?:role|position|opportunity|program)\b|\bearly[- ]career (?:role|position)\b"),
]


def read_level(title: str, text: str, min_years: Optional[int], lex: cv_lexicon.Lexicon) -> str:
    """The level of the job. 1 the level words of the title  2 a label ("Seniority: Senior")  3 phrases ("a senior-level role")
    4 the years that the job asks for (under 2: Junior, 2 to 4: Mid, 5 and more: Senior)."""
    level = lex.level_of_title(title)
    if level:
        return level
    m = _LEVEL_LABEL.search(text)
    if m:
        level = lex.level_of_title(m.group(1))
        if level:
            return level
    for name, rx in _LEVEL_PHRASES:
        if re.search(rx, text, re.I):
            return name
    if min_years is not None:
        return "Junior" if min_years < 2 else "Mid" if min_years < 5 else "Senior"
    return ""


def read_work_mode(text: str) -> str:
    """Remote, Hybrid or Onsite. "Hybrid" wins when it is in the text. The first mode that the text names wins, otherwise."""
    if re.search(r"\bhybrid\b|\b(?:one|two|three|four|1|2|3|4)\s+days?\s+(?:a|per|each|every)\s+week\s+(?:in|at)\s+the\s+office", text, re.I):
        return "Hybrid"
    hits = []
    for mode, rx in (("Remote", r"\bfully remote\b|\b100% remote\b|remote[- ]first|work(?:ing)? from (?:home|anywhere)|\bremote\b"),
                     ("Onsite", r"\bon[- ]?site\b|\bin[- ]office\b|office[- ]based|\bin the office\b|\bfive days (?:a|per) week (?:in|at) the office\b")):
        m = re.search(rx, text, re.I)
        if m:
            hits.append((m.start(), mode))
    return min(hits)[1] if hits else ""


def read_education(lines: List[Tuple[str, str]]) -> str:
    """The lowest qualification that the job asks for ("a master's degree or a PhD" is the master's degree). A qualification that is only
    preferred is not a minimum."""
    found: List[str] = []
    for kind, line in lines:
        if kind in ("offer", "company", "hire") or kind.startswith("heading:"):
            continue
        if not re.search(r"degree|diploma|phd|doctorate|bachelor|master|certificate (?:iii|iv)|high school|secondary school|year 12|\bmba\b", line, re.I):
            continue
        if kind == "nice" or re.search(r"\b(?:preferred|nice to have|a plus|bonus|desirable|advantageous)\b", line, re.I):
            continue
        for fragment in re.split(r"\s+or\s+|,|;|\band\b", line):
            label = None
            low = fragment.lower()
            for rx, name in _QUAL_RULES:
                if rx.search(low):
                    label = name
                    break
            if label is None and re.search(r"\bdegree\b", low):
                label = "Bachelor's degree"
            if label:
                found.append(label)
    return max(found, key=lambda q: _QUAL_ORDER.get(q, 99)) if found else ""


# =====================================================================
# Skills, certifications, awards
# =====================================================================
_LEVEL_WORDS = [
    (5, re.compile(r"\bexpert\b", re.I)),
    (4, re.compile(r"\badvanced\b|\bstrong\b|\bdeep\b|\bextensive\b", re.I)),
    (3, re.compile(r"\bproficient\b|\bsolid\b|\bgood\b|\bhands[- ]on\b|\bintermediate\b", re.I)),
    (2, re.compile(r"\bworking (?:knowledge|level)\b|\bfamiliar(?:ity)?\b|\bbasic\b", re.I)),
    (1, re.compile(r"\bexposure\b|\bawareness\b|\bbeginner\b", re.I)),
]
_OF_FIVE = re.compile(r"\b([1-5])\s+of\s+5\b|\b([1-5])\s*/\s*5\b")
_NICE_CUE = re.compile(r"\b(?:nice to have|preferred|preferably|bonus|a plus|desirable|advantageous|advantage|beneficial|optional|welcome|valued|would be great)\b", re.I)
_MUST_CUE = re.compile(r"\b(?:must|required|essential|mandatory|need to|needs to|you have|you hold)\b", re.I)


def _line_level(line: str) -> Optional[int]:
    m = _OF_FIVE.search(line)
    if m:
        return int(m.group(1) or m.group(2))
    for level, rx in _LEVEL_WORDS:
        if rx.search(line):
            return level
    return None


def read_skill_requirements(lines: List[Tuple[str, str]], lex: cv_lexicon.Lexicon) -> List[Dict[str, Any]]:
    """The skills of the list that the job names: {name, level 1 to 5, must}. A skill in the parts "What you bring" is a must.
    A skill in "Nice to have" or "Tech stack", or only in the list of tasks, is not. The level comes from the words next to the skill
    ("at an advanced level (4 of 5)", "5+ years of Python"). Without a word, the level is 3 (Proficient)."""
    found: Dict[str, Dict[str, Any]] = {}
    for kind, line in lines:
        if kind.startswith("heading:") or kind in ("offer", "company", "hire", "certs"):
            continue
        names = [n for _, n in lex.skills_in(line, hard_only=False)]
        if not names:
            continue
        must = kind == "must"
        if _NICE_CUE.search(line):
            must = False
        elif _MUST_CUE.search(line) and kind in ("do", "other"):
            must = True
        level = _line_level(line)
        ym = re.search(rf"\b{_NUM}\s*\+?\s*{_YEARS}\b", line, re.I)
        for name in names:
            lv = level
            if lv is None and ym and len(names) == 1:
                lv = level_from_skill_years(float(_n(ym.group(1))))
            entry = found.get(name)
            if entry is None:
                found[name] = {"name": name, "level": lv, "must": must}
            else:
                entry["must"] = entry["must"] or must
                if lv is not None and (entry["level"] is None or lv > entry["level"]):
                    entry["level"] = lv
    out = []
    for entry in found.values():
        out.append({"name": entry["name"], "level": entry["level"] if entry["level"] is not None else 3, "must": entry["must"]})
    return out[:12]


def read_certifications(lines: List[Tuple[str, str]], lex: cv_lexicon.Lexicon) -> Dict[str, List[str]]:
    """The certifications of the list that the job names, as {required, preferred}. A line or a part that says "preferred" or "nice to have"
    makes a certification preferred. "Required", "must", "essential" or the part "What you bring" makes it required."""
    required: List[str] = []
    preferred: List[str] = []
    for kind, line in lines:
        if kind.startswith("heading:") or kind in ("offer", "company", "hire"):
            continue
        for cert in lex.find_certs(line):
            name = cert["name"]
            if re.search(r"\brequired certification\b", line, re.I) or (_MUST_CUE.search(line) and not _NICE_CUE.search(line)) or (kind == "must" and not _NICE_CUE.search(line)):
                if name not in required:
                    required.append(name)
            elif name not in preferred:
                preferred.append(name)
    preferred = [p for p in preferred if p not in required]
    return {"required": required[:6], "preferred": preferred[:6]}


def read_awards(lines: List[Tuple[str, str]], lex: cv_lexicon.Lexicon) -> List[str]:
    """The kinds of awards that the job likes ("Preferred award kind: Hackathon"). A line about prizes, hackathons, papers or patents that says
    that they are a plus gives a kind too."""
    kinds: List[str] = []
    for kind, line in lines:
        if kind.startswith("heading:") or kind in ("offer", "company", "hire"):
            continue
        explicit = re.search(r"\b(?:preferred|nice to have)\s+award(?:s| kinds?)?\s*:?\s*(.+)$|\bawards?(?: kinds?)? (?:we|that we) (?:value|like|prefer)\s*:?\s*(.+)$", line, re.I)
        if explicit:
            found = lex.award_kinds_in(explicit.group(1) or explicit.group(2))
        elif kind in ("nice", "certs") and re.search(r"award|prize|hackathon|kaggle|competition|patent|publication|paper|conference|open[- ]source|scholarship|dean's list|speaker", line, re.I) \
                or (re.search(r"hackathon|kaggle|patents?|publications?|open[- ]source contributions?", line, re.I) and _NICE_CUE.search(line)):
            found = lex.award_kinds_in(line)
        else:
            continue
        for item in found:
            if item not in kinds:
                kinds.append(item)
    return kinds[:6]


# =====================================================================
# Main entry
# =====================================================================
FIELD_ORDER = ["title", "category", "location", "type", "salary", "description", "skills"]
_NEW_ORDER = ["level", "specialisation", "minYears", "maxYears", "workMode", "skillRequirements", "certifications", "awards", "educationMin", "domain"]


def parse_jd(text: str) -> Dict[str, Any]:
    lex = cv_lexicon.get()
    raw = _jd_raw_lines(text)
    lines = [l for l in raw if l]
    title = read_title(lines)
    body_raw = [l for l in raw if not _LABELLED_TITLE.match(l)]
    first = next((k for k, l in enumerate(body_raw) if l), None)
    if title and first is not None and body_raw[first].strip(" -–—|") == title:
        body_raw = body_raw[first + 1:]
    body_lines = [l for l in body_raw if l]
    description = _description_markup(body_raw)
    flat = re.sub(r"\s+", " ", " ".join(body_lines)).strip()
    parts = _parts(body_lines)
    fields: Dict[str, Any] = {}
    if title and len(title) >= 3:
        fields["title"] = title
    category = read_category(title, text)
    if category:
        fields["category"] = category
    location = read_location(text)
    if location:
        fields["location"] = location
    work_type = read_type(text)
    if work_type:
        fields["type"] = work_type
    salary = read_salary(text)
    if salary:
        fields["salary"] = salary
    if len(description) >= 30:
        fields["description"] = description
    skills = suggest_skills(title, flat[:_SKILL_FINDER_CHARS])
    if skills:
        fields["skills"] = skills
    # ----- version 2 -----
    min_years, max_years = read_years(parts, lex)
    if min_years is not None:
        fields["minYears"] = min_years
    if max_years is not None and (min_years is None or max_years >= min_years):
        fields["maxYears"] = max_years
    level = read_level(title, text, min_years, lex)
    if level:
        fields["level"] = level
    mode = read_work_mode(text)
    if mode:
        fields["workMode"] = mode
    requirements = read_skill_requirements(parts, lex)
    if requirements:
        fields["skillRequirements"] = requirements
    certs = read_certifications(parts, lex)
    if certs["required"] or certs["preferred"]:
        fields["certifications"] = certs
    awards = read_awards(parts, lex)
    if awards:
        fields["awards"] = {"preferred": awards}
    education = read_education(parts)
    if education:
        fields["educationMin"] = education
    domain, specialisation = read_domain(title, flat)
    if specialisation:
        fields["specialisation"] = specialisation
    if domain:
        fields["domain"] = domain
    detected = [k for k in FIELD_ORDER if k in fields] + [k for k in _NEW_ORDER if k in fields]
    missing = [k for k in ["title", "category", "location", "type", "salary", "description"] if k not in fields]
    return {"fields": fields, "detected": detected, "missing": missing}
