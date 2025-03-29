from abc import ABC, abstractmethod


from backend.etl.domain.base.nosql import NoSQLBaseDocument


class BaseCrawler(ABC):
    model: type(NoSQLBaseDocument)

    @abstractmethod
    def extract(self, link: str, **kwargs) -> None:
        pass
