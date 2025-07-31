from datetime import datetime
from ..utils.airflow_client import (
    trigger_dag,
    get_extracted_sources_status,
    get_dag_status_stream,
)


def trigger_etl_dag(sources: list[str]) -> dict:
    batch_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return trigger_dag("etl_dag", {"sources": sources, "batch_id": batch_id})


def get_etl_extracted_sources(dag_run_id: str) -> dict:
    return get_extracted_sources_status("etl_dag", dag_run_id)


def get_etl_status_stream(dag_run_id: str, poll_interval: int = 5) -> dict:
    return get_dag_status_stream("etl_dag", dag_run_id, poll_interval)
