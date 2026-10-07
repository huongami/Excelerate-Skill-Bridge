"""Privacy audit of the employer side (Jinder V2). QA, wave 5.

An employer must never get: a name, an e-mail, a phone number, a country, a visa, an age, a gender, the CV text, the evidence lines, a password or a token
of a talent, a score or a rank on a person, or the link between an alias and a name before the talent agreed to share it (AI_Rule Rule 5).
An employer does get, at once, the names and years of the certifications and the awards of a talent (decision D5 of docs/V2_PLAN.md), and no person name next to them.

The test makes talent with private values that are easy to find in a text ("Zelda Quixote", "Kenya", a CV file, evidence lines), calls EVERY employer endpoint
(as a Premium employer and as a Basic employer), and scans all the answers in two ways:
  1. the keys: no forbidden key, and no key outside a short list for a person card, a person detail, a compare profile and an application snapshot;
  2. the values: none of the private values of the test talent, and none of the evidence lines, study countries, names and e-mails of the 50 sample talents.
"""
import json
import re
import unittest

import helpers as H
from test_v2_infra import card, iso_in, job_body

# A key with one of these names must not be in any answer for an employer (exact match, in any case), except where `key_allowed` says so.
FORBIDDEN_KEYS = {
    "score", "fit", "fitscore", "rank", "ranking", "overall", "total", "tss", "rms", "merit", "relative_merit_score", "frs",
    "email", "phone", "mobile", "name", "studycountry", "country", "nationality", "visa", "age", "gender", "birth", "dob",
    "evidence", "evidencetext", "cv", "cvtext", "cvfile", "cv_raw_text", "original", "originalname", "filename",
    "password", "passwordhash", "hash", "token", "salt", "ip",
}
# Where the key `name` is not the name of a person: the name of a skill, a certification, an award.
NAME_PARENTS = {"skills", "skilllevels", "skillrequirements", "certifications", "awards", "othereskills", "otherskills", "benefits", "gaps", "fit"}

CARD_KEYS = {"alias", "applicationId", "awards", "certifications", "coverage", "id", "industries", "level", "locations", "matched", "partial", "qualifications",
             "roles", "saved", "skillLevels", "skills", "total", "updatedAt", "years", "yearsExperience"}
DETAIL_KEYS = CARD_KEYS | {"entitlements", "fieldsOfStudy", "job", "match", "targetRoles", "workTypes"}
COMPARE_PROFILE_KEYS = {"alias", "awards", "certifications", "coverage", "id", "level", "otherSkills", "qualifications", "roles", "skills", "years", "yearsExperience"}
SNAPSHOT_KEYS = {"alias", "awards", "certifications", "fieldsOfStudy", "industries", "level", "locations", "qualifications", "roles", "skillLevels", "skills",
                 "specialisation", "targetRoles", "updatedAt", "workModes", "workTypes", "years", "yearsExperience"}
APPLICANT_KEYS = {"alias", "awaiting", "coverage", "createdAt", "id", "matched", "origin", "status", "statusLabel", "total", "updatedAt"}
CERT_KEYS = {"name", "issuer", "year"}
AWARD_KEYS = {"name", "kind", "year"}


def walk(value, path=()):
    """Yield (path, key, value) for every key of every dictionary in the answer. A list does not add a level to the path."""
    if isinstance(value, dict):
        for k, v in value.items():
            yield path, k, v
            yield from walk(v, path + (k,))
    elif isinstance(value, list):
        for item in value:
            yield from walk(item, path)


def key_allowed(path, key, value, skills_in_job=None):
    """The few places where a key with a forbidden name is not private data."""
    k = key.lower()
    where = tuple(p.lower() for p in path)
    if k == "total":
        # the size of a list (page.total or the total of a list) and the number of skills of the job (the "of 10" in "8 of 10 skills")
        return where in ((), ("page",)) or (isinstance(value, int) and skills_in_job is not None and value == skills_in_job)
    if k == "name":
        return bool(where) and where[-1] in NAME_PARENTS
    if k == "email":
        return isinstance(value, bool)        # a notification says whether an e-mail was sent. It is not an address
    return False


def forbidden_keys_in(label, body):
    """The (label, path) of every forbidden key in one answer."""
    skills = None
    if isinstance(body, dict):
        skills = (body.get("job") or {}).get("skills")
        skills = len(skills) if isinstance(skills, list) else None
    bad = []
    for path, key, value in walk(body):
        if key.lower() in FORBIDDEN_KEYS and not key_allowed(path, key, value, skills):
            if path and path[-1] == "identity":
                continue          # the identity of an application that the talent agreed to share (checked in its own test)
            bad.append((label, ".".join(path + (key,))))
    return bad


class ScannerTests(unittest.TestCase):
    """The scanner must be able to fail. These answers are made up and they leak."""

    def test_the_scanner_finds_each_kind_of_leak(self):
        leaks = {
            "email": {"items": [{"alias": "A", "email": "a@b.c"}]},
            "a score": {"items": [{"alias": "A", "score": 71.2}]},
            "a fit": {"items": [{"alias": "A", "fit": 71.2}]},
            "an overall": {"candidates": [{"alias": "A", "overall": 3}]},
            "a person name": {"items": [{"alias": "A", "name": "Zelda"}]},
            "a country": {"items": [{"alias": "A", "studyCountry": ["Kenya"]}]},
            "evidence": {"items": [{"alias": "A", "evidence": ["Led a team"]}]},
            "a cv": {"items": [{"alias": "A", "cv": {"file": "cv.pdf"}}]},
            "a token": {"items": [{"alias": "A", "token": "abc"}]},
            "a total on a person": {"items": [{"alias": "A", "total": 99.5}]},
        }
        for name, body in leaks.items():
            self.assertTrue(forbidden_keys_in(name, body), name)

    def test_the_scanner_lets_the_allowed_keys_pass(self):
        ok = {"items": [{"alias": "A", "total": 10, "skills": ["SQL"], "certifications": [{"name": "AWS Certified Cloud Practitioner", "issuer": "AWS", "year": 2022}],
                         "awards": [{"name": "Cup", "kind": "hackathon", "year": 2023}], "skillLevels": [{"name": "SQL", "level": 3}]}],
              "job": {"skills": ["a"] * 10}, "total": 51, "page": {"page": 1, "pageSize": 10, "total": 51, "totalPages": 6}}
        self.assertEqual(forbidden_keys_in("ok", ok), [])
        self.assertTrue(forbidden_keys_in("a number that is not the skill count", {"job": {"skills": ["a"] * 10}, "items": [{"alias": "A", "total": 11}]}))


class EmployerPrivacyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api
        # a Premium employer with one job and a Basic employer
        cls.emp = cls.p.sign_up_and_in(role="recruiter", name="Pia Employer", email="pia.employer.privacy@example.test", company="Privacy Test Pty Ltd")
        cls.api.call("PUT", "/entitlements", {"plan": "premium"}, token=cls.emp["token"])
        s, cls.job = cls.api.call("POST", "/recruiter/jobs", job_body(skills=["Python", "SQL", "Microsoft Excel", "Power BI"], description="Build and run the data pipelines that feed the product, and work with the analysts every day."), token=cls.emp["token"])
        assert s in (200, 201), (s, cls.job)
        cls.basic = cls.p.sign_up_and_in(role="recruiter", name="Basil Employer", email="basil.employer.privacy@example.test", company="Basic Test Pty Ltd")
        s, cls.basic_job = cls.api.call("POST", "/recruiter/jobs", job_body(), token=cls.basic["token"])
        assert s in (200, 201), (s, cls.basic_job)
        # three talents with private values. Each value is easy to find in a text.
        cls.talents = []
        for i, (name, country, role_original, evidence) in enumerate([
                ("Zelda Quixote", "Kenya", "Zorblax Analyst", ["Led the Zephyr migration at Orionbyte Labs", "Cut the Quasar report time by 40 percent"]),
                ("Ximena Vortigern", "Peru", "Quillfeather Wrangler", ["Built the Marigold dashboard for Brackenridge Retail"]),
                ("Oswin Thackeray", "Nepal", "Gryphon Tabulator", ["Ran the Nimbus data audit for Lowcastle Freight"])]):
            t = cls.p.sign_up_and_in(name=name, email=f"{name.split()[0].lower()}.privacy.v2@example.test")
            cards = [card(j, n, level=lv) for j, (n, lv) in enumerate([("Python", 4), ("SQL", 3), ("Microsoft Excel", 4), ("Power BI", 2), ("Git", 3), ("Data analysis", 3)])]
            cards.append(card(90, "Data Analyst", source="role", anzsco="224114", occupation="Data Analyst", original=role_original))
            cards.append(card(91, "AQF Level 7 (Bachelor degree)", source="qualification", original="Bachelor's degree from Mount Vortigern University"))
            body = {"qualification": ["Bachelor's degree"], "fieldOfStudy": ["Information systems"], "studyCountry": [country], "currentRole": [role_original],
                    "industry": ["Data"], "years": "3–5 years", "yearsExperience": 4.2 + i, "level": "Mid", "skills": [n for n, _ in [("Python", 4), ("SQL", 3), ("Microsoft Excel", 4), ("Power BI", 2), ("Git", 3), ("Data analysis", 3)]],
                    "targetRole": ["Data Engineer"], "targetIndustries": [], "locations": ["Melbourne"], "workTypes": ["Full-time"], "evidence": evidence, "translation": cards,
                    "certifications": [{"name": f"AWS Certified Cloud Practitioner", "issuer": "Amazon Web Services", "year": 2022}] if i == 0 else [{"name": "Microsoft Certified: Azure Fundamentals", "issuer": "Microsoft", "year": 2023}],
                    "awards": [{"name": f"Cloud Cup Winner {i}", "kind": "hackathon", "year": 2023}]}
            s, me = cls.api.call("PATCH", "/me", {"profile": body, "onboarding": "done"}, token=t["token"])
            assert s == 200, (s, me)
            t["private"] = [name, name.split()[0], name.split()[1], t["email"], t["email"].split("@")[0], country, role_original, "Mount Vortigern"] + evidence
            cls.talents.append(t)
        # the first talent applies to the job of the Premium employer. The talent does not agree to share the identity.
        s, a = cls.api.call("POST", "/applications", {"jobId": cls.job["id"], "note": "I like data work and I would like to join the team."}, token=cls.talents[0]["token"])
        assert s in (200, 201), (s, a)
        cls.app_id = a["id"]
        cls.all_answers = None

    # ------------------------------------------------------------------ collect every employer answer
    def collect(self):
        """{label: (status, json)} for every employer endpoint, as the Premium employer and as the Basic employer."""
        if type(self).all_answers is not None:
            return type(self).all_answers
        out = {}
        call = self.api.call
        tok, btok = self.emp["token"], self.basic["token"]
        jid = self.job["id"]

        def get(label, path, token=tok):
            out[label] = call("GET", path, token=token)
            return out[label][1]

        get("jobs", "/recruiter/jobs?pageSize=50")
        get("job", f"/recruiter/jobs/{jid}")
        get("applicants", f"/recruiter/jobs/{jid}/applications")
        get("review", f"/recruiter/applications/{self.app_id}")
        ids = []
        for sort in ("best", "updated"):
            for page in (1, 2):
                r = get(f"candidates {sort} {page}", f"/recruiter/candidates?jobId={jid}&sort={sort}&page={page}&pageSize=50")
                ids += [c["id"] for c in r["items"]]
        get("candidates saved", f"/recruiter/candidates?jobId={jid}&view=saved")
        get("candidates without a job", "/recruiter/candidates")
        mine = [t["user"]["id"] for t in self.talents]
        samples = [i for i in ids if i not in mine][:2]
        for cid in mine + samples:
            get(f"candidate {cid[:6]}", f"/recruiter/candidates/{cid}?jobId={jid}")
        call("PUT", f"/recruiter/candidates/{mine[1]}/save", token=tok)
        get("candidates saved after a save", f"/recruiter/candidates?jobId={jid}&view=saved")
        get("compare of the 3 talents", f"/recruiter/compare?ids={','.join(mine)}&jobId={jid}")
        get("compare of 5 profiles", f"/recruiter/compare?ids={','.join(mine + samples)}&jobId={jid}")
        out["compare with 1 id (400)"] = call("GET", f"/recruiter/compare?ids={mine[0]}&jobId={jid}", token=tok)
        out["compare with 6 ids (400)"] = call("GET", f"/recruiter/compare?ids={','.join(ids[:6])}&jobId={jid}", token=tok)
        get("stats", "/stats")
        get("entitlements", "/entitlements")
        get("notifications", "/notifications")
        get("me", "/me")
        # an invite (Premium) makes an application
        out["invite"] = call("POST", f"/recruiter/candidates/{mine[2]}/contact", {"jobId": jid, "message": "We like your profile and your skills."}, token=tok)
        # the Basic employer
        get("basic candidates", f"/recruiter/candidates?jobId={self.basic_job['id']}", token=btok)
        get("basic candidate detail", f"/recruiter/candidates/{mine[0]}?jobId={self.basic_job['id']}", token=btok)
        get("basic jobs", "/recruiter/jobs", token=btok)
        out["basic compare (403)"] = call("GET", f"/recruiter/compare?ids={mine[0]},{mine[1]}&jobId={self.basic_job['id']}", token=btok)
        out["basic invite (403)"] = call("POST", f"/recruiter/candidates/{mine[1]}/contact", {"jobId": self.basic_job["id"]}, token=btok)
        type(self).all_answers = out
        return out

    # ------------------------------------------------------------------ 1. the keys
    def test_every_endpoint_answered_as_expected(self):
        out = self.collect()
        for label, (status, body) in out.items():
            if "(400)" in label:
                self.assertEqual(status, 400, label)
            elif "(403)" in label:
                self.assertEqual(status, 403, label)
            elif label == "invite":
                self.assertIn(status, (200, 201), (label, body))
            else:
                self.assertEqual(status, 200, (label, body))
        self.assertGreaterEqual(len(out), 25)

    def test_no_forbidden_key_in_any_answer(self):
        bad = []
        for label, (status, body) in self.collect().items():
            if label == "me":
                continue          # the employer's own account (own name and e-mail)
            bad += forbidden_keys_in(label, body)
        self.assertEqual(bad, [], "forbidden keys in employer answers")

    def test_a_person_has_only_the_keys_of_the_shared_profile(self):
        """The keys of a card, a detail, a compare profile, an application snapshot and an applicant are a closed list. A new key must be added here on purpose."""
        out = self.collect()
        seen = {"card": set(), "detail": set(), "compare": set(), "snapshot": set(), "applicant": set(), "cert": set(), "award": set()}
        for label, (status, body) in out.items():
            if status != 200 or not isinstance(body, dict):
                continue
            if label.startswith("candidates") or label.startswith("basic candidates"):
                for c in body["items"]:
                    seen["card"] |= set(c)
            elif label.startswith("candidate ") or label == "basic candidate detail":
                seen["detail"] |= set(body)
            elif label.startswith("compare"):
                for c in body["candidates"]:
                    seen["compare"] |= set(c)
            elif label == "review":
                seen["snapshot"] |= set(body["snapshot"])
            elif label == "applicants":
                for a in body["items"]:
                    seen["applicant"] |= set(a)
            for path, key, value in walk(body):
                if key == "certifications" and isinstance(value, list):
                    for c in value:
                        if isinstance(c, dict):
                            seen["cert"] |= set(c)
                if key == "awards" and isinstance(value, list):
                    for a in value:
                        if isinstance(a, dict):
                            seen["award"] |= set(a)
        self.assertLessEqual(seen["card"], CARD_KEYS)
        self.assertLessEqual(seen["detail"], DETAIL_KEYS)
        self.assertLessEqual(seen["compare"], COMPARE_PROFILE_KEYS)
        self.assertLessEqual(seen["snapshot"], SNAPSHOT_KEYS)
        self.assertLessEqual(seen["applicant"], APPLICANT_KEYS)
        self.assertLessEqual(seen["cert"], CERT_KEYS)
        self.assertLessEqual(seen["award"], AWARD_KEYS)
        for k in ("card", "detail", "compare", "snapshot", "applicant"):
            self.assertTrue(seen[k], k)       # the audit really saw this kind of object

    # ------------------------------------------------------------------ 2. the values
    def private_values(self):
        values = []
        for t in self.talents:
            values += t["private"]
        # the evidence lines, study countries and original texts of all the sample talents, and the e-mail of every talent account
        conn = self.p.conn()
        try:
            for r in conn.execute("SELECT study_country, evidence FROM profiles").fetchall():
                values += json.loads(r["study_country"] or "[]") + json.loads(r["evidence"] or "[]")
            # the original text of a role or a qualification (the title that the talent wrote) when it is not part of the name that employers see
            for r in conn.execute("SELECT original FROM translated_skills WHERE source IN ('role', 'qualification') AND original != '' AND instr(lower(mapped), lower(original)) = 0").fetchall():
                values.append(r["original"])
            # the names and e-mails of the talent that did not agree to share them with anyone
            for r in conn.execute("SELECT u.name, u.email FROM users u WHERE u.role = 'candidate' AND u.id NOT IN (SELECT candidate_id FROM applications WHERE identity_shared = 1)").fetchall():
                values += [r["name"], r["email"]]
        finally:
            conn.close()
        return sorted({v.strip() for v in values if isinstance(v, str) and len(v.strip()) >= 4})

    def test_no_private_value_in_any_answer(self):
        values = self.private_values()
        self.assertGreater(len(values), 100)        # the 50 sample talents and the 3 test talents
        for label, (status, body) in self.collect().items():
            if label == "me":
                continue
            text = json.dumps(body, ensure_ascii=False).lower()
            for v in values:
                if v.lower() in text:
                    self.fail(f"{label}: the private value {v!r} is in the answer")

    def test_the_alias_is_not_the_name(self):
        for t in self.talents:
            alias = t["user"]["alias"]
            self.assertTrue(alias)
            for part in t["user"]["name"].split():
                self.assertNotIn(part.lower(), alias.lower())

    # ------------------------------------------------------------------ the link between alias and name
    def test_no_identity_before_the_talent_agrees(self):
        out = self.collect()
        s, review = out["review"]
        self.assertIsNone(review["identity"])
        blob = json.dumps(out["review"][1]) + json.dumps(out["applicants"][1])
        for t in self.talents:
            self.assertNotIn(t["user"]["name"], blob)
            self.assertNotIn(t["email"], blob)
        # the alias is there, and nothing else names the person
        self.assertEqual(review["snapshot"]["alias"], self.talents[0]["user"]["alias"])

    def test_the_identity_shows_only_in_the_application_that_the_talent_shared(self):
        # another talent applies, the employer offers interview times, and the talent picks one and agrees to share the identity
        t = self.p.sign_up_and_in(name="Quentin Marlowe", email="quentin.marlowe.privacy.v2@example.test")
        cards = [card(j, n, level=3) for j, n in enumerate(["Python", "SQL", "Microsoft Excel", "Power BI"])]
        body = {"qualification": ["Bachelor's degree"], "fieldOfStudy": ["Information systems"], "studyCountry": ["Chile"], "currentRole": ["Data Analyst"], "industry": ["Data"],
                "years": "3–5 years", "skills": ["Python", "SQL", "Microsoft Excel", "Power BI"], "targetRole": ["Data Engineer"], "targetIndustries": [], "locations": ["Melbourne"],
                "workTypes": ["Full-time"], "evidence": [], "translation": cards}
        s, me = self.api.call("PATCH", "/me", {"profile": body, "onboarding": "done"}, token=t["token"])
        self.assertEqual(s, 200, me)
        s, a = self.api.call("POST", "/applications", {"jobId": self.job["id"], "note": "Please consider me."}, token=t["token"])
        self.assertIn(s, (200, 201), a)
        app_id = a["id"]
        emp = self.emp["token"]
        s, r = self.api.call("POST", f"/recruiter/applications/{app_id}/status", {"to": "review"}, token=emp)
        self.assertEqual(s, 200, r)
        s, r = self.api.call("POST", f"/recruiter/applications/{app_id}/status", {"to": "interview", "slots": [iso_in(3), iso_in(4)]}, token=emp)
        self.assertEqual(s, 200, r)
        s, mine = self.api.call("GET", f"/applications/{app_id}", token=t["token"])
        slot_id = mine["slots"][0]["id"]
        s, r = self.api.call("POST", f"/applications/{app_id}/slot", {"slotId": slot_id, "shareIdentity": True}, token=t["token"])
        self.assertEqual(s, 200, r)
        s, shared = self.api.call("GET", f"/recruiter/applications/{app_id}", token=emp)
        self.assertEqual(shared["identity"], {"name": t["user"]["name"], "email": t["email"]})
        # the other application and every list still have no identity
        s, other = self.api.call("GET", f"/recruiter/applications/{self.app_id}", token=emp)
        self.assertIsNone(other["identity"])
        for path in (f"/recruiter/jobs/{self.job['id']}/applications", f"/recruiter/candidates?jobId={self.job['id']}&pageSize=50",
                     f"/recruiter/candidates/{t['user']['id']}?jobId={self.job['id']}"):
            s, body = self.api.call("GET", path, token=emp)
            text = json.dumps(body)
            self.assertNotIn(t["user"]["name"], text, path)
            self.assertNotIn(t["email"], text, path)

    # ------------------------------------------------------------------ D5: certifications and awards are visible
    def test_award_and_certification_names_are_visible_without_a_person_name(self):
        out = self.collect()
        t0, t1 = self.talents[0], self.talents[1]
        want = {t0["user"]["id"]: ("AWS Certified Cloud Practitioner", "Cloud Cup Winner 0"), t1["user"]["id"]: ("Microsoft Certified: Azure Fundamentals", "Cloud Cup Winner 1")}
        for label in ("candidates best 1", "candidates updated 1"):
            items = {c["id"]: c for c in out[label][1]["items"]}
            for cid, (cert, award) in want.items():
                if cid in items:                                     # the list is one page of 50: the test talents are in the first pages
                    self.assertEqual([c["name"] for c in items[cid]["certifications"]], [cert], label)
                    self.assertEqual([a["name"] for a in items[cid]["awards"]], [award], label)
        for cid, (cert, award) in want.items():
            d = out[f"candidate {cid[:6]}"][1]
            self.assertEqual([c["name"] for c in d["certifications"]], [cert])
            self.assertEqual([a["name"] for a in d["awards"]], [award])
            self.assertEqual(d["awards"][0]["year"], 2023)
        cmp_ = out["compare of the 3 talents"][1]
        by_id = {c["id"]: c for c in cmp_["candidates"]}
        for cid, (cert, award) in want.items():
            self.assertEqual([c["name"] for c in by_id[cid]["certifications"]], [cert])
            self.assertEqual([a["name"] for a in by_id[cid]["awards"]], [award])
        snap = out["review"][1]["snapshot"]
        self.assertEqual([c["name"] for c in snap["certifications"]], ["AWS Certified Cloud Practitioner"])
        self.assertEqual([a["name"] for a in snap["awards"]], ["Cloud Cup Winner 0"])
        # the person name is not next to them
        for cid in want:
            text = json.dumps(out[f"candidate {cid[:6]}"][1])
            for t in self.talents:
                self.assertNotIn(t["user"]["name"], text)
        # a Basic employer sees them too (the 5 best profiles carry the same facts)
        basic = out["basic candidate detail"][1]
        self.assertEqual([a["name"] for a in basic["awards"]], ["Cloud Cup Winner 0"])

    def test_every_sample_talent_card_has_certification_and_award_lists(self):
        out = self.collect()
        items = [c for label in ("candidates best 1", "candidates best 2") for c in out[label][1]["items"]]
        self.assertGreaterEqual(len(items), 50)
        for c in items:
            self.assertIsInstance(c["certifications"], list)
            self.assertIsInstance(c["awards"], list)
        self.assertTrue(any(c["certifications"] for c in items))
        self.assertTrue(any(c["awards"] for c in items))

    # ------------------------------------------------------------------ the rest
    def test_the_job_pages_of_the_employer_have_no_talent_data(self):
        out = self.collect()
        for label in ("jobs", "job", "basic jobs", "stats"):
            text = json.dumps(out[label][1]).lower()
            for t in self.talents:
                self.assertNotIn(t["user"]["alias"].lower(), text, label)
        self.assertNotIn("alias", json.dumps(out["jobs"][1]))
        self.assertNotIn("alias", json.dumps(out["stats"][1]))

    def test_the_compare_has_positions_inside_an_area_and_never_a_total(self):
        cmp_ = self.collect()["compare of 5 profiles"][1]
        self.assertEqual(len(cmp_["candidates"]), 5)
        for area in cmp_["areas"]:
            positions = [r["position"] for r in area["ranks"]]
            self.assertTrue(all(isinstance(x, int) and 1 <= x <= 5 for x in positions))
        series = cmp_["radar"]["series"]
        self.assertEqual(sorted(set(series[0])), ["alias", "id", "values"])
        text = json.dumps(cmp_).lower()
        for word in ('"total"', '"score"', '"overall"', '"tss"', '"merit"', '"rms"', '"rank"'):
            self.assertNotIn(word, text)

    def test_the_errors_of_the_compare_name_ids_only(self):
        out = self.collect()
        for label in ("compare with 1 id (400)", "compare with 6 ids (400)", "basic compare (403)", "basic invite (403)"):
            text = json.dumps(out[label][1])
            for t in self.talents:
                self.assertNotIn(t["user"]["name"], text, label)
                self.assertNotIn(t["email"], text, label)

    def test_a_talent_cannot_call_an_employer_endpoint(self):
        t = self.talents[0]
        for path in ("/recruiter/candidates", f"/recruiter/candidates/{t['user']['id']}", "/recruiter/jobs", "/recruiter/compare?ids=a,b&jobId=x"):
            s, body = self.api.call("GET", path, token=t["token"])
            self.assertEqual(s, 403, path)
        s, body = self.api.call("GET", "/recruiter/candidates")
        self.assertEqual(s, 401)


if __name__ == "__main__":
    unittest.main()
