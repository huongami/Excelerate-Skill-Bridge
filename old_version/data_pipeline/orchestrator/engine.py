"""
On-Premises Pipeline Orchestrator Engine.
Lightweight DAG execution engine supporting:
- Task dependency graphs (topological sort)
- State management (PENDING, RUNNING, SUCCESS, FAILED)
- Execution context sharing between tasks
- Integrated Audit Logging and Performance Profiling
"""

import time
import uuid
import traceback
from datetime import datetime
from collections import defaultdict, deque
from data_pipeline.orchestrator.audit_logger import AuditLogger

class PipelineContext:
    def __init__(self, run_id, config):
        self.run_id = run_id
        self.config = config
        self.data_store = {}
        self.metrics = {"records_extracted": 0, "records_transformed": 0, "records_loaded": 0}

    def set(self, key, value):
        self.data_store[key] = value

    def get(self, key, default=None):
        return self.data_store.get(key, default)

class Task:
    def __init__(self, task_id, fn, retries=1):
        self.task_id = task_id
        self.fn = fn
        self.retries = retries
        self.upstream = set()
        self.downstream = set()

    def __rshift__(self, other):
        """Enable Airflow-style syntax: task_a >> task_b"""
        if isinstance(other, Task):
            self.downstream.add(other)
            other.upstream.add(self)
            return other
        elif isinstance(other, list):
            for t in other:
                self.downstream.add(t)
                t.upstream.add(self)
            return other
        raise TypeError("Invalid dependency target")

class DAG:
    def __init__(self, dag_id, description=""):
        self.dag_id = dag_id
        self.description = description
        self.tasks = {}

    def add_task(self, task):
        self.tasks[task.task_id] = task
        return task

    def _get_topological_order(self):
        in_degree = {t_id: len(task.upstream) for t_id, task in self.tasks.items()}
        queue = deque([t_id for t_id, deg in in_degree.items() if deg == 0])
        order = []

        while queue:
            curr_id = queue.popleft()
            order.append(curr_id)
            for down in self.tasks[curr_id].downstream:
                in_degree[down.task_id] -= 1
                if in_degree[down.task_id] == 0:
                    queue.append(down.task_id)

        if len(order) != len(self.tasks):
            raise ValueError(f"Cyclic dependency detected in DAG '{self.dag_id}'")
        return order

    def execute(self, config, audit_logger=None):
        run_id = f"RUN_{self.dag_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        logger = audit_logger or AuditLogger()
        context = PipelineContext(run_id, config)

        print(f"\n=======================================================")
        print(f"  [ORCHESTRATOR] STARTING DAG: {self.dag_id}")
        print(f"  Run ID: {run_id}")
        print(f"=======================================================")

        logger.log_run_start(run_id, self.dag_id)
        logger.log_event(run_id, "INFO", f"DAG '{self.dag_id}' execution started.")

        dag_start = time.time()
        order = self._get_topological_order()
        dag_failed = False
        error_msg = None

        for task_id in order:
            task = self.tasks[task_id]
            task_run_id = f"{run_id}_{task_id}"
            logger.log_task_start(task_run_id, run_id, self.dag_id, task_id)
            logger.log_event(run_id, "INFO", f"Running task: {task_id}")
            print(f"  --> Executing Task: [{task_id}]...")

            task_start = time.time()
            attempts = 0
            success = False

            while attempts <= task.retries and not success:
                attempts += 1
                try:
                    task.fn(context, logger)
                    success = True
                except Exception as e:
                    stack = traceback.format_exc()
                    print(f"    [!] Error in {task_id} (attempt {attempts}): {e}")
                    if attempts > task.retries:
                        dag_failed = True
                        error_msg = f"Task '{task_id}' failed after {attempts} attempts: {e}"
                        logger.log_task_end(task_run_id, "FAILED", time.time() - task_start, str(e))
                        logger.log_event(run_id, "ERROR", f"Task {task_id} failed: {stack}")
                        break
                    time.sleep(1)

            if success:
                duration = time.time() - task_start
                logger.log_task_end(task_run_id, "SUCCESS", duration)
                logger.log_event(run_id, "INFO", f"Task '{task_id}' succeeded in {duration:.2f}s")
                print(f"      [✓] Task [{task_id}] SUCCESS ({duration:.2f}s)")
            else:
                break

        total_duration = time.time() - dag_start
        final_status = "FAILED" if dag_failed else "SUCCESS"
        total_records = context.metrics.get("records_loaded", 0) or context.metrics.get("records_transformed", 0)

        logger.log_run_end(run_id, final_status, total_duration, total_records, error_msg)
        logger.log_event(run_id, "INFO" if not dag_failed else "ERROR", f"DAG '{self.dag_id}' finished with status: {final_status} in {total_duration:.2f}s")

        print(f"=======================================================")
        print(f"  [ORCHESTRATOR] DAG '{self.dag_id}' COMPLETED: {final_status}")
        print(f"  Duration: {total_duration:.2f}s | Records: {total_records}")
        print(f"=======================================================\n")

        return {
            "run_id": run_id,
            "dag_id": self.dag_id,
            "status": final_status,
            "duration_sec": total_duration,
            "records_processed": total_records,
            "error": error_msg,
            "context": context
        }
