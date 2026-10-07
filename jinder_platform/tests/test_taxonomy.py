"""The taxonomy, the data files, and the platform lists that come from them.

The four checkers of the data agents run as sub-processes (the exit code must be 0). The platform loader reads the same file.
The product covers three domains only: no list, no pick-list and no demo data of another field of work.
"""
import re
import subprocess
import sys
import unittest
from pathlib import Path

import helpers as H
from jinder import config, reference, skills, taxonomy, translation

DATA = Path(config.DATA_DIR)


class CheckerTests(unittest.TestCase):
    """The checkers of the Taxonomy and Data agents. They find a wrong name, a wrong count and a text that was cut."""

    def run_checker(self, folder: str, script: str):
        done = subprocess.run([sys.executable, script], cwd=str(DATA / folder), capture_output=True, text=True, timeout=600)
        self.assertEqual(done.returncode, 0, f"{script} failed:\n{done.stdout[-3000:]}\n{done.stderr[-1000:]}")

    def test_validate_taxonomy(self):
        self.run_checker("reference", "validate_taxonomy.py")

    def test_validate_jobs(self):
        self.run_checker("synthetic", "validate_jobs.py")

    def test_validate_talents(self):
        self.run_checker("synthetic", "validate_talents.py")

    def test_check_pairing(self):
        self.run_checker("synthetic", "check_pairing.py")


class LoaderTests(unittest.TestCase):
    def test_the_lists_of_the_platform_are_the_lists_of_the_taxonomy(self):
        t = taxonomy.get()
        self.assertEqual(reference.DOMAINS, ["Software Engineering", "AI & Machine Learning", "Data"])
        self.assertEqual((reference.INDUSTRIES, reference.JOB_CATEGORIES), (reference.DOMAINS, reference.DOMAINS))
        self.assertEqual(reference.LEVELS, ["Intern", "Junior", "Mid", "Senior", "Lead", "Principal"])
        self.assertEqual(reference.SKILL_LEVEL_LABELS, {1: "Beginner", 2: "Working", 3: "Proficient", 4: "Advanced", 5: "Expert"})
        self.assertEqual(reference.ROLES, t.role_titles)
        self.assertEqual(reference.FIELDS_OF_STUDY, t.fields_of_study)
        self.assertEqual((reference.LOCATIONS, reference.WORK_MODES, reference.WORK_TYPES), (t.cities, t.work_modes, t.work_types))
        self.assertEqual(reference.CERTIFICATIONS, t.certification_names)
        self.assertEqual(reference.AWARD_KINDS, t.award_kinds)
        self.assertEqual(reference.SKILL_NAMES, [s["name"] for s in t.skills])
        self.assertEqual(reference.CATEGORY_MAP, {d: [d] for d in reference.DOMAINS})
        self.assertEqual(reference.INDUSTRY_TO_CATEGORY, {d: d for d in reference.DOMAINS})
        self.assertEqual(set(reference.SKILL_SUGGESTIONS), set(reference.DOMAINS))
        for domain, names in reference.SKILL_SUGGESTIONS.items():
            self.assertEqual(len(names), 7)
            self.assertTrue(all(t.skill(n) for n in names), domain)
        self.assertTrue(all(any(s in reference.SPECIALISATIONS[d] for d in reference.DOMAINS) for s in reference.ALL_SPECIALISATIONS))

    def test_the_translation_library_uses_taxonomy_names_only(self):
        t = taxonomy.get()
        for item in translation._ROLES:
            self.assertIn(item["mapped"], t.role_titles, item["test"])
            self.assertEqual(item["anzsco"], str(t.occupation_of_role(item["mapped"])["code"]))
        for item in translation._SKILLS:
            self.assertIsNotNone(t.skill(item["mapped"]), item["test"])
        self.assertGreaterEqual(len(translation._ROLES), 30)
        self.assertGreaterEqual(len(translation._SKILLS), 40)
        for item in translation._ROLES + translation._SKILLS:
            self.assertIn(item["kind"], ("cross-border", "cross-industry", "direct"))

    def test_a_missing_file_is_a_clear_error(self):
        saved = config.TAXONOMY_PATH
        try:
            config.TAXONOMY_PATH = Path(config.VAR_DIR) / "no-such-taxonomy.json"
            with self.assertRaises(taxonomy.TaxonomyError) as cm:
                taxonomy.get()
            self.assertIn("The taxonomy file was not found", str(cm.exception))
            self.assertIn("no-such-taxonomy.json", str(cm.exception))
        finally:
            config.TAXONOMY_PATH = saved
        self.assertGreater(len(taxonomy.get().skills), 100)             # the real file is read again, once

    def test_the_file_is_read_once(self):
        self.assertIs(taxonomy.get(), taxonomy.get())


class SkillPatternTests(unittest.TestCase):
    def test_names_are_found_only_as_whole_words(self):
        cases = {
            "Customer service and plan C, R&D": [],
            "Skills: Python, R, SQL, C, Go": ["Python", "R", "SQL", "C", "Go"],
            "React with TypeScript and Node.js": ["React", "TypeScript", "Node.js"],
            "C# and C++ and .NET": ["C#", "C++", ".NET"],
            "Kubernetes.NETwork": ["Kubernetes"],
            "Go to market strategy": [],
            "We want a swift reply": [],
            "CI/CD pipelines": ["CI/CD"],
            "the rust on the pipe": [],
            "Proficient in R and Python": ["Python"],            # "R" counts in a list, not in a sentence
            "ASP.NET Core": [".NET"],
            "Reactive programming": [],
            "We use GitHub Actions daily": ["GitHub Actions", "Git"],
            "GitHub Actions": ["GitHub Actions"],             # a whole text that is a skill name gives that skill only
        }
        for text, expected in cases.items():
            self.assertEqual(sorted(skills.skills_in(text)), sorted(expected), text)

    def test_every_name_and_alias_of_the_taxonomy_gives_its_skill(self):
        for s in taxonomy.get().skills:
            for term in [s["name"]] + s.get("aliases", []):
                self.assertEqual(skills.skills_in(term), [s["name"]], term)
                self.assertEqual(skills.canonical_skill_name(term.upper()), s["name"], term)

    def test_a_long_text_is_read_quickly(self):
        import json
        import time
        jobs = json.loads((Path(config.SYNTHETIC_DIR) / "jobs.json").read_text(encoding="utf-8"))["jobs"]
        started = time.time()
        for j in jobs:
            found = skills.skills_in(j["description"])
            self.assertTrue(set(s["name"] for s in j["skills"] if s["must"]) & set(found), j["key"])    # at least one must-have skill is found
        self.assertLess(time.time() - started, 15)

    def test_related_skills_are_symmetric(self):
        for a, bs in skills.RELATED.items():
            for b in bs:
                self.assertIn(a, skills.RELATED[b])

    def test_the_skills_of_a_title(self):
        names = skills.job_skills("Senior Data Engineer, Lakehouse", "")
        self.assertTrue({"SQL", "Python"} & set(names))
        self.assertLessEqual(len(names), 8)
        reqs = skills.suggest_requirements("Machine Learning Engineer", "We use PyTorch and MLflow.", "AI & Machine Learning", 10)
        self.assertEqual({"level": 3, "must": True}, {k: reqs[0][k] for k in ("level", "must")})
        self.assertTrue({"PyTorch", "MLflow"} <= {r["name"] for r in reqs[:3]})       # the skills of the text come first
        self.assertLessEqual(len(reqs), 10)
        self.assertTrue(all(taxonomy.get().skill(r["name"]) for r in reqs))
        self.assertEqual(skills.suggest_requirements("Owner of fun", "", "Data", 10)[0]["name"], reference.SKILL_SUGGESTIONS["Data"][0])  # the usual skills of the domain


class NoOtherFieldTests(unittest.TestCase):
    """The product is for ICT only. A word of another field of work must not be in the lists, the library or the demo data."""

    CODE_WORDS = ["nurse", "nursing", "ahpra", "accountant", "hospitality", "logistics", "(?<!data )(?<!data)warehouse", "civil engineer", "chef",
                  "marketing manager", "supply chain", "patient care", "aged care", "bookkeep", "payroll", "barista", "paramedic", "teacher",
                  "operations coordinator", "customer service representative", "retail store", "cpa australia"]
    # in a job text, a client may work in health, logistics or retail: only the words of a job in another field are forbidden there
    DATA_WORDS = ["nurse", "nursing", "ahpra", "accountant", "hospitality", "civil engineer", "chef", "marketing manager", "bookkeeper", "barista",
                  "paramedic", "operations coordinator", "registered nurse"]

    def scan(self, text: str, words):
        return sorted({w for w in words if re.search(w, text, re.I)})

    def test_the_code_has_no_word_of_another_field(self):
        for name in ("reference", "skills", "translation", "seed", "taxonomy", "catalogue", "engine_bridge", "store", "util", "app"):
            text = (H.ROOT / "jinder" / f"{name}.py").read_text(encoding="utf-8")
            self.assertEqual(self.scan(text, self.CODE_WORDS), [], f"jinder/{name}.py")

    def test_the_demo_data_has_no_job_of_another_field(self):
        import json
        for name in ("jobs", "talents", "demo"):
            text = (Path(config.SYNTHETIC_DIR) / f"{name}.json").read_text(encoding="utf-8")
            self.assertEqual(self.scan(text, self.DATA_WORDS), [], f"{name}.json")
        # the titles, the roles and the skills too (a client of a job may be in another field: the client is not checked)
        jobs = json.loads((Path(config.SYNTHETIC_DIR) / "jobs.json").read_text(encoding="utf-8"))["jobs"]
        talents = json.loads((Path(config.SYNTHETIC_DIR) / "talents.json").read_text(encoding="utf-8"))["talents"]
        short = " ".join([j["title"] + " " + j["occupation"]["title"] + " " + " ".join(s["name"] for s in j["skills"]) for j in jobs]
                         + [t["currentRole"] + " " + " ".join(t["targetRole"]) + " " + " ".join(s["name"] for s in t["skills"]) for t in talents])
        self.assertEqual(self.scan(short, self.DATA_WORDS + ["supply chain", "patient care", "aged care", "bookkeep", "cpa australia"]), [])

    def test_the_lists_of_the_platform_are_ict_only(self):
        for name in ("INDUSTRIES", "ROLES", "FIELDS_OF_STUDY", "SKILL_NAMES", "CERTIFICATIONS", "JOB_CATEGORIES"):
            text = " ".join(getattr(reference, name))
            self.assertEqual(self.scan(text, self.CODE_WORDS), [], name)
        self.assertEqual(len(reference.INDUSTRIES), 3)
        for old in ("Healthcare", "Hospitality & Tourism", "Retail", "Education", "Construction", "Finance & Accounting", "Logistics & Supply Chain"):
            self.assertNotIn(old, reference.INDUSTRIES)
        for old in ("Nurse", "Chef", "Accountant", "Teacher", "Civil engineer"):
            self.assertNotIn(old, reference.ROLES)


if __name__ == "__main__":
    unittest.main()
