from abc import ABC
from typing import Optional
from uuid import UUID

from pydantic import UUID4, Field

from backend.etl.domain.base.vector import VectorBaseDocument
from backend.etl.domain.types import DataCategory


class Chunk(VectorBaseDocument, ABC):
    content: str
    document_id: UUID4
    metadata: dict = Field(default_factory=dict)
    batch_id: UUID


class ArticleChunk(Chunk):
    link: str
    platform: str

    class Config:
        category = DataCategory.ARTICLES


class RepositoryChunk(Chunk):
    name: str
    link: str
    platform: str

    class Config:
        category = DataCategory.REPOSITORIES


class YoutubeChunk(Chunk):
    link: str
    platform: str

    class Config:
        category = DataCategory.YOUTUBEVIDEOS


class PDFChunk(Chunk):
    name: str
    path: str

    class Config:
        category = DataCategory.PDFS
