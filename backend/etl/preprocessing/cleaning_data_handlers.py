from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from backend.etl.domain.cleaned_documents import (
    CleanedDocument,
    CleanedArticleDocument,
    CleanedRepositoryDocument,
    CleanedYoutubeDocument,
    CleanedPDFDocument,
)
from backend.etl.domain.documents import (
    BaseDocument,
    ArticleDocument,
    RepositoryDocument,
    YoutubeDocument,
    PDFDocument,
)
from .operations.cleaning import clean_text, clean_youtube_transcript


DocumentT = TypeVar("DocumentT", bound=BaseDocument)
CleanedDocumentT = TypeVar("CleanedDocumentT", bound=CleanedDocument)


class CleaningDataHandler(ABC, Generic[DocumentT, CleanedDocumentT]):

    @abstractmethod
    def clean(self, data_model: DocumentT) -> CleanedDocumentT:
        pass


class ArticleCleaningHandler(CleaningDataHandler):
    def clean(self, data_model: ArticleDocument) -> CleanedArticleDocument:
        valid_content = [content for content in data_model.content.values() if content]

        return CleanedArticleDocument(
            id=data_model.id,
            content=clean_text(" #### ".join(valid_content)),
            platform=data_model.platform,
            link=data_model.link,
            batch_id=data_model.batch_id,
        )


class RepositoryCleaningHandler(CleaningDataHandler):
    def clean(self, data_model: RepositoryDocument) -> CleanedRepositoryDocument:
        return CleanedRepositoryDocument(
            id=data_model.id,
            content=clean_text(" #### ".join(data_model.content.values())),
            platform=data_model.platform,
            name=data_model.name,
            link=data_model.link,
            batch_id=data_model.batch_id,
        )


class YoutubeCleaningHandler(CleaningDataHandler):
    def clean(self, data_model: YoutubeDocument) -> CleanedYoutubeDocument:
        return CleanedYoutubeDocument(
            id=data_model.id,
            content=clean_youtube_transcript(data_model.content["Content"]),
            platform=data_model.platform,
            link=data_model.link,
            batch_id=data_model.batch_id,
        )


class PDFCleaningHandler(CleaningDataHandler):
    def clean(self, data_model: PDFDocument) -> CleanedPDFDocument:
        return CleanedPDFDocument(
            id=data_model.id,
            content=clean_text(" #### ".join(data_model.content.values())),
            name=data_model.name,
            path=data_model.path,
            batch_id=data_model.batch_id,
        )
