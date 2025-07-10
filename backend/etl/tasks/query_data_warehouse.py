from typing import Annotated
from loguru import logger
from concurrent.futures import ThreadPoolExecutor, as_completed

from mongoengine.base import document
from backend.etl.domain.base.nosql import NoSQLBaseDocument
from backend.etl.domain.documents import (
    ArticleDocument,
    PDFDocument,
    YoutubeDocument,
    RepositoryDocument,
)


def query_data_warehouse() -> Annotated[list, "raw documents"]:

    documents = []
    logger.info("Fetching data from the data warehouse")
    # Fetch all data from the data warehouse
    result = fetch_all_data()
    # Flatten the list of documents
    document = [doc for query_result in result.values() for doc in query_result]
    # Add the documents to the list
    documents.extend(document)

    return documents


def fetch_all_data() -> dict[str, list[NoSQLBaseDocument]]:

    with ThreadPoolExecutor() as executor:

        future_to_query = {
            executor.submit(__fetch_articles): "articles",
            executor.submit(__fetch_youtube_videos): "youtube_videos",
            executor.submit(__fetch_repositories): "repositories",
            executor.submit(__fetch_pdfs): "pdfs",
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


def __fetch_articles() -> list[NoSQLBaseDocument]:
    return ArticleDocument.bulk_find()


def __fetch_youtube_videos() -> list[NoSQLBaseDocument]:
    return YoutubeDocument.bulk_find()


def __fetch_repositories() -> list[NoSQLBaseDocument]:
    return RepositoryDocument.bulk_find()


def __fetch_pdfs() -> list[NoSQLBaseDocument]:
    return PDFDocument.bulk_find()


if __name__ == "__main__":

    print(query_data_warehouse())
