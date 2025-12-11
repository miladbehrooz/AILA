import hashlib
from pathlib import Path
from uuid import UUID
from docling.document_converter import DocumentConverter
from .base import FileExtractor, ExtractionResult
from backend.etl.domain.documents import PDFDocument
from backend.settings import settings
from backend.utils import logger


class PDFFileExtractor(FileExtractor):
    """Extractor for PDF files.

    Attributes:
        model (type): The document model associated with PDF files.
    """

    model = PDFDocument

    def extract(self, path: str, **kwargs) -> ExtractionResult:
        """Extract content from a PDF file and persist it.

        Args:
            path (str): Path to the PDF file.
            **kwargs: Additional keyword arguments.

        Returns:
            ExtractionResult: INSERTED when stored successfully or DUPLICATE when the
                same PDF already exists.
        """
        resolved_path = Path(path)
        if not resolved_path.is_absolute():
            resolved_path = (settings.PROJECT_ROOT / resolved_path).resolve()

        file_hash = self._compute_hash(resolved_path)

        old_model = self.model.find(hash=file_hash)
        if old_model is None:
            # Backward compatibility for documents ingested before hashing was added.
            old_model = self.model.find(path=path)

        if old_model is not None:
            logger.info(
                "PDF file already exists in the database: %s (hash=%s)", path, file_hash
            )

            return ExtractionResult.DUPLICATE
        logger.info(f"Starting extracting content from PDF file: {path}")

        file_name = path.split("/")[-1].split(".")[0]

        converter = DocumentConverter()
        content = converter.convert(str(resolved_path))

        content = content.document.export_to_markdown()

        content = {"Content": content}
        batch_id = kwargs.get("batch_id")
        if batch_id is None:
            raise ValueError("batch_id is required to extract a PDF file.")
        if isinstance(batch_id, str):
            batch_id = UUID(batch_id)

        instance = self.model(
            path=path,
            content=content,
            name=file_name,
            batch_id=batch_id,
            hash=file_hash,
        )
        instance.save()

        logger.info(f"Finished extracting content from PDF file: {path}")
        return ExtractionResult.INSERTED

    def _compute_hash(self, path: Path) -> str:
        """Compute the hash of a file.

        Args:
            path (Path): Path to the file.

        Returns:
            str: Hash value.
        """
        hasher = hashlib.sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()


class WordFileExtractor(FileExtractor):
    """Extractor for Word files."""

    def extract(self, source: str, **kwargs) -> None:
        """Extract content from a Word file.

        Args:
            source (str): Path to the Word file.
            **kwargs: Additional keyword arguments.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError


class TextFileExtractor(FileExtractor):
    """Extractor for text files."""

    def extract(self, source: str, **kwargs) -> None:
        """Extract content from a text file.

        Args:
            source (str): Path to the text file.
            **kwargs: Additional keyword arguments.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError


if __name__ == "__main__":
    extractor = PDFFileExtractor()
    extractor.extract("./backend/data/book.pdf")
