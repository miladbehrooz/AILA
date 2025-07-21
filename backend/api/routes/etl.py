from fastapi import APIRouter
from ..models.etl import ETLRequest
from ..services.airflow_service import trigger_etl_dag, get_etl_status

router = APIRouter()


@router.post("/trigger")
def trigger_etl(req: ETLRequest):
    return trigger_etl_dag(req.sources)


@router.get("/status/{dag_run_id}")
def status(dag_run_id: str):
    return get_etl_status(dag_run_id)
