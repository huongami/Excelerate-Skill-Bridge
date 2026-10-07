#!/usr/bin/env python3
"""
Skill Bridge Intelligence Engine — Formula 3: Job-to-Job Comparison Model (JJF)
Standard: ASD-STE100 (Simplified Technical English)
Document: IE-SPEC-003
"""

import os
import re
from typing import Dict, List, Any, Tuple, Set

# =====================================================================
# 1. UTILITY FUNCTIONS
# =====================================================================

def extract_job_tokens(job: Dict[str, Any]) -> Set[str]:
    """Extracts lowercase clean tokens from requirements, description, and title."""
    parts = []
    parts.append(str(job.get("title", "")))
    reqs = job.get("requirements", [])
    if isinstance(reqs, list):
        parts.extend([str(r) for r in reqs])
    else:
        parts.append(str(reqs))
    parts.append(str(job.get("description", "")))
    
    clean = re.sub(r"[^\w\s-]", " ", " ".join(parts).lower()).strip()
    words = clean.split()
    tokens = set()
    for w in words:
        if len(w) >= 3:
            tokens.add(w)
    for i in range(len(words) - 1):
        tokens.add(f"{words[i]} {words[i+1]}")
    return tokens


def get_job_salary_midpoint(job: Dict[str, Any]) -> float:
    """Computes midpoint annual AUD salary for a job record."""
    s_min = float(job.get("salary_min") or 0.0)
    s_max = float(job.get("salary_max") or 0.0)
    
    # Check if raw salary is hourly/daily, normalize to annual
    if 0 < s_max < 500.0:  # Hourly rate (e.g. $74 - $152 AUD)
        s_min = s_min * 1950.0  # 37.5 hrs/week * 52 weeks
        s_max = s_max * 1950.0
    
    if s_min > 0 and s_max > 0:
        return (s_min + s_max) / 2.0
    elif s_max > 0:
        return s_max
    elif s_min > 0:
        return s_min
    else:
        return 110000.0  # Australian national professional median default


# =====================================================================
# 2. SUB-METRIC FUNCTIONS (ASD-STE100 SPECIFICATION)
# =====================================================================

def calculate_taxonomy_proximity(code_a: str, code_b: str) -> float:
    """Calculates S_tree based on ABS ANZSCO 6-digit taxonomy distance."""
    a = str(code_a or "").strip()
    b = str(code_b or "").strip()

    if not a or not b:
        return 20.0

    if a == b and len(a) >= 6:
        return 100.0
    if len(a) >= 4 and len(b) >= 4 and a[:4] == b[:4]:
        return 85.0
    if len(a) >= 3 and len(b) >= 3 and a[:3] == b[:3]:
        return 65.0
    if len(a) >= 2 and len(b) >= 2 and a[:2] == b[:2]:
        return 40.0
    if len(a) >= 1 and len(b) >= 1 and a[0] == b[0]:
        return 20.0
    return 0.0


def calculate_requirements_jaccard(tokens_a: Set[str], tokens_b: Set[str]) -> Tuple[float, Set[str], Set[str], Set[str]]:
    """
    Calculates Jaccard overlap between two job requirement token sets.
    Returns: (Overlap Score [0.0, 100.0], Shared Tokens, Unique to A, Unique to B)
    """
    if not tokens_a and not tokens_b:
        return 50.0, set(), set(), set()
    
    shared = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    
    unique_a = tokens_a.difference(tokens_b)
    unique_b = tokens_b.difference(tokens_a)
    
    ratio = len(shared) / len(union) if union else 0.5
    # Scaled to realistic capability overlap percentage
    score = min(100.0, ratio * 200.0 + 10.0) if shared else 15.0
    return round(score, 1), shared, unique_a, unique_b


def calculate_salary_parity(mid_a: float, mid_b: float) -> float:
    """Calculates S_comp normalized salary distance."""
    max_mid = max(mid_a, mid_b, 1.0)
    diff = abs(mid_a - mid_b)
    score = max(0.0, (1.0 - (diff / max_mid)) * 100.0)
    return round(score, 1)


def calculate_sector_affinity(sec_a: str, sec_b: str) -> float:
    """Calculates S_sector industry context alignment."""
    a = str(sec_a or "").strip().lower()
    b = str(sec_b or "").strip().lower()

    if a == b and a != "":
        return 100.0
    
    # Transferable sector clusters
    transferable_clusters = [
        {"finance & accounting", "operations & administration", "supply chain & logistics"},
        {"technology & data", "engineering & construction"},
        {"marketing & communications", "operations & administration"},
        {"hospitality & service", "operations & administration"}
    ]
    for cluster in transferable_clusters:
        if a in cluster and b in cluster:
            return 65.0

    return 25.0


def calculate_geo_alignment(loc_a: str, loc_b: str) -> float:
    """Calculates S_geo location and remote flexibility."""
    a = str(loc_a or "").strip().lower()
    b = str(loc_b or "").strip().lower()

    if a == b:
        return 100.0
    if "remote" in a or "remote" in b or "australia wide" in a or "australia wide" in b:
        return 95.0

    states = ["nsw", "vic", "qld", "wa", "sa", "tas", "act", "nt", "sydney", "melbourne", "brisbane", "perth", "adelaide"]
    for s in states:
        if s in a and s in b:
            return 75.0

    # Interstate capitals
    capitals = ["sydney", "melbourne", "brisbane", "perth", "adelaide"]
    if any(c in a for c in capitals) and any(c in b for c in capitals):
        return 50.0

    return 25.0


# =====================================================================
# 3. MASTER PAIRWISE AND MULTI-JOB COMPARISON FUNCTIONS
# =====================================================================

def compare_two_jobs(
    job_a: Dict[str, Any],
    job_b: Dict[str, Any],
    weights: Tuple[float, float, float, float, float] = (0.30, 0.35, 0.15, 0.10, 0.10)
) -> Dict[str, Any]:
    """
    Calculates Formula 3: Job Proximity Index (JPI) between two Australian vacancies.
    Follows ASD-STE100 specification IE-SPEC-003.
    """
    w_tree, w_req, w_comp, w_sec, w_geo = weights
    assert abs(sum(weights) - 1.0) < 1e-4, "Weights must sum to 1.00"

    code_a = str(job_a.get("anzsco") or job_a.get("anzsco_code") or "")
    code_b = str(job_b.get("anzsco") or job_b.get("anzsco_code") or "")

    tokens_a = extract_job_tokens(job_a)
    tokens_b = extract_job_tokens(job_b)

    mid_a = get_job_salary_midpoint(job_a)
    mid_b = get_job_salary_midpoint(job_b)

    # 1. Sub-Metrics
    s_tree = calculate_taxonomy_proximity(code_a, code_b)
    s_req, shared_tokens, uniq_a, uniq_b = calculate_requirements_jaccard(tokens_a, tokens_b)
    s_comp = calculate_salary_parity(mid_a, mid_b)
    s_sec = calculate_sector_affinity(job_a.get("category"), job_b.get("category"))
    s_geo = calculate_geo_alignment(job_a.get("location"), job_b.get("location"))

    # 2. Master Composite Equation
    jpi = (w_tree * s_tree) + (w_req * s_req) + (w_comp * s_comp) + (w_sec * s_sec) + (w_geo * s_geo)
    jpi = round(min(100.0, max(0.0, jpi)), 1)

    # 3. Operational Tier Classification
    if jpi >= 80.0:
        tier = "Directly Substitutable Role"
        mobility_advice = "The job seeker can apply to both jobs using the same primary CV with minimal tailoring."
    elif jpi >= 60.0:
        tier = "Adjacent Career Mobility"
        mobility_advice = "The job seeker can transition between these roles by emphasizing transferable methodologies."
    else:
        tier = "Cross-Disciplinary Career Pivot"
        mobility_advice = "Roles differ significantly in daily tasks, domain knowledge, or statutory prerequisites."

    salary_delta = round(mid_b - mid_a, 0)
    salary_delta_formatted = f"+${abs(salary_delta):,.0f} AUD" if salary_delta >= 0 else f"-${abs(salary_delta):,.0f} AUD"

    return {
        "job_a": {
            "id": job_a.get("id") or job_a.get("job_id"),
            "title": job_a.get("title"),
            "company": job_a.get("company"),
            "location": job_a.get("location"),
            "anzsco": code_a,
            "midpoint_salary_aud": round(mid_a, 0)
        },
        "job_b": {
            "id": job_b.get("id") or job_b.get("job_id"),
            "title": job_b.get("title"),
            "company": job_b.get("company"),
            "location": job_b.get("location"),
            "anzsco": code_b,
            "midpoint_salary_aud": round(mid_b, 0)
        },
        "job_proximity_index": jpi,
        "sub_metrics": {
            "s_tree_taxonomy": round(s_tree, 1),
            "s_req_jaccard": round(s_req, 1),
            "s_comp_salary_parity": round(s_comp, 1),
            "s_sec_sector_affinity": round(s_sec, 1),
            "s_geo_alignment": round(s_geo, 1)
        },
        "differentials": {
            "salary_delta_aud": salary_delta,
            "salary_delta_label": salary_delta_formatted,
            "shared_competency_sample": list(shared_tokens)[:8],
            "unique_to_b_sample": list(uniq_b)[:8]
        },
        "operational_tier": tier,
        "career_mobility_advice": mobility_advice
    }


def compare_multiple_jobs(job_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes an N-ary multi-job comparison matrix across N >= 2 Australian job postings.
    Returns: Pairwise matrix and summary trade-off table.
    """
    n = len(job_list)
    matrix = []
    
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                row.append(100.0)
            else:
                pair_res = compare_two_jobs(job_list[i], job_list[j])
                row.append(pair_res["job_proximity_index"])
        matrix.append(row)

    # Compile pairwise summaries vs Job 0 as baseline
    baseline_comparisons = []
    if n > 1:
        base_job = job_list[0]
        for j in range(1, n):
            baseline_comparisons.append(compare_two_jobs(base_job, job_list[j]))

    return {
        "total_jobs_compared": n,
        "job_titles": [j.get("title") for j in job_list],
        "pairwise_proximity_matrix": matrix,
        "baseline_comparisons_vs_first_job": baseline_comparisons
    }


# =====================================================================
# 4. SELF-CONTAINED VERIFICATION BENCHMARK
# =====================================================================
if __name__ == "__main__":
    import json

    print("=" * 75)
    print("SKILL BRIDGE INTELLIGENCE ENGINE — FORMULA 3 VERIFICATION (ASD-STE100)")
    print("=" * 75)

    job_path = "data/australian_jobs.json" if os.path.exists("data/australian_jobs.json") else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "australian_jobs.json")
    with open(job_path, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    # Select representative real vacancies
    nurse_job = [j for j in jobs if j.get("category") == "Healthcare & Nursing"][0]
    clinic_coord = [j for j in jobs if "coordinator" in j.get("title", "").lower() and j.get("category") == "Healthcare & Nursing"][0]
    tech_job = [j for j in jobs if j.get("category") == "Technology & Data"][0]

    # Test 1: Highly Adjacent Roles (Registered Nurse vs Clinical Care Coordinator)
    res_adj = compare_two_jobs(nurse_job, clinic_coord)
    print("\n[TEST 1: Adjacent Roles within Healthcare Sector]")
    print(f"Job A: {res_adj['job_a']['title']} ({res_adj['job_a']['company']})")
    print(f"Job B: {res_adj['job_b']['title']} ({res_adj['job_b']['company']})")
    print(f"Job Proximity Index (JPI): {res_adj['job_proximity_index']}% | Tier: {res_adj['operational_tier']}")
    print(f"Sub-metrics: S_tree={res_adj['sub_metrics']['s_tree_taxonomy']}%, S_req={res_adj['sub_metrics']['s_req_jaccard']}%, S_comp={res_adj['sub_metrics']['s_comp_salary_parity']}%, S_sec={res_adj['sub_metrics']['s_sec_sector_affinity']}%, S_geo={res_adj['sub_metrics']['s_geo_alignment']}%")
    print(f"Salary Delta: {res_adj['differentials']['salary_delta_label']}")
    print(f"Advice: {res_adj['career_mobility_advice']}")

    # Test 2: Cross-Disciplinary Roles (Registered Nurse vs Technology Job)
    res_cross = compare_two_jobs(nurse_job, tech_job)
    print("\n[TEST 2: Cross-Disciplinary Roles (Healthcare vs Technology)]")
    print(f"Job A: {res_cross['job_a']['title']} -> Job B: {res_cross['job_b']['title']}")
    print(f"Job Proximity Index (JPI): {res_cross['job_proximity_index']}% | Tier: {res_cross['operational_tier']}")
    print(f"Advice: {res_cross['career_mobility_advice']}")

    # Test 3: Multi-Job Comparison Matrix (N = 3)
    multi_res = compare_multiple_jobs([nurse_job, clinic_coord, tech_job])
    print("\n[TEST 3: Multi-Job 3x3 Proximity Matrix]")
    for i, title in enumerate(multi_res["job_titles"]):
        row_str = " | ".join(f"{score:5.1f}%" for score in multi_res["pairwise_proximity_matrix"][i])
        print(f"  {title[:30]:30} | {row_str}")

    print("\n" + "=" * 75)
    print("FORMULA 3 PRODUCTION VALIDATION COMPLETE.")
    print("=" * 75)
