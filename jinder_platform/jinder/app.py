"""Start the Jinder platform: database, sample data, email worker and the web server."""
import argparse
import logging
import sys
import threading

from . import __version__, config, db, mailer, parsing, seed
from . import routes  # noqa: F401 - importing registers the API routes
from .http_server import make_server


def _setup_logging():
    """Write log lines from a separate thread. A slow or full log output (a pipe that nobody reads) must never stop a request."""
    import logging.handlers
    import queue

    out = logging.StreamHandler()
    out.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S"))
    q: "queue.Queue" = queue.Queue(-1)
    root = logging.getLogger()
    root.handlers[:] = [logging.handlers.QueueHandler(q)]
    root.setLevel(logging.INFO)
    listener = logging.handlers.QueueListener(q, out)
    listener.start()
    return listener


def prepare(demo: bool = False, reset: bool = False) -> dict:
    """Create the database and the sample data. Returns what was written, and the demo passwords when demo=True."""
    if reset and config.DB_PATH.exists():
        for suffix in ("", "-wal", "-shm"):
            p = config.DB_PATH.with_name(config.DB_PATH.name + suffix)
            if p.exists():
                p.unlink()
    backup = db.init_db()   # an old database (schema version 1) is renamed to a backup file. Nothing is deleted
    conn = db.connect()
    try:
        info = {"seeded": seed.seed_all(conn), "demo": {}, "migrated": backup}
        with db.transaction(conn):
            parsing.cleanup(conn)
        if demo:
            with db.transaction(conn):
                info["demo"] = seed.seed_demo_accounts(conn)
    finally:
        conn.close()
    return info


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Jinder platform: frontend, REST API, database and the six formulas.")
    ap.add_argument("--host", default=config.HOST)
    ap.add_argument("--port", type=int, default=config.PORT)
    ap.add_argument("--demo", action="store_true", help="make two demo accounts with random passwords (shown once)")
    ap.add_argument("--reset-db", action="store_true", help="delete the database and make it again")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)  # show the start text at once, also when the output is a file

    listener = _setup_logging()
    if not config.APP_DIR.joinpath("index.html").is_file():
        print(f"The frontend folder was not found: {config.APP_DIR}\nSet JINDER_APP_DIR to the 'app' folder of Skill Bridge.", file=sys.stderr)
        return 2
    if not config.ENGINE_DIR.joinpath("01_skill_matching_model.py").is_file():
        print(f"The formula folder was not found: {config.ENGINE_DIR}\nSet JINDER_ENGINE_DIR to 'intelligence_engine'.", file=sys.stderr)
        return 2

    info = prepare(demo=args.demo, reset=args.reset_db)
    mailer.start_worker()
    server = make_server(args.host, args.port)
    url = f"http://{'localhost' if args.host in ('127.0.0.1', '0.0.0.0') else args.host}:{args.port}/"
    print("=" * 72)
    print(f"Jinder platform {__version__}")
    print(f"  App         {url}")
    print(f"  API         {url}api/health")
    print(f"  Database    {config.DB_PATH}")
    print(f"  Data        {info['seeded']}")
    if info["migrated"]:
        print(f"  Old data    The old database was kept as {info['migrated']}. Nothing was deleted. A new database was made.")
    if info["demo"]:
        print("  Demo accounts (the passwords are shown only now):")
        for email, pw in info["demo"].items():
            print(f"    {email}   {pw}")
    else:
        print("  No demo accounts. Start with --demo to make them, or create an account in the app.")
    print("  Press Ctrl+C to stop.")
    print("=" * 72)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        mailer.stop_worker()
        server.server_close()
        listener.stop()
    return 0
