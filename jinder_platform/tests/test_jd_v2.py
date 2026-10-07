"""The job description reader, version 2 (item R1): level, years, work mode, skill levels, certifications, awards, education, specialisation,
and the description in the markup of the platform ("## Heading", "- bullet") that is never cut. The old keys stay.
The tests use the built-in word lists. The last class reads the 50 job descriptions of the sample data (if the file is there) and compares
the result with the structured fields that the writer of the data gave for each job."""
import json
import unittest
from pathlib import Path

import helpers as H  # noqa: F401 - sets the paths
from jinder import cv_lexicon, jd_parser as J


def parse(text):
    return J.parse_jd(text)


class JdCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cv_lexicon.use_builtin()

    @classmethod
    def tearDownClass(cls):
        cv_lexicon.reset()


JD = """Senior Data Engineer, Lakehouse

## About the role

Mallee Mesh builds a data platform for water utilities. We need a senior data engineer. The role is fully Remote and open to people anywhere in Australia.

## What you will do

- Build Spark pipelines in Databricks that handle late and messy meter data.
- Bring in data from customer systems with Azure Data Factory.

## What you bring

- 5 to 9 years in data engineering, with Databricks and Apache Spark at an advanced level (4 of 5).
- Python and SQL at an advanced level.
- A degree in IT, or equal experience.

## Nice to have

- Azure and Terraform experience.
- Mentoring of junior engineers.

## Certifications and awards

- Required certification: Databricks Certified Data Engineer Associate.
- Preferred certification: Databricks Certified Data Engineer Professional.
- Preferred award kind: Conference talk or paper.

## What we offer

- $150,000 to $168,000 a year, plus 12% superannuation.
"""


class OldKeysTests(JdCase):
    def test_the_old_keys_and_the_old_result_shape(self):
        r = parse("Data Analyst\nA 6-month contract in Sydney. Build dashboards in Power BI, write SQL queries and clean data with Python. $700 per day.")
        f = r["fields"]
        self.assertEqual((f["title"], f["type"], f["location"], f["salary"]), ("Data Analyst", "Contract", "Sydney", "$700 per day"))
        self.assertIn(f["category"], ("Technology & Data", "Data"))
        self.assertIn("SQL", f["skills"])
        self.assertEqual(r["missing"], [])
        self.assertTrue({"title", "category", "location", "type", "salary", "description", "skills"} <= set(r["detected"]))

    def test_a_job_that_is_not_an_it_job_still_reads(self):
        r = parse("Warehouse Supervisor\nLead a team of 12 and plan daily schedules and inventory accuracy for our distribution centre.")
        self.assertIn("location", r["missing"])
        self.assertIn("salary", r["missing"])
        self.assertIn(r["fields"].get("category", ""), ("Supply Chain & Logistics", ""))

    def test_the_new_keys_are_only_there_when_the_text_shows_them(self):
        r = parse("Office helper\nWe need someone to open the post and answer the phone.")
        for key in ("level", "minYears", "maxYears", "workMode", "skillRequirements", "certifications", "awards", "educationMin", "specialisation"):
            self.assertNotIn(key, r["fields"], key)

    def test_a_big_example(self):
        f = parse(JD)["fields"]
        self.assertEqual((f["title"], f["level"], f["minYears"], f["maxYears"], f["workMode"], f["specialisation"], f["domain"]),
                         ("Senior Data Engineer, Lakehouse", "Senior", 5, 9, "Remote", "Data engineering", "Data"))
        self.assertEqual(f["certifications"], {"required": ["Databricks Certified Data Engineer Associate"], "preferred": ["Databricks Certified Data Engineer Professional"]})
        self.assertEqual(f["awards"], {"preferred": ["conference-talk"]})
        self.assertEqual(f["educationMin"], "Bachelor's degree")
        self.assertEqual(f["salary"], "$150,000 – $168,000 per year")
        by = {s["name"]: s for s in f["skillRequirements"]}
        self.assertEqual((by["Databricks"]["level"], by["Databricks"]["must"]), (4, True))
        self.assertEqual((by["Python"]["level"], by["SQL"]["level"], by["Python"]["must"]), (4, 4, True))
        self.assertEqual((by["Azure"]["must"], by["Terraform"]["must"], by["Mentoring"]["must"]), (False, False, False))


class YearsTests(JdCase):
    def years(self, line, title="Engineer"):
        f = parse(f"{title}\n## What you bring\n- {line}\n- Good team spirit.")["fields"]
        return f.get("minYears"), f.get("maxYears")

    def test_the_forms(self):
        self.assertEqual(self.years("5+ years of experience in software."), (5, None))
        self.assertEqual(self.years("3-5 years of experience."), (3, 5))
        self.assertEqual(self.years("3 to 5 years in data engineering."), (3, 5))
        self.assertEqual(self.years("At least 4 years of relevant experience."), (4, None))
        self.assertEqual(self.years("12 or more years in software and cloud work."), (12, None))
        self.assertEqual(self.years("Minimum of two years in testing."), (2, None))
        self.assertEqual(self.years("0 to 2 years of experience, or a degree project."), (0, 2))
        self.assertEqual(self.years("Three years of experience as a developer."), (3, None))

    def test_years_with_one_skill_are_not_the_years_of_the_job(self):
        self.assertEqual(self.years("3 years with Kubernetes and Terraform."), (None, None))
        self.assertEqual(self.years("3+ years of experience in Python."), (None, None))
        self.assertEqual(self.years("5 years in machine learning, with Python and PyTorch."), (5, None))
        self.assertEqual(self.years("4 years of .NET work, with SQL Server."), (4, None))

    def test_only_a_maximum(self):
        self.assertEqual(self.years("Up to 2 years of experience in support."), (None, 2))

    def test_numbers_that_are_not_experience(self):
        f = parse("Engineer\nWe were founded 12 years ago. A 2 year contract. About us: 40 people.")["fields"]
        self.assertNotIn("minYears", f)

    def test_the_maximum_is_never_less_than_the_minimum(self):
        f = parse("Engineer\n## What you bring\n- 8 to 3 years of experience.")["fields"]
        self.assertNotIn("maxYears", f)

    def test_the_part_what_you_bring_comes_first(self):
        text = "Engineer\n## About the role\nThe team has 15 years of history in this field and wants help.\n## What you bring\n- 6+ years of experience."
        self.assertEqual(parse(text)["fields"]["minYears"], 6)


class LevelTests(JdCase):
    def test_the_title_first(self):
        for title, level in (("Senior Data Engineer", "Senior"), ("Junior QA Engineer", "Junior"), ("Lead Platform Engineer", "Lead"),
                             ("Principal Architect", "Principal"), ("Data Analyst Intern", "Intern"), ("Graduate Software Developer", "Junior"),
                             ("Mid-level Backend Developer", "Mid")):
            self.assertEqual(parse(f"{title}\nWork with the team on the product every day.")["fields"]["level"], level, title)

    def test_a_label(self):
        self.assertEqual(parse("Data Engineer\nSeniority: Senior\nWork with data.")["fields"]["level"], "Senior")

    def test_a_phrase_about_this_job(self):
        self.assertEqual(parse("Data Engineer\nThis is a senior-level role in a small team.")["fields"]["level"], "Senior")

    def test_a_word_about_another_person_is_not_the_level(self):
        f = parse("Data Analyst\n## About the role\nYou report to the lead engineer and the head of data. A principal architect reviews the work.")["fields"]
        self.assertNotIn("level", f)

    def test_from_the_years_when_there_is_no_word(self):
        for years, level in (("1 to 2 years", "Junior"), ("3 to 5 years", "Mid"), ("5+ years", "Senior"), ("0 to 1 years", "Junior")):
            f = parse(f"Data Analyst\n## What you bring\n- {years} of experience.")["fields"]
            self.assertEqual(f["level"], level, years)


class WorkModeTests(JdCase):
    def test_the_words(self):
        cases = {"The role is fully Remote.": "Remote", "100% remote, work from anywhere.": "Remote", "Remote-first team.": "Remote",
                 "This is a hybrid role in Sydney.": "Hybrid", "Two days a week in the office and three at home.": "Hybrid",
                 "On-site in our Melbourne office.": "Onsite", "Office-based role.": "Onsite", "You work in the office five days a week. Onsite.": "Onsite"}
        for sentence, mode in cases.items():
            self.assertEqual(parse(f"Engineer\n{sentence}")["fields"].get("workMode"), mode, sentence)

    def test_hybrid_wins_over_remote(self):
        self.assertEqual(parse("Engineer\nHybrid: some remote days, some office days.")["fields"]["workMode"], "Hybrid")

    def test_no_word_no_mode(self):
        self.assertNotIn("workMode", parse("Engineer\nBuild things in Sydney.")["fields"])


class SkillRequirementTests(JdCase):
    def reqs(self, text):
        return {s["name"]: s for s in parse(text)["fields"].get("skillRequirements", [])}

    def test_must_and_nice_by_the_part(self):
        got = self.reqs("Engineer\n## What you bring\n- Python and SQL.\n## Nice to have\n- Docker.\n## Tech stack\nKafka and Airflow.")
        self.assertEqual({k: v["must"] for k, v in got.items()}, {"Python": True, "SQL": True, "Docker": False, "Apache Kafka": False, "Apache Airflow": False})

    def test_the_level_words_and_scores(self):
        got = self.reqs("Engineer\n## What you bring\n- Python at an expert level (5 of 5).\n- SQL, proficient.\n- Docker, working knowledge.\n- Git (2 of 5).\n- Kafka.")
        self.assertEqual([got[k]["level"] for k in ("Python", "SQL", "Docker", "Git", "Apache Kafka")], [5, 3, 2, 2, 3])

    def test_one_level_for_all_the_skills_of_a_sentence(self):
        got = self.reqs("Engineer\n## What you bring\n- Databricks and Apache Spark at an advanced level (4 of 5).")
        self.assertEqual((got["Databricks"]["level"], got["Apache Spark"]["level"]), (4, 4))

    def test_years_with_a_skill_give_its_level(self):
        got = self.reqs("Engineer\n## What you bring\n- 5+ years of Python.")
        self.assertEqual(got["Python"]["level"], 4)

    def test_a_cue_in_the_sentence_wins(self):
        got = self.reqs("Engineer\n## What you bring\n- Python.\n- Docker is a plus.\n- Terraform preferred.")
        self.assertEqual([got[k]["must"] for k in ("Python", "Docker", "Terraform")], [True, False, False])

    def test_a_skill_that_is_in_two_parts_is_a_must(self):
        got = self.reqs("Engineer\n## What you bring\n- Python.\n## Nice to have\n- Python and Docker.")
        self.assertEqual((got["Python"]["must"], got["Docker"]["must"]), (True, False))

    def test_the_skills_that_are_not_tools(self):
        got = self.reqs("Engineer\n## What you bring\n- Mentoring and Stakeholder management.\n- Agile delivery.")
        self.assertEqual(sorted(got), ["Agile delivery", "Mentoring", "Stakeholder management"])

    def test_at_most_12_skills_and_each_one_once(self):
        text = "Engineer\n## What you bring\n- " + ", ".join(["Python", "Java", "SQL", "Docker", "Kubernetes", "Terraform", "AWS", "Azure", "Git", "Linux", "React",
                                                              "Angular", "Node.js", "Redis", "Python"]) + "."
        got = parse(text)["fields"]["skillRequirements"]
        self.assertEqual(len(got), 12)
        self.assertEqual(len({s["name"] for s in got}), 12)

    def test_the_company_part_is_not_read(self):
        got = self.reqs("Engineer\n## What you bring\n- Python.\n## About Acme Pty Ltd\nWe use Java, Kafka and Docker everywhere.")
        self.assertEqual(sorted(got), ["Python"])


class CertificationAwardEducationTests(JdCase):
    def test_required_and_preferred(self):
        f = parse("Engineer\n## Certifications and awards\n- Required certification: AWS Certified Solutions Architect - Associate.\n- Preferred certification: CKA.")["fields"]
        self.assertEqual(f["certifications"], {"required": ["AWS Certified Solutions Architect - Associate"], "preferred": ["Certified Kubernetes Administrator"]})

    def test_by_the_part_and_by_the_words(self):
        f = parse("Engineer\n## What you bring\n- AZ-900 or PL-300.\n## Nice to have\n- A Terraform Associate certificate is a plus.")["fields"]
        self.assertEqual(sorted(f["certifications"]["required"]), ["Microsoft Certified: Azure Fundamentals", "Microsoft Certified: Power BI Data Analyst Associate"])
        self.assertEqual(f["certifications"]["preferred"], ["HashiCorp Certified: Terraform Associate"])

    def test_a_certification_that_the_list_does_not_have_is_left_out(self):
        self.assertNotIn("certifications", parse("Engineer\n## What you bring\n- An AWS certification is preferred.")["fields"])

    def test_award_kinds(self):
        f = parse("Engineer\n## Certifications and awards\n- Awards we value: Conference talk or paper and Security competition or bug bounty. They are preferred.")["fields"]
        self.assertEqual(f["awards"], {"preferred": ["conference-talk", "security-competition"]})
        f = parse("Engineer\n## Nice to have\n- Kaggle competitions or a hackathon win are a plus.")["fields"]
        self.assertEqual(f["awards"], {"preferred": ["data-science-competition", "hackathon"]})

    def test_education_is_the_lowest_of_the_choices(self):
        cases = {"A master's degree or a PhD in a related field.": "Master's degree", "A diploma or a degree in IT, or equal experience.": "Diploma",
                 "A degree in computer science.": "Bachelor's degree", "A PhD in statistics.": "Doctorate (PhD)", "Bachelor's degree in engineering.": "Bachelor's degree",
                 "You finished high school.": "High school"}
        for sentence, label in cases.items():
            self.assertEqual(parse(f"Engineer\n## What you bring\n- {sentence}")["fields"]["educationMin"], label, sentence)

    def test_a_degree_that_is_only_preferred_is_not_a_minimum(self):
        self.assertNotIn("educationMin", parse("Engineer\n## Nice to have\n- A master's degree.")["fields"])
        self.assertNotIn("educationMin", parse("Engineer\n## What you bring\n- A PhD is preferred.")["fields"])

    def test_a_degree_in_the_company_part_is_not_read(self):
        self.assertNotIn("educationMin", parse("Engineer\n## About us\nOur founders have a PhD and a master's degree.")["fields"])


class SpecialisationTests(JdCase):
    def test_the_title_decides(self):
        cases = {"Senior Full-stack Engineer": "Full-stack", "Machine Learning Engineer": "Machine learning engineering", "Data Engineer": "Data engineering",
                 "Analytics Engineer": "Analytics engineering", "iOS Developer": "Mobile", "DevOps Engineer": "Platform and DevOps", "QA Engineer": "Quality engineering",
                 "Business Intelligence Developer": "Business intelligence", "Computer Vision Engineer": "Computer vision", "Data Scientist": "Data science"}
        for title, spec in cases.items():
            f = parse(f"{title}\nWork on the product with a friendly team in Sydney.")["fields"]
            self.assertEqual(f["specialisation"], spec, title)

    def test_the_domain(self):
        self.assertEqual(parse("Data Engineer\nBuild pipelines.")["fields"]["domain"], "Data")
        self.assertEqual(parse("Machine Learning Engineer\nTrain models.")["fields"]["domain"], "AI & Machine Learning")
        self.assertEqual(parse("Backend Engineer\nBuild APIs.")["fields"]["domain"], "Software Engineering")


class DescriptionTests(JdCase):
    def test_the_markup_is_made_from_the_headings_and_the_bullets(self):
        text = "Data Engineer\nAbout the role\nWe build things.\nWhat you will do:\n• Build the product\n• Test it\nREQUIREMENTS\n- Python\n"
        d = parse(text)["fields"]["description"]
        self.assertEqual(d, "## About the role\n\nWe build things.\n\n## What you will do\n\n- Build the product\n- Test it\n\n## REQUIREMENTS\n\n- Python".replace("## REQUIREMENTS", "## Requirements"))

    def test_any_line_with_two_hashes_is_a_heading(self):
        d = parse("Data Engineer\n## My own strange heading\nSome text here that is long enough to count.\n## Another\n- a bullet")["fields"]["description"]
        self.assertEqual(d.splitlines()[0], "## My own strange heading")
        self.assertIn("## Another", d)
        self.assertIn("- a bullet", d)

    def test_a_text_with_no_headings_gets_none(self):
        text = "Data Analyst\nWe need a data analyst for a short contract in Sydney.\nYou will build dashboards and write SQL.\nPlease apply now."
        d = parse(text)["fields"]["description"]
        self.assertNotIn("##", d)
        self.assertEqual(d, "We need a data analyst for a short contract in Sydney.\nYou will build dashboards and write SQL.\nPlease apply now.")

    def test_a_short_line_that_looks_like_a_heading_becomes_one(self):
        text = "Data Engineer\nWho we are\nWe are a small team that builds a data platform for councils and utilities across the state.\nWhat we need\n- Python\n- SQL"
        d = parse(text)["fields"]["description"]
        self.assertIn("## Who we are", d)
        self.assertIn("## What we need", d)

    def test_a_line_that_is_a_sentence_is_not_a_heading(self):
        d = parse("Engineer\nYou will build the product.\n- Python\nPlease apply by email.")["fields"]["description"]
        self.assertNotIn("##", d)

    def test_nothing_is_cut(self):
        paragraph = "This is a long paragraph about the role and the team. " * 20          # more than 1000 characters in one line
        text = "Data Engineer\n## About the role\n" + paragraph + "\n## What you bring\n" + "\n".join(f"- Skill number {i} with a long text that keeps going on and on." for i in range(60))
        d = parse(text)["fields"]["description"]
        self.assertIn(paragraph.strip(), d)
        self.assertIn("- Skill number 59 with", d)

    def test_a_6000_character_jd_keeps_all_its_text_and_its_markup(self):
        sections = ["About the role", "What you will do", "What you bring", "Nice to have", "Tech stack", "What we offer", "About the company", "How we hire"]
        parts = ["Senior Data Engineer, Platform", ""]
        for name in sections:
            parts += [f"## {name}", ""]
            parts += [f"Paragraph about {name.lower()} that explains the work in plain words and gives the reader a clear picture of the team and the product."] * 2
            parts += [f"- Item {i} in {name.lower()}: a full sentence that says what the person will do or needs to know." for i in range(1, 9)]
            parts += [""]
        text = "\r\n".join(parts)
        self.assertGreater(len(text), 6000)
        d = parse(text)["fields"]["description"]
        self.assertEqual(d.count("\n## "), len(sections) - 1)
        self.assertTrue(d.startswith("## About the role"))
        for name in sections:
            self.assertIn(f"## {name}\n", d)
            self.assertIn(f"- Item 8 in {name.lower()}:", d)
        self.assertEqual(sum(1 for line in d.splitlines() if line.startswith("- ")), 8 * len(sections))
        self.assertGreaterEqual(len(d), 0.95 * len("\n".join(parts[2:])))        # the text is kept (the title line is the only part that goes)
        self.assertNotIn("\r", d)

    def test_a_very_long_text_is_not_silently_cut(self):
        text = "Data Engineer\n## About the role\n" + "\n".join(f"Line {i} of a very long job description with enough words to count." for i in range(400))
        d = parse(text)["fields"]["description"]
        self.assertGreater(len(text), 20000)
        self.assertIn("Line 399 of a very long", d)

    def test_the_title_line_is_not_in_the_description(self):
        d = parse("Cloud Engineer\n## About the role\nBuild and run cloud systems for our customers.")["fields"]["description"]
        self.assertNotIn("Cloud Engineer", d.splitlines()[0])
        self.assertTrue(d.startswith("## About the role"))


class SampleJobsTests(unittest.TestCase):
    """The 50 job descriptions of the sample data, with the fields that the data writer gave. The reader never saw the fields."""
    PATH = Path(cv_lexicon.default_path()).parent.parent / "synthetic" / "jobs.json"

    @classmethod
    def setUpClass(cls):
        if not cls.PATH.is_file():
            raise unittest.SkipTest("The sample jobs are not there")
        cv_lexicon.use_file()
        cls.jobs = json.loads(cls.PATH.read_text(encoding="utf-8"))["jobs"]
        cls.results = [(j, J.parse_jd(j["title"] + "\n" + j["description"])["fields"]) for j in cls.jobs]

    @classmethod
    def tearDownClass(cls):
        cv_lexicon.reset()

    def rate(self, check):
        return sum(1 for j, f in self.results if check(j, f)) / float(len(self.results))

    def test_the_rates(self):
        rates = {
            "level": self.rate(lambda j, f: f.get("level") == j["level"]),
            "minYears": self.rate(lambda j, f: f.get("minYears") == j["minYears"]),
            "maxYears": self.rate(lambda j, f: f.get("maxYears") == j["maxYears"]),
            "workMode": self.rate(lambda j, f: f.get("workMode") == j["workMode"]),
            "domain": self.rate(lambda j, f: f.get("domain") == j["domain"]),
            "specialisation": self.rate(lambda j, f: f.get("specialisation") == j["specialisation"]),
            "certifications": self.rate(lambda j, f: {k: sorted(v) for k, v in f.get("certifications", {"required": [], "preferred": []}).items()}
                                        == {k: sorted(v) for k, v in j["certifications"].items()}),
            "awards": self.rate(lambda j, f: sorted(f.get("awards", {}).get("preferred", [])) == sorted(j["awards"]["preferred"])),
        }
        print("\n[sample jobs] " + ", ".join(f"{k} {v:.0%}" for k, v in rates.items()))
        for key, floor in (("level", 0.95), ("minYears", 0.95), ("maxYears", 0.95), ("workMode", 0.98), ("domain", 0.95), ("specialisation", 0.85),
                           ("certifications", 0.95), ("awards", 0.9)):
            self.assertGreaterEqual(rates[key], floor, key)

    def test_the_skills(self):
        recall = precision = 0.0
        for j, f in self.results:
            got = {s["name"] for s in f.get("skillRequirements", [])}
            want = {s["name"] for s in j["skills"]}
            recall += len(got & want) / float(len(want))
            precision += len(got & want) / float(max(1, len(got)))
        n = float(len(self.results))
        print(f"\n[sample jobs] skill names: recall {recall / n:.0%}, precision {precision / n:.0%}")
        self.assertGreaterEqual(recall / n, 0.9)
        self.assertGreaterEqual(precision / n, 0.85)

    def test_the_description_keeps_all_the_text_and_the_headings(self):
        for j, f in self.results:
            with self.subTest(j["title"]):
                d = f["description"]
                self.assertEqual(d.replace("\r", ""), j["description"].replace("\r", "").strip())

    def test_a_degree_is_only_read_when_the_text_says_it(self):
        for j, f in self.results:
            if "educationMin" in f:
                with self.subTest(j["title"]):
                    self.assertRegex(j["description"], r"(?i)degree|diploma|phd|master|bachelor|school")


if __name__ == "__main__":
    unittest.main()
