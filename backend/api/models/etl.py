from typing import Optional
from pydantic import BaseModel


class ETLRequest(BaseModel):
    """Request payload for triggering a new ETL run.
    Attributes:
        sources (list[str]): List of source identifiers to extract and process.
    """

    sources: list[str]


class TriggerDAGResponse(BaseModel):
    """Response returned after scheduling an Airflow DAG run.
    Attributes:
        message (str): Confirmation message.
        dag_id (str): Identifier of the triggered DAG.
        dag_run_id (str): Identifier of the created DAG run.
        state (str): Initial state of the DAG run.
    """

    message: str
    dag_id: str
    dag_run_id: str
    state: str


class ExtractedSourcesResponse(BaseModel):
    """Summary of extraction results emitted by the ETL DAG.
    Attributes:
        dag_id (str): Identifier of the DAG run.
        execution_date (str): Execution date of the DAG run.
        timestamp (str): Timestamp when the DAG run was created.
        new_sources (list[str]): List of newly extracted source identifiers.
        duplicate_sources (list[str]): List of source identifiers that were duplicates.
        failed_sources (list[str]): List of source identifiers that failed extraction.
    """

    dag_id: str
    execution_date: str
    timestamp: str
    new_sources: list[str]
    duplicate_sources: list[str] = []
    failed_sources: list[str] = []


class DagRunSummary(BaseModel):
    """Minimal metadata describing an Airflow DAG run.
    Attributes:
        dag_id (Optional[str]): Identifier of the DAG.
        dag_run_id (Optional[str]): Identifier of the DAG run.
        state (Optional[str]): Current state of the DAG run.
        execution_date (Optional[str]): Execution date of the DAG run.
        start_date (Optional[str]): Start date of the DAG run.
        end_date (Optional[str]): End date of the DAG run.
        run_type (Optional[str]): Type of the DAG run.
        external_trigger (Optional[bool]): Whether the DAG run was externally triggered.
    """

    dag_id: Optional[str]
    dag_run_id: Optional[str]
    state: Optional[str]
    execution_date: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    run_type: Optional[str]
    external_trigger: Optional[bool]


class DagRunsResponse(BaseModel):
    """Paginated response that wraps many DAG run summaries.
    Attributes:
        dag_id (str): Identifier of the DAG.
        total_entries (int): Total number of DAG runs.
        dag_runs (list[DagRunSummary]): List of DAG run summaries.
    """

    dag_id: str
    total_entries: int
    dag_runs: list[DagRunSummary]


class DagRunDetailResponse(DagRunSummary):
    """Detailed DAG run representation.
    Attributes:
        conf (Optional[dict]): Configuration dictionary used to trigger the DAG run.
    """


class TaskLogResponse(BaseModel):
    """Response payload that wraps task log content.
    Attributes:
        dag_id (str): Identifier of the DAG.
        dag_run_id (str): Identifier of the DAG run.
        task_id (str): Identifier of the task.
        try_number (int): Attempt number of the task execution.
        content (str): Log content of the task execution.
    """

    dag_id: str
    dag_run_id: str
    task_id: str
    try_number: int
    content: str


class CancelDagRunResponse(BaseModel):
    """Response that confirms manual DAG cancellation.
    Attributes:
        message (str): Confirmation message.
        dag_id (str): Identifier of the DAG.
        dag_run_id (str): Identifier of the DAG run.
        batch_id (Optional[str]): Associated batch identifier, if any.
        deleted_documents (Optional[dict[str, int]]): Summary of deleted documents by category.
        deleted_vector_documents (Optional[dict[str, int]]): Summary of deleted vector documents by category.
    """

    message: str
    dag_id: str
    dag_run_id: str
    batch_id: Optional[str] = None
    deleted_documents: Optional[dict[str, int]] = None
    deleted_vector_documents: Optional[dict[str, int]] = None


class SourceValidationRequest(BaseModel):
    """Request payload for validating uploaded sources.
    Attributes:
        sources (list[str]): List of source identifiers to validate.
    """

    sources: list[str]


class UploadedFileResponse(BaseModel):
    """Response describing a file stored by the API.
    Attributes:
        stored_path (str): The internal storage path of the file.
    """

    stored_path: str
