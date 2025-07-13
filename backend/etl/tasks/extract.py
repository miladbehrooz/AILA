from typing import Annotated
from tqdm import tqdm
from loguru import logger

from airflow.decorators import task
from backend.etl.extractors.dispatcher import ExtractorDispatcher


@task
def extract_sources(sources: list[str], batch_id: str) -> bool:
    dispatcher = (
        ExtractorDispatcher.build().register_pdf().register_github().register_youtube()
    )

    logger.info(f"Starting to extract {len(sources)} source(s).")
    try:
        successful_extracts = 0
        for source in sources:
            success = _extract_source(dispatcher, source, batch_id)
            if success:
                successful_extracts += 1

        logger.info(
            f"Successfully extracted {successful_extracts} / {len(sources)} sources."
        )

        # return True only if at least one new extraction happened
        return successful_extracts > 0

    except Exception as e:
        logger.error(f"An error occurred during extraction: {e!s}")
        return False


def _extract_source(
    dispatcher: ExtractorDispatcher, source: str, batch_id: str
) -> bool:
    extractor = dispatcher.get_extractor(source)

    try:
        success = extractor.extract(source, batch_id=batch_id)

        return success
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
