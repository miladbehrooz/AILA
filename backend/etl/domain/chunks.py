from abc import ABC
from typing import Optional
from uuid import UUID

from pydantic import UUID4, Field

from backend.etl.domain.base.vector import VectorBaseDocument
from backend.etl.domain.types import DataCategory


class Chunk(VectorBaseDocument, ABC):
    """Base chunk created from a cleaned document.
    Attributes:
        content (str): Text content of the chunk.
        document_id (UUID4): Identifier of the source document.
        metadata (dict): Additional metadata associated with the chunk.
        batch_id (UUID): Identifier of the ingestion batch.
    """

    content: str
    document_id: UUID4
    metadata: dict = Field(default_factory=dict)
    batch_id: UUID


class ArticleChunk(Chunk):
    """Chunk derived from an article.
    Attributes:
        link (str): URL of the article.
        platform (str): Platform from which the article was sourced.
    """

    link: str
    platform: str

    class Config:
        """Collection metadata for article chunks."""

        category = DataCategory.ARTICLES


class RepositoryChunk(Chunk):
    """Chunk derived from a repository.
    Attributes:
        name (str): Name of the repository.
        link (str): URL of the repository.
        platform (str): Platform hosting the repository.
    """

    name: str
    link: str
    platform: str

    class Config:
        """Collection metadata for repository chunks."""

        category = DataCategory.REPOSITORIES


class YoutubeChunk(Chunk):
    """Chunk derived from a YouTube transcript.
    Attributes:
        link (str): URL of the YouTube video.
        platform (str): Platform hosting the video.
    """

    link: str
    platform: str

    class Config:
        """Collection metadata for YouTube chunks."""

        category = DataCategory.YOUTUBEVIDEOS


class PDFChunk(Chunk):
    """Chunk derived from a PDF document.
    Attributes:
        name (str): Name of the PDF document.
        path (str): File path of the PDF document.
    """

    name: str
    path: str

    class Config:
        """Collection metadata for PDF chunks."""

        category = DataCategory.PDFS
