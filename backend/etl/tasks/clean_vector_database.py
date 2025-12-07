from uuid import UUID, uuid4
from backend.utils import logger
from backend.etl.domain.cleaned_documents import (
    CleanedArticleDocument,
    CleanedPDFDocument,
    CleanedRepositoryDocument,
    CleanedYoutubeDocument,
)
from backend.etl.domain.embedded_chunks import (
    EmbeddedArticleChunk,
    EmbeddedPDFChunk,
    EmbeddedRepositoryChunk,
    EmbeddedYoutubeChunk,
)


VECTOR_DOCUMENT_MODELS = (
    CleanedArticleDocument,
    CleanedYoutubeDocument,
    CleanedRepositoryDocument,
    CleanedPDFDocument,
    EmbeddedArticleChunk,
    EmbeddedYoutubeChunk,
    EmbeddedRepositoryChunk,
    EmbeddedPDFChunk,
)


def clean_vector_database(batch_id: UUID) -> dict[str, int]:
    summary = delete_all_vectors(batch_id=batch_id)
    logger.info(
        "Deleted vector documents for batch_id {} with summary {}",
        batch_id,
        summary,
    )
    return summary


def delete_all_vectors(batch_id: UUID) -> dict[str, int]:
    deletion_summary: dict[str, int] = {}
    for document_cls in VECTOR_DOCUMENT_MODELS:
        collection_name = document_cls.get_collection_name()

        try:
            deleted_count = document_cls.bulk_delete(batch_id=batch_id)
        except Exception:
            logger.exception(
                "Failed to delete records from collection={} for batch_id={}",
                collection_name,
                batch_id,
            )
            deleted_count = 0

        deletion_summary[collection_name] = deleted_count
        logger.info(
            "Deleted {} vector document(s) from collection='{}' for batch_id={}",
            deleted_count,
            collection_name,
            batch_id,
        )

    return deletion_summary


if __name__ == "__main__":
    print(delete_all_vectors(batch_id=uuid4()))
