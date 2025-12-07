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

    @property
    def metadata(self) -> dict:
        return {
            "chunk_size": 500,
            "chunk_overlap": 50,
        }

    @abstractmethod
    def chunk(self, data_model: CleanedDocumentT) -> list[ChunkT]:
        pass


class ArticleChunkingHandler(ChunkingDataHandler):
    @property
    def metadata(self) -> dict:
        return {
            "min_length": 1000,
            "max_length": 2000,
        }

    def chunk(self, data_model: CleanedArticleDocument) -> list[ArticleChunk]:
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
    @property
    def metadata(self) -> dict:
        return {
            "chunk_size": 1500,
            "chunk_overlap": 100,
        }

    def chunk(self, data_model: CleanedRepositoryDocument) -> list[RepositoryChunk]:
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
    @property
    def metadata(self) -> dict:
        return {
            "chunk_size": 1000,
            "chunk_overlap": 50,
        }

    def chunk(self, data_model: CleanedPDFDocument) -> list[PDFChunk]:
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
    @property
    def metadata(self) -> dict:
        return {
            "chunk_size": 500,
            "chunk_overlap": 50,
        }

    def chunk(self, data_model: CleanedYoutubeDocument) -> list[YoutubeChunk]:
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
