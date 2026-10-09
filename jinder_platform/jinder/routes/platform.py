"""Notifications, plans, charts and health (Feature 7). Charts show counts about jobs and the process, never a score on a person."""
import sqlite3
from datetime import timedelta
from collections import Counter
from typing import Any, Dict

from .. import catalogue, config, db, store
from .. import engine_bridge as eb
from ..guards import require_user
from ..http_server import Ctx, route
from ..reference import PLANS
from ..util import ApiError, as_list, iso, new_id, short_id, utcnow, validation
from .applications import FINAL
from .jobs import talent_context

STAGES = ["applied", "contacted", "review", "interview", "accepted", "offer", "confirmed", "rejected", "declined"]


# ---------- Health (public) ----------
@route("GET", "/health")
def health(ctx: Ctx):
    ctx.conn.execute("SELECT 1").fetchone()
    return {"status": "ok", "database": "ok", "formulas": eb.engine_status(), "time": iso(utcnow())}


# ---------- Notifications (in-app; "Email sent (demo)" for the events that also go to the outbox) ----------
@route("GET", "/notifications")
def notifications_list(ctx: Ctx):
    user = require_user(ctx)
    rows = ctx.conn.execute("SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC, rowid DESC LIMIT 50", (user["id"],)).fetchall()
    items = [{"id": r["id"], "type": r["type"], "title": r["title"], "body": r["body"], "link": r["link"],
              "email": bool(r["email"]), "read": bool(r["read"]), "createdAt": r["created_at"]} for r in rows]
    return {"items": items, "unread": sum(1 for n in items if not n["read"])}


@route("POST", "/notifications/read")
def notifications_read(ctx: Ctx):
    user = require_user(ctx)
    ids = [i for i in as_list(ctx.body.get("ids")) if isinstance(i, str)][:200]
    if ids:
        marks = ",".join("?" for _ in ids)
        ctx.conn.execute(f"UPDATE notifications SET read = 1 WHERE user_id = ? AND id IN ({marks})", (user["id"], *ids))
    else:
        ctx.conn.execute("UPDATE notifications SET read = 1 WHERE user_id = ?", (user["id"],))
    return {"ok": True}


# ---------- Plans (the premium switch is a demo toggle; real payments are out of scope) ----------
@route("GET", "/entitlements")
def entitlements_get(ctx: Ctx):
    return store.entitlements_of(ctx.conn, require_user(ctx))


@route("PUT", "/entitlements")
def entitlements_set(ctx: Ctx):
    user = require_user(ctx)
    if not config.ALLOW_PLAN_SWITCH:
        raise ApiError(403, "FORBIDDEN", "Plan changes are not available here. Contact Jinder to change your plan.")
    plan = ctx.body.get("plan")
    validation({"plan": "" if plan in PLANS else "Choose Basic or Premium."})
    ctx.conn.execute("INSERT INTO plans (user_id, plan) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET plan = excluded.plan", (user["id"], plan))
    return store.entitlements_of(ctx.conn, user)


# ---------- Charts (Feature 7 AC5, AC6, AC8, AC9) ----------
def _count_events(conn: sqlite3.Connection, target_type: str, target_id: str) -> Counter:
    rows = conn.execute("SELECT type, COUNT(*) AS n FROM events WHERE target_type = ? AND target_id = ? GROUP BY type", (target_type, target_id)).fetchall()
    return Counter({r["type"]: r["n"] for r in rows})


@route("GET", "/stats")
def stats(ctx: Ctx):
    user = require_user(ctx)
    conn = ctx.conn
    ent = store.plan_flags(conn, user)
    if user["role"] == "candidate":
        return _candidate_stats(conn, user, ent)
    return _recruiter_stats(conn, user, ent)


def _candidate_stats(conn: sqlite3.Connection, user: sqlite3.Row, ent: Dict[str, Any]) -> Dict[str, Any]:
    apps = conn.execute("SELECT status FROM applications WHERE candidate_id = ?", (user["id"],)).fetchall()
    by = Counter(a["status"] for a in apps)
    ev = _count_events(conn, "candidate", user["id"])
    basic = {
        "applications": len(apps),
        # "Moved to the next step": beyond Applied (Feature 7 AC9)
        "movedOn": sum(n for s, n in by.items() if s not in ("applied", "contacted")),
        "confirmed": by.get("confirmed", 0),
        "byStage": [{"stage": s, "count": by[s]} for s in STAGES if by.get(s)],
        # The talent's own profile events, as counts (Feature 7 AC6). Skips are not shown (AC7).
        "profile": {"appear": ev.get("profile_appear", 0), "watch": ev.get("profile_watch", 0), "saved": ev.get("profile_saved", 0)},
    }
    advanced = None
    profile = store.load_profile(conn, user["id"])
    if ent["advancedCharts"] and profile:
        jobs = catalogue.load_jobs(conn)
        tctx = talent_context(conn, user, jobs)
        top = catalogue.recommend(tctx, jobs, 20, set())
        # Level-aware: a skill that the job asks for and the talent does not have ("missing") or has below the asked level ("below") is a skill to learn.
        # A skill that the talent has at the asked level or above ("meets") is a skill that these jobs ask for.
        learn, demand = {}, {}
        for j in top:
            for item in j["match"]["skills"]:
                bucket = learn if item["fitStatus"] in ("missing", "below") else demand if item["fitStatus"] == "meets" else None
                if bucket is None:
                    continue
                row = bucket.setdefault(item["name"], {"skill": item["name"], "count": 0, "missing": 0, "below": 0, "need": [], "yourLevel": item["level"]})
                row["count"] += 1
                row["missing"] += item["fitStatus"] == "missing"
                row["below"] += item["fitStatus"] == "below"
                row["need"].append(item["required"] or 3)

        def pick(rows: Dict[str, Dict[str, Any]], extra: bool) -> list:
            ranked = sorted(rows.values(), key=lambda r: (-r["count"], r["skill"]))[:5]
            out = []
            for r in ranked:
                row = {"skill": r["skill"], "count": r["count"], "needLevel": round(sum(r["need"]) / len(r["need"]), 1), "yourLevel": r["yourLevel"]}
                if extra:
                    row.update({"missing": r["missing"], "below": r["below"]})
                out.append(row)
            return out

        advanced = {"basis": len(top), "gapRanking": pick(learn, True), "demandForYourSkills": pick(demand, False)}
        # The talent opened the Premium insights. This marks the benefits "Skills to learn next" and "Demand for your skills" as used.
        store.track(conn, "insights_view", "feature", "insights", user["id"])
    return {"role": "candidate", "basic": basic, "advanced": advanced, "plan": ent["plan"]}


def _recruiter_stats(conn: sqlite3.Connection, user: sqlite3.Row, ent: Dict[str, Any]) -> Dict[str, Any]:
    now = iso(utcnow())
    own = catalogue.load_jobs(conn)
    own = [j for j in own if j["ownerId"] == user["id"]]
    ids = [j["id"] for j in own]
    apps = []
    if ids:
        marks = ",".join("?" for _ in ids)
        apps = conn.execute(f"SELECT id, job_id, status, origin, chosen_slot_id, slot_confirmed FROM applications WHERE job_id IN ({marks})", ids).fetchall()
    awaiting = [a for a in apps if a["status"] in ("applied", "review") or (a["status"] == "interview" and a["chosen_slot_id"] and not a["slot_confirmed"])]
    basic = {
        "openJobs": sum(1 for j in own if j["closesAt"] >= now),
        "jobsAtTarget": sum(1 for j in own if sum(1 for a in apps if a["job_id"] == j["id"] and a["origin"] == "applied") >= (j["targetApplicants"] or 0)),
        "awaitingResponse": len(awaiting),
        "totalJobs": len(own),
    }
    advanced = None
    if ent["advancedCharts"]:
        # Counts for each job, never for each person (Feature 7 privacy NFR)
        by = Counter(a["status"] for a in apps)
        jobs_out = []
        for j in own:
            ev = _count_events(conn, "job", j["id"])
            jobs_out.append({"id": j["id"], "title": j["title"], "appear": ev.get("job_appear", 0), "watch": ev.get("job_watch", 0),
                             "save": ev.get("job_save", 0),
                             "apply": sum(1 for a in apps if a["job_id"] == j["id"] and a["origin"] == "applied")})
        advanced = {"pipeline": [{"stage": s, "count": by.get(s, 0)} for s in STAGES], "jobs": jobs_out,
                    "finished": sum(1 for a in apps if a["status"] in FINAL)}
        # The employer opened the Premium charts. This marks the benefit "Pipeline by stage and interest per job" as used.
        store.track(conn, "advanced_charts_view", "feature", "advanced_charts", user["id"])
    return {"role": "recruiter", "basic": basic, "advanced": advanced, "plan": ent["plan"]}


# ---------- Demo Application Reset (Live Hackathon Testing / Demo) ----------
@route("POST", "/demo/reset-interview")
def demo_reset_interview(ctx: Ctx):
    """Reset the demo application back to interview or review stage.
    Accepts:
      - mode: 'interview' (default: 3 future slots offered, ready for candidate selection)
              or 'review' (employer schedules 1-3 slots from scratch)
      - id: optional specific application id (defaults to demo candidate's application)
    """
    conn = ctx.conn
    body = ctx.body if isinstance(ctx.body, dict) else {}
    mode = body.get("mode", "interview")
    app_id = body.get("id")

    # Find the target application
    if app_id:
        app = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
    else:
        tal = conn.execute("SELECT id FROM users WHERE email = 'candidate@demo.jinder.app'").fetchone()
        if not tal:
            tal = conn.execute("SELECT id FROM users WHERE role = 'candidate' LIMIT 1").fetchone()
        if not tal:
            raise ApiError(404, "NOT_FOUND", "No candidate found.")
        app = conn.execute("SELECT * FROM applications WHERE candidate_id = ? ORDER BY created_at DESC LIMIT 1", (tal["id"],)).fetchone()

    if not app:
        raise ApiError(404, "NOT_FOUND", "Demo application not found.")

    aid = app["id"]
    cid = app["candidate_id"]
    job = catalogue.find_job(conn, app["job_id"])
    title = job["title"] if job else "Mid Data Engineer"
    now = utcnow()

    if mode == "review":
        conn.execute("""
            UPDATE applications
            SET status = 'review', offer_text = NULL, offer_sent_at = NULL, chosen_slot_id = NULL,
                slot_confirmed = 0, identity_shared = 0, updated_at = ?
            WHERE id = ?
        """, (iso(now), aid))
        conn.execute("DELETE FROM application_slots WHERE application_id = ?", (aid,))
        conn.execute("DELETE FROM application_history WHERE application_id = ?", (aid,))
        conn.execute("INSERT INTO application_history (application_id, status, at, actor, note) VALUES (?, 'applied', ?, 'candidate', '')",
                     (aid, iso(now - timedelta(days=5))))
        conn.execute("INSERT INTO application_history (application_id, status, at, actor, note) VALUES (?, 'review', ?, 'recruiter', '')",
                     (aid, iso(now - timedelta(days=3))))
        emp = store.get_user(conn, app["recruiter_id"])
        if emp:
            store.notify(conn, emp["id"], "new_application", f"New application for {title}", "Teal Heron applied.", f"/review/{aid}")
        msg = "Demo application reset to Review stage. Employer can now schedule interview slots from scratch."
    else:
        conn.execute("""
            UPDATE applications
            SET status = 'interview', offer_text = NULL, offer_sent_at = NULL, chosen_slot_id = NULL,
                slot_confirmed = 0, identity_shared = 0, updated_at = ?
            WHERE id = ?
        """, (iso(now), aid))
        conn.execute("DELETE FROM application_slots WHERE application_id = ?", (aid,))
        future_slots = [
            (short_id(8), iso((now + timedelta(days=d + 2)).replace(hour=10 + d, minute=0, second=0, microsecond=0)), d)
            for d in (1, 2, 3)
        ]
        for sid, start_iso, pos in future_slots:
            conn.execute("INSERT INTO application_slots (id, application_id, start, position) VALUES (?, ?, ?, ?)",
                         (sid, aid, start_iso, pos))
        conn.execute("DELETE FROM application_history WHERE application_id = ?", (aid,))
        conn.execute("INSERT INTO application_history (application_id, status, at, actor, note) VALUES (?, 'applied', ?, 'candidate', '')",
                     (aid, iso(now - timedelta(days=5))))
        conn.execute("INSERT INTO application_history (application_id, status, at, actor, note) VALUES (?, 'review', ?, 'recruiter', '')",
                     (aid, iso(now - timedelta(days=4))))
        conn.execute("INSERT INTO application_history (application_id, status, at, actor, note) VALUES (?, 'interview', ?, 'recruiter', 'Offered 3 interview times')",
                     (aid, iso(now - timedelta(days=2))))
        store.notify(conn, cid, "interview_slots", f"Interview times for {title}", "Choose a time that works for you.", f"/applications/{aid}")
        msg = "Demo application reset to Interview stage. 3 interview slots are ready for candidate selection."

    return {"ok": True, "message": msg, "applicationId": aid, "status": mode}
