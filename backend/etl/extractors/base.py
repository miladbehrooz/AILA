from abc import ABC, abstractmethod
from enum import Enum

from backend.etl.domain.base.nosql import NoSQLBaseDocument


class ExtractionResult(str, Enum):
    INSERTED = "inserted"
    DUPLICATE = "duplicate"
    FAILED = "failed"


class BaseExtractor(ABC):
    model: type(NoSQLBaseDocument)

    @abstractmethod
    def extract(self, **kwargs) -> ExtractionResult:
        pass


class URLExtractor(BaseExtractor):
    pass


class FileExtractor(BaseExtractor):
    pass
