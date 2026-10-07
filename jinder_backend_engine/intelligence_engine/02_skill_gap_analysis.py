#!/usr/bin/env python3
"""
Jinder Intelligence Engine - Formula 2: Skill Gap and Readiness Model (SGF)
Standard: ASD-STE100 (Simplified Technical English)
Document: IE-SPEC-002 (see 02_SKILL_GAP_ANALYSIS.md)

Public functions:
  * evaluate_skill_gaps(candidate, job, explicit_missing_skills=None)   gaps, strengths, readiness, months to close.
  * evaluate_path(candidate, job)                                       the `path` object of "Your path to this job".
Privacy: only skills, levels, years, certifications and awards are read.
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

# =====================================================================
# 1. CONSTANTS
# =====================================================================
PARALLEL_FACTOR = 0.18        # T_total = max(T) + 0.18 x sum(other T)
READINESS_SCALE = 70.0        # JRS = 100 exp(-S / 70)
MAX_ITEM_MONTHS = 18.0        # the longest time for one skill
LEVEL_EFFORT_POWER = 1.6      # effort to reach level l (from zero) = (l / 3) ^ 1.6, so level 3 = 1.0
GAP_WEIGHTS = {"skill_must": 1.0, "skill_nice": 0.45, "cert_required": 0.90, "cert_preferred": 0.35, "experience": 0.70, "level": 0.80}
CATEGORIES = {
    "CAT-1": "Certification or credential",
    "CAT-2": "Required skill",
    "CAT-3": "Nice-to-have skill",
    "CAT-4": "Experience or level",
}


# =====================================================================
# 2. TIME TO CLOSE A GAP
# =====================================================================

def level_effort(level: float) -> float:
    """Effort to reach a level from zero: (level / 3) ^ 1.6. Level 3 (Proficient) = 1.0. monthsToLearn is the time for 1.0."""
    return (max(0.0, float(level)) / 3.0) ** LEVEL_EFFORT_POWER


def learner_factor(years: float, education_rank: Optional[int]) -> float:
    """Learning speed: 1 - 0.16 (1 - exp(-years / 8)) - 0.012 x min(education rank, 4). It is from 0.80 to 1.00."""
    return 1.0 - 0.16 * C.sat(years, 8.0) - 0.012 * min(4, education_rank or 0)


def skill_months(months_to_l3: float, have: float, need: float, related_credit: float, learner: float) -> float:
    """Months to go from level `have` to level `need`: monthsToLearn x (E(need) - E(have)) x (1 - 0.30 min(1, related credit / 0.45)) x learner.
    A related skill that the person holds makes the learning faster. The result is from 0.25 to 18 months."""
    effort = max(0.0, level_effort(need) - level_effort(have))
    speed = 1.0 - 0.30 * min(1.0, related_credit / 0.45)
    return C.clamp(months_to_l3 * effort * speed * learner, 0.25, MAX_ITEM_MONTHS)


def experience_months(shortfall_years: float) -> float:
    """Months to close an experience gap: 14 (1 - exp(-shortfall / 2.2)). It grows with the gap but it has an end."""
    return 14.0 * C.sat(shortfall_years, 2.2)


def level_months(rank_steps: float) -> float:
    """Months to close a level gap: 6 x steps ^ 1.1, at most 24."""
    return min(24.0, 6.0 * max(0.0, rank_steps) ** 1.1)


def item_severity(weight: float, months: float) -> float:
    """Severity of one gap: w x (16 (1 - exp(-T / 2.5)) + 3 ln(1 + T)). It is 0 for T = 0 and it grows smoothly."""
    return weight * (16.0 * C.sat(months, 2.5) + 3.0 * math.log(1.0 + months))


def parallel_months(months: List[float]) -> float:
    """T_total = max(T) + 0.18 x (sum(T) - max(T)): the person learns some things at the same time."""
    if not months:
        return 0.0
    top = max(months)
    return top + PARALLEL_FACTOR * (sum(months) - top)


def readiness_tier(jrs: float) -> Tuple[str, str]:
    if jrs >= 80.0:
        return "Low Gap (Immediate Deployment)", "TIER_LOW_GAP"
    if jrs >= 55.0:
        return "Moderate Gap (Fast-Track Upskilling)", "TIER_MODERATE_GAP"
    return "High Gap (Structural Bridging Required)", "TIER_HIGH_GAP"


def level_label(level: Optional[float]) -> str:
    """The word of a skill level (1 Beginner ... 5 Expert). A value between two levels takes the nearest."""
    if level is None or level <= 0:
        return "none"
    labels = C.get_taxonomy().skill_levels
    return labels.get(int(C.clamp(round(level), 1, 5)), str(level))


def _years_text(years: Optional[float]) -> str:
    if years is None:
        return ""
    return f"{years:g} year" + ("" if abs(years - 1.0) < 1e-9 else "s")


# =====================================================================
# 3. GAPS AND STRENGTHS
# =====================================================================

def _legacy_keys(item: Dict[str, Any], category: str, weight: float) -> None:
    """The keys of the old gap item, so that old callers still work."""
    item.update({"gap_name": item["item"], "category_code": category, "category_name": CATEGORIES[category], "weight": weight,
                 "duration_months": item["months"], "is_statutory_blocker": False})


def gaps_and_strengths(an: Dict[str, Any], explicit_missing: Optional[List[str]] = None) -> Dict[str, Any]:
    """Builds the gap items, the strength items and the readiness numbers from the analysis of Formula 1."""
    cand, jb = an["cand"], an["job"]
    tax = C.get_taxonomy()
    learner = learner_factor(cand["years"], cand["education_rank"])
    gaps: List[Dict[str, Any]] = []
    strengths: List[Dict[str, Any]] = []
    internal: List[Tuple[float, float]] = []          # (weight, months) for the readiness sum, also for items below the list threshold

    # ----- skills -----
    seen = set()
    for it in an["items"]:
        seen.add(it["key"])
        if it["status"] == "meets":
            strengths.append({"kind": "skill", "item": it["name"], "skill": it["name"], "have_level": it["have_level"], "need_level": it["need_level"],
                              "surplus": round(max(0.0, (it["have_effective"] or 0.0) - it["need_level"]), 2), "must": it["must"], "group": it["group"],
                              "credit": it["credit"], "note": ""})
            continue
        have = it["have_effective"] if it["status"] == "below" else 0.0
        months = skill_months(it["months"], have, it["need_level"], it["credit"] if it["status"] == "related" else 0.0, learner)
        weight = GAP_WEIGHTS["skill_must"] if it["must"] else GAP_WEIGHTS["skill_nice"]
        internal.append((weight, months))
        note = ""
        if it["status"] == "related" and it.get("related"):
            note = f"You have a related skill: {it['related']['name']}."
        gap = {"kind": "below_level" if it["status"] == "below" else "missing", "item": it["name"], "skill": it["name"],
               "have_level": it["have_level"] if it["status"] == "below" else 0, "need_level": it["need_level"], "months": round(months, 1),
               "must": it["must"], "group": it["group"], "note": note, "severity_points": round(item_severity(weight, months), 2)}
        _legacy_keys(gap, "CAT-2" if it["must"] else "CAT-3", weight)
        gaps.append(gap)
    for name in explicit_missing or []:                    # names that the caller found missing and that the job list does not have
        e = C.skill_entry(name, 3)
        if not e or e["key"] in seen or e["key"] in cand["skills"]:
            continue
        seen.add(e["key"])
        months = skill_months(e["months"], 0.0, 3.0, 0.0, learner)
        weight = GAP_WEIGHTS["skill_must"]
        internal.append((weight, months))
        gap = {"kind": "missing", "item": e["name"], "skill": e["name"], "have_level": 0, "need_level": 3.0, "months": round(months, 1), "must": True,
               "group": e["group"], "note": "", "severity_points": round(item_severity(weight, months), 2)}
        _legacy_keys(gap, "CAT-2", weight)
        gaps.append(gap)

    # ----- experience -----
    if jb["min_years"] is not None:
        short = jb["min_years"] - cand["years"]
        if short > 0:
            months = experience_months(short)
            internal.append((GAP_WEIGHTS["experience"], months))
            if short >= 0.5:
                gap = {"kind": "experience", "item": "Experience", "have_level": round(cand["years"], 1), "need_level": jb["min_years"], "months": round(months, 1),
                       "must": True, "note": "", "severity_points": round(item_severity(GAP_WEIGHTS["experience"], months), 2)}
                _legacy_keys(gap, "CAT-4", GAP_WEIGHTS["experience"])
                gaps.append(gap)
        else:
            strengths.append({"kind": "experience", "item": "Experience", "have_level": round(cand["years"], 1), "need_level": jb["min_years"],
                              "surplus": round(cand["years"] - jb["min_years"], 1), "must": True, "note": ""})

    # ----- level -----
    if cand["level_rank"] is not None and jb["level_rank"] is not None:
        steps = jb["level_rank"] - cand["level_rank"]
        if steps > 0:
            months = level_months(steps)
            internal.append((GAP_WEIGHTS["level"], months))
            if steps >= 0.75:
                gap = {"kind": "level", "item": "Level", "have_level": tax.level_name(cand["level_rank"]), "need_level": tax.level_name(jb["level_rank"]),
                       "months": round(months, 1), "must": True, "note": "",
                       "severity_points": round(item_severity(GAP_WEIGHTS["level"], months), 2)}
                _legacy_keys(gap, "CAT-4", GAP_WEIGHTS["level"])
                gaps.append(gap)
        else:
            strengths.append({"kind": "level", "item": "Level", "have_level": tax.level_name(cand["level_rank"]), "need_level": tax.level_name(jb["level_rank"]),
                              "surplus": round(-steps, 2), "must": True, "note": ""})

    # ----- certifications (a required one that is missing is a gap with months = preparation time; it is not a legal block) -----
    for c in an["cert_items"]:
        if c["held"]:
            strengths.append({"kind": "certification", "item": c["name"], "have_level": "Held", "need_level": "Required" if c["required"] else "Preferred",
                              "must": c["required"], "note": ""})
            continue
        months = c["prep_months"] * (1.0 - 0.5 * c["closeness"]) * learner
        w = GAP_WEIGHTS["cert_required"] if c["required"] else GAP_WEIGHTS["cert_preferred"]
        internal.append((w, months))
        gap = {"kind": "certification", "item": c["name"], "have_level": "none", "need_level": "Required" if c["required"] else "Preferred",
               "months": round(months, 1), "must": c["required"], "note": "", "severity_points": round(item_severity(w, months), 2)}
        _legacy_keys(gap, "CAT-1", w)
        gaps.append(gap)

    # ----- awards (a strength only) -----
    for a in an["award_items"]:
        if a["held"]:
            label = (tax.award_kinds.get(a["kind"]) or {}).get("label") or a["kind"]
            strengths.append({"kind": "award", "item": label, "have_level": "Held", "need_level": "Preferred", "must": False, "note": ""})

    # ----- readiness -----
    friction = 6.0 * (1.0 - an["occupation"])                # the cost of a move to a different kind of role
    total = sum(item_severity(w, t) for w, t in internal) + friction
    jrs = 100.0 * math.exp(-total / READINESS_SCALE)
    gsi = 100.0 - jrs
    t_total = parallel_months([t for _, t in internal])
    tier, tier_code = readiness_tier(jrs)
    gaps.sort(key=lambda g: (-g["severity_points"], g["item"]))
    return {
        "gaps": gaps, "strengths": strengths, "severity_sum": total, "friction": friction, "learner_factor": learner,
        "gsi": gsi, "jrs": jrs, "months": t_total, "tier": tier, "tier_code": tier_code,
    }


def evaluate_skill_gaps(candidate: Dict[str, Any], job: Dict[str, Any], explicit_missing_skills: Optional[List[str]] = None) -> Dict[str, Any]:
    """Formula 2: the gaps between a talent and a job, and how ready the talent is.

    S = sum over gaps of w x (16 (1 - exp(-T / 2.5)) + 3 ln(1 + T)) + 6 (1 - O)      (T in months, O = occupation closeness)
    JRS = 100 exp(-S / 70)        GSI = 100 - JRS        T_total = max(T) + 0.18 x (sum(T) - max(T))
    """
    an = F1.analyse(candidate, job)
    res = gaps_and_strengths(an, explicit_missing_skills)
    cand, jb = an["cand"], an["job"]
    gsi, jrs = round(res["gsi"], 1), round(res["jrs"], 1)
    months = round(res["months"], 1)
    return {
        "candidate_id": cand["id"], "candidate_name": cand["alias"] or cand["id"],
        "job_id": jb["id"], "job_title": jb["title"],
        "total_gaps_count": len(res["gaps"]), "classified_gaps": res["gaps"], "gaps": res["gaps"], "strengths": res["strengths"],
        "gap_severity_index": gsi, "skill_gap_pct": gsi, "job_readiness_score": jrs,
        "estimated_bridge_months": months, "estimated_closing_months": months, "months_to_close": months,
        "has_statutory_blocker": False,
        "readiness_tier": res["tier"], "readiness_tier_code": res["tier_code"],
        "learner_factor": round(res["learner_factor"], 3), "adaptation_friction": round(res["friction"], 2),
    }


# =====================================================================
# 4. THE PATH OBJECT ("Your path to this job")
# =====================================================================

def _axis(key: str, label: str, group: str, required: float, have: float) -> Dict[str, Any]:
    req, hv = round(required, 1), round(have, 1)
    status = "above" if hv >= req + 15.0 else ("fit" if hv >= req else "gap")
    return {"key": key, "label": label, "group": group, "required": req, "have": hv, "status": status}


def path_from_analysis(an: Dict[str, Any], res: Dict[str, Any]) -> Dict[str, Any]:
    """The `path` object of V2_PLAN section 5.3. `res` is the result of gaps_and_strengths."""
    cand, jb = an["cand"], an["job"]
    tax = C.get_taxonomy()
    axes: List[Dict[str, Any]] = []

    # one axis for each skill group that the job asks for. required = weighted mean of need / 5 x 100. have = weighted mean of min(level, 5) / 5 x 100.
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for it in an["items"]:
        groups.setdefault(it["group"], []).append(it)
    order = [g for g in tax.group_order if g in groups] + sorted(g for g in groups if g not in tax.group_order)
    for g in order:
        its = groups[g]
        den = sum(i["weight"] for i in its)
        required = sum(i["weight"] * i["need_level"] / 5.0 * 100.0 for i in its) / den
        have = sum(i["weight"] * min(i["have_level"] or 0.0, 5.0) / 5.0 * 100.0 for i in its) / den
        axes.append(_axis(g, tax.groups.get(g, "Other"), g, required, have))
    if jb["min_years"] is not None:
        axes.append(_axis("experience", "Experience", "experience", min(100.0, 100.0 * jb["min_years"] / 10.0), min(100.0, 100.0 * cand["years"] / 10.0)))
    if cand["level_rank"] is not None and jb["level_rank"] is not None:
        axes.append(_axis("level", "Level", "level", 100.0 * jb["level_rank"] / 5.0, 100.0 * cand["level_rank"] / 5.0))
    if an["cert_items"]:
        den = sum(c["weight"] for c in an["cert_items"])
        have = sum(c["weight"] for c in an["cert_items"] if c["held"]) / den * 100.0
        axes.append(_axis("certifications", "Certifications", "certifications", 100.0, have))

    # the fit list and the gap list
    fit: List[Dict[str, Any]] = []
    for s in sorted([s for s in res["strengths"] if s["kind"] == "skill"], key=lambda s: (-s["credit"], s["item"])):
        note = "Above the level that the job needs." if s["surplus"] >= 1.0 else ""
        fit.append({"kind": "skill", "label": s["item"], "have": level_label(s["have_level"]), "need": level_label(s["need_level"]), "note": note})
    for s in res["strengths"]:
        if s["kind"] == "experience":
            fit.append({"kind": "experience", "label": "Experience", "have": _years_text(s["have_level"]), "need": _years_text(s["need_level"]) + " or more",
                        "note": ""})
        elif s["kind"] == "level":
            fit.append({"kind": "level", "label": "Level", "have": s["have_level"], "need": s["need_level"],
                        "note": "Above the level of the job." if s["surplus"] >= 1.0 else ""})
        elif s["kind"] in ("certification", "award"):
            fit.append({"kind": s["kind"], "label": s["item"], "have": s["have_level"], "need": s["need_level"], "note": ""})
    gaps: List[Dict[str, Any]] = []
    for g in res["gaps"]:
        if g["kind"] in ("missing", "below_level"):
            have = "none" if g["kind"] == "missing" else level_label(g["have_level"])
            need = level_label(g["need_level"])
        elif g["kind"] == "experience":
            have, need = _years_text(g["have_level"]), _years_text(g["need_level"]) + " or more"
        else:
            have, need = str(g["have_level"]), str(g["need_level"])
        gaps.append({"kind": g["kind"], "label": g["item"], "have": have, "need": need, "months": g["months"], "must": bool(g["must"]), "note": g["note"]})
    return {
        "axes": axes, "fit": fit, "gaps": gaps,
        "summary": {"fitCount": len(fit), "gapCount": len(gaps), "monthsToClose": round(res["months"], 1), "readinessTier": res["tier"]},
    }


def evaluate_path(candidate: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    """Returns the `path` object of V2_PLAN section 5.3: axes, fit list, gap list and summary. The platform adds it to the job detail as `bridge.path`."""
    an = F1.analyse(candidate, job)
    return path_from_analysis(an, gaps_and_strengths(an))


# =====================================================================
# 5. SELF-CHECK
# =====================================================================
if __name__ == "__main__":
    print("FORMULA 2 SELF-CHECK")
    cand = {"id": "demo", "level": "Mid", "years_experience": 3, "current_title": "Data Analyst",
            "skills": [{"name": "SQL", "level": 4}, {"name": "Python", "level": 3}], "certifications": []}
    job = {"id": "job-1", "title": "Senior Data Engineer", "category": "Data", "level": "Senior", "min_years": 5, "max_years": 9,
           "required_skills": [{"name": "SQL", "level": 4, "must": True}, {"name": "Python", "level": 4, "must": True},
                               {"name": "Apache Airflow", "level": 3, "must": True}],
           "certifications_required": ["SnowPro Core Certification"]}
    r = evaluate_skill_gaps(cand, job)
    print("readiness", r["job_readiness_score"], "months", r["estimated_bridge_months"], "gaps", [(g["item"], g["months"]) for g in r["gaps"]])
    p = evaluate_path(cand, job)
    print("path", p["summary"], [(a["key"], a["required"], a["have"], a["status"]) for a in p["axes"]])
