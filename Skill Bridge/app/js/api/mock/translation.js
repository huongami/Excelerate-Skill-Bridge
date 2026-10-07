// MOCK BACKEND — the cross-border and cross-industry skill translation engine. The real backend replaces this file.
// A simpler copy of jinder_platform/jinder/translation.py. ICT only: every name is a name of ict_taxonomy.json (a role of the role list, a skill of the skill list).
// Input: the candidate's profile (roles, skills, qualifications, countries) and the CV evidence lines.
// Output: translated skills with a plain-language reason, an evidence level and a skill level (1 to 5). No score on the person.
// A title that is not an ICT title gives no role card. A skill that the taxonomy does not know keeps its name.
// It never uses nationality, ethnicity, gender, age or visa status. Country of study is used only for
// the AQF note on qualifications and for the word "cross-border" (Feature 2; PRD: no formal credential verification).
import { canonicalSkillName, skillsIn } from "./jobs.js";

const lower = (s) => String(s || "").toLowerCase();
const list = (v) => (Array.isArray(v) ? v : v ? [v] : []);
const escRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

// A skill with no level of its own gets the level of its evidence (rule F8)
const EVIDENCE_LEVEL = { Strong: 4, Moderate: 3, Limited: 2 };

// The occupations and the role list of the taxonomy. A role title gives an ANZSCO code, and the code gives the occupation title.
const OCCUPATIONS = {
  "261313": "Software Engineer",
  "261312": "Developer Programmer",
  "261212": "Web Developer",
  "261316": "DevOps Engineer",
  "261314": "Software Tester",
  "263211": "ICT Quality Assurance Engineer",
  "261315": "Cyber Security Engineer",
  "261112": "Solutions Architect",
  "261399": "Machine Learning Engineer",
  "261311": "Generative AI Engineer",
  "263111": "MLOps Engineer",
  "224112": "AI Research Scientist",
  "224115": "Data Scientist",
  "224114": "Data Analyst",
  "262111": "Data Engineer",
  "261111": "ICT Business Analyst",
  "224113": "Statistician",
};
const ROLE_CODES = {
  "Software Engineer": "261313",
  "Software Developer": "261312",
  "Backend Engineer": "261313",
  "Frontend Engineer": "261212",
  "Full-stack Engineer": "261312",
  "Web Developer": "261212",
  "Mobile Developer": "261312",
  "Android Developer": "261312",
  "iOS Developer": "261312",
  "Java Developer": "261312",
  ".NET Developer": "261312",
  "Python Developer": "261312",
  "Platform Engineer": "261316",
  "DevOps Engineer": "261316",
  "Site Reliability Engineer": "261316",
  "Cloud Engineer": "261316",
  "Cloud Architect": "261112",
  "Solutions Architect": "261112",
  "Software Architect": "261112",
  "QA Engineer": "263211",
  "Test Automation Engineer": "263211",
  "Software Tester": "261314",
  "Security Engineer": "261315",
  "Application Security Engineer": "261315",
  "Machine Learning Engineer": "261399",
  "Computer Vision Engineer": "261399",
  "NLP Engineer": "261399",
  "Deep Learning Engineer": "261399",
  "AI Engineer": "261311",
  "Generative AI Engineer": "261311",
  "LLM Engineer": "261311",
  "MLOps Engineer": "263111",
  "ML Platform Engineer": "263111",
  "Applied Scientist": "224112",
  "AI Research Scientist": "224112",
  "AI Research Engineer": "224112",
  "Data Engineer": "262111",
  "Analytics Engineer": "262111",
  "Big Data Engineer": "262111",
  "Data Platform Engineer": "262111",
  "ETL Developer": "262111",
  "Data Warehouse Engineer": "262111",
  "Database Administrator": "262111",
  "Data Architect": "262111",
  "Data Analyst": "224114",
  "Business Intelligence Analyst": "224114",
  "BI Developer": "224114",
  "Reporting Analyst": "224114",
  "Product Analyst": "224114",
  "Data Scientist": "224115",
  "Statistician": "224113",
  "Business Analyst": "261111",
  "Business Systems Analyst": "261111",
};
const ROLE_BY_LOWER = new Map(Object.keys(ROLE_CODES).map((t) => [lower(t), t]));
const occupationOf = (mapped) => ({ anzsco: ROLE_CODES[mapped], occupation: OCCUPATIONS[ROLE_CODES[mapped]] });

// Mapping library (about 25 role pairs and 30 skill pairs). "test" runs on one role title (without level words) or on one skill, in lower case.
// kind: "cross-border" (an overseas title, tool or standard), "cross-industry" (the same competency in a different field of work)
// or "direct" (a common name for the same thing).
// overseas: the pair is used only if the talent studied overseas, or the title has a place in brackets ("Software Developer (Vietnam)").
// weak: the last choice, when no other pair fits.
const role = (test, mapped, kind, reason, extra = {}) => ({ test: new RegExp(test), mapped, kind, reason, ...occupationOf(mapped), ...extra });
const ROLE_PAIRS = [
  role("\\b(sde|swe|software development engineer)\\b", "Software Engineer", "cross-border", "SDE and SWE are common overseas titles. In Australia the same work is a Software Engineer role."),
  role("^software developer\\b", "Software Engineer", "cross-border", "Software Developer is a common title overseas for what Australian employers call a Software Engineer.", { overseas: true }),
  role("analyst[- ]programmer|application programmer|applications developer|^(computer |web |application )?programmer$|^coder$", "Software Developer", "cross-border",
    "Programmer titles overseas match the Australian Software Developer role: you design, write and test code."),
  role("j2ee|java (developer|engineer|programmer)", "Java Developer", "direct", "Java Developer has the same meaning in Australia."),
  role("\\.net|dotnet|c# (developer|engineer)", ".NET Developer", "direct", ".NET Developer has the same meaning in Australia."),
  role("(front[- ]?end|ui|react|angular|vue) (developer|engineer)", "Frontend Engineer", "direct", "Front-end work has the same meaning in Australia. Australian ads call the role Frontend Engineer."),
  role("(back[- ]?end|server[- ]side|api) (developer|engineer)", "Backend Engineer", "direct", "Back-end work has the same meaning in Australia. Australian ads call the role Backend Engineer."),
  role("full[- ]?stack", "Full-stack Engineer", "direct", "Full-stack work has the same meaning in Australia."),
  role("(android|ios|mobile|flutter|react native)( app| application)? (developer|engineer)", "Mobile Developer", "direct", "Mobile development has the same meaning in Australia."),
  role("(system|systems|network|infrastructure|it infrastructure) (administrator|admin|engineer)|sysadmin", "Platform Engineer", "cross-industry",
    "Running servers and networks is close to platform engineering in Australia, where teams also write code to run the platform.",
    { gaps: ["Infrastructure as code (for example Terraform)"] }),
  role("devops|release engineer|build (and release )?engineer", "DevOps Engineer", "direct", "DevOps Engineer has the same meaning in Australia."),
  role("\\bsre\\b|site reliability|reliability engineer", "Site Reliability Engineer", "direct", "Site Reliability Engineer has the same meaning in Australia."),
  role("(solution|solutions|enterprise|technical) architect|solution designer", "Solutions Architect", "direct", "Solutions Architect has the same meaning in Australia."),
  role("test automation|automation (test )?(engineer|tester)|\\bsdet\\b", "Test Automation Engineer", "direct", "Test automation work has the same meaning in Australia."),
  role("(qa|quality assurance|quality) (engineer|analyst|specialist)|test engineer", "QA Engineer", "direct", "QA Engineer has the same meaning in Australia."),
  role("\\btester\\b|testing engineer|software tester", "Software Tester", "direct", "Software Tester has the same meaning in Australia."),
  role("(information|cyber|network|application|it) security (engineer|analyst|specialist|officer)|infosec|soc analyst", "Security Engineer", "cross-border",
    "Security analyst and officer titles overseas match the Australian Security Engineer role."),
  role("machine learning (engineer|developer)|\\bml engineer\\b", "Machine Learning Engineer", "direct", "Machine Learning Engineer has the same meaning in Australia."),
  role("(gen(erative)? ?ai|llm|prompt|chatbot|conversational ai) (engineer|developer)", "Generative AI Engineer", "direct", "Generative AI work has the same meaning in Australia."),
  role("applied scientist|research scientist|ai researcher|research engineer", "Applied Scientist", "cross-industry",
    "Research roles in machine learning match the Australian Applied Scientist role: you test ideas and build models that ship."),
  role("etl (developer|engineer)|informatica|datastage|ssis developer|talend", "ETL Developer", "cross-border",
    "ETL titles and tools overseas match the Australian ETL Developer and Data Engineer roles."),
  role("(big data|hadoop|spark) (engineer|developer)", "Big Data Engineer", "direct", "Big data work has the same meaning in Australia."),
  role("data (engineer|developer|pipeline engineer|integration engineer)", "Data Engineer", "direct", "Data Engineer has the same meaning in Australia."),
  role("database (administrator|admin|developer|engineer)|\\bdba\\b|sql developer", "Database Administrator", "direct",
    "Database work has the same meaning in Australia. Many teams ask for data engineering skills in the same role.",
    { gaps: ["Cloud data platforms (for example Snowflake or Databricks)"] }),
  role("\\bbi (specialist|executive|officer|consultant)|business intelligence (specialist|executive|officer|consultant)", "Data Analyst", "cross-border",
    "BI Specialist and BI Executive are common overseas titles. In Australia the same work (reports, dashboards, finding answers in data) is a Data Analyst role."),
  role("\\bmis (executive|analyst|officer|specialist|developer)|management information", "Data Analyst", "cross-border",
    "MIS titles overseas describe reporting and analysis of company data. In Australia this is a Data Analyst role."),
  role("(business intelligence|\\bbi) (analyst|developer)|power bi developer|tableau developer|report(ing)? (developer|analyst|specialist)", "Business Intelligence Analyst", "direct",
    "Business Intelligence Analyst has the same meaning in Australia."),
  role("data (analyst|analytics (specialist|executive))|analytics (analyst|executive|specialist)", "Data Analyst", "direct", "Data Analyst has the same meaning in Australia."),
  role("quantitative (analyst|researcher|developer)|\\bquant\\b", "Data Scientist", "cross-industry",
    "Quantitative work uses statistics and models on data. Australian Data Scientist roles ask for the same skills."),
  role("data scien(tist|ce (executive|specialist|engineer))|machine learning scientist", "Data Scientist", "direct", "Data Scientist has the same meaning in Australia."),
  role("business systems? analyst|(system|systems|functional|it business) analyst", "Business Systems Analyst", "cross-border",
    "Systems Analyst is a common overseas title. In Australia the same work is a Business Systems Analyst role."),
  role("business analyst|requirements analyst|\\bba\\b", "Business Analyst", "direct", "Business Analyst has the same meaning in Australia."),
  // The last choice: "Engineer", "Developer", "Staff Engineer" and "Software ..." titles. "Mechanical Engineer" is not an ICT title and gives no card.
  role("^(software |application |applications |systems )?(engineer|developer)$|^software ", "Software Engineer", "direct", "Software work has the same meaning in Australia.", { weak: true }),
];

// Skills that need a pair: another word or an overseas tool for a skill of the taxonomy. A name or alias of the taxonomy needs no pair.
const skill = (test, mapped, kind, reason) => ({ test: new RegExp(test), mapped, kind, reason });
const SKILL_PAIRS = [
  skill("spreadsheets?|google sheets|advanced excel|excel macros?", "Microsoft Excel", "direct", "Spreadsheet skills are listed as Microsoft Excel in most Australian job ads."),
  skill("kanban|sprint|backlog|stand-?ups?|scrum master|jira", "Agile delivery", "direct", "Backlogs, sprints and Kanban boards are part of agile delivery."),
  skill("qlik(view|sense)?|cognos|microstrategy|business objects|crystal reports|bi tools|reporting tools", "Data visualisation", "cross-border",
    "Overseas reporting and dashboard tools match the data visualisation skills that Australian job ads list as Power BI or Tableau."),
  skill("data (cleaning|cleansing|wrangling|preparation|munging)", "Data analysis", "direct", "Cleaning and preparing data is part of data analysis."),
  skill("predictive (model(l)?ing|analytics)|ml models?|machine-learning models?", "Machine learning", "direct", "Predictive models are what Australian job ads call machine learning."),
  skill("shell scripts?|unix scripting|linux administration|unix administration", "Linux", "direct", "Linux and Unix administration is listed as Linux in Australian job ads."),
  skill("web services|web apis?", "API design", "direct", "Building web services is what Australian job ads call API design."),
  skill("regression testing|test cases?|test plans?|test scripts?", "Manual testing", "direct", "Writing and running test cases by hand is manual testing."),
  skill("copilot|prompt writing|chatgpt prompts?", "Prompt engineering", "direct", "Writing prompts for AI models is called prompt engineering."),
  skill("leetcode|competitive programming", "Data structures and algorithms", "direct", "This is the skill that Australian job ads list as data structures and algorithms."),
  skill("solid principles|clean code", "Object-oriented design", "direct", "Design patterns and clean code are listed as object-oriented design."),
  skill("build automation|release management|deployment automation|ci ?/ ?cd|continuous (delivery|deployment)", "CI/CD", "direct", "Automated builds and releases are listed as CI/CD."),
  skill("container orchestration|openshift|helm", "Kubernetes", "direct", "Container orchestration is listed as Kubernetes."),
  skill("infrastructure automation|infrastructure[- ]as[- ]code", "Infrastructure as code", "direct", "Automating infrastructure is listed as infrastructure as code."),
  skill("alerting|splunk|datadog|new relic", "Observability", "direct", "Monitoring, logging and alerting are listed as observability."),
  skill("team management|managing (a )?team|line management|supervis(ing|ion)|people (and|&) team leadership", "Team leadership", "cross-industry",
    "Leading people transfers to any Australian role that leads a team, also in technology."),
  skill("training (junior|new)|onboarding (new|junior)|knowledge transfer", "Mentoring", "cross-industry", "Coaching and training colleagues is called mentoring."),
  skill("client communication|report writing", "Communication", "direct", "Communication has the same meaning in Australia."),
  skill("customer management|vendor management|supplier management|cross[- ](department|functional)", "Stakeholder management", "cross-industry",
    "Working with clients, vendors and other teams is what Australian employers call stakeholder management."),
  skill("project (coordination|planning|delivery)|\\bpmo\\b|prince2|waterfall", "Project management", "direct", "Planning and delivering projects is project management."),
  skill("root cause|incident (debugging|analysis)|bug fixing", "Debugging and troubleshooting", "direct", "Finding and fixing faults is listed as debugging and troubleshooting."),
  skill("escalation|issue resolution|problem resolution", "Problem solving", "direct", "Fixing escalated issues shows problem solving."),
  skill("process mapping|use cases?|business requirements|\\bbrd\\b", "Requirements analysis", "direct", "These are standard requirements analysis tasks."),
  skill("documentation|confluence|api docs", "Technical documentation", "direct", "Writing guides and specifications is technical documentation."),
  skill("hypothesis testing|regression analysis|\\bspss\\b|\\bstata\\b|\\bsas\\b", "Statistics", "cross-border",
    "Statistical analysis and tools such as SPSS or SAS are listed as statistics in Australian job ads."),
  skill("data integration|pentaho|ssis|informatica|datastage|talend", "ETL and ELT pipelines", "cross-border",
    "Overseas integration tools and data pipelines match the ETL and ELT skills of Australian job ads."),
  skill("star schema|dimensional model", "Data warehousing", "direct", "Data warehouse design has the same meaning in Australia."),
  skill("er diagrams?|schema design|database schema|entity[- ]relationship", "Data modelling", "direct", "Designing schemas is data modelling."),
  skill("database tuning|performance tuning|indexing", "Database design and tuning", "direct", "Tuning queries and indexes is database design and tuning."),
  skill("data protection|privacy compliance", "Data privacy and compliance", "cross-border",
    "Data protection rules overseas (for example GDPR) match the privacy and compliance skills that Australian employers ask for."),
  skill("pen[- ]?tests?|vulnerability (assessment|scanning)", "Penetration testing", "direct", "Testing systems for weak points is penetration testing."),
  skill("ldap|active directory|single sign[- ]on|identity management", "Authentication and authorisation", "direct", "Identity and access work is listed as authentication and authorisation."),
  skill("\\bcnn\\b|\\brnn\\b|deep nets?", "Deep learning", "direct", "Neural networks are deep learning."),
  skill("image (processing|recognition|classification)", "Computer vision", "direct", "Working with images is computer vision."),
  skill("sentiment analysis|chatbots?", "Natural language processing", "direct", "Working with text is natural language processing."),
  skill("collaborative filtering", "Recommender systems", "direct", "Recommendation engines are recommender systems."),
  skill("ml pipelines?|machine learning pipelines?", "MLOps", "direct", "Deploying and running models is MLOps."),
];

// Indicative AQF levels. Not a formal assessment (PRD: formal credential verification is out of scope).
const AQF = [
  [/doctor|phd/, "AQF Level 10 (Doctoral degree)"], [/master|mba/, "AQF Level 9 (Masters degree)"],
  [/graduate (certificate|diploma)/, "AQF Level 8 (Graduate certificate or diploma)"], [/honours/, "AQF Level 8 (Bachelor honours degree)"],
  [/bachelor/, "AQF Level 7 (Bachelor degree)"], [/advanced diploma|associate degree/, "AQF Level 6"],
  [/\bdiploma\b/, "AQF Level 5 (Diploma)"], [/certificate (iii|iv)/, "AQF Level 3–4 (Certificate III or IV)"],
];
export const aqfOf = (q) => (AQF.find(([re]) => re.test(lower(q))) || [])[1] || "";

// A short id part from letters and digits. "C#" and "C++" give the same letters, so the caller adds a hash when two names collide.
const slug = (s) => lower(s).replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const hash = (s) => { let h = 5381; for (const c of String(s)) h = ((h << 5) + h + c.charCodeAt(0)) | 0; return (h >>> 0).toString(16).slice(0, 6); };

// Words that show a level in a title. They are not part of the role.
const LEVEL_WORDS = /\b(intern(ship)?|trainee|junior|jr|jnr|graduate|grad|senior|sr|snr|lead|principal|staff|mid[- ]?level|ii|iii|iv)\b\.?/g;
// "Senior Data Engineer, Lakehouse (Vietnam)" gives "data engineer": no place in brackets, no company, no level word
const roleBase = (title) => lower(title).replace(/\([^)]*\)/g, " ").split(/\s[-–—@|]\s|,|\sat\s/)[0].replace(LEVEL_WORDS, " ").replace(/\s+/g, " ").trim().replace(/^-+|-+$/g, "").replace(/\.+$/, "");

// The typed skills: a name, or { name, level, years }. The level and the years that the talent gave are kept (key: lower case name).
function typedSkills(p) {
  const out = new Map();
  for (const s of [...list(p.skillLevels), ...list(p.skills)]) {
    if (!s || typeof s !== "object" || !s.name) continue;
    const level = Number.isInteger(s.level) && s.level >= 1 && s.level <= 5 ? s.level : null;
    const years = typeof s.years === "number" && s.years >= 0 && s.years <= 40 ? s.years : null;
    out.set(lower(s.name), { level, years });
    const canon = canonicalSkillName(s.name);
    if (canon) out.set(lower(canon), { level, years });
  }
  return out;
}
const skillNames = (p) => [...new Set(list(p.skills).map((s) => String(s && typeof s === "object" ? s.name : s || "").trim()).filter(Boolean))];

/**
 * @param {object} profile  Profile (lists). `skills` can be names or { name, level, years }.
 * @param {string[]} evidence  CV evidence lines (private to the candidate)
 * @returns {{ skills: TranslatedSkill[], gaps: string[] }}
 */
export function translate(profile, evidence = []) {
  const p = profile || {};
  const ev = list(evidence).map(String);
  const fromCv = ev.length > 0;
  const overseas = list(p.studyCountry).some((c) => c && c !== "Australia");
  const typed = typedSkills(p);
  const out = new Map();
  const gaps = new Set();

  const RANK = { Limited: 0, Moderate: 1, Strong: 2 };
  // The first evidence line that shows this skill or role: by the pattern of the pair, by the taxonomy name, or by the words of the talent
  const lineFor = (re, mapped, original) => ev.find((line) => {
    const low = lower(line);
    if (re && re.test(low)) return true;
    if (skillsIn(line).includes(mapped)) return true;
    return [mapped, original].some((w) => lower(w).length > 3 && new RegExp(`(?:^|[^a-z0-9])${escRe(lower(w))}(?![a-z0-9])`).test(low));
  });

  const add = (item, original, source, re = null) => {
    let id = `${slug(item.mapped)}--${slug(original)}`;
    if (out.has(id) && out.get(id).mapped !== item.mapped) id += `-${hash(`${item.mapped}|${original}`)}`;
    const line = lineFor(re, item.mapped, original);
    // Evidence: Strong = a CV line shows it; Moderate = a role or a skill that the candidate gave; Limited = only a title
    const evidenceLevel = line ? "Strong" : source === "skill" ? "Moderate" : fromCv ? "Moderate" : "Limited";
    const own = source === "skill" ? typed.get(lower(item.mapped)) || typed.get(lower(original)) || null : null;
    // One card for each taxonomy name. A second source can make the evidence stronger.
    const same = [...out.values()].find((s) => s.mapped === item.mapped && s.source === source);
    if (same) {
      if (RANK[evidenceLevel] > RANK[same.evidence]) {
        same.evidence = evidenceLevel;
        same.evidenceText = line || same.evidenceText;
        if (source === "skill" && !(own && own.level)) same.level = EVIDENCE_LEVEL[evidenceLevel];
      }
      if (own && own.level && own.level > (same.level || 0)) same.level = own.level;
      if (own && own.years != null && own.years > (same.years || 0)) same.years = own.years;
      if (!same.original.includes(original)) same.original += `; ${original}`;
      return;
    }
    out.set(id, {
      id, source, original, mapped: item.mapped, kind: item.kind,
      anzsco: item.anzsco || "", occupation: item.occupation || "",
      reason: item.reason, evidence: evidenceLevel, evidenceText: line || "",
      status: "suggested",
      level: source === "skill" ? (own && own.level) || EVIDENCE_LEVEL[evidenceLevel] : null,
      years: source === "skill" && own ? own.years : null,
    });
    list(item.gaps).forEach((g) => gaps.add(g));
  };

  // ----- roles: a pair for an overseas title, a title of the role list, the other pairs, a general pair -----
  for (const original of list(p.currentRole).map(String)) {
    const base = roleBase(original);
    if (!base) continue;
    const hasPlace = /\([^)]*\)/.test(original);
    let found = ROLE_PAIRS.find((i) => i.overseas && (hasPlace || overseas) && i.test.test(base));
    if (found) found = { ...found, kind: "cross-border" };
    if (!found && ROLE_BY_LOWER.has(base)) {
      const exact = ROLE_BY_LOWER.get(base);
      found = { mapped: exact, kind: "direct", ...occupationOf(exact), reason: `${exact} has the same meaning in Australia.` };
    }
    if (!found) found = ROLE_PAIRS.find((i) => !i.overseas && !i.weak && i.test.test(base));
    if (!found) { const weak = ROLE_PAIRS.find((i) => i.weak && i.test.test(base)); if (weak) found = { ...weak, kind: "direct" }; }
    if (found) add(found, original, "role", found.test || null);
  }

  // ----- skills: the name or alias of the taxonomy, a pair of the library, or the name as it is -----
  for (const name of skillNames(p)) {
    const canon = canonicalSkillName(name);
    if (canon) {
      add({ mapped: canon, kind: "direct", reason: lower(canon) === lower(name) ? `${canon} has the same name in Australia.` : `Australian job ads list this skill as ${canon}.` }, name, "skill");
      continue;
    }
    const hit = SKILL_PAIRS.find((i) => i.test.test(lower(name)));
    if (hit) { add(hit, name, "skill", hit.test); continue; }
    const shown = skillsIn(name);
    // A skill with no translation keeps its name, so the candidate can still choose to share it
    if (shown.length === 1) add({ mapped: shown[0], kind: "direct", reason: `Australian job ads list this skill as ${shown[0]}.` }, name, "skill");
    else add({ mapped: name, kind: "direct", reason: "Australian employers use the same name for this skill." }, name, "skill", new RegExp(escRe(lower(name))));
  }

  // ----- qualifications: indicative AQF level -----
  for (const q of list(p.qualification)) {
    const level = aqfOf(q);
    if (!level) continue;
    const id = `aqf--${slug(q)}`;
    out.set(id, {
      id, source: "qualification", original: q + (overseas ? " (overseas)" : ""), mapped: level, kind: overseas ? "cross-border" : "direct",
      anzsco: "", occupation: "", reason: overseas
        ? "Qualifications of this type from overseas are usually close to this Australian (AQF) level. This is a guide, not a formal assessment."
        : "This is the Australian Qualifications Framework (AQF) level of this qualification.",
      evidence: fromCv ? "Moderate" : "Limited", evidenceText: "", status: "suggested", level: null, years: null,
    });
  }
  return { skills: [...out.values()], gaps: [...gaps] };
}
