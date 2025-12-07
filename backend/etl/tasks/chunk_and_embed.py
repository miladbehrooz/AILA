from typing import Annotated
from airflow.decorators import task
from backend.etl.domain import embedded_chunks
from backend.etl.preprocessing.dispatchers import (
    ChunkingDispatcher,
    EmbeddingDispatcher,
)
from backend.utils.misc import batch


@task
def chunk_and_embed_documents(
    documents: Annotated[list, "cleaned_documents"],
) -> Annotated[list, "embedded_documents"]:
    embedded_chunks = []
    for document in documents:
        chunks = ChunkingDispatcher.dispatch(document)

        for batched_chunks in batch(chunks, 10):
            batched_embedded_chunks = EmbeddingDispatcher.dispatch(batched_chunks)
            embedded_chunks.extend(batched_embedded_chunks)

    return embedded_chunks


if __name__ == "__main__":
    from backend.etl.tasks.clean import clean_documents
    from backend.etl.tasks.query_data_warehouse import query_data_warehouse
    from uuid import uuid4

    batch_id = uuid4()
    documents = query_data_warehouse(batch_id, True)
    cleaned_documents = clean_documents(documents)
    embedded_chunks = chunk_and_embed_documents(cleaned_documents)
    print(f"Embedded {len(embedded_chunks)} chunks.")
