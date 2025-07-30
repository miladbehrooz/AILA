import requests
import ast
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

        dag_run = response.json()
        return {
            "message": "DAG triggered successfully",
            "dag_id": dag_run["dag_id"],
            "dag_run_id": dag_run["dag_run_id"],
            "state": dag_run["state"],
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

        dag_run = response.json()
        raw_value = dag_run.get("value", "[]")
        try:
            parsed_value = ast.literal_eval(raw_value)
        except (SyntaxError, ValueError):
            parsed_value = []
        return {
            "dag_id": dag_run["dag_id"],
            "execution_date": dag_run["execution_date"],
            "timestamp": dag_run["timestamp"],
            "new_sources": parsed_value,
        }

    except requests.HTTPError as e:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to fetch DAG run status: {response.text}",
        )
