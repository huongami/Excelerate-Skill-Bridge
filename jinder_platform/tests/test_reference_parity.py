"""The pick-lists of the frontend (app/js/data/reference.js) must match the taxonomy (ict_taxonomy.json).

The test reads the JavaScript file as text and turns the lists into Python values. It needs no Node.js.
It checks that every list has the same names as the taxonomy, in the same spelling (names are case-sensitive).
"""
import json
import re
import unittest
from pathlib import Path

import helpers as H  # noqa: F401 - sets the environment before the platform is imported
from jinder import config, reference

JS_FILE = config.APP_DIR / "js" / "data" / "reference.js"
LEVELS_FILE = config.APP_DIR / "js" / "data" / "levels.js"


def _strip_comments(src: str) -> str:
    """Remove // comments and /* */ comments that are outside of strings."""
    out = []
    i = 0
    n = len(src)
    while i < n:
        c = src[i]
        if c == '"':
            j = i + 1
            while j < n and src[j] != '"':
                j += 2 if src[j] == "\\" else 1
            out.append(src[i:j + 1])
            i = j + 1
        elif src.startswith("//", i):
            while i < n and src[i] != "\n":
                i += 1
        elif src.startswith("/*", i):
            end = src.find("*/", i + 2)
            i = n if end < 0 else end + 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _literal(src: str, name: str):
    """The value of `export const NAME = <array or object literal>;` as a Python value."""
    m = re.search(r"export const " + re.escape(name) + r"\s*=\s*", src)
    if not m:
        raise AssertionError("reference.js has no list named " + name)
    start = m.end()
    if src[start] not in "[{":
        raise AssertionError(name + " is not a literal list or object")
    depth = 0
    i = start
    in_str = False
    while i < len(src):
        c = src[i]
        if in_str:
            if c == "\\":
                i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c in "[{":
            depth += 1
        elif c in "]}":
            depth -= 1
            if depth == 0:
                break
        i += 1
    text = src[start:i + 1]
    strings = []

    def keep(match):
        strings.append(match.group(0))
        return "\u0000%d\u0000" % (len(strings) - 1)

    text = re.sub(r'"(?:[^"\\]|\\.)*"', keep, text)               # hide the strings
    text = re.sub(r"([{,]\s*)([A-Za-z_]\w*)\s*:", r'\1"\2":', text)   # quote the keys
    text = re.sub(r",(\s*[\]}])", r"\1", text)                     # no trailing comma
    text = re.sub("\u0000(\\d+)\u0000", lambda mm: strings[int(mm.group(1))], text)
    return json.loads(text)


class ReferenceParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tax = json.loads(config.TAXONOMY_PATH.read_text(encoding="utf-8"))
        cls.src = _strip_comments(JS_FILE.read_text(encoding="utf-8"))
        cls.levels_src = _strip_comments(LEVELS_FILE.read_text(encoding="utf-8"))

    def js(self, name):
        return _literal(self.src, name)

    def test_the_file_says_which_taxonomy_version_it_follows(self):
        self.assertIn("version %s" % self.tax["version"], JS_FILE.read_text(encoding="utf-8"))

    def test_domains(self):
        self.assertEqual(self.js("DOMAINS"), [d["name"] for d in self.tax["domains"]])
        self.assertEqual(len(self.js("DOMAINS")), 3)

    def test_specialisations_of_each_domain(self):
        expected = {d["name"]: d["specialisations"] for d in self.tax["domains"]}
        self.assertEqual(self.js("SPECIALISATIONS"), expected)

    def test_roles(self):
        self.assertEqual(self.js("ROLES"), [r["title"] for r in self.tax["roles"]])

    def test_certifications(self):
        js = self.js("CERTIFICATIONS")
        self.assertEqual([c["name"] for c in js], [c["name"] for c in self.tax["certifications"]])
        by_name = {c["name"]: c for c in self.tax["certifications"]}
        for c in js:                                              # the issuer, the domains and the tier too
            t = by_name[c["name"]]
            self.assertEqual((c["issuer"], c["domains"], c["tier"]), (t["issuer"], t["domains"], t["tier"]), c["name"])

    def test_award_kinds(self):
        js = self.js("AWARD_KINDS")
        self.assertEqual([(a["kind"], a["label"]) for a in js], [(a["kind"], a["label"]) for a in self.tax["awardKinds"]])

    def test_fields_of_study(self):
        self.assertEqual(self.js("FIELDS_OF_STUDY"), self.tax["fieldsOfStudy"])

    def test_cities(self):
        self.assertEqual(self.js("CITIES"), self.tax["cities"])
        self.assertEqual(self.js("CITIES")[-1], "Remote")

    def test_work_types(self):
        self.assertEqual(self.js("WORK_TYPES"), self.tax["workTypes"])

    def test_skill_names(self):
        js = self.js("SKILL_NAMES")
        names = [s["name"] for s in self.tax["skills"]]
        self.assertEqual(sorted(js), sorted(names))
        self.assertEqual(len(js), len(set(js)), "a skill name is in the list twice")

    def test_skill_suggestions_are_taxonomy_skills(self):
        names = {s["name"] for s in self.tax["skills"]}
        js = self.js("SKILL_SUGGESTIONS")
        self.assertEqual(sorted(js), sorted(d["name"] for d in self.tax["domains"]))
        for domain, items in js.items():
            self.assertTrue(items, domain)
            for name in items:
                self.assertIn(name, names, "%s: %s" % (domain, name))

    def test_levels_work_modes_and_skill_levels(self):
        self.assertEqual(_literal(self.levels_src, "LEVELS"), [l["name"] for l in self.tax["levels"]])
        self.assertEqual(_literal(self.levels_src, "WORK_MODES"), self.tax["workModes"])
        skill_levels = _literal(self.levels_src, "SKILL_LEVELS")
        self.assertEqual([(x["value"], x["label"]) for x in skill_levels], [(x["level"], x["label"]) for x in self.tax["skillLevels"]])

    def test_the_old_names_are_the_domains(self):
        self.assertRegex(self.src, r"export const INDUSTRIES = DOMAINS;")
        self.assertRegex(self.src, r"export const JOB_CATEGORIES = DOMAINS;")

    def test_the_backend_lists_have_the_same_names(self):
        """The server pick-lists (jinder/reference.py) and the browser pick-lists come from the same file."""
        self.assertEqual(self.js("DOMAINS"), list(reference.DOMAINS))
        self.assertEqual(self.js("ROLES"), list(reference.ROLES))
        self.assertEqual(self.js("FIELDS_OF_STUDY"), list(reference.FIELDS_OF_STUDY))
        self.assertEqual(self.js("CITIES"), list(reference.CITIES))
        self.assertEqual(sorted(self.js("SKILL_NAMES")), sorted(reference.SKILL_NAMES))
        self.assertEqual([c["name"] for c in self.js("CERTIFICATIONS")], [c if isinstance(c, str) else c["name"] for c in reference.CERTIFICATIONS])
        self.assertEqual([a["kind"] for a in self.js("AWARD_KINDS")], list(reference.AWARD_KINDS))

    def test_no_name_of_another_field_of_work(self):
        """The three-domain rule (D2): no list has an old field."""
        text = json.dumps([self.js(n) for n in ("DOMAINS", "ROLES", "FIELDS_OF_STUDY", "SKILL_NAMES")]).lower()
        # "Data Warehouse Engineer" and "Data warehousing" are ICT names, so "warehouse" alone is not a sign of an old field
        for word in ("nurse", "nursing", "accountant", "accounting", "hospitality", "supply chain", "logistics", "warehouse supervisor",
                     "civil engineer", "marketing manager", "chef", "ahpra"):
            self.assertNotIn(word, text)


if __name__ == "__main__":
    unittest.main()
