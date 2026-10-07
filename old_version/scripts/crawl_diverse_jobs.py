import ssl
import urllib.request
import urllib.parse
import json
import re

app_id = 'e53715ce'
app_key = '075eb766a5b9cb69a9c026fbbeaa9283'

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

categories_to_query = [
    {
        'category': 'Healthcare & Nursing',
        'query': 'Registered Nurse',
        'location': 'Sydney',
        'anzsco': 'ANZSCO 254411 (Registered Nurse)'
    },
    {
        'category': 'Finance & Accounting',
        'query': 'Accountant',
        'location': 'Melbourne',
        'anzsco': 'ANZSCO 221111 (Accountant / Financial Auditor)'
    },
    {
        'category': 'Marketing & Communications',
        'query': 'Marketing Manager',
        'location': 'Sydney',
        'anzsco': 'ANZSCO 225113 (Marketing Specialist)'
    },
    {
        'category': 'Supply Chain & Logistics',
        'query': 'Supply Chain Coordinator',
        'location': 'Melbourne',
        'anzsco': 'ANZSCO 133611 (Supply Chain & Logistics Coordinator)'
    },
    {
        'category': 'Engineering & Construction',
        'query': 'Civil Engineer',
        'location': 'Brisbane',
        'anzsco': 'ANZSCO 233211 (Civil Engineer)'
    },
    {
        'category': 'Operations & Management',
        'query': 'Operations Coordinator',
        'location': 'Sydney',
        'anzsco': 'ANZSCO 511112 (Program / Operations Coordinator)'
    },
    {
        'category': 'Technology & Data',
        'query': 'Data Engineer',
        'location': 'Sydney',
        'anzsco': 'ANZSCO 261313 (Data Engineer)'
    }
]

all_jobs = []

for item in categories_to_query:
    params = {
        'app_id': app_id,
        'app_key': app_key,
        'what': item['query'],
        'where': item['location'],
        'results_per_page': 2,
        'content-type': 'application/json'
    }
    url = 'https://api.adzuna.com/v1/api/jobs/au/search/1?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': 'SkillBridge-AU/1.0'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            results = data.get('results', [])
            print(f"Fetched {len(results)} jobs for {item['category']}")
            for j in results:
                sal_min = j.get('salary_min')
                sal_max = j.get('salary_max')
                if sal_min and sal_max:
                    salary_str = f"${int(sal_min):,} - ${int(sal_max):,}"
                elif sal_min:
                    salary_str = f"From ${int(sal_min):,}"
                else:
                    salary_str = 'Market Competitive (AUD)'

                clean_desc = re.sub(r'<[^>]+>', ' ', j.get('description', ''))
                clean_desc = ' '.join(clean_desc.split())

                sentences = [s.strip() for s in clean_desc.split('.') if len(s.strip()) > 15]
                reqs = sentences[:3] if sentences else ['Relevant commercial experience', 'Strong stakeholder communication']

                all_jobs.append({
                    'id': f"adzuna_{j.get('id')}",
                    'title': j.get('title'),
                    'company': j.get('company', {}).get('display_name', 'Australian Employer'),
                    'location': f"{j.get('location', {}).get('display_name', item['location'])} (Australia)",
                    'employment_type': 'Full-time',
                    'salary': salary_str,
                    'category': item['category'],
                    'anzsco': item['anzsco'],
                    'description': clean_desc,
                    'requirements': reqs,
                    'source': 'SEEK / Indeed (via Adzuna AU)',
                    'redirect_url': j.get('redirect_url'),
                    'created': j.get('created'),
                    'live_fetched': True
                })
    except Exception as e:
        print('Error fetching', item['category'], e)

# Save to data/australian_jobs.json
with open('data/australian_jobs.json', 'w', encoding='utf-8') as f:
    json.dump(all_jobs, f, indent=2, ensure_ascii=False)
print('Total diverse jobs saved:', len(all_jobs))
