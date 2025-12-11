from abc import ABC, abstractmethod
from typing import Generic, TypeVar, cast

from backend.embeddings import EmbeddingModelSingleton
from backend.etl.domain.chunks import (
    Chunk,
    ArticleChunk,
    RepositoryChunk,
    YoutubeChunk,
    PDFChunk,
)
from backend.etl.domain.embedded_chunks import (
    EmbeddedChunk,
    EmbeddedArticleChunk,
    EmbeddedRepositoryChunk,
    EmbeddedYoutubeChunk,
    EmbeddedPDFChunk,
)

ChunkT = TypeVar("ChunkT", bound=Chunk)
EmbeddedChunkT = TypeVar("EmbeddedChunkT", bound=EmbeddedChunk)

embedding_model = EmbeddingModelSingleton()


class EmbeddingDataHandler(ABC, Generic[ChunkT, EmbeddedChunkT]):
    """Base interface for mapping chunks into embedded representations."""

    def embed_batch(self, data_model: list[ChunkT]) -> list[EmbeddedChunkT]:
        """Embed a batch of chunks with the shared embedding model.
        Args:
            data_model (list[ChunkT]): List of chunk models to embed.
        Returns:
            list[EmbeddedChunkT]: List of embedded chunk models.
        """
        embedding_model_input = [data_model.content for data_model in data_model]
        embeddings = embedding_model(embedding_model_input, to_list=True)
        embedded_chunk = [
            self.map_model(data_model, cast(list[float], embedding))
            for data_model, embedding in zip(data_model, embeddings, strict=False)
        ]

        return embedded_chunk

    def embed(self, data_model: ChunkT) -> EmbeddedChunkT:
        """Embed a single chunk.
        Args:
            data_model (ChunkT): The chunk model to embed.
        Returns:
            EmbeddedChunkT: The embedded chunk model.
        """
        embedding = embedding_model(data_model.content)
        return self.map_model(data_model, cast(list[float], embedding))

    @abstractmethod
    def map_model(self, data_model: ChunkT, embedding: list[float]) -> EmbeddedChunkT:
        """Build a storage document that includes the embedding."""


class ArticleEmbeddingHandler(EmbeddingDataHandler):
    """Embedding handler for article chunks."""

    def map_model(
        self, data_model: ArticleChunk, embedding: list[float]
    ) -> EmbeddedArticleChunk:
        """Map an article chunk and its embedding into a storage model.
        Args:
            data_model (ArticleChunk): The article chunk to map.
            embedding (list[float]): The embedding vector for the chunk.
        Returns:
            EmbeddedArticleChunk: The embedded article chunk model.
        """
        return EmbeddedArticleChunk(
            id=data_model.id,
            content=data_model.content,
            embedding=embedding,
            platform=data_model.platform,
            link=data_model.link,
            document_id=data_model.document_id,
            batch_id=data_model.batch_id,
            metadata={
                "embedding_model_provider": embedding_model.provider,
                "embedding_model_name": embedding_model.model_name,
                "embedding_size": embedding_model.embedding_size,
                "max_input_length": embedding_model.max_input_length,
            },
        )


class RepositoryEmbeddingHandler(EmbeddingDataHandler):
    """Embedding handler for repository chunks."""

    def map_model(
        self, data_model: RepositoryChunk, embedding: list[float]
    ) -> EmbeddedRepositoryChunk:
        """Map a repository chunk and its embedding into a storage model.
        Args:
            data_model (RepositoryChunk): The repository chunk to map.
            embedding (list[float]): The embedding vector for the chunk.
            Returns:
            EmbeddedRepositoryChunk: The embedded repository chunk model.
        """
        return EmbeddedRepositoryChunk(
            id=data_model.id,
            content=data_model.content,
            embedding=embedding,
            platform=data_model.platform,
            name=data_model.name,
            link=data_model.link,
            document_id=data_model.document_id,
            batch_id=data_model.batch_id,
            metadata={
                "embedding_model_provider": embedding_model.provider,
                "embedding_model_name": embedding_model.model_name,
                "embedding_size": embedding_model.embedding_size,
                "max_input_length": embedding_model.max_input_length,
            },
        )


class YoutubeEmbeddingHandler(EmbeddingDataHandler):
    """Embedding handler for YouTube chunks."""

    def map_model(
        self, data_model: YoutubeChunk, embedding: list[float]
    ) -> EmbeddedYoutubeChunk:
        """Map a YouTube chunk and its embedding into a storage model.
        Args:
            data_model (YoutubeChunk): The YouTube chunk to map.
            embedding (list[float]): The embedding vector for the chunk.
        Returns:
            EmbeddedYoutubeChunk: The embedded YouTube chunk model.
        """
        return EmbeddedYoutubeChunk(
            id=data_model.id,
            content=data_model.content,
            embedding=embedding,
            platform=data_model.platform,
            link=data_model.link,
            document_id=data_model.document_id,
            batch_id=data_model.batch_id,
            metadata={
                "embedding_model_provider": embedding_model.provider,
                "embedding_size": embedding_model.embedding_size,
                "max_input_length": embedding_model.max_input_length,
            },
        )


class PDFEmbeddingHandler(EmbeddingDataHandler):
    """Embedding handler for PDF chunks."""

    def map_model(
        self, data_model: PDFChunk, embedding: list[float]
    ) -> EmbeddedPDFChunk:
        """Map a PDF chunk and its embedding into a storage model.
        Args:
            data_model (PDFChunk): The PDF chunk to map.
            embedding (list[float]): The embedding vector for the chunk.
        Returns:
            EmbeddedPDFChunk: The embedded PDF chunk model.
        """
        return EmbeddedPDFChunk(
            id=data_model.id,
            content=data_model.content,
            embedding=embedding,
            name=data_model.name,
            path=data_model.path,
            document_id=data_model.document_id,
            batch_id=data_model.batch_id,
            metadata={
                "embedding_model_provider": embedding_model.provider,
                "embedding_model_name": embedding_model.model_name,
                "embedding_size": embedding_model.embedding_size,
                "max_input_length": embedding_model.max_input_length,
            },
        )
