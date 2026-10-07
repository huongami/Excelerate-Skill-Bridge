// MOCK BACKEND — demo data, written once into the mock store. The real backend replaces this file.
// All people and companies are made up. It tells the same story as the real seed (jinder_platform/jinder/seed.py), in a smaller form:
//   - 10 sample talents with ICT profiles (aliases, skills and certifications from the synthetic talent file). Employers see them only by alias.
//   - Talent demo Teal Heron (Linh Nguyen): a Mid data analyst who studied in Vietnam and wants to become a Data Engineer. She is in interview.
//   - Employer demo Alex Morgan (Bluebushworks) with 4 jobs (from the synthetic demo file), applications, alerts and some activity for the charts.
// The demo accounts are listed in config.js (MOCK_DEMO_ACCOUNTS). The password of both is "demo1234".
import { newId, sharedProfileOf, notify } from "./core.js";
import { demoHash } from "./db.js";
import { translateKeeping } from "./routes-account.js";
import { skillMatch, namesFromList, salaryText } from "./jobs.js";
import { YEARS } from "../../data/reference.js";

export const DEMO_PASSWORD = "demo1234"; // same as CONFIG.MOCK_DEMO_PASSWORD

const DAY = 864e5;
const at = (days) => new Date(Date.now() + days * DAY).toISOString();
// The band of "Total years of work experience" for an exact number of years (the same rule as the server and the onboarding)
const bandOf = (y) => (y < 1 ? YEARS[0] : y < 3 ? YEARS[1] : y < 6 ? YEARS[2] : y <= 10 ? YEARS[3] : YEARS[4]);

// Anonymous sample talents (no names, no countries in what employers see). skills: [name, level 1 to 5, years]
const SAMPLE_CANDIDATES = [
  { alias: "Jade Koala", currentRole: ["Data Warehouse Engineer"], level: "Senior", yearsExperience: 7.1, industry: ["Data"], specialisation: "Data engineering",
    qualification: ["Bachelor's degree"], fieldOfStudy: ["Information systems"], studyCountry: ["Philippines"],
    skills: [
      ["Snowflake", 5, 5.0], ["SQL", 5, 7.0], ["Data warehousing", 5, 7.0], ["dbt", 5, 3.5], ["Data modelling", 5, 6.0],
      ["ETL and ELT pipelines", 4, 6.0], ["Python", 4, 4.0], ["Google BigQuery", 3, 1.5], ["Database design and tuning", 4, 5.0],
      ["Data governance", 3, 3.0], ["Stakeholder management", 3, 4.0],
    ],
    certifications: [{ name: "SnowPro Core Certification", issuer: "Snowflake", year: 2021 }], awards: [],
    targetRole: ["Data Warehouse Engineer", "Data Engineer"], targetIndustries: ["Data"], locations: ["Melbourne"], workModes: ["Hybrid"], workTypes: ["Full-time"],
    evidence: [
      "Own a Snowflake data warehouse of 900 tables for billing and sales; query cost fell by 33% after clustering and data warehouse sizing.",
      "Moved the sales mart from an older data warehouse to Snowflake with no gaps in reporting.",
      "Introduced dbt tests and Data modelling standards; tickets about wrong numbers fell from 22 to 4 a quarter.",
      "Wrote Data governance rules for the data owners and Technical documentation for the key tables.",
    ] },
  { alias: "Plum Heron", currentRole: ["Data Engineer"], level: "Mid", yearsExperience: 4.6, industry: ["Data"], specialisation: "Data engineering",
    qualification: ["Bachelor's degree"], fieldOfStudy: ["Information technology"], studyCountry: ["India"],
    skills: [
      ["SQL", 4, 4.6], ["Python", 4, 4.6], ["Apache Spark", 4, 3.5], ["Apache Airflow", 4, 3.5], ["AWS", 4, 4.0], ["Amazon S3", 4, 4.0],
      ["ETL and ELT pipelines", 4, 4.6], ["Data modelling", 3, 3.0], ["Data warehousing", 3, 3.0], ["Amazon Redshift", 3, 3.0], ["Git", 3, 4.6],
      ["Apache Kafka", 2, 1.0], ["Data quality", 3, 2.5], ["AWS Lambda", 3, 2.0],
    ],
    certifications: [{ name: "AWS Certified Data Engineer - Associate", issuer: "Amazon Web Services", year: 2025 }], awards: [],
    targetRole: ["Data Engineer", "Data Platform Engineer"], targetIndustries: ["Data"], locations: ["Sydney"], workModes: ["Hybrid"], workTypes: ["Full-time"],
    evidence: [
      "Run the sales data lake on Amazon S3 and Apache Spark: 3 TB loads each day in 70 minutes, down from 4 hours.",
      "Own 60 Apache Airflow DAGs; on-time delivery of the morning reports rose from 88% to 99%.",
      "Added Data quality checks (row counts and null rates) to the core tables and found many upstream issues in the first month.",
      "Modelled the Amazon Redshift sales mart, tuned its SQL and wrote small AWS Lambda functions that trigger the loads.",
    ] },
  { alias: "Amber Finch", currentRole: ["Software Engineer"], level: "Senior", yearsExperience: 8.6, industry: ["Software Engineering"], specialisation: "Backend",
    qualification: ["Master's degree"], fieldOfStudy: ["Computer science"], studyCountry: ["India", "Australia"],
    skills: [
      ["Go", 5, 6.0], ["PostgreSQL", 5, 8.0], ["SQL", 5, 8.5], ["Apache Kafka", 4, 4.5], ["System design", 5, 6.0],
      ["Microservices architecture", 5, 5.5], ["API design", 5, 7.0], ["Docker", 4, 6.0], ["Python", 3, 4.0], ["ETL and ELT pipelines", 3, 2.0],
      ["Apache Airflow", 2, 1.0], ["Apache Spark", 2, 0.8], ["AWS", 4, 4.0], ["Technical leadership", 4, 3.0],
    ],
    certifications: [{ name: "Confluent Certified Developer for Apache Kafka", issuer: "Confluent", year: 2023 }], awards: [],
    targetRole: ["Data Engineer", "Big Data Engineer"], targetIndustries: ["Data", "Software Engineering"], locations: ["Melbourne"], workModes: ["Hybrid", "Remote"], workTypes: ["Full-time", "Contract"],
    evidence: [
      "Designed an event pipeline on Apache Kafka that moves 2.4 million order events a day into PostgreSQL reporting tables.",
      "Cut the p95 latency of the order search API from 1.8 seconds to 240 ms with new PostgreSQL indexes and a result cache.",
      "Moved nightly Python batch exports to Apache Airflow and built a first Apache Spark job for the billing team.",
      "Split a monolith into Go services using a Microservices architecture and shared API design guidelines.",
    ] },
  { alias: "Cyan Puffin", currentRole: ["Full-stack Engineer"], level: "Mid", yearsExperience: 3.4, industry: ["Software Engineering"], specialisation: "Full-stack",
    qualification: ["Master's degree"], fieldOfStudy: ["Computer science"], studyCountry: ["Germany"],
    skills: [
      ["Python", 5, 3.4], ["Django", 4, 3.0], ["React", 4, 2.5], ["PostgreSQL", 4, 3.0], ["JavaScript", 3, 3.0], ["TypeScript", 4, 2.0],
      ["API design", 4, 2.5], ["Git", 4, 3.4], ["LLM APIs", 3, 1.2], ["Prompt engineering", 3, 1.2], ["Retrieval-augmented generation", 2, 0.7],
      ["Product thinking", 3, 2.0], ["SQL", 3, 3.0], ["Unit and integration testing", 4, 2.5],
    ],
    certifications: [{ name: "NVIDIA-Certified Associate: Generative AI LLMs", issuer: "NVIDIA", year: 2025 }], awards: [{ name: "Applied AI Hackathon Finalist", kind: "hackathon", year: 2025 }],
    targetRole: ["Generative AI Engineer", "AI Engineer"], targetIndustries: ["AI & Machine Learning"], locations: ["Sydney"], workModes: ["Hybrid"], workTypes: ["Full-time"],
    evidence: [
      "Built a Django and React support portal for 2,500 customers and own the API design for its 30 endpoints.",
      "Added an LLM APIs assistant that drafts replies for agents; it cut the average reply time by 22% in a 6-week pilot.",
      "Wrote the Prompt engineering guide and a test set for the assistant.",
      "Prototyped Retrieval-augmented generation over the help articles with a first search index.",
    ] },
  { alias: "Lime Kestrel", currentRole: ["Data Scientist"], level: "Senior", yearsExperience: 8.5, industry: ["Data"], specialisation: "Data science",
    qualification: ["Master's degree"], fieldOfStudy: ["Statistics"], studyCountry: ["Australia"],
    skills: [
      ["Python", 5, 8.0], ["Statistics", 5, 8.5], ["Machine learning", 5, 7.0], ["scikit-learn", 3, 7.0], ["XGBoost", 4, 5.0],
      ["Experimentation and A/B testing", 5, 6.0], ["Time series forecasting", 4, 5.0], ["SQL", 4, 8.0], ["Feature engineering", 3, 6.0],
      ["Data storytelling", 4, 5.0], ["PyTorch", 2, 1.5], ["R", 3, 6.0], ["Model evaluation", 4, 5.0], ["Stakeholder management", 4, 5.0],
    ],
    certifications: [], awards: [{ name: "Speaker, Applied Statistics Meetup", kind: "conference-talk", year: 2024 }, { name: "National Forecasting Challenge Top 10", kind: "data-science-competition", year: 2023 }],
    targetRole: ["Machine Learning Engineer"], targetIndustries: ["AI & Machine Learning"], locations: ["Brisbane"], workModes: ["Hybrid"], workTypes: ["Full-time"],
    evidence: [
      "Built the Time series forecasting model that sets weekly stock for 1,200 products; the error fell from 19% to 11%.",
      "Run Experimentation and A/B testing for pricing; a 5-week test lifted the revenue per visit by 3.4%.",
      "Trained XGBoost and scikit-learn models for lead scoring that the sales team uses every day.",
      "Started to move models to production with PyTorch; I want a Machine learning engineering role.",
    ] },
  { alias: "Coral Fox", currentRole: ["Data Engineer"], level: "Mid", yearsExperience: 3.8, industry: ["Data"], specialisation: "Data engineering",
    qualification: ["Master's degree"], fieldOfStudy: ["Information technology"], studyCountry: ["Australia"],
    skills: [
      ["Azure Data Factory", 4, 3.0], ["Azure", 4, 3.5], ["Databricks", 4, 2.5], ["Apache Spark", 4, 2.5], ["Microsoft Fabric", 3, 1.2],
      ["Python", 4, 3.8], ["SQL", 4, 3.8], ["Data lakehouse", 3, 2.0], ["ETL and ELT pipelines", 4, 3.5], ["Git", 3, 3.5],
      ["Machine learning", 3, 1.0], ["scikit-learn", 3, 0.8], ["MLflow", 1, 0.4], ["Feature engineering", 2, 0.5],
    ],
    certifications: [{ name: "Microsoft Certified: Fabric Data Engineer Associate", issuer: "Microsoft", year: 2025 }, { name: "Databricks Certified Data Engineer Associate", issuer: "Databricks", year: 2024 }], awards: [],
    targetRole: ["Machine Learning Engineer"], targetIndustries: ["AI & Machine Learning"], locations: ["Adelaide", "Melbourne"], workModes: ["Hybrid"], workTypes: ["Full-time"],
    evidence: [
      "Built a lakehouse on Databricks and Azure Data Factory for a online shop with 180 tables and a nightly refresh in 55 minutes.",
      "Converted legacy SQL jobs into Apache Spark notebooks and cut the run cost.",
      "Trained a scikit-learn churn model on the lakehouse tables and logged the runs in MLflow as my first hands-on Machine learning project.",
      "Moved the billing reports to Microsoft Fabric as a pilot for 2 teams.",
    ] },
  { alias: "Mint Fox", currentRole: ["Data Engineer"], level: "Junior", yearsExperience: 1.9, industry: ["Data"], specialisation: "Data engineering",
    qualification: ["Advanced diploma"], fieldOfStudy: ["Information technology"], studyCountry: ["Australia"],
    skills: [
      ["SQL", 4, 1.9], ["Python", 3, 1.5], ["Apache Airflow", 2, 1.0], ["ETL and ELT pipelines", 3, 1.5], ["PostgreSQL", 3, 1.7], ["Git", 3, 1.8],
      ["Pandas", 3, 1.5], ["Amazon S3", 2, 1.0], ["Data modelling", 2, 1.0], ["AWS", 2, 1.0], ["Microsoft Excel", 3, 1.5], ["Data analysis", 3, 1.2],
    ],
    certifications: [], awards: [],
    targetRole: ["Data Engineer"], targetIndustries: ["Data"], locations: ["Melbourne"], workModes: ["Onsite", "Hybrid"], workTypes: ["Full-time"],
    evidence: [
      "Built 12 ETL and ELT pipelines in Python and SQL that load sales data into PostgreSQL every night.",
      "Moved 4 pipelines to Apache Airflow with retries and alerts; failed nightly loads fell from 9 a month to 1.",
      "Stored raw files in Amazon S3 and drew the first star schema with Data modelling guidance from a senior engineer.",
      "Checked vendor files with Pandas before each load and used Git branches for every pipeline change.",
    ] },
  { alias: "Cyan Falcon", currentRole: ["Machine Learning Engineer"], level: "Mid", yearsExperience: 4.2, industry: ["AI & Machine Learning"], specialisation: "Machine learning engineering",
    qualification: ["Master's degree"], fieldOfStudy: ["Computer science"], studyCountry: ["India"],
    skills: [
      ["Python", 5, 4.2], ["PyTorch", 3, 3.0], ["XGBoost", 4, 3.5], ["Machine learning", 5, 4.0], ["scikit-learn", 4, 4.0],
      ["Model evaluation", 4, 3.0], ["Docker", 4, 3.0], ["AWS", 3, 2.5], ["MLflow", 4, 2.0], ["Amazon SageMaker", 2, 1.2], ["Kubernetes", 2, 0.8],
      ["CI/CD", 2, 1.2], ["Git", 3, 4.0], ["MLOps", 3, 1.2],
    ],
    certifications: [{ name: "AWS Certified Machine Learning Engineer - Associate", issuer: "Amazon Web Services", year: 2025 }], awards: [],
    targetRole: ["MLOps Engineer", "ML Platform Engineer"], targetIndustries: ["AI & Machine Learning"], locations: ["Sydney"], workModes: ["Hybrid"], workTypes: ["Full-time"],
    evidence: [
      "Built and shipped an XGBoost model that scores 90,000 insurance quotes a day and lifted conversions by 6%.",
      "Packaged the Python scoring service with Docker and deployed it on AWS behind a low-latency API.",
      "Track experiments in MLflow and trained a PyTorch model for document triage using a Model evaluation checklist.",
      "Want to move to MLOps: set up a first Amazon SageMaker pipeline and CI/CD checks for 2 models.",
    ] },
  { alias: "Sage Lynx", currentRole: ["Site Reliability Engineer"], level: "Senior", yearsExperience: 8.2, industry: ["Software Engineering"], specialisation: "Platform and DevOps",
    qualification: ["Bachelor's degree (Honours)"], fieldOfStudy: ["Electrical and computer engineering"], studyCountry: ["New Zealand"],
    skills: [
      ["Kubernetes", 5, 6.0], ["Prometheus", 3, 5.0], ["Grafana", 3, 5.0], ["Observability", 5, 5.5], ["Site reliability engineering", 5, 6.0],
      ["Linux", 5, 8.0], ["Go", 4, 4.0], ["Terraform", 4, 5.0], ["AWS", 3, 6.0], ["Incident response", 4, 6.0], ["Docker", 3, 7.0], ["CI/CD", 4, 5.0],
      ["Networking fundamentals", 3, 6.0], ["Technical leadership", 4, 3.0],
    ],
    certifications: [{ name: "Certified Kubernetes Administrator", issuer: "Cloud Native Computing Foundation", year: 2022 }, { name: "AWS Certified DevOps Engineer - Professional", issuer: "Amazon Web Services", year: 2023 }, { name: "HashiCorp Certified: Terraform Associate", issuer: "HashiCorp", year: 2021 }], awards: [],
    targetRole: ["Site Reliability Engineer", "Platform Engineer"], targetIndustries: ["Software Engineering"], locations: ["Melbourne"], workModes: ["Remote", "Hybrid"], workTypes: ["Full-time"],
    evidence: [
      "On-call lead for Incident response on a platform with 120 services; cut the mean time to recover from 52 to 14 minutes.",
      "Defined service level objectives with Site reliability engineering practice; error-budget reports go to every team each week.",
      "Built the Prometheus and Grafana stack and the Observability dashboards; alert noise fell by 65%.",
      "Wrote a Go operator that scales Kubernetes jobs and saves about a third of the node hours.",
    ] },
  { alias: "Slate Seal", currentRole: ["Data Analyst"], level: "Mid", yearsExperience: 4.9, industry: ["Data"], specialisation: "Data analytics",
    qualification: ["Master's degree"], fieldOfStudy: ["Data science"], studyCountry: ["Australia"],
    skills: [
      ["SQL", 5, 4.9], ["Python", 4, 3.5], ["Pandas", 4, 3.5], ["Data analysis", 4, 4.9], ["Data visualisation", 5, 4.5], ["Statistics", 3, 3.0],
      ["Experimentation and A/B testing", 3, 2.0], ["scikit-learn", 2, 1.0], ["Machine learning", 3, 1.5], ["Tableau", 4, 3.0],
      ["Microsoft Excel", 4, 4.9], ["Data storytelling", 4, 3.5], ["Looker", 3, 2.0], ["Stakeholder management", 3, 2.0],
    ],
    certifications: [{ name: "Tableau Certified Data Analyst", issuer: "Salesforce", year: 2023 }], awards: [{ name: "Open Data Prediction Cup, Silver Tier", kind: "data-science-competition", year: 2024 }],
    targetRole: ["Data Scientist"], targetIndustries: ["Data", "AI & Machine Learning"], locations: ["Sydney"], workModes: ["Hybrid", "Remote"], workTypes: ["Full-time"],
    evidence: [
      "Own the SQL model behind the weekly growth report for 4 product teams and replaced 18 manual spreadsheets.",
      "Designed and read out 12 Experimentation and A/B testing results; 3 changes shipped with a combined 7% sign-up lift.",
      "Built a first scikit-learn churn model on Pandas features as a Machine learning side project.",
      "Teach Tableau and Looker basics in a monthly workshop for colleagues.",
    ] },
];

// The demo talent: a Mid data analyst who studied in Vietnam and wants to become a Data Engineer. Her titles are overseas titles, so the
// translation shows the cross-border step ("BI Specialist" and "MIS Executive" become one Data Analyst card). She has 8 skills with levels,
// one certification and one award. She is a strong fit for data analyst jobs, a medium fit for data engineering jobs, and a weak fit for backend jobs.
const DEMO_TALENT = {
  alias: "Teal Heron", currentRole: ["BI Specialist", "MIS Executive"], level: "Mid", yearsExperience: 4.5, industry: ["Data"], specialisation: "Data analytics",
  qualification: ["Bachelor's degree"], fieldOfStudy: ["Information systems"], studyCountry: ["Vietnam"],
  skills: [["SQL", 4, 4.5], ["Python", 3, 2.5], ["Power BI", 4, 3.5], ["spreadsheets", 4, 4.5], ["Data analysis", 4, 4.0], ["dashboards", 3, 3.5], ["Informatica", 2, 0.8], ["ER diagrams", 3, 2.0]],
  certifications: [{ name: "Microsoft Certified: Power BI Data Analyst Associate", issuer: "Microsoft", year: 2024 }],
  awards: [{ name: "Smart City Hackathon Runner-up", kind: "hackathon", year: 2023 }],
  targetRole: ["Data Engineer"], targetIndustries: ["Data"], locations: ["Melbourne", "Sydney"], workModes: ["Hybrid", "Remote"], workTypes: ["Full-time"],
  evidence: [
    "Built the weekly sales and stock dashboards in Power BI for 6 regional teams, replacing 14 manual spreadsheets.",
    "Wrote SQL queries and Python scripts to clean and join data from 5 source systems before each monthly report.",
    "Designed the report data model (ER diagrams) for the company data warehouse together with two engineers.",
    "Started to load data with Informatica jobs for the monthly reports.",
  ],
};

// The 4 jobs of the demo employer. The new fields (level, years, work mode, skill levels, certifications, awards) are only for the job pages of talent:
// the employer screens of the mock keep the old fields (plan F9).
const DEMO_JOBS = [
  {
    key: "demo-data-engineer-mid", title: "Data Engineer, Solar Analytics", company: "Bluebushworks",
    domain: "Data", specialisation: "Data engineering", level: "Mid", minYears: 3, maxYears: 6,
    type: "Full-time", workMode: "Hybrid", city: "Sydney", area: "Sydney NSW",
    salary: { min: 118000, max: 138000, unit: "year" }, occupation: { code: "262111", title: "Data Engineer" },
    skills: [
      { name: "SQL", level: 4, must: true }, { name: "Python", level: 4, must: true }, { name: "ETL and ELT pipelines", level: 3, must: true },
      { name: "Data modelling", level: 3, must: true }, { name: "Apache Airflow", level: 3, must: false },
      { name: "Snowflake", level: 3, must: false }, { name: "dbt", level: 3, must: false }, { name: "AWS", level: 3, must: false },
      { name: "Git", level: 3, must: false }, { name: "Data quality", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["SnowPro Core Certification"] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 6, closesInDays: 30,
    description: `## About the role

Bluebushworks helps solar and battery installers quote, plan and track their jobs, and every installed system reports its output back to us every five minutes. The Solar Analytics team of five turns those readings into reports for installers and homeowners. We need a mid-level data engineer to take over the pipelines that load, clean and join this data. This is a Hybrid role in our Sydney office, close to the installers' product team.

## What you will do

- Run and improve the pipelines that load system readings and weather data into Snowflake.
- Schedule the jobs in Apache Airflow and handle retries and late data.
- Model tables for systems, sites and installers, so that reports stay quick.
- Move older SQL scripts into dbt models with tests.
- Add checks that catch a dead inverter feed before a homeowner does.
- Answer data questions from the product and support teams.

## What you bring

- 3 to 6 years in data engineering or a data-heavy developer role.
- SQL and Python at an advanced level (4 of 5), with tests for both.
- ETL and ELT pipelines at a proficient level (3 of 5): loads, retries and backfills.
- Data modelling at a proficient level, with clean keys and clear names.
- A habit of writing short notes so that others can run your jobs.

## Nice to have

- Apache Airflow, Snowflake or dbt in production.
- AWS basics, and Git habits for team work.
- Data quality tools or tests that you built.

## Tech stack

Python, SQL, Apache Airflow, Snowflake and dbt on AWS, with Git for all code.

## Certifications and awards

- Preferred certification: SnowPro Core Certification.

## What we offer

- $118,000 to $138,000 a year, plus 12% superannuation.
- Hybrid work: three days a week in our Sydney office and two at home.
- Four weeks of annual leave, plus two extra days to spend with family.
- A learning budget of $2,000 a year.
- A small team where your pipelines reach customers within days.

## About Bluebushworks

Bluebushworks makes planning and quoting software for solar and battery installers. It was founded in 2019 and has about 90 people, with its head office in Sydney. Its software is used on thousands of home installations each year.

## How we hire

- A 30-minute call with the data lead.
- A SQL and Python exercise that you do live with one engineer.
- A talk with two teammates about a pipeline that you built.
- An answer within a week.`,
  },
  {
    key: "demo-backend-senior", title: "Senior Backend Engineer, Installer Platform", company: "Bluebushworks",
    domain: "Software Engineering", specialisation: "Backend", level: "Senior", minYears: 6, maxYears: 11,
    type: "Full-time", workMode: "Hybrid", city: "Sydney", area: "Sydney NSW",
    salary: { min: 165000, max: 185000, unit: "year" }, occupation: { code: "261313", title: "Software Engineer" },
    skills: [
      { name: "Python", level: 5, must: true }, { name: "Django", level: 4, must: true }, { name: "PostgreSQL", level: 4, must: true },
      { name: "AWS", level: 4, must: true }, { name: "System design", level: 4, must: true }, { name: "API design", level: 4, must: true },
      { name: "Docker", level: 4, must: false }, { name: "Redis", level: 3, must: false },
      { name: "Unit and integration testing", level: 4, must: false }, { name: "Mentoring", level: 3, must: false },
      { name: "Code review", level: 4, must: false }, { name: "Observability", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["AWS Certified Solutions Architect - Associate"] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 3, closesInDays: 26,
    description: `## About the role

The Installer Platform is the backend that 2,500 solar and battery installers use to quote jobs, order equipment and book inspections. It is a Django application with a PostgreSQL database, and it has doubled in size twice in three years. We are hiring a senior backend engineer to guide its next stage: faster quotes, safer integrations with equipment suppliers and a design that more engineers can work in at once. This is a Hybrid role in Sydney.

## What you will do

- Design and build new parts of the platform in Python and Django, from quotes to orders.
- Split the largest Django app into clear modules with strong boundaries.
- Build integrations with equipment suppliers and keep them safe when a supplier is slow.
- Speed up PostgreSQL queries and plan schema changes that do not lock tables.
- Run the platform on AWS and improve the logs, traces and alerts.
- Review code and coach three engineers.
- Write design notes for the choices that last.

## What you bring

- 6 to 11 years of backend work, with Python at an expert level (5 of 5).
- Django and PostgreSQL at an advanced level (4 of 5), including migrations at scale.
- AWS at an advanced level: queues, storage, networking and cost.
- System design and API design at an advanced level, shown in live systems.
- A habit of writing and talking in plain words about trade-offs.

## Nice to have

- Redis and Observability tools at a proficient level, and Docker at an advanced level.
- Strong Unit and integration testing habits.
- Code review and Mentoring that people thank you for.

## Tech stack

Python, Django, PostgreSQL, Redis and Docker on AWS. Tests use pytest, and the team uses Git with short reviews.

## Certifications and awards

- Preferred certification: AWS Certified Solutions Architect - Associate.

## What we offer

- $165,000 to $185,000 a year, plus 12% superannuation.
- Hybrid work: three days a week in our Sydney office and two at home.
- Four weeks of annual leave and an extra day off when you finish a big release.
- A $3,000 yearly budget for books, courses and conferences.
- A light on-call rota of one week in seven.

## About Bluebushworks

Bluebushworks makes planning and quoting software for solar and battery installers. It was founded in 2019 and has about 90 people, with its head office in Sydney. Its software is used on thousands of home installations each year.

## How we hire

- A call with the head of engineering.
- A design talk about a platform that you built, with two engineers.
- A pairing session on a Django and SQL problem.
- A decision within five working days.`,
  },
  {
    key: "demo-ml-engineer-mid", title: "Machine Learning Engineer, Solar Forecasting", company: "Bluebushworks",
    domain: "AI & Machine Learning", specialisation: "Machine learning engineering", level: "Mid", minYears: 2, maxYears: 5,
    type: "Full-time", workMode: "Hybrid", city: "Sydney", area: "Sydney NSW",
    salary: { min: 126000, max: 148000, unit: "year" }, occupation: { code: "261399", title: "Machine Learning Engineer" },
    skills: [
      { name: "Python", level: 4, must: true }, { name: "Machine learning", level: 4, must: true },
      { name: "Time series forecasting", level: 3, must: true }, { name: "scikit-learn", level: 4, must: true },
      { name: "Feature engineering", level: 3, must: true }, { name: "XGBoost", level: 3, must: false },
      { name: "Model evaluation", level: 3, must: false }, { name: "MLflow", level: 3, must: false }, { name: "Docker", level: 3, must: false },
      { name: "SQL", level: 3, must: false }, { name: "Git", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["AWS Certified Machine Learning Engineer - Associate"] }, awards: { preferred: ["data-science-competition"] },
    educationMin: "Bachelor's degree", postedDaysAgo: 17, closesInDays: 4,
    description: `## About the role

Bluebushworks tells installers how much power a home system will make on each day of the year, and its customers hold us to that number. The Forecasting team of four builds the models behind it, using weather, roof shape and the past output of thousands of live systems. We need a mid-level machine learning engineer to improve those forecasts and to move the training from notebooks to a scheduled pipeline. This is a Hybrid role in our Sydney office.

## What you will do

- Improve the solar output forecasts with Time series forecasting methods and better features.
- Train and compare models in scikit-learn and XGBoost, and keep the best ones.
- Build tests that show how each model behaves on cloudy weeks and on new roof types.
- Track runs in MLflow and package models in Docker for the serving team.
- Explain forecast errors to installers and to the customer support team.
- Query system data with SQL to find new signals.

## What you bring

- 2 to 5 years of applied machine learning, with Python and scikit-learn at an advanced level (4 of 5).
- Machine learning at an advanced level, with a focus on tabular and time series data.
- Time series forecasting and Feature engineering at a proficient level (3 of 5).
- Honest checking of results: you separate the training data from the test data with care.
- Clear writing and a calm voice when a number is wrong.

## Nice to have

- XGBoost, Model evaluation and MLflow in daily work.
- Docker, SQL and Git habits for shared code.
- A result in a data science competition.

## Tech stack

Python, scikit-learn, XGBoost, MLflow, Docker and SQL on a cloud data warehouse, with Git for all code.

## Certifications and awards

- Preferred certification: AWS Certified Machine Learning Engineer - Associate.
- Preferred award kind: Data science competition.

## What we offer

- $126,000 to $148,000 a year, plus 12% superannuation.
- Hybrid work: three days a week in our Sydney office and two at home.
- Four weeks of annual leave and a short break between Christmas and New Year.
- A learning budget of $2,500 a year.
- Access to live solar data from thousands of homes, with private details removed.

## About Bluebushworks

Bluebushworks makes planning and quoting software for solar and battery installers. It was founded in 2019 and has about 90 people, with its head office in Sydney. Its software is used on thousands of home installations each year.

## How we hire

- A 30-minute call with the forecasting lead.
- A small modelling task on sample data, about two hours.
- A talk with the team about your solution.
- An offer within five working days.`,
  },
  {
    key: "demo-data-engineer-contract-closed", title: "Contract Data Engineer, Billing Migration", company: "Bluebushworks",
    domain: "Data", specialisation: "Data engineering", level: "Mid", minYears: 3, maxYears: 8,
    type: "Contract", workMode: "Hybrid", city: "Sydney", area: "Sydney NSW",
    salary: { min: 760, max: 840, unit: "day" }, occupation: { code: "262111", title: "Data Engineer" },
    skills: [
      { name: "SQL", level: 4, must: true }, { name: "ETL and ELT pipelines", level: 4, must: true },
      { name: "Azure Data Factory", level: 4, must: true }, { name: "Python", level: 3, must: true },
      { name: "Data warehousing", level: 3, must: true }, { name: "Microsoft SQL Server", level: 3, must: false },
      { name: "Azure", level: 3, must: false }, { name: "Git", level: 3, must: false }, { name: "Data quality", level: 3, must: false },
      { name: "Power BI", level: 2, must: false },
    ],
    certifications: { required: [], preferred: ["Microsoft Certified: Azure Fundamentals"] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 40, closesInDays: -2,
    description: `## About the role

Bluebushworks is moving its billing and invoicing data from an old SQL Server system to a new cloud data warehouse, and it needs a contract data engineer for four months. The work covers 45 pipelines in Azure Data Factory, plus the checks that prove the new numbers match the old ones. As a mid-level contractor, you will join a billing data team of four who are tired of month-end surprises. This is a Hybrid contract in our Sydney office.

## What you will do

- Rebuild the billing and invoice pipelines in Azure Data Factory.
- Write SQL that returns the same totals as the old system, and prove it with checks.
- Load the data into the new data warehouse with clear logs and retries.
- Report the migration status each week to the billing team.
- Build a simple Power BI page that compares old and new totals.
- Hand over the pipelines with short guides.

## What you bring

- 3 to 8 years in data engineering, with SQL and ETL and ELT pipelines at an advanced level (4 of 5).
- Azure Data Factory at an advanced level, shown by a past migration.
- Python at a proficient level (3 of 5), and Data warehousing at the same level.
- Calm communication with billing teams, who care about every cent.
- Clear weekly status notes for the billing lead and the project owner.

## Nice to have

- Microsoft SQL Server and Azure depth.
- Git habits and Data quality checks that you built.
- Power BI basics.

## Tech stack

Azure Data Factory, Microsoft SQL Server as the old source, a cloud data warehouse as the target, Python for checks and Git for code.

## Certifications and awards

- Preferred certification: Microsoft Certified: Azure Fundamentals.

## What we offer

- A day rate of $760 to $840, paid through your company or an agency.
- A four-month contract in a Hybrid pattern: three days in our Sydney office.
- A clear scope and a friendly billing team.
- Quick onboarding, with access ready on day one.

## About Bluebushworks

Bluebushworks makes planning and quoting software for solar and battery installers. It was founded in 2019 and has about 90 people, with its head office in Sydney. Its software is used on thousands of home installations each year.

## How we hire

- A 30-minute call about the contract.
- A technical chat on Azure Data Factory and SQL.
- An answer within two working days.`,
  },
];
const TARGET_APPLICANTS = [10, 8, 5, 5];

function candidateUser(c, extra = {}) {
  const typed = c.skills.map(([name, level, years]) => ({ name, level, years }));
  const profile = {
    qualification: c.qualification, fieldOfStudy: c.fieldOfStudy, studyCountry: c.studyCountry, currentRole: c.currentRole, industry: c.industry,
    years: bandOf(c.yearsExperience), yearsExperience: c.yearsExperience, level: c.level, specialisation: c.specialisation,
    skills: typed.map((s) => s.name), certifications: c.certifications, awards: c.awards,
    targetRole: c.targetRole, targetIndustries: c.targetIndustries, locations: c.locations, workModes: c.workModes, workTypes: c.workTypes,
    evidence: c.evidence, translation: [],
  };
  // The levels and years that the talent gave stay on the cards of the skills
  profile.translation = translateKeeping({ ...profile, skills: typed }, c.evidence).skills.map((s) => ({ ...s, status: "accepted" }));
  return { id: newId(), role: "candidate", name: extra.name || `Sample candidate ${c.alias}`, email: extra.email || `${c.alias.toLowerCase().replace(/\s+/g, ".")}@sample.jinder.app`,
    company: null, alias: c.alias, pw: extra.pw || demoHash(newId()), seed: !extra.pw, profile, cv: extra.cv || null, onboarding: "done", createdAt: at(-30) };
}

function application(job, cand, status, history, extra = {}) {
  const snapshot = sharedProfileOf(cand);
  const sm = skillMatch(job.skills, namesFromList(snapshot.skills));
  return {
    id: newId(), jobId: job.id, candidateId: cand.id, recruiterId: job.ownerId, origin: "applied", status, note: extra.note || "",
    snapshot, match: { coverage: sm.coverage, skills: sm.items }, history, slots: extra.slots || [], chosenSlotId: extra.chosenSlotId || null,
    slotConfirmed: !!extra.slotConfirmed, identityShared: !!extra.identityShared, offer: extra.offer || null, feedback: extra.feedback || {},
    createdAt: history[0].at, updatedAt: history[history.length - 1].at,
  };
}
const h = (status, days, by, note = "") => ({ status, at: at(days), by, note });

export function seedDemo(db) {
  if (db.seeded) return;
  db.seeded = true;
  const sample = Object.fromEntries(SAMPLE_CANDIDATES.map((c) => [c.alias, candidateUser(c)]));
  db.users.push(...Object.values(sample));

  const recruiter = { id: newId(), role: "recruiter", name: "Alex Morgan", email: "recruiter@demo.jinder.app", company: "Bluebushworks", alias: null,
    pw: demoHash(DEMO_PASSWORD), profile: null, cv: null, onboarding: null, createdAt: at(-60) };
  const demoCand = candidateUser(DEMO_TALENT,
    { name: "Linh Nguyen", email: "candidate@demo.jinder.app", pw: demoHash(DEMO_PASSWORD), cv: { name: "linh-nguyen-cv.pdf", size: 182344, addedAt: at(-12) } });
  db.users.push(recruiter, demoCand);

  const jobs = Object.fromEntries(DEMO_JOBS.map((j, i) => [j.key, {
    id: `job-${j.key}`, ownerId: recruiter.id, title: j.title, company: recruiter.company, category: j.domain, specialisation: j.specialisation,
    location: j.city, area: j.area, type: j.type, salary: salaryText(j.salary), salaryUnit: j.salary.unit, description: j.description,
    skills: j.skills.map((s) => s.name), skillRequirements: j.skills.map((s) => ({ name: s.name, level: s.level, must: s.must })),
    level: j.level, minYears: j.minYears, maxYears: j.maxYears, workMode: j.workMode, educationMin: j.educationMin,
    certifications: j.certifications, awards: j.awards, targetApplicants: TARGET_APPLICANTS[i % 4],
    postedAt: at(-j.postedDaysAgo), closesAt: at(j.closesInDays), anzsco: j.occupation.code, occupation: j.occupation.title,
  }]));
  db.postedJobs.push(...Object.values(jobs));

  // The story: Teal Heron is in interview for the data engineer job. One profile waits in review. One waits for an answer.
  // The machine learning job closes soon and has an application. A finished contract job has an accepted offer.
  const de = jobs["demo-data-engineer-mid"], be = jobs["demo-backend-senior"], ml = jobs["demo-ml-engineer-mid"], closed = jobs["demo-data-engineer-contract-closed"];
  const slots = [1, 2, 3].map((d) => ({ id: newId().slice(0, 8), start: new Date(new Date(at(d + 2)).setHours(10 + d, 0, 0, 0)).toISOString() }));
  const apps = [
    application(de, sample["Jade Koala"], "review", [h("applied", -5, "candidate"), h("review", -3, "recruiter")]),
    application(de, demoCand, "interview", [h("applied", -5, "candidate"), h("review", -4, "recruiter"), h("interview", -2, "recruiter", "Offered 3 interview times")], { slots }),
    application(de, sample["Plum Heron"], "applied", [h("applied", -1, "candidate")], { note: "I build and run data pipelines every day and I like your stack." }),
    application(be, sample["Amber Finch"], "applied", [h("applied", -2, "candidate")]),
    application(be, sample["Cyan Puffin"], "review", [h("applied", -3, "candidate"), h("review", -2, "recruiter")]),
    application(ml, sample["Lime Kestrel"], "applied", [h("applied", -6, "candidate")]),
    application(closed, sample["Coral Fox"], "confirmed",
      [h("applied", -35, "candidate"), h("review", -33, "recruiter"), h("interview", -30, "recruiter", "Offered 2 interview times"), h("accepted", -25, "recruiter"), h("offer", -24, "recruiter"), h("confirmed", -22, "candidate", "Accepted the offer")],
      { slots: [{ id: "past1", start: at(-28) }], chosenSlotId: "past1", slotConfirmed: true, identityShared: true, offer: { text: "6-month contract at $820 per day, starting next month.", sentAt: at(-24) } }),
  ];
  db.applications.push(...apps);
  const [, interview, waiting, beApplied, , mlApplied] = apps;
  notify(db, recruiter.id, { type: "new_application", title: `New application for ${de.title}`, body: "Plum Heron applied.", link: `/review/${waiting.id}` });
  notify(db, recruiter.id, { type: "new_application", title: `New application for ${be.title}`, body: "Amber Finch applied.", link: `/review/${beApplied.id}` });
  notify(db, recruiter.id, { type: "new_application", title: `New application for ${ml.title}`, body: "Lime Kestrel applied.", link: `/review/${mlApplied.id}` });
  notify(db, demoCand.id, { type: "interview_slots", title: `Interview times for ${de.title}`, body: "Choose a time that works for you.", link: `/applications/${interview.id}` });

  // Some activity for the charts of Premium: counts of what talent did with the jobs (no person is named). The numbers are the same at each start.
  let seed = 7;
  const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  for (const job of Object.values(jobs)) {
    for (const [type, n] of [["job_appear", 24], ["job_watch", 9], ["job_save", 3]]) {
      for (let i = 0, count = n + Math.floor(rnd() * 5); i < count; i++) db.events.push({ type, targetType: "job", targetId: job.id, actorId: null, at: at(-rnd() * 20) });
    }
  }
}
