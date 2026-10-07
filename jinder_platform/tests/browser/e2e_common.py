"""Shared helpers of the browser journeys (e2e_demo.py, e2e_journey.py): a report that prints each step, a small API client,
and the browser actions that every journey needs (sign in, go to a page, read the session token, press a key).

The journeys talk to the platform in two ways. They drive the screens in a real browser (the thing that is tested), and they read the
API with plain HTTP (the numbers that the screens must show). The API client uses 127.0.0.1: on Windows a request to "localhost" can wait
2 seconds for each request while the computer tries the IPv6 address first.
"""
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from cdp import Browser  # noqa: E402,F401


class Report:
    """Collect the checks. Every step prints one line: PASS, or FAIL with the detail."""

    def __init__(self, title, shots=None):
        self.title = title
        self.shots = shots or tempfile.mkdtemp(prefix="jinder-shots-")
        os.makedirs(self.shots, exist_ok=True)
        self.results = []
        self.started = time.time()

    def section(self, name):
        print(f"\n== {name}", flush=True)

    def check(self, name, ok, detail=""):
        self.results.append((name, bool(ok), detail))
        print(("PASS " if ok else "FAIL ") + name + (f"  [{str(detail)[:500]}]" if detail and not ok else ""), flush=True)
        return bool(ok)

    def info(self, text):
        print("INFO " + text, flush=True)

    def shot(self, b, name, full=False):
        path = os.path.join(self.shots, name)
        b.screenshot(path, full=full)
        return path

    def finish(self):
        failed = [r for r in self.results if not r[1]]
        print(f"\n{self.title}: {len(self.results) - len(failed)} passed, {len(failed)} failed, {time.time() - self.started:.0f} s. Screenshots: {self.shots}", flush=True)
        for name, _, detail in failed:
            print("  FAILED:", name, f"[{str(detail)[:300]}]" if detail else "")
        return 1 if failed else 0


def api_base(base):
    """The address for plain HTTP calls: 127.0.0.1 instead of localhost (see the note at the top of this file)."""
    return base.replace("://localhost", "://127.0.0.1")


def api_call(base, method, path, body=None, token=None):
    """Return (status, json). `path` starts with / and has no /api."""
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(api_base(base) + "/api" + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, (json.loads(raw) if raw else None)
        except ValueError:
            return e.code, raw


def api_login(base, email, password):
    status, res = api_call(base, "POST", "/auth/login", {"email": email, "password": password})
    assert status == 200, (status, res)
    return res["token"]


# ----- browser actions -----
def sign_in(b, base, email, password):
    """Sign in through the sign-in screen. Starts from a clean browser storage."""
    b.goto(f"{base}/#/login")
    b.eval("sessionStorage.clear(); localStorage.clear()", await_promise=False)
    b.goto(f"{base}/#/login")
    b.wait_for("document.querySelector('#email')")
    b.fill("#email", email)
    b.fill("#password", password)
    b.click("form [type=submit]")
    b.wait_for("location.hash.startsWith('#/home')", timeout=30)
    b.pump(0.8)


def go(b, base, route, wait="document.querySelector('main h1, .dash h1')", pump=0.6):
    """Open a route (for example "#/jobs") and wait for a condition."""
    b.goto(f"{base}/{route}")
    b.wait_for(wait, timeout=30)
    b.pump(pump)


def reload(b, pump=0.8):
    """Reload the page for real (a new document). `goto` of the same address only changes the fragment and does not reload. A marker in the old page tells when the new page is there."""
    b.eval("window.__qa_before_reload = true", await_promise=False)
    b.call("Page.reload")
    b.wait_for("!window.__qa_before_reload", timeout=30)
    b.wait_for("document.readyState === 'complete'", timeout=30)
    b.pump(pump)


def token_of(b):
    return b.eval("(JSON.parse(sessionStorage.getItem('jinder.session') || localStorage.getItem('jinder.session') || '{}')).token", await_promise=False)


def fetch_json(b, path):
    """GET /api<path> from inside the page, with the token of the signed-in user. Returns the parsed answer."""
    return b.eval("""(async () => { const t = JSON.parse(sessionStorage.getItem('jinder.session') || localStorage.getItem('jinder.session')).token;
      const r = await fetch('/api' + %s, { headers: { Authorization: 'Bearer ' + t } }); return await r.json(); })()""" % json.dumps(path))


KEYS = {
    "Tab": ("Tab", 9), "Enter": ("Enter", 13), "Escape": ("Escape", 27), "ArrowDown": ("ArrowDown", 40), "ArrowUp": ("ArrowUp", 38),
    "ArrowLeft": ("ArrowLeft", 37), "ArrowRight": ("ArrowRight", 39), "PageDown": ("PageDown", 34), "PageUp": ("PageUp", 33),
    "End": ("End", 35), "Home": ("Home", 36), "Space": (" ", 32),
}


def key(b, name, times=1, shift=False):
    """Press a key like a person: key down (with the character for Enter and Space, so that a button is activated), key up. The focused element gets it."""
    k, vk = KEYS[name]
    text = {"Enter": chr(13), "Space": " "}.get(name)
    for _ in range(times):
        down = {"type": "keyDown" if text else "rawKeyDown", "key": k, "code": name if name != "Space" else "Space", "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk}
        if shift:
            down["modifiers"] = 8
        if text:
            down["text"] = text
        b.call("Input.dispatchKeyEvent", down)
        up = {"type": "keyUp", "key": k, "code": down["code"], "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk}
        if shift:
            up["modifiers"] = 8
        b.call("Input.dispatchKeyEvent", up)
        b.pump(0.08)


def active(b):
    """A short description of the focused element: tag, id, class, label."""
    return b.eval("""(() => { const e = document.activeElement; if (!e) return ''; return [e.tagName.toLowerCase(), e.id ? '#' + e.id : '',
      (e.className && typeof e.className === 'string') ? '.' + e.className.split(' ').join('.') : '', e.getAttribute('aria-label') || ''].join(''); })()""", await_promise=False)


def non_extension(problems):
    """The console problems that come from the app (not from a browser extension)."""
    return [p for p in problems if "chrome-extension://" not in p]


# ----- a platform for a script that runs alone -----
def start_demo_platform(port):
    """Start the platform with the demo accounts in a temporary folder (not the folder var/ of your own data). Returns (process, talent password, employer password, log path)."""
    import subprocess
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    var = tempfile.mkdtemp(prefix="jinder-qa-")
    env = {**os.environ, "JINDER_VAR_DIR": var, "PYTHONUNBUFFERED": "1"}
    for k in ("JINDER_DB_PATH", "JINDER_UPLOAD_DIR", "JINDER_FAST_TEST_HASH"):
        env.pop(k, None)
    log = os.path.join(var, "server.log")
    proc = subprocess.Popen([sys.executable, os.path.join(root, "start.py"), "--demo", "--reset-db", "--port", str(port)], env=env, stdout=open(log, "w"), stderr=subprocess.STDOUT)
    talent_pw = employer_pw = None
    deadline = time.time() + 90
    while time.time() < deadline and not (talent_pw and employer_pw):
        time.sleep(0.4)
        for line in open(log, errors="replace"):
            if "candidate@demo.jinder.app" in line:
                talent_pw = line.split()[-1]
            if "recruiter@demo.jinder.app" in line:
                employer_pw = line.split()[-1]
    if not (talent_pw and employer_pw):
        proc.kill()
        raise RuntimeError("the platform did not start: " + open(log, errors="replace").read()[-1500:])
    return proc, talent_pw, employer_pw, log


def stop_demo_platform(proc):
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except Exception:  # noqa: BLE001
        proc.kill()
