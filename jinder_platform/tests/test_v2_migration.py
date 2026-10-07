"""Schema version 2, and the move of an old (version 1) database to a backup file (V2_PLAN.md, section 4.5 and F10).

These tests use their own temporary folders. They never touch the database of the test server.
"""
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

import helpers as H
from jinder import db

# A small part of the first schema (version 1): enough to be a real old database with data in it
V1_SCHEMA = """
CREATE TABLE schema_info (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE users (id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE);
CREATE TABLE jobs (id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '');
"""


def make_v1(path: Path, version_key="version", with_version=True, wal=True):
    """An old database file with 2 users and 1 job."""
    conn = sqlite3.connect(str(path))
    try:
        if wal:
            conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(V1_SCHEMA)
        if with_version:
            conn.execute("INSERT INTO schema_info (key, value) VALUES (?, '1')", (version_key,))
        conn.executemany("INSERT INTO users (id, name, email) VALUES (?, ?, ?)",
                         [("u1", "Old Person One", "one@example.test"), ("u2", "Old Person Two", "two@example.test")])
        conn.execute("INSERT INTO jobs (id, title, description) VALUES ('j1', 'Old job', ?)", ("x" * 3000,))
        conn.commit()
    finally:
        conn.close()


def count(path: Path, table: str) -> int:
    conn = sqlite3.connect(str(path))
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        conn.close()


def columns(path: Path, table: str):
    conn = sqlite3.connect(str(path))
    try:
        return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
    finally:
        conn.close()


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="jinder-migrate-"))
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.path = self.dir / "jinder.db"
        self.uploads = self.dir / "uploads"

    def wipe_current(self):
        for suffix in ("", "-wal", "-shm"):
            f = self.path.with_name(self.path.name + suffix)
            if f.exists():
                f.unlink()

    def test_an_old_database_is_kept_as_a_backup_and_a_new_one_is_made(self):
        make_v1(self.path)
        self.uploads.mkdir()
        (self.uploads / "cv-old.pdf").write_bytes(b"%PDF-1.4 old cv")
        backup = db.init_db(self.path, self.uploads)
        # the old file is a backup with all its data
        self.assertEqual(backup, self.dir / "jinder.db.v1.bak")
        self.assertTrue(backup.is_file())
        self.assertEqual(db.stored_version(backup), 1)
        self.assertEqual((count(backup, "users"), count(backup, "jobs")), (2, 1))
        conn = sqlite3.connect(str(backup))
        self.assertEqual(len(conn.execute("SELECT description FROM jobs").fetchone()[0]), 3000)
        conn.close()
        # the new file is a version 2 database with the real schema and no rows
        self.assertEqual(db.stored_version(self.path), 2)
        conn = sqlite3.connect(str(self.path))
        self.assertEqual(conn.execute("SELECT value FROM schema_info WHERE key = 'schema_version'").fetchone()[0], "2")
        conn.close()
        self.assertIn("role", columns(self.path, "users"))
        self.assertEqual(count(self.path, "users"), 0)
        # the uploaded files belong to the old data. They are kept with it, and the new start does not delete them.
        self.assertEqual((self.dir / "uploads.v1.bak" / "cv-old.pdf").read_bytes(), b"%PDF-1.4 old cv")
        self.assertTrue(self.uploads.is_dir())
        self.assertEqual(list(self.uploads.iterdir()), [])

    def test_a_current_database_is_not_moved(self):
        self.assertIsNone(db.init_db(self.path, self.uploads))           # a new database
        conn = db.connect(self.path)
        conn.execute("INSERT INTO users (id, role, name, email, password_hash, created_at) VALUES ('u1', 'candidate', 'A', 'a@example.test', '!', 'now')")
        conn.close()
        self.assertIsNone(db.init_db(self.path, self.uploads))           # the second start
        self.assertEqual(count(self.path, "users"), 1)
        self.assertEqual([f.name for f in self.dir.iterdir() if f.name.endswith(".bak")], [])

    def test_the_backup_name_gets_a_number_when_the_name_exists(self):
        names = []
        for _ in range(3):
            make_v1(self.path)
            names.append(db.init_db(self.path, self.uploads).name)
            self.wipe_current()
        self.assertEqual(names, ["jinder.db.v1.bak", "jinder.db.v1.2.bak", "jinder.db.v1.3.bak"])
        for name in names:
            self.assertEqual(count(self.dir / name, "users"), 2)   # none was overwritten

    def test_a_file_with_no_version_row_counts_as_version_1(self):
        make_v1(self.path, with_version=False)
        self.assertEqual(db.stored_version(self.path), 1)
        self.assertIsNotNone(db.init_db(self.path, self.uploads))
        self.wipe_current()
        make_v1(self.path, version_key="schema_version", with_version=True)     # the key of version 2 with the value 1 is still old
        self.assertEqual(db.stored_version(self.path), 1)

    def test_a_missing_or_empty_file_is_a_new_database(self):
        self.assertIsNone(db.stored_version(self.path))
        self.path.write_bytes(b"")
        self.assertIsNone(db.stored_version(self.path))
        self.assertIsNone(db.init_db(self.path, self.uploads))
        self.assertEqual(db.stored_version(self.path), 2)
        self.assertEqual([f.name for f in self.dir.iterdir() if f.name.endswith(".bak")], [])

    def test_a_database_with_a_newer_version_is_left_alone(self):
        db.init_db(self.path, self.uploads)
        conn = sqlite3.connect(str(self.path))
        conn.execute("UPDATE schema_info SET value = '9' WHERE key = 'schema_version'")
        conn.commit()
        conn.close()
        self.assertIsNone(db.init_db(self.path, self.uploads))
        self.assertEqual([f.name for f in self.dir.iterdir() if f.name.endswith(".bak")], [])

    def test_uploads_without_files_are_not_renamed(self):
        make_v1(self.path)
        self.uploads.mkdir()
        db.init_db(self.path, self.uploads)
        self.assertFalse((self.dir / "uploads.v1.bak").exists())
        self.assertTrue(self.uploads.is_dir())


class SchemaVersion2Tests(unittest.TestCase):
    """The database of the test server has the new columns (V2_PLAN.md, section 4.5)."""

    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()

    def cols(self, table):
        return {r["name"] for r in self.p.conn().execute(f"PRAGMA table_info({table})").fetchall()}

    def test_the_version_row(self):
        row = self.p.conn().execute("SELECT value FROM schema_info WHERE key = 'schema_version'").fetchone()
        self.assertEqual(row["value"], "2")

    def test_the_new_columns(self):
        self.assertTrue({"level", "years_exact", "certifications", "awards"} <= self.cols("profiles"))
        self.assertIn("level", self.cols("translated_skills"))
        self.assertTrue({"level", "specialisation", "min_years", "max_years", "work_mode", "education_min",
                         "certs_required", "certs_preferred", "awards_preferred"} <= self.cols("jobs"))
        self.assertTrue({"level", "must"} <= self.cols("job_skills"))

    def test_the_database_refuses_a_bad_level(self):
        c = self.p.conn()
        with self.assertRaises(sqlite3.IntegrityError):
            c.execute("UPDATE jobs SET level = 'Boss' WHERE id = (SELECT id FROM jobs LIMIT 1)")
        with self.assertRaises(sqlite3.IntegrityError):
            c.execute("UPDATE jobs SET work_mode = 'Space' WHERE id = (SELECT id FROM jobs LIMIT 1)")
        with self.assertRaises(sqlite3.IntegrityError):
            c.execute("UPDATE job_skills SET level = 6 WHERE job_id = (SELECT job_id FROM job_skills LIMIT 1)")

    def test_the_new_catalogue_has_the_values_of_version_2(self):
        c = self.p.conn()
        row = c.execute("SELECT COUNT(*) AS n, COUNT(level) AS levels, COUNT(min_years) AS years, COUNT(work_mode) AS modes, "
                        "SUM(salary_unit = 'day') AS days FROM jobs WHERE owner_id IS NULL").fetchone()
        self.assertEqual((row["n"], row["levels"], row["years"], row["modes"], row["days"]), (50, 50, 50, 50, 6))

    def test_a_database_of_the_first_version_2_gets_the_late_columns(self):
        # a database that was made before salary_unit, specialisation, work_modes and the years of a skill existed
        import tempfile
        from pathlib import Path
        folder = Path(tempfile.mkdtemp(prefix="jinder-late-"))
        self.addCleanup(shutil.rmtree, folder, True)
        path = folder / "jinder.db"
        import re
        text = db._SCHEMA_FILE.read_text(encoding="utf-8")
        text = re.sub(r"  salary_unit .*\n", "", text)
        text = re.sub(r"  years         REAL CHECK.*\n", "", text)
        text = re.sub(r"(awards            TEXT NOT NULL DEFAULT '\[\]'),[^\n]*\n  specialisation[^\n]*\n  work_modes[^\n]*\n\);", r"\1\n);", text)
        conn = sqlite3.connect(str(path))
        conn.executescript(text)
        conn.execute("INSERT INTO schema_info (key, value) VALUES ('schema_version', '2')")
        conn.commit()
        self.assertNotIn("salary_unit", {r[1] for r in conn.execute("PRAGMA table_info(jobs)")})
        self.assertNotIn("work_modes", {r[1] for r in conn.execute("PRAGMA table_info(profiles)")})
        conn.close()
        self.assertIsNone(db.init_db(path, folder / "uploads"))              # version 2: it is not moved
        self.assertIn("salary_unit", columns(path, "jobs"))
        self.assertTrue({"specialisation", "work_modes"} <= columns(path, "profiles"))
        self.assertIn("years", columns(path, "translated_skills"))


if __name__ == "__main__":
    unittest.main()
