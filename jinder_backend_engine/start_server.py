#!/usr/bin/env python3
"""
Jinder — Backend REST API & Intelligence Engine Launcher
=========================================================
Path: jinder_backend_engine/start_server.py

1. Verifies that the SQLite database exists. If missing, it automatically seeds
   the database with 461 Australian job requisitions and 320 candidate profiles.
2. Starts the REST API mock server on port 8095 (or custom $PORT).
3. Connects the REST API directly to the 6 intelligence engine scoring models.
"""

import sys
import os
import subprocess

PACKAGE_ROOT = os.path.abspath(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(PACKAGE_ROOT, "backend")
VAR_DIR = os.path.join(BACKEND_DIR, "var")
DB_PATH = os.path.join(VAR_DIR, "app.db")
SEED_SCRIPT = os.path.join(BACKEND_DIR, "seed_db.py")
SERVER_SCRIPT = os.path.join(BACKEND_DIR, "server.py")

# Ensure package root is in sys.path
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


def ensure_database():
    """Seeds the SQLite database if it does not exist yet."""
    os.makedirs(VAR_DIR, exist_ok=True)
    if not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) == 0:
        print("[INIT] Database not found. Running seed_db.py to populate 461 jobs & 320 candidates...")
        res = subprocess.run([sys.executable, SEED_SCRIPT], cwd=BACKEND_DIR)
        if res.returncode != 0:
            print("[ERROR] Failed to seed database. Please check backend/seed_db.py.")
            sys.exit(1)
        print("[INIT] Database successfully initialized at:", DB_PATH)
    else:
        print(f"[INIT] Existing database found at: {DB_PATH} ({os.path.getsize(DB_PATH):,} bytes)")


def main():
    print("=" * 75)
    print("JINDER — BACKEND REST API SERVER LAUNCHER")
    print("=" * 75)
    ensure_database()

    port = int(os.environ.get("PORT", os.environ.get("PRODUCT_API_PORT", 8095)))
    print(f"[SERVER] Starting REST API server on http://localhost:{port}")
    print("[SERVER] Available API Endpoints:")
    print(f"  • GET  http://localhost:{port}/api/public/stats")
    print(f"  • GET  http://localhost:{port}/api/seeker/feed (Formula 5 FRS)")
    print(f"  • POST http://localhost:{port}/api/seeker/swipe")
    print(f"  • GET  http://localhost:{port}/api/seeker/projection")
    print(f"  • POST http://localhost:{port}/api/recruiter/search (Formula 6 TSS)")
    print(f"  • POST http://localhost:{port}/api/benchmark/candidates (Formula 4 RMS)")
    print(f"  • POST http://localhost:{port}/api/compare/jobs (Formula 3 JPI)")
    print("-" * 75)
    print("Press Ctrl+C to stop the server.")
    print("=" * 75)

    # Launch server
    env = os.environ.copy()
    env["PRODUCT_API_PORT"] = str(port)
    subprocess.run([sys.executable, SERVER_SCRIPT], cwd=BACKEND_DIR, env=env)


if __name__ == "__main__":
    main()
