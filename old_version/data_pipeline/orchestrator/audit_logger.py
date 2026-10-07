"""
On-Premises Pipeline Audit Logger (SQLite-backed)
Provides an immutable, append-only ledger for all pipeline executions,
task statuses, data quality contract validations, and system logs.
"""

import sqlite3
import os
import json
from datetime import datetime

class AuditLogger:
    def __init__(self, db_path="data_pipeline/storage/pipeline_audit.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Pipeline Runs Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                run_id TEXT PRIMARY KEY,
                dag_name TEXT NOT NULL,
                status TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_sec REAL,
                records_processed INTEGER DEFAULT 0,
                error_message TEXT
            );
            """)

            # 2. Task Runs Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_runs (
                task_run_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                dag_name TEXT NOT NULL,
                task_name TEXT NOT NULL,
                status TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_sec REAL,
                error_message TEXT,
                FOREIGN KEY (run_id) REFERENCES pipeline_runs(run_id)
            );
            """)

            # 3. Data Quality Contracts Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_audit (
                check_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                table_name TEXT NOT NULL,
                check_name TEXT NOT NULL,
                status TEXT NOT NULL,
                observed_value TEXT,
                threshold TEXT,
                message TEXT,
                executed_at TEXT NOT NULL
            );
            """)

            # 4. System Logs Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL
            );
            """)
            conn.commit()

    def log_run_start(self, run_id, dag_name):
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.cursor().execute("""
                INSERT INTO pipeline_runs (run_id, dag_name, status, start_time)
                VALUES (?, ?, 'RUNNING', ?)
            """, (run_id, dag_name, now))
            conn.commit()

    def log_run_end(self, run_id, status, duration_sec, records_processed=0, error_message=None):
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.cursor().execute("""
                UPDATE pipeline_runs
                SET status = ?, end_time = ?, duration_sec = ?, records_processed = ?, error_message = ?
                WHERE run_id = ?
            """, (status, now, duration_sec, records_processed, error_message, run_id))
            conn.commit()

    def log_task_start(self, task_run_id, run_id, dag_name, task_name):
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.cursor().execute("""
                INSERT INTO task_runs (task_run_id, run_id, dag_name, task_name, status, start_time)
                VALUES (?, ?, ?, ?, 'RUNNING', ?)
            """, (task_run_id, run_id, dag_name, task_name, now))
            conn.commit()

    def log_task_end(self, task_run_id, status, duration_sec, error_message=None):
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.cursor().execute("""
                UPDATE task_runs
                SET status = ?, end_time = ?, duration_sec = ?, error_message = ?
                WHERE task_run_id = ?
            """, (status, now, duration_sec, error_message, task_run_id))
            conn.commit()

    def log_quality_check(self, run_id, table_name, check_name, status, observed_value, threshold, message):
        now = datetime.now().isoformat()
        check_id = f"{run_id}_{table_name}_{check_name}_{now}"
        with self._get_connection() as conn:
            conn.cursor().execute("""
                INSERT INTO quality_audit (check_id, run_id, table_name, check_name, status, observed_value, threshold, message, executed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (check_id, run_id, table_name, check_name, status, str(observed_value), str(threshold), message, now))
            conn.commit()

    def log_event(self, run_id, level, message):
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.cursor().execute("""
                INSERT INTO system_logs (run_id, timestamp, level, message)
                VALUES (?, ?, ?, ?)
            """, (run_id, now, level, message))
            conn.commit()

    def get_recent_runs(self, limit=20):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pipeline_runs ORDER BY start_time DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def get_quality_summary(self):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_checks,
                    SUM(CASE WHEN status = 'PASSED' THEN 1 ELSE 0 END) as passed_checks,
                    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed_checks
                FROM quality_audit
            """)
            row = cursor.fetchone()
            return dict(row) if row else {"total_checks": 0, "passed_checks": 0, "failed_checks": 0}

    def get_recent_quality_checks(self, limit=15):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM quality_audit ORDER BY executed_at DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def get_recent_logs(self, limit=50):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM system_logs ORDER BY log_id DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]
