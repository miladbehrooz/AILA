from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from backend.etl.domain.cleaned_documents import (
    CleanedArticleDocument,
    CleanedDocument,
    CleanedPDFDocument,
    CleanedRepositoryDocument,
    CleanedYoutubeDocument,
)
from backend.etl.domain.documents import (
    ArticleDocument,
    BaseDocument,
    PDFDocument,
    RepositoryDocument,
    YoutubeDocument,
)

from .operations.cleaning import clean_text, clean_youtube_transcript

DocumentT = TypeVar("DocumentT", bound=BaseDocument)
CleanedDocumentT = TypeVar("CleanedDocumentT", bound=CleanedDocument)


class CleaningDataHandler(ABC, Generic[DocumentT, CleanedDocumentT]):
    """Base interface for converting raw documents into cleaned variants.
    Args:
        data_model (DocumentT): The raw document to be cleaned.
    Returns:
        CleanedDocumentT: The cleaned document model.
    """

    @abstractmethod
    def clean(self, data_model: DocumentT) -> CleanedDocumentT:
        """Transform a raw document into its cleaned form.
        Args:
            data_model (DocumentT): The raw document to be cleaned.
        Returns:
            CleanedDocumentT: The cleaned document model.
        """


class ArticleCleaningHandler(CleaningDataHandler):
    """Cleaner specialized for article documents."""

    def clean(self, data_model: ArticleDocument) -> CleanedArticleDocument:
        """Strip empty fields and normalize article content.
        Args:
            data_model (ArticleDocument): The raw article document.
        Returns:
            CleanedArticleDocument: The cleaned article document model.
        """
        valid_content = [content for content in data_model.content.values() if content]

        return CleanedArticleDocument(
            id=data_model.id,
            content=clean_text(" #### ".join(valid_content)),
            platform=data_model.platform,
            link=data_model.link,
            batch_id=data_model.batch_id,
        )


class RepositoryCleaningHandler(CleaningDataHandler):
    """Cleaner specialized for repository documents."""

    def clean(self, data_model: RepositoryDocument) -> CleanedRepositoryDocument:
        """Normalize repository file contents into a single string.
        Args:
            data_model (RepositoryDocument): The raw repository document.
        Returns:
            CleanedRepositoryDocument: The cleaned repository document model.
        """
        return CleanedRepositoryDocument(
            id=data_model.id,
            content=clean_text(" #### ".join(data_model.content.values())),
            platform=data_model.platform,
            name=data_model.name,
            link=data_model.link,
            batch_id=data_model.batch_id,
        )


class YoutubeCleaningHandler(CleaningDataHandler):
    """Cleaner specialized for YouTube transcripts."""

    def clean(self, data_model: YoutubeDocument) -> CleanedYoutubeDocument:
        """Convert the transcript into plain text.
        Args:
            data_model (YoutubeDocument): The raw YouTube document.
        Returns:
            CleanedYoutubeDocument: The cleaned YouTube document model.
        """
        return CleanedYoutubeDocument(
            id=data_model.id,
            content=clean_youtube_transcript(data_model.content["Content"]),
            platform=data_model.platform,
            link=data_model.link,
            batch_id=data_model.batch_id,
        )


class PDFCleaningHandler(CleaningDataHandler):
    """Cleaner specialized for PDF documents."""

    def clean(self, data_model: PDFDocument) -> CleanedPDFDocument:
        """Normalize PDF content from the converter output.
        Args:
            data_model (PDFDocument): The raw PDF document.
        Returns:
            CleanedPDFDocument: The cleaned PDF document model.
        """
        return CleanedPDFDocument(
            id=data_model.id,
            content=clean_text(" #### ".join(data_model.content.values())),
            name=data_model.name,
            path=data_model.path,
            batch_id=data_model.batch_id,
        )
