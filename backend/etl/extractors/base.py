from abc import ABC, abstractmethod
from enum import Enum

from backend.etl.domain.base.nosql import NoSQLBaseDocument


class ExtractionResult(str, Enum):
    """Outcome states emitted by extractors.
    Attributes:
        INSERTED (str): Data was successfully inserted.
        DUPLICATE (str): Data already exists; no insertion performed.
        FAILED (str): Extraction process failed.
    """

    INSERTED = "inserted"
    DUPLICATE = "duplicate"
    FAILED = "failed"


class BaseExtractor(ABC):
    """Abstract base for data extractors that save to persistence models.
    Attributes:
        model (type): The document model associated with the extractor.
    """

    model: type(NoSQLBaseDocument)

    @abstractmethod
    def extract(self, **kwargs) -> ExtractionResult:
        """Perform the extraction and return its status.
        Returns:
            ExtractionResult: The result of the extraction process.
        """


class URLExtractor(BaseExtractor):
    """Extractor specialization for remote HTTP sources.
    Returns:
        ExtractionResult: The result of the extraction process.
    """


class FileExtractor(BaseExtractor):
    """Extractor specialization for local files.
    Returns:
        ExtractionResult: The result of the extraction process.
    """
