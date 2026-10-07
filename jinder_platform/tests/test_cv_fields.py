"""The CV reader on the fixture CVs (item R1 of the V2 plan).

The files are in tests/fixtures/cv (PDF and DOCX, made up, made by tests/fixtures/make_cv_fixtures.py). The true values are in expected.json.
Each file is read with the real text reader (textextract) and then with the CV reader, "as of" the day in expected.json (so that the years
do not change with time). The same checks run with the built-in word lists and with the taxonomy file (when the file is there).

The plan asks: the current role in 10 of 14 CVs or more, the level in 10 of 14 or more, the target role in every CV that states one,
and an empty field (never a wrong one) when the CV does not show it. This file checks those rates and also each CV one by one.
"""
import json
import math
import unittest
from datetime import date
from pathlib import Path

import helpers as H  # noqa: F401 - sets the paths
from jinder import cv_lexicon, cv_parser, textextract
from jinder import reference as R

FIXTURES = Path(__file__).parent / "fixtures" / "cv"
EXPECTED = json.loads((FIXTURES / "expected.json").read_text(encoding="utf-8"))
ASOF = date.fromisoformat(EXPECTED["asOf"])
FIELDS = ["currentRole", "level", "targetRole", "yearsExperience", "certifications", "awards"]


def loose(text):
    return "".join(ch for ch in str(text).lower() if ch.isalnum())


def same_name(a, b):
    a, b = loose(a), loose(b)
    return bool(a) and bool(b) and (a == b or a in b or b in a)


class Outcome:
    """What the reader gave for one CV, compared with the true values."""

    def __init__(self, name, expected, result):
        self.name, self.e, self.r = name, expected, result

    def current_role(self):
        return (self.r["currentRole"] or None) == self.e["currentRole"]

    def level(self):
        return (self.r["level"] or None) == self.e["level"]

    def target_role(self):
        return (self.r["targetRole"] or None) == self.e["targetRole"]

    def years(self):
        want, got = self.e["yearsExperience"], self.r["yearsExperience"]
        return (want is None and got is None) or (want is not None and got is not None and abs(want - got) <= 1.0)

    def certifications(self):
        got = [c["name"] for c in self.r["certifications"]]
        return len(got) == len(self.e["certifications"]) and all(any(same_name(w, g) for g in got) for w in self.e["certifications"])

    def awards(self):
        got = self.r["awards"]
        return len(got) == len(self.e["awards"]) and all(
            any(same_name(w["name"], g["name"]) and (w["kind"] or "") == (g["kind"] or "") and w["year"] == g["year"] for g in got) for w in self.e["awards"])

    def skills(self):
        names = {s["name"].lower() for s in self.r["skills"]}
        lex = cv_lexicon.get()
        return all((lex.canonical_skill(s) or s).lower() in names for s in self.e["skills"])

    def skill_levels(self):
        lex = cv_lexicon.get()
        got = {s["name"].lower(): s["level"] for s in self.r["skills"]}
        return all(got.get((lex.canonical_skill(k) or k).lower()) == v for k, v in self.e["skillLevels"].items())

    def empty_is_empty(self):
        """A field that the CV does not show must be empty in the result, and the found flag must be false."""
        checks = {"currentRole": self.r["currentRole"] == "", "level": self.r["level"] == "", "targetRole": self.r["targetRole"] == "",
                  "yearsExperience": self.r["yearsExperience"] is None, "certifications": self.r["certifications"] == [], "awards": self.r["awards"] == []}
        want_empty = {"currentRole": not self.e["currentRole"], "level": not self.e["level"], "targetRole": not self.e["targetRole"],
                      "yearsExperience": self.e["yearsExperience"] is None, "certifications": not self.e["certifications"], "awards": not self.e["awards"]}
        return [k for k in FIELDS if want_empty[k] and not (checks[k] and not self.r["found"][k])]


class FieldChecks:
    """The checks. A subclass says which word lists to use."""
    outcomes = {}

    @classmethod
    def use_lexicon(cls):
        raise NotImplementedError

    @classmethod
    def setUpClass(cls):
        cls._strict = cv_parser._STRICT
        cv_parser._STRICT = True
        cls.use_lexicon()
        cls.outcomes = {}
        for name, expected in EXPECTED["fixtures"].items():
            text = textextract.extract_text((FIXTURES / name).read_bytes())
            cls.outcomes[name] = Outcome(name, expected, cv_parser.parse_cv(text, ASOF))

    @classmethod
    def tearDownClass(cls):
        cv_parser._STRICT = cls._strict
        cv_lexicon.reset()

    # ----- the files -----
    def test_there_are_14_or_more_fixtures_in_pdf_and_docx(self):
        names = list(EXPECTED["fixtures"])
        self.assertGreaterEqual(len(names), 14)
        self.assertGreaterEqual(sum(n.endswith(".pdf") for n in names), 8)
        self.assertGreaterEqual(sum(n.endswith(".docx") for n in names), 3)
        for name in names:
            self.assertTrue((FIXTURES / name).is_file(), name)
        self.assertEqual(sorted(p.name for p in FIXTURES.iterdir() if p.suffix in (".pdf", ".docx")), sorted(names))

    def test_every_file_is_made_up(self):
        for name in EXPECTED["fixtures"]:
            text = textextract.extract_text((FIXTURES / name).read_bytes())
            self.assertNotRegex(text, r"@(?!example\.test)", name)

    # ----- the rates of the plan -----
    def rate(self, check):
        outcomes = list(self.outcomes.values())
        return sum(1 for o in outcomes if getattr(o, check)()), len(outcomes)

    def test_the_current_role_is_found_in_10_of_14_or_more(self):
        ok, n = self.rate("current_role")
        self.assertGreaterEqual(ok, math.ceil(10.0 / 14 * n), f"{ok} of {n}")

    def test_the_level_is_found_in_10_of_14_or_more(self):
        ok, n = self.rate("level")
        self.assertGreaterEqual(ok, math.ceil(10.0 / 14 * n), f"{ok} of {n}")

    def test_the_target_role_is_found_in_every_cv_that_states_one(self):
        stating = [o for o in self.outcomes.values() if o.e["targetRole"]]
        self.assertGreaterEqual(len(stating), 7)
        self.assertEqual([o.name for o in stating if not o.target_role()], [])

    def test_a_field_that_the_cv_does_not_show_is_empty_not_wrong(self):
        wrong = {o.name: o.empty_is_empty() for o in self.outcomes.values() if o.empty_is_empty()}
        self.assertEqual(wrong, {})

    def test_a_wish_for_a_role_that_is_not_in_the_list_is_not_guessed(self):
        o = self.outcomes["cv14_principal.pdf"]          # "Open to Head of AI roles"
        self.assertEqual((o.r["targetRole"], o.r["found"]["targetRole"]), ("", False))
        o = self.outcomes["cv21_inline_at_dates.pdf"]    # "Currently looking for roles in MLOps" (a skill, not a role)
        self.assertEqual(o.r["targetRole"], "")
        o = self.outcomes["cv13_no_target_awards.pdf"]   # "Looking after a team", "Looking forward to hearing from you"
        self.assertEqual(o.r["targetRole"], "")

    # ----- each CV, one by one -----
    def test_each_cv_current_role(self):
        for name, o in self.outcomes.items():
            with self.subTest(name):
                self.assertEqual(o.r["currentRole"] or None, o.e["currentRole"])

    def test_each_cv_level(self):
        for name, o in self.outcomes.items():
            with self.subTest(name):
                self.assertEqual(o.r["level"] or None, o.e["level"])

    def test_each_cv_target_role(self):
        for name, o in self.outcomes.items():
            with self.subTest(name):
                self.assertEqual(o.r["targetRole"] or None, o.e["targetRole"])

    def test_each_cv_years(self):
        for name, o in self.outcomes.items():
            with self.subTest(name):
                self.assertTrue(o.years(), f"{o.r['yearsExperience']} but the true value is {o.e['yearsExperience']}")

    def test_each_cv_certifications(self):
        for name, o in self.outcomes.items():
            with self.subTest(name):
                self.assertTrue(o.certifications(), f"{[c['name'] for c in o.r['certifications']]} but the true value is {o.e['certifications']}")

    def test_each_cv_awards(self):
        for name, o in self.outcomes.items():
            with self.subTest(name):
                self.assertTrue(o.awards(), f"{o.r['awards']} but the true value is {o.e['awards']}")

    def test_each_cv_skills_and_their_levels(self):
        for name, o in self.outcomes.items():
            with self.subTest(name):
                self.assertTrue(o.skills(), f"{sorted(s['name'] for s in o.r['skills'])} does not have all of {o.e['skills']}")
                self.assertTrue(o.skill_levels(), f"{[(s['name'], s['level']) for s in o.r['skills']]} but the true levels are {o.e['skillLevels']}")

    def test_the_old_fields_are_still_there(self):
        for name, o in self.outcomes.items():
            with self.subTest(name):
                r = o.r
                self.assertEqual(set(r["detected"]), set(r["fields"]))
                self.assertTrue(set(r["missing"]) <= {"qualification", "fieldOfStudy", "studyCountry", "currentRole", "industry", "years", "skills"})
                self.assertEqual(r["found"]["yearsExperience"], r["yearsExperience"] is not None)
                if r["currentRole"]:
                    self.assertEqual(r["fields"]["currentRole"][0], r["currentRole"])

    def test_the_industry_holds_the_domains_of_the_platform_only(self):
        """The profile keeps only the 3 domains (R.DOMAINS). The reader gives at most 2, and the first is result.domain."""
        found = 0
        for name, o in self.outcomes.items():
            with self.subTest(name):
                industry = o.r["fields"].get("industry", [])
                self.assertLessEqual(len(industry), 2)
                for value in industry:
                    self.assertIn(value, R.DOMAINS)
                self.assertEqual(o.r["domain"], industry[0] if industry else "")
                found += 1 if industry else 0
        self.assertGreaterEqual(found, math.ceil(0.8 * len(self.outcomes)))          # the fixtures are all ICT CVs: most of them show a domain

    def test_the_number_of_years_sets_the_band(self):
        for name, o in self.outcomes.items():
            with self.subTest(name):
                years = o.r["yearsExperience"]
                self.assertEqual(o.r["fields"].get("years", ""), cv_parser._band(years) if years else "")

    def test_the_rates_are_reported(self):
        """Prints how often each field is found, and how often it is right (the numbers of the report)."""
        n = len(self.outcomes)
        rows = []
        for field, check, flag in (("current role", "current_role", "currentRole"), ("level", "level", "level"), ("target role", "target_role", "targetRole"),
                                   ("years", "years", "yearsExperience"), ("certifications", "certifications", "certifications"), ("awards", "awards", "awards")):
            found = sum(1 for o in self.outcomes.values() if o.r["found"][flag])
            right = sum(1 for o in self.outcomes.values() if getattr(o, check)())
            rows.append(f"{field}: found in {found} of {n}, right in {right} of {n}")
        print(f"\n[{cv_lexicon.get().source} lists] " + "; ".join(rows))
        self.assertEqual(len(rows), 6)


class ApiTests(unittest.TestCase):
    """The result of the reader goes through the platform (upload, background reading, GET /cv/parse/:id) with the new keys."""

    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api

    def read(self, upload_path, filename, data, token):
        import time
        s, up = self.api.upload(upload_path, filename, data, token)
        self.assertEqual(s, 202, up)
        for _ in range(200):
            s, res = self.api.call("GET", f"{upload_path}/parse/{up['parse']['id']}" if upload_path == "/cv" else f"{upload_path}/{up['parse']['id']}", token=token)
            if res["status"] != "parsing":
                return res
            time.sleep(0.05)
        self.fail("The reading did not end")

    def test_a_pdf_cv_gives_the_new_keys(self):
        t = self.p.sign_up_and_in()
        data = (FIXTURES / "cv07_linkedin_export.pdf").read_bytes()
        res = self.read("/cv", "cv.pdf", data, t["token"])
        self.assertEqual(res["status"], "done", res)
        r = res["result"]
        self.assertEqual((r["currentRole"], r["level"], r["targetRole"]), ("Lead Machine Learning Engineer", "Lead", "AI Research Scientist"))
        self.assertTrue(r["found"]["certifications"] and r["found"]["awards"] and r["found"]["yearsExperience"])
        self.assertEqual(r["fields"]["currentRole"][0], "Lead Machine Learning Engineer")
        self.assertEqual(set(r["detected"]), set(r["fields"]))
        self.assertTrue(all(set(s) == {"name", "level"} for s in r["skills"]))

    def test_a_docx_cv_gives_the_new_keys(self):
        t = self.p.sign_up_and_in()
        res = self.read("/cv", "cv.docx", (FIXTURES / "cv19_docx_stacked_open_to.docx").read_bytes(), t["token"])
        r = res["result"]
        self.assertEqual((r["currentRole"], r["targetRole"], r["level"]), ("BI Developer", "Analytics Engineer", "Mid"))

    def test_a_job_description_file_keeps_its_markup(self):
        e = self.p.sign_up_and_in(role="recruiter")
        text = ["Senior Data Engineer", "About the role", "We build a data platform for water utilities.", "What you bring:", "- 5 to 9 years in data engineering.",
                "- Python at an advanced level (4 of 5).", "The role is fully Remote."]
        res = self.read("/recruiter/jobs/import", "jd.docx", H.make_docx(text), e["token"])
        f = res["result"]["fields"]
        self.assertTrue(f["description"].startswith("## About the role"))
        self.assertIn("## What you bring", f["description"])
        self.assertIn("- Python at an advanced level (4 of 5).", f["description"])
        self.assertEqual((f.get("level"), f.get("minYears"), f.get("maxYears"), f.get("workMode")), ("Senior", 5, 9, "Remote"))


class BuiltInListsTests(FieldChecks, unittest.TestCase):
    @classmethod
    def use_lexicon(cls):
        cv_lexicon.use_builtin()


@unittest.skipUnless(cv_lexicon.default_path().is_file(), "The taxonomy file is not there")
class TaxonomyListsTests(FieldChecks, unittest.TestCase):
    @classmethod
    def use_lexicon(cls):
        cv_lexicon.use_file()
        assert cv_lexicon.get().source == "taxonomy"


if __name__ == "__main__":
    unittest.main()
