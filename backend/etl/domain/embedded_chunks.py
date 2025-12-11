from abc import ABC

from pydantic import UUID4, Field
from uuid import UUID

from backend.etl.domain.types import DataCategory

from .base import VectorBaseDocument


class EmbeddedChunk(VectorBaseDocument, ABC):
    """Base embedded chunk stored in Qdrant.
    Attributes:
        content (str): Text content of the chunk.
        embedding (list[float] | None): Vector embedding of the chunk.
        document_id (UUID4): Identifier of the source document.
        metadata (dict): Additional metadata associated with the chunk.
        batch_id (UUID): Identifier of the ingestion batch.
    """

    content: str
    embedding: list[float] | None
    document_id: UUID4
    metadata: dict = Field(default_factory=dict)
    batch_id: UUID

    @classmethod
    def to_context(cls, chunks: list["EmbeddedChunk"]) -> str:
        """Render embedded chunks into a text block for prompting.
        Args:
            chunks (list[EmbeddedChunk]): List of embedded chunks.
        Returns:
            str: Formatted text block representing the chunks.
        """
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
    """Embedded chunk originating from a YouTube transcript.
    Attributes:
        platform (str): Platform hosting the video.
        link (str): URL of the YouTube video.
    """

    platform: str
    link: str

    class Config:
        """Collection metadata for YouTube embeddings."""

        name = "embedded_youtube_videos"
        category = DataCategory.YOUTUBEVIDEOS
        use_vector_index = True


class EmbeddedArticleChunk(EmbeddedChunk):
    """Embedded chunk originating from an article.
    Attributes:
        platform (str): Platform from which the article was sourced.
        link (str): URL of the article.
    """

    platform: str
    link: str

    class Config:
        """Collection metadata for article embeddings."""

        name = "embedded_articles"
        category = DataCategory.ARTICLES
        use_vector_index = True


class EmbeddedRepositoryChunk(EmbeddedChunk):
    """Embedded chunk originating from a source-code repository.
    Attributes:
        platform (str): Platform hosting the repository.
        name (str): Name of the repository.
        link (str): URL of the repository.
    """

    platform: str
    name: str
    link: str

    class Config:
        """Collection metadata for repository embeddings."""

        name = "embedded_repositories"
        category = DataCategory.REPOSITORIES
        use_vector_index = True


class EmbeddedPDFChunk(EmbeddedChunk):
    """Embedded chunk originating from a PDF.
    Attributes:
        name (str): Name of the PDF document.
        path (str): File path of the PDF document.
    """

    name: str
    path: str

    class Config:
        """Collection metadata for PDF embeddings."""

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
