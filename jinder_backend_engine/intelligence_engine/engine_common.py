#!/usr/bin/env python3
"""
Jinder Intelligence Engine - shared helpers (not a formula).
Standard: ASD-STE100 (Simplified Technical English)

This file holds the parts that all six formulas need:
  1. The taxonomy index (skills, aliases, related skills, occupations, certifications, awards, levels).
     The engine reads `../data/reference/ict_taxonomy.json` itself. If the file is missing, it uses simple defaults.
  2. The input cleaners (`prepare_candidate`, `prepare_job`). They accept the old dictionary shapes and the version 2 shapes.
  3. The smooth math functions (logistic, saturation, linear interpolation).
  4. The loader that lets one formula file use another one (the file names start with a digit, so `import` cannot load them).

Privacy: this file never reads a name, an email, a phone number, a country, a nationality, a visa, an age, a gender or a photo.
Standard library only. Python 3.9 compatible.
"""

import datetime
import functools
import importlib.util
import json
import math
import os
import re
import sys
import threading
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TAXONOMY_PATH = os.path.normpath(os.path.join(ENGINE_DIR, "..", "data", "reference", "ict_taxonomy.json"))

SIBLING_FILES = {
    "f1": "01_skill_matching_model.py",
    "f2": "02_skill_gap_analysis.py",
    "f3": "03_job_to_job_comparison.py",
    "f4": "04_candidate_benchmarking.py",
    "f5": "05_job_seeker_ranking_feed.py",
    "f6": "06_recruiter_candidate_ranking.py",
}
_LOCK = threading.RLock()


# =====================================================================
# 1. SMOOTH MATH FUNCTIONS
# =====================================================================

def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Keeps x between lo and hi."""
    return lo if x < lo else (hi if x > hi else x)


def logistic(x: float, mid: float = 0.0, k: float = 1.0) -> float:
    """S-curve from 0 to 1: 1 / (1 + exp(-k (x - mid)))."""
    z = -k * (x - mid)
    if z > 60.0:
        return 0.0
    if z < -60.0:
        return 1.0
    return 1.0 / (1.0 + math.exp(z))


def sat(x: float, scale: float) -> float:
    """Saturation curve from 0 to 1: 1 - exp(-x / scale). Negative x gives 0."""
    return 1.0 - math.exp(-max(0.0, float(x)) / max(1e-9, float(scale)))


def lerp_table(x: float, points: Sequence[Tuple[float, float]]) -> float:
    """Linear interpolation through sorted control points. Outside the range it keeps the end value."""
    if x <= points[0][0]:
        return float(points[0][1])
    if x >= points[-1][0]:
        return float(points[-1][1])
    for i in range(1, len(points)):
        x0, y0 = points[i - 1]
        x1, y1 = points[i]
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0) if x1 > x0 else float(y1)
    return float(points[-1][1])


def r1(x: Optional[float]) -> Optional[float]:
    """Rounds to one decimal. None stays None."""
    return None if x is None else round(float(x), 1)


def to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """A number from a value that can be a number or a text. A bad value gives the default."""
    if value is None or isinstance(value, bool):
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return default if (math.isnan(number) or math.isinf(number)) else number


def wavg(pairs: Iterable[Tuple[float, float]], default: float = 0.0) -> float:
    """Weighted average of (value, weight) pairs."""
    num = den = 0.0
    for value, weight in pairs:
        num += value * weight
        den += weight
    return num / den if den > 0 else default


# =====================================================================
# 2. TEXT HELPERS
# =====================================================================

_DASHES = str.maketrans({0x2013: "-", 0x2014: "-", 0x2212: "-", 0x2019: "'", 0x2018: "'", 0x00A0: " "})   # en dash, em dash, minus, quotes, no-break space


@functools.lru_cache(maxsize=100000)
def _norm_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.translate(_DASHES).lower().strip())


def norm_key(text: Any) -> str:
    """Lower case, one space between words, plain dashes. The key for every name and alias."""
    if isinstance(text, str):
        return _norm_text(text)
    return _norm_text(str(text if text is not None else ""))


def compact_key(text: Any) -> str:
    """Only letters and digits (and + and #). It joins spellings such as 'CI/CD' and 'ci cd'."""
    return re.sub(r"[^a-z0-9+#]", "", norm_key(text))


def _variants(text: Any) -> List[str]:
    base = norm_key(text)
    out = [base]
    spaced = re.sub(r"[-_/]", " ", base)
    spaced = re.sub(r"\s+", " ", spaced).strip()
    if spaced != base:
        out.append(spaced)
    stripped = re.sub(r"[^a-z0-9+#./ -]", "", base).strip()
    if stripped and stripped not in out:
        out.append(stripped)
    return out


_STOP_TOKENS = {"and", "or", "of", "the", "for", "a", "an", "in", "at", "to", "with", "on", "i", "ii", "iii", "iv", "v"}


def content_tokens(text: Any, level_words: Optional[Set[str]] = None) -> frozenset:
    """Title words without level words and small words. Light plural clean (engineers -> engineer)."""
    words = re.findall(r"[a-z0-9+#]+", norm_key(text))
    out = set()
    for w in words:
        if w in _STOP_TOKENS or (level_words and w in level_words):
            continue
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.add(w)
    return frozenset(out)


def today_year() -> int:
    return datetime.date.today().year


# =====================================================================
# 3. THE TAXONOMY INDEX
# =====================================================================

DEFAULT_LEVELS = [
    {"name": "Intern", "rank": 0, "typicalYears": [0, 0], "titleWords": ["intern", "internship", "trainee"]},
    {"name": "Junior", "rank": 1, "typicalYears": [0, 2], "titleWords": ["junior", "jr", "graduate", "entry level", "entry-level"]},
    {"name": "Mid", "rank": 2, "typicalYears": [2, 5], "titleWords": ["mid", "mid-level", "intermediate"]},
    {"name": "Senior", "rank": 3, "typicalYears": [5, 9], "titleWords": ["senior", "sr", "snr"]},
    {"name": "Lead", "rank": 4, "typicalYears": [7, 12], "titleWords": ["lead", "team lead", "tech lead", "staff"]},
    {"name": "Principal", "rank": 5, "typicalYears": [10, 40], "titleWords": ["principal", "distinguished", "head of", "director"]},
]

# Approximate city centres (latitude, longitude). Used for a smooth distance. A city that is not here has no distance.
CITY_COORDS = {
    "sydney": (-33.87, 151.21), "melbourne": (-37.81, 144.96), "brisbane": (-27.47, 153.03), "perth": (-31.95, 115.86),
    "adelaide": (-34.93, 138.60), "canberra": (-35.28, 149.13), "hobart": (-42.88, 147.33), "darwin": (-12.46, 130.84),
    "gold coast": (-28.02, 153.43), "newcastle": (-32.93, 151.78), "wollongong": (-34.42, 150.89),
}
_MODE_WORDS = {"onsite": "Onsite", "on-site": "Onsite", "on site": "Onsite", "office": "Onsite", "hybrid": "Hybrid", "remote": "Remote",
               "work from home": "Remote", "wfh": "Remote"}


class Taxonomy:
    """An index of the taxonomy file. With no file, it has the default levels and nothing else (every lookup then returns None)."""

    def __init__(self, data: Optional[Dict[str, Any]], path: str = ""):
        data = data if isinstance(data, dict) else {}
        self.data = data
        self.path = path
        self.loaded = bool(data.get("skills"))
        self._canon_memo: Dict[str, Optional[str]] = {}
        self._token_memo: Dict[str, frozenset] = {}
        self._profile_memo: Dict[str, Dict[str, float]] = {}

        levels = data.get("levels") or DEFAULT_LEVELS
        self.levels: List[Dict[str, Any]] = sorted(levels, key=lambda x: x.get("rank", 0))
        self.level_names = [l["name"] for l in self.levels]
        self.level_by_key = {norm_key(l["name"]): l for l in self.levels}
        self.max_rank = max([l.get("rank", 0) for l in self.levels] or [5])
        self.level_words: Set[str] = set()
        for l in self.levels:
            for w in l.get("titleWords") or []:
                for token in re.findall(r"[a-z0-9]+", norm_key(w)):
                    self.level_words.add(token)
            self.level_words.add(norm_key(l["name"]))

        self.groups: Dict[str, str] = {k: (v or {}).get("label", k) for k, v in (data.get("skillGroups") or {}).items()}
        self.group_order = list(self.groups.keys())
        self.domains: List[str] = [d["name"] for d in data.get("domains") or []]
        self.specialisations: Dict[str, List[str]] = {d["name"]: list(d.get("specialisations") or []) for d in data.get("domains") or []}
        self.skill_levels = {int(s["level"]): s.get("label", str(s["level"])) for s in data.get("skillLevels") or []} or {
            1: "Beginner", 2: "Working", 3: "Proficient", 4: "Advanced", 5: "Expert"}

        # ----- skills -----
        self.skills: Dict[str, Dict[str, Any]] = {}      # canonical name -> entry
        self.skill_index: Dict[str, str] = {}            # key (name, alias, variants) -> canonical name
        self.compact_index: Dict[str, str] = {}          # compact key -> canonical name
        for s in data.get("skills") or []:
            name = s["name"]
            self.skills[name] = s
        for name, s in self.skills.items():
            for text in [name] + list(s.get("aliases") or []):
                for v in _variants(text):
                    self.skill_index.setdefault(v, name)
                self.compact_index.setdefault(compact_key(text), name)
        self.related: Dict[str, Set[str]] = {n: set() for n in self.skills}
        for name, s in self.skills.items():
            for other in s.get("related") or []:
                canon = self.canon_skill_name(other)
                if canon and canon != name:
                    self.related[name].add(canon)
                    self.related[canon].add(name)      # the relation is used in both directions
        self._skill_regex: Optional[Any] = None

        # ----- occupations and roles -----
        self.occupations: Dict[str, Dict[str, Any]] = {str(o["code"]): o for o in data.get("occupations") or []}
        self.role_index: Dict[str, str] = {}
        for o in self.occupations.values():
            for t in (o.get("title"), o.get("anzscoTitle")):
                if t:
                    self.role_index.setdefault(norm_key(t), str(o["code"]))
        for r in data.get("roles") or []:
            if r.get("title") and r.get("occupationCode"):
                self.role_index.setdefault(norm_key(r["title"]), str(r["occupationCode"]))
        self.role_tokens: List[Tuple[frozenset, str]] = []
        for text, code in self.role_index.items():
            self.role_tokens.append((content_tokens(text, self.level_words), code))

        # ----- certifications -----
        self.certs: Dict[str, Dict[str, Any]] = {c["name"]: c for c in data.get("certifications") or []}
        self.cert_index: Dict[str, str] = {}
        self.cert_compact: Dict[str, str] = {}
        for name, c in self.certs.items():
            for text in [name] + list(c.get("aliases") or []):
                for v in _variants(text):
                    self.cert_index.setdefault(v, name)
                self.cert_compact.setdefault(compact_key(text), name)

        # ----- awards -----
        self.award_kinds: Dict[str, Dict[str, Any]] = {a["kind"]: a for a in data.get("awardKinds") or []}
        self.award_label_index = {norm_key(a.get("label", "")): a["kind"] for a in self.award_kinds.values() if a.get("label")}

        self.cities = [norm_key(c) for c in data.get("cities") or [] if norm_key(c) != "remote"] or list(CITY_COORDS.keys())

    # ----- skills -----
    def canon_skill_name(self, text: Any) -> Optional[str]:
        """The canonical skill name for a name or an alias (any case), or None."""
        memo_key = text if isinstance(text, str) else str(text)
        if memo_key in self._canon_memo:
            return self._canon_memo[memo_key]
        found = None
        for v in _variants(text):
            hit = self.skill_index.get(v)
            if hit:
                found = hit
                break
        if found is None and compact_key(text):
            found = self.compact_index.get(compact_key(text))
        if len(self._canon_memo) < 200000:
            self._canon_memo[memo_key] = found
        return found

    def title_tokens(self, text: Any) -> frozenset:
        """The content words of a title without level words (memoised)."""
        key = text if isinstance(text, str) else str(text)
        hit = self._token_memo.get(key)
        if hit is None:
            hit = content_tokens(key, self.level_words)
            if len(self._token_memo) < 200000:
                self._token_memo[key] = hit
        return hit

    def skill_info(self, canon: Optional[str]) -> Optional[Dict[str, Any]]:
        return self.skills.get(canon) if canon else None

    def skill_regex(self):
        """One pattern for all names and aliases (longest first). Names of 1 or 2 letters are left out, so that a text scan stays safe."""
        if self._skill_regex is None:
            keys = sorted({k for k in self.skill_index if len(k) > 2}, key=lambda k: (-len(k), k))
            if keys:
                body = "|".join(re.escape(k) for k in keys)
                self._skill_regex = re.compile(r"(?<![a-z0-9+#])(" + body + r")(?![a-z0-9+#])")
            else:
                self._skill_regex = re.compile(r"(?!x)x")
        return self._skill_regex

    def find_skills_in_text(self, text: Any) -> List[str]:
        """Canonical skill names that appear in a text. Each name once, in order of first appearance."""
        found: List[str] = []
        for m in self.skill_regex().finditer(norm_key(text)):
            canon = self.skill_index.get(m.group(1))
            if canon and canon not in found:
                found.append(canon)
        return found

    # ----- levels -----
    def level_rank(self, name: Any) -> Optional[int]:
        """The rank (0 to 5) for a level name (any case) or for a number."""
        if name is None or isinstance(name, bool):
            return None
        if isinstance(name, (int, float)):
            return int(clamp(round(float(name)), 0, self.max_rank))
        l = self.level_by_key.get(norm_key(name))
        if l:
            return int(l["rank"])
        for lv in self.levels:                      # a title word such as "sr" or "graduate"
            if norm_key(name) in {norm_key(w) for w in lv.get("titleWords") or []}:
                return int(lv["rank"])
        return None

    def level_name(self, rank: Optional[float]) -> str:
        if rank is None:
            return ""
        i = int(clamp(round(float(rank)), 0, self.max_rank))
        for l in self.levels:
            if l["rank"] == i:
                return l["name"]
        return ""

    def typical_years(self, rank: float) -> Tuple[float, float]:
        """The typical (min, max) years for a level rank. A rank between two levels gives a smooth mix."""
        rank = clamp(float(rank), 0.0, float(self.max_rank))
        lo_i, hi_i = int(math.floor(rank)), int(math.ceil(rank))
        by_rank = {l["rank"]: l for l in self.levels}
        a, b = by_rank.get(lo_i), by_rank.get(hi_i)
        if not a or not b:
            return (0.0, 5.0)
        t = rank - lo_i
        lo = a["typicalYears"][0] * (1 - t) + b["typicalYears"][0] * t
        hi = a["typicalYears"][1] * (1 - t) + b["typicalYears"][1] * t
        return (float(lo), float(hi))

    def rank_from_years(self, years: float) -> float:
        """A level rank estimated from years of experience (used only when the level is not known)."""
        mids = []
        for l in self.levels:
            lo, hi = l["typicalYears"]
            mids.append((l["rank"], (lo + min(hi, 14.0)) / 2.0 if l["rank"] > 0 else 0.0))
        pts: List[Tuple[float, float]] = []
        last = -1.0
        for rank, mid in sorted(mids, key=lambda t: t[0]):
            mid = max(mid, last + 0.5)
            pts.append((mid, float(rank)))
            last = mid
        pts[0] = (0.0, 0.5)    # no experience: between Intern and Junior
        if len(pts) > 1 and pts[1][0] <= 0.0:
            pts[1] = (0.5, pts[1][1])
        return lerp_table(float(years), pts)

    def level_from_title(self, title: Any) -> Optional[int]:
        """The level rank from words in a job title ("Senior Data Engineer" -> 3). The highest matching level wins."""
        text = " " + norm_key(title) + " "
        for l in sorted(self.levels, key=lambda x: -x["rank"]):
            for w in l.get("titleWords") or []:
                if re.search(r"(?<![a-z0-9])" + re.escape(norm_key(w)) + r"(?![a-z0-9])", text):
                    return int(l["rank"])
        return None

    # ----- occupations -----
    def occupation(self, code: Any) -> Optional[Dict[str, Any]]:
        digits = re.findall(r"\d{4,6}", str(code or ""))
        return self.occupations.get(digits[0]) if digits else None

    def occupation_for(self, code: Any = "", title: Any = "") -> Tuple[Optional[Dict[str, Any]], str]:
        """The taxonomy occupation for a code, else for a role title. Returns (occupation or None, how: 'code' | 'title' | 'tokens' | '')."""
        occ = self.occupation(code)
        if occ:
            return occ, "code"
        key = norm_key(title)
        if not key:
            return None, ""
        stripped = " ".join(w for w in key.split() if w not in self.level_words)
        for k in (key, stripped):
            if k in self.role_index:
                return self.occupations.get(self.role_index[k]), "title"
        tokens = content_tokens(key, self.level_words)
        best, best_score = None, 0.0
        for rt, rc in self.role_tokens:
            if not rt or not tokens:
                continue
            score = len(tokens & rt) / len(tokens | rt)
            if score > best_score:
                best, best_score = rc, score
        if best and best_score >= 0.5:
            return self.occupations.get(best), "tokens"
        return None, ""

    def occupation_profiles(self) -> Dict[str, Dict[str, Any]]:
        """code -> {title, domain, core_skills, methods}. Same idea as the old ANZSCO_TAXONOMY dictionary."""
        return {code: {"title": o.get("title"), "sector": o.get("domain"), "core_skills": [c["name"] for c in o.get("coreSkills") or []],
                       "transferable_methodologies": list(o.get("methods") or []), "statutory_requirements": []}
                for code, o in self.occupations.items()}

    # ----- certifications and awards -----
    def canon_cert(self, text: Any) -> Tuple[str, Optional[Dict[str, Any]]]:
        """(canonical certification name, entry or None). A name that is not in the taxonomy stays as the cleaned text."""
        for v in _variants(text):
            hit = self.cert_index.get(v)
            if hit:
                return hit, self.certs[hit]
        ck = compact_key(text)
        hit = self.cert_compact.get(ck) if ck else None
        if hit:
            return hit, self.certs[hit]
        return str(text).strip(), None

    def canon_award_kind(self, kind: Any, name: Any = "") -> str:
        k = norm_key(kind)
        if k in self.award_kinds:
            return k
        if k in self.award_label_index:
            return self.award_label_index[k]
        n = norm_key(name)
        if n in self.award_label_index:
            return self.award_label_index[n]
        return k or "other"


_TAXONOMY: Optional[Taxonomy] = None


def _read_taxonomy(path: str) -> Taxonomy:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return Taxonomy(json.load(f), path)
    except (OSError, ValueError):
        return Taxonomy({}, "")


def get_taxonomy() -> Taxonomy:
    """The taxonomy of the engine. It is loaded once. The path comes from JINDER_TAXONOMY_PATH, else from ../data/reference."""
    global _TAXONOMY
    if _TAXONOMY is None:
        with _LOCK:
            if _TAXONOMY is None:
                _TAXONOMY = _read_taxonomy(os.environ.get("JINDER_TAXONOMY_PATH") or DEFAULT_TAXONOMY_PATH)
    return _TAXONOMY


def set_taxonomy(source: Any = None) -> Taxonomy:
    """Changes the taxonomy. None reloads the default file. A dictionary or a file path loads that. An empty dictionary means 'no taxonomy'."""
    global _TAXONOMY
    with _LOCK:
        if source is None:
            _TAXONOMY = _read_taxonomy(os.environ.get("JINDER_TAXONOMY_PATH") or DEFAULT_TAXONOMY_PATH)
        elif isinstance(source, dict):
            _TAXONOMY = Taxonomy(source, "")
        else:
            _TAXONOMY = _read_taxonomy(str(source))
    return _TAXONOMY


# =====================================================================
# 4. LOADING ONE FORMULA FILE FROM ANOTHER
# =====================================================================

def load_sibling(key: str):
    """Loads a formula file of this folder (key f1 to f6) once. The file names start with a digit, so this uses the file path."""
    name = "jinder_engine_" + key
    mod = sys.modules.get(name)
    if mod is not None:
        return mod
    with _LOCK:
        mod = sys.modules.get(name)
        if mod is None:
            path = os.path.join(ENGINE_DIR, SIBLING_FILES[key])
            spec = importlib.util.spec_from_file_location(name, path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
    return mod


# =====================================================================
# 5. EDUCATION, CITY, MODE
# =====================================================================

def education_rank(text: Any) -> Optional[int]:
    """0 to 5 from the words of a qualification. None if the text is empty."""
    t = norm_key(text)
    if not t:
        return None
    if any(k in t for k in ("phd", "doctor")):
        return 5
    if any(k in t for k in ("master", "mba", "postgraduate", "graduate diploma", "graduate certificate")):
        return 4
    if any(k in t for k in ("bachelor", "degree", "aqf 7", "honours", "honors")):
        return 3
    if any(k in t for k in ("diploma", "associate degree", "aqf 5", "aqf 6")):
        return 2
    if any(k in t for k in ("certificate", "high school", "secondary")):
        return 1
    return 1


def canon_city(text: Any) -> Optional[str]:
    """A known city name (lower case) inside a text such as 'Sydney NSW', or None."""
    t = norm_key(text)
    if not t:
        return None
    best = None
    for city in CITY_COORDS:
        if re.search(r"(?<![a-z])" + re.escape(city) + r"(?![a-z])", t):
            if best is None or len(city) > len(best):
                best = city
    return best


def canon_mode(text: Any) -> Optional[str]:
    """Onsite, Hybrid or Remote from a text, or None."""
    t = norm_key(text)
    if not t:
        return None
    for word, mode in _MODE_WORDS.items():
        if re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", t):
            return mode
    return None


def distance_km(city_a: str, city_b: str) -> Optional[float]:
    """Great-circle distance between two known cities, in km. None if a city is not known."""
    a, b = CITY_COORDS.get(city_a), CITY_COORDS.get(city_b)
    if not a or not b:
        return None
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


# =====================================================================
# 5b. PAY: ONE FUNCTION THAT GIVES A YEARLY AMOUNT
# =====================================================================

HOURS_PER_YEAR = 1950.0      # 37.5 hours x 52 weeks
DAYS_PER_YEAR = 220.0        # 220 working days (a contract day rate is paid for the days that are worked)


def annual_salary(salary_min: Any, salary_max: Any, unit: Any = None) -> Tuple[float, float]:
    """The pay range of a job in AUD for one year: (yearly min, yearly max). A value that is not known is 0.0.

    unit "year" (also "yearly", "annual"): no change.   unit "day" (also "daily"): x 220 working days.   unit "hour" (also "hourly"): x 1950 hours.
    If the unit is not given (old data), the size of the number decides: a maximum below 500 is an hourly rate,
    from 500 to 3999 it is a day rate, and a larger number is a yearly pay.
    This is the only place in the engine that changes a pay to a yearly pay. Formulas 3 and 5 use it through `prepare_job`."""
    lo = to_float(salary_min, 0.0) or 0.0
    hi = to_float(salary_max, 0.0) or 0.0
    u = norm_key(unit)
    if u in ("hour", "hourly", "hr", "h"):
        factor = HOURS_PER_YEAR
    elif u in ("day", "daily", "d"):
        factor = DAYS_PER_YEAR
    elif u in ("year", "yearly", "annual", "annum", "pa", "p.a.", "y"):
        factor = 1.0
    else:
        top = max(lo, hi)
        factor = HOURS_PER_YEAR if 0 < top < 500.0 else (DAYS_PER_YEAR if 500.0 <= top < 4000.0 else 1.0)
    return lo * factor, hi * factor


# =====================================================================
# 6. INPUT CLEANERS
# =====================================================================

DEFAULT_SKILL_LEVEL = 3.0
DEFAULT_RARITY = 1.4
DEFAULT_MONTHS = 3.0


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _first(d: Dict[str, Any], *keys: str) -> Any:
    for k in keys:
        v = d.get(k)
        if v is not None and v != "":
            return v
    return None


def _skill_level(value: Any) -> Optional[float]:
    v = to_float(value)
    if v is None or not 0.5 <= v <= 5.0:
        return None
    return v


def skill_entry(name: Any, level: Any = None, tax: Optional[Taxonomy] = None, **extra: Any) -> Optional[Dict[str, Any]]:
    """One skill as the formulas use it: canonical name, key, level 1 to 5, and the taxonomy facts."""
    tax = tax or get_taxonomy()
    text = str(name or "").strip()
    if not text:
        return None
    canon = tax.canon_skill_name(text)
    info = tax.skill_info(canon)
    shown = canon or text
    kind = (info or {}).get("kind")
    if kind is None:
        kind = "method" if norm_key(extra.get("skill_type")) == "transferable" else "hard"
    lvl = _skill_level(level)
    return {
        "name": shown, "key": norm_key(shown), "level": lvl if lvl is not None else DEFAULT_SKILL_LEVEL, "level_given": lvl is not None,
        "kind": kind, "known": info is not None, "group": (info or {}).get("group") or "other",
        "rarity": float((info or {}).get("rarity") or DEFAULT_RARITY), "months": float((info or {}).get("monthsToLearn") or DEFAULT_MONTHS),
        "domains": list((info or {}).get("domains") or []),
        "years": to_float(extra.get("years")), "last_used": to_float(extra.get("last_used")),
    }


def prepare_candidate(c: Any, shared_only: bool = False, tax: Optional[Taxonomy] = None) -> Dict[str, Any]:
    """Cleans one talent dictionary (old or version 2 shape) into the form that the formulas use.

    shared_only=True is for the employer side (Formula 6): the CV text and any other text of the person are not read.
    """
    if isinstance(c, dict) and c.get("_prepared"):
        return c
    tax = tax or get_taxonomy()
    c = c if isinstance(c, dict) else {}

    # ----- skills -----
    skills: Dict[str, Dict[str, Any]] = {}
    raw_skills = c.get("skills")
    for s in _as_list(raw_skills):
        if isinstance(s, dict):
            name = _first(s, "skill_name", "name", "skill")
            entry = skill_entry(name, s.get("level"), tax, skill_type=_first(s, "skill_type", "type"), years=s.get("years"),
                                last_used=_first(s, "last_used_year", "lastUsedYear"))
        else:
            entry = skill_entry(s, None, tax)
        if entry:
            old = skills.get(entry["key"])
            if old is None or entry["level"] > old["level"]:
                skills[entry["key"]] = entry
    for sl in _as_list(c.get("skillLevels")):                       # the shared profile form: [{name, level}]
        if isinstance(sl, dict):
            entry = skill_entry(sl.get("name"), sl.get("level"), tax)
            if entry and (entry["key"] not in skills or entry["level"] > skills[entry["key"]]["level"]):
                skills[entry["key"]] = entry
    text_fallback = False
    if not skills and not shared_only:
        # Old shape without a skill list: look for skill names in the text of the person (only for the person's own screens).
        text = " ".join(str(c.get(k) or "") for k in ("cv_raw_text", "rawResume", "raw_resume_sample", "direct_skills", "transferable_skills"))
        for name in tax.find_skills_in_text(text):
            entry = skill_entry(name, 2, tax)
            if entry:
                skills[entry["key"]] = entry
                text_fallback = True

    # ----- title, level, years -----
    title_value = _first(c, "current_title", "currentTitle", "originRole", "original_job_title")
    if isinstance(title_value, list):
        title_value = title_value[0] if title_value else ""
    title = str(title_value or "").strip()
    level_rank: Optional[float] = None
    level_known = False
    lv = c.get("level_rank")
    if lv is None or isinstance(lv, bool):
        lv = None
    level_value = c.get("level")
    if lv is not None and to_float(lv) is not None:
        level_rank, level_known = float(clamp(to_float(lv), 0, tax.max_rank)), True
    elif level_value not in (None, ""):
        rk = tax.level_rank(level_value)
        if rk is not None:
            level_rank, level_known = float(rk), True
    years_raw = to_float(_first(c, "years_experience", "yearsExperience", "years_of_experience", "yearsExp"))
    if years_raw is not None:
        years_raw = clamp(years_raw, 0.0, 50.0)
    years_known = years_raw is not None
    if not level_known:
        t_rank = tax.level_from_title(title) if title else None
        if t_rank is not None:
            level_rank, level_known = float(t_rank), True
    level_estimated = not level_known
    if not level_known:
        level_rank = tax.rank_from_years(years_raw) if years_known else None
    if years_known:
        years = float(years_raw)
    elif level_rank is not None:
        lo, hi = tax.typical_years(level_rank)
        years = (lo + min(hi, lo + 4.0)) / 2.0 if level_rank < 5 else lo + 2.0
    else:
        years = 2.0

    # ----- domain, occupation anchors -----
    domain = str(_first(c, "domain", "category", "industry_category") or "").strip()
    specialisation = str(_first(c, "specialisation", "specialization") or "").strip()
    target_code = str(_first(c, "target_anzsco_code", "anzsco_code", "anzscoCode") or "")
    target_title = str(_first(c, "target_anzsco_title") or "")
    target_roles = [str(r).strip() for r in _as_list(_first(c, "target_roles", "targetRole", "targetRoles")) if str(r).strip()]
    anchors: List[Dict[str, Any]] = []
    if target_code or target_title:
        anchors.append({"code": target_code, "title": target_title, "weight": 1.0, "source": "target"})
    for role in target_roles:
        anchors.append({"code": "", "title": role, "weight": 1.0, "source": "target"})
    if title:
        anchors.append({"code": "", "title": title, "weight": 0.85, "source": "current"})
    for a in anchors:
        occ, _how = tax.occupation_for(a["code"], a["title"])
        a["occ"] = occ
        a["digits"] = (re.findall(r"\d{4,6}", a["code"]) or [str(occ["code"]) if occ else ""])[0]
        a["tokens"] = tax.title_tokens(a["title"] or (occ or {}).get("title", ""))

    # ----- certifications and awards -----
    certs: Dict[str, Dict[str, Any]] = {}
    for item in _as_list(c.get("certifications")):
        name = item.get("name") if isinstance(item, dict) else item
        if not name:
            continue
        canon, entry = tax.canon_cert(name)
        certs[norm_key(canon)] = {"name": canon, "entry": entry, "year": to_float(item.get("year")) if isinstance(item, dict) else None}
    awards: List[Dict[str, Any]] = []
    for item in _as_list(c.get("awards")):
        if isinstance(item, dict):
            kind = tax.canon_award_kind(item.get("kind"), item.get("name"))
            awards.append({"kind": kind, "name": str(item.get("name") or ""), "year": to_float(item.get("year"))})
        elif item:
            awards.append({"kind": tax.canon_award_kind(item, item), "name": str(item), "year": None})

    # ----- places, modes, types -----
    place_texts = [_first(c, "preferred_location", "preferredLocation")] + _as_list(c.get("locations"))
    cities: List[str] = []
    wants_remote = False
    for t in place_texts:
        if not t:
            continue
        city = canon_city(t)
        if city and city not in cities:
            cities.append(city)
        if norm_key(t) == "remote":
            wants_remote = True
    modes = {canon_mode(m) for m in _as_list(c.get("work_modes") or c.get("workModes")) if canon_mode(m)}
    if wants_remote:
        modes.add("Remote")
    types = {norm_key(t) for t in _as_list(c.get("work_types") or c.get("workTypes")) if str(t).strip()}

    # ----- domain affinity from the skills (each skill gives its weight, shared by the domains that it belongs to) -----
    share: Dict[str, float] = {}
    total = 0.0
    for s in skills.values():
        w = (s["level"] / 5.0)
        doms = s["domains"]
        if doms:
            for d in doms:
                share[d] = share.get(d, 0.0) + w / len(doms)
        total += w
    top = max(share.values()) if share else 0.0
    affinity = {d: (v / top if top > 0 else 0.0) for d, v in share.items()}
    if not domain and share:
        domain = max(share, key=lambda d: (share[d], d))
        domain_declared = False
    else:
        domain_declared = bool(domain)

    return {
        "_prepared": True, "_shared_only": shared_only,
        "id": _first(c, "id", "candidate_id"), "alias": _first(c, "alias"),
        "title": title, "level_rank": level_rank, "level_known": level_known, "level_estimated": level_estimated,
        "years": years, "years_known": years_known,
        "domain": domain, "domain_declared": domain_declared, "specialisation": specialisation, "affinity": affinity,
        "target_code": target_code, "target_roles": target_roles, "anchors": anchors,
        "education_rank": education_rank(c.get("highest_education")), "skills": skills, "text_fallback": text_fallback,
        "certs": certs, "awards": awards,
        "cities": cities, "wants_remote": wants_remote, "modes": modes, "types": types,
    }


def _requirement_items(raw: Any, tax: Taxonomy) -> List[Dict[str, Any]]:
    """Job skills from a list of names or of {name, level, must} dictionaries."""
    out: List[Dict[str, Any]] = []
    for r in _as_list(raw):
        if isinstance(r, dict):
            name = _first(r, "name", "skill_name", "skill")
            level, must = r.get("level"), r.get("must")
        else:
            name, level, must = r, None, None
        if not name:
            continue
        text = str(name).strip()
        canon = tax.canon_skill_name(text)
        names = [canon] if canon else []
        if not canon and len(text.split()) > 3:
            names = tax.find_skills_in_text(text)       # a long requirement sentence: take the skills that it names
        if not names:
            names = [text]
        for n in names:
            e = skill_entry(n, level, tax)
            if e:
                e["must"] = True if must is None else bool(must)
                e["need"] = float(e["level"])
                out.append(e)
    return out


def prepare_job(j: Any, tax: Optional[Taxonomy] = None) -> Dict[str, Any]:
    """Cleans one job dictionary (old or version 2 shape) into the form that the formulas use."""
    if isinstance(j, dict) and j.get("_prepared"):
        return j
    tax = tax or get_taxonomy()
    j = j if isinstance(j, dict) else {}

    # ----- skills that the job asks for: the first non-empty source wins -----
    sources = [j.get("skill_requirements"), [r for r in _as_list(j.get("required_skills")) if isinstance(r, dict)],
               j.get("requirements"), j.get("required_skills"), j.get("skills")]
    reqs: List[Dict[str, Any]] = []
    for src in sources:
        reqs = _requirement_items(src, tax)
        if reqs:
            break
    merged: Dict[str, Dict[str, Any]] = {}
    for r in reqs:
        old = merged.get(r["key"])
        if old is None:
            merged[r["key"]] = r
        else:
            old["need"] = max(old["need"], r["need"])
            old["must"] = old["must"] or r["must"]
    reqs = list(merged.values())

    code = str(_first(j, "anzsco_code", "anzsco", "anzscoCode") or "")
    title = str(j.get("title") or "")
    anzsco_title = str(_first(j, "anzsco_title", "occupation_title") or "")
    occ, how = tax.occupation_for(code, anzsco_title or title)
    if not occ and title:
        occ, how = tax.occupation_for("", title)
    occ_methods = [m for m in (occ or {}).get("methods") or []] if occ else []
    if not reqs and occ:                                    # a job with no skill list: use the occupation profile
        reqs = _requirement_items([{"name": c["name"], "level": c.get("level"), "must": c.get("must", True)} for c in occ.get("coreSkills") or []], tax)
        for r in reqs:
            r["from_occupation"] = True

    # ----- level, years -----
    level_rank: Optional[float] = None
    lv = j.get("level_rank")
    if lv is not None and not isinstance(lv, bool) and to_float(lv) is not None:
        level_rank = float(clamp(to_float(lv), 0, tax.max_rank))
    elif j.get("level") not in (None, ""):
        rk = tax.level_rank(j.get("level"))
        level_rank = float(rk) if rk is not None else None
    if level_rank is None and title:
        rk = tax.level_from_title(title)
        level_rank = float(rk) if rk is not None else None
    min_y = to_float(_first(j, "min_years", "minYears"))
    max_y = to_float(_first(j, "max_years", "maxYears"))
    if min_y is None and max_y is None and level_rank is not None:
        min_y, max_y = tax.typical_years(level_rank)
    elif min_y is None and max_y is not None:
        min_y = max(0.0, max_y - 3.0)
    # a job with a minimum and no maximum is open-ended: there is no upper limit of years (max_y stays None)
    if min_y is not None and max_y is not None and max_y < min_y:
        max_y = min_y

    # ----- place -----
    loc_text = " ".join(str(j.get(k) or "") for k in ("city", "location"))
    city = canon_city(j.get("city")) or canon_city(j.get("location"))
    mode = canon_mode(j.get("work_mode") or j.get("workMode"))
    if mode is None and "remote" in norm_key(loc_text):
        mode = "Remote"

    # ----- pay and time -----
    sal = j.get("salary") if isinstance(j.get("salary"), dict) else {}
    s_min, s_max = annual_salary(_first(j, "salary_min", "salaryMin") if _first(j, "salary_min", "salaryMin") is not None else sal.get("min"),
                                 _first(j, "salary_max", "salaryMax") if _first(j, "salary_max", "salaryMax") is not None else sal.get("max"),
                                 _first(j, "salary_unit", "salaryUnit") or sal.get("unit"))
    mid = (s_min + s_max) / 2.0 if (s_min > 0 and s_max > 0) else (s_max or s_min or None)
    days_old = to_float(j.get("days_old"))
    if days_old is None and j.get("posted_at"):
        try:
            posted = datetime.datetime.strptime(str(j["posted_at"])[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S")
            days_old = max(0.0, (datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - posted).total_seconds() / 86400.0)
        except ValueError:
            days_old = None

    # ----- certifications and awards -----
    def cert_names(values: Any) -> List[Dict[str, Any]]:
        out = []
        for v in _as_list(values):
            name = v.get("name") if isinstance(v, dict) else v
            if name:
                canon, entry = tax.canon_cert(name)
                out.append({"name": canon, "key": norm_key(canon), "entry": entry})
        return out
    certs_required = cert_names(j.get("certifications_required"))
    certs_preferred = cert_names(j.get("certifications_preferred"))
    cert_obj = j.get("certifications")
    if isinstance(cert_obj, dict):
        certs_required = certs_required or cert_names(cert_obj.get("required"))
        certs_preferred = certs_preferred or cert_names(cert_obj.get("preferred"))
    pref_awards = [tax.canon_award_kind(a, a) for a in _as_list(j.get("awards_preferred")) if a]
    award_obj = j.get("awards")
    if isinstance(award_obj, dict) and not pref_awards:
        pref_awards = [tax.canon_award_kind(a, a) for a in _as_list(award_obj.get("preferred")) if a]

    domain = str(_first(j, "domain", "category") or "").strip() or (occ or {}).get("domain", "")
    return {
        "_prepared": True,
        "id": _first(j, "id", "job_id"), "title": title, "company": str(j.get("company") or ""),
        "domain": domain, "specialisation": str(j.get("specialisation") or "").strip(),
        "level_rank": level_rank, "min_years": min_y, "max_years": max_y,
        "code": code or (str(occ["code"]) if occ else ""), "anzsco_title": anzsco_title, "occ": occ, "occ_how": how, "occ_methods": occ_methods,
        "reqs": reqs, "city": city, "mode": mode, "type": norm_key(j.get("type") or j.get("employment_type")),
        "salary_min": s_min, "salary_max": s_max, "salary_mid": mid, "days_old": days_old,
        "certs_required": certs_required, "certs_preferred": certs_preferred, "awards_preferred": pref_awards,
        "education_min": education_rank(j.get("education_min")), "location_text": loc_text.strip(),
        "category": str(j.get("category") or ""), "raw_location": str(j.get("location") or ""),
        "tokens": tax.title_tokens(title or (occ or {}).get("title", "")),
    }


# =====================================================================
# 7. SALARY BENCHMARK (used by Formula 3 and Formula 5)
# =====================================================================

# Mid-level yearly pay (AUD) for each domain. These are demo values. They are not an official statistic.
DOMAIN_BASE_SALARY = {"software engineering": 130000.0, "ai & machine learning": 150000.0, "data": 125000.0}
DEFAULT_BASE_SALARY = 130000.0
LEVEL_SALARY_GROWTH = 0.20      # pay grows by exp(0.20) for each level step above Mid


def salary_benchmark(domain: Any, level_rank: Optional[float]) -> float:
    """Typical yearly pay (AUD) for a domain and a level. B(d, r) = base(d) * exp(0.20 (r - 2)). A missing level counts as Mid."""
    base = DOMAIN_BASE_SALARY.get(norm_key(domain), DEFAULT_BASE_SALARY)
    r = 2.0 if level_rank is None else float(level_rank)
    return base * math.exp(LEVEL_SALARY_GROWTH * (r - 2.0))
