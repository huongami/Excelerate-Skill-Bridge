"""QA response times of the list and detail endpoints (53 open jobs, 51 talent profiles), 20 calls each. It starts its own platform (demo data).

Usage:  python tests/browser/qa_perf.py [--port 8160] [--calls 20] [--out times.json]
Every call must be faster than 1 second on the computer of the test. The numbers are printed. It uses 127.0.0.1 (on Windows, "localhost" can add 2 seconds to each request).
"""
import argparse
import json
import os
import statistics
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(__file__))
from e2e_common import Report, api_call, api_login, start_demo_platform, stop_demo_platform  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, default=8160)
ap.add_argument("--calls", type=int, default=20)
ap.add_argument("--out", default="")
ARGS = ap.parse_args()
R = Report("qa_perf")
BASE = f"http://127.0.0.1:{ARGS.port}"


def timed(method, path, token, n):
    times = []
    status = None
    for _ in range(n):
        t = time.perf_counter()
        status, _ = api_call(BASE, method, path, token=token)
        times.append((time.perf_counter() - t) * 1000)
    return status, times


def main():
    proc, tpw, epw, log = start_demo_platform(ARGS.port)
    out = {}
    sequential_log_size = 0
    try:
        tt = api_login(BASE, "candidate@demo.jinder.app", tpw)
        et = api_login(BASE, "recruiter@demo.jinder.app", epw)
        s, jobs = api_call(BASE, "GET", "/jobs?pageSize=50", token=tt)
        ids = [j["id"] for j in jobs["items"]]
        s, cands = api_call(BASE, "GET", "/recruiter/candidates?jobId=job-demo-data-engineer-mid&pageSize=50", token=et)
        talent_ids = [c["id"] for c in cands["items"]]
        R.info(f"data: {jobs['page']['total']} open jobs, {cands['page']['total']} talent profiles that employers can see")
        cases = [
            ("talent recommended (page 10)", "GET", "/jobs/recommended?pageSize=10", tt),
            ("talent recommended (page 50, best)", "GET", "/jobs/recommended?pageSize=50", tt),
            ("talent jobs list (page 50, newest)", "GET", "/jobs?pageSize=50&sort=newest", tt),
            ("talent job detail (with path, 8 axes, similar jobs)", "GET", f"/jobs/{ids[0]}", tt),
            ("talent job detail of a weak job", "GET", f"/jobs/{ids[-1]}", tt),
            ("talent compare with 5 jobs", "GET", "/jobs/compare?ids=" + ",".join(ids[:5]), tt),
            ("talent bookmarks", "GET", "/bookmarks?pageSize=50", tt),
            ("talent applications", "GET", "/applications?pageSize=50", tt),
            ("talent stats", "GET", "/stats", tt),
            ("employer candidates (Basic, 5 shown)", "GET", "/recruiter/candidates?jobId=job-demo-data-engineer-mid", et),
            ("employer candidates (page 50, best)", "GET", "/recruiter/candidates?jobId=job-demo-data-engineer-mid&pageSize=50&sort=best", "premium"),
            ("employer candidates (page 50, updated)", "GET", "/recruiter/candidates?jobId=job-demo-data-engineer-mid&pageSize=50&sort=updated", "premium"),
            ("employer candidate detail", "GET", f"/recruiter/candidates/{talent_ids[0]}?jobId=job-demo-data-engineer-mid", "premium"),
            ("employer compare with 5 profiles", "GET", "/recruiter/compare?ids=" + ",".join(talent_ids[:5]) + "&jobId=job-demo-data-engineer-mid", "premium"),
            ("employer jobs", "GET", "/recruiter/jobs?pageSize=50", et),
            ("employer job applications", "GET", "/recruiter/jobs/job-demo-data-engineer-mid/applications", et),
            ("employer stats (advanced)", "GET", "/stats", "premium"),
        ]
        api_call(BASE, "PUT", "/entitlements", {"plan": "basic"}, token=et)
        for label, method, path, token in cases:
            if token == "premium":
                api_call(BASE, "PUT", "/entitlements", {"plan": "premium"}, token=et)
                token = et
            elif label.startswith("employer candidates (Basic"):
                api_call(BASE, "PUT", "/entitlements", {"plan": "basic"}, token=et)
            status, times = timed(method, path, token, ARGS.calls)
            out[label] = {"status": status, "calls": len(times), "min": round(min(times)), "mean": round(statistics.mean(times)), "p95": round(sorted(times)[int(len(times) * 0.95) - 1]), "max": round(max(times))}
            R.check(f"{label}: {len(times)} calls, min {out[label]['min']} / mean {out[label]['mean']} / max {out[label]['max']} ms, all under 1000 ms", status == 200 and max(times) < 1000, str(out[label]))
        sequential_log_size = len(open(log, errors="replace").read())
        # four clients at the same time (the answer of the server is slower when 4 clients ask at once: the formulas run in one process)
        errors = []
        times_all = []

        def worker():
            for _ in range(10):
                t = time.perf_counter()
                s1, _ = api_call(BASE, "GET", f"/jobs/{ids[1]}", token=tt)
                s2, _ = api_call(BASE, "GET", "/recruiter/candidates?jobId=job-demo-data-engineer-mid&pageSize=50", token=et)
                times_all.append((time.perf_counter() - t) * 1000)
                if s1 != 200 or s2 != 200:
                    errors.append((s1, s2))
        threads = [threading.Thread(target=worker) for _ in range(4)]
        t0 = time.perf_counter()
        [t.start() for t in threads]
        [t.join() for t in threads]
        out["4 clients at once (job detail + candidates list, 10 rounds each)"] = {"rounds": len(times_all), "mean": round(statistics.mean(times_all)), "max": round(max(times_all)), "errors": len(errors), "seconds": round(time.perf_counter() - t0, 1)}
        R.check(f"4 clients at once: {len(times_all)} rounds of two calls, mean {out['4 clients at once (job detail + candidates list, 10 rounds each)']['mean']} ms, max {round(max(times_all))} ms, no error", not errors and max(times_all) < 4000, str(errors[:3]))
    finally:
        stop_demo_platform(proc)
        text = open(log, errors="replace").read()
        errs = [l for l in text.splitlines() if " ERROR " in l or "Traceback" in l]
        R.check("the server log has no ERROR line and no traceback", not errs, "; ".join(errs[:3]))
        slow = [l for l in text[:sequential_log_size].splitlines() if "-> 200 (" in l and int(l.rsplit("(", 1)[1].split(" ")[0]) > 1000]
        R.check("no request of the 20-call series took more than 1000 ms in the server log", not slow, "; ".join(slow[:3]))
        if ARGS.out:
            json.dump(out, open(ARGS.out, "w"), indent=1)
    return R.finish()


if __name__ == "__main__":
    raise SystemExit(main())
