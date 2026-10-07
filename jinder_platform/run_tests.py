#!/usr/bin/env python3
"""Run the tests.

  python run_tests.py                 unit and API tests (about 1.5 minutes)
  python run_tests.py --formulas      also run the self-checks of the six formula files (jinder_backend_engine/run_verification.py)
  python run_tests.py --browser       also run all the tests in a real browser (needs Chrome or Edge): about 11 minutes
  python run_tests.py --browser-quick also run only the two journeys in a real browser (e2e_demo.py and e2e_journey.py): about 2 minutes

What `--browser` runs. Each stage starts its own platform in a temporary folder (never the folder var/ of your own data), on port 8197,
and stops it when the stage ends. Every stage prints one line for each step (PASS or FAIL). At the end, a table shows the result of each stage.

  1. e2e_demo.py       the demo story in the real browser (the demo talent Teal Heron and the demo employer Alex Morgan at Bluebushworks)
  2. e2e_journey.py    a new talent and a new employer: CV scan, onboarding, a new job, apply, review, interview, offer, delete the account
  3. check_fe_core.py, check_fe_talent.py, check_fe_employer.py, check_fe_compare.py, check_mock_ict.py
                       the checks of the front-end parts (shared components, talent screens, employer screens, compare page) and of the browser-only mock (?mock=1)

The five checks of step 3 add about 9 minutes (69 + 179 + 121 + 106 + 50 seconds on the computer where this was measured).
The whole run is under the limit of 15 minutes, so they are part of `--browser`. Use `--browser-quick` when you need a fast answer.
The ports are 8197 for the platform and 9370 and up for the debugging port of the browser. Set JINDER_BROWSER to the path of the browser program if it is not found.
"""
import os
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BROWSER_DIR = ROOT / "tests" / "browser"
PORT = 8197
FRONT_END_CHECKS = ["check_fe_core.py", "check_fe_talent.py", "check_fe_employer.py", "check_fe_compare.py", "check_mock_ict.py"]


def run_unit_tests() -> bool:
    if os.environ.get("JINDER_REAL_HASH_IN_TESTS") != "1":      # set it to 1 to run the tests with the real (slow) hash
        os.environ["JINDER_FAST_TEST_HASH"] = "1"      # a fast password hash for the many test accounts. The browser tests below use the real one.
    sys.path.insert(0, str(ROOT / "tests"))
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py", top_level_dir=str(ROOT / "tests"))
    return unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful()


def _clean_env(var: str = "") -> dict:
    """The environment of a platform or a browser script. The unit tests change os.environ for their own temporary database
    (tests/helpers.py). A browser stage must not inherit it: it would use, and lock, the database of the unit tests.
    `var` is the data folder for the platform of the stage. Without it, the variable is removed (each script then makes its own temporary folder)."""
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    for key in ("JINDER_DB_PATH", "JINDER_UPLOAD_DIR", "JINDER_VAR_DIR", "JINDER_FAST_TEST_HASH"):
        env.pop(key, None)
    if var:
        env["JINDER_VAR_DIR"] = var
    return env


def _port_is_free(port: int) -> bool:
    import socket
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) != 0


def _stop(proc: subprocess.Popen) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    for _ in range(40):      # wait until the port is free, so that the next stage can use it
        if _port_is_free(PORT):
            return
        time.sleep(0.25)


def start_platform(var: str):
    """Start the platform with the demo accounts. Returns (process, talent password, employer password) or None."""
    log_path = os.path.join(var, "server.log")   # a file, not a pipe: nobody must have to read the server output
    server = subprocess.Popen([sys.executable, str(ROOT / "start.py"), "--demo", "--reset-db", "--port", str(PORT)], env=_clean_env(var),
                              stdout=open(log_path, "w"), stderr=subprocess.STDOUT, text=True)
    talent_pw = employer_pw = None
    deadline = time.time() + 60
    while time.time() < deadline and not (talent_pw and employer_pw):
        time.sleep(0.3)
        for line in open(log_path, errors="replace"):
            if "candidate@demo.jinder.app" in line:
                talent_pw = line.split()[-1]
            if "recruiter@demo.jinder.app" in line:
                employer_pw = line.split()[-1]
    if not (talent_pw and employer_pw):
        print("The server did not start in time. Its output:")
        print(open(log_path, errors="replace").read())
        _stop(server)
        return None
    for _ in range(60):   # wait until the server answers
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/health", timeout=3).read()
            return server, talent_pw, employer_pw
        except OSError:
            time.sleep(0.5)
    print("The server does not answer. Its output:")
    print(open(log_path, errors="replace").read())
    _stop(server)
    return None


def _stage(name: str, args: list, summary: list) -> bool:
    """Run one browser script. Its output goes to this console, so every step is visible."""
    print(f"\n{'=' * 78}\nSTAGE {name}\n{'=' * 78}", flush=True)
    started = time.time()
    code = subprocess.call([sys.executable, "-u", *args], env=_clean_env())
    summary.append((name, code == 0, time.time() - started))
    return code == 0


def run_browser_tests(front_end_checks: bool = True) -> bool:
    summary: list = []
    var = tempfile.mkdtemp(prefix="jinder-e2e-")
    shots = os.path.join(var, "screenshots")
    print(f"Temporary folder: {var} (not the folder var/ of your own data). Platform port: {PORT}.", flush=True)
    if not _port_is_free(PORT):
        print(f"Port {PORT} is in use. Stop the program that uses it, then run the tests again.")
        return False
    started = start_platform(var)
    if not started:
        return False
    server, talent_pw, employer_pw = started
    try:
        base = f"http://localhost:{PORT}"
        _stage("e2e_demo", [str(BROWSER_DIR / "e2e_demo.py"), base, talent_pw, employer_pw, os.path.join(shots, "e2e_demo")], summary)
        _stage("e2e_journey", [str(BROWSER_DIR / "e2e_journey.py"), base, os.path.join(shots, "e2e_journey")], summary)
    finally:
        _stop(server)
    if front_end_checks:
        for i, script in enumerate(FRONT_END_CHECKS):
            # each of these scripts starts its own platform (with --demo --reset-db) in its own temporary folder and stops it
            _stage(script[:-3], [str(BROWSER_DIR / script), "--port", str(PORT), "--debug-port", str(9370 + i), "--shots", os.path.join(shots, script[:-3])], summary)
    print(f"\n{'=' * 78}\nBROWSER TESTS: RESULT OF EACH STAGE\n{'=' * 78}")
    for name, ok, seconds in summary:
        print(f"  {'PASS' if ok else 'FAIL'}  {name:<20} {seconds:6.0f} s")
    print(f"  Screenshots: {shots}")
    return all(ok for _, ok, _ in summary)


def run_formula_checks() -> bool:
    script = ROOT.parent / "jinder_backend_engine" / "run_verification.py"
    return script.is_file() and subprocess.call([sys.executable, str(script)]) == 0


if __name__ == "__main__":
    ok = run_unit_tests()
    if "--formulas" in sys.argv:
        ok = run_formula_checks() and ok
    if "--browser" in sys.argv:
        ok = run_browser_tests(front_end_checks=True) and ok
    elif "--browser-quick" in sys.argv:
        ok = run_browser_tests(front_end_checks=False) and ok
    raise SystemExit(0 if ok else 1)
