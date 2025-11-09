import requests
import ast
import time
import json
from requests.auth import HTTPBasicAuth
from fastapi import HTTPException
from backend.settings import settings


def trigger_dag(dag_id: str, conf: dict) -> dict:
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

    except requests.HTTPError as e:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to trigger DAG: {response.text}",
        )


def get_extracted_sources_status(dag_id: str, dag_run_id: str) -> dict:
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

    except requests.HTTPError as e:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to fetch DAG run status: {response.text}",
        )


def get_dag_status_stream(dag_id: str, dag_run_id: str, poll_interval: int = 5):
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
