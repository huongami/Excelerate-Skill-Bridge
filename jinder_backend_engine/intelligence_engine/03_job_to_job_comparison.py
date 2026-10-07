#!/usr/bin/env python3
"""
Jinder Intelligence Engine - Formula 3: Job-to-Job Comparison Model (JJF)
Standard: ASD-STE100 (Simplified Technical English)
Document: IE-SPEC-003 (see 03_JOB_TO_JOB_COMPARISON.md)

Public functions: compare_two_jobs, compare_multiple_jobs, get_job_salary_midpoint (the old names stay).
The index JPI is symmetric: JPI(A, B) = JPI(B, A).
"""

import importlib.util
import math
import os
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple


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

# (tree, requirements, compensation, sector, place and work mode, level). The six weights sum to 1.00.
DEFAULT_WEIGHTS = (0.20, 0.34, 0.12, 0.08, 0.14, 0.12)
MODE_PROXIMITY = {
    frozenset(["Remote"]): 1.0, frozenset(["Hybrid"]): 1.0, frozenset(["Onsite"]): 1.0,
    frozenset(["Hybrid", "Remote"]): 0.70, frozenset(["Hybrid", "Onsite"]): 0.75, frozenset(["Onsite", "Remote"]): 0.40,
}
RELATED_PAIR_CREDIT = 0.40          # two different but related skills count as 0.4 of a shared skill


# =====================================================================
# 1. UTILITY FUNCTIONS
# =====================================================================

def extract_job_tokens(job: Dict[str, Any]) -> Set[str]:
    """Lower-case words and two-word pairs from the title, the requirements and the description (old helper, used when a job lists no skills)."""
    parts = [str(job.get("title", ""))]
    reqs = job.get("requirements", [])
    if isinstance(reqs, list):
        parts.extend(str(r.get("name", "")) if isinstance(r, dict) else str(r) for r in reqs)
    else:
        parts.append(str(reqs))
    parts.append(str(job.get("description", "")))
    words = re.sub(r"[^\w\s-]", " ", " ".join(parts).lower()).split()
    tokens = {w for w in words if len(w) >= 3}
    tokens.update(f"{words[i]} {words[i + 1]}" for i in range(len(words) - 1))
    return tokens


# The one function that changes a pay to a yearly pay: annual_salary(min, max, unit) -> (yearly min, yearly max).
# unit "year": no change. unit "day": x 220 working days. unit "hour": x 1950 hours. The bridge can call it. Formulas 3 and 5 use it.
annual_salary = C.annual_salary


def get_job_salary_midpoint(job: Dict[str, Any]) -> float:
    """The middle of the yearly salary range (AUD). The pay is changed to a yearly pay with annual_salary (day x 220, hour x 1950).
    With no salary, it gives the benchmark of the domain and the level of the job, else 110000."""
    jb = C.prepare_job(job)
    if jb["salary_mid"]:
        return float(jb["salary_mid"])
    if jb["domain"] or jb["level_rank"] is not None:
        return C.salary_benchmark(jb["domain"], jb["level_rank"])
    return 110000.0


# =====================================================================
# 2. SUB-METRIC FUNCTIONS (each one from 0 to 100)
# =====================================================================

def calculate_taxonomy_proximity(code_a: str, code_b: str) -> float:
    """Occupation code closeness only: 100 x exp(-0.26 (6 - c)^1.3). Unknown codes give 20.0."""
    v = F1.code_closeness(code_a, code_b)
    return round(100.0 * v, 1) if v is not None else 20.0


def calculate_requirements_jaccard(tokens_a: Set[str], tokens_b: Set[str]) -> Tuple[float, Set[str], Set[str], Set[str]]:
    """Token overlap of two jobs (used only when a job lists no skills): 100 x min(1, 2.2 x Jaccard). Returns (score, shared, only A, only B)."""
    if not tokens_a and not tokens_b:
        return 50.0, set(), set(), set()
    shared = tokens_a & tokens_b
    union = tokens_a | tokens_b
    ratio = len(shared) / len(union) if union else 0.5
    return round(100.0 * min(1.0, 2.2 * ratio), 1), shared, tokens_a - tokens_b, tokens_b - tokens_a


def calculate_salary_parity(mid_a: float, mid_b: float) -> float:
    """S_comp = 100 x exp(-|ln(Ma / Mb)| / 0.5). It is symmetric and it is 100 for equal pay."""
    a, b = max(1.0, float(mid_a)), max(1.0, float(mid_b))
    return round(100.0 * math.exp(-abs(math.log(a / b)) / 0.5), 1)


def calculate_sector_affinity(sec_a: str, sec_b: str) -> float:
    """Domain closeness from the two names only: 100 for the same domain. Two different known domains: 40 to 62. Else 25."""
    a, b = C.norm_key(sec_a), C.norm_key(sec_b)
    if a and a == b:
        return 100.0
    pairs = {frozenset(["software engineering", "ai & machine learning"]): 55.0, frozenset(["software engineering", "data"]): 45.0,
             frozenset(["ai & machine learning", "data"]): 62.0}
    return pairs.get(frozenset([a, b]), 25.0)


def calculate_geo_alignment(loc_a: str, loc_b: str, mode_a: Optional[str] = None, mode_b: Optional[str] = None) -> float:
    """Place and work-mode closeness, 0 to 100, from two location texts (and the work modes if known).
    Closeness = mode closeness x city closeness. City closeness = 1 if a job is Remote, else 0.25 + 0.75 exp(-d / 700) (0.6 if a city is not known)."""
    ma = mode_a or C.canon_mode(loc_a) or "Onsite"
    mb = mode_b or C.canon_mode(loc_b) or "Onsite"
    if ma == "Remote" or mb == "Remote":
        city = 1.0
    else:
        ca, cb = C.canon_city(loc_a), C.canon_city(loc_b)
        d = C.distance_km(ca, cb) if (ca and cb) else None
        city = (0.25 + 0.75 * math.exp(-d / 700.0)) if d is not None else (1.0 if C.norm_key(loc_a) == C.norm_key(loc_b) and loc_a else 0.6)
    return round(100.0 * MODE_PROXIMITY.get(frozenset([ma, mb]), 0.5) * city, 1)


def _skill_weights(jb: Dict[str, Any]) -> Dict[str, float]:
    """key -> need level x (1.0 for a must skill, 0.6 for another) x rarity^0.3."""
    return {r["key"]: float(r["need"]) * (1.0 if r.get("must", True) else 0.6) * max(1.0, r["rarity"]) ** 0.3 for r in jb["reqs"]}


def skill_overlap(jb_a: Dict[str, Any], jb_b: Dict[str, Any]) -> Tuple[Optional[float], List[str], List[str], List[str]]:
    """Level-weighted overlap of the skills of two jobs: sum(min) / sum(max) over the skills (a weighted Jaccard).
    A pair of related skills (one only in A, one only in B) counts as 0.4 of a shared skill. Returns (0 to 100 or None, shared, only A, only B)."""
    wa, wb = _skill_weights(jb_a), _skill_weights(jb_b)
    if not wa or not wb:
        return None, [], [], []
    names = {r["key"]: r["name"] for r in jb_a["reqs"] + jb_b["reqs"]}
    shared = [k for k in wa if k in wb]
    only_a = {k for k in wa if k not in wb}
    only_b = {k for k in wb if k not in wa}
    tax = C.get_taxonomy()
    num = sum(min(wa[k], wb[k]) for k in shared)
    den = sum(max(wa[k], wb[k]) for k in shared)
    pairs = []
    for ka in only_a:
        rel = tax.related.get(names[ka]) or set()
        for kb in only_b:
            if names[kb] in rel:
                pairs.append((-min(wa[ka], wb[kb]), tuple(sorted((ka, kb))), ka, kb))
    pairs.sort()
    used_a: Set[str] = set()
    used_b: Set[str] = set()
    for _neg, _key, ka, kb in pairs:
        if ka in used_a or kb in used_b:
            continue
        used_a.add(ka)
        used_b.add(kb)
        num += RELATED_PAIR_CREDIT * min(wa[ka], wb[kb])
        den += max(wa[ka], wb[kb])
    den += sum(wa[k] for k in only_a if k not in used_a) + sum(wb[k] for k in only_b if k not in used_b)
    score = 100.0 * num / den if den > 0 else 0.0
    shared_sorted = sorted(shared, key=lambda k: (-min(wa[k], wb[k]), k))
    return score, [names[k] for k in shared_sorted], \
        [names[k] for k in sorted(only_a, key=lambda k: (-wa[k], k))], [names[k] for k in sorted(only_b, key=lambda k: (-wb[k], k))]


def _domain_vector(jb: Dict[str, Any]) -> Dict[str, float]:
    vec: Dict[str, float] = {}
    for r in jb["reqs"]:
        doms = r.get("domains") or []
        for d in doms:
            vec[d] = vec.get(d, 0.0) + float(r["need"]) / len(doms)
    return vec


def sector_closeness(jb_a: Dict[str, Any], jb_b: Dict[str, Any]) -> float:
    """Domain closeness, 0 to 100: 50 x (same domain) + 50 x cosine of the domain shares of the two skill lists. Without skills: 100 or 25."""
    same = 1.0 if jb_a["domain"] and C.norm_key(jb_a["domain"]) == C.norm_key(jb_b["domain"]) else 0.0
    va, vb = _domain_vector(jb_a), _domain_vector(jb_b)
    if not va or not vb:
        return calculate_sector_affinity(jb_a["domain"], jb_b["domain"])
    dot = sum(va.get(k, 0.0) * vb.get(k, 0.0) for k in set(va) | set(vb))
    norm = math.sqrt(sum(x * x for x in va.values())) * math.sqrt(sum(x * x for x in vb.values()))
    return 100.0 * (0.5 * same + 0.5 * (dot / norm if norm > 0 else 0.0))


def tree_closeness(jb_a: Dict[str, Any], jb_b: Dict[str, Any]) -> float:
    """Occupation closeness of two jobs, 0 to 100: the mean of the two directions of the closeness of Formula 1 (so it is symmetric)."""
    tax = C.get_taxonomy()
    out = []
    for x, y in ((jb_a, jb_b), (jb_b, jb_a)):
        anchor = {"digits": x["code"], "occ": x["occ"], "tokens": x["tokens"]}
        value, _parts = F1._anchor_closeness(anchor, {"specialisation": x["specialisation"], "domain": x["domain"]}, y)
        out.append(value)
    return 100.0 * sum(out) / 2.0


def level_proximity(rank_a: Optional[float], rank_b: Optional[float]) -> Optional[float]:
    """Level closeness, 0 to 100: 100 x exp(-0.45 |difference|^1.2). None if a level is not known."""
    if rank_a is None or rank_b is None:
        return None
    return 100.0 * math.exp(-0.45 * abs(rank_a - rank_b) ** 1.2)


# =====================================================================
# 3. THE COMPARISON FUNCTIONS
# =====================================================================

def _job_card(job: Dict[str, Any], jb: Dict[str, Any], mid: float) -> Dict[str, Any]:
    return {"id": job.get("id") or job.get("job_id"), "title": job.get("title"), "company": job.get("company"), "location": job.get("location"),
            "anzsco": jb["code"], "midpoint_salary_aud": round(mid, 0), "level": C.get_taxonomy().level_name(jb["level_rank"]) or None,
            "work_mode": jb["mode"]}


def compare_two_jobs(job_a: Dict[str, Any], job_b: Dict[str, Any], weights: Tuple[float, ...] = DEFAULT_WEIGHTS) -> Dict[str, Any]:
    """Formula 3: the Job Proximity Index (JPI) of two jobs, from 0 to 100.

    JPI = sum(w_k S_k) / sum(w_k) over the parts that apply: S_tree, S_req, S_comp, S_sec, S_geo, S_level.
    An old 5-value weight tuple (tree, req, comp, sec, geo) still works: the level part then has no weight.
    """
    if len(weights) == 5:
        weights = tuple(weights) + (0.0,)
    assert len(weights) == 6 and abs(sum(weights) - 1.0) < 1e-4, "Weights must sum to 1.00"
    w_tree, w_req, w_comp, w_sec, w_geo, w_lvl = weights
    a, b = C.prepare_job(job_a), C.prepare_job(job_b)
    mid_a, mid_b = get_job_salary_midpoint(job_a), get_job_salary_midpoint(job_b)

    s_tree = tree_closeness(a, b)
    overlap, shared, only_a, only_b = skill_overlap(a, b)
    if overlap is None:        # no skill list: use the words of the title and the description
        s_req, shared_tokens, uniq_a, uniq_b = calculate_requirements_jaccard(extract_job_tokens(job_a), extract_job_tokens(job_b))
        shared, only_a, only_b = sorted(shared_tokens)[:8], sorted(uniq_a)[:8], sorted(uniq_b)[:8]
    else:
        s_req = overlap
    s_comp = calculate_salary_parity(mid_a, mid_b)
    s_sec = sector_closeness(a, b)
    s_geo = calculate_geo_alignment(a["location_text"] or a["raw_location"], b["location_text"] or b["raw_location"], a["mode"], b["mode"])
    s_lvl = level_proximity(a["level_rank"], b["level_rank"])

    parts = [(w_tree, s_tree), (w_req, s_req), (w_comp, s_comp), (w_sec, s_sec), (w_geo, s_geo)]
    if s_lvl is not None:
        parts.append((w_lvl, s_lvl))
    den = sum(w for w, _ in parts)
    jpi = round(max(0.0, min(100.0, sum(w * s for w, s in parts) / den)), 1) if den > 0 else 0.0

    if jpi >= 80.0:
        tier, advice = "Directly Substitutable Role", "You can apply to both jobs with the same main CV and only small changes."
    elif jpi >= 60.0:
        tier, advice = "Adjacent Career Mobility", "You can move between these roles if you show your transferable skills and ways of working."
    else:
        tier, advice = "Cross-Disciplinary Career Pivot", "The roles differ a lot in daily tasks, domain knowledge or required level."

    salary_delta = round(mid_b - mid_a, 0)
    label = f"+${abs(salary_delta):,.0f} AUD" if salary_delta >= 0 else f"-${abs(salary_delta):,.0f} AUD"
    level_delta = None if a["level_rank"] is None or b["level_rank"] is None else round(b["level_rank"] - a["level_rank"], 2)
    return {
        "job_a": _job_card(job_a, a, mid_a), "job_b": _job_card(job_b, b, mid_b),
        "job_proximity_index": jpi,
        "sub_metrics": {
            "s_tree_taxonomy": round(s_tree, 1), "s_req_jaccard": round(s_req, 1), "s_comp_salary_parity": round(s_comp, 1),
            "s_sec_sector_affinity": round(s_sec, 1), "s_geo_alignment": round(s_geo, 1), "s_level_proximity": C.r1(s_lvl),
        },
        "differentials": {
            "salary_delta_aud": salary_delta, "salary_delta_label": label, "level_delta": level_delta,
            "shared_competency_sample": list(shared)[:8], "unique_to_a_sample": list(only_a)[:8], "unique_to_b_sample": list(only_b)[:8],
        },
        "operational_tier": tier, "career_mobility_advice": advice,
    }


def compare_multiple_jobs(job_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """The N x N matrix of JPI for N >= 2 jobs, and the comparison of each job with the first one."""
    n = len(job_list)
    matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            row.append(100.0 if i == j else compare_two_jobs(job_list[i], job_list[j])["job_proximity_index"])
        matrix.append(row)
    baseline = [compare_two_jobs(job_list[0], job_list[j]) for j in range(1, n)] if n > 1 else []
    return {"total_jobs_compared": n, "job_titles": [j.get("title") for j in job_list], "pairwise_proximity_matrix": matrix,
            "baseline_comparisons_vs_first_job": baseline}


# =====================================================================
# 4. SELF-CHECK
# =====================================================================
if __name__ == "__main__":
    print("FORMULA 3 SELF-CHECK")
    a = {"id": "a", "title": "Senior Data Engineer", "category": "Data", "level": "Senior", "city": "Sydney", "work_mode": "Hybrid", "salary_min": 150000,
         "salary_max": 180000, "required_skills": [{"name": "SQL", "level": 4, "must": True}, {"name": "Apache Spark", "level": 4, "must": True}]}
    b = {"id": "b", "title": "Data Engineer", "category": "Data", "level": "Mid", "city": "Melbourne", "work_mode": "Remote", "salary_min": 120000,
         "salary_max": 140000, "required_skills": [{"name": "SQL", "level": 3, "must": True}, {"name": "Apache Airflow", "level": 3, "must": True}]}
    r1, r2 = compare_two_jobs(a, b), compare_two_jobs(b, a)
    print("JPI", r1["job_proximity_index"], r2["job_proximity_index"], r1["sub_metrics"])
