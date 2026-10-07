"""The browser-only mock backend (js/api/mock, used with ?mock=1) must be ICT only (decision D2).

The test reads the JavaScript files as text. It needs no Node.js. It checks that:
  * no file of the mock has a word of an old field of work (nurse, accountant, logistics, retail, marketing ...);
  * the embedded jobs, the demo data, the skill table, the translation tables and the samples use the names of the taxonomy;
  * the mock does not read the old CSV catalogue;
  * the demo accounts are the ones of the real seed (Teal Heron, Alex Morgan at Bluebushworks).
The browser check tests/browser/check_mock_ict.py runs the same data in a real browser.
"""
import json
import re
import unittest
from pathlib import Path

import helpers as H  # noqa: F401 - sets the environment before the platform is imported
from jinder import config

JS = Path(config.APP_DIR) / "js"
MOCK = JS / "api" / "mock"
TAX = json.loads(Path(config.TAXONOMY_PATH).read_text(encoding="utf-8"))
SYN = Path(config.SYNTHETIC_DIR)

# Words of the old fields of work (AI_Rule Rule 2). "data warehouse" is an ICT term, so it is allowed.
OLD_WORDS = re.compile(r"nurse|nursing|ahpra|accountant|accounting|\bcpa\b|hospitality|logistics|(?<!data )warehouse|\bcivil\b|\bchef\b|marketing|supply chain|patient|procurement|retail|construction|"
                       r"operations & administration|harbour", re.I)

DOMAINS = [d["name"] for d in TAX["domains"]]
SKILLS = {s["name"] for s in TAX["skills"]}
SKILL_TERMS = SKILLS | {a.lower() for s in TAX["skills"] for a in s["aliases"]} | {n.lower() for n in SKILLS}
CERTS = {c["name"] for c in TAX["certifications"]}
KINDS = {a["kind"] for a in TAX["awardKinds"]}
ROLES = {r["title"] for r in TAX["roles"]}
LEVELS = [x["name"] for x in TAX["levels"]]
CITIES = set(TAX["cities"])
TYPES = set(TAX["workTypes"])
MODES = set(TAX["workModes"])


def text(name: str) -> str:
    return (MOCK / name).read_text(encoding="utf-8")


def hits(source: str):
    return sorted({m.group(0).lower() for m in OLD_WORDS.finditer(source)})


class NoOldFieldTests(unittest.TestCase):
    def test_no_file_of_the_mock_has_a_word_of_an_old_field(self):
        for path in sorted(MOCK.glob("*.js")):
            self.assertEqual(hits(path.read_text(encoding="utf-8")), [], path.name)

    def test_the_old_categories_are_gone(self):
        for old in ("Technology & Data", "Healthcare & Nursing", "Finance & Accounting", "Supply Chain & Logistics", "Hospitality & Service", "Engineering & Construction",
                    "Marketing & Communications", "Hospitality & Tourism", "Government & Public Sector"):
            for path in MOCK.glob("*.js"):
                self.assertNotIn(old, path.read_text(encoding="utf-8"), f"{path.name}: {old}")

    def test_the_other_files_of_the_app_do_not_get_more_old_words(self):
        """The other agents own these files. The numbers are the lines that have an old word today. They must not grow."""
        known = {"views/landing.js": 3, "components/onboarding.js": 1}
        for path in sorted(JS.rglob("*.js")):
            rel = path.relative_to(JS).as_posix()
            if rel.startswith("api/mock/"):
                continue
            n = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if OLD_WORDS.search(line))
            self.assertLessEqual(n, known.get(rel, 0), f"{rel}: {n} line(s) with a word of an old field of work")


class CatalogueTests(unittest.TestCase):
    def test_the_mock_does_not_read_the_old_catalogue(self):
        src = text("jobs.js")
        for word in ("australian_jobs", "fetch(", ".csv", "parseCsv", "MOCK_JOBS_CSV_URL"):
            self.assertNotIn(word, src)

    def test_the_embedded_jobs_use_the_taxonomy(self):
        src = text("seed-jobs.js")
        self.assertEqual(len(re.findall(r"^\s+key: \"", src, re.M)), 24)
        self.assertEqual(set(re.findall(r"domain: \"([^\"]+)\"", src)) - set(DOMAINS), set())
        self.assertEqual(set(DOMAINS) - set(re.findall(r"domain: \"([^\"]+)\"", src)), set())
        self.assertTrue(set(re.findall(r"\blevel: \"([^\"]+)\"", src)) <= set(LEVELS))
        self.assertTrue(set(re.findall(r"city: \"([^\"]+)\"", src)) <= CITIES)
        self.assertTrue(set(re.findall(r"type: \"([^\"]+)\"", src)) <= TYPES)
        self.assertTrue(set(re.findall(r"workMode: \"([^\"]+)\"", src)) <= MODES)
        names = re.findall(r"\{ name: \"([^\"]+)\", level: [1-5], must: (?:true|false) \}", src)
        self.assertGreater(len(names), 150)
        self.assertEqual(sorted(set(names) - SKILLS), [])
        lists = [" ".join(pair) for pair in re.findall(r"required: \[([^\]]*)\], preferred: \[([^\]]*)\]", src)]
        certs = set(re.findall(r"\"([^\"]+)\"", " ".join(lists)))
        self.assertTrue(certs and certs <= CERTS, sorted(certs - CERTS))
        kinds = set(re.findall(r"\"([^\"]+)\"", " ".join(re.findall(r"awards: \{ preferred: \[([^\]]*)\] \}", src))))
        self.assertTrue(kinds <= KINDS, sorted(kinds - KINDS))
        for description in re.findall(r"description: `(.*?)`,\n", src, re.S):
            self.assertTrue(description.startswith("## About the role"))
            self.assertGreaterEqual(len(re.findall(r"^## ", description, re.M)), 6)
            self.assertNotIn("…", description)

    def test_the_embedded_jobs_are_jobs_of_the_synthetic_file(self):
        keys = set(re.findall(r"^\s+key: \"([^\"]+)\"", text("seed-jobs.js"), re.M))
        real = {j["key"] for j in json.loads((SYN / "jobs.json").read_text(encoding="utf-8"))["jobs"]}
        self.assertTrue(keys <= real, sorted(keys - real))

    def test_the_skill_table_is_the_taxonomy(self):
        src = text("jobs.js")
        rows = re.findall(r"^  \[\"([^\"]+)\", \"([^\"]*)\", \"([^\"]*)\"\],$", src, re.M)
        self.assertEqual([r[0] for r in rows], [s["name"] for s in TAX["skills"]])
        by = {s["name"]: s for s in TAX["skills"]}
        for name, aliases, related in rows:
            self.assertEqual(related.split("|") if related else [], by[name]["related"], name)
            self.assertTrue(set(aliases.split("|") if aliases else []) <= set(by[name]["aliases"]), name)

    def test_the_categories_are_the_three_domains(self):
        src = text("jobs.js")
        block = re.search(r"const CATEGORY_MAP = \{(.*?)\};", src, re.S).group(1)
        self.assertEqual(re.findall(r"\"([^\"]+)\":", block), DOMAINS)


class TranslationTests(unittest.TestCase):
    def test_the_translation_tables_are_the_taxonomy(self):
        src = text("translation.js")
        occ = dict(re.findall(r"^  \"(\d{6})\": \"([^\"]+)\",$", src, re.M))
        self.assertEqual(occ, {o["code"]: o["title"] for o in TAX["occupations"]})
        codes = dict(re.findall(r"^  \"([^\"]+)\": \"(\d{6})\",$", src, re.M))
        self.assertEqual(codes, {r["title"]: r["occupationCode"] for r in TAX["roles"]})

    def test_the_pairs_map_to_roles_and_skills_of_the_taxonomy(self):
        src = text("translation.js")
        mapped_roles = set(re.findall(r"^  role\(\".*?\", \"([^\"]+)\", \"(?:direct|cross-border|cross-industry)\"", src, re.M))
        mapped_skills = set(re.findall(r"^  skill\(\".*?\", \"([^\"]+)\", \"(?:direct|cross-border|cross-industry)\"", src, re.M))
        self.assertGreaterEqual(len(re.findall(r"^  role\(", src, re.M)), 25)
        self.assertGreaterEqual(len(re.findall(r"^  skill\(", src, re.M)), 30)
        self.assertEqual(sorted(mapped_roles - ROLES), [])
        self.assertEqual(sorted(mapped_skills - SKILLS), [])
        self.assertIn("AQF Level 7 (Bachelor degree)", src)


class DemoDataTests(unittest.TestCase):
    def test_the_demo_accounts_are_the_ones_of_the_real_seed(self):
        src = text("seed-demo.js")
        self.assertIn('alias: "Teal Heron"', src)
        self.assertIn("Linh Nguyen", src)
        self.assertIn('name: "Alex Morgan"', src)
        self.assertIn('company: "Bluebushworks"', src)
        self.assertIn("candidate@demo.jinder.app", src)
        self.assertIn("recruiter@demo.jinder.app", src)
        self.assertIn('targetRole: ["Data Engineer"]', src)
        demo = json.loads((SYN / "demo.json").read_text(encoding="utf-8"))["jobs"]
        self.assertEqual(re.findall(r"^\s+key: \"(demo-[^\"]+)\"", src, re.M), [j["key"] for j in demo])
        cfg = (JS / "config.js").read_text(encoding="utf-8")
        self.assertIn("Employer demo (Bluebushworks)", cfg)
        self.assertNotIn("Harbour", cfg)

    def test_the_sample_talents_are_in_the_synthetic_file(self):
        src = text("seed-demo.js")
        block = src[src.index("const SAMPLE_CANDIDATES"):src.index("const DEMO_TALENT")]
        aliases = re.findall(r"\{ alias: \"([^\"]+)\"", block)
        talents = {t["alias"]: t for t in json.loads((SYN / "talents.json").read_text(encoding="utf-8"))["talents"]}
        self.assertEqual(len(aliases), 10)
        self.assertTrue(set(aliases) <= set(talents), sorted(set(aliases) - set(talents)))
        skills = set(re.findall(r"\[\"([^\"]+)\", [1-5], [0-9.]+\]", block))
        self.assertGreater(len(skills), 40)
        self.assertEqual(sorted(skills - SKILLS), [])
        certs = set(re.findall(r"certifications: \[\{ name: \"([^\"]+)\"", block))
        self.assertTrue(certs <= CERTS, sorted(certs - CERTS))
        self.assertTrue(set(re.findall(r"kind: \"([^\"]+)\"", block)) <= KINDS)
        self.assertTrue(set(re.findall(r"industry: \[\"([^\"]+)\"\]", block)) <= set(DOMAINS))
        self.assertTrue(set(re.findall(r"currentRole: \[\"([^\"]+)\"\]", block)) <= ROLES)
        self.assertTrue(set(re.findall(r"\blevel: \"([^\"]+)\"", block)) <= set(LEVELS))

    def test_the_demo_talent_has_8_skills_with_levels(self):
        src = text("seed-demo.js")
        block = src[src.index("const DEMO_TALENT"):src.index("const DEMO_JOBS")]
        skills = re.findall(r"\[\"([^\"]+)\", ([1-5]), ([0-9.]+)\]", block)
        self.assertEqual([s[0] for s in skills], ["SQL", "Python", "Power BI", "spreadsheets", "Data analysis", "dashboards", "Informatica", "ER diagrams"])
        self.assertIn("Microsoft Certified: Power BI Data Analyst Associate", block)
        self.assertIn("Smart City Hackathon Runner-up", block)


class SampleTests(unittest.TestCase):
    def test_the_cv_samples_are_ict(self):
        src = text("cv-samples.js")
        self.assertGreaterEqual(len(re.findall(r"^  [a-z]+: \{$", src, re.M)), 5)
        self.assertTrue(set(re.findall(r"domain: \"([^\"]+)\"", src)) <= set(DOMAINS))
        self.assertTrue(set(re.findall(r"\blevel: \"([^\"]+)\"", src)) <= set(LEVELS))
        self.assertTrue(set(re.findall(r"kind: \"([^\"]+)\"", src)) <= KINDS)
        self.assertTrue(set(re.findall(r"certifications: \[\{ name: \"([^\"]+)\"", src)) <= CERTS)
        self.assertTrue(set(re.findall(r"targetRole: \[\"([^\"]+)\"\]", src)) <= ROLES)
        for names in re.findall(r"qualification: \[\"[^\"]*\"\], fieldOfStudy: \[\"([^\"]+)\"\]", src):
            self.assertIn(names, TAX["fieldsOfStudy"])

    def test_the_jd_samples_are_ict(self):
        src = text("jd-samples.js")
        self.assertGreaterEqual(len(re.findall(r"^    fields: \{$", src, re.M)), 4)
        self.assertTrue(set(re.findall(r"category: \"([^\"]+)\"", src)) <= set(DOMAINS))
        self.assertTrue(set(re.findall(r"location: \"([^\"]+)\"", src)) <= CITIES)
        self.assertTrue(set(re.findall(r"type: \"([^\"]+)\"", src)) <= TYPES)
        for description in re.findall(r"description: `(.*?)`,\n", src, re.S):
            self.assertGreaterEqual(len(re.findall(r"^## ", description, re.M)), 5)

    def test_the_storage_key_has_a_new_version(self):
        db = text("db.js")
        self.assertIn('const KEY = "jinder.mock.db.v2"', db)
        self.assertIn('"jinder.mock.db.v1"', db)       # the old data is removed


class FileHygieneTests(unittest.TestCase):
    def test_no_control_character_and_no_carriage_return(self):
        for path in sorted(MOCK.glob("*.js")) + [JS / "config.js"]:
            data = path.read_bytes()
            for bad, name in ((b"\x00", "NUL"), (b"\r", "CR"), (b"\x08", "backspace")):
                self.assertNotIn(bad, data, f"{path.name}: {name}")
            self.assertTrue(data.startswith(b"// "), path.name)
            self.assertTrue(data.endswith(b"\n"), path.name)
            if path.parent == MOCK:
                self.assertIn(b"MOCK BACKEND", data.split(b"\n")[0], path.name)


if __name__ == "__main__":
    unittest.main()
