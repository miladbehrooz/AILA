from uuid import UUID, uuid4

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
from backend.utils import logger

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
    """Remove every vector document for a batch from Mongo and Qdrant.

    Args:
        batch_id (UUID): Identifier of the batch whose vectors should be deleted.

    Returns:
        dict[str, int]: Per-collection deletion counts.
    """
    summary = delete_all_vectors(batch_id=batch_id)
    logger.info(
        "Deleted vector documents for batch_id {} with summary {}",
        batch_id,
        summary,
    )
    return summary


def delete_all_vectors(batch_id: UUID) -> dict[str, int]:
    """Delete batch-specific documents from each vector-backed collection.

    Args:
        batch_id (UUID): Batch identifier applied to the stored vectors.

    Returns:
        dict[str, int]: Per collection count of deleted items.
    """
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
