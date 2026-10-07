"""The employer journey and the hiring state machine (Features 5, 6, 7), and the privacy of every employer response."""
import json
import time
import unittest
from datetime import datetime, timedelta, timezone

import helpers as H
from test_talent_flow import onboard


def iso_in(days=0, hours=0):
    return (datetime.now(timezone.utc) + timedelta(days=days, hours=hours)).strftime("%Y-%m-%dT%H:%M:%S.000Z")


JOB = {"title": "Data Engineer", "category": "Data", "location": "Melbourne", "type": "Full-time",
       "salary": "$130,000 – $150,000 per year", "skills": ["SQL", "Python", "Apache Spark", "Data modelling", "Microsoft Excel", "Stakeholder management"],
       "description": "We need a data engineer who builds and runs data pipelines in Python and SQL, and works with analysts to keep the reports correct.",
       "targetApplicants": 5}


class EmployerBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api

    def employer(self):
        return self.p.sign_up_and_in(role="recruiter", company="Orbit Data Pty Ltd")

    def post_job(self, e, **over):
        s, j = self.api.call("POST", "/recruiter/jobs", {**JOB, "closesAt": iso_in(days=20), **over}, token=e["token"])
        self.assertEqual(s, 200, j)
        return j

    def talent(self, **kw):
        t = self.p.sign_up_and_in(**kw)
        onboard(self.p, t)
        return t


class JobPostingTests(EmployerBase):
    def test_post_validation(self):
        e = self.employer()
        s, r = self.api.call("POST", "/recruiter/jobs", {}, token=e["token"])
        f = r["error"]["fields"]
        self.assertEqual(f["title"], "Enter a job title.")
        self.assertEqual(f["category"], "Choose a domain.")
        self.assertEqual(f["location"], "Choose a location.")
        self.assertEqual(f["type"], "Choose a work type.")
        self.assertEqual(f["description"], "Write a description of at least 30 characters.")
        self.assertEqual(f["skills"], "Add 1 to 12 required skills.")
        self.assertEqual(f["targetApplicants"], "Enter a number from 1 to 10000.")
        self.assertEqual(f["closesAt"], "Choose a close date.")
        s, r = self.api.call("POST", "/recruiter/jobs", {**JOB, "closesAt": iso_in(days=-1)}, token=e["token"])
        self.assertEqual(r["error"]["fields"], {"closesAt": "The close date must be in the future."})
        s, r = self.api.call("POST", "/recruiter/jobs", {**JOB, "closesAt": iso_in(days=3), "skills": ["a"] * 13, "targetApplicants": 0}, token=e["token"])
        self.assertEqual(set(r["error"]["fields"]), {"targetApplicants"})  # 13 copies of one skill count as one skill

    def test_post_list_badge_edit(self):
        e = self.employer()
        j = self.post_job(e, closesAt=iso_in(days=3))
        self.assertEqual((j["badge"], j["label"], j["applicantCount"], j["awaitingCount"]), ("closing", "Closes in 3 days", 0, 0))
        time.sleep(0.05)       # the clock of Windows ticks every few milliseconds: two jobs in one tick have the same time, and the list then sorts them by id (a flaky test, found by QA)
        j2 = self.post_job(e, title="Senior Data Engineer", closesAt=iso_in(days=30))
        self.assertEqual((j2["badge"], j2["label"]), ("open", "Open"))
        s, lst = self.api.call("GET", "/recruiter/jobs", token=e["token"])
        self.assertEqual([i["id"] for i in lst["items"]], [j2["id"], j["id"]])  # newest first
        s, one = self.api.call("GET", f"/recruiter/jobs/{j['id']}", token=e["token"])
        self.assertIn("description", one)
        # the job joins the catalogue
        t = self.talent()
        s, found = self.api.call("GET", "/jobs?q=Orbit", token=t["token"])
        self.assertIn(j["id"], [x["id"] for x in found["items"]])
        s, d = self.api.call("GET", f"/jobs/{j['id']}", token=t["token"])
        self.assertEqual(d["company"], "Orbit Data Pty Ltd")
        self.assertTrue(d["anzsco"], "the occupation code is taken from the catalogue")
        self.assertNotIn("targetApplicants", d)
        # nobody else can read or change it
        other = self.employer()
        self.assertEqual(self.api.call("GET", f"/recruiter/jobs/{j['id']}", token=other["token"])[0], 404)
        self.assertEqual(self.api.call("PATCH", f"/recruiter/jobs/{j['id']}", {"title": "Hacked job"}, token=other["token"])[0], 404)

    def test_edit_notifies_everyone_who_applied(self):
        e = self.employer()
        j = self.post_job(e)
        t = self.talent()
        s, a = self.api.call("POST", "/applications", {"jobId": j["id"]}, token=t["token"])
        self.assertEqual(s, 200)
        s, r = self.api.call("PATCH", f"/recruiter/jobs/{j['id']}", {"closesAt": iso_in(days=-2)}, token=e["token"])
        self.assertEqual(r["error"]["fields"], {"closesAt": "The close date must be in the future."})
        s, r = self.api.call("PATCH", f"/recruiter/jobs/{j['id']}", {"description": "We now also need on-call cover and a strong grasp of data lakehouse design.", "skills": ["Python", "Data lakehouse"]}, token=e["token"])
        self.assertEqual((s, r["skills"]), (200, ["Python", "Data lakehouse"]))
        s, n = self.api.call("GET", "/notifications", token=t["token"])
        edited = [x for x in n["items"] if x["type"] == "job_edited"]
        self.assertEqual(len(edited), 1)
        self.assertEqual(edited[0]["link"], f"/applications/{a['id']}")
        self.assertEqual(edited[0]["title"], "Data Engineer was updated")

    def test_suggest_skills(self):
        e = self.employer()
        s, r = self.api.call("POST", "/recruiter/jobs/suggest-skills", {"title": "Data Analyst", "description": "Build dashboards in Power BI, write SQL queries and clean data with Python."}, token=e["token"])
        self.assertEqual(s, 200)
        for name in ("SQL", "Python", "Power BI"):
            self.assertIn(name, r["skills"])
        self.assertLessEqual(len(r["skills"]), 10)

    def test_post_from_a_file(self):
        e = self.employer()
        text = ["Senior Data Engineer – Streaming Platform",
                "Join our team in Perth as a Senior Data Engineer. You will build Kafka and Spark pipelines in Python and SQL on AWS, and design the data models. Contract. $900 - $1,100 per day."]
        s, up = self.api.upload("/recruiter/jobs/import", "jd.docx", H.make_docx(text), e["token"])
        self.assertEqual(s, 202)
        for _ in range(100):
            s, res = self.api.call("GET", f"/recruiter/jobs/import/{up['parse']['id']}", token=e["token"])
            if res["status"] != "parsing":
                break
            time.sleep(0.05)
        self.assertEqual(res["status"], "done")
        f = res["result"]["fields"]
        self.assertEqual((f["title"], f["category"], f["location"], f["type"]), ("Senior Data Engineer – Streaming Platform", "Data", "Perth", "Contract"))
        self.assertEqual(f["salary"], "$900 – $1,100 per day")
        for name in ("Apache Kafka", "Apache Spark", "Python", "SQL"):
            self.assertIn(name, f["skills"])
        self.assertEqual(res["result"]["missing"], [])
        # nothing is posted until the form is sent
        s, lst = self.api.call("GET", "/recruiter/jobs", token=e["token"])
        self.assertEqual(lst["items"], [])
        s, r = self.api.upload("/recruiter/jobs/import", "jd.txt", b"hello", e["token"])
        self.assertEqual(r["error"]["fields"]["file"], "Use a PDF or DOCX file.")
        s, up2 = self.api.upload("/recruiter/jobs/import", "bad.pdf", b"%PDF-1.4\nnothing here", e["token"])
        for _ in range(100):
            s, res2 = self.api.call("GET", f"/recruiter/jobs/import/{up2['parse']['id']}", token=e["token"])
            if res2["status"] != "parsing":
                break
            time.sleep(0.05)
        self.assertEqual(res2["status"], "failed")
        other = self.employer()
        self.assertEqual(self.api.call("GET", f"/recruiter/jobs/import/{up['parse']['id']}", token=other["token"])[0], 404)


class PipelineTests(EmployerBase):
    def test_the_full_hiring_flow(self):
        e = self.employer()
        job = self.post_job(e)
        t = self.talent(name="Zelda Quixote", email="zelda.flow@example.test")
        api, et, tt = self.api, e["token"], t["token"]
        s, a = api.call("POST", "/applications", {"jobId": job["id"], "note": "I run similar teams."}, token=tt)
        aid = a["id"]
        # the employer is told, and sees only the alias
        s, n = api.call("GET", "/notifications", token=et)
        self.assertEqual(n["items"][0]["type"], "new_application")
        self.assertEqual(n["items"][0]["link"], f"/review/{aid}")
        self.assertEqual(n["unread"], 1)
        s, lst = api.call("GET", f"/recruiter/jobs/{job['id']}/applications", token=et)
        self.assertEqual(lst["items"][0]["alias"], t["user"]["alias"])
        self.assertEqual((lst["job"]["applicantCount"], lst["job"]["awaitingCount"], lst["items"][0]["awaiting"]), (1, 1, True))
        s, ra = api.call("GET", f"/recruiter/applications/{aid}", token=et)
        self.assertIsNone(ra["identity"])
        self.assertEqual(ra["allowedNext"], ["review", "rejected"])
        # wrong moves
        s, r = api.call("POST", f"/recruiter/applications/{aid}/status", {"to": "offer"}, token=et)
        self.assertEqual((s, r["error"]["message"]), (409, "You can't move an application from Applied to Offer."))
        s, r = api.call("POST", f"/recruiter/applications/{aid}/status", {"to": "confirmed"}, token=et)
        self.assertEqual(s, 409)
        # review locks the talent's edits
        s, ra = api.call("POST", f"/recruiter/applications/{aid}/status", {"to": "review"}, token=et)
        self.assertEqual((ra["status"], ra["allowedNext"]), ("review", ["interview", "rejected"]))
        s, r = api.call("PATCH", f"/applications/{aid}", {"note": "late"}, token=tt)
        self.assertEqual((s, r["error"]["message"]), (409, "The employer is reviewing your application. You can't change it now."))
        # interview times
        for slots, msg in (([], "Offer 1 to 3 interview times."), ([iso_in(days=1)] * 4, "Offer 1 to 3 interview times."), ([iso_in(days=-1)], "Choose times in the future.")):
            s, r = api.call("POST", f"/recruiter/applications/{aid}/status", {"to": "interview", "slots": slots}, token=et)
            self.assertEqual((s, r["error"]["fields"]["slots"]), (400, msg))
        times = [iso_in(days=2), iso_in(days=3), iso_in(days=4)]
        s, ra = api.call("POST", f"/recruiter/applications/{aid}/status", {"to": "interview", "slots": times}, token=et)
        self.assertEqual((ra["status"], len(ra["slots"]), ra["canConfirmSlot"], ra["allowedNext"]), ("interview", 3, False, ["rejected"]))
        s, n = api.call("GET", "/notifications", token=tt)
        self.assertEqual(n["items"][0]["type"], "interview_slots")
        s, ta = api.call("GET", f"/applications/{aid}", token=tt)
        self.assertEqual(len(ta["slots"]), 3)
        s, lst = api.call("GET", "/applications", token=tt)
        self.assertTrue(lst["items"][0]["needsAction"])
        # the talent chooses a time and agrees to share their identity
        s, r = api.call("POST", f"/applications/{aid}/slot", {"slotId": "nope"}, token=tt)
        self.assertEqual((s, r["error"]["message"]), (409, "This time is no longer available. Choose another time."))
        s, ta = api.call("POST", f"/applications/{aid}/slot", {"slotId": ta["slots"][1]["id"], "shareIdentity": True}, token=tt)
        self.assertEqual((ta["chosenSlotId"], ta["identityShared"], ta["slotConfirmed"]), (ta["slots"][1]["id"], True, False))
        s, ra = api.call("GET", f"/recruiter/applications/{aid}", token=et)
        self.assertTrue(ra["canConfirmSlot"])
        self.assertEqual(ra["identity"], {"name": "Zelda Quixote", "email": "zelda.flow@example.test"})  # only after the talent agreed
        s, n = api.call("GET", "/notifications", token=et)
        self.assertIn("slot_chosen", [x["type"] for x in n["items"]])
        # accept before the time is confirmed: no
        self.assertEqual(ra["allowedNext"], ["rejected"])
        s, r = api.call("POST", f"/recruiter/applications/{aid}/status", {"to": "accepted"}, token=et)
        self.assertEqual((s, r["error"]["message"]), (409, "Confirm the interview time first. Then record the result."))
        s, ra = api.call("POST", f"/recruiter/applications/{aid}/confirm-slot", token=et)
        self.assertEqual((ra["slotConfirmed"], ra["allowedNext"]), (True, ["accepted", "rejected"]))
        self.assertEqual(api.call("POST", f"/recruiter/applications/{aid}/confirm-slot", token=et)[0], 409)
        s, r = api.call("POST", f"/applications/{aid}/slot", {"slotId": ta["slots"][0]["id"]}, token=tt)
        self.assertEqual((s, r["error"]["message"]), (409, "The employer has confirmed your interview time."))
        # result, offer
        s, ra = api.call("POST", f"/recruiter/applications/{aid}/status", {"to": "accepted"}, token=et)
        s, n = api.call("GET", "/notifications", token=tt)
        result = [x for x in n["items"] if x["type"] == "result"][0]
        self.assertTrue(result["email"])  # accepted and rejected also go by email
        s, r = api.call("POST", f"/recruiter/applications/{aid}/status", {"to": "offer", "offer": "short"}, token=et)
        self.assertEqual(r["error"]["fields"]["offer"], "Write the offer details (at least 10 characters).")
        s, ra = api.call("POST", f"/recruiter/applications/{aid}/status", {"to": "offer", "offer": "Full-time at $80,000. Call 0400 111 222."}, token=et)
        self.assertEqual(ra["offer"]["text"], "Full-time at $80,000. Call [phone removed].")
        self.assertEqual(ra["allowedNext"], [])
        s, ta = api.call("GET", f"/applications/{aid}", token=tt)
        self.assertEqual((ta["status"], ta["offer"]["text"]), ("offer", ra["offer"]["text"]))
        s, lst = api.call("GET", "/applications", token=tt)
        self.assertTrue(lst["items"][0]["needsAction"])
        s, ta = api.call("POST", f"/applications/{aid}/offer-reply", {"accept": True}, token=tt)
        self.assertEqual((ta["status"], ta["statusLabel"], ta["final"]), ("confirmed", "Confirmed", True))
        self.assertEqual(api.call("POST", f"/applications/{aid}/offer-reply", {"accept": True}, token=tt)[0], 409)
        # feedback from both sides. Nobody sees the other side's message to the Jinder team.
        s, r = api.call("POST", f"/applications/{aid}/feedback", {"toOther": "", "toTeam": ""}, token=tt)
        self.assertEqual(r["error"]["fields"]["form"], "Write feedback in at least one box.")
        s, ta = api.call("POST", f"/applications/{aid}/feedback", {"toOther": "Clear process. Email me at zz@example.test", "toTeam": "TEAM-NOTE-CANDIDATE"}, token=tt)
        self.assertEqual(ta["feedback"]["mine"]["toOther"], "Clear process. Email me at [email removed]")
        s, ra = api.call("POST", f"/recruiter/applications/{aid}/feedback", {"toOther": "Great interview", "toTeam": "TEAM-NOTE-EMPLOYER"}, token=et)
        self.assertEqual(ra["feedback"]["theirs"]["toOther"], "Clear process. Email me at [email removed]")
        self.assertNotIn("TEAM-NOTE-CANDIDATE", json.dumps(ra))
        s, ta = api.call("GET", f"/applications/{aid}", token=tt)
        self.assertNotIn("TEAM-NOTE-EMPLOYER", json.dumps(ta))
        self.assertEqual(ta["feedback"]["theirs"]["toOther"], "Great interview")
        # history: who and when
        who = [(h["status"], h["by"]) for h in ta["history"]]
        self.assertEqual(who[0], ("applied", "candidate"))
        self.assertIn(("review", "recruiter"), who)
        self.assertIn(("confirmed", "candidate"), who)
        self.assertTrue(all(h["at"] for h in ta["history"]))
        s, st = api.call("GET", "/stats", token=et)
        self.assertEqual(st["basic"]["totalJobs"], 1)

    def test_decline_an_offer_ends_in_rejected(self):
        e = self.employer()
        job = self.post_job(e)
        t = self.talent()
        s, a = self.api.call("POST", "/applications", {"jobId": job["id"]}, token=t["token"])
        aid = a["id"]
        self.api.call("POST", f"/recruiter/applications/{aid}/status", {"to": "review"}, token=e["token"])
        s, ra = self.api.call("POST", f"/recruiter/applications/{aid}/status", {"to": "interview", "slots": [iso_in(days=2)]}, token=e["token"])
        self.api.call("POST", f"/applications/{aid}/slot", {"slotId": ra["slots"][0]["id"], "shareIdentity": False}, token=t["token"])
        self.api.call("POST", f"/recruiter/applications/{aid}/confirm-slot", token=e["token"])
        self.api.call("POST", f"/recruiter/applications/{aid}/status", {"to": "accepted"}, token=e["token"])
        self.api.call("POST", f"/recruiter/applications/{aid}/status", {"to": "offer", "offer": "A full offer with details."}, token=e["token"])
        s, ta = self.api.call("POST", f"/applications/{aid}/offer-reply", {"accept": False}, token=t["token"])
        self.assertEqual((ta["status"], ta["statusLabel"]), ("rejected", "Not selected"))
        s, ra = self.api.call("GET", f"/recruiter/applications/{aid}", token=e["token"])
        self.assertIsNone(ra["identity"])  # the talent never agreed to share
        self.assertEqual(ra["allowedNext"], [])

    def test_reject_early_and_nobody_else_can_act(self):
        e = self.employer()
        job = self.post_job(e)
        t = self.talent()
        s, a = self.api.call("POST", "/applications", {"jobId": job["id"]}, token=t["token"])
        other = self.employer()
        self.assertEqual(self.api.call("GET", f"/recruiter/applications/{a['id']}", token=other["token"])[0], 404)
        self.assertEqual(self.api.call("POST", f"/recruiter/applications/{a['id']}/status", {"to": "review"}, token=other["token"])[0], 404)
        s, ra = self.api.call("POST", f"/recruiter/applications/{a['id']}/status", {"to": "rejected"}, token=e["token"])
        self.assertEqual((ra["status"], ra["final"]), ("rejected", True))
        s, r = self.api.call("POST", f"/recruiter/applications/{a['id']}/feedback", {"toOther": "Thanks for applying"}, token=e["token"])
        self.assertEqual(s, 200)
        s, n = self.api.call("GET", "/notifications", token=t["token"])
        self.assertEqual(n["items"][0]["type"], "feedback")
        # the system never changes a status on its own: the talent cannot move it either
        self.assertEqual(self.api.call("POST", f"/applications/{a['id']}/decline", token=t["token"])[0], 409)
        s, r = self.api.call("POST", f"/recruiter/applications/{a['id']}/feedback", {"toOther": "x"}, token=self.employer()["token"])
        self.assertEqual(s, 404)


class TalentDiscoveryTests(EmployerBase):
    def test_basic_and_premium(self):
        e = self.employer()
        job = self.post_job(e)
        s, r = self.api.call("GET", "/recruiter/candidates", token=e["token"])
        self.assertEqual(s, 200)
        self.assertEqual((r["plan"], r["limitedTo"], len(r["items"])), ("basic", 5, 5))
        self.assertGreater(r["total"], 5)
        self.assertEqual(r["job"]["id"], job["id"])
        self.assertEqual(r["skippedCount"], 0)
        coverages = [c["coverage"] for c in r["items"]]
        self.assertTrue(all(c is not None for c in coverages))
        self.assertEqual(r["page"], {"page": 1, "pageSize": 5, "total": r["total"], "totalPages": 1})   # Basic: one page of 5, the total is the real total
        first = r["items"][0]
        # version 2 adds: level, yearsExperience, certifications, awards, skillLevels, updatedAt
        self.assertEqual(set(first), {"id", "alias", "roles", "skills", "qualifications", "years", "industries", "locations", "coverage", "matched", "partial", "total", "saved", "applicationId",
                                      "level", "yearsExperience", "certifications", "awards", "skillLevels", "updatedAt"})
        self.assertEqual(first["total"], len(JOB["skills"]))
        # save, skip
        cid = first["id"]
        self.assertEqual(self.api.call("PUT", f"/recruiter/candidates/{cid}/save", token=e["token"]), (200, {"id": cid, "saved": True}))
        s, saved = self.api.call("GET", "/recruiter/candidates?view=saved", token=e["token"])
        self.assertEqual([c["id"] for c in saved["items"]], [cid])
        self.assertEqual(self.api.call("DELETE", f"/recruiter/candidates/{cid}/save", token=e["token"])[1], {"id": cid, "saved": False})
        second = r["items"][1]["id"]
        self.assertEqual(self.api.call("PUT", f"/recruiter/candidates/{second}/skip", token=e["token"])[1], {"id": second, "skipped": True})
        s, r2 = self.api.call("GET", "/recruiter/candidates", token=e["token"])
        self.assertNotIn(second, [c["id"] for c in r2["items"]])
        self.assertEqual(r2["skippedCount"], 1)
        self.assertEqual(self.api.call("DELETE", "/recruiter/candidates/skipped", token=e["token"])[1], {"ok": True})
        self.assertEqual(self.api.call("PUT", "/recruiter/candidates/nope/save", token=e["token"])[0], 404)
        # a report about a profile
        s, rep = self.api.call("POST", "/reports", {"targetType": "candidate", "targetId": cid, "reason": "not_relevant"}, token=e["token"])
        self.assertEqual(s, 200)
        # premium gate (on the server)
        s, r = self.api.call("POST", f"/recruiter/candidates/{cid}/contact", {"jobId": job["id"], "message": "Please apply, we like your skills."}, token=e["token"])
        self.assertEqual((s, r["error"]["code"]), (403, "PREMIUM_REQUIRED"))
        self.assertEqual(self.api.call("GET", f"/recruiter/compare?ids={cid},{second}&jobId={job['id']}", token=e["token"])[1]["error"]["message"],
                         "This feature is part of Premium. Upgrade in Settings to use it.")
        s, ent = self.api.call("PUT", "/entitlements", {"plan": "premium"}, token=e["token"])
        # version 2 adds crown, compareMax and benefits (see test_v2_infra.py for the benefits)
        self.assertEqual({k: v for k, v in ent.items() if k not in ("crown", "compareMax", "benefits")},
                         {"plan": "premium", "topN": None, "canContact": True, "canCompare": True, "advancedCharts": True})
        self.assertEqual((ent["crown"], ent["compareMax"]), (True, 5))
        s, r = self.api.call("GET", "/recruiter/candidates", token=e["token"])
        self.assertEqual((r["plan"], r["limitedTo"]), ("premium", None))
        self.assertGreater(r["total"], 50)
        self.assertEqual((len(r["items"]), r["page"]["pageSize"]), (10, 10))         # version 2: a page has 10 profiles by default
        s, r = self.api.call("GET", "/recruiter/candidates?pageSize=50", token=e["token"])
        self.assertEqual(len(r["items"]), 50)
        # invite
        s, r = self.api.call("POST", f"/recruiter/candidates/{cid}/contact", {"jobId": "job-nope", "message": "Please apply, we like your skills."}, token=e["token"])
        self.assertEqual(r["error"]["fields"]["jobId"], "Choose one of your jobs.")
        s, r = self.api.call("POST", f"/recruiter/candidates/{cid}/contact", {"jobId": job["id"], "message": "short"}, token=e["token"])
        self.assertEqual(r["error"]["fields"]["message"], "Write a message of 10 to 500 characters.")
        s, inv = self.api.call("POST", f"/recruiter/candidates/{cid}/contact", {"jobId": job["id"], "message": "Please apply. Call 0400 111 222 now."}, token=e["token"])
        self.assertEqual((s, inv["status"], inv["origin"]), (200, "contacted", "contacted"))
        self.assertEqual(inv["history"][0]["note"], "Please apply. Call [phone removed] now.")
        s, r = self.api.call("POST", f"/recruiter/candidates/{cid}/contact", {"jobId": job["id"], "message": "Please apply again please."}, token=e["token"])
        self.assertEqual((s, r["error"]["message"]), (409, "This person is already in the pipeline for this job."))
        # compare two profiles
        s, cmp = self.api.call("GET", f"/recruiter/compare?ids={cid},{second}&jobId={job['id']}", token=e["token"])
        self.assertEqual(s, 200)
        self.assertEqual([c["id"] for c in cmp["candidates"]], [cid, second])
        self.assertEqual(len(cmp["candidates"][0]["skills"]), len(JOB["skills"]))
        self.assertTrue(cmp["areas"])
        for row in cmp["areas"]:
            self.assertEqual({r["id"] for r in row["ranks"]}, {cid, second})
        self.assertNotIn("score", json.dumps(cmp).lower())
        self.assertEqual(self.api.call("GET", f"/recruiter/compare?ids={cid},nope&jobId={job['id']}", token=e["token"])[0], 404)

    def test_the_invited_talent_can_decline(self):
        e = self.employer()
        job = self.post_job(e)
        self.api.call("PUT", "/entitlements", {"plan": "premium"}, token=e["token"])
        t = self.talent()
        # version 2: a list has pages. The profile that changed last comes first with sort=updated.
        s, r = self.api.call("GET", "/recruiter/candidates?sort=updated&pageSize=50", token=e["token"])
        mine = [c for c in r["items"] if c["alias"] == t["user"]["alias"]]
        self.assertEqual(len(mine), 1)
        s, inv = self.api.call("POST", f"/recruiter/candidates/{mine[0]['id']}/contact", {"jobId": job["id"], "message": "We would love you to apply."}, token=e["token"])
        s, n = self.api.call("GET", "/notifications", token=t["token"])
        self.assertEqual(n["items"][0]["type"], "contacted")
        s, lst = self.api.call("GET", "/applications", token=t["token"])
        self.assertTrue(lst["items"][0]["needsAction"])
        self.assertEqual(lst["items"][0]["origin"], "contacted")
        s, ta = self.api.call("POST", f"/applications/{inv['id']}/decline", token=t["token"])
        self.assertEqual((ta["status"], ta["final"]), ("declined", True))
        s, n = self.api.call("GET", "/notifications", token=e["token"])
        self.assertEqual(n["items"][0]["type"], "contact_declined")

    def test_candidate_detail(self):
        e = self.employer()
        job = self.post_job(e)
        s, r = self.api.call("GET", "/recruiter/candidates", token=e["token"])
        cid = r["items"][0]["id"]
        s, d = self.api.call("GET", f"/recruiter/candidates/{cid}?jobId={job['id']}", token=e["token"])
        self.assertEqual(s, 200)
        self.assertEqual(len(d["match"]["skills"]), len(JOB["skills"]))
        self.assertEqual(d["job"], {"id": job["id"], "title": job["title"]})
        self.assertIn("entitlements", d)
        self.assertEqual(self.api.call("GET", "/recruiter/candidates/nope", token=e["token"])[0], 404)


class PrivacyTests(EmployerBase):
    """Feature 5 NFR: an automated test checks every employer response for personal fields."""

    def test_no_personal_data_in_any_employer_response(self):
        e = self.employer()
        job = self.post_job(e)
        self.api.call("PUT", "/entitlements", {"plan": "premium"}, token=e["token"])
        t = self.p.sign_up_and_in(name="Zelda Quixote", email="zelda.privacy@example.test")
        evidence = ["SENTINEL-EVIDENCE-LINE built a data platform in Nairobi.", "Built SQL and Python pipelines for a team of 12 analysts."]
        lines = ["EXPERIENCE", "Data Engineer - SentinelCorp (2019 - 2023)", *evidence, "EDUCATION", "Bachelor of Computer Science, Sentinel University, Kenya, 2013 - 2017",
                 "SKILLS", "SQL, Python, Apache Spark, Data modelling, Stakeholder management"]
        onboard(self.p, t, lines)
        self.assertEqual(self.api.call("PUT", "/applications-never", token=t["token"])[0], 404)
        s, a = self.api.call("POST", "/applications", {"jobId": job["id"], "note": "My note, no contact details."}, token=t["token"])
        responses = []

        def get(path):
            s, r = self.api.call("GET", path, token=e["token"])
            self.assertEqual(s, 200, path)
            responses.append(json.dumps(r))
            return r

        cands = get(f"/recruiter/candidates?jobId={job['id']}&sort=updated&pageSize=50")  # version 2: pages. The newest profile is first
        mine = next(c for c in cands["items"] if c["alias"] == t["user"]["alias"])
        get(f"/recruiter/candidates/{mine['id']}?jobId={job['id']}")
        other = cands["items"][0]["id"] if cands["items"][0]["id"] != mine["id"] else cands["items"][1]["id"]
        get(f"/recruiter/compare?ids={mine['id']},{other}&jobId={job['id']}")
        get(f"/recruiter/jobs/{job['id']}/applications")
        get(f"/recruiter/applications/{a['id']}")
        get("/recruiter/jobs")
        get("/notifications")
        get("/stats")
        blob = "\n".join(responses)
        for secret in ("Zelda", "Quixote", "zelda.privacy", "Kenya", "Nairobi", "SENTINEL", "SentinelCorp", "Sentinel University", "my-cv", "North Star"):
            self.assertNotIn(secret, blob, secret)
        # not a score on a person either
        for word in ("talent_search_score", "tss", "relative_merit", "feed_ranking", "rms"):
            self.assertNotIn(f'"{word}"', blob.lower())
        # after the talent agrees to share, the name and the email appear in ONE application only
        s, ra = self.api.call("POST", f"/recruiter/applications/{a['id']}/status", {"to": "review"}, token=e["token"])
        s, ra = self.api.call("POST", f"/recruiter/applications/{a['id']}/status", {"to": "interview", "slots": [iso_in(days=3)]}, token=e["token"])
        self.api.call("POST", f"/applications/{a['id']}/slot", {"slotId": ra["slots"][0]["id"], "shareIdentity": True}, token=t["token"])
        s, ra = self.api.call("GET", f"/recruiter/applications/{a['id']}", token=e["token"])
        self.assertEqual(ra["identity"], {"name": "Zelda Quixote", "email": "zelda.privacy@example.test"})
        self.assertNotIn("Kenya", json.dumps(ra))
        s, cand = self.api.call("GET", f"/recruiter/candidates/{mine['id']}", token=e["token"])
        self.assertNotIn("zelda.privacy", json.dumps(cand))  # the profile view stays anonymous

    def test_talent_cannot_see_the_other_sides_tools(self):
        t = self.talent()
        for path in ("/recruiter/jobs", "/recruiter/candidates"):
            self.assertEqual(self.api.call("GET", path, token=t["token"])[0], 403)


class StatsAndAlertsTests(EmployerBase):
    def test_notifications_and_charts(self):
        e = self.employer()
        job = self.post_job(e, targetApplicants=1)
        t = self.talent()
        self.api.call("GET", f"/jobs/{job['id']}", token=t["token"])  # job_watch
        self.api.call("PUT", f"/bookmarks/{job['id']}", token=t["token"])  # job_save
        self.api.call("POST", "/applications", {"jobId": job["id"]}, token=t["token"])
        s, st = self.api.call("GET", "/stats", token=e["token"])
        self.assertEqual(st["basic"], {"openJobs": 1, "jobsAtTarget": 1, "awaitingResponse": 1, "totalJobs": 1})
        self.assertIsNone(st["advanced"])
        self.api.call("PUT", "/entitlements", {"plan": "premium"}, token=e["token"])
        s, st = self.api.call("GET", "/stats", token=e["token"])
        row = st["advanced"]["jobs"][0]
        self.assertEqual((row["watch"], row["save"], row["apply"]), (1, 1, 1))
        self.assertEqual([p["stage"] for p in st["advanced"]["pipeline"]][:3], ["applied", "contacted", "review"])
        s, ts = self.api.call("GET", "/stats", token=t["token"])
        self.assertEqual((ts["basic"]["applications"], ts["basic"]["movedOn"], ts["basic"]["confirmed"]), (1, 0, 0))
        self.assertIsNone(ts["advanced"])
        self.api.call("PUT", "/entitlements", {"plan": "premium"}, token=t["token"])
        s, ts = self.api.call("GET", "/stats", token=t["token"])
        self.assertTrue(ts["advanced"]["basis"] > 0)
        self.assertEqual(set(ts["advanced"]), {"basis", "gapRanking", "demandForYourSkills"})
        # read state
        s, n = self.api.call("GET", "/notifications", token=e["token"])
        self.assertEqual(n["unread"], 1)
        self.api.call("POST", "/notifications/read", {"ids": [n["items"][0]["id"]]}, token=e["token"])
        s, n = self.api.call("GET", "/notifications", token=e["token"])
        self.assertEqual(n["unread"], 0)
        s, r = self.api.call("PUT", "/entitlements", {"plan": "gold"}, token=e["token"])
        self.assertEqual(r["error"]["fields"]["plan"], "Choose Basic or Premium.")

    def test_a_failed_email_never_blocks_the_action(self):
        # The outbox only records the message when no SMTP server is set. The action works either way.
        e = self.employer()
        job = self.post_job(e)
        t = self.talent()
        s, a = self.api.call("POST", "/applications", {"jobId": job["id"]}, token=t["token"])
        s, ra = self.api.call("POST", f"/recruiter/applications/{a['id']}/status", {"to": "rejected"}, token=e["token"])
        self.assertEqual(s, 200)
        from jinder import mailer
        mailer.process_outbox()
        c = self.p.conn()
        row = c.execute("SELECT status FROM email_outbox WHERE user_id = ? ORDER BY created_at DESC", (t["user"]["id"],)).fetchone()
        self.assertEqual(row["status"], "recorded")


if __name__ == "__main__":
    unittest.main()
