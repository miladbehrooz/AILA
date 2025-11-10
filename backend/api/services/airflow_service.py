from datetime import datetime

from ..utils.airflow_client import (
    trigger_dag,
    get_extracted_sources_status,
    get_dag_status_stream,
    list_dag_runs,
    get_dag_run,
    get_task_log,
    cancel_dag_run,
)


def _serialize_dag_run(data: dict) -> dict:
    return {
        "dag_id": data.get("dag_id"),
        "dag_run_id": data.get("dag_run_id"),
        "state": data.get("state"),
        "execution_date": data.get("execution_date"),
        "start_date": data.get("start_date"),
        "end_date": data.get("end_date"),
        "run_type": data.get("run_type"),
        "external_trigger": data.get("external_trigger"),
    }


def trigger_etl_dag(sources: list[str]) -> dict:
    batch_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return trigger_dag("etl_dag", {"sources": sources, "batch_id": batch_id})


def get_etl_extracted_sources(dag_run_id: str) -> dict:
    return get_extracted_sources_status("etl_dag", dag_run_id)


def get_etl_status_stream(dag_run_id: str, poll_interval: int = 5) -> dict:
    return get_dag_status_stream("etl_dag", dag_run_id, poll_interval)


def list_etl_runs(limit: int = 25, offset: int = 0) -> dict:
    response = list_dag_runs("etl_dag", limit=limit, offset=offset)
    dag_runs = [_serialize_dag_run(run) for run in response.get("dag_runs", [])]
    return {
        "dag_id": "etl_dag",
        "total_entries": response.get("total_entries", len(dag_runs)),
        "dag_runs": dag_runs,
    }


def get_etl_run(dag_run_id: str) -> dict:
    run = get_dag_run("etl_dag", dag_run_id)
    return _serialize_dag_run(run)


def get_etl_task_logs(dag_run_id: str, task_id: str, try_number: int = 1) -> dict:
    log_payload = get_task_log("etl_dag", dag_run_id, task_id, try_number)
    return {
        "dag_id": "etl_dag",
        "dag_run_id": dag_run_id,
        "task_id": task_id,
        "try_number": try_number,
        "content": log_payload.get("content", ""),
    }


def cancel_etl_run(dag_run_id: str) -> dict:
    return cancel_dag_run("etl_dag", dag_run_id)
