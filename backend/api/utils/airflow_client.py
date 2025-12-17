import ast
import json
import time

import requests
from fastapi import HTTPException
from requests.auth import HTTPBasicAuth

from backend.settings import settings


def trigger_dag(dag_id: str, conf: dict) -> dict:
    """Trigger an Airflow DAG run with the provided configuration.

    Args:
        dag_id (str): Identifier of the DAG to run.
        conf (dict): Configuration payload passed to the DAG run.

    Returns:
        dict: Summary of the triggered run.
    """
    url = f"{settings.AIRFLOW_API_URL}/dags/{dag_id}/dagRuns"

    try:
        response = requests.post(
            url,
            json={"conf": conf},
            auth=HTTPBasicAuth(settings.AIRFLOW_USER, settings.AIRFLOW_PASS),
        )
        response.raise_for_status()

        data = response.json()
        return {
            "message": "DAG triggered successfully",
            "dag_id": data["dag_id"],
            "dag_run_id": data["dag_run_id"],
            "state": data["state"],
        }

    except requests.HTTPError as err:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to trigger DAG: {response.text}",
        ) from err


def get_extracted_sources_status(dag_id: str, dag_run_id: str) -> dict:
    """Fetch the XCom payload summarizing the extract_sources task.

    Args:
        dag_id (str): Identifier of the DAG.
        dag_run_id (str): Identifier of the DAG run.

    Returns:
        dict: Structured extraction summary with the DAG metadata.
    """
    url = f"{settings.AIRFLOW_API_URL}/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/extract_sources/xcomEntries/return_value"

    try:
        response = requests.get(
            url, auth=HTTPBasicAuth(settings.AIRFLOW_USER, settings.AIRFLOW_PASS)
        )
        response.raise_for_status()

        data = response.json()
        raw_value = data.get("value", "{}")
        try:
            parsed_value = ast.literal_eval(raw_value)
        except (SyntaxError, ValueError):
            parsed_value = {}

        if isinstance(parsed_value, list):
            parsed_value = {"new_sources": parsed_value}

        extraction_summary = {
            "new_sources": parsed_value.get("new_sources", []),
            "duplicate_sources": parsed_value.get("duplicate_sources", []),
            "failed_sources": parsed_value.get("failed_sources", []),
        }
        return {
            "dag_id": data["dag_id"],
            "execution_date": data["execution_date"],
            "timestamp": data["timestamp"],
            **extraction_summary,
        }

    except requests.HTTPError as err:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to fetch DAG run status: {response.text}",
        ) from err


def get_dag_status_stream(dag_id: str, dag_run_id: str, poll_interval: int = 5) -> str:
    """Stream DAG state updates as Server-Sent Events.

    Args:
        dag_id (str): Identifier of the DAG.
        dag_run_id (str): Identifier of the DAG run.
        poll_interval (int, optional): Seconds between status polls.

    Yields:
        str: SSE-formatted payload with the current DAG state.
    """
    url = f"{settings.AIRFLOW_API_URL}/dags/{dag_id}/dagRuns/{dag_run_id}"

    while True:
        try:
            response = requests.get(
                url, auth=HTTPBasicAuth(settings.AIRFLOW_USER, settings.AIRFLOW_PASS)
            )
            response.raise_for_status()
            data = response.json()
            state = data.get("state", "unknown")

            yield f"data: {json.dumps({'state': state})}\n\n"

            if state in {"success", "failed"}:
                break

            time.sleep(poll_interval)
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            break


def list_dag_runs(dag_id: str, limit: int = 25, offset: int = 0) -> dict:
    """List DAG runs with pagination.

    Args:
        dag_id (str): Identifier of the DAG.
        limit (int, optional): Maximum number of runs to return. Defaults to 25.
        offset (int, optional): Offset for pagination. Defaults to 0.

    Returns:
        dict: Paginated response returned by the Airflow API.
    """
    url = f"{settings.AIRFLOW_API_URL}/dags/{dag_id}/dagRuns"
    params = {"limit": limit, "offset": offset, "order_by": "-execution_date"}

    try:
        response = requests.get(
            url,
            params=params,
            auth=HTTPBasicAuth(settings.AIRFLOW_USER, settings.AIRFLOW_PASS),
        )
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as err:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to list DAG runs: {response.text}",
        ) from err


def get_dag_run(dag_id: str, dag_run_id: str) -> dict:
    """Retrieve the metadata for a single DAG run.

    Args:
        dag_id (str): Identifier of the DAG.
        dag_run_id (str): Identifier of the DAG run.

    Returns:
        dict: Airflow API payload describing the DAG run.
    """
    url = f"{settings.AIRFLOW_API_URL}/dags/{dag_id}/dagRuns/{dag_run_id}"

    try:
        response = requests.get(
            url, auth=HTTPBasicAuth(settings.AIRFLOW_USER, settings.AIRFLOW_PASS)
        )
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as err:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to fetch DAG run: {response.text}",
        ) from err


def get_task_log(
    dag_id: str, dag_run_id: str, task_id: str, task_try_number: int = 1
) -> dict:
    """Fetch the task log for a specific attempt.

    Args:
        dag_id (str): Identifier of the DAG.
        dag_run_id (str): Identifier of the DAG run.
        task_id (str): Identifier of the task instance.
        task_try_number (int, optional): Attempt number to request. Defaults to 1.

    Returns:
        dict: Task log content and continuation token if present.
    """
    url = (
        f"{settings.AIRFLOW_API_URL}/dags/{dag_id}/dagRuns/{dag_run_id}/"
        f"taskInstances/{task_id}/logs/{task_try_number}"
    )

    response = requests.get(
        url,
        params={"full_content": "true"},
        auth=HTTPBasicAuth(settings.AIRFLOW_USER, settings.AIRFLOW_PASS),
    )
    response.raise_for_status()
    content = response.text
    try:
        data = response.json()
        content = data.get("content")
        continuation = data.get("continuation_token")
    except ValueError:
        continuation = None
        return {
            "dag_id": dag_id,
            "dag_run_id": dag_run_id,
            "task_id": task_id,
            "content": content,
            "continuation_token": continuation,
        }


def cancel_dag_run(dag_id: str, dag_run_id: str) -> dict:
    """Issue a cancellation request for a DAG run.

    Args:
        dag_id (str): Identifier of the DAG.
        dag_run_id (str): Identifier of the DAG run to cancel.

    Returns:
        dict: Confirmation payload returned by the API.
    """
    url = f"{settings.AIRFLOW_API_URL}/dags/{dag_id}/dagRuns/{dag_run_id}"

    try:
        response = requests.delete(
            url, auth=HTTPBasicAuth(settings.AIRFLOW_USER, settings.AIRFLOW_PASS)
        )
        response.raise_for_status()
        return {
            "message": "DAG run cancellation requested",
            "dag_id": dag_id,
            "dag_run_id": dag_run_id,
        }
    except requests.HTTPError as err:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to cancel DAG run: {response.text}",
        ) from err
