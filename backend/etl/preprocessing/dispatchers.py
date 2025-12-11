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
from .embedding_data_handlers import (
    EmbeddingDataHandler,
    ArticleEmbeddingHandler,
    RepositoryEmbeddingHandler,
    YoutubeEmbeddingHandler,
    PDFEmbeddingHandler,
)

from backend.etl.domain.documents import (
    BaseDocument,
    NoSQLBaseDocument,
    RepositoryDocument,
    YoutubeDocument,
)
from backend.etl.domain.cleaned_documents import VectorBaseDocument
from backend.etl.domain.types import DataCategory
from backend.utils import logger


class CleaningHandlerFactory:
    """Factory that selects cleaning handlers per document category."""

    @staticmethod
    def create_handler(data_category: DataCategory) -> CleaningDataHandler:
        """Return a cleaning handler suited for the category."""
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
    """Dispatch cleaning operations to the correct handler.
    Attributes:
        factory (CleaningHandlerFactory): Factory to create cleaning handlers.
    """

    factory = CleaningHandlerFactory()

    @classmethod
    def dispatch(cls, data_model: NoSQLBaseDocument) -> VectorBaseDocument:
        """Clean the provided raw document using the appropriate handler.
        Args:
            data_model (NoSQLBaseDocument): The raw document to clean.
        Returns:
            VectorBaseDocument: The cleaned document model.
        """
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
    """Factory that selects chunking handlers per document category."""

    @staticmethod
    def create_handler(data_category: DataCategory) -> ChunkingDataHandler:
        """Return a chunking handler suited for the category.
        Args:
            data_category (DataCategory): The category of the data to chunk.
        Returns:
            ChunkingDataHandler: The appropriate chunking handler.
        """
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
    """Dispatch chunking operations to the correct handler.
    Attributes:
        factory (ChunkingHandlerFactory): Factory to create chunking handlers.
    """

    factory = ChunkingHandlerFactory

    @classmethod
    def dispatch(cls, data_model: VectorBaseDocument) -> list[VectorBaseDocument]:
        """Chunk the cleaned document using the registered handler.
        Args:
            data_model (VectorBaseDocument): The cleaned document to chunk.
        Returns:
            list[VectorBaseDocument]: List of chunk models derived from the document.
        """
        data_category = data_model.get_category()
        handler = cls.factory.create_handler(data_category)
        chunk_models = handler.chunk(data_model)

        logger.info(
            "Document chunked successfully.",
            num=len(chunk_models),
            data_category=data_category,
        )

        return chunk_models


class EmbeddingHandlerFactory:
    """Factory that selects embedding handlers per document category."""

    @staticmethod
    def create_handler(data_category: DataCategory) -> EmbeddingDataHandler:
        """Return an embedding handler suited for the category.
        Args:
            data_category (DataCategory): The category of the data to embed.
            Returns:
            EmbeddingDataHandler: The appropriate embedding handler.
        """

        if data_category == DataCategory.ARTICLES:
            return ArticleEmbeddingHandler()
        elif data_category == DataCategory.YOUTUBEVIDEOS:
            return YoutubeEmbeddingHandler()
        elif data_category == DataCategory.REPOSITORIES:
            return RepositoryEmbeddingHandler()
        elif data_category == DataCategory.PDFS:
            return PDFEmbeddingHandler()
        else:
            raise ValueError("Unsupported data type")


class EmbeddingDispatcher:
    """Dispatch embedding operations to the correct handler.
    Attributes:
        factory (EmbeddingHandlerFactory): Factory to create embedding handlers.
    """

    factory = EmbeddingHandlerFactory

    @classmethod
    def dispatch(
        cls, data_model: VectorBaseDocument | list[VectorBaseDocument]
    ) -> VectorBaseDocument | list[VectorBaseDocument]:
        """Embed one or many chunks while enforcing a consistent category.
        Args:
            data_model (VectorBaseDocument | list[VectorBaseDocument]): The chunk(s) to
                embed.
        Returns:
            VectorBaseDocument | list[VectorBaseDocument]: The embedded chunk model(s).
        """
        is_list = isinstance(data_model, list)
        if not is_list:
            data_model = [data_model]

        if len(data_model) == 0:
            return []

        data_category = data_model[0].get_category()
        assert all(
            data_model.get_category() == data_category for data_model in data_model
        ), "Data models must be of the same category."
        handler = cls.factory.create_handler(data_category)

        embedded_chunk_model = handler.embed_batch(data_model)

        if not is_list:
            embedded_chunk_model = embedded_chunk_model[0]

        logger.info(
            "Data embedded successfully.",
            data_category=data_category,
        )

        return embedded_chunk_model


if __name__ == "__main__":
    # Example usage
    from backend.etl.domain.documents import (
        BaseDocument,
        RepositoryDocument,
        PDFDocument,
        ArticleDocument,
    )

    # example_data = YoutubeDocument().find()
    result = BaseDocument().bulk_delete(batch_id="20251206_103555")
    print(result)

    # cleaned_doc = CleaningDispatcher.dispatch(example_data)

    # with open("cleaned_doc.txt", "w") as f:
    #     f.write(cleaned_doc.content)

    # chunked_docs = ChunkingDispatcher.dispatch(cleaned_doc)
    # print(len(chunked_docs))
    # embedded_docs = EmbeddingDispatcher.dispatch(chunked_docs)
    # print(len(embedded_docs))
    # print(len(embedded_docs[0].content))
