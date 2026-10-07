"""The word lists of the CV reader and the job description reader.

The lists come from the taxonomy file (jinder_backend_engine/data/reference/ict_taxonomy.json): the level words, the roles, the skills with
their aliases, the certifications and the award kinds. If the file is missing or broken, a small list that is built in is used, so that the
readers still work. The built-in lists use the same names as the taxonomy.

Where the file is searched:  1. the environment variable JINDER_TAXONOMY_PATH  2. config.TAXONOMY_PATH (if the platform sets it)
3. config.DATA_DIR / "reference" / "ict_taxonomy.json".
"""
import json
import os
import re
import threading
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Pattern, Set, Tuple

from . import config

LEVELS = ["Intern", "Junior", "Mid", "Senior", "Lead", "Principal"]
SKILL_LEVEL_LABELS = ["Beginner", "Working", "Proficient", "Advanced", "Expert"]
DOMAINS = ["Software Engineering", "AI & Machine Learning", "Data"]


def default_path() -> Path:
    explicit = os.environ.get("JINDER_TAXONOMY_PATH") or getattr(config, "TAXONOMY_PATH", None)
    return Path(explicit) if explicit else Path(config.DATA_DIR) / "reference" / "ict_taxonomy.json"


# =====================================================================
# The built-in lists (a copy of the most used names of the taxonomy, version 2)
# =====================================================================
_BUILTIN_LEVEL_WORDS = {
    "Intern": ["intern", "internship", "trainee", "cadet", "apprentice", "student", "work experience"],
    "Junior": ["junior", "jr", "jnr", "graduate", "grad", "entry level", "entry-level", "associate", "early career", "level 1"],
    "Mid": ["mid", "mid-level", "mid level", "intermediate", "level 2", "ii"],
    "Senior": ["senior", "sr", "snr", "level 3", "iii"],
    "Lead": ["lead", "team lead", "tech lead", "technical lead", "staff", "engineering manager", "level 4", "iv"],
    "Principal": ["principal", "distinguished", "fellow", "head of", "director", "chief", "vice president", "vp", "level 5"],
}

_BUILTIN_ROLES = [
    "Software Engineer", "Software Developer", "Backend Engineer", "Frontend Engineer", "Full-stack Engineer", "Web Developer", "Mobile Developer",
    "Android Developer", "iOS Developer", "Java Developer", ".NET Developer", "Python Developer", "Platform Engineer", "DevOps Engineer",
    "Site Reliability Engineer", "Cloud Engineer", "Cloud Architect", "Solutions Architect", "Software Architect", "QA Engineer",
    "Test Automation Engineer", "Software Tester", "Security Engineer", "Application Security Engineer", "Machine Learning Engineer",
    "Computer Vision Engineer", "NLP Engineer", "Deep Learning Engineer", "AI Engineer", "Generative AI Engineer", "LLM Engineer", "MLOps Engineer",
    "ML Platform Engineer", "Applied Scientist", "AI Research Scientist", "AI Research Engineer", "Data Engineer", "Analytics Engineer",
    "Big Data Engineer", "Data Platform Engineer", "ETL Developer", "Data Warehouse Engineer", "Database Administrator", "Data Architect",
    "Data Analyst", "Business Intelligence Analyst", "BI Developer", "Reporting Analyst", "Product Analyst", "Data Scientist", "Statistician",
    "Business Analyst", "Business Systems Analyst",
]
# Roles that are not in the pick-list of the taxonomy, but are common titles. They make the reader find more titles. They are not new pick-list values.
_EXTRA_ROLES = [
    "Frontend Developer", "Backend Developer", "Full Stack Developer", "Embedded Engineer", "Embedded Software Engineer", "Firmware Engineer",
    "Game Developer", "Systems Engineer", "Network Engineer", "Systems Administrator", "IT Support Engineer", "Solutions Engineer",
    "Engineering Manager", "Data Science Manager", "Research Scientist", "Research Engineer", "Quantitative Analyst", "Database Developer",
    "SQL Developer", "Prompt Engineer", "Applied Machine Learning Engineer", "Data Visualisation Developer", "Application Developer",
]

# A title ends with one of these words
_ROLE_NOUNS = {
    "engineer", "developer", "programmer", "analyst", "scientist", "architect", "administrator", "researcher", "consultant", "specialist",
    "designer", "tester", "technician", "manager", "lead", "director", "officer", "coordinator", "owner", "strategist", "statistician",
    "technologist", "advocate", "evangelist", "founder", "cofounder", "co-founder", "intern", "trainee", "apprentice", "assistant", "executive",
    "supervisor", "advisor", "adviser", "controller", "planner", "producer", "writer", "editor", "lecturer", "tutor", "teacher", "nurse",
    "accountant", "auditor", "clerk", "buyer", "chef", "sre", "dba", "cto", "cio", "cdo", "ciso", "qa", "swe", "sdet", "sde",
    "devops", "mlops", "dev", "representative", "agent", "operator", "mathematician", "linguist", "curator",
    "steward",
}

# name | issuer | aliases (lower case, separated by "|")
_BUILTIN_CERTS = """
AWS Certified Cloud Practitioner|Amazon Web Services|aws cloud practitioner|aws ccp|clf-c02
AWS Certified AI Practitioner|Amazon Web Services|aws ai practitioner|aif-c01
AWS Certified Solutions Architect - Associate|Amazon Web Services|aws solutions architect associate|aws saa|saa-c03
AWS Certified Developer - Associate|Amazon Web Services|aws developer associate|dva-c02
AWS Certified Data Engineer - Associate|Amazon Web Services|aws data engineer associate|dea-c01
AWS Certified Machine Learning Engineer - Associate|Amazon Web Services|aws machine learning engineer associate|mla-c01
AWS Certified DevOps Engineer - Professional|Amazon Web Services|aws devops engineer professional|dop-c02
AWS Certified Security - Specialty|Amazon Web Services|aws security specialty|scs-c02
Microsoft Certified: Azure Fundamentals|Microsoft|az-900|azure fundamentals
Microsoft Certified: Azure Developer Associate|Microsoft|az-204|azure developer associate
Microsoft Certified: Azure AI Engineer Associate|Microsoft|ai-102|azure ai engineer associate
Microsoft Certified: Azure Data Scientist Associate|Microsoft|dp-100|azure data scientist associate
Microsoft Certified: Fabric Data Engineer Associate|Microsoft|dp-700|fabric data engineer associate
Microsoft Certified: Power BI Data Analyst Associate|Microsoft|pl-300|power bi data analyst associate
Microsoft Certified: DevOps Engineer Expert|Microsoft|az-400|azure devops engineer expert
Google Cloud Associate Cloud Engineer|Google Cloud|gcp associate cloud engineer|google associate cloud engineer
Google Cloud Professional Data Engineer|Google Cloud|gcp professional data engineer|google professional data engineer
Google Cloud Professional Machine Learning Engineer|Google Cloud|gcp professional machine learning engineer|google professional ml engineer
Certified Kubernetes Application Developer|Cloud Native Computing Foundation|ckad
Certified Kubernetes Administrator|Cloud Native Computing Foundation|cka
HashiCorp Certified: Terraform Associate|HashiCorp|terraform associate|hashicorp terraform associate
Databricks Certified Data Engineer Associate|Databricks|databricks data engineer associate
Databricks Certified Data Engineer Professional|Databricks|databricks data engineer professional
Databricks Certified Generative AI Engineer Associate|Databricks|databricks generative ai engineer associate
SnowPro Core Certification|Snowflake|snowpro core|snowflake snowpro core
dbt Analytics Engineering Certification|dbt Labs|dbt analytics engineering|dbt certification
Confluent Certified Developer for Apache Kafka|Confluent|ccdak|confluent kafka developer
Tableau Certified Data Analyst|Salesforce|tableau data analyst certification
Machine Learning Specialization|DeepLearning.AI and Stanford Online|andrew ng machine learning specialization|deeplearning.ai machine learning specialization
NVIDIA-Certified Associate: Generative AI LLMs|NVIDIA|nvidia generative ai llms associate|nca-genl
Professional Scrum Master I|Scrum.org|psm i|psm 1|psm1
ISTQB Certified Tester Foundation Level|ISTQB|istqb foundation|istqb ctfl|ctfl
ISTQB Certified Tester Test Automation Engineer|ISTQB|istqb test automation engineer|istqb ct-tae|ct-tae
CompTIA Security+|CompTIA|security+|comptia security plus|sy0-701
Certified Ethical Hacker|EC-Council|ceh|ec-council ceh
Offensive Security Certified Professional|OffSec|oscp|offsec oscp
Oracle Certified Professional: Java SE 17 Developer|Oracle|ocp java se 17|oracle java se 17 developer|1z0-829
PCAP: Certified Associate in Python Programming|Python Institute|pcap|python institute pcap
"""

# Other issuers. They are only used to fill the "issuer" of a certification that is not in the list.
_OTHER_ISSUERS = [
    "Amazon Web Services", "AWS", "Microsoft", "Google Cloud", "Google", "Databricks", "Snowflake", "Cloudera", "Oracle", "Cisco", "CompTIA", "ISACA",
    "ISC2", "(ISC)²", "PMI", "Scrum Alliance", "Scrum.org", "Linux Foundation", "Cloud Native Computing Foundation", "HashiCorp", "Red Hat", "Coursera",
    "Udacity", "Udemy", "edX", "DeepLearning.AI", "fast.ai", "NVIDIA", "IBM", "SAS", "Tableau", "Salesforce", "Meta", "Kaggle", "Stanford Online", "MIT",
    "LinkedIn Learning", "Pluralsight", "Confluent", "dbt Labs", "ISTQB", "EC-Council", "OffSec", "Python Institute", "Atlassian", "VMware",
]

# kind | label | keywords (regular expressions, lower case, separated by "|"). The order matters: the first kind that matches wins.
_BUILTIN_AWARD_KINDS = """
patent|Patent|patent
security-competition|Security competition or bug bounty|capture the flag|\\bctf\\b|bug bounty|hall of fame|cyber challenge|cyber security challenge
competitive-programming|Competitive programming|\\bicpc\\b|programming contest|coding contest|coding competition|coding challenge|programming competition|competitive programming|algorithm cup|codeforces|topcoder|code jam|olympiad in informatics|informatics olympiad|programming olympiad|\\bioi\\b|hackerrank
data-science-competition|Data science competition|kaggle|data science competition|forecasting challenge|prediction cup|analytics challenge|datathon|machine learning competition|ml competition|data challenge|drivendata|analytics competition|datafest|data fest|data science challenge|prediction challenge|ml challenge|data quest|data cup|data olympiad|data hunt
hackathon|Hackathon|hackathon|hack day|hackday|hack weekend|hack week|hackfest|hack night|\\bhack(?!er|ing)[a-z]*|\\b\\w*hack\\b|codeathon|game jam|makeathon
open-source|Open source contribution|open[- ]source|maintainer|core contributor|top contributor|\\bcontributor\\b|committer
scholarship|Scholarship|scholarship|fellowship|bursary
academic-excellence|Academic excellence|dean'?s (?:honou?r )?(?:list|roll)|honou?r roll|vice[- ]chancellor'?s list|university medal|first[- ]class honou?rs|valedictorian|top graduate|top of (the |my )?class|academic excellence|academic award|gold medal|prize for (the )?best student|best (?:final year project|graduating student|graduate|thesis|dissertation)|top student
conference-talk|Conference talk or paper|speaker|invited talk|keynote|best paper|paper award|meetup talk|presented at|\\btalk\\b|devconf|\\bconf\\b|\\bpresenter\\b
employer-recognition|Employer recognition|employee of the|employee spotlight|\\bspotlight\\b|top performer|high achiever|engineer of the|excellence award|excellence in|customer impact|spot award|star performer|ceo award|team award|peer award|recognition award|outstanding performance|performance award|internal award|delivery award|values award|values in action|above and beyond|innovator of the|chair(?:man|person|woman)?.?s (?:award|prize|medal|choice|recognition)|rising star|commendation|special act|meritorious|service award|long service|staff recognition
community-leadership|Community leadership|organi[sz]er|mentor of the year|\\bchair\\b|president of|volunteer of the year|community lead|ambassador|volunteer award|community (?:volunteer )?award|community service
innovation-award|Innovation award|innovation|best prototype|best idea|\\bpitch\\b|demo day|startup
employer-recognition|~Employer recognition|\\b\\w+ of the (?:year|quarter|month|half)\\b
conference-talk|~Conference talk or paper|\\bconference\\b|\\bworkshop\\b|\\bsummit\\b|\\bmeetup\\b
data-science-competition|~Data science competition|\\bchallenge\\b|\\bcompetition\\b|\\bcontest\\b
"""

# Titles of IT that no specialisation word describes. They are of the domain Software Engineering ("Salesforce Developer", "Systems Administrator")
_GENERAL_IT_TITLE = re.compile(r"\b(?:developer|programmer|software|devops|sre|sysadmin|(?:system|systems|database|network) administrator|it support|help ?desk|"
                               r"service desk|firmware|embedded|(?:solutions|cloud|software|enterprise|technical) architect|network engineer|it manager|head of it)\b", re.I)

# The more special a specialisation, the earlier it stands: when two have the same score, the first one wins.
_SPECIALISATION_KEYWORDS = {
    "Analytics engineering": r"analytics engineer|\bdbt\b",
    "MLOps": r"mlops|ml ops|model (deployment|serving|monitoring)|ml pipelines?|feature store|kubeflow|mlflow",
    "Computer vision": r"computer vision|opencv|object detection|image (recognition|classification|processing)",
    "Natural language processing": r"\bnlp\b|natural language|text mining|language model",
    "Generative AI and LLM": r"\bllm|generative ai|genai|\brag\b|prompt|langchain|ai agents?|large language",
    "Applied science and research": r"research scientist|applied scientist|\bphd\b|publications?|\bresearch\b",
    "Machine learning engineering": r"machine learning engineer|\bml engineer|model training|deep learning|pytorch|tensorflow|scikit",
    "Data science": r"data scientist|data science|statistic|forecast|predictive",
    "Data engineering": r"data engineer|\betl\b|\belt\b|data pipelines?|\bspark\b|airflow|kafka|data platform|data warehouse|lakehouse|big data|databricks",
    "Business intelligence": r"business intelligence|\bbi (developer|analyst)|power bi|tableau|looker",
    "Business analysis": r"business analyst|requirements|business systems",
    "Data analytics": r"data analyst|data analytics|business analytics|product analytics|reporting analyst|product analyst|dashboards?|\bsql\b",
    "Full-stack": r"full[- ]?stack",
    "Mobile": r"\bmobile\b|android|\bios\b|flutter|react native|swift|kotlin",
    "Platform and DevOps": r"devops|site reliability|\bsre\b|platform engineer|kubernetes|terraform|ci/cd|cloud engineer|infrastructure|observability",
    "Quality engineering": r"\bqa\b|quality assurance|\btester\b|test automation|sdet|quality engineer|\btesting\b",
    "Security engineering": r"security|appsec|pentest|penetration|threat",
    "Software architecture": r"architect|system design|solutions? architect",
    "Frontend": r"front[- ]?end|\breact\b|angular|\bvue\b|\bcss\b|\bui\b|web developer|typescript|javascript",
    "Backend": r"back[- ]?end|\bapis?\b|microservice|server[- ]side|\bjava\b|spring|\.net|golang|\bgo\b|node\.?js|django|flask|fastapi|rails",
}

# Skills that are not tools: the readers do not look for them in the whole text of a CV
_NON_HARD = {
    "Responsible AI", "Agile delivery", "Unit and integration testing", "Manual testing", "Code review", "Technical documentation",
    "Debugging and troubleshooting", "Threat modelling", "Incident response", "Data privacy and compliance", "Communication",
    "Stakeholder management", "Mentoring", "Team leadership", "Technical leadership", "Problem solving", "Teamwork", "Project management",
    "Product thinking", "Data storytelling", "Facilitation", "Continuous learning", "Estimation and planning", "Requirements analysis",
}

# name | aliases. A small copy: the full list is in the taxonomy file.
_BUILTIN_SKILLS = """
Python|py|python3|python programming
Java|java se|java ee|j2ee
JavaScript|js|ecmascript|es6
TypeScript|ts
C#|csharp|c sharp
C++|cpp
C|c language|ansi c
Go|golang
Rust
Kotlin
Swift|swiftui
PHP
Ruby
Scala
R|r language|rstudio
SQL|t-sql|tsql|pl/sql|plsql|sql queries
Shell scripting|bash|zsh
PowerShell
HTML and CSS|html|css|html5|css3|sass|scss
React|reactjs|react.js|redux
Angular|angularjs|rxjs
Vue.js|vue|vuejs|nuxt
Next.js|nextjs
Node.js|nodejs|node js|express.js|expressjs
Spring Boot|spring framework|spring mvc|spring cloud
.NET|.net core|dotnet|asp.net|asp.net core|entity framework
Django
Flask
FastAPI
Ruby on Rails|rails
React Native
Flutter
Android development|android|android sdk|jetpack compose
iOS development|ios|xcode|uikit
GraphQL
gRPC|protobuf
Pandas
NumPy|scipy
Selenium
Playwright
Cypress
Jest|vitest|mocha
pytest
JUnit|testng|mockito
AWS|amazon web services|ec2|cloudwatch|sqs|sns
Azure|microsoft azure|azure ad|entra id
Google Cloud Platform|gcp|google cloud
AWS Lambda|lambda
Amazon S3|s3
Docker|docker compose|dockerfile|containerisation|containerization
Kubernetes|k8s|eks|aks|gke|helm|argocd|argo cd|gitops
Terraform|terragrunt|opentofu
Ansible|puppet
AWS CloudFormation|cloudformation|aws cdk
Infrastructure as code|iac|pulumi|bicep
Jenkins
GitHub Actions
GitLab CI/CD|gitlab ci
Azure DevOps|azure pipelines
CI/CD|ci cd|cicd|continuous integration|continuous delivery
Linux|ubuntu|rhel|unix
Prometheus|promql
Grafana
Observability|opentelemetry|datadog|splunk
Site reliability engineering|sre
PostgreSQL|postgres
MySQL|mariadb
Microsoft SQL Server|sql server|mssql|ssis
Oracle Database
MongoDB|mongo
Redis|memcached
Amazon DynamoDB|dynamodb
Apache Cassandra|cassandra
Elasticsearch|opensearch|kibana
Snowflake|snowpark
Google BigQuery|bigquery
Amazon Redshift|redshift
Databricks|delta live tables|unity catalog
Microsoft Fabric|azure synapse|synapse
Apache Spark|spark|pyspark|spark sql
Apache Kafka|kafka|kafka streams|kinesis|event hubs
Apache Flink|flink
Apache Airflow|airflow|dagster|prefect
dbt|dbt core|dbt cloud
Azure Data Factory|adf
Apache Hadoop|hadoop|hdfs|hive
Data lakehouse|lakehouse|data lake|delta lake|iceberg|parquet
Data modelling|data modeling|dimensional modelling|star schema|data vault
Data warehousing|data warehouse|dwh
ETL and ELT pipelines|etl|elt|data pipelines|data pipeline|aws glue|informatica|talend|fivetran|airbyte
Data quality|great expectations|data validation
Data governance|data catalog|data lineage
Power BI|powerbi|dax|power query
Tableau
Looker|looker studio|lookml
Microsoft Excel|excel|vba|pivot tables
Data visualisation|data visualization|matplotlib|seaborn|plotly|d3.js|streamlit
Data analysis|exploratory data analysis|eda
Machine learning|ml|predictive modelling|supervised learning
Deep learning|neural networks|cnns|lstm
scikit-learn|sklearn
PyTorch
TensorFlow|keras
XGBoost|lightgbm|catboost
Hugging Face Transformers|hugging face|huggingface
Natural language processing|nlp|spacy|nltk|text classification
Computer vision|opencv|object detection|image classification
Generative AI|genai|llm|llms|large language models|chatgpt
Prompt engineering
Retrieval-augmented generation|rag
LangChain|langgraph|llamaindex
LLM APIs|openai api|azure openai|amazon bedrock
Vector databases|pinecone|weaviate|chroma|faiss|pgvector
LLM fine-tuning|fine-tuning|lora|qlora|peft
AI agents|agentic ai
MLflow|weights and biases|wandb
Amazon SageMaker|sagemaker
Azure Machine Learning|azure ml
Vertex AI
MLOps|ml ops|model deployment|model serving|kubeflow|feature store
Feature engineering
Time series forecasting|time series|forecasting|arima|prophet
Recommender systems|recommendation systems|recsys
Reinforcement learning
Statistics|statistical analysis|hypothesis testing|regression analysis|bayesian statistics
Experimentation and A/B testing|a/b testing|ab testing|causal inference
Model evaluation|cross-validation|hyperparameter tuning
Distributed training and GPU computing|cuda|distributed training|deepspeed|onnx
Agile delivery|agile|scrum|kanban|jira
Git|github|gitlab|bitbucket|version control
Unit and integration testing|unit testing|integration testing|tdd
Test automation|automated testing|qa automation
Code review|peer review
System design|distributed systems|software architecture
Microservices architecture|microservices|event-driven architecture
Object-oriented design|oop|design patterns|domain-driven design
Data structures and algorithms|algorithms|data structures
API design|rest api|rest apis|restful|openapi|swagger
Debugging and troubleshooting|debugging|troubleshooting
Application security|owasp|devsecops|secure coding
Communication|communication skills
Stakeholder management
Mentoring|coaching
Team leadership|people management
Technical leadership|tech lead
Problem solving
Teamwork|collaboration
Project management
Requirements analysis|business analysis|requirements gathering
"""

# Words that are too general to show a skill in a text (they are in the alias lists of the taxonomy)
_TEXT_SKIP_ALIASES = {
    "monitoring", "logging", "caching", "containers", "nosql", "transformers", "big data", "oracle", "charts", "dashboards", "dashboarding",
    "forecasting", "probability", "serverless", "gpu", "stats", "networking", "agile", "lambda", "rails", "synapse", "unix", "ubuntu", "prophet",
    "collaboration", "coaching", "algorithms", "data structures", "debugging", "troubleshooting", "backend", "frontend", "chroma",
    "iceberg", "parquet", "keras", "hive", "fine-tuning", "mocha", "vue", "ios", "android", "tdd", "oop", "eda",
}
# Names that are also common words. They count only in a list of skills, never in a sentence
_TEXT_SKIP_NAMES = {"go", "r", "c", "chroma", "prefect"}
# Names that are also words, but a capital letter shows the skill (Ruby, Swift): in a sentence they count when they are written with a capital
_TEXT_CASED = {"ruby", "rust", "swift", "scala", "dart", "excel"}
# Aliases that are too general for a CV, but good in a job description
_JD_KEEP = {"agile", "android", "ios", "tdd", "oop", "algorithms", "debugging", "troubleshooting", "excel", "coaching", "collaboration", "forecasting", "vue",
            "keras", "hive", "networking", "serverless", "caching", "monitoring", "logging", "containers", "unix", "ubuntu"}
# A short alias that is written in lower case in normal text. All the other short aliases (js, ts, ml, tf ...) must be written in capitals.
_SHORT_LOWER_OK = {"sql", "git", "aws", "gcp", "etl", "elt", "dbt", "sre", "nlp", "llm", "rag", "css", "api", "s3", "eks", "aks", "gke", "sqs", "sns",
                   "cka", "ec2", "dax", "php", "iac", "k8s", "ci/cd", "adf", "ssis"}


def _normal_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def cert_key(text: str) -> str:
    """A certification name as a key: lower case, dashes and punctuation are spaces. A plus sign stays (Security+)."""
    t = text.lower().replace("–", "-").replace("—", "-").replace("−", "-")
    return _normal_space(re.sub(r"[^a-z0-9+#]+", " ", t))


_LEVEL_PREFIX = {"senior", "sr", "snr", "junior", "jr", "jnr", "graduate", "grad", "associate", "principal", "staff", "mid", "intermediate", "lead",
                 "entry", "level", "midlevel", "experienced", "distinguished", "chief", "head"}


def role_key(text: str) -> str:
    """A job title as a key, so that "Sr. ML Engineer" and "Machine Learning Engineers" can be compared. Level words in front are dropped."""
    t = re.sub(r"\([^)]*\)", " ", text.lower()).replace("&", " and ")
    t = re.sub(r"\bfull[\s-]?stack\b", "fullstack", t)
    t = re.sub(r"\bfront[\s-]?end\b", "frontend", t)
    t = re.sub(r"\bback[\s-]?end\b", "backend", t)
    t = re.sub(r"\bml\b", "machine learning", t)
    t = re.sub(r"\bnlp\b", "natural language processing", t)
    t = re.sub(r"\bbi\b", "business intelligence", t)
    t = re.sub(r"\bdba\b", "database administrator", t)
    t = re.sub(r"\bsre\b", "site reliability engineer", t)
    t = re.sub(r"\bswe\b", "software engineer", t)
    t = re.sub(r"\bdev\b", "developer", t)
    t = re.sub(r"[^a-z0-9#+. ]+", " ", t)
    words = [w.strip(".") for w in t.split()]
    words = [w for w in words if w]
    while len(words) > 1 and words[0] in _LEVEL_PREFIX:
        words.pop(0)
    if words and len(words[-1]) > 3 and words[-1].endswith("s") and not words[-1].endswith(("ss", "us", "is", "ics")):
        words[-1] = words[-1][:-1]
    return " ".join(words)


# Skills that are tools (a language, a framework, a cloud). The built-in list has no groups, so this set stands for them.
_BUILTIN_TOOLS = {
    "Python", "Java", "JavaScript", "TypeScript", "C#", "C++", "C", "Go", "Rust", "Kotlin", "Swift", "PHP", "Ruby", "Scala", "R", "SQL", "Shell scripting",
    "PowerShell", "HTML and CSS", "React", "Angular", "Vue.js", "Next.js", "Node.js", "Spring Boot", ".NET", "Django", "Flask", "FastAPI", "Ruby on Rails",
    "React Native", "Flutter", "GraphQL", "Pandas", "NumPy", "Selenium", "Playwright", "Cypress", "Jest", "pytest", "JUnit", "AWS", "Azure",
    "Google Cloud Platform", "AWS Lambda", "Amazon S3", "Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins", "GitHub Actions", "Linux",
}


class Lexicon:
    """The lists, ready for use. Made once (see get())."""

    def __init__(self, data: Optional[Dict[str, Any]], source: str, path: Optional[str] = None):
        self.source = source            # "taxonomy" or "builtin"
        self.path = path
        data = data or {}
        # ----- levels -----
        words: Dict[str, List[str]] = {}
        for item in data.get("levels") or []:
            if isinstance(item, dict) and item.get("name") in LEVELS and isinstance(item.get("titleWords"), list):
                words[item["name"]] = [str(w).lower() for w in item["titleWords"] if str(w).strip()]
        for name in LEVELS:
            words.setdefault(name, list(_BUILTIN_LEVEL_WORDS[name]))
        self.level_words = words
        self._level_rx: List[Tuple[int, Pattern[str]]] = []
        for rank, name in enumerate(LEVELS):
            for w in words[name]:
                key = _normal_space(re.sub(r"[^a-z0-9+# ]+", " ", w.replace("-", " ")))
                if key in ("ii", "iii", "iv"):
                    self._level_rx.append((rank, re.compile(rf"(?:^| ){key}$")))     # a Roman number counts only at the end of a title
                elif key:
                    self._level_rx.append((rank, re.compile(rf"(?:^| ){re.escape(key)}(?: |$)")))
        # ----- roles -----
        titles: List[str] = []
        for item in data.get("roles") or []:
            title = item.get("title") if isinstance(item, dict) else item
            if isinstance(title, str) and title.strip():
                titles.append(title.strip())
        self.pick_roles = titles or list(_BUILTIN_ROLES)
        self.roles = list(self.pick_roles)
        for extra in _BUILTIN_ROLES + _EXTRA_ROLES:
            if extra not in self.roles:
                self.roles.append(extra)
        self._role_index: Dict[str, str] = {}
        for title in self.roles:
            self._role_index.setdefault(role_key(title), title)
        self.role_nouns: Set[str] = set(_ROLE_NOUNS) | {role_key(t).split()[-1] for t in self.roles if role_key(t)}
        # ----- skills -----
        self.skills: Dict[str, Dict[str, Any]] = {}
        listed = data.get("skills")
        if isinstance(listed, list) and listed:
            for item in listed:
                if isinstance(item, dict) and item.get("name"):
                    self.skills[item["name"]] = {"aliases": [str(a) for a in item.get("aliases") or []], "kind": item.get("kind") or "hard",
                                                 "group": item.get("group") or ""}
        else:
            for line in _BUILTIN_SKILLS.strip().splitlines():
                name, *aliases = line.split("|")
                self.skills[name] = {"aliases": aliases, "kind": "method" if name in _NON_HARD else "hard", "group": ""}
        self._skill_index: Dict[str, str] = {}
        for name, info in self.skills.items():
            self._skill_index.setdefault(name.lower(), name)
            for alias in info["aliases"]:
                self._skill_index.setdefault(alias.lower(), name)
        self._text_rx_ci, self._text_rx_cs, self._text_map = self._compile_skill_patterns()
        # ----- certifications -----
        self.certs: List[Dict[str, Any]] = []
        certs = data.get("certifications")
        if isinstance(certs, list) and certs:
            for item in certs:
                if isinstance(item, dict) and item.get("name"):
                    self._add_cert(item["name"], item.get("issuer") or "", [str(a) for a in item.get("aliases") or []])
        else:
            for line in _BUILTIN_CERTS.strip().splitlines():
                name, issuer, *aliases = line.split("|")
                self._add_cert(name, issuer, aliases)
        self._cert_keys: List[Tuple[str, Dict[str, Any]]] = sorted(
            ((k, c) for c in self.certs for k in c["keys"]), key=lambda kc: -len(kc[0]))
        self.issuers = sorted({c["issuer"] for c in self.certs if c["issuer"]} | set(_OTHER_ISSUERS), key=lambda s: -len(s))
        # ----- award kinds -----
        self.award_kinds: List[Dict[str, Any]] = []
        taxonomy_kinds: Dict[str, str] = {}
        for item in data.get("awardKinds") or []:
            if isinstance(item, dict) and item.get("kind"):
                taxonomy_kinds[item["kind"]] = item.get("label") or item["kind"]
        known: Set[str] = set()
        for line in _BUILTIN_AWARD_KINDS.strip().splitlines():
            kind, label, *keywords = line.split("|")
            generic = label.startswith("~")            # the general words of a kind (a place of a prize, "challenge"): they count last, and not alone
            label = label.lstrip("~")
            known.add(kind)
            if taxonomy_kinds and kind not in taxonomy_kinds:
                continue            # the kinds of the taxonomy are the only kinds that the reader may give
            shown = taxonomy_kinds.get(kind, label)
            self.award_kinds.append({"kind": kind, "label": shown, "generic": generic, "rx": re.compile("|".join(keywords + [re.escape(shown.lower())]), re.I)})
        for kind, label in taxonomy_kinds.items():       # a kind that the taxonomy has and the reader does not know: use the words of its label
            words_of_label = re.findall(r"[a-z]{5,}", label.lower())
            if kind not in known and words_of_label:
                self.award_kinds.append({"kind": kind, "label": label, "rx": re.compile("|".join(words_of_label), re.I)})
        # ----- domains and specialisations -----
        self.domains: List[Dict[str, Any]] = []
        for item in data.get("domains") or []:
            if isinstance(item, dict) and item.get("name"):
                self.domains.append({"name": item["name"], "specialisations": [str(s) for s in item.get("specialisations") or []]})
        if not self.domains:
            self.domains = [
                {"name": "Software Engineering", "specialisations": ["Backend", "Frontend", "Full-stack", "Mobile", "Platform and DevOps", "Quality engineering",
                                                                        "Security engineering", "Software architecture"]},
                {"name": "AI & Machine Learning", "specialisations": ["Machine learning engineering", "Generative AI and LLM", "Computer vision",
                                                                       "Natural language processing", "MLOps", "Applied science and research"]},
                {"name": "Data", "specialisations": ["Data engineering", "Data analytics", "Analytics engineering", "Business intelligence", "Data science",
                                                     "Business analysis"]},
            ]
        self.spec_domain = {s: d["name"] for d in self.domains for s in d["specialisations"]}
        self.fields_of_study = [str(f) for f in data.get("fieldsOfStudy") or [] if isinstance(f, str)]
        # The domain of a role (roles and occupations of the taxonomy) and the domains of a skill. Without the file there is no such data: the words of the
        # specialisations (_SPECIALISATION_KEYWORDS) tell the domain.
        self.domain_names = [d["name"] for d in self.domains]
        self._role_domain: Dict[str, str] = {}
        for group in ("roles", "occupations"):
            for item in data.get(group) or []:
                if isinstance(item, dict) and item.get("domain") in self.domain_names:
                    for title in (item.get("title"), item.get("anzscoTitle")):
                        if isinstance(title, str) and role_key(title):
                            self._role_domain.setdefault(role_key(title), item["domain"])
        self.skill_domains: Dict[str, List[str]] = {}
        for item in data.get("skills") or []:
            if isinstance(item, dict) and item.get("name"):
                ds = [d for d in item.get("domains") or [] if d in self.domain_names]
                if ds:
                    self.skill_domains[item["name"]] = ds

    # ----- certifications -----
    def _add_cert(self, name: str, issuer: str, aliases: List[str]) -> None:
        keys = [k for k in dict.fromkeys([cert_key(name)] + [cert_key(a) for a in aliases]) if len(k) >= 3]
        self.certs.append({"name": name, "issuer": issuer, "keys": keys})

    def find_certs(self, text: str) -> List[Dict[str, Any]]:
        """The certifications of the list that a text shows, in the order of the text. The longest name wins when names overlap."""
        ktext = " " + cert_key(text) + " "
        taken: List[Tuple[int, int]] = []
        found: List[Tuple[int, Dict[str, Any]]] = []
        tokens = set(ktext.split())
        for key, cert in self._cert_keys:
            if key.split(" ", 1)[0] not in tokens:
                continue                        # the first word of the name is not in the text: the name is not there
            start = ktext.find(" " + key + " ")
            while start >= 0:
                lo, hi = start, start + len(key) + 2
                if not any(lo < b and a < hi for a, b in taken):
                    taken.append((lo, hi))
                    found.append((lo, cert))
                    break
                start = ktext.find(" " + key + " ", start + 1)
        found.sort(key=lambda t: t[0])
        out: List[Dict[str, Any]] = []
        for _, cert in found:
            if cert not in out:
                out.append(cert)
        return out

    # ----- levels -----
    def level_of_title(self, title: str) -> Optional[str]:
        """The level that the words of a job title show. If there are more, the highest. None if there is no level word."""
        t = _normal_space(re.sub(r"[^a-z0-9+# ]+", " ", re.sub(r"\([^)]*\)", " ", title.lower()).replace("-", " ").replace("/", " ")))
        if not t:
            return None
        t = re.sub(r"\b(research|postdoctoral|post doctoral|teaching|visiting|clinical) fellow\b", " ", t)
        t = re.sub(r"\bassociate (director|principal|partner|professor|dean|vice)\b", r"\1", t)
        t = re.sub(r"\bstaff (nurse|accountant|member|members)\b", " ", t)
        best = -1
        for rank, rx in self._level_rx:
            if rank > best and rx.search(t):
                best = rank
        return LEVELS[best] if best >= 0 else None

    # ----- roles -----
    def canonical_role(self, text: str) -> Optional[str]:
        """The name in the role list for a job title, or None. "Developer" and "Engineer" are the same word here."""
        key = role_key(text)
        if not key:
            return None
        for k in (key, key.replace("developer", "engineer"), key.replace("engineer", "developer"), key.replace("programmer", "developer")):
            if k in self._role_index:
                return self._role_index[k]
        return None

    def find_roles(self, text: str) -> List[Tuple[int, int, str]]:
        """The known roles in a text: (start, end, name in the list). The longest phrase wins. A level word in front is part of the phrase."""
        toks = [(m.group(0).rstrip(".'’,"), m.start(), m.end()) for m in re.finditer(r"[A-Za-z0-9#+.&'’/\-]+", text)]
        toks = [(t, a, b) for t, a, b in toks if t]
        used = [False] * len(toks)
        found: List[Tuple[int, int, str]] = []
        for size in range(min(6, len(toks)), 0, -1):
            for i in range(len(toks) - size + 1):
                if any(used[i:i + size]):
                    continue
                phrase = " ".join(t for t, _, _ in toks[i:i + size])
                role = self.canonical_role(phrase)
                if role:
                    for k in range(i, i + size):
                        used[k] = True
                    found.append((toks[i][1], toks[i + size - 1][2], role))
        found.sort()
        return found

    def is_role_noun(self, word: str) -> bool:
        return word.lower().strip(".,") in self.role_nouns

    # ----- skills -----
    def _compile_skill_patterns(self, hard_only: bool = True) -> Tuple[Optional[Pattern[str]], Optional[Pattern[str]], Dict[str, str]]:
        """Patterns that find the skills of the list in a text: one that ignores the case, one for the names that must be written in capitals
        (a short name like ML, or a name that is also a word: Ruby, Swift). hard_only is False for a job description: the skills that are not
        tools (Communication, Mentoring, Agile delivery) count too."""
        ci: List[str] = []
        cs: List[str] = []
        mapping: Dict[str, str] = {}
        skip = _TEXT_SKIP_ALIASES if hard_only else _TEXT_SKIP_ALIASES - _JD_KEEP
        for name, info in self.skills.items():
            if hard_only and info["kind"] != "hard":
                continue
            for alias in [name] + info["aliases"]:
                low = alias.lower().strip()
                if not low or low in skip or low in _TEXT_SKIP_NAMES or (not hard_only and info["kind"] != "hard" and len(low) < 5):
                    continue
                short = len(low) <= 3 and low.isalpha()
                if (short and low not in _SHORT_LOWER_OK) or low in _TEXT_CASED:
                    for form in {alias.upper(), alias[:1].upper() + alias[1:].lower()}:
                        cs.append(re.escape(form))
                        mapping.setdefault(form, name)
                else:
                    ci.append(re.escape(low).replace(r"\ ", r"[\s-]"))
                    mapping.setdefault(low, name)
        edge_l, edge_r = r"(?<![A-Za-z0-9_+#.])", r"(?![A-Za-z0-9_+#]|\.[A-Za-z0-9])"
        rx_ci = re.compile(edge_l + "(?:" + "|".join(sorted(set(ci), key=len, reverse=True)) + ")" + edge_r, re.I) if ci else None
        rx_cs = re.compile(edge_l + "(?:" + "|".join(sorted(set(cs), key=len, reverse=True)) + ")" + edge_r) if cs else None
        return rx_ci, rx_cs, mapping

    def skills_in(self, text: str, hard_only: bool = True) -> List[Tuple[int, str]]:
        """The skills of the list that a text shows: (position, name), each name once, in the order of the text."""
        hits: List[Tuple[int, str]] = []
        rx_ci, rx_cs, mapping = (self._text_rx_ci, self._text_rx_cs, self._text_map) if hard_only else self._all_patterns()
        for rx in (rx_ci, rx_cs):
            if rx is None:
                continue
            for m in rx.finditer(text):
                raw = m.group(0)
                name = mapping.get(raw.lower()) or mapping.get(raw) or mapping.get(raw.upper()) or mapping.get(re.sub(r"[\s-]+", " ", raw.lower()))
                if name:
                    hits.append((m.start(), name))
        hits.sort()
        seen: Set[str] = set()
        out = []
        for pos, name in hits:
            if name not in seen:
                seen.add(name)
                out.append((pos, name))
        return out

    def _all_patterns(self) -> Tuple[Optional[Pattern[str]], Optional[Pattern[str]], Dict[str, str]]:
        cached = getattr(self, "_all_cache", None)
        if cached is None:
            cached = self._all_cache = self._compile_skill_patterns(hard_only=False)
        return cached

    def mention_pattern(self, name: str) -> Pattern[str]:
        """A pattern that finds a skill (its name and its longer aliases) in a text. Made once for each name."""
        cache = self.__dict__.setdefault("_mention_cache", {})
        rx = cache.get(name)
        if rx is None:
            words = [name] + [a for a in self.skills.get(name, {}).get("aliases", []) if len(a) > 3]
            rx = cache[name] = re.compile(r"(?<![A-Za-z0-9])(?:" + "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True)) + r")(?![A-Za-z0-9])", re.I)
        return rx

    def canonical_skill(self, item: str) -> Optional[str]:
        """The name in the list for one skill that a person wrote ("py", "k8s", "Kubernetes"). None if the list does not have it."""
        t = _normal_space(re.sub(r"\([^)]*\)", " ", item)).lower().strip(" .:-")
        return self._skill_index.get(t)

    def skill_kind(self, name: str) -> str:
        info = self.skills.get(name)
        return info["kind"] if info else ""

    def is_tool(self, name: str) -> bool:
        """Is the skill a language, a framework or a cloud (a tool: "3 years in Python") and not a field ("5 years in machine learning")?"""
        info = self.skills.get(name)
        if not info:
            return False
        return info["group"] in ("languages", "frameworks", "cloud") if info["group"] else name in _BUILTIN_TOOLS

    # ----- awards -----
    def award_kind(self, text: str, specific: bool = False) -> str:
        """The award kind for a line of text, or an empty string if no kind fits. specific=True leaves out the general words of the kinds
        (conference, workshop, challenge, "of the year"): a line that has only those is not sure to be an award."""
        for item in self.award_kinds:
            if specific and item.get("generic"):
                continue
            if item["rx"].search(text):
                return item["kind"]
        return ""

    def award_kinds_in(self, text: str) -> List[str]:
        """All the award kinds that a line names, in the order of the line ("Conference talk or paper and Security competition")."""
        kept: List[Tuple[int, int, str]] = []
        for item in self.award_kinds:                     # in the order of the list: the special words come first, the general words last
            m = item["rx"].search(text)
            if not m:
                continue
            if any(k != item["kind"] and a <= m.start() and m.end() <= b for a, b, k in kept):
                continue                                  # a general word inside the name of another kind ("Security competition or bug bounty")
            kept.append((m.start(), m.end(), item["kind"]))
        out: List[str] = []
        for _, _, kind in sorted(kept):
            if kind not in out:               # a kind can have more than one entry in the list
                out.append(kind)
        return out

    # ----- domains -----
    def role_domain(self, title: str) -> str:
        """The domain of a job title: from the roles of the taxonomy (also for "Senior Data Engineer"), else from the words of a specialisation in the title."""
        if not title:
            return ""
        canon = self.canonical_role(title)
        found = self._role_domain.get(role_key(canon or title), "") or self.domain_and_specialisation(title, "")[0]
        if not found and "Software Engineering" in self.domain_names and _GENERAL_IT_TITLE.search(title):
            found = "Software Engineering"            # a job title of IT in general (a developer, an administrator) is of the first domain
        return found

    def domains_of(self, titles: Iterable[str] = (), targets: Iterable[str] = (), headline: str = "", skills: Iterable[str] = (), text: str = "") -> List[str]:
        """The domains that a CV (or any person) belongs to: at most 2, the strongest first, [] when nothing fits.
        Points: the current role 10 (other roles of the past 3), a role that the person wants 6, the headline 4, each skill of the list 1 shared between the
        domains that the taxonomy gives it, the words of the specialisations in the text up to 1.5 for each specialisation. The second domain must have
        at least half of the points of the first."""
        score: Dict[str, float] = {d: 0.0 for d in self.domain_names}

        def add(domain: str, points: float) -> None:
            if domain in score:
                score[domain] += points

        for k, title in enumerate(titles):
            add(self.role_domain(title), 10.0 if k == 0 else 3.0)
        for title in targets:
            add(self.role_domain(title), 6.0)
        if headline:
            add(self.role_domain(headline), 4.0)
        for name in skills:
            ds = self.skill_domains.get(name) or []
            for d in ds:
                add(d, 1.0 / len(ds))
        if text:
            for spec, rx in _SPECIALISATION_KEYWORDS.items():
                domain = self.spec_domain.get(spec)
                if domain:
                    add(domain, 0.5 * min(3, len(re.findall(rx, text, re.I))))
        order = {d: i for i, d in enumerate(self.domain_names)}
        ranked = sorted(score.items(), key=lambda kv: (-kv[1], order[kv[0]]))
        if not ranked or ranked[0][1] < 2.5:
            return []
        out = [ranked[0][0]]
        if len(ranked) > 1 and ranked[1][1] >= 2.5 and ranked[1][1] >= 0.5 * ranked[0][1]:
            out.append(ranked[1][0])
        return out

    def domain_and_specialisation(self, title: str, text: str) -> Tuple[str, str]:
        """The specialisation (and its domain) that a title and a text show best. A word in the title counts three times."""
        best: Tuple[float, str] = (0.0, "")
        for spec, rx in _SPECIALISATION_KEYWORDS.items():
            if spec not in self.spec_domain:
                continue
            compiled = re.compile(rx, re.I)
            in_title = min(2, len(compiled.findall(title)))
            score = 10.0 * in_title + (min(5, len(compiled.findall(text))) if not in_title else 0)       # the title decides, the text breaks no tie
            if score > best[0]:
                best = (score, spec)
        spec = best[1]
        return (self.spec_domain.get(spec, ""), spec)


# =====================================================================
# Access
# =====================================================================
_lock = threading.Lock()
_cache: Dict[str, Lexicon] = {}


def _load(path: Optional[Path]) -> Lexicon:
    if path is not None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return Lexicon(data, "taxonomy", str(path))
        except (OSError, ValueError):
            pass
    return Lexicon(None, "builtin", None)


def get() -> Lexicon:
    """The lists. The taxonomy file is read once. If it cannot be read, the built-in lists are used."""
    lex = _cache.get("main")
    if lex is None:
        with _lock:
            lex = _cache.get("main")
            if lex is None:
                lex = _load(default_path())
                _cache["main"] = lex
    return lex


def use_builtin() -> None:
    """Use only the built-in lists (for a test that must not depend on the taxonomy file)."""
    with _lock:
        _cache["main"] = Lexicon(None, "builtin", None)


def use_file(path: Optional[os.PathLike] = None) -> None:
    """Read the taxonomy from this file (or from the default place, if no path is given)."""
    with _lock:
        _cache["main"] = _load(Path(path) if path else default_path())


def reset() -> None:
    with _lock:
        _cache.clear()
