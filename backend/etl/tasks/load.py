from typing import Annotated
from airflow.decorators import task
from backend.etl.domain.base.vector import VectorBaseDocument
from backend.utils.misc import batch
from backend.utils import logger


@task
def load_to_vector_db(
    documents: Annotated[list, "documents"],
) -> Annotated[bool, "successful"]:
    logger.info(f"Loading {len(documents)} documents into the vector database.")

    grouped_documents = VectorBaseDocument.group_by_class(documents)
    for document_class, documents in grouped_documents.items():
        logger.info(f"Loading documents into {document_class.get_collection_name()}")
        for documents_batch in batch(documents, size=4):
            try:
                document_class.bulk_insert(documents_batch)
            except Exception:
                logger.error(
                    f"Failed to insert documents into {document_class.get_collection_name()}"
                )

                return False

    return True


if __name__ == "__main__":
    from backend.etl.tasks.clean import clean_documents
    from backend.etl.tasks.query_data_warehouse import query_data_warehouse
    from backend.etl.tasks.chunk_and_embed import chunk_and_embed_documents

    batch_id = "batch_001"
    documents = query_data_warehouse(batch_id)
    cleaned_documents = clean_documents(documents)
    embedded_chunks = chunk_and_embed_documents(cleaned_documents)
    successful = load_to_vector_db(embedded_chunks)
    if successful:
        logger.info(
            f"Successfully loaded {len(embedded_chunks)} embedded chunks to the vector database."
        )
