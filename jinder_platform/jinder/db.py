"""SQLite access. Each request opens its own connection, so threads never share one."""
import logging
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from . import config

log = logging.getLogger("jinder.db")

SCHEMA_VERSION = "2"
VERSION_KEY = "schema_version"       # the row in schema_info. Version 1 used the key "version".
_SCHEMA_FILE = Path(__file__).with_name("schema.sql")


def connect(path: Path = None) -> sqlite3.Connection:
    """Open a connection with foreign keys on and rows that behave like dictionaries."""
    target = path or config.DB_PATH
    conn = sqlite3.connect(str(target), timeout=10, isolation_level=None)  # we begin and commit ourselves
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 8000")
    return conn


# =====================================================================
# Schema version and the move to a new database (V2_PLAN.md, F10)
# =====================================================================
def stored_version(path: Path) -> Optional[int]:
    """The schema version of a database file.

    None   the file does not exist, is empty, or has no table (a new database)
    1      a file from the first schema (it has no version row, or the key "version")
    n      the number in the row "schema_version"
    """
    if not path.is_file() or path.stat().st_size == 0:
        return None
    conn = sqlite3.connect(str(path), timeout=10)
    try:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        if not tables:
            return None
        if "schema_info" in tables:
            for key in (VERSION_KEY, "version"):
                row = conn.execute("SELECT value FROM schema_info WHERE key = ?", (key,)).fetchone()
                if row:
                    try:
                        return int(str(row[0]).strip())
                    except ValueError:
                        return 1
        return 1
    finally:
        conn.close()


def _backup_suffix(*paths: Path) -> str:
    """The first suffix ".v1.bak", ".v1.2.bak", ".v1.3.bak" ... that is free for all these paths."""
    n = 1
    while True:
        suffix = ".v1.bak" if n == 1 else f".v1.{n}.bak"
        if not any(p.with_name(p.name + suffix).exists() for p in paths):
            return suffix
        n += 1


def _flush(path: Path) -> None:
    """Write the changes in the WAL file into the main file, so that the rename takes all the data with it."""
    conn = sqlite3.connect(str(path), timeout=10)
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        conn.close()


def move_old_database(path: Path, upload_dir: Path) -> Path:
    """Rename an old database file (and the folder of uploaded CV files that belongs to it) to a backup name.

    Nothing is deleted. The backup name is `<file name>.v1.bak`. If that name exists, the name gets a number:
    `<file name>.v1.2.bak`. The uploads folder gets the same suffix. Returns the new path of the database file.
    """
    _flush(path)
    has_uploads = upload_dir.is_dir() and any(upload_dir.iterdir())
    suffix = _backup_suffix(path, upload_dir) if has_uploads else _backup_suffix(path)
    backup = path.with_name(path.name + suffix)
    try:
        os.replace(str(path), str(backup))
    except OSError as exc:
        raise RuntimeError(
            f"The old database {path} could not be renamed. Stop every program that uses it, then start again. ({type(exc).__name__})") from exc
    for side in ("-wal", "-shm"):    # normally gone after the flush. If not, they stay with the backup file
        extra = path.with_name(path.name + side)
        if extra.exists():
            try:
                os.replace(str(extra), str(backup.with_name(backup.name + side)))
            except OSError:
                pass
    if has_uploads:
        try:
            os.replace(str(upload_dir), str(upload_dir.with_name(upload_dir.name + suffix)))
        except OSError as exc:
            os.replace(str(backup), str(path))     # put the database back. Nothing has changed
            raise RuntimeError(
                f"The folder of uploaded files {upload_dir} could not be renamed. Stop every program that uses it, then start again. "
                f"({type(exc).__name__})") from exc
    return backup


# Columns that were added to the version 2 schema after the first version-2 databases were made (during the development of version 2,
# before it was released). A database from that time gets them here. A new database has them from schema.sql.
_LATE_COLUMNS = [
    ("jobs", "salary_unit", "TEXT NOT NULL DEFAULT 'year' CHECK (salary_unit IN ('year', 'day', 'hour'))"),
    ("profiles", "specialisation", "TEXT NOT NULL DEFAULT ''"),
    ("profiles", "work_modes", "TEXT NOT NULL DEFAULT '[]'"),
    ("translated_skills", "years", "REAL CHECK (years IS NULL OR (years >= 0 AND years <= 40))"),
]


def _add_late_columns(conn: sqlite3.Connection) -> None:
    for table, column, definition in _LATE_COLUMNS:
        have = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in have:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db(path: Path = None, upload_dir: Path = None) -> Optional[Path]:
    """Create the folders and the tables. Safe to run at each start.

    A database with a schema version below SCHEMA_VERSION is NOT changed. Its file is renamed to a backup
    (see move_old_database) and a new database is made. The function returns the path of the backup, or None.
    """
    target = path or config.DB_PATH
    uploads = upload_dir or config.UPLOAD_DIR
    target.parent.mkdir(parents=True, exist_ok=True)
    backup: Optional[Path] = None
    found = stored_version(target)
    if found is not None and found < int(SCHEMA_VERSION):
        backup = move_old_database(target, uploads)
        log.warning("The database %s has the old schema version %s (the new version is %s). "
                    "It was kept as %s. A new database was made. No data was deleted.",
                    target.name, found, SCHEMA_VERSION, backup.name)
    uploads.mkdir(parents=True, exist_ok=True)
    conn = connect(target)
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(_SCHEMA_FILE.read_text(encoding="utf-8"))
        _add_late_columns(conn)
        conn.execute("INSERT OR REPLACE INTO schema_info (key, value) VALUES (?, ?)", (VERSION_KEY, SCHEMA_VERSION))
    finally:
        conn.close()
    return backup


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Run a block in one transaction. It commits on success and rolls back on an error."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")


def one(conn: sqlite3.Connection, sql: str, params: tuple = ()):
    return conn.execute(sql, params).fetchone()


def all_rows(conn: sqlite3.Connection, sql: str, params: tuple = ()):
    return conn.execute(sql, params).fetchall()


def scalar(conn: sqlite3.Connection, sql: str, params: tuple = (), default=None):
    row = conn.execute(sql, params).fetchone()
    return default if row is None else row[0]
