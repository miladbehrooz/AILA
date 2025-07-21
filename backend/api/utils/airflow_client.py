import requests
from requests.auth import HTTPBasicAuth
from backend.settings import settings


def trigger_dag(dag_id: str, conf: dict) -> dict:
    url = f"{settings.AIRFLOW_API_URL}/dags/{dag_id}/dagRuns"
    response = requests.post(
        url,
        json={"conf": conf},
        auth=HTTPBasicAuth(settings.AIRFLOW_USER, settings.AIRFLOW_PASS),
    )
    response.raise_for_status()
    return response.json()


def get_dag_status(dag_id: str, dag_run_id: str) -> dict:
    url = f"{settings.AIRFLOW_API_URL}/dags/{dag_id}/dagRuns/{dag_run_id}"
    response = requests.get(
        url, auth=HTTPBasicAuth(settings.AIRFLOW_USER, settings.AIRFLOW_PASS)
    )
    response.raise_for_status()
    return response.json()
