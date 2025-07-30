from fastapi import APIRouter
from ..models.etl import ETLRequest, TriggerDAGResponse, ExtractedSourcesResponse
from ..services.airflow_service import trigger_etl_dag, get_etl_extracted_sources

router = APIRouter()


@router.post("/trigger", response_model=TriggerDAGResponse)
def trigger_etl(req: ETLRequest):
    return trigger_etl_dag(req.sources)


@router.get("/extracted-sources/{dag_run_id}", response_model=ExtractedSourcesResponse)
def get_extracted_sources(dag_run_id: str):
    return get_etl_extracted_sources(dag_run_id=dag_run_id)
