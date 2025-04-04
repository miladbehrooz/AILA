import os
import re
from urllib.parse import urlparse
from loguru import logger

from .base import BaseExtractor, URLExtractor, FileExtractor
from .article import ArticleExtractor
from .youtube import YoutubeVideoExtractor
from .github import GithubExtractor
from .files import PDFFileExtractor, WordFileExtractor, TextFileExtractor


# TODO: introduce wrapper function for register different extractors like youtube, article and ...
class ExtractorDispatcher:
    def __init__(self):
        self._url_extractors: dict[str, type[URLExtractor]] = {}
        self._file_extractors: dict[str, type[FileExtractor]] = {}

    @classmethod
    def build(cls) -> "ExtractorDispatcher":
        dispatcher = cls()

        return dispatcher

    def register_youtube(self) -> "ExtractorDispatcher":
        self.register_url_extractor("https://youtube.com", YoutubeVideoExtractor)
        return self

    def register_github(self) -> "ExtractorDispatcher":
        self.register_url_extractor("https://github.com", GithubExtractor)
        return self

    def register_pdf(self) -> "ExtractorDispatcher":
        self.register_file_extractor("pdf", PDFFileExtractor)
        return self

    def register_url_extractor(
        self, domain: str, extractor_cls: type[URLExtractor]
    ) -> "ExtractorDispatcher":
        parsed = urlparse(domain)
        domain = parsed.netloc or parsed.path
        pattern = rf"https://(www\.)?{re.escape(domain)}/*"
        self._url_extractors[pattern] = extractor_cls
        return self

    def register_file_extractor(
        self, extension: str, extractor_cls: type[FileExtractor]
    ) -> "ExtractorDispatcher":
        self._file_extractors[extension.lower()] = extractor_cls
        return self

    def get_extractor(self, source: str) -> BaseExtractor | None:
        parsed = urlparse(source)
        is_url = bool(parsed.scheme and parsed.netloc)

        if is_url:
            for pattern, extractor_cls in self._url_extractors.items():
                if re.match(pattern, source):
                    logger.info(f"Using URL extractor: {extractor_cls.__name__}")
                    return extractor_cls()
            logger.warning(f"No URL extractor matched for {source}. Using default.")
            return ArticleExtractor()

        elif os.path.isfile(source) or "." in source:
            ext = source.split(".")[-1].lower()
            extractor_cls = self._file_extractors.get(ext)
            if extractor_cls:
                logger.info(f"Using File extractor: {extractor_cls.__name__}")
                return extractor_cls()
            logger.warning(f"No file extractor for extension: {ext}")
            return None

        else:
            logger.warning(f"Input not recognized as URL or file: {source}")
            return None


if __name__ == "__main__":
    dispatcher = (
        ExtractorDispatcher()
        .build()
        .register_github()
        .register_pdf()
        .register_youtube()
    )
    # youtube
    extractor = dispatcher.get_extractor(
        "https://www.youtube.com/watch?v=RoR4XJw8wIc"
    ).extract("https://www.youtube.com/watch?v=RoR4XJw8wIc")

    # article
    extractor = dispatcher.get_extractor(
        "https://weaviate.io/blog/advanced-rag"
    ).extract("https://weaviate.io/blog/advanced-rag")

    # article
    extractor = dispatcher.get_extractor(
        "https://www.galileo.ai/blog/mastering-rag-how-to-architect-an-enterprise-rag-system?utm_medium=email&_hsmi=295779507&_hsenc=p2ANqtz-8eAJWFwi6ewcZByCnzRTPlokRRzNluJMKWKRuvtur3C15XZgRBe_IA4NDFn7y0KBNXtjhRWDVfChYwtKF-yqk8IQ9bBQ&utm_content=295779191&utm_source=hs_email#encoder"
    ).extract(
        "https://www.galileo.ai/blog/mastering-rag-how-to-architect-an-enterprise-rag-system?utm_medium=email&_hsmi=295779507&_hsenc=p2ANqtz-8eAJWFwi6ewcZByCnzRTPlokRRzNluJMKWKRuvtur3C15XZgRBe_IA4NDFn7y0KBNXtjhRWDVfChYwtKF-yqk8IQ9bBQ&utm_content=295779191&utm_source=hs_email#encoder"
    )

    # book
    extractor = dispatcher.get_extractor("backend/data/book.pdf").extract(
        "backend/data/book.pdf"
    )

    # github
    extractor = dispatcher.get_extractor(
        "https://github.com/PacktPublishing/LLM-Engineers-Handbook.git"
    )
    extractor.extract("https://github.com/PacktPublishing/LLM-Engineers-Handbook.git")
