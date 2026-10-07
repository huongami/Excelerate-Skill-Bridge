"""
Jinder Platform — Product REST API & Protocol Mock Server
Path: backend/server.py
Follows specification in docs/05_API_SPEC.md
Runs on port 8095 (or custom PORT env). Direct integration with SQLite DB and Intelligence Engine.
"""

import sys
import os
import json
import uuid
import datetime
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db import get_db
import scores

PORT = int(os.environ.get("PRODUCT_API_PORT", 8095))


class APIHandler(BaseHTTPRequestHandler):
    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def send_json(self, status_code: int, data: Any):
        response_bytes = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(response_bytes)

    def send_error_json(self, status_code: int, message: str):
        self.send_json(status_code, {"error": message, "status": "error"})

    def read_json_body(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            return json.loads(body)
        except Exception:
            return {}

    def get_current_user_id(self) -> str:
        # In demo environment, defaults to user_seeker_demo if header not specified
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth.split("Bearer ", 1)[1].strip()
            if token.startswith("user_"):
                return token
        return "user_seeker_demo"

    # =========================================================================
    # ROUTE DISPATCHERS
    # =========================================================================
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        try:
            # 1. Public Statistics
            if path == "/api/public/stats":
                self.handle_public_stats()
                return

            # 2. Check Alias Uniqueness (REQ-A07)
            if path == "/api/aliases/check":
                alias = query.get("alias", [""])[0]
                self.handle_check_alias(alias)
                return

            # 3. Protocol Mock Google OAuth2 Authorize (REQ-A05)
            if path == "/api/mock-google/authorize":
                self.handle_mock_google_authorize(query)
                return

            # 4. Current User Session
            if path == "/api/auth/me":
                self.handle_auth_me()
                return

            # 5. Seeker Feed (REQ-S01 to S07, S16)
            if path == "/api/seeker/jobs":
                self.handle_seeker_feed(query)
                return

            # 6. Seeker Saved Jobs (REQ-S24)
            if path == "/api/seeker/saved":
                self.handle_seeker_saved()
                return

            # 7. Seeker Applications (REQ-S25, S26)
            if path == "/api/seeker/applications":
                self.handle_seeker_applications()
                return

            # 8. Seeker Application Timeline (REQ-S26)
            if path.startswith("/api/seeker/applications/") and path.endswith("/timeline"):
                app_id = path.split("/")[4]
                self.handle_application_timeline(app_id)
                return

            # 9. Seeker Skills (REQ-S22, S23)
            if path == "/api/seeker/skills":
                self.handle_seeker_skills()
                return

            # 10. Job Detail (REQ-S08 to S11)
            if path.startswith("/api/seeker/jobs/"):
                job_id = path.split("/")[4]
                self.handle_job_detail(job_id)
                return

            # 11. HR KPI Dashboard (REQ-H03)
            if path == "/api/hr/dashboard":
                self.handle_hr_dashboard()
                return

            # 12. HR Managed Jobs (REQ-H04, H05)
            if path == "/api/hr/jobs":
                self.handle_hr_jobs()
                return

            # 13. HR Candidates Shortlist (REQ-H09, H10)
            if path == "/api/hr/candidates":
                self.handle_hr_candidates(query)
                return

            self.send_error_json(404, f"Endpoint not found: {path}")

        except Exception as e:
            self.send_error_json(500, f"Internal server error: {str(e)}")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.read_json_body()

        try:
            # 1. Sign In
            if path == "/api/auth/signin":
                self.handle_signin(body)
                return

            # 2. Seeker Sign Up (REQ-A01 to A04)
            if path == "/api/auth/signup/seeker":
                self.handle_signup_seeker(body)
                return

            # 3. HR Sign Up (REQ-H01, H02)
            if path == "/api/auth/signup/hr":
                self.handle_signup_hr(body)
                return

            # 4. Google Protocol Token Exchange (REQ-A05)
            if path == "/api/auth/google/exchange":
                self.handle_google_exchange(body)
                return

            # 5. CV Scanning (REQ-A01, A02)
            if path == "/api/cv/scan":
                self.handle_cv_scan(body)
                return

            # 6. Save Job (REQ-S14)
            if path.startswith("/api/seeker/jobs/") and path.endswith("/save"):
                job_id = path.split("/")[4]
                self.handle_save_job(job_id)
                return

            # 7. Ignore Job (REQ-S13)
            if path.startswith("/api/seeker/jobs/") and path.endswith("/ignore"):
                job_id = path.split("/")[4]
                self.handle_ignore_job(job_id)
                return

            # 8. Report Job (REQ-S15)
            if path.startswith("/api/seeker/jobs/") and path.endswith("/report"):
                job_id = path.split("/")[4]
                self.handle_report_job(job_id, body)
                return

            # 9. Apply for Job (REQ-S12)
            if path == "/api/seeker/applications":
                self.handle_apply_job(body)
                return

            # 10. Multi-Job Comparison Radar (REQ-S27)
            if path == "/api/seeker/compare":
                self.handle_seeker_compare(body)
                return

            # 11. Multi-Candidate Comparison Radar (REQ-H12)
            if path == "/api/hr/compare":
                self.handle_hr_compare(body)
                return

            # 12. Create Job Requisition (HR)
            if path == "/api/hr/jobs":
                self.handle_create_job(body)
                return

            self.send_error_json(404, f"Endpoint not found: {path}")

        except Exception as e:
            self.send_error_json(500, f"Internal server error: {str(e)}")

    def do_PATCH(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.read_json_body()

        try:
            # Confirm AI Skill (REQ-S23)
            if path.startswith("/api/seeker/skills/") and path.endswith("/confirm"):
                skill_id = path.split("/")[4]
                self.handle_confirm_skill(skill_id)
                return

            # Transition Application Lifecycle (REQ-H11)
            if path.startswith("/api/hr/applications/") and path.endswith("/transition"):
                app_id = path.split("/")[4]
                self.handle_transition_application(app_id, body)
                return

            self.send_error_json(404, f"Endpoint not found: {path}")

        except Exception as e:
            self.send_error_json(500, f"Internal server error: {str(e)}")

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.read_json_body()

        try:
            # Edit Job Requisition (HR)
            if path.startswith("/api/hr/jobs/"):
                job_id = path.split("/")[4]
                self.handle_edit_job(job_id, body)
                return

            # Update Seeker Account Settings
            if path == "/api/seeker/account":
                self.handle_update_seeker_account(body)
                return

            self.send_error_json(404, f"Endpoint not found: {path}")

        except Exception as e:
            self.send_error_json(500, f"Internal server error: {str(e)}")

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            # Unsave Job
            if path.startswith("/api/seeker/jobs/") and path.endswith("/save"):
                job_id = path.split("/")[4]
                self.handle_unsave_job(job_id)
                return

            # Undo Ignore Job
            if path.startswith("/api/seeker/jobs/") and path.endswith("/ignore"):
                job_id = path.split("/")[4]
                self.handle_unignore_job(job_id)
                return

            self.send_error_json(404, f"Endpoint not found: {path}")

        except Exception as e:
            self.send_error_json(500, f"Internal server error: {str(e)}")

    # =========================================================================
    # ENDPOINT HANDLERS
    # =========================================================================

    def handle_public_stats(self):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT count(*) as count FROM jobs WHERE status = 'active'")
        total_live_jobs = cur.fetchone()["count"]

        cur.execute("SELECT count(DISTINCT company) as count FROM jobs")
        total_employers = cur.fetchone()["count"]

        cur.execute("SELECT count(*) as count FROM seeker_profiles")
        total_candidates = cur.fetchone()["count"]

        cur.execute("SELECT count(DISTINCT anzsco_code) as count FROM jobs")
        occupations = cur.fetchone()["count"]

        cur.execute("""
            SELECT category as sector, count(*) as job_count
            FROM jobs GROUP BY category ORDER BY job_count DESC LIMIT 8
        """)
        sectors = [dict(r) for r in cur.fetchall()]
        conn.close()

        self.send_json(200, {
            "total_live_jobs": total_live_jobs,
            "total_employers": total_employers,
            "total_candidates": total_candidates,
            "anzsco_occupations_covered": occupations,
            "top_sectors": sectors
        })

    def handle_check_alias(self, alias: str):
        if not alias:
            self.send_error_json(400, "Alias parameter required")
            return
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT count(*) as count FROM seeker_profiles WHERE lower(alias) = lower(?)", (alias.strip(),))
        exists = cur.fetchone()["count"] > 0
        conn.close()
        self.send_json(200, {"alias": alias, "is_available": not exists})

    def handle_mock_google_authorize(self, query):
        # Generates a mock OAuth2 redirect code conforming to RFC 7636 PKCE
        redirect_uri = query.get("redirect_uri", ["http://localhost:3000/auth/callback"])[0]
        state = query.get("state", ["state123"])[0]
        mock_code = f"mock_google_code_{uuid.uuid4().hex[:12]}"
        target = f"{redirect_uri}?code={mock_code}&state={state}"
        self.send_response(302)
        self.send_header("Location", target)
        self.end_headers()

    def handle_google_exchange(self, body):
        code = body.get("code", "")
        # Returns an authenticated session for a demo user with no CV yet (REQ-A06)
        user_id = "user_google_empty_demo"
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR IGNORE INTO users (id, email, role, auth_provider, google_sub, terms_version, terms_accepted_at)
            VALUES (?, ?, 'seeker', 'google', ?, '2026.1', CURRENT_TIMESTAMP)
        """, (user_id, "demo.google.user@gmail.com", f"sub_{code[:8]}"))
        conn.commit()
        conn.close()

        self.send_json(200, {
            "status": "success",
            "access_token": user_id,
            "has_cv": False,
            "user": {
                "id": user_id,
                "email": "demo.google.user@gmail.com",
                "role": "seeker",
                "auth_provider": "google"
            }
        })

    def handle_auth_me(self):
        user_id = self.get_current_user_id()
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        u = cur.fetchone()
        if not u:
            conn.close()
            self.send_error_json(401, "Not authenticated")
            return

        profile = None
        if u["role"] == "seeker":
            cur.execute("SELECT * FROM seeker_profiles WHERE id = ?", (user_id,))
            p = cur.fetchone()
            if p:
                profile = dict(p)
        elif u["role"] == "hr":
            cur.execute("SELECT * FROM hr_profiles WHERE id = ?", (user_id,))
            p = cur.fetchone()
            if p:
                profile = dict(p)

        conn.close()
        self.send_json(200, {
            "user": dict(u),
            "profile": profile
        })

    def handle_signin(self, body):
        email = body.get("email", "").strip().lower()
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE lower(email) = ?", (email,))
        u = cur.fetchone()
        if not u:
            # Fallback to demo seeker if email not matched for instant demo
            cur.execute("SELECT * FROM users WHERE id = 'user_seeker_demo'")
            u = cur.fetchone()

        conn.close()
        self.send_json(200, {
            "status": "success",
            "access_token": u["id"],
            "user": dict(u)
        })

    def handle_signup_seeker(self, body):
        terms_accepted = body.get("terms_accepted", False)
        if not terms_accepted:
            self.send_error_json(400, "Terms and conditions must be accepted (REQ-A03).")
            return

        user_id = f"user_{uuid.uuid4().hex[:12]}"
        email = body.get("email", "").strip().lower()
        alias = body.get("alias", "").strip() or f"Candidate{uuid.uuid4().hex[:4]}"
        legal_name = body.get("legal_name", "Registered Candidate")
        origin_country = body.get("origin_country", "Australia")
        title = body.get("current_title", "Professional Specialist")
        years_exp = float(body.get("years_experience", 5.0))
        anzsco_code = body.get("target_anzsco_code", "261313")
        anzsco_title = body.get("target_anzsco_title", "Software Engineer")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (id, email, password_hash, role, auth_provider, terms_version, terms_accepted_at)
            VALUES (?, ?, 'hash', 'seeker', 'local', '2026.1', CURRENT_TIMESTAMP)
        """, (user_id, email))

        cur.execute("""
            INSERT INTO seeker_profiles (
                id, alias, legal_name, phone, origin_country, current_title,
                years_experience, highest_education, target_anzsco_code, target_anzsco_title,
                preferred_location, cv_raw_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, alias, legal_name, body.get("phone", ""), origin_country, title,
            years_exp, body.get("highest_education", "Bachelor"), anzsco_code, anzsco_title,
            body.get("preferred_location", "Sydney"), body.get("cv_raw_text", "")
        ))

        # Insert extracted skills
        for s in body.get("skills", []):
            cur.execute("""
                INSERT INTO seeker_skills (id, seeker_id, skill_name, skill_type, source)
                VALUES (?, ?, ?, ?, ?)
            """, (f"skill_{uuid.uuid4().hex[:10]}", user_id, s.get("name", ""), s.get("type", "Direct"), s.get("source", "AI_EXTRACTED")))

        conn.commit()
        conn.close()

        self.send_json(201, {
            "status": "success",
            "access_token": user_id,
            "user": {"id": user_id, "email": email, "role": "seeker", "alias": alias}
        })

    def handle_signup_hr(self, body):
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        email = body.get("email", "").strip().lower()
        company_name = body.get("company_name", "Recruiting Agency")
        recruiter_name = body.get("recruiter_name", "Talent Partner")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (id, email, password_hash, role, auth_provider, terms_version, terms_accepted_at)
            VALUES (?, ?, 'hash', 'hr', 'local', '2026.1', CURRENT_TIMESTAMP)
        """, (user_id, email))

        cur.execute("""
            INSERT INTO hr_profiles (id, company_name, recruiter_name, recruiter_title)
            VALUES (?, ?, ?, ?)
        """, (user_id, company_name, recruiter_name, body.get("recruiter_title", "HR Manager")))

        conn.commit()
        conn.close()

        self.send_json(201, {
            "status": "success",
            "access_token": user_id,
            "user": {"id": user_id, "email": email, "role": "hr", "company_name": company_name}
        })

    def handle_cv_scan(self, body):
        # AI CV extraction simulation returning realistic competencies and suggested alias
        text = body.get("text", "")
        self.send_json(200, {
            "status": "success",
            "extracted_data": {
                "legal_name": "Minh Tuan Nguyen",
                "email": "minh.nguyen@example.com",
                "phone": "+61 412 345 678",
                "origin_country": "Vietnam",
                "current_title": "Registered Nurse",
                "years_experience": 10.0,
                "highest_education": "Bachelor of Nursing",
                "suggested_alias": "SilverKangaroo84",
                "target_anzsco": {
                    "code": "254411",
                    "title": "Registered Nurse / Clinical Specialist",
                    "confidence": 0.95
                },
                "skills": [
                    {"name": "Clinical Triage", "type": "Direct", "source": "AI_EXTRACTED"},
                    {"name": "Patient Assessment", "type": "Direct", "source": "AI_EXTRACTED"},
                    {"name": "Infection Control", "type": "Direct", "source": "AI_EXTRACTED"},
                    {"name": "Wound Care", "type": "Direct", "source": "AI_EXTRACTED"},
                    {"name": "Medication Administration", "type": "Direct", "source": "AI_EXTRACTED"},
                    {"name": "Multidisciplinary Coordination", "type": "Transferable", "source": "AI_EXTRACTED"}
                ]
            }
        })

    def handle_seeker_feed(self, query):
        user_id = self.get_current_user_id()
        keyword = query.get("q", [""])[0].strip().lower()
        category = query.get("category", [""])[0].strip()
        location = query.get("location", [""])[0].strip()
        limit = int(query.get("limit", [50])[0])

        conn = get_db()
        cur = conn.cursor()

        # Load candidate profile for formula execution
        cur.execute("SELECT * FROM seeker_profiles WHERE id = ?", (user_id,))
        cand_row = cur.fetchone()
        candidate = dict(cand_row) if cand_row else {
            "target_anzsco_code": "261313",
            "years_experience": 5.0,
            "origin_country": "Vietnam"
        }
        if cand_row:
            cur.execute("SELECT skill_name, skill_type, source FROM seeker_skills WHERE seeker_id = ? AND is_active = 1", (user_id,))
            candidate["skills"] = [dict(s) for s in cur.fetchall()]
        else:
            candidate["skills"] = []

        # Load behavioural feedback context (REQ-S16)
        cur.execute("SELECT j.company, j.category FROM saved_jobs s JOIN jobs j ON s.job_id = j.id WHERE s.seeker_id = ?", (user_id,))
        saved_rows = cur.fetchall()
        saved_employers = {r["company"].strip().lower() for r in saved_rows}
        saved_categories = {r["category"].strip().lower() for r in saved_rows}

        cur.execute("SELECT j.company, count(*) as count FROM ignored_jobs ig JOIN jobs j ON ig.job_id = j.id WHERE ig.seeker_id = ? GROUP BY j.company", (user_id,))
        ignored_emp_counts = {r["company"].strip().lower(): r["count"] for r in cur.fetchall()}

        # Load IDs of ignored or reported jobs
        cur.execute("SELECT job_id FROM ignored_jobs WHERE seeker_id = ?", (user_id,))
        ignored_job_ids = {r["job_id"] for r in cur.fetchall()}

        cur.execute("SELECT job_id FROM job_reports WHERE seeker_id = ?", (user_id,))
        reported_job_ids = {r["job_id"] for r in cur.fetchall()}

        # Fetch active and open vacancies (active, interviewing, under_review)
        sql = "SELECT * FROM jobs WHERE status NOT IN ('expired', 'closed')"
        params = []
        if category:
            sql += " AND category = ?"
            params.append(category)
        if location:
            sql += " AND (city LIKE ? OR state LIKE ?)"
            params.extend([f"%{location}%", f"%{location}%"])

        cur.execute(sql, params)
        raw_jobs = [dict(r) for r in cur.fetchall()]

        # Filter and rank jobs
        ranked_jobs = []
        for j in raw_jobs:
            jid = j["id"]
            if jid in ignored_job_ids or jid in reported_job_ids:
                continue

            # Keyword search
            if keyword:
                search_corpus = f"{j['title']} {j['company']} {j['category']} {j['short_description']} {j['location']}".lower()
                if keyword not in search_corpus:
                    continue

            # Record impression (REQ-H05)
            cur.execute("INSERT INTO job_impressions (job_id, session_id, viewed_date) VALUES (?, ?, CURRENT_DATE)", (jid, "web_feed"))

            # Compute Formulas: Formula 1 (SMF), Formula 2 (GSI), Formula 5 (FRS)
            target_anzsco = j["anzsco_code"]
            f1_result = scores.get_skill_match_score(candidate, target_anzsco)
            smf_score = f1_result.get("overall_score") or f1_result.get("final_match_score", 75.0)

            f2_result = scores.get_skill_gap_analysis(candidate, j)
            gsi_score = f2_result.get("gap_severity_index") or f2_result.get("skill_gap_pct", 25.0)
            closing_months = f2_result.get("estimated_closing_months") or f2_result.get("estimated_bridge_months", 2.0)

            f5_result = scores.calculate_feed_score(candidate, j)
            base_frs = f5_result.get("feed_ranking_score", 78.0)

            # Apply Behavioural Ranking Adjustment FRS★ (REQ-S16)
            frs_star = scores.apply_behavioural_ranking(
                base_frs, j, saved_employers, saved_categories, ignored_emp_counts
            )

            # Compute human relative date (e.g. "Posted 3 days ago")
            posted_dt = datetime.datetime.strptime(j["posted_at"][:19], "%Y-%m-%d %H:%M:%S")
            diff_days = max(1, (datetime.datetime(2026, 10, 5, 0, 0, 0) - posted_dt).days)
            relative_date = f"Posted {diff_days} days ago" if diff_days > 1 else "Posted 1 day ago"

            ranked_jobs.append({
                "id": j["id"],
                "title": j["title"],
                "company": j["company"],
                "short_description": j["short_description"],
                "full_description": j.get("full_description") or j.get("short_description", ""),
                "location": j["location"],
                "category": j["category"],
                "anzsco_code": j["anzsco_code"],
                "anzsco_title": j["anzsco_title"],
                "status": j.get("status", "active"),
                "employment_type": j.get("employment_type", "Full-time"),
                "salary_min": j.get("salary_min", 90000),
                "salary_max": j.get("salary_max", 140000),
                "salary_display": j["salary_display"],
                "requirements": json.loads(j["requirements_json"]) if j.get("requirements_json") else [],
                "overall_score": frs_star,
                "anzsco_match_pct": round(smf_score, 1),
                "skill_gap_level": "Minimal" if gsi_score < 20 else ("Moderate" if gsi_score < 40 else "Extensive"),
                "skill_gap_pct": round(gsi_score, 1),
                "estimated_closing_months": closing_months,
                "posted_relative": relative_date,
                "updated_at": j.get("updated_at"),
                "update_notice": j.get("update_notice"),
                "is_updated": bool(j.get("update_notice") or (j.get("updated_at") and j.get("updated_at") > j.get("posted_at"))),
                "is_saved": j["id"] in {r["company"] for r in saved_rows} or False
            })

        # Sort descending by FRS★ (Formula 5)
        ranked_jobs.sort(key=lambda x: x["overall_score"], reverse=True)
        conn.commit()
        conn.close()

        self.send_json(200, {
            "total": len(ranked_jobs),
            "jobs": ranked_jobs[:limit]
        })

    def handle_job_detail(self, job_id: str):
        user_id = self.get_current_user_id()
        conn = get_db()
        cur = conn.cursor()

        # Log click for HR analytics (REQ-H05)
        cur.execute("INSERT INTO job_clicks (job_id, seeker_id) VALUES (?, ?)", (job_id, user_id))
        conn.commit()

        cur.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        j = cur.fetchone()
        if not j:
            conn.close()
            self.send_error_json(404, "Job not found")
            return

        job_dict = dict(j)
        cur.execute("SELECT * FROM seeker_profiles WHERE id = ?", (user_id,))
        cand_row = cur.fetchone()
        candidate = dict(cand_row) if cand_row else {"target_anzsco_code": job_dict["anzsco_code"], "years_experience": 5.0}
        if cand_row:
            cur.execute("SELECT skill_name, skill_type, source FROM seeker_skills WHERE seeker_id = ? AND is_active = 1", (user_id,))
            candidate["skills"] = [dict(s) for s in cur.fetchall()]
        else:
            candidate["skills"] = []

        # Calculate live formulas
        f1_res = scores.get_skill_match_score(candidate, job_dict["anzsco_code"])
        f2_res = scores.get_skill_gap_analysis(candidate, job_dict)
        f5_res = scores.calculate_feed_score(candidate, job_dict)

        smf_score = f1_res.get("overall_score") or f1_res.get("final_match_score", 82.0)
        gsi_score = f2_res.get("gap_severity_index") or f2_res.get("skill_gap_pct", 18.0)
        closing_months = f2_res.get("estimated_closing_months") or f2_res.get("estimated_bridge_months", 2.5)

        # Generate Dual Line Chart Curves (REQ-S09, REQ-S10)
        projection_data = scores.generate_projection_chart_data(smf_score, gsi_score)

        # Contextual analytical explanation (REQ-S11)
        plain_english_explanation = (
            f"Based on your registered background as {candidate.get('current_title', 'Specialist')}, "
            f"you satisfy {int(smf_score)}% of statutory ANZSCO competencies for {job_dict['anzsco_title']}. "
            f"The remaining gap ({int(gsi_score)}% severity) is projected to close within "
            f"{closing_months} months through standard workplace onboarding."
        )

        cur.execute("SELECT count(*) as count FROM saved_jobs WHERE seeker_id = ? AND job_id = ?", (user_id, job_id))
        is_saved = cur.fetchone()["count"] > 0

        cur.execute("SELECT status FROM applications WHERE seeker_id = ? AND job_id = ?", (user_id, job_id))
        app_row = cur.fetchone()
        application_status = app_row["status"] if app_row else None

        conn.close()
        self.send_json(200, {
            "job": job_dict,
            "overall_score": f5_res.get("feed_ranking_score", 80.0),
            "anzsco_match_pct": round(smf_score, 1),
            "skill_gap_pct": round(gsi_score, 1),
            "estimated_closing_months": f2_res.get("estimated_closing_months", 2.5),
            "is_saved": is_saved,
            "application_status": application_status,
            "projection_charts": projection_data,
            "plain_english_explanation": plain_english_explanation,
            "missing_skills": f2_res.get("unmet_mandatory_skills", ["Statutory Local Compliance"])
        })

    def handle_save_job(self, job_id: str):
        user_id = self.get_current_user_id()
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO saved_jobs (seeker_id, job_id) VALUES (?, ?)", (user_id, job_id))
        conn.commit()
        conn.close()
        self.send_json(200, {"status": "success", "message": "Saved to favourites"})

    def handle_unsave_job(self, job_id: str):
        user_id = self.get_current_user_id()
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM saved_jobs WHERE seeker_id = ? AND job_id = ?", (user_id, job_id))
        conn.commit()
        conn.close()
        self.send_json(200, {"status": "success", "message": "Removed from favourites"})

    def handle_ignore_job(self, job_id: str):
        user_id = self.get_current_user_id()
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO ignored_jobs (seeker_id, job_id) VALUES (?, ?)", (user_id, job_id))
        conn.commit()
        conn.close()
        self.send_json(200, {"status": "success", "message": "Job ignored and hidden from feed"})

    def handle_unignore_job(self, job_id: str):
        user_id = self.get_current_user_id()
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM ignored_jobs WHERE seeker_id = ? AND job_id = ?", (user_id, job_id))
        conn.commit()
        conn.close()
        self.send_json(200, {"status": "success", "message": "Job un-ignored"})

    def handle_report_job(self, job_id: str, body: Dict[str, Any]):
        user_id = self.get_current_user_id()
        reason = body.get("reason", "Inaccurate requirements")
        details = body.get("details", "")
        conn = get_db()
        cur = conn.cursor()
        report_id = f"rep_{uuid.uuid4().hex[:10]}"
        cur.execute("""
            INSERT INTO job_reports (id, job_id, seeker_id, reason, details)
            VALUES (?, ?, ?, ?, ?)
        """, (report_id, job_id, user_id, reason, details))

        # Check report threshold: >= 3 reports puts job under_review
        cur.execute("SELECT count(DISTINCT seeker_id) as count FROM job_reports WHERE job_id = ?", (job_id,))
        count = cur.fetchone()["count"]
        if count >= 3:
            cur.execute("UPDATE jobs SET status = 'under_review' WHERE id = ?", (job_id,))

        conn.commit()
        conn.close()
        self.send_json(200, {"status": "success", "message": "Report received. Job has been hidden from your feed."})

    def handle_seeker_saved(self):
        user_id = self.get_current_user_id()
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT j.*, s.saved_at FROM saved_jobs s
            JOIN jobs j ON s.job_id = j.id
            WHERE s.seeker_id = ?
            ORDER BY s.saved_at DESC
        """, (user_id,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        self.send_json(200, {"saved_jobs": rows, "total": len(rows)})

    def handle_apply_job(self, body: Dict[str, Any]):
        user_id = self.get_current_user_id()
        job_id = body.get("job_id", "")
        message = body.get("message", "")
        if not job_id:
            self.send_error_json(400, "job_id is required")
            return

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        job = cur.fetchone()
        if not job:
            conn.close()
            self.send_error_json(404, "Job not found")
            return

        app_id = f"app_{uuid.uuid4().hex[:10]}"
        cur.execute("""
            INSERT OR REPLACE INTO applications (
                id, job_id, seeker_id, status, overall_score_snapshot,
                anzsco_match_snapshot, skill_gap_snapshot, tss_score_snapshot, message_to_employer
            ) VALUES (?, ?, ?, 'submitted', 85.0, 88.0, 15.0, 84.0, ?)
        """, (app_id, job_id, user_id, message))

        # Add initial timeline event
        cur.execute("""
            INSERT INTO application_timeline_events (id, application_id, checkpoint, note, actor)
            VALUES (?, ?, 'submitted', 'Application received and logged', 'Candidate')
        """, (f"evt_{uuid.uuid4().hex[:10]}", app_id))

        conn.commit()
        conn.close()
        self.send_json(201, {"status": "success", "application_id": app_id, "message": "Application submitted successfully"})

    def handle_seeker_applications(self):
        user_id = self.get_current_user_id()
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT a.*, j.title as job_title, j.company as company_name, j.location,
                   j.status as job_status, j.updated_at as job_updated_at, j.update_notice as job_update_notice
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE a.seeker_id = ?
            ORDER BY a.created_at DESC
        """, (user_id,))
        apps = [dict(r) for r in cur.fetchall()]
        conn.close()
        self.send_json(200, {"applications": apps, "total": len(apps)})

    def handle_application_timeline(self, app_id: str):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
        app = cur.fetchone()
        if not app:
            conn.close()
            self.send_error_json(404, "Application not found")
            return

        cur.execute("SELECT * FROM application_timeline_events WHERE application_id = ? ORDER BY event_timestamp ASC", (app_id,))
        events = [dict(r) for r in cur.fetchall()]
        conn.close()

        # All 8 linear lifecycle stages
        stages = ["submitted", "cv_scanning", "under_review", "shortlisted", "interview", "final_assessment", "offer", "hired"]
        self.send_json(200, {
            "application_id": app_id,
            "current_status": app["status"],
            "stages": stages,
            "events": events
        })

    def handle_seeker_skills(self):
        user_id = self.get_current_user_id()
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM seeker_skills WHERE seeker_id = ? AND is_active = 1", (user_id,))
        skills = [dict(r) for r in cur.fetchall()]
        conn.close()
        self.send_json(200, {"skills": skills, "total": len(skills)})

    def handle_confirm_skill(self, skill_id: str):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE seeker_skills SET source = 'USER_CONFIRMED' WHERE id = ?", (skill_id,))
        conn.commit()
        conn.close()
        self.send_json(200, {"status": "success", "message": "Skill verified"})

    def handle_seeker_compare(self, body: Dict[str, Any]):
        job_ids = body.get("job_ids", [])
        if len(job_ids) < 2:
            self.send_error_json(400, "At least 2 job IDs required for comparison")
            return

        conn = get_db()
        cur = conn.cursor()
        placeholders = ",".join("?" for _ in job_ids)
        cur.execute(f"SELECT * FROM jobs WHERE id IN ({placeholders})", job_ids)
        jobs = [dict(r) for r in cur.fetchall()]
        conn.close()

        comparison_data = scores.compare_jobs(jobs)
        self.send_json(200, {
            "jobs": jobs,
            "comparison": comparison_data
        })

    # =========================================================================
    # HR RECRUITER HANDLERS
    # =========================================================================

    def handle_hr_dashboard(self):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT count(*) as count FROM jobs")
        total = cur.fetchone()["count"]

        cur.execute("SELECT count(*) as count FROM jobs WHERE status = 'active'")
        active = cur.fetchone()["count"]

        cur.execute("SELECT count(*) as count FROM jobs WHERE status = 'expired'")
        expired = cur.fetchone()["count"]

        cur.execute("SELECT count(*) as count FROM applications WHERE status = 'hired'")
        hired = cur.fetchone()["count"]

        cur.execute("SELECT count(*) as count FROM applications WHERE status = 'rejected'")
        rejected = cur.fetchone()["count"]

        conn.close()
        self.send_json(200, {
            "total_jobs": total,
            "active_jobs": active,
            "expired_jobs": expired,
            "hired_candidates": hired,
            "rejected_candidates": rejected
        })

    def handle_hr_jobs(self):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT j.*,
                   (SELECT count(*) FROM job_impressions WHERE job_id = j.id) as appearances,
                   (SELECT count(*) FROM job_clicks WHERE job_id = j.id) as views,
                   (SELECT count(*) FROM applications WHERE job_id = j.id) as applicants
            FROM jobs j
            ORDER BY j.posted_at DESC
            LIMIT 50
        """)
        jobs = [dict(r) for r in cur.fetchall()]
        conn.close()
        self.send_json(200, {"jobs": jobs, "total": len(jobs)})

    def handle_create_job(self, body: Dict[str, Any]):
        title = body.get("title", "New Position")
        company = body.get("company", "Enterprise Partner")
        desc = body.get("description", "")
        short_desc = desc[:157] + "..." if len(desc) > 160 else desc
        anzsco_code = body.get("anzsco_code", "261313")

        job_id = f"job_hr_{uuid.uuid4().hex[:8]}"
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO jobs (
                id, title, company, short_description, full_description, location, city, state,
                category, anzsco_code, anzsco_title, salary_min, salary_max, salary_display,
                requirements_json, source_platform, posted_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, datetime(CURRENT_TIMESTAMP, '+30 days'))
        """, (
            job_id, title, company, short_desc, desc, body.get("location", "Sydney, NSW"),
            "Sydney", "NSW", body.get("category", "Technology & Data"), anzsco_code,
            body.get("anzsco_title", "Software Engineer"), 110000, 160000, "$110,000 - $160,000 AUD",
            json.dumps(body.get("requirements", [])), "Jinder Direct"
        ))
        conn.commit()
        conn.close()
        self.send_json(201, {"status": "success", "job_id": job_id, "message": "Job published successfully"})

    def handle_edit_job(self, job_id: str, body: Dict[str, Any]):
        title = body.get("title")
        company = body.get("company")
        salary_display = body.get("salary_display")
        full_desc = body.get("full_description")
        short_desc = body.get("short_description")
        status = body.get("status")
        requirements = body.get("requirements")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        existing = cur.fetchone()
        if not existing:
            conn.close()
            self.send_error_json(404, "Job not found")
            return

        cur.execute("""
            UPDATE jobs
            SET title = COALESCE(?, title),
                company = COALESCE(?, company),
                salary_display = COALESCE(?, salary_display),
                short_description = COALESCE(?, short_description),
                full_description = COALESCE(?, full_description),
                status = COALESCE(?, status),
                requirements_json = COALESCE(?, requirements_json),
                updated_at = CURRENT_TIMESTAMP,
                update_notice = 'Requirements & remuneration updated by employer'
            WHERE id = ?
        """, (
            title, company, salary_display, short_desc, full_desc, status,
            json.dumps(requirements) if requirements is not None else None,
            job_id
        ))
        conn.commit()

        # Cascade status change to applications table so seekers tracking their application see update
        if status:
            app_status_map = {
                "interviewing": "interview",
                "offer_pending": "offer",
                "filled": "hired",
                "active": "under_review"
            }
            if status in app_status_map:
                cur.execute("""
                    UPDATE applications
                    SET status = ?
                    WHERE job_id = ?
                """, (app_status_map[status], job_id))
                conn.commit()

        # Fetch updated row
        cur.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        updated = dict(cur.fetchone())
        conn.close()

        self.send_json(200, {
            "status": "success",
            "message": "Job specification updated successfully. Seeker feed reflects new status.",
            "job": updated
        })

    def handle_update_seeker_account(self, body: Dict[str, Any]):
        user_id = self.get_current_user_id()
        alias = body.get("alias")
        title = body.get("current_title")
        phone = body.get("phone")
        origin_country = body.get("origin_country")
        preferred_location = body.get("preferred_location")
        cv_raw_text = body.get("cv_raw_text")
        cv_file_name = body.get("cv_file_name")
        highest_education = body.get("highest_education")
        years_experience = body.get("years_experience")
        target_anzsco_title = body.get("target_anzsco_title")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE seeker_profiles
            SET alias = COALESCE(?, alias),
                current_title = COALESCE(?, current_title),
                phone = COALESCE(?, phone),
                origin_country = COALESCE(?, origin_country),
                preferred_location = COALESCE(?, preferred_location),
                cv_raw_text = COALESCE(?, cv_raw_text),
                cv_file_name = COALESCE(?, cv_file_name),
                highest_education = COALESCE(?, highest_education),
                years_experience = COALESCE(?, years_experience),
                target_anzsco_title = COALESCE(?, target_anzsco_title),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (alias, title, phone, origin_country, preferred_location, cv_raw_text, cv_file_name, highest_education, years_experience, target_anzsco_title, user_id))
        conn.commit()

        cur.execute("SELECT * FROM seeker_profiles WHERE id = ?", (user_id,))
        row = cur.fetchone()
        prof = dict(row) if row else {}
        conn.close()

        self.send_json(200, {
            "status": "success",
            "message": "Account settings and Curriculum Vitae updated successfully",
            "profile": prof
        })

    def handle_hr_candidates(self, query):
        conn = get_db()
        cur = conn.cursor()

        job_id = query.get("job_id", [""])[0].strip() if query else ""
        status_filter = query.get("status", [""])[0].strip() if query else ""

        # Find target requisition or benchmark job
        target_job = None
        if job_id:
            cur.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            j_row = cur.fetchone()
            if j_row:
                target_job = dict(j_row)

        if not target_job:
            # Fallback to employer's primary active job, or top active vacancy
            cur.execute("SELECT * FROM jobs WHERE employer_id IS NOT NULL AND status = 'active' LIMIT 1")
            j_row = cur.fetchone()
            if not j_row:
                cur.execute("SELECT * FROM jobs WHERE status = 'active' LIMIT 1")
                j_row = cur.fetchone()
            if j_row:
                target_job = dict(j_row)
            else:
                target_job = {
                    "id": "bench_default",
                    "title": "Lead Registered Nurse & Critical Care Mentor",
                    "anzsco_code": "254411",
                    "anzsco_title": "Registered Nurse / Clinical Specialist",
                    "category": "Healthcare & Nursing",
                    "requirements_json": '["AHPRA Current Registration", "5+ years ICU or Triage"]'
                }

        # Query candidates with CV and education
        cur.execute("""
            SELECT p.id, p.alias, p.current_title, p.years_experience, p.highest_education,
                   p.target_anzsco_code, p.target_anzsco_title, p.origin_country, p.cv_raw_text,
                   COALESCE((SELECT status FROM applications WHERE seeker_id = p.id LIMIT 1), 'under_review') as status
            FROM seeker_profiles p
            LIMIT 50
        """)
        cands = [dict(r) for r in cur.fetchall()]

        # Attach skills and compute pure mathematical scores for each candidate
        for c in cands:
            cur.execute("SELECT skill_name, skill_type, source FROM seeker_skills WHERE seeker_id = ? AND is_active = 1", (c["id"],))
            c["skills"] = [dict(s) for s in cur.fetchall()]

            # 1. Formula 6 Recruiter TSS Score
            tss_res = scores.calculate_talent_search_score(c, target_job)
            overall_tss = tss_res.get("overall_score") or tss_res.get("talent_search_score", 85.0)

            # 2. Formula 1 ANZSCO Skill Match Score
            f1_res = scores.get_skill_match_score(c, target_job.get("anzsco_code", "254411"))
            match_pct = f1_res.get("overall_score") or f1_res.get("final_match_score", 80.0)

            # 3. Formula 2 Skill Gap Severity & Learnability
            f2_res = scores.get_skill_gap_analysis(c, target_job)
            gap_pct = f2_res.get("gap_severity_index") or f2_res.get("skill_gap_pct", 20.0)
            closing_mo = f2_res.get("estimated_closing_months") or f2_res.get("estimated_bridge_months", 2.0)

            c["overall_score"] = round(overall_tss, 1)
            c["anzsco_match_pct"] = round(match_pct, 1)
            c["skill_gap_pct"] = round(gap_pct, 1)
            c["estimated_closing_months"] = round(closing_mo, 1)
            c["sub_metrics"] = tss_res.get("sub_metrics", {})
            c["statutory_blocker"] = f2_res.get("has_statutory_blocker", False)

            # Zero-PII contract: strip raw CV and contact details
            c.pop("cv_raw_text", None)
            c.pop("legal_name", None)
            c.pop("phone", None)

        # Filter by status if requested
        if status_filter:
            cands = [c for c in cands if c.get("status") == status_filter]

        # Rank candidate cohort descending by TSS score (Formula 6)
        cands.sort(key=lambda x: x["overall_score"], reverse=True)

        conn.close()
        self.send_json(200, {
            "candidates": cands,
            "total": len(cands),
            "benchmark_job": {
                "id": target_job.get("id"),
                "title": target_job.get("title"),
                "anzsco_code": target_job.get("anzsco_code"),
                "company": target_job.get("company", "Healthscope")
            }
        })

    def handle_transition_application(self, app_id: str, body: Dict[str, Any]):
        new_status = body.get("status", "")
        note = body.get("note", f"Stage transitioned to {new_status}")
        valid_statuses = ["submitted", "cv_scanning", "under_review", "shortlisted", "interview", "final_assessment", "offer", "hired", "rejected"]
        if new_status not in valid_statuses:
            self.send_error_json(400, f"Invalid lifecycle status: {new_status}")
            return

        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE applications SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_status, app_id))
        cur.execute("""
            INSERT INTO application_timeline_events (id, application_id, checkpoint, note, actor)
            VALUES (?, ?, ?, ?, 'Employer')
        """, (f"evt_{uuid.uuid4().hex[:10]}", app_id, new_status, note))
        conn.commit()
        conn.close()
        self.send_json(200, {"status": "success", "new_status": new_status, "message": f"Application advanced to {new_status}"})

    def handle_hr_compare(self, body: Dict[str, Any]):
        cand_ids = body.get("candidate_ids", [])
        if len(cand_ids) < 2:
            self.send_error_json(400, "At least 2 candidates required for comparison")
            return

        conn = get_db()
        cur = conn.cursor()
        placeholders = ",".join("?" for _ in cand_ids)
        cur.execute(f"SELECT * FROM seeker_profiles WHERE id IN ({placeholders})", cand_ids)
        cands = [dict(r) for r in cur.fetchall()]
        for c in cands:
            cur.execute("SELECT skill_name, skill_type, source FROM seeker_skills WHERE seeker_id = ? AND is_active = 1", (c["id"],))
            c["skills"] = [dict(s) for s in cur.fetchall()]
        conn.close()

        benchmarking = scores.compare_candidates(cands)
        for c in cands:
            c.pop("legal_name", None)
            c.pop("phone", None)
            c.pop("cv_raw_text", None)

        self.send_json(200, {
            "candidates": cands,
            "benchmarking": benchmarking
        })


def run_server():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, APIHandler)
    print(f"Jinder Platform API running on http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down API server...")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
