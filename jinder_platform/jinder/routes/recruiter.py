"""Employer features: post and manage jobs, review applications, and find talent without seeing who they are (Features 5 and 6).

Privacy: every employer response is built from the shared profile (an allowlist). It never has a name, an email,
contact details, a country, the CV or the evidence lines. The name and email appear only for one application,
after the talent agreed when they chose an interview time (decision Q4).

Formulas: Formula 6 (TSS) puts talent profiles in order. Formula 4 (RMS) gives the areas for a side-by-side view.
The numbers of both formulas stay on the server. An employer sees per-skill matches, never a score on a person.
"""
import math
import sqlite3
from typing import Any, Dict, List, Optional

from .. import catalogue, config, parsing, store
from .. import engine_bridge as eb
from ..guards import require_role
from ..http_server import Ctx, route
from ..reference import JOB_CATEGORIES, LOCATIONS, SPECIALISATIONS, WORK_TYPES
from ..skills import occupation_for_job, results_from_breakdown, suggest_requirements
from ..util import (ApiError, as_list, clean_text, conflict, iso, jdump, jload, new_id, not_found, now_iso, page_params,
                    paginate, parse_iso, scrub_contact, short_id, unique, utcnow, validation)
from .account import check_upload
from .applications import (FINAL, STATUS_LABEL, TRANSITIONS, add_history, job_brief, load_app, log_event,
                           offer_of, read_feedback, save_feedback, snapshot_match, _feedback_pair)

DAY = 86400.0
JOB_SORTS = ("newest",)                 # the employer's job list and the applications of a job: one sort for now
CANDIDATE_SORTS = ("best", "updated")   # the first one is the default


# =====================================================================
# Jobs of an employer
# =====================================================================
def badge_of(job: Dict[str, Any]) -> Dict[str, Any]:
    """The close badge (Feature 6 AC3): green open, yellow less than 7 days, red closed or overdue."""
    closes = parse_iso(job["closesAt"])
    seconds = (closes - utcnow()).total_seconds() if closes else 0.0
    if seconds < 0:
        return {"badge": "closed", "label": "Closed", "daysLeft": -1}
    left = math.ceil(seconds / DAY)
    if left < 7:
        return {"badge": "closing", "label": "Closes in 1 day" if left <= 1 else f"Closes in {left} days", "daysLeft": left}
    return {"badge": "open", "label": "Open", "daysLeft": left}


def _awaiting(a: sqlite3.Row) -> bool:
    return a["status"] in ("applied", "review") or (a["status"] == "interview" and bool(a["chosen_slot_id"]) and not a["slot_confirmed"])


def job_summary(conn: sqlite3.Connection, j: Dict[str, Any]) -> Dict[str, Any]:
    apps = conn.execute("SELECT status, origin, chosen_slot_id, slot_confirmed FROM applications WHERE job_id = ?", (j["id"],)).fetchall()
    return {
        "id": j["id"], "title": j["title"], "category": j["category"], "location": j["location"], "type": j["type"],
        "salary": j["salary"], "postedAt": j["postedAt"], "closesAt": j["closesAt"], "skills": j["skills"],
        # version 2: level, specialisation, minYears, maxYears, workMode, skillRequirements, certifications, awards, educationMin
        **{k: j[k] for k in catalogue.JOB_EXTRA_KEYS},
        "targetApplicants": j["targetApplicants"], "applicantCount": sum(1 for a in apps if a["origin"] == "applied"),
        "contactedCount": sum(1 for a in apps if a["origin"] == "contacted"), "awaitingCount": sum(1 for a in apps if _awaiting(a)),
        **badge_of(j),
    }


def job_detail(conn: sqlite3.Connection, j: Dict[str, Any]) -> Dict[str, Any]:
    """The own job of an employer, with the full description (never cut) and the short summary."""
    return {**job_summary(conn, j), "company": j["company"], "summary": j["summary"], "description": j["description"]}


def own_job(ctx: Ctx, user: sqlite3.Row) -> Dict[str, Any]:
    j = catalogue.find_job(ctx.conn, ctx.params["id"])
    if not j or j["ownerId"] != user["id"]:
        raise not_found("We can't find this job.")
    return j


def _check_job(body: Dict[str, Any], partial: bool = False, current: Optional[Dict[str, Any]] = None):
    """Validate a job form (create, or edit with partial=True). Returns (skill names, skill requirements, clean keys of version 2).

    The skills come from `skillRequirements` when it has items (each skill with a level and "must"). Without it, they come from
    `skills` (names only: the levels are not set). `current` is the stored job: it is used to check minYears against maxYears.
    """
    has = lambda k: (not partial) or (k in body)  # noqa: E731
    extras, extra_errors = catalogue.clean_job_extras(body, current)
    reqs = extras.get("skillRequirements") or []
    skills = [r["name"] for r in reqs] if reqs else unique([clean_text(s, 60) for s in as_list(body.get("skills")) if isinstance(s, str) and clean_text(s, 60)])
    title = body.get("title") if isinstance(body.get("title"), str) else ""
    description = body.get("description") if isinstance(body.get("description"), str) else ""
    target = body.get("targetApplicants")
    try:
        target_ok = isinstance(target, (int, str, float)) and not isinstance(target, bool) and float(target) == int(float(target)) and 1 <= int(float(target)) <= 10000
    except (TypeError, ValueError, OverflowError):
        target_ok = False
    closes = parse_iso(body.get("closesAt")) if has("closesAt") and isinstance(body.get("closesAt"), str) else None
    check_skills = has("skills") or (partial and "skillRequirements" in body and "skillRequirements" not in extra_errors and bool(reqs))
    # The specialisation must belong to the domain (the category) of the job
    category = body.get("category") if "category" in body else (current or {}).get("category")
    spec = extras.get("specialisation") if "specialisation" in extras else (current or {}).get("specialisation")
    if spec and "specialisation" not in extra_errors and category in SPECIALISATIONS and spec not in SPECIALISATIONS[category]:
        extra_errors["specialisation"] = "Choose a specialisation of this domain."
    validation({
        "title": "" if not has("title") or len(title.strip()) >= 3 else "Enter a job title.",
        "category": "" if not has("category") or body.get("category") in JOB_CATEGORIES else "Choose a domain.",
        "location": "" if not has("location") or body.get("location") in LOCATIONS else "Choose a location.",
        "type": "" if not has("type") or body.get("type") in WORK_TYPES else "Choose a work type.",
        # The description is never cut. A text above the limit is refused, so that no one loses text without a message.
        "description": ("" if not has("description") else
                        "Write a description of at least 30 characters." if len(description.strip()) < 30 else
                        f"Use {catalogue.MAX_DESCRIPTION} characters or fewer in the description." if len(description.strip()) > catalogue.MAX_DESCRIPTION else ""),
        "skills": "" if not check_skills or 1 <= len(skills) <= 12 else "Add 1 to 12 required skills.",
        "targetApplicants": "" if not has("targetApplicants") or target_ok else "Enter a number from 1 to 10000.",
        # Feature 6 AC13: a close date in the past is rejected
        "closesAt": "" if not has("closesAt") else ("Choose a close date." if closes is None else ("The close date must be in the future." if closes < utcnow() else "")),
        **extra_errors,
    })
    return skills, reqs, extras


def _description_text(value: str) -> str:
    """The description as stored: line breaks are "\\n". Only control characters and the space at both ends are removed."""
    return clean_text(value, catalogue.MAX_DESCRIPTION).replace("\r\n", "\n").replace("\r", "\n")


@route("GET", "/recruiter/jobs")
def my_jobs(ctx: Ctx):
    """The jobs of the employer, one page at a time. `sort`: newest (the posting date, newest first). Ties are broken by the id."""
    user = require_role(ctx, "recruiter")
    params = page_params(ctx.query, JOB_SORTS)
    jobs = sorted((j for j in catalogue.load_jobs(ctx.conn) if j["ownerId"] == user["id"]), key=lambda j: j["id"])
    jobs.sort(key=lambda j: j["postedAt"], reverse=True)       # a stable sort: the id order stays for equal dates
    chunk, page = paginate(jobs, params)
    return {"items": [job_summary(ctx.conn, j) for j in chunk], "page": page, "sort": params.sort}


@route("POST", "/recruiter/jobs/suggest-skills")
def suggest_skills(ctx: Ctx):
    """Taxonomy skills for a job: the skills that the text shows, the core skills of the occupation of the title, the usual skills of the domain.
    `skills` has the names (as before). `skillRequirements` has the same skills with level 3 and must true."""
    require_role(ctx, "recruiter")
    title = ctx.body.get("title") if isinstance(ctx.body.get("title"), str) else ""
    description = ctx.body.get("description") if isinstance(ctx.body.get("description"), str) else ""
    category = ctx.body.get("category") if isinstance(ctx.body.get("category"), str) else None
    reqs = suggest_requirements(title, description, category, 10)
    return {"skills": [r["name"] for r in reqs], "skillRequirements": reqs}


# ---------- Post a job from a file (PDF or DOCX job description) ----------
@route("POST", "/recruiter/jobs/import")
def jobs_import(ctx: Ctx):
    user = require_role(ctx, "recruiter")
    name, ext, data = check_upload(ctx)
    stored = parsing.store_upload(data, ext)
    parse_id = parsing.create_parse(ctx.conn, "jd", user["id"], name, stored)
    ctx.after_commit.append(lambda: parsing.submit(parse_id))
    return 202, {"parse": {"id": parse_id, "status": "parsing"}}


@route("GET", "/recruiter/jobs/import/:id")
def jobs_import_status(ctx: Ctx):
    user = require_role(ctx, "recruiter")
    row = ctx.conn.execute("SELECT * FROM parses WHERE id = ? AND user_id = ? AND kind = 'jd'", (ctx.params["id"], user["id"])).fetchone()
    if not row:
        raise not_found("We can't find this file upload.")
    if row["status"] == "parsing":
        return {"id": row["id"], "status": "parsing"}
    if row["status"] == "failed":
        return {"id": row["id"], "status": "failed", "error": row["error"] or parsing.JD_FAILED}
    return {"id": row["id"], "status": "done", "result": jload(row["result"], {})}


@route("POST", "/recruiter/jobs")
def job_create(ctx: Ctx):
    user = require_role(ctx, "recruiter")
    skills, requirements, extras = _check_job(ctx.body)
    b = ctx.body
    conn = ctx.conn
    title = clean_text(b["title"], 120)
    # The occupation (ANZSCO) comes from the taxonomy: the role in the title, else the specialisation. The formulas compare jobs by occupation.
    occ = occupation_for_job(title, extras.get("specialisation"), b["category"])
    description = _description_text(b["description"])
    job_id = f"job-{short_id(8)}"
    now = now_iso()
    extras.setdefault("level", "Mid")          # the old, short form of a job has no level: it is a "Mid" job
    salary = clean_text(b.get("salary") or "", 80) or "Market competitive"
    smin, smax, unit = catalogue.parse_salary(salary)      # the numbers as written, with the unit. The formulas change them to a yearly pay.
    cols = {
        "id": job_id, "owner_id": user["id"], "title": title, "company": user["company"] or "", "category": b["category"],
        "location": b["location"], "area": b["location"], "type": b["type"], "anzsco": str(occ["code"]) if occ else "",
        "occupation": occ["title"] if occ else "",
        "salary": salary, "salary_min": smin, "salary_max": smax, "salary_unit": unit, "summary": catalogue.summary_of(description),
        "description": description, "target_applicants": int(float(b["targetApplicants"])), "posted_at": now,
        "closes_at": iso(parse_iso(b["closesAt"])), "created_at": now,
        **catalogue.extras_to_columns(extras),
    }
    conn.execute(f"INSERT INTO jobs ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})", tuple(cols.values()))
    catalogue.save_job_skills(conn, job_id, skills, requirements)
    return job_summary(conn, catalogue.find_job(conn, job_id))


@route("GET", "/recruiter/jobs/:id")
def job_get(ctx: Ctx):
    user = require_role(ctx, "recruiter")
    j = own_job(ctx, user)
    return job_detail(ctx.conn, j)


@route("PATCH", "/recruiter/jobs/:id")
def job_update(ctx: Ctx):
    """Edit a job. Everyone who applied gets a notification (Feature 6 AC10, Feature 7 AC3)."""
    user = require_role(ctx, "recruiter")
    j = own_job(ctx, user)
    skills, requirements, extras = _check_job(ctx.body, partial=True, current=j)
    b = ctx.body
    conn = ctx.conn
    sets, vals = [], []
    for key, col, limit in (("title", "title", 120), ("category", "category", 80), ("location", "location", 40), ("type", "type", 40),
                            ("salary", "salary", 80), ("description", "description", catalogue.MAX_DESCRIPTION)):
        if key in b and isinstance(b[key], str):
            sets.append(f"{col} = ?")
            value = _description_text(b[key]) if key == "description" else clean_text(b[key], limit)
            vals.append(value or "Market competitive" if key == "salary" else value)
    if "salary" in b and isinstance(b["salary"], str):
        smin, smax, unit = catalogue.parse_salary(clean_text(b["salary"], 80))
        sets += ["salary_min = ?", "salary_max = ?", "salary_unit = ?"]
        vals += [smin, smax, unit]
    if ("title" in b and isinstance(b["title"], str)) or "specialisation" in extras or "category" in b:
        # A new title can mean a new occupation. The formulas compare jobs by occupation.
        title = clean_text(b["title"], 120) if isinstance(b.get("title"), str) else j["title"]
        occ = occupation_for_job(title, extras["specialisation"] if "specialisation" in extras else j["specialisation"],
                                 b["category"] if isinstance(b.get("category"), str) else j["category"])
        if occ or "title" in b:
            sets += ["anzsco = ?", "occupation = ?"]
            vals += [str(occ["code"]) if occ else "", occ["title"] if occ else ""]
    if "location" in b and isinstance(b["location"], str):
        sets.append("area = ?")
        vals.append(clean_text(b["location"], 40))
    if "description" in b and isinstance(b["description"], str):
        sets.append("summary = ?")
        vals.append(catalogue.summary_of(_description_text(b["description"])))
    if "targetApplicants" in b:
        sets.append("target_applicants = ?")
        vals.append(int(float(b["targetApplicants"])))
    if "closesAt" in b:
        sets.append("closes_at = ?")
        vals.append(iso(parse_iso(b["closesAt"])))
    for col, value in catalogue.extras_to_columns(extras).items():
        sets.append(f"{col} = ?")
        vals.append(value)
    sets.append("edited_at = ?")
    vals.append(now_iso())
    conn.execute(f"UPDATE jobs SET {', '.join(sets)} WHERE id = ?", (*vals, j["id"]))
    if requirements:                       # skills with levels
        catalogue.save_job_skills(conn, j["id"], skills, requirements)
    elif "skills" in b:                    # names only: the levels are cleared
        catalogue.save_job_skills(conn, j["id"], skills)
    elif "skillRequirements" in extras:    # an empty list: keep the skills, clear their levels
        catalogue.save_job_skills(conn, j["id"], j["skills"])
    fresh = catalogue.find_job(conn, j["id"])
    for a in conn.execute("SELECT id, candidate_id, status FROM applications WHERE job_id = ?", (j["id"],)).fetchall():
        if a["status"] in FINAL:
            continue
        store.notify(conn, a["candidate_id"], "job_edited", f"{fresh['title']} was updated",
                     "The employer changed this job. Check the details.", f"/applications/{a['id']}")
    return job_detail(conn, fresh)


# =====================================================================
# Applications for a job (Feature 6 AC4 to AC9)
# =====================================================================
@route("GET", "/recruiter/jobs/:id/applications")
def job_applications(ctx: Ctx):
    """The applications for one job, one page at a time. `sort`: newest (the date of the application, newest first). Ties: the id."""
    user = require_role(ctx, "recruiter")
    j = own_job(ctx, user)
    params = page_params(ctx.query, JOB_SORTS)
    rows = ctx.conn.execute("SELECT * FROM applications WHERE job_id = ? ORDER BY id", (j["id"],)).fetchall()
    rows = sorted(rows, key=lambda r: r["created_at"], reverse=True)       # a stable sort: the id order stays for equal dates
    rows, page = paginate(rows, params)
    items = []
    for a in rows:
        snap = jload(a["snapshot"], {})
        match = jload(a["match_json"], {"coverage": None, "skills": []})
        items.append({
            "id": a["id"], "alias": snap.get("alias"), "origin": a["origin"], "status": a["status"], "statusLabel": STATUS_LABEL[a["status"]],
            "coverage": match["coverage"], "matched": sum(1 for s in match["skills"] if s["status"] == "match"), "total": len(match["skills"]),
            "awaiting": _awaiting(a), "updatedAt": a["updated_at"], "createdAt": a["created_at"],
        })
    return {"job": job_summary(ctx.conn, j), "items": items, "page": page, "sort": params.sort}


def recruiter_view(conn: sqlite3.Connection, a: Dict[str, Any]) -> Dict[str, Any]:
    """An application as the employer sees it. The identity is there only when the talent agreed."""
    identity = None
    if a["identity_shared"]:
        u = store.get_user(conn, a["candidate_id"])
        identity = {"name": u["name"], "email": u["email"]} if u else None
    allowed = [s for s in TRANSITIONS[a["status"]] if s != "accepted" or a["slot_confirmed"]]
    return {
        "id": a["id"], "job": job_brief(conn, a["job_id"]), "origin": a["origin"], "status": a["status"], "statusLabel": STATUS_LABEL[a["status"]],
        "note": a["note"], "history": a["history"], "slots": a["slots"], "chosenSlotId": a["chosen_slot_id"],
        "slotConfirmed": bool(a["slot_confirmed"]), "identity": identity, "offer": offer_of(a), "snapshot": a["snapshot"], "match": a["match"],
        "feedback": _feedback_pair(a, "recruiter", "candidate"), "allowedNext": allowed,
        "canConfirmSlot": a["status"] == "interview" and bool(a["chosen_slot_id"]) and not a["slot_confirmed"],
        "final": a["status"] in FINAL, "createdAt": a["created_at"], "updatedAt": a["updated_at"],
    }


def _own_app(ctx: Ctx):
    user = require_role(ctx, "recruiter")
    row = ctx.conn.execute("SELECT id FROM applications WHERE id = ? AND recruiter_id = ?", (ctx.params["id"], user["id"])).fetchone()
    if not row:
        raise not_found("We can't find this application.")
    return user, load_app(ctx.conn, row["id"])


@route("GET", "/recruiter/applications/:id")
def application_get(ctx: Ctx):
    _, a = _own_app(ctx)
    return recruiter_view(ctx.conn, a)


def _slot_text(iso_text: str) -> str:
    dt = parse_iso(iso_text)
    return dt.strftime("%d %b %Y, %H:%M UTC").lstrip("0") if dt else ""


@route("POST", "/recruiter/applications/:id/status")
def application_status(ctx: Ctx):
    """Change the status. Only valid transitions (Feature 6 AC6, AC14). Moving to Review locks the talent's edits (AC7)."""
    user, a = _own_app(ctx)
    conn = ctx.conn
    to = ctx.body.get("to")
    if to not in TRANSITIONS.get(a["status"], []):
        raise conflict(f"You can't move an application from {STATUS_LABEL[a['status']]} to {STATUS_LABEL.get(to, to) if isinstance(to, str) else to}.")
    job = catalogue.find_job(conn, a["job_id"])
    title = job["title"] if job else "your application"
    cid = a["candidate_id"]
    link = f"/applications/{a['id']}"
    if to == "interview":
        raw = [s for s in as_list(ctx.body.get("slots")) if isinstance(s, str) and parse_iso(s)]
        times = [parse_iso(s) for s in raw]
        validation({"slots": "Offer 1 to 3 interview times." if not 1 <= len(times) <= 3
                    else ("Choose times in the future." if any(t <= utcnow() for t in times) else "")})
        conn.execute("DELETE FROM application_slots WHERE application_id = ?", (a["id"],))
        conn.executemany("INSERT INTO application_slots (id, application_id, start, position) VALUES (?, ?, ?, ?)",
                         [(short_id(8), a["id"], iso(t), i) for i, t in enumerate(times)])
        conn.execute("UPDATE applications SET chosen_slot_id = NULL, slot_confirmed = 0 WHERE id = ?", (a["id"],))
        add_history(conn, a["id"], "interview", "recruiter", f"Offered {len(times)} interview time{'s' if len(times) > 1 else ''}")
        store.notify(conn, cid, "interview_slots", f"Interview times for {title}", "Choose a time that works for you.", link)
    elif to == "accepted":
        if not a["slot_confirmed"]:
            raise conflict("Confirm the interview time first. Then record the result.")
        add_history(conn, a["id"], "accepted", "recruiter")
        store.notify(conn, cid, "result", f"Good news about {title}", "The employer accepted you after the interview. An offer can follow.", link, email=True)
    elif to == "offer":
        offer = ctx.body.get("offer", "")
        offer = offer if isinstance(offer, str) else ""
        validation({"offer": "" if len(offer.strip()) >= 10 else "Write the offer details (at least 10 characters)."})
        conn.execute("UPDATE applications SET offer_text = ?, offer_sent_at = ? WHERE id = ?", (scrub_contact(clean_text(offer, 2000)).strip(), now_iso(), a["id"]))
        add_history(conn, a["id"], "offer", "recruiter")
        store.notify(conn, cid, "offer", f"You have an offer for {title}", "Read it and answer.", link, email=True)
    elif to == "rejected":
        add_history(conn, a["id"], "rejected", "recruiter")
        store.notify(conn, cid, "result", f"Update on {title}", "The employer did not select you this time. You can give feedback.", link, email=True)
    else:
        add_history(conn, a["id"], to, "recruiter")
        store.notify(conn, cid, "status", f"{title}: {STATUS_LABEL[to]}", "The employer is reviewing your application." if to == "review" else "", link)
    store.track(conn, "job_respond", "application", a["id"], user["id"])
    return recruiter_view(conn, load_app(conn, a["id"]))


@route("POST", "/recruiter/applications/:id/confirm-slot")
def application_confirm_slot(ctx: Ctx):
    _, a = _own_app(ctx)
    if not (a["status"] == "interview" and a["chosen_slot_id"] and not a["slot_confirmed"]):
        raise conflict("There is no interview time to confirm.")
    ctx.conn.execute("UPDATE applications SET slot_confirmed = 1 WHERE id = ?", (a["id"],))
    log_event(ctx.conn, a["id"], "interview", "recruiter", "Confirmed the interview time")
    slot = next((s for s in a["slots"] if s["id"] == a["chosen_slot_id"]), None)
    store.notify(ctx.conn, a["candidate_id"], "slot_confirmed", "Your interview time is confirmed", _slot_text(slot["start"]) if slot else "", f"/applications/{a['id']}")
    return recruiter_view(ctx.conn, load_app(ctx.conn, a["id"]))


@route("POST", "/recruiter/applications/:id/feedback")
def application_feedback(ctx: Ctx):
    user, a = _own_app(ctx)
    if a["status"] not in FINAL:
        raise conflict("You can give feedback when the application is finished.")
    to_other, to_team = read_feedback(ctx)
    save_feedback(ctx.conn, a["id"], "recruiter", to_other, to_team)
    if to_other:
        store.notify(ctx.conn, a["candidate_id"], "feedback", f"{user['company']} sent you feedback", "", f"/applications/{a['id']}")
    return recruiter_view(ctx.conn, load_app(ctx.conn, a["id"]))


# =====================================================================
# Anonymous talent (Feature 5)
# =====================================================================
def _pick_job(ctx: Ctx, user: sqlite3.Row, jobs: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    own = [j for j in jobs if j["ownerId"] == user["id"]]
    own.sort(key=lambda j: j["postedAt"], reverse=True)
    wanted = ctx.query.get("jobId")
    return (next((j for j in own if j["id"] == wanted), None) if wanted else None) or next((j for j in own if catalogue.is_open(j)), None) or (own[0] if own else None)


def _id_set(conn: sqlite3.Connection, table: str, user_id: str) -> set:
    return {r["candidate_id"] for r in conn.execute(f"SELECT candidate_id FROM {table} WHERE recruiter_id = ?", (user_id,)).fetchall()}


def _shared_candidate(cand: Dict[str, Any]) -> Dict[str, Any]:
    """The talent dictionary for the formulas, built from the SHARED profile only (no CV, no evidence, no private key). Made once for each request."""
    if "_engine" not in cand:
        cand["_engine"] = eb.prepare_candidate(eb.shared_candidate_dict(cand["shared"], cand["id"]), shared_only=True)
    return cand["_engine"]


def _card(conn: sqlite3.Connection, recruiter: sqlite3.Row, cand: Dict[str, Any], job: Optional[Dict[str, Any]], saved: set, apps: Dict[str, str],
          jd: Optional[Dict[str, Any]] = None):
    """The card of an anonymous talent for a job, and the value that orders the list (it never leaves the server).

    The per-skill match comes from Formula 6 (the `skill_breakdown`). The order value is `0.6 x coverage + 0.4 x TSS` of the engine.
    """
    shared = cand["shared"]
    res = {"items": [], "coverage": None, "matched": 0, "partial": 0}
    order = 0.0
    if job is not None and jd is not None:
        ts = eb.talent_score(_shared_candidate(cand), jd)
        if ts:
            res = results_from_breakdown(ts["skill_breakdown"], ts["skill_coverage"])
            order = float(ts["order_value"])
    card = {
        "id": cand["id"], "alias": shared["alias"], "roles": shared["roles"], "skills": shared["skills"],
        "qualifications": shared["qualifications"], "years": shared["years"], "industries": shared["industries"],
        "locations": shared["locations"], "coverage": res["coverage"], "matched": res["matched"], "partial": res["partial"],
        "total": len(res["items"]) if job else 0, "saved": cand["id"] in saved, "applicationId": apps.get(cand["id"]),
        # version 2: from the shared profile only (no name, no score)
        "level": shared["level"], "yearsExperience": shared["yearsExperience"], "certifications": shared["certifications"],
        "awards": shared["awards"], "skillLevels": shared["skillLevels"], "updatedAt": shared["updatedAt"],
        "_items": res["items"],
    }
    return card, order


@route("GET", "/recruiter/candidates")
def candidates_list(ctx: Ctx):
    """The anonymous talent list for a job, one page at a time.

    `sort`: best (the order of the fit to the job, default) or updated (the profile that changed last comes first).
    Ties are broken by the id. A Basic employer gets the first 5 only: one page, `limitedTo` 5, `page.total` is the real number.
    """
    user = require_role(ctx, "recruiter")
    params = page_params(ctx.query, CANDIDATE_SORTS)
    conn = ctx.conn
    jobs = catalogue.load_jobs(conn)
    job = _pick_job(ctx, user, jobs)
    ent = store.plan_flags(conn, user)
    skipped = _id_set(conn, "skipped_candidates", user["id"])
    saved = _id_set(conn, "saved_candidates", user["id"])
    view = "saved" if ctx.query.get("view") == "saved" else "all"
    apps = {r["candidate_id"]: r["id"] for r in conn.execute(
        "SELECT id, candidate_id FROM applications WHERE job_id = ? AND recruiter_id = ?", (job["id"] if job else "", user["id"])).fetchall()}
    jd = eb.prepare_job(eb.job_dict(job)) if job else None
    ranked = []
    for cand in store.candidate_pool(conn):
        if cand["id"] in skipped:
            continue
        card, order = _card(conn, user, cand, job, saved, apps, jd)
        if view == "saved" and not card["saved"]:
            continue
        ranked.append((order, cand["updated_at"], card))     # the order value never leaves the server
    ranked.sort(key=lambda t: t[2]["id"])      # the id breaks ties: the sorts below are stable
    if params.sort == "best":
        ranked.sort(key=lambda t: (-t[0], -(t[2]["coverage"] if t[2]["coverage"] is not None else -1), -t[2]["matched"]))
    else:
        ranked.sort(key=lambda t: t[1], reverse=True)
    all_cards = [c for _, _, c in ranked]
    shown, page = paginate(all_cards, params, cap=ent["topN"])
    items = []
    for c in shown:     # only the profiles of this page were shown
        store.track(conn, "profile_appear", "candidate", c["id"], user["id"])
        items.append({k: v for k, v in c.items() if not k.startswith("_")})
    if ent["plan"] == "premium" and len(shown) > config.TOP_N:
        # A Premium employer opened a list with more profiles than Basic shows. This marks the benefit "See every talent profile" as used.
        store.track(conn, "talent_list_full", "feature", "talent_list", user["id"])
    return {"job": {"id": job["id"], "title": job["title"], "skills": job["skills"]} if job else None, "items": items,
            "total": len(all_cards), "limitedTo": ent["topN"], "plan": ent["plan"], "skippedCount": len(skipped),
            "page": page, "sort": params.sort}


def _find_candidate(conn: sqlite3.Connection, cand_id: str) -> Dict[str, Any]:
    found = store.candidate_pool(conn, only_id=cand_id)
    if not found:
        raise not_found("We can't find this profile.")
    return found[0]


@route("GET", "/recruiter/candidates/:id")
def candidate_get(ctx: Ctx):
    user = require_role(ctx, "recruiter")
    conn = ctx.conn
    cand = _find_candidate(conn, ctx.params["id"])
    jobs = catalogue.load_jobs(conn)
    job = _pick_job(ctx, user, jobs)
    saved = _id_set(conn, "saved_candidates", user["id"])
    apps = {r["candidate_id"]: r["id"] for r in conn.execute(
        "SELECT id, candidate_id FROM applications WHERE job_id = ? AND recruiter_id = ?", (job["id"] if job else "", user["id"])).fetchall()}
    card, _order = _card(conn, user, cand, job, saved, apps, eb.prepare_job(eb.job_dict(job)) if job else None)
    items = card.pop("_items")
    store.track(conn, "profile_watch", "candidate", cand["id"], user["id"])
    shared = cand["shared"]
    return {**card, "job": {"id": job["id"], "title": job["title"]} if job else None,
            "match": {"coverage": card["coverage"], "skills": items}, "targetRoles": shared["targetRoles"],
            "workTypes": shared["workTypes"], "fieldsOfStudy": shared["fieldsOfStudy"], "entitlements": store.entitlements_of(conn, user)}


@route("PUT", "/recruiter/candidates/:id/save")
def candidate_save(ctx: Ctx):
    user = require_role(ctx, "recruiter")
    _find_candidate(ctx.conn, ctx.params["id"])
    cur = ctx.conn.execute("INSERT OR IGNORE INTO saved_candidates (recruiter_id, candidate_id, created_at) VALUES (?, ?, ?)",
                           (user["id"], ctx.params["id"], now_iso()))
    if cur.rowcount:
        store.track(ctx.conn, "profile_saved", "candidate", ctx.params["id"], user["id"])
    return {"id": ctx.params["id"], "saved": True}


@route("DELETE", "/recruiter/candidates/:id/save")
def candidate_unsave(ctx: Ctx):
    user = require_role(ctx, "recruiter")
    ctx.conn.execute("DELETE FROM saved_candidates WHERE recruiter_id = ? AND candidate_id = ?", (user["id"], ctx.params["id"]))
    return {"id": ctx.params["id"], "saved": False}


@route("PUT", "/recruiter/candidates/:id/skip")
def candidate_skip(ctx: Ctx):
    user = require_role(ctx, "recruiter")
    _find_candidate(ctx.conn, ctx.params["id"])
    ctx.conn.execute("INSERT OR IGNORE INTO skipped_candidates (recruiter_id, candidate_id, created_at) VALUES (?, ?, ?)",
                     (user["id"], ctx.params["id"], now_iso()))
    store.track(ctx.conn, "profile_skip", "candidate", ctx.params["id"], user["id"])
    return {"id": ctx.params["id"], "skipped": True}


@route("DELETE", "/recruiter/candidates/skipped")
def candidates_clear_skipped(ctx: Ctx):
    user = require_role(ctx, "recruiter")
    ctx.conn.execute("DELETE FROM skipped_candidates WHERE recruiter_id = ?", (user["id"],))
    return {"ok": True}


# ---------- Premium: invite a talent who did not apply ----------
@route("POST", "/recruiter/candidates/:id/contact")
def candidate_contact(ctx: Ctx):
    user = require_role(ctx, "recruiter")
    store.require_premium(ctx.conn, user, "canContact")
    conn = ctx.conn
    cand = _find_candidate(conn, ctx.params["id"])
    job = catalogue.find_job(conn, str(ctx.body.get("jobId") or ""))
    if not job or job["ownerId"] != user["id"]:
        raise ApiError(400, "VALIDATION_ERROR", "Choose one of your jobs.", {"jobId": "Choose one of your jobs."})
    if not catalogue.is_open(job):
        raise conflict("This job is closed. You can't invite someone for it.")
    if conn.execute("SELECT 1 FROM applications WHERE job_id = ? AND candidate_id = ?", (job["id"], cand["id"])).fetchone():
        raise conflict("This person is already in the pipeline for this job.")
    message = ctx.body.get("message") if isinstance(ctx.body.get("message"), str) else ""
    validation({"message": "" if 10 <= len(message.strip()) and len(message) <= 500 else "Write a message of 10 to 500 characters."})
    snapshot = cand["shared"]
    now = now_iso()
    app_id = new_id()
    msg = scrub_contact(message).strip()
    conn.execute(
        """INSERT INTO applications (id, job_id, candidate_id, recruiter_id, origin, status, note, message, snapshot, match_json,
                                     slot_confirmed, identity_shared, created_at, updated_at)
           VALUES (?, ?, ?, ?, 'contacted', 'contacted', '', ?, ?, ?, 0, 0, ?, ?)""",
        (app_id, job["id"], cand["id"], user["id"], msg, jdump(snapshot), jdump(snapshot_match(job, snapshot)), now, now))
    conn.execute("INSERT INTO application_history (application_id, status, at, actor, note) VALUES (?, 'contacted', ?, 'recruiter', ?)", (app_id, now, msg))
    store.notify(conn, cand["id"], "contacted", f"{user['company']} invited you to apply for {job['title']}", msg, f"/applications/{app_id}")
    store.track(conn, "invite", "application", app_id, user["id"])   # marks the benefit "Invite talent to apply" as used
    return recruiter_view(conn, load_app(conn, app_id))


# ---------- Premium: compare 2 to 5 profiles side by side, per skill. No combined score, no ranking of people. ----------
# The axes of the comparison radar. Each value is a number from 0 to 100. No axis is a total, and the platform never adds them up.
# The key "statutory" is the part "certification readiness" of Formula 6. The key stays (it was "Licence readiness" in version 1).
RADAR_AXES = [
    ("coverage", "Skills for this job", "skills"), ("requirement", "Requirement fit", "F6"), ("seniority", "Seniority fit", "F6"),
    ("statutory", "Certification readiness", "F6"), ("depth", "Skill depth", "F4"), ("experience", "Experience", "F4"),
    ("transferable", "Transferable skills", "F4"), ("level", "Level standing", "F4"), ("evidence", "Evidence", "F4"),
]

# The areas of Formula 4 that the comparison shows as positions: (label, key in the F4 parts)
AREAS = [("Skill depth", "skill_depth"), ("Experience", "experience_maturity"), ("Level standing", "level_standing"), ("Evidence", "evidence_rigor"),
         ("Transferable skills", "transferable_agility"), ("Certifications", "certification_strength"), ("Awards", "award_strength"),
         ("Qualification level", "education_bonus")]
AREA_TIE_BAND = 3.0   # points. Profiles within this distance of the leader of a group share its position (the "equivalent competency band")


def _metrics(cand: Dict[str, Any], jd: Dict[str, Any]):
    """Formula 4 (the merit model) and Formula 6 (the fit to the job), part by part: (F4 parts, F6 result). The numbers stay on the server.
    Only the shared profile goes into them."""
    sc = _shared_candidate(cand)
    f4 = (eb.merit_dimensions(sc, job=jd) or {}).get("sub_metrics", {})
    ts = eb.talent_score(sc, jd) or {"skill_breakdown": [], "skill_coverage": None, "sub_metrics": {}}
    return f4, ts


def _radar_values(f4: Dict[str, Any], ts: Dict[str, Any], coverage: Optional[int]) -> Dict[str, Optional[float]]:
    f6 = ts.get("sub_metrics", {})
    values: Dict[str, Optional[float]] = {
        "coverage": float(coverage) if coverage is not None else None,
        "requirement": f6.get("s_req_fit"), "seniority": f6.get("s_sen_parity"), "statutory": f6.get("s_reg_readiness"),
        "depth": f4.get("skill_depth"), "experience": f4.get("experience_maturity"), "transferable": f4.get("transferable_agility"),
        "level": f4.get("level_standing"), "evidence": f4.get("evidence_rigor"),
    }
    return {k: (round(float(v), 1) if v is not None else None) for k, v in values.items()}


def _positions(values: List[float]) -> List[int]:
    """The position of each value, 1 = the highest. Values that are within AREA_TIE_BAND of the first value of a group share the position.

    The next group starts after the group before it: values 90, 89, 70 give the positions 1, 1, 3.
    """
    order = sorted(range(len(values)), key=lambda i: (-values[i], i))
    out = [0] * len(values)
    i = 0
    while i < len(order):
        top = values[order[i]]
        j = i
        while j < len(order) and top - values[order[j]] <= AREA_TIE_BAND:
            out[order[j]] = i + 1
            j += 1
        i = j
    return out


def _area_positions(picked: List[Dict[str, Any]], f4s: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """For each area of Formula 4: the position of each profile in THAT area. The positions are never added up (F-04)."""
    out = []
    for label, key in AREAS:
        values = [m.get(key) for m in f4s]
        if any(v is None for v in values):
            continue
        out.append({"area": label, "ranks": [{"id": c["id"], "position": p} for c, p in zip(picked, _positions([float(v) for v in values]))]})
    return out


def _level(value: Any) -> Optional[int]:
    return None if value is None else int(round(float(value)))


def _skill_matrix(breakdowns: List[List[Dict[str, Any]]], picked: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """One row for each skill that the job asks for. Each profile has its level and its status: meets, below, related or missing.
    All profiles are matched against the same job, so the lists of the formula have the same skills in the same order."""
    rows = []
    for k, item in enumerate(breakdowns[0] if breakdowns else []):
        cells = {}
        for c, b in zip(picked, breakdowns):
            mine = b[k] if k < len(b) else {}
            cells[c["id"]] = {"level": _level(mine.get("have_level")), "status": mine.get("status", "missing")}
        rows.append({"skill": item["name"], "required": _level(item.get("need_level")), "must": bool(item.get("must", True)), "byCandidate": cells})
    return rows


@route("GET", "/recruiter/compare")
def compare(ctx: Ctx):
    """Two to five anonymous profiles side by side for one of the employer's jobs (Premium).

    No total and no ranking of people. The radar has one line for each profile. The areas show the position of each profile
    inside ONE area of Formula 4. The skill matrix shows the level of each profile in each skill that the job asks for.
    A refused request with ids names the ids that cannot be compared in `missing` (next to `error`).
    """
    user = require_role(ctx, "recruiter")
    store.require_premium(ctx.conn, user, "canCompare")
    conn = ctx.conn
    ids = list(dict.fromkeys(i.strip() for i in str(ctx.query.get("ids", "")).split(",") if i.strip()))
    job_id = str(ctx.query.get("jobId", "")).strip()
    bad = {"ids": "" if 2 <= len(ids) <= config.COMPARE_MAX else f"Choose 2 to {config.COMPARE_MAX} profiles to compare.",
           "jobId": "" if job_id else "Choose one of your jobs."}
    if any(bad.values()):
        raise ApiError(400, "VALIDATION_ERROR", "Some fields are not valid.", {k: v for k, v in bad.items() if v}, extra={"missing": ids[config.COMPARE_MAX:]})
    job = catalogue.find_job(conn, job_id)
    if not job or job["ownerId"] != user["id"]:
        raise not_found("We can't find this job.")
    pool = {c["id"]: c for c in store.candidate_pool(conn)}
    absent = [i for i in ids if i not in pool]
    if absent:
        raise ApiError(404, "NOT_FOUND", "We can't find one of the profiles.",
                       {"ids": "One or more of these profiles can't be compared. They may have been removed."}, extra={"missing": absent})
    picked = [pool[i] for i in ids]

    jd = eb.prepare_job(eb.job_dict(job))
    metrics = [_metrics(c, jd) for c in picked]
    matches = [results_from_breakdown(ts["skill_breakdown"], ts["skill_coverage"]) for _, ts in metrics]
    values = [_radar_values(f4, ts, matches[i]["coverage"]) for i, (f4, ts) in enumerate(metrics)]
    axes = [(k, label, f) for k, label, f in RADAR_AXES if all(v[k] is not None for v in values)]
    candidates = []
    for i, c in enumerate(picked):
        s = c["shared"]
        candidates.append({
            "id": c["id"], "alias": s["alias"], "level": s["level"], "years": s["years"], "yearsExperience": s["yearsExperience"],
            "roles": s["roles"], "qualifications": s["qualifications"], "certifications": s["certifications"], "awards": s["awards"],
            "coverage": matches[i]["coverage"], "skills": matches[i]["items"],
            "otherSkills": [x for x in s["skills"] if x not in job["skills"]],
        })
    store.track(conn, "compare_view", "job", job["id"], user["id"])   # marks the benefit "Compare up to 5 talent profiles" as used
    return {
        "job": {"id": job["id"], "title": job["title"], "skills": job["skills"]},
        "candidates": candidates,
        "radar": {"axes": [{"key": k, "label": label, "formula": f} for k, label, f in axes],
                  "series": [{"id": c["id"], "alias": c["shared"]["alias"], "values": [values[i][k] for k, _, _ in axes]} for i, c in enumerate(picked)]},
        "areas": _area_positions(picked, [f4 for f4, _ in metrics]),
        "skillMatrix": _skill_matrix([ts["skill_breakdown"] for _, ts in metrics], picked),
    }
