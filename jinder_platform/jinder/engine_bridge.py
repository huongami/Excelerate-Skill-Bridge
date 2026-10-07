"""The bridge between the platform and the six formulas in `jinder_backend_engine/intelligence_engine`.

The formulas are not changed here. This module only:
  * loads them from the engine folder,
  * builds the dictionaries that they expect (a talent and a job),
  * calls them, and cuts their output down to what the API may show.

All score math is in the engine files. See docs/changes/Formulas.md for the inputs and the results.

Privacy rules (AI_Rule Rules 5 and 9):
  * A talent dictionary never has a name, an email, a country of origin or a visa status.
  * For an employer (Formulas 4 and 6) the dictionary is built from the SHARED profile only (`shared_candidate_dict`): accepted skills with
    their levels, the level, the years, certifications, awards, roles and wishes. It never has the CV text or the evidence lines.
  * A score on a person is used only to put profiles in order. The API never sends it to an employer.
"""
import importlib.util
import logging
import threading
from typing import Any, Dict, List, Optional

from . import config, store, taxonomy
from .translation import aqf_level, aqf_of
from .util import as_list, norm

log = logging.getLogger("jinder.engine")

_T = taxonomy.get()

_FILES = {
    "f1": "01_skill_matching_model.py",
    "f2": "02_skill_gap_analysis.py",
    "f3": "03_job_to_job_comparison.py",
    "f4": "04_candidate_benchmarking.py",
    "f5": "05_job_seeker_ranking_feed.py",
    "f6": "06_recruiter_candidate_ranking.py",
}
_modules: Dict[str, Any] = {}
_load_lock = threading.Lock()


def _load(key: str):
    """Load a formula file by path. The files load `engine_common.py` and each other by path, so they must stay in one folder."""
    with _load_lock:
        if key in _modules:
            return _modules[key]
        path = config.ENGINE_DIR / _FILES[key]
        if not path.is_file():
            raise FileNotFoundError(f"Formula file not found: {path}")
        spec = importlib.util.spec_from_file_location(f"jinder_formula_{key}", str(path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # the engine files only run their tests under `if __name__ == "__main__"`
        _modules[key] = module
        return module


def engine_status() -> Dict[str, bool]:
    """Which formula files can be loaded. Used by the health check."""
    status = {}
    for key in _FILES:
        try:
            _load(key)
            status[key] = True
        except Exception:  # noqa: BLE001 - report every problem as "not loaded"
            status[key] = False
    return status


# =====================================================================
# Dictionaries for the formulas
# =====================================================================
# The words that a formula reads for the highest qualification. The platform keeps the AQF label for a qualification.
_EDUCATION_TEXT = {10: "Doctorate (PhD)", 9: "Master's degree", 8: "Graduate diploma", 7: "Bachelor's degree", 6: "Advanced diploma", 5: "Diploma",
                   3: "Certificate III or IV"}


def highest_education(qualifications: List[str]) -> str:
    """The highest qualification as words that the formulas understand ("Master's degree"). The input is raw qualifications or AQF labels."""
    best_rank, best = 0, ""
    for q in qualifications:
        rank = aqf_level(str(q)) or aqf_level(aqf_of(q))
        if rank > best_rank:
            best_rank, best = rank, _EDUCATION_TEXT.get(rank, str(q))
    return best or (str(qualifications[0]) if qualifications else "")


def _kind_of(name: str) -> str:
    return "Transferable" if _T.kind_of(name) in ("method", "soft") else "Direct"


def _skill_item(name: str, level: Any, years: Any = None) -> Dict[str, Any]:
    item = {"skill_name": name, "name": name, "skill_type": _kind_of(name), "level": level}
    if years is not None:
        item["years"] = years
    return item


def _years_value(exact: Any, band: Any) -> Optional[float]:
    """The years of experience: the exact number if the talent gave it, else the middle of the band. None if neither is there."""
    from .reference import YEARS_MIDPOINT
    if exact is not None:
        return float(exact)
    return YEARS_MIDPOINT.get(band or "")


def _common(c: Dict[str, Any], *, level, years, domain, specialisation, target_roles, qualifications, fields, locations, modes, types) -> Dict[str, Any]:
    """The keys that both talent dictionaries have."""
    if level:
        c["level"] = level
    if years is not None:
        c["years_experience"] = years
    if domain:
        c["domain"] = domain
    if specialisation:
        c["specialisation"] = specialisation
    roles = [str(r) for r in as_list(target_roles) if r]
    c["target_roles"] = roles
    first = _T.occupation_of_role(roles[0]) if roles else None
    if first:
        c["target_anzsco_code"] = str(first["code"])
    c["highest_education"] = highest_education(qualifications)
    c["field_of_study"] = [str(f) for f in as_list(fields)]
    locs = [str(x) for x in as_list(locations) if x]
    c["locations"] = locs
    if locs:
        c["preferred_location"] = locs[0]
    c["work_modes"] = [str(x) for x in as_list(modes)]
    c["work_types"] = [str(x) for x in as_list(types)]
    return c


def candidate_dict(profile: Dict[str, Any], shared: List[Dict[str, Any]], alias: str, user_id: str, index: Any = None, private: bool = True) -> Dict[str, Any]:
    """The dictionary that the formulas read for one talent.

    private=True  -> for the talent's own screens: the whole profile. Skills that the talent did not remove count (also the ones that are not
                     accepted yet), and the typed skills that have no card. The CV evidence lines are the fallback text.
    private=False -> for an employer: ONLY the shared profile (AI_Rule Rule 5, item 9). The argument `shared` (accepted rows) is used.
    `index` is not used any more (the formulas find the occupation themselves). It stays so that old calls work.
    """
    profile = profile or {}
    if not private:
        return shared_candidate_dict(store.shared_profile(alias, {**profile, "translation": shared}), user_id)
    rows = [s for s in as_list(profile.get("translation")) if isinstance(s, dict)]
    skills, seen = [], set()
    for s in rows:
        if s.get("source") != "skill" or s.get("status") == "removed" or not s.get("mapped"):
            continue
        key = norm(s["mapped"])
        if key in seen:
            continue
        seen.add(key)
        skills.append(_skill_item(s["mapped"], store.effective_level(s), s.get("years")))
    removed = {norm(s.get("mapped")) for s in rows if s.get("status") == "removed"}
    from .skills import canonical_skill_name
    for typed in as_list(profile.get("skills")):
        name = canonical_skill_name(typed) or str(typed).strip()
        if name and norm(name) not in seen and norm(name) not in removed:
            seen.add(norm(name))
            skills.append(_skill_item(name, store.DEFAULT_SKILL_LEVEL))
    roles = [str(r) for r in as_list(profile.get("currentRole")) if r]
    c: Dict[str, Any] = {
        "id": user_id, "alias": alias, "skills": skills, "current_title": roles[0] if roles else "",
        "certifications": [dict(x) for x in as_list(profile.get("certifications"))],
        "awards": [dict(x) for x in as_list(profile.get("awards"))],
    }
    industries = as_list(profile.get("industry"))
    _common(c, level=profile.get("level"), years=_years_value(profile.get("yearsExperience"), profile.get("years")),
            domain=industries[0] if industries else "", specialisation=profile.get("specialisation"), target_roles=profile.get("targetRole"),
            qualifications=[str(q) for q in as_list(profile.get("qualification"))], fields=profile.get("fieldOfStudy"),
            locations=profile.get("locations"), modes=profile.get("workModes"), types=profile.get("workTypes"))
    if not skills:
        # The text is only a fallback for the talent's own screens, and only when there is no skill at all
        c["cv_raw_text"] = " ".join([str(e) for e in as_list(profile.get("evidence"))] + roles)
    return c


def shared_candidate_dict(shared: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """The dictionary for an employer, built from the shared profile (`store.shared_profile`) and nothing else.

    It has no name, email, country, CV text, evidence line or private key. The years are the shared years (rounded to 0.5).
    """
    levels = {x["name"]: x for x in as_list(shared.get("skillLevels"))}
    skills = [_skill_item(name, (levels.get(name) or {}).get("level", store.DEFAULT_SKILL_LEVEL), (levels.get(name) or {}).get("years"))
              for name in as_list(shared.get("skills"))]
    roles = [r.get("title") for r in as_list(shared.get("roles")) if r.get("title")]
    c: Dict[str, Any] = {
        "id": user_id, "alias": shared.get("alias"), "skills": skills, "current_title": roles[0] if roles else "",
        "certifications": [dict(x) for x in as_list(shared.get("certifications"))],
        "awards": [dict(x) for x in as_list(shared.get("awards"))],
    }
    industries = as_list(shared.get("industries"))
    return _common(c, level=shared.get("level"), years=_years_value(shared.get("yearsExperience"), shared.get("years")),
                   domain=industries[0] if industries else "", specialisation=shared.get("specialisation"), target_roles=shared.get("targetRoles"),
                   qualifications=[str(q) for q in as_list(shared.get("qualifications"))], fields=shared.get("fieldsOfStudy"),
                   locations=shared.get("locations"), modes=shared.get("workModes"), types=shared.get("workTypes"))


def job_dict(job: Dict[str, Any]) -> Dict[str, Any]:
    """The dictionary that the formulas read for one job. Only job facts: nothing about a person.

    The pay is sent as it is stored, with its unit (`salary_unit`: year, day or hour). The engine changes it to a yearly pay in ONE place
    (`03_job_to_job_comparison.annual_salary`). Never change it here.
    """
    from .catalogue import requirements_of
    from .util import parse_iso, utcnow
    posted = parse_iso(job.get("postedAt"))
    days_old = max(0.5, (utcnow() - posted).total_seconds() / 86400.0) if posted else 3.0
    reqs = requirements_of(job)
    certs = job.get("certifications") or {}
    out = {
        "id": job["id"], "job_id": job["id"],
        "title": job.get("title", ""), "company": job.get("company", ""),
        "category": job.get("category", ""),
        "location": f"{job.get('location', '')} {job.get('area', '')}".strip(),
        "city": job.get("location", ""),
        "anzsco_code": job.get("anzsco", ""), "anzsco": job.get("anzsco", ""), "anzsco_title": job.get("occupation", ""),
        "salary_min": job.get("salaryMin") or 0.0, "salary_max": job.get("salaryMax") or 0.0, "salary_unit": job.get("salaryUnit") or "year",
        "type": job.get("type", ""),
        "required_skills": [{"name": r["name"], "level": r["level"], "must": r["must"]} for r in reqs],
        "requirements": [r["name"] for r in reqs],
        "description": job.get("description", ""),
        # "days_old" is used instead of "posted_at". The formula has a fixed date inside for its own tests.
        "days_old": days_old,
    }
    # The facts of version 2. A key is added only when the job has a value, so that a job without the fact is read with the safe defaults.
    extra = {
        "level": job.get("level"), "specialisation": job.get("specialisation"), "min_years": job.get("minYears"),
        "max_years": job.get("maxYears"), "work_mode": job.get("workMode"), "education_min": job.get("educationMin"),
        "certifications_required": certs.get("required") or None, "certifications_preferred": certs.get("preferred") or None,
        "awards_preferred": (job.get("awards") or {}).get("preferred") or None,
    }
    out.update({k: v for k, v in extra.items() if v is not None})
    return out


# =====================================================================
# Formula calls
# =====================================================================
def prepare_candidate(cand: Dict[str, Any], shared_only: bool = False) -> Dict[str, Any]:
    """The talent dictionary after the cleaning of the engine. A prepared dictionary can be sent to any formula again (it is faster)."""
    return _load("f1").C.prepare_candidate(cand, shared_only=shared_only)


def prepare_job(job: Dict[str, Any]) -> Dict[str, Any]:
    return _load("f1").C.prepare_job(job)


def job_fit(candidate: Dict[str, Any], job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Formula 1: the product fit (0 to 100, one decimal), its parts and the skill breakdown. None if the formula fails."""
    try:
        return _load("f1").evaluate_job_fit(candidate, job)
    except Exception:  # noqa: BLE001
        log.exception("Formula 1 (fit) failed")
        return None


def smf(candidate: Dict[str, Any], job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Formula 1 (SMF): how close the talent is to the occupation of the job, with the sub-metrics of the 8 axes."""
    try:
        return _load("f1").evaluate_skill_match(candidate, job)
    except Exception:  # noqa: BLE001
        log.exception("Formula 1 failed")
        return None


def gap_analysis(candidate: Dict[str, Any], job: Dict[str, Any], missing_skills: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """Formula 2 (GSI and JRS): the gaps of the talent, how severe they are, and how many months it takes to close them."""
    try:
        return _load("f2").evaluate_skill_gaps(candidate, job, explicit_missing_skills=list(missing_skills or []))
    except Exception:  # noqa: BLE001
        log.exception("Formula 2 failed")
        return None


def path(candidate: Dict[str, Any], job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Formula 2: the path object of V2_PLAN section 5.3 (radar axes, fit list, gap list, summary). Plain JSON."""
    try:
        return _load("f2").evaluate_path(candidate, job)
    except Exception:  # noqa: BLE001
        log.exception("Formula 2 (path) failed")
        return None


def proximity(job_a: Dict[str, Any], job_b: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Formula 3 (JPI): how close two jobs are."""
    try:
        return _load("f3").compare_two_jobs(job_a, job_b)
    except Exception:  # noqa: BLE001
        log.exception("Formula 3 failed")
        return None


def salary_midpoint(job: Dict[str, Any]) -> int:
    """The middle of the yearly pay of a job, in AUD (Formula 3 changes a day or hour rate to a yearly pay)."""
    try:
        return int(round(_load("f3").get_job_salary_midpoint(job)))
    except Exception:  # noqa: BLE001
        return 0


def proximity_matrix(jobs: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    try:
        return _load("f3").compare_multiple_jobs(jobs)
    except Exception:  # noqa: BLE001
        log.exception("Formula 3 matrix failed")
        return None


def merit_dimensions(candidate: Dict[str, Any], job: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Formula 4 (RMS): the parts of the merit model. The platform shows the parts, never the combined number.
    With a job, the skill depth is the mean level of the skills that the job asks for."""
    try:
        return _load("f4").calculate_candidate_merit_score(candidate, job=job) if job is not None else _load("f4").calculate_candidate_merit_score(candidate)
    except Exception:  # noqa: BLE001
        log.exception("Formula 4 failed")
        return None


def feed_scores(candidate: Dict[str, Any], jobs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Formula 5 (FRS): a feed score for each job, with the employer diversity penalty. Returns {job_id: result}.
    Send ALL the open jobs of the list: a job alone gets no penalty, so its score would differ from its score in the list."""
    if not jobs:
        return {}
    try:
        ranked = _load("f5").rank_job_feed_for_candidate(candidate, jobs, top_limit=len(jobs))
        return {item["job_id"]: item for item in ranked["top_feed"]}
    except Exception:  # noqa: BLE001
        log.exception("Formula 5 failed")
        return {}


def talent_score(candidate: Dict[str, Any], job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Formula 6 (TSS): the fit of a shared profile to a job. Used only to put profiles in order. The result has `order_value`,
    `skill_coverage` and the `skill_breakdown`. The caller must never send a number of it to an employer."""
    try:
        return _load("f6").compute_talent_search_score(candidate, job)
    except Exception:  # noqa: BLE001
        log.exception("Formula 6 failed")
        return None


def behavioural_adjust(base_frs: float, company: str, category: str, saved_companies: set, saved_categories: set,
                       ignored_counts: Dict[str, int]) -> float:
    """FRS* : the feedback loop of Formula 5 (+10% saved employer, +5% saved sector, -25% after 3 ignored jobs).

    The numbers come from `docs/02_FORMULAS_MATHEMATICAL_SPEC.md`, section 6.3.
    """
    score = float(base_frs)
    emp, cat = norm(company), norm(category)
    if emp and emp in saved_companies:
        score *= 1.10
    if cat and cat in saved_categories:
        score *= 1.05
    if emp and ignored_counts.get(emp, 0) >= 3:
        score *= 0.75
    return round(min(100.0, max(0.0, score)), 2)


# The axes of "how this job fits you". Each value is a number from 0 to 100 that a formula gives.
JOB_FIT_AXES = [
    ("occupation", "Occupation fit", "F1"), ("skills", "Skills", "F1"), ("methods", "Work methods", "F1"), ("readiness", "Readiness", "F2"),
    ("capability", "Capability", "F5"), ("pay", "Pay upside", "F5"), ("location", "Location", "F5"), ("freshness", "Freshness", "F5"),
]


def job_fit_axes(f1: Dict[str, Any], f2: Dict[str, Any], f5: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The values of Formulas 1, 2 and 5 for one talent and one job, in a fixed order, with one decimal."""
    s1, s5 = f1["sub_metrics"], f5["sub_metrics"]
    values = {
        "occupation": s1["s_tree_taxonomy"], "skills": s1["s_direct_competency"], "methods": s1["s_trans_methodology"],
        "readiness": f2["job_readiness_score"],
        "capability": s5["s_cap_capability"], "pay": s5["s_wage_upside"], "location": s5["s_loc_location"], "freshness": s5["s_rec_recency"],
    }
    return [{"key": k, "label": label, "formula": formula, "value": round(float(values[k]), 1)} for k, label, formula in JOB_FIT_AXES]
