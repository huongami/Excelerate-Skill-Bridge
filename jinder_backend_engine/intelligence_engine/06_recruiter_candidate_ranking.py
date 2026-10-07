#!/usr/bin/env python3
"""
Jinder Intelligence Engine - Formula 6: Employer Talent Search Ranking Engine (TSR)
Standard: ASD-STE100 (Simplified Technical English)
Document: IE-SPEC-006 (see 06_RECRUITER_CANDIDATE_RANKING.md)

TSS = w_req S_req + w_sen S_sen + w_evid S_evid + w_reg S_reg + w_audit S_audit

This formula runs for the employer. It reads the SHARED profile only:
skills with levels, level, years, roles, certifications, awards, education and the work preferences.
It never reads the CV text, the evidence lines, a name, an email, a country or any other private field.
The platform uses TSS only to put profiles in order. The platform never shows it.
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
F4 = C.load_sibling("f4")

# (requirement fit, seniority fit, evidence rigor, certification readiness, profile completeness). The five weights sum to 1.00.
DEFAULT_WEIGHTS = (0.44, 0.25, 0.18, 0.08, 0.05)
REQ_WEIGHTS = (0.65, 0.22, 0.13)          # S_req = 100 (0.65 skills + 0.22 occupation + 0.13 domain) + bonus
SEN_WEIGHTS = (0.55, 0.45)                # S_sen = 100 (0.55 level fit + 0.45 years fit)
ORDER_WEIGHTS = (0.60, 0.40)              # the order value of the platform: 0.6 coverage + 0.4 TSS
NOT_RELEVANT = 0.55                       # a skill that the job does not ask for counts 0.55 in the evidence


# =====================================================================
# 1. SUB-METRICS
# =====================================================================

def requirement_fit(an: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
    """S_req = 100 (0.65 K + 0.22 O + 0.13 D) + 3 A + 2 P, capped at 100.
    K = min(1, mean credit / 1.05) over all skills that the job lists (a skill above the level gives a little more),
    O = occupation closeness, D = domain fit, A = share of preferred award kinds held, P = share of preferred certifications held."""
    items = an["items"]
    den = sum(i["weight"] for i in items)
    k = min(1.0, (sum(i["weight"] * i["credit"] for i in items) / den) / 1.05) if den > 0 else an["s_direct"] / 100.0
    o = an["occupation"]
    d = an["domain"] if an["domain"] is not None else o
    pref = [c for c in an["cert_items"] if not c["required"]]
    p = (sum(1 for c in pref if c["held"]) / len(pref)) if pref else 0.0
    a = an["award_fit"] if an["award_fit"] is not None else 0.0
    w1, w2, w3 = REQ_WEIGHTS
    value = min(100.0, 100.0 * (w1 * k + w2 * o + w3 * d) + 3.0 * a + 2.0 * p)
    return value, {"skills": k, "occupation": o, "domain": d}


def seniority_fit(an: Dict[str, Any]) -> float:
    """S_sen = 100 (0.55 level fit + 0.45 years fit). The level fit comes from level ranks, the years fit from exact years. Job title words are not used."""
    lv = an["level"] if an["level"] is not None else 0.6
    yr = an["years"] if an["years"] is not None else 0.6
    return 100.0 * (SEN_WEIGHTS[0] * lv + SEN_WEIGHTS[1] * yr)


def evidence_rigor_for_job(an: Dict[str, Any]) -> float:
    """S_evid = 0.50 x 100 (1 - exp(-Q / 4)) + 0.30 x certification strength + 0.20 x award strength.
    Q = sum over all skills of (level / 5)^2 x (0.7 + 0.3 min(1, years with the skill / 4)) x relevance (1.0 if the job asks for the skill
    or a related skill, else 0.55). A certification counts fully if it shows a skill that the job asks for (or the job lists it), else 0.6.
    The CV text length is not used."""
    cand, jb = an["cand"], an["job"]
    tax = C.get_taxonomy()
    wanted = {r["key"] for r in jb["reqs"]}
    related = set()
    for r in jb["reqs"]:
        related.update(C.norm_key(x) for x in tax.related.get(r["name"], ()))
    q = 0.0
    for s in cand["skills"].values():
        rel = 1.0 if (s["key"] in wanted or s["key"] in related) else NOT_RELEVANT
        yrs = s.get("years")
        q += (F1.effective_level(s) / 5.0) ** 2 * (0.7 + 0.3 * min(1.0, (yrs if yrs is not None else 2.0) / 4.0)) * rel
    listed = {c["key"] for c in jb["certs_required"] + jb["certs_preferred"]}
    total = 0.0
    for key, c in cand["certs"].items():
        evid = {C.norm_key(tax.canon_skill_name(e) or e) for e in (c["entry"] or {}).get("evidences") or []}
        rel = 1.0 if (key in listed or evid & wanted) else 0.6
        tier_w = F4.TIER_WEIGHT.get((c["entry"] or {}).get("tier"), 0.7)
        age = (an["ref_year"] - c["year"]) if c.get("year") else 0.0
        total += tier_w * rel * (0.7 + 0.3 * math.exp(-max(0.0, age) / 4.0))
    cert_strength = 100.0 * C.sat(total, 1.8)
    return 0.50 * 100.0 * C.sat(q, 4.0) + 0.30 * cert_strength + 0.20 * F4.award_strength(cand, an["ref_year"])


def certification_readiness(an: Dict[str, Any]) -> float:
    """S_reg: readiness for the certifications that the job lists. A held certification gives credit 1. A missing one gives
    0.30 (required) or 0.25 (preferred) x how well the person holds the skills that it shows.
    Required and preferred listed: 100 (0.8 R + 0.2 P).  Only required: 100 R.  Only preferred: 100 (0.7 + 0.3 P).
    No certification listed: 90 + 0.10 x the certification strength of the profile. There is no legal block."""
    req = [c["credit"] for c in an["cert_items"] if c["required"]]
    pref = [c["credit"] for c in an["cert_items"] if not c["required"]]
    r = sum(req) / len(req) if req else None
    p = sum(pref) / len(pref) if pref else None
    if r is not None and p is not None:
        return 100.0 * (0.8 * r + 0.2 * p)
    if r is not None:
        return 100.0 * r
    if p is not None:
        return 100.0 * (0.7 + 0.3 * p)
    return 90.0 + 0.10 * F4.certification_strength(an["cand"], an["ref_year"])


def profile_completeness(cand: Dict[str, Any]) -> float:
    """S_audit, 0 to 100: the share of the profile fields that are filled (level, exact years, skill levels, certifications, awards,
    education, domain, target role, current role, place). It checks the data contract of the shared profile. It does not read any text."""
    skills = list(cand["skills"].values())
    given = (sum(1 for s in skills if s["level_given"]) / len(skills)) if skills else 0.0
    checks = [(1.0, 1.0 if cand["level_known"] and not cand["level_estimated"] else 0.0), (1.0, 1.0 if cand["years_known"] else 0.0),
              (1.5, C.sat(len(skills), 6.0)), (1.0, given), (0.5, 1.0 if cand["certs"] else 0.0), (0.5, 1.0 if cand["awards"] else 0.0),
              (0.5, 1.0 if cand["education_rank"] is not None else 0.0), (0.5, 1.0 if cand["domain_declared"] else 0.0),
              (0.5, 1.0 if cand["target_roles"] or cand["target_code"] else 0.0), (0.5, 1.0 if cand["title"] else 0.0),
              (0.5, 1.0 if cand["cities"] else 0.0)]
    return 100.0 * sum(w * v for w, v in checks) / sum(w for w, _ in checks)


# =====================================================================
# 2. THE TALENT SEARCH SCORE
# =====================================================================

def compute_talent_search_score(candidate: Dict[str, Any], job: Dict[str, Any],
                                weights: Tuple[float, float, float, float, float] = DEFAULT_WEIGHTS) -> Dict[str, Any]:
    """Formula 6: the Talent Search Score (TSS) of a shared profile for a job, from 0 to 100. It is used for the order only.

    TSS = 0.44 S_req + 0.25 S_sen + 0.18 S_evid + 0.08 S_reg + 0.05 S_audit
    """
    assert abs(sum(weights) - 1.0) < 1e-4, "Weights must sum to 1.00"
    w_req, w_sen, w_evid, w_reg, w_audit = weights
    an = F1.analyse(candidate, job, shared_only=True)
    cand, jb = an["cand"], an["job"]
    s_req, req_parts = requirement_fit(an)
    s_sen = seniority_fit(an)
    s_evid = evidence_rigor_for_job(an)
    s_reg = certification_readiness(an)
    s_audit = profile_completeness(cand)
    tss = max(0.0, min(100.0, w_req * s_req + w_sen * s_sen + w_evid * s_evid + w_reg * s_reg + w_audit * s_audit))
    coverage = an["coverage"] if an["coverage"] is not None else an["s_direct"]
    missing = [c["name"] for c in an["cert_items"] if c["required"] and not c["held"]]
    role = (cand["target_roles"] or [None])[0] or jb.get("anzsco_title") or cand["title"]
    return {
        "candidate_id": cand["id"], "candidate_name": cand["alias"] or cand["id"], "target_role": role,
        "talent_search_score": round(tss, 1), "overall_score": round(tss, 1), "tss_exact": tss,
        "sub_metrics": {
            "s_req_fit": round(s_req, 1), "s_sen_parity": round(s_sen, 1), "s_evid_rigor": round(s_evid, 1),
            "s_reg_readiness": round(s_reg, 1), "s_audit_contract": round(s_audit, 1),
            "s_level_fit": C.r1(None if an["level"] is None else 100.0 * an["level"]), "s_years_fit": C.r1(None if an["years"] is None else 100.0 * an["years"]),
            "s_skill_credit": round(100.0 * req_parts["skills"], 1),
        },
        "skill_coverage": C.r1(coverage), "skill_breakdown": an["items"],
        "order_value": ORDER_WEIGHTS[0] * coverage + ORDER_WEIGHTS[1] * tss,
        "target_years_demanded": jb["min_years"], "candidate_years_held": round(cand["years"], 1),
        "statutory_note": ("Missing required certification: " + ", ".join(missing)) if missing else "Ready",
    }


def rank_candidates_for_job_requisition(job: Dict[str, Any], all_candidates: List[Dict[str, Any]], top_limit: int = 20) -> Dict[str, Any]:
    """The pool of shared profiles in order of TSS for one job (ties: candidate id)."""
    scored = [compute_talent_search_score(c, job) for c in all_candidates]
    scored.sort(key=lambda x: (-x["tss_exact"], str(x["candidate_id"])))
    for i, item in enumerate(scored):
        item["shortlist_rank"] = i + 1
    jb = C.prepare_job(job)
    return {"job_id": jb["id"], "job_title": jb["title"], "job_company": jb["company"], "job_sector": jb["category"] or jb["domain"],
            "total_pool_evaluated": len(all_candidates), "total_shortlist_output": min(top_limit, len(scored)), "ranked_shortlist": scored[:top_limit]}


# =====================================================================
# 3. SELF-CHECK
# =====================================================================
if __name__ == "__main__":
    print("FORMULA 6 SELF-CHECK")
    job = {"id": "j1", "title": "Senior Data Engineer", "category": "Data", "level": "Senior", "min_years": 5, "max_years": 9,
           "required_skills": [{"name": "SQL", "level": 4, "must": True}, {"name": "Apache Spark", "level": 4, "must": True}],
           "certifications_required": ["Databricks Certified Data Engineer Professional"]}
    pool = [{"id": "a", "alias": "Talent A", "level": "Senior", "years_experience": 8, "skills": [{"name": "SQL", "level": 5}, {"name": "Apache Spark", "level": 4}],
             "certifications": [{"name": "Databricks Certified Data Engineer Professional", "year": 2025}]},
            {"id": "b", "alias": "Talent B", "level": "Mid", "years_experience": 3, "skills": [{"name": "SQL", "level": 3}]}]
    for r in rank_candidates_for_job_requisition(job, pool)["ranked_shortlist"]:
        print(r["shortlist_rank"], r["candidate_name"], r["talent_search_score"], r["sub_metrics"])
