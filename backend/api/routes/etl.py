from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Query, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from ..models.etl import (
    ETLRequest,
    TriggerDAGResponse,
    ExtractedSourcesResponse,
    DagRunsResponse,
    DagRunDetailResponse,
    TaskLogResponse,
    CancelDagRunResponse,
    UploadedFileResponse,
)
from ..services.airflow_service import (
    trigger_etl_dag,
    get_etl_extracted_sources,
    get_etl_status_stream,
    list_etl_runs,
    get_etl_run,
    get_etl_task_logs,
    cancel_etl_run,
)
from backend.settings import settings

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


@router.get("/runs", response_model=DagRunsResponse)
def list_runs(limit: int = Query(25, ge=1, le=200), offset: int = Query(0, ge=0)):
    return list_etl_runs(limit=limit, offset=offset)


@router.get("/runs/{dag_run_id}", response_model=DagRunDetailResponse)
def get_run(dag_run_id: str):
    return get_etl_run(dag_run_id)


@router.get("/runs/{dag_run_id}/logs", response_model=TaskLogResponse)
def get_run_logs(
    dag_run_id: str,
    task_id: str = Query(..., description="Airflow task_id to fetch logs for"),
    try_number: int = Query(1, ge=1, description="Task try number"),
):
    return get_etl_task_logs(dag_run_id, task_id, try_number)


@router.delete("/runs/{dag_run_id}", response_model=CancelDagRunResponse)
def cancel_run(dag_run_id: str):
    return cancel_etl_run(dag_run_id)


@router.post("/upload-file", response_model=UploadedFileResponse)
async def upload_file(file: UploadFile = File(...)):
    uploads_dir = settings.UPLOADS_DIR
    uploads_dir.mkdir(parents=True, exist_ok=True)

    filename = Path(file.filename or "uploaded_file").name
    stored_name = f"{uuid4()}_{filename}"
    destination = uploads_dir / stored_name

    try:
        content = await file.read()
        destination.write_bytes(content)
    except Exception as exc:  # pragma: no cover - defensive
        if destination.exists():
            destination.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to store file: {exc}")

    relative_path = destination.relative_to(settings.PROJECT_ROOT)

    return UploadedFileResponse(stored_path=str(relative_path))
