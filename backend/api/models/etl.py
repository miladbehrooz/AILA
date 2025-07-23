from typing import Optional
from pydantic import BaseModel


class ETLRequest(BaseModel):
    sources: list[str]


class TriggerDAGResponse(BaseModel):
    message: str
    dag_id: str
    dag_run_id: str
    state: str


class DAGStatusResponse(BaseModel):
    dag_id: str
    dag_run_id: str
    state: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
