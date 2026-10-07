"""
On-Premises Data Pipeline Embedded Web Server & REST API.
Built entirely using Python standard library + DuckDB + SQLite.
Zero external framework dependencies (no Flask/FastAPI required).
Serves:
- Interactive Web Operations Dashboard
- REST APIs for DAG triggering, pipeline health, audit log, and DuckDB SQL console
"""

import os
import sys
import json
import yaml
import duckdb
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add root path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from data_pipeline.orchestrator.audit_logger import AuditLogger
from data_pipeline.dags.job_ingestion_dag import create_job_ingestion_dag
from data_pipeline.dags.resume_ingestion_dag import create_resume_ingestion_dag
from data_pipeline.dags.alignment_matrix_dag import create_alignment_matrix_dag

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "pipeline_config.yaml")

def get_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

class PipelineApiHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/dashboard":
            self._serve_dashboard()
            return
        elif path == "/api/status":
            self._serve_status()
            return
        elif path == "/api/logs":
            self._serve_logs()
            return
        elif path == "/api/quality":
            self._serve_quality()
            return
        else:
            # Fallback to static file serving in web dir
            web_dir = os.path.dirname(__file__)
            target_file = os.path.join(web_dir, path.lstrip('/'))
            if os.path.exists(target_file) and not os.path.isdir(target_file):
                super().do_GET()
            else:
                self.send_error(404, "Endpoint not found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        try:
            body = json.loads(post_data) if post_data else {}
        except json.JSONDecodeError:
            body = {}

        if path == "/api/trigger":
            self._handle_trigger(body)
        elif path == "/api/query":
            self._handle_query(body)
        else:
            self.send_error(404, "Endpoint not found")

    def _serve_dashboard(self):
        dash_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
        if not os.path.exists(dash_path):
            self.send_error(404, "Dashboard HTML not found")
            return
        with open(dash_path, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _serve_status(self):
        config = get_config()
        logger = AuditLogger(config["storage"]["audit_db_path"])
        duck_path = config["storage"]["duckdb_path"]

        tables_data = []
        if os.path.exists(duck_path):
            try:
                con = duckdb.connect(duck_path)
                tables = con.execute("SHOW TABLES;").fetchall()
                for t in tables:
                    t_name = t[0]
                    cnt = con.execute(f"SELECT COUNT(*) FROM {t_name}").fetchone()[0]
                    tables_data.append({"name": t_name, "count": cnt})
                con.close()
            except Exception as e:
                tables_data = [{"error": str(e)}]

        db_size_mb = 0.0
        if os.path.exists(duck_path):
            db_size_mb = round(os.path.getsize(duck_path) / (1024 * 1024), 2)

        data = {
            "pipeline_name": config["pipeline"]["name"],
            "version": config["pipeline"]["version"],
            "duckdb_size_mb": db_size_mb,
            "tables": tables_data,
            "quality_summary": logger.get_quality_summary(),
            "recent_runs": logger.get_recent_runs(limit=10)
        }

        self._send_json(data)

    def _serve_logs(self):
        config = get_config()
        logger = AuditLogger(config["storage"]["audit_db_path"])
        self._send_json({"logs": logger.get_recent_logs(limit=50)})

    def _serve_quality(self):
        config = get_config()
        logger = AuditLogger(config["storage"]["audit_db_path"])
        self._send_json({
            "summary": logger.get_quality_summary(),
            "checks": logger.get_recent_quality_checks(limit=25)
        })

    def _handle_trigger(self, body):
        dag_name = body.get("dag", "all")
        config = get_config()
        logger = AuditLogger(config["storage"]["audit_db_path"])

        results = []
        try:
            if dag_name in ["jobs", "all"]:
                d1 = create_job_ingestion_dag()
                results.append(d1.execute(config, logger))

            if dag_name in ["resumes", "all"]:
                d2 = create_resume_ingestion_dag()
                results.append(d2.execute(config, logger))

            if dag_name in ["alignment", "all"]:
                d3 = create_alignment_matrix_dag()
                results.append(d3.execute(config, logger))

            # Clean context object before JSON serialization
            cleaned_results = []
            for r in results:
                cleaned_results.append({
                    "run_id": r["run_id"],
                    "dag_id": r["dag_id"],
                    "status": r["status"],
                    "duration_sec": round(r["duration_sec"], 3),
                    "records_processed": r["records_processed"],
                    "error": r["error"]
                })

            self._send_json({"status": "SUCCESS", "results": cleaned_results})
        except Exception as e:
            self._send_json({"status": "FAILED", "error": str(e)}, status_code=500)

    def _handle_query(self, body):
        query = body.get("query", "").strip()
        if not query:
            self._send_json({"error": "Query string is empty"}, status_code=400)
            return

        config = get_config()
        duck_path = config["storage"]["duckdb_path"]
        if not os.path.exists(duck_path):
            self._send_json({"error": "DuckDB warehouse not initialized"}, status_code=500)
            return

        try:
            con = duckdb.connect(duck_path)
            df = con.execute(query).fetchdf()
            con.close()

            # Convert to list of dicts, handle NaN
            records = df.where(df.notnull(), None).to_dict(orient="records")
            columns = list(df.columns)
            self._send_json({
                "columns": columns,
                "row_count": len(records),
                "data": records[:100]  # Cap at 100 rows for web preview
            })
        except Exception as e:
            self._send_json({"error": str(e)}, status_code=400)

    def _send_json(self, data, status_code=200):
        body = json.dumps(data, default=str).encode('utf-8')
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

def start_web_server(host="127.0.0.1", port=8085):
    print("=" * 65)
    print(f"  [ON-PREM SERVER] Skill Bridge Data Pipeline Operations Center")
    print(f"  URL: http://{host}:{port}/dashboard")
    print(f"  REST API: http://{host}:{port}/api/status")
    print("=" * 65)

    server = HTTPServer((host, port), PipelineApiHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Server stopped by user.")
        server.server_close()

if __name__ == "__main__":
    start_web_server()
