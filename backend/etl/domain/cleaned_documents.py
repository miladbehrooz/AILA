from abc import ABC
from typing import Optional
from uuid import UUID

from .base.vector import VectorBaseDocument
from .types import DataCategory


class CleanedDocument(VectorBaseDocument, ABC):
    """Base cleaned document emitted by preprocessing.
    Attributes:
        content (str): Cleaned text content of the document.
        batch_id (UUID): Identifier of the ingestion batch.
    """

    content: str
    batch_id: UUID


class CleanedArticleDocument(CleanedDocument):
    """Cleaned document derived from an article.
    Attributes:
        platform (str): Platform from which the article was sourced.
        link (str): URL of the article.
        image (Optional[str]): Optional image URL associated with the article.
    """

    platform: str
    link: str
    image: Optional[str] = None

    class Config:
        """Collection metadata for cleaned articles."""

        name = "cleaned_articles"
        category = DataCategory.ARTICLES
        use_vector_index = False


class CleanedYoutubeDocument(CleanedDocument):
    """Cleaned document derived from a YouTube transcript.
    Attributes:
        platform (str): Platform hosting the video.
        link (str): URL of the YouTube video.
    """

    platform: str
    link: str

    class Config:
        """Collection metadata for cleaned videos."""

        name = "cleaned_youtube_videos"
        category = DataCategory.YOUTUBEVIDEOS
        use_vector_index = False


class CleanedRepositoryDocument(CleanedDocument):
    """Cleaned document derived from a repository.
    Attributes:
        platform (str): Platform hosting the repository.
        name (str): Name of the repository.
        link (str): URL of the repository.
    """

    platform: str
    name: str
    link: str

    class Config:
        """Collection metadata for cleaned repositories."""

        name = "cleaned_repositories"
        category = DataCategory.REPOSITORIES
        use_vector_index = False


class CleanedPDFDocument(CleanedDocument):
    """Cleaned document derived from a PDF.
    Attributes:
        name (str): Name of the PDF document.
        path (str): File path of the PDF document.
    """

    name: str
    path: str

    class Config:
        """Collection metadata for cleaned PDFs."""

        name = "cleaned_pdfs"
        category = DataCategory.PDFS
        use_vector_index = False
