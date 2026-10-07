#!/usr/bin/env python3
"""Check how well the 50 synthetic talents pair with the 50 synthetic jobs.

Standard library only. Run:  python check_pairing.py [--verbose]

For each talent and each job, the script computes a simple "must-have coverage":

    coverage = (sum of credits over the job's must-have skills) / (number of must-have skills)

    credit 1.0  if the talent has the skill at a level >= the required level
    credit 0.5  if the talent has the skill one level below the required level
    credit 0.0  otherwise (two or more levels below, or the skill is missing)

If a job has no must-have skill, all of its skills are used instead.
This is a rough check of the data only. It is NOT the platform match score.

Requirements (exit code 0 if all hold, 1 if not):
    * each job has at least 3 talents with coverage >= 0.6
    * each talent has at least 3 jobs with coverage >= 0.6
    * each "bridge" talent (target role in another specialisation) has at least 2 jobs in the
      target area (jobs of the target specialisation) with coverage >= 0.4
"""
import importlib.util
import json
import os
import statistics
import sys

sys.dont_write_bytecode = True  # do not leave a __pycache__ folder next to the data

HERE = os.path.dirname(os.path.abspath(__file__))
TALENTS_PATH = os.path.join(HERE, "talents.json")
JOBS_PATH = os.path.join(HERE, "jobs.json")
DEMO_PATH = os.path.join(HERE, "demo.json")

THRESHOLD = 0.6
BRIDGE_THRESHOLD = 0.4
MIN_TALENTS_PER_JOB = 3
MIN_JOBS_PER_TALENT = 3
MIN_BRIDGE_JOBS = 2
PARTIAL_CREDIT = 0.5


def load_role_specs():
    """Take ROLE_SPECS from validate_talents.py, so that both scripts use one table."""
    path = os.path.join(HERE, "validate_talents.py")
    spec = importlib.util.spec_from_file_location("validate_talents_roles", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ROLE_SPECS


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def job_list(data):
    if isinstance(data, dict):
        for key in ("jobs", "items"):
            if isinstance(data.get(key), list):
                return data[key]
        return []
    return data if isinstance(data, list) else []


def job_skills(job):
    """Return a list of (name, level, must). Accepts the names used by the plan and by the engine."""
    raw = job.get("skills")
    if not (isinstance(raw, list) and raw and isinstance(raw[0], dict)):
        raw = job.get("skillRequirements") or job.get("required_skills") or []
    out = []
    for s in raw:
        if isinstance(s, dict):
            out.append((s.get("name"), int(s.get("level", 3)), bool(s.get("must", True))))
    return out


def coverage(talent_levels, requirements):
    musts = [r for r in requirements if r[2]] or requirements
    if not musts:
        return 0.0
    total = 0.0
    for name, need, _ in musts:
        have = talent_levels.get(name, 0)
        if have >= need:
            total += 1.0
        elif have and have == need - 1:
            total += PARTIAL_CREDIT
    return total / len(musts)


def median(values):
    return statistics.median(values) if values else 0


def run_table(talents, jobs, role_specs, verbose, label):
    levels = []
    for t in talents:
        levels.append({s["name"]: s["level"] for s in t["skills"]})
    reqs = [job_skills(j) for j in jobs]
    cov = [[coverage(levels[i], reqs[k]) for k in range(len(jobs))] for i in range(len(talents))]

    per_talent = [sum(1 for k in range(len(jobs)) if cov[i][k] >= THRESHOLD) for i in range(len(talents))]
    per_job = [sum(1 for i in range(len(talents)) if cov[i][k] >= THRESHOLD) for k in range(len(jobs))]

    problems = []
    bridge_rows = []
    for i, t in enumerate(talents):
        if per_talent[i] < MIN_JOBS_PER_TALENT:
            problems.append(f"talent {t['alias']} ({t['currentRole']}, {t['level']}) has {per_talent[i]} jobs at >= {THRESHOLD}")
        target_specs = set()
        for r in t["targetRole"]:
            target_specs |= role_specs.get(r, set())
        if t["specialisation"] not in target_specs:
            area = [k for k, j in enumerate(jobs) if j.get("specialisation") in target_specs]
            good = [k for k in area if cov[i][k] >= BRIDGE_THRESHOLD]
            best = max((cov[i][k] for k in area), default=0.0)
            bridge_rows.append((t["alias"], t["specialisation"], "/".join(t["targetRole"]), len(area), len(good), best))
            if len(good) < MIN_BRIDGE_JOBS:
                problems.append(f"bridge talent {t['alias']} ({t['specialisation']} -> {sorted(target_specs)}) has {len(good)} "
                                f"target-area jobs at >= {BRIDGE_THRESHOLD} (area has {len(area)} jobs, best {best:.2f})")
    for k, j in enumerate(jobs):
        if per_job[k] < MIN_TALENTS_PER_JOB:
            problems.append(f"job {j.get('key') or j.get('title')} ({j.get('title')}) has {per_job[k]} talents at >= {THRESHOLD}")

    print(f"=== {label}: {len(talents)} talents x {len(jobs)} jobs ===")
    if verbose:
        print("\nJobs per talent (coverage >= %.1f):" % THRESHOLD)
        for i, t in enumerate(talents):
            print(f"  {per_talent[i]:3d}  {t['alias']:<16} {t['level']:<9} {t['specialisation']}")
        print("\nTalents per job (coverage >= %.1f):" % THRESHOLD)
        for k, j in enumerate(jobs):
            print(f"  {per_job[k]:3d}  {str(j.get('key')):<28} {j.get('level', ''):<9} {j.get('title')}")
    print("\nTable                         min   median   max")
    print(f"Jobs per talent (>= {THRESHOLD:.1f})      {min(per_talent):>3}   {median(per_talent):>6}   {max(per_talent):>3}")
    print(f"Talents per job (>= {THRESHOLD:.1f})      {min(per_job):>3}   {median(per_job):>6}   {max(per_job):>3}")
    all_cov = [c for row in cov for c in row]
    print(f"Coverage over all pairs     {min(all_cov):>5.2f}   {median(all_cov):>6.2f}   {max(all_cov):>5.2f}")
    if bridge_rows:
        print(f"\nBridge talents ({len(bridge_rows)}): target-area jobs with coverage >= {BRIDGE_THRESHOLD}")
        print("  talent             from -> to                                                   area  ok  best")
        for alias, frm, to, area, good, best in bridge_rows:
            print(f"  {alias:<18} {frm} -> {to}"[:78].ljust(78) + f" {area:>4} {good:>3}  {best:.2f}")
    return problems, per_talent, per_job


def main():
    verbose = "--verbose" in sys.argv
    if not os.path.exists(JOBS_PATH):
        print("jobs.json does not exist yet. Run this script again when the Jobs agent has written it.")
        return 2
    role_specs = load_role_specs()
    talents = load_json(TALENTS_PATH)["talents"]
    jobs = job_list(load_json(JOBS_PATH))
    if not jobs:
        print("jobs.json has no jobs.")
        return 2

    problems, _, _ = run_table(talents, jobs, role_specs, verbose, "jobs.json")

    if os.path.exists(DEMO_PATH):
        demo_jobs = job_list(load_json(DEMO_PATH))
        if demo_jobs:
            print()
            demo_problems, _, _ = run_table(talents, demo_jobs, role_specs, verbose, "demo.json (information only)")
            if demo_problems:
                print("\nDemo-job notes (not part of the requirement):")
                for p in demo_problems:
                    if p.startswith("job "):
                        print("  -", p)

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s):")
        for p in problems:
            print("  -", p)
        return 1
    print("\nOK: each job has >= %d talents, each talent has >= %d jobs, each bridge talent has >= %d target-area jobs."
          % (MIN_TALENTS_PER_JOB, MIN_JOBS_PER_TALENT, MIN_BRIDGE_JOBS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
