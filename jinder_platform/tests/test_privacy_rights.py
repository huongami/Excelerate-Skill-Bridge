"""The user's control over their data: export a copy and delete the account (AI_Rule Rule 5, item 7)."""
import json
import unittest
from datetime import datetime, timedelta, timezone

import helpers as H
from jinder import parsing
from test_talent_flow import onboard


class DataRightsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api

    def test_export_has_the_users_data_and_no_secrets(self):
        t = self.p.sign_up_and_in(name="Export Person", email="export.person@example.test")
        onboard(self.p, t)
        s, jobs = self.api.call("GET", "/jobs?pageSize=2", token=t["token"])
        self.api.call("PUT", f"/bookmarks/{jobs['items'][0]['id']}", token=t["token"])
        self.api.call("POST", "/applications", {"jobId": jobs["items"][1]["id"], "note": "hello"}, token=t["token"])
        s, data = self.api.call("GET", "/me/export", token=t["token"])
        self.assertEqual(s, 200)
        self.assertEqual(data["account"]["email"], "export.person@example.test")
        self.assertTrue(data["account"]["profile"]["translation"])
        self.assertEqual(len(data["bookmarks"]), 1)
        self.assertEqual(len(data["applications"]), 1)
        text = json.dumps(data).lower()
        for banned in ("password", "scrypt$", t["token"]):
            self.assertNotIn(banned, text)
        self.assertEqual(self.api.call("GET", "/me/export")[0], 401)

    def test_employer_export_has_no_identity_of_talent(self):
        e = self.p.sign_up_and_in(role="recruiter", company="Export Co")
        t = self.p.sign_up_and_in(name="Hidden Person", email="hidden.person@example.test")
        onboard(self.p, t)
        closes = (datetime.now(timezone.utc) + timedelta(days=9)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        s, job = self.api.call("POST", "/recruiter/jobs", {"title": "Export Analyst", "category": "Data", "location": "Sydney", "type": "Full-time", "skills": ["SQL"],
                                                           "targetApplicants": 2, "closesAt": closes, "description": "Analyse data and report on it every single week."}, token=e["token"])
        self.api.call("POST", "/applications", {"jobId": job["id"]}, token=t["token"])
        s, data = self.api.call("GET", "/me/export", token=e["token"])
        self.assertEqual((len(data["jobs"]), len(data["applications"])), (1, 1))
        self.assertNotIn("Hidden", json.dumps(data))
        self.assertNotIn("hidden.person", json.dumps(data))

    def test_delete_the_account(self):
        t = self.p.sign_up_and_in(name="Delete Person", email="delete.person@example.test")
        onboard(self.p, t)
        c = self.p.conn()
        stored = [r["stored_name"] for r in c.execute("SELECT stored_name FROM cv_files WHERE user_id = ?", (t["user"]["id"],)).fetchall()]
        self.assertTrue(stored and parsing.upload_path(stored[0]).exists())
        e = self.p.sign_up_and_in(role="recruiter")
        s, before = self.api.call("GET", "/recruiter/candidates", token=e["token"])
        s, r = self.api.call("POST", "/me/delete", {"password": "wrong password"}, token=t["token"])
        self.assertEqual((s, r["error"]["fields"]["password"]), (400, "Your password is not correct."))
        self.assertEqual(self.api.call("GET", "/me", token=t["token"])[0], 200)
        self.assertEqual(self.api.call("POST", "/me/delete", {"password": t["password"]}, token=t["token"]), (204, None))
        self.assertEqual(self.api.call("GET", "/me", token=t["token"])[0], 401)
        self.assertEqual(self.api.call("POST", "/auth/login", {"email": t["email"], "password": t["password"]})[0], 401)
        self.assertFalse(parsing.upload_path(stored[0]).exists())
        for table in ("users", "profiles", "translated_skills", "cv_files", "sessions"):
            col = "id" if table == "users" else ("user_id")
            self.assertEqual(c.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} = ?", (t["user"]["id"],)).fetchone()[0], 0, table)
        s, after = self.api.call("GET", "/recruiter/candidates", token=e["token"])
        self.assertEqual(after["total"], before["total"] - 1)
        # the same email can be used again
        self.p.sign_up_and_in(name="Delete Person", email="delete.person@example.test")

    def test_deleting_an_employer_removes_their_jobs(self):
        e = self.p.sign_up_and_in(role="recruiter", company="Gone Co Pty Ltd")
        t = self.p.sign_up_and_in()
        onboard(self.p, t)
        closes = (datetime.now(timezone.utc) + timedelta(days=9)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        s, job = self.api.call("POST", "/recruiter/jobs", {"title": "Gone Analyst", "category": "Data", "location": "Sydney", "type": "Full-time", "skills": ["SQL"],
                                                           "targetApplicants": 2, "closesAt": closes, "description": "Analyse data and report on it every single week."}, token=e["token"])
        self.api.call("POST", "/applications", {"jobId": job["id"]}, token=t["token"])
        self.assertEqual(self.api.call("POST", "/me/delete", {"password": e["password"]}, token=e["token"])[0], 204)
        self.assertEqual(self.api.call("GET", f"/jobs/{job['id']}", token=t["token"])[0], 404)
        s, apps = self.api.call("GET", "/applications", token=t["token"])
        self.assertEqual(apps["items"], [])


if __name__ == "__main__":
    unittest.main()
