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

    result = delete_all_data(batch_id=batch_id)
    logger.info(
        f"Deleted {result} documents wtih batch_id {batch_id} from the data warehouse."
    )
    return result


def delete_all_data(batch_id: UUID) -> dict[str, int]:

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
    return ArticleDocument.bulk_delete(batch_id=batch_id)


def __delete_youtube_videos(batch_id: UUID) -> int:
    return YoutubeDocument.bulk_delete(batch_id=batch_id)


def __delete_repositories(batch_id: UUID) -> int:
    return RepositoryDocument.bulk_delete(batch_id=batch_id)


def __delete_pdfs(batch_id: UUID) -> int:
    return PDFDocument.bulk_delete(batch_id=batch_id)


if __name__ == "__main__":
    result = delete_all_data(batch_id=uuid4())
    print(result)
