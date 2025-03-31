from .base import BaseCrawler


class PDFFileCrawler(BaseCrawler):

    def __init__(self) -> None:
        super().__init__()

    def extract(self, source: str, **kwargs) -> None:
        raise NotImplementedError


class WordFileCrawler(BaseCrawler):

    def __init__(self) -> None:
        super().__init__()

    def extract(self, source: str, **kwargs) -> None:
        raise NotImplementedError


class TextFileCrawler(BaseCrawler):

    def __init__(self) -> None:
        super().__init__()

    def extract(self, source: str, **kwargs) -> None:
        raise NotImplementedError
