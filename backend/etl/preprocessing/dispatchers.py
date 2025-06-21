from loguru import logger
from pydantic.type_adapter import P

from .cleaning_data_handlers import (
    CleaningDataHandler,
    ArticleCleaningHandler,
    YoutubeCleaningHandler,
    RepositoryCleaningHandler,
    PDFCleaningHandler,
)

from .chunking_data_handlers import (
    ChunkingDataHandler,
    ArticleChunkingHandler,
    PDFChunkingHandler,
    YoutubeChunkingHandler,
    RepositoryChunkingHandler,
)
from backend.etl.domain.documents import NoSQLBaseDocument, RepositoryDocument
from backend.etl.domain.cleaned_documents import VectorBaseDocument
from backend.etl.domain.types import DataCategory


class CleaningHandlerFactory:
    @staticmethod
    def create_handler(data_category: DataCategory) -> CleaningDataHandler:
        if data_category == DataCategory.ARTICLES:
            return ArticleCleaningHandler()
        elif data_category == DataCategory.YOUTUBEVIDEOS:
            return YoutubeCleaningHandler()
        elif data_category == DataCategory.REPOSITORIES:
            return RepositoryCleaningHandler()
        elif data_category == DataCategory.PDFS:
            return PDFCleaningHandler()
        else:
            raise ValueError("Unsupported data type")


class CleaningDispatcher:
    factory = CleaningHandlerFactory()

    @classmethod
    def dispatch(cls, data_model: NoSQLBaseDocument) -> VectorBaseDocument:
        data_category = DataCategory(data_model.get_collection_name())
        handler = cls.factory.create_handler(data_category)
        clean_model = handler.clean(data_model)

        logger.info(
            "Document cleaned successfully.",
            data_category=data_category,
            cleaned_content_len=len(clean_model.content),
        )

        return clean_model


class ChunkingHandlerFactory:
    @staticmethod
    def create_handler(data_category: DataCategory) -> ChunkingDataHandler:
        if data_category == DataCategory.ARTICLES:
            return ArticleChunkingHandler()
        elif data_category == DataCategory.YOUTUBEVIDEOS:
            return YoutubeChunkingHandler()
        elif data_category == DataCategory.REPOSITORIES:
            return RepositoryChunkingHandler()
        elif data_category == DataCategory.PDFS:
            return PDFChunkingHandler()
        else:
            raise ValueError("Unsupported data type")


class ChunkingDispatcher:
    factory = ChunkingHandlerFactory

    @classmethod
    def dispatch(cls, data_model: VectorBaseDocument) -> list[VectorBaseDocument]:
        data_category = data_model.get_category()
        handler = cls.factory.create_handler(data_category)
        chunk_models = handler.chunk(data_model)

        logger.info(
            "Document chunked successfully.",
            num=len(chunk_models),
            data_category=data_category,
        )

        return chunk_models


if __name__ == "__main__":
    # Example usage
    from backend.etl.domain.documents import RepositoryDocument, PDFDocument

    example_data = PDFDocument().find()

    cleaned_doc = CleaningDispatcher.dispatch(example_data)
    print(cleaned_doc)
    chunked_docs = ChunkingDispatcher.dispatch(cleaned_doc)
    print(len(chunked_docs))
    for chunk in chunked_docs:
        print(
            chunk.content[:100], chunk.document_id, chunk.id
        )  # Print first 50 characters of each chunk
