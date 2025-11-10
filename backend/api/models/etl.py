from typing import Optional
from pydantic import BaseModel


class ETLRequest(BaseModel):
    sources: list[str]


class TriggerDAGResponse(BaseModel):
    message: str
    dag_id: str
    dag_run_id: str
    state: str


class ExtractedSourcesResponse(BaseModel):
    dag_id: str
    execution_date: str
    timestamp: str
    new_sources: list[str]
    duplicate_sources: list[str] = []
    failed_sources: list[str] = []


class DagRunSummary(BaseModel):
    dag_id: Optional[str]
    dag_run_id: Optional[str]
    state: Optional[str]
    execution_date: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    run_type: Optional[str]
    external_trigger: Optional[bool]


class DagRunsResponse(BaseModel):
    dag_id: str
    total_entries: int
    dag_runs: list[DagRunSummary]


class DagRunDetailResponse(DagRunSummary):
    pass


class TaskLogResponse(BaseModel):
    dag_id: str
    dag_run_id: str
    task_id: str
    try_number: int
    content: str


class CancelDagRunResponse(BaseModel):
    message: str
    dag_id: str
    dag_run_id: str


class SourceValidationRequest(BaseModel):
    sources: list[str]
