"""
Skill Bridge - Large-Scale Australian Job & Candidate Data Exporter
===================================================================
Exports real-world Australian job listings (via Adzuna AU REST API)
and international candidate profiles into clean CSV formats for UI & Engineering teams.
"""

import os
import ssl
import json
import csv
import re
import urllib.request
import urllib.parse
from typing import List, Dict, Any

APP_ID = os.getenv("ADZUNA_APP_ID", "e53715ce")
APP_KEY = os.getenv("ADZUNA_APP_KEY", "075eb766a5b9cb69a9c026fbbeaa9283")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Query configurations across diverse Australian industries
JOB_QUERIES = [
    {"what": "Registered Nurse", "where": "Sydney", "category": "Healthcare & Nursing", "anzsco": "ANZSCO 254411 (Registered Nurse)"},
    {"what": "Clinical Care Coordinator", "where": "Melbourne", "category": "Healthcare & Nursing", "anzsco": "ANZSCO 254499 (Nurse / Healthcare Coordinator)"},
    {"what": "Financial Accountant", "where": "Melbourne", "category": "Finance & Accounting", "anzsco": "ANZSCO 221111 (Accountant)"},
    {"what": "Auditor", "where": "Sydney", "category": "Finance & Accounting", "anzsco": "ANZSCO 221211 (Auditor)"},
    {"what": "Marketing Specialist", "where": "Sydney", "category": "Marketing & Communications", "anzsco": "ANZSCO 225113 (Marketing Specialist)"},
    {"what": "Digital Marketing Lead", "where": "Melbourne", "category": "Marketing & Communications", "anzsco": "ANZSCO 225111 (Advertising & Marketing Specialist)"},
    {"what": "Supply Chain Coordinator", "where": "Melbourne", "category": "Supply Chain & Logistics", "anzsco": "ANZSCO 133611 (Supply Chain Coordinator)"},
    {"what": "Warehouse Operations Supervisor", "where": "Sydney", "category": "Supply Chain & Logistics", "anzsco": "ANZSCO 133612 (Procurement & Logistics Manager)"},
    {"what": "Civil Engineer", "where": "Brisbane", "category": "Engineering & Construction", "anzsco": "ANZSCO 233211 (Civil Engineer)"},
    {"what": "Structural Engineer", "where": "Perth", "category": "Engineering & Construction", "anzsco": "ANZSCO 233214 (Structural Engineer)"},
    {"what": "Operations Coordinator", "where": "Sydney", "category": "Operations & Administration", "anzsco": "ANZSCO 511112 (Program / Operations Coordinator)"},
    {"what": "Business Operations Analyst", "where": "Melbourne", "category": "Operations & Administration", "anzsco": "ANZSCO 224711 (Management / Organisation Analyst)"},
    {"what": "Data Engineer", "where": "Sydney", "category": "Technology & Data", "anzsco": "ANZSCO 261313 (Data Engineer)"},
    {"what": "Software Developer", "where": "Melbourne", "category": "Technology & Data", "anzsco": "ANZSCO 261312 (Developer Programmer)"},
    {"what": "Hotel Operations Manager", "where": "Sydney", "category": "Hospitality & Service", "anzsco": "ANZSCO 141999 (Accommodations & Hospitality Manager)"}
]

def fetch_live_jobs() -> List[Dict[str, Any]]:
    print(f"[*] Fetching live jobs from Adzuna Australia across {len(JOB_QUERIES)} sectors...")
    collected_jobs = []
    
    for item in JOB_QUERIES:
        params = {
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "what": item["what"],
            "where": item["where"],
            "results_per_page": 5, # 5 per query = ~75 jobs total
            "content-type": "application/json"
        }
        url = "https://api.adzuna.com/v1/api/jobs/au/search/1?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "SkillBridge-AU-Ingest/1.0"})
        
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                results = data.get("results", [])
                print(f"   [+] {item['category']} ('{item['what']}' in {item['where']}): Ingested {len(results)} jobs.")
                
                for j in results:
                    sal_min = j.get("salary_min")
                    sal_max = j.get("salary_max")
                    if sal_min and sal_max:
                        salary_display = f"${int(sal_min):,} - ${int(sal_max):,} AUD"
                    elif sal_min:
                        salary_display = f"From ${int(sal_min):,} AUD"
                    else:
                        salary_display = "Market Competitive (AUD)"

                    clean_desc = re.sub(r"<[^>]+>", " ", j.get("description", ""))
                    clean_desc = " ".join(clean_desc.split())

                    sentences = [s.strip() for s in clean_desc.split(".") if len(s.strip()) > 15]
                    reqs = " | ".join(sentences[:4]) if sentences else "Relevant commercial experience | Stakeholder communication"

                    collected_jobs.append({
                        "job_id": f"adzuna_{j.get('id')}",
                        "title": j.get("title", ""),
                        "company": j.get("company", {}).get("display_name", "Australian Employer"),
                        "location": j.get("location", {}).get("display_name", item["where"]),
                        "industry_category": item["category"],
                        "anzsco_code": item["anzsco"],
                        "employment_type": "Full-time",
                        "salary_range": salary_display,
                        "salary_min": sal_min or "",
                        "salary_max": sal_max or "",
                        "key_requirements": reqs,
                        "description": clean_desc,
                        "source_platform": "SEEK / Indeed (via Adzuna AU)",
                        "posting_url": j.get("redirect_url", ""),
                        "date_posted": j.get("created", "")
                    })
        except Exception as e:
            print(f"   [!] Error on {item['what']}: {e}")

    return collected_jobs

def get_comprehensive_candidate_pool() -> List[Dict[str, Any]]:
    return [
        {
            "candidate_id": "CAND-001",
            "full_name": "Minh Tran",
            "origin_country": "Vietnam 🇻🇳",
            "target_country": "Australia 🇦🇺",
            "industry_category": "Operations & Logistics",
            "original_job_title": "Operations Team Lead",
            "original_company": "Saigon Service Group (Ho Chi Minh City)",
            "years_of_experience": 4.8,
            "education": "Bachelor of International Business - Foreign Trade University (FTU)",
            "anzsco_code": "511112",
            "anzsco_occupation": "Program and Project / Operations Coordinator",
            "direct_skills": "People & Team Leadership (12 staff) | Warehouse Escalation Resolution",
            "transferable_skills": "SLA Tracking & Reporting | Cross-Department Coordination | Vendor Management",
            "skill_evidence_excerpts": "Managed 12-person customer operations team; resolved inventory delivery bottlenecks between central warehouse and retail branches; built weekly Google Sheets SLA tracking models.",
            "honest_gaps": "Australian Workplace Health & Safety (WHS) legislative frameworks; Enterprise Jira Automation.",
            "transferability_rationale": "Directly transfers to Australian logistics and operations coordination roles requiring multi-party stakeholder alignment and fast-paced delivery governance."
        },
        {
            "candidate_id": "CAND-002",
            "full_name": "Elena Rostova",
            "origin_country": "Germany 🇩🇪",
            "target_country": "Australia 🇦🇺",
            "industry_category": "Finance & Accounting",
            "original_job_title": "Senior Financial Accountant",
            "original_company": "Berlin FinServices GmbH",
            "years_of_experience": 5.5,
            "education": "Master of Science in Accounting & Corporate Finance - Humboldt University Berlin",
            "anzsco_code": "221111",
            "anzsco_occupation": "Accountant (General) / Corporate Auditor",
            "direct_skills": "IFRS Statutory Financial Reporting | Multi-Currency Ledger Reconciliation | SAP ERP",
            "transferable_skills": "Budget Variance Modeling | Cash Flow Forecasting | Internal Audit Governance",
            "skill_evidence_excerpts": "Prepared quarterly IFRS financial statements and led annual corporate audits for €45M entity; reconciled 4 subsidiary balance sheets across multi-currency accounts.",
            "honest_gaps": "Australian Taxation Office (ATO) legislation; Business Activity Statements (BAS) & GST reporting; CPA Australia local charter conversion.",
            "transferability_rationale": "German IFRS corporate reporting is directly equivalent to Australian Accounting Standards Board (AASB) frameworks, enabling immediate ledger reconciliation capability."
        },
        {
            "candidate_id": "CAND-003",
            "full_name": "Amara Okafor",
            "origin_country": "Nigeria 🇳🇬 / UK 🇬🇧",
            "target_country": "Australia 🇦🇺",
            "industry_category": "Healthcare & Nursing",
            "original_job_title": "Senior Clinical Care Nurse Specialist",
            "original_company": "St. Mary's NHS Foundation Trust (London)",
            "years_of_experience": 6.0,
            "education": "Bachelor of Nursing Science (BNSc) - University of Ibadan; Registered Nurse (NMC UK)",
            "anzsco_code": "254411",
            "anzsco_occupation": "Registered Nurse (Medical & Surgical)",
            "direct_skills": "Emergency Patient Triage | Acute Medication Administration | Clinical Care Plan Governance",
            "transferable_skills": "Multidisciplinary Discharge Pathways | Infection Prevention Protocols | Ward Mentorship",
            "skill_evidence_excerpts": "Managed acute surgical admissions ward delivering clinical triage and individualized patient care plans under statutory NHS healthcare regulations.",
            "honest_gaps": "AHPRA Australian nursing registration bridging assessment; Australian Pharmaceutical Benefits Scheme (PBS) and Medicare claim workflows.",
            "transferability_rationale": "High-volume NHS acute clinical care experience transfers 1:1 to Australian state hospital networks and private healthcare providers."
        },
        {
            "candidate_id": "CAND-004",
            "full_name": "Marcus Vance",
            "origin_country": "United Kingdom 🇬🇧",
            "target_country": "Australia 🇦🇺",
            "industry_category": "Marketing & Communications",
            "original_job_title": "Brand & Digital Campaign Marketing Lead",
            "original_company": "Manchester Retail Media Ltd",
            "years_of_experience": 4.2,
            "education": "BA (Hons) in Marketing & Digital Media - University of Manchester",
            "anzsco_code": "225113",
            "anzsco_occupation": "Marketing Specialist / Campaign Lead",
            "direct_skills": "Multi-Channel Digital Strategy | Performance Marketing & Attribution | GA4 & Tableau",
            "transferable_skills": "Creative Agency Management | Funnel ROI Optimization | Stakeholder Commercial Storytelling",
            "skill_evidence_excerpts": "Managed £1.2M annual marketing budget across paid search, programmatic and social; drove 34% qualified inbound growth through customer journey optimization.",
            "honest_gaps": "Australian Consumer Law (ACCC / Ad Standards guidelines); Local Australian media publisher and influencer ecosystems.",
            "transferability_rationale": "Performance digital marketing methodologies and funnel economics are universally applicable to Australian corporate and agency environments."
        },
        {
            "candidate_id": "CAND-005",
            "full_name": "Priya Sharma",
            "origin_country": "India 🇮🇳",
            "target_country": "Australia 🇦🇺",
            "industry_category": "Technology & Data",
            "original_job_title": "Lead Software Engineer (Big Data & Analytics)",
            "original_company": "Tech Mahindra (Pune)",
            "years_of_experience": 5.2,
            "education": "B.Tech in Computer Science - Pune University",
            "anzsco_code": "261313",
            "anzsco_occupation": "Software Engineer / Data Engineer",
            "direct_skills": "Cloud Data Platforms (AWS Glue/S3/EMR) | Streaming Pipelines (Apache Kafka) | SQL Optimization",
            "transferable_skills": "Distributed Systems Architecture | Agile Backlog Grooming | CI/CD DevOps Automation",
            "skill_evidence_excerpts": "Architected streaming ETL data pipelines ingesting 50M+ records daily; optimized query execution plans reducing compute cluster expenditures by 35%.",
            "honest_gaps": "Snowflake & dbt production ecosystems (primarily AWS native stack); Australian enterprise cybersecurity frameworks (IRAP / Essential 8).",
            "transferability_rationale": "Large-scale distributed data pipeline design directly meets the requirements of Australian tech scale-ups and financial institutions."
        },
        {
            "candidate_id": "CAND-006",
            "full_name": "Mateo Hernandez",
            "origin_country": "Colombia 🇨🇴 / Spain 🇪🇸",
            "target_country": "Australia 🇦🇺",
            "industry_category": "Engineering & Construction",
            "original_job_title": "Senior Civil Project Engineer",
            "original_company": "Ferrovial Agroman (Madrid)",
            "years_of_experience": 7.0,
            "education": "Civil Engineering Degree (BSc & MSc) - Universidad Politécnica de Madrid",
            "anzsco_code": "233211",
            "anzsco_occupation": "Civil Engineer / Infrastructure Project Engineer",
            "direct_skills": "Structural Design Analysis (AutoCAD Civil 3D) | Reinforced Concrete Quality Auditing | Site QA/QC",
            "transferable_skills": "Subcontractor Procurement | Contractor Safety Compliance | Primavera P6 Scheduling",
            "skill_evidence_excerpts": "Supervised civil infrastructure works on €60M urban rail tunnel project; verified structural reinforcement bar compliance and managed site subcontractors.",
            "honest_gaps": "Engineers Australia Stage 1 CDR migration skills assessment; Australian Standards (AS/NZS 1170 structural design codes).",
            "transferability_rationale": "European heavy infrastructure engineering standards provide rigorous technical rigor that translates directly to Australian transport and mining projects."
        },
        {
            "candidate_id": "CAND-007",
            "full_name": "Kenji Tanaka",
            "origin_country": "Japan 🇯🇵",
            "target_country": "Australia 🇦🇺",
            "industry_category": "Hospitality & Service",
            "original_job_title": "Guest Experience & Operations Manager",
            "original_company": "Park Hyatt Tokyo",
            "years_of_experience": 5.0,
            "education": "Bachelor of Hospitality Management - Rikkyo University (Tokyo)",
            "anzsco_code": "141999",
            "anzsco_occupation": "Accommodations and Hospitality Manager",
            "direct_skills": "Five-Star Luxury Guest Services | Front Office Operations (Opera PMS) | VIP Relationship Management",
            "transferable_skills": "Shift Scheduling & Staff Mentorship | Crisis Escalation Handling | Service Quality Auditing",
            "skill_evidence_excerpts": "Managed 25-person front office and concierge staff in 178-room luxury property; achieved 98.4% Net Promoter Score (NPS) across corporate traveler segment.",
            "honest_gaps": "Responsible Service of Alcohol (RSA NSW/VIC certificate); Australian Fair Work modern hospitality award regulations.",
            "transferability_rationale": "World-class Japanese hospitality standards (Omotenashi) and front office operations transfer seamlessly to Australia's premium luxury hotels and resorts."
        },
        {
            "candidate_id": "CAND-008",
            "full_name": "Fatima Al-Hassan",
            "origin_country": "Jordan 🇯🇴 / UAE 🇦🇪",
            "target_country": "Australia 🇦🇺",
            "industry_category": "Operations & Administration",
            "original_job_title": "Regional Procurement & Sourcing Coordinator",
            "original_company": "Aramex Logistics (Dubai)",
            "years_of_experience": 4.5,
            "education": "BSc in Supply Chain Management - American University of Sharjah",
            "anzsco_code": "133612",
            "anzsco_occupation": "Procurement and Supply Manager",
            "direct_skills": "Vendor Contract Negotiation | Strategic Sourcing (RFP/RFQ) | Oracle NetSuite ERP",
            "transferable_skills": "Supplier Risk Evaluation | Spend Analytics | Cost Optimization Modeling",
            "skill_evidence_excerpts": "Negotiated commercial procurement contracts across 14 Middle East freight hubs; reduced supplier freight operational costs by 18% through volume consolidation.",
            "honest_gaps": "Australian Modern Slavery Act corporate compliance reporting; Australian Contract Law specifics.",
            "transferability_rationale": "High-volume international freight procurement rigor transfers directly to Australian mining, retail, and FMCG supply chains."
        }
    ]

def main():
    print("=" * 65)
    print("  Skill Bridge - Large-Scale Australian Datasets Exporter")
    print("=" * 65)
    
    os.makedirs("data", exist_ok=True)

    # 1. Collect Jobs
    jobs = fetch_live_jobs()
    if not jobs:
        print("[!] Live fetch returned empty, preserving existing jobs...")
        if os.path.exists("data/australian_jobs.json"):
            with open("data/australian_jobs.json", "r", encoding="utf-8") as f:
                jobs = json.load(f)

    # 2. Export Jobs to CSV
    jobs_csv_path = "data/australian_jobs_dataset.csv"
    if jobs:
        headers = list(jobs[0].keys())
        with open(jobs_csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(jobs)
        print(f"[✓] EXPORTED: {len(jobs)} Australian Jobs to '{jobs_csv_path}'")

        # Save JSON as well
        with open("data/australian_jobs.json", "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)

    # 3. Collect Candidates
    candidates = get_comprehensive_candidate_pool()
    cand_csv_path = "data/international_candidates_dataset.csv"
    headers = list(candidates[0].keys())
    with open(cand_csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(candidates)
    print(f"[✓] EXPORTED: {len(candidates)} International Candidates to '{cand_csv_path}'")

    # Format Candidates for JSON UI compatibility
    json_candidates = []
    for c in candidates:
        directs = [d.strip() for d in c["direct_skills"].split("|")]
        transfers = [t.strip() for t in c["transferable_skills"].split("|")]
        
        skill_items = []
        for d in directs:
            skill_items.append({"name": d, "type": "Direct", "evidence": c["skill_evidence_excerpts"][:85] + "..."})
        for t in transfers:
            skill_items.append({"name": t, "type": "Transferable", "evidence": c["skill_evidence_excerpts"][:85] + "..."})

        json_candidates.append({
            "id": c["candidate_id"],
            "name": c["full_name"],
            "origin": f"{c['origin_country']} → {c['target_country']}",
            "avatar": "".join([part[0] for part in c["full_name"].split()[:2]]).upper(),
            "category": c["industry_category"],
            "targetRole": c["anzsco_occupation"],
            "originRole": f"{c['original_job_title']} @ {c['original_company']} ({c['years_of_experience']} yrs)",
            "skills": skill_items,
            "gaps": c["honest_gaps"]
        })

    with open("data/australian_candidates.json", "w", encoding="utf-8") as f:
        json.dump(json_candidates, f, indent=2, ensure_ascii=False)

    print("\n[+] SUCCESS! Both CSV datasets exported and ready to send to teammates.")

if __name__ == "__main__":
    main()
