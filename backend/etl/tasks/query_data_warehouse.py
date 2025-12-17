from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Annotated
from uuid import UUID, uuid4

from airflow.decorators import task

from backend.etl.domain.base.nosql import NoSQLBaseDocument
from backend.etl.domain.documents import (
    ArticleDocument,
    PDFDocument,
    RepositoryDocument,
    YoutubeDocument,
)
from backend.utils import logger


@task
def query_data_warehouse(
    batch_id: UUID, new_extraction: bool
) -> Annotated[list, "raw documents"]:
    """Fetch all raw documents belonging to a batch from the warehouse.

    Args:
        batch_id (UUID): Identifier for the extraction batch.
        new_extraction (bool): Whether the upstream extraction produced new data.

    Returns:
        list: Raw document models, or an empty list when nothing new is available.
    """
    if not new_extraction:
        logger.info("No new data extracted. Skipping warehouse query.")
        return []

    documents = []
    logger.info("Fetching data from the data warehouse")
    # Fetch all data from the data warehouse
    result = fetch_all_data(batch_id)
    # Flatten the list of documents
    document = [doc for query_result in result.values() for doc in query_result]
    # Add the documents to the list
    documents.extend(document)
    logger.info(f"Fetched {len(documents)} documents from the data warehouse.")

    return documents


def fetch_all_data(batch_id: UUID) -> dict[str, list[NoSQLBaseDocument]]:
    """Load all document types concurrently for the requested batch.

    Args:
        batch_id (UUID): Identifier assigned to the extracted sources.

    Returns:
        dict[str, list[NoSQLBaseDocument]]: Mapping with the records fetched for each
            collection.
    """

    with ThreadPoolExecutor() as executor:

        future_to_query = {
            executor.submit(__fetch_articles, batch_id): "articles",
            executor.submit(__fetch_youtube_videos, batch_id): "youtube_videos",
            executor.submit(__fetch_repositories, batch_id): "repositories",
            executor.submit(__fetch_pdfs, batch_id): "pdfs",
        }

        results = {}
        for future in as_completed(future_to_query):
            query_name = future_to_query[future]
            try:
                results[query_name] = future.result()
            except Exception:
                logger.exception(f"{query_name} request failed.")

                results[query_name] = []

    return results


def __fetch_articles(batch_id: UUID) -> list[NoSQLBaseDocument]:
    """Retrieve article documents for the target batch.
    Args:
        batch_id (UUID): Batch identifier to filter the articles.
    Returns:
        list[NoSQLBaseDocument]: List of article documents for the batch.
    """
    return ArticleDocument.bulk_find(batch_id=batch_id)


def __fetch_youtube_videos(batch_id: UUID) -> list[NoSQLBaseDocument]:
    """Retrieve YouTube documents for the target batch.
    Args:
        batch_id (UUID): Batch identifier to filter the YouTube videos.
    Returns:
            list[NoSQLBaseDocument]: List of YouTube documents for the batch.
    """
    return YoutubeDocument.bulk_find(batch_id=batch_id)


def __fetch_repositories(batch_id: UUID) -> list[NoSQLBaseDocument]:
    """Retrieve repository documents for the target batch.
    Args:
        batch_id (UUID): Batch identifier to filter the repositories.
    Returns:
        list[NoSQLBaseDocument]: List of repository documents for the batch.
    """
    return RepositoryDocument.bulk_find(batch_id=batch_id)


def __fetch_pdfs(batch_id: UUID) -> list[NoSQLBaseDocument]:
    """Retrieve PDF documents for the target batch.
    Args:
        batch_id (UUID): Batch identifier to filter the PDFs.
    Returns:
        list[NoSQLBaseDocument]: List of PDF documents for the batch.
    """
    return PDFDocument.bulk_find(batch_id=batch_id)


if __name__ == "__main__":
    batch_id = uuid4()
    docs = query_data_warehouse(batch_id, True)
    print(docs)
