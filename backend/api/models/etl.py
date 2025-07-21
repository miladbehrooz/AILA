from pydantic import BaseModel
from typing import List


class ETLRequest(BaseModel):
    sources: List[str]
