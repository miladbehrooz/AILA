import json
from typing import Any
from uuid import UUID, uuid4

from backend.etl.tasks.clean_data_warehouse import clean_data_warehouse
from backend.etl.tasks.clean_vector_database import clean_vector_database
from backend.utils import logger

from ..utils.airflow_client import (
    cancel_dag_run,
    get_dag_run,
    get_dag_status_stream,
    get_extracted_sources_status,
    get_task_log,
    list_dag_runs,
    trigger_dag,
)


def _serialize_dag_run(data: dict) -> dict:
    """Map an Airflow DAG run payload into the API schema.

    Args:
        data (dict): Raw run data returned by Airflow.

    Returns:
        dict: Normalized DAG run representation.
    """
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
    """Trigger the ETL DAG with the provided sources.

    Args:
        sources (list[str]): URLs or file paths to ingest.

    Returns:
        dict: Airflow API response describing the scheduled run.
    """
    batch_id = uuid4()
    return trigger_dag("etl_dag", {"sources": sources, "batch_id": str(batch_id)})


def get_etl_extracted_sources(dag_run_id: str) -> dict:
    """Fetch the extraction summary for a DAG run.

    Args:
        dag_run_id (str): Airflow DAG run identifier.

    Returns:
        dict: Extraction summary merged with DAG metadata.
    """
    return get_extracted_sources_status("etl_dag", dag_run_id)


def get_etl_status_stream(dag_run_id: str, poll_interval: int = 5) -> dict:
    """Stream ETL DAG status updates for a run.

    Args:
        dag_run_id (str): Airflow DAG run identifier.
        poll_interval (int, optional): Seconds between poll requests. Defaults to 5.

    Returns:
        dict: Generator that yields SSE-formatted state updates.
    """
    return get_dag_status_stream("etl_dag", dag_run_id, poll_interval)


def list_etl_runs(limit: int = 25, offset: int = 0) -> dict:
    """List ETL DAG runs with pagination.

    Args:
        limit (int, optional): Max number of runs per page. Defaults to 25.
        offset (int, optional): Pagination offset. Defaults to 0.

    Returns:
        dict: Paginated response that includes normalized DAG runs.
    """
    response = list_dag_runs("etl_dag", limit=limit, offset=offset)
    dag_runs = [_serialize_dag_run(run) for run in response.get("dag_runs", [])]
    return {
        "dag_id": "etl_dag",
        "total_entries": response.get("total_entries", len(dag_runs)),
        "dag_runs": dag_runs,
    }


def get_etl_run(dag_run_id: str) -> dict:
    """Get ETL DAG run metadata.

    Args:
        dag_run_id (str): Airflow DAG run identifier.

    Returns:
        dict: Normalized DAG run representation.
    """
    run = get_dag_run("etl_dag", dag_run_id)
    return _serialize_dag_run(run)


def get_etl_task_logs(dag_run_id: str, task_id: str, try_number: int = 1) -> dict:
    """Fetch task logs for a DAG run.

    Args:
        dag_run_id (str): Airflow DAG run identifier.
        task_id (str): Task identifier inside the DAG.
        try_number (int, optional): Attempt number to inspect. Defaults to 1.

    Returns:
        dict: Task log payload with metadata.
    """
    log_payload = get_task_log("etl_dag", dag_run_id, task_id, try_number)
    return {
        "dag_id": "etl_dag",
        "dag_run_id": dag_run_id,
        "task_id": task_id,
        "try_number": try_number,
        "content": log_payload.get("content", ""),
    }


def cancel_etl_run(dag_run_id: str) -> dict:
    """Cancel a DAG run and clean up related data.

    Args:
        dag_run_id (str): Airflow DAG run identifier.

    Returns:
        dict: Cancellation payload including cleanup summaries.
    """
    batch_id = _get_batch_id_from_dag_run(dag_run_id)
    logger.info(
        "Cancelling ETL dag_run_id {} with associated batch_id {}", dag_run_id, batch_id
    )
    response = cancel_dag_run("etl_dag", dag_run_id)

    if not batch_id:
        logger.info(
            "No batch_id found for dag_run_id {}. Skipping Mongo cleanup.", dag_run_id
        )
        return response

    deletion_summary = clean_data_warehouse(batch_id=batch_id)
    vector_deletion_summary = clean_vector_database(batch_id=batch_id)
    response["batch_id"] = str(batch_id)
    response["deleted_documents"] = deletion_summary
    response["deleted_vector_documents"] = vector_deletion_summary

    return response


def _get_batch_id_from_dag_run(dag_run_id: str) -> UUID | None:
    """Extract the batch_id from the DAG run conf payload.

    Args:
        dag_run_id (str): Airflow DAG run identifier.

    Returns:
        UUID | None: Batch identifier if present, otherwise None.
    """
    try:
        dag_run = get_dag_run("etl_dag", dag_run_id)
    except Exception as exc:
        logger.warning(
            "Unable to fetch dag_run_id {} to determine batch_id: {}", dag_run_id, exc
        )
        return None

    conf: Any = dag_run.get("conf")
    if conf is None:
        logger.info(
            "dag_run_id {} conf payload missing. Cannot derive batch_id.", dag_run_id
        )
        return None

    if isinstance(conf, str):
        try:
            conf = json.loads(conf)
        except json.JSONDecodeError:
            logger.warning(
                "dag_run_id {} conf payload is not valid JSON. Cannot derive batch_id.",
                dag_run_id,
            )
            return None

    if not isinstance(conf, dict):
        logger.warning(
            "dag_run_id {} conf payload is not a dictionary. Cannot derive batch_id.",
            dag_run_id,
        )
        return None

    batch_id_str = conf.get("batch_id")
    if not batch_id_str:
        logger.info("dag_run_id {} conf payload lacks batch_id.", dag_run_id)
        return None

    try:
        return UUID(batch_id_str)
    except ValueError:
        logger.warning(
            "dag_run_id {} batch_id {} is not a valid UUID.", dag_run_id, batch_id_str
        )
        return None
