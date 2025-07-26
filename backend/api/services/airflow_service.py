from datetime import datetime
from ..utils.airflow_client import trigger_dag, get_dag_status

# TODO: use the conf parameter to pass the sources and batch_id dynamically


def trigger_etl_dag(sources: list[str]) -> dict:
    batch_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return trigger_dag("etl_dag", {"sources": sources, "batch_id": batch_id})


def get_etl_status(dag_run_id: str) -> dict:
    return get_dag_status("etl_dag", dag_run_id)
