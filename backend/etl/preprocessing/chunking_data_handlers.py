import hashlib
from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

from backend.etl.domain.chunks import (
    Chunk,
    ArticleChunk,
    RepositoryChunk,
    PDFChunk,
    YoutubeChunk,
)
from backend.etl.domain.cleaned_documents import (
    CleanedDocument,
    CleanedArticleDocument,
    CleanedPDFDocument,
    CleanedRepositoryDocument,
    CleanedYoutubeDocument,
)

from .operations import chunk_article, chunk_text

CleanedDocumentT = TypeVar("CleanedDocumentT", bound=CleanedDocument)
ChunkT = TypeVar("ChunkT", bound=Chunk)


class ChunkingDataHandler(ABC, Generic[CleanedDocumentT, ChunkT]):
    """Base interface for splitting cleaned documents into chunks.
    Attributes:
        metadata (dict): Chunking parameters used by the handler.
    """

    @property
    def metadata(self) -> dict:
        """Describe chunking parameters applied by the handler.
        Returns:
            dict: Chunking configuration parameters.
        """
        return {
            "chunk_size": 500,
            "chunk_overlap": 50,
        }

    @abstractmethod
    def chunk(self, data_model: CleanedDocumentT) -> list[ChunkT]:
        """Split the cleaned document into chunk models.
        Args:
            data_model (CleanedDocumentT): The cleaned document to chunk.
        Returns:
            list[ChunkT]: List of chunk models derived from the document.
        """


class ArticleChunkingHandler(ChunkingDataHandler):
    """Chunking strategy optimized for long-form articles.
    Attributes:
        metadata (dict): Chunking parameters specific to articles.
    """

    @property
    def metadata(self) -> dict:
        """Describe the target article chunk length boundaries.
        Returns:
            dict: Article-specific chunking configuration.
        """
        return {
            "min_length": 1000,
            "max_length": 2000,
        }

    def chunk(self, data_model: CleanedArticleDocument) -> list[ArticleChunk]:
        """Split article text into overlapping extracts.
        Args:
            data_model (CleanedArticleDocument): The cleaned article to chunk.
        Returns:
            list[ArticleChunk]: List of article chunk models.
        """
        data_models_list = []

        cleaned_content = data_model.content
        chunks = chunk_article(
            cleaned_content,
            min_length=self.metadata["min_length"],
            max_length=self.metadata["max_length"],
        )

        for chunk in chunks:
            chunk_id = hashlib.md5(chunk.encode()).hexdigest()
            model = ArticleChunk(
                id=UUID(chunk_id, version=4),
                content=chunk,
                platform=data_model.platform,
                link=data_model.link,
                document_id=data_model.id,
                metadata=self.metadata,
                batch_id=data_model.batch_id,
            )
            data_models_list.append(model)

        return data_models_list


class RepositoryChunkingHandler(ChunkingDataHandler):
    """Chunking strategy for repository file contents.
    Attributes:
        metadata (dict): Chunking parameters specific to repositories.
    """

    @property
    def metadata(self) -> dict:
        """Expose repository-specific chunking parameters."""
        return {
            "chunk_size": 1500,
            "chunk_overlap": 100,
        }

    def chunk(self, data_model: CleanedRepositoryDocument) -> list[RepositoryChunk]:
        """Split repository text into balanced windows.
        Args:
            data_model (CleanedRepositoryDocument): The cleaned repository to chunk.
        Returns:
            list[RepositoryChunk]: List of repository chunk models.
        """
        data_models_list = []

        cleaned_content = data_model.content
        chunks = chunk_text(
            cleaned_content,
            chunk_size=self.metadata["chunk_size"],
            chunk_overlap=self.metadata["chunk_overlap"],
        )

        for chunk in chunks:
            chunk_id = hashlib.md5(chunk.encode()).hexdigest()
            model = RepositoryChunk(
                id=UUID(chunk_id, version=4),
                content=chunk,
                platform=data_model.platform,
                name=data_model.name,
                link=data_model.link,
                document_id=data_model.id,
                metadata=self.metadata,
                batch_id=data_model.batch_id,
            )
            data_models_list.append(model)

        return data_models_list


class PDFChunkingHandler(ChunkingDataHandler):
    """Chunking strategy for PDFs produced by the converter.
    Attributes:
        metadata (dict): Chunking parameters specific to PDFs.
    """

    @property
    def metadata(self) -> dict:
        """Expose PDF-specific chunking parameters.
        Returns:
            dict: PDF chunking configuration.
        """
        return {
            "chunk_size": 1000,
            "chunk_overlap": 50,
        }

    def chunk(self, data_model: CleanedPDFDocument) -> list[PDFChunk]:
        """Split PDF text into fixed-size windows.
        Args:
            data_model (CleanedPDFDocument): The cleaned PDF to chunk.
        Returns:
            list[PDFChunk]: List of PDF chunk models.
        """
        data_models_list = []

        cleaned_content = data_model.content
        chunks = chunk_text(
            cleaned_content,
            chunk_size=self.metadata["chunk_size"],
            chunk_overlap=self.metadata["chunk_overlap"],
        )

        for chunk in chunks:
            chunk_id = hashlib.md5(chunk.encode()).hexdigest()
            model = PDFChunk(
                id=UUID(chunk_id, version=4),
                content=chunk,
                name=data_model.name,
                path=data_model.path,
                document_id=data_model.id,
                metadata=self.metadata,
                batch_id=data_model.batch_id,
            )
            data_models_list.append(model)

        return data_models_list


class YoutubeChunkingHandler(ChunkingDataHandler):
    """Chunking strategy for YouTube transcripts.
    Attributes:
        metadata (dict): Chunking parameters specific to YouTube transcripts.
    """

    @property
    def metadata(self) -> dict:
        """Expose chunking parameters tuned for transcripts.
        Returns:
            dict: YouTube transcript chunking configuration.
        """
        return {
            "chunk_size": 500,
            "chunk_overlap": 50,
        }

    def chunk(self, data_model: CleanedYoutubeDocument) -> list[YoutubeChunk]:
        """Split transcript text into manageable pieces.
        Args:
            data_model (CleanedYoutubeDocument): The cleaned YouTube transcript to chunk.
        Returns:
            list[YoutubeChunk]: List of YouTube chunk models.
        """
        data_models_list = []

        cleaned_content = data_model.content
        chunks = chunk_text(
            cleaned_content,
            chunk_size=self.metadata["chunk_size"],
            chunk_overlap=self.metadata["chunk_overlap"],
        )

        for chunk in chunks:
            chunk_id = hashlib.md5(chunk.encode()).hexdigest()
            model = YoutubeChunk(
                id=UUID(chunk_id, version=4),
                content=chunk,
                platform=data_model.platform,
                link=data_model.link,
                document_id=data_model.id,
                metadata=self.metadata,
                batch_id=data_model.batch_id,
            )
            data_models_list.append(model)

        return data_models_list
