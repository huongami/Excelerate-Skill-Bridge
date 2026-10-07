"""The email outbox (Feature 7 AC2, AC13).

An event writes a message to the outbox in the same transaction. This worker sends the message later.
A failed email never blocks the action that caused it. It is tried again, up to 5 times.
Without SMTP settings, the worker only records the message ("recorded"): nothing leaves the server.
The log has message ids only. It never has an address or a text (AI_Rule Rule 5, item 6).
"""
import logging
import smtplib
import ssl
import threading
from datetime import timedelta
from email.message import EmailMessage

from . import config, db
from .util import iso, now_iso, utcnow

log = logging.getLogger("jinder.mailer")
MAX_ATTEMPTS = 5
_stop = threading.Event()


def _send_smtp(to_addr: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"] = config.SMTP_FROM
    msg["To"] = to_addr
    msg["Subject"] = " ".join(subject.split())   # one line: a line break in a header would be an error (or an attack)
    msg.set_content(body)
    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15) as smtp:
        smtp.starttls(context=ssl.create_default_context())   # the server certificate is checked
        if config.SMTP_USER:
            smtp.login(config.SMTP_USER, config.SMTP_PASSWORD)
        smtp.send_message(msg)


def process_outbox(limit: int = 20) -> int:
    """Handle the pending messages that are due. Returns how many were handled."""
    conn = db.connect()
    handled = 0
    try:
        rows = conn.execute(
            "SELECT o.id, o.subject, o.body, o.attempts, u.email FROM email_outbox o JOIN users u ON u.id = o.user_id "
            "WHERE o.status = 'pending' AND (o.next_attempt_at IS NULL OR o.next_attempt_at <= ?) ORDER BY o.created_at LIMIT ?",
            (now_iso(), limit)).fetchall()
        for r in rows:
            handled += 1
            if not config.SMTP_HOST:
                conn.execute("UPDATE email_outbox SET status = 'recorded', attempts = attempts + 1 WHERE id = ?", (r["id"],))
                continue
            try:
                _send_smtp(r["email"], r["subject"], r["body"])
                conn.execute("UPDATE email_outbox SET status = 'sent', attempts = attempts + 1 WHERE id = ?", (r["id"],))
            except Exception as exc:  # noqa: BLE001 - any failure means "try again later"
                attempts = r["attempts"] + 1
                status = "failed" if attempts >= MAX_ATTEMPTS else "pending"
                retry = iso(utcnow() + timedelta(minutes=2 ** attempts))
                conn.execute("UPDATE email_outbox SET status = ?, attempts = ?, next_attempt_at = ? WHERE id = ?", (status, attempts, retry, r["id"]))
                log.warning("Email %s failed (%s). Attempt %d.", r["id"], type(exc).__name__, attempts)
    finally:
        conn.close()
    return handled


def _loop(interval: float) -> None:
    while not _stop.wait(interval):
        try:
            process_outbox()
        except Exception:  # noqa: BLE001
            log.exception("The outbox worker failed")


def start_worker(interval: float = 20.0) -> threading.Thread:
    t = threading.Thread(target=_loop, args=(interval,), name="jinder-outbox", daemon=True)
    t.start()
    return t


def stop_worker() -> None:
    _stop.set()
