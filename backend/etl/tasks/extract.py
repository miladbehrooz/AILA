from typing import Annotated
from tqdm import tqdm
from loguru import logger

from airflow.decorators import task
from backend.etl.extractors.dispatcher import ExtractorDispatcher


@task
def extract_sources(sources: list[str]) -> Annotated[list[str], "crawled_links"]:
    dispatcher = (
        ExtractorDispatcher.build().register_pdf().register_github().register_youtube()
    )

    logger.info(f"Starting to extract {len(sources)} source(s).")

    successfull_extracts = 0
    for source in tqdm(sources):
        successfull_extract = _extract_source(dispatcher, source)
        successfull_extracts += successfull_extract

    logger.info(
        f"Successfully extracted {successfull_extracts} / {len(sources)} sources."
    )

    return sources


def _extract_source(dispatcher: ExtractorDispatcher, source: str) -> bool:
    extractor = dispatcher.get_extractor(source)

    try:
        extractor.extract(source)

        return True
    except Exception as e:
        logger.error(f"An error occurred while extracting: {e!s}")

        return False


if __name__ == "__main__":
    sources = [
        "https://weaviate.io/blog/advanced-rag,"
        "https://www.youtube.com/watch?v=T-D1OfcDW1M&t=5s",
        "backend/data/book.pdf",
        "https://github.com/PacktPublishing/LLM-Engineers-Handbook.git",
    ]

    extract_sources(sources)
