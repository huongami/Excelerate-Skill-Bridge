import unittest
import helpers as H


class AdminRoutesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = H.Platform.get()

    def test_overview(self):
        status, res = self.p.api.call("GET", "/admin/overview")
        self.assertEqual(status, 200)
        self.assertEqual(res["status"], "healthy")
        self.assertIn("counts", res)
        self.assertIn("database", res)
        self.assertTrue(res["database"]["wal_enabled"])
        self.assertIn("traffic", res)

    def test_tables_and_schema(self):
        status, res = self.p.api.call("GET", "/admin/tables")
        self.assertEqual(status, 200)
        self.assertGreater(res["totalTables"], 5)
        names = [t["name"] for t in res["tables"]]
        self.assertIn("users", names)
        self.assertIn("jobs", names)
        self.assertIn("profiles", names)

    def test_table_data_pagination_and_redaction(self):
        status, res = self.p.api.call("GET", "/admin/table-data?table=users&limit=10&offset=0")
        self.assertEqual(status, 200)
        self.assertEqual(res["table"], "users")
        self.assertGreater(len(res["rows"]), 0)
        # Check password hash redaction
        for r in res["rows"]:
            if "password_hash" in r:
                self.assertEqual(r["password_hash"], "[PROTECTED BCRYPT HASH]")

    def test_traffic_telemetry(self):
        status, res = self.p.api.call("GET", "/admin/traffic")
        self.assertEqual(status, 200)
        self.assertIn("uptimeSeconds", res)
        self.assertIn("totalRequests", res)
        self.assertIn("statusCodes", res)
        self.assertIn("databaseEvents", res)

    def test_dataflow_pipeline(self):
        status, res = self.p.api.call("GET", "/admin/dataflow")
        self.assertEqual(status, 200)
        self.assertIn("stages", res)
        self.assertEqual(len(res["stages"]), 4)
        self.assertIn("eventsStream", res)

    def test_sql_runner_select_allowed(self):
        status, res = self.p.api.call("POST", "/admin/sql", {"sql": "SELECT id, email, role FROM users LIMIT 3;"})
        self.assertEqual(status, 200)
        self.assertEqual(res["columns"], ["id", "email", "role"])
        self.assertEqual(len(res["rows"]), 3)
        self.assertIn("durationMs", res)

    def test_sql_runner_mutation_blocked(self):
        status, res = self.p.api.call("POST", "/admin/sql", {"sql": "DELETE FROM users WHERE id = '1';"})
        self.assertEqual(status, 403)
        self.assertEqual(res["error"]["code"], "FORBIDDEN")

    def test_wal_checkpoint_action(self):
        status, res = self.p.api.call("POST", "/admin/action", {"action": "wal_checkpoint"})
        self.assertEqual(status, 200)
        self.assertTrue(res["ok"])


if __name__ == "__main__":
    unittest.main()
