// MOCK BACKEND — the embedded ICT job catalogue: 24 of the 50 synthetic jobs of jinder_backend_engine/data/synthetic/jobs.json.
// All jobs and companies are made up. The mock API (jobs.js) reads this list. Keep it the same as prompt.md.
// Each job has: key, title, company, domain (one of the 3 domains), specialisation, level (Intern to Principal), minYears, maxYears,
// type, workMode, city, area, salary { min, max, unit: "year" or "day" }, occupation { code, title } (ANZSCO), skills [{ name, level 1 to 5, must }],
// certifications { required, preferred }, awards { preferred }, educationMin, postedDaysAgo, closesInDays and description.
// The description is never cut. It uses a small markup: a line "## Heading", a line "- bullet", and plain paragraphs.
// postedDaysAgo and closesInDays count from the day when the app starts, so that the jobs are always open.
export const SEED_JOBS = [
  {
    key: "data-eng-senior-02", title: "Senior Data Engineer, Lakehouse", company: "Mallee Mesh",
    domain: "Data", specialisation: "Data engineering", level: "Senior", minYears: 5, maxYears: 9,
    type: "Full-time", workMode: "Remote", city: "Remote", area: "Remote (Australia)",
    salary: { min: 150000, max: 168000, unit: "year" }, occupation: { code: "262111", title: "Data Engineer" },
    skills: [
      { name: "Databricks", level: 4, must: true }, { name: "Apache Spark", level: 4, must: true }, { name: "Data lakehouse", level: 4, must: true },
      { name: "Python", level: 4, must: true }, { name: "SQL", level: 4, must: true }, { name: "Azure Data Factory", level: 3, must: false },
      { name: "Azure", level: 3, must: false }, { name: "Data governance", level: 3, must: false }, { name: "Data modelling", level: 4, must: false },
      { name: "CI/CD", level: 3, must: false }, { name: "Infrastructure as code", level: 2, must: false },
    ],
    certifications: { required: ["Databricks Certified Data Engineer Associate"], preferred: ["Databricks Certified Data Engineer Professional"] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 15, closesInDays: 34,
    description: `## About the role

Mallee Mesh builds a data platform for water utilities and regional councils, and it is moving from a patchwork of databases to one lakehouse on Databricks. The Platform Data team of seven builds the bronze, silver and gold layers, and the rules that keep meter and flow data trustworthy. We need a senior data engineer to set the standards for those layers and to onboard the first six customers. The role is fully Remote and open to people anywhere in Australia.

## What you will do

- Design the lakehouse layers and the naming, testing and release rules for each one.
- Build Spark pipelines in Databricks that handle late and messy meter data.
- Bring in data from customer systems with Azure Data Factory.
- Set up access rules and lineage so that each council sees only its own data.
- Add CI/CD for notebooks and jobs, with tests before each release.
- Help customers' own analysts use the gold tables.
- Review pull requests and guide two mid-level engineers.

## What you bring

- 5 to 9 years in data engineering, with Databricks and Apache Spark at an advanced level (4 of 5).
- Data lakehouse design at an advanced level: layers, partitioning and table formats.
- Python and SQL at an advanced level.
- A good sense of cost: you can predict what a job will cost before you run it.
- A Databricks data engineer certification, as listed below.

## Nice to have

- Azure and Azure Data Factory experience.
- Data modelling at an advanced level, and Data governance at a proficient level.
- CI/CD for data, and a first look at Infrastructure as code with Terraform.

## Tech stack

Databricks and Apache Spark on Azure, Delta tables, Azure Data Factory, Python and SQL, with Terraform for the environments and GitHub for CI/CD.

## Certifications and awards

- Required certification: Databricks Certified Data Engineer Associate.
- Preferred certification: Databricks Certified Data Engineer Professional.

## What we offer

- $150,000 to $168,000 a year, plus 12% superannuation.
- Fully Remote work in Australia, with a team week in Adelaide twice a year.
- $2,000 for your home office and a yearly co-working pass.
- Four weeks of annual leave and a paid winter shutdown week in July.
- Exam fees for Databricks and Azure certifications.

## About Mallee Mesh

Mallee Mesh makes data software for water utilities and regional councils. It was founded in 2017 and has about 85 people who work from many towns and cities. Its customers manage water for more than two million homes.

## How we hire

- A video call with the head of data.
- A talk about a lakehouse or Spark system that you built.
- A design exercise on a late-data problem, with two engineers.
- A decision within a week.`,
  },
  {
    key: "data-science-mid-01", title: "Data Scientist, Product Analytics", company: "Gumnutlabs",
    domain: "Data", specialisation: "Data science", level: "Mid", minYears: 3, maxYears: 6,
    type: "Full-time", workMode: "Remote", city: "Remote", area: "Remote (Australia)",
    salary: { min: 124000, max: 146000, unit: "year" }, occupation: { code: "224115", title: "Data Scientist" },
    skills: [
      { name: "Python", level: 4, must: true }, { name: "Pandas", level: 4, must: true }, { name: "scikit-learn", level: 3, must: true },
      { name: "Statistics", level: 3, must: true }, { name: "SQL", level: 3, must: true }, { name: "Data visualisation", level: 3, must: false },
      { name: "Machine learning", level: 3, must: false }, { name: "Feature engineering", level: 3, must: false },
      { name: "NumPy", level: 3, must: false }, { name: "Git", level: 3, must: false }, { name: "Communication", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["PCAP: Certified Associate in Python Programming"] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 19, closesInDays: 20,
    description: `## About the role

Gumnutlabs makes a language-learning app that about 400,000 people open each week, and the Product Analytics team works out which lessons keep learners coming back. The team of five data scientists and analysts studies behaviour, builds churn and recommendation models and helps product teams run experiments. We want a mid-level data scientist who likes to turn a vague question into a clear answer. This role is fully Remote in Australia.

## What you will do

- Study how learners move through lessons, and find where they drop out.
- Build churn and next-lesson models, and check that they help real learners.
- Help product teams plan and read experiments.
- Prepare data with Pandas and SQL, and keep the notebooks tidy and reusable.
- Share results in short write-ups and a monthly talk.
- Review a colleague's analysis each week.

## What you bring

- 3 to 6 years as a data scientist or analyst who builds models.
- Python and Pandas at an advanced level (4 of 5), with clean, tested code.
- scikit-learn, Statistics and SQL at a proficient level (3 of 5).
- Good judgement: you can say what a result does and does not prove.
- A calm voice in remote meetings and clear writing.

## Nice to have

- Machine learning and Feature engineering for behaviour data.
- NumPy, Data visualisation and Git habits.
- Strong Communication with product managers and designers.

## Tech stack

Python with Pandas, NumPy and scikit-learn, SQL on a cloud data warehouse, Jupyter notebooks, Git and a shared experiment platform.

## Certifications and awards

- Preferred certification: PCAP: Certified Associate in Python Programming.

## What we offer

- $124,000 to $146,000 a year, plus 12% superannuation.
- Remote work from anywhere in Australia, with a team week in Sydney each year.
- A one-off $1,000 for your home desk, plus a monthly internet payment.
- Four weeks of annual leave and a Monday off at the end of each quarter.
- A free subscription for you and your family to the app, in any language.

## About Gumnutlabs

Gumnutlabs builds language-learning apps. It was founded in 2018 and has about 100 people, most of whom work from home. Its data team is one of the oldest teams in the company.

## How we hire

- A video call with the head of data.
- A short analysis task on a sample of learner data, about three hours.
- A talk with two team members about the choices in your analysis.
- An answer within a week.`,
  },
  {
    key: "data-bi-mid-01", title: "Business Intelligence Developer", company: "Blackbutt Relay",
    domain: "Data", specialisation: "Business intelligence", level: "Mid", minYears: 4, maxYears: 8,
    type: "Full-time", workMode: "Onsite", city: "Melbourne", area: "Melbourne VIC",
    salary: { min: 112000, max: 130000, unit: "year" }, occupation: { code: "224114", title: "Data Analyst" },
    skills: [
      { name: "Power BI", level: 4, must: true }, { name: "SQL", level: 4, must: true }, { name: "Data modelling", level: 3, must: true },
      { name: "Microsoft SQL Server", level: 3, must: true }, { name: "Data visualisation", level: 4, must: true },
      { name: "Data warehousing", level: 3, must: false }, { name: "Microsoft Excel", level: 3, must: false },
      { name: "Requirements analysis", level: 3, must: false }, { name: "Stakeholder management", level: 3, must: false },
      { name: "Data quality", level: 3, must: false },
    ],
    certifications: { required: ["Microsoft Certified: Power BI Data Analyst Associate"], preferred: [] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 13, closesInDays: 24,
    description: `## About the role

Blackbutt Relay makes payroll and workforce software, and its customers' managers use the reporting pages to see hours, costs and leave. The BI team of five builds the reports for 2,000 employers on Power BI and SQL Server, and it needs a mid-level developer to rebuild the oldest reports. You will work Onsite in our Melbourne office, next to the product and support teams who know what customers ask for. Most of your reports will be used by people who are not data experts.

## What you will do

- Rebuild the 40 oldest customer reports in Power BI with clean models and fast queries.
- Write SQL Server queries and views that feed the reports.
- Design star-schema models that make new reports quick to build.
- Sit with customers' managers to learn what they need to see, and then simplify the page.
- Check the numbers against payroll results and fix differences.
- Document each report for the support team.

## What you bring

- 4 to 8 years in business intelligence or reporting.
- Power BI and Data visualisation at an advanced level (4 of 5): clear pages, good filters and quick refreshes.
- SQL at an advanced level, and Microsoft SQL Server at a proficient level (3 of 5).
- Data modelling at a proficient level, with star schemas and clean keys.
- A current Power BI Data Analyst certification, as listed below.
- Calm, helpful Stakeholder management when a manager says that a number is wrong.

## Nice to have

- Data warehousing and Microsoft Excel depth.
- Requirements analysis and workshop skills.
- Data quality habits, such as reconciliation checks for money.

## Tech stack

Power BI, SQL Server with views and stored procedures, a small data warehouse and Microsoft Excel exports for some customers.

## Certifications and awards

- Required certification: Microsoft Certified: Power BI Data Analyst Associate.

## What we offer

- $112,000 to $130,000 a year, plus 12% superannuation.
- Onsite work in our Melbourne office, five days a week, with a central location.
- Four weeks of annual leave and a day off for your birthday.
- Exam fees and study days for Microsoft certifications.
- A team lunch each fortnight.

## About Blackbutt Relay

Blackbutt Relay builds payroll, rostering and workforce reporting software for employers. It was founded in 2010 and has about 190 people in Melbourne. Its customers range from cafes to hospital groups.

## How we hire

- A short call with the BI lead.
- A Power BI exercise that you do in the office, about two hours.
- A chat with the product manager and a support lead.
- An answer within five working days.`,
  },
  {
    key: "data-analytics-mid-01", title: "Data Analyst, Growth", company: "Stringybark Data",
    domain: "Data", specialisation: "Data analytics", level: "Mid", minYears: 2, maxYears: 5,
    type: "Full-time", workMode: "Hybrid", city: "Melbourne", area: "Melbourne VIC",
    salary: { min: 108000, max: 126000, unit: "year" }, occupation: { code: "224114", title: "Data Analyst" },
    skills: [
      { name: "SQL", level: 4, must: true }, { name: "Data analysis", level: 4, must: true }, { name: "Data visualisation", level: 4, must: true },
      { name: "Power BI", level: 3, must: true }, { name: "Microsoft Excel", level: 4, must: false }, { name: "Python", level: 2, must: false },
      { name: "Apache Airflow", level: 1, must: false }, { name: "ETL and ELT pipelines", level: 2, must: false },
      { name: "Data quality", level: 3, must: false }, { name: "Stakeholder management", level: 3, must: false },
      { name: "Data storytelling", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["Microsoft Certified: Power BI Data Analyst Associate"] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 18, closesInDays: 38,
    description: `## About the role

Stringybark Data makes booking and membership software for fitness studios, and the Growth team uses data to find out why members join, stay or leave. The team of five analysts and one engineer needs a mid-level data analyst who is strong in SQL and who wants to grow toward data engineering. You will spend most of your time on analysis and dashboards, and some of it building the pipelines behind them, with a data engineer as your coach. You will work in Melbourne on a Hybrid schedule.

## What you will do

- Answer questions such as why trial members do not join, using SQL and clear charts.
- Build and own the Power BI dashboards for the Growth and Studio Success teams.
- Run a monthly review of membership trends with the studio owners' success managers.
- Check the quality of the data behind your reports and report problems at the source.
- Build one new pipeline each quarter with the data engineer, step by step.
- Tell the story of each analysis in a short note that a studio owner can read in two minutes.

## What you bring

- 2 to 5 years as a data or business analyst.
- SQL and Data analysis at an advanced level (4 of 5): window functions, cohorts and funnels.
- Data visualisation at an advanced level, and Power BI at a proficient level (3 of 5).
- Curiosity about data engineering: you want to learn how the tables get built.
- Good habits with stakeholders: you ask what decision a number will support.

## Nice to have

- Python, ETL and ELT pipelines and Apache Airflow at a beginner level (1 to 2 of 5). This is the skill that we will help you grow.
- Microsoft Excel at an advanced level and Data quality habits.
- Data storytelling and Stakeholder management with non-technical people.

## Tech stack

SQL on a cloud data warehouse, Power BI and Microsoft Excel for reporting, a little Python, and Apache Airflow for the pipelines that the data engineer owns. Your first pipeline will be small.

## Certifications and awards

- Preferred certification: Microsoft Certified: Power BI Data Analyst Associate.

## What we offer

- $108,000 to $126,000 a year, plus 12% superannuation.
- Hybrid work: two days a week in our Melbourne office and three at home.
- Four weeks of annual leave and the Friday before Easter as a bonus day.
- A clear path to a data engineer role, with a learning plan and a coach.
- A $2,000 yearly budget for courses and exam fees.

## About Stringybark Data

Stringybark Data builds booking, payment and membership software for fitness studios. It was founded in 2016 and has about 130 people in Melbourne. Its analysts sit next to the product teams.

## How we hire

- A 30-minute call with the analytics lead about your recent analyses.
- A SQL and chart exercise that you do at home in about two hours.
- A talk with the analysts and the data engineer about your work.
- An answer within a week.`,
  },
  {
    key: "data-eng-junior-01", title: "Junior Data Engineer, Farm Data", company: "Saltbushworks",
    domain: "Data", specialisation: "Data engineering", level: "Junior", minYears: 0, maxYears: 2,
    type: "Full-time", workMode: "Onsite", city: "Brisbane", area: "Brisbane QLD",
    salary: { min: 90000, max: 104000, unit: "year" }, occupation: { code: "262111", title: "Data Engineer" },
    skills: [
      { name: "SQL", level: 3, must: true }, { name: "Python", level: 3, must: true }, { name: "ETL and ELT pipelines", level: 2, must: true },
      { name: "Git", level: 2, must: false }, { name: "Apache Airflow", level: 2, must: false }, { name: "Microsoft Excel", level: 2, must: false },
      { name: "Data quality", level: 2, must: false }, { name: "PostgreSQL", level: 2, must: false },
      { name: "Data modelling", level: 2, must: false }, { name: "Communication", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["AWS Certified Cloud Practitioner"] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 11, closesInDays: 37,
    description: `## About the role

Saltbushworks collects sensor and drone data from thousands of paddocks, and the Farm Data team turns it into tables that agronomists and apps can trust. The team of four wants a junior data engineer, and it welcomes an analyst who knows SQL and Microsoft Excel and wants to start building pipelines. You will learn how data moves from a soil probe to a farm dashboard and take over one pipeline in your first six months. This is an Onsite role in Brisbane.

## What you will do

- Run and watch the daily pipelines that load sensor readings into PostgreSQL.
- Write SQL to answer questions from agronomists, then turn the best ones into saved tables.
- Fix small pipeline bugs with a senior engineer, and write down what you learned.
- Add simple data quality checks, such as a soil reading that is out of range.
- Move one spreadsheet process into a scheduled pipeline.
- Share your results in the weekly team meeting.

## What you bring

- 0 to 2 years of experience in data work, or a degree project with a real data set.
- SQL at a proficient level (3 of 5): joins, grouping and window functions.
- Python at a proficient level (3 of 5), for scripts that read, clean and write data.
- A first look at ETL and ELT pipelines (2 of 5): you know the idea of extract, transform and load.
- Care for details and a wish to ask why a number looks odd.

## Nice to have

- Apache Airflow, PostgreSQL or Data modelling from a course or a project.
- Microsoft Excel skill, which helps you talk with agronomists.
- Git basics, Data quality curiosity and clear Communication.

## Tech stack

Python and SQL, PostgreSQL, Apache Airflow for scheduling and Git. Raw files sit in AWS cloud storage, and a small dashboard tool shows results to farm staff.

## Certifications and awards

- Preferred certification: AWS Certified Cloud Practitioner.

## What we offer

- $90,000 to $104,000 a year, plus 12% superannuation.
- Onsite work in our Brisbane office, five days a week.
- Four weeks of annual leave and paid time to attend one industry meetup each month.
- A mentor, a learning plan and a review every quarter.
- A farm visit each year to see where the data comes from.

## About Saltbushworks

Saltbushworks builds sensors, drone imaging and apps for farms. It was founded in 2019 and has about 90 people, with a head office in Brisbane and a field team in regional Queensland. Its customers grow grain, cotton and fruit.

## How we hire

- A short call with the data team lead.
- A small SQL and Python exercise in the office.
- A chat with two teammates about what you want to learn first.
- A reply within a week, with feedback that you can use even if the answer is no.`,
  },
  {
    key: "data-eng-mid-02", title: "Contract Data Engineer, Fabric Migration", company: "Banksiapath",
    domain: "Data", specialisation: "Data engineering", level: "Mid", minYears: 3, maxYears: 8,
    type: "Contract", workMode: "Hybrid", city: "Sydney", area: "Sydney NSW",
    salary: { min: 720, max: 800, unit: "day" }, occupation: { code: "262111", title: "Data Engineer" },
    skills: [
      { name: "Microsoft Fabric", level: 4, must: true }, { name: "Azure Data Factory", level: 4, must: true }, { name: "SQL", level: 4, must: true },
      { name: "Python", level: 3, must: true }, { name: "Data warehousing", level: 3, must: true },
      { name: "ETL and ELT pipelines", level: 4, must: false }, { name: "Power BI", level: 3, must: false }, { name: "Azure", level: 3, must: false },
      { name: "Git", level: 3, must: false }, { name: "Data modelling", level: 3, must: false },
    ],
    certifications: { required: ["Microsoft Certified: Fabric Data Engineer Associate"], preferred: [] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 2, closesInDays: 13,
    description: `## About the role

A mid-size insurer has asked Banksiapath to move its reporting from an old SQL Server data warehouse to Microsoft Fabric. You will join a team of five as the mid-level engineer on a five-month contract to rebuild 60 pipelines in Azure Data Factory and Fabric, check that the numbers match and retire the old servers. The client is friendly, the scope is clear and the end date is fixed. This is a Hybrid contract in Sydney.

## What you will do

- Rebuild the claims and policy pipelines in Microsoft Fabric and Azure Data Factory.
- Move the data warehouse tables and write SQL that returns the same results as the old system.
- Write comparison checks that prove each migrated table matches.
- Connect the new tables to the Power BI reports that the business uses.
- Keep a clear log of each pipeline: status, owner and test result.
- Hand over to the client's team with short guides and a recorded demo.

## What you bring

- 3 to 8 years in data engineering, with Microsoft Fabric and Azure Data Factory at an advanced level (4 of 5).
- SQL at an advanced level and Python at a proficient level (3 of 5).
- Data warehousing at a proficient level, and ETL and ELT pipelines experience from at least one migration.
- A current Fabric data engineer certification, as listed below.
- Clear daily notes: you tell the team what you finished and what is blocked.

## Nice to have

- Power BI and Azure skills.
- Data modelling and Git habits for a shared workspace.
- A past data warehouse migration that finished on time.

## Tech stack

Microsoft Fabric, Azure Data Factory, SQL Server as the old source, Power BI for reports, Python for checks and Git for code.

## Certifications and awards

- Required certification: Microsoft Certified: Fabric Data Engineer Associate.

## What we offer

- A day rate of $720 to $800, paid through your company or an agency.
- A five-month contract, with a possible extension.
- Hybrid work: three days a week on the client site in Sydney and two at home.
- A friendly client with a clear plan.
- Fast onboarding: access is ready on your first day.

## About Banksiapath

Banksiapath is a data migration and reporting consultancy. It was founded in 2015 and has about 60 people in Sydney. Contractors and staff work in the same teams.

## How we hire

- A 30-minute call about the project and your dates.
- A technical chat on Fabric, Data Factory and SQL.
- An answer within two working days of the call.`,
  },
  {
    key: "data-analytics-junior-01", title: "Junior Data Analyst, Operations", company: "Pinkgum Analytics",
    domain: "Data", specialisation: "Data analytics", level: "Junior", minYears: 1, maxYears: 2,
    type: "Full-time", workMode: "Hybrid", city: "Perth", area: "Perth WA",
    salary: { min: 76000, max: 88000, unit: "year" }, occupation: { code: "224114", title: "Data Analyst" },
    skills: [
      { name: "Microsoft Excel", level: 3, must: true }, { name: "SQL", level: 3, must: true }, { name: "Data analysis", level: 3, must: true },
      { name: "Data visualisation", level: 3, must: true }, { name: "Tableau", level: 2, must: false }, { name: "Statistics", level: 2, must: false },
      { name: "Communication", level: 3, must: false }, { name: "Data quality", level: 2, must: false }, { name: "Teamwork", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["Tableau Certified Data Analyst"] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 21, closesInDays: 25,
    description: `## About the role

Pinkgum Analytics helps ports, rail operators and haulage companies in Western Australia see where their time and money go. The Operations Insights team of eight turns messy logs and spreadsheets into reports that planners use each morning. We are hiring a junior data analyst who is good with spreadsheets and wants to get strong in SQL and dashboards. This is a Hybrid role in Perth, with three days in the office and two at home.

## What you will do

- Build and refresh the daily reports on truck turnaround, queue times and rail delays.
- Write SQL queries that join messy gate, weighbridge and rail data.
- Clean spreadsheets that customers send, and flag the odd rows to the sender.
- Make charts and simple dashboards in Tableau, with help from a senior analyst.
- Present one finding each month to a customer planning team.
- Write down your steps so that anyone can repeat your analysis.

## What you bring

- 1 to 2 years in an analyst role, or a degree with a strong data project.
- Microsoft Excel at a proficient level (3 of 5): lookups, pivot tables and clean formulas.
- SQL and Data analysis at a proficient level (3 of 5): you can answer a question with a query and explain the result.
- Data visualisation at a proficient level, with charts that are simple and honest.
- Teamwork: you ask questions and you share your drafts early.

## Nice to have

- Tableau practice from a course or a job, and basic Statistics.
- Data quality instincts: you notice when a number is too good.
- Clear Communication with people who work in trucks and on rail lines.

## Tech stack

SQL on a cloud database, Microsoft Excel, Tableau for dashboards, and shared drives for the customer files. We are slowly moving the manual steps to scheduled jobs.

## Certifications and awards

- Preferred certification: Tableau Certified Data Analyst.

## What we offer

- $76,000 to $88,000 a year, plus 12% superannuation.
- Hybrid work: three days a week in our Perth office and two at home.
- Four weeks of annual leave, with no need to explain a sick day.
- A senior analyst as your coach, with a check-in each week.
- Support for the Tableau exam and for evening courses.

## About Pinkgum Analytics

Pinkgum Analytics makes operations reports and planning tools for the resources and transport industries. It was founded in 2019 and has about 40 people in Perth. Its analysts work close to the customers.

## How we hire

- A short call to hear what you enjoy about data.
- A spreadsheet and SQL exercise of about 90 minutes.
- A friendly chat with two analysts.
- We reply within a week and we always give feedback.`,
  },
  {
    key: "data-analytics-intern-01", title: "Data Analyst Intern, Summer Program", company: "Coolibah Ridge Software",
    domain: "Data", specialisation: "Data analytics", level: "Intern", minYears: 0, maxYears: 1,
    type: "Graduate / Internship", workMode: "Onsite", city: "Sydney", area: "Sydney NSW",
    salary: { min: 58000, max: 68000, unit: "year" }, occupation: { code: "224114", title: "Data Analyst" },
    skills: [
      { name: "Microsoft Excel", level: 3, must: true }, { name: "SQL", level: 2, must: true }, { name: "Data visualisation", level: 2, must: true },
      { name: "Communication", level: 3, must: true }, { name: "Data analysis", level: 2, must: false }, { name: "Power BI", level: 1, must: false },
      { name: "Continuous learning", level: 3, must: false }, { name: "Teamwork", level: 3, must: false }, { name: "Python", level: 1, must: false },
    ],
    certifications: { required: [], preferred: ["Microsoft Certified: Azure Fundamentals"] }, awards: { preferred: ["scholarship"] },
    educationMin: "Diploma", postedDaysAgo: 16, closesInDays: 38,
    description: `## About the role

Coolibah Ridge Software makes grants and reporting software for councils and community groups, and each summer it takes four interns for ten weeks. The data analyst intern joins the Insights team to help answer questions such as which community programs reach the most people. You will work on real data sets, build your first dashboards and present them to the whole company in the last week. This is an Onsite internship in our Sydney office, five days a week.

## What you will do

- Clean and combine program data from spreadsheets and databases.
- Write simple SQL queries to answer questions from the Insights team.
- Build a first dashboard on program reach and share it with a council customer.
- Check numbers with a buddy before you share them.
- Present your project to the company in the final week.

## What you bring

- 0 to 1 years of work experience. You are studying for a diploma or a degree in IT, business, maths or a related field.
- Microsoft Excel at a proficient level (3 of 5), including pivot tables.
- SQL and Data visualisation at a working level (2 of 5).
- Friendly, clear Communication, in writing and in person.
- A wish to learn fast and to ask when you are unsure.

## Nice to have

- Data analysis projects from your course, a club or a volunteer job.
- A first look at Power BI or Python.
- Continuous learning habits and good Teamwork.

## Tech stack

Microsoft Excel, SQL on a cloud database and Power BI for dashboards. A little Python is used for data cleaning.

## Certifications and awards

- Preferred certification: Microsoft Certified: Azure Fundamentals.
- Preferred award kind: Scholarship.

## What we offer

- $58,000 to $68,000 a year pro rata, which is paid for the ten weeks of the program, plus 12% superannuation.
- Onsite work in our Sydney office, five days a week, with a desk, a laptop and a buddy.
- A weekly lunch with leaders from different parts of the company.
- A reference letter and a chance to apply for our graduate program.
- Free fruit and coffee, and a short walk from the station.

## About Coolibah Ridge Software

Coolibah Ridge Software builds grants, reporting and community program software for councils and community groups. It was founded in 2014 and has about 70 people in Sydney. It takes four summer interns each year.

## How we hire

- A short online form about your course.
- A 20-minute call with the Insights lead.
- A small Excel task that we do together.
- An answer by the end of the following week, so that you can plan your holidays.`,
  },
  {
    key: "data-ba-mid-01", title: "Business Analyst (Contract), Digital Services", company: "Mulgawire Technologies",
    domain: "Data", specialisation: "Business analysis", level: "Mid", minYears: 4, maxYears: 9,
    type: "Contract", workMode: "Onsite", city: "Canberra", area: "Canberra ACT",
    salary: { min: 680, max: 750, unit: "day" }, occupation: { code: "261111", title: "ICT Business Analyst" },
    skills: [
      { name: "Requirements analysis", level: 4, must: true }, { name: "Stakeholder management", level: 4, must: true },
      { name: "SQL", level: 3, must: true }, { name: "Data analysis", level: 3, must: true },
      { name: "Technical documentation", level: 4, must: true }, { name: "Data visualisation", level: 3, must: false },
      { name: "Microsoft Excel", level: 4, must: false }, { name: "Facilitation", level: 4, must: false },
      { name: "Agile delivery", level: 3, must: false }, { name: "Project management", level: 3, must: false },
      { name: "Data modelling", level: 2, must: false },
    ],
    certifications: { required: ["Professional Scrum Master I"], preferred: [] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 12, closesInDays: 15,
    description: `## About the role

A state agency has asked Mulgawire Technologies to improve its online licence renewal service, and the project needs a business analyst for a six-month contract. As a mid-level analyst, you will run workshops with agency staff, write the requirements for new features and use data from the current service to show where people get stuck. The delivery team of ten works in short sprints with a product owner from the agency. This is an Onsite contract in Canberra.

## What you will do

- Run workshops with agency staff and turn their ideas into clear requirements.
- Write user stories and acceptance criteria that developers and testers can use.
- Query the service data in SQL to find where applicants leave the renewal form.
- Show the findings in simple charts and in a short report for the steering group.
- Keep the backlog in order with the product owner and join the sprint ceremonies.
- Write the process and data documents that the agency needs for its records.

## What you bring

- 4 to 9 years as a business analyst on software or digital projects.
- Requirements analysis and Stakeholder management at an advanced level (4 of 5).
- SQL and Data analysis at a proficient level (3 of 5), to check your ideas against real data.
- Technical documentation at an advanced level: process maps, data dictionaries and clear specifications.
- A current Professional Scrum Master I certificate, as listed below.
- Availability for Onsite work in Canberra, five days a week.

## Nice to have

- Facilitation of workshops with many voices.
- Agile delivery and Project management experience on public sector projects.
- Data visualisation, Microsoft Excel and a first view of Data modelling.

## Tech stack

SQL on the agency's reporting database, Microsoft Excel and a work tracking tool for the backlog. Charts are made in Power BI or in Excel.

## Certifications and awards

- Required certification: Professional Scrum Master I.

## What we offer

- A day rate of $680 to $750, paid through your company or an agency.
- Onsite work at our Canberra office and at the agency, with parking or a transport pass.
- A six-month contract, with a likely extension.
- A clear project, an engaged product owner and no weekend work.

## About Mulgawire Technologies

Mulgawire Technologies delivers IT services for federal and state agencies. It was founded in 2009 and has about 400 people, with its head office in Canberra. Most of its projects run for several years.

## How we hire

- A 30-minute call about the contract and your availability.
- A conversation about two projects where you were the analyst.
- An answer within three working days.`,
  },
  {
    key: "swe-platform-mid-01", title: "DevOps Engineer, Client Delivery", company: "Tallowbridge Cloud",
    domain: "Software Engineering", specialisation: "Platform and DevOps", level: "Mid", minYears: 3, maxYears: 5,
    type: "Full-time", workMode: "Onsite", city: "Melbourne", area: "Melbourne VIC",
    salary: { min: 122000, max: 140000, unit: "year" }, occupation: { code: "261316", title: "DevOps Engineer" },
    skills: [
      { name: "Azure", level: 4, must: true }, { name: "Azure DevOps", level: 4, must: true }, { name: "Terraform", level: 3, must: true },
      { name: "Docker", level: 3, must: true }, { name: "CI/CD", level: 4, must: true }, { name: "Kubernetes", level: 3, must: false },
      { name: "PowerShell", level: 3, must: false }, { name: "Linux", level: 3, must: false }, { name: "Shell scripting", level: 3, must: false },
      { name: "Cloud security", level: 3, must: false },
    ],
    certifications: { required: ["HashiCorp Certified: Terraform Associate"], preferred: ["Microsoft Certified: DevOps Engineer Expert"] }, awards: { preferred: [] },
    educationMin: "Diploma", postedDaysAgo: 13, closesInDays: 24,
    description: `## About the role

Tallowbridge Cloud helps banks, utilities and councils move their systems to the cloud, and the Client Delivery team builds the pipelines and environments for each project. This mid-level role puts you on two or three client projects at a time, mostly on Azure, with a lead who reviews your designs. Each project has a new setup, so the work stays fresh. This is an Onsite role in our Melbourne office, with client site visits when needed.

## What you will do

- Build Azure environments with Terraform that pass the client's security review.
- Set up Azure DevOps pipelines that build, test and deploy applications in one flow.
- Package applications in Docker and deploy them to Kubernetes or to app services.
- Write PowerShell and shell scripts that remove manual steps for the client's staff.
- Check cloud security settings and fix the findings that you can.
- Hand each project over with clear diagrams and a short training session.

## What you bring

- 3 to 5 years of DevOps or cloud work, with a diploma or a degree in IT, or equal experience.
- Azure and Azure DevOps at an advanced level (4 of 5).
- CI/CD at an advanced level: you design pipelines, not just edit them.
- Terraform and Docker at a proficient level (3 of 5).
- A Terraform certification, as listed below.
- Easy, clear conversation with client engineers who know their systems better than you.

## Nice to have

- Kubernetes at a proficient level.
- PowerShell, Linux and Shell scripting skills.
- Cloud security knowledge, such as network rules, identity and secret storage.

## Tech stack

Azure with Azure DevOps, Terraform, Docker, Kubernetes on Azure, PowerShell and Linux. Some clients also use AWS.

## Certifications and awards

- Required certification: HashiCorp Certified: Terraform Associate.
- Preferred certification: Microsoft Certified: DevOps Engineer Expert.

## What we offer

- $122,000 to $140,000 a year, plus 12% superannuation.
- Onsite work in our Melbourne office, five days a week, with a travel allowance for client sites.
- Four weeks of annual leave and one paid day each year to volunteer for a cause that you choose.
- Exam fees and study days for Azure and Terraform certifications.
- A lead who spends time on your growth plan.

## About Tallowbridge Cloud

Tallowbridge Cloud is a cloud consultancy for banks, utilities and councils. It was founded in 2013 and has about 200 people in Sydney and Melbourne. Its engineers move between client projects every few months.

## How we hire

- A 30-minute call about your projects.
- A technical interview on pipelines and Terraform.
- A conversation with the delivery lead.
- An offer within five working days.`,
  },
  {
    key: "swe-backend-lead-01", title: "Lead Backend Engineer, Streaming Services", company: "Bunyipstream",
    domain: "Software Engineering", specialisation: "Backend", level: "Lead", minYears: 8, maxYears: 14,
    type: "Full-time", workMode: "Hybrid", city: "Melbourne", area: "Melbourne VIC",
    salary: { min: 190000, max: 215000, unit: "year" }, occupation: { code: "261313", title: "Software Engineer" },
    skills: [
      { name: "Kotlin", level: 4, must: true }, { name: "Microservices architecture", level: 5, must: true },
      { name: "System design", level: 5, must: true }, { name: "Technical leadership", level: 4, must: true },
      { name: "Team leadership", level: 4, must: true }, { name: "AWS", level: 4, must: true }, { name: "Amazon DynamoDB", level: 3, must: false },
      { name: "Apache Kafka", level: 3, must: false }, { name: "Observability", level: 4, must: false }, { name: "Mentoring", level: 4, must: false },
      { name: "Estimation and planning", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["AWS Certified Solutions Architect - Associate"] }, awards: { preferred: ["employer-recognition"] },
    educationMin: "Bachelor's degree", postedDaysAgo: 17, closesInDays: 14,
    description: `## About the role

During a grand final, Bunyipstream sends live video to more than 400,000 viewers at once, and the backend must not blink. The Streaming Services group owns the session, entitlement and playback-start services, written in Kotlin on AWS. We are looking for a lead engineer to run a team of six, set its technical direction and keep the services calm on the loudest weekends of the year. The role is Hybrid and based in Melbourne.

## What you will do

- Lead six engineers: plan the quarter, split the work and clear the blockers.
- Set the design of the playback-start path so that it stays fast when traffic jumps tenfold.
- Decide where to cut services apart and where to keep them together.
- Review the designs of other teams that depend on your services.
- Run the pre-event checklist and lead the calm, blame-free review afterwards.
- Grow two senior engineers toward lead roles.
- Agree budgets and risks with the head of platform every month.

## What you bring

- 8 to 14 years of backend work, with Kotlin at an advanced level (4 of 5).
- Expert Microservices architecture and System design skills (5 of 5), proved by systems that survived real peaks.
- Technical leadership at an advanced level: other teams ask you for design advice.
- Team leadership at an advanced level: you have managed or led a team of five or more.
- AWS at an advanced level (4 of 5), including cost and failure planning.
- Calm communication with product managers and executives.

## Nice to have

- Amazon DynamoDB and Apache Kafka at a proficient level.
- Strong Observability practice: service levels, alerts that matter and clear dashboards.
- Hands-on Estimation and planning with an agile team, and Mentoring that people thank you for.

## Tech stack

Kotlin on the JVM, AWS with Amazon DynamoDB and Apache Kafka, containers on AWS Fargate and a shared Observability stack built on OpenTelemetry.

## Certifications and awards

- Preferred certification: AWS Certified Solutions Architect - Associate.
- Preferred award kind: Employer recognition.

## What we offer

- $190,000 to $215,000 a year, plus 12% superannuation.
- Hybrid work: two days a week in our Melbourne office, with a quiet room for calls.
- Five weeks of annual leave and a recovery day after each major live event.
- Free season passes to the sport that we stream.
- A $4,000 yearly budget for leadership courses and conferences.

## About Bunyipstream

Bunyipstream streams live sport and events to browsers, phones and television apps. It was founded in 2015 and has about 180 people in Melbourne. Its engineers are on call for the events that they build.

## How we hire

- A conversation with the head of platform about the team and its goals.
- A design review of a real streaming problem, with two engineers.
- A leadership session with the product lead and one of your future reports.
- A decision within a week of the leadership session.`,
  },
  {
    key: "swe-architect-principal-01", title: "Principal Solutions Architect, Cloud Practice", company: "Tallowbridge Cloud",
    domain: "Software Engineering", specialisation: "Software architecture", level: "Principal", minYears: 12, maxYears: null,
    type: "Full-time", workMode: "Hybrid", city: "Sydney", area: "Sydney NSW",
    salary: { min: 225000, max: 255000, unit: "year" }, occupation: { code: "261112", title: "Solutions Architect" },
    skills: [
      { name: "System design", level: 5, must: true }, { name: "Microservices architecture", level: 5, must: true },
      { name: "API design", level: 5, must: true }, { name: "AWS", level: 5, must: true }, { name: "Technical leadership", level: 5, must: true },
      { name: "Stakeholder management", level: 5, must: true }, { name: "Authentication and authorisation", level: 4, must: false },
      { name: "Cloud security", level: 4, must: false }, { name: "Database design and tuning", level: 4, must: false },
      { name: "Networking fundamentals", level: 3, must: false }, { name: "Communication", level: 5, must: false },
      { name: "Estimation and planning", level: 4, must: false },
    ],
    certifications: { required: ["AWS Certified Solutions Architect - Associate"], preferred: ["AWS Certified Security - Specialty"] }, awards: { preferred: ["conference-talk", "security-competition"] },
    educationMin: "Bachelor's degree", postedDaysAgo: 5, closesInDays: 44,
    description: `## About the role

Tallowbridge Cloud designs cloud systems for banks, utilities and councils, and its biggest projects run for years and cost millions. The Principal Solutions Architect shapes the technical design of those projects, signs off the key decisions and speaks for the practice in front of clients. You will mentor eight architects, review designs across the whole practice and be the person who says where a design will hurt in two years. This is a Hybrid role based in Sydney, with client travel.

## What you will do

- Own the target design of three large client programs and keep it simple.
- Run design reviews for every major project and write clear decisions.
- Join sales talks to explain the approach, the risks and the cost in plain words.
- Set patterns for Microservices architecture, API design and data design across the practice.
- Mentor architects and lead engineers, and help them grow into the next level.
- Work with the security team on identity, network and data rules for regulated clients.
- Write papers and give talks that show the practice's thinking.

## What you bring

- 12 or more years in software and cloud work, with at least five years as an architect of large systems.
- System design, Microservices architecture and API design at an expert level (5 of 5).
- AWS at an expert level, from landing zones to data and messaging services.
- Technical leadership that other architects follow without being told.
- Stakeholder management at an expert level (5 of 5): you can calm an angry steering committee.
- The AWS Solutions Architect certification, as listed below.

## Nice to have

- Authentication and authorisation, Cloud security and Networking fundamentals at a deep level.
- Database design and tuning for very large systems.
- Strong Communication and Estimation and planning skills for client proposals.

## Tech stack

AWS as the main platform, with Azure for some clients. Typical designs use microservices on Kubernetes, event streaming, managed databases and infrastructure as code.

## Certifications and awards

- Required certification: AWS Certified Solutions Architect - Associate.
- Preferred certification: AWS Certified Security - Specialty.
- Awards we value: Conference talk or paper and Security competition or bug bounty. They are preferred, not required.

## What we offer

- $225,000 to $255,000 a year, plus 12% superannuation.
- Hybrid work: two days a week in our Sydney office, and the rest at home or with clients.
- Five weeks of annual leave and a paid sabbatical week after three years.
- A $5,000 yearly budget for conferences, writing and courses.
- A share in the practice bonus pool.

## About Tallowbridge Cloud

Tallowbridge Cloud is a cloud consultancy for banks, utilities and councils. It was founded in 2013 and has about 200 people in Sydney and Melbourne. Architects sit in the centre of its projects, not at the edge.

## How we hire

- A conversation with the head of the practice.
- A review of a design that you led, which you present to three architects.
- A panel on how you work with clients and with engineers.
- A decision within a week of the panel.`,
  },
  {
    key: "swe-platform-lead-01", title: "Lead Site Reliability Engineer (Contract)", company: "Numbatforge",
    domain: "Software Engineering", specialisation: "Platform and DevOps", level: "Lead", minYears: 9, maxYears: 14,
    type: "Contract", workMode: "Remote", city: "Remote", area: "Remote (Australia)",
    salary: { min: 1080, max: 1200, unit: "day" }, occupation: { code: "261316", title: "DevOps Engineer" },
    skills: [
      { name: "Site reliability engineering", level: 5, must: true }, { name: "Kubernetes", level: 4, must: true },
      { name: "Observability", level: 5, must: true }, { name: "Incident response", level: 5, must: true },
      { name: "Terraform", level: 4, must: true }, { name: "Technical leadership", level: 4, must: true }, { name: "Linux", level: 4, must: false },
      { name: "Go", level: 3, must: false }, { name: "Prometheus", level: 4, must: false }, { name: "Grafana", level: 3, must: false },
      { name: "Mentoring", level: 4, must: false },
    ],
    certifications: { required: ["AWS Certified DevOps Engineer - Professional"], preferred: [] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 10, closesInDays: 9,
    description: `## About the role

Numbatforge hosts build pipelines for thousands of software teams, and an outage stops them all. The company wants a lead reliability engineer for a six-month contract to set up service levels, tidy the alerts and teach two teams how to run incident reviews. You will work with the head of engineering and have a free hand in how to get there. The work is fully Remote in Australia, with one planning week in Melbourne.

## What you will do

- Define service levels and error budgets with the product teams, and publish them.
- Rebuild the alert rules so that each page tells the on-call person what to do next.
- Run two live game days where we break things on purpose, then fix the gaps.
- Lead incident reviews and train two teams to run them without you.
- Review the Kubernetes and Terraform setup for single points of failure.
- Leave a runbook library and a short plan for the next 12 months.

## What you bring

- 9 to 14 years of operations, platform or reliability work.
- Site reliability engineering, Observability and Incident response at an expert level (5 of 5).
- Kubernetes and Terraform at an advanced level (4 of 5).
- Technical leadership across teams that you do not manage.
- A current AWS DevOps professional certification, as listed below.

## Nice to have

- Linux depth and Go for small tools.
- Prometheus at an advanced level and Grafana at a proficient level.
- Mentoring of on-call engineers who are new to incident work.

## Tech stack

Kubernetes and Terraform on Linux hosts, Prometheus and Grafana for metrics, and Go services. The monitoring is largely open source.

## Certifications and awards

- Required certification: AWS Certified DevOps Engineer - Professional.

## What we offer

- A day rate of $1,080 to $1,200, paid through your company or an agency.
- A six-month contract that can extend by agreement.
- Fully Remote work, with one planning week in Melbourne and travel paid.
- A small, senior team and direct access to the head of engineering.
- No on-call duty beyond the game days, unless you choose it.

## About Numbatforge

Numbatforge is a remote-first company with about 70 people across Australia. It started in 2020 around an open-source build tool. Today the company sells hosted pipelines to software teams.

## How we hire

- A video call with the head of engineering.
- A conversation about a reliability project that you led.
- A reference check, then a decision within three working days.`,
  },
  {
    key: "swe-backend-mid-01", title: "Backend Engineer (Go), Developer Tools", company: "Numbatforge",
    domain: "Software Engineering", specialisation: "Backend", level: "Mid", minYears: 3, maxYears: 6,
    type: "Full-time", workMode: "Remote", city: "Remote", area: "Remote (Australia)",
    salary: { min: 125000, max: 145000, unit: "year" }, occupation: { code: "261313", title: "Software Engineer" },
    skills: [
      { name: "Go", level: 4, must: true }, { name: "gRPC", level: 3, must: true }, { name: "PostgreSQL", level: 3, must: true },
      { name: "Docker", level: 3, must: true }, { name: "API design", level: 3, must: true }, { name: "Redis", level: 2, must: false },
      { name: "Linux", level: 3, must: false }, { name: "CI/CD", level: 3, must: false },
      { name: "Unit and integration testing", level: 3, must: false }, { name: "Technical documentation", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["Certified Kubernetes Application Developer"] }, awards: { preferred: ["open-source"] },
    educationMin: "Bachelor's degree", postedDaysAgo: 5, closesInDays: 33,
    description: `## About the role

Numbatforge makes the build and deploy tools that thousands of developers use every day. The Pipelines team runs the service that schedules those builds and streams logs back to the browser. The team has five engineers in three time zones, and it needs a mid-level Go engineer to take over the log streaming and queue work. You will ship to production in your first fortnight and own a service by the end of your first quarter.

## What you will do

- Build and maintain the Go services that schedule builds and stream logs to users.
- Add gRPC endpoints and keep their contracts stable for the web app and the command line tool.
- Move build metadata into PostgreSQL tables that stay fast at 50 million rows.
- Use Redis for short-lived queues and tune the expiry rules.
- Write the tests and the runbook for each change that you ship.
- Answer questions from open-source users in our public issue tracker twice a week.
- Hand work to teammates in other time zones with short, clear written notes.

## What you bring

- 3 to 6 years of backend work, with Go at an advanced level (4 of 5).
- gRPC and API design skills at a proficient level (3 of 5), including versioning and error design.
- Proficient PostgreSQL skills and everyday Docker use.
- Comfort on Linux, and CI/CD pipelines that you can fix when they break.
- Unit and integration testing as a habit, not a chore.
- Clear Technical documentation: you leave notes that a stranger could follow.

## Nice to have

- Redis experience beyond a simple cache.
- A merged contribution to an open-source project of any size.
- Experience with build systems or container runtimes.

## Tech stack

Go, gRPC with Protocol Buffers, PostgreSQL, Redis and Docker on Linux hosts. We build Numbatforge with Numbatforge, so the team also lives in the product's own CI/CD pipelines.

## Certifications and awards

- Preferred certification: Certified Kubernetes Application Developer.
- Preferred award kind: Open source contribution.

## What we offer

- $125,000 to $145,000 a year, plus 12% superannuation.
- Remote work from anywhere in Australia, with a team week in a different city twice a year.
- $1,500 for your home office and a monthly internet allowance.
- Four weeks of annual leave and a company-wide shutdown between Christmas and New Year.
- A learning budget of $2,000 a year.

## About Numbatforge

Numbatforge is a remote-first company with about 70 people across Australia. It started in 2020 around an open-source build tool. Today the company sells hosted pipelines to software teams.

## How we hire

- A video call with the engineering manager and a team member.
- A take-home task of about two hours, which we pay you for.
- A paired session on the code that you wrote, with two future teammates.
- An offer within a week of the final conversation.`,
  },
  {
    key: "swe-backend-senior-01", title: "Senior Backend Engineer, Payments", company: "Quokkawave Systems",
    domain: "Software Engineering", specialisation: "Backend", level: "Senior", minYears: 5, maxYears: 10,
    type: "Full-time", workMode: "Hybrid", city: "Sydney", area: "Sydney NSW",
    salary: { min: 175000, max: 195000, unit: "year" }, occupation: { code: "261313", title: "Software Engineer" },
    skills: [
      { name: "Java", level: 5, must: true }, { name: "Spring Boot", level: 4, must: true }, { name: "Apache Kafka", level: 4, must: true },
      { name: "PostgreSQL", level: 4, must: true }, { name: "Kubernetes", level: 4, must: true }, { name: "System design", level: 4, must: true },
      { name: "API design", level: 4, must: false }, { name: "Docker", level: 4, must: false },
      { name: "Unit and integration testing", level: 4, must: false }, { name: "Observability", level: 3, must: false },
      { name: "Mentoring", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["Confluent Certified Developer for Apache Kafka"] }, awards: { preferred: ["conference-talk"] },
    educationMin: "Bachelor's degree", postedDaysAgo: 2, closesInDays: 28,
    description: `## About the role

Quokkawave Systems runs the card and bank-transfer rails behind about 40,000 small shops across Australia. The Payments squad owns the service that approves each sale and settles it the next morning. Volume doubled last year, and the settlement service now needs a senior engineer to split it into clean domains. You will join six engineers and shape how money moves through the platform.

## What you will do

- Design and build the Java services that approve, capture and settle card payments.
- Split the settlement monolith into smaller services without dropping a single transaction.
- Model payment events on Kafka topics and make every consumer safe to replay.
- Tune PostgreSQL queries and schemas for tables that grow by millions of rows each week.
- Run your services on Kubernetes and share the on-call rota with the squad.
- Review code, write design notes and coach two mid-level engineers.
- Work with the risk and billing teams to turn new scheme rules into working software.

## What you bring

- 5 to 10 years of backend work, with Java at an expert level (5 of 5) and Spring Boot at an advanced level (4 of 5).
- Advanced Apache Kafka skills: partitioning, idempotent consumers and schema changes with no downtime.
- Advanced PostgreSQL skills, including indexing, locking and safe migrations.
- Advanced Kubernetes skills: you ship manifests, tune resource limits and debug a failing pod on your own.
- Advanced System design skills, shown in real systems that carry money.
- Strong API design, Docker and Unit and integration testing habits, with Observability in mind from day one.

## Nice to have

- Knowledge of card scheme rules or open banking standards.
- A talk or write-up about a payments or messaging design.
- A record of Mentoring people who later became tech leads.

## Tech stack

Java 21 with Spring Boot, Apache Kafka, PostgreSQL, Docker and Kubernetes on AWS. Builds run in GitHub Actions, and dashboards run on Prometheus and Grafana.

## Certifications and awards

- Preferred certification: Confluent Certified Developer for Apache Kafka.
- Preferred award kind: Conference talk or paper.

## What we offer

- $175,000 to $195,000 a year, plus 12% superannuation.
- Hybrid work: three days a week in our Sydney office and two at home.
- Four weeks of annual leave, ten days of personal leave and 18 weeks of paid parental leave.
- A learning budget of $3,000 a year and two conference days.
- An on-call rota of one week in six, with time back in lieu.

## About Quokkawave Systems

Quokkawave Systems builds payment and point-of-sale software for small merchants. It was founded in 2017 and has about 260 people, most of them in Sydney. Every product team runs its own services and ships to production daily.

## How we hire

- A 30-minute chat with the hiring manager about your recent work.
- A 90-minute pairing session on a small Java and Kafka exercise.
- A system design talk with two engineers, then a values chat with the squad lead.
- You hear back within a week of each step, and offers go out within three weeks.`,
  },
  {
    key: "swe-fullstack-intern-01", title: "Software Engineering Intern, Web Platform", company: "Rosellaworks",
    domain: "Software Engineering", specialisation: "Full-stack", level: "Intern", minYears: 0, maxYears: 1,
    type: "Graduate / Internship", workMode: "Hybrid", city: "Sydney", area: "Sydney NSW",
    salary: { min: 56000, max: 64000, unit: "year" }, occupation: { code: "261312", title: "Developer Programmer" },
    skills: [
      { name: "JavaScript", level: 2, must: true }, { name: "HTML and CSS", level: 2, must: true }, { name: "Git", level: 2, must: true },
      { name: "Teamwork", level: 3, must: true }, { name: "React", level: 2, must: false }, { name: "SQL", level: 1, must: false },
      { name: "Node.js", level: 1, must: false }, { name: "Communication", level: 2, must: false },
      { name: "Continuous learning", level: 3, must: false },
    ],
    certifications: { required: [], preferred: [] }, awards: { preferred: [] },
    educationMin: "High school", postedDaysAgo: 16, closesInDays: 38,
    description: `## About the role

Rosellaworks builds classroom tools for primary and secondary schools, and each year it runs a paid internship for students who want to build real software. This six-month internship sits in the Web Platform team and fits around your studies, with two or three days a week. You will work on the teacher dashboard with a mentor and ship at least one feature to real schools. We choose people for curiosity and teamwork first, and for skill second.

## What you will do

- Build small screens in the teacher dashboard with a mentor beside you.
- Fix bugs that teachers report, starting with the easy ones.
- Write simple SQL queries to answer questions from the support team.
- Learn how code moves from your laptop to a live school.
- Present your work to the whole company at the end of the internship.

## What you bring

- Enrolment in a computer science, software engineering or similar course. You do not need a finished degree.
- 0 to 1 years of experience, or a few small projects that you built yourself.
- JavaScript, HTML and CSS at a working level (2 of 5).
- Git basics: you have made a commit and opened a pull request.
- Teamwork and the courage to ask for help early.

## Nice to have

- A first look at React, Node.js or SQL.
- Clear Communication in writing and in meetings.
- Continuous learning habits: a course, a club or a weekend project.

## Tech stack

JavaScript and React in the browser, a Node.js API, a PostgreSQL database and Git with pull requests. You learn the rest on the job.

## What we offer

- $56,000 to $64,000 a year for a full working week, paid pro rata for two or three days a week, plus 12% superannuation.
- Hybrid work: one day a week in our Sydney office and the rest at home.
- Flexible days around exams and study weeks.
- A mentor, a buddy and a review every month.
- A strong chance of a graduate offer if the internship goes well.

## About Rosellaworks

Rosellaworks makes planning and assessment tools for schools. It was founded in 2018 and has about 45 people in Sydney. Teachers and former teachers work next to the engineers.

## How we hire

- A short online form about your projects and your course.
- A 30-minute chat with two people from the team.
- A small, friendly coding exercise that we do together.
- An answer within a week.`,
  },
  {
    key: "swe-backend-junior-01", title: "Junior Backend Developer, Node.js", company: "Moretonbyte",
    domain: "Software Engineering", specialisation: "Backend", level: "Junior", minYears: 0, maxYears: 2,
    type: "Full-time", workMode: "Hybrid", city: "Brisbane", area: "Brisbane QLD",
    salary: { min: 82000, max: 96000, unit: "year" }, occupation: { code: "261312", title: "Developer Programmer" },
    skills: [
      { name: "TypeScript", level: 3, must: true }, { name: "Node.js", level: 3, must: true }, { name: "SQL", level: 3, must: true },
      { name: "Git", level: 3, must: true }, { name: "NestJS", level: 2, must: false }, { name: "API design", level: 2, must: false },
      { name: "Jest", level: 2, must: false }, { name: "Docker", level: 1, must: false }, { name: "Teamwork", level: 2, must: false },
    ],
    certifications: { required: [], preferred: [] }, awards: { preferred: ["competitive-programming"] },
    educationMin: "Bachelor's degree", postedDaysAgo: 12, closesInDays: 40,
    description: `## About the role

Moretonbyte runs the booking and ticketing system for ferries and tour operators around Moreton Bay and the Queensland coast. The backend is a set of Node.js services, and the team of five wants a junior developer who writes tidy TypeScript and asks good questions. You will pair with a senior engineer every week and ship small features in your first month. This is a Hybrid role in Brisbane, with two days a week at home.

## What you will do

- Build small features in our Node.js services, such as a new fare rule or a booking reminder.
- Write SQL queries and migrations for booking and passenger tables.
- Add tests with Jest for every change that you make.
- Fix bugs that support staff report, and explain the cause in the ticket.
- Join code reviews as both author and reviewer.
- Learn how a request moves from the mobile app to the database and back.

## What you bring

- 0 to 2 years of experience, or a strong final-year project or work placement.
- TypeScript and Node.js at a proficient level (3 of 5): you can build a small service from a blank folder.
- SQL at a proficient level (3 of 5), including joins and simple indexes.
- Git at a proficient level: branches, pull requests and merge conflicts do not scare you.
- Teamwork: you say what you are stuck on early.

## Nice to have

- NestJS, Jest or API design practice from a course or a side project.
- A first look at Docker.
- A result in a coding contest or a hackathon.

## Tech stack

TypeScript on Node.js with NestJS, PostgreSQL, Jest and Docker. Services run on AWS, and the team uses GitHub for code and reviews.

## Certifications and awards

- Preferred award kind: Competitive programming.

## What we offer

- $82,000 to $96,000 a year, plus 12% superannuation.
- Hybrid work: three days in our Brisbane office and two at home.
- A named mentor and a 12-month learning plan that you write with your lead.
- Four weeks of annual leave and ten days of personal leave.
- Free ferry passes when you travel with the team to the islands for our yearly offsite.

## About Moretonbyte

Moretonbyte builds booking and ticketing software for ferries, tours and marinas in Queensland. It was founded in 2017 and has about 55 people in Brisbane. Its small teams ship every week.

## How we hire

- A 20-minute call about the projects that you built.
- A friendly coding session where we write a small API together.
- A chat with two teammates about how you like to learn.
- Feedback on the day of the coding session, and an answer within the week.`,
  },
  {
    key: "swe-frontend-mid-02", title: "Frontend Engineer (Angular), Merchant Portal", company: "Quokkawave Systems",
    domain: "Software Engineering", specialisation: "Frontend", level: "Mid", minYears: 3, maxYears: 7,
    type: "Full-time", workMode: "Onsite", city: "Sydney", area: "Sydney NSW",
    salary: { min: 112000, max: 128000, unit: "year" }, occupation: { code: "261212", title: "Web Developer" },
    skills: [
      { name: "Angular", level: 4, must: true }, { name: "TypeScript", level: 4, must: true }, { name: "HTML and CSS", level: 3, must: true },
      { name: "Cypress", level: 3, must: true }, { name: "API design", level: 3, must: false }, { name: "Git", level: 3, must: false },
      { name: "Unit and integration testing", level: 3, must: false }, { name: "Data visualisation", level: 3, must: false },
      { name: "Web accessibility", level: 2, must: false }, { name: "Agile delivery", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["Professional Scrum Master I"] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 19, closesInDays: 16,
    description: `## About the role

Merchants use the Quokkawave Systems portal to check sales, refunds and payouts, and about 60,000 people sign in each week. The portal is an Angular application that has grown over six years, and the team is now cleaning up its structure and its charts. The work is Onsite at our Sydney office, where the portal team of seven sits together with design and support. As a mid-level engineer, you will own the reports pages and bring them up to the standard of the new payment screens.

## What you will do

- Refactor the reports pages in Angular and TypeScript into small, tested parts.
- Build new charts and tables, with Data visualisation that a shop owner can read at a glance.
- Write end-to-end tests with Cypress for the most used merchant flows.
- Agree API changes with backend engineers and keep the contracts clear.
- Fix accessibility problems that support staff report.
- Take part in planning, demos and the retrospective each fortnight.

## What you bring

- 3 to 7 years of frontend work, with Angular and TypeScript at an advanced level (4 of 5).
- HTML and CSS at a proficient level (3 of 5), including responsive tables.
- Cypress at a proficient level: you write tests that do not flake.
- Good API design sense, and Git habits that keep the history clear.
- Comfort with Unit and integration testing in Angular.

## Nice to have

- Web accessibility knowledge at a working level.
- Agile delivery experience in a squad with a product owner.
- Experience with dashboards that show money, such as payouts and fees.

## Tech stack

Angular and TypeScript, Cypress, a REST API built in Java, Git with pull requests, and a design system shared with the mobile apps.

## Certifications and awards

- Preferred certification: Professional Scrum Master I.

## What we offer

- $112,000 to $128,000 a year, plus 12% superannuation.
- Onsite work in our Sydney office, five days a week, with a standing desk and a quiet room.
- Four weeks of annual leave and half-day Fridays in January.
- A $2,500 learning budget and a yearly conference day.
- Free fruit, coffee and a monthly team lunch.

## About Quokkawave Systems

Quokkawave Systems builds payment and point-of-sale software for small merchants. It was founded in 2017 and has about 260 people, most of them in Sydney. Product teams sit together and ship to production every day.

## How we hire

- A 30-minute call with the hiring manager.
- A technical talk about an Angular app that you built.
- A pairing session on a small reports page, with two teammates.
- An answer within a week.`,
  },
  {
    key: "ai-mle-lead-01", title: "Lead Machine Learning Engineer, Foundation Models", company: "Dingocreek Labs",
    domain: "AI & Machine Learning", specialisation: "Machine learning engineering", level: "Lead", minYears: 7, maxYears: 13,
    type: "Full-time", workMode: "Remote", city: "Remote", area: "Remote (Australia)",
    salary: { min: 200000, max: 228000, unit: "year" }, occupation: { code: "261399", title: "Machine Learning Engineer" },
    skills: [
      { name: "Python", level: 5, must: true }, { name: "Deep learning", level: 5, must: true }, { name: "PyTorch", level: 5, must: true },
      { name: "Model evaluation", level: 4, must: true }, { name: "Distributed training and GPU computing", level: 4, must: true },
      { name: "Technical leadership", level: 4, must: true }, { name: "Team leadership", level: 4, must: true },
      { name: "Machine learning", level: 5, must: false }, { name: "Mentoring", level: 4, must: false }, { name: "MLflow", level: 3, must: false },
      { name: "Statistics", level: 4, must: false }, { name: "Responsible AI", level: 3, must: false },
    ],
    certifications: { required: [], preferred: [] }, awards: { preferred: ["conference-talk"] },
    educationMin: "Master's degree", postedDaysAgo: 20, closesInDays: 22,
    description: `## About the role

Dingocreek Labs is an independent research lab that trains language and vision models for Australian science and industry, and it publishes most of its work. The Foundation Models group of nine trains models on a cluster of 256 GPUs and needs a lead who can keep the research ambitious and the training runs reliable. You will set the technical plan, manage a team of five and stay close to the code. The role is fully Remote in Australia.

## What you will do

- Plan and run large training jobs, from data pipeline to checkpoint and restart.
- Design the evaluation suite that tells us if a new model is really better.
- Lead five engineers and researchers: set goals, remove blockers and give honest feedback.
- Speed up training with better parallelism, mixed precision and smarter data loading.
- Work with the safety group on tests for harmful or biased output.
- Write papers and technical reports with the team.
- Represent the lab at partner meetings and at one or two conferences a year.

## What you bring

- 7 to 13 years in machine learning, with Python, Deep learning and PyTorch at an expert level (5 of 5).
- Distributed training and GPU computing at an advanced level (4 of 5): sharding, memory limits and failure recovery.
- Model evaluation at an advanced level, including benchmarks that can be gamed and how to avoid them.
- Technical leadership and Team leadership at an advanced level, shown by teams that you led.
- A master's degree or a PhD in a related field, or equal research work.

## Nice to have

- Responsible AI practice, with real red-team or bias testing work.
- MLflow and Statistics skills for careful experiments.
- Mentoring of researchers who are new to engineering.

## Tech stack

Python and PyTorch with a Slurm GPU cluster, an experiment tracker built on MLflow, Linux nodes with fast storage and a small set of internal tools for data processing.

## Certifications and awards

- Preferred award kind: Conference talk or paper.

## What we offer

- $200,000 to $228,000 a year, plus 12% superannuation.
- Fully Remote work in Australia, with two lab weeks a year in Canberra.
- A fair share of compute for your own research ideas, every month.
- Five weeks of annual leave and a $6,000 yearly budget for conferences and travel.
- Time to publish: one day a fortnight for papers.

## About Dingocreek Labs

Dingocreek Labs is an independent AI research lab. It was founded in 2021 and has about 40 people who work from home across Australia. It publishes its papers and releases some models to the public.

## How we hire

- A call with the research director.
- A technical talk about a training project that you led.
- A session with two researchers on evaluation and design.
- A decision within eight working days.`,
  },
  {
    key: "ai-genai-junior-01", title: "Junior AI Engineer, Prompt and Evaluation", company: "Gidgeebyte",
    domain: "AI & Machine Learning", specialisation: "Generative AI and LLM", level: "Junior", minYears: 0, maxYears: 2,
    type: "Full-time", workMode: "Onsite", city: "Perth", area: "Perth WA",
    salary: { min: 88000, max: 102000, unit: "year" }, occupation: { code: "261311", title: "Generative AI Engineer" },
    skills: [
      { name: "Python", level: 3, must: true }, { name: "Prompt engineering", level: 3, must: true }, { name: "LLM APIs", level: 2, must: true },
      { name: "Generative AI", level: 2, must: true }, { name: "Git", level: 2, must: false }, { name: "FastAPI", level: 2, must: false },
      { name: "SQL", level: 2, must: false }, { name: "Retrieval-augmented generation", level: 1, must: false },
      { name: "Teamwork", level: 3, must: false }, { name: "Continuous learning", level: 3, must: false },
      { name: "Communication", level: 3, must: false },
    ],
    certifications: { required: ["AWS Certified AI Practitioner"], preferred: [] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 13, closesInDays: 34,
    description: `## About the role

Gidgeebyte checks every answer that its assistants send, and the Prompt and Evaluation team writes the tests that do the checking. As a junior AI engineer you will write prompts, build test sets and run reports that tell the product team when an update makes the assistant better or worse. You will learn how large language models behave when they meet messy, real messages. This is an Onsite role in our Perth office, with a mentor at the next desk.

## What you will do

- Write and improve prompts for new assistant features with your mentor.
- Build test sets of customer messages, with private details removed.
- Run the evaluation suite on every release and write a short report.
- Call LLM APIs from small Python scripts and FastAPI endpoints.
- Query conversation data with SQL to find where the assistant struggles.
- Share what you learn in a short note every week.

## What you bring

- 0 to 2 years of experience, or a university or bootcamp project that used an LLM.
- Python at a proficient level (3 of 5), including reading and writing files and calling web APIs.
- Prompt engineering at a proficient level: clear instructions, examples and checks.
- LLM APIs and Generative AI basics (2 of 5): you know tokens, temperature and why models make things up.
- The AWS AI Practitioner certificate, as listed below.
- Good Teamwork and honest Communication.

## Nice to have

- Git, FastAPI or SQL from your own projects.
- A first project with Retrieval-augmented generation.
- Continuous learning: you follow the field and try new ideas.

## Tech stack

Python, FastAPI, hosted LLM APIs, a SQL database, a small evaluation tool that we wrote ourselves and Git.

## Certifications and awards

- Required certification: AWS Certified AI Practitioner.

## What we offer

- $88,000 to $102,000 a year, plus 12% superannuation.
- Onsite work in our Perth office, five days a week, with a desk next to your mentor.
- Four weeks of annual leave and ten days of personal leave.
- Exam fees paid for the next AWS certification.
- Lunch on Fridays and a team walk along the river each month.

## About Gidgeebyte

Gidgeebyte is a young company with about 25 people. It was founded in 2024, with its main office in Perth. It builds AI assistants for small service businesses.

## How we hire

- A 20-minute call with the team lead about your first LLM project.
- A short exercise on writing and testing a prompt.
- A visit to the Perth office and a chat with two engineers.
- A decision within five working days of your visit.`,
  },
  {
    key: "ai-genai-mid-01", title: "Generative AI Engineer, Customer Assistants", company: "Gidgeebyte",
    domain: "AI & Machine Learning", specialisation: "Generative AI and LLM", level: "Mid", minYears: 2, maxYears: 4,
    type: "Full-time", workMode: "Remote", city: "Remote", area: "Remote (Australia)",
    salary: { min: 135000, max: 158000, unit: "year" }, occupation: { code: "261311", title: "Generative AI Engineer" },
    skills: [
      { name: "Prompt engineering", level: 4, must: true }, { name: "LLM APIs", level: 4, must: true }, { name: "Python", level: 4, must: true },
      { name: "Retrieval-augmented generation", level: 3, must: true }, { name: "FastAPI", level: 3, must: true },
      { name: "Vector databases", level: 3, must: false }, { name: "LangChain", level: 3, must: false },
      { name: "Generative AI", level: 3, must: false }, { name: "Git", level: 3, must: false },
      { name: "Experimentation and A/B testing", level: 2, must: false }, { name: "Product thinking", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["Databricks Certified Generative AI Engineer Associate"] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 6, closesInDays: 27,
    description: `## About the role

Gidgeebyte builds AI assistants for trade and field-service businesses: plumbers, electricians and cleaners who answer customer messages between jobs. The assistants read the question, check the job calendar and draft a reply that the owner approves with one tap. We are a team of 25 and the product is only two years old, so each engineer shapes it. This Remote role suits a mid-level engineer who likes to ship small improvements every week.

## What you will do

- Write and test prompts for quoting, booking and follow-up messages.
- Build retrieval over each business's price list and past jobs, so that quotes stay accurate.
- Add new tools to the assistant, such as a calendar check or a parts lookup.
- Run small A/B tests on reply quality and measure how often owners accept a draft.
- Watch real conversations (with private details removed) to learn what to fix next.
- Keep the FastAPI services fast and cheap to run.

## What you bring

- 2 to 4 years of software or machine learning work, with Python at an advanced level (4 of 5).
- Prompt engineering and LLM APIs at an advanced level: you know how to make a model follow a format.
- Retrieval-augmented generation and FastAPI at a proficient level (3 of 5).
- Judgement about quality: you can tell a good reply from one that only sounds good.
- Willingness to work in a small team that decides fast.

## Nice to have

- Vector databases, LangChain and Generative AI projects that you finished.
- Experimentation and A/B testing habits.
- Product thinking and good Git manners.

## Tech stack

Python, FastAPI, hosted LLM APIs, LangChain for some flows, a vector database and Git. Everything runs on a managed cloud with simple deploys.

## Certifications and awards

- Preferred certification: Databricks Certified Generative AI Engineer Associate.

## What we offer

- $135,000 to $158,000 a year, plus 12% superannuation.
- Remote work from anywhere in Australia, with a team week in Perth each year.
- A model budget for your own experiments and $1,500 for your home office.
- Four weeks of annual leave and a company shutdown between Christmas and New Year.
- Share options that vest over four years.

## About Gidgeebyte

Gidgeebyte is a young company with about 25 people. It was founded in 2024, with its main office in Perth and most staff working from home. It builds AI assistants for small service businesses.

## How we hire

- A short video call with a founder.
- A two-hour paid task on a prompt and retrieval problem.
- A talk with two engineers about your solution.
- An offer within five working days.`,
  },
  {
    key: "ai-mlops-mid-01", title: "MLOps Engineer (Contract), Azure", company: "Tallowbridge Cloud",
    domain: "AI & Machine Learning", specialisation: "MLOps", level: "Mid", minYears: 2, maxYears: 6,
    type: "Contract", workMode: "Hybrid", city: "Sydney", area: "Sydney NSW",
    salary: { min: 760, max: 840, unit: "day" }, occupation: { code: "263111", title: "MLOps Engineer" },
    skills: [
      { name: "MLOps", level: 3, must: true }, { name: "Azure Machine Learning", level: 4, must: true }, { name: "Docker", level: 3, must: true },
      { name: "Python", level: 3, must: true }, { name: "Azure DevOps", level: 3, must: true }, { name: "CI/CD", level: 3, must: false },
      { name: "Kubernetes", level: 2, must: false }, { name: "MLflow", level: 3, must: false }, { name: "Git", level: 3, must: false },
      { name: "Terraform", level: 2, must: false }, { name: "Observability", level: 2, must: false },
    ],
    certifications: { required: ["Microsoft Certified: Azure Data Scientist Associate"], preferred: [] }, awards: { preferred: [] },
    educationMin: "Bachelor's degree", postedDaysAgo: 4, closesInDays: 8,
    description: `## About the role

A large utility client of Tallowbridge Cloud has built 14 machine learning models in notebooks and now wants them to run as a reliable service. You will join a client team of six as the mid-level MLOps engineer on a four-month contract to move the models to Azure Machine Learning, with pipelines, tests and monitoring. The client's data scientists will learn from you as you build. This is a Hybrid contract in Sydney, with two days a week on the client site.

## What you will do

- Turn notebooks into Python packages with tests and clear inputs.
- Build Azure Machine Learning pipelines for training, scoring and retraining.
- Package models in Docker and deploy them to managed endpoints.
- Set up Azure DevOps pipelines with approvals before each release.
- Add checks and alerts for bad data and drifting predictions.
- Teach two data scientists how to run the pipelines themselves.

## What you bring

- 2 to 6 years of software, data or machine learning engineering.
- Azure Machine Learning at an advanced level (4 of 5), and MLOps at a proficient level (3 of 5).
- Docker, Python and Azure DevOps at a proficient level.
- A clear way of explaining pipelines to people who build models, not software.
- The Azure Data Scientist Associate certificate, as listed below.

## Nice to have

- CI/CD design, Git branching and MLflow tracking.
- Kubernetes and Terraform at a working level (2 of 5).
- Observability practice for model services.

## Tech stack

Azure Machine Learning, Azure DevOps, Docker, Python, MLflow for tracking and Terraform for environments. Some models run on Kubernetes.

## Certifications and awards

- Required certification: Microsoft Certified: Azure Data Scientist Associate.

## What we offer

- A day rate of $760 to $840, paid through your company or an agency.
- A four-month contract, with a good chance of extension.
- Hybrid work: two days a week on the client site in Sydney and the rest at home.
- A client team that is keen to learn.
- Fast start: we aim to finish onboarding in two working days.

## About Tallowbridge Cloud

Tallowbridge Cloud is a cloud consultancy for banks, utilities and councils. It was founded in 2013 and has about 200 people in Sydney and Melbourne. Contractors work in the same teams as staff.

## How we hire

- A 30-minute call about the contract.
- A technical chat on Azure Machine Learning and pipelines.
- An answer within two working days of the technical chat.`,
  },
  {
    key: "ai-vision-senior-01", title: "Senior Computer Vision Engineer, Maritime Sensing", company: "Torrensline Systems",
    domain: "AI & Machine Learning", specialisation: "Computer vision", level: "Senior", minYears: 6, maxYears: 12,
    type: "Full-time", workMode: "Onsite", city: "Adelaide", area: "Adelaide SA",
    salary: { min: 150000, max: 172000, unit: "year" }, occupation: { code: "261399", title: "Machine Learning Engineer" },
    skills: [
      { name: "Computer vision", level: 5, must: true }, { name: "PyTorch", level: 4, must: true }, { name: "Deep learning", level: 4, must: true },
      { name: "C++", level: 4, must: true }, { name: "Python", level: 4, must: true }, { name: "Model evaluation", level: 4, must: true },
      { name: "Distributed training and GPU computing", level: 3, must: false }, { name: "Docker", level: 3, must: false },
      { name: "Linux", level: 3, must: false }, { name: "Git", level: 3, must: false }, { name: "Technical documentation", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["Microsoft Certified: Azure AI Engineer Associate"] }, awards: { preferred: ["patent"] },
    educationMin: "Bachelor's degree (Honours)", postedDaysAgo: 10, closesInDays: 45,
    description: `## About the role

Torrensline Systems builds camera and sensor systems that watch the water: ports, ships and coastlines. The vision team of nine trains models that find small boats and floating objects in video at long range, and then ships them to edge computers on vessels. We are hiring a senior computer vision engineer to improve detection in rough weather and at night. This is an Onsite role in Adelaide, where the lab and the test tank are.

## What you will do

- Improve the detection and tracking models for small objects in noisy video.
- Write the C++ inference code that runs the models on edge hardware in real time.
- Train models on multi-GPU machines and manage the labelled data sets.
- Build test rigs and field trials that show how models behave in rain, glare and darkness.
- Prepare clear reports and demos for customers and for the review board.
- Help two junior engineers with their experiments and their code.

## What you bring

- 6 to 12 years in computer vision or a related field, with Computer vision at an expert level (5 of 5).
- PyTorch and Deep learning at an advanced level (4 of 5), including detection and tracking models.
- C++ and Python at an advanced level: you have shipped real-time code.
- Model evaluation at an advanced level, with sound test design and honest numbers.
- A bachelor's degree with honours in engineering, computer science or physics, or more.

## Nice to have

- Distributed training and GPU computing for large video data sets.
- Docker, Linux and Git for repeatable builds on edge devices.
- Strong Technical documentation, because customers audit our work.
- A patent or a published paper in vision or sensing.

## Tech stack

Python and PyTorch for training, C++ with CUDA for inference, Docker and Linux on edge computers, and Git. The lab has a 16-GPU server and a water test tank.

## Certifications and awards

- Preferred certification: Microsoft Certified: Azure AI Engineer Associate.
- Preferred award kind: Patent.

## What we offer

- $150,000 to $172,000 a year, plus 12% superannuation.
- Onsite work in our Adelaide lab, five days a week, with sea trials a few times a year.
- Four weeks of annual leave and extra days off after each sea trial.
- Support for conference trips and for your own patent filings.
- A modern lab with a quiet room and a coffee machine that works.

## About Torrensline Systems

Torrensline Systems builds sensing and vision systems for ports, vessels and coastal monitoring. It was founded in 2012 and has about 120 people in Adelaide. Much of its work is for customers in the maritime industry.

## How we hire

- A call with the vision lead.
- A technical talk about a vision system that you built.
- A day in the lab, with a short design exercise and lunch with the team.
- A decision within a week of your visit.`,
  },
  {
    key: "ai-mle-mid-01", title: "Machine Learning Engineer, Personalisation", company: "Lyrebirdlogic",
    domain: "AI & Machine Learning", specialisation: "Machine learning engineering", level: "Mid", minYears: 2, maxYears: 5,
    type: "Full-time", workMode: "Hybrid", city: "Sydney", area: "Sydney NSW",
    salary: { min: 128000, max: 150000, unit: "year" }, occupation: { code: "261399", title: "Machine Learning Engineer" },
    skills: [
      { name: "Python", level: 4, must: true }, { name: "Machine learning", level: 4, must: true }, { name: "PyTorch", level: 3, must: true },
      { name: "Feature engineering", level: 3, must: true }, { name: "Model evaluation", level: 3, must: true },
      { name: "scikit-learn", level: 4, must: false }, { name: "Docker", level: 3, must: false }, { name: "Git", level: 3, must: false },
      { name: "MLflow", level: 2, must: false }, { name: "SQL", level: 3, must: false }, { name: "Statistics", level: 3, must: false },
    ],
    certifications: { required: [], preferred: ["Machine Learning Specialization"] }, awards: { preferred: ["data-science-competition"] },
    educationMin: "Bachelor's degree", postedDaysAgo: 2, closesInDays: 29,
    description: `## About the role

Lyrebirdlogic builds search and recommendation tools for online marketplaces, and its models decide which of 4 million listings a shopper sees first. The Personalisation team of seven trains and ships the ranking models behind the home page and the email digests. We are hiring a mid-level machine learning engineer to own the first-stage retrieval models and to bring new ideas from notebook to production. You will work with a data scientist, a backend engineer and a product manager on one goal: more relevant clicks.

## What you will do

- Train and tune ranking and retrieval models in PyTorch and scikit-learn.
- Build features from clicks, searches and listing data, and keep them fresh each day.
- Check each model with offline tests and a careful online experiment before it ships.
- Package models in Docker and hand them to the serving team with clear tests.
- Track experiments in MLflow so that anyone can reproduce a result.
- Look into odd results, such as a drop in clicks on a single category, and find the cause.

## What you bring

- 2 to 5 years of applied machine learning, with Python and Machine learning at an advanced level (4 of 5).
- PyTorch at a proficient level (3 of 5): you have trained and debugged a neural model.
- Feature engineering and Model evaluation at a proficient level, including bias in click data.
- Good SQL and Statistics, so that you can read an experiment result for yourself.
- Clean Git history and tests for your data code.

## Nice to have

- scikit-learn depth, with gradient boosting and calibration.
- MLflow or a similar tracker in daily use.
- A result in a data science competition, such as a top finish.

## Tech stack

Python, PyTorch, scikit-learn, Docker, MLflow and Git. Data sits in a data warehouse that you query with SQL, and models are served by a Go service owned by the serving team.

## Certifications and awards

- Preferred certification: Machine Learning Specialization.
- Preferred award kind: Data science competition.

## What we offer

- $128,000 to $150,000 a year, plus 12% superannuation.
- Hybrid work: in our Sydney office on three days that the team picks together, and at home on two.
- Four weeks of annual leave and a company shutdown in the first week of January.
- A GPU workstation in the office and cloud credits for your own experiments.
- A $3,000 yearly budget for papers, courses and conferences.

## About Lyrebirdlogic

Lyrebirdlogic makes search and recommendation software for online marketplaces. It was founded in 2017 and has about 110 people in Sydney. Its research reading group meets every Thursday.

## How we hire

- A 30-minute chat about your recent models.
- A take-home task on a small ranking data set, about three hours long.
- A talk with the team about your solution and the trade-offs.
- An answer within a week.`,
  },
];
