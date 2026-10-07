#!/usr/bin/env python3
"""
Jinder Intelligence Engine - Formula 4: Candidate Benchmarking Model (CCF)
Standard: ASD-STE100 (Simplified Technical English)
Document: IE-SPEC-004 (see 04_CANDIDATE_BENCHMARKING.md)

The model gives merit dimensions for one profile. The platform shows the dimensions one by one (areas and radar axes).
It never shows the total (`relative_merit_score`) and it never ranks people with it.
It reads the shared profile only: skills with levels, level, years, certifications, awards, education. It never reads the CV text.
"""

import importlib.util
import math
import os
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
F1 = C.load_sibling("f1")

# (skill depth, experience, evidence rigor, transferable agility, level standing). The five weights sum to 1.00.
DEFAULT_WEIGHTS = (0.30, 0.20, 0.22, 0.12, 0.16)
EQUIVALENT_BAND = 8.0          # a total difference of 8 points or less is the "equivalent band" of compare_two_candidates
TIER_WEIGHT = {"foundation": 0.5, "associate": 1.0, "professional": 1.6, "specialty": 1.6}
FIELD_WORDS = ("computer", "software", "information", "data", "mathemat", "statistic", "engineering", "physic", "informatics", "artificial", "machine")


# =====================================================================
# 1. THE DIMENSIONS
# =====================================================================

def _hard(cand: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [s for s in cand["skills"].values() if s["kind"] not in ("method", "soft")]


def skill_depth_profile(cand: Dict[str, Any]) -> float:
    """Skill depth of a profile, 0 to 100: 100 (1 - exp(-P / 4.2)), P = sum over hard skills of (level / 5)^1.6 x rarity^0.4."""
    p = sum((F1.effective_level(s) / 5.0) ** 1.6 * max(1.0, s["rarity"]) ** 0.4 for s in _hard(cand))
    return 100.0 * C.sat(p, 4.2)


def skill_depth_for_job(cand: Dict[str, Any], job: Dict[str, Any]) -> Optional[float]:
    """Skill depth against a job, 0 to 100: the weighted mean of (level / 5) over the skills that the job asks for. A skill that is not held counts 0."""
    jb = C.prepare_job(job)
    if not jb["reqs"]:
        return None
    num = den = 0.0
    for r in jb["reqs"]:
        s = cand["skills"].get(r["key"])
        w = F1.requirement_weight(r)
        num += w * ((F1.effective_level(s) / 5.0) if s else 0.0)
        den += w
    return 100.0 * num / den if den > 0 else None


def experience_maturity(years: float) -> float:
    """Experience, 0 to 100: 100 (1 - exp(-years / 6.5))."""
    return 100.0 * C.sat(years, 6.5)


def level_standing(rank: Optional[float]) -> Optional[float]:
    """Level standing, 0 to 100: 100 (rank / 5)^0.9. None if the level is not known."""
    if rank is None:
        return None
    return 100.0 * (C.clamp(rank / 5.0)) ** 0.9


def certification_strength(cand: Dict[str, Any], ref_year: Optional[int] = None) -> float:
    """Certification strength, 0 to 100: 100 (1 - exp(-W / 1.8)), W = sum of tier weight x (0.7 + 0.3 exp(-age / 4)).
    Tier weights: foundation 0.5, associate 1.0, professional 1.6, specialty 1.6, other 0.7."""
    ref_year = ref_year or C.today_year()
    total = 0.0
    for c in cand["certs"].values():
        tier = (c["entry"] or {}).get("tier")
        w = TIER_WEIGHT.get(tier, 0.7)
        age = (ref_year - c["year"]) if c.get("year") else 0.0
        total += w * (0.7 + 0.3 * math.exp(-max(0.0, age) / 4.0))
    return 100.0 * C.sat(total, 1.8)


def award_strength(cand: Dict[str, Any], ref_year: Optional[int] = None) -> float:
    """Award strength, 0 to 100: 100 (1 - exp(-W / 1.5)), W = sum of (0.6 + 0.4 exp(-age / 6)) over the awards."""
    ref_year = ref_year or C.today_year()
    total = 0.0
    for a in cand["awards"]:
        age = (ref_year - a["year"]) if a.get("year") else 0.0
        total += 0.6 + 0.4 * math.exp(-max(0.0, age) / 6.0)
    return 100.0 * C.sat(total, 1.5)


def evidence_rigor(cand: Dict[str, Any]) -> float:
    """Evidence rigor, 0 to 100, from skill levels, years with each skill, certifications and awards. The CV text is NOT used.
    E = 0.50 x 100 (1 - exp(-Q / 5)) + 0.30 x certification strength + 0.20 x award strength,
    Q = sum over all skills of (level / 5)^2 x (0.7 + 0.3 min(1, years with the skill / 4))."""
    q = 0.0
    for s in cand["skills"].values():
        yrs = s.get("years")
        q += (F1.effective_level(s) / 5.0) ** 2 * (0.7 + 0.3 * min(1.0, (yrs if yrs is not None else 2.0) / 4.0))
    return 0.50 * 100.0 * C.sat(q, 5.0) + 0.30 * certification_strength(cand) + 0.20 * award_strength(cand)


def transferable_agility(cand: Dict[str, Any]) -> float:
    """Transferable agility, 0 to 100: 0.7 x 100 (1 - exp(-M / 2.6)) + 0.3 x (skill groups used / 7) x 100,
    M = sum over method and soft skills of (level / 5)^1.3 x rarity^0.3."""
    m = sum((F1.effective_level(s) / 5.0) ** 1.3 * max(1.0, s["rarity"]) ** 0.3 for s in cand["skills"].values() if s["kind"] in ("method", "soft"))
    groups = {s["group"] for s in cand["skills"].values() if s["group"] != "other"}
    n_groups = max(7, len(C.get_taxonomy().group_order))
    return 0.7 * 100.0 * C.sat(m, 2.6) + 0.3 * 100.0 * min(1.0, len(groups) / n_groups)


def education_level(cand: Dict[str, Any], fields: Any = None) -> Optional[float]:
    """Education, 0 to 100: 100 x (rank / 5)^0.8 x relevance. Relevance is 1.0 for a computing or maths field, 0.6 for another, 0.8 if not known."""
    rank = cand.get("education_rank")
    if rank is None:
        return None
    names = [str(f).lower() for f in (fields if isinstance(fields, list) else [fields]) if f]
    relevance = 0.8 if not names else (1.0 if any(w in n for n in names for w in FIELD_WORDS) else 0.6)
    return 100.0 * (C.clamp(rank / 5.0)) ** 0.8 * relevance


# =====================================================================
# 2. MERIT SCORE OF ONE PROFILE
# =====================================================================

def calculate_candidate_merit_score(cand: Dict[str, Any], weights: Tuple[float, float, float, float, float] = DEFAULT_WEIGHTS,
                                    job: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Formula 4: the merit dimensions of one profile, and the Relative Merit Score (RMS) that combines them.

    RMS = min(100, w1 depth + w2 experience + w3 evidence + w4 transferable + w5 level standing + education bonus (0 to 5)).
    With `job`, the skill depth is the mean level of the skills that the job asks for. The platform shows the dimensions, never the RMS.
    """
    assert abs(sum(weights) - 1.0) < 1e-4, "Weights must sum to 1.00"
    w_depth, w_exp, w_evid, w_trans, w_level = weights
    p = C.prepare_candidate(cand, shared_only=True)
    depth_job = skill_depth_for_job(p, job) if job is not None else None
    depth = depth_job if depth_job is not None else skill_depth_profile(p)
    exp_s = experience_maturity(p["years"])
    evid = evidence_rigor(p)
    trans = transferable_agility(p)
    stand = level_standing(p["level_rank"])
    edu = education_level(p, cand.get("field_of_study") if isinstance(cand, dict) else None)
    edu_bonus = 5.0 * edu / 100.0 if edu is not None else 0.5
    parts = [(w_depth, depth), (w_exp, exp_s), (w_evid, evid), (w_trans, trans)]
    if stand is not None:
        parts.append((w_level, stand))
    den = sum(w for w, _ in parts)
    rms = round(max(0.0, min(100.0, sum(w * v for w, v in parts) / den + edu_bonus)), 1)
    return {
        "candidate_id": p["id"], "candidate_name": p["alias"] or p["id"],
        "relative_merit_score": rms, "overall_score": rms,
        "sub_metrics": {
            "skill_depth": round(depth, 1), "experience_maturity": round(exp_s, 1), "evidence_rigor": round(evid, 1),
            "transferable_agility": round(trans, 1), "level_standing": C.r1(stand),
            "certification_strength": round(certification_strength(p), 1), "award_strength": round(award_strength(p), 1),
            "skill_breadth": round(100.0 * C.sat(len(_hard(p)), 10.0), 1), "education_level": C.r1(edu),
            "gap_penalty_deduction": 0.0, "education_bonus": round(edu_bonus, 2),
        },
        "depth_basis": "job" if depth_job is not None else "profile",
        "verified_years_exp": round(p["years"], 1), "has_statutory_gap": False,
    }


# =====================================================================
# 3. HEAD-TO-HEAD AND COHORT
# =====================================================================

def compare_two_candidates(cand_a: Dict[str, Any], cand_b: Dict[str, Any], job: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Head-to-head RMS of two profiles: the difference and a verdict. A difference of 8 points or less is the equivalent band."""
    ea, eb = calculate_candidate_merit_score(cand_a, job=job), calculate_candidate_merit_score(cand_b, job=job)
    delta = round(ea["relative_merit_score"] - eb["relative_merit_score"], 1)
    name_a, name_b = ea["candidate_name"], eb["candidate_name"]
    if delta > EQUIVALENT_BAND:
        verdict, superior = f"{name_a} has clearly more merit (+{delta} points).", name_a
    elif delta < -EQUIVALENT_BAND:
        verdict, superior = f"{name_b} has clearly more merit (+{abs(delta)} points).", name_b
    else:
        verdict, superior = f"The two profiles are in the same band (difference {abs(delta)} points). Choose on the fit to the job.", "Equivalent"
    return {"candidate_a": ea, "candidate_b": eb, "score_delta": delta, "hiring_verdict": verdict, "recommended_candidate": superior}


def rank_candidate_cohort(candidates: List[Dict[str, Any]], job: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """The RMS of N profiles, with the position and the percentile of each one in the group."""
    evaluated = [calculate_candidate_merit_score(c, job=job) for c in candidates]
    evaluated.sort(key=lambda x: (-x["relative_merit_score"], str(x["candidate_id"])))
    n = len(evaluated)
    for i, item in enumerate(evaluated):
        item["cohort_rank"] = i + 1
        item["cohort_percentile"] = round((1.0 - i / max(1, n - 1)) * 100.0, 1) if n > 1 else 100.0
    return {"total_candidates": n, "top_ranked_candidate": evaluated[0]["candidate_name"] if n else None, "ranked_shortlist": evaluated}


# =====================================================================
# 4. SELF-CHECK
# =====================================================================
if __name__ == "__main__":
    print("FORMULA 4 SELF-CHECK")
    a = {"id": "a", "alias": "Talent A", "level": "Senior", "years_experience": 8, "highest_education": "Master's degree",
         "skills": [{"name": "Python", "level": 5}, {"name": "SQL", "level": 4}, {"name": "Communication", "level": 4}],
         "certifications": [{"name": "SnowPro Core Certification", "year": 2025}], "awards": [{"name": "Hack", "kind": "hackathon", "year": 2024}]}
    b = {"id": "b", "alias": "Talent B", "level": "Junior", "years_experience": 1, "skills": [{"name": "Python", "level": 2}]}
    print(compare_two_candidates(a, b)["hiring_verdict"])
    print(calculate_candidate_merit_score(a)["sub_metrics"])
