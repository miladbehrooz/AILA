from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from ..models.etl import ETLRequest, TriggerDAGResponse, ExtractedSourcesResponse
from ..services.airflow_service import (
    trigger_etl_dag,
    get_etl_extracted_sources,
    get_etl_status_stream,
)

router = APIRouter()


@router.post("/trigger", response_model=TriggerDAGResponse)
def trigger_etl(req: ETLRequest):
    return trigger_etl_dag(req.sources)


# TODO: make it Endpoint with Polling Logic
@router.get("/extracted-sources/{dag_run_id}", response_model=ExtractedSourcesResponse)
def get_extracted_sources(dag_run_id: str):
    return get_etl_extracted_sources(dag_run_id=dag_run_id)


@router.get("/stream-etl-status/{dag_run_id}")
def stream_etl_status(dag_run_id: str):
    return StreamingResponse(
        get_etl_status_stream(dag_run_id), media_type="text/event-stream"
    )


# TODO: endpoint with Polling Logic or stream for status of the ETL DAG (sucessfull or failed)
