#!/usr/bin/env python3
"""
Jinder Intelligence Engine - Formula 1: Skill Match Model (SMF) and Talent-Job Fit
Standard: ASD-STE100 (Simplified Technical English)
Document: IE-SPEC-001 (see 01_SKILL_MATCHING_MODEL.md)

This file has two public scores:
  * evaluate_skill_match(candidate, job_or_code)  the skill match (the old name and keys stay).
  * evaluate_job_fit(candidate, job)              the product "fit": 0 to 100, one decimal, continuous.
Both use one analysis (`analyse`). The other formula files use the same analysis.

Privacy: the formulas read skills, levels, years, roles, certifications, awards, places and work preferences only.
They never read a name, an email, a country, a nationality, a visa, an age, a gender or a photo.
"""

import importlib.util
import math
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple


def _load_common():
    name = "jinder_engine_common"
    mod = sys.modules.get(name)
    if mod is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine_common.py")
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return mod


C = _load_common()

# =====================================================================
# 1. CONSTANTS
# =====================================================================

# The weights of the product fit (sum = 1.00). A part that does not apply to a job is left out and the others grow to sum 1.00.
# Certifications and awards are not weighted parts. They add or remove points (see CERT_ADJUST_POINTS and AWARD_BONUS_POINTS).
FIT_WEIGHTS: Dict[str, float] = {
    "skills": 0.39, "methods": 0.04, "occupation": 0.16, "level": 0.10, "experience": 0.09,
    "domain": 0.10, "location": 0.07, "work_type": 0.02, "education": 0.03,
}
CERT_ADJUST_POINTS = 7.0          # certification adjustment = 7 (certification credit - 0.45): +3.85 if all are held, -3.15 if none is held
CERT_NEUTRAL = 0.45
IMPLIED_METHOD_WEIGHT = 0.4       # the methods of the job occupation count 0.4 of a method that the job lists
ASSUMED_METHOD_BASE = 0.5         # a method or soft skill that is not listed counts as an assumed level 0.5 + 0.3 x level rank ...
ASSUMED_METHOD_PER_RANK = 0.3
ASSUMED_METHOD_FACTOR = 0.5       # ... at half credit (the person did not list it, so it is not proven)
AWARD_BONUS_POINTS = 3.0          # the largest bonus (points on the 0 to 100 scale) for preferred awards
SURPLUS_CREDIT = 0.12             # the largest extra credit for a skill above the required level
UNDER_POWER = 1.3                 # credit below the required level = (have / need) ^ 1.3
RELATED_MAX = 0.55                # the largest credit for related skills
DEFAULT_BENCHMARK_YEARS = {1: 5.0, 2: 3.0, 3: 2.0, 4: 1.0, 5: 0.5}   # old ANZSCO skill level -> years (old dictionary shape only)
CODE_DECAY = 0.26                 # occupation code closeness = exp(-0.26 (6 - common digits) ^ 1.3)
OCC_PART_WEIGHTS = {"code": 0.26, "skills": 0.22, "title": 0.22, "spec": 0.16, "domain": 0.14}
WORK_TYPE_SIMILARITY = {
    frozenset(["full-time", "part-time"]): 0.50, frozenset(["full-time", "contract"]): 0.40, frozenset(["part-time", "contract"]): 0.50,
    frozenset(["full-time", "graduate / internship"]): 0.45, frozenset(["part-time", "graduate / internship"]): 0.40,
    frozenset(["contract", "graduate / internship"]): 0.25,
}


def get_taxonomy():
    return C.get_taxonomy()


# =====================================================================
# 2. PRIMITIVE FUNCTIONS (each one is documented in 01_SKILL_MATCHING_MODEL.md)
# =====================================================================

def skill_credit(have: float, need: float) -> float:
    """Credit of one required skill, from 0 to 1.12.
    have >= need:  1 + 0.12 (1 - exp(-(have - need) / 1.2))      (a small bonus above the level)
    have <  need:  (have / need) ^ 1.3                           (partial credit below the level)"""
    need = max(0.5, float(need))
    have = max(0.0, float(have))
    if have >= need:
        return 1.0 + SURPLUS_CREDIT * (1.0 - math.exp(-(have - need) / 1.2))
    return (have / need) ** UNDER_POWER


def effective_level(skill: Dict[str, Any], ref_year: Optional[int] = None) -> float:
    """The level of a skill after a small fade for a skill that was not used for years: level x (0.80 + 0.20 exp(-age / 3))."""
    last = skill.get("last_used")
    if last is None:
        return float(skill["level"])
    age = max(0.0, (ref_year or C.today_year()) - float(last))
    return float(skill["level"]) * (0.80 + 0.20 * math.exp(-age / 3.0))


def requirement_weight(req: Dict[str, Any]) -> float:
    """The weight of a required skill: (2 if must else 1) x rarity^0.6 x (0.7 + 0.1 x need level)."""
    return (2.0 if req.get("must", True) else 1.0) * (max(1.0, float(req.get("rarity", 1.0))) ** 0.6) * (0.7 + 0.1 * float(req["need"]))


def level_fit(candidate_rank: Optional[float], job_rank: Optional[float]) -> Optional[float]:
    """Level fit from 0 to 1. d = talent rank - job rank.
    d < 0 (below the level):  exp(-0.55 |d|^1.2)        d >= 0 (above the level):  exp(-0.28 d^1.2). None if a level is not known."""
    if candidate_rank is None or job_rank is None:
        return None
    d = float(candidate_rank) - float(job_rank)
    return math.exp(-0.55 * (-d) ** 1.2) if d < 0 else math.exp(-0.28 * d ** 1.2)


def years_fit(years: Optional[float], min_years: Optional[float], max_years: Optional[float]) -> Optional[float]:
    """Years fit from 0 to 1 against the years that the job asks for (lo = min, hi = max; hi = None means open-ended).
    y < lo:        0.92 exp(-(((lo - y) / s) ^ 1.4)), s = max(1.5, 0.6 lo)
    lo <= y <= hi: 0.92 + 0.08 (y - lo) / (hi - lo)         (open-ended: 0.92 + 0.08 min(1, (y - lo) / s))
    y > hi:        1 - 0.25 (1 - exp(-(y - hi) / 6))"""
    if years is None or min_years is None:
        return None
    lo = float(min_years)
    y = float(years)
    if y < lo:
        s = max(1.5, 0.6 * lo)
        return 0.92 * math.exp(-(((lo - y) / s) ** 1.4))
    if max_years is None:
        return 0.92 + 0.08 * min(1.0, (y - lo) / max(2.0, 0.6 * lo))
    hi = float(max_years)
    if y <= hi:
        return 0.92 + 0.08 * (y - lo) / (hi - lo) if hi > lo else 1.0
    return 1.0 - 0.25 * (1.0 - math.exp(-(y - hi) / 6.0))


def calculate_experience_multiplier(years_exp: float, skill_level: Any = None, min_years: Optional[float] = None,
                                    max_years: Optional[float] = None, level_rank: Optional[float] = None) -> float:
    """Phi: the experience multiplier of the skill match, from 0.78 to 1.05. Phi = 0.78 + 0.27 x years fit.
    The old call (years, ANZSCO skill level 1 to 5) still works: it gives min_years from DEFAULT_BENCHMARK_YEARS."""
    if min_years is None and level_rank is None:
        try:
            min_years = DEFAULT_BENCHMARK_YEARS.get(int(skill_level), 5.0) if skill_level is not None else 3.0
        except (TypeError, ValueError):
            min_years = 3.0
    elif min_years is None:
        min_years, max_years = get_taxonomy().typical_years(level_rank)
    e = years_fit(max(0.0, float(years_exp or 0.0)), min_years, max_years)
    return round(0.78 + 0.27 * (e if e is not None else 0.6), 3)


def code_closeness(code_a: Any, code_b: Any) -> Optional[float]:
    """Closeness of two ANZSCO codes from 0 to 1: exp(-0.26 (6 - c)^1.3), c = the number of equal first digits. None if a code is not usable."""
    a = (re.findall(r"\d{4,6}", str(code_a or "")) or [""])[0]
    b = (re.findall(r"\d{4,6}", str(code_b or "")) or [""])[0]
    if not a or not b:
        return None
    common = 0
    for x, y in zip(a, b):
        if x != y:
            break
        common += 1
    if a == b:
        common = 6
    return math.exp(-CODE_DECAY * (6 - min(6, common)) ** 1.3) if common < 6 else 1.0


def calculate_taxonomy_tree_score(cand_code: str, target_code: str) -> float:
    """S_tree from two codes only: 100 x exp(-0.26 (6 - c)^1.3). Unknown codes give 30.0 (a neutral value).
    The full model (evaluate_skill_match) also uses titles, skills, specialisation and domain, so it does not stop at 30."""
    v = code_closeness(cand_code, target_code)
    return round(100.0 * v, 1) if v is not None else 30.0


def _occupation_profile(occ: Optional[Dict[str, Any]]) -> Dict[str, float]:
    """skill key -> level x (1.0 for a must skill, 0.6 for another) for the core skills of a taxonomy occupation."""
    if not occ:
        return {}
    tax = get_taxonomy()
    memo = tax._profile_memo.get(str(occ.get("code")))
    if memo is not None:
        return memo
    out: Dict[str, float] = {}
    for s in occ.get("coreSkills") or []:
        canon = tax.canon_skill_name(s["name"]) or s["name"]
        out[C.norm_key(canon)] = float(s.get("level", 3)) * (1.0 if s.get("must", True) else 0.6)
    tax._profile_memo[str(occ.get("code"))] = out
    return out


def ruzicka(a: Dict[str, float], b: Dict[str, float]) -> float:
    """Weighted Jaccard of two {key: weight} dictionaries: sum(min) / sum(max). It is symmetric."""
    keys = set(a) | set(b)
    if not keys:
        return 0.0
    num = sum(min(a.get(k, 0.0), b.get(k, 0.0)) for k in keys)
    den = sum(max(a.get(k, 0.0), b.get(k, 0.0)) for k in keys)
    return num / den if den > 0 else 0.0


def _anchor_closeness(anchor: Dict[str, Any], cand: Dict[str, Any], job: Dict[str, Any]) -> Tuple[float, Dict[str, Optional[float]]]:
    """Closeness (0 to 1) of one role of the talent (anchor) to the occupation of the job, with its parts."""
    tax = get_taxonomy()
    parts: Dict[str, Optional[float]] = {k: None for k in OCC_PART_WEIGHTS}
    parts["code"] = code_closeness(anchor.get("digits"), job.get("code"))
    a_occ, j_occ = anchor.get("occ"), job.get("occ")
    if a_occ and j_occ:
        parts["skills"] = ruzicka(_occupation_profile(a_occ), _occupation_profile(j_occ)) if a_occ is not j_occ else 1.0
    a_tokens = anchor.get("tokens") or frozenset()
    j_tokens = job.get("tokens") or tax.title_tokens(job.get("title") or (j_occ or {}).get("title", ""))
    if a_tokens and j_tokens:
        parts["title"] = len(a_tokens & j_tokens) / len(a_tokens | j_tokens)
    j_spec = C.norm_key(job.get("specialisation"))
    if j_spec:
        c_spec = C.norm_key(cand.get("specialisation"))
        a_specs = {C.norm_key(s) for s in (a_occ or {}).get("specialisations") or []}
        a_domain = (a_occ or {}).get("domain") or cand.get("domain")
        if c_spec and c_spec == j_spec:
            parts["spec"] = 1.0
        elif j_spec in a_specs:
            parts["spec"] = 0.85
        elif a_domain and job.get("domain") and C.norm_key(a_domain) == C.norm_key(job.get("domain")):
            parts["spec"] = 0.35
        else:
            parts["spec"] = 0.05
    a_domain = (a_occ or {}).get("domain") or cand.get("domain")
    if a_domain and job.get("domain"):
        parts["domain"] = 1.0 if C.norm_key(a_domain) == C.norm_key(job["domain"]) else 0.15
    num = sum(OCC_PART_WEIGHTS[k] * v for k, v in parts.items() if v is not None)
    den = sum(OCC_PART_WEIGHTS[k] for k, v in parts.items() if v is not None)
    return (num / den if den > 0 else 0.0), parts


def occupation_closeness(cand: Dict[str, Any], job: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
    """O: the closeness of the talent roles (target roles and current title) to the occupation of the job, from 0 to 1.
    O = max over the roles of (role weight x closeness). Closeness = weighted mean of: code, occupation skills, title words, specialisation, domain.
    The parts that are not known are left out. With no role at all, O comes from specialisation and domain."""
    best, best_parts, best_source = 0.0, {}, ""
    anchors = cand.get("anchors") or []
    if not anchors:
        anchors = [{"digits": "", "occ": None, "tokens": frozenset(), "weight": 0.7, "source": "none"}]
    for a in anchors:
        value, parts = _anchor_closeness(a, cand, job)
        value *= float(a.get("weight", 1.0))
        if value > best or not best_parts:
            best, best_parts, best_source = value, parts, a.get("source", "")
    if not anchors or all(v is None for v in best_parts.values()):
        best = 0.30
    return C.clamp(best), {"parts": best_parts, "source": best_source}


def domain_fit(cand: Dict[str, Any], job: Dict[str, Any]) -> Optional[float]:
    """Domain fit from 0 to 1: the mean of (a) the declared domain equal to the job domain (1 or 0.15) and
    (b) the share of the talent skills that belong to the job domain, relative to the talent top domain."""
    jd = job.get("domain")
    if not jd:
        return None
    aff = cand.get("affinity", {}).get(jd)
    declared = None
    if cand.get("domain_declared") and cand.get("domain"):
        declared = 1.0 if C.norm_key(cand["domain"]) == C.norm_key(jd) else 0.15
    if aff is None and declared is None:
        return None
    if aff is None:
        return declared
    return aff if declared is None else 0.5 * declared + 0.5 * aff


def location_fit(cand: Dict[str, Any], job: Dict[str, Any]) -> Optional[float]:
    """Location and work-mode fit from 0 to 1. Remote fits everyone (1.0).
    Onsite:  0.25 + 0.75 exp(-d / 700)    Hybrid:  0.40 + 0.60 exp(-d / 900)    (d = km to the nearest preferred city)
    A work mode that the talent did not choose gives x 0.9 (not for Remote jobs). None if nothing is known."""
    mode = job.get("mode")
    if mode == "Remote":
        return 1.0
    city = job.get("city")
    if mode is None and city is None:
        return None
    mode = mode or "Onsite"
    dists = [d for d in (C.distance_km(city, c) for c in cand.get("cities") or []) if d is not None] if city else []
    if dists:
        d = min(dists)
        base = (0.25 + 0.75 * math.exp(-d / 700.0)) if mode == "Onsite" else (0.40 + 0.60 * math.exp(-d / 900.0))
    elif cand.get("wants_remote") and not cand.get("cities"):
        base = 0.40 if mode == "Onsite" else 0.60
    else:
        base = 0.60
    if cand.get("modes") and mode not in cand["modes"]:
        base *= 0.9
    return base


def work_type_fit(cand: Dict[str, Any], job: Dict[str, Any]) -> Optional[float]:
    """Work type fit from 0 to 1: 1 for the same type, else the best similarity to a type that the talent chose. None if not known."""
    jt = job.get("type")
    types = cand.get("types") or set()
    if not jt or not types:
        return None
    if jt in types:
        return 1.0
    return max(WORK_TYPE_SIMILARITY.get(frozenset([jt, t]), 0.20) for t in types)


def education_fit(cand: Dict[str, Any], job: Dict[str, Any]) -> Optional[float]:
    """Education fit from 0.2 to 1. Education is a soft factor: it is never a hard limit and it never gives 0.
    1 if the talent has the minimum or more, else 0.2 + 0.8 exp(-0.7 x steps below). A talent with no qualification counts as 0 steps of education.
    None if the job asks for no education."""
    need = job.get("education_min")
    if need is None:
        return None
    have = cand.get("education_rank")
    have = 0 if have is None else have
    return 1.0 if have >= need else 0.2 + 0.8 * math.exp(-0.7 * (need - have))


# =====================================================================
# 3. THE PER-SKILL MATCH
# =====================================================================

def _related_credit(req: Dict[str, Any], cand: Dict[str, Any], ref_year: int) -> Tuple[float, Optional[Dict[str, Any]], int]:
    """Credit for related skills: min(0.55, 0.45 r^1.2 + 0.04 (n - 1)), r = min(1, best related level / need). Returns (credit, best skill, n)."""
    tax = get_taxonomy()
    rel_names = tax.related.get(req["name"]) or ()
    held = []
    for name in rel_names:
        s = cand["skills"].get(C.norm_key(name))
        if s:
            held.append((effective_level(s, ref_year), s))
    if not held:
        return 0.0, None, 0
    held.sort(key=lambda t: -t[0])
    ratio = min(1.0, held[0][0] / max(0.5, req["need"]))
    credit = min(RELATED_MAX, 0.45 * ratio ** 1.2 + 0.04 * (len(held) - 1))
    return credit, {"name": held[0][1]["name"], "level": round(held[0][0], 2)}, len(held)


def match_requirements(cand: Dict[str, Any], reqs: List[Dict[str, Any]], ref_year: Optional[int] = None) -> List[Dict[str, Any]]:
    """The credit of each required skill. This list is the `skill_breakdown`.
    status: 'meets' (level >= need), 'below' (the skill is held under the level), 'related' (only a related skill), 'missing'."""
    ref_year = ref_year or C.today_year()
    items = []
    for r in reqs:
        s = cand["skills"].get(r["key"])
        need = float(r["need"])
        related, rel_n = None, 0
        if s:
            have = effective_level(s, ref_year)
            credit = skill_credit(have, need)
            status = "meets" if have >= need - 1e-9 else "below"
            have_level = round(float(s["level"]), 2)
        else:
            credit, related, rel_n = _related_credit(r, cand, ref_year)
            status = "related" if related else "missing"
            have_level = None
            have = 0.0
        items.append({
            "name": r["name"], "key": r["key"], "group": r["group"], "kind": r["kind"], "must": bool(r.get("must", True)),
            "need_level": round(need, 2), "have_level": have_level, "have_effective": round(have, 3),
            "credit": round(credit, 4), "weight": round(requirement_weight(r), 4), "status": status, "related": related, "related_count": rel_n,
            "rarity": r["rarity"], "months": r["months"],
        })
    return items


def _method_requirements(job: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """(listed, implied). Listed: the method and soft skills in the job skill list.
    Implied: the methods of the job occupation (level 3, not required). The implied ones feed S_trans only; they are not in the skill breakdown."""
    tax = get_taxonomy()
    listed = [r for r in job["reqs"] if r["kind"] in ("method", "soft")]
    have = {r["key"] for r in listed}
    implied = []
    for name in job.get("occ_methods") or []:
        e = C.skill_entry(name, 3, tax)
        if e and e["key"] not in have:
            e["must"], e["need"] = False, 3.0
            implied.append(e)
            have.add(e["key"])
    return listed, implied


def assumed_method_level(level_rank: Optional[float]) -> float:
    """The level that Formula 1 assumes for a method or soft skill that the person did not list: 0.5 + 0.3 x level rank (Mid: 1.1)."""
    return ASSUMED_METHOD_BASE + ASSUMED_METHOD_PER_RANK * (2.0 if level_rank is None else float(level_rank))


def _trans_score(items: List[Dict[str, Any]], level_rank: Optional[float]) -> Optional[float]:
    """S_trans: like the other skill scores, but a method or soft skill that is missing (or only related) gets at least
    0.5 x credit(assumed level, need level). People seldom list the way they work, and a more senior person works in more ways."""
    den = sum(i["weight"] for i in items)
    if den <= 0:
        return None
    assumed = assumed_method_level(level_rank)
    num = 0.0
    for i in items:
        c = i["credit"]
        if i["status"] in ("missing", "related"):
            c = max(c, ASSUMED_METHOD_FACTOR * skill_credit(assumed, i["need_level"]))
        num += i["weight"] * c
    return 100.0 * min(1.0, num / den)


def _score_items(items: List[Dict[str, Any]]) -> Optional[float]:
    """100 x min(1, sum(weight x credit) / sum(weight)). None for an empty list."""
    den = sum(i["weight"] for i in items)
    if den <= 0:
        return None
    return 100.0 * min(1.0, sum(i["weight"] * i["credit"] for i in items) / den)


def analyse(candidate: Any, job: Any, ref_year: Optional[int] = None, shared_only: bool = False) -> Dict[str, Any]:
    """The analysis of one talent and one job. Every part is a number from 0 to 1 (None if it does not apply).
    Formulas 1, 2, 5 and 6 read this result. The inputs can be old or version 2 dictionaries, or prepared ones.
    shared_only=True is for the employer side: the CV text is not read."""
    cand = C.prepare_candidate(candidate, shared_only=shared_only)
    jb = C.prepare_job(job)
    ref_year = ref_year or C.today_year()
    tax = get_taxonomy()

    hard_reqs = [r for r in jb["reqs"] if r["kind"] not in ("method", "soft")]
    listed_reqs, implied_reqs = _method_requirements(jb)
    hard_items = match_requirements(cand, hard_reqs, ref_year)
    listed_items = match_requirements(cand, listed_reqs, ref_year)
    implied_items = match_requirements(cand, implied_reqs, ref_year)
    for i in implied_items:
        i["weight"] = round(i["weight"] * IMPLIED_METHOD_WEIGHT, 4)
        i["implied"] = True
    method_items = listed_items + implied_items
    all_items = hard_items + listed_items            # the skills that the job lists (the skill breakdown)

    # ----- the skill parts (0 to 100) -----
    dom = domain_fit(cand, jb)
    s_direct = _score_items(hard_items)
    if s_direct is None:      # a job with no skill list: the talent skill share in the job domain gives a value
        s_direct = 100.0 * (0.25 + 0.5 * (dom if dom is not None else 0.4))
    s_trans = _trans_score(method_items, cand["level_rank"])
    if s_trans is None:       # no method is asked: the talent method skills give a value
        mine = [s for s in cand["skills"].values() if s["kind"] in ("method", "soft")]
        s_trans = 100.0 * (0.30 + 0.60 * C.sat(sum(effective_level(s, ref_year) / 5.0 for s in mine), 2.5))
    # the coverage is the weighted share of all required skills that are met (credit capped at 1)
    cov_items = [i for i in all_items if i["weight"] > 0]
    coverage = (100.0 * sum(i["weight"] * min(1.0, i["credit"]) for i in cov_items) / sum(i["weight"] for i in cov_items)) if cov_items else None

    occ, occ_info = occupation_closeness(cand, jb)
    lvl = level_fit(cand["level_rank"], jb["level_rank"])
    yrs = years_fit(cand["years"], jb["min_years"], jb["max_years"])
    loc = location_fit(cand, jb)
    wtype = work_type_fit(cand, jb)
    edu = education_fit(cand, jb)

    # ----- certifications: required (weight 2) and preferred (weight 1) -----
    cert_items = []
    held_keys = set(cand["certs"].keys())
    for group, weight, near in ((jb["certs_required"], 2.0, 0.30), (jb["certs_preferred"], 1.0, 0.25)):
        for c in group:
            held = c["key"] in held_keys
            closeness = 0.0
            evid = (c["entry"] or {}).get("evidences") or []
            if evid:
                vals = []
                for e in evid:
                    s = cand["skills"].get(C.norm_key(tax.canon_skill_name(e) or e))
                    vals.append(min(1.0, effective_level(s, ref_year) / 3.0) if s else 0.0)
                closeness = sum(vals) / len(vals)
            cert_items.append({"name": c["name"], "required": group is jb["certs_required"], "held": held, "weight": weight,
                               "closeness": round(closeness, 3), "credit": 1.0 if held else near * closeness,
                               "prep_months": float((c["entry"] or {}).get("prepMonths") or 2.0), "tier": (c["entry"] or {}).get("tier")})
    cert_fit = (sum(i["weight"] * i["credit"] for i in cert_items) / sum(i["weight"] for i in cert_items)) if cert_items else None

    # ----- awards: the share of the preferred award kinds that the talent has (recent awards count more) -----
    award_fit = None
    award_items = []
    if jb["awards_preferred"]:
        vals = []
        for kind in jb["awards_preferred"]:
            mine = [a for a in cand["awards"] if a["kind"] == kind]
            if mine:
                best = 0.0
                for a in mine:
                    age = (ref_year - a["year"]) if a.get("year") else None
                    best = max(best, 0.8 if age is None else 0.6 + 0.4 * math.exp(-max(0.0, age) / 6.0))
                vals.append(best)
                award_items.append({"kind": kind, "held": True, "credit": round(best, 3)})
            else:
                vals.append(0.0)
                award_items.append({"kind": kind, "held": False, "credit": 0.0})
        award_fit = sum(vals) / len(vals)

    return {
        "cand": cand, "job": jb, "ref_year": ref_year,
        "items": all_items, "hard_items": hard_items, "method_items": method_items,
        "s_direct": s_direct, "s_trans": s_trans, "coverage": coverage,
        "occupation": occ, "occupation_info": occ_info, "level": lvl, "years": yrs, "domain": dom,
        "location": loc, "work_type": wtype, "education": edu,
        "cert_fit": cert_fit, "cert_items": cert_items, "award_fit": award_fit, "award_items": award_items,
    }


# =====================================================================
# 4. THE SKILL MATCH (SMF) - the old name and keys stay
# =====================================================================

def _tier(score: float) -> Tuple[str, str]:
    if score >= 85.0:
        return "Direct Industry Alignment", "TIER_1_DIRECT"
    if score >= 70.0:
        return "Transferable Cross-Sector Capability", "TIER_2_TRANSFERABLE"
    return "Emerging Career Bridge", "TIER_3_BRIDGE"


def _target_to_job(target: Any) -> Dict[str, Any]:
    """The second argument of evaluate_skill_match: an ANZSCO code (text) or a job dictionary."""
    if isinstance(target, dict):
        job = dict(target)
        if "skill_level" in job and job.get("min_years") is None and job.get("minYears") is None and job.get("level") is None:
            try:
                job["min_years"] = DEFAULT_BENCHMARK_YEARS.get(int(job["skill_level"]), 5.0)
            except (TypeError, ValueError):
                pass
        return job
    return {"anzsco_code": str(target or "").strip()}


def smf_from_analysis(an: Dict[str, Any], weights: Tuple[float, float, float] = (0.25, 0.50, 0.25)) -> Dict[str, float]:
    """The numbers of the skill match: S_tree, S_direct, S_trans, Phi, the base and the final score (not rounded)."""
    w1, w2, w3 = weights
    s_tree = 100.0 * an["occupation"]
    e = an["years"] if an["years"] is not None else 0.6
    l = an["level"] if an["level"] is not None else 0.6
    phi = 0.78 + 0.27 * (0.55 * e + 0.45 * l)
    base = w1 * s_tree + w2 * an["s_direct"] + w3 * an["s_trans"]
    return {"s_tree": s_tree, "s_direct": an["s_direct"], "s_trans": an["s_trans"], "phi": phi, "base": base, "final": max(0.0, min(100.0, base * phi))}


def evaluate_skill_match(candidate: Dict[str, Any], target_occupation_code_or_dict: Any,
                         weights: Tuple[float, float, float] = (0.25, 0.50, 0.25)) -> Dict[str, Any]:
    """Formula 1: the skill match (SMF) of a talent to a job (or to an ANZSCO code of the taxonomy).

    SMF = min(100, (w1 S_tree + w2 S_direct + w3 S_trans) x Phi),  Phi = 0.78 + 0.27 (0.55 years fit + 0.45 level fit).
    """
    assert abs(sum(weights) - 1.0) < 1e-4, "Weights must sum to 1.00"
    an = analyse(candidate, _target_to_job(target_occupation_code_or_dict))
    cand, jb = an["cand"], an["job"]
    m = smf_from_analysis(an, weights)
    final = round(m["final"], 1)
    tier, tier_code = _tier(final)
    hard, meth = an["hard_items"], an["method_items"]
    occ = jb.get("occ") or {}
    return {
        "candidate_id": cand["id"], "candidate_name": cand["alias"] or cand["id"],
        "target_anzsco_code": jb["code"], "target_anzsco_title": jb["anzsco_title"] or occ.get("title") or jb["title"] or "Certified Occupation",
        "sub_metrics": {
            "s_tree_taxonomy": round(m["s_tree"], 1), "s_direct_competency": round(m["s_direct"], 1), "s_trans_methodology": round(m["s_trans"], 1),
            "phi_experience_multiplier": round(m["phi"], 3),
            "s_level_fit": C.r1(None if an["level"] is None else 100.0 * an["level"]),
            "s_years_fit": C.r1(None if an["years"] is None else 100.0 * an["years"]),
        },
        "competency_breakdown": {
            "matched_core_skills": [i["name"] for i in hard if i["status"] == "meets"],
            "missing_core_skills": [i["name"] for i in hard if i["status"] != "meets"],
            "matched_transferable_skills": [i["name"] for i in meth if i["status"] == "meets"],
            "missing_transferable_skills": [i["name"] for i in meth if i["status"] != "meets"],
            "statutory_requirements": [c["name"] for c in an["cert_items"] if c["required"]],
        },
        "skill_breakdown": an["items"],
        "skill_coverage": C.r1(an["coverage"]),
        "base_composite_score": round(m["base"], 1), "final_match_score": final, "overall_score": final,
        "match_tier": tier, "match_tier_code": tier_code, "is_direct_ready": final >= 85.0,
    }


# =====================================================================
# 5. THE PRODUCT FIT (0 to 100, one decimal, continuous)
# =====================================================================

def fit_from_analysis(an: Dict[str, Any], weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """fit = 100 x sum(w_i p_i) / sum(w_i) over the parts that apply (each p_i from 0 to 1)
             + 7 (certification credit - 0.45)   (only if the job lists certifications)
             + 3 x award credit                  (only if the job lists preferred award kinds).  The result is kept between 0 and 100."""
    w = dict(FIT_WEIGHTS)
    if weights:
        w.update(weights)
    parts = {
        "skills": an["s_direct"] / 100.0, "methods": an["s_trans"] / 100.0, "occupation": an["occupation"], "level": an["level"],
        "experience": an["years"], "domain": an["domain"], "location": an["location"], "work_type": an["work_type"], "education": an["education"],
    }
    used = {k: v for k, v in parts.items() if v is not None and w.get(k, 0.0) > 0}
    den = sum(w[k] for k in used)
    base = 100.0 * sum(w[k] * used[k] for k in used) / den if den > 0 else 0.0
    cert_adj = CERT_ADJUST_POINTS * (an["cert_fit"] - CERT_NEUTRAL) if an["cert_fit"] is not None else 0.0
    bonus = AWARD_BONUS_POINTS * an["award_fit"] if an["award_fit"] is not None else 0.0
    exact = max(0.0, min(100.0, base + cert_adj + bonus))
    shown = dict(parts)
    shown["certifications"] = an["cert_fit"]
    return {
        "fit": round(exact, 1), "fit_exact": exact,
        "parts": {k: C.r1(None if v is None else 100.0 * v) for k, v in shown.items()},
        "weights": {k: round(w[k] / den, 4) for k in used} if den > 0 else {},
        "bonus": {"certifications": round(cert_adj, 2), "awards": round(bonus, 2)},
    }


def evaluate_job_fit(candidate: Dict[str, Any], job: Dict[str, Any], weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """The product fit of a talent to a job: 0 to 100, one decimal, continuous. The platform mixes it as 0.55 fit + 0.45 FRS.

    Parts (each 0 to 100): skills, methods, occupation, level, experience, domain, location, work_type, education, certifications.
    The certification part is not weighted: it adds or removes points (`bonus.certifications`). Awards add up to 3 points (`bonus.awards`).
    The result also has the `skill_breakdown` (one item for each required skill) and the facts behind the level and years parts.
    """
    an = analyse(candidate, job)
    cand, jb = an["cand"], an["job"]
    tax = get_taxonomy()
    res = fit_from_analysis(an, weights)
    items = an["items"]
    res.update({
        "candidate_id": cand["id"], "job_id": jb["id"],
        "skill_breakdown": items,
        "skill_coverage": C.r1(an["coverage"]),
        "counts": {"required": len(items), "meets": sum(1 for i in items if i["status"] == "meets"), "below": sum(1 for i in items if i["status"] == "below"),
                   "related": sum(1 for i in items if i["status"] == "related"), "missing": sum(1 for i in items if i["status"] == "missing")},
        "level": {"candidate": tax.level_name(cand["level_rank"]), "job": tax.level_name(jb["level_rank"]), "estimated": cand["level_estimated"],
                  "gap": None if cand["level_rank"] is None or jb["level_rank"] is None else round(cand["level_rank"] - jb["level_rank"], 2)},
        "years": {"candidate": round(cand["years"], 1), "min": jb["min_years"], "max": jb["max_years"], "known": cand["years_known"]},
        "certifications": an["cert_items"], "awards": an["award_items"],
        "occupation": {"closeness": round(an["occupation"], 4), "source": an["occupation_info"].get("source")},
    })
    return res


# =====================================================================
# 6. OLD HELPERS (kept so that old callers do not break)
# =====================================================================

def extract_candidate_text_corpus(candidate: Dict[str, Any]) -> str:
    """All text of the talent skills and CV in one lower-case string (old helper)."""
    parts = []
    for s in candidate.get("skills", []) or []:
        parts.append(" ".join(str(s.get(k, "")) for k in ("name", "skill_name", "evidence", "evidence_quote")) if isinstance(s, dict) else str(s))
    for key in ("direct_skills", "transferable_skills", "skill_evidence_excerpts", "rawResume", "raw_resume_sample", "cv_raw_text",
                "original_job_title", "current_title", "originRole", "highest_education"):
        parts.append(str(candidate.get(key, "")))
    return " ".join(parts).lower()


def tokenize_text(text: str) -> set:
    """Lower-case words and two-word pairs (old helper)."""
    words = re.sub(r"[^\w\s-]", " ", str(text).lower()).split()
    tokens = {w for w in words if len(w) >= 2}
    tokens.update(f"{words[i]} {words[i + 1]}" for i in range(len(words) - 1))
    return tokens


def calculate_competency_overlap(cand_corpus: str, required_skills: List[str]) -> Tuple[float, List[str], List[str]]:
    """Old text-based overlap. It looks for the skill names (and aliases) in a text. Returns (score 0 to 100, matched, missing)."""
    tax = get_taxonomy()
    if not required_skills:
        return 75.0, [], []
    found = {C.norm_key(x) for x in tax.find_skills_in_text(cand_corpus)}
    text = C.norm_key(cand_corpus)
    matched, missing = [], []
    for req in required_skills:
        canon = tax.canon_skill_name(req) or req
        if C.norm_key(canon) in found or C.norm_key(req) in text:
            matched.append(req)
        else:
            missing.append(req)
    num = sum(max(1.0, (tax.skill_info(tax.canon_skill_name(s)) or {}).get("rarity", 1.4)) for s in matched)
    den = sum(max(1.0, (tax.skill_info(tax.canon_skill_name(s)) or {}).get("rarity", 1.4)) for s in required_skills)
    return round(100.0 * num / den, 1), matched, missing


# =====================================================================
# 7. SELF-CHECK
# =====================================================================
if __name__ == "__main__":
    print("FORMULA 1 SELF-CHECK")
    cand = {"id": "demo", "alias": "Demo talent", "level": "Mid", "years_experience": 4, "domain": "Data", "current_title": "Data Analyst",
            "skills": [{"name": "SQL", "level": 4}, {"name": "Python", "level": 3}, {"name": "Tableau", "level": 3}],
            "preferred_location": "Sydney"}
    job = {"id": "job-1", "title": "Data Engineer", "category": "Data", "level": "Mid", "min_years": 3, "max_years": 6, "city": "Sydney",
           "work_mode": "Hybrid", "required_skills": [{"name": "SQL", "level": 4, "must": True}, {"name": "Python", "level": 4, "must": True},
                                                       {"name": "Apache Airflow", "level": 3, "must": False}]}
    fit = evaluate_job_fit(cand, job)
    print("fit", fit["fit"], fit["parts"])
    print("SMF", evaluate_skill_match(cand, job)["final_match_score"])
