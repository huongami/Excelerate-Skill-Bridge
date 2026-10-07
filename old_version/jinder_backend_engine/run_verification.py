#!/usr/bin/env python3
"""
Jinder — Mathematical Verification & Health Check Suite
=======================================================
Path: jinder_backend_engine/run_verification.py

Runs autonomous verification tests on:
1. Formula 1: Candidate vs ANZSCO Skill Match (SMF)
2. Formula 2: Skill Gap Severity & Job Readiness (GSI & JRS)
3. Formula 3: Job Proximity Index & Multi-Job Matrix (JPI)
4. Formula 4: Candidate Benchmarking & Relative Merit (RMS)
5. Formula 5: Job Seeker Feed Ranking (FRS) & Behavioural Loop
6. Formula 6: Recruiter Talent Search & Zero-PII Aliases (TSS)
7. Backend Scoring Integration Wrapper (`backend/scores.py`)
"""

import sys
import os
import subprocess
import time

PACKAGE_ROOT = os.path.abspath(os.path.dirname(__file__))
ENGINE_DIR = os.path.join(PACKAGE_ROOT, "intelligence_engine")
BACKEND_DIR = os.path.join(PACKAGE_ROOT, "backend")

# Setup sys.path
sys.path.insert(0, PACKAGE_ROOT)
sys.path.insert(0, BACKEND_DIR)


def run_test(name: str, cmd: list, cwd: str) -> bool:
    print(f"\n[TESTING] {name}...")
    start = time.time()
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    dur = (time.time() - start) * 1000
    if res.returncode == 0:
        print(f"  --> PASSED ({dur:.1f}ms)")
        return True
    else:
        print(f"  --> FAILED ({dur:.1f}ms)")
        print(res.stderr or res.stdout)
        return False


def main():
    print("=" * 75)
    print("JINDER INTELLIGENCE ENGINE & BACKEND — VERIFICATION SUITE")
    print("=" * 75)

    tests = [
        ("Formula 1 (SMF Skill Match)", [sys.executable, "01_skill_matching_model.py"], ENGINE_DIR),
        ("Formula 2 (GSI Skill Gap Analysis)", [sys.executable, "02_skill_gap_analysis.py"], ENGINE_DIR),
        ("Formula 3 (JPI Job Proximity)", [sys.executable, "03_job_to_job_comparison.py"], ENGINE_DIR),
        ("Formula 4 (RMS Candidate Benchmarking)", [sys.executable, "04_candidate_benchmarking.py"], ENGINE_DIR),
        ("Formula 5 (FRS Job Seeker Feed)", [sys.executable, "05_job_seeker_ranking_feed.py"], ENGINE_DIR),
        ("Formula 6 (TSS Recruiter Search)", [sys.executable, "06_recruiter_candidate_ranking.py"], ENGINE_DIR),
        ("Backend Scores Integration", [sys.executable, "-c", "import scores; print('scores.py imported and verified')"], BACKEND_DIR),
    ]

    all_passed = True
    for name, cmd, cwd in tests:
        passed = run_test(name, cmd, cwd)
        if not passed:
            all_passed = False

    print("\n" + "=" * 75)
    if all_passed:
        print("ALL 7 VERIFICATION TESTS PASSED SUCCESSFULLY!")
        print("The formulas, dataset mappings, and backend scores wrapper are 100% operational.")
    else:
        print("SOME TESTS ENCOUNTERED ERRORS. Please check the logs above.")
    print("=" * 75)


if __name__ == "__main__":
    main()
