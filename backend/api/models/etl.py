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
