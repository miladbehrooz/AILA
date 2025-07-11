from typing import Annotated
from backend.etl.preprocessing.dispatchers import CleaningDispatcher


def clean_documents(
    documents: Annotated[list, "raw_documents"],
) -> Annotated[list, "cleaned_documents"]:
    cleaned_documents = []
    for document in documents:
        cleaned_document = CleaningDispatcher.dispatch(document)
        cleaned_documents.append(cleaned_document)

    return cleaned_documents


if __name__ == "__main__":
    from backend.etl.tasks.query_data_warehouse import query_data_warehouse

    batch_id = "batch_001"
    documents = query_data_warehouse(batch_id)
    cleaned_documents = clean_documents(documents)
    print(f"Cleaned {len(cleaned_documents)} documents.")
    for doc in cleaned_documents:
        print(
            doc.Config.name, doc.content[:100], "\n"
        )  # Print the first 100 characters of each cleaned document
