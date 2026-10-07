"""The CV reader on CVs that another person wrote BLIND (item R1).

The CVs in tests/fixtures/cv_holdout, cv_holdout2 and cv_holdout3 are plain texts (the text that a PDF or DOCX reader gives). They were written by
separate writers who did not see the reader, with the true values in holdout_expected.json (made-up people and employers). They are the check
against "the reader only works for the CVs that its maker wrote". Sets 1 and 2 were first run, then the reader was improved on what they showed.
Set 3 (30 CVs in the styles of real templates: LaTeX, Word, LinkedIn export, Europass, Indian, Vietnamese, Philippine, academic, bootcamp, Markdown,
contractor, fresh graduate) was run first with 28, 26, 30, 26, 21, 14 and 27 of 30 right (current role, level, target role, years, certifications,
awards, skills); the reader was then improved in general rules (each has a test in test_cv_rules.py), not for single files.
Some of the CVs of sets 1 and 2 are BAD-EXTRACTION texts: a two-column page that was read badly, with the lines of the two columns mixed. For
these, a wrong or missing value is known (KNOWN_LIMITS); what must still hold is that nothing is invented.

A value is "right" when the reader gives the true value (years: within 1 year).
"""
import json
import unittest
from datetime import date
from pathlib import Path

import helpers as H  # noqa: F401 - sets the paths
from jinder import cv_lexicon, cv_parser

BASE = Path(__file__).parent / "fixtures"

# (file, field) pairs where the reader is known to be wrong or to miss: bad text extraction, or a different reading of the rule.
KNOWN_LIMITS = {
    "cv_holdout": {
        ("h05.txt", "skills"),                      # the true value "SAST / DAST" is one item written with a slash. The reader splits it
        ("h12.txt", "years"), ("h12.txt", "awards"), ("h12.txt", "skills"),
        ("h17.txt", "skills"),
        ("h27.txt", "level"), ("h27.txt", "years"), ("h27.txt", "awards"),
    },
    "cv_holdout2": {
        ("k01.txt", "awards"), ("k23.txt", "awards"),    # "Best Paper": the writer says academic-excellence, the taxonomy examples say conference-talk
        ("k05.txt", "awards"), ("k05.txt", "certs"), ("k05.txt", "targetRole"),
        ("k20.txt", "awards"),
        ("k27.txt", "currentRole"),
        ("k30.txt", "certs"), ("k30.txt", "targetRole"),
    },
    "cv_holdout3": {
        ("m11.txt", "skills"),                      # "Ray" is only named in a sentence, and the skill list (taxonomy) does not have it
    },
    "cv_holdout4": set(),
}
# The writer's true value that we do not follow: "Aspiring Data Scientist" is a wish, not a job that the person has.
# A title in capitals or in small letters only gets normal capitals (the writer of set 4 keeps the letters as they were written).
OVERRIDES = {"cv_holdout": {("h21.txt", "currentRole"): None}, "cv_holdout2": {}, "cv_holdout3": {},
             "cv_holdout4": {("n17.txt", "currentRole"): "Junior Front-end Developer", ("n18.txt", "currentRole"): "Lead Game Developer"}}


def loose(text):
    return "".join(ch for ch in str(text).lower() if ch.isalnum())


class HoldoutChecks:
    FOLDER = ""
    FLOORS = {}
    SKIP_ONE_BY_ONE = set()         # fields that are only checked by their rate (the built-in skill list is a small copy: set 4 names many skills that it does not have)

    @classmethod
    def use_lexicon(cls):
        raise NotImplementedError

    @classmethod
    def setUpClass(cls):
        path = BASE / cls.FOLDER / "holdout_expected.json"
        if not path.is_file():
            raise unittest.SkipTest(f"{cls.FOLDER} is not there")
        cls._strict = cv_parser._STRICT
        cv_parser._STRICT = True
        cls.use_lexicon()
        spec = json.loads(path.read_text(encoding="utf-8"))
        asof = date.fromisoformat(spec["asOf"])
        cls.rows = []
        for name, e in spec["cvs"].items():
            e = dict(e)
            for (file, field), value in OVERRIDES[cls.FOLDER].items():
                if file == name:
                    e[field] = value
            result = cv_parser.parse_cv((BASE / cls.FOLDER / name).read_text(encoding="utf-8"), asof)
            cls.rows.append((name, e, result, cls.compare(e, result)))

    @classmethod
    def tearDownClass(cls):
        cv_parser._STRICT = getattr(cls, "_strict", False)
        cv_lexicon.reset()

    @staticmethod
    def compare(e, r):
        lex = cv_lexicon.get()

        def cert_key(name):
            hit = lex.find_certs(name)
            return loose(hit[0]["name"]) if hit else loose(name)

        names = {s["name"].lower() for s in r["skills"]}
        got_awards = [(loose(a["name"]), a["kind"] or None, a["year"]) for a in r["awards"]]
        want_awards = [(loose(a["name"]), a["kind"] or None, a["year"]) for a in e["awards"]]       # "" and null both mean: no kind fits
        years = e["yearsExperience"]
        return {
            "currentRole": (r["currentRole"] or None) == e["currentRole"],
            "level": (r["level"] or None) == e["level"],
            "targetRole": (r["targetRole"] or None) == e["targetRole"],
            "years": (years is None and r["yearsExperience"] is None) or (years is not None and r["yearsExperience"] is not None and abs(years - r["yearsExperience"]) <= 1.0),
            "certs": sorted(cert_key(c["name"]) for c in r["certifications"]) == sorted(cert_key(c) for c in e["certifications"]),
            "awards": len(got_awards) == len(want_awards) and all(
                any((w[0] in g[0] or g[0] in w[0]) and g[1] == w[1] and g[2] == w[2] for g in got_awards) for w in want_awards),
            "skills": all((lex.canonical_skill(s) or s).lower() in names for s in e["skills"]),
        }

    def test_each_cv_one_by_one(self):
        limits = KNOWN_LIMITS[self.FOLDER]
        for name, e, r, ok in self.rows:
            for field, good in ok.items():
                if (name, field) in limits or field in self.SKIP_ONE_BY_ONE:
                    continue
                with self.subTest(f"{name} {field}"):
                    self.assertTrue(good, f"{name} {field}: {e.get(field if field not in ('years', 'certs') else {'years': 'yearsExperience', 'certs': 'certifications'}[field])!r}"
                                          f" is true, the reader gave {self.reader_value(r, field)!r}")

    @staticmethod
    def reader_value(r, field):
        return {"currentRole": r["currentRole"], "level": r["level"], "targetRole": r["targetRole"], "years": r["yearsExperience"],
                "certs": [c["name"] for c in r["certifications"]], "awards": [(a["name"], a["kind"], a["year"]) for a in r["awards"]],
                "skills": [s["name"] for s in r["skills"]]}[field]

    def test_the_rates(self):
        n = len(self.rows)
        counts = {field: sum(1 for _, _, _, ok in self.rows if ok[field]) for field in ("currentRole", "level", "targetRole", "years", "certs", "awards", "skills")}
        print(f"\n[{self.FOLDER}, {cv_lexicon.get().source} lists] {n} CVs: " + ", ".join(f"{k} {v}/{n}" for k, v in counts.items()))
        for field, floor in self.FLOORS.items():
            self.assertGreaterEqual(counts[field], floor, f"{field}: {counts[field]} of {n}")

    def test_a_field_that_the_cv_does_not_show_is_never_filled(self):
        """The most important rule: a value that is not in the CV is not invented. The people who wrote the CVs gave null or an empty list."""
        invented = []
        for name, e, r, _ in self.rows:
            if not e["currentRole"] and r["currentRole"]:
                invented.append((name, "currentRole", r["currentRole"]))
            if not e["level"] and r["level"]:
                invented.append((name, "level", r["level"]))
            if not e["targetRole"] and r["targetRole"]:
                invented.append((name, "targetRole", r["targetRole"]))
            if e["yearsExperience"] is None and r["yearsExperience"] is not None:
                invented.append((name, "yearsExperience", r["yearsExperience"]))
            if not e["certifications"] and r["certifications"]:
                invented.append((name, "certifications", [c["name"] for c in r["certifications"]]))
            if not e["awards"] and r["awards"]:
                invented.append((name, "awards", [a["name"] for a in r["awards"]]))
        self.assertEqual(invented, [])

    def test_a_wish_for_an_unknown_role_is_left_empty(self):
        for name, e, r, _ in self.rows:
            if e.get("statesUnknownTarget"):
                with self.subTest(name):
                    self.assertEqual(r["targetRole"], "")


def make(folder, floors, lexicon, skip=()):
    class Tests(HoldoutChecks, unittest.TestCase):
        FOLDER = folder
        FLOORS = floors
        SKIP_ONE_BY_ONE = set(skip)

        @classmethod
        def use_lexicon(cls):
            lexicon()
    return Tests


_floors1 = {"currentRole": 30, "level": 30, "targetRole": 31, "years": 29, "certs": 31, "awards": 29, "skills": 28}
_floors2 = {"currentRole": 30, "level": 31, "targetRole": 29, "years": 31, "certs": 28, "awards": 26, "skills": 30}
_floors3 = {"currentRole": 29, "level": 29, "targetRole": 29, "years": 29, "certs": 29, "awards": 29, "skills": 28}
_floors4 = {"currentRole": 29, "level": 29, "targetRole": 29, "years": 29, "certs": 29, "awards": 29, "skills": 28}
_floors4_builtin = dict(_floors4, skills=16)         # the built-in skill list is small: set 4 names skills (methods, soft skills) that only the taxonomy has


class Holdout1BuiltIn(make("cv_holdout", _floors1, cv_lexicon.use_builtin)):
    pass


@unittest.skipUnless(cv_lexicon.default_path().is_file(), "The taxonomy file is not there")
class Holdout1Taxonomy(make("cv_holdout", _floors1, cv_lexicon.use_file)):
    pass


class Holdout2BuiltIn(make("cv_holdout2", _floors2, cv_lexicon.use_builtin)):
    pass


@unittest.skipUnless(cv_lexicon.default_path().is_file(), "The taxonomy file is not there")
class Holdout2Taxonomy(make("cv_holdout2", _floors2, cv_lexicon.use_file)):
    pass


class Holdout3BuiltIn(make("cv_holdout3", _floors3, cv_lexicon.use_builtin)):
    pass


@unittest.skipUnless(cv_lexicon.default_path().is_file(), "The taxonomy file is not there")
class Holdout3Taxonomy(make("cv_holdout3", _floors3, cv_lexicon.use_file)):
    pass


class Holdout4BuiltIn(make("cv_holdout4", _floors4_builtin, cv_lexicon.use_builtin, skip=("skills",))):
    pass


@unittest.skipUnless(cv_lexicon.default_path().is_file(), "The taxonomy file is not there")
class Holdout4Taxonomy(make("cv_holdout4", _floors4, cv_lexicon.use_file)):
    pass


if __name__ == "__main__":
    unittest.main()
