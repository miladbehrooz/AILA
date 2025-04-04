from abc import ABC, abstractmethod


from backend.etl.domain.base.nosql import NoSQLBaseDocument


class BaseExtractor(ABC):
    model: type(NoSQLBaseDocument)

    @abstractmethod
    def extract(self, **kwargs) -> None:
        pass


class URLExtractor(BaseExtractor):
    pass


class FileExtractor(BaseExtractor):
    pass
