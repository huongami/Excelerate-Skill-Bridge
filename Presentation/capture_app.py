import subprocess, time, json, urllib.request, asyncio, websockets, base64, tempfile, os

def get_token(email, pw):
    req = urllib.request.Request('http://localhost:8095/api/auth/login',
        data=json.dumps({'email': email, 'password': pw}).encode(),
        headers={'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(req).read().decode())['token']

cand_token = get_token('candidate@demo.jinder.app', 'z4CJiNScZXnU')
rec_token = get_token('recruiter@demo.jinder.app', 'Jpr0N8Jtadqo')

user_data = tempfile.mkdtemp()
chrome_proc = subprocess.Popen([
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '--headless',
    '--disable-gpu',
    '--remote-debugging-port=9335',
    f'--user-data-dir={user_data}',
    '--window-size=1920,1080',
    'about:blank'
])

time.sleep(2.5)

async def run():
    tabs = json.loads(urllib.request.urlopen('http://localhost:9335/json').read().decode())
    ws_url = tabs[0]['webSocketDebuggerUrl']
    async with websockets.connect(ws_url) as ws:
        async def call(method, params=None):
            cid = int(time.time()*1000) % 100000
            await ws.send(json.dumps({'id': cid, 'method': method, 'params': params or {}}))
            while True:
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=10.0))
                if msg.get('id') == cid:
                    return msg.get('result', {})

        await call('Page.enable')

        async def capture_page(token, hash_path, filename):
            if token:
                js = f'''
                localStorage.setItem("jinder.session", JSON.stringify({{ token: "{token}" }}));
                sessionStorage.removeItem("jinder.session");
                window.location.href = "http://localhost:8095/{hash_path}";
                '''
            else:
                js = f'''
                localStorage.clear();
                sessionStorage.clear();
                window.location.href = "http://localhost:8095/{hash_path}";
                '''
            await call('Runtime.evaluate', {'expression': js})
            await asyncio.sleep(2.5)
            res = await call('Page.captureScreenshot', {'format': 'png'})
            img_data = base64.b64decode(res['data'])
            out_path = f'Presentation/audio/{filename}'
            with open(out_path, 'wb') as f:
                f.write(img_data)
            print(f'Captured {filename}: {len(img_data)} bytes')

        # 1. Login screen
        await capture_page(None, '#/login', 'app_01_login.png')

        # 2. Talent Home (Linh Nguyen Profile, Radar & Recommendations)
        await capture_page(cand_token, '#/home', 'app_02_talent_home.png')

        # 3. Talent Jobs Feed (Ranked Matches with FRS)
        await capture_page(cand_token, '#/jobs', 'app_03_jobs_feed.png')

        # 4. Talent Job Detail (Capability Overlap & Blockers)
        await capture_page(cand_token, '#/jobs/job-da-001', 'app_04_job_detail.png')

        # 5. Employer Candidates View (Anonymized Wildlife Cards)
        await capture_page(rec_token, '#/candidates', 'app_05_wildlife_cards.png')

        # 6. Employer Candidate Detail (Teal Heron / AQF Level 7 Evidence)
        await capture_page(rec_token, '#/candidates/cand-001', 'app_06_candidate_detail.png')

        # 7. Multi-Profile Compare Tray
        await capture_page(rec_token, '#/compare?ids=cand-001,cand-002', 'app_07_compare_tray.png')

try:
    asyncio.run(run())
finally:
    chrome_proc.terminate()
    print("Done capturing app screens!")
