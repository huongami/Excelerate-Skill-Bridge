// MOCK BACKEND — the Jinder job catalogue and recommendations. The real backend replaces this file.
// Data: the 24 embedded ICT jobs of seed-jobs.js (copied from the synthetic job file of the backend data) and the jobs that employers post.
// There is no CSV file and no network call. All job data is internal Jinder data. The three domains are the only categories.
// Skill names, the words that show a skill and the related skills come from jinder_backend_engine/data/reference/ict_taxonomy.json.
// The match uses only skills, roles, domains, level, locations and work types.
// It never uses nationality, ethnicity, gender, age, visa status or country of study.
import { SEED_JOBS } from "./seed-jobs.js";
import { levelRank } from "../../data/levels.js";

// A job category is one of the 3 domains. The domain of a profile is stored in `industry` and `targetIndustries` (plan F6).
// The map keeps the old shape of this file: category -> the profile domains that fit it.
const CATEGORY_MAP = {
  "Software Engineering": ["Software Engineering"],
  "AI & Machine Learning": ["AI & Machine Learning"],
  "Data": ["Data"],
};

// The skills of the taxonomy: [name, words that show the skill (aliases, separated by "|"), related skills (separated by "|")].
// Made from ict_taxonomy.json (172 skills). Change the taxonomy first, then this table.
const SKILL_TABLE = [
  ["Python", "py|python3|python 3|python programming", "R|Ruby|Shell scripting|Go|MATLAB"],
  ["Java", "java se|java ee|j2ee|jdk|java programming", "Kotlin|C#|Scala|Spring Boot|Go"],
  ["JavaScript", "js|javascript es6|es6|ecmascript|vanilla js|vanilla javascript", "TypeScript|Node.js|React|HTML and CSS|PHP"],
  ["TypeScript", "ts|typed javascript", "JavaScript|Node.js|Angular|React|Next.js"],
  ["C#", "csharp|c sharp|c-sharp", "Java|.NET|Kotlin|C++|Azure Functions"],
  ["C++", "cpp|c plus plus|cplusplus", "C|Rust|C#|Distributed training and GPU computing|Data structures and algorithms"],
  ["C", "c language|ansi c|c programming", "C++|Rust|Go"],
  ["Go", "golang|go lang|go programming", "Rust|Java|Python|C"],
  ["Rust", "rust lang|rustlang", "C++|Go|C|Swift"],
  ["Kotlin", "kotlin multiplatform", "Java|Android development|Swift|Scala|C#"],
  ["Swift", "swiftui|swift ui", "iOS development|Kotlin|Rust"],
  ["PHP", "php 8|php7|php programming", "Laravel|JavaScript|Ruby"],
  ["Ruby", "ruby programming|ruby lang", "Ruby on Rails|Python|PHP"],
  ["Scala", "scala 3|scala lang", "Java|Kotlin|Apache Spark"],
  ["R", "r language|r programming|rstudio|r studio|tidyverse", "Python|Statistics|MATLAB"],
  ["SQL", "structured query language|t-sql|tsql|pl/sql|plsql|sql queries|ansi sql", "PostgreSQL|MySQL|Microsoft SQL Server|Database design and tuning|Oracle Database"],
  ["Shell scripting", "bash|zsh|bash scripting|unix shell", "Linux|PowerShell|Python|Ansible"],
  ["PowerShell", "powershell core|pwsh", "Shell scripting|Azure|Ansible"],
  ["MATLAB", "matlab simulink|simulink|octave", "Python|R|NumPy"],
  ["HTML and CSS", "html|css|html5|css3|html/css|sass|scss|responsive design|responsive web design", "JavaScript|Tailwind CSS|Web accessibility"],
  ["React", "reactjs|react.js|react hooks|redux", "JavaScript|TypeScript|Next.js|React Native|Vue.js"],
  ["Angular", "angularjs|angular 2|rxjs|angular cli", "TypeScript|React|Vue.js"],
  ["Vue.js", "vue|vuejs|vue 3|nuxt|nuxt.js", "React|JavaScript|Angular"],
  ["Next.js", "nextjs|next js", "React|Node.js|TypeScript|Tailwind CSS"],
  ["Node.js", "nodejs|node js|express.js|expressjs", "JavaScript|TypeScript|NestJS|API design|Next.js"],
  ["NestJS", "nest.js|nest js", "Node.js|TypeScript|Spring Boot"],
  ["Spring Boot", "spring framework|spring mvc|spring cloud|spring boot 3", "Java|Kotlin|Microservices architecture|.NET|NestJS"],
  [".NET", ".net core|dotnet|asp.net|asp.net core|entity framework|.net framework|.net 8", "C#|Spring Boot|Azure"],
  ["Django", "django rest framework|drf", "Python|Flask|FastAPI|Ruby on Rails|Laravel"],
  ["Flask", "flask framework|flask api", "Python|Django|FastAPI"],
  ["FastAPI", "fast api|pydantic", "Python|Flask|Django"],
  ["Ruby on Rails", "rails|ruby rails|ror", "Ruby|Django|Laravel"],
  ["Laravel", "laravel framework|laravel php", "PHP|Ruby on Rails|Django"],
  ["React Native", "react-native|reactnative|expo", "React|Flutter|Android development|iOS development"],
  ["Flutter", "dart|flutter dart|dart language", "React Native|Android development|iOS development"],
  ["Android development", "android|android sdk|android studio|jetpack compose|android app development", "Kotlin|Java|Flutter|React Native"],
  ["iOS development", "ios|ios app development|uikit|xcode|apple development", "Swift|Flutter|React Native"],
  ["GraphQL", "graph ql|apollo|apollo graphql", "API design|gRPC|Node.js"],
  ["gRPC", "protocol buffers|protobuf", "API design|GraphQL|Microservices architecture"],
  ["Tailwind CSS", "tailwind|tailwindcss", "HTML and CSS|React|Next.js"],
  ["Pandas", "pandas library|pandas dataframe|dataframes", "NumPy|Python|Data analysis|scikit-learn|Feature engineering"],
  ["NumPy", "numpy arrays|scipy|numerical python", "Pandas|Python|MATLAB"],
  ["Selenium", "selenium webdriver|webdriver|selenium grid", "Playwright|Cypress|Test automation"],
  ["Playwright", "playwright test", "Cypress|Selenium|Test automation"],
  ["Cypress", "cypress.io|cypress e2e", "Playwright|Selenium|Jest|Test automation"],
  ["Jest", "jest testing|vitest|react testing library|mocha|jasmine", "JavaScript|Cypress|Unit and integration testing"],
  ["pytest", "py.test|unittest|python unittest", "Python|Unit and integration testing|JUnit"],
  ["JUnit", "junit 5|testng|mockito", "Java|Unit and integration testing|pytest"],
  ["AWS", "amazon web services|aws cloud|ec2|amazon ec2|amazon rds|cloudwatch|amazon sqs|sqs|sns|amazon sns", "Azure|Google Cloud Platform|AWS Lambda|Amazon S3|AWS CloudFormation"],
  ["Azure", "microsoft azure|azure cloud|azure active directory|azure ad|entra id|azure vm|azure app service|azure blob storage", "AWS|Google Cloud Platform|Azure Functions|Azure DevOps|PowerShell"],
  ["Google Cloud Platform", "gcp|google cloud|google cloud services|cloud run|gcs|google cloud storage", "AWS|Azure|Google BigQuery|Vertex AI"],
  ["AWS Lambda", "lambda|aws serverless|serverless|serverless functions|aws api gateway", "Azure Functions|AWS|Amazon S3|Microservices architecture"],
  ["Amazon S3", "s3|aws s3|s3 bucket|object storage|simple storage service", "AWS|Data lakehouse|Azure|AWS Lambda"],
  ["Azure Functions", "azure function apps|function apps|durable functions", "AWS Lambda|Azure|C#"],
  ["Docker", "docker compose|dockerfile|containers|containerisation|containerization|docker containers|container images", "Kubernetes|Linux|CI/CD|MLflow|MLOps"],
  ["Kubernetes", "k8s|kube|eks|aks|gke|openshift|helm|helm charts|argo cd|argocd|gitops|container orchestration", "Docker|Terraform|Observability|Site reliability engineering|Prometheus"],
  ["Terraform", "terraform cloud|hcl|opentofu|terragrunt", "Infrastructure as code|AWS CloudFormation|Ansible|Kubernetes"],
  ["Ansible", "ansible playbooks|puppet|configuration management", "Terraform|Infrastructure as code|Linux|Shell scripting|PowerShell"],
  ["AWS CloudFormation", "cloudformation|aws cdk|cdk", "Terraform|Infrastructure as code|AWS"],
  ["Infrastructure as code", "iac|pulumi|bicep|azure bicep|arm templates|infrastructure-as-code", "Terraform|AWS CloudFormation|Ansible"],
  ["Jenkins", "jenkinsfile|jenkins pipelines", "CI/CD|GitHub Actions|GitLab CI/CD|Azure DevOps"],
  ["GitHub Actions", "github workflows|gh actions", "CI/CD|Jenkins|GitLab CI/CD|Git|Azure DevOps"],
  ["GitLab CI/CD", "gitlab ci|gitlab pipelines|gitlab-ci", "CI/CD|GitHub Actions|Jenkins"],
  ["Azure DevOps", "azure pipelines|azure repos|vsts|tfs|azure boards", "CI/CD|GitHub Actions|Azure|Jenkins"],
  ["CI/CD", "ci cd|cicd|ci/cd pipelines|continuous integration|continuous delivery|continuous deployment|build pipelines|deployment pipelines", "Jenkins|GitHub Actions|GitLab CI/CD|Azure DevOps|Docker"],
  ["Linux", "ubuntu|red hat|rhel|centos|debian|unix|linux administration|linux server", "Shell scripting|Networking fundamentals|Docker|Ansible|Site reliability engineering"],
  ["Prometheus", "promql|prometheus monitoring|alertmanager", "Grafana|Observability|Kubernetes"],
  ["Grafana", "grafana dashboards|grafana loki", "Prometheus|Observability|Data visualisation"],
  ["Observability", "monitoring|logging|opentelemetry|otel|distributed tracing|datadog|new relic|splunk|application monitoring|apm", "Prometheus|Grafana|Site reliability engineering|Incident response|Kubernetes"],
  ["Site reliability engineering", "sre|site reliability|reliability engineering|slo|error budgets", "Observability|Incident response|Kubernetes|Linux"],
  ["Networking fundamentals", "computer networking|tcp/ip|tcp ip|dns|load balancing|load balancers|vpc|firewalls|subnets|vpn|network security basics", "Linux|Cloud security|Azure|Penetration testing"],
  ["Cloud security", "cloud security posture|aws security|azure security|iam policies|identity and access management|iam|kms|secrets management|hashicorp vault|zero trust", "Authentication and authorisation|Application security|Networking fundamentals|AWS|Threat modelling"],
  ["PostgreSQL", "postgres|psql|pgsql", "MySQL|SQL|Microsoft SQL Server|Database design and tuning|Oracle Database"],
  ["MySQL", "mariadb|mysql database|aurora mysql", "PostgreSQL|SQL|Microsoft SQL Server"],
  ["Microsoft SQL Server", "sql server|mssql|ms sql|ssms|ssis|ssrs|azure sql", "SQL|PostgreSQL|Oracle Database|Azure Data Factory|MySQL"],
  ["Oracle Database", "oracle|oracle db|oracle rdbms", "SQL|Microsoft SQL Server|PostgreSQL"],
  ["MongoDB", "mongo|mongo db|mongoose|nosql|document database|document databases", "Amazon DynamoDB|Redis|Apache Cassandra|Elasticsearch"],
  ["Redis", "redis cache|caching|in-memory cache|memcached", "MongoDB|Amazon DynamoDB|System design|Elasticsearch"],
  ["Amazon DynamoDB", "dynamodb|dynamo db|aws dynamodb", "MongoDB|Apache Cassandra|AWS|Redis"],
  ["Apache Cassandra", "cassandra|scylladb|datastax", "Amazon DynamoDB|MongoDB|Apache Kafka"],
  ["Elasticsearch", "elastic search|opensearch|kibana|elk|elastic stack|solr", "MongoDB|Observability|Redis|Vector databases"],
  ["Snowflake", "snowflake data cloud|snowpark|snowflake sql|snowpipe", "Google BigQuery|Amazon Redshift|Databricks|Data warehousing|Microsoft Fabric"],
  ["Google BigQuery", "bigquery|big query|bq", "Snowflake|Amazon Redshift|Google Cloud Platform|Data warehousing|Looker"],
  ["Amazon Redshift", "redshift|aws redshift|redshift spectrum", "Snowflake|Google BigQuery|AWS|Data warehousing"],
  ["Databricks", "databricks lakehouse|unity catalog|delta live tables|databricks sql|databricks workflows", "Apache Spark|Data lakehouse|Snowflake|Microsoft Fabric"],
  ["Microsoft Fabric", "azure synapse|synapse analytics|azure synapse analytics|onelake|synapse", "Azure Data Factory|Power BI|Databricks|Snowflake"],
  ["Apache Spark", "spark|pyspark|spark sql|spark streaming|spark structured streaming", "Databricks|Apache Hadoop|Scala|Apache Flink|Apache Kafka"],
  ["Apache Kafka", "kafka|confluent|kafka streams|kafka connect|ksql|event streaming|kinesis|amazon kinesis|azure event hubs|event hubs|rabbitmq|message queues|pub/sub", "Apache Flink|Apache Spark|Microservices architecture|Apache Cassandra"],
  ["Apache Flink", "flink|flink sql|stream processing|apache beam", "Apache Kafka|Apache Spark|Java"],
  ["Apache Airflow", "airflow|airflow dags|dags|dagster|prefect|workflow orchestration|data orchestration|mwaa|cloud composer", "ETL and ELT pipelines|dbt|Azure Data Factory|Python"],
  ["dbt", "dbt core|dbt cloud|data build tool|dbt models", "SQL|Data modelling|ETL and ELT pipelines|Apache Airflow|Data quality"],
  ["Azure Data Factory", "adf|data factory|synapse pipelines", "ETL and ELT pipelines|Microsoft Fabric|Azure|Apache Airflow|Microsoft SQL Server"],
  ["Apache Hadoop", "hadoop|hdfs|hive|apache hive|mapreduce|hbase|big data", "Apache Spark|Data lakehouse|Data warehousing"],
  ["Data lakehouse", "lakehouse|data lake|data lakes|delta lake|apache iceberg|iceberg|apache hudi|hudi|parquet|medallion architecture", "Databricks|Amazon S3|Apache Spark|Data warehousing|Apache Hadoop"],
  ["Data modelling", "data modeling|dimensional modelling|dimensional modeling|kimball|star schema|data vault|entity relationship|er diagrams|erd|conceptual data model|logical data model", "Data warehousing|Database design and tuning|dbt|SQL|Data governance"],
  ["Data warehousing", "data warehouse|dwh|edw|enterprise data warehouse|olap|data marts|data mart", "Data modelling|Snowflake|ETL and ELT pipelines|SQL|Google BigQuery"],
  ["ETL and ELT pipelines", "etl|elt|data pipelines|data pipeline|data integration|data ingestion|aws glue|informatica|talend|fivetran|airbyte|batch processing", "Apache Airflow|dbt|Apache Spark|Azure Data Factory|Data warehousing"],
  ["Data quality", "data validation|great expectations|data testing|data profiling|data cleansing|data cleaning|data observability|deequ", "Data governance|dbt|ETL and ELT pipelines"],
  ["Data governance", "data catalog|data catalogue|data lineage|master data management|mdm|data stewardship|collibra|data management", "Data quality|Data privacy and compliance|Data modelling|Responsible AI"],
  ["Database design and tuning", "database design|schema design|query optimisation|query optimization|query tuning|database indexing|indexing|normalisation|normalization|performance tuning|database administration|dba|stored procedures|database migration", "SQL|PostgreSQL|Data modelling|Microsoft SQL Server|System design"],
  ["Power BI", "powerbi|power bi desktop|dax|power query|power bi service|microsoft power bi", "Tableau|Looker|Data visualisation|Microsoft Excel|Microsoft Fabric"],
  ["Tableau", "tableau desktop|tableau server|tableau prep|tableau public", "Power BI|Looker|Data visualisation"],
  ["Looker", "looker studio|lookml|google data studio|data studio", "Power BI|Tableau|Data visualisation|Google BigQuery"],
  ["Microsoft Excel", "excel|spreadsheets|ms excel|vba|excel vba|pivot tables|google sheets|vlookup|xlookup", "Data analysis|Power BI|Data visualisation"],
  ["Data visualisation", "data visualization|dashboards|dashboarding|charts|matplotlib|seaborn|plotly|d3|d3.js|bokeh|streamlit|visual analytics", "Power BI|Tableau|Data storytelling|Data analysis|Grafana"],
  ["Data analysis", "data analytics|exploratory data analysis|eda|data mining|ad hoc analysis|business analytics", "SQL|Statistics|Data visualisation|Microsoft Excel|Pandas"],
  ["Machine learning", "ml|machine-learning|ml models|predictive modelling|predictive modeling|supervised learning|unsupervised learning|classical ml|applied machine learning|statistical learning|predictive analytics|ai/ml", "Deep learning|scikit-learn|Statistics|Feature engineering|Model evaluation"],
  ["Deep learning", "dl|neural networks|neural network|cnns|rnns|lstm|convolutional neural networks|gans|autoencoders", "Machine learning|PyTorch|TensorFlow|Computer vision|Natural language processing"],
  ["scikit-learn", "sklearn|scikit learn|scikitlearn", "Machine learning|Python|Pandas|XGBoost|Feature engineering"],
  ["PyTorch", "torch|pytorch lightning|torchvision", "TensorFlow|Deep learning|Hugging Face Transformers|Computer vision|Reinforcement learning"],
  ["TensorFlow", "tf|keras|tensorflow keras|tf.keras|tensorflow lite|tflite|tensorflow serving", "PyTorch|Deep learning|Machine learning|Computer vision"],
  ["XGBoost", "lightgbm|catboost|gradient boosting|gradient boosted trees|gbm|random forest|random forests|decision trees", "scikit-learn|Machine learning|Feature engineering"],
  ["Hugging Face Transformers", "hugging face|huggingface|transformers|hf transformers|bert|sentence transformers|huggingface transformers", "PyTorch|Natural language processing|Generative AI|LLM fine-tuning"],
  ["Natural language processing", "nlp|text mining|text classification|spacy|nltk|named entity recognition|ner|sentiment analysis|text analytics", "Hugging Face Transformers|Machine learning|Deep learning|Generative AI"],
  ["Computer vision", "image recognition|image classification|object detection|opencv|image processing|yolo|image segmentation|video analytics|ocr", "Deep learning|PyTorch|Machine learning|TensorFlow"],
  ["Generative AI", "genai|gen ai|gen-ai|large language models|large language model|llm|llms|foundation models|generative models|chatgpt|gpt|gpt-4|llm applications|generative artificial intelligence|diffusion models", "Prompt engineering|Retrieval-augmented generation|LLM APIs|LLM fine-tuning|Natural language processing"],
  ["Prompt engineering", "prompt design|prompting|prompt optimisation|prompt optimization|prompt templates|few-shot prompting|chain of thought", "Generative AI|LLM APIs|Retrieval-augmented generation|AI agents"],
  ["Retrieval-augmented generation", "rag|retrieval augmented generation|rag pipelines|rag systems|semantic search|knowledge retrieval|embeddings", "Vector databases|LangChain|Generative AI|LLM APIs|Prompt engineering"],
  ["LangChain", "langgraph|llamaindex|llama index|llm orchestration|semantic kernel|langsmith", "Retrieval-augmented generation|LLM APIs|AI agents|Generative AI"],
  ["LLM APIs", "openai api|openai|azure openai|anthropic api|claude api|gemini api|amazon bedrock|bedrock|llm integration|chat completions|function calling", "Generative AI|Prompt engineering|Retrieval-augmented generation|LangChain|AI agents"],
  ["Vector databases", "vector database|vector db|pinecone|weaviate|chroma|chromadb|milvus|qdrant|faiss|pgvector|vector search|vector stores|embedding stores", "Retrieval-augmented generation|Elasticsearch|PostgreSQL|Generative AI"],
  ["LLM fine-tuning", "fine-tuning|fine tuning|finetuning|lora|qlora|peft|rlhf|instruction tuning|model distillation|parameter-efficient fine-tuning|llm training", "Hugging Face Transformers|Deep learning|Generative AI|Distributed training and GPU computing"],
  ["AI agents", "agentic ai|agentic workflows|llm agents|agent frameworks|tool calling|tool use|multi-agent systems|multi-agent|model context protocol|mcp servers|autonomous agents|agent orchestration|crewai|autogen", "LangChain|Generative AI|LLM APIs|Prompt engineering"],
  ["Responsible AI", "ai ethics|ai governance|ai safety|ethical ai|fairness and bias|model fairness|bias mitigation|guardrails|ai guardrails|explainability|explainable ai|xai|trustworthy ai|model interpretability", "Data privacy and compliance|Model evaluation|Data governance|Generative AI"],
  ["MLflow", "ml flow|experiment tracking|weights and biases|weights & biases|wandb|w&b|neptune|comet ml|model registry", "MLOps|Machine learning|Docker"],
  ["Amazon SageMaker", "sagemaker|aws sagemaker|sagemaker studio|sagemaker pipelines|sagemaker endpoints", "Azure Machine Learning|Vertex AI|MLOps|AWS"],
  ["Azure Machine Learning", "azure ml|azureml|azure ml studio|azure ai studio|azure ai foundry|ai foundry", "Amazon SageMaker|Vertex AI|MLOps|Azure"],
  ["Vertex AI", "google vertex ai|vertex ai pipelines|vertex ai studio", "Amazon SageMaker|Azure Machine Learning|Google Cloud Platform|MLOps"],
  ["MLOps", "ml ops|machine learning operations|model deployment|model serving|ml pipelines|ml pipeline|kubeflow|model monitoring|feature store|feature stores|bentoml|seldon|ml platform|llmops", "MLflow|Docker|CI/CD|Machine learning|Kubernetes"],
  ["Feature engineering", "feature selection|feature extraction|feature design|feature creation|dimensionality reduction|pca|data preprocessing|data preparation", "Machine learning|Pandas|Data analysis|scikit-learn|XGBoost"],
  ["Time series forecasting", "time series|time-series|forecasting|demand forecasting|arima|facebook prophet|sarima|forecast models|anomaly detection", "Statistics|Machine learning|Data analysis"],
  ["Recommender systems", "recommendation systems|recommendation engines|recommender engines|recsys|collaborative filtering|personalisation models|ranking models|learning to rank", "Machine learning|Deep learning|Feature engineering"],
  ["Reinforcement learning", "rl|deep reinforcement learning|q-learning|policy gradients", "Deep learning|Machine learning|PyTorch"],
  ["Statistics", "stats|statistical analysis|statistical modelling|statistical modeling|hypothesis testing|regression analysis|bayesian statistics|bayesian methods|probability|inferential statistics|descriptive statistics|statistical inference", "Data analysis|Machine learning|R|Experimentation and A/B testing|Time series forecasting"],
  ["Experimentation and A/B testing", "a/b testing|ab testing|a/b tests|split testing|experiment design|experimentation|controlled experiments|causal inference|multivariate testing", "Statistics|Data analysis|Product thinking"],
  ["Model evaluation", "model validation|cross-validation|cross validation|model metrics|precision and recall|evaluation metrics|model testing|llm evaluation|llm evals|evals|model performance|hyperparameter tuning|hyperparameter optimisation|model selection", "Machine learning|Statistics|scikit-learn|Responsible AI"],
  ["Distributed training and GPU computing", "cuda|gpu computing|gpu programming|gpu|distributed training|deepspeed|horovod|multi-gpu training|nvidia gpus|triton inference server|model parallelism|model optimisation|onnx|tensorrt", "PyTorch|Deep learning|LLM fine-tuning|C++"],
  ["Agile delivery", "agile|scrum|kanban|sprint planning|agile methodologies|agile methodology|scrum master|jira|scaled agile|sprints|agile development", "Project management|Estimation and planning|Teamwork|Facilitation"],
  ["Git", "github|gitlab|bitbucket|version control|source control|gitflow|git flow|branching strategies|git workflow|svn", "CI/CD|Code review|GitHub Actions"],
  ["Unit and integration testing", "unit testing|integration testing|unit tests|tdd|test-driven development|test driven development|bdd|behaviour-driven development|behavior-driven development|mocking|automated tests|contract testing|code coverage", "Test automation|pytest|JUnit|Jest|Code review"],
  ["Test automation", "automated testing|qa automation|test automation framework|sdet|e2e testing|end-to-end testing|api testing|regression testing|ui automation|test frameworks|postman|rest assured", "Selenium|Playwright|Cypress|Unit and integration testing|Performance testing"],
  ["Manual testing", "manual qa|exploratory testing|test cases|test case design|test planning|uat|user acceptance testing|regression test cases|test scripts|bug reporting|defect management|functional testing|test execution|qa testing|quality assurance", "Test automation|Requirements analysis|Debugging and troubleshooting|Web accessibility"],
  ["Performance testing", "load testing|stress testing|jmeter|apache jmeter|k6|gatling|locust|performance test|soak testing|capacity testing|performance engineering", "Test automation|Observability|System design"],
  ["Code review", "peer review|code reviews|pull request reviews|pr reviews|reviewing code|code quality", "Git|Mentoring|Unit and integration testing|Teamwork"],
  ["System design", "software architecture|solution architecture|solutions architecture|architecture design|scalable systems|high-level design|hld|low-level design|lld|distributed systems|scalability|system architecture|technical design|design documents|architecture patterns", "Microservices architecture|API design|Object-oriented design|Database design and tuning|Redis"],
  ["Microservices architecture", "microservices|microservice|service-oriented architecture|soa|event-driven architecture|event driven architecture|event-driven systems|service mesh|api gateway", "System design|API design|Docker|Kubernetes|Apache Kafka"],
  ["Object-oriented design", "oop|object oriented programming|object-oriented programming|design patterns|solid principles|domain-driven design|ddd|clean architecture|clean code|oo design|uml", "System design|Java|C#|Unit and integration testing|Data structures and algorithms"],
  ["Data structures and algorithms", "dsa|algorithms|data structures|algorithm design|competitive programming|leetcode|algorithmic problem solving|complexity analysis|big o", "Problem solving|C++|Object-oriented design"],
  ["API design", "restful|rest api|rest apis|restful api|restful apis|openapi|swagger|api development|web services|web apis|api design and development|json apis|soap|api versioning|api documentation", "GraphQL|gRPC|Microservices architecture|Authentication and authorisation|Node.js"],
  ["Technical documentation", "technical writing|architecture decision records|adr|runbooks|api docs|confluence|design docs|readme|knowledge base articles", "Communication|Requirements analysis|System design"],
  ["Debugging and troubleshooting", "debugging|troubleshooting|root cause analysis|rca|bug fixing|issue diagnosis|production support|problem diagnosis|fault finding|log analysis", "Problem solving|Incident response|Observability|Unit and integration testing|Manual testing"],
  ["Application security", "appsec|owasp|owasp top 10|secure coding|devsecops|secure software development|sast|dast|dependency scanning|code security|security best practices|xss|web application security|vulnerability scanning", "Authentication and authorisation|Threat modelling|Penetration testing|Cloud security|Data privacy and compliance"],
  ["Authentication and authorisation", "authentication|authorisation|authorization|oauth|oauth2|oauth 2.0|openid connect|oidc|jwt|json web tokens|sso|single sign-on|saml|identity management|identity and access|keycloak|okta|auth0|rbac|mfa|passkeys", "Application security|Cloud security|API design"],
  ["Penetration testing", "pen testing|pentesting|pentest|ethical hacking|red teaming|red team|burp suite|metasploit|vulnerability assessment|security testing|offensive security|bug bounty|ctf|capture the flag|nmap|kali linux", "Application security|Threat modelling|Networking fundamentals|Linux"],
  ["Threat modelling", "threat modeling|stride threat model|attack trees|security architecture|security design reviews|risk assessment|security risk assessment|mitre att&ck|attack surface analysis", "Application security|Cloud security|Penetration testing|System design"],
  ["Incident response", "incident management|on-call|on call|oncall|postmortems|post-mortems|post-incident reviews|security incident response|incident handling|pagerduty|opsgenie|outage response", "Observability|Site reliability engineering|Debugging and troubleshooting"],
  ["Web accessibility", "accessibility|a11y|wcag|wcag 2.1|wcag 2.2|wai-aria|accessible design|inclusive design|screen reader testing", "HTML and CSS|React|Manual testing"],
  ["Data privacy and compliance", "data privacy|privacy act|gdpr|pii|pii handling|data protection|privacy by design|soc 2|soc2|iso 27001|australian privacy principles|regulatory compliance", "Data governance|Responsible AI|Application security|Cloud security"],
  ["Communication", "communication skills|written communication|verbal communication|presentation skills|presenting|public speaking|clear communication|technical communication|written and verbal communication|interpersonal skills", "Stakeholder management|Technical documentation|Data storytelling|Teamwork|Facilitation"],
  ["Stakeholder management", "stakeholder engagement|stakeholder communication|client management|client relationships|customer management|expectation management|relationship management|business partnering", "Communication|Product thinking|Requirements analysis|Project management|Team leadership"],
  ["Mentoring", "coaching|mentorship|mentoring juniors|coaching engineers|onboarding new starters|knowledge sharing|training others|peer coaching|developing others", "Team leadership|Code review|Technical leadership|Continuous learning"],
  ["Team leadership", "leading teams|team lead|people management|people leadership|line management|engineering management|managing engineers|managing teams|team management|direct reports", "Mentoring|Technical leadership|Stakeholder management|Project management"],
  ["Technical leadership", "tech lead|technical lead|technical direction|technical strategy|architecture leadership|leading technical decisions|engineering leadership|technical mentoring|staff engineering|technical ownership|engineering excellence", "Team leadership|System design|Mentoring|Stakeholder management|Estimation and planning"],
  ["Problem solving", "analytical thinking|analytical skills|critical thinking|logical thinking|creative problem solving|solution oriented|problem-solving|analytical problem solving|structured thinking|analytical mindset", "Debugging and troubleshooting|Data structures and algorithms|Continuous learning"],
  ["Teamwork", "collaboration|team player|cross-functional collaboration|cross functional teams|working in teams|pair programming|team collaboration|collaborative working|working with designers|partnering with product", "Communication|Agile delivery|Code review|Continuous learning"],
  ["Project management", "project delivery|program management|programme management|delivery management|project planning|pmp|project coordination|release management|roadmap delivery|prince2", "Agile delivery|Stakeholder management|Estimation and planning|Team leadership"],
  ["Product thinking", "product management|product sense|product mindset|roadmapping|product roadmap|product strategy|user-centred thinking|customer-centric thinking|product discovery|product ownership|product owner|okrs", "Stakeholder management|Requirements analysis|Experimentation and A/B testing"],
  ["Data storytelling", "data story telling|insight communication|communicating insights|presenting data|presenting insights|analytics storytelling|executive reporting|reporting to executives|insight storytelling|data communication", "Data visualisation|Communication|Stakeholder management"],
  ["Facilitation", "workshop facilitation|facilitating workshops|running workshops|retrospectives|meeting facilitation|design thinking|design sprints|stakeholder workshops|scrum ceremonies|event storming|requirements workshops", "Communication|Agile delivery|Stakeholder management|Requirements analysis"],
  ["Continuous learning", "self-learning|self learning|quick learner|fast learner|learning agility|lifelong learning|self-taught|adaptability|growth mindset|learning new technologies|upskilling", "Problem solving|Mentoring|Teamwork"],
  ["Estimation and planning", "estimation|story points|sprint estimation|planning poker|capacity planning|delivery planning|effort estimation|timeline planning|backlog refinement|backlog grooming|roadmap planning|task breakdown", "Agile delivery|Project management|Technical leadership"],
  ["Requirements analysis", "business analysis|requirements gathering|requirements elicitation|user stories|acceptance criteria|functional requirements|non-functional requirements|use cases|bpmn|process mapping|process modelling|process modeling|business requirements|brd|functional specifications|gap analysis", "Stakeholder management|Technical documentation|Product thinking|Facilitation|Manual testing"],
];

// ---------- Helpers ----------
const norm = (s) => String(s || "").toLowerCase().trim();
const list = (v) => (Array.isArray(v) ? v : v ? [v] : []);
const escRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

// One letter names count only inside a list ("Python, R, SQL"). Four names that are also common words count only with a capital letter.
// A word that is a part of a longer word never counts: "java" is not in "javascript", and "js" is not in "node.js".
const LIST_ONLY = new Set(["c", "r", "go"]);
const CAPITAL_ONLY = new Set(["swift", "rust", "ruby", "spark"]);
const LEFT = "(?:^|[^a-z0-9.])";
const RIGHT = "(?![a-z0-9])";

const NAME_OF = new Map();   // lower case name or alias -> name (for a text that is the whole skill)
const RELATED = new Map();   // lower case name -> Set of lower case names (both ways)
const FINDERS = [];          // [name, (raw, lower) => index of the first hit, or -1]

const relate = (a, b) => { if (!RELATED.has(a)) RELATED.set(a, new Set()); RELATED.get(a).add(b); };
for (const [name, aliasText, relatedText] of SKILL_TABLE) {
  const key = norm(name);
  const terms = [...new Set([key, ...aliasText.split("|").filter(Boolean).map(norm)])];
  for (const t of terms) NAME_OF.set(t, name);
  for (const r of relatedText.split("|").filter(Boolean).map(norm)) { relate(key, r); relate(r, key); }

  // A short alias ("js", "ml", "k8s") is not searched in a text: it is too easy to find by chance. It still counts when it is the whole text.
  const plain = terms.filter((t) => (t.length >= 3 || /[#+.]/.test(t)) && !CAPITAL_ONLY.has(t) && !LIST_ONLY.has(t)).sort((a, b) => b.length - a.length);
  const capital = terms.filter((t) => CAPITAL_ONLY.has(t));
  const listOnly = terms.filter((t) => LIST_ONLY.has(t));
  const tests = [];
  if (plain.length) {
    const re = new RegExp(`${LEFT}(?:${plain.map(escRe).join("|")})${RIGHT}`, "m");
    tests.push((raw, low) => { const m = re.exec(low); return m ? m.index : -1; });
  }
  for (const t of capital) {
    const re = new RegExp(`(?:^|[^A-Za-z0-9.])(?:${t[0].toUpperCase()}${t.slice(1)}|${t.toUpperCase()})(?![A-Za-z0-9])`, "m");
    tests.push((raw) => { const m = re.exec(raw); return m ? m.index : -1; });
  }
  for (const t of listOnly) {
    const re = new RegExp(`(?:^|[,;:/|•(\\-]\\s*|\\band\\s+|&\\s*)${escRe(t)}(?=\\s*(?:[,;/|•)]|\\band\\b|&\\s|$))`, "m");
    tests.push((raw, low) => { const m = re.exec(low); return m ? m.index : -1; });
  }
  FINDERS.push([name, (raw, low) => tests.reduce((best, f) => { const i = f(raw, low); return i >= 0 && (best < 0 || i < best) ? i : best; }, -1)]);
}

/** The skill names that a text shows, in the order of their first place in the text. */
export function skillsIn(text) {
  const raw = String(text || "");
  const low = raw.toLowerCase();
  const found = [];
  for (const [name, find] of FINDERS) { const i = find(raw, low); if (i >= 0) found.push([i, name]); }
  return found.sort((a, b) => a[0] - b[0]).map(([, name]) => name);
}
/** The taxonomy name of a text that is the whole skill (a name or an alias, any case), or "". "golang" gives "Go". */
export const canonicalSkillName = (text) => NAME_OF.get(norm(text).replace(/\s+/g, " ").replace(/[.,;]+$/, "")) || "";

// Words of a role title. A level word is not part of the role.
const STOP = new Set(["and", "the", "for", "with", "remote", "senior", "junior", "intern", "internship", "graduate", "contract", "mid", "lead", "principal", "staff", "head", "office", "anzsco"]);
// Role nouns that are in many roles. A match on only these words is weak.
const GENERIC = new Set(["engineer", "engineering", "developer", "analyst", "specialist", "architect", "scientist", "administrator", "manager", "officer", "consultant", "executive", "programmer", "designer", "researcher", "tester", "expert"]);
const words = (s) => norm(s).split(/[^a-z0-9+#]+/).filter((w) => w.length > 1 && !STOP.has(w));
const LEVEL_WORDS = /\b(intern(ship)?|junior|jr|graduate|senior|sr|lead|principal|staff|mid[- ]?level|contract)\b/g;
// "Senior Data Engineer, Lakehouse" -> "data engineer"
const rolePhrase = (t) => norm(t).replace(/\([^)]*\)/g, " ").split(/\s[-–—|@]\s|,/)[0].replace(LEVEL_WORDS, " ").replace(/\s+/g, " ").trim();

// ---------- The catalogue ----------
const DAY = 864e5;
export function salaryText(s) {
  if (!s || !s.min) return "Market competitive";
  const money = (n) => `$${Number(n).toLocaleString("en-AU")}`;
  const unit = s.unit === "day" ? "per day" : s.unit === "hour" ? "per hour" : "per year";
  return s.max && s.max !== s.min ? `${money(s.min)} – ${money(s.max)} ${unit}` : `${money(s.min)} ${unit}`;
}
// The short text of a job: the first whole sentences of the description that fit in 200 characters. Headings and bullets are left out.
// The description itself is never cut and keeps its line breaks (the "## Heading" and "- bullet" markup).
function summaryOf(text, max = 200) {
  const flat = String(text || "").split("\n").map((l) => l.trim()).filter((l) => l && !l.startsWith("#") && !/^[-*•]\s/.test(l)).join(" ").replace(/\s+/g, " ");
  if (flat.length <= max) return flat;
  let out = "";
  for (const s of flat.match(/[^.!?]+[.!?]+(?:\s|$)/g) || []) { if ((out + s).trim().length > max) break; out += s; }
  if (out.trim()) return out.trim();
  const cut = flat.slice(0, max);
  return cut.slice(0, cut.lastIndexOf(" ")).replace(/[,.;:]$/, "") + "…";
}

// All job data is Jinder's own data. IDs are internal ("job-<key>", as in the real backend). No links to other sites are kept.
// The new V2 fields (level, years, work mode, skill levels, certifications, awards) are added where the seed has them.
function fromSeed(r) {
  const now = Date.now();
  return {
    id: `job-${r.key}`,
    title: r.title,
    company: r.company,
    category: r.domain,
    specialisation: r.specialisation,
    location: r.city,
    area: r.area,
    type: r.type,
    anzsco: r.occupation.code,
    occupation: r.occupation.title,
    salary: salaryText(r.salary),
    salaryUnit: r.salary.unit,
    postedAt: new Date(now - r.postedDaysAgo * DAY),
    closesAt: new Date(now + r.closesInDays * DAY),
    summary: summaryOf(r.description),
    description: r.description,
    skills: r.skills.map((s) => s.name),
    skillRequirements: r.skills.map((s) => ({ name: s.name, level: s.level, must: s.must })),
    level: r.level,
    minYears: r.minYears,
    maxYears: r.maxYears,
    workMode: r.workMode,
    educationMin: r.educationMin,
    certifications: { required: [...r.certifications.required], preferred: [...r.certifications.preferred] },
    awards: { preferred: [...r.awards.preferred] },
  };
}

const jobs = SEED_JOBS.map(fromSeed);

// The catalogue is embedded, so there is nothing to load. The function stays because the routes wait for it.
export const loadJobs = () => Promise.resolve();

// Jobs that employers post on Jinder (db.postedJobs) join the catalogue. Dates are ISO strings in the db.
function fromPosted(p) {
  const description = String(p.description || "").replace(/\r\n?/g, "\n").trim();
  return { ...p, postedAt: new Date(p.postedAt), closesAt: new Date(p.closesAt), summary: summaryOf(description), description, anzsco: p.anzsco || "", occupation: p.occupation || "" };
}
export const catalogue = (db) => [...jobs, ...((db && db.postedJobs) || []).map(fromPosted)];
export const isOpen = (j) => !j.closesAt || j.closesAt.getTime() >= Date.now();
export const findJob = (db, id) => catalogue(db).find((j) => j.id === id) || null;
export function jobSource(db) {
  const all = catalogue(db);
  const latest = all.reduce((m, j) => (j.postedAt && (!m || j.postedAt > m) ? j.postedAt : m), null);
  return { openCount: all.filter(isOpen).length, updatedAt: latest ? latest.toISOString() : null };
}
// Skill names found in a text (for employers: "Suggest skills from the description")
export const suggestSkills = (text) => skillsIn(text).slice(0, 10);

// ---------- Per-skill match (Feature 3) ----------
// Each required skill of a job is "match", "partial" or "gap", with a reason.
// coverage = (matches + 0.5 × partials) / required skills × 100. It summarises the skills of one job.
// It is not a score on the person (PRD: per-skill matching, no single score on a person).
// Related skills: the candidate has a skill that the taxonomy lists as related → "partial".

// The candidate's skills as names: their own, the taxonomy names that they map to, and accepted translations
function mySkillNames(p) {
  const shared = list(p.translation).filter((s) => (s.status === "accepted" || s.status === "edited") && s.source === "skill").map((s) => s.mapped);
  const names = new Map();
  for (const s of [...list(p.skills).map((x) => (x && typeof x === "object" ? x.name : x)), ...shared].filter(Boolean)) {
    names.set(norm(s), canonicalSkillName(s) || s);
    for (const c of skillsIn(s)) names.set(norm(c), c);
  }
  return names; // key: lower case, value: display name
}
export const namesFromProfile = (p) => mySkillNames(p || {});
// For employers: the skills of a shared profile (already taxonomy names)
export const namesFromList = (skills) => mySkillNames({ skills });

export function skillMatch(jobSkills, names) {
  const items = jobSkills.map((s) => {
    const k = norm(s);
    if (names.has(k)) return { name: s, status: "match", reason: "Has this skill." };
    const group = RELATED.get(k);
    const via = group && [...names.keys()].find((n) => group.has(n));
    if (via) return { name: s, status: "partial", via: names.get(via), reason: `Has ${names.get(via)}, which is related.` };
    return { name: s, status: "gap", reason: "No evidence of this skill yet." };
  });
  const m = items.filter((i) => i.status === "match").length;
  const p = items.filter((i) => i.status === "partial").length;
  return { items, coverage: items.length ? Math.round(((m + 0.5 * p) / items.length) * 100) : null, matched: m, partial: p };
}

// How close a list of roles is to a job: 3 = the same role or the same occupation, 2 = the same field and the same kind of role,
// 1 = the same field only, 0.5 = only a role noun like "engineer", 0 = nothing.
function roleCloseness(roles, job) {
  const jobPhrase = rolePhrase(job.title);
  const occupation = norm(job.occupation);
  const jobWords = words(`${job.title} ${job.occupation || ""}`);
  let best = 0;
  for (const role of roles) {
    const phrase = rolePhrase(role);
    if (!phrase) continue;
    if (phrase === jobPhrase || phrase === occupation || jobPhrase.includes(phrase)) return 3;
    const mine = new Set(words(role));
    const hits = jobWords.filter((w) => mine.has(w));
    const field = hits.some((w) => !GENERIC.has(w)), noun = hits.some((w) => GENERIC.has(w));
    best = Math.max(best, field && noun ? 2 : field ? 1 : noun ? 0.5 : 0);
  }
  return best;
}
const TARGET_POINTS = { 0: 0, 0.5: 8, 1: 14, 2: 22, 3: 30 };
const PAST_POINTS = { 0: 0, 0.5: 4, 1: 8, 2: 13, 3: 18 };
const RECOMMEND_MIN = 45;   // a job with a lower rank is not recommended (it is still in the search)

// Fit to the candidate's goals. Used to rank and to choose recommendations, never shown as a number.
// rank = coverage × 0.4 + target role (up to 30) or past role (up to 18) + domain 15 + location 10 + work type 5 + level (up to 8)
function matcher(profile) {
  const p = profile || {};
  const names = mySkillNames(p);
  const targetRoles = list(p.targetRole);
  const pastRoles = list(p.currentRole);
  const domains = new Set([...list(p.targetIndustries), ...list(p.industry)]);
  const locations = new Set(list(p.locations));
  const types = new Set(list(p.workTypes));
  const myLevel = levelRank(p.level);

  return (job) => {
    const reasons = [];
    const notes = [];
    const target = roleCloseness(targetRoles, job);
    const past = roleCloseness(pastRoles, job);
    const sm = skillMatch(job.skills, names);
    const jobDomains = CATEGORY_MAP[job.category] || [job.category];
    const domainHit = jobDomains.find((d) => domains.has(d));
    const remote = job.location === "Remote" || job.workMode === "Remote";
    const locationHit = locations.has(job.location) || remote;
    const typeHit = types.size === 0 || types.has(job.type);
    const jobLevel = levelRank(job.level);
    const gap = myLevel >= 0 && jobLevel >= 0 ? Math.abs(myLevel - jobLevel) : -1;
    const levelPoints = gap === 0 ? 8 : gap === 1 ? 4 : 0;
    const roleScore = Math.max(TARGET_POINTS[target], PAST_POINTS[past]);
    const rank = Math.round((sm.coverage ?? 0) * 0.4 + roleScore + (domainHit ? 15 : 0) + (locationHit ? 10 : 0) + (typeHit ? 5 : 0) + levelPoints);

    if (target >= 2) reasons.push(job.occupation ? `Matches your target role (ANZSCO: ${job.occupation})` : "Matches your target role");
    else if (past >= 2) reasons.push("Close to a role you have had");
    else if (target || past) reasons.push(`Similar type of role (${job.title})`);
    if (sm.matched) reasons.push(`You have ${sm.matched} of the ${job.skills.length} skills${sm.partial ? `, and ${sm.partial} related` : ""}`);
    if (domainHit) reasons.push(`In a domain you chose: ${domainHit}`);
    if (gap >= 0 && gap <= 1) reasons.push(`Level fits: ${job.level}`);
    if (remote && !locations.has(job.location)) reasons.push("Remote role: you can work from anywhere in Australia");
    else if (locationHit) reasons.push(`Location you prefer: ${job.location}`);
    if (!typeHit) notes.push(`This role is ${job.type}`);
    if (gap >= 2) notes.push(`This role is ${job.level} level`);
    if (locations.size && !locationHit) notes.push(`Location: ${job.location}`);
    if (!job.skills.length) notes.push("This job lists no skills yet");

    return {
      coverage: sm.coverage, skills: sm.items,
      matchedSkills: sm.items.filter((i) => i.status === "match").map((i) => i.name),
      partialSkills: sm.items.filter((i) => i.status === "partial").map((i) => i.name),
      gaps: sm.items.filter((i) => i.status === "gap").map((i) => i.name),
      // A job that is 2 or more levels away from the level of the candidate is not recommended (it is still in the search)
      reasons, notes, rank, recommended: rank >= RECOMMEND_MIN && gap < 2 && (reasons.length > 1 || target >= 2),
    };
  };
}

// The card fields (no full description; no owner or internal fields)
const card = (job, match) => {
  const { description, ownerId, targetApplicants, editedAt, ...rest } = job;
  return { ...rest, status: isOpen(job) ? "open" : "closed", match };
};
const byRank = (a, b) => b.match.rank - a.match.rank || (b.postedAt || 0) - (a.postedAt || 0) || String(a.id).localeCompare(String(b.id));

// Feature 3 AC2: closed, skipped and applied jobs are not recommended
export function recommend(db, profile, limit = 5, exclude = new Set()) {
  if (!profile) return [];
  const m = matcher(profile);
  return catalogue(db).filter((j) => isOpen(j) && !exclude.has(j.id))
    .map((j) => card(j, m(j)))
    .filter((j) => j.match.recommended)
    .sort(byRank)
    .slice(0, limit);
}

// Keyword search over title, company, occupation, domain, specialisation, level and skills. Open jobs that are not skipped.
export function searchJobs(db, profile, { q = "", location = "", limit = 50 } = {}, exclude = new Set()) {
  const terms = norm(q).split(/\s+/).filter(Boolean);
  const m = matcher(profile);
  const hits = catalogue(db).filter((j) => {
    if (!isOpen(j) || exclude.has(j.id)) return false;
    if (location && j.location !== location) return false;
    const hay = norm(`${j.title} ${j.company} ${j.occupation} ${j.category} ${j.specialisation || ""} ${j.level || ""} ${j.skills.join(" ")} ${j.area}`);
    return terms.every((t) => hay.includes(t));
  }).map((j) => card(j, m(j))).sort(byRank);
  return { total: hits.length, items: hits.slice(0, limit) };
}

export function jobDetail(db, profile, id) {
  const job = findJob(db, id);
  if (!job) return null;
  const m = matcher(profile);
  // Similar jobs: same ANZSCO occupation, or 3+ shared skills. Open jobs only.
  const similar = catalogue(db).filter((j) => j.id !== id && isOpen(j) &&
    ((job.anzsco && j.anzsco === job.anzsco) || j.skills.filter((s) => job.skills.includes(s)).length >= 3))
    .map((j) => card(j, m(j))).sort(byRank).slice(0, 3);
  return { ...card(job, m(job)), description: job.description, similar };
}
