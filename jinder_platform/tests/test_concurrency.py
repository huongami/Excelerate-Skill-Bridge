"""Many users at the same time: no "database is locked", no 5xx, no lost bookmark."""
import threading
import unittest

import helpers as H


class ConcurrencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()
        cls.api = cls.p.api

    def test_parallel_users(self):
        users = [self.p.sign_up_and_in() for _ in range(8)]
        s, r = self.api.call("GET", "/jobs?pageSize=6", token=users[0]["token"])
        job_ids = [j["id"] for j in r["items"]]
        statuses = []
        lock = threading.Lock()

        def work(u):
            codes = []
            for jid in job_ids:
                codes.append(self.api.call("PUT", f"/bookmarks/{jid}", token=u["token"])[0])
                codes.append(self.api.call("GET", "/jobs?pageSize=5", token=u["token"])[0])
                codes.append(self.api.call("GET", f"/jobs/{jid}", token=u["token"])[0])
                codes.append(self.api.call("PUT", f"/jobs/{jid}/skip", token=u["token"])[0])
                codes.append(self.api.call("POST", "/reports", {"targetType": "job", "targetId": jid, "reason": "other"}, token=u["token"])[0])
                codes.append(self.api.call("GET", "/notifications", token=u["token"])[0])
            with lock:
                statuses.extend(codes)

        threads = [threading.Thread(target=work, args=(u,)) for u in users]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=120)
        self.assertEqual(len(statuses), len(users) * len(job_ids) * 6)
        self.assertEqual(set(statuses), {200})
        for u in users:
            s, b = self.api.call("GET", "/bookmarks", token=u["token"])
            self.assertEqual(len(b["items"]), len(job_ids))

    def test_parallel_applications_to_one_job_are_unique(self):
        from test_talent_flow import onboard
        t = self.p.sign_up_and_in()
        onboard(self.p, t)
        s, r = self.api.call("GET", "/jobs?pageSize=1", token=t["token"])
        jid = r["items"][0]["id"]
        codes = []

        def apply():
            codes.append(self.api.call("POST", "/applications", {"jobId": jid}, token=t["token"])[0])

        threads = [threading.Thread(target=apply) for _ in range(6)]
        for th in threads:
            th.start()
        for th in threads:
            th.join(timeout=60)
        self.assertEqual(sorted(codes), [200] + [409] * 5)


if __name__ == "__main__":
    unittest.main()
