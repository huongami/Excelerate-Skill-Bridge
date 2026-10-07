"""Talent job discovery: recommendations, search, detail, bookmarks, skip and report (Feature 3).

Tracking events are written here, on the server side (Feature 7 AC4).
"""
import sqlite3
from typing import Any, Dict, List, Optional, Set

from .. import catalogue, config, store
from .. import engine_bridge as eb
from ..guards import require_role, require_user
from ..http_server import Ctx, route
from ..util import ApiError, clean_text, new_id, norm, not_found, now_iso, page_params, paginate, validation

REPORT_REASONS = ("not_relevant", "wrong_location_or_type", "misleading", "other")
_NOT_FOUND = "This job does not exist or was removed."
JOB_SORTS = ("best", "newest")                  # the first one is the default
BOOKMARK_SORTS = ("saved", "best", "newest")


# =====================================================================
# Shared helpers (also used by other route modules)
# =====================================================================
def talent_context(conn: sqlite3.Connection, user: sqlite3.Row, jobs: List[Dict[str, Any]]) -> catalogue.TalentContext:
    """Build the ranking context for one talent: profile, shared skills, and what they saved and skipped."""
    profile = store.load_profile(conn, user["id"])
    shared = [s for s in (profile or {}).get("translation", []) if store.is_shared(s)]
    by_id = {j["id"]: j for j in jobs}
    saved_companies: Set[str] = set()
    saved_categories: Set[str] = set()
    for r in conn.execute("SELECT job_id FROM bookmarks WHERE user_id = ?", (user["id"],)).fetchall():
        j = by_id.get(r["job_id"])
        if j:
            saved_companies.add(norm(j["company"]))
            saved_categories.add(norm(j["category"]))
    ignored: Dict[str, int] = {}
    for r in conn.execute("SELECT job_id FROM skips WHERE user_id = ?", (user["id"],)).fetchall():
        j = by_id.get(r["job_id"])
        if j:
            ignored[norm(j["company"])] = ignored.get(norm(j["company"]), 0) + 1
    return catalogue.TalentContext(user["id"], user["alias"] or "", profile, shared, saved_companies, saved_categories,
                                   ignored, jobs=jobs)


def _ids(conn: sqlite3.Connection, table: str, user_id: str) -> Set[str]:
    return {r["job_id"] for r in conn.execute(f"SELECT job_id FROM {table} WHERE user_id = ?", (user_id,)).fetchall()}


def flagger(conn: sqlite3.Connection, user: sqlite3.Row):
    """Add the talent's own flags to a job: bookmarked, skipped and applicationId."""
    saved = _ids(conn, "bookmarks", user["id"])
    skipped = _ids(conn, "skips", user["id"])
    applied = {r["job_id"]: r["id"] for r in conn.execute("SELECT id, job_id FROM applications WHERE candidate_id = ?", (user["id"],)).fetchall()}

    def add(job: Dict[str, Any]) -> Dict[str, Any]:
        return {**job, "bookmarked": job["id"] in saved, "skipped": job["id"] in skipped, "applicationId": applied.get(job["id"])}

    return add, skipped, set(applied)


def _appear(conn: sqlite3.Connection, user: sqlite3.Row, items: List[Dict[str, Any]]) -> None:
    for j in items:
        store.track(conn, "job_appear", "job", j["id"], user["id"])


# =====================================================================
# Recommendations, search, detail
# =====================================================================
@route("GET", "/jobs/recommended")
def jobs_recommended(ctx: Ctx):
    """Recommended jobs, one page at a time. `sort`: best (default) or newest. `page`, `pageSize` (10 by default, up to 50)."""
    user = require_role(ctx, "candidate")
    params = page_params(ctx.query, JOB_SORTS)
    jobs = catalogue.load_jobs(ctx.conn)
    add, skipped, applied = flagger(ctx.conn, user)
    tctx = talent_context(ctx.conn, user, jobs)
    ranked = catalogue.sort_pairs(catalogue.recommended_pairs(tctx, jobs, skipped | applied), params.sort)
    chunk, page = paginate(ranked, params)
    items = [catalogue.card(j, m) for j, m in chunk]
    _appear(ctx.conn, user, items)    # only the jobs of this page were shown
    return {"items": [add(j) for j in items], "page": page, "sort": params.sort, "source": catalogue.job_source(jobs)}


@route("GET", "/jobs")
def jobs_search(ctx: Ctx):
    """Search the open jobs, one page at a time. `q`, `location`, `sort` (best or newest), `page`, `pageSize`."""
    user = require_role(ctx, "candidate")
    params = page_params(ctx.query, JOB_SORTS)
    jobs = catalogue.load_jobs(ctx.conn)
    add, skipped, _ = flagger(ctx.conn, user)
    tctx = talent_context(ctx.conn, user, jobs)
    q = str(ctx.query.get("q", ""))[:100]
    ranked = catalogue.sort_pairs(catalogue.search_pairs(tctx, jobs, q, str(ctx.query.get("location", "")), skipped), params.sort)
    chunk, page = paginate(ranked, params)
    items = [catalogue.card(j, m) for j, m in chunk]
    _appear(ctx.conn, user, items)
    return {"total": page["total"], "items": [add(j) for j in items], "page": page, "sort": params.sort, "source": catalogue.job_source(jobs)}


_PROXIMITY_PARTS = [("taxonomy", "Occupation", "s_tree_taxonomy"), ("requirements", "Requirements", "s_req_jaccard"), ("salary", "Salary", "s_comp_salary_parity"),
                    ("sector", "Sector", "s_sec_sector_affinity"), ("place", "Place", "s_geo_alignment")]


def _skill_matrix(tctx: catalogue.TalentContext, picked: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """One row for each skill that at least one of the jobs asks for: the talent's own level, and what each job asks.

    A job with no skill levels asks for each of its skills at level 3 and "must" (see catalogue.requirements_of).
    """
    rows: Dict[str, Dict[str, Any]] = {}
    for job in picked:
        for req in catalogue.requirements_of(job):
            row = rows.get(norm(req["name"]))
            if row is None:
                row = rows[norm(req["name"])] = {"skill": req["name"], "yours": tctx.level_of(req["name"]), "byJob": {j["id"]: None for j in picked}}
            row["byJob"][job["id"]] = {"required": req["level"], "must": req["must"]}
    return list(rows.values())


@route("GET", "/jobs/compare")
def jobs_compare(ctx: Ctx):
    """Two to five jobs side by side (free for talent). For each job: the talent's fit (Formulas 1, 2 and 5, as radar values).
    For each pair of jobs: how close they are (Formula 3). The skill matrix: the talent's level and what each job asks."""
    user = require_role(ctx, "candidate")
    ids = list(dict.fromkeys(i.strip() for i in str(ctx.query.get("ids", "")).split(",") if i.strip()))
    if not 2 <= len(ids) <= config.COMPARE_MAX:
        # `missing` names the ids that cannot be compared: the ones above the limit. With too few ids there is nothing to name.
        raise ApiError(400, "VALIDATION_ERROR", "Some fields are not valid.", {"ids": f"Choose 2 to {config.COMPARE_MAX} jobs to compare."},
                       extra={"missing": ids[config.COMPARE_MAX:]})
    jobs = catalogue.load_jobs(ctx.conn)
    by_id = {j["id"]: j for j in jobs}
    absent = [i for i in ids if i not in by_id]
    if absent:
        raise ApiError(404, "NOT_FOUND", _NOT_FOUND, {"ids": "One or more of these jobs do not exist or were removed."}, extra={"missing": absent})
    picked = [by_id[i] for i in ids]
    tctx = talent_context(ctx.conn, user, jobs)
    ranked = {j["id"]: m for j, m in tctx.rank_all(picked)}
    add, _, _ = flagger(ctx.conn, user)
    out_jobs = []
    for j in picked:
        c = add(catalogue.card(j, ranked[j["id"]]))
        c["axes"] = catalogue.fit_axes_for(tctx, j)
        c["salaryMidpoint"] = eb.salary_midpoint(eb.job_dict(j))
        out_jobs.append(c)
    pairs = []
    for a in range(len(picked)):
        for b in range(a + 1, len(picked)):    # every pair: 2 jobs give 1 pair, 5 jobs give 10
            res = eb.proximity(eb.job_dict(picked[a]), eb.job_dict(picked[b]))
            if not res:
                continue
            pairs.append({
                "a": picked[a]["id"], "b": picked[b]["id"], "index": res["job_proximity_index"], "tier": res["operational_tier"],
                "advice": res["career_mobility_advice"], "salaryChange": res["differentials"]["salary_delta_label"],
                "parts": [{"key": k, "label": label, "value": res["sub_metrics"][src]} for k, label, src in _PROXIMITY_PARTS],
            })
    return {"jobs": out_jobs, "axes": [{"key": k, "label": label, "formula": f} for k, label, f in eb.JOB_FIT_AXES], "pairs": pairs,
            "skillMatrix": _skill_matrix(tctx, picked)}


@route("GET", "/jobs/:id")
def job_detail(ctx: Ctx):
    user = require_role(ctx, "candidate")
    jobs = catalogue.load_jobs(ctx.conn)
    tctx = talent_context(ctx.conn, user, jobs)
    job = catalogue.job_detail(tctx, jobs, ctx.params["id"])
    if not job:
        raise not_found(_NOT_FOUND)
    store.track(ctx.conn, "job_watch", "job", job["id"], user["id"])
    add, _, _ = flagger(ctx.conn, user)
    return {**add(job), "similar": [add(j) for j in job["similar"]]}


# =====================================================================
# Skip (Feature 3 AC4). Skipped jobs leave the recommendations and the search.
# =====================================================================
@route("PUT", "/jobs/:id/skip")
def job_skip(ctx: Ctx):
    user = require_role(ctx, "candidate")
    job_id = ctx.params["id"]
    if not catalogue.find_job(ctx.conn, job_id):
        raise not_found(_NOT_FOUND)
    ctx.conn.execute("INSERT OR IGNORE INTO skips (user_id, job_id, created_at) VALUES (?, ?, ?)", (user["id"], job_id, now_iso()))
    # Skip counts improve the recommendations (Formula 5 feedback loop). They are never shown to users (Feature 7 AC7).
    store.track(ctx.conn, "job_skip", "job", job_id, user["id"])
    return {"jobId": job_id, "skipped": True}


@route("DELETE", "/jobs/:id/skip")
def job_unskip(ctx: Ctx):
    user = require_role(ctx, "candidate")
    ctx.conn.execute("DELETE FROM skips WHERE user_id = ? AND job_id = ?", (user["id"], ctx.params["id"]))
    return {"jobId": ctx.params["id"], "skipped": False}


# =====================================================================
# Bookmarks (Feature 3 AC5, AC10)
# =====================================================================
@route("GET", "/bookmarks")
def bookmarks_list(ctx: Ctx):
    """Saved jobs, one page at a time. `sort`: saved (default: the job that was saved last comes first), best or newest (posting date)."""
    user = require_role(ctx, "candidate")
    params = page_params(ctx.query, BOOKMARK_SORTS)
    jobs = catalogue.load_jobs(ctx.conn)
    by_id = {j["id"]: j for j in jobs}
    # A removed job is left out. A closed job stays, with status "closed".
    rows = ctx.conn.execute("SELECT job_id FROM bookmarks WHERE user_id = ? ORDER BY created_at DESC, rowid DESC", (user["id"],)).fetchall()
    saved = [by_id[r["job_id"]] for r in rows if r["job_id"] in by_id]
    tctx = talent_context(ctx.conn, user, jobs)
    match = {j["id"]: m for j, m in tctx.rank_all(saved)}
    pairs = [(j, match[j["id"]]) for j in saved]          # in the order of saving: the newest bookmark first
    if params.sort != "saved":
        pairs = catalogue.sort_pairs(pairs, params.sort)
    chunk, page = paginate(pairs, params)
    add, _, _ = flagger(ctx.conn, user)
    return {"items": [add(catalogue.card(j, m)) for j, m in chunk], "page": page, "sort": params.sort}


@route("PUT", "/bookmarks/:jobId")
def bookmark_add(ctx: Ctx):
    user = require_role(ctx, "candidate")
    job_id = ctx.params["jobId"]
    if not catalogue.find_job(ctx.conn, job_id):
        raise not_found(_NOT_FOUND)
    cur = ctx.conn.execute("INSERT OR IGNORE INTO bookmarks (user_id, job_id, created_at) VALUES (?, ?, ?)", (user["id"], job_id, now_iso()))
    if cur.rowcount:
        store.track(ctx.conn, "job_save", "job", job_id, user["id"])
    return {"jobId": job_id, "bookmarked": True}


@route("DELETE", "/bookmarks/:jobId")
def bookmark_remove(ctx: Ctx):
    user = require_role(ctx, "candidate")
    ctx.conn.execute("DELETE FROM bookmarks WHERE user_id = ? AND job_id = ?", (user["id"], ctx.params["jobId"]))
    return {"jobId": ctx.params["jobId"], "bookmarked": False}


# =====================================================================
# Reports (Feature 3 AC6, Feature 5 AC6)
# =====================================================================
@route("POST", "/reports")
def report_create(ctx: Ctx):
    user = require_user(ctx)
    b = ctx.body
    target_type = b.get("targetType")
    target_id = clean_text(b.get("targetId"), 100)
    reason = b.get("reason")
    details = b.get("details", "")
    details = details if isinstance(details, str) else ""
    allowed = (user["role"] == "candidate" and target_type == "job") or (user["role"] == "recruiter" and target_type == "candidate")
    validation({
        "targetType": "" if allowed else "You can't report this.",
        "reason": "" if reason in REPORT_REASONS else "Choose a reason.",
        "details": "" if len(details) <= 500 else "Use 500 characters or fewer.",
    })
    if not target_id:
        raise ApiError(400, "VALIDATION_ERROR", "Some fields are not valid.", {"targetId": "Choose what to report."})
    # A repeat report of the same item by the same user updates the old one (no duplicates, Feature 3 NFR).
    ctx.conn.execute(
        """INSERT INTO reports (id, user_id, target_type, target_id, reason, details, at) VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(user_id, target_type, target_id) DO UPDATE SET reason = excluded.reason, details = excluded.details, at = excluded.at""",
        (new_id(), user["id"], target_type, target_id, reason, clean_text(details, 500), now_iso()))
    return {"ok": True}
