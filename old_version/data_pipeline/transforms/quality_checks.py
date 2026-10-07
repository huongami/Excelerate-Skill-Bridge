"""
On-Premises Data Quality & Contract Assertion Suite
Implements data contracts and assertion tests across Bronze, Silver, and Gold layers.
All test outcomes are logged directly to the SQLite audit database for governance.
"""

def run_table_quality_contracts(duck_conn, table_name: str, run_id: str, audit_logger) -> dict:
    """Executes standard data quality assertions against a DuckDB table."""
    results = {"total": 0, "passed": 0, "failed": 0, "tests": []}

    def _assert(check_name, condition_sql, expect_zero, threshold, failure_msg):
        results["total"] += 1
        try:
            val = duck_conn.execute(condition_sql).fetchone()[0]
            if expect_zero:
                passed = (val == 0)
            else:
                passed = (val > 0)

            status = "PASSED" if passed else "FAILED"
            if passed:
                results["passed"] += 1
            else:
                results["failed"] += 1

            audit_logger.log_quality_check(
                run_id=run_id,
                table_name=table_name,
                check_name=check_name,
                status=status,
                observed_value=val,
                threshold=threshold,
                message="Assertion satisfied." if passed else failure_msg
            )
            results["tests"].append({"check": check_name, "status": status, "observed": val, "threshold": threshold})
        except Exception as e:
            results["failed"] += 1
            audit_logger.log_quality_check(
                run_id=run_id,
                table_name=table_name,
                check_name=check_name,
                status="ERROR",
                observed_value="ERROR",
                threshold=threshold,
                message=f"Execution error: {e}"
            )
            results["tests"].append({"check": check_name, "status": "ERROR", "error": str(e)})

    # Test 1: Table exists and is non-empty
    _assert(
        check_name="row_count_not_zero",
        condition_sql=f"SELECT COUNT(*) FROM {table_name}",
        expect_zero=False,
        threshold="> 0",
        failure_msg=f"Table {table_name} is empty!"
    )

    if table_name == "silver_jobs":
        # Test 2: Primary Key Non-null
        _assert(
            check_name="primary_key_not_null",
            condition_sql=f"SELECT COUNT(*) FROM {table_name} WHERE job_id IS NULL OR job_id = ''",
            expect_zero=True,
            threshold="0",
            failure_msg="Found NULL or empty job_ids in silver_jobs"
        )
        # Test 3: ANZSCO Format (4-6 digits)
        _assert(
            check_name="valid_anzsco_format",
            condition_sql=f"SELECT COUNT(*) FROM {table_name} WHERE anzsco_code IS NULL OR LENGTH(anzsco_code) < 4",
            expect_zero=True,
            threshold="0",
            failure_msg="Invalid ANZSCO code format detected"
        )
        # Test 4: Salary bounds sanity (max >= min if both present)
        _assert(
            check_name="salary_bounds_sanity",
            condition_sql=f"SELECT COUNT(*) FROM {table_name} WHERE salary_max > 0 AND salary_min > 0 AND salary_max < salary_min",
            expect_zero=True,
            threshold="0",
            failure_msg="Salary max is lower than salary min!"
        )

    elif table_name == "silver_candidates":
        # Test 2: Candidate ID Non-null
        _assert(
            check_name="candidate_id_not_null",
            condition_sql=f"SELECT COUNT(*) FROM {table_name} WHERE candidate_id IS NULL OR candidate_id = ''",
            expect_zero=True,
            threshold="0",
            failure_msg="Found NULL candidate_id in silver_candidates"
        )
        # Test 3: Experience sanity (years between 0 and 50)
        _assert(
            check_name="experience_years_range",
            condition_sql=f"SELECT COUNT(*) FROM {table_name} WHERE years_of_experience < 0 OR years_of_experience > 50",
            expect_zero=True,
            threshold="0",
            failure_msg="Unrealistic candidate experience years detected"
        )
        # Test 4: Evidence length completeness (> 20 chars)
        _assert(
            check_name="evidence_content_completeness",
            condition_sql=f"SELECT COUNT(*) FROM {table_name} WHERE LENGTH(skill_evidence_excerpts) < 20",
            expect_zero=True,
            threshold="0",
            failure_msg="Evidence excerpts are missing or too short"
        )

    elif table_name == "gold_capability_alignment_matrix":
        # Test 2: Match scores range (0 to 100)
        _assert(
            check_name="match_score_range_0_100",
            condition_sql=f"SELECT COUNT(*) FROM {table_name} WHERE match_score < 0 OR match_score > 100",
            expect_zero=True,
            threshold="0",
            failure_msg="Match score outside [0, 100] range"
        )

    return results
