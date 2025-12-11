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

router = APIRouter(tags=["ETL"])


@router.post("/runs", response_model=TriggerDAGResponse)
def create_run(req: ETLRequest) -> TriggerDAGResponse:
    """Trigger a new ETL DAG run for the provided sources.

    Args:
        req (ETLRequest): Request body that lists the sources to ingest.

    Returns:
        TriggerDAGResponse: API payload describing the triggered run.
    """
    return trigger_etl_dag(req.sources)


@router.get(
    "/runs/{dag_run_id}/extracted-sources", response_model=ExtractedSourcesResponse
)
def get_extracted_sources(dag_run_id: str) -> ExtractedSourcesResponse:
    """Return the extraction summary for a DAG run.

    Args:
        dag_run_id (str): Airflow DAG run identifier.

    Returns:
        ExtractedSourcesResponse: Extraction statistics.
    """
    return get_etl_extracted_sources(dag_run_id=dag_run_id)


@router.get("/runs/{dag_run_id}/status/stream")
def stream_run_status(dag_run_id: str) -> StreamingResponse:
    """Stream DAG state updates to the client.

    Args:
        dag_run_id (str): Airflow DAG run identifier.

    Returns:
        StreamingResponse: Server-sent event stream.
    """
    return StreamingResponse(
        get_etl_status_stream(dag_run_id), media_type="text/event-stream"
    )


@router.get("/runs", response_model=DagRunsResponse)
def list_runs(
    limit: int = Query(25, ge=1, le=200), offset: int = Query(0, ge=0)
) -> DagRunsResponse:
    """List DAG runs with pagination support.

    Args:
        limit (int, optional): Maximum number of runs to return. Defaults to 25.
        offset (int, optional): Offset for pagination. Defaults to 0.

    Returns:
        DagRunsResponse: Paginated list of DAG run summaries.
    """
    return list_etl_runs(limit=limit, offset=offset)


@router.get("/runs/{dag_run_id}", response_model=DagRunDetailResponse)
def get_run(dag_run_id: str) -> DagRunDetailResponse:
    """Fetch full metadata for a DAG run.

    Args:
        dag_run_id (str): Airflow DAG run identifier.

    Returns:
        DagRunDetailResponse: DAG run metadata.
    """
    return get_etl_run(dag_run_id)


@router.get("/runs/{dag_run_id}/logs", response_model=TaskLogResponse)
def get_run_logs(
    dag_run_id: str,
    task_id: str = Query(..., description="Airflow task_id to fetch logs for"),
    try_number: int = Query(1, ge=1, description="Task try number"),
) -> TaskLogResponse:
    """Fetch task logs for a DAG run and task instance.

    Args:
        dag_run_id (str): Airflow DAG run identifier.
        task_id (str): Task identifier inside the DAG.
        try_number (int, optional): Attempt number for the task. Defaults to 1.

    Returns:
        TaskLogResponse: Task log content.
    """
    return get_etl_task_logs(dag_run_id, task_id, try_number)


@router.delete("/runs/{dag_run_id}", response_model=CancelDagRunResponse)
def cancel_run(dag_run_id: str) -> CancelDagRunResponse:
    """Cancel a pending DAG run.

    Args:
        dag_run_id (str): Airflow DAG run identifier.

    Returns:
        CancelDagRunResponse: Cancellation confirmation.
    """
    return cancel_etl_run(dag_run_id)


@router.post("/files", response_model=UploadedFileResponse)
async def upload_file(file: UploadFile = File(...)) -> UploadedFileResponse:
    """Persist an uploaded file to the backend uploads directory.

    Args:
        file (UploadFile): File uploaded by the client.

    Returns:
        UploadedFileResponse: Relative path to the stored file.
    """
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
