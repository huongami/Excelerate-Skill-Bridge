#!/usr/bin/env python3
"""
On-Premises Data Pipeline CLI Runner
Unified entry point for DAG execution, data contracts testing, DuckDB SQL console, and web operations server.
"""

import sys
import os
import argparse
import yaml
import duckdb
from datetime import datetime

# Add root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_pipeline.orchestrator.audit_logger import AuditLogger
from data_pipeline.dags.job_ingestion_dag import create_job_ingestion_dag
from data_pipeline.dags.resume_ingestion_dag import create_resume_ingestion_dag
from data_pipeline.dags.alignment_matrix_dag import create_alignment_matrix_dag

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "pipeline_config.yaml")

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_sql(query, config):
    duck_path = config["storage"]["duckdb_path"]
    if not os.path.exists(duck_path):
        print(f"[!] DuckDB warehouse not found at '{duck_path}'. Run the pipeline first.")
        return

    con = duckdb.connect(duck_path)
    print(f"\n[DUCKDB SQL QUERY]: {query}\n" + "-" * 60)
    try:
        df = con.execute(query).fetchdf()
        print(df.to_string())
    except Exception as e:
        print(f"[!] SQL Error: {e}")
    finally:
        con.close()

def print_status(audit_logger, config):
    print("\n" + "=" * 65)
    print("  Skill Bridge - On-Premises Data Pipeline Status")
    print("=" * 65)

    duck_path = config["storage"]["duckdb_path"]
    if os.path.exists(duck_path):
        con = duckdb.connect(duck_path)
        tables = con.execute("SHOW TABLES;").fetchall()
        print("\n[+] DuckDB Lakehouse Tables:")
        for t in tables:
            t_name = t[0]
            cnt = con.execute(f"SELECT COUNT(*) FROM {t_name}").fetchone()[0]
            print(f"  • {t_name.ljust(35)}: {cnt:>6} records")
        con.close()
    else:
        print("\n[!] DuckDB warehouse: Not yet initialized.")

    q_summary = audit_logger.get_quality_summary()
    print("\n[+] Data Quality Contracts Summary:")
    print(f"  • Total Assertions Executed : {q_summary.get('total_checks', 0)}")
    print(f"  • Passed Contracts          : {q_summary.get('passed_checks', 0)}")
    print(f"  • Failed Contracts          : {q_summary.get('failed_checks', 0)}")

    runs = audit_logger.get_recent_runs(limit=5)
    print("\n[+] Recent Pipeline Runs (Audit Ledger):")
    if not runs:
        print("  (No runs recorded yet)")
    for r in runs:
        dur = f"{r['duration_sec']:.2f}s" if r.get('duration_sec') else 'N/A'
        print(f"  [{r['status']}] {r['dag_name'].ljust(26)} | RunID: {r['run_id']} | Dur: {dur}")
    print("=" * 65 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Skill Bridge On-Premises Data Pipeline CLI")
    parser.add_argument("--all", action="store_true", help="Execute complete Medallion pipeline (Jobs -> Resumes -> Alignment)")
    parser.add_argument("--dag", type=str, choices=["jobs", "resumes", "alignment"], help="Execute a specific DAG")
    parser.add_argument("--status", action="store_true", help="Print Lakehouse tables, data contracts, and audit runs")
    parser.add_argument("--sql", type=str, help="Execute an analytical SQL query against the DuckDB Lakehouse")
    parser.add_argument("--web", action="store_true", help="Start the on-premises interactive Web Operations Dashboard")

    args = parser.parse_args()
    config = load_config()
    logger = AuditLogger(config["storage"]["audit_db_path"])

    if args.sql:
        run_sql(args.sql, config)
        return

    if args.status:
        print_status(logger, config)
        return

    if args.web:
        from data_pipeline.web.server import start_web_server
        host = config["web_dashboard"]["host"]
        port = config["web_dashboard"]["port"]
        start_web_server(host, port)
        return

    if args.dag:
        if args.dag == "jobs":
            dag = create_job_ingestion_dag()
        elif args.dag == "resumes":
            dag = create_resume_ingestion_dag()
        elif args.dag == "alignment":
            dag = create_alignment_matrix_dag()
        dag.execute(config, logger)
        return

    if args.all or len(sys.argv) == 1:
        print("\n🚀 EXECUTING COMPLETE END-TO-END ON-PREMISES DATA PIPELINE...")
        
        # DAG 1: Jobs Ingestion & Standardization
        dag_jobs = create_job_ingestion_dag()
        res1 = dag_jobs.execute(config, logger)
        if res1["status"] != "SUCCESS":
            print(f"[!] Pipeline aborted due to failure in {dag_jobs.dag_id}")
            sys.exit(1)

        # DAG 2: Real Resumes & PII Scrubbing
        dag_resumes = create_resume_ingestion_dag()
        res2 = dag_resumes.execute(config, logger)
        if res2["status"] != "SUCCESS":
            print(f"[!] Pipeline aborted due to failure in {dag_resumes.dag_id}")
            sys.exit(1)

        # DAG 3: Gold Alignment & Market Marts
        dag_alignment = create_alignment_matrix_dag()
        res3 = dag_alignment.execute(config, logger)
        if res3["status"] != "SUCCESS":
            print(f"[!] Pipeline aborted due to failure in {dag_alignment.dag_id}")
            sys.exit(1)

        print("\n🎉 ALL PIPELINE DAGS COMPLETED SUCCESSFULLY!")
        print_status(logger, config)

if __name__ == "__main__":
    main()
