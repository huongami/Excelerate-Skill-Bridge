// Reference lists for forms (dropdowns, chips). Frontend-owned, static.
// The lists of names come from ict_taxonomy.json version 2 (jinder_backend_engine/data/reference).
// Use the same spelling as the taxonomy. Do not add a name that is not in the taxonomy.
// Users can also type their own value where the form allows it (not for YEARS and LEVELS).
// Do not add lists for sensitive data (nationality, visa status, age, gender). See AI_Rule.md Rule 5.

// Levels, skill levels and work modes live in levels.js (one place). They are exported here too.
export { LEVELS, SKILL_LEVELS, WORK_MODES } from "./levels.js";

// from ict_taxonomy.json version 2: domains and their specialisations
export const DOMAINS = ["Software Engineering", "AI & Machine Learning", "Data"];
export const SPECIALISATIONS = {
  "Software Engineering": [
    "Backend", "Frontend", "Full-stack", "Mobile", "Platform and DevOps", "Quality engineering",
    "Security engineering", "Software architecture",
  ],
  "AI & Machine Learning": [
    "Machine learning engineering", "Generative AI and LLM", "Computer vision", "Natural language processing",
    "MLOps", "Applied science and research",
  ],
  "Data": [
    "Data engineering", "Data analytics", "Analytics engineering", "Business intelligence", "Data science",
    "Business analysis",
  ],
};
// Old names. The UI word is "Domain" now (plan F6). The profile keys `industry` and `targetIndustries` do not change.
export const INDUSTRIES = DOMAINS;
export const JOB_CATEGORIES = DOMAINS;

// from ict_taxonomy.json version 2: cities. "Remote" is the last item.
export const CITIES = ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Canberra", "Remote"];
export const LOCATIONS = CITIES;
export const WORK_TYPES = ["Full-time", "Part-time", "Contract", "Graduate / Internship"];

// from ict_taxonomy.json version 2: role titles (a title has no level word; the level is separate)
export const ROLES = [
  "Software Engineer", "Software Developer", "Backend Engineer", "Frontend Engineer", "Full-stack Engineer",
  "Web Developer", "Mobile Developer", "Android Developer", "iOS Developer", "Java Developer", ".NET Developer",
  "Python Developer", "Platform Engineer", "DevOps Engineer", "Site Reliability Engineer", "Cloud Engineer",
  "Cloud Architect", "Solutions Architect", "Software Architect", "QA Engineer", "Test Automation Engineer",
  "Software Tester", "Security Engineer", "Application Security Engineer", "Machine Learning Engineer",
  "Computer Vision Engineer", "NLP Engineer", "Deep Learning Engineer", "AI Engineer", "Generative AI Engineer",
  "LLM Engineer", "MLOps Engineer", "ML Platform Engineer", "Applied Scientist", "AI Research Scientist",
  "AI Research Engineer", "Data Engineer", "Analytics Engineer", "Big Data Engineer", "Data Platform Engineer",
  "ETL Developer", "Data Warehouse Engineer", "Database Administrator", "Data Architect", "Data Analyst",
  "Business Intelligence Analyst", "BI Developer", "Reporting Analyst", "Product Analyst", "Data Scientist",
  "Statistician", "Business Analyst", "Business Systems Analyst",
];

// from ict_taxonomy.json version 2: fields of study
export const FIELDS_OF_STUDY = [
  "Computer science", "Software engineering", "Information technology", "Information systems", "Data science",
  "Artificial intelligence", "Statistics", "Mathematics", "Electrical and computer engineering", "Cyber security",
  "Physics", "Economics",
];

// from ict_taxonomy.json version 2: certifications. `tier` is foundation, associate, professional or specialty.
export const CERTIFICATIONS = [
  { name: "AWS Certified Cloud Practitioner", issuer: "Amazon Web Services", domains: ["Software Engineering", "AI & Machine Learning", "Data"], tier: "foundation" },
  { name: "AWS Certified AI Practitioner", issuer: "Amazon Web Services", domains: ["AI & Machine Learning"], tier: "foundation" },
  { name: "AWS Certified Solutions Architect - Associate", issuer: "Amazon Web Services", domains: ["Software Engineering"], tier: "associate" },
  { name: "AWS Certified Developer - Associate", issuer: "Amazon Web Services", domains: ["Software Engineering"], tier: "associate" },
  { name: "AWS Certified Data Engineer - Associate", issuer: "Amazon Web Services", domains: ["Data"], tier: "associate" },
  { name: "AWS Certified Machine Learning Engineer - Associate", issuer: "Amazon Web Services", domains: ["AI & Machine Learning"], tier: "associate" },
  { name: "AWS Certified DevOps Engineer - Professional", issuer: "Amazon Web Services", domains: ["Software Engineering"], tier: "professional" },
  { name: "AWS Certified Security - Specialty", issuer: "Amazon Web Services", domains: ["Software Engineering"], tier: "specialty" },
  { name: "Microsoft Certified: Azure Fundamentals", issuer: "Microsoft", domains: ["Software Engineering", "AI & Machine Learning", "Data"], tier: "foundation" },
  { name: "Microsoft Certified: Azure Developer Associate", issuer: "Microsoft", domains: ["Software Engineering"], tier: "associate" },
  { name: "Microsoft Certified: Azure AI Engineer Associate", issuer: "Microsoft", domains: ["AI & Machine Learning"], tier: "associate" },
  { name: "Microsoft Certified: Azure Data Scientist Associate", issuer: "Microsoft", domains: ["AI & Machine Learning", "Data"], tier: "associate" },
  { name: "Microsoft Certified: Fabric Data Engineer Associate", issuer: "Microsoft", domains: ["Data"], tier: "associate" },
  { name: "Microsoft Certified: Power BI Data Analyst Associate", issuer: "Microsoft", domains: ["Data"], tier: "associate" },
  { name: "Microsoft Certified: DevOps Engineer Expert", issuer: "Microsoft", domains: ["Software Engineering"], tier: "professional" },
  { name: "Google Cloud Associate Cloud Engineer", issuer: "Google Cloud", domains: ["Software Engineering"], tier: "associate" },
  { name: "Google Cloud Professional Data Engineer", issuer: "Google Cloud", domains: ["Data"], tier: "professional" },
  { name: "Google Cloud Professional Machine Learning Engineer", issuer: "Google Cloud", domains: ["AI & Machine Learning"], tier: "professional" },
  { name: "Certified Kubernetes Application Developer", issuer: "Cloud Native Computing Foundation", domains: ["Software Engineering"], tier: "associate" },
  { name: "Certified Kubernetes Administrator", issuer: "Cloud Native Computing Foundation", domains: ["Software Engineering"], tier: "professional" },
  { name: "HashiCorp Certified: Terraform Associate", issuer: "HashiCorp", domains: ["Software Engineering"], tier: "associate" },
  { name: "Databricks Certified Data Engineer Associate", issuer: "Databricks", domains: ["Data"], tier: "associate" },
  { name: "Databricks Certified Data Engineer Professional", issuer: "Databricks", domains: ["Data"], tier: "professional" },
  { name: "Databricks Certified Generative AI Engineer Associate", issuer: "Databricks", domains: ["AI & Machine Learning"], tier: "associate" },
  { name: "SnowPro Core Certification", issuer: "Snowflake", domains: ["Data"], tier: "associate" },
  { name: "dbt Analytics Engineering Certification", issuer: "dbt Labs", domains: ["Data"], tier: "associate" },
  { name: "Confluent Certified Developer for Apache Kafka", issuer: "Confluent", domains: ["Software Engineering", "Data"], tier: "associate" },
  { name: "Tableau Certified Data Analyst", issuer: "Salesforce", domains: ["Data"], tier: "associate" },
  { name: "Machine Learning Specialization", issuer: "DeepLearning.AI and Stanford Online", domains: ["AI & Machine Learning"], tier: "associate" },
  { name: "NVIDIA-Certified Associate: Generative AI LLMs", issuer: "NVIDIA", domains: ["AI & Machine Learning"], tier: "associate" },
  { name: "Professional Scrum Master I", issuer: "Scrum.org", domains: ["Software Engineering", "AI & Machine Learning", "Data"], tier: "associate" },
  { name: "ISTQB Certified Tester Foundation Level", issuer: "ISTQB", domains: ["Software Engineering"], tier: "foundation" },
  { name: "ISTQB Certified Tester Test Automation Engineer", issuer: "ISTQB", domains: ["Software Engineering"], tier: "professional" },
  { name: "CompTIA Security+", issuer: "CompTIA", domains: ["Software Engineering"], tier: "associate" },
  { name: "Certified Ethical Hacker", issuer: "EC-Council", domains: ["Software Engineering"], tier: "associate" },
  { name: "Offensive Security Certified Professional", issuer: "OffSec", domains: ["Software Engineering"], tier: "professional" },
  { name: "Oracle Certified Professional: Java SE 17 Developer", issuer: "Oracle", domains: ["Software Engineering"], tier: "professional" },
  { name: "PCAP: Certified Associate in Python Programming", issuer: "Python Institute", domains: ["Software Engineering", "AI & Machine Learning", "Data"], tier: "associate" },
];

// from ict_taxonomy.json version 2: award kinds. `kind` is the value that the API stores. `label` is the text for people.
export const AWARD_KINDS = [
  { kind: "competitive-programming", label: "Competitive programming" },
  { kind: "hackathon", label: "Hackathon" },
  { kind: "data-science-competition", label: "Data science competition" },
  { kind: "open-source", label: "Open source contribution" },
  { kind: "conference-talk", label: "Conference talk or paper" },
  { kind: "employer-recognition", label: "Employer recognition" },
  { kind: "scholarship", label: "Scholarship" },
  { kind: "academic-excellence", label: "Academic excellence" },
  { kind: "patent", label: "Patent" },
  { kind: "community-leadership", label: "Community leadership" },
  { kind: "security-competition", label: "Security competition or bug bounty" },
  { kind: "innovation-award", label: "Innovation award" },
];

// Skill suggestions for each domain (quick-add chips). From the core skills of the occupations in the taxonomy.
export const SKILL_SUGGESTIONS = {
  "Software Engineering": ["Git", "API design", "Debugging and troubleshooting", "Docker", "Unit and integration testing", "SQL", "CI/CD", "JavaScript", "System design"],
  "AI & Machine Learning": ["Python", "Machine learning", "Deep learning", "PyTorch", "Model evaluation", "Statistics", "scikit-learn", "Feature engineering", "Generative AI"],
  "Data": ["SQL", "Python", "Data visualisation", "Statistics", "Data modelling", "Data analysis", "Microsoft Excel", "Power BI", "ETL and ELT pipelines"],
};

// from ict_taxonomy.json version 2: skill names (the one spelling). Sorted for the skills dropdown.
export const SKILL_NAMES = [
  ".NET", "AI agents", "API design", "AWS", "AWS CloudFormation", "AWS Lambda", "Agile delivery", "Amazon DynamoDB",
  "Amazon Redshift", "Amazon S3", "Amazon SageMaker", "Android development", "Angular", "Ansible", "Apache Airflow",
  "Apache Cassandra", "Apache Flink", "Apache Hadoop", "Apache Kafka", "Apache Spark", "Application security",
  "Authentication and authorisation", "Azure", "Azure Data Factory", "Azure DevOps", "Azure Functions",
  "Azure Machine Learning", "C", "C#", "C++", "CI/CD", "Cloud security", "Code review", "Communication",
  "Computer vision", "Continuous learning", "Cypress", "Data analysis", "Data governance", "Data lakehouse",
  "Data modelling", "Data privacy and compliance", "Data quality", "Data storytelling",
  "Data structures and algorithms", "Data visualisation", "Data warehousing", "Database design and tuning",
  "Databricks", "Debugging and troubleshooting", "Deep learning", "Distributed training and GPU computing", "Django",
  "Docker", "ETL and ELT pipelines", "Elasticsearch", "Estimation and planning", "Experimentation and A/B testing",
  "Facilitation", "FastAPI", "Feature engineering", "Flask", "Flutter", "Generative AI", "Git", "GitHub Actions",
  "GitLab CI/CD", "Go", "Google BigQuery", "Google Cloud Platform", "Grafana", "GraphQL", "HTML and CSS",
  "Hugging Face Transformers", "Incident response", "Infrastructure as code", "JUnit", "Java", "JavaScript",
  "Jenkins", "Jest", "Kotlin", "Kubernetes", "LLM APIs", "LLM fine-tuning", "LangChain", "Laravel", "Linux", "Looker",
  "MATLAB", "MLOps", "MLflow", "Machine learning", "Manual testing", "Mentoring", "Microservices architecture",
  "Microsoft Excel", "Microsoft Fabric", "Microsoft SQL Server", "Model evaluation", "MongoDB", "MySQL",
  "Natural language processing", "NestJS", "Networking fundamentals", "Next.js", "Node.js", "NumPy",
  "Object-oriented design", "Observability", "Oracle Database", "PHP", "Pandas", "Penetration testing",
  "Performance testing", "Playwright", "PostgreSQL", "Power BI", "PowerShell", "Problem solving", "Product thinking",
  "Project management", "Prometheus", "Prompt engineering", "PyTorch", "Python", "R", "React", "React Native",
  "Recommender systems", "Redis", "Reinforcement learning", "Requirements analysis", "Responsible AI",
  "Retrieval-augmented generation", "Ruby", "Ruby on Rails", "Rust", "SQL", "Scala", "Selenium", "Shell scripting",
  "Site reliability engineering", "Snowflake", "Spring Boot", "Stakeholder management", "Statistics", "Swift",
  "System design", "Tableau", "Tailwind CSS", "Team leadership", "Teamwork", "Technical documentation",
  "Technical leadership", "TensorFlow", "Terraform", "Test automation", "Threat modelling", "Time series forecasting",
  "TypeScript", "Unit and integration testing", "Vector databases", "Vertex AI", "Vue.js", "Web accessibility",
  "XGBoost", "dbt", "gRPC", "iOS development", "pytest", "scikit-learn",
];

// All skills for the skills dropdown (the taxonomy skills, sorted)
export const SKILLS = [...new Set([...SKILL_NAMES, ...Object.values(SKILL_SUGGESTIONS).flat()])]
  .sort((a, b) => a.localeCompare(b));

export const QUALIFICATIONS = [
  "High school", "Certificate III or IV", "Diploma", "Advanced diploma", "Associate degree",
  "Bachelor's degree", "Bachelor's degree (Honours)", "Graduate certificate", "Graduate diploma",
  "Master's degree", "MBA", "Doctorate (PhD)",
];

// Countries where qualifications are often earned. Used only for AQF equivalence, never for ranking.
export const COUNTRIES = [
  "Australia", "Bangladesh", "Brazil", "Canada", "Chile", "China", "Colombia", "Egypt", "France", "Germany",
  "Ghana", "Hong Kong", "India", "Indonesia", "Iran", "Ireland", "Italy", "Japan", "Kenya", "Malaysia",
  "Mexico", "Nepal", "Netherlands", "New Zealand", "Nigeria", "Pakistan", "Peru", "Philippines", "Singapore",
  "South Africa", "South Korea", "Spain", "Sri Lanka", "Taiwan", "Thailand", "Turkey", "United Arab Emirates",
  "United Kingdom", "United States", "Vietnam", "Zimbabwe",
];

export const YEARS = ["Less than 1 year", "1–2 years", "3–5 years", "6–10 years", "More than 10 years"];
