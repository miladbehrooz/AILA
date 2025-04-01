from .base import BaseExtractor


class PDFFileExtractor(BaseExtractor):

    def extract(self, source: str, **kwargs) -> None:
        raise NotImplementedError


class WordFileExtractor(BaseExtractor):

    def extract(self, source: str, **kwargs) -> None:
        raise NotImplementedError


class TextFileExtractor(BaseExtractor):

    def extract(self, source: str, **kwargs) -> None:
        raise NotImplementedError
