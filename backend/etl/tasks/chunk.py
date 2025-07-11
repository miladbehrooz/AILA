from typing import Annotated
from backend.etl.preprocessing.dispatchers import ChunkingDispatcher


def chunk_documents(
    documents: Annotated[list, "cleaned_documents"],
) -> Annotated[list, "chunked_documents"]:
    chunked_documents = []
    for document in documents:
        chunked_document = ChunkingDispatcher.dispatch(document)
        chunked_documents.append(chunked_document)

    return chunked_documents


if __name__ == "__main__":
    from backend.etl.tasks.clean import clean_documents
    from backend.etl.tasks.query_data_warehouse import query_data_warehouse

    batch_id = "batch_001"
    documents = query_data_warehouse(batch_id)
    cleaned_documents = clean_documents(documents)
    chunked_documents = chunk_documents(cleaned_documents)
    print(f"Chunked {len(chunked_documents)} documents.")
    # print(chunked_documents[0])
    for doc in chunked_documents:
        for chunk in doc:
            print(chunk.Config.category, chunk.content[:100], "\n")
            break
    #
