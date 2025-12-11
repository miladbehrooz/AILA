from typing import TypedDict
from uuid import UUID, uuid4
from airflow.decorators import task
from backend.etl.extractors.dispatcher import ExtractorDispatcher
from backend.etl.extractors.base import ExtractionResult
from backend.utils import logger


class ExtractionSummary(TypedDict):
    """Summary of extraction outcomes grouped by status.
    Attributes:
        new_sources (list[str]): List of sources that were newly inserted.
        duplicate_sources (list[str]): List of sources that were found to be duplicates.
        failed_sources (list[str]): List of sources for which extraction failed.
    """

    new_sources: list[str]
    duplicate_sources: list[str]
    failed_sources: list[str]


@task
def extract_sources(sources: list[str], batch_id: UUID) -> ExtractionSummary:
    """Extract each requested source with the appropriate extractor.

    Args:
        sources (list[str]): URLs or file paths to ingest.
        batch_id (UUID): Identifier assigned to the extraction batch.

    Returns:
        ExtractionSummary: Aggregated statistics of inserted, duplicate, and failed
            sources.
    """
    dispatcher = (
        ExtractorDispatcher.build().register_pdf().register_github().register_youtube()
    )

    logger.info(f"Starting to extract {len(sources)} source(s).")
    summary: ExtractionSummary = {
        "new_sources": [],
        "duplicate_sources": [],
        "failed_sources": [],
    }

    for source in sources:
        result = _extract_source(dispatcher, source, batch_id)

        if result == ExtractionResult.INSERTED:
            summary["new_sources"].append(source)
        elif result == ExtractionResult.DUPLICATE:
            summary["duplicate_sources"].append(source)
        else:
            summary["failed_sources"].append(source)

    logger.info(
        (
            "Extraction summary - new: {new_count}, duplicates: {dup_count}, "
            "failed: {fail_count} (total requested: {total})"
        ).format(
            new_count=len(summary["new_sources"]),
            dup_count=len(summary["duplicate_sources"]),
            fail_count=len(summary["failed_sources"]),
            total=len(sources),
        )
    )

    return summary


def _extract_source(
    dispatcher: ExtractorDispatcher, source: str, batch_id: UUID
) -> ExtractionResult:
    """Run a single extractor and normalize its return type.

    Args:
        dispatcher (ExtractorDispatcher): Dispatcher with registered extractors.
        source (str): URL or path pointing to the source to ingest.
        batch_id (UUID): Identifier assigned to the extraction batch.

    Returns:
        ExtractionResult: Normalized status code from the extractor.
    """
    extractor = dispatcher.get_extractor(source)

    try:
        result = extractor.extract(source, batch_id=batch_id)

        if isinstance(result, ExtractionResult):
            return result

        return ExtractionResult.INSERTED if result else ExtractionResult.FAILED
    except Exception as e:
        logger.error(f"An error occurred while extracting: {e!s}")

        return ExtractionResult.FAILED


if __name__ == "__main__":
    sources = [
        "https://weaviate.io/blog/advanced-rag,"
        "https://www.youtube.com/watch?v=T-D1OfcDW1M&t=5s",
        "backend/data/book.pdf",
        "https://github.com/PacktPublishing/LLM-Engineers-Handbook.git",
    ]
    extract_sources(sources, uuid4())
