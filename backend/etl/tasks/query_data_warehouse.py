from typing import Annotated

from loguru import logger

from concurrent.futures import ThreadPoolExecutor, as_completed
from airflow.decorators import task

from backend.etl.domain.base.nosql import NoSQLBaseDocument
from backend.etl.domain.documents import (
    ArticleDocument,
    PDFDocument,
    YoutubeDocument,
    RepositoryDocument,
)


@task
def query_data_warehouse(
    batch_id: str, is_extracted: bool
) -> Annotated[list, "raw documents"]:
    if is_extracted:

        documents = []
        logger.info("Fetching data from the data warehouse")
        # Fetch all data from the data warehouse
        result = fetch_all_data(batch_id)
        # Flatten the list of documents
        document = [doc for query_result in result.values() for doc in query_result]
        # Add the documents to the list
        documents.extend(document)

        return documents

    return []


def fetch_all_data(batch_id: str) -> dict[str, list[NoSQLBaseDocument]]:

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
            except Exception as exc:
                logger.exception(f"{query_name} request failed.")

                results[query_name] = []

    return results


def __fetch_articles(batch_id: str) -> list[NoSQLBaseDocument]:
    return ArticleDocument.bulk_find(batch_id=batch_id)


def __fetch_youtube_videos(batch_id: str) -> list[NoSQLBaseDocument]:
    return YoutubeDocument.bulk_find(batch_id=batch_id)


def __fetch_repositories(batch_id: str) -> list[NoSQLBaseDocument]:
    return RepositoryDocument.bulk_find(batch_id=batch_id)


def __fetch_pdfs(batch_id: str) -> list[NoSQLBaseDocument]:
    return PDFDocument.bulk_find(batch_id=batch_id)


if __name__ == "__main__":
    batch_id = "batch_001"
    docs = query_data_warehouse(batch_id)
    print(docs)
