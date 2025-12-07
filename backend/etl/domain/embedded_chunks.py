from abc import ABC

from pydantic import UUID4, Field

from backend.etl.domain.types import DataCategory

from .base import VectorBaseDocument


class EmbeddedChunk(VectorBaseDocument, ABC):
    content: str
    embedding: list[float] | None
    document_id: UUID4
    metadata: dict = Field(default_factory=dict)
    batch_id: str

    @classmethod
    def to_context(cls, chunks: list["EmbeddedChunk"]) -> str:
        context = ""
        for i, chunk in enumerate(chunks):
            fields = chunk.model_dump()
            # Optionally remove fields that are not useful
            fields.pop("embedding", None)
            fields.pop("document_id", None)

            formatted_fields = "\n".join(
                f"{k.capitalize()}: {v}" for k, v in fields.items()
            )

            context += f"""Chunk {i + 1}:
            Type: {chunk.__class__.__name__}
            {formatted_fields}
            """
        return context.strip()


class EmbeddedYoutubeChunk(EmbeddedChunk):
    platform: str
    link: str

    class Config:
        name = "embedded_youtube_videos"
        category = DataCategory.YOUTUBEVIDEOS
        use_vector_index = True


class EmbeddedArticleChunk(EmbeddedChunk):
    platform: str
    link: str

    class Config:
        name = "embedded_articles"
        category = DataCategory.ARTICLES
        use_vector_index = True


class EmbeddedRepositoryChunk(EmbeddedChunk):
    platform: str
    name: str
    link: str

    class Config:
        name = "embedded_repositories"
        category = DataCategory.REPOSITORIES
        use_vector_index = True


class EmbeddedPDFChunk(EmbeddedChunk):
    name: str
    path: str

    class Config:
        name = "embedded_pdfs"
        category = DataCategory.PDFS
        use_vector_index = True


if __name__ == "__main__":
    emb_pdf_chunk = EmbeddedPDFChunk(
        content="Sample PDF content",
        embedding=[0.1, 0.2, 0.3],
        document_id="12345678901223323232323232323232",
        metadata={"author": "John Doe", "title": "Sample PDF"},
        name="Sample PDF",
        path="/path/to/sample.pdf",
    )
    print(emb_pdf_chunk.to_context([emb_pdf_chunk]))
