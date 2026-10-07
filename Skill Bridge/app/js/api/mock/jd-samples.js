// MOCK BACKEND — sample results for "post a job from a file". The mock cannot read a PDF or DOCX file,
// so it returns one of these made-up job descriptions. The real backend reads the file. The real backend replaces this file.
// All samples are ICT (3 domains only). A description uses the JD markup: "## Heading" lines, "- bullet" lines and plain paragraphs.
// A job description file rarely has a close date or a target number of applicants, so those stay with the employer.
export const JD_SAMPLES = {
  backend: {
    label: "Backend Engineer",
    fields: {
      title: "Backend Engineer, Payments API",
      category: "Software Engineering",
      location: "Sydney",
      type: "Full-time",
      salary: "$130,000 – $150,000 per year",
      description: `## About the role

We are looking for a Backend Engineer to build and run the payments API of our online platform. You will work in a team of six in our Sydney office, with two days at home each week.

## What you will do

- Build and test REST APIs in Python and Django.
- Design PostgreSQL tables and keep the queries fast.
- Review code from other engineers and fix problems in production.
- Add monitoring and alerts for each new service.

## What you bring

- 3 to 6 years of backend work.
- Python and PostgreSQL at an advanced level.
- API design and unit tests for all your code.

## Nice to have

- Docker, Redis or AWS in production.

## Tech stack

Python, Django, PostgreSQL, Redis, Docker and AWS, with Git and CI/CD for all code.`,
    },
    missing: [],
  },
  data: {
    label: "Data Analyst",
    fields: {
      title: "Data Analyst (Contract)",
      category: "Data",
      type: "Contract",
      salary: "$700 per day",
      description: `## About the role

A 6-month contract for a Data Analyst. You will help the product team to make decisions with data.

## What you will do

- Build dashboards in Power BI and share them with business teams.
- Write SQL queries and clean data with Python.
- Explain the results to people who are not data experts.

## What you bring

- 2 to 5 years as a data analyst or a reporting analyst.
- SQL and Power BI at a proficient level.
- Clear written and spoken communication.

## Nice to have

- Data modelling, dbt or Microsoft Excel with large files.

## Tech stack

SQL, Python, Power BI and Microsoft Excel.`,
    },
    missing: ["location"],
  },
  ml: {
    label: "Machine Learning Engineer",
    fields: {
      title: "Machine Learning Engineer, Demand Forecasting",
      category: "AI & Machine Learning",
      location: "Melbourne",
      type: "Full-time",
      description: `## About the role

Join our forecasting team to build and run machine learning models that predict how many orders we will get each week. The team has four engineers and one data scientist.

## What you will do

- Train and compare models in Python with scikit-learn and XGBoost.
- Build features from order and calendar data.
- Track experiments with MLflow and move the best model to production.
- Check each model with clear tests and share the results.

## What you bring

- 2 to 5 years in machine learning or data science.
- Python, machine learning and time series forecasting at an advanced level.
- A habit of writing short notes so that others can repeat your work.

## Nice to have

- Docker, SQL and Git for team work.

## Tech stack

Python, scikit-learn, XGBoost, MLflow, Docker and SQL.`,
    },
    missing: ["salary"],
  },
  devops: {
    label: "DevOps Engineer",
    fields: {
      title: "DevOps Engineer, Cloud Platform",
      category: "Software Engineering",
      location: "Remote",
      type: "Full-time",
      salary: "$140,000 – $160,000 per year",
      description: `## About the role

We run one cloud platform for 12 product teams, and we want a DevOps Engineer to make it faster and safer. This role is fully Remote and open to people anywhere in Australia.

## What you will do

- Build and improve CI/CD pipelines with GitHub Actions.
- Write Terraform code for AWS and keep it tested.
- Run Kubernetes clusters and fix problems at night in turns with the team.
- Add monitoring with Prometheus and Grafana.

## What you bring

- 4 to 8 years of work with Linux, AWS and containers.
- Terraform, Docker and Kubernetes at a proficient level or better.
- Good habits for incident response and for writing runbooks.

## Nice to have

- Python or Go for tools, and an AWS certification.

## Tech stack

AWS, Terraform, Kubernetes, Docker, GitHub Actions, Prometheus and Grafana.`,
    },
    missing: [],
  },
};

// Choose a sample from the file name. "fail" or "corrupt" in the name → the read fails (to test the error path).
export function jdSampleFor(fileName) {
  const n = String(fileName || "").toLowerCase();
  if (/fail|corrupt/.test(n)) return null;
  if (/machine|(^|[^a-z])ml([^a-z]|$)|(^|[^a-z])ai([^a-z]|$)|scientist/.test(n)) return JD_SAMPLES.ml;
  if (/devops|cloud|platform|infra|sre/.test(n)) return JD_SAMPLES.devops;
  if (/data|analyst|bi([^a-z]|$)/.test(n)) return JD_SAMPLES.data;
  return JD_SAMPLES.backend;
}
