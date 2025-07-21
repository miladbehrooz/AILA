from ..utils.airflow_client import trigger_dag, get_dag_status


def trigger_etl_dag(sources: list[str]) -> dict:
    return trigger_dag("etl_dag", {"sources": sources})


def get_etl_status(dag_run_id: str) -> dict:
    return get_dag_status("etl_dag", dag_run_id)
