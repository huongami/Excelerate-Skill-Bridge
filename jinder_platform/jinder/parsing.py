"""Reading uploaded files in the background (a CV for a talent, a job description for an employer).

The upload request returns at once with status "parsing". The browser then asks for the result (polling).
A file that cannot be read gives status "failed" and a plain message. No file content is written to the log.
"""
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from . import catalogue, config, db
from .cv_parser import parse_cv
from .jd_parser import parse_jd
from .textextract import UnreadableFile, extract_text
from .util import jdump, new_id, now_iso

log = logging.getLogger("jinder.parsing")
_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="jinder-parse")

CV_FAILED = "We couldn't read this CV. Try a different file, or enter your details yourself."
JD_FAILED = "We couldn't read this file. Try a different file, or fill in the form yourself."


def upload_path(stored_name: str) -> Path:
    """The path of a stored upload. The name is made by the server, so it has no folder part."""
    return (config.UPLOAD_DIR / Path(stored_name).name)


def store_upload(data: bytes, ext: str) -> str:
    """Write an upload into the private folder. Return the stored name. Nothing in the folder is ever served."""
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored = f"{new_id()}{ext}"
    path = upload_path(stored)
    path.write_bytes(data)
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return stored


def delete_upload(stored_name: str) -> None:
    """Delete a stored file. On Windows a file that is being read cannot be deleted at once, so try again a few times."""
    path = upload_path(stored_name)
    for attempt in range(8):
        try:
            path.unlink()
            return
        except FileNotFoundError:
            return
        except OSError:
            time.sleep(0.05 * (attempt + 1))
    log.warning("A stored file could not be deleted. The start-up clean-up will try again.")


def create_parse(conn, kind: str, user_id: str, file_name: str, stored_name: str) -> str:
    parse_id = new_id()
    conn.execute(
        "INSERT INTO parses (id, kind, user_id, file_name, stored_name, status, created_at) VALUES (?, ?, ?, ?, ?, 'parsing', ?)",
        (parse_id, kind, user_id, file_name, stored_name, now_iso()))
    return parse_id


def submit(parse_id: str) -> None:
    """Start reading after the request has committed."""
    _pool.submit(_run, parse_id)


def _finish(parse_id: str, status: str, result: Optional[dict] = None, error: Optional[str] = None) -> None:
    conn = db.connect()
    try:
        conn.execute("UPDATE parses SET status = ?, result = ?, error = ?, finished_at = ? WHERE id = ?",
                     (status, jdump(result) if result is not None else None, error, now_iso(), parse_id))
    finally:
        conn.close()


def _clean_jd(result: dict) -> dict:
    """The keys of version 2 of a job (level, years, work mode, skill levels, certifications ...) that the reader returned go through
    the same checks as the job form. A value that is not valid is left out. The other fields stay as the reader gave them."""
    fields = catalogue.clean_import_fields(dict(result.get("fields") or {}))
    detected = [k for k in result.get("detected", []) if k in fields]
    detected += [k for k in catalogue.JOB_EXTRA_KEYS if k in fields and k not in detected]
    return {**result, "fields": fields, "detected": detected}


def _run(parse_id: str) -> None:
    conn = db.connect()
    try:
        row = conn.execute("SELECT kind, stored_name FROM parses WHERE id = ?", (parse_id,)).fetchone()
    finally:
        conn.close()
    if not row:
        return
    kind = row["kind"]
    failed = CV_FAILED if kind == "cv" else JD_FAILED
    try:
        data = upload_path(row["stored_name"]).read_bytes()
        text = extract_text(data)
        result = parse_cv(text) if kind == "cv" else _clean_jd(parse_jd(text))
        _finish(parse_id, "done", result)
    except (UnreadableFile, FileNotFoundError):
        # An unreadable file, or a file that the user replaced before we read it
        _finish(parse_id, "failed", error=failed)
    except Exception:  # noqa: BLE001 - never leave a parse in the "parsing" state
        log.exception("Reading a file failed")
        _finish(parse_id, "failed", error=failed)
    finally:
        # A job description file is read once. The file is not needed afterwards, also when the reading failed.
        if kind == "jd":
            delete_upload(row["stored_name"])


def cleanup(conn) -> None:
    """At start-up: end the readings that a restart stopped, forget old job description results, and delete files that no row uses."""
    from datetime import timedelta
    from .util import iso, utcnow
    conn.execute("UPDATE parses SET status = 'failed', error = ?, finished_at = ? WHERE status = 'parsing'", (CV_FAILED, now_iso()))
    day_ago = iso(utcnow() - timedelta(days=1))
    conn.execute("DELETE FROM parses WHERE kind = 'jd' AND created_at < ?", (day_ago,))
    used = {r[0] for r in conn.execute("SELECT stored_name FROM cv_files UNION SELECT stored_name FROM parses")}
    if config.UPLOAD_DIR.is_dir():
        cutoff = utcnow().timestamp() - 86400
        for f in config.UPLOAD_DIR.iterdir():
            try:
                if f.is_file() and f.name not in used and f.stat().st_mtime < cutoff:
                    f.unlink()
            except OSError:
                pass
