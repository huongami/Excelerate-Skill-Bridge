"""Applications and the hiring lifecycle: the talent side (Feature 4). The state machine is enforced here, on the server.

The system never changes a status on its own (Feature 6 AC12).
Flow:  applied -> review -> interview -> accepted | rejected -> offer -> confirmed  (the talent declines the offer -> rejected).
Invited by an employer (Premium):  contacted -> interview -> same flow. The talent can decline: contacted -> declined.
"""
import sqlite3
from typing import Any, Dict, List, Optional

from .. import catalogue, store
from .. import engine_bridge as eb
from ..guards import require_role
from ..http_server import Ctx, route
from ..skills import results_from_breakdown, skill_match, skill_names_from
from ..util import (ApiError, clean_text, conflict, jload, jdump, new_id, not_found, now_iso, page_params, paginate, parse_iso,
                    scrub_contact, short_id, utcnow, validation)

TRANSITIONS = {
    "applied": ["review", "rejected"],
    "contacted": ["interview", "rejected"],
    "review": ["interview", "rejected"],
    "interview": ["accepted", "rejected"],
    "accepted": ["offer", "rejected"],
    "offer": [],            # the talent answers the offer
    "confirmed": [], "rejected": [], "declined": [],
}
FINAL = ("confirmed", "rejected", "declined")
STATUS_LABEL = {
    "applied": "Applied", "contacted": "Contacted", "review": "In review", "interview": "Interview", "accepted": "Accepted",
    "offer": "Offer", "confirmed": "Confirmed", "rejected": "Not selected", "declined": "Declined",
}


# =====================================================================
# Helpers (also used by the employer routes)
# =====================================================================
def add_history(conn: sqlite3.Connection, app_id: str, status: str, by: str, note: str = "") -> str:
    """Change the status and write a history row: who changed it, and when."""
    now = now_iso()
    conn.execute("UPDATE applications SET status = ?, updated_at = ? WHERE id = ?", (status, now, app_id))
    conn.execute("INSERT INTO application_history (application_id, status, at, actor, note) VALUES (?, ?, ?, ?, ?)",
                 (app_id, status, now, by, clean_text(note, 600)))
    return now


def log_event(conn: sqlite3.Connection, app_id: str, status: str, by: str, note: str) -> None:
    """A history row that does not change the status (for example, "Chose an interview time")."""
    now = now_iso()
    conn.execute("UPDATE applications SET updated_at = ? WHERE id = ?", (now, app_id))
    conn.execute("INSERT INTO application_history (application_id, status, at, actor, note) VALUES (?, ?, ?, ?, ?)",
                 (app_id, status, now, by, clean_text(note, 600)))


def job_brief(conn: sqlite3.Connection, job_id: str) -> Dict[str, Any]:
    j = catalogue.find_job(conn, job_id)
    if not j:
        return {"id": job_id, "title": "Removed job", "company": "", "location": "", "area": "", "type": "", "status": "closed",
                "skills": [], "ownedOnJinder": False}
    return {"id": j["id"], "title": j["title"], "company": j["company"], "location": j["location"], "area": j["area"],
            "type": j["type"], "status": "open" if catalogue.is_open(j) else "closed", "skills": j["skills"],
            "ownedOnJinder": bool(j["ownerId"])}


def snapshot_match(job: Optional[Dict[str, Any]], snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """The match that the employer and the talent see: per skill of the job, against the shared skills only (Formula 6, level-aware)."""
    if not job:
        return {"coverage": None, "skills": []}
    ts = eb.talent_score(eb.shared_candidate_dict(snapshot, snapshot.get("alias") or ""), eb.job_dict(job))
    if ts:
        sm = results_from_breakdown(ts["skill_breakdown"], ts["skill_coverage"])
    else:
        sm = skill_match(job["skills"], skill_names_from(snapshot.get("skills", [])))
    return {"coverage": sm["coverage"], "skills": sm["items"]}


def load_app(conn: sqlite3.Connection, app_id: str) -> Optional[Dict[str, Any]]:
    r = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
    if not r:
        return None
    a = dict(r)
    a["history"] = [{"status": h["status"], "at": h["at"], "by": h["actor"], "note": h["note"]} for h in
                    conn.execute("SELECT * FROM application_history WHERE application_id = ? ORDER BY id", (app_id,)).fetchall()]
    a["slots"] = [{"id": s["id"], "start": s["start"]} for s in
                  conn.execute("SELECT * FROM application_slots WHERE application_id = ? ORDER BY position", (app_id,)).fetchall()]
    a["feedback"] = {f["side"]: {"toOther": f["to_other"], "toTeam": f["to_team"], "at": f["at"]} for f in
                     conn.execute("SELECT * FROM application_feedback WHERE application_id = ?", (app_id,)).fetchall()}
    a["snapshot"] = jload(a["snapshot"], {})
    a["match"] = jload(a["match_json"], {"coverage": None, "skills": []})
    return a


def offer_of(a: Dict[str, Any]) -> Optional[Dict[str, str]]:
    return {"text": a["offer_text"], "sentAt": a["offer_sent_at"]} if a.get("offer_text") else None


def _feedback_pair(a: Dict[str, Any], mine: str, theirs: str) -> Dict[str, Any]:
    """Each side sees its own feedback fully, and the other side's message to them only (never the other side's "toTeam")."""
    other = a["feedback"].get(theirs)
    return {"mine": a["feedback"].get(mine), "theirs": {"toOther": other["toOther"], "at": other["at"]} if other else None}


def candidate_view(conn: sqlite3.Connection, a: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": a["id"], "jobId": a["job_id"], "job": job_brief(conn, a["job_id"]), "origin": a["origin"], "status": a["status"],
        "statusLabel": STATUS_LABEL[a["status"]], "note": a["note"], "canEdit": a["status"] == "applied", "final": a["status"] in FINAL,
        "history": a["history"], "slots": a["slots"], "chosenSlotId": a["chosen_slot_id"], "slotConfirmed": bool(a["slot_confirmed"]),
        "identityShared": bool(a["identity_shared"]), "offer": offer_of(a), "snapshot": a["snapshot"], "match": a["match"],
        "feedback": _feedback_pair(a, "candidate", "recruiter"), "createdAt": a["created_at"], "updatedAt": a["updated_at"],
    }


def _mine(ctx: Ctx):
    user = require_role(ctx, "candidate")
    row = ctx.conn.execute("SELECT id FROM applications WHERE id = ? AND candidate_id = ?", (ctx.params["id"], user["id"])).fetchone()
    if not row:
        raise not_found("We can't find this application.")
    return user, load_app(ctx.conn, row["id"])


def _must_be(a: Dict[str, Any], statuses, message: str) -> None:
    if a["status"] not in statuses:
        raise conflict(message)


def _notify_owner(ctx: Ctx, a: Dict[str, Any], type_: str, title: str, body: str = "") -> None:
    if a["recruiter_id"]:
        store.notify(ctx.conn, a["recruiter_id"], type_, title, body, f"/review/{a['id']}")


# =====================================================================
# Apply (Feature 4 AC1, AC2, AC12, AC13)
# =====================================================================
@route("POST", "/applications")
def application_create(ctx: Ctx):
    user = require_role(ctx, "candidate")
    conn = ctx.conn
    job = catalogue.find_job(conn, str(ctx.body.get("jobId") or ""))
    if not job:
        raise not_found("This job does not exist or was removed.")
    if not catalogue.is_open(job):
        raise conflict("This job is closed. You can't apply now.")
    if conn.execute("SELECT 1 FROM applications WHERE candidate_id = ? AND job_id = ?", (user["id"], job["id"])).fetchone():
        raise conflict("You have already applied for this job.")
    note = ctx.body.get("note", "")
    note = note if isinstance(note, str) else ""
    validation({"note": "" if len(note) <= 500 else "Use 500 characters or fewer."})
    snapshot = store.shared_profile_of(conn, user)
    if not snapshot["skills"]:
        raise conflict("Accept at least one translated skill before you apply. Go to Settings › Review translated skills.")
    now = now_iso()
    app_id = new_id()
    # A frozen copy of the shared profile as submitted (Feature 4 NFR). Never the original CV.
    conn.execute(
        """INSERT INTO applications (id, job_id, candidate_id, recruiter_id, origin, status, note, snapshot, match_json,
                                     slot_confirmed, identity_shared, created_at, updated_at)
           VALUES (?, ?, ?, ?, 'applied', 'applied', ?, ?, ?, 0, 0, ?, ?)""",
        (app_id, job["id"], user["id"], job["ownerId"], scrub_contact(note).strip(), jdump(snapshot),
         jdump(snapshot_match(job, snapshot)), now, now))
    conn.execute("INSERT INTO application_history (application_id, status, at, actor, note) VALUES (?, 'applied', ?, 'candidate', '')", (app_id, now))
    store.track(conn, "job_apply", "job", job["id"], user["id"])
    if job["ownerId"]:
        store.notify(conn, job["ownerId"], "new_application", f"New application for {job['title']}", f"{user['alias']} applied.", f"/review/{app_id}")
    return candidate_view(conn, load_app(conn, app_id))


# =====================================================================
# List, detail, edit
# =====================================================================
APPLICATION_SORTS = ("updated", "best", "newest")    # the first one is the default (the order before version 2)


@route("GET", "/applications")
def application_list(ctx: Ctx):
    """The applications of the talent, one page at a time.

    `sort`: updated (default: the application that changed last comes first), best (the skill coverage, highest first)
    or newest (the date of the application, newest first). Ties are broken by the id.
    """
    user = require_role(ctx, "candidate")
    params = page_params(ctx.query, APPLICATION_SORTS)
    rows = ctx.conn.execute("SELECT id, updated_at, created_at, match_json FROM applications WHERE candidate_id = ?", (user["id"],)).fetchall()

    def coverage(r) -> int:
        c = jload(r["match_json"], {}).get("coverage")
        return -1 if c is None else c

    rows = sorted(rows, key=lambda r: r["id"])          # the id breaks ties: the sorts below keep this order for equal values
    if params.sort == "best":
        rows = sorted(rows, key=lambda r: -coverage(r))
    elif params.sort == "newest":
        rows = sorted(rows, key=lambda r: r["created_at"], reverse=True)
    else:
        rows = sorted(rows, key=lambda r: r["updated_at"], reverse=True)
    chunk, page = paginate(rows, params)
    items = []
    for r in chunk:      # only the applications of this page are loaded in full
        a = load_app(ctx.conn, r["id"])
        v = candidate_view(ctx.conn, a)
        needs = ((a["status"] == "interview" and not a["chosen_slot_id"]) or a["status"] in ("offer", "contacted")
                 or (a["status"] in FINAL and "candidate" not in a["feedback"]))
        items.append({"id": v["id"], "job": v["job"], "status": v["status"], "statusLabel": v["statusLabel"], "origin": v["origin"],
                      "final": v["final"], "coverage": v["match"]["coverage"], "createdAt": v["createdAt"],
                      "updatedAt": v["updatedAt"], "needsAction": needs})
    return {"items": items, "page": page, "sort": params.sort}


@route("GET", "/applications/:id")
def application_get(ctx: Ctx):
    _, a = _mine(ctx)
    return candidate_view(ctx.conn, a)


@route("PATCH", "/applications/:id")
def application_update(ctx: Ctx):
    """Edit the note until the employer moves the application to Review (Feature 4 AC6, AC14)."""
    _, a = _mine(ctx)
    _must_be(a, ["applied"], "The employer is reviewing your application. You can't change it now.")
    note = ctx.body.get("note", "")
    note = note if isinstance(note, str) else ""
    validation({"note": "" if len(note) <= 500 else "Use 500 characters or fewer."})
    ctx.conn.execute("UPDATE applications SET note = ?, updated_at = ? WHERE id = ?", (scrub_contact(note).strip(), now_iso(), a["id"]))
    return candidate_view(ctx.conn, load_app(ctx.conn, a["id"]))


# =====================================================================
# Interview, offer, decline, feedback
# =====================================================================
@route("POST", "/applications/:id/slot")
def application_slot(ctx: Ctx):
    """Pick an interview time (Feature 4 AC8, AC15). The talent can agree to share their name and email (decision Q4)."""
    user, a = _mine(ctx)
    _must_be(a, ["interview"], "This application has no interview to book.")
    if a["slot_confirmed"]:
        raise conflict("The employer has confirmed your interview time.")
    slot = next((s for s in a["slots"] if s["id"] == ctx.body.get("slotId")), None)
    if not slot:
        raise conflict("This time is no longer available. Choose another time.")
    start = parse_iso(slot["start"])
    if start is None or start < utcnow():
        raise conflict("This time has passed. Choose another time.")
    share = ctx.body.get("shareIdentity") is True
    ctx.conn.execute("UPDATE applications SET chosen_slot_id = ?, identity_shared = ? WHERE id = ?", (slot["id"], 1 if share else 0, a["id"]))
    log_event(ctx.conn, a["id"], "interview", "candidate", "Chose an interview time" + (" and shared their name and email" if share else ""))
    job = catalogue.find_job(ctx.conn, a["job_id"])
    _notify_owner(ctx, a, "slot_chosen", f"{user['alias']} chose an interview time", job["title"] if job else "")
    return candidate_view(ctx.conn, load_app(ctx.conn, a["id"]))


@route("POST", "/applications/:id/offer-reply")
def application_offer_reply(ctx: Ctx):
    """Answer an offer (Feature 4 AC10). A declined offer ends in "rejected"."""
    user, a = _mine(ctx)
    _must_be(a, ["offer"], "There is no offer to answer.")
    accept = ctx.body.get("accept") is True
    add_history(ctx.conn, a["id"], "confirmed" if accept else "rejected", "candidate", "Accepted the offer" if accept else "Declined the offer")
    _notify_owner(ctx, a, "offer_reply", f"{user['alias']} {'accepted' if accept else 'declined'} your offer")
    store.track(ctx.conn, "job_respond", "job", a["job_id"], user["id"])
    return candidate_view(ctx.conn, load_app(ctx.conn, a["id"]))


@route("POST", "/applications/:id/decline")
def application_decline(ctx: Ctx):
    """Decline an invitation from an employer (the Premium path)."""
    user, a = _mine(ctx)
    _must_be(a, ["contacted"], "You can decline only an invitation.")
    add_history(ctx.conn, a["id"], "declined", "candidate", "Declined the invitation")
    _notify_owner(ctx, a, "contact_declined", f"{user['alias']} declined your invitation")
    return candidate_view(ctx.conn, load_app(ctx.conn, a["id"]))


def read_feedback(ctx: Ctx):
    to_other = ctx.body.get("toOther", "")
    to_team = ctx.body.get("toTeam", "")
    to_other = to_other if isinstance(to_other, str) else ""
    to_team = to_team if isinstance(to_team, str) else ""
    validation({
        "toOther": "" if len(to_other) <= 1000 else "Use 1000 characters or fewer.",
        "toTeam": "" if len(to_team) <= 1000 else "Use 1000 characters or fewer.",
        "form": "" if to_other.strip() or to_team.strip() else "Write feedback in at least one box.",
    })
    # Contact details never go to the other side. The note for the Jinder team is only plain text.
    return scrub_contact(to_other).strip(), clean_text(to_team, 1000)


def save_feedback(conn: sqlite3.Connection, app_id: str, side: str, to_other: str, to_team: str) -> None:
    conn.execute(
        """INSERT INTO application_feedback (application_id, side, to_other, to_team, at) VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(application_id, side) DO UPDATE SET to_other = excluded.to_other, to_team = excluded.to_team, at = excluded.at""",
        (app_id, side, to_other, to_team, now_iso()))


@route("POST", "/applications/:id/feedback")
def application_feedback(ctx: Ctx):
    """Feedback at the final stage (Feature 4 AC11): to the other side and to the Jinder team."""
    user, a = _mine(ctx)
    _must_be(a, FINAL, "You can give feedback when the application is finished.")
    to_other, to_team = read_feedback(ctx)
    save_feedback(ctx.conn, a["id"], "candidate", to_other, to_team)
    if a["recruiter_id"] and to_other:
        _notify_owner(ctx, a, "feedback", f"{user['alias']} sent you feedback")
    return candidate_view(ctx.conn, load_app(ctx.conn, a["id"]))
