// MOCK BACKEND — sample CV parse results. The mock cannot read a real file, so it returns one of these.
// The UI shows a "Demo mode" banner in mock mode. All people here are made up (no real PII). All samples are ICT (3 domains only).
// File name rules (lower case): "fail" or "corrupt" → a parse failure; "ml", "machine", "research", "scientist" or "ai" → machine learning;
// "software", "developer", "backend", "java" or "swe" → software; "devops", "admin", "infra", "cloud" or "platform" → systems administrator;
// "analyst" or "business" (and not "data") → business analyst; any other name → the data analyst.
// A field that the CV does not show is not in `fields` and is not in `found` (the same as the real CV reader, plan R1 and F11).
// skills: the names as the person wrote them. skillLevels: the level (1 to 5) that the CV gives to a skill.
export const CV_SAMPLES = {
  data: {
    label: "Data analyst (BI Specialist), Vietnam",
    domain: "Data",
    fields: {
      qualification: ["Bachelor's degree"], fieldOfStudy: ["Information systems"], studyCountry: ["Vietnam"],
      currentRole: ["BI Specialist", "MIS Executive"], industry: ["Data"], years: "3–5 years", yearsExperience: 4.5, level: "Mid",
      skills: ["SQL", "Python", "Power BI", "Spreadsheets", "Data analysis", "Dashboards", "Informatica", "ER diagrams"],
      targetRole: ["Data Engineer"],
      certifications: [{ name: "Microsoft Certified: Power BI Data Analyst Associate", issuer: "Microsoft", year: 2024 }],
      awards: [{ name: "Smart City Hackathon Runner-up", kind: "hackathon", year: 2023 }],
    },
    skillLevels: [
      { name: "SQL", level: 4 }, { name: "Python", level: 3 }, { name: "Power BI", level: 4 }, { name: "Spreadsheets", level: 4 },
      { name: "Data analysis", level: 4 }, { name: "Dashboards", level: 3 }, { name: "Informatica", level: 2 }, { name: "ER diagrams", level: 3 },
    ],
    evidence: [
      "Built the weekly sales and stock dashboards in Power BI for 6 regional teams, replacing 14 manual spreadsheets.",
      "Wrote SQL queries and Python scripts to clean and join data from 5 source systems before each monthly report.",
      "Designed the report data model (ER diagrams) for the company data warehouse together with two engineers.",
      "Started to load data with Informatica jobs for the monthly reports.",
    ],
    missing: [],
  },
  software: {
    label: "Software developer (Java), India",
    domain: "Software Engineering",
    fields: {
      qualification: ["Bachelor's degree"], fieldOfStudy: ["Computer science"], studyCountry: ["India"],
      currentRole: ["Java Developer"], industry: ["Software Engineering"], years: "3–5 years", yearsExperience: 4.2, level: "Mid",
      skills: ["Java", "Spring Boot", "PostgreSQL", "REST APIs", "Docker", "Git", "Unit testing"],
      targetRole: ["Backend Engineer"],
      certifications: [{ name: "AWS Certified Developer - Associate", issuer: "Amazon Web Services", year: 2023 }],
      awards: [{ name: "Regional Hackathon Winner", kind: "hackathon", year: 2022 }],
    },
    skillLevels: [
      { name: "Java", level: 4 }, { name: "Spring Boot", level: 4 }, { name: "PostgreSQL", level: 3 }, { name: "REST APIs", level: 4 },
      { name: "Docker", level: 3 }, { name: "Git", level: 4 }, { name: "Unit testing", level: 3 },
    ],
    evidence: [
      "Built 12 REST endpoints in Java and Spring Boot for an order tracking service used by 3 internal teams.",
      "Designed the PostgreSQL schema and tuned 6 slow queries; the slowest page fell from 4 seconds to 600 ms.",
      "Wrote unit tests for the pricing rules with JUnit and ran them in a Jenkins pipeline on every commit.",
      "Packaged the service with Docker and shared the code in Git with pull request reviews.",
    ],
    missing: [],
  },
  ml: {
    label: "Machine learning researcher, Germany",
    domain: "AI & Machine Learning",
    // This CV does not state a desired role: the field stays empty and the screen shows a hint (plan F11).
    fields: {
      qualification: ["Master's degree"], fieldOfStudy: ["Mathematics"], studyCountry: ["Germany"],
      currentRole: ["Research Scientist"], industry: ["AI & Machine Learning"], years: "6–10 years", yearsExperience: 7, level: "Senior",
      skills: ["Python", "PyTorch", "Deep learning", "Statistics", "scikit-learn", "Model evaluation", "Feature engineering"],
      awards: [{ name: "Open Data Prediction Cup Gold Tier", kind: "data-science-competition", year: 2024 }],
    },
    skillLevels: [
      { name: "Python", level: 5 }, { name: "PyTorch", level: 4 }, { name: "Deep learning", level: 4 }, { name: "Statistics", level: 5 },
      { name: "scikit-learn", level: 4 }, { name: "Model evaluation", level: 4 }, { name: "Feature engineering", level: 3 },
    ],
    evidence: [
      "Trained and compared 6 deep learning models in PyTorch to predict equipment faults; the best model found 91% of the faults.",
      "Built the model evaluation set-up (cross-validation and error analysis) and ran the statistics tests for each paper.",
      "Used scikit-learn pipelines and feature engineering to cut the training time of the baseline model by 60%.",
      "Presented the results to 3 product teams and wrote the project documentation.",
    ],
    missing: [],
  },
  analyst: {
    label: "Business analyst, Philippines",
    domain: "Data",
    // This CV has no dates, so it shows no years of experience. It has no certification and no award.
    fields: {
      qualification: ["Bachelor's degree"], fieldOfStudy: ["Information technology"], studyCountry: ["Philippines"],
      currentRole: ["Business Analyst"], industry: ["Data"], years: "1–2 years", level: "Junior",
      skills: ["Requirements gathering", "SQL", "Power BI", "Dashboards", "Process mapping", "UAT", "Jira"],
      targetRole: ["Data Analyst"],
    },
    skillLevels: [
      { name: "Requirements gathering", level: 3 }, { name: "SQL", level: 3 }, { name: "Power BI", level: 3 }, { name: "Dashboards", level: 2 },
      { name: "Process mapping", level: 3 }, { name: "UAT", level: 3 }, { name: "Jira", level: 3 },
    ],
    evidence: [
      "Led requirements gathering workshops with 4 business teams and wrote 60 user stories for a customer portal.",
      "Wrote SQL queries and Power BI dashboards that showed the weekly ticket numbers to 3 managers.",
      "Mapped 9 business processes and ran UAT with 12 testers before each release.",
      "Tracked the backlog in Jira with a 2-week sprint plan.",
    ],
    missing: ["years"],
  },
  devops: {
    label: "Systems administrator, Brazil",
    domain: "Software Engineering",
    fields: {
      qualification: ["Bachelor's degree"], fieldOfStudy: ["Information technology"], studyCountry: ["Brazil"],
      currentRole: ["Systems Administrator"], industry: ["Software Engineering"], years: "6–10 years", yearsExperience: 8, level: "Senior",
      skills: ["Linux", "Bash scripting", "Ansible", "Docker", "Networking fundamentals", "Monitoring", "AWS"],
      targetRole: ["DevOps Engineer"],
      certifications: [{ name: "AWS Certified Solutions Architect - Associate", issuer: "Amazon Web Services", year: 2022 }],
    },
    skillLevels: [
      { name: "Linux", level: 5 }, { name: "Bash scripting", level: 4 }, { name: "Ansible", level: 3 }, { name: "Docker", level: 3 },
      { name: "Networking fundamentals", level: 4 }, { name: "Monitoring", level: 3 }, { name: "AWS", level: 3 },
    ],
    evidence: [
      "Ran 60 Linux servers for 3 teams and wrote Bash scripts that cut the patch time from 2 days to 3 hours.",
      "Moved the server set-up to Ansible playbooks, so that a new server took 20 minutes instead of 1 day.",
      "Set up monitoring and alerts that cut the number of night calls by half.",
      "Moved two internal tools to Docker containers on AWS.",
    ],
    missing: [],
  },
};

export function sampleFor(fileName) {
  const n = String(fileName || "").toLowerCase();
  if (/fail|corrupt/.test(n)) return null;
  if (/machine|(^|[^a-z])ml([^a-z]|$)|research|scientist|(^|[^a-z])ai([^a-z]|$)/.test(n)) return CV_SAMPLES.ml;
  if (/software|developer|backend|java|swe/.test(n)) return CV_SAMPLES.software;
  if (/devops|admin|infra|cloud|platform/.test(n)) return CV_SAMPLES.devops;
  if (/data/.test(n)) return CV_SAMPLES.data;
  if (/analyst|business/.test(n)) return CV_SAMPLES.analyst;
  return CV_SAMPLES.data;
}

// The answer of GET /cv/parse/:id when the read is done. It has the shape of the real answer:
// fields (only what the CV shows), detected, missing, evidence, domain, skills [{ name, level }] and found (the V2 fields that the CV showed).
export function parseResultOf(sample) {
  const detected = Object.keys(sample.fields).filter((k) => !sample.missing.includes(k));
  const fields = Object.fromEntries(detected.map((k) => [k, sample.fields[k]]));
  const filled = (k) => k in fields && !(Array.isArray(fields[k]) && !fields[k].length);
  return {
    fields, detected, missing: sample.missing, evidence: sample.evidence, sampleLabel: sample.label, domain: sample.domain, skills: sample.skillLevels,
    found: { currentRole: filled("currentRole"), targetRole: filled("targetRole"), level: filled("level"), yearsExperience: filled("yearsExperience"),
      certifications: filled("certifications"), awards: filled("awards") },
  };
}
