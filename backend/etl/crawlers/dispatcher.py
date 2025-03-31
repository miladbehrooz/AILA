import os
from urllib.parse import urlparse
from typing import Dict
from loguru import logger

from .base import BaseCrawler
from .article import ArticleCrawler
from .youtube import YoutubeVideoCrawler
from .files import PDFFileCrawler, WordFileCrawler, TextFileCrawler


FILE_EXTENSION_DISPATCH_TABLE: Dict[str, BaseCrawler] = {
    ".pdf": PDFFileCrawler(),
    ".docx": WordFileCrawler(),
    ".txt": TextFileCrawler(),
}


# TODO: think about how to register new crawlers
class CrawlerDispatcher:
    def __init__(self) -> None:
        self.url_crawler = {}
        self.file_crawlers = {}
        self.url_crawlers: Dict[str, BaseCrawler] = {
            "www.youtube.com": YoutubeVideoCrawler(),
        }

        self.file_crawlers: Dict[str, BaseCrawler] = FILE_EXTENSION_DISPATCH_TABLE

        self.default_crawler = ArticleCrawler()

    # def register_url_crawler(self, domain: str, crawler: BaseCrawler) -> None:
    #     self.url_crawlers[domain] = crawler

    # def register_file_crawler(self, extension: str, crawler: BaseCrawler) -> None:
    #     self.file_crawlers[extension.lower()] = crawler

    def extract(self, source: str, **kwargs) -> None:
        try:
            if source.startswith("https"):
                parsed_url = urlparse(source)
                domain = parsed_url.netloc.lower()
                crawler = self.url_crawlers.get(domain, self.default_crawler)

            else:
                extension = os.path.splitext(source)[1].lower()
                crawler = self.file_crawlers.get(extension)
                if crawler is None:
                    logger.warning(
                        f"No crawler registered for file extension: {extension}"
                    )
                    return

            crawler.extract(source, **kwargs)

        except Exception as e:
            logger.error(f"Failed to dispatch and extract: {e}")


if __name__ == "__main__":
    dispatcher = CrawlerDispatcher()

    dispatcher.extract("https://www.youtube.com/watch?v=RoR4XJw8wIc")
    dispatcher.extract("https://weaviate.io/blog/advanced-rag")
    # dispatcher.extract("path/to/file.pdf")
