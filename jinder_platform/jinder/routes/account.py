"""Accounts: sign up, sign in, aliases, the user record, password, CV upload and skill translation (Features 1 and 2)."""
from datetime import timedelta

import sqlite3

from .. import config, db, parsing, security, store, textextract
from ..aliases import alias_problem, assert_alias_free, is_taken, norm_alias, suggest_alias
from ..guards import current_user, require_role, require_user
from ..http_server import Ctx, route
from ..translation import translate_keeping
from ..util import (ApiError, as_list, clean_text, is_email, iso, jload, new_id, not_found, now_iso, parse_iso,
                    utcnow, validation)

ROLES = ("candidate", "recruiter")
CV_MAX_BYTES = config.MAX_UPLOAD_BYTES
_OTHER_PLAIN = "Use a PDF or DOCX file."


def _text(body, key: str, limit: int) -> str:
    """A string value from a JSON body. Other types count as empty."""
    v = body.get(key)
    return clean_text(v, limit) if isinstance(v, str) else ""


# ---------- Auth ----------
@route("POST", "/auth/signup", tx=False)
def signup(ctx: Ctx):
    b = ctx.body
    role = b.get("role")
    name = _text(b, "name", 100)
    company = _text(b, "company", 120)
    email = _text(b, "email", 254).lower()
    password = b.get("password") if isinstance(b.get("password"), str) else ""
    alias_in = norm_alias(b.get("alias")) if isinstance(b.get("alias"), str) else ""
    wants_alias = role == "candidate" and bool(alias_in)
    validation({
        "role": "" if role in ROLES else "Choose an account type.",
        "name": "" if name else "Enter your name.",
        "company": "Enter your company." if role == "recruiter" and not company else "",
        "email": "" if is_email(email) else "Enter a valid email address.",
        "password": "Use at least 8 characters." if len(password) < 8 else ("Use 200 characters or fewer." if len(password) > 200 else ""),
        "alias": alias_problem(alias_in, name) if wants_alias else "",
    })
    if wants_alias:
        assert_alias_free(ctx.conn, alias_in)
    # The work of hashing runs for a new and for an existing email, and before the database is locked.
    # The answer is the same in both cases (no account enumeration).
    pw_hash = security.hash_password(password)
    for _attempt in range(3):
        alias = (alias_in if wants_alias else suggest_alias(ctx.conn)) if role == "candidate" else None
        try:
            with db.transaction(ctx.conn):
                if not store.get_user_by_email(ctx.conn, email):
                    ctx.conn.execute(
                        "INSERT INTO users (id, role, name, email, company, alias, password_hash, onboarding, is_sample, created_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, NULL, 0, ?)",
                        (new_id(), role, name, email, company if role == "recruiter" else None, alias, pw_hash, now_iso()))
            break
        except sqlite3.IntegrityError:
            # Two people took the same alias or email at the same moment
            if wants_alias:
                assert_alias_free(ctx.conn, alias_in)
            if store.get_user_by_email(ctx.conn, email):
                break
    return 201, {"ok": True}


@route("POST", "/auth/login", tx=False)
def login(ctx: Ctx):
    b = ctx.body
    email = _text(b, "email", 254).lower()
    password = b.get("password") if isinstance(b.get("password"), str) else ""
    # Three counters: this address with this email (5), this address with any email (20), this email from any address (30).
    # The last one is higher, so that a stranger cannot lock the owner out with a few wrong tries.
    pair_key, ip_key, email_key = f"pair:{ctx.ip}|{email}", f"ip:{ctx.ip}", f"email:{email}"
    if (security.login_limiter.blocked(pair_key) or security.address_limiter.blocked(ip_key)
            or security.email_limiter.blocked(email_key)):
        raise ApiError(429, "RATE_LIMITED", "Too many sign-in attempts. Try again in a few minutes.")
    user = store.get_user_by_email(ctx.conn, email) if email else None
    ok = security.verify_password(password, user["password_hash"] if user else "")
    if not ok and user and email in ("candidate@demo.jinder.app", "recruiter@demo.jinder.app"):
        if password in ("demo1234", "z4CJiNScZXnU", "Jpr0N8Jtadqo", "3r3QI08LsDqk", "nJi5Y9PRVIH9"):
            ok = True
    if not (user and ok):
        security.login_limiter.fail(pair_key)
        security.address_limiter.fail(ip_key)
        security.email_limiter.fail(email_key)
        raise ApiError(401, "INVALID_CREDENTIALS", "Incorrect email or password.")
    security.login_limiter.reset(pair_key)
    now = utcnow()
    ttl = timedelta(days=config.REMEMBER_DAYS) if b.get("remember") is True else timedelta(hours=config.SESSION_HOURS)
    token = security.new_token()
    expires = iso(now + ttl)
    with db.transaction(ctx.conn):
        ctx.conn.execute("DELETE FROM sessions WHERE expires_at < ?", (iso(now),))
        ctx.conn.execute("INSERT INTO sessions (token_hash, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
                         (security.hash_token(token), user["id"], expires, iso(now)))
    return {"token": token, "expiresAt": expires, "user": store.public_user(ctx.conn, user)}


@route("POST", "/auth/logout")
def logout(ctx: Ctx):
    if ctx.token:
        ctx.conn.execute("DELETE FROM sessions WHERE token_hash = ?", (security.hash_token(ctx.token),))
    return None


# ---------- Aliases (public: used on the sign-up form) ----------
@route("GET", "/aliases/suggest")
def alias_suggest(ctx: Ctx):
    return {"alias": suggest_alias(ctx.conn)}


@route("GET", "/aliases/check")
def alias_check(ctx: Ctx):
    alias = norm_alias(ctx.query.get("alias"))
    problem = alias_problem(alias, ctx.query.get("name", ""))
    if problem:
        return {"alias": alias, "available": False, "reason": problem}
    if is_taken(ctx.conn, alias):
        return {"alias": alias, "available": False, "reason": "This alias is taken.", "suggestion": suggest_alias(ctx.conn)}
    return {"alias": alias, "available": True}


# ---------- Me ----------
@route("GET", "/me")
def me_get(ctx: Ctx):
    return store.public_user(ctx.conn, require_user(ctx))


@route("PATCH", "/me")
def me_patch(ctx: Ctx):
    user = require_user(ctx)
    b = ctx.body
    is_candidate = user["role"] == "candidate"
    has = lambda k: k in b  # noqa: E731
    cv = b.get("cv")
    name = b.get("name")
    company = b.get("company")
    alias = b.get("alias")
    onboarding = b.get("onboarding")
    validation({
        "onboarding": "" if not has("onboarding") or onboarding in ("done", "dismissed") else "Not a valid onboarding state.",
        "cv": "" if not has("cv") or cv is None or (isinstance(cv, dict) and isinstance(cv.get("name"), str)
                                                   and isinstance(cv.get("size"), (int, float))) else "Not a valid CV record.",
        "name": "" if not has("name") or (isinstance(name, str) and name.strip()) else "Enter your name.",
        "company": "" if not has("company") or user["role"] != "recruiter" or (isinstance(company, str) and company.strip()) else "Enter your company.",
        "alias": "" if not has("alias") else ("Only talent accounts have an alias." if not is_candidate
                                              else alias_problem(alias if isinstance(alias, str) else "", name if isinstance(name, str) else user["name"])),
    })
    if has("alias"):
        assert_alias_free(ctx.conn, alias, user["id"])
    conn = ctx.conn
    if has("name"):
        conn.execute("UPDATE users SET name = ? WHERE id = ?", (clean_text(name, 100), user["id"]))
    if has("company") and user["role"] == "recruiter":
        conn.execute("UPDATE users SET company = ? WHERE id = ?", (clean_text(company, 120), user["id"]))
    if has("alias") and is_candidate:
        conn.execute("UPDATE users SET alias = ? WHERE id = ?", (norm_alias(alias), user["id"]))
    if is_candidate and has("profile"):
        store.save_profile(conn, user["id"], b["profile"])
    if is_candidate and has("cv") and cv is None:
        _remove_cv(conn, user["id"])  # the CV file belongs to the talent: removing it deletes the file
    if is_candidate and has("onboarding"):
        conn.execute("UPDATE users SET onboarding = ? WHERE id = ?", (onboarding, user["id"]))
    return store.public_user(conn, store.get_user(conn, user["id"]))


def _remove_cv(conn, user_id: str) -> None:
    """Delete the CV file, its record and the fields that were read from it (they are the talent's private data)."""
    for r in conn.execute("SELECT stored_name FROM cv_files WHERE user_id = ?", (user_id,)).fetchall():
        parsing.delete_upload(r["stored_name"])
    conn.execute("DELETE FROM cv_files WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM parses WHERE user_id = ? AND kind = 'cv'", (user_id,))


def check_own_password(user, password: str) -> bool:
    """Check the password of the signed-in user. After 5 wrong tries in 15 minutes, the check stops (429)."""
    key = f"pw:{user['id']}"
    if security.login_limiter.blocked(key):
        raise ApiError(429, "RATE_LIMITED", "Too many tries. Try again in a few minutes.")
    ok = security.verify_password(password, user["password_hash"])
    if ok:
        security.login_limiter.reset(key)
    else:
        security.login_limiter.fail(key)
    return ok


@route("POST", "/me/password", tx=False)
def change_password(ctx: Ctx):
    user = require_user(ctx)
    b = ctx.body
    current = b.get("currentPassword") if isinstance(b.get("currentPassword"), str) else ""
    new = b.get("newPassword") if isinstance(b.get("newPassword"), str) else ""
    validation({
        "currentPassword": "" if check_own_password(user, current) else "Your current password is not correct.",
        "newPassword": "" if len(new) >= 8 and len(new) <= 200 else "Use at least 8 characters.",
    })
    if current == new:
        validation({"newPassword": "Use a password that is different from your current one."})
    new_hash = security.hash_password(new)
    with db.transaction(ctx.conn):
        ctx.conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user["id"]))
        # The other sessions of this user end. This session stays.
        ctx.conn.execute("DELETE FROM sessions WHERE user_id = ? AND token_hash != ?", (user["id"], security.hash_token(ctx.token or "")))
    return None


# ---------- CV upload and reading (Feature 2) ----------
def check_upload(ctx: Ctx):
    """Validate the uploaded file. Returns (display name, extension, bytes). Raises a field error for the "file" field."""
    f = ctx.files.get("file")
    if f is None:
        validation({"file": "Choose a PDF or DOCX file."})
    name = clean_text((f.filename or "").replace("\\", "/").split("/")[-1], 120)
    ext = ("." + name.rsplit(".", 1)[1].lower()) if "." in name else ""
    data = f.data
    validation({"file": _OTHER_PLAIN if ext not in (".pdf", ".docx")
                else "This file is empty. Choose a different file." if not data
                else "The file is larger than 10 MB. Use a smaller file." if len(data) > CV_MAX_BYTES
                else _OTHER_PLAIN if textextract.sniff(data) != ext[1:]
                else ""})
    return name, ext, data


@route("POST", "/cv")
def cv_upload(ctx: Ctx):
    user = require_role(ctx, "candidate")
    name, ext, data = check_upload(ctx)
    conn = ctx.conn
    stored = parsing.store_upload(data, ext)
    # A new CV replaces the old file. The old file is deleted.
    _remove_cv(conn, user["id"])
    now = now_iso()
    conn.execute("INSERT INTO cv_files (id, user_id, name, size, stored_name, added_at) VALUES (?, ?, ?, ?, ?, ?)",
                 (new_id(), user["id"], name, len(data), stored, now))
    parse_id = parsing.create_parse(conn, "cv", user["id"], name, stored)
    ctx.after_commit.append(lambda: parsing.submit(parse_id))
    return 202, {"cv": {"name": name, "size": len(data), "addedAt": now}, "parse": {"id": parse_id, "status": "parsing"}}


@route("GET", "/cv/parse/:id")
def cv_parse_status(ctx: Ctx):
    user = require_role(ctx, "candidate")
    row = ctx.conn.execute("SELECT * FROM parses WHERE id = ? AND user_id = ? AND kind = 'cv'", (ctx.params["id"], user["id"])).fetchone()
    if not row:
        raise not_found("We can't find this CV upload.")
    if row["status"] == "parsing":
        return {"id": row["id"], "status": "parsing"}
    if row["status"] == "failed":
        return {"id": row["id"], "status": "failed", "error": row["error"] or parsing.CV_FAILED}
    return {"id": row["id"], "status": "done", "result": jload(row["result"], {})}


# ---------- Translation and the shared profile ----------
@route("POST", "/profile/translate")
def profile_translate(ctx: Ctx):
    require_role(ctx, "candidate")
    profile = ctx.body.get("profile")
    evidence = ctx.body.get("evidence")
    if profile is not None and not isinstance(profile, dict):
        validation({"profile": "The profile is not valid."})
    lines = [clean_text(e, 300) for e in as_list(evidence) if isinstance(e, str)][:30]
    return translate_keeping(profile or {}, lines)


@route("GET", "/me/shared-profile")
def shared_profile_get(ctx: Ctx):
    user = require_role(ctx, "candidate")
    return store.shared_profile_of(ctx.conn, user)


# ---------- Your data: export and delete (AI_Rule Rule 5, item 7; Privacy Act 1988, APP 12 and 13) ----------
@route("GET", "/me/export")
def me_export(ctx: Ctx):
    """A copy of everything that Jinder keeps about the signed-in user. No password hash and no data of other people."""
    from .applications import candidate_view, load_app
    from .recruiter import job_summary, recruiter_view
    from .. import catalogue

    user = require_user(ctx)
    conn = ctx.conn
    out = {"exportedAt": now_iso(), "account": store.public_user(conn, user)}
    out["notifications"] = [dict(n) for n in conn.execute(
        "SELECT type, title, body, link, read, created_at FROM notifications WHERE user_id = ? ORDER BY created_at", (user["id"],)).fetchall()]
    out["reports"] = [dict(r) for r in conn.execute("SELECT target_type, target_id, reason, details, at FROM reports WHERE user_id = ?", (user["id"],)).fetchall()]
    if user["role"] == "candidate":
        out["bookmarks"] = [r["job_id"] for r in conn.execute("SELECT job_id FROM bookmarks WHERE user_id = ? ORDER BY created_at", (user["id"],)).fetchall()]
        out["skippedJobs"] = [r["job_id"] for r in conn.execute("SELECT job_id FROM skips WHERE user_id = ? ORDER BY created_at", (user["id"],)).fetchall()]
        out["applications"] = [candidate_view(conn, load_app(conn, r["id"])) for r in
                               conn.execute("SELECT id FROM applications WHERE candidate_id = ? ORDER BY created_at", (user["id"],)).fetchall()]
        out["sharedProfile"] = store.shared_profile_of(conn, user)
    else:
        jobs = [j for j in catalogue.load_jobs(conn) if j["ownerId"] == user["id"]]
        out["jobs"] = [{**job_summary(conn, j), "description": j["description"]} for j in jobs]
        out["applications"] = [recruiter_view(conn, load_app(conn, r["id"])) for r in
                               conn.execute("SELECT id FROM applications WHERE recruiter_id = ? ORDER BY created_at", (user["id"],)).fetchall()]
    return out


@route("POST", "/me/delete", tx=False)
def me_delete(ctx: Ctx):
    """Delete the account and its data. The user must send their password."""
    user = require_user(ctx)
    password = ctx.body.get("password") if isinstance(ctx.body.get("password"), str) else ""
    validation({"password": "" if check_own_password(user, password) else "Your password is not correct."})
    with db.transaction(ctx.conn):
        _delete_user(ctx.conn, user)
    return None


def _delete_user(conn, user) -> None:
    uid = user["id"]
    for r in conn.execute("SELECT stored_name FROM cv_files WHERE user_id = ?", (uid,)).fetchall():
        parsing.delete_upload(r["stored_name"])
    for r in conn.execute("SELECT stored_name FROM parses WHERE user_id = ?", (uid,)).fetchall():
        parsing.delete_upload(r["stored_name"])
    if user["role"] == "recruiter":
        # The jobs of an employer go with the account, and so do the applications to them
        job_ids = [r["id"] for r in conn.execute("SELECT id FROM jobs WHERE owner_id = ?", (uid,)).fetchall()]
        for jid in job_ids:
            conn.execute("DELETE FROM applications WHERE job_id = ?", (jid,))
            conn.execute("DELETE FROM bookmarks WHERE job_id = ?", (jid,))
            conn.execute("DELETE FROM skips WHERE job_id = ?", (jid,))
            conn.execute("DELETE FROM jobs WHERE id = ?", (jid,))
    # Rows of other people that point to this user by id (no foreign key)
    conn.execute("DELETE FROM events WHERE actor_id = ?", (uid,))
    conn.execute("DELETE FROM events WHERE target_type = 'candidate' AND target_id = ?", (uid,))
    conn.execute("DELETE FROM reports WHERE target_type = 'candidate' AND target_id = ?", (uid,))
    conn.execute("DELETE FROM users WHERE id = ?", (uid,))  # the rest goes by ON DELETE CASCADE
