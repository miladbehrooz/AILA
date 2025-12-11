from concurrent.futures import ThreadPoolExecutor, as_completed
from uuid import UUID, uuid4
from backend.utils import logger
from backend.etl.domain.documents import (
    ArticleDocument,
    PDFDocument,
    YoutubeDocument,
    RepositoryDocument,
)


def clean_data_warehouse(batch_id: UUID) -> dict[str, int]:
    """Delete all raw documents for a batch from the Mongo warehouse.

    Args:
        batch_id (UUID): Identifier that groups the extracted sources.

    Returns:
        dict[str, int]: Per-collection deletion counts.
    """

    result = delete_all_data(batch_id=batch_id)
    logger.info(
        f"Deleted {result} documents wtih batch_id {batch_id} from the data warehouse."
    )
    return result


def delete_all_data(batch_id: UUID) -> dict[str, int]:
    """Remove documents of every type concurrently.

    Args:
        batch_id (UUID): Identifier of the batch to remove.

    Returns:
        dict[str, int]: Per-type deletion counts.
    """

    with ThreadPoolExecutor() as executor:

        future_to_query = {
            executor.submit(__delete_articles, batch_id): "articles",
            executor.submit(__delete_youtube_videos, batch_id): "youtube_videos",
            executor.submit(__delete_repositories, batch_id): "repositories",
            executor.submit(__delete_pdfs, batch_id): "pdfs",
        }

        results = {}

        for future in as_completed(future_to_query):
            query_name = future_to_query[future]
            try:
                results[query_name] = future.result()
            except Exception as exc:
                logger.exception(f"{query_name} request failed.")
                results[query_name] = []
    return results


def __delete_articles(batch_id: UUID) -> int:
    """Remove articles for the target batch.
    Args:
        batch_id (UUID): Identifier of the batch to remove.
    Returns:
        int: Number of articles deleted.
    """
    return ArticleDocument.bulk_delete(batch_id=batch_id)


def __delete_youtube_videos(batch_id: UUID) -> int:
    """Remove videos for the target batch.
    Args:
        batch_id (UUID): Identifier of the batch to remove.
    Returns:
        int: Number of YouTube videos deleted.
    """
    return YoutubeDocument.bulk_delete(batch_id=batch_id)


def __delete_repositories(batch_id: UUID) -> int:
    """Remove repositories for the target batch."""
    return RepositoryDocument.bulk_delete(batch_id=batch_id)


def __delete_pdfs(batch_id: UUID) -> int:
    """Remove PDFs for the target batch.
    Args:
        batch_id (UUID): Identifier of the batch to remove.
    Returns:
        int: Number of PDFs deleted.
    """
    return PDFDocument.bulk_delete(batch_id=batch_id)


if __name__ == "__main__":
    result = delete_all_data(batch_id=uuid4())
    print(result)
