"""Skill names, the words that show them in a text, and the per-skill match (Feature 3; version 2: levels).

The skill names, their aliases and the related skills come from the taxonomy (`taxonomy.py`). The per-skill match of the product
uses the result of the formulas (the `skill_breakdown` of Formula 1). The function `skill_match` here is a small, level-aware
fallback for code that has no formula result. Both give the same SkillResult.

SkillResult (one skill that a job asks for):
  name       the skill name of the job
  status     "match", "partial" or "gap" (the old words; old clients know them)
  fitStatus  the status of the formulas: "meets", "below", "related" or "missing"
  required   the level that the job asks for (1 to 5), or null
  level      the level of the person (1 to 5), or null if the person does not have the skill
  must       true if the skill is a must-have
  reason     one short sentence. A related skill also has "via": the name of the related skill

The mapping of the statuses:   meets -> match    below -> partial    related -> partial    missing -> gap

The match uses only skills and levels. It never uses nationality, ethnicity, gender, age, visa status or country of study (Feature 3 AC11).
"""
import re
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from . import taxonomy
from .util import as_list, norm

_T = taxonomy.get()

# =====================================================================
# Patterns: the name and the aliases of each skill, as whole words
# =====================================================================
_LEFT = r"(?<![A-Za-z0-9])"
_LEFT_AFTER_DOT = r"(?<![A-Za-z0-9.])"
_RIGHT = r"(?![A-Za-z0-9])"
# A name of one letter (C, R) or a common word (Go) counts only in a list: "Python, R, SQL" or "(C)". Not in "plan C" or "R and D".
_LIST_LEFT = r"(?:(?<=^)|(?<=[,;:(/|•·\n])|(?<=[,;:(/|•·\n] )|(?<=\n ))"
_LIST_RIGHT = r"(?=\s*(?:[,;)/|•·\n]|$))"
_LIST_ONLY = {"c", "r", "go"}
# A name that is also an ordinary word. It counts only with a capital letter ("Swift", "Spark"), not in "swift delivery".
_CAPITAL_ONLY = {"swift", "rust", "ruby", "spark", "hive", "helm", "rails", "expo", "mocha", "torch", "elk", "dart", "scala", "kube"}


def _regex_for(term: str, canonical: str) -> str:
    low = term.lower()
    # A term that starts with a letter or a digit does not follow a dot: "js" is not found in "Node.js". A term that starts with a sign (.NET) can.
    left = _LEFT_AFTER_DOT if term[:1].isalnum() else _LEFT
    body = re.escape(term.strip()).replace(r"\ ", r"[\s-]+").replace(r"\-", r"[\s-]")
    if low in _LIST_ONLY:
        return f"(?-i:{_LIST_LEFT}{re.escape(canonical)}{_LIST_RIGHT})" if low == canonical.lower() else ""
    if low in _CAPITAL_ONLY:
        return f"{left}(?-i:{re.escape(term[:1].upper() + term[1:])}|{re.escape(term.upper())}){_RIGHT}"
    return f"{left}{body}{_RIGHT}"


def _first_token(term: str) -> str:
    m = re.search(r"[a-z0-9]+", term.lower())
    return m.group(0) if m else ""


SKILL_NAMES: List[str] = [s["name"] for s in _T.skills]
# (skill name, compiled pattern that finds the name or one alias as a whole word)
SKILL_PATTERNS: List[Tuple[str, "re.Pattern[str]"]] = []
_INDEX: Dict[str, List[int]] = {}        # first word of a term -> the skills that have a term with this first word (a quick filter)
_EXACT: Dict[str, str] = {}              # a whole text that is a skill name or an alias (lower case, "-" as a space) -> the skill name


def _exact_key(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").lower().replace("-", " ")).strip()


for _i, _s in enumerate(_T.skills):
    _terms = []
    for _term in [_s["name"]] + list(_s.get("aliases", [])):
        _x = _exact_key(_term)
        if _x and _x not in _EXACT:
            _EXACT[_x] = _s["name"]
        _rx = _regex_for(_term, _s["name"])
        if _rx and _rx not in _terms:
            _terms.append(_rx)
        _tok = _first_token(_term)
        if _tok and _i not in _INDEX.setdefault(_tok, []):
            _INDEX[_tok].append(_i)
    SKILL_PATTERNS.append((_s["name"], re.compile("|".join(sorted(_terms, key=len, reverse=True)), re.I | re.M)))


def canonical_skill_name(text: Any) -> Optional[str]:
    """The skill name for a text that is a whole skill name or alias ("golang" gives "Go"), or None."""
    return _EXACT.get(_exact_key(text))


def skills_in(text: Any) -> List[str]:
    """The skill names that a text shows, in the order of their first place in the text.

    A whole text that is a skill name or an alias gives that skill. In a longer text, a name counts only as a whole word:
    "C" is not found in "Customer", "R" not in "React", ".NET" not in "Kubernetes.NETwork".
    """
    raw = str(text or "")
    whole = canonical_skill_name(raw)
    if whole:
        return [whole]
    words = set(re.findall(r"[a-z0-9]+", raw.lower()))
    candidates = sorted({i for w in words for i in _INDEX.get(w, ())})
    found = []
    for i in candidates:
        name, rx = SKILL_PATTERNS[i]
        m = rx.search(raw)
        if m:
            found.append((m.start(), name))
    return [name for _, name in sorted(found)]


# =====================================================================
# Related skills, and the skills that describe how a person works
# =====================================================================
RELATED: Dict[str, Set[str]] = {}       # lower case name -> lower case names of the related skills (both ways)
for _s in _T.skills:
    for _r in _s.get("related", []):
        RELATED.setdefault(norm(_s["name"]), set()).add(norm(_r))
        RELATED.setdefault(norm(_r), set()).add(norm(_s["name"]))

# Skills of the kind "method" or "soft": how a person works, not a tool. The formulas treat them as "transferable" skills.
TRANSFERABLE_SKILLS = {norm(s["name"]) for s in _T.skills if s.get("kind") in ("method", "soft")}


def canonical_skills(skills: Iterable[Any]) -> set:
    """A skill counts as its own name and as any taxonomy skill that it shows ("aws" gives "AWS")."""
    out = set()
    for s in as_list(skills):
        out.add(norm(s))
        out.update(norm(x) for x in skills_in(s))
    return out


def skill_names_from(skills: Iterable[Any], shared: Iterable[Any] = ()) -> Dict[str, str]:
    """A map of lower case -> display name for the skills of a person, expanded to the taxonomy names."""
    names: Dict[str, str] = {}
    for s in list(as_list(skills)) + list(as_list(shared)):
        names[norm(s)] = str(s)
        for c in skills_in(s):
            names[norm(c)] = c
    return names


# =====================================================================
# Skills for a job title (the suggestion in the job form)
# =====================================================================
def occupation_of_title(title: Any) -> Optional[Dict[str, Any]]:
    """The taxonomy occupation for a job title: the longest role of the pick-list that the title contains ("Senior Data Engineer, Lakehouse"
    gives "Data Engineer"), or None."""
    low = " " + re.sub(r"[^a-z0-9+#.]+", " ", str(title or "").lower()) + " "
    best, best_len = None, 0
    for role in _T.roles:
        words = " " + re.sub(r"[^a-z0-9+#.]+", " ", role["title"].lower()).strip() + " "
        if words in low and len(words) > best_len:
            best, best_len = role, len(words)
    return _T.occupations.get(str(best["occupationCode"])) if best else None


def occupation_for_job(title: Any, specialisation: Any = None, domain: Any = None) -> Optional[Dict[str, Any]]:
    """The taxonomy occupation (code, title ...) for a job: from the title (a role of the role list), else from the specialisation, else None."""
    occ = occupation_of_title(title)
    if occ:
        return occ
    for o in _T.occupations.values():
        if specialisation and specialisation in o.get("specialisations", []) and (not domain or o.get("domain") == domain):
            return o
    return None


def suggest_requirements(title: Any, text: Any = "", domain: Any = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Taxonomy skills for a job: [{name, level 3, must true}]. First the skills that the text shows (tools first), then the core skills of
    the occupation of the title, then the usual skills of the domain. At most `limit`."""
    names: List[str] = []

    def add(name: str) -> None:
        if name not in names and len(names) < limit:
            names.append(name)

    found = skills_in(f"{title}\n{text}")
    for n in found:
        if _T.kind_of(n) == "hard":
            add(n)
    occ = occupation_of_title(title)
    if occ and len(names) < 5:
        for c in occ.get("coreSkills", []):
            add(c["name"])
    if len(names) < 3 and domain in _T.domains:
        from .reference import SKILL_SUGGESTIONS
        for n in SKILL_SUGGESTIONS.get(domain, []):
            add(n)
    for n in found:
        add(n)
    return [{"name": n, "level": 3, "must": True} for n in names]


def job_skills(title: Any, text: Any, limit: int = 8) -> List[str]:
    """The skills of a job: those that the text shows, plus the core skills of the occupation of the title when the text shows fewer than 3."""
    return [r["name"] for r in suggest_requirements(title, text, None, limit)]


# =====================================================================
# The per-skill match
# =====================================================================
STATUS_OF_FIT = {"meets": "match", "below": "partial", "related": "partial", "missing": "gap"}


def _reason(fit: str, have: Optional[float], need: Optional[float], via: Optional[str]) -> str:
    if fit == "meets":
        return "Has this skill."
    if fit == "below":
        return f"Has this skill at level {int(round(have))}. The job asks for level {int(round(need))}." if have and need else "Has this skill below the level that the job asks for."
    if fit == "related":
        return f"Has {via}, which is related." if via else "Has a related skill."
    return "No evidence of this skill yet."


def _result(name: str, fit: str, required: Optional[float], have: Optional[float], must: bool, via: Optional[str] = None) -> Dict[str, Any]:
    out = {"name": name, "status": STATUS_OF_FIT[fit], "fitStatus": fit, "required": None if required is None else int(round(required)),
           "level": None if have is None else int(round(have)), "must": bool(must), "reason": _reason(fit, have, required, via)}
    if via:
        out["via"] = via
    return out


def _summary(items: List[Dict[str, Any]], coverage: Optional[float]) -> Dict[str, Any]:
    matched = sum(1 for i in items if i["fitStatus"] == "meets")
    partial = sum(1 for i in items if i["status"] == "partial")
    return {"items": items, "coverage": None if coverage is None else _js_round(coverage), "matched": matched, "partial": partial}


def results_from_breakdown(breakdown: Iterable[Dict[str, Any]], coverage: Optional[float] = None) -> Dict[str, Any]:
    """The SkillResult list from the `skill_breakdown` of Formula 1 or Formula 6 (one item for each skill of the job).

    `coverage` is the level-aware skill coverage of the formula (0 to 100). It is rounded to a whole number (the old key).
    """
    items = []
    for b in breakdown:
        related = b.get("related") or None
        items.append(_result(b["name"], b["status"], b.get("need_level"), b.get("have_level"), bool(b.get("must", True)),
                             related.get("name") if isinstance(related, dict) else None))
    return _summary(items, coverage)


def skill_match(job_skills: List[Any], names: Dict[str, str], levels: Optional[Dict[str, float]] = None,
                required: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """Each required skill of a job is "match", "partial" or "gap", with a reason. A small fallback without the formulas.

    `names` is the map of the skills of the person (see skill_names_from). `levels` (lower case name -> level) and `required`
    (lower case name -> level that the job asks for) make the match level-aware: a skill below the asked level is "partial" (fitStatus "below").
    Without them, every held skill is level 3 and every job skill asks for level 3.
    coverage = round(sum of the credits / number of skills x 100). A skill that meets its level has credit 1, a skill below has (have / need),
    a related skill has 0.5. It summarises the skills of ONE job. It is not a score on the person.
    """
    levels, required = levels or {}, required or {}
    items, credit = [], 0.0
    for s in job_skills:
        name = s["name"] if isinstance(s, dict) else str(s)
        must = s.get("must", True) if isinstance(s, dict) else True
        k = norm(name)
        need = float(s.get("level") if isinstance(s, dict) and s.get("level") else required.get(k, 3))
        if k in names:
            have = float(levels.get(k, 3))
            if have >= need:
                items.append(_result(name, "meets", need, have, must))
                credit += 1.0
            else:
                items.append(_result(name, "below", need, have, must))
                credit += have / need
            continue
        # A related skill from the taxonomy gives partial credit
        via = next((n for n in names if n in RELATED.get(k, ())), None)
        if via:
            items.append(_result(name, "related", need, None, must, names[via]))
            credit += 0.5
        else:
            items.append(_result(name, "missing", need, None, must))
    return _summary(items, 100.0 * credit / len(items) if items else None)


def _js_round(x: float) -> int:
    """Round half up, like JavaScript Math.round, so that the API gives the same numbers as the mock."""
    import math
    return int(math.floor(x + 0.5))
